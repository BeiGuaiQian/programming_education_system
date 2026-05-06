"""SQLite-backed vector store for local RAG retrieval."""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Protocol

from programming_education_system.config.llm_config import Config


class VectorChunk(Protocol):
    chunk_id: str
    topic: str
    title: str
    text: str
    source: str
    url: str
    examples: List[str]
    metadata: Dict[str, Any]

    def searchable_text(self) -> str:
        ...


class SQLiteVectorStore:
    """Persist chunk embeddings and run cosine search.

    This is intentionally simple: SQLite stores JSON vectors, which is enough
    for a teaching system and keeps deployment lightweight. The public class can
    later be replaced by FAISS, Chroma, Milvus, or pgvector without changing
    QAAgent.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(self._resolve_db_path(db_path or Config.RAG_VECTOR_DB))
        self._init_database()

    def _resolve_db_path(self, db_path: str) -> Path:
        path = Path(db_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _init_database(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_vectors (
                    chunk_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    source TEXT DEFAULT '',
                    url TEXT DEFAULT '',
                    examples_json TEXT DEFAULT '[]',
                    metadata_json TEXT DEFAULT '{}',
                    content_hash TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rag_vectors_topic ON rag_vectors(topic)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rag_vectors_hash ON rag_vectors(content_hash)")

    def missing_chunks(self, chunks: Iterable[VectorChunk]) -> List[VectorChunk]:
        """Return chunks whose current content is not indexed yet."""
        chunk_list = list(chunks)
        if not chunk_list:
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT chunk_id, content_hash FROM rag_vectors").fetchall()
        indexed = dict(rows)
        return [
            chunk
            for chunk in chunk_list
            if indexed.get(chunk.chunk_id) != self.content_hash(chunk)
        ]

    def upsert_vectors(self, chunks: List[VectorChunk], vectors: List[List[float]]) -> None:
        if not chunks or not vectors:
            return
        rows = []
        for chunk, vector in zip(chunks, vectors):
            if not vector:
                continue
            rows.append(
                (
                    chunk.chunk_id,
                    chunk.topic,
                    chunk.title,
                    chunk.text,
                    chunk.source,
                    chunk.url,
                    json.dumps(chunk.examples, ensure_ascii=False),
                    json.dumps(chunk.metadata, ensure_ascii=False),
                    self.content_hash(chunk),
                    json.dumps(vector),
                )
            )
        if not rows:
            return
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO rag_vectors(
                    chunk_id, topic, title, text, source, url, examples_json,
                    metadata_json, content_hash, vector_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    topic=excluded.topic,
                    title=excluded.title,
                    text=excluded.text,
                    source=excluded.source,
                    url=excluded.url,
                    examples_json=excluded.examples_json,
                    metadata_json=excluded.metadata_json,
                    content_hash=excluded.content_hash,
                    vector_json=excluded.vector_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                rows,
            )

    def search(
        self,
        query_vector: List[float],
        topic: str | None = None,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        if not query_vector:
            return []
        sql = "SELECT chunk_id, topic, title, text, source, url, examples_json, metadata_json, vector_json FROM rag_vectors"
        params: List[Any] = []
        if topic:
            sql += " WHERE topic = ?"
            params.append(topic)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        scored = []
        for row in rows:
            vector = json.loads(row[8])
            score = self.cosine_similarity(query_vector, vector)
            if score <= 0:
                continue
            scored.append(
                {
                    "chunk_id": row[0],
                    "topic": row[1],
                    "title": row[2],
                    "question": row[2],
                    "answer": row[3],
                    "text": row[3],
                    "source": row[4],
                    "url": row[5],
                    "examples": json.loads(row[6] or "[]"),
                    "metadata": json.loads(row[7] or "{}"),
                    "vector_score": round(score, 4),
                }
            )
        scored.sort(key=lambda item: item["vector_score"], reverse=True)
        return scored[:limit]

    @staticmethod
    def content_hash(chunk: VectorChunk) -> str:
        import hashlib

        raw = f"{chunk.topic}|{chunk.title}|{chunk.text}|{chunk.examples}|{chunk.metadata}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def cosine_similarity(left: List[float], right: List[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)
