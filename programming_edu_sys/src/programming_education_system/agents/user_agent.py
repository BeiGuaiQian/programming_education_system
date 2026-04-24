"""User-facing agent responsible for context-aware request preparation."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.utils.context_manager import context_manager
from programming_education_system.utils.validation import (
    ValidationError,
    validate_and_sanitize_request,
)

logger = logging.getLogger(__name__)


class SimpleContextAnalyzer:
    """Builds a compact prompt from recent history for LLM-based context analysis."""

    def __init__(self):
        self.max_history_analysis = 20

    def analyze_context(self, user_id: str, current_input: str) -> Dict[str, Any]:
        try:
            history = context_manager.get_dialog_history(user_id, limit=self.max_history_analysis)
            analysis_prompt = self._build_analysis_prompt(current_input, history)
            return {
                "success": True,
                "history_count": len(history),
                "analysis_prompt": analysis_prompt,
                "raw_history": history,
            }
        except Exception as exc:
            logger.error("Context analysis failed: %s", exc)
            return {"success": False, "error": str(exc), "history_count": 0, "raw_history": []}

    def _build_analysis_prompt(self, current_input: str, history: List[Dict[str, Any]]) -> str:
        history_lines = ["对话历史:"]
        for index, dialog in enumerate(history[-10:], start=1):
            user_msg = str(dialog.get("user_input", ""))[:500]
            agent_msg = str(dialog.get("agent_response", ""))[:500]
            history_lines.append(f"{index}. 用户: {user_msg}")
            if agent_msg:
                history_lines.append(f"   助手: {agent_msg}")

        history_text = "\n".join(history_lines)
        return f"""请根据下面的对话历史分析用户当前输入，并仅返回 JSON：
{history_text}

当前输入: {current_input}

