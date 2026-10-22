# VERIFY — External identity at the API boundary

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| API auth contract tests | `uv run --locked pytest tests/test_api_security.py tests/test_mcp_oidc.py` | — | `artifacts/evidence/phase-015-api-auth-tests.txt` | PENDING |
| Local Keycloak revocation over API TCP | `uv run --locked python scripts/check_keycloak_oidc.py` | — | `artifacts/evidence/phase-015-keycloak-api.txt` | PENDING |
| Fast gate | `uv run --locked python scripts/check_fast.py` | — | `artifacts/evidence/phase-015-fast.txt` | PENDING |
| Full local gate | `uv run --locked python scripts/check_full.py` with isolated ports/project | — | `artifacts/evidence/phase-015-full-gate.txt` | PENDING |
| Harness docs gate | `python scripts/harness/check.py --root . --project p05 --docs` | — | `artifacts/evidence/phase-015-harness-docs-check.txt` | PENDING |
| External issuer acceptance | Await issuer selection and credentials/config | — | — | INCOMPLETE |
| Revocation of previously accepted jobs | Separate authorization-policy phase and decision | — | — | OUT OF SCOPE |

No acceptance claim is made until each command and its output are recorded.
