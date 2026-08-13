# 🚀 Deploy This Platform to Your VPS NOW!

## ⚡ Super Quick Start (Copy & Paste)

**Time Required: 15-20 minutes**

---

## Step 1: Connect to VPS & Install Requirements

Copy and paste this entire block into your VPS terminal:

```bash
# Update system and install Docker
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install git -y

echo "✅ Installation complete! Now LOG OUT and LOG BACK IN for Docker permissions to take effect."
```

**⚠️ IMPORTANT: After running the above, you MUST log out and log back into your VPS:**
```bash
exit
# Then SSH back in
ssh user@your-vps-ip
```

---

## Step 2: Clone and Configure

```bash
# Create directory and clone
cd /opt
sudo mkdir -p apps && sudo chown $USER:$USER apps
cd apps
git clone <YOUR_REPO_URL_HERE> platform
cd platform

# Create environment file
cp .env.example .env

# Edit with nano (or use vi)
nano .env
```

**Replace these values in the .env file:**
```bash
# Change YOUR_VPS_IP to your actual VPS IP address
DEMO_MODE=true
BACKEND_API_URL=http://YOUR_VPS_IP:8000
FRONTEND_URL=http://YOUR_VPS_IP:3000
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

---

## Step 3: Deploy!

```bash
# Build and start everything
docker-compose up -d --build

# Wait 2-3 minutes for build...
# Check if everything is running
docker-compose ps
```

You should see:
```
NAME                STATUS
backend             Up
frontend            Up
dynamodb-local      Up
```

---

## Step 4: Open Firewall

```bash
# Quick firewall setup
sudo apt install ufw -y
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw --force enable
```

---

## Step 5: Test It!

```bash
# Test backend
curl http://localhost:8000/api/v1/health

# Should show: {"status":"healthy"}
```

**Open in your browser:**
- API Docs: `http://YOUR_VPS_IP:8000/docs`
- Frontend: `http://YOUR_VPS_IP:3000`

---

## ✅ That's It! You're Done!

Your platform is now running!

---

## 🎯 What You Get

- ✅ FastAPI Backend with REST API
- ✅ Next.js Frontend (if implemented)
- ✅ AWS Bedrock AI Integration (ready)
- ✅ Terraform Infrastructure as Code
- ✅ Azure DevOps CI/CD (ready)
- ✅ Security Scanning (Checkov + Trivy)
- ✅ Approval Workflows
- ✅ Module Registry (5 approved AWS modules)
- ✅ Complete API Documentation

---

## 📖 Quick API Tests

### Test 1: Health Check
```bash
curl http://YOUR_VPS_IP:8000/api/v1/health
```

### Test 2: List Available Modules
```bash
curl http://YOUR_VPS_IP:8000/api/v1/modules
```

### Test 3: AI Analysis (Demo Mode)
```bash
curl -X POST http://YOUR_VPS_IP:8000/api/v1/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create two EC2 instances for my web app",
    "application": "webapp",
    "environment": "dev"
  }'
```

### Test 4: View API Documentation
Open in browser: `http://YOUR_VPS_IP:8000/docs`

---

## 🔧 Daily Management Commands

```bash
# Navigate to app directory
cd /opt/apps/platform

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart all services
docker-compose restart

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View resource usage
docker stats
```

---

## 🔄 How to Update

```bash
cd /opt/apps/platform
git pull
docker-compose down
docker-compose up -d --build
```

---

## 🆘 Troubleshooting

### Can't access from browser?
```bash
# Check if services are running
docker-compose ps

# Check firewall
sudo ufw status

# Check logs for errors
docker-compose logs
```

### Services won't start?
```bash
# Check Docker is running
sudo systemctl status docker

# If not, start it
sudo systemctl start docker

# Then try again
docker-compose up -d
```

### Port already in use?
```bash
# Find what's using the port
sudo lsof -i :8000

# Kill it
sudo kill -9 <PID>

# Or just restart
docker-compose down
docker-compose up -d
```

### Out of disk space?
```bash
# Clean up Docker
docker system prune -a -f

# Check disk space
df -h
```

---

## 🔐 Production Setup (Optional)

For production use with real AWS/Azure:

```bash
cd /opt/apps/platform
nano .env
```

Change these:
```bash
DEMO_MODE=false

# AWS Credentials
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514

# Azure DevOps (if using)
AZDO_ORGANIZATION=your-org
AZDO_PROJECT=your-project
AZDO_PIPELINE_ID=1
AZDO_PAT=your_personal_access_token

# Terraform State
S3_TFSTATE_BUCKET=your-tfstate-bucket
DYNAMODB_LOCK_TABLE=your-lock-table
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

---

## 🌐 Add Nginx Reverse Proxy (Recommended)

```bash
# Install Nginx
sudo apt install nginx -y

# Create config
sudo nano /etc/nginx/sites-available/platform
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name YOUR_VPS_IP;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable and start
sudo ln -s /etc/nginx/sites-available/platform /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

Now access at: `http://YOUR_VPS_IP` (port 80)

