# ---------------------------------------------------------------------------
# S3 Module
# Approved enterprise S3 module: encryption always on, public access always
# blocked, versioning and logging on by default, optional lifecycle rules.
# ---------------------------------------------------------------------------

locals {
  name = "${var.application}-${var.environment}-${var.bucket_suffix}"

  common_tags = merge(
    {
      Application = var.application
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "s3"
    },
    var.tags
  )
}

resource "aws_s3_bucket" "this" {
  bucket = local.name

  tags = merge(local.common_tags, {
    Name = local.name
  })
}

# Public access is always blocked; not configurable by design.
resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

# Encryption is always enforced; SSE-KMS if a key is supplied, else SSE-S3.
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = var.kms_key_id != null
  }
}

resource "aws_s3_bucket_logging" "this" {
  count  = var.enable_logging ? 1 : 0
  bucket = aws_s3_bucket.this.id

  target_bucket = var.logging_target_bucket
  target_prefix = "s3-access-logs/${local.name}/"

  lifecycle {
    precondition {
      condition     = var.logging_target_bucket != null
      error_message = "logging_target_bucket must be set when enable_logging is true."
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = var.lifecycle_enabled ? 1 : 0
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}
