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
        analysis = request.get("intent_analysis", {})

        if self._is_answer_request(content) or analysis.get("needs_exercise_context"):
            return await self._handle_answer_request(user_id, content, context)
        return await self._handle_exercise_request(user_id, content, context, analysis)

    async def _handle_exercise_request(
        self,
        user_id: str,
        content: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        profile = await self.personal_agent.get_user_profile(user_id)
        topic = analysis.get("topic") or self._infer_topic(content) or self._choose_topic_from_profile(profile)
        difficulty = self._choose_adaptive_difficulty(
            requested=analysis.get("difficulty") or self._infer_difficulty(content),
            profile=profile,
            topic=topic,
            context=context,
        )

        questions = self.question_bank_manager.search_questions(
            keyword="",
            topic=topic if topic != "general_programming" else None,
            difficulty=difficulty,
            limit=1,
        )
        if questions:
            question = self._to_display_question(questions[0])
            source = "question_bank"
        else:
            question = await self._generate_exercise_with_llm(content, topic, difficulty, profile)
            source = "ai_generated"

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

    async def _handle_answer_request(self, user_id: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        target_question = self._find_recent_question(context)
        if target_question:
            description = target_question.get("content", {}).get("description", "")
            answer = target_question.get("content", {}).get("answer") or target_question.get("answer")
            if not answer:
                answer = await self._generate_answer_with_llm(description)
            return {
                "response": self._format_guided_answer(description, answer),
                "details": {
                    "answer_provided": True,
                    "source": "question_bank" if target_question.get("answer") else "llm_generated",
                    "personalized": True,
                    "question": target_question,
                },
                "success": True,
            }

        inferred_question = self._extract_question_from_request(content)
        answer = await self._generate_answer_with_llm(inferred_question)
        return {
            "response": self._format_guided_answer(inferred_question, answer),
            "details": {"answer_provided": True, "source": "llm_generated_direct", "personalized": True},
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
            payload = content
        else:
            payload = {
                "title": f"{question.get('topic', 'general')} 练习",
                "description": str(content or ""),
                "requirements": ["完成题目要求"],
                "examples": question.get("examples", []),
                "hints": question.get("hints", []),
                "answer": question.get("answer", ""),
            }
        return {
            "question_id": question.get("question_id") or f"bank_{question.get('id')}",
            "topic": question.get("topic", "general"),
            "difficulty": question.get("difficulty", "beginner"),
            "type": question.get("question_type", question.get("type", "coding")),
            "content": {
                "title": payload.get("title") or f"{question.get('topic', 'general')} 练习",
                "description": payload.get("description", ""),
                "requirements": payload.get("requirements", ["完成题目要求"]),
                "examples": payload.get("examples", []),
                "hints": payload.get("hints", []),
                "answer": payload.get("answer") or question.get("answer", ""),
            },
            "answer": question.get("answer", payload.get("answer", "")),
        }

    async def _generate_exercise_with_llm(
        self, content: str, topic: str, difficulty: str, profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        system_prompt = (
            "角色：你是编程教育出题智能体。\n"
            "任务：生成一道适合学生当前水平的 Python 编程练习题。\n"
            "输出：只返回 JSON，不要 Markdown，不要解释。\n"
            "质量要求：题目必须可验证、目标单一、描述清楚；提示应由浅到深；参考答案应能运行。\n"
            "JSON schema：{\n"
            '  "title": "题目标题",\n'
            '  "description": "题目描述",\n'
            '  "requirements": ["明确要求"],\n'
            '  "examples": [{"input": "函数调用示例", "output": "期望输出"}],\n'
            '  "hints": ["轻提示", "中提示", "强提示"],\n'
            '  "answer": "Python参考代码"\n'
            "}"
        )
        user_message = f"""主题: {topic or 'general_programming'}
难度: {difficulty or 'beginner'}
用户请求: {content}
用户画像: {profile}

请生成练习题 JSON。"""
        response = await llm_client.generate_response(system_prompt, user_message, use_cache=False)
        parsed = self._parse_json_response(response)
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
        question_id = self.question_bank_manager.question_bank.add_question(
            topic=topic or "general",
            content=content_payload["description"],
            difficulty=DifficultyLevel(safe_difficulty),
            question_type=QuestionType.CODING,
            answer=content_payload["answer"],
            hints=content_payload["hints"],
            examples=content_payload["examples"],
            tags=[topic] if topic else [],
            source="ai_generated",
            metadata={"title": content_payload["title"], "adaptive": True},
        )
        return {
            "question_id": f"bank_{question_id}" if question_id else "generated_llm",
            "topic": topic or "general",
            "difficulty": safe_difficulty,
            "type": "coding",
            "content": content_payload,
            "answer": content_payload["answer"],
        }

    async def _generate_answer_with_llm(self, question_text: str) -> str:
        system_prompt = (
            "角色：你是编程助教。\n"
            "任务：为一道编程题提供教学型解答。\n"
            "教学策略：先讲思路，再给代码；先提示，再答案；指出常见错误。\n"
            "输出格式：使用中文，分为「解题思路」「参考代码」「常见错误」「变式练习」。"
        )
        user_message = f"题目:\n{question_text}\n\n请给出教学型参考解答。"
        return await llm_client.generate_response(system_prompt, user_message, use_cache=False)

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
        if requested in DIFFICULTY_ORDER and requested != "beginner":
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
        answer_keywords = ["答案", "解答", "讲解", "怎么做", "如何实现", "solution", "answer"]
        generation_keywords = ["生成", "出题", "练习", "题目", "quiz", "test", "exam"]
        return any(keyword in content_lower for keyword in answer_keywords) and not any(
            keyword in content_lower for keyword in generation_keywords
        )
