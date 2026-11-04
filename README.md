# Cloud Run WebSocket-to-SSH relay (standard WebSocket only)

This repository implements a WebSocket relay to an existing SSH server. It **does not support** a key-less `GET / HTTP/1.1` Upgrade payload as a raw SSH transport. Clients must perform a complete RFC 6455 WebSocket handshake and send SSH bytes as **binary WebSocket frames**.

## Files
- `Dockerfile` — Cloud Run container
- `requirements.txt` — Python WebSocket library
- `server.py` — `/ssh?token=...` WebSocket relay and `/health` endpoint

## Deploy from Cloud Shell

```bash
gcloud run deploy ssh-ws-relay --source . --region us-west1 --port 8080 --timeout 3600 --allow-unauthenticated --set-env-vars SSH_HOST=YOUR_VPS_IP,SSH_PORT=22,RELAY_TOKEN=REPLACE_WITH_LONG_RANDOM_SECRET
```

Your VPS firewall must allow Cloud Run to reach its SSH port. Cloud Run outbound IP is dynamic unless you configure static egress. Avoid exposing SSH publicly without firewall controls, strong SSH keys, and rate limiting. Store relay tokens in Secret Manager for production instead of committing them to GitHub or using plain env vars.

## Client

A WebSocket client must connect to `wss://YOUR_SERVICE.run.app/ssh?token=YOUR_TOKEN` using a standard handshake, then bridge binary WebSocket frames to SSH. An HTTP Injector custom payload containing only GET/Host/Upgrade/Connection is **not** a compatible WebSocket client by itself.

Cloud Run WebSocket sessions are subject to request timeout (max 60 minutes). Reconnection is necessary.
