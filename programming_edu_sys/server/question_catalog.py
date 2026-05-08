"""Curated question bank for the browser question-center experience."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from programming_education_system.models.question_schema import normalize_question


QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "py-func-001",
        "topic": "python_basics",
        "topic_name": "Python 基础",
        "difficulty": "beginner",
        "type": "coding",
        "title": "两个数相加",
        "content": "编写函数 `add(a, b)`，返回两个参数的和。",
        "answer": "def add(a, b):\n    return a + b",
        "starter_code": "def add(a, b):\n    # TODO: 返回 a 和 b 的和\n    pass\n",
        "expected_function": "add",
        "hidden_tests": [
            {"call": "add(2, 3)", "expected": 5},
            {"call": "add(-1, 1)", "expected": 0},
            {"call": "add(10, 25)", "expected": 35},
        ],
        "hints": ["先写出函数头 `def add(a, b):`。", "使用 `return` 返回 `a + b`。"],
        "examples": [
            {"input": "add(2, 3)", "output": "5"},
            {"input": "add(-1, 1)", "output": "0"},
        ],
        "tags": ["函数", "return", "参数"],
        "estimated_minutes": 6,
    },
    {
        "id": "py-func-002",
        "topic": "python_basics",
        "topic_name": "Python 基础",
        "difficulty": "beginner",
        "type": "coding",
        "title": "判断偶数",
        "content": "编写函数 `is_even(n)`，如果 `n` 是偶数返回 `True`，否则返回 `False`。",
        "answer": "def is_even(n):\n    return n % 2 == 0",
        "starter_code": "def is_even(n):\n    # TODO: 如果 n 是偶数返回 True，否则返回 False\n    pass\n",
        "expected_function": "is_even",
        "hidden_tests": [
            {"call": "is_even(4)", "expected": True},
            {"call": "is_even(7)", "expected": False},
            {"call": "is_even(0)", "expected": True},
        ],
        "hints": ["偶数除以 2 的余数是 0。", "比较表达式本身会得到布尔值。"],
        "examples": [
            {"input": "is_even(4)", "output": "True"},
            {"input": "is_even(7)", "output": "False"},
        ],
        "tags": ["函数", "条件", "取模"],
        "estimated_minutes": 7,
    },
    {
        "id": "py-func-003",
        "topic": "python_basics",
        "topic_name": "Python 基础",
        "difficulty": "beginner",
        "type": "debugging",
        "title": "修复返回值错误",
        "content": "下面的函数只打印了结果，但题目要求返回字符串。请改正它：\n\n```python\ndef greet(name):\n    print(f\"Hello, {name}!\")\n```",
        "answer": "def greet(name):\n    return f\"Hello, {name}!\"",
        "starter_code": "def greet(name):\n    print(f\"Hello, {name}!\")\n",
        "expected_function": "greet",
        "hidden_tests": [
            {"call": "greet('Alice')", "expected": "Hello, Alice!"},
            {"call": "greet('Python')", "expected": "Hello, Python!"},
        ],
        "hints": ["题目要求返回时，优先检查是否用了 `return`。", "`print` 只是显示内容。"],
        "examples": [{"input": "greet('Alice')", "output": "Hello, Alice!"}],
        "tags": ["函数", "return", "调试"],
        "estimated_minutes": 8,
    },
    {
        "id": "py-list-001",
        "topic": "data_structures",
        "topic_name": "数据结构",
        "difficulty": "intermediate",
        "type": "coding",
        "title": "列表求和",
        "content": "编写函数 `sum_list(nums)`，返回列表中所有数字的和。",
        "answer": "def sum_list(nums):\n    total = 0\n    for n in nums:\n        total += n\n    return total",
        "starter_code": "def sum_list(nums):\n    # TODO: 返回 nums 中所有数字的和\n    pass\n",
        "expected_function": "sum_list",
        "hidden_tests": [
            {"call": "sum_list([1, 2, 3])", "expected": 6},
            {"call": "sum_list([])", "expected": 0},
            {"call": "sum_list([-2, 5, 7])", "expected": 10},
        ],
        "hints": ["可以从 `total = 0` 开始累计。", "用 `for` 循环依次处理列表元素。"],
        "examples": [
            {"input": "sum_list([1, 2, 3])", "output": "6"},
            {"input": "sum_list([])", "output": "0"},
        ],
        "tags": ["列表", "循环", "累计"],
        "estimated_minutes": 10,
    },
    {
        "id": "py-list-002",
        "topic": "data_structures",
        "topic_name": "数据结构",
        "difficulty": "intermediate",
        "type": "coding",
        "title": "反转列表",
        "content": "编写函数 `reverse_list(items)`，返回一个反转后的新列表，不要修改原列表。",
        "answer": "def reverse_list(items):\n    return items[::-1]",
        "starter_code": "def reverse_list(items):\n    # TODO: 返回反转后的新列表\n    pass\n",
        "expected_function": "reverse_list",
        "hidden_tests": [
            {"call": "reverse_list([1, 2, 3])", "expected": [3, 2, 1]},
            {"call": "reverse_list(['a', 'b'])", "expected": ["b", "a"]},
        ],
        "hints": ["可以使用切片。", "`items[::-1]` 会生成一个反向的新列表。"],
        "examples": [{"input": "reverse_list([1, 2, 3])", "output": "[3, 2, 1]"}],
        "tags": ["列表", "切片"],
        "estimated_minutes": 9,
    },
    {
        "id": "py-dict-001",
        "topic": "data_structures",
        "topic_name": "数据结构",
        "difficulty": "intermediate",
        "type": "coding",
        "title": "统计单词出现次数",
        "content": "编写函数 `count_words(words)`，接收字符串列表，返回每个字符串出现次数组成的字典。",
        "answer": "def count_words(words):\n    counts = {}\n    for word in words:\n        counts[word] = counts.get(word, 0) + 1\n    return counts",
        "starter_code": "def count_words(words):\n    # TODO: 返回每个字符串出现次数组成的字典\n    pass\n",
        "expected_function": "count_words",
        "hidden_tests": [
            {"call": "count_words(['a', 'b', 'a'])", "expected": {"a": 2, "b": 1}},
            {"call": "count_words([])", "expected": {}},
        ],
        "hints": ["字典适合保存“键 -> 次数”。", "`dict.get(key, 0)` 可以给不存在的键一个默认值。"],
        "examples": [{"input": "count_words(['a', 'b', 'a'])", "output": "{'a': 2, 'b': 1}"}],
        "tags": ["字典", "循环", "计数"],
        "estimated_minutes": 14,
    },
    {
        "id": "py-algo-001",
        "topic": "algorithms",
        "topic_name": "算法入门",
        "difficulty": "advanced",
        "type": "algorithm",
        "title": "寻找最大值",
        "content": "编写函数 `find_max(nums)`，不使用内置 `max`，返回列表中的最大值。可以假设列表非空。",
        "answer": "def find_max(nums):\n    current = nums[0]\n    for n in nums[1:]:\n        if n > current:\n            current = n\n    return current",
        "starter_code": "def find_max(nums):\n    # TODO: 不使用 max，返回列表最大值\n    pass\n",
        "expected_function": "find_max",
        "hidden_tests": [
            {"call": "find_max([3, 1, 9, 2])", "expected": 9},
            {"call": "find_max([-5, -2, -9])", "expected": -2},
        ],
        "hints": ["先把第一个元素当作当前最大值。", "遍历剩下元素，遇到更大的就更新。"],
        "examples": [{"input": "find_max([3, 1, 9, 2])", "output": "9"}],
        "tags": ["算法", "循环", "比较"],
        "estimated_minutes": 12,
    },
    {
        "id": "py-oop-001",
        "topic": "oop",
        "topic_name": "面向对象",
        "difficulty": "advanced",
        "type": "coding",
        "title": "创建学生类",
        "content": "创建 `Student` 类，包含 `name` 和 `score` 属性，并提供 `is_passed()` 方法，分数大于等于 60 返回 `True`。",
        "answer": "class Student:\n    def __init__(self, name, score):\n        self.name = name\n        self.score = score\n\n    def is_passed(self):\n        return self.score >= 60",
        "starter_code": "class Student:\n    def __init__(self, name, score):\n        # TODO: 保存 name 和 score\n        pass\n\n    def is_passed(self):\n        # TODO: 分数大于等于 60 返回 True\n        pass\n",
        "expected_function": "",
        "hidden_tests": [
            {"call": "Student('Alice', 80).is_passed()", "expected": True},
            {"call": "Student('Bob', 59).is_passed()", "expected": False},
        ],
        "hints": ["使用 `__init__` 初始化属性。", "方法里用 `self.score` 访问分数。"],
        "examples": [{"input": "Student('Alice', 80).is_passed()", "output": "True"}],
        "tags": ["类", "方法", "self"],
        "estimated_minutes": 16,
    },
]


def list_questions(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    keyword: Optional[str] = None,
) -> List[Dict[str, Any]]:
    items = [normalize_question(item, source="static_question_bank") for item in QUESTIONS]
    if topic and topic != "all":
        items = [item for item in items if item["topic"] == topic]
    if difficulty and difficulty != "all":
        items = [item for item in items if item["difficulty"] == difficulty]
    if question_type and question_type != "all":
        items = [item for item in items if item["question_type"] == question_type or item["type"] == question_type]
    if keyword:
        lowered = keyword.lower()
        items = [
            item
            for item in items
            if lowered in item["title"].lower()
            or lowered in item["description"].lower()
            or lowered in str(item.get("content", "")).lower()
            or any(lowered in tag.lower() for tag in item["tags"])
        ]
    return items


def get_question(question_id: str) -> Optional[Dict[str, Any]]:
    for item in list_questions():
        if item["id"] == question_id or item["question_id"] == question_id:
            return item
    return None


def get_question_facets() -> Dict[str, Any]:
    topics = {}
    difficulties = {}
    types = {}
    for item in list_questions():
        topics[item["topic"]] = item["topic_name"]
        difficulties[item["difficulty"]] = difficulties.get(item["difficulty"], 0) + 1
        types[item["question_type"]] = types.get(item["question_type"], 0) + 1
    return {
        "topics": [{"value": key, "label": value} for key, value in topics.items()],
        "difficulties": [{"value": key, "count": value} for key, value in difficulties.items()],
        "types": [{"value": key, "count": value} for key, value in types.items()],
    }
