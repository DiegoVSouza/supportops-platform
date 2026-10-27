# Progress

- Kit initialization completed.

## 2026-10-15 — Intake and plan review

- Original acceptance criteria were reconciled into six local phases with SPEC, PLAN, and VERIFY before product code.
- Coordinator plan review: accepted. Every phase plan declares local path ownership, forbidden changes, 2–4 tasks, verification, and stop condition.
- Intake baseline used earlier P00–P04 wheel versions. This historical state was superseded by the phase 007 package install and consumer evidence below.
- The RAG profile is enabled; governance is full because the platform is multi-tenant, handles private ticket data, and has an irreversible refund action.

## 2026-10-15 — Local API and retrieval components

- API baseline and contracts committed as `549ab1f`; tenant scope, rate bounds, pending refund approval, and idempotency are exercised by unit/API tests.
- RAG/MCP local implementation includes deterministic tenant-scoped retrieval, API citations, and principal-injected in-memory MCP tools.
- Baseline local API tests passed; runtime persistence, service-backed task-broker delivery, authenticated network MCP transport, replay evaluation, and degraded-agent regression were then INCOMPLETE or PENDING. Current package/API status is recorded in phase 007 below.

## 2026-10-15 — Roadmap remediation phase 007

- Phase 007 was created and reviewed before product changes. Its five acceptance requirements cover API reconciliation, approved wheel integration, service path, retrieval/MCP security, observability, and evidence-backed state.
- The initial phase-007 note listed P00/P02/P04 releases as not installed and P01/P03 provenance as pending. Those statements are superseded by the verified artifact manifest below.
- PostgreSQL/pgvector, Redis, LocalStack, Docker runtime, authenticated network MCP, dashboard/alert E2E, and replay/model evaluation remain INCOMPLETE or PENDING until their respective checks run.

## 2026-10-15 — Phase 007 local remediation evidence

- API package is 0.3.0. ADR-005 restores `/healthz`, `/v1/tickets/{ticket_id}/approve`, and `/v1/feedback` additively; `/health` remains a hidden compatibility alias. OpenAPI export check passes.
- Approved local wheels pin P01 0.1.1, P02 0.2.0, P03 0.3.1, and P04 0.1.2 alongside P00 1.0.1. Provenance is recorded in `sources.lock.json`; P05 package consumers and `verify_packages.py` pass.
- Deterministic hashed vectors are fake control-flow fixtures, not semantic embeddings. Local hybrid retrieval and the tenant-scoped PostgreSQL pgvector/full-text adapter contract pass. The migration declares pgvector 0.8.7, cosine distance, HNSW, and GIN indexes; PostgreSQL service execution remains INCOMPLETE and semantic quality remains PENDING.
- MCP 2.3.0 Streamable HTTP bearer verification derives tenant/roles/scopes from trusted SDK request context. Authenticated and cross-tenant calls pass using the official SDK client over in-process ASGI; TCP-hosted service/identity-provider acceptance remains INCOMPLETE.
- Fake/local checks, package gate, and full gate were rerun; exact outputs are saved in `artifacts/evidence/remediation-*.txt`. PostgreSQL/Redis/LocalStack E2E, dashboard/alert E2E, replay/model evaluation remain INCOMPLETE/PENDING.
- `docker info` was attempted for service integration and exited 1 because Docker Desktop's Linux engine pipe was unavailable. No Compose or service E2E was run.

## 2026-10-21 — pgvector and authenticated MCP service gates

- PostgreSQL 16 with pgvector 0.8.7 applied the migration and verified the HNSW and GIN indexes. Hybrid retrieval returned the matching tenant's row and excluded another tenant using deterministic fake vectors. The script used a psycopg adapter for the repository's asyncpg-style placeholders because native asyncpg is absent from the lock; native driver integration remains INCOMPLETE.
- Authenticated MCP Streamable HTTP ran over loopback TCP. The local verifier allowed the matching tenant, denied cross-tenant retrieval, and rejected a missing bearer with HTTP 401. External identity-provider acceptance remains INCOMPLETE.
- The full gate remains INCOMPLETE: local tests, package provenance and OpenAPI pass, but the API still lacks a durable PostgreSQL/Redis queue-to-P04 worker-to-P01 agent product path. Semantic evaluation, replay, model quality, cost and comparable latency remain PENDING. Evidence: `artifacts/evidence/phase-008-service-gates-rerun.txt` and `phase-008-full-gate-rerun.txt`.


