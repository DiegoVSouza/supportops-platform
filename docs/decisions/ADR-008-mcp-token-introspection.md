# ADR-008: Introspect external bearer tokens at the MCP boundary

## Status

Accepted and verified against a disposable local Keycloak 26.8.1 realm. Acceptance against an external identity provider remains pending until its issuer and test credentials are configured.

## Context

P05's Streamable HTTP server previously trusted only short-lived locally signed HS256 tokens. That supported the local worker but did not give an authorization server an opportunity to report that an external access token had been revoked.

## Decision

- Keep the local signer for internal worker delegation.
- Optionally configure `MCP_OIDC_INTROSPECTION_URL`, `MCP_OIDC_CLIENT_ID`, `MCP_OIDC_CLIENT_SECRET`, `MCP_OIDC_ISSUER`, and `MCP_OIDC_AUDIENCE` for direct MCP callers.
- Submit introspection as an authenticated HTTP POST and validate active state, issuer, audience, subject, tenant, roles, scope, and expiry.
- Introspect every external MCP request without a positive-result cache. Fail closed on errors or invalid responses.
- Require HTTPS for remote endpoints; allow HTTP only for loopback development/test endpoints.
- Keep the API's local HS256 auth and the durable worker's acceptance-time authorization snapshot unchanged. Revocation is therefore not propagated to a job after it has been accepted.
- Do not log bearer tokens or client credentials. Store actual configuration only in an operator-managed environment, never in Git.
- For RFC 7662 responses that omit optional `sub`, use the provider's non-empty `username` claim as the MCP principal subject. The Keycloak 26.8.1 local gate exercises this behavior; external provider claim semantics still require validation.

## Compatibility

No HTTP route or MCP tool schema changes. Bump the P05 package to 0.4.2 because the supported runtime authentication behavior and configuration changed. Existing internal worker tokens continue to use the local verifier.

## Verification and limits

The local protocol issuer test exercises active-to-revoked behavior over MCP loopback TCP. The Keycloak 26.8.1 container test obtains a token from a real local issuer, introspects its claims, calls an allowlisted read tool over MCP loopback TCP, revokes the token, and confirms the same MCP resource returns HTTP 401. Neither test represents an external/production provider. API bearer auth and revocation of already-queued work remain outside this decision.

Sources: [RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html); [MCP Python SDK authorization](https://py.sdk.modelcontextprotocol.io/run/authorization/); [Keycloak Docker](https://www.keycloak.org/getting-started/getting-started-docker); [Keycloak realm import](https://www.keycloak.org/server/importExport).
