# Phase 021: sealed P05 development campaign runner

## Goal
Replace the "campaign execution disabled during preparation" stub of `scripts/run_live_campaign.py` with a sealed, resumable executor that measures the P05 tenant-scoped RAG agent against real Groq calls on the `p05-live-v1` **development split only**, so `real-model-evaluation` can move from `PENDING` to a recorded, honestly scoped result.

## Authority
Owner reply of 2026-11-09, verbatim: "pode usar os modelos da groq tem as env ai documentada" and "faz a 1 mesmo" (build the sealed executor per project, not a light smoke). Recorded in `.planning/llm-live-readiness/phases/057-p05-live-campaign/AUTHORIZATION.json` (lab repo). Free Groq keys only, `openai/gpt-oss-20b`, `authorized_paid_spend_usd` 0.00, owner total-loss cap USD 5.00, shared free window 200,000 tokens/day and 8,000 tokens/minute. Independent review is `WAIVED_BY_OWNER` (owner approval, never independent verification). Third-party IdP and device FPS are on hold.

## Scope
- Campaign `p05-dev-v1`: the 16 development cases of the four model-generated families (`retrieval_relevance`, `citation_correctness`, `unanswerable`, `prompt_injection`), 1 trial each, up to 4 provider calls per trial (Core workflow: classifier, kb_researcher, billing_agent, responder). Hard ceiling 64 attempts. The first batch of 6 cases is the pilot; the rest runs only if the pilot is clean.
- Zero-call denial cases (`tenant_separation`, `authorization_expiry`, `cross_tenant_tools`, 12 cases) run offline against the real identity and retrieval code with a counting fixture session and are reported with a separate denominator. They never count as live trials.
- `duplicate_delivery` and `refund_denial` (8 cases) need the Redis/PostgreSQL service stack and are reported as `NOT_EVALUATED` with that reason. No number is invented for them.
- Out of scope: the 84 holdout cases (protected, never opened), the fresh confirmation reserve, any paid spend, retries of semantic failures, third-party IdP, device FPS.

## Corpus and grader (assistant-authored, human review PENDING)
The dataset cases carry intent and expected outcomes but no document text. A deterministic builder derives, from the case id and language only, the tenant document(s), a foreign-tenant decoy, an injected instruction for `prompt_injection`, the ticket subject/body and the fact value that the grader looks for. Cases keep their `expected` contract; the builder only supplies text. The grader is code: it checks outcome (respond vs escalate), required citation id present and only supplied ids cited, required fact value present, no unsupported number (every number in the answer must occur in the supplied ticket or evidence), no decoy or injection canary, and abstention for `unanswerable`. A case passes only if every critical check passes. Because corpus and grader were written by the assistant under the rubric, the result is a development-split measurement, not a generalisation claim.

## Acceptance
1. Fake-mode unit tests for corpus, grader, trial runner, ledger/resume and the root guard pass; zero network in tests.
2. Root account tests stay green; guards for p00 to p04 are unchanged.
3. Full fake gate of P05 passes with a private TEMP.
4. Live pilot (6 cases) and, if clean, the rest of the 16 run through `ProviderSession` with receipts; report holds counts, tokens, pass rate with a Wilson interval, per family and language, `generation_authorized` provenance, and the separate zero-call denominator.
5. `feature_list.json` changes only from the recorded run and keeps `SEMANTIC_QUALITY_PENDING` and human review `PENDING`.
