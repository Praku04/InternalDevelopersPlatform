# Azure DevOps Setup Guide

## Overview

This platform uses Azure DevOps for:
- Source control (Azure Repos)
- CI/CD pipelines
- Environment management
- Approval workflows
- Pull request automation

## Prerequisites

- Azure DevOps Organization
- Azure DevOps Project
- AWS Account with IAM permissions
- Permissions to create service connections
- Permissions to create environments

## Step 1: Create Azure DevOps Project

```bash
# Using Azure CLI
az devops project create \
  --name "AI-Cloud-Self-Service" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --visibility private \
  --source-control git
```

Or create via Azure DevOps portal: `https://dev.azure.com/YOUR_ORG`

## Step 2: Initialize Repository

```bash
# Clone the repository
git clone https://YOUR_ORG@dev.azure.com/YOUR_ORG/AI-Cloud-Self-Service/_git/ai-cloud-platform
cd ai-cloud-platform

# Add remote if migrating from existing repo
git remote add azdo https://YOUR_ORG@dev.azure.com/YOUR_ORG/AI-Cloud-Self-Service/_git/ai-cloud-platform
git push azdo main
```

## Step 3: Configure AWS Service Connection (OIDC)

### Why OIDC?
- No permanent AWS credentials stored in Azure DevOps
- Short-lived tokens (15-60 minutes)
- Automatic credential rotation
- Better security posture

### AWS Setup

1. **Create OIDC Provider in AWS IAM**

```bash
aws iam create-open-id-connect-provider \
  --url "https://vstoken.dev.azure.com/YOUR_ORG_ID" \
  --client-id-list "api://AzureADTokenExchange" \
  --thumbprint-list "$(curl -s https://vstoken.dev.azure.com/YOUR_ORG_ID | openssl x509 -fingerprint -noout | cut -d'=' -f2)"
```

2. **Create IAM Role for Terraform Plan**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/vstoken.dev.azure.com/ORG_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "vstoken.dev.azure.com/ORG_ID:sub": "sc://YOUR_ORG/YOUR_PROJECT/terraform-plan-connection",
          "vstoken.dev.azure.com/ORG_ID:aud": "api://AzureADTokenExchange"
        }
      }
    }
  ]
}
```

3. **Create IAM Role for Terraform Apply**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/vstoken.dev.azure.com/ORG_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "vstoken.dev.azure.com/ORG_ID:sub": "sc://YOUR_ORG/YOUR_PROJECT/terraform-apply-connection",
          "vstoken.dev.azure.com/ORG_ID:aud": "api://AzureADTokenExchange"
        }
      }
    }
  ]
}
```

4. **Attach Policies to Roles**

```bash
# Plan role - read-only
aws iam attach-role-policy \
  --role-name TerraformPlanRole \
  --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

# Apply role - managed by custom policy
aws iam put-role-policy \
  --role-name TerraformApplyRole \
  --policy-name TerraformApplyPolicy \
  --policy-document file://terraform-apply-policy.json
```

### Azure DevOps Service Connection Setup

1. Navigate to: `Project Settings → Service connections`
2. Click **New service connection**
3. Select **AWS**
4. Choose **Workload Identity federation**
5. Enter:
   - **Connection name**: `aws-terraform-plan`
   - **AWS Account ID**: Your AWS account ID
   - **Role ARN**: `arn:aws:iam::ACCOUNT_ID:role/TerraformPlanRole`
   - **Session name**: `azdo-terraform-plan`
6. Repeat for apply connection: `aws-terraform-apply`

## Step 4: Create Environments

Create three environments for approval gates:

### DEV Environment
```bash
# No approvals required for DEV
az pipelines environment create \
  --name "DEV" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service"
```

### UAT Environment
```bash
az pipelines environment create \
  --name "UAT" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service"

# Add approval
az pipelines environment approval create \
  --environment-name "UAT" \
  --approvers "team-leads@company.com" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service"
```

### PROD Environment
```bash
az pipelines environment create \
  --name "PROD" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service"

# Add approvals (requires multiple)
az pipelines environment approval create \
  --environment-name "PROD" \
  --approvers "managers@company.com,security@company.com,platform-admins@company.com" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service" \
  --minimum-approvers 2
```

### Configure Environment Approval Policies

In Azure DevOps Portal:
1. Go to `Pipelines → Environments → PROD`
2. Click on `Approvals and checks`
3. Add **Approvals** with:
   - Approvers: managers@company.com, security@company.com, platform-admins@company.com
   - Minimum number of approvers: 2
   - Instructions: "Review Terraform plan, security scan results, and cost estimate before approval"
4. Add **Business Hours** check (optional)
5. Add **Required template** check (optional)

## Step 5: Configure Variable Groups

Create variable groups for shared configuration:

```bash
# Create variable group
az pipelines variable-group create \
  --name "terraform-config" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service" \
  --variables \
    AWS_REGION=ap-south-1 \
    TERRAFORM_VERSION=1.9.0 \
    S3_TFSTATE_BUCKET=ai-cloud-platform-tfstate \
    DYNAMODB_LOCK_TABLE=ai-cloud-platform-tfstate-lock
```

For secrets:
```bash
# Link to Azure Key Vault (recommended)
az pipelines variable-group create \
  --name "terraform-secrets" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service" \
  --authorize true \
  --variables-from-key-vault \
    --vault-name "ai-cloud-kv"
```

## Step 6: Create Pipeline

```bash
# Create pipeline from YAML
az pipelines create \
  --name "Terraform-Deployment" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service" \
  --repository "ai-cloud-platform" \
  --branch "main" \
  --yml-path "azure-devops/pipelines/deployment.yml"
```

## Step 7: Configure Branch Policies

Protect the main branch:

```bash
# Enable pull request policy
az repos policy create \
  --policy-type "Minimum number of reviewers" \
  --repository-id "YOUR_REPO_ID" \
  --branch "main" \
  --organization "https://dev.azure.com/YOUR_ORG" \
  --project "AI-Cloud-Self-Service" \
  --blocking true \
  --enabled true \
  --minimum-approver-count 1
```

Additional policies:
- Require work item linking
- Require build validation
- Automatically include reviewers

## Step 8: Test the Setup

1. **Test Service Connection**
```bash
# From pipeline
aws sts get-caller-identity
```

2. **Test Pipeline Trigger**
```bash
git commit --allow-empty -m "Test pipeline trigger"
git push
```

3. **Verify Environments**
- Check DEV environment accessible
- Check UAT requires approval
- Check PROD requires multiple approvals

## Troubleshooting

### OIDC Connection Failed
- Verify OIDC provider thumbprint matches
- Check IAM role trust policy
- Verify service connection subject matches role condition

### Pipeline Permission Denied
- Grant pipeline permissions to service connection
- Grant pipeline permissions to environments
- Check variable group permissions

### Approval Not Working
- Verify approvers have access to project
- Check environment approval configuration
- Verify minimum approvers count

## Security Best Practices

1. **Never use permanent AWS keys**
2. **Use separate roles for plan and apply**
3. **Limit apply role permissions** (principle of least privilege)
4. **Rotate OIDC thumbprints** when Azure DevOps updates
5. **Enable audit logging** for all environments
6. **Review approvers regularly**
7. **Use Azure Key Vault** for secrets
8. **Enable branch protection**

## Next Steps

- [Configure Pipelines](pipelines.md)
- [Set up Approval Workflows](approvals.md)
- [AWS Federation Details](aws-federation.md)
