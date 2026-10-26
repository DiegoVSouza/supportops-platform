# Phase 017 — Live campaign preparation

## Goal

Prepare P05's reviewed synthetic RAG, tenant-security, MCP, authorization, and delivery dataset plus a guarded campaign reservation dry-run. The eventual live evaluation must use the actual integrated API/Redis worker/PostgreSQL retrieval/installed orchestration/MCP/Groq path with correlated content-free OTLP traces.

## Current evidence and constraints

- Revalidated repository HEAD: `bdffccc744bd3fb1675e990bc32c40f6813766d5` (`feat(rag): run live Groq tasks through the Docker service stack`).
- P05 permits up to USD 2 per task; phase 018's one synthetic RAG task at an estimated USD 0.01 is a narrow prior exception, not campaign approval.
- The prior live service acceptance did not exercise MCP tools and kept refunds blocked. It is not representative of the requested broad security/RAG campaign.
- No credentials, provider calls, Docker mutations, real customer data, external communications, or refund execution are in scope.

## Acceptance criteria

1. A versioned dataset contains 120 unique semantic cases: 36 development and 84 sealed holdout, covering retrieval relevance, grounded answer/citation correctness, unanswerable questions, tenant separation, authorization expiry, injection, cross-tenant tools, duplicate delivery, and refund denial.
2. Every family has at least three unique cases. Inputs use 72 English and 48 Portuguese examples, including adversarial/informal cases. Each case records expected action/tools, required facts/citations, forbidden behavior, rubric, criticality, finite call/token caps, and synthetic tenant/authorization context.
3. Config includes three trials, at most four normal provider calls per trial, per-task and cumulative request/input/output/spend ceilings, fresh confirmation reserve, human review coverage, timeouts/retry/chunk/pacing/wall-clock fields, and budget approval source. New campaign limits remain `PENDING` until reconciled with existing authorization.
4. Dry-run reports the 24-call pilot and 1,440-call full-campaign ceiling without SDK construction, credential reads, network, or Docker mutation. Generation fails before dispatch on missing approval, quota, model preflight, cap, or reviewer capacity.
5. Graders and offline tests reject cross-tenant reads/writes, unauthorized tool effects, real refunds, injection bypass, fabricated citations, duplicate committed effects, expired authorization and silent fake fallback. Zero-call safety denials are reported separately from model-generated trials.
6. Holdout consumption is tracked; any fix informed by holdout requires at least 20 fresh unique confirmation cases before generalization claims. Human review missing or unproven means `INCOMPLETE`.

## Out of scope

Provider execution, customer data, real refunds or messages, public deployment, public ports, cross-project source imports, package/API changes, paid budget increases, or changing historical campaign evidence.
