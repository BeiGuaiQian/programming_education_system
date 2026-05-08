"""Question bank data model backed by SQLite."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from programming_education_system.config.llm_config import Config
from programming_education_system.models.question_schema import normalize_question

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuestionType(Enum):
    CODING = "coding"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_ANSWER = "text_answer"
    DEBUGGING = "debugging"
    ALGORITHM = "algorithm"


class Question:
    """In-memory representation of one question."""

    def __init__(
        self,
        id: int,
        topic: str,
        content: str,
        difficulty: DifficultyLevel,
        question_type: QuestionType,
        answer: str = "",
        hints: Optional[List[str]] = None,
        examples: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[str]] = None,
        created_time: Optional[str] = None,
        updated_time: Optional[str] = None,
        usage_count: int = 0,
        success_rate: float = 0.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.topic = topic
        self.content = content
        self.difficulty = difficulty
        self.question_type = question_type
        self.answer = answer
        self.hints = hints or []
        self.examples = examples or []
        self.tags = tags or []
        self.created_time = created_time or datetime.now().isoformat()
        self.updated_time = updated_time or datetime.now().isoformat()
        self.usage_count = usage_count
        self.success_rate = success_rate
        self.source = source
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "topic": self.topic,
            "content": self.content,
            "difficulty": self.difficulty.value,
            "question_type": self.question_type.value,
            "answer": self.answer,
            "hints": self.hints,
            "examples": self.examples,
            "tags": self.tags,
            "created_time": self.created_time,
            "updated_time": self.updated_time,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "source": self.source,
            "metadata": self.metadata,
        }
        return normalize_question(
            data,
            source=self.source,
            question_id=f"bank_{self.id}",
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        return cls(
            id=data["id"],
            topic=data["topic"],
            content=data["content"],
            difficulty=DifficultyLevel(data["difficulty"]),
            question_type=QuestionType(data["question_type"]),
            answer=data.get("answer", ""),
            hints=data.get("hints", []),
            examples=data.get("examples", []),
            tags=data.get("tags", []),
            created_time=data.get("created_time"),
            updated_time=data.get("updated_time"),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0),
            source=data.get("source", "system"),
            metadata=data.get("metadata", {}),
        )


class QuestionBank:
    """SQLite-backed storage and query interface for questions."""

    def __init__(self, db_path: str = ""):
        self.db_path = str(self._resolve_db_path(db_path or Config.QUESTION_BANK_DB))
        self._init_database()

    def _resolve_db_path(self, db_path: str) -> Path:
        path = Path(db_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _init_database(self):
        logger.info("Using question bank database at %s", self.db_path)
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    difficulty TEXT NOT NULL CHECK(difficulty IN ('beginner', 'intermediate', 'advanced')),
                    question_type TEXT NOT NULL CHECK(question_type IN ('coding', 'multiple_choice', 'text_answer', 'debugging', 'algorithm')),
                    answer TEXT DEFAULT '',
                    hints TEXT DEFAULT '[]',
                    examples TEXT DEFAULT '[]',
                    tags TEXT DEFAULT '[]',
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    source TEXT DEFAULT 'system',
                    metadata TEXT DEFAULT '{}',
                    content_hash TEXT UNIQUE
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_usage ON questions(usage_count)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_success_rate ON questions(success_rate)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_hash ON questions(content_hash)")

    @staticmethod
    def _generate_content_hash(content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def add_question(
        self,
        topic: str,
        content: str,
        difficulty: DifficultyLevel,
        question_type: QuestionType,
        answer: str = "",
        hints: Optional[List[str]] = None,
        examples: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[str]] = None,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        try:
            content_hash = self._generate_content_hash(content)
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO questions
                    (topic, content, difficulty, question_type, answer, hints, examples, tags, source, metadata, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        topic,
                        content,
                        difficulty.value,
                        question_type.value,
                        answer,
                        json.dumps(hints or [], ensure_ascii=False),
                        json.dumps(examples or [], ensure_ascii=False),
                        json.dumps(tags or [], ensure_ascii=False),
                        source,
                        json.dumps(metadata or {}, ensure_ascii=False),
                        content_hash,
                    ),
                )
                if cursor.lastrowid:
                    return cursor.lastrowid
                row = cursor.execute(
                    "SELECT id FROM questions WHERE content_hash = ?",
                    (content_hash,),
                ).fetchone()
                return row[0] if row else None
        except Exception as exc:
            logger.error("Failed to add question: %s", exc)
            return None

    def get_question(self, question_id: int) -> Optional[Question]:
        try:
            with self._connect() as conn:
                row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
            return self._row_to_question(row) if row else None
        except Exception as exc:
            logger.error("Failed to get question: %s", exc)
            return None

    def get_questions_by_filters(
        self,
        topic: str = None,
        difficulty: DifficultyLevel = None,
        question_type: QuestionType = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Question]:
        try:
            query = "SELECT * FROM questions WHERE 1=1"
            params: List[Any] = []
            if topic:
                query += " AND topic = ?"
                params.append(topic)
            if difficulty:
                query += " AND difficulty = ?"
                params.append(difficulty.value)
            if question_type:
                query += " AND question_type = ?"
                params.append(question_type.value)
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                query += " AND (" + " OR ".join(tag_conditions) + ")"

            query += " ORDER BY usage_count DESC, success_rate DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            with self._connect() as conn:
                rows = conn.execute(query, params).fetchall()
            return [self._row_to_question(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to filter questions: %s", exc)
            return []

    def search_questions(self, keyword: str, limit: int = 10) -> List[Question]:
        try:
            search_term = f"%{keyword}%"
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM questions
                    WHERE content LIKE ? OR topic LIKE ? OR tags LIKE ?
                    ORDER BY usage_count DESC
                    LIMIT ?
                    """,
                    (search_term, search_term, search_term, limit),
                ).fetchall()
            return [self._row_to_question(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to search questions: %s", exc)
            return []

    def update_question_usage(self, question_id: int, success: bool = True):
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT usage_count, success_rate FROM questions WHERE id = ?",
                    (question_id,),
                ).fetchone()
                if not row:
                    return
                usage_count, current_success_rate = row
                new_usage_count = usage_count + 1
                success_count = current_success_rate * usage_count + (1 if success else 0)
                new_success_rate = success_count / new_usage_count
                conn.execute(
                    """
                    UPDATE questions
                    SET usage_count = ?, success_rate = ?, updated_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_usage_count, new_success_rate, question_id),
                )
        except Exception as exc:
            logger.error("Failed to update question usage: %s", exc)

    def get_popular_questions(self, topic: str = None, limit: int = 10) -> List[Question]:
        try:
            if topic:
                query = "SELECT * FROM questions WHERE topic = ? ORDER BY usage_count DESC, success_rate DESC LIMIT ?"
                params = (topic, limit)
            else:
                query = "SELECT * FROM questions ORDER BY usage_count DESC, success_rate DESC LIMIT ?"
                params = (limit,)
            with self._connect() as conn:
                rows = conn.execute(query, params).fetchall()
            return [self._row_to_question(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to get popular questions: %s", exc)
            return []

    def get_questions_by_success_rate(
        self, min_rate: float = 0.0, max_rate: float = 1.0, topic: str = None, limit: int = 10
    ) -> List[Question]:
        try:
            if topic:
                query = (
                    "SELECT * FROM questions WHERE topic = ? AND success_rate BETWEEN ? AND ? "
                    "ORDER BY success_rate DESC LIMIT ?"
                )
                params = (topic, min_rate, max_rate, limit)
            else:
                query = (
                    "SELECT * FROM questions WHERE success_rate BETWEEN ? AND ? "
                    "ORDER BY success_rate DESC LIMIT ?"
                )
                params = (min_rate, max_rate, limit)
            with self._connect() as conn:
                rows = conn.execute(query, params).fetchall()
            return [self._row_to_question(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to get questions by success rate: %s", exc)
            return []

    def delete_question(self, question_id: int) -> bool:
        try:
            with self._connect() as conn:
                cursor = conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            return cursor.rowcount > 0
        except Exception as exc:
            logger.error("Failed to delete question: %s", exc)
            return False

    def get_statistics(self) -> Dict[str, Any]:
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                stats: Dict[str, Any] = {}
                stats["total_questions"] = cursor.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
                stats["questions_by_topic"] = dict(
                    cursor.execute("SELECT topic, COUNT(*) FROM questions GROUP BY topic").fetchall()
                )
                stats["questions_by_difficulty"] = dict(
                    cursor.execute("SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty").fetchall()
                )
                stats["questions_by_type"] = dict(
                    cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type").fetchall()
                )
                avg_usage, avg_success = cursor.execute(
                    "SELECT AVG(usage_count), AVG(success_rate) FROM questions"
                ).fetchone()
                stats["average_usage_count"] = round(avg_usage or 0, 2)
                stats["average_success_rate"] = round(avg_success or 0, 2)
            return stats
        except Exception as exc:
            logger.error("Failed to get statistics: %s", exc)
            return {}

    def batch_import_questions(self, questions_data: List[Dict[str, Any]]) -> Dict[str, int]:
        imported = 0
        skipped = 0
        errors = 0
        for question_data in questions_data:
            try:
                question_id = self.add_question(
                    topic=question_data["topic"],
                    content=question_data["content"],
                    difficulty=DifficultyLevel(question_data["difficulty"]),
                    question_type=QuestionType(question_data.get("question_type", "coding")),
                    answer=question_data.get("answer", ""),
                    hints=question_data.get("hints", []),
                    examples=question_data.get("examples", []),
                    tags=question_data.get("tags", []),
                    source=question_data.get("source", "import"),
                    metadata=question_data.get("metadata", {}),
                )
                if question_id:
                    imported += 1
                else:
                    skipped += 1
            except Exception as exc:
                logger.error("Failed to import one question: %s", exc)
                errors += 1
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total_processed": len(questions_data),
        }

    def export_questions(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            filters = filters or {}
            difficulty = filters.get("difficulty")
            if difficulty and not isinstance(difficulty, DifficultyLevel):
                difficulty = DifficultyLevel(str(difficulty))

            questions = self.get_questions_by_filters(
                topic=filters.get("topic"),
                difficulty=difficulty,
                question_type=filters.get("question_type"),
                tags=filters.get("tags"),
                limit=filters.get("limit", 1000),
            )
            return [question.to_dict() for question in questions]
        except Exception as exc:
            logger.error("Failed to export questions: %s", exc)
            return []

    def _row_to_question(self, row) -> Question:
        return Question(
            id=row[0],
            topic=row[1],
            content=row[2],
            difficulty=DifficultyLevel(row[3]),
            question_type=QuestionType(row[4]),
            answer=row[5],
            hints=json.loads(row[6]) if row[6] else [],
            examples=json.loads(row[7]) if row[7] else [],
            tags=json.loads(row[8]) if row[8] else [],
            created_time=row[9],
            updated_time=row[10],
            usage_count=row[11],
            success_rate=row[12],
            source=row[13],
            metadata=json.loads(row[14]) if row[14] else {},
        )
