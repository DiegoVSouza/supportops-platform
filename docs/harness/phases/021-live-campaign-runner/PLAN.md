# Plan

1. Write SPEC, PLAN, VERIFY and run the plan check (`artifacts/evidence/live-campaign-runner/plan-check.txt`).
2. Tests first: `tests/test_campaign_corpus.py`, `tests/test_campaign_observe.py`, `tests/test_campaign_execution.py` (fake provider, no network). Then `scripts/campaign_corpus.py`, `scripts/campaign_observe.py`.
3. Root guard in the lab repo (phase 057): authorization-gated branch for `p05-dev-v1` in `scripts/harness/live_free_account.py` with tests; `AUTHORIZATION.json`.
4. `scripts/campaign_execution.py` and the `--execute-free` path of `scripts/run_live_campaign.py`: committed-source fingerprint, ledger reservation per trial, lease, private fake-first dry execution, resumable batches, content-free per-trial records under `artifacts/evals/live/p05-dev-v1/`, Wilson interval.
5. Full fake gate (`uv run --locked python scripts/check_full.py`, private TEMP) and root tests; commit.
6. Live: catalog preflight, window check, pilot (`--max-trials 6`), review, then resume for the remaining 10 only if clean. Pace batches; stop on any non-ok outcome.
7. Update `docs/harness/feature_list.json` from the recorded run only; regenerate the P07 catalog after reading its `git status`; commit explicit paths.

allowed_write_paths:
- docs/harness/phases/021-live-campaign-runner/**
- scripts/campaign_corpus.py
- scripts/campaign_observe.py
- scripts/campaign_execution.py
- scripts/run_live_campaign.py
- evals/live-campaign.json
- evals/live-execution.json
- evals/graders/**
- tests/test_campaign_*.py
- tests/test_live_campaign_preparation.py
- docs/harness/progress.md
- docs/harness/decisions.md
- docs/harness/failures.md
- docs/harness/feature_list.json
- artifacts/evidence/live-campaign-runner/**
- artifacts/evals/live/p05-dev-v1/**
- README.md

lab-repo paths (phase 057): `.planning/llm-live-readiness/phases/057-p05-live-campaign/**`, `scripts/harness/live_free_account.py`, `scripts/harness/test_live_free_account.py`, `projects/p07/src/data/catalog.generated.json` (regenerated, explicit path only).

forbidden_changes: `.env`, `harness-kit/**`, other projects' sources, holdout cases and their protections, prompts of the accounted Core workflow, dependencies, prior evidence, Git history, any push.
llm_mode: fake until step 6.
Budget: step 6 only, at most 64 provider attempts, free keys, USD 0.00 paid.
max_tries: 3 per step; a failing guard is reported, not bypassed.
stop_condition: any non-ok provider outcome, window exhausted, ledger or receipt mismatch, uncertain attempt.
