# DC Projects - Quick Start Guide

## 🚀 Start Development in 30 Seconds

```bash
# 1. Navigate to project
cd /Volumes/Prajwal/Working../DC_Projects_Final

# 2. Start development
make dev

# 3. Open in browser
open http://localhost:5000

# 4. Login
# Username: admin
# Password: admin
```

**That's it!** Your DC Projects app is running! ✅

---

## 📋 Essential Commands

### Development
```bash
make dev           # Start development server (port 5000)
make logs-dev      # View logs in real-time
make stop-dev      # Stop development
make shell-dev     # Open container shell
make restart-dev   # Restart development
```

### Production
```bash
make prod          # Start production server (port 80)
make logs-prod     # View production logs
make stop-prod     # Stop production
make shell-prod    # Open container shell
make restart-prod  # Restart production
```

### Maintenance
```bash
make clean         # Remove all containers and volumes
make build-dev     # Rebuild development image
make build-prod    # Rebuild production image
make help          # Show all commands
```

---

## 🌐 Access URLs

### Development
- **Application:** http://localhost:5000
- **Health Check:** http://localhost:5000/_health
- **Default Login:** admin / admin

### Production
- **Application:** http://localhost
- **Nginx:** http://localhost (port 80)
- **Flask App:** http://localhost:8000 (direct, behind Nginx)

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Docker image configuration |
| `docker-compose.dev.yml` | Development services setup |
| `docker-compose.prod.yml` | Production services setup |
| `.env.dev` | Development environment variables |
| `.env.prod` | Production environment variables |
| `nginx.prod.conf` | Nginx reverse proxy config |
| `Makefile` | Command shortcuts |
| `DOCKER_SETUP.md` | Detailed documentation |

---

## ⚙️ Configuration

### Change Development Port
Edit `docker-compose.dev.yml`:
```yaml
ports:
  - "5001:5000"  # Change 5001 to your preferred port
```

### Change Production Secret Key
Edit `.env.prod`:
```bash
DC_SECRET_KEY=your_very_secure_random_key_32_chars_minimum
```

Generate secure key:
```bash
openssl rand -base64 32
```

---

## 🔧 Troubleshooting

### Port Already in Use?
```bash
# Development (5000)
lsof -i :5000
kill -9 <PID>

# Production (80)
lsof -i :80
kill -9 <PID>
```

### Container Won't Start?
```bash
make logs-dev        # Check error
make build-dev       # Rebuild
make dev             # Try again
```

### Database Issues?
```bash
make shell-dev       # Open container
rm data/dc_projects.db   # Delete database
exit                 # Exit container
make restart-dev     # Restart (recreates DB)
```

---

## 📊 Docker Commands (Alternative)

If you prefer not using `make`:

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f
docker-compose -f docker-compose.dev.yml down

# Production
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml down
```

---

## 📝 Next Steps

1. **Change admin password** - Login and update your password
2. **Configure projects** - Add your projects and shots
3. **Enable SSL** - For production, follow DOCKER_SETUP.md
4. **Backup data** - Regular database backups recommended

---

## 🆘 Need Help?

- 📖 Full docs: Read `DOCKER_SETUP.md`
- 🐛 Errors: Check `make logs-dev` or `make logs-prod`
- 🔄 Restart: `make restart-dev` or `make restart-prod`
- 🧹 Reset: `make clean` (removes everything)

---

## ✅ What's Running?

### Development
- ✓ Flask app on port 5000
- ✓ Auto-reload on code changes
- ✓ SQLite database in `./data`
- ✓ Hot debugging enabled

### Production
- ✓ Flask app with Gunicorn (4 workers)
- ✓ Nginx reverse proxy on port 80
- ✓ Health checks enabled
- ✓ Persistent volumes
- ✓ SSL/HTTPS ready

---

**Ready to go!** 🎉

Start with: `make dev`
