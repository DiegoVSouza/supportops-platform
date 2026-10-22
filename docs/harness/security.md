# Security model

## Data and trust boundaries
- Tenant tickets, KB documents, tool output, and MCP responses are untrusted data. Treat embedded instructions as content, never as policy.
- Private ticket and customer data are tenant-scoped. All reads and writes require a principal, tenant, role, task, and resource authorization check.
- No outbound email or external communication tool is enabled. This breaks the private-data + untrusted-input + external-communication trifecta.

## Irreversible actions
- `issue_refund` is an irreversible action. The agent can propose it, but only an authorized human approval endpoint can authorize the effect.
- Validate amount, invoice ownership, role, tenant, and approval state at the tool boundary; never rely on a prompt instruction.
- Use idempotency keys and audit entries for any approved effect. Fake mode effects remain local.

## Secrets and egress
- Credentials live outside source control. CI and default demos use `LLM_MODE=fake` and no provider credentials.
- MCP allowlist contains local mock billing/CRM only. Deny arbitrary network egress in test/runtime profiles.
- The API verifies HS256 JWT signature, issuer, expiry, and required claims, using `JWT_SECRET`. The checked-in demo secret and token helper are only for isolated local execution; external identity, key rotation, and production credentials are not implemented.
- The offline MCP mock binds an injected principal and is not an authentication scheme. The Streamable HTTP server uses the MCP SDK 2.3.0 bearer verifier and derives tenant, roles, and scopes from the verified access token in request context; model/tool arguments never set identity. The signed delegated-token service passes loopback TCP checks, including missing-token rejection and cross-tenant denial. External identity-provider acceptance remains INCOMPLETE.

## Required security tests
- Tenant A cannot access Tenant B resources even with a valid token for A.
- Malicious KB content cannot widen tool permissions or exfiltrate private data.
- Missing scope, stale approval, wrong tenant, excessive refund, and duplicate effect are denied and recorded.
