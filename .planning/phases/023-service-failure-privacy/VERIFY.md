# Verify — Reverify service failure privacy

Status: PLANNED.

- [ ] Worker-persisted errors contain only a fixed allowlisted code after a synthetic exception.
- [ ] Authenticated API masks legacy raw error content; unauthenticated access remains denied.
- [ ] Synthetic sentinel and exception details are absent from database and exported traces.
- [ ] Full fake-mode service acceptance passes in the unique phase-owned Compose project.
- [ ] Exact source candidate remains unchanged; existing Docker identities/states/networks/volumes match before and after; temporary owned resources are absent afterward.
- [ ] Commands, exit codes, sanitized output, source fingerprint, and inventory evidence are saved.
- [ ] User reviews and campaign/model quality remain PENDING; no approval is inferred.
