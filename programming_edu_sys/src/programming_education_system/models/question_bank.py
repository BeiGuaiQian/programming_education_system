# programming_education_system/models/question_bank.py
"""
题库数据模型
"""
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class QuestionType(Enum):
    """题目类型枚举"""
    MULTIPLE_CHOICE = "multiple_choice"
    CODE_COMPLETION = "code_completion"
    ALGORITHM = "algorithm"
    DEBUGGING = "debugging"

class DifficultyLevel(Enum):
    """难度级别枚举"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class Question:
    """题目类"""
    id: str
    type: QuestionType
    topic: str
    difficulty: DifficultyLevel
    content: str
    answer: str
    hints: List[str] = None
    test_cases: List[Dict[str, Any]] = None

class QuestionBank:
    """题库管理类"""
    
    def __init__(self):
        self.questions: Dict[str, Question] = {}
        self._initialize_sample_questions()
    
    def _initialize_sample_questions(self):
        """初始化示例题目"""
        sample_questions = [
            Question(
                id="q1",
                type=QuestionType.MULTIPLE_CHOICE,
                topic="python_basics",
                difficulty=DifficultyLevel.BEGINNER,
                content="Python中哪个关键字用于定义函数？\nA. function\nB. def\nC. define\nD. func",
                answer="B",
                hints=["想想Python的函数定义语法"]
            ),
            Question(
                id="q2",
                type=QuestionType.CODE_COMPLETION,
                topic="python_basics",
                difficulty=DifficultyLevel.BEGINNER,
                content="完成以下函数，使其返回两个数的和：\ndef add(a, b):\n    # 你的代码 here",
                answer="return a + b",
                hints=["使用return语句返回结果"]
            ),
            Question(
                id="q3",
                type=QuestionType.ALGORITHM,
                topic="algorithms",
                difficulty=DifficultyLevel.INTERMEDIATE,
                content="编写一个函数，判断一个数是否为素数",
                answer="def is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
                test_cases=[
                    {"input": 2, "expected": True},
                    {"input": 4, "expected": False},
                    {"input": 17, "expected": True}
                ]
            )
        ]
        
        for question in sample_questions:
            self.questions[question.id] = question
    
    def get_questions_by_filters(self, topic: str = None, 
                               difficulty: DifficultyLevel = None,
                               question_type: QuestionType = None,
                               limit: int = 10) -> List[Question]:
        """根据过滤器获取题目"""
        filtered_questions = []
        
        for question in self.questions.values():
            if topic and question.topic != topic:
                continue
            if difficulty and question.difficulty != difficulty:
                continue
            if question_type and question.type != question_type:
                continue
            filtered_questions.append(question)
            
            if len(filtered_questions) >= limit:
                break
        
        return filtered_questions
    
    def add_question(self, question: Question):
        """添加题目"""
        self.questions[question.id] = question