## 2026-10-22 — Phase 009 durable local runtime

- ADR-006 and version 0.4.0 add PostgreSQL product state/outbox, native asyncpg pgvector retrieval, Redis atomic rate limiting, signed delegated MCP tokens, P04 0.1.3 queue/worker, P01 0.1.1 LangGraph, approval resume and fake-only execution.
- Unit/contract/package suite: 86 passed. Native asyncpg/pgvector migration and hybrid tenant retrieval, cross-process Redis, authenticated loopback MCP, durable API restart, HITL, indirect-injection blocks, correlated trace, dashboard/alert and non-root services passed. Worker kill after a committed simulated effect recovered the job with exactly one product ledger row.
- Fake control quality gate passed ten fixtures; deliberately degraded control returned exit 1 and was rejected. Semantic/model quality, cost and comparable latency remain PENDING. External identity provider remains INCOMPLETE.
- Full evidence: `artifacts/evidence/phase-009-full-gate-final.txt`; crash evidence: `phase-009-crash-recovery.txt`; versioned API contract: `openapi.yaml`; decision: `docs/decisions/ADR-006-durable-runtime.md`.

- P05 0.4.0 wheel was built from source commit `4807292`, installed in an isolated target, and its packaged migration 003 was loaded/applied against the real PostgreSQL 16/pgvector 0.8.7 service. SHA-256 and artifact commit are recorded in `docs/harness/sources.lock.json`; see `phase-009-wheel-*.txt`.


## 2026-10-22 - Phase 010 retry recovery

- Independent review found an MCP connection failure wrapped in `ExceptionGroup` was classified permanent by the P04 adapter. A red test reproduced the P04 job as failed; after allowlisted recursive classification, the same real localhost refusal transitions to retrying and recovers on redelivery. Mixed groups, auth failures, and botocore `ClientError` remain permanent.
- The standalone worker loop backs off and retries explicit botocore endpoint/connect/read/closed-connection errors instead of exiting. Worker docs disclose the acceptance-time authorization snapshot and its local revocation limit; service E2E records that the snapshot survives delayed human approval unchanged.
- Phase 010 full fake-mode gate passed (92 tests, package/OpenAPI/fake evaluation gates, Docker promtool, pgvector/Redis/LocalStack/TCP MCP/API-to-worker-to-RAG service path, durable identity snapshot, HITL, correlated traces, alerts and crash recovery). See `artifacts/evidence/phase-010-full-gate.txt` and `phase-010-service-summary.json`.
- P05 0.4.0 wheel remains immutable; phase 010 releases the fix as 0.4.1 without route/schema changes. P05 0.4.1 source commit `f508d81`, wheel commit `3fa9ac9`, and SHA-256 `E07FA5827255923B4B8C48FC673B7CA222E6DCD46536D2C6089360EECFB495D4` are recorded in sources.lock; isolated consumer applied the packaged migration to PostgreSQL 16/pgvector 0.8.7 (exit 0).
- Real model quality, replay, cost, comparable latency remain PENDING; external identity/revocation remains INCOMPLETE. No production claim follows from local fake-mode service evidence.


## 2026-10-22 - Phase 011 OAuth introspection adapter

P05 now has an optional RFC 7662 token-introspection adapter for direct Streamable HTTP MCP callers. It validates active state, issuer, audience, subject, tenant, roles, scope, and expiry on every request without caching; local short-lived worker tokens remain supported. A local loopback protocol test showed an active token could call the MCP tool and the same token was denied after the issuer reported it inactive. Evidence: `artifacts/evidence/phase-011-introspection-green.txt`. The configured external provider is still pending; API auth remains local HS256 and queued jobs continue using the accepted authorization snapshot. The full gate ran with `--skip-services` (exit 2/INCOMPLETE) to avoid changing the already-running Docker stack; unit suite passed with 102 tests. Model eval remains PENDING: no traceable two-configuration cassette exists, and no live model run is authorized.

### Phase 011 local Keycloak verification update

