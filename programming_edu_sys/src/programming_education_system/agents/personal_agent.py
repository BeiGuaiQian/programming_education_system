# programming_education_system/agents/personal_agent.py
"""
个性化学习代理
"""
from typing import Dict, Any, List
from programming_education_system.models.user_profile import UserProfile, KnowledgeMastery
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

class UserBehaviorTrackingAgent:
    """用户行为追踪子代理"""
    
    def __init__(self):
        self.behavior_logs = {}  # user_id -> list of behaviors
    
    async def track_behavior(self, user_id: str, behavior_data: Dict[str, Any]):
        """追踪用户行为"""
        if user_id not in self.behavior_logs:
            self.behavior_logs[user_id] = []
        
        self.behavior_logs[user_id].append({
            **behavior_data,
            "timestamp": "2024-01-01 10:00:00"  # 简化时间戳
        })
    
    async def get_user_behaviors(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户行为记录"""
        return self.behavior_logs.get(user_id, [])[:limit]

class UserCognitionUpdateAgent:
    """用户认知更新子代理"""
    
    def __init__(self):
        self.user_profiles = {}  # user_id -> UserProfile
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """更新用户画像"""
        if user_id not in self.user_profiles:
            # 创建新用户画像
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                learning_style=profile_data.get("learning_style", "visual"),
                programming_level=profile_data.get("programming_level", "beginner"),
                preferred_topics=profile_data.get("preferred_topics", ["python_basics"]),
                learning_goals=profile_data.get("learning_goals", [])
            )
        
        profile = self.user_profiles[user_id]
        
        # 更新掌握度（如果有相关信息）
        if "topic" in profile_data and "correct" in profile_data:
            profile.update_mastery(
                profile_data["topic"],
                profile_data["correct"],
                profile_data.get("difficulty", "beginner")
            )
        
        # 更新其他属性
        if "programming_level" in profile_data:
            profile.programming_level = profile_data["programming_level"]
        if "learning_style" in profile_data:
            profile.learning_style = profile_data["learning_style"]
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            return {
                "user_id": profile.user_id,
                "learning_style": profile.learning_style,
                "programming_level": profile.programming_level,
                "preferred_topics": profile.preferred_topics,
                "knowledge_mastery": {k: v.mastery_level for k, v in profile.knowledge_mastery.items()},
                "weak_topics": profile.get_weak_topics(),
                "learning_goals": profile.learning_goals
            }
        else:
            # 返回默认画像
            return {
                "user_id": user_id,
                "learning_style": "visual",
                "programming_level": "beginner",
                "preferred_topics": ["python_basics"],
                "knowledge_mastery": {},
                "weak_topics": [],
                "learning_goals": ["掌握Python基础"]
            }

class PersonalizedSuggestionAgent:
    """个性化建议子代理"""
    
    async def generate_personalized_suggestion(self, user_profile: Dict[str, Any]) -> List[str]:
        """生成个性化学习建议"""
        suggestions = []
        
        # 基于薄弱知识点建议
        weak_topics = user_profile.get("weak_topics", [])
        if weak_topics:
            suggestions.append(f"检测到你在以下知识点需要加强: {', '.join(weak_topics[:3])}")
            suggestions.append(f"建议针对'{weak_topics[0]}'进行专项练习")
        
        # 基于学习目标建议
        learning_goals = user_profile.get("learning_goals", [])
        if "web_development" in learning_goals:
            suggestions.append("要实现Web开发目标，建议学习路径: Python基础 → Flask/Django → 前端基础")
        
        # 基于学习风格建议
        learning_style = user_profile.get("learning_style", "visual")
        if learning_style == "visual":
            suggestions.append("根据你的视觉学习风格，建议多查看图表和示例代码")
        elif learning_style == "kinesthetic":
            suggestions.append("根据你的动手学习风格，建议多进行编码实践")
        
        # 使用LLM生成更个性化的建议
        if suggestions:
            system_prompt = """你是一个个性化学习顾问，请基于用户的学习情况和特点，提供具体、可操作的学习建议。"""
            
            user_message = f"用户画像：{user_profile}\n已有建议：{suggestions}\n请补充更多个性化学习建议："
            
            llm_suggestions = await llm_client.generate_response(system_prompt, user_message)
            suggestions.append(f"AI建议: {llm_suggestions}")
        
        return suggestions

class LearningPathGenerationAgent:
    """学习路径生成子代理"""
    
    async def generate_learning_path(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """生成个性化学习路径"""
        user_level = user_profile.get("programming_level", "beginner")
        weak_topics = user_profile.get("weak_topics", [])
        learning_goals = user_profile.get("learning_goals", [])
        
        # 基础学习路径模板
        learning_paths = {
            "beginner": [
                "Python基础语法",
                "数据类型和结构",
                "函数和模块",
                "面向对象编程基础",
                "错误处理"
            ],
            "intermediate": [
                "高级数据结构",
                "算法基础",
                "文件操作",
                "常用库的使用",
                "项目实践"
            ],
            "advanced": [
                "设计模式",
                "并发编程",
                "性能优化",
                "架构设计",
                "大型项目开发"
            ]
        }
        
        base_path = learning_paths.get(user_level, learning_paths["beginner"])
        
        # 插入薄弱知识点的复习
        final_path = []
        for topic in base_path:
            final_path.append(topic)
            # 在相关主题后插入薄弱知识点复习
            for weak_topic in weak_topics[:2]:  # 最多关注前2个薄弱点
                if self._is_related(topic, weak_topic):
                    final_path.append(f"复习: {weak_topic}")
        
        # 添加基于学习目标的高级主题
        if "web_development" in learning_goals and user_level != "beginner":
            final_path.extend(["Web框架学习", "数据库基础", "前端基础"])
        
        return {
            "level": user_level,
            "path": final_path,
            "estimated_duration": f"{len(final_path) * 2} 小时",
            "focus_areas": weak_topics[:3] if weak_topics else ["全面学习"]
        }
    
    def _is_related(self, topic: str, weak_topic: str) -> bool:
        """判断主题相关性（简化）"""
        topic_map = {
            "Python基础语法": ["python_basics"],
            "数据类型和结构": ["data_structures"],
            "算法基础": ["algorithms"]
        }
        
        for main_topic, related in topic_map.items():
            if topic == main_topic and weak_topic in related:
                return True
        return False

class PersonalizedLearningAgent(BaseAgent):
    """个性化学习代理"""
    
    def __init__(self):
        super().__init__("PersonalizedLearningAgent")
        self.tracking_agent = UserBehaviorTrackingAgent()
        self.cognition_agent = UserCognitionUpdateAgent()
        self.suggestion_agent = PersonalizedSuggestionAgent()
        self.path_agent = LearningPathGenerationAgent()
    
    async def track_user_behavior(self, behavior_data: Dict[str, Any]):
        """追踪用户行为"""
        user_id = behavior_data["user_id"]
        await self.tracking_agent.track_behavior(user_id, behavior_data)
        
        # 基于行为更新认知画像
        await self.cognition_agent.update_user_profile(user_id, behavior_data)
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """更新用户画像"""
        await self.cognition_agent.update_user_profile(user_id, profile_data)
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        return await self.cognition_agent.get_user_profile(user_id)
    
    async def generate_personalized_suggestion(self, user_id: str) -> List[str]:
        """生成个性化建议"""
        user_profile = await self.get_user_profile(user_id)
        return await self.suggestion_agent.generate_personalized_suggestion(user_profile)
    
    async def generate_learning_path(self, user_id: str) -> Dict[str, Any]:
        """生成学习路径"""
        user_profile = await self.get_user_profile(user_id)
        return await self.path_agent.generate_learning_path(user_profile)
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理个性化学习请求"""
        user_id = request["user_id"]
        content = request["content"]
        
        self.log_activity("处理个性化学习请求", {"user_id": user_id})
        
        if "建议" in content or "suggestion" in content.lower():
            # 生成个性化建议
            suggestions = await self.generate_personalized_suggestion(user_id)
            return {
                "response": "个性化学习建议",
                "details": {"suggestions": suggestions}
            }
        
        elif "路径" in content or "path" in content.lower():
            # 生成学习路径
            learning_path = await self.generate_learning_path(user_id)
            return {
                "response": "个性化学习路径",
                "details": {"learning_path": learning_path}
            }
        
        elif "画像" in content or "profile" in content.lower():
            # 返回用户画像
            user_profile = await self.get_user_profile(user_id)
            return {
                "response": "用户学习画像",
                "details": {"user_profile": user_profile}
            }
        
        else:
            # 默认返回建议
            suggestions = await self.generate_personalized_suggestion(user_id)
            return {
                "response": "个性化学习建议",
                "details": {"suggestions": suggestions}
            }