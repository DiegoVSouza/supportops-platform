# PLAN — Isolated full service gate

allowed_write_paths: `README.md`; `docker-compose.services.yml`; `scripts/check_services.py`; `scripts/check_network_mcp.py`; `docs/harness/phases/014/`; `docs/harness/progress.md`; `docs/harness/feature_list.json`; `artifacts/evidence/phase-014-*`.

1. Parameterize the Compose project, host ports, and evidence filenames.
2. Add an empty-project guard and cleanup for only the stack started by this gate.
3. Run the fast and full checks on unused loopback ports and capture evidence.
4. Reconcile feature status and progress with the results; retain any unmet external gates as INCOMPLETE/PENDING.
5. Test signed MCP access over the Compose TCP network using the service URL configured in the API container.

Do not change existing Docker projects, use live LLMs, call an external identity provider, publish a package, or deploy.

Plan review: accepted. The gate uses a fresh Compose project, dedicated loopback ports, phase-specific evidence names, and scoped teardown.
