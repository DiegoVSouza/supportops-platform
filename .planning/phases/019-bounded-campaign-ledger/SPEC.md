# Phase 019 — Bounded campaign ledger for P05

## Goal

Add durable P05 campaign reservations, atomic cumulative caps, an OS-level campaign lease, and content-free read-only resume inspection. Preserve the recovered Docker stack and keep campaign dispatch disabled until human, quota, budget, and model gates are evidenced.

## Starting evidence

- Phase 017 prepared 120 synthetic RAG/tool/security cases (36 development / 84 holdout; 72 English / 48 Portuguese), with a 24-call pilot, 1,440-call primary campaign, and 240-call fresh confirmation reserve.
- The profile allows up to USD 2 per task, but the previous local RAG evaluation was explicitly limited to USD 0.01 estimated. It does not authorize the broad campaign. Paid campaign spend remains USD 0.
- Human dataset/rubric review, cumulative limits, provider quota, runtime candidate identity, model preflight, confirmation funding, pacing, and maximum campaign duration remain pending.
- P05 contains sensitive tenant/RAG contexts. The campaign ledger may store identifiers and usage metadata only; it must never store queries, retrieved text, answers, citations, tool arguments, or customer data.
- A Docker restart recovery phase has just validated the owned local stack. This ledger phase must not restart, stop, rebuild, recreate, or mutate service containers/volumes.

## Acceptance criteria

1. Append-only SQLite events reserve calls/tokens/cost before attempts, reconcile known usage, retain full reservations when usage is unknown, and prohibit rerunning uncertain/completed trials.
2. Cumulative request/token/estimated-cost caps are atomic across P05 campaign IDs and concurrent reservations.
3. OS lease prevents simultaneous local campaign execution and releases normally. Lease metadata contains no tenant, trace, query, answer, citation, tool, or credential data.
4. `--resume CAMPAIGN_ID --dry-run` opens the ledger read-only, returns sanitized attempt/usage metadata, rejects unknown/empty campaigns with exit 2, and never dispatches an attempt.
5. Dry-run and blocked execution do not read `.env`, initialize provider clients, access the network, contact services, perform refund/message/tool effects, or mutate Docker. Generation stays blocked for every unresolved approval/limit.
6. Focused ledger and campaign tests plus the full fake gate with service checks explicitly skipped pass; the prior isolated-service acceptance remains the service evidence for this phase.

## Out of scope

Groq dispatch, tenant/RAG/MCP runtime changes, live Docker changes, cross-project accounting, quota/budget increases, dataset/rubric edits, customer data, real refunds/messages, public deployment, or external effects.

## Status

`PLANNED`; broad model evaluation and local-live promotion remain `INCOMPLETE`.
