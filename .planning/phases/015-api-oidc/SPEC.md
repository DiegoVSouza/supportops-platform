# SPEC — External identity at the API boundary

P05 currently authenticates API requests with a locally signed HS256 token. Add an optional RFC 7662 verifier for API bearer tokens, using the existing MCP verifier contract after removing resource-specific authorization from token validation. Keep local HS256 tokens available for isolated fake-mode development and internal worker delegation. External identity must be explicitly configured; missing, inactive, expired, malformed, wrong-issuer, wrong-audience, or unreachable introspection responses fail closed with HTTP 401. Authorization scopes remain enforced by each API route and tenant scoping continues to use only verified claims.

Acceptance:
- API dependency supports local tokens in fake mode and the configured introspection verifier for external bearer tokens.
- Contract tests cover active token, revoked/inactive token, timeout, malformed claims, issuer/audience mismatch, missing credentials, and route-level scope denial.
- A disposable local Keycloak integration proves an active token can call an authorized route and the same token is denied after revocation.
- No bearer, client secret, or token response is logged; the API routes and OpenAPI schema remain unchanged.
- `check_fast.py` and the full fake-mode gate pass. External provider acceptance remains separate until run against the user's issuer.

Does not solve revocation for jobs accepted before the original token is revoked; that requires a separate durable authorization policy decision. No live model calls or external deployment.
