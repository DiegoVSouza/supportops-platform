# VERIFY — P05 Redis queue transport

Status: PASS_LOCAL_SERVICE; external IdP and model-quality evaluation remain
INCOMPLETE/PENDING as recorded in their existing gates.

## Evidence

- `uv run --locked python -m pytest -q`: 104 passed.
- `uv run --locked python scripts/verify_packages.py`: PASS; P04 0.1.4 wheel
  version and SHA-256 match `docs/harness/sources.lock.json`.
- `uv run --locked python scripts/export_openapi.py --check`: PASS.
- `docker compose -f docker-compose.services.yml config --quiet`: PASS with
  temporary test signing keys supplied through the environment.
- `uv run --locked python scripts/check_full.py`: PASS, exit 0. Evidence is in
  `artifacts/evidence/phase-017-full-gate.txt`.
- P05 0.4.3 wheel built from source commit `a77a16c2f461b16a674323fa2205cd4943a12ed5`
  and installed into an isolated target. The packaged migration applied against
  disposable PostgreSQL 16/pgvector 0.8.7; see `phase-017-wheel-build.txt` and
  `phase-017-wheel-consumer.txt`.
- The isolated service run verified PostgreSQL/pgvector, Redis Streams delivery,
  API restart recovery, MCP authorization, tenant isolation, authorization lease
  expiry, human approval, worker crash recovery after effect, one effect row,
  alerts, traces and non-root containers. It removed only its temporary Compose
  project and volumes.
- Model quality, provider cost/latency and external IdP acceptance remain
  PENDING/INCOMPLETE; the fake evaluation is explicitly fixture-only.
