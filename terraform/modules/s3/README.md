# S3 Module

Approved enterprise S3 module. Public access is always blocked and
encryption is always enforced (SSE-KMS if a key is supplied, otherwise
SSE-S3/AES256). Versioning, server access logging, and lifecycle rules for
noncurrent versions are supported.

## Capabilities

- `encryption`
- `public-access-blocked`
- `versioning`
- `logging`
- `lifecycle-policy`

## Supported Environments

`dev`, `uat`, `prod`

## Inputs

See `variables.tf`. Key inputs: `versioning_enabled`, `kms_key_id`,
`enable_logging` + `logging_target_bucket`, `lifecycle_enabled`.

## Outputs

| Name | Description |
|------|-------------|
| bucket_id | Name of the bucket |
| bucket_arn | ARN of the bucket |

## Security Notes

- `aws_s3_bucket_public_access_block` is unconditionally applied with all four settings `true`.
- Encryption cannot be disabled through this module.
