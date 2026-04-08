"""Exercise generation and answer support agent."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.models.question_bank import DifficultyLevel, QuestionType
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.utils.question_bank_manager import QuestionBankManager

logger = logging.getLogger(__name__)


class EnhancedExerciseGenerationAgent(BaseAgent):
    """Generate exercises or provide answers to previously generated exercises."""

    def __init__(self, personal_agent):
        super().__init__("EnhancedExerciseGenerationAgent")
        self.personal_agent = personal_agent
        self.question_bank_manager = QuestionBankManager()

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        user_id = request["user_id"]
        content = request["content"]
        context = request.get("context", {})

        if self._is_answer_request(content):
            return await self._handle_answer_request(user_id, content, context)
        return await self._handle_exercise_request(user_id, content, context)

    async def _handle_exercise_request(
        self, user_id: str, content: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        topic = self._infer_topic(content)
        difficulty = self._infer_difficulty(content)
        questions = self.question_bank_manager.search_questions(
            keyword="",
            topic=topic,
            difficulty=difficulty,
            limit=1,
        )

        if questions:
            question = self._to_display_question(questions[0])
            source = "question_bank"
        else:
            question = await self._generate_exercise_with_llm(content, topic, difficulty)
            source = "ai_generated"

        response = self._format_exercise_response(question, source)
        details = {
            "type": "exercise",
            "topic": question.get("topic", topic or "general"),
            "difficulty": question.get("difficulty", difficulty or "intermediate"),
            "personalized": False,
            "source": source,
            "question_count": 1,
            "exercise": question,
        }

        await self.personal_agent.track_user_behavior(
            {
                "user_id": user_id,
                "intent": "exercise",
                "topic": details["topic"],
                "difficulty": details["difficulty"],
            }
        )
        return {"response": response, "details": details, "success": True}

    async def _handle_answer_request(
        self, user_id: str, content: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        target_question = self._find_recent_question(context)
        if target_question:
            answer = target_question.get("content", {}).get("answer") or target_question.get("answer")
            if not answer:
                answer = await self._generate_answer_with_llm(target_question["content"]["description"])
            response = f"参考解答:\n\n{answer}"
            details = {
                "answer_provided": True,
                "source": "question_bank" if target_question.get("answer") else "llm_generated",
                "personalized": False,
                "question": target_question,
            }
            return {"response": response, "details": details, "success": True}

        inferred_question = self._extract_question_from_request(content)
        answer = await self._generate_answer_with_llm(inferred_question)
        return {
            "response": f"参考解答:\n\n{answer}",
            "details": {
                "answer_provided": True,
                "source": "llm_generated_direct",
                "personalized": False,
            },
            "success": True,
        }

    def _find_recent_question(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        recent_history = context.get("recent_history", [])
        for item in reversed(recent_history):
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
        content = question.get("content")
        if isinstance(content, dict):
            return {
                "question_id": question.get("question_id") or f"bank_{question.get('id')}",
                "topic": question.get("topic", "general"),
                "difficulty": question.get("difficulty", "intermediate"),
                "type": question.get("question_type", question.get("type", "coding")),
                "content": {
                    "title": content.get("title") or f"{question.get('topic', 'general')} 练习",
                    "description": content.get("description", ""),
                    "requirements": content.get("requirements", ["完成题目要求"]),
                    "examples": content.get("examples", []),
                    "hints": content.get("hints", []),
                    "answer": content.get("answer") or question.get("answer", ""),
                },
                "answer": question.get("answer", ""),
            }
        return {
            "question_id": f"bank_{question.get('id')}",
            "topic": question.get("topic", "general"),
            "difficulty": question.get("difficulty", "intermediate"),
            "type": question.get("question_type", "coding"),
            "content": {
                "title": f"{question.get('topic', 'general')} 练习",
                "description": question.get("content", ""),
                "requirements": ["完成题目要求"],
                "examples": question.get("examples", []),
                "hints": question.get("hints", []),
                "answer": question.get("answer", ""),
            },
            "answer": question.get("answer", ""),
        }

    async def _generate_exercise_with_llm(
        self, content: str, topic: str, difficulty: str
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a programming education assistant. Return a JSON object describing one coding exercise."
        )
        user_message = f"""Create one {difficulty or 'intermediate'} exercise about {topic or 'general programming'}.
