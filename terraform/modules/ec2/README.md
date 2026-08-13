# EC2 Module

Standard enterprise EC2 module. Launches one or more EC2 instances with
IMDSv2 enforced, mandatory encrypted EBS root volumes, optional detailed
CloudWatch monitoring, optional AWS Backup tagging, and support for
attaching a least-privilege IAM instance profile.

## Capabilities

- `private-subnet`
- `encrypted-ebs`
- `monitoring`
- `iam-role`
- `imdsv2`
- `backup-tagging`

## Supported Environments

`dev`, `uat`, `prod`

## Example

```hcl
module "ec2" {
  source = "../../modules/ec2"

  application            = "payment"
  environment             = "dev"
  instance_type           = "t3.medium"
  instance_count          = 2
  ami_id                  = "ami-0123456789abcdef0"
  subnet_ids              = module.vpc.private_subnet_ids
  security_group_ids      = [module.security_group.security_group_id]
  associate_public_ip     = false
  ebs_volume_size         = 30
  ebs_encrypted           = true
  detailed_monitoring     = true
  enable_backup           = true
}
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| application | Application name | string | — |
| environment | dev / uat / prod | string | — |
| instance_type | EC2 instance type | string | `t3.medium` |
| instance_count | Number of instances | number | `1` |
| ami_id | Approved AMI ID | string | — |
| subnet_ids | Subnet IDs | list(string) | — |
| security_group_ids | Security group IDs | list(string) | — |
| associate_public_ip | Assign public IP | bool | `false` |
| ebs_volume_size | Root volume size (GB) | number | `30` |
| ebs_encrypted | Encrypt root volume (must be `true`) | bool | `true` |
| kms_key_id | Customer-managed KMS key | string | `null` |
| detailed_monitoring | Enable detailed monitoring | bool | `true` |
| enable_backup | Tag for AWS Backup plan | bool | `true` |
| instance_profile_name | IAM instance profile name | string | `null` |
| tags | Extra tags | map(string) | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| instance_ids | IDs of created instances |
| private_ips | Private IPs of instances |
| instance_arns | ARNs of created instances |

## Security Notes

- `ebs_encrypted` is validated to always be `true` — encryption cannot be disabled through this module.
- IMDSv2 (`http_tokens = required`) is always enforced.
- `associate_public_ip` defaults to `false`; sensitive workloads should never set it `true`.
