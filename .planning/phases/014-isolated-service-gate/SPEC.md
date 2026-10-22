# Run the P05 service gate in an isolated stack

The latest P05 release has local Keycloak acceptance, but its full service gate was skipped to preserve an already-running Docker stack. Add a repeatable full-gate path that starts only a fresh, uniquely named P05 stack on dedicated loopback ports, records phase-specific evidence, and removes only resources created by that run.

Acceptance: `check_full.py` runs without `--skip-services` and exits 0; the service gate refuses to reuse an existing Compose project; the isolated containers and volumes are removed after the run; current feature status and progress cite the new evidence. Model evaluation and external identity acceptance stay PENDING/INCOMPLETE where evidence is unavailable.
