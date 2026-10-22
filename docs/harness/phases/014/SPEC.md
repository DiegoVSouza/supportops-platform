# SPEC — Isolated full service gate

Run the current P05 fake-mode service integration gate in a fresh Docker Compose project with dedicated loopback ports. Preserve the existing `p05-remediation-009` and all other projects' stacks. The isolated stack must be removed after execution, and its exact evidence must distinguish local service acceptance from external identity and model evaluation.
