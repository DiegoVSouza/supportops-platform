# Phase 024 verification

## Status

**FAIL / INCOMPLETE.** The offline gates passed, and the isolated full gate ran one fresh synthetic failure probe. The bounded read-only Jaeger poll found the expected failure spans, but the probe's privacy assertion detected that the synthetic exception sentinel was present in the exported trace. No trace body or sentinel value was written to evidence. The task/trace identifiers were not emitted by the probe and are unavailable; do not reconstruct them, query the trace again, or replay the task. The failure is immutable and requires a new phase and a new task after a source-backed fix.

The full gate exited 2 because service acceptance stopped at the privacy assertion. Remaining service acceptance, including crash recovery, is INCOMPLETE. This run is not a pass.

The root cause is now reproduced offline: in the locked OpenTelemetry SDK, `record_exception=False` suppresses exception events but does not suppress the context manager's automatic ERROR status or its exception-message description. The P05 `worker.run` and `agent.triage` spans therefore can export exception content through `status.description`. See `offline-status-repro.txt` and the next phase plan. This explains the leak; it does not make the live trace safe.

Docker cleanup and inventory reconciliation passed: phase-owned containers/network/volumes were removed; global counts stayed 102 containers, 21 networks, and 89 volumes. Identity diffs are empty. Container status strings can age naturally; no unrelated identity changed.

## Evidence

`artifacts/evidence/failure-trace-export-024/`.
