# 🔐 Get Azure DevOps Values - Step by Step

You need to get 3 values from Azure DevOps to complete the configuration.

---

## ✅ What We Already Have

```
✅ AZDO_ORGANIZATION = prakashranjan0943
✅ AZDO_PROJECT = Internal Deployment Portal
✅ GIT_REPOSITORY = https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/Internal%20Deployment%20Portal
```

---

## 🔑 Step 1: Create Personal Access Token (PAT)

### 1.1 Go to Token Creation Page
Open this URL in your browser:
```
https://dev.azure.com/prakashranjan0943/_usersSettings/tokens
```

### 1.2 Click "+ New Token"

### 1.3 Configure the Token
- **Name:** `InternalDevPortal-API`
- **Organization:** `prakashranjan0943`
- **Expiration:** 90 days (recommended) or Custom
- **Scopes:** Click "Show all scopes" and select:
  - ✅ **Build** → Read & execute
  - ✅ **Code** → Read & write
  - ✅ **Release** → Read, write & execute
  - ✅ **Project and Team** → Read

### 1.4 Click "Create"

### 1.5 COPY THE TOKEN IMMEDIATELY
⚠️ **IMPORTANT:** You will only see this token once!

Copy it and save it as:
```
AZDO_PAT=<paste_your_token_here>
```

---

## 📁 Step 2: Get Repository ID

### 2.1 Go to Your Repository
Open this URL:
```
https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/Internal%20Deployment%20Portal
```

### 2.2 Method A: From Repository Settings (Easiest)

1. Click on **"Project Settings"** (gear icon in bottom left)
2. Under **"Repos"**, click **"Repositories"**
3. Click on **"Internal Deployment Portal"**
4. Look for **"Repository ID"** - it's a GUID like: `12345678-1234-1234-1234-123456789abc`
5. Copy this GUID

### 2.3 Method B: From URL (Alternative)

1. Go to repository: https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/Internal%20Deployment%20Portal
2. Click on **"Branches"**
3. Look at the URL - it contains the repository ID:
   ```
   https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/Internal%20Deployment%20Portal/branches?_a=all
   ```
4. Or use Azure DevOps REST API:
   ```bash
   curl -u :YOUR_PAT_TOKEN https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_apis/git/repositories?api-version=7.1
   ```

### 2.4 Method C: Use PowerShell (Quick)

Run this command (after you have your PAT):
```powershell
$pat = "YOUR_PAT_TOKEN_HERE"
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$pat"))
$headers = @{Authorization = "Basic $base64"}
$response = Invoke-RestMethod -Uri "https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_apis/git/repositories?api-version=7.1" -Headers $headers
$response.value | Where-Object {$_.name -eq "Internal Deployment Portal"} | Select-Object id, name
```

Save the ID as:
```
AZDO_REPOSITORY_ID=<paste_repository_id_here>
```

---

## 🔧 Step 3: Create Deployment Pipeline (Optional for Now)

You can skip this for now and use `AZDO_PIPELINE_ID=1` as a placeholder.

### When You're Ready to Create the Pipeline:

1. Go to: https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_build

2. Click **"New pipeline"**

3. Select **"Azure Repos Git"**

4. Select repository: **"Internal Deployment Portal"**

5. Choose **"Existing Azure Pipelines YAML file"**

6. Select path: `/azure-devops/pipelines/deployment.yml`

7. Click **"Save"** (don't run yet)

8. Note the Pipeline ID from the URL:
   ```
   https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_build?definitionId=<PIPELINE_ID>
   ```

For now, you can use:
```
AZDO_PIPELINE_ID=1
```

---

## 📝 Your Complete .env File

Once you have the values, create `.env` on your VPS:

```bash
# On your VPS
cd ~/InternalDevelopersPlatform

cat > .env << 'EOF'
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DEMO_MODE=false

# AWS
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514
DYNAMODB_ENDPOINT_URL=http://dynamodb-local:8000

# Azure DevOps
AZDO_ORGANIZATION=prakashranjan0943
AZDO_PROJECT=Internal Deployment Portal
AZDO_REPOSITORY_ID=<PASTE_REPOSITORY_ID_HERE>
AZDO_PIPELINE_ID=1
AZDO_PAT=<PASTE_YOUR_PAT_HERE>

# Git
GIT_REPOSITORY=https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/Internal%20Deployment%20Portal
GIT_BRANCH=main

# Backend
BACKEND_API_URL=http://corridors:8100
TERRAFORM_MODULES_PATH=/terraform-modules

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8100
EOF
```

---

## ✅ Quick Checklist

Fill in these values:

### Required Now:
- [ ] **AZDO_PAT** - Personal Access Token (from Step 1)
- [ ] **AZDO_REPOSITORY_ID** - Repository GUID (from Step 2)

### Optional (can use placeholder):
- [ ] **AZDO_PIPELINE_ID** - Can use `1` for now (from Step 3)

---

## 🚀 After You Have the Values

1. **Create .env on VPS** with the values above

2. **Deploy:**
   ```bash
   cd ~/InternalDevelopersPlatform
   git pull origin main
   docker-compose down
   docker-compose build --no-cache backend
   docker-compose up -d
   sleep 15
   curl http://localhost:8100/api/v1/health
   ```

3. **Verify:**
   ```bash
   docker-compose ps
   # All 3 containers should be "Up"
   
   docker-compose logs backend | grep -i azure
   # Should show Azure DevOps configuration
   ```

---

## 🔍 Test Azure DevOps Connection

Once deployed, test the connection:

```bash
# Test health with Azure DevOps info
curl http://localhost:8100/api/v1/ai/health

# Should return:
{
  "status": "healthy",
  "bedrock_configured": true,
  "demo_mode": false,
  "azure_devops": "configured"
}
```

---

## 🐛 If PAT is Invalid

You'll see error in logs:
```
Azure DevOps API: 401 Unauthorized
```

**Solution:**
1. Create a new PAT with correct scopes
2. Update `.env` with new PAT
3. Restart: `docker-compose restart backend`

---

## 📞 Need Help?

If you get stuck at any step, share:
1. Which step you're on
2. Any error messages you see
3. Screenshot (if helpful)

---

**Next:** Get your PAT from Step 1, then your Repository ID from Step 2, and we'll create the `.env` file!
