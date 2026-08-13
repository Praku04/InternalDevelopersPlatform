# AI Prompt Engineering (Planned — Bedrock integration lands in a later phase)

Prompt templates will live under `ai/prompts/`. Not yet populated in Phase 1.
Every AI response must be structured JSON validated against
`ai/schemas/deployment_specification.schema.json` before use — see
`backend/app/models/deployment.py::AIDeploymentRecommendation`.
