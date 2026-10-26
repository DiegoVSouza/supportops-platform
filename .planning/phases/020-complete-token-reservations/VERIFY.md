# Verify — Complete P05 campaign token reservations

Save command output and exits under `artifacts/evidence/live-token-reservations/`.

- [x] Primary, confirmation, and additive input/output token maxima match the frozen campaign config.
- [x] Dry-run remains content-free and reports provider, credentials, network, and Docker untouched.
- [x] Generation remains disabled; paid spend stays USD 0 and quota/reviews stay `PENDING`.
- [x] Focused preparation tests (11) and fast offline checks pass (exit 0).
- [x] Full fake gate completed in follow-up phase 021 with `uv run --locked python scripts/check_full.py` (exit 0), including service security/traces/recovery. The earlier global-Python import failures were an invocation error; locked dependencies are installed. Semantic/model evaluation remains `PENDING`.
- [x] Evidence/progress are updated, staged paths reviewed, and implementation committed locally as `52bd868d99169eff4df2acf084832a71ab32d8bf`; historical artifacts/stacks are unchanged.

Evidence: `artifacts/evidence/live-token-reservations/`. Focused preparation tests: 11 passed. `scripts/check_fast.py`: exit 0. `scripts/check_full.py --skip-services`: exit 2 / `INCOMPLETE` with package integration consumers `NOT_INSTALLED`, retrieval/OpenAPI/quality imports unavailable, services omitted, and semantic/model evaluation `PENDING`. No provider, credentials, network, or Docker was accessed.

Correction: that historical full-gate command used the global Python. The locked rerun passed every offline layer (127 tests and package consumers); only the deliberate service omission caused exit 2. Phase 021 then passed the full isolated fake service gate. Historical output remains preserved; current evidence is `artifacts/evidence/locked-acceptance/check-full.txt`.
