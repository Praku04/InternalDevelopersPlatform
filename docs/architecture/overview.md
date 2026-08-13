# Architecture Overview

## Core principle

Reuse approved Terraform modules whenever possible. Generate new Terraform
only when the requested capability does not already exist. The AI never
directly bypasses security controls or approval workflows.

## Request flow

```
User → Portal → Backend → Bedrock → Structured Deployment Specification
     → Policy Engine → Terraform → Security Validation → Cost Validation
     → Approval → Controlled Deployment Role → AWS
```

Amazon Bedrock is an orchestration/recommendation layer. It produces a
schema-validated Deployment Specification (see
`ai/schemas/deployment_specification.schema.json`); it never receives
credentials capable of running `terraform apply`, `terraform destroy`,
arbitrary AWS CLI commands, or IAM changes. See `ai/guardrails/ai_guardrails.md`.

## Phase 1 scope (this repository state)

Implemented:
- Repository structure
- Terraform modules: `vpc`, `ec2`, `security-group`, `alb`, `s3` (each with
  `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`, and a
  `module.json` registry entry)
- Module metadata schema and deployment specification schema
- Backend (FastAPI): module registry endpoints, deployment request
  endpoints backed by an in-memory store, a Terraform root-config generator
  that composes approved modules (vpc → security-group → ec2 → alb → s3)
  from a DeploymentSpecification, a whitelisted TerraformEngine
  (`fmt`/`init`/`validate`/`plan` only — no `apply`/`destroy` methods exist
  on the class at all), and health check
- Frontend (Next.js + Tailwind): dashboard, module catalog, an EC2
  self-service form (`/catalog/ec2`) that submits a DeploymentSpecification,
  and a request detail page that triggers Terraform generation/validation
  and displays the step-by-step result
- Docker Compose for local development
- Test suite for the module registry, the deployment specification schema,
  the Terraform generator/engine, and the API endpoints

Not yet implemented (see `docs/architecture/deployment-flow.md` and the
phase plan in the original build prompt): Bedrock integration, `terraform
apply` execution (deliberately unreachable — see Section 17), security
scanning (Checkov/Trivy), cost estimation, approval workflow, Jenkins
deployment, AWS resource inventory, dashboard data, drift detection,
authentication.

## Self-service EC2 flow (implemented end-to-end through `terraform plan`)

```
/catalog/ec2 form → POST /api/v1/requests → DeploymentSpecification stored
→ POST /api/v1/terraform/plan → generator composes vpc+security-group+ec2
  modules → TerraformEngine runs fmt/init/validate/plan
→ result shown on /requests/{id}
```

This stops at `plan`, matching Section 46's MVP shape up through validation
— Jenkins, security scanning, approval, and `apply` are the next steps
(Phases 6–9).

## Module registry

`terraform/modules/<name>/module.json` is the source of truth for what's
approved, its capabilities, and supported environments. The backend's
`ModuleRegistryRepository` (Phase 1: filesystem-backed) reads these files
directly; a later phase swaps this for a DynamoDB-backed `Modules` /
`ModuleVersions` table behind the same interface.
