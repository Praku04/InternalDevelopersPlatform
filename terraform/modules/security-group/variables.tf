variable "application" {
  description = "Application name, used for tagging and naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, uat, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID the security group belongs to"
  type        = string
}

variable "name_suffix" {
  description = "Suffix appended to the security group name (e.g. 'ec2', 'alb', 'rds')"
  type        = string
}

variable "description" {
  description = "Description of the security group"
  type        = string
  default     = "Managed by Terraform"
}

variable "ingress_rules" {
  description = "List of ingress rules. Wide-open SSH/RDP (0.0.0.0/0 on 22 or 3389) is rejected by policy."
  type = list(object({
    description = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}

variable "egress_rules" {
  description = "List of egress rules"
  type = list(object({
    description = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = [
    {
      description = "Allow all outbound"
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}

locals {
  # Policy guardrail: block unrestricted SSH (22) or RDP (3389) from the internet.
  unrestricted_sensitive_ports = [
    for rule in var.ingress_rules :
    rule if contains(rule.cidr_blocks, "0.0.0.0/0") && (
      (rule.from_port <= 22 && rule.to_port >= 22) ||
      (rule.from_port <= 3389 && rule.to_port >= 3389)
    )
  ]
}

# Fails plan/apply if a caller tries to open SSH/RDP to the world, enforcing
# the "no unrestricted SSH / no unrestricted RDP" policy at the module level.
resource "terraform_data" "policy_guard" {
  lifecycle {
    precondition {
      condition     = length(local.unrestricted_sensitive_ports) == 0
      error_message = "Ingress rules must not expose port 22 (SSH) or 3389 (RDP) to 0.0.0.0/0."
    }
  }
}
