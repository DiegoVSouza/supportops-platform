# Plan — Quality and security

## allowed_write_paths
- `supportops_platform/quality/**`, `supportops_platform/governance/**`
- `evals/**`, `tests/security/**`, `tests/e2e/**`, `docs/**`, `artifacts/**`, `.github/workflows/**`

## forbidden_changes
- No weakening tests or baselines; no LLM judge or live provider calls without explicit approval.
- No P02 source import; use approved wheel or documented double.

## Tasks
1. Define regression dataset, deterministic graders, and threshold rationale.
2. Implement limits, tool authorization, injection checks, and PII handling.
3. Add >=30 adversarial cases and API-level negative tests.
4. Run fake CI and record failures, limitations, and package integration gate.

## Stop condition
Stop if a security bypass is found; fix or mark the release gate blocked/incomplete, never suppress the case.
