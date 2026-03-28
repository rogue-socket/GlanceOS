#!/usr/bin/env bash
set -e

upsert_env_var() {
  local file="$1"
  local key="$2"
  local value="$3"
  local tmp_file
  tmp_file="$(mktemp)"

  awk -v key="$key" -v value="$value" '
    BEGIN { found = 0 }
    $0 ~ ("^" key "=") {
      print key "=" value
      found = 1
      next
    }
    { print }
    END {
      if (!found) {
        print key "=" value
      }
    }
  ' "$file" > "$tmp_file"

  mv "$tmp_file" "$file"
}

read_env_value() {
  local file="$1"
  local key="$2"
  if [ ! -f "$file" ]; then
    echo ""
    return
  fi
  local line
  line="$(grep -E "^${key}=" "$file" | head -n 1 || true)"
  echo "${line#*=}"
}

prompt_key() {
  local env_name="$1"
  local prompt_label="$2"
  local current_value="$3"
  local input=""

  # Allow non-interactive automation via exported env vars.
  if [ -n "${!env_name:-}" ]; then
    printf '%s' "${!env_name}"
    return
  fi

  if [ ! -t 0 ]; then
    printf '%s' "$current_value"
    return
  fi

  if [ -n "$current_value" ]; then
    read -r -p "$prompt_label [press Enter to keep existing]: " input
    if [ -n "$input" ]; then
      printf '%s' "$input"
      return
    fi
    printf '%s' "$current_value"
    return
  fi

  read -r -p "$prompt_label [optional, press Enter to skip]: " input
  printf '%s' "$input"
}

echo "=== GlanceOS Setup ==="
echo ""

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
  PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
  PYTHON_CMD="python"
else
  echo "Error: Python 3 is required but not found."
  echo "Install it from https://www.python.org or via your package manager."
  exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# ── Backend ──────────────────────────────────────
echo ""
echo "[1/4] Creating Python virtual environment..."
cd backend
$PYTHON_CMD -m venv venv

# Activate (works on Linux/macOS)
source venv/bin/activate

echo "[2/4] Installing backend dependencies..."
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "[*] Creating .env from .env.example..."
  cp .env.example .env
fi

echo "[*] Configure API keys (optional but recommended)..."
CURRENT_WEATHER_KEY="$(read_env_value .env WEATHER_API_KEY)"
CURRENT_GITHUB_TOKEN="$(read_env_value .env GITHUB_TOKEN)"
CURRENT_WEATHER_CITY="$(read_env_value .env WEATHER_CITY)"
CURRENT_GITHUB_USERNAME="$(read_env_value .env GITHUB_USERNAME)"
CURRENT_TODOIST_API_TOKEN="$(read_env_value .env TODOIST_API_TOKEN)"
CURRENT_TODOIST_PROJECT_ID="$(read_env_value .env TODOIST_PROJECT_ID)"
CURRENT_GOOGLE_CALENDAR_ICS_URL="$(read_env_value .env GOOGLE_CALENDAR_ICS_URL)"
CURRENT_GOOGLE_CALENDAR_ID="$(read_env_value .env GOOGLE_CALENDAR_ID)"
CURRENT_GOOGLE_CALENDAR_API_KEY="$(read_env_value .env GOOGLE_CALENDAR_API_KEY)"
CURRENT_NEWS_LLM_API_KEY="$(read_env_value .env NEWS_LLM_API_KEY)"

if [ -z "$CURRENT_WEATHER_CITY" ]; then
  CURRENT_WEATHER_CITY="Hyderabad,IN"
fi

if [ -z "$CURRENT_GITHUB_USERNAME" ]; then
  CURRENT_GITHUB_USERNAME="octocat"
fi

