# Infrastructure Security Policy

## Overview

This document defines the security requirements for all infrastructure deployed through the AI Cloud Self-Service Platform.

## Mandatory Security Controls

### 1. Network Security

#### 1.1 Security Groups
- **CRITICAL**: No security group shall allow ingress from 0.0.0.0/0 to SSH (port 22)
- **CRITICAL**: No security group shall allow ingress from 0.0.0.0/0 to RDP (port 3389)
- **CRITICAL**: No security group shall allow ingress from 0.0.0.0/0 to all ports
- **HIGH**: Security groups should follow least privilege principle
- **HIGH**: Security group rules must have descriptions

#### 1.2 VPC Configuration
- **HIGH**: VPC subnets must not assign public IP addresses by default
- **HIGH**: Private subnets must route through NAT Gateway
- **MEDIUM**: VPC Flow Logs should be enabled
- **MEDIUM**: Network ACLs should be configured for additional protection

### 2. Data Protection

#### 2.1 Encryption at Rest
- **CRITICAL**: S3 buckets must have encryption enabled
- **CRITICAL**: RDS databases must be encrypted
- **CRITICAL**: EBS volumes must be encrypted
- **HIGH**: CloudWatch log groups must be encrypted
- **HIGH**: DynamoDB tables must be encrypted
- **HIGH**: EKS secrets must be encrypted

#### 2.2 Encryption in Transit
- **HIGH**: ALB listeners must use HTTPS/TLS
- **HIGH**: RDS connections must use TLS
- **MEDIUM**: Internal communication should use TLS where possible

### 3. Access Control

#### 3.1 IAM Policies
- **CRITICAL**: No IAM policies with full "*:*" administrative privileges
- **CRITICAL**: No IAM policies with wildcard principals
- **HIGH**: IAM policies should follow least privilege
- **HIGH**: IAM roles should have trust policies with specific principals
- **MEDIUM**: IAM policies should have conditions where appropriate

#### 3.2 Resource Access
- **CRITICAL**: RDS instances must not be publicly accessible
- **CRITICAL**: S3 buckets must not be publicly readable unless explicitly required
- **HIGH**: Lambda functions should use VPC when accessing internal resources
- **HIGH**: EC2 instances should use IAM roles, not access keys

### 4. Monitoring and Logging

#### 4.1 CloudWatch
- **HIGH**: EC2 instances must have detailed monitoring enabled
- **HIGH**: RDS enhanced monitoring should be enabled
- **MEDIUM**: Lambda functions should log to CloudWatch
- **MEDIUM**: CloudWatch alarms should be configured for critical metrics

#### 4.2 Audit Logging
- **HIGH**: CloudTrail must be enabled
- **HIGH**: S3 access logging should be enabled
- **MEDIUM**: VPC Flow Logs should be enabled
- **MEDIUM**: Load Balancer access logs should be enabled

### 5. Instance Configuration

#### 5.1 EC2 Instances
- **CRITICAL**: EC2 instances must use IMDSv2
- **HIGH**: EC2 instances should not use deprecated instance types
- **HIGH**: EC2 instances should be in private subnets unless specifically required
- **MEDIUM**: EC2 instances should have termination protection in production
- **MEDIUM**: EC2 user data should not contain secrets

#### 5.2 Container Security
- **HIGH**: EKS clusters must use private endpoints
- **HIGH**: EKS control plane logging must be enabled
- **MEDIUM**: Container images should be scanned for vulnerabilities
- **MEDIUM**: Containers should not run as root

### 6. Backup and Recovery

#### 6.1 RDS
- **HIGH**: RDS automated backups must be enabled
- **MEDIUM**: RDS backup retention should be at least 7 days
- **MEDIUM**: RDS deletion protection should be enabled for production

#### 6.2 DynamoDB
- **HIGH**: DynamoDB point-in-time recovery should be enabled for production
- **MEDIUM**: DynamoDB should have backup schedules

### 7. Tagging Requirements

All resources must have the following tags:
- **Application**: Application name
- **Environment**: dev, uat, or prod
- **Owner**: Team or individual responsible
- **ManagedBy**: ai-cloud-platform
- **CostCenter**: Cost allocation (optional)
- **DataClassification**: public, internal, confidential, restricted (optional)

### 8. Compliance Requirements

#### 8.1 Data Residency
- **CRITICAL**: Resources must be deployed in approved regions only
- Approved regions:
  - ap-south-1 (Mumbai) - Primary
  - ap-southeast-1 (Singapore)
  - us-east-1 (N. Virginia) - Global services only

#### 8.2 Service Restrictions
- Prohibited services (require security review):
  - Public RDS instances
  - Public S3 buckets (without explicit approval)
  - IAM users with access keys (service accounts)
  - Lambda functions with admin permissions

## Environment-Specific Requirements

### Development (DEV)
- All mandatory controls apply
- Cost controls: Instances should auto-stop outside business hours
- Data: No production data allowed

### UAT
- All mandatory controls apply
- Production-like configuration required
- Data: Anonymized production data only

### Production (PROD)
- All mandatory controls apply
- Additional requirements:
  - Multi-AZ deployment for critical services
  - Backup retention: minimum 30 days
  - Deletion protection enabled
  - Change management approval required
  - Monitoring alerts configured

## Security Scanning

### Pre-Deployment
1. **Terraform Validation**: Syntax and configuration checks
2. **Checkov**: Policy compliance scanning
3. **Trivy**: Vulnerability and misconfiguration scanning
4. **Custom Policies**: Organization-specific checks

### Deployment Blocking

Deployments will be blocked if:
- Any **CRITICAL** severity issues are detected
- Any **HIGH** severity issues are detected
- Custom policy violations are detected
- Required approvals are not obtained

### Exceptions

Security exceptions must:
1. Be documented with justification
2. Be approved by Security team
3. Be time-bound (expiration date)
4. Be reviewed quarterly
5. Be tracked in exceptions registry

Exception request process:
1. Submit exception request with:
   - Resource details
   - Security control being waived
   - Business justification
   - Compensating controls
   - Expiration date
2. Security team review (2 business days)
3. Approval/rejection decision
4. Exception tracked in baseline file

## Incident Response

### Security Findings
- **CRITICAL**: Immediate remediation required (4 hours)
- **HIGH**: Remediation within 24 hours
- **MEDIUM**: Remediation within 7 days
- **LOW**: Remediation within 30 days

### Detection
- AWS GuardDuty findings
- Security Hub findings
- CloudWatch Alarms
- Manual security reviews

### Response
1. Identify affected resources
2. Assess impact
3. Contain if active threat
4. Remediate vulnerability
5. Document incident
6. Review and improve controls

## Compliance Validation

### Continuous Monitoring
- Daily: Automated security scans
- Weekly: Compliance reports
- Monthly: Security reviews
- Quarterly: Comprehensive audits

### Reporting
- Security dashboard (real-time)
- Weekly compliance reports to teams
- Monthly reports to management
- Quarterly reports to audit committee

## Policy Updates

- Policy owner: Security Team
- Review frequency: Quarterly
- Update process:
  1. Propose changes
  2. Security team review
  3. Stakeholder feedback
  4. Approval by CISO
  5. Communication to teams
  6. Implementation in automation

## References

- AWS Security Best Practices
- CIS AWS Foundations Benchmark
- NIST Cybersecurity Framework
- Organization Security Standards
- Data Protection Policy
- Incident Response Plan

## Contact

- Security Team: security@company.com
- Platform Team: platform@company.com
- Emergency: security-oncall@company.com
