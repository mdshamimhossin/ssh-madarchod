import asyncio
import os
from http import HTTPStatus
from urllib.parse import urlsplit, parse_qs
from websockets.asyncio.server import serve

PORT = int(os.environ.get('PORT', '8080'))
SSH_HOST = os.environ.get('SSH_HOST', '127.0.0.1')
SSH_PORT = int(os.environ.get('SSH_PORT', '22'))
RELAY_TOKEN = os.environ.get('RELAY_TOKEN', '')

async def process_request(connection, request):
    if request.path == '/health':
        return connection.respond(HTTPStatus.OK, 'OK\n')
    if urlsplit(request.path).path != '/ssh':
        return connection.respond(HTTPStatus.NOT_FOUND, 'Not found\n')
    token = parse_qs(urlsplit(request.path).query).get('token', [''])[0]
    if not RELAY_TOKEN or token != RELAY_TOKEN:
        return connection.respond(HTTPStatus.FORBIDDEN, 'Forbidden\n')
    return None

async def relay(ws):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(SSH_HOST, SSH_PORT), timeout=15)
    except (OSError, TimeoutError):
        await ws.close(code=1011, reason='SSH backend unavailable')
        return

    async def ws_to_tcp():
        async for message in ws:
            if not isinstance(message, bytes):
                await ws.close(code=1003, reason='Binary frames required')
                break
            writer.write(message)
            await writer.drain()

    async def tcp_to_ws():
        while data := await reader.read(16384):
            await ws.send(data)

    tasks = [asyncio.create_task(ws_to_tcp()), asyncio.create_task(tcp_to_ws())]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    async with serve(relay, '0.0.0.0', PORT, process_request=process_request, max_size=None, ping_interval=25, ping_timeout=30):
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
