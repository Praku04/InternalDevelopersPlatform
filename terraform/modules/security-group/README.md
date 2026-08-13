# Security Group Module

Approved enterprise security group module with a built-in policy guardrail:
plans that attempt to open port 22 (SSH) or 3389 (RDP) to `0.0.0.0/0` fail
at plan/apply time via a Terraform `precondition`, enforcing the "no
unrestricted SSH / no unrestricted RDP" security policy at the module level
(in addition to Checkov/Trivy scanning downstream).

## Capabilities

- `ingress-egress-rules`
- `policy-guardrail-ssh-rdp`

## Supported Environments

`dev`, `uat`, `prod`

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| application | Application name | string | — |
| environment | dev / uat / prod | string | — |
| vpc_id | VPC ID | string | — |
| name_suffix | Suffix for SG name (e.g. `ec2`, `alb`) | string | — |
| description | SG description | string | `Managed by Terraform` |
| ingress_rules | List of ingress rule objects | list(object) | `[]` |
| egress_rules | List of egress rule objects | list(object) | allow-all outbound |
| tags | Extra tags | map(string) | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| security_group_id | ID of the security group |
| security_group_name | Name of the security group |
