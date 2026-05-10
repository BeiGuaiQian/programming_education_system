"""Exercise generation and answer support agent."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.agents.profile_guidance import (
    build_profile_instruction,
    build_profile_summary,
    infer_user_type,
)
from programming_education_system.models.question_bank import DifficultyLevel, QuestionType
from programming_education_system.models.question_schema import normalize_question
from programming_education_system.utils.agent_interaction_logger import log_agent_interaction
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.utils.question_bank_manager import QuestionBankManager

logger = logging.getLogger(__name__)


DIFFICULTY_ORDER = ["beginner", "intermediate", "advanced"]



class EnhancedExerciseGenerationAgent(BaseAgent):
    """Generate adaptive exercises or provide guided answers."""

    def __init__(self, personal_agent):
        super().__init__("EnhancedExerciseGenerationAgent")
        self.personal_agent = personal_agent
        self.question_bank_manager = QuestionBankManager()

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        user_id = request["user_id"]
        content = request["content"]
        context = request.get("context", {})
        context.setdefault("request_id", request.get("request_id", ""))
        user_profile = await self._load_user_profile(user_id)
        context["user_profile"] = user_profile
        context["profile_instruction"] = build_profile_instruction(user_profile, "exercise")
        analysis = request.get("intent_analysis", {})
        log_agent_interaction(
            "sub_agent_received",
            "MainAgent",
            self.name,
            request_id=str(request.get("request_id", "")),
            user_id=user_id,
            payload={
                "content": content,
                "intent_analysis": analysis,
                "task_context": context.get("task_context"),
                "target_exercise_id": (request.get("target_exercise") or {}).get("question_id"),
                "recent_history_count": len(context.get("recent_history", [])),
                "user_type": infer_user_type(user_profile),
            },
        )

        task_context = context.get("task_context", {}) or {}
        context_action = str(task_context.get("action") or "")
        if (
            context_action in {"answer_current_exercise", "hint_current_exercise", "clarify_missing_context"}
            or analysis.get("needs_exercise_context")
            or request.get("target_exercise")
        ):
            result = await self._handle_answer_request(
                user_id,
                content,
                context,
                request.get("target_exercise"),
                analysis,
            )
        else:
            result = await self._handle_exercise_request(user_id, content, context, analysis)
        log_agent_interaction(
            "sub_agent_completed",
            self.name,
            "MainAgent",
            request_id=str(request.get("request_id", "")),
            user_id=user_id,
            payload={
                "success": result.get("success"),
                "response": result.get("response"),
                "details": result.get("details"),
            },
        )
        return result

    async def _handle_exercise_request(
        self,
        user_id: str,
        content: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        profile = context.get("user_profile") or await self._load_user_profile(user_id)
        constraints = await self._build_exercise_constraints(content, context, analysis, profile)
        topic = constraints["topic"] or self._choose_topic_from_profile(profile)
        difficulty = self._choose_adaptive_difficulty(
            requested=constraints.get("requested_difficulty"),
            profile=profile,
            topic=topic,
            context=context,
        )
        constraints["difficulty"] = difficulty

        selection = await self._select_question_from_bank(constraints)
        question = selection.get("question")
        source = "question_bank" if question else "ai_generated"
        if not question:
            question = await self._generate_exercise_with_llm(content, topic, difficulty, profile, constraints)
            source = "ai_generated"

        output_analysis = await self._analyze_exercise_match(question, constraints)
        if not output_analysis["valid"] and source == "question_bank":
            question = await self._generate_exercise_with_llm(content, topic, difficulty, profile, constraints)
            source = "ai_generated"
            output_analysis = await self._analyze_exercise_match(question, constraints)

        if not output_analysis["valid"]:
            constraints["validation_feedback"] = output_analysis
            question = await self._generate_exercise_with_llm(content, topic, difficulty, profile, constraints)
            source = "ai_generated_retry"
            output_analysis = await self._analyze_exercise_match(question, constraints)

        log_agent_interaction(
            "exercise_selection",
            self.name,
            self.name,
            request_id=str(context.get("request_id", "")),
            user_id=user_id,
            payload={
                "constraints": constraints,
                "candidate_count": selection.get("candidate_count", 0),
                "selected_source": source,
                "selected_question_id": question.get("question_id"),
                "selection_reason": selection.get("reason") or output_analysis.get("reason"),
                "output_analysis": output_analysis,
            },
        )

        learning_chain = self._build_learning_chain(question, profile)
        details = {
            "type": "exercise",
            "topic": question.get("topic", topic or "general"),
            "difficulty": question.get("difficulty", difficulty or "beginner"),
            "personalized": True,
            "source": source,
            "question_count": 1,
            "exercise": question,
            "learning_chain": learning_chain,
            "constraints": constraints,
            "output_analysis": output_analysis,
        }
        await self.personal_agent.track_user_behavior(
            {
                "user_id": user_id,
                "intent": "exercise",
                "topic": details["topic"],
                "difficulty": details["difficulty"],
                "content": content,
            }
        )
        return {"response": self._format_exercise_response(question, source, learning_chain), "details": details, "success": True}

    async def _handle_answer_request(
        self,
        user_id: str,
        content: str,
        context: Dict[str, Any],
        target_exercise: Optional[Dict[str, Any]] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        analysis = analysis or {}
        profile = context.get("user_profile") or await self._load_user_profile(user_id)
        answer_style = await self._build_answer_style(content, context, analysis, profile)
        target_question = self._resolve_target_question(context, target_exercise)
        if target_question:
            description = self._question_description(target_question)
            answer = self._question_answer(target_question)
            source = "question_bank" if answer else "llm_generated"
            if not answer and not answer_style["hint_only"]:
                answer = await self._generate_answer_with_llm(description, profile)
            response = await self._format_contextual_answer(
                question=target_question,
                answer=answer,
                style=answer_style,
                user_id=user_id,
                profile=profile,
            )
            return {
                "response": response,
                "details": {
                    "answer_provided": True,
                    "source": source,
                    "personalized": True,
                    "question": target_question,
                    "answer_style": answer_style,
                },
                "success": True,
            }

        task_context = context.get("task_context", {}) or {}
        if str(task_context.get("action") or "") == "clarify_missing_context":
            return {
                "response": "我在当前会话里没有找到可以解答的上一道题。你可以先让我出一道题，或者把题目内容发给我，我再给你讲解。",
                "details": {"answer_provided": False, "reason": "missing_current_question_context"},
                "success": True,
            }

        inferred_question = self._extract_question_from_request(content)
        answer = await self._generate_answer_with_llm(inferred_question, profile)
        response = await self._format_contextual_answer(
            question={"content": {"description": inferred_question, "answer": answer, "hints": []}},
            answer=answer,
            style=answer_style,
            user_id=user_id,
            profile=profile,
        )
        return {
            "response": response,
            "details": {
                "answer_provided": True,
                "source": "llm_generated_direct",
                "personalized": True,
                "answer_style": answer_style,
            },
            "success": True,
        }

    def _resolve_target_question(
        self,
        context: Dict[str, Any],
        target_exercise: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if isinstance(target_exercise, dict):
            return self._to_display_question(target_exercise)
        conversation_context = context.get("conversation_context") or {}
        current_conversation_id = str(
            context.get("conversation_id")
            or (context.get("external_learning_context") or {}).get("conversation_id")
            or ""
        ) or None
        stored_conversation_id = conversation_context.get("last_conversation_id")
        if (
            current_conversation_id
            and stored_conversation_id
            and str(current_conversation_id) != str(stored_conversation_id)
        ):
            return None
        last_question = conversation_context.get("last_question")
        if isinstance(last_question, dict):
            return self._to_display_question(last_question)
        return self._find_recent_question(context)

    def _find_recent_question(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        recent_history = context.get("recent_history", [])
        current_conversation_id = str(
            context.get("conversation_id")
            or (context.get("external_learning_context") or {}).get("conversation_id")
            or ""
        ) or None
        for item in reversed(recent_history):
            if current_conversation_id and str(item.get("conversation_id") or "") != str(current_conversation_id):
                continue
            if isinstance(item.get("question"), dict):
                return self._to_display_question(item["question"])
            question_id = item.get("question_id")
            if not question_id:
                continue
            if str(question_id).startswith("bank_"):
                numeric_id = str(question_id).split("_", 1)[1]
                if numeric_id.isdigit():
                    question = self.question_bank_manager.question_bank.get_question(int(numeric_id))
                    if question:
                        return self._to_display_question(question.to_dict())
        return None

    def _to_display_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        normalized = normalize_question(
            question,
            source=question.get("source") or "question_bank",
            question_id=question.get("question_id") or (
                f"bank_{question.get('id')}" if question.get("id") is not None else None
            ),
        )
        payload = {
            **normalized["content_payload"],
            "requirements": normalized["content_payload"].get("requirements") or ["完成题目要求"],
        }
        return {
            **normalized,
            "question_id": normalized["question_id"],
            "topic": normalized["topic"],
            "difficulty": normalized["difficulty"],
            "type": normalized["question_type"],
            "content": {
                "title": payload["title"],
                "description": payload["description"],
                "requirements": payload["requirements"],
                "examples": payload["examples"],
                "hints": payload["hints"],
                "answer": payload["answer"],
                "starter_code": payload.get("starter_code", ""),
                "expected_function": payload.get("expected_function", ""),
                "hidden_tests": payload.get("hidden_tests", []),
            },
            "answer": normalized["answer"],
        }

    async def _build_exercise_constraints(
        self,
        content: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
        profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        task_context = context.get("task_context", {}) or {}
        original_input = str(task_context.get("original_input") or "").strip()
        optimized_input = str(task_context.get("optimized_input") or "").strip()
        profile = profile or context.get("user_profile") or {}
        fallback_topic = str(
            analysis.get("topic")
            or task_context.get("topic_hint")
            or self._choose_topic_from_profile(profile)
            or "python_basics"
        )
        fallback_difficulty = str(analysis.get("difficulty") or task_context.get("difficulty") or "beginner")
        if fallback_difficulty not in DIFFICULTY_ORDER:
            fallback_difficulty = "beginner"

        system_prompt = (
            "You are the exercise agent's task-analysis sub-agent. "
            "Read the optimized user input, task context, routing analysis, and user profile. "
            "Produce structured exercise constraints for generation and selection. "
            "Infer only from the provided structured context and do not answer the user. Return strict JSON only."
        )
        user_message = json.dumps(
            {
                "current_input": content,
                "original_input": original_input,
                "optimized_input": optimized_input,
                "task_context": task_context,
                "routing_analysis": analysis,
                "profile_summary": build_profile_summary(profile),
                "allowed_topics": [
                    "python_basics",
                    "data_structures",
                    "algorithms",
                    "oop",
                    "web_development",
                    "data_science",
                    "general_programming",
                ],
                "allowed_difficulties": DIFFICULTY_ORDER,
                "output_schema": {
                    "topic": fallback_topic,
                    "subtopic": "short free-text subtopic, empty if none",
                    "requested_difficulty": fallback_difficulty,
                    "focus_requirements": ["explicit exercise requirements inferred by the agent"],
                    "must_use_question_bank": False,
                    "reason": "short reason",
                },
            },
            ensure_ascii=False,
        )
        parsed: Dict[str, Any] = {}
        try:
            response = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=False,
                task_type="exercise",
            )
            parsed = self._parse_json_response(response)
        except Exception as exc:
            logger.warning("Exercise constraint analysis failed: %s", exc)

        topic = str(parsed.get("topic") or fallback_topic or "python_basics")
        if topic not in {
            "python_basics",
            "data_structures",
            "algorithms",
            "oop",
            "web_development",
            "data_science",
            "general_programming",
        }:
            topic = fallback_topic if fallback_topic != "general_programming" else "python_basics"
        requested_difficulty = str(parsed.get("requested_difficulty") or fallback_difficulty)
        if requested_difficulty not in DIFFICULTY_ORDER:
            requested_difficulty = fallback_difficulty
        focus_requirements = parsed.get("focus_requirements") or []
        if not isinstance(focus_requirements, list):
            focus_requirements = [str(focus_requirements)]
        return {
            "raw_request": content,
            "original_input": original_input or content,
            "optimized_input": optimized_input or content,
            "topic": topic,
            "subtopic": str(parsed.get("subtopic") or "").strip()[:80],
            "focus_requirements": [str(item)[:120] for item in focus_requirements if str(item).strip()][:8],
            "requested_difficulty": requested_difficulty,
            "explicit_difficulty": requested_difficulty,
            "difficulty": requested_difficulty,
            "avoid_question_ids": self._recent_question_ids(context),
            "must_use_question_bank": bool(parsed.get("must_use_question_bank", False)),
            "reason": str(parsed.get("reason") or "llm_constraint_analysis")[:120],
        }

    @staticmethod
    def _recent_question_ids(context: Dict[str, Any]) -> List[str]:
        question_ids: List[str] = []
        conversation_question = (context.get("conversation_context") or {}).get("last_question")
        if isinstance(conversation_question, dict) and conversation_question.get("question_id"):
            question_ids.append(str(conversation_question["question_id"]))
        for item in context.get("recent_history", [])[-12:]:
            question_id = item.get("question_id")
            if question_id:
                question_ids.append(str(question_id))
            question = item.get("question")
            if isinstance(question, dict) and question.get("question_id"):
                question_ids.append(str(question["question_id"]))
        deduped: List[str] = []
        for question_id in question_ids:
            if question_id not in deduped:
                deduped.append(question_id)
        return deduped


    def _collect_question_candidates(self, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        seen = set()
        candidates: List[Dict[str, Any]] = []

        def add_many(items: List[Dict[str, Any]]) -> None:
            for item in items:
                key = self._candidate_key(item)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(item)

        topic = constraints.get("topic")
        search_topic = topic if topic and topic != "general_programming" else None
        add_many(
            self.question_bank_manager.search_questions(
                "",
                topic=search_topic,
                difficulty=constraints.get("difficulty"),
                limit=20,
            )
        )
        if not candidates:
            add_many(
                self.question_bank_manager.search_questions(
                    "",
                    topic=search_topic,
                    difficulty=None,
                    limit=20,
                )
            )
        return candidates

    async def _select_question_from_bank(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        candidates = self._collect_question_candidates(constraints)
        ranked: List[tuple] = []
        for raw_question in candidates[:8]:
            question = self._to_display_question(raw_question)
            output_analysis = await self._analyze_exercise_match(question, constraints)
            if output_analysis["valid"]:
                ranked.append((output_analysis["score"], question, output_analysis))

        if not ranked:
            return {
                "question": None,
                "candidate_count": len(candidates),
                "reason": "no_question_bank_match",
            }
        ranked.sort(key=lambda item: item[0], reverse=True)
        _, question, output_analysis = ranked[0]
        return {
            "question": question,
            "candidate_count": len(candidates),
            "reason": output_analysis.get("reason", "matched_question_bank"),
            "output_analysis": output_analysis,
        }

    @staticmethod
    def _candidate_key(question: Dict[str, Any]) -> str:
        return str(question.get("question_id") or question.get("id") or question.get("description") or question)

    async def _analyze_exercise_match(self, question: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._to_display_question(question)
        system_prompt = (
            "You are the exercise agent's output review sub-agent. "
            "Judge whether the proposed programming exercise satisfies the structured constraints. "
            "Reason from the full request, task context, question content, topic, difficulty, and profile-derived requirements. "
            "Return strict JSON only."
        )
        user_message = json.dumps(
            {
                "constraints": constraints,
                "question": self._question_prompt_payload(normalized),
                "question_meta": {
                    "question_id": normalized.get("question_id"),
                    "topic": normalized.get("topic"),
                    "difficulty": normalized.get("difficulty"),
                    "source": normalized.get("source"),
                },
                "output_schema": {
                    "valid": True,
                    "score": 0,
                    "missing": ["what still does not satisfy the request"],
                    "reason": "short reason",
                },
            },
            ensure_ascii=False,
        )
        try:
            response = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=False,
                task_type="exercise",
            )
            parsed = self._parse_json_response(response)
            if parsed:
                score = parsed.get("score", 0)
                try:
                    score = int(score)
                except (TypeError, ValueError):
                    score = 0
                missing = parsed.get("missing") or []
                if not isinstance(missing, list):
                    missing = [str(missing)]
                return {
                    "valid": bool(parsed.get("valid", False)),
                    "score": score,
                    "missing": [str(item)[:120] for item in missing if str(item).strip()][:8],
                    "reason": str(parsed.get("reason") or "llm_output_review")[:120],
                    "reviewed_by": "llm",
                }
        except Exception as exc:
            logger.warning("Exercise output review failed: %s", exc)
        return self._structural_exercise_check(normalized, constraints)

    def _structural_exercise_check(self, question: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        missing: List[str] = []
        score = 0
        question_id = str(question.get("question_id") or "")
        if question_id and question_id in constraints.get("avoid_question_ids", []):
            missing.append("recently_used_question")
            score -= 10
        requested_topic = constraints.get("topic")
        if requested_topic and requested_topic != "general_programming":
            if question.get("topic") == requested_topic:
                score += 2
            else:
                missing.append(f"topic:{requested_topic}")
        requested_difficulty = constraints.get("difficulty")
        if requested_difficulty in DIFFICULTY_ORDER:
            if question.get("difficulty") == requested_difficulty:
                score += 2
            else:
                missing.append(f"difficulty:{requested_difficulty}")
        description = self._question_description(question).strip()
        if description:
            score += 1
        else:
            missing.append("description")
        if self._question_answer(question):
            score += 1
        else:
            missing.append("reference_answer")
        if (question.get("content", {}) or {}).get("examples"):
            score += 1
        else:
            missing.append("examples")
        if (question.get("content", {}) or {}).get("hints"):
            score += 1
        else:
            missing.append("hints")
        return {
            "valid": not missing and score >= 4,
            "score": score,
            "missing": missing,
            "reason": "structural_output_check",
            "reviewed_by": "structural_fallback",
        }

    async def _generate_exercise_with_llm(
        self,
        content: str,
        topic: str,
        difficulty: str,
        profile: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        constraints = constraints or {}
        profile_instruction = build_profile_instruction(profile, "exercise")
        system_prompt = (
            "You are a programming exercise generation agent. "
            "Generate one Python exercise that satisfies the structured constraints and the user's current request. "
            "The exercise must be verifiable, focused, clear, and appropriate for the user's profile. "
            "Return strict JSON only, with fields: title, description, requirements, examples, hints, answer. "
            f"{profile_instruction}"
        )
        user_message = json.dumps(
            {
                "topic": topic or "general_programming",
                "subtopic": constraints.get("subtopic") or "",
                "difficulty": difficulty or "beginner",
                "focus_requirements": constraints.get("focus_requirements") or [],
                "avoid_question_ids": constraints.get("avoid_question_ids") or [],
                "validation_feedback": constraints.get("validation_feedback"),
                "user_request": content,
                "profile_summary": build_profile_summary(profile),
            },
            ensure_ascii=False,
        )
        response = await llm_client.generate_response(
            system_prompt,
            user_message,
            use_cache=False,
            task_type="exercise",
        )
        parsed = self._parse_json_response(response)
        if not parsed:
            return self._to_display_question({
                "question_id": "generated_llm_unparsed",
                "topic": topic or "general",
                "difficulty": difficulty if difficulty in DIFFICULTY_ORDER else "beginner",
                "type": "coding",
                "content": {
                    "title": "AI 练习题",
                    "description": content,
                    "requirements": ["完成题目要求"],
                    "examples": [],
                    "hints": ["先写出函数签名。", "明确输入和输出关系。", "用一个简单例子手动走一遍。"],
                    "answer": "",
                    "starter_code": "",
                    "expected_function": "",
                    "hidden_tests": [],
                },
                "answer": "",
                "source": "ai_generated",
                "tags": [topic, constraints.get("subtopic"), *constraints.get("focus_requirements", [])],
                "metadata": {"subtopic": constraints.get("subtopic"), "unparsed": True},
            })
        content_payload = {
            "title": parsed.get("title", "AI 练习题"),
            "description": parsed.get("description", content),
            "requirements": parsed.get("requirements", ["完成题目要求"]),
            "examples": parsed.get("examples", []),
            "hints": parsed.get(
                "hints",
                ["先写出函数签名。", "明确输入和输出的关系。", "用一个简单例子手动走一遍。"],
            ),
            "answer": parsed.get("answer", ""),
        }
        safe_difficulty = difficulty if difficulty in DIFFICULTY_ORDER else "beginner"
        return self._to_display_question({
            "question_id": "generated_llm",
            "topic": topic or "general",
            "difficulty": safe_difficulty,
            "type": "coding",
            "content": {
                **content_payload,
                "starter_code": "",
                "expected_function": "",
                "hidden_tests": [],
            },
            "answer": content_payload["answer"],
            "source": "ai_generated",
            "tags": [topic, constraints.get("subtopic"), *constraints.get("focus_requirements", [])],
            "metadata": {"title": content_payload["title"], "adaptive": True, "subtopic": constraints.get("subtopic")},
        })

    async def _generate_answer_with_llm(self, question_text: str, profile: Optional[Dict[str, Any]] = None) -> str:
        profile = profile or {}
        system_prompt = (
            "角色：你是编程助教。\n"
            "任务：为一道编程题提供教学型解答。\n"
            "教学策略：先讲思路，再给代码；先提示，再答案；指出常见错误。\n"
            "输出格式：使用中文，分为「解题思路」「参考代码」「常见错误」「变式练习」。"
            "\n\n"
            f"{build_profile_instruction(profile, 'exercise')}"
        )
        user_message = (
            f"题目:\n{question_text}\n\n"
            f"用户画像摘要:\n{build_profile_summary(profile)}\n\n"
            "请给出教学型参考解答。"
        )
        return await llm_client.generate_response(
            system_prompt,
            user_message,
            use_cache=False,
            task_type="exercise",
        )

    async def _build_answer_style(
        self,
        content: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
        profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        task_context = context.get("task_context", {}) or {}
        original_input = str(task_context.get("original_input") or "").strip()
        optimized_input = str(task_context.get("optimized_input") or "").strip()
        action = str(task_context.get("action") or "")
        teaching_mode = str(analysis.get("teaching_mode") or "explain")
        already_answered = task_context.get("already_answered", [])
        if not isinstance(already_answered, list):
            already_answered = []
        profile = profile or context.get("user_profile") or {}

        system_prompt = (
            "You are the exercise explanation agent's response-style planner. "
            "Read the optimized request, task context, routing analysis, and user profile, then decide how the explanation should be written. "
            "Infer style from the full input and return strict JSON only."
        )
        user_message = json.dumps(
            {
                "current_input": content,
                "original_input": original_input,
                "optimized_input": optimized_input,
                "task_context": task_context,
                "routing_analysis": analysis,
                "profile_summary": build_profile_summary(profile),
                "allowed_response_kinds": [
                    "hint",
                    "guided_answer",
                    "direct_answer",
                    "detailed",
                    "simplified",
                    "code_walkthrough",
                ],
                "output_schema": {
                    "response_kind": "guided_answer",
                    "hint_only": False,
                    "wants_direct_answer": False,
                    "wants_detail": False,
                    "wants_line_by_line": False,
                    "wants_simple": False,
                    "wants_concise": False,
                    "avoid_repetition": False,
                    "focus": ["aspects to emphasize"],
                    "reason": "short reason",
                },
            },
            ensure_ascii=False,
        )
        parsed: Dict[str, Any] = {}
        try:
            response = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=False,
                task_type="exercise",
            )
            parsed = self._parse_json_response(response)
        except Exception as exc:
            logger.warning("Exercise answer style planning failed: %s", exc)

        allowed_kinds = {"hint", "guided_answer", "direct_answer", "detailed", "simplified", "code_walkthrough"}
        response_kind = str(parsed.get("response_kind") or "").strip()
        if response_kind not in allowed_kinds:
            response_kind = "hint" if action == "hint_current_exercise" or teaching_mode == "hint" else "guided_answer"
        focus = parsed.get("focus") or []
        if not isinstance(focus, list):
            focus = [str(focus)]
        avoid_repetition = bool(parsed.get("avoid_repetition")) if parsed else bool(already_answered)
        hint_only = bool(parsed.get("hint_only")) if parsed else response_kind == "hint"

        return {
            "response_kind": response_kind,
            "hint_only": hint_only,
            "wants_direct_answer": bool(parsed.get("wants_direct_answer", response_kind == "direct_answer")),
            "wants_detail": bool(parsed.get("wants_detail", response_kind == "detailed")),
            "wants_line_by_line": bool(parsed.get("wants_line_by_line", response_kind == "code_walkthrough")),
            "wants_simple": bool(parsed.get("wants_simple", response_kind == "simplified")),
            "wants_concise": bool(parsed.get("wants_concise", False)),
            "avoid_repetition": avoid_repetition,
            "focus": [str(item)[:120] for item in focus if str(item).strip()][:6] or [str(task_context.get("user_requirement") or "current request")],
            "action": action,
            "teaching_mode": teaching_mode or "explain",
            "context_summary": str(task_context.get("context_summary") or "").strip(),
            "already_answered": [str(item) for item in already_answered[:6] if str(item).strip()],
            "original_input": original_input or content,
            "optimized_input": optimized_input or content,
            "style_reason": str(parsed.get("reason") or "agent_style_planning")[:120],
        }

    async def _format_contextual_answer(
        self,
        question: Dict[str, Any],
        answer: str,
        style: Dict[str, Any],
        user_id: str,
        profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        llm_response = await self._generate_contextual_answer_with_llm(question, answer, style, user_id, profile)
        if self._is_usable_llm_answer(llm_response):
            return llm_response.strip()
        return self._format_contextual_answer_fallback(question, answer, style)

    async def _generate_contextual_answer_with_llm(
        self,
        question: Dict[str, Any],
        answer: str,
        style: Dict[str, Any],
        user_id: str,
        profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        profile = profile or await self._load_user_profile(user_id)
        system_prompt = (
            "角色：你是编程练习讲解智能体。\n"
            "任务：根据学生本轮具体要求讲解当前题目，而不是固定复述参考答案。\n"
            "硬性要求：\n"
            "1. 必须直接回应 current_request 中的要求。\n"
            "2. 题目和参考答案是主要依据，不要讲其他题。\n"
            "3. 如果 response_kind=hint，只给分级提示和引导问题，不给完整代码。\n"
            "4. 如果用户要求详细、进一步、逐步、每一步，要展开思路、变量变化、代码步骤和原因。\n"
            "5. 如果 already_answered 非空，避免完整复述这些点；需要重复时换角度并补充新细节。\n"
            "6. 语言自然，像助教现场讲题，不要写成模板说明，不要提到系统、上下文、JSON。\n"
            "7. 输出中文，可使用必要的 Markdown 小标题和代码块。"
            "\n\n"
            f"{build_profile_instruction(profile, 'exercise')}"
        )
        user_message = json.dumps(
            {
                "current_request": style.get("optimized_input") or style.get("original_input"),
                "original_input": style.get("original_input"),
                "response_kind": style.get("response_kind"),
                "focus": style.get("focus"),
                "avoid_repetition": style.get("avoid_repetition"),
                "context_summary": style.get("context_summary"),
                "already_answered": style.get("already_answered"),
                "teaching_mode": style.get("teaching_mode"),
                "question": self._question_prompt_payload(question),
                "reference_answer": answer,
                "user_profile": {
                    "programming_level": profile.get("programming_level"),
                    "weak_topics": profile.get("weak_topics", []),
                    "preferred_topics": profile.get("preferred_topics", []),
                    "summary": build_profile_summary(profile),
                },
            },
            ensure_ascii=False,
        )
        try:
            return await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=False,
                task_type="exercise",
            )
        except Exception as exc:
            logger.warning("Contextual exercise explanation failed: %s", exc)
            return ""

    async def _load_user_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            return await self.personal_agent.get_user_profile(user_id)
        except Exception as exc:
            logger.warning("Loading user profile for exercise agent failed: %s", exc)
            return {}

    @staticmethod
    def _is_usable_llm_answer(response: str) -> bool:
        return bool(response and len(response.strip()) >= 30)

    def _format_contextual_answer_fallback(
        self,
        question: Dict[str, Any],
        answer: str,
        style: Dict[str, Any],
    ) -> str:
        content = question.get("content", {}) or {}
        title = content.get("title") or question.get("title") or "这道题"
        description = self._question_description(question)
        hints = content.get("hints") or question.get("hints") or []
        examples = content.get("examples") or question.get("examples") or []

        if style.get("hint_only"):
            return self._format_hint_only_answer(title, description, hints)

        if style.get("response_kind") == "direct_answer":
            lines = [
                "可以，直接给你参考答案：",
                "",
                f"题目: {title}",
            ]
            if answer:
                lines.extend(["", self._format_code_or_text(answer)])
            else:
                lines.append("\n这道题暂时没有可用的参考答案，我可以先帮你拆解思路。")
            return "\n".join(lines)

        intro = "这次我换个角度讲，重点放在你追问的部分。" if style.get("avoid_repetition") else "这道题可以这样理解。"
        if style.get("wants_simple"):
            intro = "换成更直白的话说，这道题就是先把目标拆小，再把步骤写成代码。"

        lines = [
            intro,
            "",
            f"题目: {title}",
            f"核心目标: {description[:260]}",
            "",
            "1. 先看目标",
            "先确认函数要接收什么、返回什么，以及有没有特殊输入。不要急着写代码，先用一个小例子手算一遍。",
            "",
            "2. 再拆步骤",
            "把题目拆成“初始化状态 -> 重复更新 -> 返回结果”三个部分。循环题尤其要盯住变量在每一轮之后代表什么。",
            "",
            "3. 为什么这样写",
            "这样写的好处是每一步状态都很明确，既方便检查边界情况，也能避免把上一轮和下一轮的值混在一起。",
        ]

        if examples:
            example = examples[0]
            lines.extend(
                [
                    "",
                    "4. 用例子走一遍",
                    f"可以先拿 `{example.get('input', '')}` 手动推一遍，看看是否能得到 `{example.get('output', '')}`。",
                ]
            )

        if answer:
            lines.extend(["", "参考代码:", self._format_code_or_text(answer)])
            if style.get("wants_line_by_line") or style.get("wants_detail"):
                walkthrough = self._build_code_walkthrough(answer)
                if walkthrough:
                    lines.extend(["", "代码怎么读:", walkthrough])

        lines.extend(
            [
                "",
                "容易出错的地方:",
                "- 忘记处理边界输入。",
                "- 循环范围多一轮或少一轮。",
                "- 更新变量时顺序不清楚，导致后面的值用错。",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _format_hint_only_answer(title: str, description: str, hints: List[Any]) -> str:
        lines = [
            "先不给完整答案，我们按提示往前推。",
            "",
            f"题目: {title}",
            f"你要解决的是: {description[:260]}",
            "",
            "可以按这个顺序想:",
        ]
        if hints:
            lines.extend(f"{index}. {str(hint)}" for index, hint in enumerate(hints[:3], start=1))
        else:
            lines.extend(
                [
                    "1. 先写出函数名、参数和返回值。",
                    "2. 用一个最小输入手算结果。",
                    "3. 把手算过程翻译成条件判断或循环。",
                ]
            )
        lines.extend(["", "如果你卡在某一步，可以直接说“第几步不会”，我再只讲那一步。"])
        return "\n".join(lines)

    @staticmethod
    def _build_code_walkthrough(answer: str) -> str:
        code_lines = [
            line.rstrip()
            for line in answer.splitlines()
            if line.strip() and not line.strip().startswith("```")
        ]
        if not code_lines:
            return ""
        explanations: List[str] = []
        for line in code_lines[:12]:
            stripped = line.strip()
            if stripped.startswith("def "):
                meaning = "定义函数入口，参数就是题目给你的输入。"
            elif stripped.startswith("if "):
                meaning = "处理特殊情况或边界条件。"
            elif stripped.startswith("for ") or stripped.startswith("while "):
                meaning = "重复执行核心更新逻辑。"
            elif "return" in stripped:
                meaning = "把最终结果交回给调用者。"
            elif "=" in stripped:
                meaning = "保存或更新当前状态。"
            else:
                meaning = "完成当前步骤的一部分逻辑。"
            explanations.append(f"- `{stripped}`：{meaning}")
        return "\n".join(explanations)

    @staticmethod
    def _format_code_or_text(answer: str) -> str:
        stripped = answer.strip()
        if not stripped:
            return ""
        if "```" in stripped:
            return stripped
        looks_like_code = bool(re.search(r"^\s*(def|class|import|from|if|for|while|return)\b", stripped, re.MULTILINE))
        if looks_like_code:
            return f"```python\n{stripped}\n```"
        return stripped

    @staticmethod
    def _question_description(question: Dict[str, Any]) -> str:
        content = question.get("content", {}) or {}
        return str(
            content.get("description")
            or question.get("description")
            or content.get("title")
            or question.get("title")
            or ""
        )

    @staticmethod
    def _question_answer(question: Dict[str, Any]) -> str:
        content = question.get("content", {}) or {}
        return str(content.get("answer") or question.get("answer") or "")

    def _question_prompt_payload(self, question: Dict[str, Any]) -> Dict[str, Any]:
        content = question.get("content", {}) or {}
        return {
            "question_id": question.get("question_id"),
            "topic": question.get("topic"),
            "difficulty": question.get("difficulty"),
            "title": content.get("title") or question.get("title"),
            "description": self._question_description(question),
            "requirements": content.get("requirements") or question.get("requirements") or [],
            "examples": content.get("examples") or question.get("examples") or [],
            "hints": content.get("hints") or question.get("hints") or [],
            "starter_code": content.get("starter_code") or question.get("starter_code") or "",
            "expected_function": content.get("expected_function") or question.get("expected_function") or "",
        }

    def _format_exercise_response(self, question: Dict[str, Any], source: str, learning_chain: Dict[str, Any]) -> str:
        content = question["content"]
        lines = [
            "已生成练习题:",
            "",
            f"标题: {content.get('title', '练习题')}",
            f"主题: {question.get('topic', 'general')} | 难度: {question.get('difficulty', 'beginner')}",
            f"描述: {content.get('description', '')}",
            "",
            "要求:",
        ]
        lines.extend(f"- {item}" for item in content.get("requirements", []) or ["完成题目要求"])
        if content.get("examples"):
            lines.append("")
            lines.append("示例:")
            for example in content["examples"]:
                lines.append(f"- 输入: {example.get('input', '')}")
                lines.append(f"  输出: {example.get('output', '')}")
        if content.get("hints"):
            lines.append("")
            lines.append("分级提示:")
            for index, hint in enumerate(content["hints"][:3], start=1):
                lines.append(f"{index}. {hint}")
        lines.append("")
        lines.append(f"下一步: {learning_chain['next_step']}")
        lines.append(f"来源: {source}")
        return "\n".join(lines)

    @staticmethod
    def _format_guided_answer(question_text: str, answer: str) -> str:
        return (
            "参考解答\n\n"
            "建议先自己尝试 5 到 10 分钟。如果卡住，再按下面顺序查看：\n"
            "1. 先确认输入、输出和边界条件。\n"
            "2. 再写出函数签名和核心逻辑。\n"
            "3. 最后对照参考代码检查。\n\n"
            f"题目摘要:\n{question_text[:500]}\n\n"
            f"{answer}"
        )

    def _build_learning_chain(self, question: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        topic = question.get("topic", "general")
        difficulty = question.get("difficulty", "beginner")
        mastery = profile.get("knowledge_mastery", {}).get(topic, 0.5)
        if mastery < 0.45:
            next_step = "完成后先看提示订正，再做一道同主题基础变式题。"
            follow_up_difficulty = "beginner"
        elif mastery > 0.75 and difficulty != "advanced":
            next_step = "完成后尝试改写成更通用的函数，并挑战进阶变式题。"
            follow_up_difficulty = self._next_difficulty(difficulty)
        else:
            next_step = "完成后提交代码评测，系统会根据结果推荐下一题。"
            follow_up_difficulty = difficulty
        return {
            "topic": topic,
            "current_mastery": mastery,
            "follow_up_difficulty": follow_up_difficulty,
            "next_step": next_step,
        }

    @staticmethod
    def _parse_json_response(response: str) -> Dict[str, Any]:
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {}

    @staticmethod
    def _extract_question_from_request(content: str) -> str:
        return content.strip() or content

    @staticmethod
    def _choose_topic_from_profile(profile: Dict[str, Any]) -> str:
        weak_topics = profile.get("weak_topics", [])
        if weak_topics:
            return weak_topics[0]
        preferred_topics = profile.get("preferred_topics", [])
        return preferred_topics[0] if preferred_topics else "python_basics"

    @staticmethod
    def _choose_adaptive_difficulty(
        requested: Optional[str],
        profile: Dict[str, Any],
        topic: str,
        context: Dict[str, Any],
    ) -> str:
        if requested in DIFFICULTY_ORDER:
            return requested
        mastery = profile.get("knowledge_mastery", {}).get(topic, 0.5)
        recent_score = context.get("learning_progress", {}).get("last_score")
        if isinstance(recent_score, (int, float)) and recent_score < 60:
            return "beginner"
        if mastery >= 0.78:
            return "advanced"
        if mastery >= 0.55:
            return "intermediate"
        return "beginner"

    @staticmethod
    def _next_difficulty(difficulty: str) -> str:
        index = DIFFICULTY_ORDER.index(difficulty) if difficulty in DIFFICULTY_ORDER else 0
        return DIFFICULTY_ORDER[min(index + 1, len(DIFFICULTY_ORDER) - 1)]