JSON 格式:
{{
  "user_intent": "exercise|answer|explanation|concept|example|general",
  "needs_context": true,
  "key_points": ["关键点1"],
  "exercise_reference": {{
    "has_exercise": false,
    "exercise_content": "",
    "exercise_topic": ""
  }},
  "suggested_enhancement": "如果需要补全上下文，这里给出更完整的用户请求"
}}"""


class EnhancedUserAgent(BaseAgent):
    """Preprocess user requests before handing them to MainAgent."""

    def __init__(self, main_agent):
        super().__init__("EnhancedUserAgent")
        self.main_agent = main_agent
        self.current_user_id = None
        self.llm_client = None
        self.context_analyzer = SimpleContextAnalyzer()

    def _get_llm_client(self):
        if self.llm_client is None:
            from programming_education_system.utils.llm_utils import llm_client

            self.llm_client = llm_client
        return self.llm_client

    async def enhance_user_input_with_context(self, content: str, user_id: str) -> Dict[str, Any]:
        try:
            context_analysis = self.context_analyzer.analyze_context(user_id, content)
            if not context_analysis["success"]:
                return await self._fallback_enhancement(content, user_id)

            llm_client = self._get_llm_client()
            system_prompt = (
                "你是对话分析助手。严格按用户消息要求输出一个 JSON 对象，不要输出 markdown 或解释。"
            )
            analysis_response = await llm_client.generate_response(
                system_prompt,
                context_analysis["analysis_prompt"],
                use_cache=False,
            )
            analysis_result = self._parse_analysis_result(analysis_response)
            enhanced_content = self._build_enhanced_input(content, analysis_result)

            return {
                "original_content": content,
                "enhanced_content": enhanced_content,
                "was_enhanced": enhanced_content != content,
                "context_analysis": {
                    "success": True,
                    "llm_analysis": analysis_result,
                    "history_count": context_analysis["history_count"],
                },
                "analysis_confidence": 0.8,
                "target_exercise": analysis_result.get("exercise_reference"),
            }
        except Exception as exc:
            logger.error("Enhancing user input failed: %s", exc)
            return await self._fallback_enhancement(content, user_id)

    def _parse_analysis_result(self, analysis_response: str) -> Dict[str, Any]:
        cleaned_response = analysis_response.strip()
        try:
            if cleaned_response.startswith("{"):
                return json.loads(cleaned_response)
            match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse analysis result: %s", exc)

        return {
            "user_intent": "general",
            "needs_context": False,
            "key_points": [],
            "exercise_reference": {
                "has_exercise": False,
                "exercise_content": "",
                "exercise_topic": "",
            },
            "suggested_enhancement": "",
        }

    def _build_enhanced_input(self, original_input: str, analysis_result: Dict[str, Any]) -> str:
        user_intent = analysis_result.get("user_intent", "general")
        needs_context = analysis_result.get("needs_context", False)
        key_points = [str(point) for point in analysis_result.get("key_points", [])[:3]]
        exercise_ref = analysis_result.get("exercise_reference", {}) or {}
        suggested_enhancement = str(analysis_result.get("suggested_enhancement", "")).strip()

        if user_intent == "answer" and exercise_ref.get("has_exercise"):
            return self._build_exercise_answer_request(original_input, exercise_ref)
        if needs_context and key_points:
            return self._build_context_aware_request(original_input, key_points)
        if suggested_enhancement and suggested_enhancement != original_input:
            return suggested_enhancement
        return original_input

    def _build_exercise_answer_request(self, original_input: str, exercise_ref: Dict[str, Any]) -> str:
        exercise_content = str(exercise_ref.get("exercise_content", "")).strip()
        exercise_topic = str(exercise_ref.get("exercise_topic", "")).strip()
        if not exercise_content:
            return original_input
        return (
            f"用户请求: {original_input}\n\n"
            f"需要解答的题目主题: {exercise_topic or 'unknown'}\n"
            f"题目内容: {exercise_content}\n\n"
            "请针对该题目提供完整、清晰的解答。"
        )

    def _build_context_aware_request(self, original_input: str, key_points: List[str]) -> str:
        context_summary = "\n".join(f"- {point}" for point in key_points)
        return (
            f"用户请求: {original_input}\n\n"
            f"相关上下文:\n{context_summary}\n\n"
            "请结合这些上下文回答用户。"
        )

    async def _fallback_enhancement(self, content: str, user_id: str) -> Dict[str, Any]:
        try:
            dialog_history = context_manager.get_dialog_history(user_id, limit=5)
            system_prompt = "请根据最近对话帮助补全用户输入；如果无需补全，原样返回。"
            user_message = f"用户输入: {content}\n"
            if dialog_history:
                user_message += "\n最近对话:\n"
                for index, history in enumerate(dialog_history[-3:], start=1):
                    user_message += f"{index}. 用户: {history.get('user_input', '')}\n"
                    user_message += f"   助手: {str(history.get('agent_response', ''))[:100]}\n"
            llm_client = self._get_llm_client()
            response = await llm_client.generate_response(system_prompt, user_message)
            enhanced_content = response.strip() if response and response.strip() else content
            return {
                "original_content": content,
                "enhanced_content": enhanced_content,
                "was_enhanced": enhanced_content != content,
                "context_analysis": {"success": False, "error": "fallback_used"},
                "analysis_confidence": 0.3,
                "target_exercise": None,
            }
        except Exception as exc:
            logger.error("Fallback enhancement failed: %s", exc)
            return {
                "original_content": content,
                "enhanced_content": content,
                "was_enhanced": False,
                "context_analysis": {"success": False, "error": str(exc)},
                "analysis_confidence": 0.1,
                "target_exercise": None,
            }

    def _plain_enhancement(self, content: str) -> Dict[str, Any]:
        return {
            "original_content": content,
            "enhanced_content": content,
            "was_enhanced": False,
            "context_analysis": {"success": True, "skipped": True, "reason": "fast_path"},
            "analysis_confidence": 1.0,
            "target_exercise": None,
        }

    def _should_enhance_user_input(self, request_type: str, content: str, user_id: str) -> bool:
        if len(content.strip()) > 1200:
            return False
        history = context_manager.get_dialog_history(user_id, limit=3)
        if not history:
            return False
        if request_type != "auto" and len(content.strip()) > 12:
            return False
        return len(content.strip()) <= 120

    async def receive_user_request(
        self,
        request_type: str,
        content: str,
        user_id: str,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Validate, enhance, and forward a request to the main agent."""
        try:
            safe_request = validate_and_sanitize_request(
                {"type": request_type, "content": content, "user_id": user_id}
            )
        except ValidationError as exc:
            return {
                "success": False,
                "error": str(exc),
                "response": str(exc),
                "details": {},
                "detected_intent": "unknown",
            }

        request_type = safe_request["type"]
        content = safe_request["content"]
        user_id = safe_request["user_id"]
        self.current_user_id = user_id

        original_preview = content[:50] + "..." if len(content) > 50 else content
        self.log_activity(
            "接收用户原始请求",
            {
                "user_id": user_id,
                "request_type": request_type,
                "original_content": original_preview,
            },
        )

        if self._should_enhance_user_input(request_type, content, user_id):
            enhancement_result = await self.enhance_user_input_with_context(content, user_id)
        else:
            enhancement_result = self._plain_enhancement(content)
        conversation_context = context_manager.get_conversation_context(user_id) or {}
        dialog_history = context_manager.get_dialog_history(user_id, limit=10)
        external_learning_context = (context or {}).get("external_learning_context", {})

        request = {
            "type": request_type,
            "content": enhancement_result["enhanced_content"],
            "original_content": enhancement_result["original_content"],
            "user_id": user_id,
            "timestamp": self._get_timestamp(),
            "enhancement_info": {
                "was_enhanced": enhancement_result["was_enhanced"],
                "analysis_confidence": enhancement_result.get("analysis_confidence", 0.5),
                "context_analysis": enhancement_result.get("context_analysis", {}),
            },
            "context": {
                "conversation_context": conversation_context,
                "recent_history": dialog_history,
                "learning_progress": context_manager.get_learning_progress(user_id) or {},
                "external_learning_context": external_learning_context,
            },
            "target_exercise": enhancement_result.get("target_exercise"),
        }
        return await self.forward_to_main_agent(request)

    async def save_conversation_result(
        self, user_id: str, request: Dict[str, Any], result: Dict[str, Any]
    ):
        try:
            question_id = None
            details = result.get("details", {})
            if "questions" in details and details["questions"]:
                first_question = details["questions"][0]
                question_id = first_question.get("question_id")
            elif "exercise" in details:
                question_id = details["exercise"].get("question_id")

            dialog_data = {
                "user_input": str(request.get("original_content", "")),
                "agent_response": str(result.get("response", "")),
                "intent": str(result.get("detected_intent", "unknown")),
                "topic": str(result.get("details", {}).get("topic", "general")),
                "question_id": question_id,
                "session_id": f"session_{int(time.time())}",
            }
            context_manager.save_dialog_history(user_id, dialog_data)

            current_context = context_manager.get_conversation_context(user_id) or {}
            current_context.update(
                {
                    "last_intent": str(result.get("detected_intent", "unknown")),
                    "last_topic": str(result.get("details", {}).get("topic", "general")),
                    "last_interaction_time": str(request.get("timestamp", "")),
                    "interaction_count": current_context.get("interaction_count", 0) + 1,
                }
            )

            if result.get("detected_intent") == "exercise" and "details" in result:
                exercise_details = result["details"]
                current_context["last_exercise_topic"] = str(exercise_details.get("topic", "general"))
                current_context["last_exercise_type"] = str(exercise_details.get("type", "unknown"))
                current_context["last_exercise_time"] = str(request.get("timestamp", ""))
                if "questions" in exercise_details and exercise_details["questions"]:
                    first_question = exercise_details["questions"][0]
                    description = first_question.get("content", {}).get("description", "")
                    current_context["last_question_preview"] = str(description)[:100]
                    current_context["last_question_id"] = first_question.get("question_id")
                elif "exercise" in exercise_details:
                    description = exercise_details["exercise"].get("content", {}).get("description", "")
                    current_context["last_question_preview"] = str(description)[:100]
                    current_context["last_question_id"] = exercise_details["exercise"].get("question_id")

            context_manager.save_conversation_context(user_id, current_context)
        except Exception as exc:
            logger.error("Saving conversation result failed: %s", exc)

    async def forward_to_main_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self.log_activity(
            "转发优化后的请求给主代理",
            {
                "request_type": str(request.get("type", "")),
                "was_enhanced": request["enhancement_info"]["was_enhanced"],
                "analysis_confidence": request["enhancement_info"].get("analysis_confidence", 0.5),
                "target_exercise_found": request.get("target_exercise") is not None,
            },
        )
        result = await self.main_agent.process(request)
        await self.save_conversation_result(request["user_id"], request, result)
        return result

    async def collect_and_return_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        self.log_activity(
            "返回结果给用户",
            {
                "result_type": type(results).__name__,
                "detected_intent": str(results.get("detected_intent", "unknown")),
            },
        )

        formatted_result = {
            "success": results.get("success", True),
            "user_id": self.current_user_id,
            "response": str(results.get("response", "请求处理完成")),
            "details": results.get("details", {}),
            "suggestions": results.get("suggestions", []),
            "request_type": str(results.get("detected_intent", "unknown")),
            "processing_info": {
                "input_enhanced": results.get("enhancement_applied", False),
                "context_used": results.get("context_used", False),
                "analysis_confidence": results.get("enhancement_info", {}).get(
                    "analysis_confidence", 0.5
                ),
                "target_exercise_used": results.get("target_exercise") is not None,
            },
        }
        if "error" in results:
            formatted_result["error"] = str(results["error"])
        return formatted_result

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.receive_user_request(
            request.get("type", "auto"),
            request.get("content", ""),
            request.get("user_id", "anonymous"),
        )
        return await self.collect_and_return_results(result)

    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()
