# Verification

Result: PASS for the scoped acceptance.

The fake full service gate passed with 110 tests, Docker E2E, security, adversarial and recovery checks. The dedicated live image includes the locked optional Groq SDK and prompt files. One live API/Redis-worker/PostgreSQL-RAG task passed every assertion with four actual calls (1748 input / 468 output tokens), a shipping citation, tenant denial, idempotency and correlated content-free Jaeger spans. Live refunds remain explicitly blocked before generation.

Evidence: artifacts/evidence/live-docker/ contains executed commands, exit codes, retained failed attempts and sanitized results. Timestamped phase Groq reports are additional real-run evidence. Historical reports are preserved.

Every live run authenticated the requested model catalog before generation. Model: openai/gpt-oss-20b; official Groq SDK: 1.7.0; Docker Engine: 29.1.3. Only numbered root credentials were read silently. No silent fake fallback, paid provider fallback, kit edits, push, refunds or outbound customer messages occurred. Estimated costs derive only from observed usage; billed cost remains PENDING. This small synthetic sample does not establish general model quality.

Fake remains the default. Service integration checks use dedicated Compose projects. All 28 pre-existing container names are still present; this is not a health claim about unrelated stacks. Newly started live stacks are left available.
