output "instance_ids" {
  description = "IDs of the created EC2 instances"
  value       = aws_instance.this[*].id
}

output "private_ips" {
  description = "Private IP addresses of the instances"
  value       = aws_instance.this[*].private_ip
}

output "instance_arns" {
  description = "ARNs of the created EC2 instances"
  value       = aws_instance.this[*].arn
}
