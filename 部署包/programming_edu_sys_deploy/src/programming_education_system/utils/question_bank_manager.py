"""Question bank management helpers."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from programming_education_system.config.llm_config import Config
from programming_education_system.models.question_bank import DifficultyLevel, QuestionBank

logger = logging.getLogger(__name__)


class QuestionBankManager:
    """High-level wrapper around the SQLite-backed question bank."""

    def __init__(self, db_path: str = ""):
        self.question_bank = QuestionBank(db_path or Config.QUESTION_BANK_DB)

    def initialize_sample_data(self):
        """Seed the bank with a small set of starter questions."""
        sample_questions = [
            {
                "topic": "python_basics",
                "content": "编写一个函数，接受两个数字参数并返回它们的和。",
                "difficulty": "beginner",
                "question_type": "coding",
                "answer": "def add(a, b):\n    return a + b",
                "hints": ["使用 def 定义函数", "使用 return 返回结果"],
                "examples": [
                    {"input": "add(2, 3)", "output": "5"},
                    {"input": "add(-1, 1)", "output": "0"},
                ],
                "tags": ["函数", "基础"],
                "source": "system",
            },
            {
                "topic": "python_basics",
                "content": "编写一个函数，判断一个整数是否为偶数。",
                "difficulty": "beginner",
                "question_type": "coding",
                "answer": "def is_even(n):\n    return n % 2 == 0",
                "hints": ["可以使用取模运算", "偶数除以 2 的余数为 0"],
                "examples": [
                    {"input": "is_even(4)", "output": "True"},
                    {"input": "is_even(7)", "output": "False"},
                ],
                "tags": ["函数", "条件判断"],
                "source": "system",
            },
            {
                "topic": "data_structures",
                "content": "编写一个函数，反转列表中的元素。",
                "difficulty": "intermediate",
                "question_type": "coding",
                "answer": "def reverse_list(lst):\n    return lst[::-1]",
                "hints": ["可以使用切片", "也可以使用 reversed()"],
                "examples": [
                    {"input": "reverse_list([1, 2, 3])", "output": "[3, 2, 1]"},
                    {"input": "reverse_list(['a', 'b', 'c'])", "output": "['c', 'b', 'a']"},
                ],
                "tags": ["列表", "基础算法"],
                "source": "system",
            },
            {
                "topic": "algorithms",
                "content": "实现冒泡排序算法。",
                "difficulty": "intermediate",
                "question_type": "coding",
                "answer": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr",
                "hints": ["使用双重循环", "交换相邻逆序元素"],
                "examples": [
                    {"input": "bubble_sort([64, 34, 25, 12])", "output": "[12, 25, 34, 64]"},
                ],
                "tags": ["排序", "算法"],
                "source": "system",
            },
            {
                "topic": "oop",
                "content": "创建一个 Person 类，包含 name 和 age 属性，以及 introduce 方法。",
                "difficulty": "intermediate",
                "question_type": "coding",
                "answer": "class Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n\n    def introduce(self):\n        return f'我叫{self.name}，今年{self.age}岁。'",
                "hints": ["在 __init__ 中初始化属性", "使用 self 访问实例属性"],
                "examples": [
                    {"input": "p = Person('张三', 25)\np.introduce()", "output": "我叫张三，今年25岁。"},
                ],
                "tags": ["类", "面向对象"],
                "source": "system",
            },
        ]

        result = self.question_bank.batch_import_questions(sample_questions)
        logger.info("Sample question data initialized: %s", result)
        return result

    def search_questions(
        self, keyword: str, topic: str = None, difficulty: str = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search questions by keyword or filters."""
        if keyword:
            questions = self.question_bank.search_questions(keyword, limit)
        else:
            questions = self.question_bank.get_questions_by_filters(
                topic=topic,
                difficulty=self._normalize_difficulty(difficulty),
                limit=limit,
            )
        return [question.to_dict() for question in questions]

    def get_question_stats(self) -> Dict[str, Any]:
        return self.question_bank.get_statistics()

    def export_to_json(self, file_path: str, filters: Dict[str, Any] = None):
        filters = filters or {}
        if filters.get("difficulty"):
            filters = {**filters, "difficulty": self._normalize_difficulty(filters["difficulty"])}

        questions = self.question_bank.export_questions(filters)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(questions, file, ensure_ascii=False, indent=2)

        logger.info("Question bank exported to %s with %s questions", file_path, len(questions))

    def import_from_json(self, file_path: str) -> Dict[str, int]:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                questions_data = json.load(file)

            result = self.question_bank.batch_import_questions(questions_data)
            logger.info("Question bank imported from %s: %s", file_path, result)
            return result
        except Exception as exc:
            logger.error("Failed to import question bank: %s", exc)
            return {"imported": 0, "skipped": 0, "errors": 1, "total_processed": 0}

    @staticmethod
    def _normalize_difficulty(difficulty):
        if not difficulty:
            return None
        if isinstance(difficulty, DifficultyLevel):
            return difficulty
        return DifficultyLevel(str(difficulty))


question_bank_manager = QuestionBankManager()
