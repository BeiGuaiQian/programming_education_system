# programming_education_system/models/knowledge_base.py
"""
知识库数据模型
"""
from typing import Dict, List, Any

class KnowledgeBase:
    """知识库类"""
    
    def __init__(self):
        self.knowledge_items: Dict[str, List[Dict[str, Any]]] = {
            "python_basics": [
                {
                    "question": "Python中如何定义函数？",
                    "answer": "使用def关键字定义函数，例如：def function_name(parameters):",
                    "examples": ["def greet(name):\n    return f'Hello, {name}!''"]
                },
                {
                    "question": "Python中的列表和元组有什么区别？",
                    "answer": "列表是可变的，使用方括号[]定义；元组是不可变的，使用圆括号()定义",
                    "examples": ["列表: my_list = [1, 2, 3]", "元组: my_tuple = (1, 2, 3)"]
                }
            ],
            "data_structures": [
                {
                    "question": "什么是栈？",
                    "answer": "栈是一种后进先出(LIFO)的数据结构",
                    "examples": ["可以使用列表实现栈: stack = []", "stack.append(1)  # 入栈", "stack.pop()  # 出栈"]
                }
            ],
            "algorithms": [
                {
                    "question": "什么是二分查找？",
                    "answer": "二分查找是一种在有序数组中查找元素的算法，时间复杂度为O(log n)",
                    "examples": ["def binary_search(arr, target):\n    left, right = 0, len(arr)-1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1"]
                }
            ]
        }
    
    def search(self, query: str, topic: str = None) -> List[Dict[str, Any]]:
        """搜索知识库"""
        results = []
        
        if topic and topic in self.knowledge_items:
            # 在指定主题中搜索
            for item in self.knowledge_items[topic]:
                if query.lower() in item["question"].lower() or query.lower() in item["answer"].lower():
                    results.append(item)
        else:
            # 在所有主题中搜索
            for topic_items in self.knowledge_items.values():
                for item in topic_items:
                    if query.lower() in item["question"].lower() or query.lower() in item["answer"].lower():
                        results.append(item)
        
        return results
    
    def add_knowledge(self, topic: str, question: str, answer: str, examples: List[str] = None):
        """添加知识条目"""
        if topic not in self.knowledge_items:
            self.knowledge_items[topic] = []
        
        self.knowledge_items[topic].append({
            "question": question,
            "answer": answer,
            "examples": examples or []
        })