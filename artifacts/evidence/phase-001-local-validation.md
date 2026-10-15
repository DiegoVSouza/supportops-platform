# Phase 001 — Local validation evidence

Generated from commands executed in the P05 repository on 2026-10-15.

## uv run --locked pytest

Command: `uv run --locked pytest`

Exit code: `0`

```text
........                                                                 [100%]
8 passed in 0.58s
```

## uv run --locked python scripts/check_full.py

Command: `uv run --locked python scripts/check_full.py`

Exit code: `2`

```text
$ C:\estudo\Golpe\lab\projects\p05\.venv\Scripts\python.exe -m compileall -q supportops_platform tests
exit_code=0
$ uv run --locked pytest
exit_code=0
........                                                                 [100%]
8 passed in 0.58s
$ C:\estudo\Golpe\lab\projects\p05\.venv\Scripts\python.exe scripts/verify_packages.py
exit_code=2
P01 orchestration: INCOMPLETE
P02 toolkit: INCOMPLETE
P03 observability: INCOMPLETE
P04 async: INCOMPLETE
Package integration gate: INCOMPLETE (P01 orchestration, P02 toolkit, P03 observability, P04 async)
check-full: INCOMPLETE; local checks ran and one or more mandatory gates remain unavailable
```

## uv build --wheel --out-dir %TEMP%/p05-phase001-wheel

Command: `uv build --wheel --out-dir %TEMP%/p05-phase001-wheel`

Exit code: `0`

```text
Building wheel...
Successfully built C:\Users\dvsdi\AppData\Local\Temp\p05-phase001-wheel\supportops_platform-0.1.0-py3-none-any.whl
```

## docker compose config

Command: `docker compose config`

Exit code: `0`

```text
name: p05
services:
  api:
    build:
      context: C:\estudo\Golpe\lab\projects\p05
      dockerfile: Dockerfile
    environment:
      LLM_MODE: fake
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')
      timeout: 3s
      interval: 10s
      retries: 3
    networks:
      default: null
    ports:
      - mode: ingress
        target: 8080
        published: "8080"
        protocol: tcp
networks:
  default:
    name: p05_default
```
