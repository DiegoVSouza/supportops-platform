# Verify — Safe worker failure reporting

Status: PLANNED. Save exact commands, exits and sanitized outputs in `artifacts/evidence/worker-failure-privacy/`.

- [ ] Local queue and fake worker persist allowlisted error codes only.
- [ ] P05 `ServiceWorker` hands only fixed messages to the installed P04 worker; transient failure remains retryable and permanent failure remains terminal.
- [ ] Durable task status and authenticated API response mask raw and legacy exception text while preserving known safe failure codes.
- [ ] Focused locked tests and fast gate pass; full locked offline gate passes unit/package/fake-control layers and explicitly returns INCOMPLETE for skipped services.
- [ ] Protected historical artifacts, evals, datasets, rubrics, campaign ledgers, packages, Compose/Terraform configuration and existing service state remain untouched.
- [ ] No provider, credentials, network, Docker CLI/daemon, service, customer data, or external effect was accessed.
- [ ] Staged diff is limited to plan paths, passes whitespace/secret review, and is committed locally.
- [ ] Human/independent review, external identity, semantic model evaluation and promotion remain PENDING/INCOMPLETE.
