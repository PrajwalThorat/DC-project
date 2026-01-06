#!/usr/bin/env python3
"""
Create MySQL database with all required tables, constraints, and columns.
This is the single entry point for database initialization.

Handles:
 - Database creation
 - Table creation via SQLAlchemy
 - Unique constraint on (project_id, code)
 - Reel column addition

Usage: python3 create_mysql_db.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'dc_projects')

print(f"🔧 Setting up MySQL database: {DB_NAME} at {DB_HOST}:{DB_PORT}")
print(f"👤 User: {DB_USER}")

# Step 1: Connect to MySQL and create database
import pymysql

try:
    print("\n1️⃣  Connecting to MySQL server...")
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    print(f"   ✓ Connected to {DB_HOST}:{DB_PORT}")
    
    # Create database if not exists
    print(f"\n2️⃣  Creating database '{DB_NAME}' if not exists...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"   ✓ Database '{DB_NAME}' ready")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ✗ Error connecting to MySQL: {e}")
    sys.exit(1)

# Step 2: Import Flask app and create all tables
print(f"\n3️⃣  Creating tables via SQLAlchemy...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from app import app, db
    
    with app.app_context():
        db.create_all()
        print(f"   ✓ All tables created successfully")
        
except Exception as e:
    print(f"   ✗ Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Add unique constraint on (project_id, code)
print(f"\n4️⃣  Adding unique constraint on (project_id, code)...")
try:
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    # Check if constraint already exists
    cursor.execute("""
        SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE TABLE_NAME='shot' AND TABLE_SCHEMA=%s 
        AND CONSTRAINT_NAME='uk_shot_project_code'
    """, (DB_NAME,))
    
    if cursor.fetchone():
        print(f"   ⓘ Unique constraint already exists")
    else:
        # Add the new constraint
        print(f"   - Adding unique constraint...")
        try:
            cursor.execute("""
                ALTER TABLE shot ADD UNIQUE KEY uk_shot_project_code (project_id, code)
            """)
            conn.commit()
            print(f"   ✓ Unique constraint added successfully")
        except pymysql.err.ProgrammingError as e:
            if "Duplicate entry" in str(e):
                print(f"   ⚠ Warning: Duplicate shot codes exist in database")
                print(f"   Run this to find them:")
                print(f"   SELECT project_id, code, COUNT(*) FROM shot GROUP BY project_id, code HAVING COUNT(*) > 1;")
                conn.rollback()
            elif "Duplicate key name" in str(e):
                print(f"   ⓘ Constraint appears to exist already")
            else:
                raise
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ✗ Error adding constraint: {e}")
    sys.exit(1)

# Step 4: Ensure reel column exists
print(f"\n5️⃣  Ensuring reel column exists in shot table...")
try:
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    # Check if reel column exists
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME='shot' AND TABLE_SCHEMA=%s AND COLUMN_NAME='reel'
    """, (DB_NAME,))
    
    if cursor.fetchone():
        print(f"   ✓ Reel column already exists")
    else:
        print(f"   - Adding reel column...")
        cursor.execute("""
            ALTER TABLE shot ADD COLUMN reel VARCHAR(100) NULL AFTER code
        """)
        conn.commit()
        print(f"   ✓ Reel column added successfully")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ✗ Error adding reel column: {e}")
    sys.exit(1)

print(f"\n✅ Database setup complete!")
print(f"   Database: {DB_NAME}")
print(f"   Host: {DB_HOST}:{DB_PORT}")
print(f"   User: {DB_USER}")
print(f"\n🚀 Ready to run: python3 app.py")
