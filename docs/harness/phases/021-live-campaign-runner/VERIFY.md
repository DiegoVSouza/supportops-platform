# Verify

Status: INCOMPLETE until the evidence below exists.

- [ ] Plan check saved (`artifacts/evidence/live-campaign-runner/plan-check.txt`).
- [ ] New unit tests pass in fake mode with exit code and output saved.
- [ ] Root tests `python -m unittest discover -s scripts/harness -p "test_live_*.py"` pass (baseline before this phase: 79 tests OK).
- [ ] `uv run --locked python scripts/check_full.py` exit 0 with output saved.
- [ ] Live pilot report saved under `artifacts/evals/live/p05-dev-v1/`.
- [ ] Remaining development cases run or the stop reason is recorded.
- [ ] `feature_list.json` updated from the report only.

Independent review: `WAIVED_BY_OWNER`. Human review of corpus and grader: PENDING.
