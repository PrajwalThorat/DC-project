# DC Projects - Getting Started (Clone to Running in 5 Minutes)

## 📋 Prerequisites

Before you start, make sure you have:

1. **Docker** installed and running
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Available for Windows, Mac, Linux
   - Once installed, start the Docker application

2. **Git** installed
   - [Download Git](https://git-scm.com/downloads)
   - Or use GitHub Desktop

3. **Basic terminal/command prompt knowledge**
   - Windows: PowerShell or Command Prompt
   - Mac/Linux: Terminal

---

## 🚀 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
# Clone the repo
git clone <repository-url> DC_Projects_Final

# Navigate into the project
cd DC_Projects_Final
```

**Expected output:**
```
Cloning into 'DC_Projects_Final'...
...
```

---

### Step 2: Verify Docker is Running

```bash
# Check Docker version
docker --version

# Expected output:
# Docker version 20.10.x or higher
```

**If Docker is not running:**
- Windows: Open Docker Desktop application
- Mac: Open Docker.app from Applications
- Linux: Start Docker service

Wait 30 seconds for Docker to fully start.

---

### Step 3: Start Production Environment

```bash
# Navigate to project folder (if not already there)
cd DC_Projects_Final

# Start production with Docker
make prod
```

**Expected output:**
```
Starting DC Projects in PRODUCTION mode...
⚠️  Make sure to set DC_SECRET_KEY in .env.prod
docker-compose -f docker-compose.prod.yml up -d
[+] Running 3/3
 ✔ Network dc_projects_final_dc-prod-network  Created
 ✔ Container dc-projects-prod                 Started
 ✔ Container dc-projects-nginx-prod           Started
✓ Production started on http://localhost:80
✓ Behind Nginx reverse proxy
```

**Wait 10-15 seconds for database to initialize and app to start.**

---

### Step 4: Verify Application is Running

```bash
# Check health status
curl http://localhost/_health

# Expected output:
# {"ok":true}
```

Or check container status:

```bash
docker-compose -f docker-compose.prod.yml ps

# Expected output shows 2 containers RUNNING
```

---

### Step 5: Open in Browser

Open your web browser and navigate to:

```
http://localhost
```

You should see the DC Projects login page.

---

### Step 6: Login

Enter credentials:

```
Username: admin
Password: admin
```

Click "Login"

You should now see the main dashboard!

---

## ✅ You're Done!

Your DC Projects application is now running in Docker! 🎉

---

## 📌 Common URLs

| Purpose | URL |
|---------|-----|
| **Main Application** | http://localhost |
| **API - Projects** | http://localhost/api/projects |
| **API - Shots** | http://localhost/api/shots |
| **Health Check** | http://localhost/_health |
| **Login Page** | http://localhost/login |

---

## 🛠️ Useful Commands After Setup

### View Logs (if something goes wrong)

```bash
# View real-time logs
make logs-prod

# Exit logs: Ctrl+C
```

### Stop the Application

```bash
make stop-prod
```

### Restart the Application

```bash
make restart-prod
```

### Development Mode (Optional)

If you want to develop and make code changes:

```bash
# Start development mode (with auto-reload)
make dev

# Opens on port 5000
# http://localhost:5000
```

### Check Running Containers

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Open Container Shell (Advanced)

```bash
make shell-prod

# You can now run Python commands
# Type: exit
```

---

## 📂 Project Structure

```
DC_Projects_Final/
├── app.py                      # Main Flask application
├── Dockerfile                  # Docker image definition
├── docker-compose.prod.yml     # Production Docker setup
├── docker-compose.dev.yml      # Development Docker setup
├── nginx.prod.conf             # Nginx configuration
├── requirements.txt            # Python dependencies
├── Makefile                    # Commands (make prod, make dev, etc.)
├── init-db.sh                  # Database initialization script
├── templates/                  # HTML templates
├── static/                     # CSS, JavaScript
├── data/                       # SQLite database (created on first run)
└── logs/                       # Application logs (created on first run)
```

---

## 🔍 What Happens on First Run?

When you run `make prod`:

1. ✅ Docker downloads Python image
2. ✅ Builds your application image
3. ✅ Creates SQLite database
4. ✅ Initializes database tables
5. ✅ Creates default admin user (admin/admin)
6. ✅ Starts Nginx reverse proxy (port 80)
7. ✅ Starts Flask application (port 8000)
8. ✅ Ready for access!

All of this happens automatically - **no manual setup needed!**

---

## 🌍 Works on Any OS

This setup works identically on:
- ✅ **Windows** (PowerShell or Command Prompt)
- ✅ **Mac** (Terminal)
- ✅ **Linux** (Terminal)

Just clone, navigate, and run `make prod`!

---

## 💾 Your Data

All your data is stored in the `./data` folder:

```
./data/
└── dc_projects.db    (SQLite database)
```

This persists between container restarts, so:
- ✅ Data doesn't disappear when you stop the app
- ✅ Can backup by copying this folder
- ✅ Can restore by putting folder back

---

## 🆘 Troubleshooting

### Docker not found

```bash
# Make sure Docker is installed and running
docker --version

# If not installed, download from:
# https://www.docker.com/products/docker-desktop
```

### Port 80 already in use

Edit `docker-compose.prod.yml`:

```yaml
ports:
  - "8080:80"  # Change 80 to 8080
```

Then access: `http://localhost:8080`

### Can't access http://localhost

```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# View logs to see errors
make logs-prod

# Restart
make stop-prod
make prod
```

### Database error on login

```bash
# Stop the app
make stop-prod

# Remove database to reset
rm -rf data

# Start again (recreates database)
make prod
```

### Still having issues?

View detailed logs:

```bash
make logs-prod

# Look for ERROR messages and search for solutions
```

---

## 📚 Learn More

After getting started, read these guides:

- **QUICKSTART.md** - Quick reference for commands
- **DOCKER_SETUP.md** - Detailed Docker documentation
- **PORTABLE_SETUP.md** - Portable setup across OS
- **APP_REVIEW.md** - Application features and API

---

## 🎯 Next Steps

1. ✅ **Create a Project**
   - Click "New Project"
   - Enter project name

2. ✅ **Add Shots**
   - Click "Add Shot"
   - Enter shot code (e.g., `HD_R01_SH01_V001`)
   - The "V001" version will auto-extract

3. ✅ **Upload Files**
   - Add Plate (image)
   - Add MOV (video)
   - Add EXR (image sequence)

4. ✅ **Test Features**
   - Click on a shot
   - View preview
   - Add comments
   - Test edit/delete

---

## 🔐 Security Notes

- ✅ Default credentials: admin/admin
- ⚠️ Change password after first login (in production)
- ✅ Database is SQLite (single file)
- ✅ All data stored in `./data` folder

For production deployment:
- Update `DC_SECRET_KEY` in `.env.prod`
- Enable SSL/HTTPS (see nginx.prod.conf)
- Use strong passwords

---

## ✨ Summary

```bash
# That's all you need:
git clone <repo-url>
cd DC_Projects_Final
make prod
# Open http://localhost
# Login: admin/admin
# Done! 🎉
```

---

## 📞 Need Help?

- Check logs: `make logs-prod`
- Restart app: `make restart-prod`
- View commands: `make help`
- Read docs: QUICKSTART.md, DOCKER_SETUP.md

---

**You're now ready to use DC Projects!** 🚀
