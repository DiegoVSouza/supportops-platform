CREATE TABLE IF NOT EXISTS platform_objects (
  tenant_id text NOT NULL, kind text NOT NULL, id text NOT NULL, data jsonb NOT NULL,
  PRIMARY KEY (tenant_id,kind,id)
);
CREATE TABLE IF NOT EXISTS platform_jobs (
  id text PRIMARY KEY, tenant_id text NOT NULL, idempotency_key text NOT NULL,
  ticket_id text NOT NULL, principal jsonb NOT NULL, trace_context jsonb NOT NULL,
  status text NOT NULL DEFAULT 'queued', result jsonb, error text, approval_id text,
  generation integer NOT NULL DEFAULT 0, dispatched boolean NOT NULL DEFAULT false,
  backend_task_id text, created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id,idempotency_key)
);
CREATE INDEX IF NOT EXISTS platform_jobs_pending ON platform_jobs(created_at) WHERE NOT dispatched;
CREATE TABLE IF NOT EXISTS platform_effects (
  job_id text PRIMARY KEY REFERENCES platform_jobs(id), result jsonb NOT NULL
);
