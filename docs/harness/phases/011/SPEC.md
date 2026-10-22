# SPEC — Verify and revoke external MCP bearer tokens

P05 currently accepts only locally signed HS256 tokens in its network MCP verifier. That does not let a configured OAuth authorization server establish token activity or report revocation. Add an optional OAuth 2.0 token-introspection verifier for the existing Streamable HTTP resource server, retaining the local signer for internal short-lived worker delegation. Introspection must happen for each external-token request, fail closed on inactive, malformed, expired, wrong-issuer, or wrong-audience responses, and never log the bearer or client secret.

Acceptance: unit/contract tests exercise active and revoked RFC 7662 responses and failure cases; an MCP loopback TCP gate proves an active token can call an authorized tool and the same token is denied after introspection reports it inactive. The full fake-mode gate remains green. External IdP compatibility is separately reported INCOMPLETE until run against the user's configured issuer. No public HTTP/MCP route/schema change; no live model/provider calls.

## Local identity-provider acceptance

A disposable Keycloak realm provides a concrete local issuer for this phase. Acceptance additionally requires obtaining a token from that realm, validating its active claims using the configured RFC 7662 verifier, revoking it at Keycloak, and observing the token become inactive. This proves local Keycloak interoperability only; it does not establish compatibility with an external or production identity provider.
