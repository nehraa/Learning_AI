#!/bin/bash
# RFAI Setup Script
# Initializes database and prepares the system

set -e  # Exit on error

echo "================================================"
echo "RFAI - Routine Focus AI Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Initialize database
echo "Initializing database..."
python3 database/init_db.py
if [ $? -eq 0 ]; then
    echo "✅ Database initialized"
else
    echo "❌ Database initialization failed"
    exit 1
fi
echo ""

# Create logs directory
mkdir -p ~/.rfai/logs
echo "✅ Logs directory created"
echo ""

# Platform-specific setup
OS="$(uname -s)"
case "${OS}" in
    Linux*)
        echo "Platform: Linux"
        echo ""
        echo "${YELLOW}Optional: Install xdotool for better window tracking:${NC}"
        echo "  sudo apt-get install xdotool"
        echo ""
        ;;
    Darwin*)
        echo "Platform: macOS"
        echo ""
        echo "${YELLOW}Optional: Install macOS-specific packages:${NC}"
        echo "  pip3 install pyobjc-framework-Cocoa pyobjc-framework-Quartz"
        echo ""
        ;;
    CYGWIN*|MINGW*|MSYS*)
        echo "Platform: Windows"
        echo ""
        echo "${YELLOW}Optional: Install Windows-specific packages:${NC}"
        echo "  pip3 install pywin32"
        echo ""
        ;;
    *)
        echo "Platform: Unknown"
        ;;
esac

# Print success message
echo "================================================"
echo "${GREEN}✅ RFAI Setup Complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. (Optional) Set ANTHROPIC_API_KEY for AI plan generation:"
echo "     export ANTHROPIC_API_KEY='your-key-here'"
echo ""
echo "  2. Start the server:"
echo "     python3 rfai_server.py"
echo ""
echo "  3. Open dashboard:"
echo "     http://localhost:5000"
echo ""
echo "For help, see: RFAI_GUIDE.md"
echo "================================================"
