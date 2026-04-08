"""Lightweight scientific cognitive API compatible with the original public interface."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CognitiveSnapshot:
    timestamp: datetime
    overall_level: float
    dimension_scores: Dict[str, float]
    domain_mastery: Dict[str, float]
    confidence: float


@dataclass
class InteractionAnalysis:
    interaction_id: str
    user_id: str
    timestamp: datetime
    interaction_type: str
    content: str
    user_response: str
    required_cognitive_level: float
    cognitive_demands: Dict[str, float]
    knowledge_components: List[str]
    performance_score: float
    quality_indicators: Dict[str, float]
    error_patterns: List[str]
    demonstrated_abilities: Dict[str, float]
    inferred_cognitive_state: Dict[str, Any]
    llm_cognitive_analysis: Dict[str, Any]
    analysis_confidence: float


@dataclass
class UserCognitiveProfile:
    user_id: str
    created_at: datetime
    updated_at: datetime
    overall_cognitive_level: float = 0.5
    cognitive_dimensions: Dict[str, float] = field(default_factory=dict)
    knowledge_domains: Dict[str, float] = field(default_factory=dict)
    learning_style: str = "balanced"
    learning_pace: str = "moderate"
    confidence_level: float = 0.5
    metacognitive_skills: Dict[str, float] = field(default_factory=dict)
    cognitive_history: List[CognitiveSnapshot] = field(default_factory=list)
    interaction_count: int = 0
    assessment_confidence: float = 0.5
    data_sufficiency: float = 0.1
    consistency_score: float = 0.5
    personalization_params: Dict[str, Any] = field(default_factory=dict)


class ScientificCognitiveAPI:
    """Provides simple cognition tracking and recommendation APIs."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("ScientificCognitiveAPI")
        self.user_profiles: Dict[str, UserCognitiveProfile] = {}
        self.interaction_history: Dict[str, List[InteractionAnalysis]] = {}

    async def analyze_learning_interaction(
        self, user_id: str, interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        profile = self._get_or_create_profile(user_id)
        analysis = self._build_analysis(user_id, interaction_data, profile)
        self.interaction_history.setdefault(user_id, []).append(analysis)
        self._update_profile(profile, analysis)

        return {
            "success": True,
            "analysis_id": analysis.interaction_id,
            "cognitive_analysis": {
                "performance_score": analysis.performance_score,
                "cognitive_level_demonstrated": analysis.required_cognitive_level,
                "knowledge_components_activated": analysis.knowledge_components,
                "error_patterns_identified": analysis.error_patterns,
                "analysis_confidence": analysis.analysis_confidence,
            },
            "updated_cognitive_state": await self.get_cognitive_state(user_id),
            "scientific_recommendations": await self._generate_scientific_recommendations(
                user_id, analysis, await self.get_cognitive_state(user_id)
            ),
            "debug_info": await self.debug_cognitive_state(user_id),
            "timestamp": datetime.now().isoformat(),
        }

    async def get_cognitive_state(self, user_id: str) -> Dict[str, Any]:
        profile = self._get_or_create_profile(user_id)
        return {
            "user_id": user_id,
            "overall_cognitive_level": profile.overall_cognitive_level,
            "cognitive_dimensions": profile.cognitive_dimensions,
            "knowledge_domains": profile.knowledge_domains,
            "learning_characteristics": {
                "learning_style": profile.learning_style,
                "learning_pace": profile.learning_pace,
                "confidence_level": profile.confidence_level,
            },
            "learning_trend": self._compute_learning_trend(profile),
            "metacognitive_skills": profile.metacognitive_skills,
            "assessment_quality": {
                "confidence": profile.assessment_confidence,
                "data_sufficiency": profile.data_sufficiency,
                "consistency": profile.consistency_score,
            },
            "personalization_params": profile.personalization_params,
            "interaction_count": profile.interaction_count,
            "last_updated": profile.updated_at.isoformat(),
        }

    async def get_personalized_learning_parameters(
        self, user_id: str, learning_context: str = "general"
    ) -> Dict[str, Any]:
        cognitive_state = await self.get_cognitive_state(user_id)
        level = cognitive_state["overall_cognitive_level"]
        return {
            "user_id": user_id,
            "learning_context": learning_context,
            "parameters": {
                "explanation_depth": max(0.3, 0.9 - level * 0.4),
                "example_complexity": min(1.0, 0.3 + level * 0.6),
                "conceptual_scaffolding": max(0.2, 0.8 - level * 0.5),
                "hint_strategy": "guided" if level < 0.4 else "balanced" if level < 0.7 else "minimal",
                "feedback_granularity": "detailed" if level < 0.4 else "focused" if level < 0.7 else "strategic",
                "progression_pace": "slow" if level < 0.4 else "moderate" if level < 0.7 else "adaptive",
            },
            "cognitive_basis": {
                "overall_level": level,
                "learning_style": cognitive_state["learning_characteristics"]["learning_style"],
                "confidence_level": cognitive_state["learning_characteristics"]["confidence_level"],
            },
        }

    async def get_learning_progression_analysis(self, user_id: str) -> Dict[str, Any]:
        profile = self._get_or_create_profile(user_id)
        return {
            "user_id": user_id,
            "has_sufficient_history": len(profile.cognitive_history) >= 2,
            "current_state": await self.get_cognitive_state(user_id),
            "progression_analysis": {
                "trend": self._compute_learning_trend(profile),
                "progress_rate": self._calculate_progress_rate(profile),
                "learning_consistency": profile.consistency_score,
                "development_trajectory": "steady_growth" if self._compute_learning_trend(profile) == "improving" else "stable",
            },
            "learning_trajectory": [
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "overall_level": snapshot.overall_level,
                    "key_strengths": [k for k, v in snapshot.dimension_scores.items() if v >= 0.65][:3],
                    "development_focus": min(snapshot.dimension_scores, key=snapshot.dimension_scores.get),
                }
                for snapshot in profile.cognitive_history
            ],
        }

    async def get_cognitive_strengths_weaknesses(self, user_id: str) -> Dict[str, Any]:
        cognitive_state = await self.get_cognitive_state(user_id)
        dimensions = cognitive_state["cognitive_dimensions"]
        strengths = [
            {"dimension": key, "display_name": key, "strength_level": value}
            for key, value in sorted(dimensions.items(), key=lambda item: item[1], reverse=True)
            if value >= 0.65
        ][:3]
        weaknesses = [
            {"dimension": key, "display_name": key, "weakness_level": value}
            for key, value in sorted(dimensions.items(), key=lambda item: item[1])
            if value < 0.55
        ][:3]
        return {
            "user_id": user_id,
            "cognitive_strengths": strengths,
            "cognitive_weaknesses": weaknesses,
            "development_priorities": [item["dimension"] for item in weaknesses] or ["balanced_development"],
            "balance_assessment": {
                "balance_level": self._calculate_balance_level(dimensions),
                "balance_status": "well_balanced" if self._calculate_balance_level(dimensions) >= 0.75 else "needs_balancing",
            },
        }

    async def get_learning_recommendations(
        self, user_id: str, learning_goal: str = None
    ) -> Dict[str, Any]:
        state = await self.get_cognitive_state(user_id)
        level = state["overall_cognitive_level"]
        weak_domains = [
            domain for domain, score in sorted(state["knowledge_domains"].items(), key=lambda item: item[1]) if score < 0.6
        ]
        return {
            "user_id": user_id,
            "learning_goal": learning_goal,
            "recommendations": {
                "recommended_difficulty": "beginner" if level < 0.4 else "intermediate" if level < 0.7 else "advanced",
                "focus_areas": weak_domains[:2] or ["python_basics"],
                "suggested_topics": weak_domains[:3] or ["python_basics", "data_structures"],
                "learning_strategy": "foundation_focused" if level < 0.4 else "balanced_approach" if level < 0.7 else "challenge_based",
                "estimated_pace": state["learning_characteristics"].get("learning_pace", "moderate"),
                "confidence": state["assessment_quality"]["confidence"],
            },
            "cognitive_basis": {
                "current_level": level,
                "weak_domains": weak_domains,
            },
        }

    async def debug_cognitive_state(self, user_id: str) -> Dict[str, Any]:
        profile = self._get_or_create_profile(user_id)
        return {
            "user_id": user_id,
            "has_profile": True,
            "interaction_count": profile.interaction_count,
            "profile_details": {
                "overall_level": profile.overall_cognitive_level,
                "last_updated": profile.updated_at.isoformat(),
                "assessment_confidence": profile.assessment_confidence,
                "data_sufficiency": profile.data_sufficiency,
            },
            "recent_performance": [
                {
                    "timestamp": item.timestamp.isoformat(),
                    "performance_score": item.performance_score,
                    "analysis_confidence": item.analysis_confidence,
                    "type": item.interaction_type,
                }
                for item in self.interaction_history.get(user_id, [])[-5:]
            ],
        }

    def _get_or_create_profile(self, user_id: str) -> UserCognitiveProfile:
        if user_id not in self.user_profiles:
            now = datetime.now()
            self.user_profiles[user_id] = UserCognitiveProfile(
                user_id=user_id,
                created_at=now,
                updated_at=now,
                cognitive_dimensions={
                    "remember": 0.5,
                    "understand": 0.5,
                    "apply": 0.5,
                    "analyze": 0.5,
                    "evaluate": 0.5,
                    "create": 0.5,
                },
                knowledge_domains={
                    "python_basics": 0.5,
                    "data_structures": 0.5,
                    "algorithms": 0.5,
                    "oop": 0.5,
                    "functional": 0.5,
                    "concurrency": 0.5,
                    "debugging": 0.5,
                },
                metacognitive_skills={
                    "planning": 0.5,
                    "monitoring": 0.5,
                    "evaluation": 0.5,
                    "regulation": 0.5,
                },
                personalization_params={
                    "explanation_depth": 0.7,
                    "example_complexity": 0.5,
                    "hint_frequency": 0.6,
                },
            )
        return self.user_profiles[user_id]

    def _build_analysis(
        self, user_id: str, interaction_data: Dict[str, Any], profile: UserCognitiveProfile
    ) -> InteractionAnalysis:
        content = str(interaction_data.get("content", ""))
        response = str(interaction_data.get("user_response", ""))
        score = self._estimate_performance_score(response, interaction_data.get("metadata", {}))
        level = max(0.2, min(1.0, 0.4 + len(content) / 500))
        knowledge_components = self._extract_knowledge_components(content)
        error_patterns = self._extract_error_patterns(response)
        dimensions = {
            key: max(0.1, min(1.0, value + (score - 0.5) * 0.08))
            for key, value in profile.cognitive_dimensions.items()
        }
        return InteractionAnalysis(
            interaction_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            timestamp=datetime.now(),
            interaction_type=str(interaction_data.get("type", "general")),
            content=content,
            user_response=response,
            required_cognitive_level=level,
            cognitive_demands=dimensions,
            knowledge_components=knowledge_components,
            performance_score=score,
            quality_indicators={
                "accuracy": score,
                "completeness": min(1.0, score + 0.05),
                "depth": level,
                "logical_coherence": score,
            },
            error_patterns=error_patterns,
            demonstrated_abilities=dimensions,
            inferred_cognitive_state={"level": score, "trend": self._compute_learning_trend(profile)},
            llm_cognitive_analysis={"mode": "lightweight_fallback"},
            analysis_confidence=0.65,
        )

    def _update_profile(self, profile: UserCognitiveProfile, analysis: InteractionAnalysis) -> None:
        profile.interaction_count += 1
        profile.updated_at = datetime.now()
        profile.overall_cognitive_level = max(
            0.1,
            min(1.0, profile.overall_cognitive_level * 0.8 + analysis.performance_score * 0.2),
        )
        profile.cognitive_dimensions.update(analysis.demonstrated_abilities)
        for component in analysis.knowledge_components:
            domain = self._map_component_to_domain(component)
            profile.knowledge_domains[domain] = max(
                0.1,
                min(1.0, profile.knowledge_domains.get(domain, 0.5) * 0.85 + analysis.performance_score * 0.15),
            )
        profile.confidence_level = max(0.1, min(1.0, profile.confidence_level * 0.8 + analysis.performance_score * 0.2))
        profile.assessment_confidence = min(1.0, 0.3 + profile.interaction_count * 0.05)
        profile.data_sufficiency = min(1.0, profile.interaction_count / 10)
        profile.consistency_score = self._calculate_consistency(profile)
        profile.cognitive_history.append(
            CognitiveSnapshot(
                timestamp=datetime.now(),
                overall_level=profile.overall_cognitive_level,
                dimension_scores=dict(profile.cognitive_dimensions),
                domain_mastery=dict(profile.knowledge_domains),
                confidence=profile.assessment_confidence,
            )
        )
        profile.cognitive_history = profile.cognitive_history[-20:]

    async def _generate_scientific_recommendations(
        self, user_id: str, analysis: InteractionAnalysis, cognitive_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        recommendations = await self.get_learning_recommendations(user_id, analysis.interaction_type)
        return {
            "immediate_focus": recommendations["recommendations"]["focus_areas"][0],
            "learning_strategy": recommendations["recommendations"]["learning_strategy"],
            "cognitive_development_priority": min(
                cognitive_state["cognitive_dimensions"], key=cognitive_state["cognitive_dimensions"].get
            ),
            "practice_recommendations": [f"Practice more on {item}" for item in analysis.knowledge_components[:3]],
            "meta_cognitive_guidance": [
                "Review the solution after each attempt.",
                "Write down the key mistake before moving on." if analysis.error_patterns else "Summarize the core idea in one sentence.",
            ],
        }

    def _estimate_performance_score(self, response: str, metadata: Dict[str, Any]) -> float:
        if isinstance(metadata.get("code_quality"), (int, float)):
            return max(0.1, min(1.0, float(metadata["code_quality"])))
        if isinstance(metadata.get("success"), bool):
            return 0.75 if metadata["success"] else 0.35
        length_bonus = min(0.2, len(response) / 500)
        return 0.5 + length_bonus

    def _extract_knowledge_components(self, content: str) -> List[str]:
        mapping = {
            "list": "data_structures",
            "dict": "data_structures",
            "class": "oop",
            "object": "oop",
            "sort": "algorithms",
            "递归": "algorithms",
            "debug": "debugging",
            "error": "debugging",
            "async": "concurrency",
            "function": "python_basics",
            "函数": "python_basics",
        }
        lowered = content.lower()
        found = [value for key, value in mapping.items() if key in lowered]
        return found or ["python_basics"]

    def _extract_error_patterns(self, response: str) -> List[str]:
        lowered = response.lower()
        patterns = []
        if "error" in lowered or "exception" in lowered:
            patterns.append("runtime_error")
        if "wrong" in lowered or "bug" in lowered or "错误" in lowered:
            patterns.append("logic_error")
        return patterns

    def _map_component_to_domain(self, component: str) -> str:
        return component if component in {
            "python_basics", "data_structures", "algorithms", "oop", "functional", "concurrency", "debugging"
        } else "python_basics"

    def _compute_learning_trend(self, profile: UserCognitiveProfile) -> str:
        history = profile.cognitive_history
        if len(history) < 2:
            return "stable"
        delta = history[-1].overall_level - history[0].overall_level
        if delta > 0.05:
            return "improving"
        if delta < -0.05:
            return "declining"
        return "stable"

    def _calculate_progress_rate(self, profile: UserCognitiveProfile) -> float:
        history = profile.cognitive_history
        if len(history) < 2:
            return 0.0
        elapsed_days = max(1, (history[-1].timestamp - history[0].timestamp).days or 1)
        return (history[-1].overall_level - history[0].overall_level) / elapsed_days

    def _calculate_consistency(self, profile: UserCognitiveProfile) -> float:
        history = [item.overall_level for item in profile.cognitive_history[-5:]]
        if len(history) < 2:
            return 0.5
        mean = sum(history) / len(history)
        variance = sum((item - mean) ** 2 for item in history) / len(history)
        return max(0.1, min(1.0, 1.0 / (1.0 + variance * 10)))

    def _calculate_balance_level(self, dimensions: Dict[str, float]) -> float:
        values = list(dimensions.values())
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return max(0.1, min(1.0, 1.0 / (1.0 + variance * 10)))


_scientific_cognitive_api: Optional[ScientificCognitiveAPI] = None


async def get_scientific_cognitive_api() -> ScientificCognitiveAPI:
    global _scientific_cognitive_api
    if _scientific_cognitive_api is None:
        _scientific_cognitive_api = ScientificCognitiveAPI()
    return _scientific_cognitive_api


def get_scientific_cognitive_api_sync() -> ScientificCognitiveAPI:
    global _scientific_cognitive_api
    if _scientific_cognitive_api is None:
        _scientific_cognitive_api = ScientificCognitiveAPI()
    return _scientific_cognitive_api
