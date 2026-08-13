# VPS Deployment Guide
## AI-Powered Infrastructure Platform

Complete step-by-step guide to deploy this platform on your VPS.

---

## 📋 Prerequisites

### Your VPS Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: Minimum 2GB (4GB recommended)
- **CPU**: 2+ cores
- **Disk**: 20GB+ free space
- **Network**: Public IP with open ports 80, 443

### Required Accounts (Optional for full features)
- AWS Account (for Bedrock AI and deployments)
- Azure DevOps Account (for CI/CD pipelines)

---

## 🚀 Step-by-Step Deployment

### Step 1: Connect to Your VPS

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Update system packages
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
exit
```

### Step 3: Install Git and Clone Repository

```bash
# SSH back into your VPS
ssh user@your-vps-ip

# Install git
sudo apt install git -y

# Clone your repository
cd /opt
sudo mkdir -p apps
sudo chown $USER:$USER apps
cd apps
git clone <your-repository-url> infrastructure-platform
cd infrastructure-platform
```

### Step 4: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit the environment file
nano .env
```

**Minimal Configuration (Demo Mode):**
```bash
# Demo Mode - No AWS/Azure required
DEMO_MODE=true

# Backend Configuration
BACKEND_API_URL=http://localhost:8000
FRONTEND_URL=http://your-vps-ip:3000

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

**Production Configuration (Full Features):**
```bash
# Production Mode
DEMO_MODE=false

# AWS Configuration
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514

# Azure DevOps (Optional)
AZDO_ORGANIZATION=your-org
AZDO_PROJECT=your-project
AZDO_PIPELINE_ID=1
AZDO_PAT=your-personal-access-token

# Terraform State (Optional)
S3_TFSTATE_BUCKET=your-tfstate-bucket
DYNAMODB_LOCK_TABLE=your-lock-table

# Backend Configuration
BACKEND_API_URL=http://your-vps-ip:8000
FRONTEND_URL=http://your-vps-ip:3000

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d --build

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f
```

Expected output:
```
NAME                    STATUS
backend                 Up
frontend                Up
```

### Step 6: Verify Deployment

```bash
# Test backend health
curl http://localhost:8000/api/v1/health

# Expected: {"status":"healthy"}

# Test frontend (from browser)
# Open: http://your-vps-ip:3000
```

### Step 7: Configure Firewall

```bash
# Install UFW (if not installed)
sudo apt install ufw -y

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow backend API port
sudo ufw allow 8000/tcp

