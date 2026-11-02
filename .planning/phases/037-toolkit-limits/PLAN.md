# Plan 037

allowed_write_paths: `projects/p05/supportops_platform/agents/demo_live.py`, `projects/p05/tests/test_demo_live.py`, `projects/p05/.planning/phases/037-toolkit-limits/**`, `projects/p05/artifacts/evidence/toolkit-limits-037/**`, `projects/p05/docs/harness/feature_list.json`, `projects/p05/docs/harness/progress.md`.

1. Add tests first (red): real tokens are reported, a token crossing denies, an expired run never calls the provider.
2. Implement `ExecutionLimits` in `DemoClient`.
3. Run `tests/test_demo_live.py`, then `python scripts/check_fast.py`.
4. Record the evidence and the feature status.

stop conditions: a failing existing test that can only pass by weakening it; any live provider call from a test.
