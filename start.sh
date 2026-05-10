#!/bin/bash
# RSA Question Generator — Mac/Linux one-click launcher
# First time: chmod +x start.sh && ./start.sh
# Every time after: ./start.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/rsa_app"
SECRETS_DIR="$APP_DIR/.streamlit"
SECRETS_FILE="$SECRETS_DIR/secrets.toml"
ENV_FILE="$SCRIPT_DIR/.env"
API_KEY=""
if [ -f "$ENV_FILE" ]; then
    API_KEY=$(grep "^ANTHROPIC_API_KEY=" "$ENV_FILE" | cut -d= -f2-)
fi

echo ""
echo "======================================"
echo "  RSA Question Generator — Launcher  "
echo "======================================"
echo ""

# ── Step 1: Check Python ────────────────────────────────────────────────────
echo "[1/4] Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo "      ERROR: Python3 not found."
    echo "      Install it: brew install python"
    exit 1
fi
echo "      OK: $(python3 --version)"

# ── Step 2: Install requirements ───────────────────────────────────────────
echo "[2/4] Installing requirements..."
pip3 install -r "$APP_DIR/requirements.txt" -q
echo "      OK"

# ── Step 3: API key setup ───────────────────────────────────────────────────
echo "[3/4] Checking API key..."
if [ -z "$API_KEY" ]; then
    echo ""
    echo "      First time setup — enter the Anthropic API key:"
    read -p "      API Key: " API_KEY
    echo "ANTHROPIC_API_KEY=$API_KEY" > "$ENV_FILE"
    echo "      Saved to .env (won't ask again)"
else
    echo "      OK: key loaded from .env"
fi
mkdir -p "$SECRETS_DIR"
echo "ANTHROPIC_API_KEY = \"$API_KEY\"" > "$SECRETS_FILE"

# ── Step 4: Install cloudflared if missing ──────────────────────────────────
echo "[4/4] Checking cloudflared..."
if ! command -v cloudflared &>/dev/null; then
    echo "      Not found. Installing via Homebrew..."
    if ! command -v brew &>/dev/null; then
        echo "      Homebrew not found. Install from https://brew.sh then re-run."
        exit 1
    fi
    brew install cloudflared -q
fi
echo "      OK: $(cloudflared --version 2>&1 | head -1)"

# ── Kill any existing instances ─────────────────────────────────────────────
pkill -f "streamlit run" 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 1

# ── Start Streamlit ─────────────────────────────────────────────────────────
echo ""
echo "Starting Streamlit..."
cd "$APP_DIR"
streamlit run app.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!
sleep 4

# ── Start Cloudflare tunnel ─────────────────────────────────────────────────
echo "Starting Cloudflare tunnel..."
CF_LOG="/tmp/cf_tunnel.log"
cloudflared tunnel --url http://localhost:8501 --logfile "$CF_LOG" &
CF_PID=$!

# Wait for tunnel URL
echo "Waiting for public URL..."
URL=""
for i in $(seq 1 30); do
    sleep 2
    if [ -f "$CF_LOG" ]; then
        URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$CF_LOG" | head -1)
        [ -n "$URL" ] && break
    fi
done

echo ""
echo "======================================"
echo "  APP IS LIVE!"
echo ""
if [ -n "$URL" ]; then
    echo "  Share this link:"
    echo "  $URL"
    open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null
else
    echo "  Local: http://localhost:8501"
    open "http://localhost:8501" 2>/dev/null
fi
echo ""
echo "  Keep this terminal open while using the app."
echo "======================================"
echo ""
echo "Press Ctrl+C to stop everything."

# Wait and cleanup on exit
trap "kill $STREAMLIT_PID $CF_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
