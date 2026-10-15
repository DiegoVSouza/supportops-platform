# Plan — Documentation and local release

## allowed_write_paths
`README.md`, `README.pt-BR.md`, `docs/**`, `scripts/demo*`, `artifacts/**`, package metadata, local Git tags.

## forbidden_changes
No external publication, push, cloud deploy, public PR, or claim of green integration when package gates are pending.

## Tasks
1. Write architecture, decisions, threat model, operations runbook, and 5-minute demo.
2. Add reproducible fake-mode CLI demo and verify README commands.
3. Record gate matrix, versions/commits/hashes, limitations, and knowledge/interview docs.
4. Create local v0.1.0 tag only if all acceptance gates pass; otherwise report incomplete without tag.

## Stop condition
Do not tag while any mandatory package integration, tenant, recovery, or security gate is incomplete.
