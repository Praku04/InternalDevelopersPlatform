# AI Flow (Planned — Bedrock integration lands in a later phase)

For a natural-language request, the AI must not immediately generate
Terraform. It follows this sequence:

1. Understand request
2. Extract requirements
3. Identify environment
4. Identify resources
5. Search module registry (`GET/POST /api/v1/modules`, `/modules/search`)
6. Search Terraform repository
7. Search security policies
8. Determine reusable modules
9. Determine missing capabilities
10. Build deployment specification
11. Present summary to user
12. Generate Terraform (only for missing capabilities)
13. Validate
14. Security scan
15. Cost estimate
16. Approval
17. Deployment

Raw model output is never trusted directly. It must parse into
`AIDeploymentRecommendation` (`backend/app/models/deployment.py`), which is
schema-validated against `ai/schemas/deployment_specification.schema.json`
before any downstream step uses it.
