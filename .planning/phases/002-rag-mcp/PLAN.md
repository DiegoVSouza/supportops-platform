# Plan — RAG and MCP

## allowed_write_paths
- `supportops_platform/rag/**`, `supportops_platform/mcp/**`, `tests/rag/**`, `tests/mcp/**`
- `evals/retrieval/**`, `docs/**`, `artifacts/**`, `pyproject.toml`, `uv.lock`

## forbidden_changes
- No unverified MCP APIs, no outbound tools, no live embeddings, no sibling source imports.

## Tasks
1. Define KB document/chunk/citation contracts and ingestion limits.
2. Implement deterministic local retrieval double and hit@k eval with adversarial KB cases.
3. Verify official MCP API and implement billing/CRM mock server and restricted client.
4. Test injection isolation, malformed tool input, and denied unauthorized tool calls.

## Stop condition
If SDK/spec APIs cannot be verified or pinned, keep local contract doubles and mark MCP integration INCOMPLETE.
