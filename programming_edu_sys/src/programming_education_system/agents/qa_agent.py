"""Question answering agent with knowledge-base lookup and cognition-aware fallback."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from programming_education_system.agents.profile_guidance import (
    build_profile_instruction,
    build_profile_summary,
    infer_user_type,
)
from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.cognition_judger.cognitive_api_scientific import (
    get_scientific_cognitive_api_sync,
)
from programming_education_system.models.knowledge_base import KnowledgeBase
from programming_education_system.utils.agent_interaction_logger import log_agent_interaction
from programming_education_system.utils.llm_utils import llm_client

logger = logging.getLogger(__name__)


class ThinkingQAAgent:
    """Handles open-ended questions using cognition-aware prompting."""

    def __init__(self) -> None:
        self.name = "ThinkingQAAgent"
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def think_and_answer(
        self, complex_question: str, user_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        context = context or {}
        user_profile = context.get("user_profile") or {}
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        learning_params = await self.cognition_api.get_personalized_learning_parameters(
            user_id, "explanation"
        )
        teaching_mode = context.get("intent_analysis", {}).get("teaching_mode", "explain")
        system_prompt = self._build_system_prompt(
            cognitive_state,
            learning_params,
            teaching_mode,
            user_profile=user_profile,
        )
        retrieval_context = context.get("retrieval_context", {})
        retrieval_text = context.get("retrieval_text", "")
        task_context = context.get("task_context") or {}
        user_requirement = str(task_context.get("user_requirement") or "").strip()
        context_summary = str(task_context.get("context_summary") or "").strip()
        already_answered = self._format_list(task_context.get("already_answered") or [])
        avoid_repeating = self._format_list(task_context.get("avoid_repeating") or [])
        user_message = (
            f"学生问题: {complex_question}\n\n"
            f"用户画像摘要:\n{build_profile_summary(user_profile) if user_profile else '无'}\n\n"
            f"用户本轮要求:\n{user_requirement or '无'}\n\n"
            f"用户代理提供的必要上下文:\n{context_summary or '无'}\n\n"
            f"历史中已经讲过的要点:\n{already_answered or '无'}\n\n"
            f"本轮应避免重复:\n{avoid_repeating or '无'}\n\n"
            f"检索到的课程资料:\n{retrieval_text or '未检索到课程资料。'}\n\n"
            "回答要求:\n"
            "1. 先判断课程资料是否与学生问题直接相关；不相关时不要硬套资料。\n"
            "2. 相关资料只能作为证据和例子，最终回答必须紧扣学生问题。\n"
            "3. 资料不足时明确说明“课程资料没有直接覆盖”，再用通用编程知识补充。\n"
            "4. 面向编程学习者，用短例子或小练习帮助理解。\n"
            "5. 如果用户代理提供了已经讲过的要点，本轮只补充当前请求需要的新信息，不要完整重复旧答案。\n"
            "6. 不要编造不存在的来源，不要回答与问题无关的内容。"
        )
        answer = await llm_client.generate_response_with_retry(
            system_prompt,
            user_message,
            use_cache=False,
            max_retries=1,
            task_type="qa",
        )
        answer_source = "llm_thinking"
        if self._is_llm_unavailable_answer(answer):
            answer = self._build_retrieval_fallback_answer(
                complex_question,
                retrieval_context,
                user_profile=user_profile,
            )
            answer_source = "qa_retrieval_fallback"
        return {
            "answer": answer,
            "answer_source": answer_source,
            "cognitive_level_used": cognitive_state["overall_cognitive_level"],
            "learning_parameters": learning_params,
            "personalization_applied": True,
            "retrieval_context": retrieval_context,
            "user_type": infer_user_type(user_profile) if user_profile else self._user_type_from_cognition(cognitive_state),
            "profile_summary": build_profile_summary(user_profile) if user_profile else "",
        }

    def _build_system_prompt(
        self,
        cognitive_state: Dict[str, Any],
        learning_params: Dict[str, Any],
        teaching_mode: str = "explain",
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        level = cognitive_state["overall_cognitive_level"]
        depth = learning_params.get("parameters", {}).get("explanation_depth", 0.7)
        user_profile = user_profile or {}
        user_type = infer_user_type(user_profile) if user_profile else self._user_type_from_cognition(cognitive_state)
        mode_instruction = {
            "hint": "优先给提示和引导问题，不要一开始就给完整答案。",
            "quiz": "解释后给一个 1 分钟小测题来检查理解。",
            "debug": "优先定位错误原因，并给出最小修改建议。",
            "plan": "优先给阶段化学习路径和下一步行动。",
            "explain": "按概念、例子、常见误区、小练习的顺序讲解。",
        }.get(teaching_mode, "按概念、例子、常见误区、小练习的顺序讲解。")
        base_instruction = (
            "回答必须直接回应学生当前问题。"
            "如果检索资料和问题不匹配，要降低资料权重，避免答非所问。"
            "不要因为上下文里出现了某个知识点，就偏离当前问题。"
        )
        profile_instruction = build_profile_instruction(user_profile, "qa") if user_profile else ""
        profile_summary = build_profile_summary(user_profile) if user_profile else ""
        profile_block = (
            f"{profile_instruction}\n用户画像摘要:\n{profile_summary}\n"
            if user_profile
            else ""
        )
        if user_type == "beginner":
            return (
                "你是耐心的编程入门助教。使用简单中文、短步骤和一个具体例子。"
                f"解释深度约 {depth:.1f}。{mode_instruction}{base_instruction}"
                f"{profile_block}"
            )
        if user_type == "intermediate":
            return (
                "你是实践型编程助教。兼顾概念、例子和常见误区。"
                f"解释深度约 {depth:.1f}。{mode_instruction}{base_instruction}"
                f"{profile_block}"
            )
        return (
            "你是进阶编程导师。包含更深层推理、取舍和最佳实践。"
            f"解释深度约 {depth:.1f}。{mode_instruction}{base_instruction}"
            f"{profile_block}"
        )

    @staticmethod
    def _format_list(items: List[Any], limit: int = 6) -> str:
        if not isinstance(items, list):
            return ""
        return "\n".join(f"- {str(item)[:160]}" for item in items[:limit] if str(item).strip())

    @staticmethod
    def _format_recent_history(history: List[Dict[str, Any]], limit: int = 3) -> str:
        lines: List[str] = []
        for index, item in enumerate(history[-limit:], start=1):
            user_input = str(item.get("user_input", "")).strip()
            agent_response = str(item.get("agent_response", "")).strip()
            if not user_input:
                continue
            lines.append(f"{index}. 用户: {user_input[:180]}")
            if agent_response:
                lines.append(f"   助手: {agent_response[:240]}")
        return "\n".join(lines)

    @staticmethod
    def _is_llm_unavailable_answer(answer: str) -> bool:
        return "目前无法调用大模型" in str(answer or "")

    @staticmethod
    def _user_type_from_cognition(cognitive_state: Dict[str, Any]) -> str:
        level = float(cognitive_state.get("overall_cognitive_level", 0.5) or 0.5)
        if level < 0.4:
            return "beginner"
        if level < 0.7:
            return "intermediate"
        return "advanced"

    @staticmethod
    def _build_retrieval_fallback_answer(
        question: str,
        retrieval_context: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        hits = retrieval_context.get("hits") or []
        user_type = infer_user_type(user_profile or {}) if user_profile else "intermediate"
        if hits:
            first = hits[0]
            title = str(first.get("title") or "相关资料")
            text = " ".join(str(first.get("text") or "").split())
            if len(text) > 420:
                text = text[:419].rstrip() + "…"
            if user_type == "advanced":
                extra = (
                    "\n\n进阶关注点：可以进一步追问它的边界条件、抽象方式、"
                    "复杂度取舍或工程中的使用场景。"
                )
            elif user_type == "beginner":
                extra = "\n\n下一步：先用自己的话复述这个概念，再写一个 3 行以内的小例子。"
            else:
                extra = "\n\n下一步：可以用一个小例子验证这个概念是否真正理解。"
            return (
                "大模型暂时不可用，我先根据课程资料给你一个简要说明。\n\n"
                f"当前问题：{question}\n\n"
                f"可参考资料：{title}\n\n"
                f"核心内容：{text}\n\n"
                "如果需要更细的步骤，可以稍后再让我继续展开。"
                f"{extra}"
            )
        return (
            "大模型暂时不可用，而且当前问题没有匹配到足够明确的课程资料。\n"
            "建议稍后重试，或把想问的概念、代码片段再具体写一下。"
        )


class KnowledgeBaseRetrievalAgent:
    """Looks up concise answers from the local knowledge base."""

    def __init__(self) -> None:
        self.knowledge_base = KnowledgeBase()
        self.cognition_api = get_scientific_cognitive_api_sync()
        self._enhance_knowledge_base()

    def _enhance_knowledge_base(self) -> None:
        seeds = {
            "python_basics": [
                {
                    "question": "How do I start learning Python?",
                    "answer": "Start with syntax, variables, conditions, loops, and functions, then practice with small scripts.",
                    "examples": ["Write a calculator, a guess-the-number game, or a todo list."],
                }
            ],
            "interactive_help": [
                {
                    "question": "What can this system do?",
                    "answer": "It can answer programming questions, generate practice exercises, review code, and offer learning suggestions.",
                    "examples": ["Ask for an exercise, request a code review, or ask for a study path."],
                }
            ],
        }
        for topic, items in seeds.items():
            for item in items:
                self.knowledge_base.add_knowledge(topic, item["question"], item["answer"], item["examples"])

    async def retrieve_from_knowledge_base(
        self,
        question: str,
        user_id: str,
        topic: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        topic = topic or "general_programming"
        results = self.knowledge_base.search(question, topic=None if topic == "general_programming" else topic)
        if not results:
            return {"found": False, "answer": ""}

        best_match = results[0]
        if best_match.get("score", 0) < 4.0:
            return {"found": False, "answer": "", "retrieval_context": self.knowledge_base.build_context(question)}
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        personalized_answer = await self._personalize_knowledge_answer(
            best_match,
            cognitive_state,
            user_profile=user_profile,
        )
        user_type = infer_user_type(user_profile or {}) if user_profile else self._user_type_from_cognition(cognitive_state)
        return {
            "found": True,
            "answer": personalized_answer,
            "examples": best_match.get("examples", []),
            "source": "knowledge_base",
            "confidence": "high",
            "personalized": True,
            "user_type": user_type,
            "profile_summary": build_profile_summary(user_profile or {}) if user_profile else "",
            "retrieval_context": self.knowledge_base.build_context(question, limit=3),
            "citations": [
                self._citation_from_result(item)
                for item in results[:3]
            ],
        }

    async def _personalize_knowledge_answer(
        self,
        knowledge_item: Dict[str, Any],
        cognitive_state: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        base_answer = str(knowledge_item.get("answer", ""))
        user_profile = user_profile or {}
        user_type = infer_user_type(user_profile) if user_profile else self._user_type_from_cognition(cognitive_state)
        if user_type == "beginner":
            return (
                "先抓住核心想法："
                f"{base_answer}\n\n"
                "你可以先把它写成一句自己的话，再看一个最小例子。"
            )
        if user_type == "advanced":
            return (
                "先给结论："
                f"{base_answer}\n\n"
                "进阶看法：重点关注它的抽象边界、输入输出约定、副作用控制，以及在工程里如何复用。"
            )
        return (
            "给你一个实用解释："
            f"{base_answer}\n\n"
            "建议顺手写一个小例子，把概念和代码对应起来。"
        )

    @staticmethod
    def _user_type_from_cognition(cognitive_state: Dict[str, Any]) -> str:
        level = float(cognitive_state.get("overall_cognitive_level", 0.5) or 0.5)
        if level < 0.4:
            return "beginner"
        if level < 0.7:
            return "intermediate"
        return "advanced"

    @staticmethod
    def _citation_from_result(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "chunk_id": item.get("chunk_id", ""),
            "source": item.get("source", "knowledge_base"),
            "url": item.get("url", ""),
            "topic": item.get("topic"),
            "title": item.get("title") or item.get("question"),
            "score": item.get("score"),
            "lexical_score": item.get("lexical_score", 0),
            "vector_score": item.get("vector_score", 0),
            "retrieval_mode": item.get("retrieval_mode", "lexical"),
        }


class QAAgent(BaseAgent):
    """Main question answering agent."""

    def __init__(self, personal_agent) -> None:
        super().__init__("QAAgent")
        self.thinking_agent = ThinkingQAAgent()
        self.kb_agent = KnowledgeBaseRetrievalAgent()
        self.personal_agent = personal_agent
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def answer_question(
        self, question: str, user_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        self.log_activity("answering question", {"user_id": user_id})
        context = context or {}
        user_profile = context.get("user_profile") or await self._load_user_profile(user_id)
        context["user_profile"] = user_profile
        context["profile_instruction"] = build_profile_instruction(user_profile, "qa")
        context["profile_summary"] = build_profile_summary(user_profile)
        user_type = infer_user_type(user_profile)
        intent_analysis = context.get("intent_analysis") or {}
        task_context = context.get("task_context") or {}
        topic = str(
            intent_analysis.get("topic")
            or task_context.get("topic_hint")
            or "general_programming"
        )
        retrieval_context = self.kb_agent.knowledge_base.build_context(question, topic=topic, limit=3)
        if not retrieval_context.get("hits") and topic != "general_programming":
            retrieval_context = self.kb_agent.knowledge_base.build_context(question, topic=None, limit=3)
        retrieval_text = self.kb_agent.knowledge_base.format_context_for_prompt(retrieval_context)
        enriched_context = {
            **(context or {}),
            "retrieval_context": retrieval_context,
            "retrieval_text": retrieval_text,
        }
        thinking_result = await self.thinking_agent.think_and_answer(question, user_id, enriched_context)
        citations = [
            {
                "chunk_id": hit.get("chunk_id", ""),
                "source": hit.get("source", "knowledge_base"),
                "url": hit.get("url", ""),
                "topic": hit.get("topic"),
                "title": hit.get("title"),
                "score": hit.get("score"),
                "lexical_score": hit.get("lexical_score", 0),
                "vector_score": hit.get("vector_score", 0),
                "retrieval_mode": hit.get("retrieval_mode", "lexical"),
            }
            for hit in retrieval_context.get("hits", [])
        ]
        return {
            "response": thinking_result["answer"],
            "examples": [],
            "source": thinking_result.get("answer_source", "llm_thinking"),
            "needs_thinking": True,
            "cognitive_level_used": thinking_result["cognitive_level_used"],
            "personalized": thinking_result["personalization_applied"],
            "learning_parameters": thinking_result.get("learning_parameters", {}),
            "retrieval_context": retrieval_context,
            "citations": citations,
            "user_type": thinking_result.get("user_type", user_type),
            "profile_summary": thinking_result.get("profile_summary", context["profile_summary"]),
        }

    async def _load_user_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            return await self.personal_agent.get_user_profile(user_id)
        except Exception as exc:
            logger.warning("Loading user profile for QA failed: %s", exc)
            return {}

    @staticmethod
    def _topic_from_context(context: Dict[str, Any]) -> Optional[str]:
        for item in reversed(context.get("recent_history", [])):
            topic = item.get("topic")
            if topic and topic != "general":
                return str(topic)
            analysis = item.get("intent_analysis") or {}
            topic = analysis.get("topic")
            if topic and topic != "general_programming":
                return str(topic)
        conversation_topic = (context.get("conversation_context") or {}).get("last_topic")
        if conversation_topic and conversation_topic != "general":
            return str(conversation_topic)
        return None

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        question = request["content"]
        user_id = request["user_id"]
        context = {**request.get("context", {}), "intent_analysis": request.get("intent_analysis", {})}
        user_profile = context.get("user_profile") or await self._load_user_profile(user_id)
        context["user_profile"] = user_profile
        log_agent_interaction(
            "sub_agent_received",
            "MainAgent",
            self.name,
            request_id=str(request.get("request_id", "")),
            user_id=user_id,
            payload={
                "question": question,
                "intent_analysis": request.get("intent_analysis", {}),
                "task_context": context.get("task_context"),
                "recent_history_count": len(context.get("recent_history", [])),
                "user_type": infer_user_type(user_profile),
                "profile_summary": build_profile_summary(user_profile),
            },
        )
        result = await self.answer_question(question, user_id, context)
        task_context = context.get("task_context") or {}
        topic = str(
            context.get("intent_analysis", {}).get("topic")
            or task_context.get("topic_hint")
            or "general_programming"
        )

        await self.personal_agent.track_user_behavior(
            {
                "user_id": user_id,
                "question_type": "qa",
                "topic": topic,
                "complexity": "complex" if result["needs_thinking"] else "simple",
                "content": question[:100],
                "cognitive_level": result.get("cognitive_level_used", 0.5),
                "personalization_applied": result.get("personalized", False),
                "user_type": result.get("user_type") or infer_user_type(user_profile),
            }
        )

        cognitive_insights = await self._get_scientific_cognitive_insights(user_id, topic)
        response_data = {
            "success": True,
            "response": result["response"],
            "details": {
                "source": result["source"],
                "examples": result["examples"],
                "topic": topic,
                "answer_type": "detailed" if result["needs_thinking"] else "quick",
                "personalized": result.get("personalized", False),
                "user_type": result.get("user_type") or infer_user_type(user_profile),
                "profile_summary": result.get("profile_summary") or build_profile_summary(user_profile),
                "cognitive_insights": cognitive_insights,
                "retrieval_context": result.get("retrieval_context", {}),
                "citations": result.get("citations", []),
            },
        }
        if result["needs_thinking"] or cognitive_insights.get("needs_improvement", False):
            response_data["details"]["learning_tips"] = await self._generate_scientific_learning_tips(
                user_id, topic
            )
        log_agent_interaction(
            "sub_agent_completed",
            self.name,
            "MainAgent",
            request_id=str(request.get("request_id", "")),
            user_id=user_id,
            payload=response_data,
        )
        return response_data

    async def _get_scientific_cognitive_insights(self, user_id: str, topic: str) -> Dict[str, Any]:
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        learning_recs = await self.cognition_api.get_learning_recommendations(user_id, f"study {topic}")
        topic_mastery = self._analyze_topic_mastery(cognitive_state, topic)
        return {
            "current_level": cognitive_state["overall_cognitive_level"],
            "learning_trend": cognitive_state.get("learning_trend", "stable"),
            "topic_mastery": topic_mastery,
            "needs_improvement": topic_mastery < 0.6,
            "recommended_difficulty": learning_recs.get("recommendations", {}).get(
                "recommended_difficulty", "intermediate"
            ),
            "focus_areas": learning_recs.get("recommendations", {}).get("focus_areas", []),
        }

    async def _generate_scientific_learning_tips(self, user_id: str, topic: str) -> List[str]:
        insights = await self._get_scientific_cognitive_insights(user_id, topic)
        level = insights.get("current_level", 0.5)
        tips: List[str] = []
        if level < 0.4:
            tips.extend(
                [
                    "Strengthen the basics first with short daily practice.",
                    "Rebuild the idea using one tiny example before solving a harder problem.",
                ]
            )
        elif level < 0.7:
            tips.extend(
                [
                    "Mix concept review with hands-on coding to reinforce understanding.",
                    "Try a slightly harder variation after you finish a standard example.",
                ]
            )
        else:
            tips.extend(
                [
                    "Compare multiple solutions and reason about tradeoffs.",
                    "Turn this topic into a reusable pattern or utility to deepen mastery.",
                ]
            )
        tips.append(f"Next focus topic: {topic}")
        return tips

    def _analyze_topic_mastery(self, cognitive_state: Dict[str, Any], topic: str) -> float:
        knowledge_domains = cognitive_state.get("knowledge_domains", {})
        topic_to_domain = {
            "python_basics": "python_basics",
            "data_structures": "data_structures",
            "algorithms": "algorithms",
            "oop": "oop",
            "web_development": "python_basics",
            "data_science": "algorithms",
        }
        domain = topic_to_domain.get(topic, "python_basics")
        domain_score = knowledge_domains.get(domain, 0.5)
        understanding_score = cognitive_state.get("cognitive_dimensions", {}).get("understand", 0.5)
        return (domain_score + understanding_score) / 2
