# Phase 002 — RAG and MCP evidence

Generated from P05 local commands on 2026-10-15. The MCP client/server test is in-memory; no live network, provider, or external effect is used.

## uv run --locked pytest

Command: `uv run --locked pytest`

Exit code: `0`

```text
................................................                         [100%]
48 passed in 1.30s
```

## uv run --locked python scripts/eval_retrieval.py

Command: `uv run --locked python scripts/eval_retrieval.py`

Exit code: `0`

```text
evaluation=deterministic-local-retrieval
cases=4
hit_at_3=4/4 (1.000)
interpretation=fixture coverage only; not LLM quality
```

## uv run --locked python scripts/check_full.py

Command: `uv run --locked python scripts/check_full.py`

Exit code: `2`

```text
$ C:\estudo\Golpe\lab\projects\p05\.venv\Scripts\python.exe -m compileall -q supportops_platform tests
exit_code=0
$ uv run --locked pytest
exit_code=0
................................................                         [100%]
48 passed in 1.37s
$ uv run --locked python scripts/eval_retrieval.py
exit_code=0
evaluation=deterministic-local-retrieval
cases=4
hit_at_3=4/4 (1.000)
interpretation=fixture coverage only; not LLM quality
$ C:\estudo\Golpe\lab\projects\p05\.venv\Scripts\python.exe scripts/verify_packages.py
exit_code=2
P01 orchestration: INCOMPLETE
P02 toolkit: INCOMPLETE
P03 observability: INCOMPLETE
P04 async: INCOMPLETE
Package integration gate: INCOMPLETE (P01 orchestration, P02 toolkit, P03 observability, P04 async)
check-full: INCOMPLETE; local checks ran and one or more mandatory gates remain unavailable
```
