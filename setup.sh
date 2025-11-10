#!/bin/bash

echo "======================================================================"
echo "  ENHANCED LEARNING CURATION SYSTEM - SETUP"
echo "======================================================================"
echo ""

# Check Python version (show what python3 reports)
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if missing
VENV="./venv"
if [ -d "$VENV" ]; then
	echo "✓ Virtual environment already exists at $VENV - skipping creation"
else
	echo ""
	echo "Creating virtual environment..."
	python3 -m venv venv
fi

# Activate virtual environment (if possible) or use its python/pip directly
if [ -f "$VENV/bin/activate" ]; then
	echo "Activating virtual environment..."
	# shellcheck disable=SC1091
	source "$VENV/bin/activate"
	PIP_CMD="$VENV/bin/pip"
	PY_CMD="$VENV/bin/python"
else
	echo "venv activation script not found; will use $VENV/bin/python and pip if available"
	PIP_CMD="$VENV/bin/pip"
	PY_CMD="$VENV/bin/python"
fi

echo ""
echo "Installing dependencies (this may take a few minutes)..."
$PY_CMD -m pip install --upgrade pip
$PIP_CMD install -r requirements.txt

echo ""
echo "======================================================================"
echo "  SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "To start the system:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Run server:          ./run.sh or python app.py (the app will prefer ./venv if present)"
echo "  3. Open browser:        http://localhost:5000"
echo ""
echo "======================================================================"
