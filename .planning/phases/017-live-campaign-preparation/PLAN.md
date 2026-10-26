# Plan — Live campaign preparation

## Execution controls

- `llm_mode`: `fake`; data authoring, grader checks and dry-run are offline.
- `allowed_write_paths`:
  - `.planning/phases/017-live-campaign-preparation/**`
  - `evals/datasets/live-v1/**`
  - `evals/rubrics/live-v1/**`
  - `evals/live-campaign.json`
  - `scripts/run_live_campaign.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/decisions.md`
  - `artifacts/evidence/live-campaign-preparation/**`
- `forbidden_changes`: API/auth/RAG/MCP/worker/prompts, Docker/Compose or migration files, other repositories, harness-kit, root `.env`, secrets, historical provider evidence, public ports/deployment, customer data, real refund/effects, external communications, paid usage, or threshold relaxation.
- Budget source: profile maximum is USD 2/task; the prior explicit allowance was USD 0.01 estimated for one RAG evaluation. Expanded campaign, retries, confirmation, human review tooling and any optional judge traffic require separately evidenced caps and approval; until then these are `PENDING`. Never treat four keys as four quotas.
- Planned load to display, not authorization: pilot 6 development cases × 1 trial × at most 4 calls = 24 normal calls; full campaign 120 × 3 × 4 = 1,440 calls before retries/confirmation. Reserve at least 20 fresh confirmation cases per affected project before holdout; at the same trial/call caps this adds up to 240 calls if all 20 use provider generation.
- Validation: P05 fast/fake checks, dataset and split integrity, rubric calibration with deliberate bad outputs, safety-denial accounting, dry-run isolation and generation block tests. Save command, exit code and sanitized output under the evidence path.
- Stop condition: no provider call until budget/quota, reviewers, dataset/rubric freeze, runtime identity, model preflight, and every finite cap are approved. Stop on any critical safety failure; holdout-informed fixes consume holdout and require fresh confirmation. No public deployment.

## Tasks

1. **Freeze reviewed cases and safety rubrics** — inspect current RAG/API/MCP/authorization contracts and failure taxonomy; write 120 unique synthetic scenarios in the 36/84 split and 72/48 language composition. Track source groups to prevent split leakage; document zero-call denial applicability.
2. **Add dry-run and fail-closed reservation config** — validate stage and manifest, report trial/call/confirmation reservations and all unresolved budget fields without secrets, SDK, network or Docker. Block generation before dispatch whenever any required approval/cap is pending.
3. **Prove graders, security controls, and provenance** — demonstrate deliberate bad answers/citations/tools/tenant scopes/expiry/duplicates/refund attempts fail; verify fake and zero-call denials are separated from provider trials; run safe offline gates and save sanitized evidence.

## Plan review

Coordinator review completed against P05's full-governance policy, integrated-runtime acceptance, and portfolio requirements. The 36/84 split, 72/48 language allocation, 24-call pilot, 1,440-call maximum, and 240-call 20-case confirmation reserve are consistent. This phase does not authorize budget or code in the protected runtime paths. Accepted for preparation execution on 2026-10-26. A clean-context verifier is still required for finished phase gates.
