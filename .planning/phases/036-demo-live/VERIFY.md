# Verify — 036 demo-live-v1

Status: PASS_LOCAL_OFFLINE. No provider was contacted. The live smoke is `PENDING` (W4 smoke, then W8).

| Check | Command | Result | Evidence |
| --- | --- | --- | --- |
| New tests, fake transport | `uv run --locked pytest tests/test_demo_live.py` | 15 passed, 2 skipped with a stated reason | `artifacts/evidence/demo-live-v1/pytest-full.txt` |
| Same tests against PostgreSQL 16 | `P05_TEST_PG_DSN=... pytest tests/test_demo_live.py -v` | 17 passed, exit 0 | `artifacts/evidence/demo-live-v1/pytest-demo-live-postgres.txt` |
| Whole suite | `uv run --locked pytest` | exit 0 | `artifacts/evidence/demo-live-v1/pytest-full.txt` |
| OpenAPI | `python scripts/export_openapi.py --check` | PASS | regenerated `openapi.yaml` |

Not run: `check_full.py` service gate, a real Groq call, the 429 behavior of the real provider, rate-limit header names on a real response (the code reads `x-ratelimit-remaining-tokens` and `x-ratelimit-remaining-requests`, from Groq's documentation). Version bump and wheel are left to W8.
