#!/bin/bash
# DobotHub (Client) - Setup dependencies
set -e

echo "🤖 Installing DobotHub dependencies..."

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
    echo "⚠️  requirements.txt not found, skipping pip install"
fi

echo ""
echo "✅ DobotHub setup complete!"
echo ""
echo "To activate virtual environment manually:"
echo "  source venv/bin/activate"
echo ""
echo "To start DobotHub:"
echo "  ./start.sh"
