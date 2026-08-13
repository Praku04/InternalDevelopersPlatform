variable "application" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, uat, prod)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "instance_count" {
  description = "Number of EC2 instances to create"
  type        = number
  default     = 1
}

variable "ami_id" {
  description = "Approved AMI ID to launch. Must come from the approved AMI list."
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs to launch instances into (private subnets recommended)"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs to attach"
  type        = list(string)
}

variable "associate_public_ip" {
  description = "Whether to associate a public IP. Must be false for private/sensitive workloads."
  type        = bool
  default     = false
}

variable "ebs_volume_size" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 30
}

variable "ebs_encrypted" {
  description = "Whether the root EBS volume is encrypted. Required by policy — cannot be disabled."
  type        = bool
  default     = true

  validation {
    condition     = var.ebs_encrypted == true
    error_message = "EBS encryption is mandatory by policy and cannot be disabled."
  }
}

variable "kms_key_id" {
  description = "Optional customer-managed KMS key for EBS encryption"
  type        = string
  default     = null
}

variable "detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Whether to tag instances for inclusion in the AWS Backup plan"
  type        = bool
  default     = true
}

variable "instance_profile_name" {
  description = "IAM instance profile name to attach (least-privilege role, no admin access)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
