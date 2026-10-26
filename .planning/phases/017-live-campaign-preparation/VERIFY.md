# Verify — Live campaign preparation

Use repository artifacts and commands, not implementation-chat claims. Save each command, exit code and sanitized output under `artifacts/evidence/live-campaign-preparation/`.

- [ ] Exactly 120 unique semantic cases exist: 36 development / 84 sealed holdout; all required families have at least three cases and 72/48 language counts are correct.
- [x] Structural split/source-group, context, expected action/tools, fact/citation fields, forbidden behavior, rubric, criticality and finite-cap validation passed. Semantic authoring and independent review remain PENDING; this is not a claim that all 120 cases are semantically distinct.
- [ ] Graders reject fabricated/irrelevant citations, unsupported answers, injection bypass, tenant leaks, cross-tenant tool calls, expired access, duplicate effects and refund execution.
- [x] Zero-call safety denials are distinct from live provider trials; fake/replay outputs cannot count as live results.
- [x] Config contains three trials, per-case four-call maximum, per-call/task caps, confirmation reserve, human review requirements, deadlines/retry/chunk/pacing/wall-clock and approval source. Cumulative request/token/spend limits and account quota remain PENDING.
- [x] Dry-run is independent of secrets/SDK/network/Docker and reports pilot 24 / full 1,440 calls plus 240 fresh-confirmation calls and PENDING blockers.
- [x] Generation is disabled and the runner fails closed; campaign execution was not attempted.
- [x] Focused and offline fast/full subgates passed; full check remains INCOMPLETE because service integration was explicitly omitted. No critical safety gate was weakened.
- [ ] No holdout-informed fix is presented as generalized without fresh unique confirmation; no human review is claimed without provenance.
- [ ] No customer data, real refund/message, public deployment, or secret appears in artifacts; staged paths stay within plan ownership.
