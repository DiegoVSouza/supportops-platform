# Docker restart recovery

Repair P05 dependency loss after Docker daemon restart. API/worker logs show psycopg DNS failure for postgres while dependency containers are exited. Apply consistent unless-stopped restart policy to service Compose, preserve existing volumes and credentials, and restore the P05 fake stack. Keep live worker stopped to prevent unapproved generation. Validate using isolated fake-mode service acceptance and real container state. No provider calls, external messages, refunds, or unrelated stack changes.
