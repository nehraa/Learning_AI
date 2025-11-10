#!/usr/bin/env bash
set -e

VENV="./venv"

if [ -d "$VENV" ]; then
	if [ -f "$VENV/bin/activate" ]; then
		# shellcheck disable=SC1091
		source "$VENV/bin/activate"
		echo "Activated virtualenv at $VENV"
		python app.py
		exit $?
	elif [ -x "$VENV/bin/python" ]; then
		echo "Using $VENV/bin/python to run app.py"
		exec "$VENV/bin/python" app.py
	fi
fi

echo "Virtual environment not found at ./venv. Please run ./setup.sh to create it, or activate your environment manually."
exit 1
