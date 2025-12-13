#!/bin/bash
# Database initialization script for Docker

cd /app

# Wait for database to be accessible
echo "Initializing database..."

# Run Python to initialize database
python3 << 'PYEOF'
import os
import sys
from pathlib import Path

# Add app path
sys.path.insert(0, '/app')

# Import Flask app
from app import app, db, ensure_db

# Initialize database with app context
with app.app_context():
    try:
        ensure_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("✅ Database ready")
PYEOF

exit $?
