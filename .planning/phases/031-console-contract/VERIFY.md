# Verification

PASS — 2026-10-30, offline fake scope. Live service acceptance of the new route runs through the root stack check.

| Command (cwd: projects/p05) | Exit | Evidence |
| --- | --- | --- |
| `uv run --locked pytest -q tests/test_api_security.py` before the code | 1, expected red | `artifacts/evidence/console-contract-031/red-first.txt` |
| `uv run --locked pytest -q` attempt 1 | 1, version pin not yet bumped, and a sandbox temp directory denied | `pytest-attempt1.txt` |
| `uv run --locked pytest -q --basetemp ...` attempt 2 | 0 | `pytest-attempt2.txt` |
| `uv run --locked python -m pytest` after the role rule, attempt 3 | 0, 167 passed, 2 warnings in 16.77s | `pytest-attempt3.txt` |
| `uv run --locked python scripts/export_openapi.py --check` | 0 | command output above; contract regenerated |
| `python scripts/check_fast.py` | 0 | same run |

The only pre-existing test changed is the version pin in `test_health_is_fake_by_default_and_openapi_is_versioned`, required by the intended bump. No assertion was weakened.
