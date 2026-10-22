# SPEC — Complete remaining authorized local remediation

## Intake
Implement durable PostgreSQL product repositories and P04 SQS worker integration, Redis rate limits, native pgvector retrieval, authenticated TCP MCP with signed JWT verification, HITL resume, correlated service traces, adversarial/evaluation gates, and reproducible local infrastructure.

Baseline: phase 008 commits and feature inventory; independent repository on main, clean before this phase. LLM_MODE=fake; approved local wheel boundaries remain mandatory.

## Acceptance
Every implemented path has meaningful contract and real service checks. Each executed gate records command, exit code and output under artifacts/evidence/. Required unavailable checks return INCOMPLETE/nonzero. Replay/model quality, cost and comparable latency remain PENDING without traceable cassettes. No external identity service or live provider is required for signed local authentication.

## Contracts
Additive product API/runtime changes require ADR-006, version 0.4.0, regenerated OpenAPI and updated contract consumers. Existing routes and in-memory test behavior remain compatible.
