#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENV="$REPO_ROOT/venv"

ensure_venv() {
	if [ -x "$VENV/bin/python" ]; then
		return 0
	fi

	echo "Virtual environment not found. Running setup..."
	"$REPO_ROOT/setup.sh"
}

pick_port() {
	local start_port="$1"
	local port="$start_port"
	local max_tries=10
	local tries=0

	while [ $tries -lt $max_tries ]; do
		if command -v lsof >/dev/null 2>&1; then
			if ! lsof -n -P -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
				echo "$port"
				return 0
			fi
		else
			# Fallback: assume port is free if lsof is unavailable
			echo "$port"
			return 0
		fi

		port=$((port + 1))
		tries=$((tries + 1))
	done

	# If everything is busy, just return the start port and let Flask error
	echo "$start_port"
}

ensure_venv

# Activate venv
if [ -f "$VENV/bin/activate" ]; then
	# shellcheck disable=SC1091
	source "$VENV/bin/activate"
fi

echo "Ensuring RFAI database is initialized..."
python database/init_db.py >/dev/null 2>&1 || true

HOST="${HOST:-0.0.0.0}"
BASE_PORT="${PORT:-5000}"
PORT_CHOSEN="$(pick_port "$BASE_PORT")"

NO_DAEMONS_FLAG=""
if [ "${NO_DAEMONS:-0}" = "1" ]; then
	NO_DAEMONS_FLAG="--no-daemons"
fi

echo "Starting RFAI on http://$HOST:$PORT_CHOSEN"
exec python rfai_server.py --host "$HOST" --port "$PORT_CHOSEN" $NO_DAEMONS_FLAG
