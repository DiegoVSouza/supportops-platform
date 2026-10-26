# Verify — Bounded campaign ledger for P05

Save exact commands/exits and sanitized output under `artifacts/evidence/live-campaign-ledger/`.

- [x] Ledger is append-only, reserves before dispatch, retains unknown usage, and disallows replay of uncertain/completed trials.
- [x] Cumulative request/token/cost checks are atomic across campaign IDs and concurrent attempts.
- [x] OS lease excludes another process and releases normally; metadata has no tenant or content fields.
- [x] Resume inspection is read-only, content-free, rejects unknown/empty campaigns with exit 2, and never dispatches.
- [x] Offline dry-run and blocked execution do not access `.env`, provider, network, services, effects, or Docker.
- [x] Focused tests (6 ledger, 11 campaign) pass; fake full gate reports 127 passing tests, 2 warnings, and `INCOMPLETE` because service checks were explicitly omitted.
- [x] Existing service/recovery evidence and all P05-owned containers/volumes are unchanged.
- [x] Decisions, failures, progress, evidence/report, and bilingual knowledge are updated; staged diff is reviewed and committed.
- [ ] Independent clean-context verification remains separately recorded.

Campaign dispatch, human review, account quota, approved finite caps, model preflight, confirmation, broad service evaluation, canary, and rollback remain promotion gates.
