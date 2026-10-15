# SupportOps Platform Architecture

P05 is an independently versioned Python service. The API, deterministic retrieval,
tool policy, asynchronous task boundary, and telemetry interfaces live inside this
repository. P00–P04 are consumed only as reviewed, installed wheels with locked
version, source commit, and artifact digest; no neighboring source paths are imported.

```text
HTTP API -> tenant authorization -> application services -> task adapter
                                      |                    |
                                      |                    +-> P04 adapter contract
                                      +-> bounded local retrieval -> citations
                                      +-> LocalToolGateway -> in-memory MCP billing/CRM boundary
API / worker / agent / tools -> telemetry adapter -> P03 package contract
```

The current runtime uses process-local ticket and approval storage for development.
The configured HMAC key verifies local JWTs. Fake mode generates an ephemeral key if
`JWT_SECRET` is absent. Refund requests create pending approvals; no refund effect is
implemented. P00–P03 use approved local wheels; P04's service-backed integration remains
gated because its FastAPI pin conflicts with P05's locked version.

The lexical retriever has a 100-document, 64 KB per-document, and 10-result limit.
The MCP SDK server is exercised in memory with synthetic records. The authenticated
local gateway performs scope and tenant checks; the SDK mock itself has no network
transport and must not be exposed as an authenticated service.

## Trust boundaries

- Request content, knowledge-base text, model output, and tool output are untrusted.
- Tenant identity comes from the authenticated principal, never request payloads.
- A refund requires an explicit scoped human approver and remains pending in fake mode.
- Knowledge retrieval returns cited data only; it cannot invoke tools or grant permissions.
- The demo makes no provider calls and reports no model quality metrics.
