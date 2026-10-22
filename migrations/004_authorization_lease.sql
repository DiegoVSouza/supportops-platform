ALTER TABLE platform_jobs
  ADD COLUMN IF NOT EXISTS authorization_expires_at timestamptz;

UPDATE platform_jobs
SET authorization_expires_at = created_at + interval '15 minutes'
WHERE authorization_expires_at IS NULL;

ALTER TABLE platform_jobs
  ALTER COLUMN authorization_expires_at SET DEFAULT (now() + interval '15 minutes'),
  ALTER COLUMN authorization_expires_at SET NOT NULL;

CREATE INDEX IF NOT EXISTS platform_jobs_authorization_expiry
  ON platform_jobs(authorization_expires_at)
  WHERE status IN ('queued', 'needs_approval');
