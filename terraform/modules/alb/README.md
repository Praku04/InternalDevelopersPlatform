# ALB Module

Approved enterprise Application Load Balancer module. Supports internal or
internet-facing ALBs, HTTP→HTTPS redirect when a certificate is supplied,
S3 access logging, and target group attachment.

## Capabilities

- `http-listener`
- `https-listener`
- `access-logs`
- `target-group`

## Supported Environments

`dev`, `uat`, `prod`

## Inputs

See `variables.tf` for the full list. Key inputs: `internal`, `certificate_arn`
(enables HTTPS + HTTP redirect), `enable_access_logs` + `access_logs_bucket`.

## Outputs

| Name | Description |
|------|-------------|
| alb_arn | ARN of the load balancer |
| alb_dns_name | DNS name of the load balancer |
| target_group_arn | ARN of the target group |

## Security Notes

- `drop_invalid_header_fields = true` is always set.
- Access logging is on by default; a bucket must be supplied or plan fails.
- When a certificate is supplied, HTTP automatically redirects to HTTPS with a modern TLS policy.
