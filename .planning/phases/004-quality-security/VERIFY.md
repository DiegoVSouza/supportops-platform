# Verify — Quality and security

- [x] MCP tenant boundary rejects unauthenticated calls and cross-tenant reads; caller-supplied tenant fields do not select identity.
- [x] Dual-control refund behavior rejects the requesting subject as approver.
- [x] RAG citation response is tenant-scoped and scope-protected through the API.
- [x] Thirty prompt-injection fixtures are treated as data; API tests cover auth, tenant boundaries, rate/size limits, refund amount limits, feedback bounds, and PII-free metrics.
- [ ] Deliberately degraded fake-response regression threshold — PENDING; no quality gate for degraded agent output is implemented.
- [ ] Real-provider degraded-output evaluation — PENDING; no paid provider or replay cassette was authorized/provided.
- [x] Fake mode remains the default and fake fixtures are not reported as model-quality metrics.

Evidence: `artifacts/evidence/followup-full-gate.txt`. Real-provider quality and service-backed security checks remain PENDING/INCOMPLETE.
