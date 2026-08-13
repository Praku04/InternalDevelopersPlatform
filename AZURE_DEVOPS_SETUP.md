# 🔵 Azure DevOps Setup Guide

## Your Azure DevOps Organization

**Organization URL:** `https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal`  
**Organization Name:** `prakashranjan0943`  
**Project Name:** `Internal Deployment Portal`

---

## 📋 Prerequisites

Before setting up the CI/CD pipelines, you need:

1. ✅ Access to Azure DevOps organization
2. ✅ Repository created in the project
3. ⚙️ Personal Access Token (PAT) with permissions
4. ⚙️ Azure DevOps Pipeline created

---

## 🔐 Step 1: Create Personal Access Token (PAT)

1. Go to: https://dev.azure.com/prakashranjan0943/_usersSettings/tokens

2. Click **"+ New Token"**

3. Configure the token:
   - **Name:** `InternalDevelopersPlatform-API`
   - **Organization:** `prakashranjan0943`
   - **Expiration:** 90 days (or custom)
   - **Scopes:** Custom defined
     - ✅ **Build** → Read & execute
     - ✅ **Code** → Read & write
     - ✅ **Release** → Read, write & execute
     - ✅ **Project and Team** → Read

4. Click **Create** and **copy the token** (you won't see it again!)

5. Save it securely - you'll need it for the `.env` file

---

## 📁 Step 2: Create Repository

1. Go to: https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git

2. If no repository exists:
   - Click **"+ New repository"**
   - **Name:** `InternalDevelopersPlatform`
   - **Type:** Git
   - Click **Create**

3. Get the Repository ID:
   - Go to repository settings
   - Copy the **Repository ID** (GUID format)
   - Save it for configuration

**Alternative:** Use your existing GitHub repository and set up a mirror to Azure DevOps

---

## 🔧 Step 3: Configure Environment Variables

### Option A: Local Development

Create a `.env` file in the project root:

```bash
cd ~/InternalDevelopersPlatform
cp .env.example .env
nano .env
```

Update these values:

```bash
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DEMO_MODE=false

# AWS Configuration
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514

# Azure DevOps Configuration
AZDO_ORGANIZATION=prakashranjan0943
AZDO_PROJECT=Internal Deployment Portal
AZDO_REPOSITORY_ID=your-repo-id-here  # Get from Step 2
AZDO_PIPELINE_ID=1  # Get from Step 4
AZDO_PAT=your-pat-token-here  # From Step 1

# Git Configuration
GIT_REPOSITORY=https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/InternalDevelopersPlatform
GIT_BRANCH=main

# Backend API URL (use your VPS IP or domain)
BACKEND_API_URL=http://corridors:8100

# DynamoDB
DYNAMODB_ENDPOINT_URL=http://localhost:8001

# S3 Configuration (when you set up AWS)
S3_BUCKET=internal-dev-portal-artifacts
S3_TFSTATE_BUCKET=internal-dev-portal-tfstate
DYNAMODB_LOCK_TABLE=internal-dev-portal-tfstate-lock
```

### Option B: Docker Environment Variables

Update `docker-compose.yml` to add Azure DevOps configuration:

```yaml
services:
  backend:
    environment:
      - AZDO_ORGANIZATION=prakashranjan0943
      - AZDO_PROJECT=Internal Deployment Portal
      - AZDO_REPOSITORY_ID=${AZDO_REPOSITORY_ID}
      - AZDO_PIPELINE_ID=${AZDO_PIPELINE_ID}
      - AZDO_PAT=${AZDO_PAT}
```

---

## 🚀 Step 4: Create Deployment Pipeline

### 4.1 Upload Pipeline YAML

1. Go to: https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/InternalDevelopersPlatform

2. Navigate to `azure-devops/pipelines/`

3. Push the `deployment.yml` file to your repository:
   ```bash
   git add azure-devops/
   git commit -m "Add Azure DevOps deployment pipeline"
   git push
   ```

### 4.2 Create Pipeline in Azure DevOps

1. Go to: https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_build

2. Click **"New pipeline"**

3. Select **"Azure Repos Git"** (or **"GitHub"** if using GitHub mirror)

4. Select your repository: `InternalDevelopersPlatform`

5. Choose **"Existing Azure Pipelines YAML file"**

6. Select the path: `/azure-devops/pipelines/deployment.yml`

7. Click **"Continue"**

8. Review the pipeline and click **"Save"** (don't run yet)

9. **Note the Pipeline ID:**
   - Look at the URL: `https://dev.azure.com/.../pipelines/{PIPELINE_ID}/...`
   - Copy the ID number
   - Update your `.env` file: `AZDO_PIPELINE_ID={PIPELINE_ID}`

---

## 🔗 Step 5: Configure Service Connections (Optional for AWS)

If you want to deploy to AWS, set up a service connection:

1. Go to: https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_settings/adminservices

2. Click **"New service connection"**

3. Select **"AWS for Terraform"** or **"AWS"**

4. Configure:
   - **Connection name:** `AWS-Production`
   - **Access Key ID:** (from AWS IAM)
   - **Secret Access Key:** (from AWS IAM)
   - **Region:** `ap-south-1`

5. Click **Save**

---

## 🧪 Step 6: Test the Setup

### Test 1: Check Configuration

```bash
cd ~/InternalDevelopersPlatform
docker-compose restart backend
docker-compose logs backend | grep -i "azure"
```

Should see: `Azure DevOps configured: prakashranjan0943/Internal Deployment Portal`

### Test 2: Test API Health with Azure DevOps

```bash
curl http://localhost:8100/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "azure_devops": "configured"
}
```

### Test 3: Test Pipeline Trigger (Demo Mode)

```bash
curl -X POST http://localhost:8100/api/v1/deployments/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-123"
  }'
```

If `DEMO_MODE=true`, should return simulated pipeline response.

---

## 📊 Current Configuration Status

Update your `.env.example` and `.env` files:

```bash
# Already updated in .env.example:
✅ AZDO_ORGANIZATION=prakashranjan0943
✅ AZDO_PROJECT=Internal Deployment Portal
✅ GIT_REPOSITORY=https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/InternalDevelopersPlatform

# You need to add:
⚙️ AZDO_REPOSITORY_ID=<from Step 2>
⚙️ AZDO_PIPELINE_ID=<from Step 4>
⚙️ AZDO_PAT=<from Step 1>
```

---

## 🔐 Security Best Practices

### For Production:

1. **Never commit PAT to Git:**
   - The `.env` file is in `.gitignore`
   - Use environment variables or AWS Secrets Manager

2. **Use AWS Secrets Manager for PAT:**
   ```python
   import boto3
   
   def get_azdo_pat():
       client = boto3.client('secretsmanager', region_name='ap-south-1')
       response = client.get_secret_value(SecretId='azdo/pat')
       return response['SecretString']
   ```

3. **Rotate PAT regularly:**
   - Set expiration to 90 days
   - Create new token before expiration
   - Update in Secrets Manager

4. **Use Azure DevOps Variable Groups:**
   - Store sensitive variables in Azure DevOps
   - Reference in pipelines with `${{ variables.VARIABLE_NAME }}`

---

## 📝 Pipeline Workflow

Once configured, the deployment workflow:

1. **User creates request** via UI → Backend API
2. **Backend generates Terraform** code
3. **Backend triggers Azure DevOps pipeline** with request parameters
4. **Pipeline executes:**
   - ✅ Validate Terraform syntax
   - ✅ Security scan (Checkov)
   - ✅ Generate plan
   - ✅ Manual approval (optional)
   - ✅ Apply infrastructure changes
   - ✅ Update backend with status
5. **User views deployment status** in UI

---

## 🐛 Troubleshooting

### Issue: "Azure DevOps organization not configured"

**Solution:** Check `.env` file has:
```bash
AZDO_ORGANIZATION=prakashranjan0943
```

### Issue: "Azure DevOps PAT not configured"

**Solution:** Add PAT to `.env`:
```bash
AZDO_PAT=your-token-here
```

Or enable demo mode:
```bash
DEMO_MODE=true
```

### Issue: "Pipeline trigger failed: 401 Unauthorized"

**Solution:** 
1. Verify PAT is correct
2. Check PAT hasn't expired
3. Verify PAT has required permissions (Build: Read & execute)

### Issue: "Repository ID not found"

**Solution:**
1. Go to Azure DevOps repository settings
2. Copy the Repository GUID
3. Add to `.env`: `AZDO_REPOSITORY_ID=<guid>`

---

## 📚 Useful Links

- **Your Organization:** https://dev.azure.com/prakashranjan0943
- **Your Project:** https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal
- **Pipelines:** https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_build
- **Repos:** https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git
- **Token Management:** https://dev.azure.com/prakashranjan0943/_usersSettings/tokens
- **Service Connections:** https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_settings/adminservices

---

## ✅ Next Steps

1. [ ] Create Personal Access Token (Step 1)
2. [ ] Get Repository ID (Step 2)
3. [ ] Configure `.env` file (Step 3)
4. [ ] Create deployment pipeline (Step 4)
5. [ ] Test configuration (Step 6)
6. [ ] Deploy on VPS with new configuration

**Once complete, restart your backend:**
```bash
cd ~/InternalDevelopersPlatform
docker-compose restart backend
```

---

**Status:** Azure DevOps organization configured  
**Organization:** `prakashranjan0943`  
**Project:** `Internal Deployment Portal`  
**Ready for:** Pipeline creation and PAT setup
