# SPEC — Use Redis Streams for durable job delivery

Use the shared P04 Redis Streams broker for P05 durable job dispatch. Keep PostgreSQL as the source of truth for jobs, authorization expiry, approvals and effects. Preserve the HTTP/MCP contracts, tenant isolation, retry/recovery and the 15-minute authorization lease.

Acceptance requires an approved P04 wheel with exact provenance, API-to-Redis-to-worker service coverage, delivery recovery after Redis/client restart, approval flow and a passing P05 full local gate.
