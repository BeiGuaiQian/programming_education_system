"""SQLite-backed storage for users, sessions, and chat history."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


class AppStore:
    """Persistent application store for auth and chat data."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(Path(db_path))
        self._local = threading.local()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            self._init_db()
        except sqlite3.DatabaseError as exc:
            if not self._is_database_corruption(exc):
                raise
            self.close()
            self._recover_malformed_database(exc)
            self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is not None:
            return connection

        connection = self._open_connection()
        self._local.connection = connection
        return connection

    def _open_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.db_path,
            timeout=5,
            check_same_thread=False,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA temp_store=MEMORY")
            connection.execute("PRAGMA cache_size=-20000")
            connection.execute("PRAGMA mmap_size=268435456")
        except sqlite3.DatabaseError:
            connection.close()
            raise
        return connection

    def close(self) -> None:
        connection = getattr(self._local, "connection", None)
        if connection is not None:
            connection.close()
            self._local.connection = None

    def _recover_malformed_database(self, exc: sqlite3.DatabaseError) -> None:
        db_path = Path(self.db_path)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        for suffix in ("", "-wal", "-shm"):
            path = Path(f"{self.db_path}{suffix}")
            if not path.exists():
                continue
            backup = db_path.with_name(f"{db_path.name}{suffix}.corrupt-{timestamp}")
            if backup.exists():
                backup = db_path.with_name(
                    f"{db_path.name}{suffix}.corrupt-{timestamp}-{secrets.token_hex(3)}"
                )
            path.replace(backup)
        print(
            f"SQLite database was malformed and has been backed up near {db_path}. "
            f"A fresh database will be created. Original error: {exc}"
        )

    @staticmethod
    def _is_database_corruption(exc: sqlite3.DatabaseError) -> bool:
        message = str(exc).lower()
        return "malformed" in message or "file is not a database" in message

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    nickname TEXT,
                    avatar_url TEXT,
                    bio TEXT,
                    learning_goal TEXT,
                    learning_style TEXT,
                    preferred_pace TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    access_token_hash TEXT NOT NULL UNIQUE,
                    refresh_token_hash TEXT NOT NULL UNIQUE,
                    access_expires_at TEXT NOT NULL,
                    refresh_expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    request_type TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                    FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_access ON sessions(access_token_hash);
                CREATE INDEX IF NOT EXISTS idx_sessions_refresh ON sessions(refresh_token_hash);
                CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(username, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, id ASC);

                CREATE TABLE IF NOT EXISTS lesson_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    score REAL NOT NULL,
                    feedback TEXT NOT NULL,
                    structured_feedback TEXT,
                    submitted_at TEXT NOT NULL,
                    FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_lesson_submissions_user_lesson
                ON lesson_submissions(username, lesson_id, submitted_at DESC);

                CREATE TABLE IF NOT EXISTS question_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    score REAL NOT NULL,
                    feedback TEXT NOT NULL,
                    test_result TEXT,
                    submitted_at TEXT NOT NULL,
                    FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_question_submissions_user_question
                ON question_submissions(username, question_id, submitted_at DESC);

                CREATE TABLE IF NOT EXISTS learning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT,
                    duration_seconds REAL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_learning_events_user_created
                ON learning_events(username, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_learning_events_user_target
                ON learning_events(username, target_type, target_id);
                """
            )
            user_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(users)").fetchall()
            }
            if "nickname" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
            if "avatar_url" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
            if "bio" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN bio TEXT")
            if "learning_goal" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN learning_goal TEXT")
            if "learning_style" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN learning_style TEXT")
            if "preferred_pace" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN preferred_pace TEXT")
            conn.execute(
                """
                UPDATE users
                SET nickname = username
                WHERE nickname IS NULL OR TRIM(nickname) = ''
                """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(lesson_submissions)").fetchall()
            }
            if "structured_feedback" not in columns:
                conn.execute("ALTER TABLE lesson_submissions ADD COLUMN structured_feedback TEXT")

    def validate_username(self, username: str) -> str:
        normalized = username.strip()
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise ValueError("用户名需为 3-32 位，仅支持字母、数字和下划线")
        return normalized

    def validate_password(self, password: str) -> str:
        if len(password) < 6:
            raise ValueError("密码至少需要 6 位")
        if len(password) > 128:
            raise ValueError("密码长度不能超过 128 位")
        return password

    def create_user(self, username: str, password: str) -> Dict[str, Any]:
        username = self.validate_username(username)
        password = self.validate_password(password)
        if self.get_user(username) is not None:
            raise ValueError("用户名已存在")

        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        now = self._now()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, password_salt, nickname, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, password_hash, salt, username, now, now),
            )
        return self.get_user(username) or {"username": username, "created_at": now}

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    username,
                    nickname,
                    avatar_url,
                    bio,
                    learning_goal,
                    learning_style,
                    preferred_pace,
                    created_at,
                    updated_at
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
        return dict(row) if row else None

    def update_user_profile(
        self,
        username: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_nickname = nickname.strip() if nickname is not None else None
        clean_avatar = avatar_url.strip() if avatar_url is not None else None
        clean_bio = bio.strip() if bio is not None else None

        if clean_nickname is not None and not 1 <= len(clean_nickname) <= 32:
            raise ValueError("昵称长度需要在 1-32 个字符之间")
        if clean_avatar is not None and len(clean_avatar) > 500:
            raise ValueError("头像地址不能超过 500 个字符")
        if clean_bio is not None and len(clean_bio) > 160:
            raise ValueError("个人简介不能超过 160 个字符")

        updates: List[str] = []
        values: List[Any] = []
        if clean_nickname is not None:
            updates.append("nickname = ?")
            values.append(clean_nickname)
        if clean_avatar is not None:
            updates.append("avatar_url = ?")
            values.append(clean_avatar)
        if clean_bio is not None:
            updates.append("bio = ?")
            values.append(clean_bio)

        if not updates:
            user = self.get_user(username)
            if user is None:
                raise ValueError("用户不存在")
            return user

        updates.append("updated_at = ?")
        values.append(self._now())
        values.append(username)

        with self._connect() as conn:
            cursor = conn.execute(
                f"""
                UPDATE users
                SET {", ".join(updates)}
                WHERE username = ?
                """,
                tuple(values),
            )
        if cursor.rowcount == 0:
            raise ValueError("用户不存在")
        user = self.get_user(username)
        if user is None:
            raise ValueError("用户不存在")
        return user

    def update_learning_preferences(
        self,
        username: str,
        learning_goal: Optional[str] = None,
        learning_style: Optional[str] = None,
        preferred_pace: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_goal = learning_goal.strip() if learning_goal is not None else None
        clean_style = learning_style.strip() if learning_style is not None else None
        clean_pace = preferred_pace.strip() if preferred_pace is not None else None

        if clean_goal is not None and len(clean_goal) > 120:
            raise ValueError("学习目标不能超过 120 个字符")
        if clean_style is not None and clean_style not in {
            "",
            "concept_first",
            "example_first",
            "practice_first",
            "debug_first",
        }:
            raise ValueError("学习方式不在支持范围内")
        if clean_pace is not None and clean_pace not in {"", "slow", "normal", "fast"}:
            raise ValueError("学习节奏不在支持范围内")

        updates: List[str] = []
        values: List[Any] = []
        if clean_goal is not None:
            updates.append("learning_goal = ?")
            values.append(clean_goal)
        if clean_style is not None:
            updates.append("learning_style = ?")
            values.append(clean_style)
        if clean_pace is not None:
            updates.append("preferred_pace = ?")
            values.append(clean_pace)

        if not updates:
            user = self.get_user(username)
            if user is None:
                raise ValueError("用户不存在")
            return user

        updates.append("updated_at = ?")
        values.append(self._now())
        values.append(username)

        with self._connect() as conn:
            cursor = conn.execute(
                f"""
                UPDATE users
                SET {", ".join(updates)}
                WHERE username = ?
                """,
                tuple(values),
            )
        if cursor.rowcount == 0:
            raise ValueError("用户不存在")
        user = self.get_user(username)
        if user is None:
            raise ValueError("用户不存在")
        return user

    def verify_user(self, username: str, password: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT password_hash, password_salt
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
        if row is None:
            return False
        expected = str(row["password_hash"])
        calculated = self._hash_password(password, str(row["password_salt"]))
        return hmac.compare_digest(expected, calculated)

    def ensure_user(self, username: str, password: str) -> None:
        try:
            if self.get_user(username) is None:
                self.create_user(username, password)
        except (ValueError, sqlite3.IntegrityError):
            return

    def create_session(
        self,
        username: str,
        access_token: str,
        refresh_token: str,
        access_expires_at: str,
        refresh_expires_at: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    username, access_token_hash, refresh_token_hash,
                    access_expires_at, refresh_expires_at, created_at, revoked_at
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    username,
                    self._hash_token(access_token),
                    self._hash_token(refresh_token),
                    access_expires_at,
                    refresh_expires_at,
                    self._now(),
                ),
            )

    def get_session_by_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        return self._get_session("access_token_hash", self._hash_token(access_token))

    def get_session_by_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        return self._get_session("refresh_token_hash", self._hash_token(refresh_token))

    def revoke_session_by_access_token(self, access_token: str) -> None:
        self._revoke_session("access_token_hash", self._hash_token(access_token))

    def revoke_session_by_refresh_token(self, refresh_token: str) -> None:
        self._revoke_session("refresh_token_hash", self._hash_token(refresh_token))

    def create_conversation(self, username: str, title: str) -> Dict[str, Any]:
        conversation_id = secrets.token_hex(12)
        now = self._now()
        clean_title = (title or "新对话").strip()[:80] or "新对话"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, username, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (conversation_id, username, clean_title, now, now),
            )
        return {
            "id": conversation_id,
            "username": username,
            "title": clean_title,
            "created_at": now,
            "updated_at": now,
        }

    def get_conversation(self, username: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, title, created_at, updated_at
                FROM conversations
                WHERE id = ? AND username = ?
                """,
                (conversation_id, username),
            ).fetchone()
        return dict(row) if row else None

    def add_message(
        self,
        username: str,
        conversation_id: str,
        role: str,
        content: str,
        request_type: str | None = None,
    ) -> Dict[str, Any]:
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (conversation_id, username, role, content, request_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (conversation_id, username, role, content, request_type, now),
            )
            conn.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ? AND username = ?
                """,
                (now, conversation_id, username),
            )
        return {
            "conversation_id": conversation_id,
            "username": username,
            "role": role,
            "content": content,
            "request_type": request_type,
            "created_at": now,
        }

    def list_conversations(self, username: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,
                    (
                        SELECT m.content
                        FROM messages m
                        WHERE m.conversation_id = c.id
                        ORDER BY m.id DESC
                        LIMIT 1
                    ) AS last_message,
                    (
                        SELECT COUNT(*)
                        FROM messages m
                        WHERE m.conversation_id = c.id
                    ) AS message_count
                FROM conversations c
                WHERE c.username = ?
                ORDER BY c.updated_at DESC
                """,
                (username,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_messages(self, username: str, conversation_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT m.id, m.role, m.content, m.request_type, m.created_at
                FROM messages m
                INNER JOIN conversations c ON c.id = m.conversation_id
                WHERE m.conversation_id = ? AND c.username = ?
                ORDER BY m.id ASC
                """,
                (conversation_id, username),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_conversation(self, username: str, conversation_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ? AND username = ?
                """,
                (conversation_id, username),
            )
            cursor = conn.execute(
                """
                DELETE FROM conversations
                WHERE id = ? AND username = ?
                """,
                (conversation_id, username),
            )
            return cursor.rowcount > 0

    def update_conversation_title(self, username: str, conversation_id: str, title: str) -> bool:
        now = self._now()
        clean_title = (title or "新对话").strip()[:80] or "新对话"
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ? AND username = ?
                """,
                (clean_title, now, conversation_id, username),
            )
            return cursor.rowcount > 0

    def save_lesson_submission(
        self,
        username: str,
        lesson_id: str,
        code: str,
        passed: bool,
        score: float,
        feedback: str,
        structured_feedback: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        submitted_at = self._now()
        structured_json = (
            json.dumps(structured_feedback, ensure_ascii=False)
            if structured_feedback is not None
            else None
        )
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO lesson_submissions
                (username, lesson_id, code, passed, score, feedback, structured_feedback, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    lesson_id,
                    code,
                    int(passed),
                    score,
                    feedback,
                    structured_json,
                    submitted_at,
                ),
            )
        return {
            "id": cursor.lastrowid,
            "username": username,
            "lesson_id": lesson_id,
            "passed": passed,
            "score": score,
            "feedback": feedback,
            "structured_feedback": structured_feedback,
            "submitted_at": submitted_at,
        }

    def get_latest_lesson_submission(self, username: str, lesson_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, lesson_id, code, passed, score, feedback, structured_feedback, submitted_at
                FROM lesson_submissions
                WHERE username = ? AND lesson_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (username, lesson_id),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["passed"] = bool(data["passed"])
        if data.get("structured_feedback"):
            try:
                data["structured_feedback"] = json.loads(data["structured_feedback"])
            except json.JSONDecodeError:
                data["structured_feedback"] = None
        return data

    def get_lesson_progress_summary(self, username: str) -> Dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, lesson_id, passed, score, submitted_at
                FROM lesson_submissions
                WHERE username = ?
                ORDER BY id ASC
                """,
                (username,),
            ).fetchall()

        per_lesson: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            data = dict(row)
            lesson_id = str(data["lesson_id"])
            item = per_lesson.setdefault(
                lesson_id,
                {
                    "lesson_id": lesson_id,
                    "attempts": 0,
                    "best_score": 0.0,
                    "latest_score": 0.0,
                    "passed": False,
                    "last_submitted_at": None,
                },
            )
            item["attempts"] += 1
            score = float(data["score"])
            item["best_score"] = max(float(item["best_score"]), score)
            item["latest_score"] = score
            item["passed"] = bool(data["passed"]) or bool(item["passed"])
            item["last_submitted_at"] = data["submitted_at"]

        return {
            "total_attempts": len(rows),
            "completed_lessons": sum(1 for item in per_lesson.values() if item["passed"]),
            "average_best_score": (
                round(
                    sum(float(item["best_score"]) for item in per_lesson.values())
                    / len(per_lesson),
                    1,
                )
                if per_lesson
                else 0.0
            ),
            "lessons": list(per_lesson.values()),
        }

    def list_recent_lesson_submissions(self, username: str, limit: int = 8) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT lesson_id, passed, score, submitted_at
                FROM lesson_submissions
                WHERE username = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (username, limit),
            ).fetchall()
        return [
            {
                **dict(row),
                "passed": bool(row["passed"]),
            }
            for row in rows
        ]

    def save_question_submission(
        self,
        username: str,
        question_id: str,
        code: str,
        passed: bool,
        score: float,
        feedback: str,
        test_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        submitted_at = self._now()
        test_result_json = (
            json.dumps(test_result, ensure_ascii=False)
            if test_result is not None
            else None
        )
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO question_submissions
                (username, question_id, code, passed, score, feedback, test_result, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    question_id,
                    code,
                    int(passed),
                    score,
                    feedback,
                    test_result_json,
                    submitted_at,
                ),
            )
        return {
            "id": cursor.lastrowid,
            "username": username,
            "question_id": question_id,
            "passed": passed,
            "score": score,
            "feedback": feedback,
            "test_result": test_result,
            "submitted_at": submitted_at,
        }

    def get_latest_question_submission(self, username: str, question_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, username, question_id, code, passed, score, feedback, test_result, submitted_at
                FROM question_submissions
                WHERE username = ? AND question_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (username, question_id),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["passed"] = bool(data["passed"])
        if data.get("test_result"):
            try:
                data["test_result"] = json.loads(data["test_result"])
            except json.JSONDecodeError:
                data["test_result"] = None
        return data

    def get_question_progress_summary(self, username: str) -> Dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, question_id, passed, score, submitted_at
                FROM question_submissions
                WHERE username = ?
                ORDER BY id ASC
                """,
                (username,),
            ).fetchall()

        per_question: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            data = dict(row)
            question_id = str(data["question_id"])
            item = per_question.setdefault(
                question_id,
                {
                    "question_id": question_id,
                    "attempts": 0,
                    "best_score": 0.0,
                    "latest_score": 0.0,
                    "passed": False,
                    "last_submitted_at": None,
                },
            )
            item["attempts"] += 1
            score = float(data["score"])
            item["best_score"] = max(float(item["best_score"]), score)
            item["latest_score"] = score
            item["passed"] = bool(data["passed"]) or bool(item["passed"])
            item["last_submitted_at"] = data["submitted_at"]

        return {
            "total_attempts": len(rows),
            "completed_questions": sum(1 for item in per_question.values() if item["passed"]),
            "average_best_score": (
                round(
                    sum(float(item["best_score"]) for item in per_question.values())
                    / len(per_question),
                    1,
                )
                if per_question
                else 0.0
            ),
            "questions": list(per_question.values()),
        }

    def record_learning_event(
        self,
        username: str,
        event_type: str,
        target_type: str,
        target_id: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        clean_event_type = event_type.strip()[:80]
        clean_target_type = target_type.strip()[:80]
        clean_target_id = target_id.strip()[:160] if target_id else None
        if not clean_event_type or not clean_target_type:
            raise ValueError("事件类型和目标类型不能为空")

        clean_duration = None
        if duration_seconds is not None:
            clean_duration = max(0.0, min(float(duration_seconds), 24 * 60 * 60))

        metadata_json = (
            json.dumps(metadata or {}, ensure_ascii=False)[:4000]
            if metadata is not None
            else None
        )
        created_at = self._now()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO learning_events
                (username, event_type, target_type, target_id, duration_seconds, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    clean_event_type,
                    clean_target_type,
                    clean_target_id,
                    clean_duration,
                    metadata_json,
                    created_at,
                ),
            )
        return {
            "id": cursor.lastrowid,
            "username": username,
            "event_type": clean_event_type,
            "target_type": clean_target_type,
            "target_id": clean_target_id,
            "duration_seconds": clean_duration,
            "metadata": metadata or {},
            "created_at": created_at,
        }

    def get_learning_behavior_summary(self, username: str, limit: int = 12) -> Dict[str, Any]:
        user = self.get_user(username) or {}
        with self._connect() as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_events,
                    COALESCE(SUM(duration_seconds), 0) AS total_duration_seconds,
                    COALESCE(AVG(NULLIF(duration_seconds, 0)), 0) AS average_duration_seconds
                FROM learning_events
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
            target_rows = conn.execute(
                """
                SELECT
                    target_type,
                    target_id,
                    COUNT(*) AS event_count,
                    COALESCE(SUM(duration_seconds), 0) AS duration_seconds,
                    MAX(created_at) AS last_seen_at
                FROM learning_events
                WHERE username = ?
                GROUP BY target_type, target_id
                ORDER BY duration_seconds DESC, event_count DESC
                LIMIT ?
                """,
                (username, limit),
            ).fetchall()
            signal_event_rows = conn.execute(
                """
                SELECT event_type, target_type, target_id, duration_seconds, metadata, created_at
                FROM learning_events
                WHERE username = ?
                ORDER BY id ASC
                """,
                (username,),
            ).fetchall()
            question_submission_rows = conn.execute(
                """
                SELECT question_id, passed, score, submitted_at
                FROM question_submissions
                WHERE username = ?
                ORDER BY id ASC
                """,
                (username,),
            ).fetchall()
            lesson_submission_rows = conn.execute(
                """
                SELECT lesson_id, passed, score, submitted_at
                FROM lesson_submissions
                WHERE username = ?
                ORDER BY id ASC
                """,
                (username,),
            ).fetchall()
            recent_rows = conn.execute(
                """
                SELECT event_type, target_type, target_id, duration_seconds, metadata, created_at
                FROM learning_events
                WHERE username = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (username, limit),
            ).fetchall()

        recent_events = []
        for row in recent_rows:
            data = dict(row)
            if data.get("metadata"):
                try:
                    data["metadata"] = json.loads(data["metadata"])
                except json.JSONDecodeError:
                    data["metadata"] = {}
            else:
                data["metadata"] = {}
            recent_events.append(data)

        total_duration = float(totals["total_duration_seconds"] if totals else 0.0)
        stuck_targets = [
            dict(row)
            for row in target_rows
            if float(row["duration_seconds"] or 0.0) >= 180 and str(row["target_type"]) in {"question", "lesson"}
        ]
        learning_signals = self._build_learning_signals(
            [self._decode_event_row(row) for row in signal_event_rows],
            [dict(row) for row in question_submission_rows],
            [dict(row) for row in lesson_submission_rows],
        )
        return {
            "preferences": {
                "learning_goal": user.get("learning_goal") or "",
                "learning_style": user.get("learning_style") or "",
                "preferred_pace": user.get("preferred_pace") or "",
            },
            "total_events": int(totals["total_events"] if totals else 0),
            "total_duration_seconds": round(total_duration, 1),
            "average_duration_seconds": round(float(totals["average_duration_seconds"] if totals else 0.0), 1),
            "target_focus": [dict(row) for row in target_rows],
            "stuck_targets": stuck_targets[:5],
            "recent_events": recent_events,
            "learning_signals": learning_signals,
        }

    @staticmethod
    def _decode_event_row(row: Any) -> Dict[str, Any]:
        data = dict(row)
        if data.get("metadata"):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except (TypeError, json.JSONDecodeError):
                data["metadata"] = {}
        else:
            data["metadata"] = {}
        return data

    @staticmethod
    def _build_first_pass_stats(rows: List[Dict[str, Any]], target_key: str) -> Dict[str, Any]:
        if not rows:
            return {
                "target_count": 0,
                "first_pass_count": 0,
                "first_pass_rate": 0.0,
                "average_attempts": 0.0,
            }
        per_target: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            target_id = str(row.get(target_key) or "")
            if not target_id:
                continue
            item = per_target.setdefault(target_id, {"attempts": 0, "first_pass": None})
            item["attempts"] += 1
            if item["first_pass"] is None:
                item["first_pass"] = bool(row.get("passed"))
        target_count = len(per_target)
        first_pass_count = sum(1 for item in per_target.values() if item["first_pass"])
        return {
            "target_count": target_count,
            "first_pass_count": first_pass_count,
            "first_pass_rate": round(first_pass_count / target_count, 3) if target_count else 0.0,
            "average_attempts": round(
                sum(int(item["attempts"]) for item in per_target.values()) / target_count,
                2,
            )
            if target_count
            else 0.0,
        }

    @staticmethod
    def _new_topic_metric(topic: str) -> Dict[str, Any]:
        return {
            "topic": topic,
            "submissions": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "first_attempt_targets": 0,
            "first_passed_targets": 0,
            "first_pass_rate": 0.0,
            "answer_views": 0,
            "hint_views": 0,
            "dwell_seconds": 0.0,
            "average_dwell_seconds": 0.0,
            "dwell_event_count": 0,
            "consecutive_failures": 0,
        }

    def _build_learning_signals(
        self,
        events: List[Dict[str, Any]],
        question_submissions: List[Dict[str, Any]],
        lesson_submissions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        topic_metrics: Dict[str, Dict[str, Any]] = {}
        target_first_attempt: Set[str] = set()
        current_failure_streak: Dict[str, int] = {}
        answer_view_count = 0
        hint_view_count = 0
        open_count = 0
        long_dwell_targets: Dict[str, Dict[str, Any]] = {}

        for event in events:
            event_type = str(event.get("event_type") or "")
            target_type = str(event.get("target_type") or "")
            target_id = str(event.get("target_id") or "")
            metadata = event.get("metadata") or {}
            topic = str(metadata.get("topic") or "general")
            metric = topic_metrics.setdefault(topic, self._new_topic_metric(topic))

            if event_type.endswith("_open"):
                open_count += 1

            if event_type in {"question_answer_view", "lesson_answer_view", "answer_view"}:
                answer_view_count += 1
                metric["answer_views"] += 1

            if event_type in {"question_hint_view", "lesson_hint_view", "hint_view", "question_hints_visible"}:
                hint_view_count += 1
                metric["hint_views"] += 1

            duration = float(event.get("duration_seconds") or 0.0)
            if duration > 0 and target_type in {"question", "lesson"}:
                metric["dwell_seconds"] += duration
                metric["dwell_event_count"] += 1
                if duration >= 180 and target_id:
                    long_dwell_targets[target_id] = {
                        "target_type": target_type,
                        "target_id": target_id,
                        "topic": topic,
                        "duration_seconds": round(
                            float(long_dwell_targets.get(target_id, {}).get("duration_seconds", 0.0)) + duration,
                            1,
                        ),
                    }

            if event_type not in {"question_submit", "lesson_submit"}:
                continue

            passed = bool(metadata.get("passed"))
            metric["submissions"] += 1
            if passed:
                metric["passed"] += 1
                current_failure_streak[topic] = 0
            else:
                metric["failed"] += 1
                current_failure_streak[topic] = current_failure_streak.get(topic, 0) + 1

            target_key = f"{target_type}:{target_id}" if target_id else f"{event_type}:{len(target_first_attempt)}"
            if target_key not in target_first_attempt:
                target_first_attempt.add(target_key)
                metric["first_attempt_targets"] += 1
                if passed:
                    metric["first_passed_targets"] += 1

        for topic, metric in topic_metrics.items():
            submissions = int(metric["submissions"])
            metric["pass_rate"] = round(int(metric["passed"]) / submissions, 3) if submissions else 0.0
            first_attempts = int(metric["first_attempt_targets"])
            metric["first_pass_rate"] = (
                round(int(metric["first_passed_targets"]) / first_attempts, 3) if first_attempts else 0.0
            )
            dwell_events = int(metric["dwell_event_count"])
            metric["average_dwell_seconds"] = (
                round(float(metric["dwell_seconds"]) / dwell_events, 1) if dwell_events else 0.0
            )
            metric["dwell_seconds"] = round(float(metric["dwell_seconds"]), 1)
            metric["consecutive_failures"] = int(current_failure_streak.get(topic, 0))

        question_first_pass = self._build_first_pass_stats(question_submissions, "question_id")
        lesson_first_pass = self._build_first_pass_stats(lesson_submissions, "lesson_id")
        target_count = int(question_first_pass["target_count"]) + int(lesson_first_pass["target_count"])
        first_pass_count = int(question_first_pass["first_pass_count"]) + int(lesson_first_pass["first_pass_count"])
        total_submission_count = len(question_submissions) + len(lesson_submissions)
        interaction_base = max(open_count, total_submission_count, 1)
        consecutive_failures_by_topic = {
            topic: int(metric["consecutive_failures"])
            for topic, metric in topic_metrics.items()
            if int(metric.get("consecutive_failures", 0)) > 0
        }

        return {
            "total_submission_count": total_submission_count,
            "question_submission_count": len(question_submissions),
            "lesson_submission_count": len(lesson_submissions),
            "first_pass_rate": round(first_pass_count / target_count, 3) if target_count else 0.0,
            "question_first_pass_rate": question_first_pass["first_pass_rate"],
            "lesson_first_pass_rate": lesson_first_pass["first_pass_rate"],
            "average_attempts_per_question": question_first_pass["average_attempts"],
            "average_attempts_per_lesson": lesson_first_pass["average_attempts"],
            "answer_view_count": answer_view_count,
            "hint_view_count": hint_view_count,
            "answer_view_rate": round(answer_view_count / interaction_base, 3),
            "hint_view_rate": round(hint_view_count / interaction_base, 3),
            "frequent_answer_view": answer_view_count >= 3 and answer_view_count / interaction_base >= 0.25,
            "frequent_hint_view": hint_view_count >= 3 and hint_view_count / interaction_base >= 0.35,
            "consecutive_failures_by_topic": consecutive_failures_by_topic,
            "long_dwell_targets": sorted(
                long_dwell_targets.values(),
                key=lambda item: float(item.get("duration_seconds", 0.0)),
                reverse=True,
            )[:5],
            "topic_metrics": topic_metrics,
        }

    def _get_session(self, column: str, hashed_token: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT username, access_expires_at, refresh_expires_at, created_at, revoked_at
                FROM sessions
                WHERE {column} = ?
                """,
                (hashed_token,),
            ).fetchone()
        if row is None:
            return None

        session = dict(row)
        revoked_at = session.get("revoked_at")
        if revoked_at:
            return None

        now = datetime.now(timezone.utc)
        access_expires_at = datetime.fromisoformat(str(session["access_expires_at"]))
        refresh_expires_at = datetime.fromisoformat(str(session["refresh_expires_at"]))
        if access_expires_at <= now and column == "access_token_hash":
            return None
        if refresh_expires_at <= now and column == "refresh_token_hash":
            return None
        return session

    def _revoke_session(self, column: str, hashed_token: str) -> None:
        with self._connect() as conn:
            conn.execute(
                f"""
                UPDATE sessions
                SET revoked_at = COALESCE(revoked_at, ?)
                WHERE {column} = ?
                """,
                (self._now(), hashed_token),
            )

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120000,
        )
        return digest.hex()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
