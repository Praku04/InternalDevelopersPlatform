# Checkov Security Scanning Integration

## Overview

Checkov is a static code analysis tool for infrastructure-as-code. It scans Terraform configurations for security and compliance issues before deployment.

## Integration Architecture

```
Azure DevOps Pipeline
    ↓
Terraform Configuration
    ↓
Checkov Scan
    ├─ Built-in Checks
    ├─ Custom Checks
    └─ Policy Rules
    ↓
Results (JSON)
    ├─ PASSED: Continue
    ├─ FAILED (CRITICAL/HIGH): Block
    └─ FAILED (MEDIUM/LOW): Warning
    ↓
Backend API (Security Results)
    ↓
Dashboard Display
```

## Configuration

### Location
- Main config: `security/checkov/config.yaml`
- Custom checks: `security/checkov/custom-checks/`
- Baseline (exceptions): `security/checkov/baseline.json`

### Check Severity Levels

| Severity | Action | Examples |
|----------|--------|----------|
| CRITICAL | Block deployment | Wildcard IAM policies, public RDS |
| HIGH | Block deployment | Unencrypted S3, open SSH/RDP |
| MEDIUM | Warning only | Missing logging, no MFA |
| LOW | Informational | Missing tags, naming conventions |

## Built-in Checks

### Network Security
- `CKV_AWS_23`: No SSH from 0.0.0.0/0
- `CKV_AWS_24`: No RDP from 0.0.0.0/0
- `CKV_AWS_25`: No all ports from 0.0.0.0/0
- `CKV_AWS_130`: Subnets don't assign public IPs

### Encryption
- `CKV_AWS_19`: S3 encryption enabled
- `CKV_AWS_126`: RDS encryption enabled
- `CKV_AWS_150`: RDS encrypted at rest
- `CKV_AWS_158`: CloudWatch logs encrypted

### IAM
- `CKV_AWS_33`: No wildcard KMS principals
- `CKV_AWS_34`: No full admin policies
- `CKV_AWS_40`: No wildcard IAM policies

### EC2
- `CKV_AWS_46`: Detailed monitoring enabled
- `CKV_AWS_47`: IMDSv2 enabled
- `CKV_AWS_79`: IMDSv1 disabled
- `CKV_AWS_88`: No deprecated instance types

### Database
- `CKV_AWS_129`: RDS IAM authentication
- `CKV_AWS_157`: RDS not publicly accessible
- `CKV_AWS_161`: RDS IAM authentication

### Load Balancers
- `CKV_AWS_131`: ALB drops invalid headers

## Custom Checks

### 1. Required Tags (`CKV_AWS_CUSTOM_001`)

**Purpose**: Ensure all resources have required tags

**Required Tags**:
- Application
- Environment
- Owner
- ManagedBy

**Implementation**: `security/checkov/custom-checks/check_required_tags.py`

**Example**:
```hcl
resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"
  
  tags = {
    Application = "payment-service"
    Environment = "prod"
    Owner       = "platform-team"
    ManagedBy   = "ai-cloud-platform"
  }
}
```

### 2. Approved Regions (`CKV_AWS_CUSTOM_002`)

**Purpose**: Ensure resources deployed in approved regions only

**Approved Regions**:
- ap-south-1 (Mumbai)
- ap-southeast-1 (Singapore)
- us-east-1 (N. Virginia, global services only)

**Implementation**: `security/checkov/custom-checks/check_approved_regions.py`

**Example**:
```hcl
provider "aws" {
  region = "ap-south-1"  # ✓ Approved
}
```

## Running Checkov

### In Pipeline (Automatic)
```yaml
- script: |
    checkov --directory . \
      --config-file security/checkov/config.yaml \
      --output json \
      --output-file-path checkov-results.json
  displayName: 'Run Checkov Security Scan'
```

### Locally (Manual)
```bash
# Install Checkov
pip install checkov

# Run scan
cd terraform/generated/REQ-12345
checkov --directory . \
  --config-file ../../../security/checkov/config.yaml \
  --compact

# Run with custom checks
checkov --directory . \
  --external-checks-dir ../../../security/checkov/custom-checks
```

