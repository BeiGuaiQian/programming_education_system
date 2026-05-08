"""User-facing agent responsible for context-aware request preparation."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.models.question_schema import normalize_question
from programming_education_system.utils.agent_interaction_logger import log_agent_interaction
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
                task_type="user_context",
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
            "context_decision": None,
        }

    def _contextual_exercise_enhancement(
        self,
        content: str,
        target_question: Dict[str, Any],
        context_decision: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        normalized = normalize_question(target_question)
        return {
            "original_content": content,
            "enhanced_content": content,
            "was_enhanced": False,
            "context_analysis": {
                "success": True,
                "rule_based": True,
                "reason": "last_question_followup",
                "target_question_id": normalized.get("question_id"),
            },
            "analysis_confidence": float((context_decision or {}).get("confidence", 0.98) or 0.98),
            "target_exercise": normalized,
            "context_decision": context_decision,
        }

    def _decision_enhancement(
        self,
        content: str,
        decision: Dict[str, Any],
        target_question: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        action = str(decision.get("action", "plain"))
        if action in {"answer_current_exercise", "hint_current_exercise"} and target_question:
            return self._contextual_exercise_enhancement(content, target_question, decision)

        rewritten = str(decision.get("optimized_input") or decision.get("rewritten_content", "")).strip()
        enhanced_content = rewritten if self._is_safe_enhancement(content, rewritten) else content
        return {
            "original_content": content,
            "enhanced_content": enhanced_content,
            "was_enhanced": enhanced_content != content,
            "context_analysis": {
                "success": True,
                "llm_context_decision": decision,
                "reason": "llm_context_resolver",
            },
            "analysis_confidence": float(decision.get("confidence", 0.75) or 0.75),
            "target_exercise": None,
            "context_decision": decision,
        }

    def _build_context_optimized_request(
        self,
        content: str,
        decision: Dict[str, Any],
        target_question: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        action = str(decision.get("action", "plain"))
        optimized_input = str(decision.get("optimized_input") or decision.get("rewritten_content") or "").strip()
        if not self._is_safe_optimized_input(content, optimized_input):
            optimized_input = content

        target = target_question if action in {"answer_current_exercise", "hint_current_exercise"} else None
        normalized_target = normalize_question(target) if isinstance(target, dict) else None
        return {
            "original_content": content,
            "enhanced_content": optimized_input,
            "was_enhanced": optimized_input != content,
            "context_analysis": {
                "success": True,
                "llm_context_decision": decision,
                "reason": "llm_input_optimizer",
            },
            "analysis_confidence": float(decision.get("confidence", 0.75) or 0.75),
            "target_exercise": normalized_target,
            "context_decision": decision,
        }

    async def _resolve_context_with_llm(
        self,
        content: str,
        request_type: str,
        recent_history: List[Dict[str, Any]],
        target_question: Dict[str, Any] | None,
        current_conversation_id: str | None,
    ) -> Dict[str, Any] | None:
        if request_type not in {"auto", "exercise", "qa", "evaluation", "personal"}:
            return None
        if len(content.strip()) > 1200:
            return None

        last_question_payload = self._question_for_decision_prompt(target_question)
        history_payload = self._history_for_optimizer_prompt(recent_history)
        system_prompt = (
            "你是编程教育系统的用户输入优化器和上下文裁决器。"
            "你必须先读取当前会话历史、最近题目和当前输入，再把用户输入优化成一个"
            "主代理和子代理可以独立理解的请求。不要回答用户问题，不要生成题目，不要写代码。"
            "只返回严格 JSON，不要 Markdown。\n\n"
            "你要解决的问题：\n"
            "1. 如果用户追问上一轮，要把必要上下文写进 optimized_input。\n"
            "2. 如果用户只是说“我不会/继续/这个呢/为什么”等类似的话，要结合当前会话判断真实指向。\n"
            "3. optimized_input 必须保留用户本轮意图，不能把“再来一道”改成“解答上一题”，要以用户本轮意图为最重。\n"
            "4. context_summary 只写与本轮有关的上下文，不要复制整段历史回复。\n"
            "5. already_answered 写已经讲过的点，供子代理避免复读。\n\n"
            "允许的 action：\n"
            "- answer_current_exercise：用户想要当前题目的参考解答或完整讲解。\n"
            "- hint_current_exercise：用户卡住了、不会、没思路，需要当前题目的提示或引导。\n"
            "- generate_new_exercise：用户想再来一道、换一道、生成新题。\n"
            "- answer_question：普通概念问答或解释。\n"
            "- evaluate_code：检查代码、解释报错、评估实现。\n"
            "- personal_plan：学习建议、学习路径、下一步规划。\n"
            "- clarify_missing_context：用户含糊引用历史，但当前会话没有可引用对象。\n"
            "- plain：无需上下文，保持原输入。\n\n"
            "硬性规则：\n"
            "1. 只有 last_question 不为空时，才能选择 answer_current_exercise 或 hint_current_exercise。\n"
            "2. 用户说“我不会、没思路、卡住了、不会写”等，且 last_question 存在，通常选择 hint_current_exercise。\n"
            "3. 用户说“再来一道、换一道、类似的、重新出”，选择 generate_new_exercise。\n"
            "4. 如果 last_question 为空且用户说“我不会/这个怎么做/继续”等，选择 clarify_missing_context。\n"
            "5. 不要根据非当前会话内容臆造题目。\n\n"
            "输出 JSON schema：{\n"
            '  "action": "answer_current_exercise|hint_current_exercise|generate_new_exercise|answer_question|evaluate_code|personal_plan|clarify_missing_context|plain",\n'
            '  "intent": "exercise|qa|evaluation|personal",\n'
            '  "optimized_input": "带必要上下文的用户请求，不能回答问题",\n'
            '  "context_summary": "与本轮最相关的历史摘要，80字以内",\n'
            '  "already_answered": ["历史中已经回答过的要点"],\n'
            '  "relevant_turns": [1,2],\n'
            '  "use_last_question": false,\n'
            '  "needs_exercise_context": false,\n'
            '  "confidence": 0.0,\n'
            '  "reason": "20字以内"\n'
            "}"
        )
        system_prompt = (
            "你是编程教育系统的用户输入优化智能体。\n"
            "你的职责是读取当前输入、当前会话历史和最近题目，把用户输入整理成主代理和子代理可以独立理解的任务包。\n"
            "不要回答用户问题，不要生成题目，不要写解答代码；只返回严格 JSON，不要 Markdown。\n\n"
            "工作原则：\n"
            "1. optimized_input 必须保留用户本轮真实意图，并补足必要上下文。\n"
            "2. 如果当前输入依赖历史，optimized_input 必须脱离历史也能看懂。\n"
            "3. 如果当前输入已经完整明确，optimized_input 可以等于原文。\n"
            "4. context_summary 只写与本轮任务有关的历史事实。\n"
            "5. already_answered 写历史中已经讲过的要点，avoid_repeating 写本轮应避免重复的表达。\n"
            "6. 只根据给定历史和 last_question 判断，不要臆造题目或背景。\n\n"
            "action 只能取：\n"
            "- answer_current_exercise：讲解或给出当前题目的参考思路/答案。\n"
            "- hint_current_exercise：针对当前题目给提示、引导或分步帮助。\n"
            "- generate_new_exercise：生成新练习题。\n"
            "- answer_question：解释概念、原理、用法、区别或为什么。\n"
            "- evaluate_code：检查代码、解释报错、定位 bug 或评价实现。\n"
            "- personal_plan：学习建议、学习路径、薄弱点分析。\n"
            "- clarify_missing_context：用户引用了历史对象，但当前上下文不足以确定对象。\n"
            "- plain：无需历史上下文，保持原输入。\n\n"
            "输出 JSON schema：\n"
            "{\n"
            '  "action": "answer_current_exercise|hint_current_exercise|generate_new_exercise|answer_question|evaluate_code|personal_plan|clarify_missing_context|plain",\n'
            '  "intent": "exercise|qa|evaluation|personal",\n'
            '  "optimized_input": "带必要上下文的用户请求，不能回答问题",\n'
            '  "topic_hint": "python_basics|data_structures|algorithms|oop|web_development|data_science|general_programming",\n'
            '  "user_requirement": "本轮用户对输出的具体要求",\n'
            '  "context_summary": "与本轮最相关的历史摘要，120字以内",\n'
            '  "already_answered": ["历史中已经回答过的要点"],\n'
            '  "avoid_repeating": ["本轮应避免重复的表达或例子"],\n'
            '  "relevant_turns": [1, 2],\n'
            '  "use_last_question": false,\n'
            '  "needs_exercise_context": false,\n'
            '  "confidence": 0.0,\n'
            '  "reason": "20字以内的判断理由"\n'
            "}"
        )
        user_message = json.dumps(
            {
                "current_input": content,
                "request_type": request_type,
                "conversation_id": current_conversation_id,
                "last_question": last_question_payload,
                "conversation_history": history_payload,
            },
            ensure_ascii=False,
        )
        try:
            response = await self._get_llm_client().generate_response(
                system_prompt,
                user_message,
                use_cache=False,
                task_type="user_context",
            )
            decision = self._parse_context_decision(response)
            action = str(decision.get("action", "plain"))
            if action in {"answer_current_exercise", "hint_current_exercise"} and not target_question:
                decision["action"] = "clarify_missing_context"
                decision["use_last_question"] = False
                decision["needs_exercise_context"] = True
                decision["intent"] = "exercise"
                decision["optimized_input"] = content
            return decision
        except Exception as exc:
            logger.warning("LLM context resolution failed: %s", exc)
            return None

    async def _legacy_resolve_context_with_llm(
        self,
        content: str,
        request_type: str,
        recent_history: List[Dict[str, Any]],
        target_question: Dict[str, Any] | None,
        current_conversation_id: str | None,
    ) -> Dict[str, Any] | None:
        """Kept as a fallback shape reference for older callers."""
        history_payload = [
            {
                "user": str(item.get("user_input", ""))[:500],
                "assistant": str(item.get("agent_response", ""))[:700],
                "intent": item.get("intent") or item.get("request_type") or item.get("agent_request_type"),
                "question_id": item.get("question_id"),
            }
            for item in recent_history[-6:]
        ]
        system_prompt = (
            "你是编程教育系统的会话裁决器。你只读取当前会话历史、最近题目和当前输入，"
            "判断下一步应该做什么。不要回答用户问题，不要生成题目，不要写代码。"
            "只返回严格 JSON，不要 Markdown。\n\n"
            "允许的 action：\n"
            "- answer_current_exercise：用户想要当前题目的参考解答或完整讲解。\n"
            "- hint_current_exercise：用户卡住了、不会、没思路，需要当前题目的提示或引导。\n"
            "- generate_new_exercise：用户想再来一道、换一道、生成新题。\n"
            "- answer_question：普通概念问答或解释。\n"
            "- evaluate_code：检查代码、解释报错、评估实现。\n"
            "- personal_plan：学习建议、学习路径、下一步规划。\n"
            "- clarify_missing_context：用户在说“我不会/这个怎么做”等，但当前会话没有可引用题目。\n"
            "- plain：无需上下文，保持原输入。\n\n"
            "硬性规则：\n"
            "1. 只有 last_question 不为空时，才能选择 answer_current_exercise 或 hint_current_exercise。\n"
            "2. 如果用户说“我不会、没思路、卡住了、不会写”等，且 last_question 存在，选择 hint_current_exercise。\n"
            "3. 如果用户说“再来一道、换一道、类似的、重新出”，选择 generate_new_exercise，不要把上一题当目标题。\n"
            "4. 如果用户含糊地引用上一题，但 last_question 为空，选择 clarify_missing_context。\n"
            "5. 不要根据非当前会话内容臆造题目。"
        )
        user_message = json.dumps(
            {
                "current_input": content,
                "request_type": request_type,
                "conversation_id": current_conversation_id,
                "last_question": last_question_payload,
                "recent_history": history_payload,
                "output_schema": {
                    "action": "answer_current_exercise|hint_current_exercise|generate_new_exercise|answer_question|evaluate_code|personal_plan|clarify_missing_context|plain",
                    "intent": "exercise|qa|evaluation|personal",
                    "use_last_question": False,
                    "needs_exercise_context": False,
                    "rewritten_content": "",
                    "confidence": 0.0,
                    "reason": "20字以内",
                },
            },
            ensure_ascii=False,
        )
        try:
            response = await self._get_llm_client().generate_response(
                system_prompt,
                user_message,
                use_cache=False,
            )
            decision = self._parse_context_decision(response)
            action = str(decision.get("action", "plain"))
            if action in {"answer_current_exercise", "hint_current_exercise"} and not target_question:
                action = "clarify_missing_context"
                decision["action"] = action
                decision["use_last_question"] = False
                decision["needs_exercise_context"] = True
                decision["intent"] = "exercise"
            return decision
        except Exception as exc:
            logger.warning("LLM context resolution failed: %s", exc)
            return None

    @staticmethod
    def _question_for_decision_prompt(question: Dict[str, Any] | None) -> Dict[str, Any] | None:
        if not isinstance(question, dict):
            return None
        normalized = normalize_question(question)
        return {
            "question_id": normalized.get("question_id"),
            "topic": normalized.get("topic"),
            "difficulty": normalized.get("difficulty"),
            "title": normalized.get("title"),
            "description": normalized.get("description"),
            "hints": normalized.get("hints", [])[:3],
            "answer_available": bool(normalized.get("answer")),
        }

    @staticmethod
    def _history_for_optimizer_prompt(history: List[Dict[str, Any]], limit: int = 24) -> List[Dict[str, Any]]:
        compact_history: List[Dict[str, Any]] = []
        selected = history[-limit:]
        offset = max(0, len(history) - len(selected))
        for index, item in enumerate(selected, start=offset + 1):
            user_input = str(item.get("user_input", "")).strip()
            agent_response = str(item.get("agent_response", "")).strip()
            if not user_input:
                continue
            compact_history.append(
                {
                    "turn": index,
                    "user": user_input[:500],
                    "assistant_summary": agent_response[:500],
                    "intent": item.get("intent") or item.get("request_type") or item.get("agent_request_type"),
                    "topic": item.get("topic") or (item.get("intent_analysis") or {}).get("topic"),
                    "question_id": item.get("question_id"),
                    "has_question": isinstance(item.get("question"), dict) or bool(item.get("question_id")),
                }
            )
        return compact_history

    def _parse_context_decision(self, response: str) -> Dict[str, Any]:
        fallback = {
            "action": "plain",
            "intent": "qa",
            "use_last_question": False,
            "needs_exercise_context": False,
            "rewritten_content": "",
            "optimized_input": "",
            "topic_hint": "general_programming",
            "user_requirement": "",
            "context_summary": "",
            "already_answered": [],
            "avoid_repeating": [],
            "relevant_turns": [],
            "confidence": 0.5,
            "reason": "parse_fallback",
        }
        try:
            cleaned = response.strip()
            if cleaned.startswith("{"):
                data = json.loads(cleaned)
            else:
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                data = json.loads(match.group()) if match else fallback
        except (json.JSONDecodeError, ValueError, AttributeError):
            return fallback

        allowed_actions = {
            "answer_current_exercise",
            "hint_current_exercise",
            "generate_new_exercise",
            "answer_question",
            "evaluate_code",
            "personal_plan",
            "clarify_missing_context",
            "plain",
        }
        action = str(data.get("action", "plain"))
        if action not in allowed_actions:
            action = "plain"
        intent = str(data.get("intent", "qa"))
        if intent not in {"exercise", "qa", "evaluation", "personal"}:
            intent = {
                "answer_current_exercise": "exercise",
                "hint_current_exercise": "exercise",
                "generate_new_exercise": "exercise",
                "clarify_missing_context": "exercise",
                "evaluate_code": "evaluation",
                "personal_plan": "personal",
            }.get(action, "qa")
        try:
            confidence = max(0.0, min(1.0, float(data.get("confidence", 0.7))))
        except (TypeError, ValueError):
            confidence = 0.7
        return {
            "action": action,
            "intent": intent,
            "use_last_question": bool(data.get("use_last_question", False)),
            "needs_exercise_context": bool(data.get("needs_exercise_context", action in {"answer_current_exercise", "hint_current_exercise", "clarify_missing_context"})),
            "rewritten_content": str(data.get("rewritten_content", ""))[:600],
            "optimized_input": str(data.get("optimized_input") or data.get("rewritten_content") or "")[:1200],
            "topic_hint": str(data.get("topic_hint") or "general_programming")[:80],
            "user_requirement": str(data.get("user_requirement") or "")[:300],
            "context_summary": str(data.get("context_summary", ""))[:500],
            "already_answered": [
                str(item)[:160]
                for item in (data.get("already_answered") or [])
                if str(item).strip()
            ][:6],
            "avoid_repeating": [
                str(item)[:160]
                for item in (data.get("avoid_repeating") or [])
                if str(item).strip()
            ][:6],
            "relevant_turns": [
                int(item)
                for item in (data.get("relevant_turns") or [])
                if isinstance(item, int) or str(item).isdigit()
            ][:8],
            "confidence": confidence,
            "reason": str(data.get("reason", "llm_context"))[:60],
        }

    @staticmethod
    def _is_safe_optimized_input(original_input: str, optimized: str) -> bool:
        if not optimized:
            return False
        if len(optimized) > 1200:
            return False
        forbidden = ["答案是", "参考代码如下", "```"]
        if any(token in optimized for token in forbidden):
            return False
        if len(original_input.strip()) > 20 and len(optimized.strip()) < max(8, len(original_input.strip()) // 2):
            return False
        return True

    def _should_enhance_user_input(self, request_type: str, content: str, user_id: str) -> bool:
        if len(content.strip()) > 1200:
            return False
        history = context_manager.get_dialog_history(user_id, limit=3)
        if not history:
            return False
        if request_type != "auto" and len(content.strip()) > 12:
            return False
        return len(content.strip()) <= 120

    @staticmethod
    def _is_exercise_followup(content: str) -> bool:
        lowered = content.lower().strip()
        if not lowered:
            return False
        answer_terms = [
            "答案",
            "给答案",
            "解答",
            "怎么做",
            "咋做",
            "如何做",
            "如何实现",
            "怎么写",
            "写法",
            "代码",
            "思路",
            "提示",
            "讲解",
            "不会",
            "参考代码",
            "参考答案",
            "solution",
            "answer",
            "hint",
        ]
        reference_terms = [
            "这题",
            "这道题",
            "这个题",
            "这个",
            "这道",
            "它",
            "该题",
            "上一题",
            "上一次",
            "上一个",
            "上面",
            "前面",
            "刚才",
            "刚刚",
            "你刚才",
            "刚出的",
            "你生成的题",
            "生成的题目",
            "那道题",
            "那个",
            "那个练习",
            "这个练习",
        ]
        new_question_terms = [
            "再来一道",
            "再出一道",
            "换一道",
            "重新出",
            "出一道题",
            "生成一道",
            "给我一道",
            "再生成",
        ]
        has_answer_action = any(term in lowered for term in answer_terms)
        has_reference = any(term in lowered for term in reference_terms)
        asks_new_question = any(term in lowered for term in new_question_terms)
        if asks_new_question and not has_answer_action:
            return False
        return has_reference and has_answer_action

    @staticmethod
    def _is_exercise_help_request(content: str) -> bool:
        lowered = content.lower().strip()
        if not lowered:
            return False
        help_terms = [
            "不会",
            "不会做",
            "不会写",
            "不懂",
            "看不懂",
            "没思路",
            "没有思路",
            "卡住",
            "卡住了",
            "做不出来",
            "写不出来",
            "不知道怎么写",
            "不知道怎么做",
            "help",
            "stuck",
        ]
        new_question_terms = [
            "再来一道",
            "再出一道",
            "再练一题",
            "换一道",
            "重新出",
            "重新生成",
            "出一道题",
            "生成一道",
            "给我一道",
            "再生成",
        ]
        return any(term in lowered for term in help_terms) and not any(
            term in lowered for term in new_question_terms
        )

    @staticmethod
    def _is_new_exercise_request(content: str) -> bool:
        lowered = content.lower().strip()
        if not lowered:
            return False
        new_question_terms = [
            "再来一道",
            "再出一道",
            "再练一题",
            "换一道",
            "重新出",
            "重新生成",
            "出一道题",
            "生成一道",
            "给我一道",
            "再生成",
            "类似的",
            "同类型",
            "another",
            "new exercise",
            "new problem",
        ]
        answer_terms = [
            "答案",
            "给答案",
            "解答",
            "怎么做",
            "咋做",
            "如何做",
            "如何实现",
            "怎么写",
            "写法",
            "代码",
            "思路",
            "提示",
            "讲解",
            "不会",
            "参考代码",
            "参考答案",
            "solution",
            "answer",
            "hint",
        ]
        return any(term in lowered for term in new_question_terms) and not any(
            term in lowered for term in answer_terms
        )

    @staticmethod
    def _last_question_from_context(
        conversation_context: Dict[str, Any],
        current_conversation_id: str | None = None,
    ) -> Dict[str, Any] | None:
        stored_conversation_id = conversation_context.get("last_conversation_id")
        if (
            current_conversation_id
            and stored_conversation_id
            and str(stored_conversation_id) != str(current_conversation_id)
        ):
            return None
        last_question = conversation_context.get("last_question")
        if isinstance(last_question, dict) and (
            last_question.get("question_id") or last_question.get("description") or last_question.get("content")
        ):
            return normalize_question(last_question)
        return None

    @staticmethod
    def _sanitize_conversation_context(
        conversation_context: Dict[str, Any],
        current_conversation_id: str | None = None,
    ) -> Dict[str, Any]:
        sanitized = dict(conversation_context)
        stored_conversation_id = sanitized.get("last_conversation_id")
        if (
            current_conversation_id
            and stored_conversation_id
            and str(stored_conversation_id) != str(current_conversation_id)
        ):
            for key in [
                "last_question",
                "last_question_preview",
                "last_question_id",
                "last_exercise_topic",
                "last_exercise_type",
                "last_exercise_time",
                "last_conversation_id",
            ]:
                sanitized.pop(key, None)
        return sanitized

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
        request_id = str((context or {}).get("request_id") or uuid4())
        self.current_user_id = user_id
        self.log_activity(
            "received user request",
            {
                "request_id": request_id,
                "user_id": user_id,
                "request_type": request_type,
                "original_content": content[:50] + "..." if len(content) > 50 else content,
            },
        )
        log_agent_interaction(
            "user_request_received",
            "User",
            "EnhancedUserAgent",
            request_id=request_id,
            user_id=user_id,
            payload={
                "request_type": request_type,
                "content": content,
                "external_context_keys": list((context or {}).keys()),
            },
        )

        external_learning_context = (context or {}).get("external_learning_context", {})
        current_conversation_id = str(
            (context or {}).get("conversation_id") or external_learning_context.get("conversation_id") or ""
        ) or None
        conversation_context = context_manager.get_conversation_context(user_id) or {}
        target_question = self._last_question_from_context(conversation_context, current_conversation_id)
        sanitized_conversation_context = self._sanitize_conversation_context(
            conversation_context,
            current_conversation_id,
        )

        dialog_history = context_manager.get_dialog_history(user_id, limit=100)
        if current_conversation_id:
            dialog_history = [
                item
                for item in dialog_history
                if str(item.get("conversation_id") or "") == str(current_conversation_id)
            ]
        runtime_history = (context or {}).get("recent_history", [])
        combined_history = self._merge_histories(dialog_history, runtime_history)

        context_decision = await self._resolve_context_with_llm(
            content,
            request_type,
            combined_history,
            target_question,
            current_conversation_id,
        )

        if context_decision and float(context_decision.get("confidence", 0.0) or 0.0) >= 0.55:
            enhancement_result = self._build_context_optimized_request(content, context_decision, target_question)
        else:
            enhancement_result = self._plain_enhancement(content)

        external_learning_context = (context or {}).get("external_learning_context", {})
        task_context = self._build_task_context(
            enhancement_result,
            context_decision,
            target_question,
            combined_history,
            current_conversation_id,
        )

        log_agent_interaction(
            "user_agent_input_optimized",
            "EnhancedUserAgent",
            "MainAgent",
            request_id=request_id,
            user_id=user_id,
            payload={
                "original_content": content,
                "optimized_content": enhancement_result["enhanced_content"],
                "was_enhanced": enhancement_result["was_enhanced"],
                "context_decision": enhancement_result.get("context_decision"),
                "target_exercise_id": (
                    enhancement_result.get("target_exercise") or {}
                ).get("question_id"),
                "history_total": len(combined_history),
                "history_for_subagents": self._history_for_subagents(combined_history, context_decision),
                "task_context": task_context,
            },
        )

        request = {
            "type": request_type,
            "content": enhancement_result["enhanced_content"],
            "original_content": enhancement_result["original_content"],
            "user_id": user_id,
            "request_id": request_id,
            "timestamp": self._get_timestamp(),
            "enhancement_info": {
                "was_enhanced": enhancement_result["was_enhanced"],
                "context_used": (
                    enhancement_result["was_enhanced"]
                    or enhancement_result.get("target_exercise") is not None
                    or (
                        isinstance(enhancement_result.get("context_decision"), dict)
                        and enhancement_result["context_decision"].get("action") != "plain"
                    )
                ),
                "analysis_confidence": enhancement_result.get("analysis_confidence", 0.5),
                "context_analysis": enhancement_result.get("context_analysis", {}),
            },
            "context": {
                "conversation_context": sanitized_conversation_context,
                "recent_history": self._history_for_subagents(combined_history, context_decision),
                "full_history_count": len(combined_history),
                "task_context": task_context,
                "learning_progress": context_manager.get_learning_progress(user_id) or {},
                "external_learning_context": external_learning_context,
                "conversation_id": current_conversation_id,
            },
            "target_exercise": enhancement_result.get("target_exercise"),
            "context_decision": enhancement_result.get("context_decision"),
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
        return merged[-50:]

    @staticmethod
    def _history_for_subagents(
        combined_history: List[Dict[str, Any]],
        decision: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:
        relevant_turns = set()
        if isinstance(decision, dict):
            for item in decision.get("relevant_turns") or []:
                try:
                    relevant_turns.add(int(item))
                except (TypeError, ValueError):
                    pass
        selected: List[Dict[str, Any]] = []
        for index, item in enumerate(combined_history, start=1):
            if index in relevant_turns:
                selected.append(item)
        for item in combined_history[-8:]:
            if item not in selected:
                selected.append(item)
        return selected[-12:]

    def _build_task_context(
        self,
        enhancement_result: Dict[str, Any],
        decision: Dict[str, Any] | None,
        target_question: Dict[str, Any] | None,
        combined_history: List[Dict[str, Any]],
        conversation_id: str | None,
    ) -> Dict[str, Any]:
        decision = decision if isinstance(decision, dict) else {}
        target_payload = self._question_for_decision_prompt(target_question)
        return {
            "original_input": enhancement_result.get("original_content", ""),
            "optimized_input": enhancement_result.get("enhanced_content", ""),
            "context_summary": str(decision.get("context_summary", "")),
            "already_answered": decision.get("already_answered", []) if isinstance(decision.get("already_answered"), list) else [],
            "avoid_repeating": decision.get("avoid_repeating", []) if isinstance(decision.get("avoid_repeating"), list) else [],
            "topic_hint": str(decision.get("topic_hint") or "general_programming"),
            "user_requirement": str(decision.get("user_requirement") or ""),
            "action": decision.get("action", "plain"),
            "intent_hint": decision.get("intent"),
            "reason": decision.get("reason"),
            "confidence": decision.get("confidence", enhancement_result.get("analysis_confidence", 0.5)),
            "target_question": target_payload,
            "conversation_id": conversation_id,
            "history_turn_count": len(combined_history),
        }

    @staticmethod
    def _compact_question(question: Dict[str, Any] | None) -> Dict[str, Any] | None:
        if not isinstance(question, dict):
            return None
        normalized = normalize_question(question)
        return {
            "question_id": normalized.get("question_id"),
            "source": normalized.get("source"),
            "topic": normalized.get("topic"),
            "difficulty": normalized.get("difficulty"),
            "title": normalized.get("title"),
            "description": normalized.get("description"),
            "question_type": normalized.get("question_type"),
            "starter_code": normalized.get("starter_code", ""),
            "expected_function": normalized.get("expected_function", ""),
            "hidden_tests": normalized.get("hidden_tests", []),
            "hints": normalized.get("hints", []),
            "answer": normalized.get("answer", ""),
            "examples": normalized.get("examples", []),
            "tags": normalized.get("tags", []),
            "estimated_minutes": normalized.get("estimated_minutes", 10),
        }

    def _question_from_result(self, result: Dict[str, Any]) -> Dict[str, Any] | None:
        details = result.get("details", {}) or {}
        if isinstance(details.get("exercise"), dict):
            return self._compact_question(details["exercise"])
        if isinstance(details.get("question"), dict):
            return self._compact_question(details["question"])
        questions = details.get("questions")
        if isinstance(questions, list) and questions and isinstance(questions[0], dict):
            return self._compact_question(questions[0])
        return None

    async def save_conversation_result(self, user_id: str, request: Dict[str, Any], result: Dict[str, Any]):
        try:
            saved_question = self._question_from_result(result)
            question_id = saved_question.get("question_id") if saved_question else None
            details = result.get("details", {})
            if not question_id and "questions" in details and details["questions"]:
                question_id = details["questions"][0].get("question_id")
            elif not question_id and "exercise" in details:
                question_id = details["exercise"].get("question_id")

            context_manager.save_dialog_history(
                user_id,
                {
                    "user_input": str(request.get("original_content", "")),
                    "agent_response": str(result.get("response", "")),
                    "intent": str(result.get("detected_intent", "unknown")),
                    "topic": str(result.get("details", {}).get("topic", "general")),
                    "question_id": question_id,
                    "question": saved_question,
                    "conversation_id": (
                        request.get("context", {}).get("conversation_id")
                        or request.get("context", {}).get("external_learning_context", {}).get("conversation_id")
                    ),
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
                if saved_question:
                    current_context["last_question"] = saved_question
                    current_context["last_question_preview"] = str(saved_question.get("description", ""))[:160]
                    current_context["last_question_id"] = saved_question.get("question_id")
                    conversation_id = (
                        request.get("context", {}).get("conversation_id")
                        or request.get("context", {}).get("external_learning_context", {}).get("conversation_id")
                    )
                    if conversation_id:
                        current_context["last_conversation_id"] = str(conversation_id)
            context_manager.save_conversation_context(user_id, current_context)
        except Exception as exc:
            logger.error("Saving conversation result failed: %s", exc)

    async def forward_to_main_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self.log_activity(
            "forwarding request to main agent",
            {
                "request_id": request.get("request_id"),
                "request_type": str(request.get("type", "")),
                "was_enhanced": request["enhancement_info"]["was_enhanced"],
                "analysis_confidence": request["enhancement_info"].get("analysis_confidence", 0.5),
                "target_exercise_found": request.get("target_exercise") is not None,
            },
        )
        log_agent_interaction(
            "handoff",
            "EnhancedUserAgent",
            "MainAgent",
            request_id=str(request.get("request_id", "")),
            user_id=str(request.get("user_id", "")),
            payload={
                "request_type": request.get("type"),
                "content": request.get("content"),
                "original_content": request.get("original_content"),
                "enhancement_info": request.get("enhancement_info"),
                "context_decision": request.get("context_decision"),
                "task_context": request.get("context", {}).get("task_context"),
                "recent_history_count": len(request.get("context", {}).get("recent_history", [])),
                "target_exercise_id": (request.get("target_exercise") or {}).get("question_id"),
            },
        )
        result = await self.main_agent.process(request)
        log_agent_interaction(
            "handoff_result",
            "MainAgent",
            "EnhancedUserAgent",
            request_id=str(request.get("request_id", "")),
            user_id=str(request.get("user_id", "")),
            payload={
                "detected_intent": result.get("detected_intent"),
                "intent_analysis": result.get("intent_analysis"),
                "success": result.get("success"),
                "response": result.get("response"),
                "details": result.get("details"),
            },
        )
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
            "detected_intent": str(results.get("detected_intent", "unknown")),
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
