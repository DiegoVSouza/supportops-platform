# Plan

1. Add `infra/logging/` and copy it into the image.

allowed_write_paths: `infra/logging/**`, `Dockerfile`, `.planning/phases/034-json-logs/**`. forbidden_changes: application code. llm_mode: fake. budget: USD 0. validation: deployed logs parse as JSON, lab phase 008. stop conditions: three failed attempts.
