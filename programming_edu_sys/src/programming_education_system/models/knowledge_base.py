"""In-memory knowledge base used by the QA agent."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class KnowledgeBase:
    """Stores lightweight topic-based knowledge entries."""

    def __init__(self) -> None:
        self.knowledge_items: Dict[str, List[Dict[str, Any]]] = {
            "python_basics": [
                {
                    "question": "Python 中如何定义函数？",
                    "answer": "使用 `def` 关键字定义函数，例如 `def function_name(params):`。",
                    "examples": ["def greet(name):\n    return f'Hello, {name}!'"],
                },
                {
                    "question": "Python 中列表和元组有什么区别？",
                    "answer": "列表是可变序列，使用 `[]`；元组是不可变序列，使用 `()`。",
                    "examples": ["my_list = [1, 2, 3]", "my_tuple = (1, 2, 3)"],
                },
            ],
            "data_structures": [
                {
                    "question": "什么是栈？",
                    "answer": "栈是一种后进先出（LIFO）的数据结构，常见操作有入栈和出栈。",
                    "examples": [
                        "stack = []",
                        "stack.append(1)  # 入栈",
                        "stack.pop()  # 出栈",
                    ],
                }
            ],
            "algorithms": [
                {
                    "question": "什么是二分查找？",
                    "answer": "二分查找是在有序序列中查找目标值的算法，时间复杂度通常是 O(log n)。",
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
                }
            ],
        }

    def search(self, query: str, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search entries by fuzzy substring match."""
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        candidates: List[Dict[str, Any]] = []
        topic_items = {topic: self.knowledge_items.get(topic, [])} if topic else self.knowledge_items

        for topic_name, items in topic_items.items():
            for item in items:
                score = self._score_item(normalized_query, item)
                if score <= 0:
                    continue
                candidates.append({**item, "topic": topic_name, "_score": score})

        candidates.sort(key=lambda item: item["_score"], reverse=True)
        for item in candidates:
            item.pop("_score", None)
        return candidates

    def add_knowledge(
        self,
        topic: str,
        question: str,
        answer: str,
        examples: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add one knowledge entry."""
        self.knowledge_items.setdefault(topic, []).append(
            {
                "question": question,
                "answer": answer,
                "examples": examples or [],
                "metadata": metadata or {},
            }
        )

    def get_topics(self) -> List[str]:
        """Return all topic names."""
        return sorted(self.knowledge_items.keys())

    def _score_item(self, query: str, item: Dict[str, Any]) -> int:
        question = str(item.get("question", "")).lower()
        answer = str(item.get("answer", "")).lower()
        examples = " ".join(str(example).lower() for example in item.get("examples", []))

        score = 0
        if query in question:
            score += 3
        if query in answer:
            score += 2
        if query in examples:
            score += 1

        query_tokens = [token for token in query.split() if token]
        if query_tokens:
            score += sum(token in question for token in query_tokens)
            score += sum(token in answer for token in query_tokens)

        return score
