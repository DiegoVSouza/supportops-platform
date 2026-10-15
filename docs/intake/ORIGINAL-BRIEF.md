# Original P05 brief

Source: `specs/P05-supportops-platform.md` in the lab curriculum. All monorepo paths are adapted under this independent repository. P01–P04 code is integrated only through locally built, versioned, approved packages; no sibling imports and no external publication.

## Preserved goals and acceptance
- Supervisor/worker support triage with RAG, citations, billing/CRM MCP tools, authenticated tenant-scoped API, async execution and HITL approvals.
- End-to-end guardrails, evals, observability, dashboards, local Compose, Terraform plan, and benchmarks in fake/replay mode.
- Tenant A cannot read tenant B; malicious KB content cannot cause prohibited tools; high refunds pause for approval; duplicate worker recovery does not repeat effects.
- OpenAPI contract freezes after phase 003. Numbers require real `artifacts/runs/` or remain `PENDING`.
- No cloud deployment, package publication, fine-tuning, or full web UI.
