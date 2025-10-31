# src/programming_education_system/utils/question_bank_manager.py
"""
题库管理工具
"""
import json
import logging
from typing import Dict, Any, List
from programming_education_system.models.question_bank import QuestionBank, DifficultyLevel, QuestionType

logger = logging.getLogger(__name__)

class QuestionBankManager:
    """题库管理器"""
    
    def __init__(self, db_path: str = "question_bank.db"):
        self.question_bank = QuestionBank(db_path)
    
    def initialize_sample_data(self):
        """初始化示例数据"""
        sample_questions = [
            {
                "topic": "python_basics",
                "content": "编写一个函数，接受两个数字参数并返回它们的和。",
                "difficulty": "beginner",
                "question_type": "coding",
                "answer": "def add(a, b):\n    return a + b",
                "hints": ["使用def关键字定义函数", "使用return语句返回结果"],
                "examples": [
                    {"input": "add(2, 3)", "output": "5"},
                    {"input": "add(-1, 1)", "output": "0"}
                ],
                "tags": ["函数", "基础"],
                "source": "system"
            },
            {
                "topic": "python_basics",
                "content": "编写一个函数，判断一个数字是否为偶数。",
                "difficulty": "beginner", 
                "question_type": "coding",
                "answer": "def is_even(n):\n    return n % 2 == 0",
                "hints": ["使用取模运算符%", "偶数除以2的余数为0"],
                "examples": [
                    {"input": "is_even(4)", "output": "True"},
                    {"input": "is_even(7)", "output": "False"}
                ],
                "tags": ["函数", "条件判断"],
                "source": "system"
            },
            {
                "topic": "data_structures",
                "content": "编写一个函数，反转列表中的元素。",
                "difficulty": "intermediate",
                "question_type": "coding", 
                "answer": "def reverse_list(lst):\n    return lst[::-1]",
                "hints": ["使用切片操作", "也可以使用reversed()函数"],
                "examples": [
                    {"input": "reverse_list([1, 2, 3])", "output": "[3, 2, 1]"},
                    {"input": "reverse_list(['a', 'b', 'c'])", "output": "['c', 'b', 'a']"}
                ],
                "tags": ["列表", "算法"],
                "source": "system"
            },
            {
                "topic": "algorithms", 
                "content": "实现冒泡排序算法。",
                "difficulty": "intermediate",
                "question_type": "coding",
                "answer": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr",
                "hints": ["使用双重循环", "比较相邻元素并交换"],
                "examples": [
                    {"input": "bubble_sort([64, 34, 25, 12, 22, 11, 90])", "output": "[11, 12, 22, 25, 34, 64, 90]"}
                ],
                "tags": ["排序", "算法"],
                "source": "system"
            },
            {
                "topic": "oop",
                "content": "创建一个Person类，包含name和age属性，以及一个introduce方法。",
                "difficulty": "intermediate",
                "question_type": "coding",
                "answer": "class Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n    \n    def introduce(self):\n        return f\"我叫{self.name}，今年{self.age}岁。\"",
                "hints": ["使用__init__方法初始化属性", "使用self关键字访问实例属性"],
                "examples": [
                    {"input": "p = Person('张三', 25)\np.introduce()", "output": "我叫张三，今年25岁。"}
                ],
                "tags": ["类", "面向对象"],
                "source": "system"
            }
        ]
        
        result = self.question_bank.batch_import_questions(sample_questions)
        logger.info(f"示例数据初始化完成: {result}")
        return result
    
    def search_questions(self, keyword: str, topic: str = None, difficulty: str = None, 
                        limit: int = 10) -> List[Dict[str, Any]]:
        """搜索题目"""
        if keyword:
            questions = self.question_bank.search_questions(keyword, limit)
        else:
            difficulty_enum = DifficultyLevel(difficulty) if difficulty else None
            questions = self.question_bank.get_questions_by_filters(
                topic=topic, 
                difficulty=difficulty_enum,
                limit=limit
            )
        
        return [q.to_dict() for q in questions]
    
    def get_question_stats(self) -> Dict[str, Any]:
        """获取题库统计"""
        return self.question_bank.get_statistics()
    
    def export_to_json(self, file_path: str, filters: Dict[str, Any] = None):
        """导出题库到JSON文件"""
        questions = self.question_bank.export_questions(filters)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        
        logger.info(f"题库已导出到: {file_path}, 共{len(questions)}道题目")
    
    def import_from_json(self, file_path: str) -> Dict[str, int]:
        """从JSON文件导入题库"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            
            result = self.question_bank.batch_import_questions(questions_data)
            logger.info(f"从{file_path}导入完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"导入题库失败: {e}")
            return {'imported': 0, 'skipped': 0, 'errors': 1, 'total_processed': 0}

# 全局题库管理器实例
question_bank_manager = QuestionBankManager()