DROP INDEX IF EXISTS platform_jobs_authorization_expiry;
ALTER TABLE platform_jobs DROP COLUMN IF EXISTS authorization_expires_at;
