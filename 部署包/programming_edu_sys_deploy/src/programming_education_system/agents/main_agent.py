"""Main routing agent for the programming education system."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.agents.evaluation_agent import AnswerEvaluationAgent
from programming_education_system.agents.exercise_agent import EnhancedExerciseGenerationAgent
from programming_education_system.agents.personal_agent import PersonalizedLearningAgent
from programming_education_system.agents.qa_agent import QAAgent

logger = logging.getLogger(__name__)


@dataclass
class IntentAnalysis:
    """Structured routing signal shared by all downstream agents."""

    intent: str = "qa"
    topic: str = "general_programming"
    difficulty: str = "beginner"
    confidence: float = 0.5
    reason: str = "fallback"
    needs_code_review: bool = False
    needs_exercise_context: bool = False
    teaching_mode: str = "explain"

    def normalized(self) -> "IntentAnalysis":
        if self.intent not in {"qa", "exercise", "evaluation", "personal"}:
            self.intent = "qa"
        if self.difficulty not in {"beginner", "intermediate", "advanced"}:
            self.difficulty = "beginner"
        if self.teaching_mode not in {"explain", "hint", "quiz", "debug", "plan"}:
            self.teaching_mode = "explain"
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        return self


class MainAgent(BaseAgent):
    """Enhances requests, detects intent, and dispatches work."""

    VALID_INTENTS = {"qa", "exercise", "evaluation", "personal"}

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
        """Rewrite short ambiguous inputs only when recent history is necessary."""
        original_content = request["content"]
        context = request.get("context", {})
        request_type = request.get("type", "auto")
        enhancement_info = request.get("enhancement_info", {})
        already_processed = bool(enhancement_info) and (
            enhancement_info.get("was_enhanced", False)
            or enhancement_info.get("context_analysis", {}).get("success", False)
            or enhancement_info.get("context_analysis", {}).get("skipped", False)
        )
        if already_processed:
            return request
        if request_type != "auto" or not context.get("recent_history") or len(original_content.strip()) > 50:
            return self._mark_unenhanced(request, original_content)

        try:
            system_prompt = (
                "角色：你是编程教育系统的上下文改写器。\n"
                "任务：只在当前输入依赖最近对话时，补全成一个明确、可独立理解的学习请求。\n"
                "约束：不得改变用户意图，不得添加新需求，不得回答问题。\n"
                "输出：只输出改写后的用户请求；如果原输入已经明确，逐字原样返回。"
            )
            history_context = "\n".join(
                [
                    f"- 用户: {history.get('user_input', '')}\n- 助手: {str(history.get('agent_response', ''))[:180]}"
                    for history in context.get("recent_history", [])[-3:]
                ]
            )
            user_message = (
                f"当前输入:\n{original_content}\n\n"
                f"最近对话:\n{history_context}\n\n"
                "请执行上下文改写。"
            )
            enhanced_content = (
                await self._get_llm_client().generate_response(system_prompt, user_message, use_cache=True)
            ).strip()
            if self._is_safe_enhancement(original_content, enhanced_content):
                return {
                    **request,
                    "content": enhanced_content,
                    "original_content": original_content,
                    "enhancement_info": {
                        **request.get("enhancement_info", {}),
                        "was_enhanced": True,
                        "context_used": True,
                        "original_content": original_content,
                        "enhancement_reason": "based_on_recent_history",
                    },
                }
        except Exception as exc:
            logger.warning("Request enhancement failed: %s", exc)

        return self._mark_unenhanced(request, original_content)

    async def analyze_intent_with_context(self, content: str, context: Dict[str, Any]) -> IntentAnalysis:
        fast_intent = self._fast_intent_analysis(content)
        if fast_intent and fast_intent.confidence >= 0.86:
            return fast_intent

        system_prompt = (
            "角色：你是编程教育多智能体系统的路由分类器。\n"
            "任务：判断用户请求应该交给哪个子智能体处理。\n"
            "意图定义：\n"
            "- qa：解释概念、回答为什么、怎么理解、区别是什么。\n"
            "- exercise：生成练习题、给题目提示、请求某题答案或解法。\n"
            "- evaluation：检查代码、解释报错、评审实现、定位 bug。\n"
            "- personal：学习路径、学习建议、学习画像、下一步规划。\n"
            "输出：只返回 JSON，不要 Markdown，不要自然语言。\n"
            "JSON schema：{\n"
            '  "intent": "qa|exercise|evaluation|personal",\n'
            '  "topic": "python_basics|data_structures|algorithms|oop|web_development|data_science|general_programming",\n'
            '  "difficulty": "beginner|intermediate|advanced",\n'
            '  "confidence": 0.0,\n'
            '  "reason": "不超过20字",\n'
            '  "needs_code_review": false,\n'
            '  "needs_exercise_context": false,\n'
            '  "teaching_mode": "explain|hint|quiz|debug|plan"\n'
            "}\n"
            "规则：有代码并要求检查/报错/为什么错，优先 evaluation；要求出题优先 exercise；"
            "要求学习计划优先 personal；否则通常是 qa。"
        )
        context_info = ""
        if context.get("recent_history"):
            history_lines = []
            for index, history in enumerate(context["recent_history"][-6:], start=1):
                history_lines.append(f"{index}. 用户: {history.get('user_input', '')}")
                history_lines.append(f"   助手: {str(history.get('agent_response', ''))[:180]}")
            context_info = "\n".join(history_lines)

        user_message = f"当前输入:\n{content}\n\n最近对话:\n{context_info or '无'}"
        try:
            response = await self._get_llm_client().generate_response(system_prompt, user_message, use_cache=False)
            intent_data = self._parse_llm_response(response)
            if intent_data and intent_data.get("intent"):
                analysis = self._intent_from_mapping(intent_data).normalized()
                if fast_intent and fast_intent.topic != "general_programming":
                    analysis.topic = fast_intent.topic
                if fast_intent and fast_intent.difficulty != "beginner":
                    analysis.difficulty = fast_intent.difficulty
                if analysis.confidence >= 0.45:
                    return analysis
        except Exception as exc:
            logger.error("Intent analysis failed: %s", exc)

        return fast_intent or self._fallback_intent_analysis(content)

    async def analyze_intent(self, request: Dict[str, Any]) -> IntentAnalysis:
        content = request["content"].strip()
        request_type = request.get("type", "auto")
        context = request.get("context", {})
        if request_type != "auto" and request_type in self.VALID_INTENTS:
            base = self._fallback_intent_analysis(content)
            base.intent = request_type
            base.confidence = 1.0
            base.reason = "explicit_request_type"
            return base.normalized()
        return await self.analyze_intent_with_context(content, context)

    async def dispatch_to_sub_agent(self, analysis: IntentAnalysis, request: Dict[str, Any]) -> Dict[str, Any]:
        agents = {
            "qa": self.qa_agent,
            "exercise": self.exercise_agent,
            "evaluation": self.evaluation_agent,
            "personal": self.personal_agent,
        }
        request.setdefault("context", {})
        request["intent_analysis"] = asdict(analysis)
        result = await agents.get(analysis.intent, self.qa_agent).process(request)
        result["detected_intent"] = analysis.intent
        result["intent_analysis"] = asdict(analysis)
        result["enhancement_applied"] = request.get("enhancement_info", {}).get("was_enhanced", False)
        result["context_used"] = request.get("enhancement_info", {}).get("context_used", False)
        result["enhancement_info"] = request.get("enhancement_info", {})
        result["target_exercise"] = request.get("target_exercise")
        if request.get("enhancement_info", {}).get("was_enhanced", False):
            result["original_content"] = request.get("enhancement_info", {}).get("original_content", request["content"])
        return result

    async def _sync_external_profile(self, request: Dict[str, Any]) -> None:
        external_context = request.get("context", {}).get("external_learning_context", {})
        profile = external_context.get("profile") or {}
        level = external_context.get("level") or {}
        if not profile and not level:
            return
        await self.personal_agent.update_user_profile(
            request["user_id"],
            {
                "learning_style": profile.get("learning_style") or "balanced",
                "learning_goals": [profile.get("learning_goal")] if profile.get("learning_goal") else [],
                "programming_level": level.get("name") or "beginner",
                "content": request.get("content", ""),
                "topic": self._infer_topic(request.get("content", "")),
            },
        )

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        enhanced_request = await self.enhance_request_with_context(request)
        await self._sync_external_profile(enhanced_request)
        analysis = await self.analyze_intent(enhanced_request)
        result = await self.dispatch_to_sub_agent(analysis, enhanced_request)
        await self.personal_agent.track_user_behavior(
            {
                "user_id": enhanced_request["user_id"],
                "intent": analysis.intent,
                "topic": analysis.topic,
                "difficulty": analysis.difficulty,
                "content": enhanced_request["content"],
                "original_content": enhanced_request.get("original_content", enhanced_request["content"]),
                "was_enhanced": enhanced_request.get("enhancement_info", {}).get("was_enhanced", False),
                "context_used": enhanced_request.get("enhancement_info", {}).get("context_used", False),
                "external_learning_context": enhanced_request.get("context", {}).get("external_learning_context", {}),
                "timestamp": enhanced_request.get("timestamp", "unknown"),
            }
        )
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
        return {}

    def _intent_from_mapping(self, data: Dict[str, Any]) -> IntentAnalysis:
        return IntentAnalysis(
            intent=str(data.get("intent", "qa")),
            topic=str(data.get("topic") or self._infer_topic(str(data))),
            difficulty=str(data.get("difficulty") or "beginner"),
            confidence=float(data.get("confidence", 0.6) or 0.6),
            reason=str(data.get("reason", "llm"))[:60],
            needs_code_review=bool(data.get("needs_code_review", False)),
            needs_exercise_context=bool(data.get("needs_exercise_context", False)),
            teaching_mode=str(data.get("teaching_mode", "explain")),
        )

    def _fast_intent_analysis(self, content: str) -> Optional[IntentAnalysis]:
        content_lower = content.lower()
        has_code = self._looks_like_code(content)
        topic = self._infer_topic(content)
        difficulty = self._infer_difficulty(content)

        if has_code and any(token in content_lower for token in ["检查", "评估", "评价", "review", "报错", "错误", "为什么错", "bug"]):
            return IntentAnalysis("evaluation", topic, difficulty, 0.95, "code_review_signal", True, False, "debug")
        if any(token in content_lower for token in ["生成练习", "出一道题", "给我一道题", "练习题", "刷题", "quiz", "exercise"]):
            return IntentAnalysis("exercise", topic, difficulty, 0.92, "exercise_signal", False, False, "quiz")
        if any(token in content_lower for token in ["这道题答案", "参考答案", "解答这题", "solution", "answer"]) and not has_code:
            return IntentAnalysis("exercise", topic, difficulty, 0.86, "answer_request_signal", False, True, "hint")
        if any(token in content_lower for token in ["学习路径", "学习计划", "推荐", "规划", "我该学什么", "接下来应该学什么", "建议"]):
            return IntentAnalysis("personal", topic, difficulty, 0.9, "personal_learning_signal", False, False, "plan")
        if any(token in content_lower for token in ["是什么", "为什么", "怎么理解", "解释", "区别", "what is", "how to"]):
            return IntentAnalysis("qa", topic, difficulty, 0.88, "qa_signal", False, False, "explain")
        if has_code:
            return IntentAnalysis("evaluation", topic, difficulty, 0.82, "code_detected", True, False, "debug")
        return None

    def _fallback_intent_analysis(self, content: str) -> IntentAnalysis:
        content_lower = content.lower()
        topic = self._infer_topic(content)
        difficulty = self._infer_difficulty(content)
        if self._looks_like_code(content):
            return IntentAnalysis("evaluation", topic, difficulty, 0.75, "fallback_code_detected", True, False, "debug")
        if any(keyword in content_lower for keyword in ["练习", "题目", "作业", "exercise", "problem", "出题"]):
            return IntentAnalysis("exercise", topic, difficulty, 0.7, "fallback_keyword", False, False, "quiz")
        if any(keyword in content_lower for keyword in ["建议", "推荐", "学习路径", "suggestion", "advice", "规划"]):
            return IntentAnalysis("personal", topic, difficulty, 0.7, "fallback_keyword", False, False, "plan")
        return IntentAnalysis("qa", topic, difficulty, 0.6, "fallback_default", False, False, "explain")

    @staticmethod
    def _looks_like_code(content: str) -> bool:
        return bool(
            re.search(r"```|^\s*(def|class|import|from)\s+", content, re.MULTILINE)
            or re.search(r"\b(print|return|for|while|if)\b.*[:)]", content)
        )

    @staticmethod
    def _infer_topic(content: str) -> str:
        lowered = content.lower()
        topic_keywords = {
            "data_structures": ["list", "dict", "tuple", "set", "列表", "字典", "集合", "元组", "append"],
            "algorithms": ["algorithm", "sort", "search", "递归", "算法", "排序", "查找", "二分"],
            "oop": ["class", "object", "inherit", "继承", "面向对象", "类", "对象"],
            "web_development": ["flask", "django", "html", "css", "javascript", "前端"],
            "data_science": ["pandas", "numpy", "机器学习", "数据分析"],
            "python_basics": ["python", "def", "function", "变量", "函数", "语法", "循环", "条件", "print", "return"],
        }
        for topic, keywords in topic_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                return topic
        return "general_programming"

    @staticmethod
    def _infer_difficulty(content: str) -> str:
        lowered = content.lower()
        if any(word in lowered for word in ["高级", "困难", "advanced", "复杂", "挑战"]):
            return "advanced"
        if any(word in lowered for word in ["中等", "intermediate", "进阶"]):
            return "intermediate"
        return "beginner"

    @staticmethod
    def _mark_unenhanced(request: Dict[str, Any], original_content: str) -> Dict[str, Any]:
        return {
            **request,
            "enhancement_info": {
                **request.get("enhancement_info", {}),
                "was_enhanced": False,
                "context_used": False,
                "original_content": original_content,
            },
        }

    @staticmethod
    def _is_safe_enhancement(original: str, enhanced: str) -> bool:
        if not enhanced or enhanced == original:
            return False
        if len(enhanced) > 600 or len(enhanced) < len(original):
            return False
        forbidden = ["```", "{", "}", "回答", "答案是"]
        return not any(token in enhanced for token in forbidden)
