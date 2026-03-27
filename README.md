# GlanceOS

A smart, tile-based dashboard for Raspberry Pi (and any Linux/macOS machine). Glassmorphic draggable/resizable widgets, real-time data via WebSocket, lofi ASCII art vibes.

```
┌────────┬────────┬────────┬────────┐
│ Clock  │  Lofi  │Weather │ System │
├────────┴──┬─────┴──┬─────┴────────┤
│  Cricket  │  News  │   Trending   │
├───────────┴────────┴──────────────┤
│          GitHub Activity          │
└───────────────────────────────────┘
```

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (with npm)
- **Git**

## Quick Start

```bash
git clone <your-repo-url> && cd GlanceOS
chmod +x setup.sh
./setup.sh
```

This creates a Python venv, installs all dependencies, creates `backend/.env`, and prompts for API keys during setup.

For non-interactive installs, export keys before running setup:

```bash
export WEATHER_API_KEY="your_openweathermap_key"
export GITHUB_TOKEN="your_github_token"
./setup.sh
```

Then start both services:

```bash
# Terminal 1 — Backend
cd backend
source venv/bin/activate
python run.py

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## Manual Setup

If you prefer to do it step by step:

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env with your keys
python run.py
```

The API server starts at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard starts at `http://localhost:5173` and proxies API/WebSocket requests to the backend.

## Configuration

`setup.sh` now asks for API keys and writes them to `backend/.env`.
You can still edit `backend/.env` manually:

| Variable          | Description                          | Required |
|-------------------|--------------------------------------|----------|
| `WEATHER_API_KEY` | OpenWeatherMap API key               | No*      |
| `GITHUB_TOKEN`    | GitHub personal access token         | No*      |
| `WEATHER_CITY`    | Default weather city (e.g. Hyderabad,IN) | No |
| `GITHUB_USERNAME` | GitHub username for activity widget  | No       |
| `HOST`            | Backend bind address (default `0.0.0.0`) | No   |
| `PORT`            | Backend port (default `8000`)        | No       |
| `LOG_LEVEL`       | Backend log verbosity (default `WARNING`) | No |

*Widgets show sample data when keys are not configured.

Get your keys:
- Weather: https://openweathermap.org/api (free tier)
- GitHub: https://github.com/settings/tokens (no scopes needed for public data)

## Widgets

| Widget     | Data Source           | Update Interval |
|------------|-----------------------|-----------------|
| Clock      | Client-side           | 1s              |
| Lofi Art   | ASCII scenes (local)  | 12s cycle       |
| Weather    | OpenWeatherMap API    | 10 min          |
| System     | psutil (CPU/RAM/Disk) | 3s              |
| Cricket    | ESPN / CricAPI        | 2 min           |
| News       | Google News RSS       | 15 min          |
| Trending   | GitHub Trending       | 30 min          |
| GitHub     | GitHub Events API     | 5 min           |

All widgets are draggable and resizable. Layouts persist in localStorage.

## Architecture

```
Frontend (React + Tailwind + Vite)
        │
   WebSocket / REST
        │
Backend (Python FastAPI + APScheduler)
        │
   Linux OS layer (psutil, systemd)
```

- **Frontend**: React 19, Tailwind CSS v4, react-grid-layout, Framer Motion
- **Backend**: FastAPI, APScheduler, httpx, psutil, WebSockets
- **Data flow**: Backend polls APIs on schedule → caches results → pushes via WebSocket → frontend renders

## Raspberry Pi Deployment

```bash
# Install the backend as a systemd service
sudo cp deploy/glanceos-backend.service /etc/systemd/system/
sudo systemctl enable --now glanceos-backend

# Build the frontend for production (served by FastAPI at :8000)
cd frontend
npm run build

# Launch Chromium in kiosk mode
chmod +x deploy/kiosk.sh
deploy/kiosk.sh
```

Production URL: `http://localhost:8000`

## Project Structure

```
GlanceOS/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── config.py            # Pydantic settings (.env)
│   │   ├── ws_manager.py        # WebSocket connection manager
│   │   ├── scheduler.py         # APScheduler jobs
│   │   ├── routers/
│   │   │   ├── api.py           # REST endpoints
│   │   │   └── ws.py            # WebSocket endpoint
│   │   └── services/
│   │       ├── system_monitor.py
│   │       ├── weather.py
│   │       ├── github.py
│   │       ├── cricket.py
│   │       ├── news.py
│   │       ├── trending.py
│   │       └── lofi.py
│   ├── run.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── WidgetCard.jsx
│   │   │   └── widgets/          # All widget components
│   │   ├── hooks/useWebSocket.js
│   │   └── context/ThemeContext.jsx
│   └── vite.config.js
├── deploy/
│   ├── glanceos-backend.service
│   └── kiosk.sh
├── setup.sh
└── .gitignore
```

## License

MIT