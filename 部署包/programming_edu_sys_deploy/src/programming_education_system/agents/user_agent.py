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
            return {
                "success": True,
                "history_count": len(history),
                "analysis_prompt": self._build_analysis_prompt(current_input, history),
                "raw_history": history,
            }
        except Exception as exc:
            logger.error("Context analysis failed: %s", exc)
            return {"success": False, "error": str(exc), "history_count": 0, "raw_history": []}

    def _build_analysis_prompt(self, current_input: str, history: List[Dict[str, Any]]) -> str:
        history_lines = ["对话历史:"]
        for index, dialog in enumerate(history[-8:], start=1):
            user_msg = str(dialog.get("user_input", ""))[:350]
            agent_msg = str(dialog.get("agent_response", ""))[:350]
            history_lines.append(f"{index}. 用户: {user_msg}")
            if agent_msg:
                history_lines.append(f"   助手: {agent_msg}")

        return f"""请分析当前输入是否依赖对话历史。只返回 JSON。
{chr(10).join(history_lines)}

当前输入:
{current_input}

输出 JSON schema:
{{
  "user_intent": "exercise|answer|explanation|concept|example|debug|plan|general",
  "needs_context": false,
  "key_points": ["只列出与当前输入直接相关的上下文"],
  "exercise_reference": {{
    "has_exercise": false,
    "exercise_content": "",
    "exercise_topic": ""
  }},
  "suggested_enhancement": "如果 needs_context 为 true，给出补全后的请求；否则为空字符串"
}}

规则:
- 不要回答用户问题。
- 不要凭空补充历史里没有的题目或概念。
- 当前输入已经明确时，needs_context=false。
- 如果用户说“再举个例子/换个说法/为什么/继续/那它呢”，通常 needs_context=true。
- suggested_enhancement 要保留用户这次的追问动作，例如“再举例”不能改写成“重新解释上一题”。"""


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

            system_prompt = (
                "角色：你是编程教育对话上下文分析器。\n"
                "任务：判断当前输入是否需要历史上下文，并输出严格 JSON。\n"
                "约束：不要回答问题，不要生成代码，不要输出 Markdown，不要添加 schema 之外的字段。\n"
                "关键原则：追问要被补全为“基于上一轮主题继续回答当前追问”，不能改写成重复上一轮问题。"
            )
            analysis_response = await self._get_llm_client().generate_response(
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
                "target_exercise": self._target_exercise_or_none(analysis_result),
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
            "exercise_reference": {"has_exercise": False, "exercise_content": "", "exercise_topic": ""},
            "suggested_enhancement": "",
        }

    def _build_enhanced_input(self, original_input: str, analysis_result: Dict[str, Any]) -> str:
        if not analysis_result.get("needs_context", False):
            return original_input
        user_intent = analysis_result.get("user_intent", "general")
        key_points = [str(point) for point in analysis_result.get("key_points", [])[:3] if str(point).strip()]
        exercise_ref = analysis_result.get("exercise_reference", {}) or {}
        suggested_enhancement = str(analysis_result.get("suggested_enhancement", "")).strip()

        if user_intent == "answer" and exercise_ref.get("has_exercise"):
            return self._build_exercise_answer_request(original_input, exercise_ref)
        if self._is_safe_enhancement(original_input, suggested_enhancement):
            return suggested_enhancement
        if key_points:
            return self._build_context_aware_request(original_input, key_points)
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
            "请针对该题目提供思路、分级提示和参考解法。"
        )

    def _build_context_aware_request(self, original_input: str, key_points: List[str]) -> str:
        context_summary = "\n".join(f"- {point}" for point in key_points)
        return (
            f"用户当前追问: {original_input}\n\n"
            f"相关上下文:\n{context_summary}\n\n"
            "请只回答当前追问需要新增的信息，避免完整重复上一轮答案。"
        )

    @staticmethod
    def _target_exercise_or_none(analysis_result: Dict[str, Any]) -> Dict[str, Any] | None:
        exercise_ref = analysis_result.get("exercise_reference") or {}
        if isinstance(exercise_ref, dict) and exercise_ref.get("has_exercise"):
            return exercise_ref
        return None

    @staticmethod
    def _is_safe_enhancement(original_input: str, enhanced: str) -> bool:
        if not enhanced or enhanced == original_input:
            return False
        if len(enhanced) > 600:
            return False
        if any(token in enhanced for token in ["```", "{", "}", "答案是"]):
            return False
        return True

    async def _fallback_enhancement(self, content: str, user_id: str) -> Dict[str, Any]:
        return {
            "original_content": content,
            "enhanced_content": content,
            "was_enhanced": False,
            "context_analysis": {"success": False, "error": "fallback_plain_input"},
            "analysis_confidence": 0.3,
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
        self.log_activity(
            "received user request",
            {
                "user_id": user_id,
                "request_type": request_type,
                "original_content": content[:50] + "..." if len(content) > 50 else content,
            },
        )

        if self._should_enhance_user_input(request_type, content, user_id):
            enhancement_result = await self.enhance_user_input_with_context(content, user_id)
        else:
            enhancement_result = self._plain_enhancement(content)

        conversation_context = context_manager.get_conversation_context(user_id) or {}
        dialog_history = context_manager.get_dialog_history(user_id, limit=10)
        runtime_history = (context or {}).get("recent_history", [])
        combined_history = self._merge_histories(dialog_history, runtime_history)
        external_learning_context = (context or {}).get("external_learning_context", {})

        request = {
            "type": request_type,
            "content": enhancement_result["enhanced_content"],
            "original_content": enhancement_result["original_content"],
            "user_id": user_id,
            "timestamp": self._get_timestamp(),
            "enhancement_info": {
                "was_enhanced": enhancement_result["was_enhanced"],
                "context_used": enhancement_result["was_enhanced"],
                "analysis_confidence": enhancement_result.get("analysis_confidence", 0.5),
                "context_analysis": enhancement_result.get("context_analysis", {}),
            },
            "context": {
                "conversation_context": conversation_context,
                "recent_history": combined_history,
                "learning_progress": context_manager.get_learning_progress(user_id) or {},
                "external_learning_context": external_learning_context,
            },
            "target_exercise": enhancement_result.get("target_exercise"),
        }
        return await self.forward_to_main_agent(request)

    @staticmethod
    def _merge_histories(
        stored_history: List[Dict[str, Any]],
        runtime_history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen = set()
        for item in [*stored_history, *runtime_history]:
            user_input = str(item.get("user_input", ""))
            agent_response = str(item.get("agent_response", ""))
            key = (user_input, agent_response[:80])
            if not user_input or key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged[-10:]

    async def save_conversation_result(self, user_id: str, request: Dict[str, Any], result: Dict[str, Any]):
        try:
            question_id = None
            details = result.get("details", {})
            if "questions" in details and details["questions"]:
                question_id = details["questions"][0].get("question_id")
            elif "exercise" in details:
                question_id = details["exercise"].get("question_id")

            context_manager.save_dialog_history(
                user_id,
                {
                    "user_input": str(request.get("original_content", "")),
                    "agent_response": str(result.get("response", "")),
                    "intent": str(result.get("detected_intent", "unknown")),
                    "topic": str(result.get("details", {}).get("topic", "general")),
                    "question_id": question_id,
                    "intent_analysis": result.get("intent_analysis", {}),
                    "session_id": f"session_{int(time.time())}",
                },
            )

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
                if "exercise" in exercise_details:
                    description = exercise_details["exercise"].get("content", {}).get("description", "")
                    current_context["last_question_preview"] = str(description)[:100]
                    current_context["last_question_id"] = exercise_details["exercise"].get("question_id")
            context_manager.save_conversation_context(user_id, current_context)
        except Exception as exc:
            logger.error("Saving conversation result failed: %s", exc)

    async def forward_to_main_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self.log_activity(
            "forwarding request to main agent",
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
            "returning result to user",
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
            "intent_analysis": results.get("intent_analysis", {}),
            "processing_info": {
                "input_enhanced": results.get("enhancement_applied", False),
                "context_used": results.get("context_used", False),
                "analysis_confidence": results.get("enhancement_info", {}).get("analysis_confidence", 0.5),
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
