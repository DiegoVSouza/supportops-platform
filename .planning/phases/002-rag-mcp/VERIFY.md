# Verify — RAG and MCP

- [x] Local lexical retrieval chunks documents and returns deterministic tenant-filtered citations with stable source IDs.
- [x] Deterministic hit@k runs on the saved fixture corpus; the score measures fixture coverage only.
- [x] API triage loads tenant from the authenticated ticket, invokes the P01 fake runner, and includes citations in its response and trace.
- [x] MCP SDK client/server tool contracts run in memory; authorization and input bounds are tested.
- [x] Thirty prompt-injection fixtures remain untrusted retrieved text and cannot grant tool capability.
- [x] MCP server handlers receive a server-injected principal; calls without one fail closed and cross-tenant reads are denied.
- [x] Official SDK/package versions and wheel provenance are recorded in `docs/harness/sources.lock.json`.
- [ ] Embedding-backed retrieval, replay cassettes, and network MCP authentication/interoperability — INCOMPLETE; lexical and in-memory adapters only.

Evidence: `artifacts/evidence/followup-full-gate.txt`, `artifacts/evidence/followup-package-gate.txt`.
