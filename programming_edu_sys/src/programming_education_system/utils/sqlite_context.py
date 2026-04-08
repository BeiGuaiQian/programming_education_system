"""SQLite-based context backend used when Redis is unavailable."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from programming_education_system.config.llm_config import Config

logger = logging.getLogger(__name__)


class SQLiteContextManager:
    """Persist lightweight context in a local SQLite database."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(self._resolve_db_path(db_path))
        self._init_database()

    def _resolve_db_path(self, db_path: Optional[str]) -> Path:
        path = Path(db_path or Config.SQLITE_CONTEXT_DB)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _init_database(self) -> None:
        logger.info("Using SQLite context database at %s", self.db_path)
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_context (
                    user_id TEXT PRIMARY KEY,
                    context_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dialog_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    dialog_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_progress (
                    user_id TEXT PRIMARY KEY,
                    progress_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def save_conversation_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        current = self.get_conversation_context(user_id) or {}
        merged = {**current, **context, "last_updated": datetime.now().isoformat()}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_context(user_id, context_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    context_json=excluded.context_json,
                    updated_at=excluded.updated_at
                """,
                (user_id, json.dumps(merged, ensure_ascii=False), datetime.now().isoformat()),
            )
        return True

    def get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT context_json FROM conversation_context WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save_dialog_history(self, user_id: str, dialog: Dict[str, Any]) -> bool:
        payload = dict(dialog)
        payload.setdefault("timestamp", datetime.now().isoformat())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO dialog_history(user_id, dialog_json, created_at)
                VALUES (?, ?, ?)
                """,
                (user_id, json.dumps(payload, ensure_ascii=False), datetime.now().isoformat()),
            )
            conn.execute(
                """
                DELETE FROM dialog_history
                WHERE user_id = ?
                  AND id NOT IN (
                      SELECT id FROM dialog_history
                      WHERE user_id = ?
                      ORDER BY id DESC
                      LIMIT 100
                  )
                """,
                (user_id, user_id),
            )
        return True

    def get_dialog_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT dialog_json FROM dialog_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [json.loads(row[0]) for row in reversed(rows)]

    def save_learning_progress(self, user_id: str, progress: Dict[str, Any]) -> bool:
        current = self.get_learning_progress(user_id) or {}
        merged = {**current, **progress, "last_updated": datetime.now().isoformat()}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO learning_progress(user_id, progress_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    progress_json=excluded.progress_json,
                    updated_at=excluded.updated_at
                """,
                (user_id, json.dumps(merged, ensure_ascii=False), datetime.now().isoformat()),
            )
        return True

    def get_learning_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT progress_json FROM learning_progress WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def clear_user_data(self, user_id: str) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM conversation_context WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM dialog_history WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM learning_progress WHERE user_id = ?", (user_id,))
        return True
