# Plan

- allowed_write_paths: `.planning/phases/021-locked-local-acceptance/**`, `.planning/phases/020-complete-token-reservations/VERIFY.md`, `artifacts/evidence/locked-acceptance/**`, `artifacts/evidence/live-token-reservations/full-locked-skip-services.txt`, `docs/harness/progress.md`, `docs/knowledge/locked-local-acceptance.md`.
- llm_mode: fake; use `uv run --locked` for Python gates.
- Operational ownership: create only empty Compose project `p05-locked-acceptance-021`; use dedicated free loopback ports. Refuse pre-existing project resources. Preserve all existing stacks and volumes, including stopped live workers.
- forbidden_changes: runtime, prompts, datasets, graders, budgets/approvals, credentials, kit, sibling repos, existing Docker resources, provider access and public/external actions.
- Validation: full fake gate with isolated services, exact exit and sanitized output, before/after container identity comparison, no temporary containers/volumes remaining.
- Stop condition: ownership/port conflict, provider mode mismatch, changed existing container state or failure requiring product changes beyond this plan.

1. Confirm locked imports and correct the prior global-Python diagnosis; preserve old evidence.
2. Snapshot existing containers and port availability; run full fake acceptance in the fresh namespace with phase-owned evidence.
3. Record outcome, remaining live gates and the locked command in progress/knowledge; review staged diff and commit locally.

Plan review: accepted. Existing `check_services.py` refuses non-empty namespaces, uses fake Compose configuration, and removes only the resources it created. Fresh ports prevent conflicts with existing P05 and unrelated stacks. Independent verification remains pending.
