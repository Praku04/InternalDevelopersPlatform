variable "application" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, uat, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for the load balancer (public subnets for internet-facing ALBs)"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs to attach to the ALB"
  type        = list(string)
}

variable "internal" {
  description = "Whether the ALB is internal (private) or internet-facing"
  type        = bool
  default     = true
}

variable "target_port" {
  description = "Port that targets (e.g. EC2 instances) listen on"
  type        = number
  default     = 80
}

variable "target_ids" {
  description = "IDs of targets (e.g. EC2 instance IDs) to register"
  type        = list(string)
  default     = []
}

variable "health_check_path" {
  description = "Path used for target group health checks"
  type        = string
  default     = "/"
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection (recommended true for prod)"
  type        = bool
  default     = false
}

variable "enable_access_logs" {
  description = "Enable ALB access logs to S3"
  type        = bool
  default     = true
}

variable "access_logs_bucket" {
  description = "S3 bucket name for ALB access logs (required if enable_access_logs is true)"
  type        = string
  default     = null
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS listener. If null, only HTTP listener is created (not recommended for prod)."
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
