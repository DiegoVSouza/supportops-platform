# Plan

1. Block both historical entry points and test refusal before credential, network and service operations.
2. Run locked fake tests and fast checks; record sanitized commands, cwd, exit and output.

allowed_write_paths: `.planning/phases/026-disable-unaccounted-live/**`, `scripts/run_live_groq_eval.py`, `scripts/check_live_services.py`, `tests/test_legacy_live_guard.py`, `artifacts/evidence/disable-unaccounted-live-026/**`.

forbidden_changes: historical artifacts, other projects, budgets, credentials, provider calls, existing assertions, Docker lifecycle, paid use and external effects. Budget zero calls and USD 0. max_tries: 3 per failure; no live replay. Plan-check is implementer self-assessment; stop on unexpected external access.
