#!/usr/bin/env bash

# ROUTINE FOCUS AI - QUICK START SCRIPT
# This script starts the complete RFAI system with all daemons

set -e

PROJECT_DIR="/Users/abhinavnehra/Downloads/Learning_AI"
PORT="${1:-5001}"

echo "════════════════════════════════════════════════════════"
echo "  🎯 ROUTINE FOCUS AI (RFAI)"
echo "════════════════════════════════════════════════════════"
echo

# Check if venv exists
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "❌ Python virtual environment not found at $PROJECT_DIR/.venv"
    echo "Please run: python3 -m venv $PROJECT_DIR/.venv"
    exit 1
fi

# Activate venv
echo "📦 Activating Python environment..."
source "$PROJECT_DIR/.venv/bin/activate"

# Check dependencies
echo "🔍 Checking dependencies..."
MISSING=()

for pkg in opencv pyaudio pynput psutil; do
    if ! python3 -c "import ${pkg}" 2>/dev/null; then
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "⚠️  Missing packages: ${MISSING[*]}"
    echo "Installing..."
    pip install opencv-python pyaudio pynput psutil pyobjc-framework-Cocoa -q
    echo "✅ Dependencies installed"
fi

# Kill any existing server on this port
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "🛑 Stopping existing server on port $PORT..."
    pkill -f "rfai_server.*--port $PORT" 2>/dev/null || true
    sleep 1
fi

echo
echo "════════════════════════════════════════════════════════"
echo "  🚀 STARTING RFAI SERVER"
echo "════════════════════════════════════════════════════════"
echo
echo "  📊 Dashboard: http://localhost:$PORT"
echo "  🔌 API: http://localhost:$PORT/api"
echo "  💚 Health: http://localhost:$PORT/health"
echo
echo "  Daemons:"
echo "    ✓ TimeTrackerDaemon (active app monitoring)"
echo "    ✓ FocusDetectorDaemon (keyboard/mouse signals)"
echo "    ✓ AttentionMonitorDaemon (camera/mic/system signals)"
echo
echo "  Data Collection:"
echo "    ✓ Real-time attention scoring (every 5s)"
echo "    ✓ Session tracking & persistence"
echo "    ✓ Training data export"
echo
echo "  Schedule:"
echo "    09:00-12:00 - 🔬 Science Learning (3h)"
echo "    13:00-14:00 - 🧠 Self-Help (1h)"
echo "    18:00-19:30 - 🎬 Movies (1.5h)"
echo
echo "════════════════════════════════════════════════════════"
echo "Press Ctrl+C to stop the server"
echo "════════════════════════════════════════════════════════"
echo

# Start the server
cd "$PROJECT_DIR"
python3 rfai_server.py --port $PORT
