# Plan — Integration skeleton

## allowed_write_paths
- `supportops_platform/**`, `tests/contracts/**`, `tests/integration/**`, `infra/**`, `docker-compose.yml`
- `docs/**`, `artifacts/**`, `pyproject.toml`, `uv.lock`, `Makefile`, `README*`

## forbidden_changes
- No sibling-source imports, kit edits, external package publish, cloud deployment, or live LLM calls.
- Do not mark doubles as successful real integration.

## Tasks
1. Define package-version manifest and adapter contracts for P01–P04; add doubles.
2. Build health endpoint and compose service skeleton.
3. Add local wheel installation/verification script that records origin commit and SHA-256.
4. Test available installed packages; report unavailable integrations as INCOMPLETE.

## Stop condition
Stop real integration when a package has no reviewed version/contract or build artifact; continue independent components.
