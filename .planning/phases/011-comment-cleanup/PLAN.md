# Plan

LLM_MODE: fake

allowed_write_paths: `.planning/phases/011-comment-cleanup/`, `supportops_platform/async_tasks/durable.py`, `artifacts/evidence/comment-cleanup*.txt`.

1. Remove redundant comments while retaining safety rationale.
2. Run the fast check and compare the Python token stream; save results.

Forbidden: behavior, interface, prompt, dependency, or tool changes. Stop on a failed check.