A disposable Keycloak 26.8.1 container issued a test token; authenticated RFC 7662 introspection accepted its claims, and after calling Keycloak's revocation endpoint the same token became inactive. Evidence: `artifacts/evidence/phase-011-introspection-green.txt` and `phase-011-keycloak-oidc.txt`. This proves local Keycloak interoperability only. External issuer acceptance, API identity/revocation, and revocation of accepted queued work remain INCOMPLETE; API auth remains local HS256 and queued jobs continue using the accepted authorization snapshot. The full gate ran with `--skip-services` (exit 2/INCOMPLETE) to avoid changing the already-running P05 service stack; the complete unit suite now passes 103 tests. Model eval remains PENDING: fake fixtures do not evaluate model quality, no traceable two-configuration model cassette exists, and no live model run is authorized.

### Phase 011 release and identity gate closure

- Keycloak 26.8.1 issued a disposable user token. The token called `lookup_invoice` over authenticated MCP Streamable HTTP on loopback TCP; after token revocation, MCP rejected the same token with HTTP 401. See `artifacts/evidence/phase-011-keycloak-oidc.txt`. External IdP, API identity/revocation, and revocation of accepted jobs remain INCOMPLETE.
- P05 0.4.2 was built from source commit `7e3e6fca067e41d210e2f9010eb77636a3ca7458`, wheel artifact commit `092e65a3bf69a1f0d7e70a54a1aaa8642dc56bdc`, SHA-256 `65B0CEACEB017CEB2781ABF597ED8C9A70892EEE1933D3942C8B02EE4861EE79`. Its packaged migration passed against the disposable PostgreSQL 16/pgvector 0.8.7 consumer. Provenance is in `docs/harness/sources.lock.json`.
- Unit/full non-service gates passed (103 tests); `check_full.py --skip-services` returned 2/INCOMPLETE because the wider service stack was intentionally omitted. Model evaluation and comparable cost/latency stay PENDING; fixtures are fake controls, no valid model cassette exists, and no live paid call is authorized.

## 2026-10-22 — Phase 014 isolated full local gate

- The full gate now accepts a unique Compose project, dedicated loopback ports, and a phase-specific evidence prefix. It refuses to start on a non-empty project and removes only the stack it created, including its volumes.
- The first isolated attempt found that the host-port MCP check relied on the default `28001` allowlist. The service check now exercises unauthenticated denial, signed tenant-A access, and tenant-B denial over the API-to-MCP Compose TCP address. Diagnostic output is in `artifacts/evidence/phase-014-first-full-gate.txt`.
- `uv run --locked python scripts/check_fast.py` passed. `uv run --locked python scripts/check_full.py` passed without `--skip-services`: 103 tests, package and OpenAPI gates, fake-control regression check, PostgreSQL/Redis/LocalStack service flow, API restart recovery, HITL, tenant and injection controls, correlated traces, alerts, and worker crash recovery. Evidence: `artifacts/evidence/phase-014-full-gate.txt` and `phase-014-service-summary.json`.
- The isolated project left no containers, volumes, or networks. All 10 pre-existing P05 services remained running; see `artifacts/evidence/phase-014-cleanup.txt`.
- External identity acceptance and revocation of accepted jobs remain INCOMPLETE. Replay/model quality, cost, and comparable latency remain PENDING without authorized model runs or traceable cassettes.

## 2026-10-22 — Phase 015 API identity plan

- Phase 015 is planned to add optional RFC 7662 authentication at the API boundary, reusing the existing introspection contract while keeping API scopes and tenant checks local to the route layer. Local fake-mode HS256 remains available for development.
- The plan includes active/revoked token checks through the API using disposable Keycloak and explicitly excludes revocation of jobs accepted before token revocation. That policy remains pending a separate decision.
- Review: accepted for implementation. Harness docs check passed with 0 errors and 0 warnings. No product code or identity credentials changed in this planning task.

## 2026-10-22 — Phase 015 API identity implementation

- API authentication can use the configured RFC 7662 verifier (`API_AUTH_MODE=oidc`, `API_OIDC_*`); local HS256 remains the default for fake-mode development. API route scopes and tenant checks still run after token verification.
- Unit contracts passed (28 tests). Disposable Keycloak 26.8.1 proved an active bearer could call the API and MCP; after revocation both returned HTTP 401. Fast gate passed. Full isolated fake-mode gate passed with 104 tests; local model-quality fixtures remain control-flow only.
- Keycloak and the isolated full-gate Compose stack were removed. Existing P05 and other lab stacks were preserved. External issuer acceptance remains incomplete. At that point expiry enforcement was pending; see phase 016 below for the selected lease and its verification. Model evaluation remains PENDING by user choice.

