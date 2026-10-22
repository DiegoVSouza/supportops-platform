# PLAN — Add OAuth token introspection to authenticated MCP

allowed_write_paths: supportops_platform/mcp/identity.py; supportops_platform/mcp/runtime.py; tests/**; scripts/check_services.py; scripts/check_fast.py; scripts/check_full.py; docs/harness/phases/011/**; docs/harness/feature_list.json; docs/harness/progress.md; docs/harness/agent-card.md; docs/harness/security.md; docs/harness/sources.lock.json; docs/decisions/ADR-008-mcp-token-introspection.md; artifacts/evidence/**; pyproject.toml; uv.lock; supportops_platform/__init__.py; artifacts/packages/**
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