User request: {content}
Return JSON:
{{
  "title": "...",
  "description": "...",
  "requirements": ["..."],
  "examples": [{{"input": "...", "output": "..."}}],
  "hints": ["..."],
  "answer": "..."
}}"""
        response = await llm_client.generate_response(system_prompt, user_message, use_cache=False)
        parsed = self._parse_json_response(response)
        content_payload = {
            "title": parsed.get("title", "AI 练习题"),
            "description": parsed.get("description", content),
            "requirements": parsed.get("requirements", ["完成题目要求"]),
            "examples": parsed.get("examples", []),
            "hints": parsed.get("hints", []),
            "answer": parsed.get("answer", ""),
        }
        question_id = self.question_bank_manager.question_bank.add_question(
            topic=topic or "general",
            content=content_payload["description"],
            difficulty=DifficultyLevel(difficulty or "intermediate"),
            question_type=QuestionType.CODING,
            answer=content_payload["answer"],
            hints=content_payload["hints"],
            examples=content_payload["examples"],
            tags=[topic] if topic else [],
            source="ai_generated",
        )
        return {
            "question_id": f"bank_{question_id}" if question_id else "generated_llm",
            "topic": topic or "general",
            "difficulty": difficulty or "intermediate",
            "type": "coding",
            "content": content_payload,
            "answer": content_payload["answer"],
        }

    async def _generate_answer_with_llm(self, question_text: str) -> str:
        system_prompt = "You are a programming tutor. Provide a clear solution and explanation."
        user_message = (
            f"Question:\n{question_text}\n\n"
            "Please provide a reference solution, a short explanation, and common mistakes to avoid."
        )
        return await llm_client.generate_response(system_prompt, user_message, use_cache=False)

    def _format_exercise_response(self, question: Dict[str, Any], source: str) -> str:
        content = question["content"]
        lines = [
            "已生成练习题:\n",
            f"标题: {content.get('title', '练习题')}",
            f"描述: {content.get('description', '')}",
            "要求:",
        ]
        lines.extend(f"- {item}" for item in content.get("requirements", []) or ["完成题目要求"])
        if content.get("examples"):
            lines.append("示例:")
            for example in content["examples"]:
                lines.append(f"- 输入: {example.get('input', '')}")
                lines.append(f"  输出: {example.get('output', '')}")
        if content.get("hints"):
            lines.append("提示:")
            lines.extend(f"- {hint}" for hint in content["hints"])
        lines.append(f"来源: {source}")
        return "\n".join(lines)

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
        answer_phrases = ["这道题的答案", "这个题目的解答", "请解答", "求答案", "帮忙解答", "怎么做"]
        result = content
        for phrase in answer_phrases:
            result = result.replace(phrase, "")
        return result.strip() or content

    @staticmethod
    def _infer_topic(content: str) -> Optional[str]:
        mappings = {
            "python_basics": ["python", "函数", "变量", "循环"],
            "data_structures": ["列表", "字典", "集合", "元组"],
            "algorithms": ["算法", "排序", "查找", "递归"],
            "oop": ["类", "对象", "继承", "封装"],
        }
        lowered = content.lower()
        for topic, keywords in mappings.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                return topic
        return None

    @staticmethod
    def _infer_difficulty(content: str) -> Optional[str]:
        lowered = content.lower()
        if any(word in lowered for word in ["简单", "入门", "beginner"]):
            return "beginner"
        if any(word in lowered for word in ["高级", "困难", "advanced"]):
            return "advanced"
        if any(word in lowered for word in ["中等", "intermediate"]):
            return "intermediate"
        return None

    @staticmethod
    def _is_answer_request(content: str) -> bool:
        content_lower = content.lower()
        answer_keywords = ["答案", "解答", "讲解", "怎么做", "如何实现", "solution", "answer"]
        exercise_generation_keywords = ["生成", "出题", "练习", "题目", "quiz", "test", "exam"]
        has_answer_signal = any(keyword in content_lower for keyword in answer_keywords)
        is_generation_request = any(keyword in content_lower for keyword in exercise_generation_keywords)
        return has_answer_signal and not is_generation_request