### Docker
```bash
docker run --rm \
  -v $(pwd):/tf \
  bridgecrew/checkov \
  -d /tf \
  --config-file /tf/security/checkov/config.yaml
```

## Handling Violations

### Critical/High Violations
Deployment is automatically blocked. To proceed:

1. **Fix the issue** (recommended):
```hcl
# Before (blocked)
resource "aws_security_group" "example" {
  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ✗ CRITICAL
  }
}

# After (passes)
resource "aws_security_group" "example" {
  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # ✓ PASSES
  }
}
```

2. **Request exception** (requires approval):
   - Document justification
   - Get Security team approval
   - Add to baseline file
   - Set expiration date

### Medium/Low Violations
Warnings are logged but don't block deployment. Should be fixed in next iteration.

## Baseline File (Exceptions)

### Purpose
Track approved exceptions to security policies.

### Location
`security/checkov/baseline.json`

### Format
```json
{
  "exceptions": [
    {
      "check_id": "CKV_AWS_23",
      "resource": "aws_security_group.bastion",
      "justification": "Bastion host requires SSH access from approved VPN range",
      "approved_by": "security-team@company.com",
      "approval_date": "2024-01-15",
      "expiration_date": "2024-07-15",
      "compensating_controls": [
        "MFA required for SSH",
        "Session logging enabled",
        "IP restricted to VPN range"
      ]
    }
  ]
}
```

### Creating Exception
```bash
# Generate baseline from current state
checkov --directory . \
  --create-baseline \
  --output-baseline-as-skipped security/checkov/baseline.json
```

## Integration with Backend

### Security Scan Callback
Pipeline sends results to backend:

```http
POST /api/v1/deployments/{request_id}/security
Content-Type: application/json

{
  "scan_type": "checkov",
  "status": "COMPLETED",
  "results": {
    "summary": {
      "passed": 45,
      "failed": 2,
      "skipped": 3
    },
    "failed_checks": [
      {
        "check_id": "CKV_AWS_23",
        "severity": "CRITICAL",
        "resource": "aws_security_group.web",
        "file": "main.tf",
        "line": 42
      }
    ]
  }
}
```

### Dashboard Display
- Total checks: Passed/Failed/Skipped
- Critical violations (red)
- High violations (orange)
- Medium violations (yellow)
- Low violations (blue)
- Exception list with expiration dates

## Continuous Improvement

### Adding Custom Checks

1. **Create check file**:
```python
# security/checkov/custom-checks/check_new_policy.py
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck

class NewPolicyCheck(BaseResourceCheck):
    def __init__(self):
        name = "Check new policy requirement"
        id = "CKV_AWS_CUSTOM_003"
        supported_resources = ["aws_instance"]
        categories = [CheckCategories.GENERAL_SECURITY]
        super().__init__(name=name, id=id, categories=categories, 
                         supported_resources=supported_resources)
    
    def scan_resource_conf(self, conf):
        # Check logic
        if condition:
            return CheckResult.PASSED
        return CheckResult.FAILED

check = NewPolicyCheck()
```

2. **Test locally**:
```bash
checkov -d . --external-checks-dir security/checkov/custom-checks
```

3. **Update documentation**
4. **Commit and deploy**

### Monitoring Check Effectiveness

Track metrics:
- Most common violations
- Time to fix violations
- Exception trends
- False positive rate

Regular reviews:
- Monthly: Review violations and trends
- Quarterly: Review check effectiveness
- Annually: Update policies

## Troubleshooting

### Checkov Not Running
```bash
# Check Checkov version
checkov --version

# Verify config file
cat security/checkov/config.yaml

# Test with verbose output
checkov -d . --config-file security/checkov/config.yaml -v
```

### False Positives
1. Verify the check is correct
2. If legitimate exception, add to baseline
3. If check is wrong, disable in config:
```yaml
skip-check:
  - CKV_AWS_XXX  # Reason for skipping
```

### Performance Issues
```yaml
# Reduce scope
download-external-modules: false
skip-dirs:
  - .terraform
  - node_modules
```

## References

- [Checkov Documentation](https://www.checkov.io/)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [CIS AWS Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- Internal Security Policy: `security/policies/security-policy.md`
