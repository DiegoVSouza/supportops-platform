# Spec — 036 demo-live-v1

Parent: lab `projects/p07/.planning/phases/003-real-portfolio` (stage W4). Offline code only; the live smoke is a separate, recorded step.

## Goal

An accounted live path that public traffic can use. It is the substitute that `accounted_guard_required` (`agents/live_groq.py`) and `live refund/approval workflow is not enabled` (`agents/triage.py`) were waiting for. Both guards stay for every configuration that does not enable it.

## Requirements

| ID | Rule |
| --- | --- |
| DL-001 | Enabled only when `DEMO_LIVE_DSN` is set and `LLM_MODE=live`. Otherwise the old guards apply unchanged |
| DL-002 | Every model call reserves its worst-case cost in a Postgres ledger before the provider is contacted |
| DL-003 | The ledger fails closed at the ceiling (default and maximum USD 10). A ceiling above 10 is refused. A restart with a larger value does not raise a stored ceiling |
| DL-004 | A reservation and the ceiling check are one atomic statement. Tested at the boundary and with concurrent reservations |
| DL-005 | A 429 moves to the next numbered credential and bills nothing. All credentials limited means `ProviderBusy`, with the reservation released |
| DL-006 | A call that may have reached the provider without a receipt keeps its reservation |
| DL-007 | A receipt with the wrong model or out-of-range usage is refused and charged at the worst case |
| DL-008 | The ledger being unreachable denies the call |
| DL-009 | `llm_steps` (additive) lists, per call: step, agent, model, key slot, attempts, tokens, latency, estimated cost. No credential, no visitor text |
| DL-010 | A decided approval resumes with no new model call |
| DL-011 | No path substitutes fake output when a limit is reached |

## Out of scope here

Fly deploy, secrets, the live smoke, the P06 console showing the steps (the regenerated client is included).

## Known limit

The refund amount comes from the deterministic `propose_refund` tool (2500 cents), not from the model. The model triages and answers; the gate and a human decide. The site must not say the model chose the amount.
