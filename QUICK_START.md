# Quick Start Guide
## AI-Powered AWS Self-Service Infrastructure Platform

Get the platform running locally in 5 minutes.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

---

## 🚀 Quick Start (Local Development)

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd SelfServicePortal

# Copy environment file
cp .env.example .env

# Edit .env with your settings (optional for demo mode)
```

### 2. Start with Docker Compose (Easiest)

```bash
# Build and start all services
docker compose up --build

# Services will be available at:
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

### 3. Or Run Locally

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 4. Access the Platform

- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/api/v1/health

---

## 📝 Quick Test

### Test 1: Check Health

```bash
curl http://localhost:8000/api/v1/health | jq
```

Expected: `{"status": "healthy"}`

### Test 2: List Modules

```bash
curl http://localhost:8000/api/v1/modules | jq
```

Expected: List of 5 approved modules (VPC, EC2, Security Group, ALB, S3)

### Test 3: AI Analysis (Demo Mode)

```bash
curl -X POST http://localhost:8000/api/v1/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create two EC2 instances for my payment app in dev",
    "application": "payment",
    "environment": "dev"
  }' | jq
```

Expected: AI recommendation with module matches

### Test 4: Create Deployment Request

```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ-TEST001",
    "source": "self_service",
    "user_id": "test-user",
    "application": "payment",
    "environment": "dev",
    "region": "ap-south-1",
    "resources": [
      {
        "type": "ec2",
        "module": "ec2",
        "version": "1.0.0",
        "action": "reuse",
        "configuration": {
          "instance_type": "t3.micro",
          "instance_count": 2
        }
      }
    ]
  }' | jq
```

Expected: Created request with ID

---

## 🛠️ Using Makefile Commands

### Installation
```bash
make install              # Install all dependencies
make backend-install      # Install backend only
make frontend-install     # Install frontend only
```

### Development
```bash
make backend-run          # Run backend server
make frontend-dev         # Run frontend dev server
make dev                  # Run both (parallel)
```

### Testing
```bash
make test                 # Run all tests
make backend-test         # Backend tests only
make frontend-test        # Frontend tests only
```

### Code Quality
```bash
make lint                 # Run linters
make format               # Format code
make security             # Run security scans
```

### Terraform
```bash
make terraform-fmt        # Format Terraform
make terraform-validate   # Validate modules
```

### Utilities
```bash
make clean                # Clean build artifacts
make docker-up            # Start Docker services
make docker-down          # Stop Docker services
make docker-logs          # View logs
```

---

## 🔧 Configuration

### Demo Mode (Default)

The platform runs in demo mode by default:
- No real AWS calls
- No real Azure DevOps calls
- Simulated responses for testing

```bash
# In .env
DEMO_MODE=true
```

### Production Mode

To connect to real services:

```bash
# In .env
DEMO_MODE=false

# AWS Configuration
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514

# Azure DevOps
AZDO_ORGANIZATION=your-org
AZDO_PROJECT=AI-Cloud-Self-Service
AZDO_PIPELINE_ID=1
AZDO_PAT=<your-pat>

# State Management
S3_TFSTATE_BUCKET=ai-cloud-platform-tfstate
DYNAMODB_LOCK_TABLE=ai-cloud-platform-tfstate-lock
```

---

## 📚 Next Steps

### Explore API
Visit http://localhost:8000/docs for interactive API documentation

### Read Documentation
- [Architecture Overview](docs/architecture/overview.md)
- [Azure DevOps Setup](docs/azure-devops/setup.md)
- [Security Policy](security/policies/security-policy.md)
- [API Reference](docs/api/api-reference.md)

### Test Workflows

**1. Self-Service Flow:**
```
Create Request → Generate Terraform → Validate → Security Scan → Plan → Approve → Deploy
```

**2. AI Flow:**
```
Natural Language → AI Analysis → Module Discovery → Create Request → Deploy
```

**3. Approval Flow:**
```
Create Workflow → Pending Approvals → Approve/Reject → Can Deploy?
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
cd backend
pip install -r requirements.txt --force-reinstall

# Check for port conflicts
lsof -i :8000  # Kill any process using port 8000
```

### Frontend Won't Start

```bash
# Check Node version
node --version  # Should be 18+

# Clean and reinstall
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

### Database Connection Issues

```bash
# Restart Docker Compose
docker compose down
docker compose up -d

# Check DynamoDB Local
curl http://localhost:8001
```

### Tests Failing

```bash
# Run with verbose output
cd backend
pytest -v --tb=short

# Run specific test
pytest tests/test_api.py -v
```

---

## 📞 Get Help

- **Documentation**: `/docs` directory
- **API Docs**: http://localhost:8000/docs
- **Issues**: Check logs with `docker compose logs -f`
- **Health Check**: `curl http://localhost:8000/api/v1/health`

---

## 🎯 Common Tasks

### Create a New Module

```bash
# Using make command
make generate-module NAME=lambda

# Or manually
mkdir -p terraform/modules/lambda
cd terraform/modules/lambda
# Create: main.tf, variables.tf, outputs.tf, versions.tf, README.md, module.json
```

### Run Security Scan

```bash
# Checkov
make security-checkov

# Trivy
make security-trivy

# Both
make security
```

### Validate Everything

```bash
make validate-all
```

### Deploy to Dev (Placeholder)

```bash
# Will use Azure DevOps in production
make deploy-dev
```

---

## ✅ Verification Checklist

After quick start, verify:

- [ ] Backend running on :8000
- [ ] Frontend running on :3000
- [ ] API docs accessible
- [ ] Health check returns healthy
- [ ] Modules endpoint returns 5 modules
- [ ] AI analysis works (demo mode)
- [ ] Request creation works
- [ ] Tests pass

---

## 🎉 Success!

You now have a running instance of the AI-Powered AWS Self-Service Infrastructure Platform!

**Next:**
1. Explore API docs at http://localhost:8000/docs
2. Read [FINAL_IMPLEMENTATION_STATUS.md](FINAL_IMPLEMENTATION_STATUS.md) for complete feature list
3. Review [docs/architecture/complete-flow.md](docs/architecture/complete-flow.md) for architecture
4. Configure AWS and Azure DevOps for production deployment
