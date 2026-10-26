# Cleanup verification

- Review format and names; check that prompts, provider parameters, budgets and retry policies have not changed.
- Run existing offline fast and full checks; save command, exit code and output in artifacts/evidence/code-cleanup/.
- Inspect staged paths and diff for secrets and generated files. Verify no old commit was rewritten.
- Results: PENDING.
