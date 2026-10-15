# Intake decisions — P05 SupportOps Platform

- Product: multi-tenant support triage platform with authenticated API, asynchronous workers, RAG citations, MCP billing/CRM tools, human approval for sensitive actions, and end-to-end traces.
- Success: fake-mode E2E ticket flow returns a cited response; high refund pauses for approval; tenant isolation and injection/tool-policy tests deny prohibited access; a single trace links API through persistence.
- Profile: `agent-saas`; agent, RAG, MCP tools, trace loop, and governance are justified by multi-tenant private ticket data and untrusted KB content.
- Runtime: custom loop for predictable, testable orchestration; provider calls remain disabled in CI (`LLM_MODE=fake`). Live mode requires separate budget and authorization.
- Risk: full governance; each tool checks tenant, principal, role, task state, and approval state. Refund is irreversible and requires HITL. The Rule of Two is satisfied by `external_comms: false`: outputs may be generated but no outbound communication tool exists.
- Dependencies: local development begins with contract doubles. Real integration is gated on approved, versioned P01–P04 packages installed from local artifacts; record source repo, commit, package version, and SHA-256. Never import sibling source paths or publish externally.
- Budget: configured ceiling is $2/task, but this task uses no paid LLM calls. Metrics from fake runs are control-flow metrics only, not model quality.
- API: `openapi.yaml` v1; freeze after phase 003. Changes require ADR, version bump, and consumer update.
