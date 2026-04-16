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
from typing import Any, Dict, List, Optional


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


class AppStore:
    """Persistent application store for auth and chat data."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(Path(db_path))
        self._local = threading.local()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is not None:
            return connection

        connection = sqlite3.connect(
            self.db_path,
            timeout=5,
            check_same_thread=False,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.execute("PRAGMA cache_size=-20000")
        connection.execute("PRAGMA mmap_size=268435456")
        self._local.connection = connection
        return connection

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
                SELECT username, nickname, avatar_url, bio, created_at, updated_at
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
