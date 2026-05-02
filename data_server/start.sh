#!/bin/bash
# data_server - Start server
set -e

echo "☁️  Starting data_server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Run './install.sh' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Copy .env.example to .env and configure your database:"
    echo "   cp .env.example .env"
    exit 1
fi

# Get config from .env
source .env

# Check required environment variables
if [ -z "$MARIADB_HOST" ] || [ -z "$MARIADB_USER" ] || [ -z "$MARIADB_DATABASE" ]; then
    echo "❌ Missing required environment variables in .env"
    echo "   Please set: MARIADB_HOST, MARIADB_USER, MARIADB_DATABASE"
    exit 1
fi

# Start the Flask server
PORT=${PORT:-5001}
HOST=${HOST:-0.0.0.0}

echo "Starting Flask server on http://$HOST:$PORT"
echo "Database: $MARIADB_USER@$MARIADB_HOST:$MARIADB_DATABASE"
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
