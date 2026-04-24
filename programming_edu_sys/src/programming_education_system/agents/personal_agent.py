"""Personalized learning agent with lightweight profile management."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.models.user_profile import UserProfile
from programming_education_system.utils.llm_utils import llm_client


class UserBehaviorTrackingAgent:
    """Stores user behavior records in memory."""

    def __init__(self) -> None:
        self.behavior_logs: Dict[str, List[Dict[str, Any]]] = {}

    async def track_behavior(self, user_id: str, behavior_data: Dict[str, Any]) -> None:
        self.behavior_logs.setdefault(user_id, []).append(
            {
                **behavior_data,
                "timestamp": behavior_data.get("timestamp") or datetime.now().isoformat(),
            }
        )

    async def get_user_behaviors(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.behavior_logs.get(user_id, [])[-limit:]


class UserCognitionUpdateAgent:
    """Maintains a practical user profile without heavy external dependencies."""

    def __init__(self) -> None:
        self.user_profiles: Dict[str, UserProfile] = {}

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        profile = self.user_profiles.setdefault(
            user_id,
            UserProfile(
                user_id=user_id,
                learning_style=profile_data.get("learning_style", "visual"),
                programming_level=profile_data.get("programming_level", "beginner"),
                preferred_topics=list(profile_data.get("preferred_topics", ["python_basics"])),
                learning_goals=list(profile_data.get("learning_goals", [])),
            ),
        )

        if "programming_level" in profile_data:
            profile.programming_level = str(profile_data["programming_level"])
        if "learning_style" in profile_data:
            profile.learning_style = str(profile_data["learning_style"])
        if "learning_goals" in profile_data:
            profile.learning_goals = [
                str(goal)
                for goal in profile_data.get("learning_goals", [])
                if str(goal).strip()
            ]

        topic = profile_data.get("topic") or self._infer_topic(profile_data.get("content", ""))
        is_correct = self._infer_correctness(profile_data)
        if topic:
            profile.update_mastery(topic, is_correct, str(profile_data.get("difficulty", "beginner")))
            if topic not in profile.preferred_topics:
                profile.preferred_topics.append(topic)

        profile.updated_at = datetime.now()

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        profile = self.user_profiles.get(user_id)
        if profile is None:
            return {
                "user_id": user_id,
                "learning_style": "visual",
                "programming_level": "beginner",
                "preferred_topics": ["python_basics"],
                "knowledge_mastery": {},
                "weak_topics": [],
                "learning_goals": [],
            }

        return {
            "user_id": profile.user_id,
            "learning_style": profile.learning_style,
            "programming_level": profile.programming_level,
            "preferred_topics": profile.preferred_topics,
            "knowledge_mastery": {
                topic: mastery.mastery_level for topic, mastery in profile.knowledge_mastery.items()
            },
            "weak_topics": profile.get_weak_topics(),
            "learning_goals": profile.learning_goals,
            "updated_at": profile.updated_at.isoformat(),
        }

    def _infer_correctness(self, profile_data: Dict[str, Any]) -> bool:
        if "correct" in profile_data:
            return bool(profile_data["correct"])
        score = profile_data.get("score")
        if isinstance(score, (int, float)):
            return score >= 0.6
        content = str(profile_data.get("content", "")).lower()
        return not any(token in content for token in ["error", "bug", "wrong", "失败", "错误"])

    def _infer_topic(self, content: str) -> str:
        lowered = str(content).lower()
        mapping = {
            "list": "data_structures",
            "dict": "data_structures",
            "class": "oop",
            "object": "oop",
            "sort": "algorithms",
            "递归": "algorithms",
            "函数": "python_basics",
            "loop": "python_basics",
            "async": "advanced_python",
        }
        for keyword, topic in mapping.items():
            if keyword in lowered:
                return topic
        return "python_basics"


class PersonalizedSuggestionAgent:
    """Generates lightweight suggestions from the current profile."""

    async def generate_personalized_suggestion(self, user_profile: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        weak_topics = user_profile.get("weak_topics", [])
        if weak_topics:
            suggestions.append(f"建议优先复习这些薄弱主题：{', '.join(weak_topics[:3])}。")
            suggestions.append(f"可以先做 2 到 3 道与 {weak_topics[0]} 相关的基础练习。")

        learning_style = user_profile.get("learning_style", "visual")
        if learning_style == "visual":
            suggestions.append("你更适合图示化和带例子的讲解方式。")
        elif learning_style == "kinesthetic":
            suggestions.append("你更适合边学边写，建议每学一个点就立刻做小练习。")
        else:
            suggestions.append("建议把概念总结成自己的笔记，再配合少量练习巩固。")

        preferred_topics = user_profile.get("preferred_topics", [])
        if preferred_topics:
            suggestions.append(f"接下来可以围绕 {preferred_topics[0]} 做一次针对性提升。")

        prompt = (
            "请基于以下用户画像，补充 2 条简洁、可执行的编程学习建议。"
            f"\n用户画像: {user_profile}"
        )
        llm_response = await llm_client.generate_response(
            system_prompt="你是编程学习教练。",
            user_message=prompt,
            use_cache=False,
        )
        if llm_response and "目前无法调用大模型" not in llm_response:
            suggestions.append(f"AI建议：{llm_response.strip()}")

        deduped: List[str] = []
        for item in suggestions:
            if item not in deduped:
                deduped.append(item)
        return deduped[:5]


class LearningPathGenerationAgent:
    """Builds a simple staged learning path."""

    def __init__(self) -> None:
        self.base_paths = {
            "beginner": [
                "Python 基础语法",
                "条件与循环",
                "函数",
                "常用数据结构",
                "基础调试",
            ],
            "intermediate": [
                "函数式拆分",
                "面向对象",
                "文件与模块",
                "常用算法",
                "项目实践",
            ],
            "advanced": [
                "异步编程",
                "性能优化",
                "工程化结构",
                "测试设计",
                "复杂项目实践",
            ],
        }

    async def generate_learning_path(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        level = str(user_profile.get("programming_level", "beginner"))
        weak_topics = list(user_profile.get("weak_topics", []))
        preferred_topics = list(user_profile.get("preferred_topics", []))
        path = list(self.base_paths.get(level, self.base_paths["beginner"]))

        for topic in weak_topics[:2]:
            path.insert(0, f"专项补强：{topic}")
        if preferred_topics:
            path.append(f"扩展实践：{preferred_topics[0]}")

        return {
            "level": level,
            "path": path,
            "estimated_duration": f"{max(2, len(path) * 2)} 小时",
            "focus_areas": weak_topics[:3] or preferred_topics[:2] or ["python_basics"],
        }


class PersonalizedLearningAgent(BaseAgent):
    """High-level personalized learning agent."""

    def __init__(self) -> None:
        super().__init__("PersonalizedLearningAgent")
        self.tracking_agent = UserBehaviorTrackingAgent()
        self.cognition_agent = UserCognitionUpdateAgent()
        self.suggestion_agent = PersonalizedSuggestionAgent()
        self.path_agent = LearningPathGenerationAgent()

    async def track_user_behavior(self, behavior_data: Dict[str, Any]) -> None:
        user_id = behavior_data["user_id"]
        await self.tracking_agent.track_behavior(user_id, behavior_data)
        await self.cognition_agent.update_user_profile(user_id, behavior_data)

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        await self.cognition_agent.update_user_profile(user_id, profile_data)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        return await self.cognition_agent.get_user_profile(user_id)

    async def generate_personalized_suggestion(self, user_id: str) -> List[str]:
        user_profile = await self.get_user_profile(user_id)
        return await self.suggestion_agent.generate_personalized_suggestion(user_profile)

    async def generate_learning_path(self, user_id: str) -> Dict[str, Any]:
        user_profile = await self.get_user_profile(user_id)
        return await self.path_agent.generate_learning_path(user_profile)

    async def get_learning_summary(self, user_id: str) -> Dict[str, Any]:
        profile = await self.get_user_profile(user_id)
        behaviors = await self.tracking_agent.get_user_behaviors(user_id)
        intent_counter = Counter(item.get("intent", "unknown") for item in behaviors)
        return {
            "profile": profile,
            "recent_behavior_count": len(behaviors),
            "common_intents": intent_counter.most_common(3),
        }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        user_id = request["user_id"]
        content = str(request.get("content", ""))
        lowered = content.lower()
        self.log_activity("processing personalized request", {"user_id": user_id})

        if any(keyword in lowered for keyword in ["path", "路线", "路径"]):
            learning_path = await self.generate_learning_path(user_id)
            path_text = "\n".join(f"{index + 1}. {item}" for index, item in enumerate(learning_path["path"]))
            return {
                "success": True,
                "response": (
                    f"个性化学习路径\n当前水平：{learning_path['level']}\n"
                    f"预计投入：{learning_path['estimated_duration']}\n{path_text}"
                ),
                "details": {"learning_path": learning_path},
            }

        if any(keyword in lowered for keyword in ["profile", "画像"]):
            user_profile = await self.get_user_profile(user_id)
            return {
                "success": True,
                "response": (
                    f"学习画像\n学习风格：{user_profile['learning_style']}\n"
                    f"当前水平：{user_profile['programming_level']}\n"
                    f"薄弱主题：{', '.join(user_profile['weak_topics']) or '暂无明显薄弱点'}"
                ),
                "details": {"user_profile": user_profile},
            }

        suggestions = await self.generate_personalized_suggestion(user_id)
        suggestion_text = "\n".join(f"- {item}" for item in suggestions)
        return {
            "success": True,
            "response": f"个性化学习建议\n{suggestion_text}",
            "details": {"suggestions": suggestions},
        }
