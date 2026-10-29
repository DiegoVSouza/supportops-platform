"""Durable P05 campaign reservations and local process lease."""

from __future__ import annotations

import json
import os
import socket
import sqlite3
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator


class CampaignBlocked(RuntimeError):
    """A campaign action would violate the durable execution contract."""


class CampaignLedger:
    def __init__(
        self,
        path: Path,
        *,
        campaign_id: str,
        read_only: bool = False,
    ) -> None:
        self.path = path
        self.campaign_id = campaign_id
        self.read_only = read_only
        if not read_only:
            path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(path)) as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("PRAGMA synchronous=FULL")
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id TEXT NOT NULL,
                        case_id TEXT NOT NULL,
                        trial INTEGER NOT NULL,
                        event TEXT NOT NULL CHECK(event IN ('reserved','completed')),
                        reserved_calls INTEGER NOT NULL,
                        reserved_input_tokens INTEGER NOT NULL,
                        reserved_output_tokens INTEGER NOT NULL,
                        reserved_cost_usd TEXT NOT NULL,
                        actual_input_tokens INTEGER,
                        actual_output_tokens INTEGER,
                        actual_cost_usd TEXT,
                        outcome TEXT,
                        error_class TEXT,
                        created_at_utc TEXT NOT NULL,
                        UNIQUE(campaign_id, case_id, trial, event)
                    );
                    CREATE TRIGGER IF NOT EXISTS events_no_update
                    BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'append-only ledger'); END;
                    CREATE TRIGGER IF NOT EXISTS events_no_delete
                    BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'append-only ledger'); END;
                    """
                )
                db.commit()

    def _connect(self) -> sqlite3.Connection:
        if self.read_only:
            return sqlite3.connect(
                f"file:{self.path.as_posix()}?mode=ro", uri=True, timeout=30
            )
        return sqlite3.connect(self.path, timeout=30, isolation_level=None)

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        db = self._connect()
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def _latest(db: sqlite3.Connection) -> list[sqlite3.Row]:
        return db.execute(
            """SELECT e.* FROM events e JOIN (
                 SELECT campaign_id,case_id,trial,MAX(sequence) AS sequence
                 FROM events GROUP BY campaign_id,case_id,trial
               ) latest ON e.sequence=latest.sequence"""
        ).fetchall()

    def totals(self) -> dict[str, int | Decimal]:
        with self._db() as db:
            rows = self._latest(db)
        return {
            "requests": sum(row["reserved_calls"] for row in rows),
            "input_tokens": sum(
                row["actual_input_tokens"]
                if row["actual_input_tokens"] is not None
                else row["reserved_input_tokens"]
                for row in rows
            ),
            "output_tokens": sum(
                row["actual_output_tokens"]
                if row["actual_output_tokens"] is not None
                else row["reserved_output_tokens"]
                for row in rows
            ),
            "estimated_cost_usd": sum(
                (
                    Decimal(row["actual_cost_usd"])
                    if row["actual_cost_usd"] is not None
                    else Decimal(row["reserved_cost_usd"])
                )
                for row in rows
            ),
        }

    def reserve(
        self,
        *,
        case_id: str,
        trial: int,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: Decimal,
        caps: dict[str, int | Decimal],
        calls: int = 1,
    ) -> None:
        if self.read_only:
            raise CampaignBlocked("read-only ledger")
        if (
            type(calls) is not int
            or not 1 <= calls <= 4
            or trial < 1
            or input_tokens < 1
            or output_tokens < 1
            or estimated_cost_usd < 0
        ):
            raise CampaignBlocked("invalid trial reservation")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT 1 FROM events WHERE campaign_id=? AND case_id=? AND trial=?",
                (self.campaign_id, case_id, trial),
            ).fetchone()
            if existing:
                raise CampaignBlocked("trial already has a reservation or result")
            rows = self._latest(db)
            current = {
                "requests": sum(row["reserved_calls"] for row in rows),
                "input_tokens": sum(
                    row["actual_input_tokens"]
                    if row["actual_input_tokens"] is not None
                    else row["reserved_input_tokens"]
                    for row in rows
                ),
                "output_tokens": sum(
                    row["actual_output_tokens"]
                    if row["actual_output_tokens"] is not None
                    else row["reserved_output_tokens"]
                    for row in rows
                ),
                "estimated_cost_usd": sum(
                    Decimal(row["actual_cost_usd"])
                    if row["actual_cost_usd"] is not None
                    else Decimal(row["reserved_cost_usd"])
                    for row in rows
                ),
            }
            projected = {
                **current,
                "requests": current["requests"] + calls,
                "input_tokens": current["input_tokens"] + input_tokens,
                "output_tokens": current["output_tokens"] + output_tokens,
                "estimated_cost_usd": current["estimated_cost_usd"] + estimated_cost_usd,
            }
            if any(projected[key] > caps[key] for key in projected):
                raise CampaignBlocked("cumulative reservation cap would be exceeded")
            db.execute(
                """INSERT INTO events(campaign_id,case_id,trial,event,reserved_calls,
                   reserved_input_tokens,reserved_output_tokens,reserved_cost_usd,created_at_utc)
                   VALUES(?,?,?,'reserved',?,?,?,?,?)""",
                (
                    self.campaign_id,
                    case_id,
                    trial,
                    calls,
                    input_tokens,
                    output_tokens,
                    str(estimated_cost_usd),
                    datetime.now(UTC).isoformat(),
                ),
            )
            db.commit()

    def complete(
        self,
        *,
        case_id: str,
        trial: int,
        input_tokens: int | None,
        output_tokens: int | None,
        actual_cost_usd: Decimal | None,
        outcome: str,
        error_class: str | None,
    ) -> None:
        if self.read_only:
            raise CampaignBlocked("read-only ledger")
        with self._db() as db:
            reservation = db.execute(
                """SELECT reserved_calls,reserved_input_tokens,reserved_output_tokens,
                   reserved_cost_usd FROM events WHERE campaign_id=? AND case_id=? AND trial=?
                   AND event='reserved'""",
                (self.campaign_id, case_id, trial),
            ).fetchone()
            if not reservation:
                raise CampaignBlocked("trial has no reservation")
            db.execute(
                """INSERT INTO events(campaign_id,case_id,trial,event,reserved_calls,
                   reserved_input_tokens,reserved_output_tokens,reserved_cost_usd,
                   actual_input_tokens,actual_output_tokens,actual_cost_usd,outcome,error_class,created_at_utc)
                   VALUES(?,?,?,'completed',?,?,?,?,?,?,?,?,?,?)""",
                (
                    self.campaign_id,
                    case_id,
                    trial,
                    reservation["reserved_calls"],
                    reservation["reserved_input_tokens"],
                    reservation["reserved_output_tokens"],
                    reservation["reserved_cost_usd"],
                    input_tokens,
                    output_tokens,
                    str(actual_cost_usd) if actual_cost_usd is not None else None,
                    outcome,
                    error_class,
                    datetime.now(UTC).isoformat(),
                ),
            )

    def reserved_trials(self) -> list[dict[str, Any]]:
        with self._db() as db:
            rows = db.execute(
                """SELECT case_id,trial,event,outcome,error_class,actual_input_tokens,
                   actual_output_tokens,actual_cost_usd FROM events
                   WHERE campaign_id=? ORDER BY sequence""",
                (self.campaign_id,),
            ).fetchall()
        return [dict(row) for row in rows]


class CampaignLease:
    def __init__(self, path: Path, *, campaign_id: str) -> None:
        self.path = path
        self.campaign_id = campaign_id
        self.file: Any = None

    def __enter__(self) -> CampaignLease:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+b")
        self.file.seek(0, os.SEEK_END)
        if self.file.tell() == 0:
            self.file.write(b"\0")
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.file.close()
            raise CampaignBlocked("another P05 campaign holds the local lease") from exc
        metadata = json.dumps(
            {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "campaign_id": self.campaign_id,
                "started_at_utc": datetime.now(UTC).isoformat(),
            },
            sort_keys=True,
        ).encode("utf-8")
        self.file.seek(1)
        self.file.truncate()
        self.file.write(metadata)
        self.file.flush()
        return self

    def __exit__(self, *_: object) -> None:
        if self.file is not None:
            if os.name == "nt":
                import msvcrt

                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
            self.file.close()
