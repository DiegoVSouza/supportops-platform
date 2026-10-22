# VERIFY — External identity at the API boundary

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| API auth contract tests | `uv run --locked pytest tests/test_api_security.py tests/test_mcp_oidc.py` | 0 | `artifacts/evidence/phase-015-api-auth-tests.txt` | PASS; 28 passed |
| Local Keycloak API and MCP token revocation | `uv run --locked python scripts/check_keycloak_oidc.py` | 0 | `artifacts/evidence/phase-015-keycloak-api.txt` | PASS_LOCAL_KEYCLOAK_26.8.1; API and MCP return 401 after revocation |
| Fast gate | `uv run --locked python scripts/check_fast.py` | 0 | `artifacts/evidence/phase-015-fast.txt` | PASS |
| Full local gate | `uv run --locked python scripts/check_full.py` with isolated ports/project | 0 | `artifacts/evidence/phase-015-full-gate.txt` | PASS_LOCAL_FAKE_MODE; 104 tests |
| Harness docs gate | `python scripts/harness/check.py --root . --project p05 --docs` | 0 | `artifacts/evidence/phase-015-harness-docs-check.txt` | PASS (0 errors, 0 warnings) |
| External issuer acceptance | Await issuer selection and credentials/config | — | — | INCOMPLETE |
| Revocation of previously accepted jobs | Separate authorization-policy phase and decision | — | — | OUT OF SCOPE |

No acceptance claim is made until each command and its output are recorded.
