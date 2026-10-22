# VERIFY — MCP OAuth token introspection and revocation

| Layer / gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| RFC 7662 verifier unit/contract and MCP loopback TCP active-to-revoked flow | `uv run --locked pytest tests/test_mcp_oidc.py -q` | 0 | `artifacts/evidence/phase-011-introspection-green.txt` | PASS_LOCAL_PROTOCOL; this uses a local test issuer |
| Keycloak-issued token calls MCP over loopback TCP; provider revocation then yields HTTP 401 | `uv run --locked python scripts/check_keycloak_oidc.py` with isolated compose project `p05-oidc-011` | 0 | `artifacts/evidence/phase-011-keycloak-oidc.txt` | PASS_LOCAL_KEYCLOAK_26.8.1; not external-provider or production acceptance |
| Unit/contract/package suite | `uv run --locked pytest -q` | 0 | `artifacts/evidence/phase-011-unit.txt` | PASS; 103 passed |
| Fast gate | `uv run --locked python scripts/check_fast.py` | 0 | `artifacts/evidence/phase-011-fast.txt` | PASS |
| OpenAPI package version and compatibility paths | `uv run --locked python scripts/export_openapi.py --check` | 0 | `artifacts/evidence/phase-011-openapi.txt` | PASS; version 0.4.2, routes unchanged |
| Compose configuration | `docker compose -f docker-compose.services.yml config --quiet` with local-only placeholder variables | 0 | `artifacts/evidence/phase-011-compose-config.txt` | PASS |
| Fake control regression | `uv run --locked python scripts/check_quality.py` | 0 | `artifacts/evidence/phase-011-fake-quality.txt` | PASS fixtures only; model quality PENDING |
| Full gate with existing Docker service stack intentionally not touched | `uv run --locked python scripts/check_full.py --skip-services` | 2 | `artifacts/evidence/phase-011-full-gate-without-existing-stack.txt` | INCOMPLETE by design; unit/package/fake/retrieval gates passed, service-stack gate omitted |
| External identity provider acceptance | Local Keycloak is verified; external issuer/audience, production credentials/TLS and API identity integration are not configured | — | `docs/harness/feature_list.json`; `docs/harness/sources.lock.json` | INCOMPLETE |
| API token revocation and revocation of accepted durable jobs | Not implemented by this MCP-only adapter; queued jobs keep the documented authorization snapshot | — | `docs/decisions/ADR-008-mcp-token-introspection.md` | INCOMPLETE |
| Replay/model quality/cost/comparable latency | No valid model cassette for two configurations and no live run authorized | — | `docs/harness/feature_list.json` | PENDING |

No live model, external issuer, paid provider call, deployment, or publication was performed. The local Keycloak test is a real provider interoperability gate for Keycloak 26.8.1; external IdP acceptance, API identity integration, and revocation of accepted queued jobs remain incomplete.
