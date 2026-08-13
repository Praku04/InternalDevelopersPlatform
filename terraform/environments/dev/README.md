# dev environment

Per-application Terraform root configurations for the dev environment
are generated here by the deployment engine (Section 22 of the build
prompt), composing modules from `terraform/modules/`. Not yet populated —
Phase 1 ships the modules themselves and their registry metadata; the
generation of environment root configs happens once the deployment
pipeline (Phase 6+) is implemented.
