# DC Projects - Quick Reference Card

## ⚡ The 30-Second Setup

```bash
# 1. Clone repo
git clone <url> DC_Projects_Final
cd DC_Projects_Final

# 2. Start Docker
make prod

# 3. Open browser
# http://localhost

# 4. Login
# admin / admin
```

Done! ✅

---

## 🎯 Essential Commands

### Start/Stop

| Command | Purpose |
|---------|---------|
| `make prod` | Start production (port 80) |
| `make dev` | Start development (port 5000) |
| `make stop-prod` | Stop production |
| `make stop-dev` | Stop development |
| `make restart-prod` | Restart production |

### Monitoring

| Command | Purpose |
|---------|---------|
| `make logs-prod` | View production logs |
| `make logs-dev` | View development logs |
| `docker-compose -f docker-compose.prod.yml ps` | Container status |
| `curl http://localhost/_health` | Health check |

### Maintenance

| Command | Purpose |
|---------|---------|
| `make clean` | Remove all containers |
| `make build-prod` | Rebuild Docker image |
| `make shell-prod` | Open container shell |
| `make help` | Show all commands |

---

## 🌐 Access Points

| URL | Purpose |
|-----|---------|
| `http://localhost` | Main application |
| `http://localhost:5000` | Development (if using `make dev`) |
| `http://localhost/_health` | Health check API |
| `http://localhost/api/projects` | API endpoint |

---

## 👤 Default Login

```
Username: admin
Password: admin
```

---

## 📁 Important Folders

| Folder | Purpose |
|--------|---------|
| `./data/` | SQLite database (persists) |
| `./templates/` | HTML files |
| `./static/` | CSS, JavaScript, images |
| `./logs/` | Application logs |

---

## 🆘 Quick Fixes

### App not starting?
```bash
make logs-prod
# Check for ERROR messages
```

### Port already in use?
```bash
# Edit docker-compose.prod.yml
# Change ports: "80:80" to "8080:80"
# Access: http://localhost:8080
```

### Database error?
```bash
make stop-prod
rm -rf data
make prod
```

### Docker not running?
```bash
# Start Docker Desktop application
docker --version  # Verify it's running
```

---

## 📚 Documentation Files

- **GETTING_STARTED.md** ← You are here
- **QUICKSTART.md** - Fast track to first run
- **DOCKER_SETUP.md** - Detailed Docker guide
- **PORTABLE_SETUP.md** - Multi-OS setup
- **APP_REVIEW.md** - App features
- **README.md** - Project overview

---

## ✨ Key Features

✅ Login & authentication
✅ Project management
✅ Shot tracking
✅ Video preview (Plate/MOV/EXR)
✅ Comments & feedback
✅ CSV import/export
✅ Nuke integration
✅ Cross-platform (Windows/Mac/Linux)

---

## 🚀 Deployment

This image is ready to deploy to:
- Docker Hub
- AWS ECS
- Google Cloud Run
- Azure Container Instances
- Any Docker-compatible host

Just build and push:
```bash
docker build -t dcproject:latest .
docker push <registry>/dcproject:latest
```

---

## 📞 Support

- Logs: `make logs-prod`
- Status: `docker-compose -f docker-compose.prod.yml ps`
- Restart: `make restart-prod`
- Help: `make help`

---

**Ready? Run:** `make prod`

**Then open:** http://localhost
