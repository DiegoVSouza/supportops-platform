# Specification

`/healthz` only proves the process runs. Add `/readyz`, outside the public contract, that returns 200 only when PostgreSQL and Redis answer, and 503 naming the failed dependency otherwise. Add reverse migrations for 002, 003 and 004 under `migrations/down/`, proven by an up, down, up cycle in the lab's disposable database check.
