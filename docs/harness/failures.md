# Failures

Record recurring builder or product failures here before fixing them.

## 2026-10-26 — Application restart without backing services

Observed: P05 API/worker restarted repeatedly with psycopg OperationalError (Name or service not known); PostgreSQL/Redis containers were exited after Docker restart. Cause: inconsistent restart policies, with on-failure only on application processes. Correction: consistent unless-stopped policy in Compose and the existing owned containers, followed by state-preserving dependency recovery. Explicitly stopped services still require manual startup. Evidence: artifacts/evidence/docker-restart-recovery/. No Docker daemon restart was forced because other projects share the daemon.
