# Verify — RAG and MCP

- [x] Retrieval returns source IDs/citations and deterministic ranking for the fixture corpus.
- [x] hit@k runs on saved fake/replay dataset; its score is not model quality.
- [x] MCP tool contracts reject invalid schemas and unauthorized tool use.
- [x] Prompt injection embedded in KB cannot invoke a prohibited tool; 30 adversarial fixtures remain data-only citations.
- [x] Record official SDK/spec versions and separate unit/integration results. The SDK server/client runs in memory; network MCP integration remains INCOMPLETE.

Validation evidence: `artifacts/evidence/phase-002-rag-mcp.md`. Local package integration is not claimed by the SDK in-memory contract test.
