# Multi-Cloud Architecture

## Overview

The AI-Powered Self-Service Infrastructure Platform supports multiple cloud providers:
- **AWS** (Amazon Web Services)
- **Azure** (Microsoft Azure)
- **GCP** (Google Cloud Platform)

## Design Principles

1. **Provider Abstraction**: Common interface for all cloud providers
2. **Terraform Native**: Leverage Terraform's multi-cloud support
3. **Provider-Specific Modules**: Separate module registry per provider
4. **Unified API**: Single API for all clouds
5. **Cloud-Specific IAM**: Separate authentication per provider
6. **Consistent Security**: Same security policies across clouds

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER PORTAL                          │
│              Self Service | AI Chat (Multi-Cloud)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API (Unified)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 CLOUD PROVIDER ABSTRACTION                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ AWS Adapter │  │Azure Adapter│  │ GCP Adapter │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└───────┬───────────────────┬──────────────────┬──────────────┘
        │                   │                  │
        ▼                   ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    AWS      │    │    AZURE    │    │     GCP     │
│  Modules    │    │   Modules   │    │   Modules   │
└─────────────┘    └─────────────┘    └─────────────┘
        │                   │                  │
        ▼                   ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Azure DevOps│    │ Azure DevOps│    │ Azure DevOps│
│  Pipeline   │    │  Pipeline   │    │  Pipeline   │
│   (AWS)     │    │  (Azure)    │    │   (GCP)     │
└─────────────┘    └─────────────┘    └─────────────┘
        │                   │                  │
        ▼                   ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│     AWS     │    │    AZURE    │    │     GCP     │
│ Resources   │    │  Resources  │    │  Resources  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Cloud Provider Support Matrix

| Feature | AWS | Azure | GCP |
|---------|-----|-------|-----|
| Compute | EC2 | VM | Compute Engine |
| Network | VPC | VNet | VPC |
| Storage | S3 | Blob Storage | Cloud Storage |
| Database | RDS | SQL Database | Cloud SQL |
| Load Balancer | ALB/NLB | App Gateway | Cloud Load Balancing |
| Container | EKS | AKS | GKE |
| Serverless | Lambda | Functions | Cloud Functions |
| IAM | IAM | AAD + RBAC | IAM |
| Monitoring | CloudWatch | Monitor | Cloud Monitoring |

## Module Registry Structure

```
terraform/
├── modules/
│   ├── aws/
│   │   ├── compute/
│   │   │   ├── ec2/
│   │   │   ├── lambda/
│   │   │   └── eks/
│   │   ├── networking/
│   │   │   ├── vpc/
│   │   │   ├── security-group/
│   │   │   └── alb/
│   │   ├── storage/
│   │   │   ├── s3/
│   │   │   └── ebs/
│   │   └── database/
│   │       ├── rds/
│   │       └── dynamodb/
│   ├── azure/
│   │   ├── compute/
│   │   │   ├── vm/
│   │   │   ├── functions/
│   │   │   └── aks/
│   │   ├── networking/
│   │   │   ├── vnet/
│   │   │   ├── nsg/
│   │   │   └── app-gateway/
│   │   ├── storage/
│   │   │   ├── blob/
│   │   │   └── disk/
│   │   └── database/
│   │       ├── sql/
│   │       └── cosmos/
│   └── gcp/
│       ├── compute/
│       │   ├── compute-engine/
│       │   ├── cloud-functions/
│       │   └── gke/
│       ├── networking/
│       │   ├── vpc/
│       │   ├── firewall/
│       │   └── load-balancer/
│       ├── storage/
│       │   ├── cloud-storage/
│       │   └── persistent-disk/
│       └── database/
│           ├── cloud-sql/
│           └── firestore/
```

## Request Format (Multi-Cloud)

### Deployment Request Schema

```json
{
  "request_id": "REQ-12345",
  "cloud_provider": "aws|azure|gcp",
  "application_name": "payment-service",
  "environment": "prod",
  "region": "us-east-1",  // Cloud-specific region
  "resources": [
    {
      "type": "compute",
      "provider_service": "ec2|vm|compute-engine",
      "configuration": {
        // Provider-specific config
      }
    }
  ]
}
```

## Authentication Per Provider

### AWS
- OIDC with Azure DevOps
- IAM Roles (TerraformPlanRole, TerraformApplyRole)
- Regional restrictions

