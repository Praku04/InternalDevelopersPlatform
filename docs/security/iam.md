# IAM Architecture (Planned)

Separate least-privilege roles, none of which is `AdministratorAccess`:

- `PortalUserRole`
- `BackendRole`
- `BedrockExecutionRole` — no Terraform/deployment permissions
- `TerraformPlanRole`
- `TerraformDeploymentRole` — the only role that can `apply`
- `SecurityScanRole`
- `InventoryReadRole`
- `ProductionDeploymentRole` — separate, tightly controlled, prod only

Not yet implemented as actual IAM policy documents in this phase — recorded
here as the target design (`infrastructure/platform/iam/` is reserved for
that work).
