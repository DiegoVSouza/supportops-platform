# SupportOps Platform Architecture

P05 is an independently versioned Python service. The API, deterministic retrieval,
tool policy, asynchronous task boundary, and telemetry interfaces live inside this
repository. P00–P04 are consumed only as reviewed, installed wheels with locked
version, source commit, and artifact digest; no neighboring source paths are imported.

```text
HTTP API -> tenant authorization -> application services -> task adapter
                                      |                    |
                                      |                    +-> P04 adapter contract
                                      +-> local retrieval -> citations
                                      +-> tool policy -> MCP billing/CRM boundary
API / worker / agent / tools -> telemetry adapter -> P03 package contract
```

The current runtime uses process-local ticket and approval storage for development.
The fake credentials in `supportops_platform.api.app` are test fixtures and are not a
production identity provider. Refund requests create pending approvals; no refund
effect is implemented. Real persistence, queue delivery, and P01–P04 integration
remain gated until their approved artifacts and service-backed checks are available.

## Trust boundaries

- Request content, knowledge-base text, model output, and tool output are untrusted.
- Tenant identity comes from the authenticated principal, never request payloads.
- A refund requires an explicit scoped human approver and remains pending in fake mode.
- Knowledge retrieval returns cited data only; it cannot invoke tools or grant permissions.
- The demo makes no provider calls and reports no model quality metrics.
