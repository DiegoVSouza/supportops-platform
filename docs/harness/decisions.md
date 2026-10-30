# Intake decisions — P05 SupportOps Platform

- Product: multi-tenant support triage platform with authenticated API, asynchronous workers, RAG citations, MCP billing/CRM tools, human approval for sensitive actions, and end-to-end traces.
- Success: fake-mode E2E ticket flow returns a cited response; high refund pauses for approval; tenant isolation and injection/tool-policy tests deny prohibited access; a single trace links API through persistence.
- Profile: `agent-saas`; agent, RAG, MCP tools, trace loop, and governance are justified by multi-tenant private ticket data and untrusted KB content.
- Runtime: custom loop for predictable, testable orchestration; provider calls remain disabled in CI (`LLM_MODE=fake`). Live mode requires separate budget and authorization.
- Risk: full governance; each tool checks tenant, principal, role, task state, and approval state. Refund is irreversible and requires HITL. The Rule of Two is satisfied by `external_comms: false`: outputs may be generated but no outbound communication tool exists.
- Dependencies: local development begins with contract doubles. Real integration is gated on approved, versioned P01–P04 packages installed from local artifacts; record source repo, commit, package version, and SHA-256. Never import sibling source paths or publish externally.
- Budget: configured ceiling is $2/task; phase 018 uses only the explicitly permitted free-plan allowance with an estimated per-run ceiling of $0.01. Fake metrics remain control-flow only, not model quality.
- API: `openapi.yaml` v1; freeze after phase 003. Changes require ADR, version bump, and consumer update.
- Phase 018 decision (2026-10-26): run one opt-in Groq RAG-agent evaluation with synthetic tenant-A content and local retrieval only. Keep MCP/refund tools out of the run, cap estimated exposure at USD 0.01 within the existing USD 2/task budget, and preserve fake CI behavior.

## 2026-10-26 — Live Docker acceptance

Use opt-in Groq live mode with numbered credentials and authenticated model preflight. Preserve deterministic fake defaults and fail closed on provider/contract failures. Only local synthetic acceptance and the designated free allowance are authorized; billed cost remains PENDING. Evidence: artifacts/evidence/live-docker/.

## 2026-10-26 — P05 broad live campaign preparation

Prepared an offline-only P05 campaign dataset, grader checks and reservation dry-runs. The requested row counts and structural contracts are present, but independent semantic review remains pending; campaign generation stays disabled. The displayed call/token ceilings do not authorize spend. Cumulative account quota, budget, human review, runtime identity, and campaign approval remain pending. No Groq call or Docker/service mutation was made. Evidence: `artifacts/evidence/live-campaign-preparation/phase-017-preparation.md`.

## 2026-10-26 — Recover P05 after Docker restart

The user requested diagnosis and repair of restarting P05 services. Application containers used on-failure while PostgreSQL, Redis and telemetry had no restart policy; after daemon restart the application could not resolve its stopped PostgreSQL dependency. Set all service policies to unless-stopped, update only the 19 existing containers owned by p05-remediation-009 and p05-live-020, and start dependencies before application processes without recreating containers or volumes. Keep the live worker explicitly stopped to prevent provider dispatch. Validate actual health and configuration plus a separate isolated fake-mode full service gate. Broad campaign budget/review gates remain unchanged.
## 2026-10-26 — Privacy-safe campaign ledger

Phase 019 adds P05-local reservation accounting, a process lease, and content-free read-only resume inspection. It does not authorize campaign calls, change the prior USD 0.01 single-task exception, or modify any Docker stack. Campaign spend remains USD 0; quota, finite cumulative caps, human review, candidate identity, confirmation funding, and model preflight remain `PENDING`. Ledger records must not contain tenant content.
## 2026-10-30 — Console contract

P06 consumes `openapi.yaml`. ADR-009 adds an approval list and typed responses without changing existing payloads; package moves to 0.4.4.
