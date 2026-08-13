# Temporary Fix to Get Backend Running

The backend has import issues due to missing/mismatched classes. Here's a quick fix to get it running:

## Quick Fix: Comment Out Problematic Routes

On your VPS, edit these files:

### 1. Edit main.py

```bash
nano ~/InternalDevelopersPlatform/backend/app/main.py
```

Find this line (around line 14):
```python
from app.api import health, modules, requests, terraform, deployments, approvals, ai, inventory
```

Change to (comment out problematic imports):
```python
from app.api import health, modules, requests  # terraform, deployments, approvals, ai, inventory
```

Find where routers are included (around line 35-40):
```python
app.include_router(health.router, tags=["health"])
app.include_router(modules.router, prefix="/api/v1/modules", tags=["modules"])
app.include_router(requests.router, prefix="/api/v1/requests", tags=["requests"])
# app.include_router(terraform.router, prefix="/api/v1/terraform", tags=["terraform"])
# app.include_router(deployments.router, prefix="/api/v1/deployments", tags=["deployments"])
# app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])
# app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
# app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])
```

Save: Ctrl+X, Y, Enter

### 2. Rebuild and Restart

```bash
cd ~/InternalDevelopersPlatform
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
sleep 10
docker-compose ps
curl http://localhost:8100/api/v1/health
```

## What This Does

This will start the backend with only the essential endpoints:
- ✅ `/api/v1/health` - Health check
- ✅ `/api/v1/modules` - List modules
- ✅ `/api/v1/requests` - Create/list requests

The frontend will work with these three endpoints for basic functionality.

## Test After Fix

```bash
# Health check
curl http://localhost:8100/api/v1/health

# List modules
curl http://localhost:8100/api/v1/modules

# Access frontend
# http://YOUR_VPS_IP:3200
```

## To Fix Properly Later

The proper fix requires:
1. Creating missing TerraformGenerator class
2. Fixing DeploymentRequest references throughout
3. Implementing missing models

But for now, this gets your platform running!
