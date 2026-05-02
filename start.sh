#!/bin/bash
# DobotHub (Client) - Start server
set -e

echo "🤖 Starting DobotHub..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Run './install.sh' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Default port to 8080 if not specified
PORT=${1:-8080}

# Start the Flask server
echo "Starting Flask server on http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

python3 web_server.py "$PORT"
