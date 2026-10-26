# Plan

- allowed_write_paths: `docker-compose.services.yml`, `.planning/phases/018-docker-restart-recovery/**`, `artifacts/evidence/docker-restart-recovery/**`, `docs/harness/decisions.md`, `docs/harness/progress.md`, `docs/harness/failures.md`, `docs/knowledge/docker-recovery.md`.
- llm_mode: fake. No provider budget is authorized.
- Operational ownership: only existing `p05-remediation-009` and `p05-live-020` containers, plus a fresh empty `p05-recovery-021` validation project. Never delete existing volumes or recreate existing containers/secrets. Stop live worker before recovering dependencies.
- forbidden_changes: sibling stacks/projects, kit, credentials, runtime/prompt/agent behavior, model calls, dataset/graders, public deployment.

1. Save sanitized diagnosis and snapshot existing container identity, service state, and restart policy.
2. Set unless-stopped consistently in Compose and update existing P05 container restart policies without recreation; recover fake dependencies before application. Keep live worker stopped and recover only its infrastructure/API.
3. Run fast and full isolated fake service gates with dedicated free loopback ports and phase-owned evidence. Verify healthy fake API/dependencies, stable worker and preserved existing volumes.
4. Record result, remaining gates and recovery instructions; review staged diff and commit locally.

Plan review: accepted for this user-requested local repair. Consistent restart policy corrects the observed asymmetry, retains explicit manual stops and preserves state. Isolated gate refuses non-empty project and cleans only resources it creates. Clean-context verification remains pending until independently performed. Stop on ownership mismatch, port conflict, provider mode mismatch or evidence of data loss.
