"""Question answering agent with knowledge-base lookup and cognition-aware fallback."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.cognition_judger.cognitive_api_scientific import (
    get_scientific_cognitive_api_sync,
)
from programming_education_system.models.knowledge_base import KnowledgeBase
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
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        learning_params = await self.cognition_api.get_personalized_learning_parameters(
            user_id, "explanation"
        )
        system_prompt = self._build_system_prompt(cognitive_state, learning_params)
        user_message = f"Question: {complex_question}"
        if context:
            user_message += f"\nContext: {context}"
        answer = await llm_client.generate_response(system_prompt, user_message, use_cache=False)
        return {
            "answer": answer,
            "cognitive_level_used": cognitive_state["overall_cognitive_level"],
            "learning_parameters": learning_params,
            "personalization_applied": True,
        }

    def _build_system_prompt(
        self, cognitive_state: Dict[str, Any], learning_params: Dict[str, Any]
    ) -> str:
        level = cognitive_state["overall_cognitive_level"]
        depth = learning_params.get("parameters", {}).get("explanation_depth", 0.7)
        if level < 0.4:
            return (
                "You are a patient programming tutor. Use simple language, short steps, and one concrete example. "
                f"Keep the explanation depth around {depth:.1f}."
            )
        if level < 0.7:
            return (
                "You are a practical programming tutor. Balance concept explanation with examples and common pitfalls. "
                f"Keep the explanation depth around {depth:.1f}."
            )
        return (
            "You are an advanced programming mentor. Include deeper reasoning, tradeoffs, and best practices. "
            f"Keep the explanation depth around {depth:.1f}."
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

    async def retrieve_from_knowledge_base(self, question: str, user_id: str) -> Dict[str, Any]:
        results = self.knowledge_base.search(question)
        if not results:
            return {"found": False, "answer": ""}

        best_match = results[0]
        cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
        personalized_answer = await self._personalize_knowledge_answer(best_match, cognitive_state)
        return {
            "found": True,
            "answer": personalized_answer,
            "examples": best_match.get("examples", []),
            "source": "knowledge_base",
            "confidence": "high",
            "personalized": True,
        }

    async def _personalize_knowledge_answer(
        self, knowledge_item: Dict[str, Any], cognitive_state: Dict[str, Any]
    ) -> str:
        base_answer = str(knowledge_item.get("answer", ""))
        level = cognitive_state.get("overall_cognitive_level", 0.5)
        if level < 0.4:
            prefix = "Begin with the core idea: "
        elif level < 0.7:
            prefix = "Here is a practical explanation: "
        else:
            prefix = "Here is the concise answer plus the deeper takeaway: "
        return prefix + base_answer


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
        kb_result = await self.kb_agent.retrieve_from_knowledge_base(question, user_id)
        if kb_result.get("found") and kb_result.get("confidence") == "high":
            return {
                "response": kb_result["answer"],
                "examples": kb_result.get("examples", []),
                "source": kb_result.get("source", "knowledge_base"),
                "needs_thinking": False,
                "personalized": kb_result.get("personalized", False),
            }

        thinking_result = await self.thinking_agent.think_and_answer(question, user_id, context)
        return {
            "response": thinking_result["answer"],
            "examples": [],
            "source": "llm_thinking",
            "needs_thinking": True,
            "cognitive_level_used": thinking_result["cognitive_level_used"],
            "personalized": thinking_result["personalization_applied"],
            "learning_parameters": thinking_result.get("learning_parameters", {}),
        }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        question = request["content"]
        user_id = request["user_id"]
        result = await self.answer_question(question, user_id, request.get("context"))
        topic = self._extract_topic(question)

        await self.personal_agent.track_user_behavior(
            {
                "user_id": user_id,
                "question_type": "qa",
                "topic": topic,
                "complexity": "complex" if result["needs_thinking"] else "simple",
                "content": question[:100],
                "cognitive_level": result.get("cognitive_level_used", 0.5),
                "personalization_applied": result.get("personalized", False),
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
                "cognitive_insights": cognitive_insights,
            },
        }
        if result["needs_thinking"] or cognitive_insights.get("needs_improvement", False):
            response_data["details"]["learning_tips"] = await self._generate_scientific_learning_tips(
                user_id, topic
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

    def _extract_topic(self, question: str) -> str:
        lowered = question.lower()
        topic_keywords = {
            "python_basics": ["python", "def", "function", "变量", "函数", "语法"],
            "data_structures": ["list", "dict", "tuple", "set", "列表", "字典"],
            "algorithms": ["algorithm", "sort", "search", "递归", "算法"],
            "oop": ["class", "object", "inherit", "继承", "面向对象"],
            "web_development": ["flask", "django", "html", "css", "javascript", "前端"],
            "data_science": ["pandas", "numpy", "机器学习", "数据分析"],
        }
        for topic, keywords in topic_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                return topic
        return "general_programming"
