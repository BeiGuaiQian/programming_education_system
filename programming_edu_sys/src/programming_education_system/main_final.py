"""System orchestration for the programming education platform."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any, Dict

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from programming_education_system.agents.evaluation_agent import AnswerEvaluationAgent
from programming_education_system.agents.exercise_agent import (
    EnhancedExerciseGenerationAgent as ExerciseGenerationAgent,
)
from programming_education_system.agents.main_agent import MainAgent
from programming_education_system.agents.personal_agent import PersonalizedLearningAgent
from programming_education_system.agents.qa_agent import QAAgent
from programming_education_system.agents.user_agent import EnhancedUserAgent as UserAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class ProgrammingEducationSystem:
    """Coordinates agents, context, and personalized learning profiles."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("ProgrammingEducationSystem")
        from programming_education_system.config.llm_config import Config

        if not Config.validate_config():
            self.logger.warning("系统配置验证失败，某些功能可能受限")

        self.user_contexts: Dict[str, Dict[str, Any]] = {}
        self.initialize_agents()

    def initialize_agents(self) -> None:
        self.logger.info("初始化智能体...")
        self.personal_agent = PersonalizedLearningAgent()
        self.qa_agent = QAAgent(personal_agent=self.personal_agent)
        self.exercise_agent = ExerciseGenerationAgent(personal_agent=self.personal_agent)
        self.evaluation_agent = AnswerEvaluationAgent(personal_agent=self.personal_agent)
        self.main_agent = MainAgent(
            self.qa_agent,
            self.exercise_agent,
            self.evaluation_agent,
            self.personal_agent,
        )
        self.user_agent = UserAgent(self.main_agent)
        self.logger.info("所有智能体初始化完成")

    def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                "user_id": user_id,
                "recent_history": [],
                "learning_goals": [],
                "preferred_difficulty": "medium",
                "external_learning_context": {},
                "last_interaction_time": asyncio.get_event_loop().time(),
            }
        return self.user_contexts[user_id]

    def update_external_learning_context(self, user_id: str, external_context: Dict[str, Any] | None) -> None:
        if not external_context:
            return
        context = self._get_user_context(user_id)
        context["external_learning_context"] = external_context
        if isinstance(external_context.get("recent_history"), list):
            context["recent_history"] = external_context["recent_history"][-40:]
        if external_context.get("conversation_id"):
            context["conversation_id"] = str(external_context["conversation_id"])
        profile = external_context.get("profile", {})
        learning_goal = profile.get("learning_goal")
        if learning_goal:
            context["learning_goals"] = [learning_goal]

    async def sync_external_profile(
        self,
        user_id: str,
        content: str,
        external_context: Dict[str, Any] | None,
    ) -> None:
        """Feed persisted learning signals into the personalized profile before routing."""
        external_context = external_context or {}
        profile = external_context.get("profile") or {}
        level = external_context.get("level") or {}
        behavior = external_context.get("behavior") or {}
        progress = external_context.get("progress") or {}
        question_progress = external_context.get("question_progress") or {}
        learning_signals = external_context.get("learning_signals") or behavior.get("learning_signals") or {}
        if not any([profile, level, behavior, progress, question_progress, learning_signals]):
            return

        await self.personal_agent.update_user_profile(
            user_id,
            {
                "learning_style": profile.get("learning_style") or "balanced",
                "learning_goals": [profile.get("learning_goal")] if profile.get("learning_goal") else [],
                "programming_level": level.get("name") or "beginner",
                "content": content,
                "lesson_progress": progress,
                "question_progress": question_progress,
                "learning_behavior": behavior,
                "real_learning_signals": learning_signals,
                "skip_mastery_update": True,
            },
        )

    def _update_user_context(self, user_id: str, user_input: str, agent_response: str) -> None:
        context = self._get_user_context(user_id)
        context["recent_history"].append(
            {
                "user_input": user_input,
                "agent_response": agent_response,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )
        context["recent_history"] = context["recent_history"][-10:]
        context["last_interaction_time"] = asyncio.get_event_loop().time()

    async def process_user_request(
        self,
        request_type: str,
        content: str,
        user_id: str = "user_001",
        external_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self.logger.info("处理用户请求 - 类型: %s, 用户: %s", request_type, user_id)
        try:
            context = self._get_user_context(user_id)
            self.update_external_learning_context(user_id, external_context)
            await self.sync_external_profile(
                user_id,
                content,
                context.get("external_learning_context", {}),
            )

            result = await self.user_agent.receive_user_request(
                request_type="auto" if request_type == "auto" else request_type,
                content=content,
                user_id=user_id,
                context=context,
            )
            final_result = await self.user_agent.collect_and_return_results(result)

            self._update_user_context(user_id, content, final_result.get("response", ""))
            return final_result
        except Exception as exc:
            self.logger.error("处理用户请求时出错: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "user_id": user_id,
                "response": "系统处理请求时出现错误。",
            }

    async def get_system_status(self) -> Dict[str, Any]:
        active_users = len(self.user_contexts)
        return {
            "system": "running",
            "profile_framework": "personalized_learning_agent",
            "agents_initialized": True,
            "active_users": active_users,
            "user_contexts_stored": active_users,
            "timestamp": asyncio.get_event_loop().time(),
        }

    async def get_user_profile_report(self, user_id: str) -> Dict[str, Any]:
        """Return the personalized profile report for the current user."""
        try:
            user_profile = await self.personal_agent.get_user_profile(user_id)
            user_context = self._get_user_context(user_id)
            return {
                "user_id": user_id,
                "profile_source": "personalized_learning_agent",
                "user_profile": user_profile,
                "interaction_history": {
                    "total_interactions": len(user_context.get("recent_history", [])),
                    "recent_activity": user_context.get("last_interaction_time", 0),
                },
                "report_generated_at": asyncio.get_event_loop().time(),
            }
        except Exception as exc:
            self.logger.error("获取用户画像报告失败: %s", exc)
            return {"error": str(exc)}

    async def clear_user_context(self, user_id: str) -> None:
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
            self.logger.info("已清除用户 %s 的上下文", user_id)

    async def get_user_context_summary(self, user_id: str) -> Dict[str, Any]:
        context = self._get_user_context(user_id)
        return {
            "user_id": user_id,
            "history_length": len(context.get("recent_history", [])),
            "last_interaction": context.get("last_interaction_time", 0),
            "learning_goals": context.get("learning_goals", []),
            "preferred_difficulty": context.get("preferred_difficulty", "medium"),
        }


_system_instance: ProgrammingEducationSystem | None = None


def get_system() -> ProgrammingEducationSystem:
    global _system_instance
    if _system_instance is None:
        _system_instance = ProgrammingEducationSystem()
    return _system_instance


async def demo() -> None:
    system = get_system()
    user_id = "student_001"

    print("=" * 60)
    print("编程教育智能体系统演示")
    print("=" * 60)

    result1 = await system.process_user_request("qa", "Python 中什么是函数？", user_id)
    print(f"问答示例: {result1['response'][:120]}")

    result2 = await system.process_user_request("qa", "参数有哪些类型？", user_id)
    print(f"上下文追问: {result2['response'][:120]}")
    print(f"是否使用上下文: {result2.get('context_used', False)}")

    result3 = await system.process_user_request("exercise", "生成一个 Python 列表练习", user_id)
    print(f"练习示例: {result3['response'][:120]}")

    context_summary = await system.get_user_context_summary(user_id)
    print(f"上下文历史条数: {context_summary['history_length']}")

    profile_report = await system.get_user_profile_report(user_id)
    print(f"用户画像字段: {list(profile_report.keys())}")


if __name__ == "__main__":
    asyncio.run(demo())
