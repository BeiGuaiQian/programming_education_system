"""Local hybrid RAG knowledge base used by the QA agent.

The retrieval stack has two layers:
1. Lexical retrieval, which is dependency-free and always available.
2. Optional embedding retrieval, persisted in SQLite and enabled by config.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from programming_education_system.config.llm_config import Config
from programming_education_system.models.rag_vector_store import SQLiteVectorStore
from programming_education_system.services.embedding_service import embedding_client

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeChunk:
    """One retrievable piece of teaching material."""

    chunk_id: str
    topic: str
    title: str
    text: str
    source: str = "knowledge_base"
    url: str = ""
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def searchable_text(self) -> str:
        return " ".join([self.title, self.text, " ".join(self.examples)])


class KnowledgeBase:
    """Hybrid lexical/vector retrieval index for programming education content."""

    def __init__(self) -> None:
        self.chunks: List[KnowledgeChunk] = []
        self._token_cache: Dict[str, List[str]] = {}
        self.vector_store = SQLiteVectorStore()
        self.vector_enabled = Config.RAG_USE_VECTOR and embedding_client.initialized
        self._add_seed_chunks()
        self._ingest_lesson_catalog()
        self._build_vector_index_if_enabled()

    def search(self, query: str, topic: Optional[str] = None, limit: int = 4) -> List[Dict[str, Any]]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        expanded_limit = max(limit * 2, 8)
        lexical = self._lexical_search(normalized_query, topic=topic, limit=expanded_limit)
        if not self.vector_enabled:
            return lexical[:limit]

        query_vector = embedding_client.embed_query(query)
        vector = self.vector_store.search(query_vector, topic=topic, limit=expanded_limit)
        return self._merge_hybrid_results(lexical, vector)[:limit]

    def add_knowledge(
        self,
        topic: str,
        question: str,
        answer: str,
        examples: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        source = (metadata or {}).get("source", "runtime")
        self._add_chunk(
            topic=topic,
            title=question,
            text=answer,
            source=source,
            examples=examples or [],
            metadata=metadata or {},
        )
        self._build_vector_index_if_enabled()

    def get_topics(self) -> List[str]:
        return sorted({chunk.topic for chunk in self.chunks})

    def build_context(self, query: str, topic: Optional[str] = None, limit: int = 4) -> Dict[str, Any]:
        hits = self.search(query, topic=topic, limit=limit)
        snippets = []
        for index, item in enumerate(hits, start=1):
            snippets.append(
                {
                    "rank": index,
                    "chunk_id": item["chunk_id"],
                    "topic": item["topic"],
                    "title": item["title"],
                    "text": item["text"],
                    "examples": item.get("examples", [])[:2],
                    "source": item.get("source", "knowledge_base"),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),
                    "lexical_score": item.get("lexical_score", 0),
                    "vector_score": item.get("vector_score", 0),
                    "retrieval_mode": item.get("retrieval_mode", "lexical"),
                }
            )
        return {
            "query": query,
            "topic": topic,
            "retriever": "hybrid_vector_lexical" if self.vector_enabled else "lexical",
            "hits": snippets,
        }

    def format_context_for_prompt(self, retrieval_context: Dict[str, Any]) -> str:
        hits = retrieval_context.get("hits", [])
        if not hits:
            return "未检索到课程资料。"

        blocks = []
        for hit in hits:
            examples = "\n".join(f"示例: {example}" for example in hit.get("examples", []))
            source = hit.get("source", "knowledge_base")
            url = f" URL: {hit['url']}" if hit.get("url") else ""
            blocks.append(
                f"[{hit['rank']}] {hit['title']} ({source}{url})\n"
                f"主题: {hit['topic']}\n"
                f"检索方式: {hit.get('retrieval_mode', 'lexical')}\n"
                f"内容: {hit['text']}\n"
                f"{examples}".strip()
            )
        return "\n\n".join(blocks)

    def format_context_for_prompt(
        self,
        retrieval_context: Dict[str, Any],
        max_hits: int = 2,
        max_text_chars: int = 420,
        max_example_chars: int = 220,
    ) -> str:
        hits = retrieval_context.get("hits", [])
        if not hits:
            return "未检索到课程资料。"

        blocks = []
        for hit in hits[:max_hits]:
            examples = "\n".join(
                f"示例: {self._truncate_for_prompt(str(example), max_example_chars)}"
                for example in hit.get("examples", [])[:1]
            )
            source = hit.get("source", "knowledge_base")
            url = f" URL: {hit['url']}" if hit.get("url") else ""
            text = self._truncate_for_prompt(str(hit.get("text", "")), max_text_chars)
            blocks.append(
                f"[{hit['rank']}] {hit['title']} ({source}{url})\n"
                f"主题: {hit['topic']}\n"
                f"检索方式: {hit.get('retrieval_mode', 'lexical')}\n"
                f"内容: {text}\n"
                f"{examples}".strip()
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _truncate_for_prompt(text: str, max_chars: int) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_chars:
            return compact
        return compact[: max(0, max_chars - 1)].rstrip() + "…"

    def _lexical_search(
        self, normalized_query: str, topic: Optional[str] = None, limit: int = 8
    ) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(normalized_query)
        candidates: List[Dict[str, Any]] = []
        for chunk in self.chunks:
            if topic and chunk.topic != topic:
                continue
            score = self._score_chunk(normalized_query, query_tokens, chunk)
            if score <= 0:
                continue
            result = self._chunk_to_result(chunk, score)
            result["lexical_score"] = result["score"]
            result["vector_score"] = 0.0
            result["retrieval_mode"] = "lexical"
            candidates.append(result)

        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates[:limit]

    def _merge_hybrid_results(
        self,
        lexical_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        max_lexical = max(
            (item.get("lexical_score", item.get("score", 0)) for item in lexical_results),
            default=1.0,
        )
        for item in lexical_results:
            chunk_id = item["chunk_id"]
            lexical_score = item.get("lexical_score", item.get("score", 0))
            normalized_lexical = lexical_score / max_lexical if max_lexical else 0.0
            merged[chunk_id] = {
                **item,
                "lexical_score": round(lexical_score, 4),
                "vector_score": 0.0,
                "score": round(Config.RAG_LEXICAL_WEIGHT * normalized_lexical, 4),
                "retrieval_mode": "hybrid_lexical",
            }
        for item in vector_results:
            chunk_id = item["chunk_id"]
            vector_score = item.get("vector_score", 0.0)
            if chunk_id in merged:
                merged[chunk_id]["vector_score"] = vector_score
                merged[chunk_id]["score"] = round(
                    merged[chunk_id]["score"] + Config.RAG_VECTOR_WEIGHT * vector_score,
                    4,
                )
                merged[chunk_id]["retrieval_mode"] = "hybrid"
            else:
                merged[chunk_id] = {
                    **item,
                    "lexical_score": 0.0,
                    "score": round(Config.RAG_VECTOR_WEIGHT * vector_score, 4),
                    "retrieval_mode": "hybrid_vector",
                }
        results = list(merged.values())
        results.sort(key=lambda item: item["score"], reverse=True)
        return results

    def _build_vector_index_if_enabled(self) -> None:
        if not self.vector_enabled:
            return
        missing = self.vector_store.missing_chunks(self.chunks)
        if not missing:
            return
        batch_size = 32
        indexed = 0
        for start in range(0, len(missing), batch_size):
            batch = missing[start : start + batch_size]
            vectors = embedding_client.embed_texts([chunk.searchable_text() for chunk in batch])
            if not vectors:
                logger.info("Vector indexing stopped because embeddings are unavailable.")
                self.vector_enabled = False
                return
            self.vector_store.upsert_vectors(batch, vectors)
            indexed += len(vectors)
        logger.info("RAG vector index updated with %s chunks.", indexed)

    def _add_seed_chunks(self) -> None:
        seeds = [
            {
                "topic": "python_basics",
                "title": "Python 中如何定义函数？",
                "text": "使用 def 关键字定义函数，例如 def function_name(params):。函数可以用 return 返回结果。",
                "examples": ["def greet(name):\n    return f'Hello, {name}!'"],
            },
            {
                "topic": "data_structures",
                "title": "Python 中列表和元组有什么区别？",
                "text": "列表是可变序列，使用 []；元组是不可变序列，使用 ()。如果数据需要修改，通常使用列表。",
                "examples": ["my_list = [1, 2, 3]", "my_tuple = (1, 2, 3)"],
            },
            {
                "topic": "data_structures",
                "title": "Python 列表 append 是什么？",
                "text": "append 是列表对象的方法，用来把一个元素追加到列表末尾。它会原地修改原列表，并返回 None。",
                "examples": ["items = [1, 2]\nitems.append(3)\nprint(items)  # [1, 2, 3]"],
            },
            {
                "topic": "algorithms",
                "title": "什么是二分查找？",
                "text": "二分查找是在有序序列中查找目标值的算法，时间复杂度通常是 O(log n)。关键是每次缩小一半搜索范围。",
                "examples": [
                    "def binary_search(arr, target):\n"
                    "    left, right = 0, len(arr) - 1\n"
                    "    while left <= right:\n"
                    "        mid = (left + right) // 2\n"
                    "        if arr[mid] == target:\n"
                    "            return mid\n"
                    "        if arr[mid] < target:\n"
                    "            left = mid + 1\n"
                    "        else:\n"
                    "            right = mid - 1\n"
                    "    return -1"
                ],
            },
        ]
        for item in seeds:
            self._add_chunk(
                topic=item["topic"],
                title=item["title"],
                text=item["text"],
                source="内置知识库",
                examples=item.get("examples", []),
                metadata={"kind": "seed"},
            )

    def _ingest_lesson_catalog(self) -> None:
        try:
            from server.lesson_catalog import LESSONS
        except Exception:
            return

        for lesson in LESSONS:
            lesson_id = str(lesson.get("id", "lesson"))
            topic = str(lesson.get("topic", "general_programming"))
            lesson_title = str(lesson.get("title", lesson_id))
            source = lesson.get("source") or {}
            source_title = str(source.get("title", "课程目录"))
            source_url = str(source.get("url", ""))

            summary = self._stringify(lesson.get("summary", ""))
            if summary:
                self._add_chunk(
                    topic=topic,
                    title=lesson_title,
                    text=summary,
                    source=source_title,
                    url=source_url,
                    metadata={"kind": "lesson_summary", "lesson_id": lesson_id},
                )

            for index, point in enumerate(lesson.get("knowledge_points", []) or [], start=1):
                title = self._stringify(point.get("title", f"{lesson_title} 知识点 {index}"))
                explanation = self._stringify(point.get("explanation", ""))
                example = self._stringify(point.get("example", ""))
                if not explanation and not example:
                    continue
                self._add_chunk(
                    topic=topic,
                    title=f"{lesson_title} - {title}",
                    text=explanation,
                    source=source_title,
                    url=source_url,
                    examples=[example] if example else [],
                    metadata={
                        "kind": "knowledge_point",
                        "lesson_id": lesson_id,
                        "point_index": index,
                        "difficulty": lesson.get("difficulty", ""),
                    },
                )

            exercise = lesson.get("exercise") or {}
            exercise_text = self._stringify(exercise.get("description", ""))
            if exercise_text:
                examples = [
                    self._stringify(example)
                    for example in exercise.get("examples", []) or exercise.get("test_cases", []) or []
                ]
                self._add_chunk(
                    topic=topic,
                    title=f"{lesson_title} - 练习: {exercise.get('title', '')}",
                    text=exercise_text,
                    source="课程练习",
                    url=source_url,
                    examples=[example for example in examples if example],
                    metadata={
                        "kind": "exercise",
                        "lesson_id": lesson_id,
                        "difficulty": lesson.get("difficulty", ""),
                    },
                )

    def _add_chunk(
        self,
        topic: str,
        title: str,
        text: str,
        source: str,
        url: str = "",
        examples: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        text = self._stringify(text).strip()
        title = self._stringify(title).strip()
        if not title or not text:
            return
        metadata = metadata or {}
        raw_id = f"{topic}|{title}|{text[:120]}|{metadata.get('lesson_id', '')}|{metadata.get('point_index', '')}"
        chunk_id = hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:12]
        if any(chunk.chunk_id == chunk_id for chunk in self.chunks):
            return
        self.chunks.append(
            KnowledgeChunk(
                chunk_id=chunk_id,
                topic=topic,
                title=title,
                text=text,
                source=source,
                url=url,
                examples=examples or [],
                metadata=metadata,
            )
        )

    def _score_chunk(self, query: str, query_tokens: List[str], chunk: KnowledgeChunk) -> float:
        title = chunk.title.lower()
        text = chunk.text.lower()
        examples = " ".join(str(example).lower() for example in chunk.examples)
        document = f"{title} {text} {examples}"
        doc_tokens = self._tokens_for_chunk(chunk)
        query_concepts = self._extract_concepts(query)

        score = 0.0
        if query in title:
            score += 5.0
        if query in text:
            score += 3.0
        if query in examples:
            score += 1.0
        if query_tokens and doc_tokens:
            score += self._cosine_similarity(query_tokens, doc_tokens) * 6.0
            score += len(set(query_tokens) & set(doc_tokens)) * 0.35
        if any(token in title for token in query_tokens):
            score += 0.8
        for concept in query_concepts:
            if concept in title:
                score += 4.0
            elif concept in text:
                score += 2.0
        if any(marker in query for marker in ["是什么", "什么是", "what is"]):
            if any(marker in title for marker in ["基础", "定义", "为什么需要", "是什么", "如何定义"]):
                score += 3.0
            if self._has_unasked_specialized_term(title, query):
                score *= 0.65
        if query_concepts and not any(concept in document for concept in query_concepts):
            return 0.0
        return score

    def _tokens_for_chunk(self, chunk: KnowledgeChunk) -> List[str]:
        cached = self._token_cache.get(chunk.chunk_id)
        if cached is not None:
            return cached
        tokens = self._tokenize(chunk.searchable_text())
        self._token_cache[chunk.chunk_id] = tokens
        return tokens

    @staticmethod
    def _chunk_to_result(chunk: KnowledgeChunk, score: float) -> Dict[str, Any]:
        return {
            "chunk_id": chunk.chunk_id,
            "topic": chunk.topic,
            "title": chunk.title,
            "question": chunk.title,
            "answer": chunk.text,
            "text": chunk.text,
            "examples": chunk.examples,
            "source": chunk.source,
            "url": chunk.url,
            "score": round(score, 4),
            "metadata": chunk.metadata,
        }

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return "; ".join(f"{key}: {KnowledgeBase._stringify(item)}" for key, item in value.items())
        if isinstance(value, Iterable):
            return "\n".join(KnowledgeBase._stringify(item) for item in value)
        return str(value)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        ascii_tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*|\d+", text.lower())
        cjk_text = "".join(re.findall(r"[\u4e00-\u9fff]+", text))
        cjk_tokens: List[str] = []
        for size in (1, 2, 3, 4):
            cjk_tokens.extend(
                cjk_text[index : index + size]
                for index in range(max(0, len(cjk_text) - size + 1))
            )
        return ascii_tokens + cjk_tokens

    @staticmethod
    def _extract_concepts(text: str) -> List[str]:
        concept_terms = [
            "函数",
            "列表",
            "元组",
            "字典",
            "集合",
            "循环",
            "条件",
            "变量",
            "赋值",
            "字符串",
            "索引",
            "切片",
            "缩进",
            "递归",
            "排序",
            "查找",
            "二分",
            "类",
            "对象",
            "继承",
            "append",
            "return",
            "print",
            "def",
            "class",
        ]
        lowered = text.lower()
        return [term for term in concept_terms if term.lower() in lowered]

    @staticmethod
    def _has_unasked_specialized_term(title: str, query: str) -> bool:
        specialized_terms = [
            "文档字符串",
            "lambda",
            "类型标注",
            "默认值",
            "关键字参数",
            "闭包",
            "装饰器",
            "生成器",
        ]
        return any(term in title and term not in query for term in specialized_terms)

    @staticmethod
    def _extract_concepts(text: str) -> List[str]:
        concept_terms = [
            "函数",
            "列表",
            "元组",
            "字典",
            "集合",
            "循环",
            "条件",
            "变量",
            "赋值",
            "字符串",
            "索引",
            "切片",
            "缩进",
            "递归",
            "排序",
            "查找",
            "二分",
            "类",
            "对象",
            "继承",
            "append",
            "return",
            "print",
            "def",
            "class",
        ]
        lowered = text.lower()
        return [term for term in concept_terms if term.lower() in lowered]

    @staticmethod
    def _has_unasked_specialized_term(title: str, query: str) -> bool:
        specialized_terms = [
            "文档字符串",
            "lambda",
            "类型标注",
            "默认值",
            "关键字参数",
            "闭包",
            "装饰器",
            "生成器",
        ]
        return any(term in title and term not in query for term in specialized_terms)

    @staticmethod
    def _cosine_similarity(left: List[str], right: List[str]) -> float:
        left_counts = Counter(left)
        right_counts = Counter(right)
        common = set(left_counts) & set(right_counts)
        numerator = sum(left_counts[token] * right_counts[token] for token in common)
        left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
        right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
        if not left_norm or not right_norm:
            return 0.0
        return numerator / (left_norm * right_norm)
