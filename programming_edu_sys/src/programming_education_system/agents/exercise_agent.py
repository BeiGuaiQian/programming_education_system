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

SUBTOPIC_KEYWORDS = {
    "dynamic_programming": ["动态规划", "dp", "dynamic programming", "状态转移", "最优子结构", "爬楼梯", "背包"],
    "iteration": ["迭代", "循环", "iteration", "iterative", "for", "while"],
    "recursion": ["递归", "recursion", "recursive", "基准情况", "递归情况"],
    "sorting": ["排序", "sort", "冒泡", "选择排序", "插入排序", "快速排序"],
    "searching": ["查找", "搜索", "search", "二分", "binary search"],
    "functions": ["函数", "function", "def", "return"],
}


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

        if self._is_answer_request(content) or analysis.get("needs_exercise_context") or request.get("target_exercise"):
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
        constraints = self._build_exercise_constraints(content, context, analysis)
        topic = constraints["topic"] or self._choose_topic_from_profile(profile)
        difficulty = self._choose_adaptive_difficulty(
            requested=constraints.get("requested_difficulty"),
            profile=profile,
            topic=topic,
            context=context,
        )
        constraints["difficulty"] = difficulty

        selection = self._select_question_from_bank(constraints)
        question = selection.get("question")
        source = "question_bank" if question else "ai_generated"
        if not question:
            question = await self._generate_exercise_with_llm(content, topic, difficulty, profile, constraints)
            validation = self._analyze_exercise_match(question, constraints)
            if not validation["valid"]:
                question = self._build_rule_based_exercise(content, topic, difficulty, constraints)
                source = "rule_based_generated"
            else:
                source = "ai_generated"

        output_analysis = self._analyze_exercise_match(question, constraints)
        if not output_analysis["valid"] and source == "question_bank":
            question = await self._generate_exercise_with_llm(content, topic, difficulty, profile, constraints)
            source = "ai_generated"
            output_analysis = self._analyze_exercise_match(question, constraints)

        if not output_analysis["valid"]:
            question = self._build_rule_based_exercise(content, topic, difficulty, constraints)
            source = "rule_based_generated"
            output_analysis = self._analyze_exercise_match(question, constraints)

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
        answer_style = self._build_answer_style(content, context, analysis)
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

        if self._is_vague_answer_followup(content):
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

    def _build_exercise_constraints(
        self,
        content: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        task_context = context.get("task_context", {}) or {}
        original_input = str(task_context.get("original_input") or "").strip()
        optimized_input = str(task_context.get("optimized_input") or "").strip()
        combined = "\n".join([original_input, content, optimized_input]).strip()
        explicit_difficulty = self._infer_difficulty(combined)
        analysis_difficulty = str(analysis.get("difficulty") or "")
        requested_difficulty = explicit_difficulty
        if not requested_difficulty and analysis_difficulty in {"intermediate", "advanced"}:
            requested_difficulty = analysis_difficulty

        subtopic = self._infer_subtopic(combined)
        topic = analysis.get("topic") or self._infer_topic(combined) or "general_programming"
        if topic == "general_programming" and subtopic in {"dynamic_programming", "iteration", "recursion", "sorting", "searching"}:
            topic = "algorithms"
        if topic == "general_programming" and subtopic == "functions":
            topic = "python_basics"

        keywords = self._extract_request_keywords(combined, subtopic)
        return {
            "raw_request": content,
            "original_input": original_input or content,
            "optimized_input": optimized_input or content,
            "topic": topic,
            "subtopic": subtopic,
            "keywords": keywords,
            "requested_difficulty": requested_difficulty,
            "explicit_difficulty": explicit_difficulty,
            "difficulty": requested_difficulty or analysis_difficulty or "beginner",
            "avoid_question_ids": self._recent_question_ids(context),
            "must_match_keywords": bool(keywords),
        }

    @staticmethod
    def _infer_subtopic(content: str) -> Optional[str]:
        lowered = content.lower()
        for subtopic, keywords in SUBTOPIC_KEYWORDS.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                return subtopic
        return None

    @staticmethod
    def _extract_request_keywords(content: str, subtopic: Optional[str]) -> List[str]:
        lowered = content.lower()
        keywords: List[str] = []
        if subtopic and subtopic in SUBTOPIC_KEYWORDS:
            keywords.extend(SUBTOPIC_KEYWORDS[subtopic][:4])
        for keyword_group in SUBTOPIC_KEYWORDS.values():
            for keyword in keyword_group:
                if keyword.lower() in lowered and keyword not in keywords:
                    keywords.append(keyword)
        return keywords[:8]

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

    def _select_question_from_bank(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        candidates = self._collect_question_candidates(constraints)
        ranked: List[tuple] = []
        for raw_question in candidates:
            question = self._to_display_question(raw_question)
            output_analysis = self._analyze_exercise_match(question, constraints)
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

        for keyword in constraints.get("keywords", [])[:5]:
            add_many(self.question_bank_manager.search_questions(keyword=keyword, limit=12))

        topic = constraints.get("topic")
        add_many(
            self.question_bank_manager.search_questions(
                keyword="",
                topic=topic if topic and topic != "general_programming" else None,
                difficulty=constraints.get("difficulty"),
                limit=20,
            )
        )
        if constraints.get("explicit_difficulty"):
            add_many(
                self.question_bank_manager.search_questions(
                    keyword="",
                    topic=topic if topic and topic != "general_programming" else None,
                    difficulty=None,
                    limit=20,
                )
            )
        return candidates

    @staticmethod
    def _candidate_key(question: Dict[str, Any]) -> str:
        return str(question.get("question_id") or question.get("id") or question.get("description") or question)

    def _analyze_exercise_match(self, question: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._to_display_question(question)
        search_text = self._question_search_text(normalized)
        score = 0
        missing: List[str] = []
        matched_keywords = [
            keyword
            for keyword in constraints.get("keywords", [])
            if keyword.lower() in search_text
        ]

        question_id = str(normalized.get("question_id") or "")
        if question_id and question_id in constraints.get("avoid_question_ids", []):
            missing.append("recently_used_question")
            score -= 10

        requested_topic = constraints.get("topic")
        if requested_topic and requested_topic != "general_programming":
            if normalized.get("topic") == requested_topic:
                score += 2
            else:
                missing.append(f"topic:{requested_topic}")

        requested_difficulty = constraints.get("difficulty")
        if constraints.get("explicit_difficulty"):
            if normalized.get("difficulty") == requested_difficulty:
                score += 3
            else:
                missing.append(f"difficulty:{requested_difficulty}")
        elif normalized.get("difficulty") == requested_difficulty:
            score += 1

        if constraints.get("must_match_keywords"):
            if matched_keywords:
                score += 5 + min(len(matched_keywords), 3)
            else:
                missing.append("requested_keyword_or_subtopic")

        description = self._question_description(normalized).strip()
        request_texts = {
            str(constraints.get("raw_request") or "").strip(),
            str(constraints.get("optimized_input") or "").strip(),
        }
        if description and description not in request_texts:
            score += 1
        else:
            missing.append("concrete_description")
        if self._question_answer(normalized):
            score += 1
        else:
            missing.append("reference_answer")
        if normalized.get("content", {}).get("examples"):
            score += 1
        else:
            missing.append("examples")
        if normalized.get("content", {}).get("hints"):
            score += 1
        else:
            missing.append("hints")

        valid = not missing and score >= (7 if constraints.get("must_match_keywords") else 3)
        return {
            "valid": valid,
            "score": score,
            "missing": missing,
            "matched_keywords": matched_keywords,
            "reason": "matched_requirements" if valid else "missing_requirements",
        }

    def _question_search_text(self, question: Dict[str, Any]) -> str:
        content = question.get("content", {}) or {}
        parts = [
            question.get("question_id", ""),
            question.get("topic", ""),
            question.get("difficulty", ""),
            content.get("title", ""),
            content.get("description", ""),
            " ".join(str(item) for item in content.get("requirements", [])),
            " ".join(str(item) for item in content.get("hints", [])),
            " ".join(str(item) for item in content.get("examples", [])),
            self._question_answer(question),
            " ".join(str(item) for item in question.get("tags", [])),
            json.dumps(question.get("metadata", {}), ensure_ascii=False),
        ]
        return " ".join(parts).lower()

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
            "角色：你是编程教育出题智能体。\n"
            "任务：生成一道严格符合用户要求的 Python 编程练习题。\n"
            "输出：只返回 JSON，不要 Markdown，不要解释。\n"
            "质量要求：题目必须可验证、目标单一、描述清楚；提示应由浅到深；参考答案应能运行。\n"
            "硬性要求：必须匹配给定主题、子主题、关键词和难度。用户要求简单时不得生成中高级题。\n"
            "JSON schema：{\n"
            '  "title": "题目标题",\n'
            '  "description": "题目描述",\n'
            '  "requirements": ["明确要求"],\n'
            '  "examples": [{"input": "函数调用示例", "output": "期望输出"}],\n'
            '  "hints": ["轻提示", "中提示", "强提示"],\n'
            '  "answer": "Python参考代码"\n'
            "}"
            "\n\n"
            f"{profile_instruction}\n"
            "出题时必须把画像落到题面设计里：初学者目标单一、示例更多、提示更细；稳定提升型给适度变式；进阶型可以加入复杂度、边界和工程化要求。"
        )
        user_message = f"""主题: {topic or 'general_programming'}
子主题: {constraints.get('subtopic') or '未指定'}
难度: {difficulty or 'beginner'}
必须体现的关键词: {constraints.get('keywords') or []}
需要避开的题目ID: {constraints.get('avoid_question_ids') or []}
用户请求: {content}
用户画像摘要:
{build_profile_summary(profile)}

请生成练习题 JSON。"""
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
                "tags": constraints.get("keywords", []),
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
            "tags": [topic, constraints.get("subtopic"), *constraints.get("keywords", [])],
            "metadata": {"title": content_payload["title"], "adaptive": True, "subtopic": constraints.get("subtopic")},
        })

    def _build_rule_based_exercise(
        self,
        content: str,
        topic: str,
        difficulty: str,
        constraints: Dict[str, Any],
    ) -> Dict[str, Any]:
        subtopic = constraints.get("subtopic")
        if subtopic == "dynamic_programming":
            payload = {
                "title": "动态规划入门：爬楼梯",
                "description": "编写函数 climb_stairs(n)，使用动态规划计算到达第 n 级台阶共有多少种走法。每次可以走 1 级或 2 级台阶，n 为正整数。",
                "requirements": [
                    "函数名为 climb_stairs，参数 n 表示台阶数",
                    "使用动态规划思想，明确状态含义和状态转移",
                    "返回走到第 n 级台阶的不同方法数",
                    "按简单入门难度实现，不需要处理复杂输入",
                ],
                "examples": [
                    {"input": "climb_stairs(1)", "output": "1"},
                    {"input": "climb_stairs(2)", "output": "2"},
                    {"input": "climb_stairs(5)", "output": "8"},
                ],
                "hints": [
                    "设 dp[i] 表示到达第 i 级台阶的方法数。",
                    "到达第 i 级可以从 i-1 走一步，也可以从 i-2 走两步。",
                    "状态转移为 dp[i] = dp[i-1] + dp[i-2]。",
                ],
                "answer": (
                    "def climb_stairs(n):\n"
                    "    if n <= 2:\n"
                    "        return n\n"
                    "    dp = [0] * (n + 1)\n"
                    "    dp[1], dp[2] = 1, 2\n"
                    "    for i in range(3, n + 1):\n"
                    "        dp[i] = dp[i - 1] + dp[i - 2]\n"
                    "    return dp[n]"
                ),
            }
        elif subtopic == "recursion":
            payload = {
                "title": "递归入门：列表求和",
                "description": "编写函数 recursive_sum(numbers)，使用递归计算列表中所有整数的和。",
                "requirements": ["必须使用递归", "空列表返回 0", "不得使用 sum()"],
                "examples": [{"input": "recursive_sum([1, 2, 3])", "output": "6"}],
                "hints": ["先写空列表的基准情况。", "每次取第一个元素，加上剩余列表的递归结果。"],
                "answer": (
                    "def recursive_sum(numbers):\n"
                    "    if not numbers:\n"
                    "        return 0\n"
                    "    return numbers[0] + recursive_sum(numbers[1:])"
                ),
            }
        elif subtopic == "iteration":
            payload = {
                "title": "迭代入门：累加偶数",
                "description": "编写函数 sum_even(numbers)，使用循环计算列表中所有偶数的和。",
                "requirements": ["必须使用循环", "遇到偶数才累加", "返回整数结果"],
                "examples": [{"input": "sum_even([1, 2, 3, 4])", "output": "6"}],
                "hints": ["先准备 total = 0。", "遍历列表，判断数字能否被 2 整除。"],
                "answer": (
                    "def sum_even(numbers):\n"
                    "    total = 0\n"
                    "    for number in numbers:\n"
                    "        if number % 2 == 0:\n"
                    "            total += number\n"
                    "    return total"
                ),
            }
        else:
            payload = {
                "title": "函数练习：计算平方和",
                "description": "编写函数 square_sum(a, b)，返回两个数字平方后的和。",
                "requirements": ["定义函数", "使用 return 返回结果", "保持实现简洁"],
                "examples": [{"input": "square_sum(2, 3)", "output": "13"}],
                "hints": ["平方可以写成 x * x。", "先分别计算两个平方，再相加。"],
                "answer": "def square_sum(a, b):\n    return a * a + b * b",
            }
        return self._to_display_question({
            "question_id": f"generated_rule_{subtopic or topic or 'general'}",
            "topic": topic if topic != "general_programming" else "python_basics",
            "difficulty": difficulty if difficulty in DIFFICULTY_ORDER else "beginner",
            "type": "coding",
            "content": {
                **payload,
                "starter_code": "",
                "expected_function": "",
                "hidden_tests": [],
            },
            "answer": payload["answer"],
            "source": "rule_based_generated",
            "tags": [topic, subtopic, *constraints.get("keywords", [])],
            "metadata": {"subtopic": subtopic, "requested_content": content},
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

    def _build_answer_style(
        self,
        content: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        task_context = context.get("task_context", {}) or {}
        original_input = str(task_context.get("original_input") or "").strip()
        optimized_input = str(task_context.get("optimized_input") or "").strip()
        combined = "\n".join([original_input, content, optimized_input]).lower()
        action = str(task_context.get("action") or "")
        teaching_mode = str(analysis.get("teaching_mode") or "")

        direct_terms = [
            "答案",
            "给答案",
            "完整答案",
            "直接给",
            "参考代码",
            "完整代码",
            "最终代码",
            "solution",
            "answer",
            "full code",
            "final code",
        ]
        hint_terms = [
            "提示",
            "给点思路",
            "引导",
            "不要答案",
            "别给答案",
            "先别给代码",
            "不会",
            "没思路",
            "没有思路",
            "卡住",
            "做不出来",
            "写不出来",
            "hint",
            "stuck",
        ]
        detail_terms = [
            "详细",
            "进一步",
            "展开",
            "每一步",
            "一步步",
            "逐步",
            "具体",
            "为什么",
            "原理",
            "过程",
            "再讲",
            "讲一遍",
            "看不懂",
            "多讲",
            "深入",
            "执行过程",
            "detail",
            "detailed",
            "more",
            "step by step",
            "step-by-step",
        ]
        line_terms = ["逐行", "每行", "代码每一步", "每一步的含义", "代码含义", "执行过程", "line by line"]
        simple_terms = ["简单点", "通俗", "白话", "换种说法", "换个说法", "听不懂", "看不懂", "simpler"]
        concise_terms = ["简洁", "简单说", "短一点", "只要", "不用太长", "brief", "short"]
        repeat_terms = ["再", "继续", "进一步", "展开", "讲一遍", "换种", "换个", "again", "continue"]

        wants_direct_answer = any(term in combined for term in direct_terms)
        wants_detail = any(term in combined for term in detail_terms)
        wants_line_by_line = any(term in combined for term in line_terms)
        wants_simple = any(term in combined for term in simple_terms)
        wants_concise = any(term in combined for term in concise_terms)
        asks_for_hint = any(term in combined for term in hint_terms)
        hint_only = (action == "hint_current_exercise" or asks_for_hint) and not (
            wants_direct_answer or wants_detail or wants_line_by_line
        )
        already_answered = task_context.get("already_answered", [])
        if not isinstance(already_answered, list):
            already_answered = []

        focus = self._extract_answer_focus(combined)
        if hint_only:
            response_kind = "hint"
        elif wants_line_by_line:
            response_kind = "code_walkthrough"
        elif wants_detail:
            response_kind = "detailed"
        elif wants_simple:
            response_kind = "simplified"
        elif wants_direct_answer:
            response_kind = "direct_answer"
        else:
            response_kind = "guided_answer"

        return {
            "response_kind": response_kind,
            "hint_only": hint_only,
            "wants_direct_answer": wants_direct_answer,
            "wants_detail": wants_detail,
            "wants_line_by_line": wants_line_by_line,
            "wants_simple": wants_simple,
            "wants_concise": wants_concise,
            "avoid_repetition": bool(already_answered) and any(term in combined for term in repeat_terms),
            "focus": focus,
            "action": action,
            "teaching_mode": teaching_mode or "explain",
            "context_summary": str(task_context.get("context_summary") or "").strip(),
            "already_answered": [str(item) for item in already_answered[:6] if str(item).strip()],
            "original_input": original_input or content,
            "optimized_input": optimized_input or content,
        }

    @staticmethod
    def _extract_answer_focus(combined: str) -> List[str]:
        focus_map = {
            "解题思路": ["思路", "怎么想", "从哪入手", "分析"],
            "代码步骤": ["代码", "写法", "实现", "逐行", "每行", "每一步"],
            "执行过程": ["执行过程", "运行过程", "变量变化", "过程"],
            "原因解释": ["为什么", "原理", "原因"],
            "边界条件": ["边界", "特殊情况", "输入输出"],
            "测试方法": ["测试", "用例", "检查"],
            "常见错误": ["错误", "坑", "容易错"],
        }
        focus = [
            label
            for label, terms in focus_map.items()
            if any(term in combined for term in terms)
        ]
        return focus or ["解题思路", "代码步骤"]

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
        if not response or len(response.strip()) < 30:
            return False
        fallback_markers = [
            "目前无法调用大模型",
            "基础模式",
            "按系统内置逻辑",
            "我先按基础模式",
        ]
        if any(marker in response for marker in fallback_markers):
            return False
        old_template = "参考解答\n\n建议先自己尝试 5 到 10 分钟"
        return old_template not in response

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
        answer_phrases = ["这道题的答案", "这个题目的解答", "请解答", "求答案", "帮我解答", "怎么做"]
        result = content
        for phrase in answer_phrases:
            result = result.replace(phrase, "")
        return result.strip() or content

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

    @staticmethod
    def _infer_topic(content: str) -> Optional[str]:
        mappings = {
            "python_basics": ["python", "函数", "变量", "循环", "条件", "print", "def"],
            "data_structures": ["列表", "字典", "集合", "元组", "list", "dict", "set", "tuple"],
            "algorithms": ["算法", "排序", "查找", "递归", "sort", "search"],
            "oop": ["类", "对象", "继承", "封装", "class", "object"],
        }
        lowered = content.lower()
        for topic, keywords in mappings.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                return topic
        return None

    @staticmethod
    def _infer_difficulty(content: str) -> Optional[str]:
        lowered = content.lower()
        if any(word in lowered for word in ["简单", "入门", "beginner", "基础"]):
            return "beginner"
        if any(word in lowered for word in ["高级", "困难", "advanced", "挑战"]):
            return "advanced"
        if any(word in lowered for word in ["中等", "intermediate", "进阶"]):
            return "intermediate"
        return None

    @staticmethod
    def _is_answer_request(content: str) -> bool:
        content_lower = content.lower()
        answer_keywords = [
            "答案",
            "给答案",
            "解答",
            "讲解",
            "怎么做",
            "咋做",
            "如何做",
            "如何实现",
            "怎么写",
            "写法",
            "参考代码",
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
            "solution",
            "answer",
            "hint",
        ]
        generation_keywords = ["生成", "出题", "练习", "题目", "quiz", "test", "exam"]
        return any(keyword in content_lower for keyword in answer_keywords) and not any(
            keyword in content_lower for keyword in generation_keywords
        )

    @staticmethod
    def _is_vague_answer_followup(content: str) -> bool:
        content_lower = content.lower().strip()
        reference_terms = [
            "这个",
            "这题",
            "这道题",
            "该题",
            "它",
            "上一题",
            "上一次",
            "刚才",
            "刚刚",
            "那个",
        ]
        action_terms = [
            "答案",
            "解答",
            "怎么做",
            "咋做",
            "如何做",
            "如何实现",
            "怎么写",
            "写法",
            "参考代码",
            "讲解",
            "提示",
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
        ]
        has_action = any(term in content_lower for term in action_terms)
        has_reference = any(term in content_lower for term in reference_terms)
        return has_action and (has_reference or len(content_lower) <= 12)
