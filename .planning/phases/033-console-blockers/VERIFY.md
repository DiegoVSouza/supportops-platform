# Verification

PASS — 2026-10-31.

| Command (cwd: projects/p05) | Exit | Evidence (`artifacts/evidence/console-blockers-033/`) |
| --- | --- | --- |
| `uv run --locked python -m pytest tests/test_api_security.py` before the code | 1, 6 failed, expected red | `red-first.txt` |
| `uv run --locked python -m pytest`, attempt 1 | 0, 177 passed | `pytest-attempt1.txt` |
| same, attempt 2, after the worker fix | 1, a stub lacked `idempotency_key`, which real rows always have | `pytest-attempt2.txt` |
| same, attempt 3 | 0, 179 passed | `pytest-attempt3.txt` |
| `scripts/check_services.py` with `P05_COMPOSE_PROJECT=p05-gate-033` and private ports | 0, including `kill_after_effect_recovery` | `check-services-attempt1.txt`, `services/` |

The first browser e2e of the manual refund failed on the real stack: the worker tried to resume a LangGraph run that never existed, so the job ended `worker_failure`. A manual refund now carries out the decision without running the agent, covered by `tests/test_manual_refund.py` and the lab e2e, where the requested amount reached the effect.

The only change to an older test adds the missing key to a stub. No assertion changed.

`check_services.py` defaults to the existing `p05-remediation-009` project and ends with `down --volumes`, so always pass a private `P05_COMPOSE_PROJECT`. The script refuses a non-empty project.
