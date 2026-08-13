# Quick VPS Deployment Checklist

## ⚡ Fast Track Deployment (30 minutes)

### Prerequisites
- [ ] VPS with Ubuntu 20.04+ (2GB RAM, 2 CPU cores)
- [ ] Root or sudo access
- [ ] Public IP address

---

## 📝 Step-by-Step Instructions

### 1️⃣ Initial Setup (5 minutes)

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in
exit
ssh user@your-vps-ip
```

### 2️⃣ Clone Repository (2 minutes)

```bash
# Install Git
sudo apt install git -y

# Create app directory
cd /opt
sudo mkdir -p apps && sudo chown $USER:$USER apps
cd apps

# Clone repository (replace with your repo URL)
git clone <YOUR_REPOSITORY_URL> platform
cd platform
```

### 3️⃣ Configure Environment (3 minutes)

```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

**For Demo/Testing:**
```bash
DEMO_MODE=true
BACKEND_API_URL=http://YOUR_VPS_IP:8100
FRONTEND_URL=http://YOUR_VPS_IP:3200
NEXT_PUBLIC_API_BASE_URL=http://YOUR_VPS_IP:8100
```

**For Production with AWS:**
```bash
DEMO_MODE=false
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514
BACKEND_API_URL=http://YOUR_VPS_IP:8100
FRONTEND_URL=http://YOUR_VPS_IP:3200
NEXT_PUBLIC_API_BASE_URL=http://YOUR_VPS_IP:8100
```

Save: `Ctrl+X`, `Y`, `Enter`

### 4️⃣ Deploy Application (5 minutes)

```bash
# Build and start services
docker-compose up -d --build

# Wait for build to complete...
# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Expected output:
```
NAME                STATUS
backend             Up
frontend            Up
dynamodb-local      Up
```

### 5️⃣ Configure Firewall (2 minutes)

```bash
# Install and configure firewall
sudo apt install ufw -y
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8100/tcp  # Backend API
sudo ufw allow 3200/tcp  # Frontend UI
sudo ufw enable
```

### 6️⃣ Verify Deployment (3 minutes)

```bash
# Test backend
curl http://localhost:8100/api/v1/health

# Should return: {"status":"healthy"}

# Test modules endpoint
curl http://localhost:8100/api/v1/modules | head -20
```

From your browser:
- **Frontend (UI)**: `http://YOUR_VPS_IP:3200`
- **Backend API Docs**: `http://YOUR_VPS_IP:8100/docs`
- **Health Check**: `http://YOUR_VPS_IP:8100/api/v1/health`

### 7️⃣ Set Up Nginx (Optional - 5 minutes)

```bash
# Install Nginx
sudo apt install nginx -y

# Create config
sudo nano /etc/nginx/sites-available/platform
```

Paste this:
```nginx
server {
    listen 80;
    server_name YOUR_VPS_IP;

    # Frontend
    location / {
        proxy_pass http://localhost:3200;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API Docs
    location /docs {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/platform /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 8️⃣ Set Up Auto-Start (5 minutes)

```bash
# Create systemd service
sudo nano /etc/systemd/system/platform.service
```

Paste this:
```ini
[Unit]
Description=Infrastructure Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/apps/platform
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=YOUR_USERNAME

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual username, then:

```bash
# Enable service
sudo systemctl daemon-reload
sudo systemctl enable platform
sudo systemctl start platform
```

---

## ✅ Verification Checklist

Run these commands to verify everything:

```bash
# 1. Check Docker containers
docker-compose ps
# All should show "Up"

# 2. Check backend health
curl http://localhost:8000/api/v1/health
# Should return: {"status":"healthy"}

# 3. Check backend modules
curl http://localhost:8000/api/v1/modules
# Should return JSON array

# 4. Check Nginx (if installed)
sudo systemctl status nginx
# Should show "active (running)"

# 5. Check auto-start service
sudo systemctl status platform
# Should show "active"

# 6. Test from browser
# Open: http://YOUR_VPS_IP:8000/docs
# Open: http://YOUR_VPS_IP:3000
```

