# Security model

## Data and trust boundaries
- Tenant tickets, KB documents, tool output, and MCP responses are untrusted data. Treat embedded instructions as content, never as policy.
- Private ticket and customer data are tenant-scoped. All reads and writes require a principal, tenant, role, task, and resource authorization check.
- No outbound email or external communication tool is enabled. This breaks the private-data + untrusted-input + external-communication trifecta.

## Irreversible actions
- `issue_refund` is an irreversible action. The agent can propose it, but only an authorized human approval endpoint can authorize the effect.
- Validate amount, invoice ownership, role, tenant, and approval state at the tool boundary; never rely on a prompt instruction.
- Use idempotency keys and audit entries for any approved effect. Fake mode effects remain local.

## Secrets and egress
- Credentials live outside source control. CI and default demos use `LLM_MODE=fake` and no provider credentials.
- MCP allowlist contains local mock billing/CRM only. Deny arbitrary network egress in test/runtime profiles.
- The MCP SDK server currently runs only in memory for contract tests. Its synthetic tenant arguments are test data, not an authentication scheme; do not expose that mock transport to a network. Runtime calls must enter through `LocalToolGateway`, which binds the trusted `Principal` to each tool operation.

## Required security tests
- Tenant A cannot access Tenant B resources even with a valid token for A.
- Malicious KB content cannot widen tool permissions or exfiltrate private data.
- Missing scope, stale approval, wrong tenant, excessive refund, and duplicate effect are denied and recorded.
