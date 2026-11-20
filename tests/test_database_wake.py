"""A scale-to-zero database answers "starting up" for a while; boot must wait for it instead of crashing."""

import psycopg
import pytest

from supportops_platform import persistence
from supportops_platform.persistence import PostgresStore


class Conn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *_args, **_kwargs):
        return []


def test_migrate_waits_for_a_database_that_is_still_starting(monkeypatch):
    attempts = []

    def connect(dsn, **_kwargs):
        attempts.append(dsn)
        if len(attempts) < 3:
            raise psycopg.OperationalError("FATAL:  the database system is starting up")
        return Conn()

    monkeypatch.setattr(persistence.psycopg, "connect", connect)
    slept = []
    store = PostgresStore("postgresql://x")
    store.wait_sleep = slept.append
    store.migrate()
    assert len(attempts) == 3
    assert slept == [1, 2]


def test_migrate_gives_up_with_the_original_error_after_the_deadline(monkeypatch):
    def connect(dsn, **_kwargs):
        raise psycopg.OperationalError("FATAL:  the database system is starting up")

    monkeypatch.setattr(persistence.psycopg, "connect", connect)
    store = PostgresStore("postgresql://x", wait_seconds=0)
    store.wait_sleep = lambda _s: None
    with pytest.raises(psycopg.OperationalError, match="starting up"):
        store.migrate()
