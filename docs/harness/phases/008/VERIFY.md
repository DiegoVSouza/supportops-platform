# VERIFY — PostgreSQL pgvector and authenticated TCP MCP gates

## Verification record

| Layer / requirement | Command | Exit code | Evidence path | Status |
| --- | --- | ---: | --- | --- |
| PostgreSQL migration, pgvector indexes, tenant-filtered hybrid retrieval | `uv run --locked python artifacts/evidence/phase-008-service-gates.py` | 0 | `artifacts/evidence/phase-008-service-gates-rerun.txt` | PASS service query; deterministic fake embeddings and psycopg test adapter |
| MCP bearer auth, tenant boundary, missing-token denial over TCP | same service-gates command | 0 | `artifacts/evidence/phase-008-service-gates-rerun.txt` | PASS local TCP with test verifier; external identity INCOMPLETE |
| Approved wheel/package gate, 77 tests, retrieval fixtures, OpenAPI check | `.\.venv\Scripts\python.exe scripts/check_full.py` | 2 | `artifacts/evidence/phase-008-full-gate-rerun.txt` | Local checks PASS; product acceptance INCOMPLETE |
| Durable API→P04 worker→P01 agent path with PostgreSQL/Redis | Not implemented in current runtime | — | `artifacts/evidence/phase-008-full-gate-rerun.txt` | INCOMPLETE |
| Replay/model quality, cost, comparable latency | No cassettes or authorized live runs | — | `docs/harness/feature_list.json` | PENDING |

## Review checklist
- [x] Exact commands, exit codes, and output are saved.
- [x] Versioned package provenance and OpenAPI compatibility remain checked.
- [x] No sibling-source imports or live model calls were used.
- [x] Feature, progress, agent-card, and source-lock status matches evidence.
- [x] Staged changes are limited to phase evidence/state/docs and contain no credentials.
