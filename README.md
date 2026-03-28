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

This creates a Python venv, installs all dependencies, creates `backend/.env`, and prompts for API keys plus Google Calendar connection details during setup.

For non-interactive installs, export keys before running setup:

```bash
export WEATHER_API_KEY="your_openweathermap_key"
export GITHUB_TOKEN="your_github_token"
export TODOIST_API_TOKEN="your_todoist_token"
export GOOGLE_CALENDAR_ICS_URL="your_google_calendar_ics_url"
export NEWS_LLM_API_KEY="your_gemini_key"
./setup.sh
```

When you run the backend with `python run.py`, GlanceOS checks missing service credentials and prompts interactively (one-time) for:

1. `WEATHER_API_KEY`
2. `GITHUB_TOKEN`
3. `TODOIST_API_TOKEN`
4. `NEWS_LLM_API_KEY` (also auto-detected from `GEMINI_API_KEY` / `GOOGLE_API_KEY`)
5. Google Calendar config: `GOOGLE_CALENDAR_ICS_URL` or `GOOGLE_CALENDAR_ID` + `GOOGLE_CALENDAR_API_KEY`

Entered values are persisted to `backend/.env`.

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
| `TODOIST_API_TOKEN` | Todoist API token                  | No |
| `TODOIST_PROJECT_ID` | Todoist project ID filter         | No |
| `GOOGLE_CALENDAR_ICS_URL` | Google Calendar ICS URL (private/public calendars) | No |
| `GOOGLE_CALENDAR_ID` | Google Calendar ID for API mode | No |
| `GOOGLE_CALENDAR_API_KEY` | Google Calendar API key for API mode | No |
| `NEWS_LLM_API_KEY` | API key for LLM-based News crux summaries | No |
| `NEWS_USE_LLM` | Enable/disable News LLM summaries (`true/false`) | No |
| `NEWS_LLM_PROVIDER` | LLM provider (`gemini` default) | No |
| `NEWS_LLM_BASE_URL` | LLM base URL (default Gemini API) | No |
| `NEWS_LLM_MODEL` | LLM model for News summaries (default `gemini-2.0-flash-lite`) | No |
| `WEATHER_CITY`    | Default weather city (e.g. Hyderabad,IN) | No |
| `GITHUB_USERNAME` | GitHub username for activity widget  | No       |
| `HOST`            | Backend bind address (default `0.0.0.0`) | No   |
| `PORT`            | Backend port (default `8000`)        | No       |
| `LOG_LEVEL`       | Backend log verbosity (default `WARNING`) | No |

*Widgets show offline/unavailable states when required live data cannot be fetched.

Get your keys:
- Weather: https://openweathermap.org/api (free tier)
- GitHub: https://github.com/settings/tokens (no scopes needed for public data)
- Todoist: https://app.todoist.com/app/settings/integrations/developer
- News LLM (optional): Gemini API key from Google AI Studio
- Google Calendar:
        - Recommended: Google Calendar Settings -> Integrate calendar -> Secret address in iCal format -> set `GOOGLE_CALENDAR_ICS_URL`
        - Alternative: enable Google Calendar API and set `GOOGLE_CALENDAR_ID` + `GOOGLE_CALENDAR_API_KEY`

## Widgets

| Widget     | Data Source           | Update Interval |
|------------|-----------------------|-----------------|
| Clock      | Client-side           | 1s              |
| Lofi Art   | ASCII scenes (local)  | 12s cycle       |
| Weather    | OpenWeatherMap API    | 10 min          |
| System     | psutil (CPU/RAM/Disk) | 3s              |
| Cricket    | ESPN / CricAPI        | 2 min           |
| News       | Google News RSS + optional LLM crux | 15 min |
| Trending   | GitHub Trending       | 30 min          |
| GitHub     | GitHub Events API     | 5 min           |
| Calendar   | Google Calendar (ICS/API) | 5 min       |
| Todo       | Todoist API           | 2 min           |

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