## 2026-10-22 — Phase 016 durable authorization lease

- Applied the selected 15-minute lease from initial task acceptance. Migration 004 backfills existing jobs from `created_at`; retries and HITL resumes do not renew expiry. Expired jobs fail before dispatch/execution, and an expired approval resume returns HTTP 409; callers must submit a new task with fresh authorization and a new idempotency key. The simulated refund transaction also enforces the expiry.
- The first service run exposed that raising the expiry error inside the transaction rolled back the `failed` state. The expiry update now commits before HTTP 409 is raised; the corrected full gate passed.
- Fast gate and harness documentation gate passed. Full isolated service acceptance passed with 104 tests, including expired pre-dispatch and post-approval cases, the prior service flow, and worker crash recovery. Evidence: `artifacts/evidence/phase-016-full-gate.txt`; temporary Compose resources were removed.
- Replay/model evaluation remains PENDING per user choice; local fake controls make no model-quality claim. External issuer acceptance remains INCOMPLETE.

## 2026-10-23 — Phase 017 Redis Streams transport

- P05 durable delivery now uses the approved P04 0.1.4 Redis Streams wheel. PostgreSQL remains the source of task state; Redis Streams consumer groups handle delivery, delayed retries, reclaim and dead-letter routing. Local service Compose no longer needs LocalStack SQS.
- Updated the immutable P04 wheel provenance and P05 dependency lock. Unit and contract suite passed (104 tests); OpenAPI, package provenance and Docker Compose configuration checks passed.
- The isolated full fake-mode service gate passed with PostgreSQL/pgvector and Redis. It covered API restart recovery, tenant isolation, MCP auth, 15-minute authorization expiry, HITL, worker crash after a committed effect, and one ledger effect. Evidence: `artifacts/evidence/phase-017-full-gate.txt`, `phase-017-service-summary.json`, `phase-017-product-trace.json`, and `phase-017-service-down-alert.json`. Gate-created containers, network, and volumes were removed; existing stacks were preserved.
- Model quality, replay, provider cost/latency, and external IdP acceptance remain PENDING/INCOMPLETE. The deterministic fixtures are not model-quality evidence.

## 2026-10-26 — Phase 018 live RAG agent evaluation

- Added optional Groq-backed Core client with local tenant-scoped retrieval, citation-only evidence, no tools, and a USD 0.01 estimated cap. Fake RAG client remains unchanged.
- The first synthetic case had a missing dispatch message and correctly escalated. The final case asked where the link appears in a received message and passed tenant scope, citation, approval, and four-step assertions: 4 calls, 1575 input / 371 output tokens, estimated cost USD 0.000229425; billed cost `PENDING`.
- Two offline live-client tests and the 106-test full unit/contract gate passed. Docker-dependent service E2E remains incomplete.

## 2026-10-26 — Live evaluation readability cleanup

- Separate fixture construction, model catalog lookup, result assertions and artifact writing; format the client/triage code and exercise citations in the KB test.
- Full offline gate: INCOMPLETE (106 tests pass; Docker service E2E unavailable).
- Offline helper and static checks passed; no live calls were needed. Evidence: artifacts/evidence/code-cleanup/.

## 2026-10-26 — Live Docker acceptance

The fake full service gate passed with 110 tests, Docker E2E, security, adversarial and recovery checks. The dedicated live image includes the locked optional Groq SDK and prompt files. One live API/Redis-worker/PostgreSQL-RAG task passed every assertion with four actual calls (1748 input / 468 output tokens), a shipping citation, tenant denial, idempotency and correlated content-free Jaeger spans. Live refunds remain explicitly blocked before generation. Evidence: artifacts/evidence/live-docker/.

## 2026-10-26 - Docker restart recovery

