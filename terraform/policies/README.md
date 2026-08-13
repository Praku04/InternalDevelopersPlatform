# Terraform Policies

Sentinel/OPA-style policy-as-code for the Policy Engine (Section 18) lands
here in a later phase. Phase 1 enforces the highest-value checks directly
inside the modules themselves (mandatory EBS/S3 encryption, blocked S3
public access, no unrestricted SSH/RDP) via Terraform preconditions and
variable validations — see each module's README "Security Notes" section.
