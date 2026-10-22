# Plan

allowed_write_paths: `README.md`, `docker-compose.services.yml`, `scripts/check_services.py`, `scripts/check_network_mcp.py`, `docs/harness/phases/014/`, `docs/harness/progress.md`, `docs/harness/feature_list.json`, `artifacts/evidence/phase-014-*`, `.planning/phases/014-isolated-service-gate/`.

1. Make service host ports, Compose project, and evidence prefix configurable while keeping existing defaults.
2. Refuse to use a non-empty Compose project and always tear down only the fresh stack created by this gate, including its volumes.
3. Run the fast check and the complete gate with dedicated loopback ports; save command, exit code, and output.
4. Update P05 status from the saved evidence without changing external identity or model-evaluation claims.
5. Exercise signed MCP authentication over the Compose TCP network from the API container so the isolated gate does not depend on the public development port.

No shared kit, sibling project, external provider, live model, or existing Docker stack may be changed.

Plan review: accepted. The gate checks that its selected Compose project is empty before starting; a unique project name and verified-free host ports isolate services, and cleanup uses only that project with its volumes.
