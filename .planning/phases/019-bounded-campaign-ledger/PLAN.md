# Plan — Bounded campaign ledger for P05

## Execution controls

- `llm_mode`: `fake`; campaign preparation is offline.
- `allowed_write_paths`:
  - `.planning/phases/019-bounded-campaign-ledger/**`
  - `scripts/campaign_ledger.py`
  - `scripts/run_live_campaign.py`
  - `tests/test_campaign_ledger.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/decisions.md`
  - `docs/harness/failures.md`
  - `docs/harness/progress.md`
  - `docs/knowledge/live-campaign-ledger.md`
  - `artifacts/evidence/live-campaign-ledger/**`
- `forbidden_changes`: `.env`, tenant/RAG/MCP/auth/worker/prompts/runtime, datasets/rubrics/campaign approvals, Docker/Compose/service stacks and volumes, historic live/recovery evidence, other repos, harness-kit, provider/network/service calls, refund/message/tool effects, public deployment, and push.
- Budget: USD 0 paid campaign ceiling. The prior USD 0.01 one-task estimate does not fund the campaign. Free quota, cumulative request/token/spend/time limits, confirmation capacity and human review remain `PENDING`.
- Validation: focused ledger and preparation tests, fast checks, full fake gate with `--skip-services`, CLI help/dry-run/blocked execution. Preserve existing artifacts written by the legacy check scripts and never touch Docker-owned state.
- Stop condition: no Groq dispatcher or campaign call in this phase. A missing approval or finite limit yields `INCOMPLETE`.

## Tasks

1. **Test privacy-safe durable state** — append-only ledger, unknown-usage retention, immutable attempts, cumulative concurrency, cross-process lease, and content-free operational metadata.
2. **Implement P05-local accounting and resume inspection** — add SQLite journal/lease and extend the campaign CLI with read-only resume while leaving all tenant/security/runtime code unchanged.
3. **Verify without touching live services** — run focused and full fake gates with service checks skipped, capture sanitized outputs, preserve prior evidence, update knowledge and project state, and review staged paths.

## Plan review

Reviewed against P05 Phase 017, the tenant/RAG content boundary, and the Docker recovery commit. No runtime, dataset, rubric, compose, container, or volume path is in scope. The ledger accepts identifiers and usage counters only. Prior single-task permission is not extended to the 120-case campaign. Accepted for offline execution on 2026-10-26; clean-context review remains outstanding.
