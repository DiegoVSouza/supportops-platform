# Phase 025 verification

## Status

**PASS — scoped technical privacy and fake-service acceptance.** Candidate `28a81fcf14c0a1ce32a24837abd2aab4f192fdf7` adds `set_status_on_exception=False` and retains `record_exception=False` at every P05-owned span call site and in the one-shot probe. The phase-024 trace was not queried or replayed.

`uv run --locked python scripts/check_fast.py` passed. Focused tests passed (25). The complete offline suite passed (138 tests, 2 pre-existing deprecation warnings). The isolated fake full gate passed, including the new one-shot service privacy probe (`trace_spans=7`, both expected failure spans observed, sentinel absent), complete service/E2E acceptance, and kill-after-effect recovery.

The full gate exited 0. Only the cached image `sha256:0af6c40c175c5fa2f5278c01dac843b3978635ab36b9ee947071c75649203f30` was used, with source/script mounts read-only. No provider request, credential read, paid use, image build/pull, or external call occurred. After cleanup, containers/networks/volumes remained 102/21/89; normalized existing container state/image diff was empty, network and volume identity diffs were empty, and no phase-owned containers remained.

This PASS is scoped to P05 telemetry privacy and local fake operations. Real model quality/cost, broad campaign, human/independent review, external identity acceptance, promotion and rollback approvals remain PENDING/INCOMPLETE. Phase 024 remains a historical privacy FAIL.

## Evidence

- Prior root-cause reproduction: `artifacts/evidence/failure-trace-export-024/offline-status-repro.txt`.
- Candidate source hashes, locked offline gates, sanitized full gate, sanitized trace metadata, and Docker reconciliation: `artifacts/evidence/span-status-privacy-025/`.

## Review state

Implementer verification only. Independent review, human review, semantic/model quality, campaign approval, identity acceptance, and promotion remain PENDING/INCOMPLETE.
