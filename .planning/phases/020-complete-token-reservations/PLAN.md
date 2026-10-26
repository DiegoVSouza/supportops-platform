# Plan — Complete P05 campaign token reservations

## Execution controls

- `llm_mode`: `fake`; only the offline dry-run is exercised.
- `allowed_write_paths`:
  - `.planning/phases/020-complete-token-reservations/**`
  - `scripts/run_live_campaign.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/progress.md`
  - `artifacts/evidence/live-token-reservations/**`
- `forbidden_changes`: `.env`, P05 runtime/security/RAG/MCP/worker/prompts, dataset/rubric/config caps, Docker/services/containers/volumes, historic reports, sibling repositories, budget approvals, provider/network access, or external effects.
- Budget: no provider calls; paid spend stays zero and free quota remains `PENDING`.
- Validation: focused campaign test, `-S` pilot dry-run, fast checks, and full fake gate with `--skip-services`; preserve prior evidence written by check scripts.
- Stop condition: no change can authorize dispatch or alter the live stack.

## Tasks

1. Add failing assertions for primary, confirmation, and additive token maxima using current config values.
2. Publish those existing values in the dry-run response without content fields.
3. Run focused/full offline checks, record evidence/progress, and commit reviewed paths.

## Plan review

The missing values already exist in the project campaign configuration; this phase only exposes them through its documented dry-run interface. No token cap is changed and no account authorization is inferred. Accepted on 2026-10-26.
