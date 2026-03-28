# GlanceOS Frontend

## Run

```bash
npm install
npm run dev
```

## Remote Backend Setup (Fixes Vite ws proxy ECONNREFUSED/ECONNRESET)

When backend is running on another machine, set frontend env vars before starting Vite.

1. Copy `.env.example` to `.env`.
2. Set:

```bash
VITE_BACKEND_URL=http://<remote-machine-ip>:8000
# optional explicit override
# VITE_WS_URL=ws://<remote-machine-ip>:8000/ws
```

Optional (if you want to avoid Vite proxy entirely):

```bash
VITE_DISABLE_PROXY=true
```

Then restart `npm run dev`.

## Env Variables

- `VITE_BACKEND_URL`: Base backend URL for deriving websocket endpoint.
- `VITE_WS_URL`: Explicit websocket URL override.
- `VITE_PROXY_API_TARGET`: Vite `/api` proxy target (default `http://localhost:8000`).
- `VITE_PROXY_WS_TARGET`: Vite `/ws` proxy target (default `ws://localhost:8000`).
- `VITE_DISABLE_PROXY`: Set `true` to disable `/api` and `/ws` proxy.
