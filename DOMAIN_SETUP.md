# DC Projects - Local Domain Setup (dcproject.com)

## Setup Local Domain (macOS)

### Step 1: Edit /etc/hosts

Open terminal and edit the hosts file:

```bash
sudo nano /etc/hosts
```

Add this line at the end:

```
127.0.0.1    dcproject.com www.dcproject.com
```

Save (Ctrl+O, Enter, Ctrl+X)

### Step 2: Verify Setup

```bash
# Should resolve to 127.0.0.1
ping dcproject.com

# Expected output:
# PING dcproject.com (127.0.0.1): 56 data bytes
```

### Step 3: Start Production

```bash
cd /Volumes/Prajwal/Working../DC_Projects_Final

# Make sure no services are running
make clean

# Start production
make prod
```

### Step 4: Access Application

Open browser and go to:

```
http://dcproject.com
```

Or:

```
http://www.dcproject.com
```

**Login:** `admin` / `admin`

---

## How It Works

1. **Local hosts file** maps dcproject.com → 127.0.0.1 (localhost)
2. **Browser** visits http://dcproject.com
3. **Routes to** 127.0.0.1:80
4. **Nginx** listens on port 80
5. **Nginx** proxies to Flask app on port 8000

---

## Troubleshooting

### Browser shows "Cannot reach dcproject.com"

**Fix:** Make sure hosts file was edited correctly:

```bash
# Check if domain is in hosts
grep dcproject.com /etc/hosts

# Should show:
# 127.0.0.1    dcproject.com www.dcproject.com
```

### Browser shows ERR_NAME_NOT_RESOLVED

**Fix:** Flush DNS cache on macOS:

```bash
# Flush DNS
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Wait 5 seconds
sleep 5

# Try again
ping dcproject.com
```

### Nginx shows "Bad Gateway"

**Fix:** Make sure Flask app is running:

```bash
# Check if container is running
docker-compose -f docker-compose.prod.yml ps

# View logs
make logs-prod
```

### Port 80 Permission Denied (macOS)

**Fix:** Nginx needs sudo permission for port 80:

```bash
# Stop current
make stop-prod

# Run with sudo
sudo docker-compose -f docker-compose.prod.yml up -d

# View logs
sudo docker-compose -f docker-compose.prod.yml logs -f
```

Or use higher port (8080):

```bash
# Edit docker-compose.prod.yml
# Change: ports: "80:80" → ports: "8080:80"

# Then access:
# http://dcproject.com:8080
```

---

## Quick Commands

```bash
# Start production on dcproject.com
make prod

# View logs
make logs-prod

# Stop production
make stop-prod

# Access from another machine
http://dcproject.com          # macOS/Linux
http://dcproject.com:8080     # If using port 8080

# Check if running
curl http://dcproject.com

# Health check
curl http://dcproject.com/_health
```

---

## Reset Local Domain

To remove the local domain mapping:

```bash
# Edit hosts file
sudo nano /etc/hosts

# Remove this line:
# 127.0.0.1    dcproject.com www.dcproject.com

# Flush DNS
sudo dscacheutil -flushcache
```

---

## Access from Other Machines

If you want to access dcproject.com from another machine on your network:

1. Find your local IP:
```bash
ifconfig | grep inet
# Look for something like: 192.168.x.x
```

2. On other machine's hosts file, use your IP instead of 127.0.0.1:
```
192.168.1.100    dcproject.com www.dcproject.com
```

---

## Production URLs

| URL | Purpose |
|-----|---------|
| `http://dcproject.com` | Main application |
| `http://dcproject.com/login` | Login page |
| `http://dcproject.com/api/session` | Current user |
| `http://dcproject.com/api/projects` | List projects |
| `http://dcproject.com/_health` | Health check |

---

## Notes

- ✅ Works on macOS, Linux, Windows (same /etc/hosts approach)
- ✅ No DNS changes needed (local only)
- ✅ Perfect for development & testing
- ⚠️ Only works on this machine
- ⚠️ Port 80 may require sudo on macOS

For production on real domain, update:
1. DNS records to point dcproject.com to your server IP
2. SSL certificate in nginx.prod.conf
3. Update FLASK_SECRET_KEY in .env.prod
