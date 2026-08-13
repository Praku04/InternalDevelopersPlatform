# Security Policies

## EC2
- IMDSv2 required (enforced in `terraform/modules/ec2`)
- EBS encryption required (enforced in `terraform/modules/ec2`, cannot be disabled)
- Approved AMI only
- Mandatory tags
- No unrestricted SSH / RDP (enforced in `terraform/modules/security-group` via a plan-time precondition)

## S3
- Encryption (enforced in `terraform/modules/s3`, cannot be disabled)
- Public access blocked (enforced unconditionally in `terraform/modules/s3`)
- Versioning where required
- Lifecycle policy
- Logging where required

## RDS (module not yet implemented)
- Encryption
- Private subnet
- Deletion protection in production
- Backup
- No public accessibility

## IAM
- Least privilege
- No wildcard admin policies
- No unnecessary access keys

## Networking
- No unrestricted sensitive ports
- Approved CIDRs
- Private subnet for sensitive services

Checkov/Trivy/AWS Config/Security Hub scanning (Section 19) is planned for
a later phase — not yet wired into a pipeline.
