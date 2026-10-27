# Phase 023 — Reverify failure privacy through isolated services

Status: PLANNED. Reverify committed phase 022 without changing the evaluated source candidate.

## Goal

Exercise P05's sanitized failure persistence and authenticated API reads across the real isolated Compose/PostgreSQL boundary. Existing unit tests and a prior P05 service stack do not verify this changed behavior. Keep every unrelated Docker resource untouched.

## Acceptance criteria

1. A synthetic sentinel exception passed through the actual service worker is persisted only as a fixed allowlisted category; sentinel text and traceback are absent from database state and telemetry.
2. The authenticated task API masks a legacy stored raw error and returns only the documented safe category; an unauthenticated caller remains denied.
3. The phase 022 source candidate remains byte-identical and at its existing commit; only isolated fake-mode local services are used.
4. Before/after inventory proves all pre-existing Docker container identities and states, networks, and volumes are preserved, and phase-owned temporary resources are removed.
5. Evidence records exact commands/exits and sanitized outputs. No model/provider, credentials, external network, paid spend, customer data, or live ledger is accessed.

## Out of scope

Source-candidate changes, live generation, external IdP, deployment, changes to existing Compose projects/stacks, general model quality, human/independent approval, and promotion.
