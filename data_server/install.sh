#!/bin/bash
# data_server - Setup dependencies
set -e

echo "☁️  Installing data_server dependencies..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python packages from requirements.txt..."
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found in data_server directory"
    exit 1
fi

echo ""
echo "✅ data_server setup complete!"
echo ""
echo "Before starting the server:"
echo "  1. Copy .env.example to .env"
echo "  2. Update database credentials in .env"
echo "  3. Initialize database: mysql -u <user> -p <db> < migrations/001_initial_schema.sql"
echo "  4. Create a test user: python3 scripts/create_user.py --username admin --password secret"
echo ""
echo "To activate virtual environment manually:"
echo "  source venv/bin/activate"
echo ""
echo "To start data_server:"
echo "  ./start.sh"
