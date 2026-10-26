# Phase 017 preparation evidence

## Status

**INCOMPLETE.** Offline campaign preparation and reservation checks are recorded. The dataset has the requested row counts and structural fields, but the cases are synthetic drafts without independent semantic review; do not treat them as 120 reviewed, distinct semantic scenarios. Human review, cumulative budget/quota, campaign authorization, runtime identity, model catalog preflight, persistent ledger/lease and clean-context verification remain pending.

## Dataset and limits

- 120 rows: 36 development / 84 fixed-in-repository holdout; 72 English / 48 Portuguese; nine required families. Source groups are unique and do not cross splits.
- SHA-256 (`cases.jsonl`): `84bf4a8aab99bd1f62e0508630753fbe088f3323254cfa8d6921682a124cc551`.
- Pilot reservation: 6 cases, 24 gross maximum provider calls. Development: 432; holdout: 1,008; primary total: 1,440. A 20-case fresh confirmation reserve adds 240. Additive maximum is 1,704 calls, 6,979,584 input tokens and 872,448 output tokens.
- 39 safety-denial cases are separately accounted as zero-call checks. Adjusted provider-call ceiling after these denials is 972; they are excluded from the live quality denominator.
- Per-task configured maximum is USD 2.00, but authorized campaign spend is USD 0.00. Cumulative campaign spend, request/token caps, Groq quota and confirmation funding are `PENDING`; arithmetic is a reservation display, not spend approval.

## Commands and evidence

All command output below is sanitized and stored in this directory.

| Command | Exit | Evidence | Result |
|---|---:|---|---|
| `uv run --locked python -m unittest discover -s tests -p test_live_campaign_preparation.py -v` | 0 | `focused-tests.txt` | 10 focused tests passed. |
| `uv run --locked python scripts/check_fast.py` | 0 | `check-fast.txt` | Fast offline gate passed. |
| `uv run --locked python scripts/check_full.py --skip-services` with project-local pytest basetemp | 2 | `check-full-offline.txt` | Offline subgates passed; aggregate INCOMPLETE because service integration was intentionally skipped. |
| `uv run --locked python scripts/run_live_campaign.py --stage pilot --dry-run` | 0 | `pilot-dry-run.json` | 24-call gross ceiling; provider not accessed. |
| `uv run --locked python scripts/run_live_campaign.py --stage development --dry-run` | 0 | `development-dry-run.json` | 432-call gross ceiling; provider not accessed. |
| `uv run --locked python scripts/run_live_campaign.py --stage holdout --dry-run` | 0 | `holdout-dry-run.json` | 1,008-call gross ceiling; provider not accessed. |

No Groq credentials were read and no provider, network, Docker, OTLP, customer-data, refund, or external-message action occurred. The phase plan forbids service changes; Docker availability therefore does not close the omitted service gate.

## Promotion blockers

1. Independent reviewers must author/review semantic distinctness, coverage and rubric calibration, including deliberate failure examples.
2. Approve finite cumulative request, token, spend, pacing, wall-clock and quota ceilings; maintain one cumulative account ledger across all keys.
3. Obtain explicit campaign authorization and reserve human review capacity.
4. Verify current model catalog, runtime/service identity and actual integrated API/Postgres/Redis/agent/MCP/Groq path in its separately planned phase.
5. Implement durable serialized campaign lease and cumulative ledger before any execution; the current runner is dry-run only.
6. Complete clean-context phase review and later quality, safety, operations, consumption, canary and rollback gates before any local-live promotion.

No campaign may start from these artifacts while any blocker is pending.
