# ⚡ Quick Deploy Guide

## Deploy in 5 Commands

```bash
# 1. Navigate to project
cd ~/InternalDevelopersPlatform

# 2. Make deploy script executable
chmod +x deploy.sh

# 3. Run deployment
./deploy.sh

# 4. Open firewall ports
sudo ufw allow 8100/tcp && sudo ufw allow 3200/tcp

# 5. Access your portal
# Frontend: http://YOUR_VPS_IP:3200
# API Docs: http://YOUR_VPS_IP:8100/docs
```

## Or Manual Deploy

```bash
# Stop old containers
docker-compose down

# Build and start
docker-compose build --no-cache
docker-compose up -d

# Check status
docker-compose ps
curl http://localhost:8100/api/v1/health
```

## Port Summary

| Service | Port | URL |
|---------|------|-----|
| Frontend UI | **3200** | http://YOUR_IP:3200 |
| Backend API | **8100** | http://YOUR_IP:8100 |
| API Docs | **8100** | http://YOUR_IP:8100/docs |
| Health Check | **8100** | http://YOUR_IP:8100/api/v1/health |

## Quick Tests

```bash
# Test backend
curl http://localhost:8100/api/v1/health

# Test modules
curl http://localhost:8100/api/v1/modules

# View logs
docker-compose logs -f
```

## Common Commands

```bash
# Restart everything
docker-compose restart

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Update and redeploy
git pull && docker-compose build && docker-compose up -d
```

## Troubleshooting

### Containers won't start
```bash
docker-compose down
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

### Port conflict
```bash
# Check what's using the port
sudo lsof -i :8100
sudo lsof -i :3200

# Kill the process
sudo kill -9 <PID>
```

### Can't access from browser
```bash
# Open firewall
sudo ufw allow 8100/tcp
sudo ufw allow 3200/tcp
sudo ufw reload
```

## Success Checklist

- ✅ All containers running: `docker-compose ps`
- ✅ Backend healthy: `curl http://localhost:8100/api/v1/health`
- ✅ Frontend loads: `http://YOUR_IP:3200`
- ✅ API docs accessible: `http://YOUR_IP:8100/docs`
- ✅ No errors in logs: `docker-compose logs`

## What You Get

✅ **Modern UI** - Dashboard, Request Form, Module Catalog
✅ **REST API** - Complete backend with FastAPI
✅ **5 Modules** - VPC, EC2, S3, ALB, Security Group
✅ **Demo Mode** - Works without AWS credentials
✅ **API Docs** - Interactive Swagger documentation

## Next Steps

1. ✅ Deploy (you're here!)
2. 📊 Browse dashboard at http://YOUR_IP:3200
3. 🔍 Check modules at http://YOUR_IP:3200/modules
4. ➕ Create request at http://YOUR_IP:3200/new-request
5. 📖 Read API docs at http://YOUR_IP:8100/docs

---

**Need help?** Check `FRONTEND_UPDATES.md` for detailed information.