### Azure
- Service Principal with OIDC
- Azure RBAC roles (Contributor, Reader)
- Subscription/Resource Group scoped

### GCP
- Workload Identity Federation
- Service Account with roles (roles/compute.admin, roles/storage.admin)
- Project-scoped permissions

## CI/CD Pipeline Per Cloud

### Shared Pipeline Stages
1. Validate
2. Security Scan (provider-agnostic checks)
3. Plan
4. Approval
5. Apply
6. Post-Deployment Validation

### Cloud-Specific Configurations

**AWS Pipeline:**
```yaml
variables:
  CLOUD_PROVIDER: aws
  AWS_SERVICE_CONNECTION: aws-terraform-apply
  STATE_BACKEND: s3
```

**Azure Pipeline:**
```yaml
variables:
  CLOUD_PROVIDER: azure
  AZURE_SERVICE_CONNECTION: azure-terraform-apply
  STATE_BACKEND: azurerm
```

**GCP Pipeline:**
```yaml
variables:
  CLOUD_PROVIDER: gcp
  GCP_SERVICE_CONNECTION: gcp-terraform-apply
  STATE_BACKEND: gcs
```

## Security Policies (Multi-Cloud)

### Universal Policies
- Encryption at rest (all clouds)
- Encryption in transit (all clouds)
- No public access by default
- Required tags/labels
- Approved regions only

### Provider-Specific Policies

**AWS:**
- No SSH/RDP from 0.0.0.0/0
- IMDSv2 required
- S3 public access block
- RDS not publicly accessible

**Azure:**
- No SSH/RDP from internet
- VM managed identities
- Storage account firewall enabled
- SQL no public endpoint

**GCP:**
- No SSH/RDP from 0.0.0.0/0
- Compute Engine with service account
- Cloud Storage uniform bucket-level access
- Cloud SQL private IP only

## AI Module Discovery (Multi-Cloud)

The AI system prompt includes provider-specific context:

```
User Request: "Create a VM for payment app in prod on Azure"

AI Analysis:
1. Cloud Provider: Azure
2. Service: Virtual Machine
3. Search: Azure VM modules
4. Security: Azure-specific policies
5. Output: Azure-specific deployment spec
```

## Cost Estimation (Multi-Cloud)

Different pricing APIs per provider:
- AWS: AWS Pricing API / Cost Explorer
- Azure: Azure Pricing API / Cost Management
- GCP: Cloud Billing API / Pricing Calculator

## Inventory (Multi-Cloud)

Track resources across all clouds:

```json
{
  "resource_id": "i-1234567890abcdef0",
  "cloud_provider": "aws",
  "resource_type": "ec2_instance",
  "region": "us-east-1",
  "application": "payment",
  "environment": "prod"
}
```

## Migration Support

The platform can support cloud-to-cloud migrations:

```
Source: AWS EC2
Target: Azure VM
Action: Generate equivalent Azure configuration
Review: Manual approval required
Execute: Blue-green deployment
```

## Hybrid Cloud Deployments

Support multi-cloud architectures:

```yaml
deployment:
  application: payment-service
  components:
    frontend:
      cloud: aws
      service: ec2
      region: us-east-1
    backend:
      cloud: azure
      service: vm
      region: eastus
    database:
      cloud: gcp
      service: cloud-sql
      region: us-central1
```

## Monitoring & Observability

Unified monitoring across clouds:
- AWS: CloudWatch
- Azure: Azure Monitor
- GCP: Cloud Monitoring
- Aggregated: DataDog / Splunk / Prometheus

## Disaster Recovery

Multi-cloud DR strategies:
- Primary: AWS us-east-1
- Secondary: Azure eastus
- Tertiary: GCP us-central1

## Compliance

Cloud-specific compliance:
- AWS: AWS Config, Security Hub, GuardDuty
- Azure: Azure Policy, Security Center, Defender
- GCP: Security Command Center, Policy Intelligence

## Implementation Priority

### Phase 1 (Current)
- ✅ AWS fully implemented

### Phase 2 (Next)
- Azure support
- Azure module registry
- Azure authentication
- Azure pipelines

### Phase 3
- GCP support
- GCP module registry
- GCP authentication
- GCP pipelines

### Phase 4
- Multi-cloud deployments
- Cloud migration support
- Unified cost dashboard
- Cross-cloud networking
