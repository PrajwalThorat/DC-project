# DC Projects - MySQL Setup Guide

This application now uses **MySQL exclusively**. All SQLite code has been removed.

## Prerequisites

1. **MySQL Server** running locally on `localhost:3306`
2. **Python 3.8+** with pip

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment (.env)

Create or edit `.env` file in the project root:

```env
# Application
DC_SECRET_KEY=your-secure-secret-key-here
ENVIRONMENT=development
DEBUG=True

# Database (MySQL only)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=dc_projects

# Project paths
DC_PROJECTS_ROOT=/path/to/projects
```

### 3. Initialize Database

```bash
python3 create_mysql_db.py
```

This script will:
- ✅ Create the MySQL database if it doesn't exist
- ✅ Create all required tables
- ✅ Add unique constraint on (project_id, code)
- ✅ Ensure reel column exists in shot table
- ✅ Create default admin user (username: `admin`, password: `admin`)

### 4. Run the Application

```bash
python3 app.py
```

The app will start on `http://localhost:5000` (development) or port 8000 (production).

## Database Features

### Unique Shot Codes

Each shot code must be unique per project. Attempting to create or import duplicate shot codes will be rejected:
- **API Response**: 400 Bad Request with error message
- **CSV Import**: Duplicates are skipped with error logged

### Reel Column

Shots now support a dedicated `reel` column for better tracking:
- Stored separately in the database (not parsed from code)
- Can be set during shot creation or CSV import
- Used for grouping and filtering in the UI

## Database Structure

### Key Tables

- **user**: Users with roles (admin, producer, supervisor, artist)
- **project**: Projects with folder paths and metadata
- **shot**: Shots with code (UNIQUE per project), reel, status, assignments
- **comment**: Comments on shots with author metadata

### Unique Constraints

- `(project_id, code)` on `shot` table - ensures shot codes are unique per project
- `username` on `user` table - ensures usernames are globally unique

## Troubleshooting

### Error: "Can't connect to MySQL server"

- Verify MySQL is running: `mysql -u root -p`
- Check credentials in `.env` file
- Ensure port 3306 is accessible

### Error: "Duplicate entry" during database setup

If you have duplicate shot codes in existing data:
```sql
SELECT project_id, code, COUNT(*) FROM shot 
GROUP BY project_id, code 
HAVING COUNT(*) > 1;
```

Delete duplicates manually or update codes to be unique.

### CSV Import Issues

- Ensure CSV has `code` column (required)
- Duplicate codes within same project will be skipped
- Codes already in the project database will be skipped

## API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project

### Shots
- `GET /api/projects/<id>/shots` - List shots (supports filtering)
- `POST /api/projects/<id>/shots` - Create shot
- `PUT /api/shots/<id>` - Update shot
- `DELETE /api/shots/<id>` - Delete shot
- `POST /api/shots/bulk_delete` - Delete multiple shots

### CSV Operations
- `POST /api/projects/<id>/import_preview` - Preview CSV before import
- `POST /api/projects/<id>/import_csv` - Import shots from CSV
- `GET /api/projects/<id>/export_csv` - Export shots to CSV

## Production Deployment

For production:

1. Set environment variables:
   ```env
   ENVIRONMENT=production
   DEBUG=False
   PROD_PORT=8000
   ```

2. Use a production WSGI server (Gunicorn):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. Set up MySQL with proper backups and replication

## Support

For issues or questions, check the logs or contact the development team.