Corrected inconsistent service restart policies after Docker startup left PostgreSQL/Redis stopped and API/worker failing DNS resolution. All Compose services now use unless-stopped. Recovered the 19 existing P05-owned containers without recreation or volume deletion; both API health endpoints return 200, backing services are healthy and fake worker is stable. Live worker remains explicitly stopped to prevent provider dispatch. Fast and full isolated fake gates passed; the latter exercised service E2E/security/worker recovery and cleaned its own resources. Evidence: `artifacts/evidence/docker-restart-recovery/report.md`. No daemon restart was forced; independent clean-context review remains pending. Broad model evaluation and campaign gates are unchanged.
## 2026-10-26 — Phase 019 privacy-safe campaign ledger

- Added P05-local append-only reservations, atomic cumulative caps, process lease, and content-free read-only resume. Unknown usage remains reserved; uncertain/completed trials cannot be replayed.
- Focused tests passed: 6 ledger tests and 11 campaign preparation tests. Full fake gate passed 127 tests with 2 warnings and returned `INCOMPLETE` because services were explicitly skipped; prior Docker recovery evidence remains unchanged.
- Groq dispatcher, human review, finite approved quota/caps, model preflight, runtime candidate identity, confirmation capacity, broad campaign, canary, and rollback remain pending. No provider call or Docker mutation occurred. Evidence: `artifacts/evidence/live-campaign-ledger/`.

## 2026-10-26 — Phase 020 complete token reservations

- Exposed the frozen primary, confirmation, and additive input/output token maxima in the content-free offline campaign dry-run; no config caps or authorization changed. Focused preparation tests (11) and fast checks passed. Full gate remains `INCOMPLETE` (exit 2): package consumers are not installed, service checks were explicitly omitted, and semantic/model evaluation remains `PENDING`. No Groq, credentials, network, or Docker access occurred. Evidence: `artifacts/evidence/live-token-reservations/`.

## 2026-10-26 — Phase 021 locked local acceptance

- Corrected the phase 020 diagnosis: its full-gate invocation used global Python outside the locked environment. The locked offline rerun passed 127 tests and every package/RAG/OpenAPI/control check; the historical failed invocation remains preserved.
- Full fake acceptance passed with exit 0 in the isolated `p05-locked-acceptance-021` Docker project, including service authorization, tenant separation, adversarial requests, correlated traces and kill-after-effect worker recovery. Temporary containers/volumes/network were removed; all pre-existing container identities and states were preserved, including the stopped live worker.
- Broad batch dispatch, shared account enforcement, quota/caps/reviews, real campaign quality and promotion canary/rollback remain INCOMPLETE. No Groq calls occurred. Evidence: `artifacts/evidence/locked-acceptance/`.

## 2026-10-27 — Phase 022 worker failure privacy

- Local fake workers now store fixed allowlisted failure codes. The P05 `ServiceWorker` converts permanent failures to the installed P04 worker's safe failure message and retains `TransientFailure` retry behavior with a fixed category. `DurableQueue.get` and the authenticated `/v1/tasks/{id}` response also mask arbitrary/legacy stored strings.
- Focused locked tests passed (38), including local failure persistence, the installed P04 worker behind the P05 wrapper, durable error reads, authenticated API responses, an in-memory span exporter, and an AST check requiring all P05 spans to disable automatic exception recording. Existing transient MCP retry regressions remain covered.
- Fast gate passed. Full locked fake/offline gate: 133 tests passed with two deprecation warnings; package provenance, fake retrieval controls, OpenAPI and both positive/negative quality controls passed. Overall status is INCOMPLETE because service integration was explicitly skipped to preserve running P05 stacks. No Docker/provider/external service or external network was used; existing protocol tests use ephemeral loopback listeners, and the retry refusal test targets closed `127.0.0.1:9`.
- Historical errors were masked on reads, not rewritten. Service-backed persistence and API behavior must be reverified in a later isolated service gate. Model quality remains PENDING; campaign approvals and promotion remain INCOMPLETE.

## 2026-10-27 — Phase 023 isolated service verification

