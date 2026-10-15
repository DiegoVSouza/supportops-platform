---
name: lab-commits
description: Create atomic Conventional Commits for completed changes in the lab or an independent portfolio project.
---

# Lab commits

Follow the [requested reference](https://medium.com/linkapi-solutions/conventional-commits-pattern-3778d1a1e657).

Use `type(scope): imperative English description`. Scope is required by this lab; use the affected component. Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Use `!` before the colon or a `BREAKING CHANGE:` footer for incompatible API changes; record the required ADR and version change. Optional body explains why; include phase/task references in the body.

Examples: `feat(router): add supervisor termination limits`, `test(worker): cover duplicate delivery`, `docs(api): explain tenant scopes`.

Commit every completed logical task, including documentation and configuration. Do not commit each editor save. Before committing, check `git rev-parse --show-toplevel` against the intended project, inspect status and diff, run relevant checks and save evidence, then stage explicit task paths. Preserve unrelated user changes. Inspect the staged diff for secrets and generated files. Commit locally and record the hash in the task handoff. Do not push or bypass hooks. Never claim a commit occurred unless Git returned success.

Each `projects/<pid>` has its own `.git`; the lab repository excludes `projects/`. Never stage project code into the lab. Commit planning separately when implementation spans multiple tasks. If validation is unavailable, record INCOMPLETE rather than claiming success. Hook validation enforces syntax; human/agent review enforces meaning and atomicity.
