#!/usr/bin/env bash
set -e

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
  echo "    → Edit backend/.env to add your API keys"
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
