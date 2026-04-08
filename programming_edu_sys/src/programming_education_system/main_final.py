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
from programming_education_system.cognition_judger.cognitive_api_scientific import (
    get_scientific_cognitive_api_sync,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class ProgrammingEducationSystem:
    """Coordinates agents, context, and cognition tracking."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("System-Scientific")
        from programming_education_system.config.llm_config import Config

        if not Config.validate_config():
            self.logger.warning("系统配置验证失败，某些功能可能受限")

        self.cognition_api = get_scientific_cognitive_api_sync()
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
                "last_interaction_time": asyncio.get_event_loop().time(),
            }
        return self.user_contexts[user_id]

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
        self, request_type: str, content: str, user_id: str = "user_001"
    ) -> Dict[str, Any]:
        self.logger.info("处理用户请求 - 类型: %s, 用户: %s", request_type, user_id)
        try:
            start_time = asyncio.get_event_loop().time()
            _ = self._get_user_context(user_id)

            result = await self.user_agent.receive_user_request(
                request_type="auto" if request_type == "auto" else request_type,
                content=content,
                user_id=user_id,
            )
            final_result = await self.user_agent.collect_and_return_results(result)
            processing_time = asyncio.get_event_loop().time() - start_time

            self._update_user_context(user_id, content, final_result.get("response", ""))

            effective_type = final_result.get("request_type") or request_type
            if effective_type in (None, "unknown", "auto"):
                effective_type = request_type if request_type != "auto" else final_result.get("details", {}).get("source", "qa")

            await self._record_scientific_cognitive_data(
                user_id,
                str(effective_type),
                content,
                final_result,
                processing_time,
            )
            return await self._enhance_with_scientific_cognition(
                user_id,
                final_result,
                str(effective_type),
                content,
            )
        except Exception as exc:
            self.logger.error("处理用户请求时出错: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "user_id": user_id,
                "response": "系统处理请求时出现错误。",
            }

    async def _record_scientific_cognitive_data(
        self,
        user_id: str,
        request_type: str,
        original_content: str,
        result: Dict[str, Any],
        processing_time: float,
    ) -> None:
        try:
            details = result.get("details") or {}
            interaction_data = {
                "type": request_type,
                "content": original_content,
                "user_response": result.get("response", ""),
                "processing_time": processing_time,
                "context": f"request_type={request_type}; topic={details.get('topic', 'general')}",
                "metadata": {
                    "code_quality": result.get("code_quality", 0.5),
                    "explanation_quality": result.get("explanation_quality", 0.5),
                    "response_length": len(result.get("response", "")),
                    "success": result.get("success", True),
                    "interaction_type": request_type,
                    "detected_intent": request_type,
                    "topic": details.get("topic", "general"),
                    "source": details.get("source"),
                    "complexity": self._estimate_complexity(result, original_content),
                    "context_used": result.get("context_used", False),
                    "enhancement_applied": result.get("enhancement_applied", False),
                    "processing_info": result.get("processing_info", {}),
                },
            }
            analysis_result = await self.cognition_api.analyze_learning_interaction(user_id, interaction_data)
            if analysis_result.get("success"):
                self.logger.info("科学认知分析完成 - 用户: %s", user_id)
        except Exception as exc:
            self.logger.warning("记录科学认知数据失败: %s", exc)

    async def _enhance_with_scientific_cognition(
        self,
        user_id: str,
        result: Dict[str, Any],
        request_type: str,
        original_content: str,
    ) -> Dict[str, Any]:
        try:
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
            learning_context = self._map_learning_context(request_type, original_content)
            learning_params = await self.cognition_api.get_personalized_learning_parameters(
                user_id,
                learning_context,
            )
            progression_analysis = await self.cognition_api.get_learning_progression_analysis(user_id)
            strengths_weaknesses = await self.cognition_api.get_cognitive_strengths_weaknesses(user_id)
            learning_goal = self._infer_learning_goal(original_content, request_type)
            learning_recommendations = await self.cognition_api.get_learning_recommendations(
                user_id,
                learning_goal,
            )

            result.setdefault("cognitive_insights", {})
            result["cognitive_insights"].update(
                {
                    "user_cognitive_state": cognitive_state,
                    "learning_parameters": learning_params,
                    "progression_analysis": progression_analysis,
                    "strengths_weaknesses": strengths_weaknesses,
                    "learning_recommendations": learning_recommendations,
                    "scientific_analysis_timestamp": cognitive_state.get("last_updated", ""),
                }
            )

            params = learning_params.get("parameters", {})
            result["scientifically_guided_response"] = self._apply_scientific_guidance(
                result.get("response", ""),
                params,
                cognitive_state,
            )
            self.logger.info(
                "科学认知增强完成 - 用户: %s, 认知水平: %.3f",
                user_id,
                cognitive_state.get("overall_cognitive_level", 0.5),
            )
        except Exception as exc:
            self.logger.warning("集成科学认知数据失败: %s", exc)
        return result

    def _infer_learning_goal(self, content: str, request_type: str) -> str:
        lowered = content.lower()
        if "function" in lowered or "函数" in content:
            return "掌握函数编程"
        if "class" in lowered or "对象" in content or "类" in content:
            return "理解面向对象编程"
        if "algorithm" in lowered or "算法" in content:
            return "学习算法设计"
        if "data structure" in lowered or "数据结构" in content:
            return "掌握数据结构"
        if request_type == "exercise":
            return "提高编程实践能力"
        if "debug" in lowered or "错误" in content:
            return "提升调试和排错能力"
        return "提高编程能力"

    def _map_learning_context(self, request_type: str, content: str) -> str:
        lowered = content.lower()
        if request_type == "qa":
            if any(token in lowered for token in ["what is", "是什么", "基础", "入门"]):
                return "new_concept"
            if any(token in lowered for token in ["how", "如何", "怎么"]):
                return "skill_application"
            return "conceptual_understanding"
        if request_type == "exercise":
            return "practice"
        if request_type == "evaluation":
            return "feedback"
        return "general"

    def _apply_scientific_guidance(
        self,
        original_response: str,
        params: Dict[str, Any],
        cognitive_state: Dict[str, Any],
    ) -> str:
        guided_response = original_response
        explanation_depth = float(params.get("explanation_depth", 0.7))
        if explanation_depth < 0.4 and len(guided_response) > 300:
            sentences = [segment.strip() for segment in guided_response.split("。") if segment.strip()]
            guided_response = "。".join(sentences[:3]) + ("。" if sentences else "")

        hint_strategy = params.get("hint_strategy", "balanced")
        if hint_strategy == "guided":
            guided_response += "\n\n提示：如果你希望我把这一步拆得更细，我可以继续展开。"
        elif hint_strategy == "balanced":
            guided_response += "\n\n有任何卡住的地方都可以继续追问我。"

        cognitive_level = float(cognitive_state.get("overall_cognitive_level", 0.5))
        if cognitive_level > 0.7:
            guided_response += "\n\n你已经可以尝试更复杂一些的变体题了。"
        elif cognitive_level < 0.4:
            guided_response += "\n\n先把基础概念吃透就很好，慢一点也没关系。"
        return guided_response

    def _estimate_complexity(self, result: Dict[str, Any], original_content: str) -> float:
        complexity = 0.5
        response = result.get("response", "")
        if len(response) > 500:
            complexity += 0.2
        elif len(response) < 100:
            complexity -= 0.1

        complex_keywords = ["继承", "多态", "递归", "算法", "复杂度", "设计模式", "架构", "异步", "并发"]
        if any(keyword in original_content for keyword in complex_keywords):
            complexity += 0.3
        return max(0.1, min(1.0, complexity))

    async def get_system_status(self) -> Dict[str, Any]:
        active_users = len(self.user_contexts)
        return {
            "system": "running",
            "cognitive_framework": "scientific_cognitive_api",
            "agents_initialized": True,
            "active_users": active_users,
            "user_contexts_stored": active_users,
            "timestamp": asyncio.get_event_loop().time(),
        }

    async def get_user_cognitive_report(self, user_id: str) -> Dict[str, Any]:
        try:
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
            progression_analysis = await self.cognition_api.get_learning_progression_analysis(user_id)
            strengths_weaknesses = await self.cognition_api.get_cognitive_strengths_weaknesses(user_id)
            user_context = self._get_user_context(user_id)
            return {
                "user_id": user_id,
                "cognitive_state": cognitive_state,
                "progression_analysis": progression_analysis,
                "strengths_weaknesses": strengths_weaknesses,
                "interaction_history": {
                    "total_interactions": len(user_context.get("recent_history", [])),
                    "recent_activity": user_context.get("last_interaction_time", 0),
                },
                "report_generated_at": asyncio.get_event_loop().time(),
            }
        except Exception as exc:
            self.logger.error("获取用户认知报告失败: %s", exc)
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

    cognitive_report = await system.get_user_cognitive_report(user_id)
    print(f"认知状态字段: {list(cognitive_report.keys())}")


if __name__ == "__main__":
    asyncio.run(demo())
