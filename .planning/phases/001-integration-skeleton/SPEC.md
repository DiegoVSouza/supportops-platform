# Phase 001 — Integration skeleton

## Goal and acceptance
Create `supportops_platform` with health check, package boundary adapters, compose skeleton, and release metadata. Local interface doubles let components develop in parallel. Real package integration must pass only after approved P01–P04 wheel artifacts are installed and their version, source commit, and SHA-256 are recorded.

## Dependencies
P00–P04 repositories are independent. The skeleton may not import from `../p00` etc. Missing packages mean integration is INCOMPLETE, while the local double is clearly labeled.
