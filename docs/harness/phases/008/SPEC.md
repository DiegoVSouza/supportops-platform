# SPEC — PostgreSQL pgvector and authenticated TCP MCP gates

## Objective
Exercise pgvector migration/hybrid retrieval against isolated PostgreSQL, authenticated MCP through TCP, and available product service path using already pinned wheels; reconcile traces/evals/docs.

## Acceptance
- Every executed gate records exact command, exit code, and output in rtifacts/evidence/.
- PASS applies only to the named layer; skipped/unavailable gates are INCOMPLETE and model evaluation without cassettes is PENDING.
- No project product code changes are planned in this evidence-first phase unless a concrete defect is found and separately scoped.
