# Verify 037

- [x] New tests red before the change, green after (`artifacts/evidence/toolkit-limits-037/red.txt`, `green.txt`)
- [x] `tests/test_demo_live.py` passes with no network (two tests skip without Postgres)
- [x] `python scripts/check_fast.py` exit 0 (`artifacts/evidence/toolkit-limits-037/check-fast.txt`)
- [x] Deployed on Fly with one live run under the limit (`artifacts/evidence/status-reconcile/`)
