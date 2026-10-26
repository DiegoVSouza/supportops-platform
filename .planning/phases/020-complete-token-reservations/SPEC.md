# Phase 020 — Complete P05 campaign token reservations

## Goal

Expose P05's already configured primary, confirmation, and additive input/output token maxima through the offline campaign dry-run so the root account-wide inventory can aggregate the documented ceilings.

## Constraints

- Campaign generation remains disabled; USD 0 paid campaign budget and the prior one-task exception are unchanged.
- Preserve the 120-case dataset, zero-call denial handling, tool/security gates, and all Docker/runtime state.
- Token ceilings are conservative planning maxima, not quota or spend approval.

## Acceptance criteria

1. Dry-run JSON exposes primary, confirmation, and additive input/output token maxima already stored in `planned_reservations`.
2. No query, retrieval, answer, citation, trace, or tool content is added to output; report stays content-free.
3. Tests assert the published values match the fixed config while safety flags remain false and generation remains blocked.
4. Focused and full fake gates pass with services explicitly skipped; evidence identifies that service checks remain incomplete.

## Out of scope

Changing planned caps/config, budget/review state, runtime behavior, datasets/rubrics, provider or Docker calls, or campaign dispatch.
