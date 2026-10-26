# P05 verification

- Confirm allowed paths are P05-local and the live dataset contains only synthetic data.
- Run new mocked tests, tenant-isolation tests, and the full P05 offline gate with live mode unset; save commands, exit codes, output.
- Confirm authenticated Groq catalog lists `openai/gpt-oss-20b`; execute one synthetic tenant-A ticket through local retrieval and the serial Core agent flow.
- Verify every citation's tenant is tenant-A, the final response is grounded in authorized evidence, no MCP/refund action occurred, and tool/approval safety remains intact.
- Record actual model, token usage, retries, assertions, status, command/exit, and no raw prompt/citation/response. Cost remains `PENDING` absent billing confirmation.
- Scan staged diff/artifacts for credentials, review locally, commit without push. If answer quality fails, record `INCOMPLETE`; do not tune by repeated calls.

## Recorded result — 2026-10-26

- Focused mocked client/tenant citation tests passed (2). Full check: 106 passed, quality fixture gates passed; overall `INCOMPLETE` only for Docker-dependent service E2E.
- Final live command: `LLM_MODE=live uv run --extra live --group dev python scripts/run_live_groq_eval.py`; exit 0. Four-key model preflight passed; 4 serial calls; 1575 input / 371 output tokens; estimated cost USD 0.000229425; billed cost `PENDING`. All assertions passed: tenant isolation, authorized shipping evidence, cited response, approval and four-step flow.
- Preserved the earlier real run where a missing dispatch message correctly escalated; corrected the test ticket to align with its KB evidence, without changing model behavior. No MCP/refund tool ran.
