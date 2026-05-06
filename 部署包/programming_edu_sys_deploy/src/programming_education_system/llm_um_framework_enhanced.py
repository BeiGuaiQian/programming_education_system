"""Compatibility wrapper for the enhanced LLM user-model framework."""

from __future__ import annotations

from programming_education_system.cognition_judger.cognitive_api_scientific import (
    CognitiveSnapshot,
    InteractionAnalysis,
    UserCognitiveProfile,
)
from programming_education_system.utils.llm_utils import llm_client


class EnhancedLLMUMFramework:
    """Thin compatibility layer that reuses the lightweight cognition API implementation."""

    def __init__(self, llm_client_instance=None, storage_backend=None) -> None:
        self.llm = llm_client_instance or llm_client
        self.storage = storage_backend
        self.user_profiles = {}
        self.interaction_history = {}

    async def analyze_interaction_cognitive(self, user_id: str, interaction_data):
        from programming_education_system.cognition_judger.cognitive_api_scientific import (
            ScientificCognitiveAPI,
        )

        api = ScientificCognitiveAPI()
        result = await api.analyze_learning_interaction(user_id, interaction_data)
        analysis_id = result.get("analysis_id", f"{user_id}_analysis")
        cognitive = result.get("cognitive_analysis", {})
        return InteractionAnalysis(
            interaction_id=analysis_id,
            user_id=user_id,
            timestamp=__import__("datetime").datetime.now(),
            interaction_type=str(interaction_data.get("type", "general")),
            content=str(interaction_data.get("content", "")),
            user_response=str(interaction_data.get("user_response", "")),
            required_cognitive_level=float(cognitive.get("cognitive_level_demonstrated", 0.5)),
            cognitive_demands={
                "remember": 0.5,
                "understand": 0.5,
                "apply": 0.5,
                "analyze": 0.5,
                "evaluate": 0.5,
                "create": 0.5,
            },
            knowledge_components=list(cognitive.get("knowledge_components_activated", [])),
            performance_score=float(cognitive.get("performance_score", 0.5)),
            quality_indicators={"accuracy": float(cognitive.get("performance_score", 0.5))},
            error_patterns=list(cognitive.get("error_patterns_identified", [])),
            demonstrated_abilities={
                "remember": 0.5,
                "understand": 0.5,
                "apply": 0.5,
                "analyze": 0.5,
                "evaluate": 0.5,
                "create": 0.5,
            },
            inferred_cognitive_state={"level": float(cognitive.get("cognitive_level_demonstrated", 0.5))},
            llm_cognitive_analysis={"source": "compatibility_wrapper"},
            analysis_confidence=float(cognitive.get("analysis_confidence", 0.6)),
        )

    async def get_user_profile(self, user_id: str):
        return self.user_profiles.get(user_id)

    async def get_cognitive_state(self, user_id: str):
        from programming_education_system.cognition_judger.cognitive_api_scientific import (
            ScientificCognitiveAPI,
        )

        api = ScientificCognitiveAPI()
        return await api.get_cognitive_state(user_id)

    async def debug_cognitive_state(self, user_id: str):
        from programming_education_system.cognition_judger.cognitive_api_scientific import (
            ScientificCognitiveAPI,
        )

        api = ScientificCognitiveAPI()
        return await api.debug_cognitive_state(user_id)


__all__ = [
    "CognitiveSnapshot",
    "InteractionAnalysis",
    "UserCognitiveProfile",
    "EnhancedLLMUMFramework",
]
