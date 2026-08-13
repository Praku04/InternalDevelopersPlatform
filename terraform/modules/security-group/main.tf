locals {
  name = "${var.application}-${var.environment}-${var.name_suffix}-sg"

  common_tags = merge(
    {
      Application = var.application
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "security-group"
    },
    var.tags
  )
}

resource "aws_security_group" "this" {
  name        = local.name
  description = var.description
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  dynamic "egress" {
    for_each = var.egress_rules
    content {
      description = egress.value.description
      from_port   = egress.value.from_port
      to_port     = egress.value.to_port
      protocol    = egress.value.protocol
      cidr_blocks = egress.value.cidr_blocks
    }
  }

  tags = merge(local.common_tags, {
    Name = local.name
  })

  depends_on = [terraform_data.policy_guard]
}
