# Complete End-to-End Deployment Flow

## Overview

This document describes the complete deployment flow from user request through AWS resource creation.

## Deployment Flow Diagram

```
┌─────────────────────────┐
│       USER PORTAL       │
│ Self Service | AI Chat  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     FastAPI Backend     │
│   - Request Validation  │
│   - Policy Check        │
│   - Module Discovery    │
└────────────┬────────────┘
             │
    ┌────────┴─────────┐
    │                  │
    ▼                  ▼
┌─────────┐     ┌──────────────┐
│ Bedrock │     │   DynamoDB   │
│   AI    │     │ (Requests)   │
└────┬────┘     └──────────────┘
     │
     ▼
┌──────────────────────┐
│  MODULE REGISTRY     │
│  - Search modules    │
│  - Match capabilities│
└────────┬─────────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
REUSE      GENERATE
MODULE      MODULE
    │          │
    │          ├─→ Git Branch
    │          ├─→ Azure DevOps PR
    │          └─→ Manual Review
    │
    └────┬─────┘
         │
         ▼
┌──────────────────────┐
│ Terraform Generator  │
│ - Compose modules    │
│ - Generate config    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Azure DevOps Pipeline│
└────────┬─────────────┘
         │
         ├─→ Terraform Validate
         ├─→ Checkov (security)
         ├─→ Trivy (vulnerabilities)
         ├─→ Terraform Plan
         ├─→ Cost Estimation
         ├─→ Approval (environment-based)
         ├─→ Terraform Apply
         │
         ▼
┌──────────────────────┐
│         AWS          │
│   (via IAM Role)     │
└────────┬─────────────┘
         │
         ├─→ Post Deployment Validation
         ├─→ Resource Inventory Update
         ├─→ Audit Log
         │
         ▼
┌──────────────────────┐
│      Dashboard       │
│  - Status Update     │
│  - Resources         │
│  - Security Status   │
└──────────────────────┘
```

## Two Entry Points

### 1. Self-Service Form
```
User fills form:
  Application: payment
  Environment: DEV
  Instance Type: t3.micro
  Count: 2
  EBS Encryption: YES
  Monitoring: YES

↓
POST /api/v1/requests
{
  "application_name": "payment",
  "environment": "dev",
  "resources": [
    {
      "type": "ec2",
      "properties": {
        "instance_type": "t3.micro",
        "instance_count": 2,
        "ebs_encrypted": true,
        "monitoring": true
      }
    }
  ]
}
```

### 2. Natural Language (AI)
```
User: "Create two EC2 servers for payment app in dev with encrypted EBS"

↓
Bedrock AI:
  - Extracts requirements
  - Searches module registry
  - Validates security policies
  - Generates deployment specification

↓
Same DeploymentSpecification format as form
```

## Critical Security Controls

### 1. AI Guardrails
- **NO** direct `terraform apply`
- **NO** direct `terraform destroy`
- **NO** AWS CLI execution
- **NO** IAM modification
- **NO** approval bypass

AI only generates structured requests that flow through controlled pipelines.

### 2. Approval Gates

| Environment | Approvers Required |
|-------------|-------------------|
| DEV | Security policy pass |
| UAT | Team Lead + Security |
| PROD | Manager + Security + Platform Admin |

### 3. Security Scanning
All deployments must pass:
- Checkov policy validation
- Trivy vulnerability scan
- Custom policy checks
- No critical violations allowed

## Module Discovery Logic

```python
def find_module(requirements):
    # 1. Search module registry
    matches = search_modules(requirements.capabilities)
    
    # 2. Score matches
    for match in matches:
        score = calculate_compatibility(requirements, match)
    
    # 3. Decision
    if best_match.score >= 0.9:
        return "REUSE", best_match
    elif best_match.score >= 0.7:
        return "NEEDS_REVIEW", best_match
    else:
        return "GENERATE", None
```

## Terraform Workspace Isolation

Each deployment request gets isolated workspace:
```
terraform/generated/
  ├── REQ-10001/
  │   ├── main.tf
  │   ├── variables.tf
  │   ├── terraform.tfvars
  │   ├── versions.tf
  │   └── outputs.tf
  ├── REQ-10002/
  └── ...
```

Never modify approved module source during deployment.

## State Management

```
S3 Backend:
  Bucket: ai-cloud-platform-tfstate-<account>
  Key: deployments/<environment>/<request-id>/terraform.tfstate
  Encrypt: YES
  Locking: DynamoDB table

Separate states for:
  - DEV environment
  - UAT environment
  - PROD environment
  - Per-request isolation
```

## Azure DevOps → AWS Authentication

Using OIDC/Workload Identity Federation (NO permanent keys):

```
Azure DevOps Pipeline
  ↓
Azure DevOps Service Connection (OIDC)
  ↓
AWS STS AssumeRoleWithWebIdentity
  ↓
Assume TerraformApplyRole
  ↓
Temporary credentials (15-60 min)
  ↓
Terraform Apply to AWS
```

## Deployment States

```
PENDING → Waiting for validation
VALIDATING → Running terraform validate
SECURITY_SCANNING → Running Checkov/Trivy
PLANNING → Running terraform plan
AWAITING_APPROVAL → Waiting for human approval
APPROVED → Approval granted
DEPLOYING → Running terraform apply
COMPLETED → Successfully deployed
FAILED → Deployment failed
REJECTED → Approval rejected
```

## Post-Deployment Actions

1. **Resource Inventory Update**
   - Query AWS for created resources
   - Store in DynamoDB inventory table
   - Tag with deployment metadata

2. **Audit Event**
   - Record all actions
   - Include user, timestamp, resources
   - Immutable audit trail

3. **Dashboard Update**
   - Real-time status via EventBridge
   - Resource counts
   - Cost updates
   - Security status

4. **Notification**
   - User notification (deployment complete)
   - Team notification (if configured)
   - Audit notification (for compliance team)

## Error Handling

If deployment fails at any stage:
1. Capture detailed error
2. Store in deployment record
3. DO NOT retry automatically
4. Present error to user with remediation guidance
5. For partial failures: document exact state, DO NOT auto-destroy

## Drift Detection

Scheduled drift detection:
```
EventBridge Rule (daily)
  ↓
Lambda Function
  ↓
terraform plan -detailed-exitcode
  ↓
If drift detected:
  - Record in DynamoDB
  - Alert platform team
  - Display in dashboard
  - DO NOT auto-remediate production
```
