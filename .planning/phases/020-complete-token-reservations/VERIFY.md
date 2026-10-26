# Verify — Complete P05 campaign token reservations

Save command output and exits under `artifacts/evidence/live-token-reservations/`.

- [x] Primary, confirmation, and additive input/output token maxima match the frozen campaign config.
- [x] Dry-run remains content-free and reports provider, credentials, network, and Docker untouched.
- [x] Generation remains disabled; paid spend stays USD 0 and quota/reviews stay `PENDING`.
- [ ] Focused and fast offline checks pass. Full gate remains `INCOMPLETE` (exit 2): package consumers are not installed and service checks were explicitly omitted; historical artifacts/stacks are unchanged.
- [ ] Evidence/progress are updated; staged diff is reviewed and committed locally.

Evidence: `artifacts/evidence/live-token-reservations/`. Focused preparation tests: 11 passed. `scripts/check_fast.py`: exit 0. `scripts/check_full.py --skip-services`: exit 2 / `INCOMPLETE` with package integration consumers `NOT_INSTALLED`, retrieval/OpenAPI/quality imports unavailable, services omitted, and semantic/model evaluation `PENDING`. No provider, credentials, network, or Docker was accessed.
