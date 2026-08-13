# Terraform Module Development

Every approved module under `terraform/modules/<name>/` must contain:

- `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`
- `README.md` documenting capabilities, inputs, outputs, and an example
- `module.json` — registry metadata (see `ai/schemas/module_metadata.schema.json`)
  with `status: "approved"` and `security_status: "approved"` only after
  human review

AI-generated modules (Section 14/15 of the original build prompt) start at
`status: "pending_review"` and go through the Git branch → PR → CI →
human review flow described in `docs/architecture/ai-flow.md` before a
maintainer flips them to `approved`. Not yet implemented in this phase.
