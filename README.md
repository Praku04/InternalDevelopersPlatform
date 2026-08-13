# AI-Powered Multi-Cloud Self-Service Infrastructure Platform

An enterprise-grade, AI-powered self-service infrastructure platform supporting **AWS, Azure, and GCP** with comprehensive security controls, approval workflows, and Azure DevOps CI/CD integration.

**Core principle:** AI searches existing Terraform modules FIRST before generating new code, enforcing security policies, and requiring appropriate approvals—all without direct access to infrastructure execution.

## 🌟 Key Features

- **🤖 AI-Powered**: Natural language infrastructure requests using Amazon Bedrock
- **☁️ Multi-Cloud**: Support for AWS, Azure, and GCP through provider abstraction
- **🔒 Security First**: 6 layers of security validation before deployment
- **♻️ Module Reuse**: Intelligent module discovery prevents code duplication
- **✅ Smart Approvals**: Risk-based approval workflows (DEV/UAT/PROD)
- **🔐 Zero Trust**: AI cannot execute Terraform, AWS CLI, or bypass approvals
- **📊 Complete Audit**: Full traceability from request to cloud resource
- **🚀 Azure DevOps Native**: Full CI/CD integration with approval gates

## Status: Active Development

**AWS**: Production-ready ✅
**Azure**: Architecture complete, ready for module development 🔜
**GCP**: Architecture complete, ready for module development 🔜

Foundation complete. Implementing full end-to-end deployment workflow with multi-cloud support, AI orchestration, security scanning, and approval workflows.

## Repository layout

```
frontend/        Next.js + TypeScript + Tailwind portal
backend/          FastAPI + Pydantic backend
ai/               Prompts, tool schemas, guardrails, knowledge base
terraform/        Approved module registry (vpc, ec2, security-group, alb, s3, rds) + environments + generated configs
azure-devops/     Pipelines, templates, environment definitions for CI/CD
security/         Checkov/Trivy configs and IAM policies
infrastructure/   Platform's own AWS infra (DynamoDB, IAM, S3, KMS, EventBridge, Step Functions)
docs/             Architecture, security, API, operations, and Azure DevOps documentation
scripts/          Deployment and utility scripts
```

## Quick start

```bash
# Backend
cd backend
pip install -r requirements.txt --break-system-packages
pytest -v
uvicorn app.main:app --reload --port 8000

# Frontend (separate shell)
cd frontend
npm install
npm run dev
```

Or via Docker Compose: `cp .env.example .env && docker compose up --build`.

See [`docs/development/setup.md`](docs/development/setup.md) for details.

## Security principle

Amazon Bedrock is an orchestration/recommendation layer only. It never
receives credentials capable of `terraform apply`/`destroy`, arbitrary AWS
CLI, IAM changes, or approval bypass. See
[`ai/guardrails/ai_guardrails.md`](ai/guardrails/ai_guardrails.md) and
[`docs/security/iam.md`](docs/security/iam.md).

## Documentation

- [Architecture overview](docs/architecture/overview.md)
- [AI flow](docs/architecture/ai-flow.md)
- [Deployment flow](docs/architecture/deployment-flow.md)
- [Azure DevOps setup](docs/azure-devops/setup.md)
- [Azure DevOps pipelines](docs/azure-devops/pipelines.md)
- [Azure DevOps approvals](docs/azure-devops/approvals.md)
- [AWS authentication (OIDC)](docs/azure-devops/aws-federation.md)
- [Security policies](docs/security/policies.md)
- [IAM architecture](docs/security/iam.md)
- [Checkov integration](docs/security/checkov.md)
- [API reference](docs/api/api-reference.md)
- [Terraform module development](docs/terraform/module-development.md)
- [Terraform standards](docs/terraform/standards.md)
- [Local development setup](docs/development/setup.md)
- [Operations runbook](docs/operations/runbook.md)