---

## 🎯 Quick Commands Reference

### Daily Operations
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Start services
docker-compose up -d

# Update application
cd /opt/apps/platform
git pull
docker-compose up -d --build
```

### Troubleshooting
```bash
# Check what's running
docker-compose ps

# Check resource usage
docker stats

# View detailed logs
docker-compose logs backend --tail=100
docker-compose logs frontend --tail=100

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Clean restart
docker-compose down
docker-compose up -d --build
```

---

## 🚨 Common Issues & Solutions

### Issue: "Port already in use"
```bash
# Find and kill process using port
sudo lsof -i :8100
sudo kill -9 <PID>

# Or change ports in docker-compose.yml
```

### Issue: "Cannot connect to Docker daemon"
```bash
# Start Docker
sudo systemctl start docker

# Add user to docker group (if not done)
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: "Out of disk space"
```bash
# Clean Docker
docker system prune -a

# Remove old images
docker image prune -a
```

### Issue: "Out of memory"
```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: "Can't access from browser"
```bash
# Check firewall
sudo ufw status

# Open port if needed
sudo ufw allow 8100/tcp
sudo ufw allow 3200/tcp

# Check if services are running
docker-compose ps
curl http://localhost:8100/api/v1/health
```

---

## 🔒 Security (Optional but Recommended)

### 1. Change Default Ports
Edit `docker-compose.yml` to use non-standard ports:
```yaml
ports:
  - "8080:8000"  # Instead of 8000:8000
  - "3001:3000"  # Instead of 3000:3000
```

### 2. Add SSL Certificate (If you have a domain)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is set up automatically
```

### 3. Restrict API Access
Add to Nginx config:
```nginx
location /api {
    # Allow only specific IPs
    allow YOUR_IP;
    deny all;
    
    proxy_pass http://localhost:8000;
}
```

### 4. Set Strong Secrets
```bash
# Generate secret
openssl rand -hex 32

# Add to .env
nano .env
# Add: SECRET_KEY=generated_secret_here
```

---

## 📊 Monitoring

### Basic Monitoring Commands
```bash
# System resources
htop

# Docker container stats
docker stats

# Disk usage
df -h

# Service status
sudo systemctl status platform

# Application logs
docker-compose logs -f --tail=50
```

### Set Up External Monitoring (Recommended)
Use free services like:
- **UptimeRobot** (uptimerobot.com)
- **Pingdom** (pingdom.com)

Monitor these URLs:
- `http://YOUR_VPS_IP:8100/api/v1/health`
- `http://YOUR_VPS_IP:3200`

---

## 🎉 You're Done!

**Your platform is now running at:**

- 🌐 **Frontend**: http://YOUR_VPS_IP:3000
- 🔌 **API**: http://YOUR_VPS_IP:8000
- 📖 **API Docs**: http://YOUR_VPS_IP:8000/docs

**Next Steps:**
1. ✅ Test the health endpoint
2. ✅ Browse API documentation
3. ✅ Test creating a deployment request
4. 📝 Configure AWS credentials (for production)
5. 🔐 Set up SSL certificate (if using domain)
6. 📊 Set up monitoring

**Need Help?**
- Full guide: See `VPS_DEPLOYMENT_GUIDE.md`
- Logs: `docker-compose logs -f`
- Status: `docker-compose ps`
- Quick start: See `QUICK_START.md`

---

## 💡 Pro Tips

1. **Always keep backups**: 
   ```bash
   # Backup .env file
   cp .env .env.backup
   ```

2. **Monitor logs regularly**:
   ```bash
   docker-compose logs -f --tail=50
   ```

3. **Update regularly**:
   ```bash
   cd /opt/apps/platform
   git pull
   docker-compose up -d --build
   ```

4. **Test after updates**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

5. **Keep Docker clean**:
   ```bash
   # Weekly cleanup
   docker system prune -f
   ```