- Reverified phase 022 against isolated fake-mode PostgreSQL/Redis/API/worker/MCP/telemetry services. A synthetic exception traversed the actual service worker and installed P04 task backend; only `invalid_input` persisted. A legacy raw error was masked by the authenticated task endpoint as `worker_failure`, while unauthenticated access returned 401. The sentinel was absent from database/outbox/API data. The direct probe's Jaeger trace was not observed; phase 022's in-memory exporter test and the complete service gate's correlated trace check passed separately.
- A service assertion exposed a stale expectation for raw `authorization lease expired`. It now requires `authorization_expired` and retains denial/no-effect checks. Full locked acceptance passed: 133 tests, retrieval fixture, package provenance, OpenAPI, positive/negative fake quality controls, isolated service/E2E/crash recovery; exit 0. Fast gate passed.
- Docker was constrained to existing local image `supportops-platform:groq-live`, read-only current source/script mounts, project `p05-phase023-failure-privacy`, and dedicated free loopback ports. No build, pull, provider, credential, paid use, or external connection occurred. The phase-owned containers/network/volumes were fully removed. Inventories: 102 existing container identities, 21 networks, 89 volumes were stable; one unrelated `gossett_backend` status age advanced but it remained `Restarting (1)` both before and after. See `artifacts/evidence/service-failure-privacy-023/`.
- The service assertion update changes test infrastructure only; product source/dependency/evaluation files remain identical to the phase 022 candidate `7bb496d16ad3ba0b175037a6a658f45a88eba61d`. Human/independent review, real model quality, dispatch/campaign approval and promotion remain PENDING/INCOMPLETE.

## 2026-10-27 — Phase 024 failure trace export: FAIL / INCOMPLETE

- Candidate `7f87d97b178145ba8739c42e04a62eca267c493d` changed the failure-privacy probe to bounded read-only Jaeger polling and fail closed when correlated failure spans are absent. Offline gates passed (focused 23 tests; complete offline suite 136 collected, pytest exit 0; fast check exit 0).
- The isolated full fake gate ran exactly one fresh synthetic failure task. The probe found the expected worker spans, then failed because the exported trace contained the synthetic exception sentinel. No trace body or sentinel value was retained in the artifact. The trace/task IDs were not emitted, remain unavailable, and will not be reconstructed, queried, or replayed. The complete service gate returned exit 2 / INCOMPLETE; service acceptance and crash recovery did not complete.
- An offline SDK reproduction established the likely exact cause: `record_exception=False` removes exception events, but automatic exception status still records the exception message in `status.description`. Phase 025 will set `set_status_on_exception=False` on all P05-owned spans and test both events and status descriptions.
- The phase Compose `down --volumes --remove-orphans` completed. Container/network/volume counts reconciled at 102/21/89; identity diffs are empty; the phase namespace is absent. The evidence does not establish all unrelated container status strings as unchanged, only that identities and inventories reconcile.
- Evidence: `artifacts/evidence/failure-trace-export-024/`. This is a privacy failure, not quality evidence. Model/campaign approvals, human/independent review and promotion remain pending/incomplete.

## 2026-10-27 — Phase 025 span status privacy: PASS scoped gates

- Fixed all P05-owned API, worker, agent, queue, MCP, tool and probe spans to suppress both exception events and automatic exception status descriptions. The in-memory regressions cover the worker and nested agent spans, events, status, attributes, serialized spans, the safe `invalid_input` failure code, and the locked SDK default behavior. AST coverage requires both options at every P05 span call site.
- Candidate `28a81fcf14c0a1ce32a24837abd2aab4f192fdf7` was committed before service startup. Fast and focused gates passed (25 focused tests); the complete offline suite passed 138 tests with two pre-existing deprecation warnings.
- The isolated fake full gate passed (exit 0), including one new service failure task. Jaeger readback observed seven spans and both expected failure spans; the sentinel was absent. Full service acceptance, correlated trace checks and kill-after-effect recovery passed. The generated product trace was reduced to operation names, service names, attribute keys and counts; no span attribute values or response bodies remain in the artifact.
- Only the cached `supportops-platform:groq-live` image (`sha256:0af6c40c175c5fa2f5278c01dac843b3978635ab36b9ee947071c75649203f30`) was used with read-only current source/script mounts. No provider calls, credential reads, paid use, image builds/pulls, or external calls occurred. Phase resources were removed; global Docker inventories remained 102 containers, 21 networks and 89 volumes. Existing container state/image and network/volume identity diffs were empty.
- Phase 024 remains a historical privacy FAIL; its unknown task/trace was never queried or replayed. P05 model quality, campaign approval, human/independent review, external identity, promotion and rollback remain PENDING/INCOMPLETE.
