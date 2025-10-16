# programming_education_system/agents/exercise_agent.py
"""
练习生成代理
"""
from typing import Dict, Any, List
from programming_education_system.models.question_bank import QuestionBank, DifficultyLevel, QuestionType
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

class ExistingQuestionBankAgent:
    """现有题库子代理"""
    
    def __init__(self):
        self.question_bank = QuestionBank()
    
    async def retrieve_from_question_bank(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从题库检索题目"""
        topic = filters.get("topic")
        difficulty = filters.get("difficulty")
        question_type = filters.get("question_type")
        limit = filters.get("limit", 5)
        
        questions = self.question_bank.get_questions_by_filters(
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            limit=limit
        )
        
        return [{
            "id": q.id,
            "type": q.type.value,
            "topic": q.topic,
            "difficulty": q.difficulty.value,
            "content": q.content,
            "answer": q.answer,
            "hints": q.hints or []
        } for q in questions]

class AutoExerciseGenerationAgent:
    """自动题目生成子代理"""
    
    async def auto_generate_programming_exercise(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """自动生成编程题目"""
        system_prompt = """你是一个编程教育专家，擅长设计适合不同难度级别的编程练习题。
你需要根据主代理发来的的提示词生成一个合适的编程题目，题目要求如下
1.优先检索我提供的题库搜索满足用户需求的题目
2.如果题库没有合适的题目，自动生成适合用户的编程练习题
3.生成的题目符合当前用户的认知水平

"""
        
        user_message = f"请生成一个关于{topic}的编程题目，难度级别为{difficulty}。要求：\n1. 题目描述清晰\n2. 提供示例输入输出"
        
        generated_content = await llm_client.generate_response(system_prompt, user_message)
        
        return {
            "type": "algorithm",
            "topic": topic,
            "difficulty": difficulty,
            "content": generated_content,
            "source": "auto_generated"
        }

class QuizGenerationAgent:
    """测验生成子代理"""
    
    async def generate_adaptive_quiz(self, user_profile: Dict[str, Any], topic: str = None) -> Dict[str, Any]:
        """生成自适应测验"""
        # 基于用户画像调整难度
        user_level = user_profile.get("programming_level", "beginner")
        weak_topics = user_profile.get("weak_topics", [])
        
        target_topic = topic or (weak_topics[0] if weak_topics else "python_basics")
        
        # 根据用户水平确定难度
        difficulty_map = {
            "beginner": DifficultyLevel.BEGINNER,
            "intermediate": DifficultyLevel.INTERMEDIATE,
            "advanced": DifficultyLevel.ADVANCED
        }
        difficulty = difficulty_map.get(user_level, DifficultyLevel.BEGINNER)
        
        return {
            "topic": target_topic,
            "difficulty": difficulty.value,
            "question_count": 5,
            "adaptive": True,
            "focus_areas": weak_topics[:2] if weak_topics else [target_topic]
        }

class ExerciseGenerationAgent(BaseAgent):
    """练习生成代理"""
    
    def __init__(self, personal_agent):
        super().__init__("ExerciseGenerationAgent")
        self.bank_agent = ExistingQuestionBankAgent()
        self.auto_agent = AutoExerciseGenerationAgent()
        self.quiz_agent = QuizGenerationAgent()
        self.personal_agent = personal_agent
    
    async def generate_exercise(self, exercise_type: str, difficulty: str, 
                              user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """生成练习总入口"""
        self.log_activity("生成练习", {
            "type": exercise_type,
            "difficulty": difficulty
        })
        
        if exercise_type == "preset":
            # 预设题库练习
            filters = {
                "difficulty": DifficultyLevel(difficulty),
                "limit": 3
            }
            questions = await self.bank_agent.retrieve_from_question_bank(filters)
            return {"type": "preset", "questions": questions}
        
        elif exercise_type == "dynamic":
            # 动态生成练习
            topic = user_profile.get("preferred_topics", ["python_basics"])[0]
            exercise = await self.auto_agent.auto_generate_programming_exercise(topic, difficulty)
            return {"type": "dynamic", "exercise": exercise}
        
        elif exercise_type == "quiz":
            # 生成测验
            quiz = await self.quiz_agent.generate_adaptive_quiz(user_profile)
            # 为测验获取具体题目
            filters = {
                "topic": quiz["topic"],
                "difficulty": DifficultyLevel(quiz["difficulty"]),
                "limit": quiz["question_count"]
            }
            questions = await self.bank_agent.retrieve_from_question_bank(filters)
            quiz["questions"] = questions
            return {"type": "quiz", "quiz": quiz}
        
        else:
            return {"error": "不支持的练习类型"}
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理练习生成请求"""
        user_id = request["user_id"]
        content = request["content"]
        
        # 解析请求内容获取参数
        exercise_type = self._parse_exercise_type(content)
        difficulty = self._parse_difficulty(content)
        
        # 获取用户画像
        user_profile = await self.personal_agent.get_user_profile(user_id)
        
        # 生成练习
        result = await self.generate_exercise(exercise_type, difficulty, user_profile)
        
        # 记录用户行为
        behavior_data = {
            "user_id": user_id,
            "exercise_type": exercise_type,
            "difficulty": difficulty,
            "topic": result.get("topic", "general")
        }
        await self.personal_agent.track_user_behavior(behavior_data)
        
        return {
            "response": f"已生成{exercise_type}类型的练习",
            "details": result
        }
    
    def _parse_exercise_type(self, content: str) -> str:
        """从内容解析练习类型"""
        content_lower = content.lower()
        
        if "测验" in content_lower or "测试" in content_lower:
            return "quiz"
        elif "动态" in content_lower or "生成" in content_lower:
            return "dynamic"
        else:
            return "preset"  # 默认预设题库
    
    def _parse_difficulty(self, content: str) -> str:
        """从内容解析难度"""
        content_lower = content.lower()
        
        if "高级" in content_lower or "困难" in content_lower:
            return "advanced"
        elif "中级" in content_lower:
            return "intermediate"
        else:
            return "beginner"  # 默认初级