# Allow frontend port
sudo ufw allow 3000/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 8: Set Up Nginx Reverse Proxy (Recommended)

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/infrastructure-platform
```

Add this configuration:
```nginx
# Backend API
server {
    listen 80;
    server_name api.your-domain.com;  # or use IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name your-domain.com;  # or use IP

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/infrastructure-platform /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable Nginx to start on boot
sudo systemctl enable nginx
```

### Step 9: Set Up SSL with Let's Encrypt (Optional)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Certbot will automatically configure Nginx for HTTPS

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 10: Set Up Auto-Start on Reboot

```bash
# Docker Compose service file
sudo nano /etc/systemd/system/infrastructure-platform.service
```

Add this content:
```ini
[Unit]
Description=Infrastructure Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/apps/infrastructure-platform
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=your-username

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable infrastructure-platform

# Start service
sudo systemctl start infrastructure-platform

# Check status
sudo systemctl status infrastructure-platform
```

---

## 🔧 Configuration & Management

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart backend only
docker-compose restart backend

# Restart frontend only
docker-compose restart frontend
```

### Update Application

```bash
cd /opt/apps/infrastructure-platform

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup Data

```bash
# Create backup directory
mkdir -p ~/backups

# Backup environment file
cp .env ~/backups/.env.$(date +%Y%m%d)

# Backup Docker volumes (if any)
docker-compose down
tar -czf ~/backups/volumes-$(date +%Y%m%d).tar.gz docker/volumes/
docker-compose up -d
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check Docker status
sudo systemctl status docker

# Check logs
docker-compose logs

# Restart Docker
sudo systemctl restart docker
docker-compose up -d
```

### Port Already in Use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or change ports in .env and docker-compose.yml
```

### Can't Access from Browser

```bash
# Check if services are running
docker-compose ps

# Check firewall
sudo ufw status

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check logs
docker-compose logs
sudo tail -f /var/log/nginx/error.log
```

### Out of Memory

```bash
# Check memory usage
free -h

# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Docker Build Fails

```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔒 Security Hardening

### 1. Change Default Ports

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change 8000 to custom port
```

### 2. Set Strong Secrets

Edit `.env`:
```bash
# Generate random secret
openssl rand -hex 32

# Add to .env
SECRET_KEY=your-generated-secret
JWT_SECRET=another-generated-secret
```

### 3. Restrict API Access

Edit Nginx configuration:
```nginx
location /api/ {
    # Allow only specific IPs
    allow 1.2.3.4;
    deny all;
    
    proxy_pass http://localhost:8000;
}
```

### 4. Enable HTTPS Only

```bash
# Force HTTPS in Nginx
sudo nano /etc/nginx/sites-available/infrastructure-platform
```

Add redirect:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. Set Up Fail2Ban

```bash
# Install Fail2Ban
sudo apt install fail2ban -y

# Configure
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[nginx-http-auth]
enabled = true

[sshd]
enabled = true
maxretry = 3
bantime = 3600
```

```bash
# Start Fail2Ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📊 Monitoring

### Set Up Basic Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor in real-time
htop                    # CPU/Memory
docker stats            # Docker containers
sudo iotop              # Disk I/O
sudo nethogs            # Network
```

### Set Up Uptime Monitoring

Use external services like:
- UptimeRobot (free)
- Pingdom
- StatusCake

Monitor these endpoints:
- `http://your-vps-ip:8000/api/v1/health`
- `http://your-vps-ip:3000`

---

## 🎯 Testing Your Deployment

### Test 1: Health Check

```bash
curl http://your-vps-ip:8000/api/v1/health
```

Expected: `{"status":"healthy"}`

### Test 2: List Modules

```bash
curl http://your-vps-ip:8000/api/v1/modules | jq
```

Expected: JSON array with 5 modules

### Test 3: API Documentation

Open in browser:
```
http://your-vps-ip:8000/docs
```

Expected: Swagger/OpenAPI documentation

### Test 4: Frontend

Open in browser:
```
http://your-vps-ip:3000
```

Expected: Application homepage

---

## 📞 Quick Reference

### Important Paths
```
Application: /opt/apps/infrastructure-platform
Logs: docker-compose logs
Nginx Config: /etc/nginx/sites-available/
SSL Certs: /etc/letsencrypt/live/
Environment: /opt/apps/infrastructure-platform/.env
```

### Important Commands
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update code
git pull && docker-compose up -d --build

# Check status
docker-compose ps
```

### Important Ports
```
Backend API: 8000
Frontend: 3000
HTTP: 80
HTTPS: 443
```

---

## ✅ Post-Deployment Checklist

- [ ] Services running (docker-compose ps)
- [ ] Backend health check passes
- [ ] Frontend accessible
- [ ] API documentation accessible
- [ ] Firewall configured
- [ ] Nginx reverse proxy set up
- [ ] SSL certificate installed (if using domain)
- [ ] Auto-start on reboot configured
- [ ] Backup strategy in place
- [ ] Monitoring set up
- [ ] Logs accessible

---

## 🎉 Success!

Your platform is now deployed on your VPS!

**Access Points:**
- **API**: http://your-vps-ip:8000
- **API Docs**: http://your-vps-ip:8000/docs
- **Frontend**: http://your-vps-ip:3000

**Next Steps:**
1. Configure AWS credentials (if using production mode)
2. Set up Azure DevOps integration (if needed)
3. Configure DNS to point to your VPS
4. Set up SSL with Let's Encrypt
5. Configure backups
6. Set up monitoring

**Need Help?**
- Check logs: `docker-compose logs -f`
- Review troubleshooting section above
- Check API docs: http://your-vps-ip:8000/docs
