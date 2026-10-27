# SupportOps Platform Architecture

P05 is an independently versioned Python service. The API, deterministic retrieval,
tool policy, asynchronous task boundary, and telemetry interfaces live inside this
repository. P00–P04 are consumed only as reviewed, installed wheels with locked
version, source commit, and artifact digest; no neighboring source paths are imported.

```text
HTTP API -> tenant authorization -> application services -> task adapter
                                      |                    |
                                      |                    +-> P04 adapter contract
                                      +-> hybrid lexical/fake-vector retrieval -> citations
                                      +-> LocalToolGateway -> scoped MCP tool boundary
API / worker / agent / tools -> telemetry adapter -> P03 package contract
```

The current runtime uses process-local ticket and approval storage for development.
The configured HMAC key verifies local JWTs. Fake mode generates an ephemeral key if
`JWT_SECRET` is absent. Refund requests create pending approvals; no refund effect is
implemented. P00–P04 use approved local wheels. P04 provides the in-memory development
adapter and Redis Streams transport. PostgreSQL remains the authoritative task ledger;
Redis carries queued delivery and delayed retries. The service-backed flow is covered
by phase 017.

The local hybrid retriever has a 100-document, 64 KB per-document, and 10-result
limit. Deterministic hashed-token vectors exist only for control-flow tests and do
not represent semantic embeddings. A separate asyncpg-compatible adapter and
pgvector 0.8.7 migration define cosine/HNSW plus PostgreSQL full-text retrieval;
the native asyncpg retriever and migration were exercised against the isolated PostgreSQL service. The hashed vectors remain deterministic fixtures; semantic retrieval quality is PENDING.

MCP now has two boundaries: the offline mock with an injected principal, and a
Streamable HTTP server factory whose principal is built only from the SDK's verified
`get_access_token()` request context. The local E2E uses the pinned MCP 2.3.0 SDK over loopback TCP with signed delegated
tokens, rejects missing bearer tokens and denies cross-tenant access. External identity
provider and deployment acceptance remain INCOMPLETE.

## Trust boundaries

- Request content, knowledge-base text, model output, and tool output are untrusted.
- Tenant identity comes from the authenticated principal, never request payloads.
- A refund requires an explicit scoped human approver and remains pending in fake mode.
- Knowledge retrieval returns cited data only; it cannot invoke tools or grant permissions.
- The demo makes no provider calls and reports no model quality metrics.

## Worker failure privacy

P05 workers map exception types to a fixed error-code allowlist before handing a
failure to the installed P04 worker. Local fake-worker failures use the same codes.
Durable reads and the authenticated task-status route normalize stored legacy values
again, so historical exception strings are not returned to callers. The P04 worker
wheel remains version 0.1.4; this P05 boundary does not change its package or claim
that existing database rows were rewritten. Service-backed failure persistence and
response behavior still require a later isolated service gate.

P05-owned OpenTelemetry spans disable automatic exception-event recording. They may
still set error status, but do not attach exception message, traceback, or arbitrary
exception attributes. The phase verifies the worker span with an in-memory exporter
and checks the invariant across every P05-owned span call.
