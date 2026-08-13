# VPC Module

Approved enterprise VPC module. Provisions a VPC with public and private
subnets spread across the given availability zones, an internet gateway,
optional NAT gateway(s) for private-subnet egress, and optional VPC flow
logs shipped to CloudWatch.

## Capabilities

- `public-subnet`
- `private-subnet`
- `nat-gateway`
- `flow-logs`
- `multi-az`

## Supported Environments

`dev`, `uat`, `prod`

## Example

```hcl
module "vpc" {
  source = "../../modules/vpc"

  application           = "payment"
  environment            = "dev"
  cidr_block              = "10.10.0.0/16"
  azs                     = ["ap-south-1a", "ap-south-1b"]
  public_subnet_cidrs     = ["10.10.0.0/24", "10.10.1.0/24"]
  private_subnet_cidrs    = ["10.10.10.0/24", "10.10.11.0/24"]
  enable_nat_gateway      = true
  single_nat_gateway      = true
  enable_flow_logs        = true
}
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| application | Application name | string | — |
| environment | dev / uat / prod | string | — |
| cidr_block | VPC CIDR | string | `10.0.0.0/16` |
| azs | Availability zones | list(string) | — |
| public_subnet_cidrs | Public subnet CIDRs | list(string) | — |
| private_subnet_cidrs | Private subnet CIDRs | list(string) | — |
| enable_nat_gateway | Enable NAT gateway | bool | `true` |
| single_nat_gateway | Use one shared NAT gateway | bool | `true` |
| enable_flow_logs | Enable VPC flow logs | bool | `true` |
| tags | Extra tags | map(string) | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | ID of the VPC |
| vpc_cidr_block | CIDR block of the VPC |
| public_subnet_ids | Public subnet IDs |
| private_subnet_ids | Private subnet IDs |
| nat_gateway_ids | NAT gateway IDs |
| internet_gateway_id | Internet gateway ID |

## Security Notes

- Public subnets do not auto-assign public IPs (`map_public_ip_on_launch = false`).
- Flow logs default to on and retain 365 days in `prod`, 30 days elsewhere.
