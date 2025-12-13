# DC Projects - Portable Docker Setup (Any OS)

## 🎯 What is This?

A fully self-contained Docker image that runs on **Windows, Mac, or Linux** with automatic domain resolution inside containers.

**No host file editing needed!**

---

## 🚀 Quick Start (Any OS)

### Step 1: Make sure Docker is running

```bash
# Start Docker Desktop (if not already running)
# On Mac: Open Docker.app
# On Windows: Open Docker Desktop
# On Linux: Docker daemon should be running
```

### Step 2: Navigate to project

```bash
cd /path/to/DC_Projects_Final
```

### Step 3: Start production

```bash
make prod
```

### Step 4: Access application

**Open in browser:**

```
http://localhost
```

Or:

```
http://127.0.0.1
```

Or (if your DNS supports it):

```
http://dcproject.com
```

### Step 5: Login

```
Username: admin
Password: admin
```

---

## 🌐 How Domain Works (No Host File Needed!)

### The Magic

Instead of editing your machine's `/etc/hosts` file, we use Docker's `extra_hosts` feature:

```yaml
extra_hosts:
  - "dcproject.com:127.0.0.1"
  - "www.dcproject.com:127.0.0.1"
```

This means:
- Inside Docker containers, `dcproject.com` always resolves to `127.0.0.1`
- Works the same way on Windows, Mac, Linux
- No host file editing required
- Portable across all machines

---

## 📊 Network Architecture

```
Your Machine
    ↓
Docker Network (internal)
    ↓
Container knows dcproject.com = 127.0.0.1
    ↓
Nginx (port 80)
    ↓
Flask App (port 8000)
```

---

## 🛠️ Available Commands

### Production (Port 80)

```bash
make prod              # Start production
make logs-prod         # View logs
make stop-prod         # Stop production
make shell-prod        # Open container shell
make restart-prod      # Restart
make build-prod        # Rebuild image
```

### Development (Port 5000)

```bash
make dev               # Start development
make logs-dev          # View logs
make stop-dev          # Stop development
make shell-dev         # Open container shell
```

### Maintenance

```bash
make clean             # Remove everything
make help              # Show all commands
```

---

## 🔗 Access URLs

### Development
```
http://localhost:5000
```

### Production
```
http://localhost              (via Nginx)
http://127.0.0.1              (via Nginx)
http://dcproject.com          (works inside Docker)
```

### API
```
http://localhost/api/projects
http://localhost/api/shots
http://localhost/_health
```

---

## ✅ What's Automatic

✅ **Database initialization** - Creates tables and default admin user on first run
✅ **Domain resolution** - dcproject.com works inside containers without host file editing
✅ **Port mapping** - Port 80 (Nginx) → 8000 (Flask)
✅ **Persistent storage** - Data saved in `./data` folder
✅ **Cross-platform** - Same setup works Windows, Mac, Linux

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | Production setup with extra_hosts |
| `docker-compose.dev.yml` | Development setup |
| `Dockerfile` | Multi-stage build with DB init |
| `nginx.prod.conf` | Reverse proxy config |
| `init-db.sh` | Database initialization script |
| `app.py` | Flask application |

---

## 🔧 First Run

On first run, the image will:

1. ✅ Build multi-stage Docker image
2. ✅ Initialize SQLite database
3. ✅ Create default admin user (admin/admin)
4. ✅ Start Nginx reverse proxy
5. ✅ Start Flask application
6. ✅ Ready for login

---

## 🐛 Troubleshooting

### Can't access http://localhost

**Fix:** Make sure Docker is running

```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# View logs
make logs-prod
```

### Database error on login

**Fix:** Database initializes automatically, but if needed:

```bash
# Reinitialize database
make stop-prod
rm -rf data
make prod
```

### Port 80 already in use

**Fix:** Use different port by editing docker-compose.prod.yml:

```yaml
ports:
  - "8080:80"  # Use 8080 instead
```

Then access: `http://localhost:8080`

---

## 🌍 Run on Any Machine

The image is completely self-contained:

1. **Copy entire project folder** to any computer
2. **Install Docker** on that computer
3. **Run**: `make prod`
4. **Access**: `http://localhost`

That's it! No configuration needed!

---

## 💾 Persistent Data

All data is stored in the `./data` folder on your machine:

```
./data/
└── dc_projects.db    (SQLite database)
```

This folder is **volume-mounted**, so:
- ✅ Data persists after container stops
- ✅ Can backup by copying `./data` folder
- ✅ Shared across container restarts

---

## 🔒 Security Notes

- ✅ Default admin/admin changes on first login
- ⚠️ Use strong DC_SECRET_KEY in .env.prod for production
- ✅ SSL/HTTPS ready (enable in nginx.prod.conf)
- ✅ All services contained in Docker network

---

## 📝 Environment Variables

Set in `.env.prod` for production:

```bash
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=False
DC_SECRET_KEY=your_secure_key_here
```

For development (`.env.dev`):

```bash
ENVIRONMENT=development
DEBUG=True
```

---

## 🎉 You're Ready!

Run this now:

```bash
make prod
```

Then open: **http://localhost**

Enjoy! 🚀
