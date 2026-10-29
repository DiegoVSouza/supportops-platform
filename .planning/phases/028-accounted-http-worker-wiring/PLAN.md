# Plan

1. Add explicit optional triage handler to actual API and ServiceWorker; adapt accounted runner to return the existing AgentTriageRun contract, preserving fixture-only public default and a separate internal live construction option.
2. Test authenticated HTTP execution, wrong tenant/scope, queue lease rechecks, no fallback and strict output/receipt/privacy contracts. Run locked focused/fast/full offline checks with fresh scratch; report service omissions and commit evidence.

allowed_write_paths: .planning/phases/028-accounted-http-worker-wiring/**; supportops_platform/agents/accounted.py; supportops_platform/api/app.py; supportops_platform/service_runtime.py; tests/test_accounted_identity.py; tests/test_accounted_http.py; artifacts/evidence/accounted-http-028/**; docs/harness/progress.md.
forbidden_changes: legacy provider guard removal, existing manifests/ledgers/results, sibling imports, production IdP, provider calls/credentials/budget changes, Docker lifecycle, real refunds/effects, weaker tests and human approvals. Fake mode, zero calls/USD 0 paid. max_tries3, no replay of uncertain work. Stop on external access, identity leakage or invalid provenance. Plan-check implementer self-assessment.
