# DC Projects - Docker Setup Guide (Dev & Prod)

## Quick Start

### Development (Recommended for setup)
```bash
# 1. Clone/Navigate to project
cd /Volumes/Prajwal/Working../DC_Projects_Final

# 2. Start development environment
make dev

# 3. Access application
# Browser: http://localhost:5000
# Login: admin / admin

# 4. View logs
make logs-dev

# 5. Stop when done
make stop-dev
```

### Production
```bash
# 1. Set secure secret key
echo "DC_SECRET_KEY=your_secure_random_key_min_32_chars" >> .env.prod

# 2. Start production environment
make prod

# 3. Access application
# Browser: http://localhost (via Nginx)

# 4. View logs
make logs-prod

# 5. Stop when done
make stop-prod
```

---

## Environment Profiles

### Development Profile
**Use for:** Local development, testing, debugging

**Configuration:**
- Port: `5000` (Direct Flask)
- Debug: `True`
- Hot-reload: Enabled (code changes auto-reload)
- Logging: DEBUG level
- Database: SQLite (local file)
- Volumes: Mounted for live editing

**Access:**
```
http://localhost:5000
```

**Commands:**
```bash
make dev              # Start
make logs-dev         # View logs
make shell-dev        # Open container shell
make build-dev        # Rebuild image
make stop-dev         # Stop
make restart-dev      # Restart
```

---

### Production Profile
**Use for:** Deployment, live servers, stable environments

**Configuration:**
- Port: `8000` (Behind Nginx)
- Debug: `False`
- Server: Gunicorn (4 workers)
- Logging: INFO level
- Reverse Proxy: Nginx
- Database: Persistent volume
- Security: Enhanced

**Access:**
```
http://localhost (port 80 via Nginx)
```

**Commands:**
```bash
make prod             # Start
make logs-prod        # View logs
make shell-prod       # Open container shell
make build-prod       # Rebuild image
make stop-prod        # Stop
make restart-prod     # Restart
```

---

## File Structure

```
/Volumes/Prajwal/Working../DC_Projects_Final/
├── app.py                      # Main Flask app
├── Dockerfile                  # Multi-stage build
├── docker-compose.dev.yml      # Dev configuration
├── docker-compose.prod.yml     # Prod configuration
├── nginx.prod.conf             # Nginx config (production)
├── requirements.txt            # Python dependencies
├── Makefile                    # Commands
├── .env.example               # Environment variables example
├── .env.dev                   # Development env vars
├── .env.prod                  # Production env vars (CREATE YOURSELF)
├── templates/                 # HTML templates
├── static/                    # CSS, JS, images
├── data/                      # SQLite database (generated)
└── logs/                      # Application logs (generated)
```

---

## Detailed Setup Instructions

### Step 1: Install Docker

**macOS:**
```bash
# Using Homebrew
brew install docker docker-compose

# Or download Docker Desktop from:
# https://www.docker.com/products/docker-desktop
```

**Windows/Linux:**
- Download from https://www.docker.com/products/docker-desktop

---

### Step 2: Setup Environment Files

```bash
# Copy example to actual files
cp .env.example .env.dev

# Create production file (with secure key)
cat > .env.prod << EOF
ENVIRONMENT=production
FLASK_APP=app.py
FLASK_ENV=production
DEBUG=False
DC_SECRET_KEY=$(openssl rand -base64 32)
PROD_PORT=8000
PROD_HOST=0.0.0.0
WORKERS=4
LOG_LEVEL=INFO
EOF
```

---

### Step 3: Start Development

```bash
# Navigate to project
cd /Volumes/Prajwal/Working../DC_Projects_Final

# Start development
make dev

# Wait 5-10 seconds for startup
# Check logs
make logs-dev

# Open browser
open http://localhost:5000
```

**First Run:**
- Database creates automatically
- Tables initialize
- Default user: `admin` / `admin`

---

### Step 4: Stop Development

```bash
# Stop containers
make stop-dev

# View volumes
docker volume ls

# Clean everything (removes data too)
make clean
```

---

## Production Deployment

### Step 1: Prepare Production

