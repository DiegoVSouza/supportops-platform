# Verify — Bounded campaign ledger for P05

Save exact commands/exits and sanitized output under `artifacts/evidence/live-campaign-ledger/`.

- [ ] Ledger is append-only, reserves before dispatch, retains unknown usage, and disallows replay of uncertain/completed trials.
- [ ] Cumulative request/token/cost checks are atomic across campaign IDs and concurrent attempts.
- [ ] OS lease excludes another process and releases normally; metadata has no tenant or content fields.
- [ ] Resume inspection is read-only, content-free, rejects unknown/empty campaigns with exit 2, and never dispatches.
- [ ] Offline dry-run and blocked execution do not access `.env`, provider, network, services, effects, or Docker.
- [ ] Focused tests and fake gates pass; full gate skips services explicitly and any resulting status is reported honestly.
- [ ] Existing service/recovery evidence and all P05-owned containers/volumes are unchanged.
- [ ] Decisions, failures, progress, evidence/report, and bilingual knowledge are updated; staged diff is reviewed and committed.
- [ ] Independent clean-context verification remains separately recorded.

Campaign dispatch, human review, account quota, approved finite caps, model preflight, confirmation, broad service evaluation, canary, and rollback remain promotion gates.
