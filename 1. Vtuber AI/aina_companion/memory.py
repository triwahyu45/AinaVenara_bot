from __future__ import annotations

import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from .config import data_dir

SCHEMA_VERSION = 1
VALID_ROLES = {"user", "model", "system"}


class LegacyDatabaseError(RuntimeError):
    """Raised when an unversioned database must not be reused silently."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id() -> str:
    return str(uuid.uuid4())


class MemoryStore:
    """SQLite repository for local conversation memory only."""

    def __init__(self, path: Path | None = None):
        self.path = path or data_dir() / "memory_v2.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        existing_tables = {
            row["name"]
            for row in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if existing_tables and "schema_migrations" not in existing_tables:
            self.db.close()
            raise LegacyDatabaseError(
                f"Database legacy tanpa versi tidak digunakan: {self.path}. "
                "Pilih database v2 baru agar data lama tidak merusak sesi."
            )

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied = {
            row["version"] for row in self.db.execute("SELECT version FROM schema_migrations")
        }
        if 1 not in applied:
            self._apply_v1()
        self.db.commit()

    def _apply_v1(self) -> None:
        with self.db:
            self.db.executescript(
                """
                CREATE TABLE sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'model', 'system')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX messages_session_created_at
                    ON messages(session_id, created_at, id);
                CREATE TABLE facts (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self.db.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, utc_now()),
            )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            with self.db:
                yield self.db

    def schema_version(self) -> int:
        with self._lock:
            row = self.db.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
        return int(row["version"] or 0)

    def create_session(self, title: str = "Percakapan baru") -> str:
        session_id = new_id()
        now = utc_now()
        with self._transaction():
            self.db.execute(
                "INSERT INTO sessions(id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title.strip() or "Percakapan baru", now, now),
            )
        return session_id

    def ensure_session(self, session_id: str | None = None) -> str:
        with self._lock:
            if session_id and self.db.execute(
                "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
            ).fetchone():
                return session_id
            existing = self.db.execute(
                "SELECT id FROM sessions ORDER BY updated_at DESC, created_at DESC LIMIT 1"
            ).fetchone()
            return existing["id"] if existing else self.create_session()

    def delete_session(self, session_id: str) -> None:
        with self._transaction():
            self.db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def add_message(self, session_id: str, role: str, content: str) -> str:
        if role not in VALID_ROLES:
            raise ValueError(f"Role pesan tidak valid: {role}")
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Isi pesan tidak boleh kosong.")
        message_id = new_id()
        now = utc_now()
        with self._transaction():
            self.db.execute(
                """
                INSERT INTO messages(id, session_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, clean_content, now),
            )
            self.db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
            )
        return message_id

    def recent_messages(self, session_id: str, limit: int) -> list[dict[str, str]]:
        if limit <= 0:
            return []
        with self._lock:
            rows = self.db.execute(
                """
                SELECT id, role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def message_count(self, session_id: str) -> int:
        with self._lock:
            row = self.db.execute(
                "SELECT COUNT(*) AS count FROM messages WHERE session_id = ?", (session_id,)
            ).fetchone()
        return int(row["count"])

    def sessions(self) -> list[dict[str, str]]:
        with self._lock:
            rows = self.db.execute(
                """
                SELECT id, title, summary, created_at, updated_at
                FROM sessions
                ORDER BY updated_at DESC, created_at DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def summary(self, session_id: str) -> str:
        with self._lock:
            row = self.db.execute(
                "SELECT summary FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row["summary"] if row else ""

    def set_summary(self, session_id: str, summary: str) -> None:
        with self._transaction():
            cursor = self.db.execute(
                "UPDATE sessions SET summary = ?, updated_at = ? WHERE id = ?",
                (summary.strip(), utc_now(), session_id),
            )
        if cursor.rowcount != 1:
            raise KeyError(f"Sesi tidak ditemukan: {session_id}")

    def add_fact(self, content: str) -> str:
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Isi fakta tidak boleh kosong.")
        fact_id = new_id()
        now = utc_now()
        with self._transaction():
            self.db.execute(
                """
                INSERT INTO facts(id, content, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (fact_id, clean_content, now, now),
            )
        return fact_id

    def update_fact(self, fact_id: str, content: str, enabled: bool = True) -> None:
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Isi fakta tidak boleh kosong.")
        with self._transaction():
            cursor = self.db.execute(
                """
                UPDATE facts SET content = ?, enabled = ?, updated_at = ?
                WHERE id = ?
                """,
                (clean_content, int(enabled), utc_now(), fact_id),
            )
        if cursor.rowcount != 1:
            raise KeyError(f"Fakta tidak ditemukan: {fact_id}")

    def delete_fact(self, fact_id: str) -> None:
        with self._transaction():
            self.db.execute("DELETE FROM facts WHERE id = ?", (fact_id,))

    def facts(self, enabled_only: bool = False) -> list[dict[str, object]]:
        where = " WHERE enabled = 1" if enabled_only else ""
        with self._lock:
            rows = self.db.execute(
                f"SELECT id, content, enabled, created_at, updated_at FROM facts{where} ORDER BY rowid"
            ).fetchall()
            return [dict(row) for row in rows]

    def clear(self) -> None:
        with self._transaction():
            self.db.execute("DELETE FROM messages")
            self.db.execute("DELETE FROM sessions")
            self.db.execute("DELETE FROM facts")

    def close(self) -> None:
        with self._lock:
            self.db.close()

    def context(self, session_id: str, limit: int) -> dict[str, object]:
        with self._lock:
            return {
                "summary": self.summary(session_id),
                "facts": [fact["content"] for fact in self.facts(enabled_only=True)],
                "messages": self.recent_messages(session_id, limit),
            }
