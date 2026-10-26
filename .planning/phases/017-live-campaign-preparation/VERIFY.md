# Verify — Live campaign preparation

Use repository artifacts and commands, not implementation-chat claims. Save each command, exit code and sanitized output under `artifacts/evidence/live-campaign-preparation/`.

- [ ] Exactly 120 unique semantic cases exist: 36 development / 84 sealed holdout; all required families have at least three cases and 72/48 language counts are correct.
- [ ] Related scenarios/source groups cannot cross splits. Each case records synthetic tenant/authorization context, expected action/tools, facts/citations, forbidden behavior, rubric, criticality and finite caps.
- [ ] Graders reject fabricated/irrelevant citations, unsupported answers, injection bypass, tenant leaks, cross-tenant tool calls, expired access, duplicate effects and refund execution.
- [ ] Zero-call safety denials are distinct from real provider trials; fixture and fake outputs cannot count as live results.
- [ ] Config contains three trials, per-case four-call maximum, all per-call/task/cumulative ceilings, confirmation reserve, human review requirements, deadlines/retry/chunk/pacing/wall-clock and approval source.
- [ ] Dry-run is independent of secrets/SDK/network/Docker and reports pilot 24 / full 1,440 calls plus at least 240 fresh-confirmation call capacity and every `PENDING` blocker.
- [ ] Generation fails before dispatch unless all campaign ceilings, reviewer capacity, model preflight, and runtime/candidate identities are frozen.
- [ ] Offline tests pass with no unexpected skips; critical safety gates are not weakened.
- [ ] No holdout-informed fix is presented as generalized without fresh unique confirmation; no human review is claimed without provenance.
- [ ] No customer data, real refund/message, public deployment, or secret appears in artifacts; staged paths stay within plan ownership.
