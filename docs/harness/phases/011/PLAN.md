# PLAN — Add OAuth token introspection to authenticated MCP

allowed_write_paths: supportops_platform/mcp/identity.py; supportops_platform/mcp/runtime.py; tests/**; scripts/check_services.py; scripts/check_fast.py; scripts/check_full.py; scripts/export_openapi.py; scripts/check_wheel_consumer.py; docs/harness/phases/011/**; docs/harness/feature_list.json; docs/harness/progress.md; docs/harness/agent-card.md; docs/harness/security.md; docs/harness/sources.lock.json; docs/decisions/ADR-008-mcp-token-introspection.md; artifacts/evidence/**; artifacts/packages/**; pyproject.toml; uv.lock; supportops_platform/__init__.py; openapi.yaml; .env.example; docker-compose.services.yml
forbidden_changes: root roadmap; sibling source imports; shared kit; unrelated files/stacks; weakened tests; external deploy/publish/push/PR/merge; Terraform apply; live/paid LLM; publishing packages; storing bearer/client secrets in source, evidence, traces, or logs.

llm_mode: fake

dependencies: installed MCP SDK 2.3.0 TokenVerifier protocol, existing httpx client, local loopback test endpoint, Python 3.13.12, uv lock/cache and existing isolated P05 stack. Use official MCP and OAuth 2.0 introspection documentation; record versions and sources.

## Observable tasks
1. Add focused red tests for active, revoked, malformed, wrong-issuer/audience, expired, and unreachable introspection results.
2. Implement a fail-closed RFC 7662 verifier and compose it with the local short-lived delegated-token verifier; external tokens are introspected on every MCP request.
3. Prove active-to-revoked behavior through MCP over loopback TCP using a local protocol test issuer; preserve service isolation and worker delegation behavior.
4. Run unit/fast/package/full gates, record evidence, update security/status/source lock, and release a new local patch wheel with provenance.

## Checks
Red then green focused tests; `uv run --locked python scripts/check_fast.py`; unit suite; existing package gate; MCP TCP service integration; `uv run --locked python scripts/check_full.py`; OpenAPI check; evidence command/exit/output; diff and staged secret review.

## Stop condition
If local Docker/services are unavailable, keep the corresponding service gate INCOMPLETE and continue unit/contract checks. A local protocol issuer proves RFC 7662 adapter behavior only; mark acceptance against an external provider INCOMPLETE until the user supplies issuer/audience and local test credentials. Keep model evaluation PENDING without traceable model cassettes or explicit live-run authorization. Do not store credentials or tokens in repo/evidence.

## Plan review
Reviewed before implementation: four observable tasks; only P05-owned code/docs/artifacts are writable; internal delegated tokens remain supported; revocation is checked per external MCP request; no source-controlled secrets or live LLM calls.

## Plan amendment
The release updates the OpenAPI package-version metadata without changing routes or schemas, adds blank optional OIDC variables to `.env.example`, and forwards OIDC settings only to the MCP container. These owned paths are now explicit above; no client secret is stored in the repository.

## Plan amendment — isolated Keycloak interoperability gate

Task 3 now includes an isolated Keycloak 26.8.1 dev container with an imported disposable realm, a confidential introspection client, a test user, and a loopback-only published port. A standalone integration check will obtain a user token, introspect it through the implemented RFC 7662 verifier, revoke it at Keycloak, and prove the same token becomes inactive. Existing MCP loopback TCP tests continue to cover the MCP authorization boundary.

Additional allowed_write_paths: docker-compose.oidc-test.yml; infra/keycloak/**; scripts/check_keycloak_oidc.py; docs/harness/sources.lock.json; docs/harness/phases/011/**; artifacts/evidence/**.

Additional dependencies: Docker Engine; free isolated host port 28180; official Keycloak image quay.io/keycloak/keycloak:26.8.1; local image pull availability. Test-only bootstrap/client/user credentials may appear only in disposable test configuration and must be clearly labeled; never use real credentials or save issued bearer tokens.

Updated checks: verify port 28180 is unoccupied; `docker compose -p p05-oidc-011 -f docker-compose.oidc-test.yml config --quiet`; start only the dedicated Keycloak service; wait for readiness; run `uv run --locked python scripts/check_keycloak_oidc.py`; save commands, exit codes and redacted output; stop only the `p05-oidc-011` stack created for this gate. Preserve all other stacks. If Keycloak cannot start or port is occupied, record INCOMPLETE and leave unrelated containers untouched.

Stop condition: local Keycloak proves interoperability with that local provider only. External issuer acceptance, production configuration, API token revocation, and propagation to queued jobs remain INCOMPLETE. Model evaluation remains PENDING without traceable model cassettes or live-run authorization.

## Plan amendment — isolated wheel consumer database

Task 4's 0.4.2 wheel consumer smoke will use a disposable PostgreSQL/pgvector service in the same task-owned Compose project, published only on verified-free loopback port 26433. Never point the consumer at the already-running P05 PostgreSQL service because the smoke applies migrations. Start only `postgres-consumer`, use a unique temporary consumer database, and remove only the task-owned `p05-oidc-011` stack after checks.

Additional allowed_write_paths: artifacts/packages/**; artifacts/evidence/**; docs/harness/sources.lock.json; docker-compose.oidc-test.yml; docs/harness/phases/011/**.

Checks: verify 26433 free; validate Compose config; start `postgres-consumer` only; install the built 0.4.2 wheel into a fresh isolated target; run `scripts/check_wheel_consumer.py` using the disposable PostgreSQL DSN; record commit, artifact SHA-256, commands, exit codes and redacted output; stop only `p05-oidc-011`. If the port is occupied or service cannot start, mark the consumer smoke INCOMPLETE and do not use pre-existing databases.

## Plan amendment — exercise Keycloak bearer at MCP TCP boundary

The Keycloak integration check will use its issued bearer against a real loopback Streamable HTTP MCP server on verified-free port 28181 before revocation, then prove the same request is rejected after revocation. The test realm's audience mapper includes the exact MCP resource URI used by that ephemeral test server. This joins real local-provider introspection with the already existing protocol-contract TCP test.

Additional dependencies: free loopback port 28181 and a local uvicorn test server. Verify the port before binding; do not alter the pre-existing P05 MCP service on 28001. The test server runs in-process and is stopped by the check.

Updated acceptance: Keycloak token must pass the MCP SDK authorization boundary and call an allowlisted read-only tool; after provider revocation, the same token must receive HTTP 401. Record no token or credential values.
