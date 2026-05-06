"""User learning profile data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class KnowledgeMastery:
    """Mastery state for one knowledge topic."""

    topic: str
    mastery_level: float
    last_practiced: datetime
    error_patterns: List[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """Learning profile used by personalized agents."""

    user_id: str
    learning_style: str = "visual"
    programming_level: str = "beginner"
    preferred_topics: List[str] = field(default_factory=list)
    knowledge_mastery: Dict[str, KnowledgeMastery] = field(default_factory=dict)
    learning_goals: List[str] = field(default_factory=list)
    study_time_patterns: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_mastery(self, topic: str, correct: bool, difficulty: str) -> None:
        """Update mastery with a small difficulty-aware adjustment."""
        if topic not in self.knowledge_mastery:
            self.knowledge_mastery[topic] = KnowledgeMastery(
                topic=topic,
                mastery_level=0.5,
                last_practiced=datetime.now(),
            )

        difficulty_weight = {
            "beginner": 1.0,
            "medium": 1.1,
            "intermediate": 1.1,
            "advanced": 1.25,
        }.get(str(difficulty), 1.0)
        adjustment = (0.1 if correct else -0.15) * difficulty_weight
        mastery = self.knowledge_mastery[topic]
        mastery.mastery_level = max(0.1, min(1.0, mastery.mastery_level + adjustment))
        mastery.last_practiced = datetime.now()
        self.updated_at = datetime.now()

    def get_weak_topics(self, threshold: float = 0.6) -> List[str]:
        """Return topics whose mastery is below the threshold."""
        return [
            topic
            for topic, mastery in self.knowledge_mastery.items()
            if mastery.mastery_level < threshold
        ]

    def get_learning_path_suggestions(self) -> List[str]:
        """Return simple learning path suggestions."""
        weak_topics = self.get_weak_topics()
        suggestions: List[str] = []
        if weak_topics:
            suggestions.append(f"建议优先复习这些薄弱知识点：{', '.join(weak_topics[:3])}")
        if "web_development" in self.learning_goals and "python_basics" not in self.knowledge_mastery:
            suggestions.append("建议先学习 Python 基础，再学习 Web 开发。")
        return suggestions
