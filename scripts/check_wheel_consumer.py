"""Verify the built P05 wheel is independently importable and carries its migrations."""

import os
from importlib import resources
from pathlib import Path

import psycopg
import supportops_platform
from supportops_platform.persistence import PostgresStore

EXPECTED = os.environ["P05_WHEEL_TARGET"]
PACKAGE_ROOT = Path(supportops_platform.__file__).resolve().parent
assert Path(supportops_platform.__file__).resolve().is_relative_to(Path(EXPECTED).resolve())
assert supportops_platform.__version__ == "0.4.3"
migration = resources.files("supportops_platform").joinpath("migrations/003_product_state.sql")
assert migration.is_file() and "platform_jobs" in migration.read_text(encoding="utf-8")
PostgresStore(os.environ["P05_TEST_DSN"]).migrate()
with psycopg.connect(os.environ["P05_TEST_DSN"]) as connection:
    extension = connection.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()[0]
    jobs = connection.execute("SELECT to_regclass('platform_jobs')").fetchone()[0]
assert extension == "0.8.7" and jobs == "platform_jobs"
print(f"isolated wheel consumer: PASS; version={supportops_platform.__version__}; source={PACKAGE_ROOT}; migration loaded/applied; PostgreSQL pgvector={extension}")