```bash
# Create .env.prod with secure key
cat > .env.prod << EOF
ENVIRONMENT=production
FLASK_APP=app.py
FLASK_ENV=production
DEBUG=False
DC_SECRET_KEY=$(openssl rand -base64 32)
PROD_PORT=8000
PROD_HOST=0.0.0.0
WORKERS=4
LOG_LEVEL=INFO
EOF

# Make sure directory exists
mkdir -p data logs
```

### Step 2: Enable SSL/HTTPS (Optional)

1. **Generate self-signed certificate (testing only):**
```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365
```

2. **Uncomment SSL section in nginx.prod.conf:**
```nginx
listen 443 ssl http2;
ssl_certificate /etc/nginx/certs/cert.pem;
ssl_certificate_key /etc/nginx/certs/key.pem;
```

3. **Uncomment HTTP to HTTPS redirect:**
```nginx
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

### Step 3: Start Production

```bash
# Build and start
make build-prod
make prod

# Verify
make logs-prod

# Access
open http://localhost
```

---

## Useful Commands

### View Status
```bash
# Development
docker-compose -f docker-compose.dev.yml ps

# Production
docker-compose -f docker-compose.prod.yml ps
```

### View Logs
```bash
# Development (tail last 50 lines)
docker-compose -f docker-compose.dev.yml logs -f --tail=50

# Production (with timestamps)
docker-compose -f docker-compose.prod.yml logs -f --timestamps
```

### Access Container Shell
```bash
# Development
make shell-dev

# Production
make shell-prod

# Inside container
ls -la
python app.py --version
exit  # to exit
```

### Database Operations
```bash
# Access container
make shell-dev

# Inside container:
python -c "from app import db, app; app.app_context().push(); db.drop_all(); db.create_all()"

# Exit
exit
```

### View Application Files
```bash
# Development
docker exec dc-projects-dev ls -la /app

# Production
docker exec dc-projects-prod ls -la /app
```

---

## Troubleshooting

### Port Already in Use

**Development (port 5000):**
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.dev.yml
ports:
  - "5001:5000"  # Use 5001 instead
```

**Production (port 8000):**
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Container Won't Start

```bash
# Check logs
make logs-dev

# Rebuild
make build-dev
make dev

# If still failing, check Docker daemon
docker info
```

### Database Lock Issues

```bash
# Remove database and restart
make shell-dev
rm data/dc_projects.db
exit
make restart-dev
```

### Permission Denied

```bash
# Fix permissions
chmod +x app.py

# Add Docker permissions (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

---

## Performance Tuning

### Development
```yaml
# docker-compose.dev.yml
environment:
  - PYTHONUNBUFFERED=1     # Real-time logs
  - FLASK_ENV=development
```

### Production
```yaml
# docker-compose.prod.yml
command: gunicorn \
  --workers 4 \           # CPU cores
  --worker-class sync \   # Sync workers
  --bind 0.0.0.0:8000 \
  --timeout 120 \         # Long requests
  --access-logfile - \
  app:app
```

---

## Monitoring

### Application Health
```bash
# Development
curl http://localhost:5000/_health

# Production
curl http://localhost/_health
```

### Container Stats
```bash
# CPU and Memory usage
docker stats dc-projects-dev
```

### Database Size
```bash
docker exec dc-projects-dev du -sh /app/data/
```

---

## Backup & Restore

### Backup Database
```bash
# Development
docker cp dc-projects-dev:/app/data/dc_projects.db ./backup_$(date +%Y%m%d).db

# Production
docker cp dc-projects-prod:/app/data/dc_projects.db ./backup_$(date +%Y%m%d).db
```

### Restore Database
```bash
# Stop container
make stop-dev

# Copy backup
docker cp ./backup_20231215.db dc-projects-dev:/app/data/dc_projects.db

# Start
make dev
```

---

## Security Checklist

- [ ] Change default admin password
- [ ] Update DC_SECRET_KEY in .env.prod (random 32+ chars)
- [ ] Enable SSL/HTTPS for production
- [ ] Use strong database passwords
- [ ] Restrict Nginx access to trusted IPs
- [ ] Keep Docker images updated
- [ ] Regular database backups
- [ ] Monitor logs for errors
- [ ] Use firewall rules

---

## Support

For issues:
1. Check logs: `make logs-dev` or `make logs-prod`
2. Restart: `make restart-dev` or `make restart-prod`
3. Clean rebuild: `make build-dev` or `make build-prod`
4. Report with logs attached
