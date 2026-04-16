"""Learning-center lesson catalog backed by authoritative references."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


LESSONS: List[Dict[str, Any]] = [
    {
        "id": "python-functions-basics",
        "language": "python",
        "title": "函数定义基础",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 4.8 Defining Functions",
            "url": "https://docs.python.org/3.12/tutorial/controlflow.html#defining-functions",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "这一节先解决一个最常见的问题：同一段逻辑以后还要用很多次，怎么办？"
            "Python 里的函数就是为这件事准备的。"
            "我们把一段代码整理成一个有名字的小步骤，以后需要时只调用这个名字，"
            "代码会更短，也更容易检查和修改。"
        ),
        "knowledge_points": [
            {
                "title": "1. 先知道为什么需要函数",
                "explanation": (
                    "先不用急着背语法。可以先把函数想成一个“可重复使用的小步骤”。"
                    "比如生成问候语这件事，本质上每次都差不多：拿到一个名字，拼成一句话。"
                    "如果每次都重新写一遍，代码会越来越散；"
                    "把它放进函数里，就像给这件事贴了一个清楚的标签。"
                ),
                "example": (
                    "# 这是一次性的写法：能用，但下次还得再写一遍\n"
                    "name = 'Alice'\n"
                    "message = f\"Hello, {name}!\"\n"
                    "print(message)"
                ),
            },
            {
                "title": "2. 用 def 给这段逻辑起名字",
                "explanation": (
                    "在 Python 里，定义函数从 `def` 开始。"
                    "`greet` 是函数名，表示这个函数负责“问候”；"
                    "括号里的 `name` 是它需要的材料；"
                    "冒号后面换行并缩进，缩进里面的代码就是这个函数真正要做的事。"
                    "你可以把这一行读成：定义一个叫 greet 的函数，它需要一个 name。"
                ),
                "example": (
                    "def greet(name):\n"
                    "    # 根据传进来的 name 生成一句问候语\n"
                    "    return f\"Hello, {name}!\""
                ),
            },
            {
                "title": "3. 参数让函数可以处理不同情况",
                "explanation": (
                    "如果函数里把名字写死成 Alice，那它只能问候 Alice。"
                    "参数的作用，就是把这个固定值变成一个可以变化的位置。"
                    "调用函数时传入 Alice，`name` 就临时代表 Alice；"
                    "传入 Bob，`name` 就临时代表 Bob。"
                    "同一个函数因此可以服务很多不同输入。"
                ),
                "example": (
                    "def greet(name):\n"
                    "    return f\"Hello, {name}!\"\n\n"
                    "# 同一个函数，换一个参数，就得到不同结果\n"
                    "greet('Alice')  # Hello, Alice!\n"
                    "greet('Bob')    # Hello, Bob!"
                ),
            },
            {
                "title": "4. return 表示“把结果交出去”",
                "explanation": (
                    "`return` 不是为了把内容显示在屏幕上，"
                    "而是把函数算出的结果交回给调用它的地方。"
                    "这样外面的代码才能继续保存这个结果、比较这个结果，或者把它传给下一步使用。"
                    "所以题目里写“返回”，通常就要用 `return`；"
                    "只用 `print` 只是让人看见了结果，程序本身并没有拿到它。"
                ),
                "example": (
                    "def double(n):\n"
                    "    return n * 2\n\n"
                    "# double(5) 的结果被交给 result，后面还能继续使用\n"
                    "result = double(5)\n"
                    "print(result)  # 10"
                ),
            },
            {
                "title": "5. 做题时按这个顺序检查",
                "explanation": (
                    "刚开始写函数，出错很正常，不用慌。"
                    "可以按一个固定顺序检查：函数名是不是题目要求的名字，"
                    "参数有没有写，函数体有没有缩进，最后有没有用 `return` 返回结果。"
                    "这几个点对了，大多数基础函数题就已经走在正确方向上了。"
                ),
                "example": (
                    "def greet(name):\n"
                    "    print(f\"Hello, {name}!\")\n\n"
                    "# 这段代码能在屏幕上显示内容\n"
                    "# 但函数没有 return，所以返回值其实是 None\n"
                    "# 如果题目要求“返回字符串”，这里就应该改成 return"
                ),
            },
        ],
        "exercise": {
            "id": "python-functions-basics-ex-01",
            "title": "实现一个问候函数",
            "expected_function": "greet",
            "description": (
                "现在把上面的思路合起来用一次。"
                "请写一个叫 `greet` 的函数，它接收一个名字 `name`，"
                "然后把问候语作为结果返回。"
                "比如传入 `Alice`，函数应该返回 `Hello, Alice!`。"
            ),
            "requirements": [
                "函数名必须是 `greet`。",
                "函数必须接收一个参数 `name`。",
                "返回值必须是字符串，而不是使用 `print` 输出。",
                "传入 `Alice` 时应返回 `Hello, Alice!`。",
            ],
            "examples": [
                {"input": "greet('Alice')", "output": "Hello, Alice!"},
                {"input": "greet('Bob')", "output": "Hello, Bob!"},
            ],
            "hints": [
                "第一步先写函数头：`def greet(name):`。",
                "第二步在函数体里缩进一层，写出要返回的问候语。",
                "题目要的是“返回结果”，所以这里应该用 `return`，不要只写 `print`。",
                "如果你会 f-string，可以写成：`return f\"Hello, {name}!\"`。",
            ],
            "starter_code": (
                "def greet(name):\n"
                "    # TODO: 返回形如 Hello, Alice! 的字符串\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def greet(name):\n"
                "    return f\"Hello, {name}!\"\n"
            ),
            "hidden_tests": [
                {"call": "greet('Alice')", "expected": "Hello, Alice!"},
                {"call": "greet('Python')", "expected": "Hello, Python!"},
                {"call": "greet('张三')", "expected": "Hello, 张三!"},
            ],
        },
    }
]


def list_lessons(language: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return lesson summaries for the learning center."""
    items = LESSONS
    if language:
        items = [lesson for lesson in items if lesson.get("language") == language]
    return [
        {
            "id": lesson["id"],
            "language": lesson["language"],
            "title": lesson["title"],
            "topic": lesson["topic"],
            "difficulty": lesson["difficulty"],
            "summary": lesson["summary"],
            "source": lesson["source"],
        }
        for lesson in items
    ]


def get_lesson(lesson_id: str) -> Optional[Dict[str, Any]]:
    """Return full lesson details by id."""
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            return lesson
    return None
