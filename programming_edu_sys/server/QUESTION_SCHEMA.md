# 统一题目结构

新增课程题、题库题或智能体生成题时，建议尽量使用下面的统一字段。
系统会自动兼容旧字段，但统一字段更方便后续维护和扩展。

```python
{
    "question_id": "py-func-001",
    "source": "static_question_bank",  # static_question_bank / lesson / ai_generated / import
    "topic": "python_basics",
    "difficulty": "beginner",          # beginner / intermediate / advanced
    "title": "两个数相加",
    "description": "编写函数 `add(a, b)`，返回两个参数的和。",
    "question_type": "coding",         # coding / debugging / algorithm / multiple_choice / text_answer
    "starter_code": "def add(a, b):\n    pass\n",
    "expected_function": "add",
    "hidden_tests": [
        {"call": "add(2, 3)", "expected": 5},
        {"call": "add(-1, 1)", "expected": 0},
    ],
    "hints": ["先写出函数头。", "使用 return 返回结果。"],
    "answer": "def add(a, b):\n    return a + b",
    "examples": [
        {"input": "add(2, 3)", "output": "5"},
    ],
    "tags": ["函数", "return", "参数"],
    "estimated_minutes": 6,
}
```

## 兼容说明

当前系统仍保留这些旧字段：

- `id` 等价于 `question_id`
- `content` 等价于 `description`
- `type` 等价于 `question_type`
- `test_cases` 等价于 `hidden_tests`

也就是说，旧的 `question_catalog.py`、`lesson_catalog.py` 和智能体生成题不会失效。

## 推荐新增位置

- 浏览器题库固定题：编辑 `server/question_catalog.py`
- 学习中心课程练习：编辑 `server/lesson_catalog.py` 中对应 lesson 的 `exercise`
- 智能体动态生成题：由 `exercise_agent.py` 生成后会自动标准化

## 判题要求

如果题目需要自动判题，至少提供：

- `expected_function`
- `hidden_tests`

`hidden_tests` 中的 `call` 会在用户代码命名空间中执行，`expected` 是期望返回值。
例如：

```python
{"call": "is_even(4)", "expected": True}
```