WEATHER_KEY="$(prompt_key WEATHER_API_KEY "OpenWeatherMap API key" "$CURRENT_WEATHER_KEY")"
GITHUB_TOKEN_VALUE="$(prompt_key GITHUB_TOKEN "GitHub personal access token" "$CURRENT_GITHUB_TOKEN")"
WEATHER_CITY_VALUE="$(prompt_key WEATHER_CITY "Weather city (e.g. Hyderabad,IN)" "$CURRENT_WEATHER_CITY")"
GITHUB_USERNAME_VALUE="$(prompt_key GITHUB_USERNAME "GitHub username for activity widget" "$CURRENT_GITHUB_USERNAME")"
TODOIST_API_TOKEN_VALUE="$(prompt_key TODOIST_API_TOKEN "Todoist API token" "$CURRENT_TODOIST_API_TOKEN")"
TODOIST_PROJECT_ID_VALUE="$(prompt_key TODOIST_PROJECT_ID "Todoist project ID (optional, for filtering)" "$CURRENT_TODOIST_PROJECT_ID")"
GOOGLE_CALENDAR_ICS_URL_VALUE="$(prompt_key GOOGLE_CALENDAR_ICS_URL "Google Calendar ICS URL (recommended for private calendars)" "$CURRENT_GOOGLE_CALENDAR_ICS_URL")"
GOOGLE_CALENDAR_ID_VALUE="$(prompt_key GOOGLE_CALENDAR_ID "Google Calendar ID (for API mode)" "$CURRENT_GOOGLE_CALENDAR_ID")"
GOOGLE_CALENDAR_API_KEY_VALUE="$(prompt_key GOOGLE_CALENDAR_API_KEY "Google Calendar API key (for API mode)" "$CURRENT_GOOGLE_CALENDAR_API_KEY")"
NEWS_LLM_API_KEY_VALUE="$(prompt_key NEWS_LLM_API_KEY "Gemini API key for News crux summaries (optional)" "$CURRENT_NEWS_LLM_API_KEY")"

upsert_env_var .env WEATHER_API_KEY "$WEATHER_KEY"
upsert_env_var .env GITHUB_TOKEN "$GITHUB_TOKEN_VALUE"
upsert_env_var .env WEATHER_CITY "$WEATHER_CITY_VALUE"
upsert_env_var .env GITHUB_USERNAME "$GITHUB_USERNAME_VALUE"
upsert_env_var .env TODOIST_API_TOKEN "$TODOIST_API_TOKEN_VALUE"
upsert_env_var .env TODOIST_PROJECT_ID "$TODOIST_PROJECT_ID_VALUE"
upsert_env_var .env GOOGLE_CALENDAR_ICS_URL "$GOOGLE_CALENDAR_ICS_URL_VALUE"
upsert_env_var .env GOOGLE_CALENDAR_ID "$GOOGLE_CALENDAR_ID_VALUE"
upsert_env_var .env GOOGLE_CALENDAR_API_KEY "$GOOGLE_CALENDAR_API_KEY_VALUE"
upsert_env_var .env NEWS_LLM_API_KEY "$NEWS_LLM_API_KEY_VALUE"

if [ -z "$WEATHER_KEY" ] || [ -z "$GITHUB_TOKEN_VALUE" ]; then
  echo "[*] One or more API keys are empty. Related widgets will show offline/unavailable states."
fi

cd ..

# ── Frontend ─────────────────────────────────────
if ! command -v npm &> /dev/null; then
  echo "Error: npm is required but not found."
  echo "Install Node.js from https://nodejs.org"
  exit 1
fi

echo "[3/4] Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "[4/4] Done!"
echo ""
echo "To start GlanceOS:"
echo "  Terminal 1:  cd backend && source venv/bin/activate && python run.py"
echo "  Terminal 2:  cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:5173"
echo ""
echo "Tip: set WEATHER_API_KEY, GITHUB_TOKEN, TODOIST_API_TOKEN, GOOGLE_CALENDAR_ICS_URL (or GOOGLE_CALENDAR_ID + GOOGLE_CALENDAR_API_KEY), and NEWS_LLM_API_KEY before running setup for non-interactive installs."
