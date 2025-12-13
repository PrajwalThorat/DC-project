# DC Projects - Docker Setup Guide

## Prerequisites
- Docker installed (https://www.docker.com/products/docker-desktop)
- Docker Compose installed (comes with Docker Desktop)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone/Navigate to project directory:**
```bash
cd /Volumes/Prajwal/Working../DC_Projects_Final
```

2. **Build and start the containers:**
```bash
docker-compose up -d
```

3. **Access the application:**
   - Direct Flask: `http://localhost:5000`
   - Via Nginx: `http://localhost:80`

4. **Stop the application:**
```bash
docker-compose down
```

### Option 2: Using Docker CLI Only

1. **Build the Docker image:**
```bash
docker build -t dc-projects:latest .
```

2. **Run the container:**
```bash
docker run -d \
  --name dc-projects \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e DC_SECRET_KEY=your_secure_key_here \
  dc-projects:latest
```

3. **Access the application:**
   - `http://localhost:5000`

## Configuration

### Environment Variables

Set these in `docker-compose.yml` or when running the container:

```yaml
environment:
  - FLASK_APP=app.py
  - DC_SECRET_KEY=your_very_secure_random_key_here
```

### Volume Mounts

The docker-compose file mounts:
- `./data:/app/data` - Persistent database storage
- `./templates:/app/templates` - HTML templates

### Port Configuration

- **Flask Direct:** Port 5000
- **Nginx Reverse Proxy:** Port 80 (HTTP), 443 (HTTPS)

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Access at http://localhost:8080
```

## URLs

### Development (Docker Compose with Nginx)
- **Main App:** `http://localhost` or `http://localhost:80`
- **Direct Flask:** `http://localhost:5000`
- **API Base:** `http://localhost/api`
- **Login:** `http://localhost/login`

### Production (Change hostname)
In `nginx.conf`:
```nginx
server_name yourdomain.com;
```

Then access:
- **Main App:** `http://yourdomain.com`
- **API Base:** `http://yourdomain.com/api`

## SSL/HTTPS Setup

### For Production with SSL:

1. **Update nginx.conf** to add SSL certificates:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    
    # ... rest of config
}
```

2. **Mount certificates in docker-compose.yml:**
```yaml
volumes:
  - ./certs:/etc/nginx/certs:ro
```

## Database

- **Location:** `/app/data/dc_projects.db` (inside container)
- **Host Location:** `./data/dc_projects.db` (your machine)
- **Auto-initialized:** Yes, on first run

## Default Credentials

- **Username:** `admin`
- **Password:** `admin`

⚠️ **Change immediately in production!**

## Viewing Logs

```bash
# All containers
docker-compose logs -f

# Specific service
docker-compose logs -f dc-projects

# Flask app logs
docker logs -f dc-projects-app
```

## Troubleshooting

### Port Already in Use
```bash
# Find what's using port 5000
lsof -i :5000

# Change port in docker-compose.yml
ports:
  - "5001:5000"
```

### Database Issues
```bash
# Clear database and restart
docker-compose down
rm -rf data/dc_projects.db
docker-compose up -d
```

### Container won't start
```bash
# Check logs
docker-compose logs dc-projects

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

### Using reverse proxy (Nginx/Apache)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Using cloud platforms (AWS, GCP, Azure)
1. Push image to container registry
2. Deploy as container service
3. Configure environment variables
4. Set up persistent storage for `/app/data`

## Scaling

For multiple instances with load balancing:
```yaml
services:
  dc-projects-1:
    # config...
  dc-projects-2:
    # config...
  dc-projects-3:
    # config...
```

Then configure Nginx to load balance between them.
