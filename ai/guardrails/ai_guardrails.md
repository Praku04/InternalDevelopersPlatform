# AI Guardrails

These rules are enforced structurally (schema validation, whitelisted
operations, separate IAM roles) — not just as prompt instructions the model
is asked to follow. The AI orchestration layer never holds credentials
capable of violating them.

1. Never bypass approval.
2. Never invent AWS resources.
3. Never claim deployment succeeded without deployment evidence.
4. Never expose credentials.
5. Never execute arbitrary commands.
6. Never modify production without authorization.
7. Always prefer approved modules.
8. Always validate Terraform.
9. Always run security checks.
10. Never destroy infrastructure without explicit authorization.
11. Require additional approval for destructive operations.
12. Explain why generated code was required.

## How this is enforced (not just prompted)

| Guardrail | Structural enforcement |
|---|---|
| No direct `apply`/`destroy` | `BedrockExecutionRole` has no Terraform/deployment permissions; only `TerraformDeploymentRole`, assumed by the deployment engine, can apply |
| No arbitrary AWS CLI | AI never receives AWS credentials; it emits a schema-validated Deployment Specification, nothing else |
| No approval bypass | Approval status lives in the backend's Approval Engine, not in the AI's output — a `"status": "approved"` field from the model is never trusted |
| No invented state | AI Operations Assistant queries DynamoDB/inventory tables before answering; it does not answer from model memory alone |
| No untrusted structured output | Every AI response is validated against `ai/schemas/*.schema.json` before use |
