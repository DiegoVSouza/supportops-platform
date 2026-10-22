# PLAN — API identity with RFC 7662

## allowed_write_paths
- `supportops_platform/auth/**`, `supportops_platform/api/app.py`, `supportops_platform/mcp/identity.py`
- `tests/test_api_security.py`, `tests/test_mcp_oidc.py`, `scripts/check_keycloak_oidc.py`
- `infra/keycloak/p05-local-realm.json`
- `docs/harness/phases/015/**`, `docs/harness/security.md`, `docs/harness/feature_list.json`, `docs/harness/progress.md`
- `artifacts/evidence/phase-015-*`

## forbidden_changes
- No external issuer or production credential unless supplied by the user.
- No API route/schema changes; no token or secret logging.
- No change to accepted-job authorization or claim that token revocation cancels queued work.
- No live model/provider call, package publish, or deployment.

## Tasks
1. Extract the generic RFC 7662 response validation into the API auth boundary; keep MCP-specific scope checks at the MCP route/resource boundary.
2. Add explicit API identity configuration with fail-closed behavior while retaining local fake-mode HS256.
3. Exercise authorization, denial, revocation and failure cases through API tests and a disposable Keycloak TCP flow.
4. Run fast and full local gates, save command/exit/output evidence, and update harness status precisely.

## Verification
- `uv run --locked python scripts/check_fast.py`
- `uv run --locked python scripts/check_full.py` with isolated Compose project and free ports
- `python scripts/check_keycloak_oidc.py` against disposable local Keycloak
- `python scripts/harness/check.py --root . --project p05 --docs`

Plan review: accepted. Implementation completed within the approved API identity boundary.
