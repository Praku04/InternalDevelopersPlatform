# Deployment Flow (Planned)

```
Portal → API → Deployment Specification → Approved Module
       → Terraform Plan → Security Scan → Approval → Jenkins
       → Terraform Apply → AWS → Deployment Status → Dashboard
```

`apply` and `destroy` are whitelisted operations executed only through the
authorized deployment workflow (Jenkins in Phase 1's target design), never
exposed directly to the frontend or to the AI. See Section 17 / 22 of the
original build prompt.
