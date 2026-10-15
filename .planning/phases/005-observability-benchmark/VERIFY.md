# Verify — Observability and benchmarks

- [ ] One trace contains API → queue → worker → agent → LLM → tool → DB spans when real adapters are installed.
- [ ] Loop, error, latency, and cost fields are bounded and avoid tenant/PII cardinality leaks.
- [ ] Two replay configurations execute reproducibly; benchmark metrics cite run artifacts or remain PENDING.
- [ ] Missing P03 integration is clearly INCOMPLETE rather than simulated PASS.
