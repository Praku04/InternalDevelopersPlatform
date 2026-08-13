# ---------------------------------------------------------------------------
# EC2 Module
# Approved enterprise EC2 module: IMDSv2 enforced, EBS encryption mandatory,
# optional detailed monitoring, optional backup tagging, least-privilege
# instance profile attachment.
# ---------------------------------------------------------------------------

locals {
  name = "${var.application}-${var.environment}-ec2"

  common_tags = merge(
    {
      Application = var.application
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "ec2"
      Backup      = var.enable_backup ? "true" : "false"
    },
    var.tags
  )
}

resource "aws_instance" "this" {
  count = var.instance_count

  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = element(var.subnet_ids, count.index % length(var.subnet_ids))
  vpc_security_group_ids      = var.security_group_ids
  associate_public_ip_address = var.associate_public_ip
  monitoring                  = var.detailed_monitoring
  iam_instance_profile        = var.instance_profile_name

  # IMDSv2 required by policy (no session-less/IMDSv1 access).
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size = var.ebs_volume_size
    encrypted   = var.ebs_encrypted
    kms_key_id  = var.kms_key_id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name}-${count.index + 1}"
  })

  lifecycle {
    precondition {
      condition     = var.ebs_encrypted
      error_message = "EBS encryption is mandatory; ebs_encrypted must be true."
    }
  }
}
