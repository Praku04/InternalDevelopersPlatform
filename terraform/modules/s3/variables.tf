variable "application" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, uat, prod)"
  type        = string
}

variable "bucket_suffix" {
  description = "Suffix appended to the bucket name for uniqueness/purpose (e.g. 'data', 'logs')"
  type        = string
}

variable "versioning_enabled" {
  description = "Enable bucket versioning"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "Optional customer-managed KMS key ARN for SSE-KMS. If null, SSE-S3 (AES256) is used."
  type        = string
  default     = null
}

variable "enable_logging" {
  description = "Enable S3 server access logging"
  type        = bool
  default     = true
}

variable "logging_target_bucket" {
  description = "Target bucket for access logs (required if enable_logging is true)"
  type        = string
  default     = null
}

variable "lifecycle_enabled" {
  description = "Enable a lifecycle rule to transition/expire noncurrent versions"
  type        = bool
  default     = true
}

variable "noncurrent_version_expiration_days" {
  description = "Days after which noncurrent versions are expired"
  type        = number
  default     = 90
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
