# Verify — Reverify service failure privacy

Status: PASS for locked fake/local service controls; model-quality, independent review, and promotion remain PENDING.

- [x] Worker-persisted failure contains only `invalid_input`; the synthetic sentinel is absent from worker persistence and its outbox record.
- [x] Authenticated API masks a legacy sentinel row to `worker_failure`; unauthenticated access returns 401.
- [x] The synthetic sentinel is absent from the database and API output. The direct probe's trace was not observed in Jaeger; the locked in-memory exporter regression passes, and the full service gate independently verified correlated traces for the real service path.
- [x] Full fake-mode service acceptance passes in the unique phase-owned Compose project: 133 tests and all required fake/local service checks passed; aggregate exit 0.
- [x] P05 phase 022 runtime/source and evaluation files remain unchanged. All 102 container identities and normalized states, 21 networks, and 89 volumes match; phase resources are removed. One unrelated `gossett_backend` status age advanced while it remained `Restarting (1)` both before and after; no command targeted it.
- [x] Commands, exit codes, sanitized output, candidate source check, and inventory evidence are saved under `artifacts/evidence/service-failure-privacy-023/` and this phase's evidence folder.
- [x] User reviews, model quality, independent review, campaign approval, and promotion remain PENDING; no approval is inferred.

Regression found during service rerun: two existing service assertions expected raw `authorization lease expired` text, while phase 022 intentionally returns the fixed `authorization_expired` category. The assertions were updated to require that category while preserving failed-status, authorization-denial, and no-effect checks. The failed run is retained as historical evidence; the corrected complete service gate passed.

Offline image build note: `docker build --network=none` could not install `uv==0.12.7` because that tool is not vendored. No image was created or pulled. The service gate therefore used the existing local `supportops-platform:groq-live` image (dependency versions match `uv.lock`) with the current P05 source and scripts bind-mounted read-only; Compose ran with `--no-build` and no pull.
