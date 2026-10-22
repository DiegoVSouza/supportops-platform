# SPEC — Preserve retry semantics for grouped transport failures

## Intake
A clean-context review of phase 009 reproduced an MCP connection failure wrapped in `ExceptionGroup`. The service adapter currently translates scalar transport errors to P04 `TransientFailure`, so the grouped failure is classified as permanent and can reach DLQ. The standalone loop also needs bounded recovery for SQS endpoint/read timeouts. Durable jobs currently persist a local authorization snapshot and mint a delegated MCP token on resume; clarify this trust boundary and prove delayed resume uses the stored tenant/scopes without allowing caller-controlled identity changes.

## Acceptance
- A real loopback MCP connection refusal passes through `call_tool` and the P04 worker path, transitions to retrying, does not dead-letter on the first attempt, and succeeds after the dependency recovers.
- Nested transport exception groups are transient only when all leaf causes are approved transient transport errors; permission/authentication and mixed/permanent groups remain permanent.
- SQS endpoint and read timeouts are recovered by the standalone loop without swallowing permanent broker/configuration failures.
- Durable-job authorization snapshot and token expiry semantics are documented and tested on delayed resume.
- Unit, service, package, and full gates report command, exit code and saved output. No live LLM or external side effects.

## Compatibility
No public HTTP/MCP schema changes. The already-built 0.4.0 wheel remains immutable; code changes require P05 patch version 0.4.1 and a new wheel with provenance.
