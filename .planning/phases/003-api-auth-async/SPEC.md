# Phase 003 — API, authorization, and async tasks

## Goal and acceptance
Freeze OpenAPI v1 for ticket create/read, human approval, feedback, health, and metrics. Enforce JWT scopes, tenant isolation, rate limits, async task state, and approval before sensitive billing effects. Tenant A must never read Tenant B data.
