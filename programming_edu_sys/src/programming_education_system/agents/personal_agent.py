"""Personalized learning agent with persistent profile management."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.agents.profile_guidance import (
    build_profile_instruction,
    build_profile_summary,
    infer_user_type,
)
from programming_education_system.models.user_profile import UserProfile
from programming_education_system.utils.agent_interaction_logger import log_agent_interaction
from programming_education_system.utils.context_manager import context_manager
from programming_education_system.utils.llm_utils import llm_client


class UserBehaviorTrackingAgent:
    """Stores recent user behavior records and mirrors summary data to context storage."""

    def __init__(self) -> None:
        self.behavior_logs: Dict[str, List[Dict[str, Any]]] = {}

    async def track_behavior(self, user_id: str, behavior_data: Dict[str, Any]) -> None:
        payload = {**behavior_data, "timestamp": behavior_data.get("timestamp") or datetime.now().isoformat()}
        self.behavior_logs.setdefault(user_id, []).append(payload)
        self.behavior_logs[user_id] = self.behavior_logs[user_id][-100:]
        external_context = payload.get("external_learning_context") or {}
        try:
            context_manager.save_learning_progress(
                user_id,
                {
                    "last_intent": payload.get("intent"),
                    "last_topic": payload.get("topic"),
                    "last_difficulty": payload.get("difficulty"),
                    "last_score": payload.get("evaluation_score"),
                    "recent_error_patterns": payload.get("error_patterns", []),
                    "lesson_progress": payload.get("lesson_progress")
                    or external_context.get("progress"),
                    "question_progress": payload.get("question_progress")
                    or external_context.get("question_progress"),
                    "real_learning_signals": payload.get("real_learning_signals")
                    or external_context.get("learning_signals"),
                },
            )
        except Exception:
            pass

    async def get_user_behaviors(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.behavior_logs.get(user_id, [])[-limit:]


class UserCognitionUpdateAgent:
    """Maintains and persists a practical user profile."""

    def __init__(self) -> None:
        self.user_profiles: Dict[str, UserProfile] = {}

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        profile = await self._load_or_create_profile(user_id, profile_data)
        if "programming_level" in profile_data:
            profile.programming_level = str(profile_data["programming_level"])
        if "learning_style" in profile_data:
            profile.learning_style = str(profile_data["learning_style"])
        if "learning_goals" in profile_data:
            profile.learning_goals = [str(goal) for goal in profile_data.get("learning_goals", []) if str(goal).strip()]

        topic = profile_data.get("topic") or "python_basics"
        is_correct = self._infer_correctness(profile_data)
        if topic:
            profile.update_mastery(topic, is_correct, str(profile_data.get("difficulty", "beginner")))
            mastery = profile.knowledge_mastery[topic]
            for pattern in profile_data.get("error_patterns", []) or []:
                if pattern not in mastery.error_patterns:
                    mastery.error_patterns.append(str(pattern))
            if topic not in profile.preferred_topics:
                profile.preferred_topics.append(topic)

        learning_signals = (
            profile_data.get("real_learning_signals")
            or profile_data.get("learning_signals")
            or (profile_data.get("learning_behavior") or {}).get("learning_signals")
        )
        if isinstance(learning_signals, dict) and learning_signals:
            self._apply_real_learning_signals(profile, learning_signals)

        profile.updated_at = datetime.now()
        await self._persist_profile(profile)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        profile = await self._load_or_create_profile(user_id, {})
        return self._profile_to_dict(profile)

    async def _load_or_create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        stored = self._load_stored_profile(user_id)
        if stored:
            profile = self._profile_from_dict(stored)
        else:
            profile = UserProfile(
                user_id=user_id,
                learning_style=profile_data.get("learning_style", "visual"),
                programming_level=profile_data.get("programming_level", "beginner"),
                preferred_topics=list(profile_data.get("preferred_topics", ["python_basics"])),
                learning_goals=list(profile_data.get("learning_goals", [])),
            )
        self.user_profiles[user_id] = profile
        return profile

    def _load_stored_profile(self, user_id: str) -> Dict[str, Any] | None:
        getter = getattr(context_manager, "get_user_profile", None)
        if not getter:
            return None
        try:
            return getter(user_id)
        except Exception:
            return None

    async def _persist_profile(self, profile: UserProfile) -> None:
        saver = getattr(context_manager, "save_user_profile", None)
        if not saver:
            return
        try:
            saver(profile.user_id, self._profile_to_dict(profile))
        except Exception:
            pass

    def _profile_to_dict(self, profile: UserProfile) -> Dict[str, Any]:
        return {
            "user_id": profile.user_id,
            "learning_style": profile.learning_style,
            "programming_level": profile.programming_level,
            "preferred_topics": profile.preferred_topics,
            "knowledge_mastery": {topic: mastery.mastery_level for topic, mastery in profile.knowledge_mastery.items()},
            "error_patterns": {topic: mastery.error_patterns for topic, mastery in profile.knowledge_mastery.items()},
            "weak_topics": profile.get_weak_topics(),
            "learning_goals": profile.learning_goals,
            "study_time_patterns": profile.study_time_patterns,
            "updated_at": profile.updated_at.isoformat(),
        }

    def _profile_from_dict(self, data: Dict[str, Any]) -> UserProfile:
        profile = UserProfile(
            user_id=data["user_id"],
            learning_style=data.get("learning_style", "visual"),
            programming_level=data.get("programming_level", "beginner"),
            preferred_topics=list(data.get("preferred_topics", ["python_basics"])),
            learning_goals=list(data.get("learning_goals", [])),
        )
        error_patterns = data.get("error_patterns", {})
        for topic, level in data.get("knowledge_mastery", {}).items():
            profile.update_mastery(topic, bool(float(level) >= 0.5), "beginner")
            profile.knowledge_mastery[topic].mastery_level = float(level)
            profile.knowledge_mastery[topic].error_patterns = list(error_patterns.get(topic, []))
        profile.study_time_patterns = dict(data.get("study_time_patterns", {}))
        return profile

    def _apply_real_learning_signals(self, profile: UserProfile, signals: Dict[str, Any]) -> None:
        profile.study_time_patterns["behavior_metrics"] = self._compact_learning_signals(signals)
        topic_metrics = signals.get("topic_metrics") or {}
        for topic, metric in topic_metrics.items():
            topic_name = str(topic or "general")
            if topic_name == "general" and not metric.get("submissions"):
                continue

            submissions = self._safe_int(metric.get("submissions"))
            pass_rate = self._safe_float(metric.get("pass_rate"))
            first_pass_rate = self._safe_float(metric.get("first_pass_rate"))
            consecutive_failures = self._safe_int(metric.get("consecutive_failures"))
            answer_views = self._safe_int(metric.get("answer_views"))
            hint_views = self._safe_int(metric.get("hint_views"))
            average_dwell = self._safe_float(metric.get("average_dwell_seconds"))

            if submissions > 0:
                estimated = 0.25 + pass_rate * 0.45 + first_pass_rate * 0.2
            else:
                estimated = 0.5
            estimated -= min(consecutive_failures, 5) * 0.06
            estimated -= min(answer_views + hint_views, 6) * 0.015
            if average_dwell >= 600:
                estimated -= 0.08
            elif average_dwell >= 300:
                estimated -= 0.04
            estimated = self._clamp(estimated, 0.1, 0.95)

            if topic_name not in profile.knowledge_mastery:
                profile.update_mastery(topic_name, estimated >= 0.55, "beginner")
            mastery = profile.knowledge_mastery[topic_name]
            mastery.mastery_level = self._clamp(mastery.mastery_level * 0.65 + estimated * 0.35, 0.1, 1.0)
            mastery.last_practiced = datetime.now()

            patterns = mastery.error_patterns
            if consecutive_failures >= 2:
                self._add_pattern(patterns, f"连续失败 {consecutive_failures} 次")
            if answer_views >= 2 or signals.get("frequent_answer_view"):
                self._add_pattern(patterns, "频繁查看参考答案")
            if hint_views >= 3 or signals.get("frequent_hint_view"):
                self._add_pattern(patterns, "频繁查看提示")
            if average_dwell >= 300:
                self._add_pattern(patterns, "题目停留时间较长")

            if submissions > 0 and topic_name not in profile.preferred_topics:
                profile.preferred_topics.append(topic_name)

    def _compact_learning_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        topic_metrics = {}
        for topic, metric in (signals.get("topic_metrics") or {}).items():
            topic_metrics[str(topic)] = {
                "submissions": self._safe_int(metric.get("submissions")),
                "pass_rate": self._safe_float(metric.get("pass_rate")),
                "first_pass_rate": self._safe_float(metric.get("first_pass_rate")),
                "consecutive_failures": self._safe_int(metric.get("consecutive_failures")),
                "answer_views": self._safe_int(metric.get("answer_views")),
                "hint_views": self._safe_int(metric.get("hint_views")),
                "average_dwell_seconds": self._safe_float(metric.get("average_dwell_seconds")),
            }
        return {
            "total_submission_count": self._safe_int(signals.get("total_submission_count")),
            "question_submission_count": self._safe_int(signals.get("question_submission_count")),
            "lesson_submission_count": self._safe_int(signals.get("lesson_submission_count")),
            "first_pass_rate": self._safe_float(signals.get("first_pass_rate")),
            "question_first_pass_rate": self._safe_float(signals.get("question_first_pass_rate")),
            "lesson_first_pass_rate": self._safe_float(signals.get("lesson_first_pass_rate")),
            "average_attempts_per_question": self._safe_float(signals.get("average_attempts_per_question")),
            "average_attempts_per_lesson": self._safe_float(signals.get("average_attempts_per_lesson")),
            "answer_view_count": self._safe_int(signals.get("answer_view_count")),
            "hint_view_count": self._safe_int(signals.get("hint_view_count")),
            "answer_view_rate": self._safe_float(signals.get("answer_view_rate")),
            "hint_view_rate": self._safe_float(signals.get("hint_view_rate")),
            "frequent_answer_view": bool(signals.get("frequent_answer_view")),
            "frequent_hint_view": bool(signals.get("frequent_hint_view")),
            "consecutive_failures_by_topic": dict(signals.get("consecutive_failures_by_topic") or {}),
            "long_dwell_targets": list(signals.get("long_dwell_targets") or [])[:5],
            "topic_metrics": topic_metrics,
        }

    @staticmethod
    def _add_pattern(patterns: List[str], pattern: str) -> None:
        if pattern not in patterns:
            patterns.append(pattern)

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    def _infer_correctness(self, profile_data: Dict[str, Any]) -> bool:
        if "correct" in profile_data:
            return bool(profile_data["correct"])
        score = profile_data.get("score")
        if isinstance(score, (int, float)):
            return score >= 0.6
        evaluation_score = profile_data.get("evaluation_score")
        if isinstance(evaluation_score, (int, float)):
            return evaluation_score >= 70
        return True


class PersonalizedSuggestionAgent:
    """Generates suggestions from the current profile."""

    async def generate_personalized_suggestion(self, user_profile: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        weak_topics = user_profile.get("weak_topics", [])
        if weak_topics:
            suggestions.append(f"建议优先复习这些薄弱主题：{', '.join(weak_topics[:3])}。")
            suggestions.append(f"先做 2 道 {weak_topics[0]} 的基础题，再做 1 道变式题。")

        error_patterns = user_profile.get("error_patterns", {})
        common_errors = [pattern for patterns in error_patterns.values() for pattern in patterns]
        if common_errors:
            top_error = Counter(common_errors).most_common(1)[0][0]
            suggestions.append(f"最近常见问题是 {top_error}，建议先做一次针对性订正。")

        behavior_metrics = (user_profile.get("study_time_patterns") or {}).get("behavior_metrics") or {}
        if behavior_metrics:
            total_submissions = int(behavior_metrics.get("total_submission_count") or 0)
            first_pass_rate = float(behavior_metrics.get("first_pass_rate") or 0.0)
            if total_submissions >= 3 and first_pass_rate < 0.5:
                suggestions.append("首次通过率偏低，做题前先写清输入输出样例。")
            if behavior_metrics.get("frequent_answer_view"):
                suggestions.append("查看答案偏多，建议先写思路和伪代码再对照答案。")
            if behavior_metrics.get("frequent_hint_view"):
                suggestions.append("提示依赖偏高，建议每题先独立尝试 10 分钟。")
            failure_topics = behavior_metrics.get("consecutive_failures_by_topic") or {}
            if failure_topics:
                topic, count = max(failure_topics.items(), key=lambda item: int(item[1] or 0))
                suggestions.append(f"{topic} 连续失败 {count} 次，先回到对应基础题巩固。")
            long_dwell_targets = behavior_metrics.get("long_dwell_targets") or []
            if long_dwell_targets:
                suggestions.append("部分题目停留较久，建议向助教请求分步骤提示。")

        learning_style = user_profile.get("learning_style", "visual")
        if learning_style == "visual":
            suggestions.append("讲新概念时建议配合流程图、表格或输入输出示例。")
        elif learning_style == "kinesthetic":
            suggestions.append("每学一个概念后立刻写 5 到 10 行小代码验证。")
        else:
            suggestions.append("建议先用自己的话总结概念，再用一道短题检查理解。")

        prompt = (
            "角色：你是编程学习教练。\n"
            "任务：基于用户画像补充 2 条具体、可执行的学习建议。\n"
            "约束：不要泛泛而谈；每条建议必须包含一个具体行动；不要重复已有建议。\n"
            "输出：只输出两条短建议，每条不超过 35 个字。\n"
            f"{build_profile_instruction(user_profile, 'personal')}\n"
            f"用户画像摘要:\n{build_profile_summary(user_profile)}\n"
            f"已有建议:\n{suggestions}"
        )
        llm_response = await llm_client.generate_response(
            system_prompt=(
                "你是编程教育中的个性化学习教练，回答必须具体、可执行。"
                "必须先读取用户画像摘要，再按当前用户类型调整建议力度、粒度和下一步任务。"
            ),
            user_message=prompt,
            use_cache=False,
            task_type="personal",
        )
        if llm_response and "目前无法调用大模型" not in llm_response:
            suggestions.append(f"AI建议：{llm_response.strip()}")

        deduped: List[str] = []
        for item in suggestions:
            if item not in deduped:
                deduped.append(item)
        return deduped[:5]


class LearningPathGenerationAgent:
    """Builds a staged learning path."""

    def __init__(self) -> None:
        self.base_paths = {
            "beginner": ["Python 基础语法", "条件与循环", "函数", "常用数据结构", "基础调试"],
            "intermediate": ["函数式拆分", "面向对象", "文件与模块", "常用算法", "项目实践"],
            "advanced": ["异步编程", "性能优化", "工程化结构", "测试设计", "复杂项目实践"],
        }

    async def generate_learning_path(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        level = str(user_profile.get("programming_level", "beginner"))
        weak_topics = list(user_profile.get("weak_topics", []))
        preferred_topics = list(user_profile.get("preferred_topics", []))
        path = list(self.base_paths.get(level, self.base_paths["beginner"]))
        for topic in reversed(weak_topics[:2]):
            path.insert(0, f"专项补强：{topic}")
        if preferred_topics:
            path.append(f"扩展实践：{preferred_topics[0]}")
        return {
            "level": level,
            "path": path,
            "estimated_duration": f"{max(2, len(path) * 2)} 小时",
            "focus_areas": weak_topics[:3] or preferred_topics[:2] or ["python_basics"],
        }


class PersonalizedLearningAgent(BaseAgent):
    """High-level personalized learning agent."""

    def __init__(self) -> None:
        super().__init__("PersonalizedLearningAgent")
        self.tracking_agent = UserBehaviorTrackingAgent()
        self.cognition_agent = UserCognitionUpdateAgent()
        self.suggestion_agent = PersonalizedSuggestionAgent()
        self.path_agent = LearningPathGenerationAgent()

    async def track_user_behavior(self, behavior_data: Dict[str, Any]) -> None:
        user_id = behavior_data["user_id"]
        await self.tracking_agent.track_behavior(user_id, behavior_data)
        await self.cognition_agent.update_user_profile(user_id, behavior_data)

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        await self.cognition_agent.update_user_profile(user_id, profile_data)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        return await self.cognition_agent.get_user_profile(user_id)

    async def generate_personalized_suggestion(self, user_id: str) -> List[str]:
        user_profile = await self.get_user_profile(user_id)
        return await self.suggestion_agent.generate_personalized_suggestion(user_profile)

    async def generate_learning_path(self, user_id: str) -> Dict[str, Any]:
        user_profile = await self.get_user_profile(user_id)
        return await self.path_agent.generate_learning_path(user_profile)

    async def get_learning_summary(self, user_id: str) -> Dict[str, Any]:
        profile = await self.get_user_profile(user_id)
        behaviors = await self.tracking_agent.get_user_behaviors(user_id)
        intent_counter = Counter(item.get("intent", "unknown") for item in behaviors)
        return {"profile": profile, "recent_behavior_count": len(behaviors), "common_intents": intent_counter.most_common(3)}

    async def _decide_personal_action(
        self,
        content: str,
        request: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> str:
        context = request.get("context", {}) or {}
        task_context = context.get("task_context") or {}
        system_prompt = (
            "You are the personalized learning agent's request planner. "
            "Choose which personal-learning output should be produced from the optimized user input, task context, and profile. "
            "Infer from the full request and return strict JSON only."
        )
        user_message = json.dumps(
            {
                "content": content,
                "task_context": task_context,
                "intent_analysis": request.get("intent_analysis", {}),
                "profile_summary": build_profile_summary(user_profile),
                "allowed_actions": ["learning_path", "profile_summary", "suggestions"],
                "output_schema": {"action": "suggestions", "reason": "short reason"},
            },
            ensure_ascii=False,
        )
        try:
            response = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=False,
                task_type="personal",
            )
            data = json.loads(response.strip())
            action = str(data.get("action") or "suggestions")
            if action in {"learning_path", "profile_summary", "suggestions"}:
                return action
        except Exception:
            pass
        return "suggestions"

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        user_id = request["user_id"]
        content = str(request.get("content", ""))
        user_profile = await self.get_user_profile(user_id)
        self.log_activity("processing personalized request", {"user_id": user_id})
        log_agent_interaction(
            "sub_agent_received",
            "MainAgent",
            self.name,
            request_id=str(request.get("request_id", "")),
            user_id=user_id,
            payload={
                "content": content,
                "intent_analysis": request.get("intent_analysis", {}),
                "task_context": request.get("context", {}).get("task_context"),
                "user_type": infer_user_type(user_profile),
            },
        )

        personal_action = await self._decide_personal_action(content, request, user_profile)
        if personal_action == "learning_path":
            learning_path = await self.path_agent.generate_learning_path(user_profile)
            path_text = "\n".join(f"{index + 1}. {item}" for index, item in enumerate(learning_path["path"]))
            response_data = {
                "success": True,
                "response": f"个性化学习路径\n当前水平：{learning_path['level']}\n预计投入：{learning_path['estimated_duration']}\n{path_text}",
                "details": {"learning_path": learning_path, "topic": "personal_learning"},
            }
            log_agent_interaction(
                "sub_agent_completed",
                self.name,
                "MainAgent",
                request_id=str(request.get("request_id", "")),
                user_id=user_id,
                payload=response_data,
            )
            return response_data

        if personal_action == "profile_summary":
            response_data = {
                "success": True,
                "response": (
                    f"学习画像\n学习风格：{user_profile['learning_style']}\n"
                    f"当前水平：{user_profile['programming_level']}\n"
                    f"薄弱主题：{', '.join(user_profile['weak_topics']) or '暂无明显薄弱点'}"
                ),
                "details": {"user_profile": user_profile, "topic": "personal_learning"},
            }
            log_agent_interaction(
                "sub_agent_completed",
                self.name,
                "MainAgent",
                request_id=str(request.get("request_id", "")),
                user_id=user_id,
                payload=response_data,
            )
            return response_data

        suggestions = await self.suggestion_agent.generate_personalized_suggestion(user_profile)
        suggestion_text = "\n".join(f"- {item}" for item in suggestions)
        response_data = {
            "success": True,
            "response": f"个性化学习建议\n{suggestion_text}",
            "details": {"suggestions": suggestions, "topic": "personal_learning"},
        }
        log_agent_interaction(
            "sub_agent_completed",
            self.name,
            "MainAgent",
            request_id=str(request.get("request_id", "")),
            user_id=user_id,
            payload=response_data,
        )
        return response_data
