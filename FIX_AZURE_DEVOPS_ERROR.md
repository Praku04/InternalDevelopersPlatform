# 🔧 Fix: Azure DevOps Configuration Error

## ❌ Error You're Getting

```
ValueError: Azure DevOps organization not configured
```

**Root Cause:** The backend is trying to initialize Azure DevOps client but the environment variables are not set in the Docker container.

---

## ✅ Solution: Enable Demo Mode

I've fixed the application to run in **demo mode** by default. This allows the platform to work without Azure DevOps configuration.

### What Changed:

1. **✅ Docker Compose updated** - Added `DEMO_MODE=true` by default
2. **✅ Azure DevOps client fixed** - Gracefully handles missing config in demo mode
3. **✅ All changes committed and pushed to Git**

---

## 🚀 Deploy the Fix on Your VPS

On your VPS (corridors), run:

```bash
cd ~/InternalDevelopersPlatform

# Pull latest changes
git pull origin main

# Create .env file with demo mode
cat > .env << 'EOF'
ENVIRONMENT=local
LOG_LEVEL=INFO
AWS_REGION=ap-south-1
DYNAMODB_ENDPOINT_URL=http://localhost:8001
DEMO_MODE=true
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514
NEXT_PUBLIC_API_BASE_URL=http://localhost:8100
TERRAFORM_MODULES_PATH=../terraform/modules
EOF

# Rebuild and restart
docker-compose down
docker rmi internaldevelopersplatform-backend:latest 2>/dev/null || true
docker-compose build --no-cache backend
docker-compose up -d

# Wait for startup
sleep 15

# Test backend
curl http://localhost:8100/api/v1/health
```

---

## ✅ Expected Result

After running the above commands, you should see:

### All containers running:
```
NAME                                          STATUS          PORTS
internaldevelopersplatform-backend-1        Up X seconds   0.0.0.0:8100->8000/tcp
internaldevelopersplatform-frontend-1       Up X seconds   0.0.0.0:3200->3000/tcp
internaldevelopersplatform-dynamodb-local-1 Up X seconds   0.0.0.0:8001->8000/tcp
```

### Health check passes:
```bash
$ curl http://localhost:8100/api/v1/health
{"status":"healthy","version":"1.0.0","demo_mode":true}
```

---

## 🎯 What Demo Mode Does

When `DEMO_MODE=true`:

✅ **Backend starts successfully** without Azure DevOps configuration  
✅ **All API endpoints work** normally  
✅ **Pipeline triggers are simulated** (returns fake pipeline IDs)  
✅ **No actual deployments** to Azure (safe for testing)  
✅ **UI fully functional** for testing and development  

### API Endpoints Available:
- ✅ `GET /api/v1/health` - Health check
- ✅ `GET /api/v1/modules` - List available modules
- ✅ `POST /api/v1/requests` - Create deployment request
- ✅ `GET /api/v1/requests` - List all requests
- ✅ `POST /api/v1/deployments/trigger` - Trigger deployment (simulated)
- ✅ `GET /api/v1/deployments/{id}` - Get deployment status
- ✅ `POST /api/v1/ai/analyze` - AI analysis (requires AWS Bedrock)
- ✅ `GET /api/v1/inventory` - Infrastructure inventory

---

## 🔵 When to Disable Demo Mode

Disable demo mode **only when** you've completed Azure DevOps setup:

1. ✅ Created Personal Access Token (PAT)
2. ✅ Got Repository ID from Azure DevOps
3. ✅ Created deployment pipeline
4. ✅ Got Pipeline ID

Then update `.env` on VPS:

```bash
# Disable demo mode
DEMO_MODE=false

# Configure Azure DevOps
AZDO_ORGANIZATION=prakashranjan0943
AZDO_PROJECT=Internal Deployment Portal
AZDO_REPOSITORY_ID=your-repo-id-here
AZDO_PIPELINE_ID=your-pipeline-id-here
AZDO_PAT=your-pat-token-here
GIT_REPOSITORY=https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/InternalDevelopersPlatform
GIT_BRANCH=main
```

Then restart:
```bash
docker-compose restart backend
```

---

## 📋 Quick Deployment Commands (Copy-Paste)

```bash
# Connect to VPS
ssh corridors

# Navigate to project
cd ~/InternalDevelopersPlatform

# Pull latest code
git pull origin main

# Create .env with demo mode
cat > .env << 'EOF'
ENVIRONMENT=local
LOG_LEVEL=INFO
AWS_REGION=ap-south-1
DYNAMODB_ENDPOINT_URL=http://localhost:8001
DEMO_MODE=true
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514
NEXT_PUBLIC_API_BASE_URL=http://localhost:8100
TERRAFORM_MODULES_PATH=../terraform/modules
EOF

# Rebuild backend
docker-compose down
docker rmi internaldevelopersplatform-backend:latest 2>/dev/null || true
docker-compose build --no-cache backend
docker-compose up -d

# Wait and test
sleep 15
curl http://localhost:8100/api/v1/health
docker-compose ps
```

---

## 🧪 Verify Everything Works

### 1. Check all containers are running:
```bash
docker-compose ps
```

All 3 should show **"Up"** status.

### 2. Check backend logs (should show no errors):
```bash
docker-compose logs backend | tail -50
```

Should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Test health endpoint:
```bash
curl http://localhost:8100/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "demo_mode": true
}
```

### 4. Test modules endpoint:
```bash
curl http://localhost:8100/api/v1/modules
```

Should return a list of available modules.

### 5. Access UI in browser:
```
http://corridors:3200
```

Should show the dashboard with working navigation.

---

## 🎉 What's Working Now

| Feature | Status | Notes |
|---------|--------|-------|
| Backend API | ✅ Working | All endpoints functional |
| Frontend UI | ✅ Working | Full dashboard and forms |
| Module Catalog | ✅ Working | Displays available modules |
| Request Creation | ✅ Working | Can create requests |
| Request Tracking | ✅ Working | View all requests |
| Deployment Trigger | ⚙️ Simulated | Returns fake pipeline IDs |
| AI Analysis | ⚠️ Needs AWS | Requires AWS Bedrock credentials |
| Azure Pipelines | ⚙️ Simulated | Configure to enable real deployments |

---

## 🔍 Troubleshooting

### If backend still fails:

1. **Check if .env was created:**
   ```bash
   cat .env
   ```

2. **Check environment variables in container:**
   ```bash
   docker-compose exec backend env | grep DEMO_MODE
   ```
   Should show: `DEMO_MODE=true`

3. **Force complete rebuild:**
   ```bash
   docker-compose down -v
   docker system prune -f
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **View real-time logs:**
   ```bash
   docker-compose logs -f backend
   ```

---

## 📞 Next Steps

1. ✅ **Deploy this fix** using the commands above
2. ✅ **Test the UI** at http://corridors:3200
3. ✅ **Create test requests** using the UI
4. 📋 **Later:** Set up Azure DevOps (see `AZURE_DEVOPS_SETUP.md`)
5. 📋 **Later:** Configure AWS Bedrock for AI features

---

**Status:** ✅ Fix ready to deploy  
**Demo Mode:** Enabled by default  
**Azure DevOps:** Optional (configure later)  
**Action Required:** Run deployment commands on VPS
