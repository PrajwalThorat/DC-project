# DC Projects - Digital Content Tracker

A professional project management and shot tracking application for design studios.

**Built with:** Flask • SQLite (default) • MySQL (optional) • SQLAlchemy

---

## 🚀 Quick Start (2 Minutes)

### No Setup Required!

The app uses **SQLite by default** - it works immediately out of the box!

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run application
python3 app.py

# 3. Open browser
# http://localhost:5000

# 4. Login with default credentials
# Username: admin
# Password: admin
```

That's it! ✅

---

## ⚙️ Configuration

### Default Setup (SQLite)
Works out of the box with no configuration needed. Data stored in `dc_projects.db`

### Switch to MySQL (Optional)

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=dc_user
DB_PASSWORD=your_password
DB_NAME=dc_projects
```

Or set environment variables:
```bash
export DB_TYPE=mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=dc_user
export DB_PASSWORD=your_password
export DB_NAME=dc_projects
```

---

## ✨ Features

- 🎬 **Project Management** - Create and organize projects
- 📹 **Shot Tracking** - Track shots with status and assignments
- 👥 **User Roles** - Admin, Producer, Supervisor, Artist, Lead, IT
- 💬 **Comments** - Collaborative discussion on shots
- 📁 **File Management** - Track MOV, EXR, Nuke, and plate paths
- 🔐 **Secure Authentication** - Session-based login

---

## 📁 Project Structure

```
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env.example             # Configuration template
├── README.md                # This file
├── MYSQL_SETUP.md           # MySQL setup guide
├── ENV_VARIABLES.md         # Configuration reference
├── migrate_sqlite_to_mysql.py # Data migration
├── templates/               # HTML templates
├── static/                  # CSS & JavaScript
├── projects/                # Project folders
└── dc_projects.db           # SQLite database (auto-created)
```

---

## 🔄 Data Migration

To migrate from SQLite to MySQL:

```bash
# Set MySQL environment variables
export DB_TYPE=mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=dc_user
export DB_PASSWORD=your_password
export DB_NAME=dc_projects

# Run migration script
python migrate_sqlite_to_mysql.py
```

---

## 🚀 Production Deployment

Before deploying:

1. Create `.env` file with your settings
2. Set `ENVIRONMENT=production` in `.env`
3. Use a strong `DC_SECRET_KEY`
4. For SQLite: ensure write permissions on `dc_projects.db`
5. For MySQL: ensure database credentials are secure
6. Consider using Nginx as reverse proxy
7. Enable HTTPS/SSL

---

## 🆘 Troubleshooting

**Port 5000 Already in Use**
```bash
python3 app.py --port 5001
```

**Dependencies Missing**
```bash
pip install -r requirements.txt
```

**Database Error (SQLite)**
```bash
# Delete old database and start fresh
rm dc_projects.db
python3 app.py
```

**MySQL Connection Error**
- Verify MySQL is running
- Check credentials in `.env`
- Ensure database exists: `CREATE DATABASE dc_projects;`

---

## 📚 Documentation

- `MYSQL_SETUP.md` - Detailed MySQL setup with Docker examples
- `ENV_VARIABLES.md` - All configuration variables
- `.env.example` - Configuration template

---

## 📊 Tech Stack

| Component | Purpose |
|-----------|---------|
| **Flask** | Web framework |
| **SQLAlchemy** | ORM |
| **SQLite** | Default database |
| **MySQL** | Optional production database |
| **HTML/CSS/JS** | Frontend |

---

**Status:** Production Ready ✅
**Version:** 2.0.0
**Last Updated:** January 5, 2025