---

## 🔒 Add SSL (If You Have a Domain)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal is configured automatically
```

---

## 🤖 Auto-Start on Reboot

```bash
# Create service file
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

Replace `YOUR_USERNAME` with your username, then:

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable platform
sudo systemctl start platform

# Check status
sudo systemctl status platform
```

---

## 📊 Monitoring Setup

### Option 1: Basic Monitoring (Free)

Install monitoring tools:
```bash
sudo apt install htop iotop nethogs -y
```

Use them:
```bash
htop           # System resources
docker stats   # Container resources
sudo iotop     # Disk I/O
sudo nethogs   # Network usage
```

### Option 2: External Monitoring (Recommended)

Use **UptimeRobot** (free):
1. Go to https://uptimerobot.com
2. Create free account
3. Add monitors for:
   - `http://YOUR_VPS_IP:8000/api/v1/health`
   - `http://YOUR_VPS_IP:3000`

Get email alerts if your site goes down!

---

## 💾 Backup Strategy

### Quick Backup Script

```bash
# Create backup script
nano ~/backup.sh
```

Paste this:
```bash
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Backup .env
cp /opt/apps/platform/.env $BACKUP_DIR/.env.$DATE

# Backup data volumes (if any)
cd /opt/apps/platform
docker-compose down
tar -czf $BACKUP_DIR/data-$DATE.tar.gz ./data 2>/dev/null || true
docker-compose up -d

echo "Backup completed: $BACKUP_DIR"
```

```bash
# Make executable
chmod +x ~/backup.sh

# Run it
~/backup.sh

# Schedule daily backups (optional)
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup.sh") | crontab -
```

---

## 🎓 Understanding the Architecture

### Components:
1. **Backend (FastAPI)**: REST API server on port 8000
2. **Frontend (Next.js)**: Web UI on port 3000
3. **DynamoDB Local**: Database for local dev/testing
4. **Terraform Modules**: Infrastructure as Code templates
5. **AI Integration**: Amazon Bedrock for AI features
6. **Security**: Checkov + Trivy scanning

### Data Flow:
```
User → Frontend → Backend API → AI/Terraform → AWS
                       ↓
                  DynamoDB (local)
```

---

## 📚 Documentation

- **Full Deployment Guide**: `VPS_DEPLOYMENT_GUIDE.md`
- **Step-by-Step Checklist**: `DEPLOYMENT_CHECKLIST.md`
- **Quick Start**: `QUICK_START.md`
- **Architecture**: `docs/architecture/overview.md`
- **API Reference**: Access at `/docs` endpoint
- **Security Policies**: `security/policies/`

---

## 🎯 Next Steps After Deployment

1. ✅ **Test all endpoints** - Use the API docs
2. ✅ **Configure monitoring** - Set up UptimeRobot
3. ✅ **Add SSL** - If you have a domain
4. ✅ **Set up backups** - Run the backup script
5. ✅ **Configure AWS** - Add real credentials for production
6. ✅ **Set up CI/CD** - Connect Azure DevOps
7. ✅ **Harden security** - Change default ports, add firewall rules

---

## 🆘 Getting Help

### Check Logs
```bash
docker-compose logs -f
```

### Check Service Status
```bash
docker-compose ps
sudo systemctl status platform
```

### Test Connectivity
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/modules
```

### Common Issues
- **Can't connect**: Check firewall with `sudo ufw status`
- **Port in use**: Kill process with `sudo lsof -i :8000`
- **Out of memory**: Add swap space (see troubleshooting)
- **Build fails**: Clean Docker with `docker system prune -a`

---

## 🎉 Success!

**Your Infrastructure Platform is Live!**

**Access URLs:**
- 🌐 Frontend: `http://YOUR_VPS_IP:3000`
- 🔌 Backend API: `http://YOUR_VPS_IP:8000`
- 📖 API Docs: `http://YOUR_VPS_IP:8000/docs`
- ❤️ Health: `http://YOUR_VPS_IP:8000/api/v1/health`

**What You Can Do:**
- ✅ Make infrastructure deployment requests
- ✅ Use AI to analyze requirements
- ✅ Deploy AWS resources (with real credentials)
- ✅ Manage approvals and workflows
- ✅ Track resource inventory
- ✅ View comprehensive audit trails

**Enjoy your new platform! 🚀**

---

## 📞 Quick Reference

| Item | Command/URL |
|------|-------------|
| Start Services | `docker-compose up -d` |
| Stop Services | `docker-compose down` |
| View Logs | `docker-compose logs -f` |
| Check Status | `docker-compose ps` |
| Restart | `docker-compose restart` |
| Update | `git pull && docker-compose up -d --build` |
| API Docs | `http://YOUR_VPS_IP:8000/docs` |
| Frontend | `http://YOUR_VPS_IP:3000` |
| Health Check | `http://YOUR_VPS_IP:8000/api/v1/health` |

---

*For detailed instructions, see `VPS_DEPLOYMENT_GUIDE.md` and `DEPLOYMENT_CHECKLIST.md`*
