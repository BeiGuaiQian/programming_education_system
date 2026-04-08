"""Main routing agent for the programming education system."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.agents.evaluation_agent import AnswerEvaluationAgent
from programming_education_system.agents.exercise_agent import EnhancedExerciseGenerationAgent
from programming_education_system.agents.personal_agent import PersonalizedLearningAgent
from programming_education_system.agents.qa_agent import QAAgent

logger = logging.getLogger(__name__)


class MainAgent(BaseAgent):
    """Enhances requests, detects intent, and dispatches work."""

    def __init__(
        self,
        qa_agent: QAAgent,
        exercise_agent: EnhancedExerciseGenerationAgent,
        evaluation_agent: AnswerEvaluationAgent,
        personal_agent: PersonalizedLearningAgent,
    ):
        super().__init__("MainAgent")
        self.qa_agent = qa_agent
        self.exercise_agent = exercise_agent
        self.evaluation_agent = evaluation_agent
        self.personal_agent = personal_agent
        self.llm_client = None

    def _get_llm_client(self):
        if self.llm_client is None:
            from programming_education_system.utils.llm_utils import llm_client

            self.llm_client = llm_client
        return self.llm_client

    async def enhance_request_with_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        original_content = request["content"]
        context = request.get("context", {})
        if not context.get("recent_history") or len(original_content.strip()) > 50:
            return {
                **request,
                "enhancement_info": {
                    "was_enhanced": False,
                    "context_used": False,
                    "original_content": original_content,
                },
            }

        try:
            system_prompt = (
                "You are a context understanding assistant. Expand the user's short input using the "
                "recent conversation only when necessary, and return only the rewritten request."
            )
            history_context = "\n".join(
                [
                    f"- User: {history.get('user_input', '')}\n- Assistant: {str(history.get('agent_response', ''))[:100]}"
                    for history in context.get("recent_history", [])[-3:]
                ]
            )
            user_message = (
                f"Current input: {original_content}\n\nRecent conversation:\n{history_context}\n\n"
                "If the input is already clear, return it unchanged."
            )
            llm_client = self._get_llm_client()
            enhanced_content = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=True,
            )
            if enhanced_content and len(enhanced_content.strip()) > len(original_content.strip()):
                return {
                    **request,
                    "content": enhanced_content.strip(),
                    "original_content": original_content,
                    "enhancement_info": {
                        "was_enhanced": True,
                        "context_used": True,
                        "original_content": original_content,
                        "enhancement_reason": "based_on_recent_history",
                    },
                }
        except Exception as exc:
            logger.warning("Request enhancement failed: %s", exc)

        return {
            **request,
            "enhancement_info": {
                "was_enhanced": False,
                "context_used": False,
                "original_content": original_content,
            },
        }

    async def analyze_intent_with_context(self, content: str, context: Dict[str, Any]) -> str:
        system_prompt = (
            "You are an intent analysis assistant. Return JSON only, in the form "
            '{"intent": "qa|exercise|evaluation|personal", "confidence": 0.0, "reason": "..."}'
        )
        context_info = ""
        if context.get("recent_history"):
            history_lines = []
            for index, history in enumerate(context["recent_history"][-10:], start=1):
                history_lines.append(f"{index}. User: {history.get('user_input', '')}")
                history_lines.append(f"   Assistant: {history.get('agent_response', '')}")
            context_info = "\n".join(history_lines)

        user_message = f"Current input: {content}\n\nRecent conversation:\n{context_info}"
        try:
            llm_client = self._get_llm_client()
            response = await llm_client.generate_response(system_prompt, user_message, use_cache=False)
            intent_data = self._parse_llm_response(response)
            if intent_data and intent_data.get("intent"):
                return intent_data["intent"]
        except Exception as exc:
            logger.error("Intent analysis failed: %s", exc)
        return await self._fallback_intent_analysis(content)

    async def analyze_intent(self, request: Dict[str, Any]) -> str:
        content = request["content"].strip()
        request_type = request.get("type", "auto")
        context = request.get("context", {})
        if request_type != "auto" and request_type in {"qa", "exercise", "evaluation", "personal"}:
            return request_type
        return await self.analyze_intent_with_context(content, context)

    async def dispatch_to_sub_agent(self, intent: str, request: Dict[str, Any]) -> Dict[str, Any]:
        agents = {
            "qa": self.qa_agent,
            "exercise": self.exercise_agent,
            "evaluation": self.evaluation_agent,
            "personal": self.personal_agent,
        }
        target_agent = agents.get(intent, self.qa_agent)
        request.setdefault("context", {})
        result = await target_agent.process(request)
        result["detected_intent"] = intent
        result["enhancement_applied"] = request.get("enhancement_info", {}).get("was_enhanced", False)
        result["context_used"] = request.get("enhancement_info", {}).get("context_used", False)
        result["enhancement_info"] = request.get("enhancement_info", {})
        result["target_exercise"] = request.get("target_exercise")
        if request.get("enhancement_info", {}).get("was_enhanced", False):
            result["original_content"] = request.get("enhancement_info", {}).get(
                "original_content", request["content"]
            )
        return result

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        enhanced_request = await self.enhance_request_with_context(request)
        intent = await self.analyze_intent(enhanced_request)
        result = await self.dispatch_to_sub_agent(intent, enhanced_request)
        behavior_data = {
            "user_id": enhanced_request["user_id"],
            "intent": intent,
            "content": enhanced_request["content"],
            "original_content": enhanced_request.get("original_content", enhanced_request["content"]),
            "was_enhanced": enhanced_request.get("enhancement_info", {}).get("was_enhanced", False),
            "context_used": enhanced_request.get("enhancement_info", {}).get("context_used", False),
            "timestamp": enhanced_request.get("timestamp", "unknown"),
        }
        await self.personal_agent.track_user_behavior(behavior_data)
        return result

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        response_lower = response.lower()
        for intent in ("qa", "exercise", "evaluation", "personal"):
            if f'"intent": "{intent}"' in response_lower or f"'intent': '{intent}'" in response_lower:
                return {"intent": intent, "confidence": 0.7, "reason": "extracted_from_text"}
        return {}

    async def _fallback_intent_analysis(self, content: str) -> str:
        content_lower = content.lower()
        exercise_keywords = ["练习", "题目", "作业", "exercise", "problem", "生成练习", "出一道题"]
        evaluation_keywords = ["评价", "检查", "review", "evaluate", "代码", "运行结果", "测试代码"]
        personal_keywords = ["建议", "推荐", "学习路径", "suggestion", "advice", "规划"]
        has_code = "def " in content or "import " in content or ("=" in content and ":" in content)
        if any(keyword in content_lower for keyword in evaluation_keywords) or has_code:
            return "evaluation"
        if any(keyword in content_lower for keyword in exercise_keywords):
            return "exercise"
        if any(keyword in content_lower for keyword in personal_keywords):
            return "personal"
        return "qa"
