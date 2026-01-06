#!/bin/bash
# DC Projects - Simple Startup Script

echo "=================================="
echo "DC Projects - Starting Application"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo ""
    echo "Please create .env file:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your configuration"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
echo "✓ Checking dependencies..."
python3 -c "import flask, flask_sqlalchemy, pymysql" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Required packages not installed"
    echo ""
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

echo "✓ All checks passed!"
echo ""
echo "Starting DC Projects..."
echo "Application will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the application"
echo "=================================="
echo ""

python3 app.py
