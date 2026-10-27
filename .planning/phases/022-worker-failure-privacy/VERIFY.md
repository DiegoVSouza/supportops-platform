# Verify — Safe worker failure reporting

Status: OFFLINE CONTROL PASS; SERVICES/EXTERNAL IDENTITY INCOMPLETE; MODEL QUALITY/HUMAN AND INDEPENDENT REVIEW PENDING. Exact commands, exits, sanitized output and protected hashes are in `artifacts/evidence/worker-failure-privacy/`.

- [x] Local queue and fake worker persist allowlisted error codes only.
- [x] P05 `ServiceWorker` hands only fixed messages to the installed P04 worker; transient failure remains retryable and permanent failure remains terminal.
- [x] All P05-owned spans set `record_exception=False`; the in-memory exporter test confirms worker errors produce no exception event, and an AST invariant covers every P05 span call.
- [x] Durable task status and authenticated API response mask raw and legacy exception text while preserving known safe failure codes.
- [x] Focused locked tests passed (38); fast gate passed; full locked offline gate passed 133 tests, package/fake-control layers, and OpenAPI. Gate exits 2/INCOMPLETE because services were explicitly skipped to preserve the running stack.
- [x] 218 protected tracked evidence/eval/config/package files match phase-base HEAD byte-for-byte. No service or Docker command was run.
- [x] No provider, credential value, external network/service, customer data, or external effect was accessed. Existing MCP protocol tests used only ephemeral loopback listeners; transport refusal targeted closed `127.0.0.1:9`. GROQ and OTEL export environment variable names were unset in the full-gate child process without reading values.
- [x] Staged diff is limited to plan paths and passes whitespace/secret review; local implementation commit is created after review.
- [x] Human/independent review, external identity, semantic model evaluation and promotion remain PENDING/INCOMPLETE.
