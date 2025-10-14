# programming_education_system/models/user_profile.py
"""
用户画像数据模型
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class KnowledgeMastery:
    """知识点掌握情况"""
    topic: str
    mastery_level: float  # 0-1之间的掌握度
    last_practiced: datetime
    error_patterns: List[str] = field(default_factory=list)

@dataclass
class UserProfile:
    """用户学习画像"""
    user_id: str
    learning_style: str = "visual"  # visual, auditory, reading, kinesthetic
    programming_level: str = "beginner"  # beginner, intermediate, advanced
    preferred_topics: List[str] = field(default_factory=list)
    knowledge_mastery: Dict[str, KnowledgeMastery] = field(default_factory=dict)
    learning_goals: List[str] = field(default_factory=list)
    study_time_patterns: Dict[str, int] = field(default_factory=dict)  # 学习时间模式
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_mastery(self, topic: str, correct: bool, difficulty: str):
        """更新知识点掌握度"""
        if topic not in self.knowledge_mastery:
            self.knowledge_mastery[topic] = KnowledgeMastery(
                topic=topic, 
                mastery_level=0.5, 
                last_practiced=datetime.now()
            )
        
        mastery = self.knowledge_mastery[topic]
        adjustment = 0.1 if correct else -0.15
        mastery.mastery_level = max(0.1, min(1.0, mastery.mastery_level + adjustment))
        mastery.last_practiced = datetime.now()
        self.updated_at = datetime.now()
    
    def get_weak_topics(self, threshold: float = 0.6) -> List[str]:
        """获取薄弱知识点"""
        return [topic for topic, mastery in self.knowledge_mastery.items() 
                if mastery.mastery_level < threshold]
    
    def get_learning_path_suggestions(self) -> List[str]:
        """获取学习路径建议"""
        weak_topics = self.get_weak_topics()
        suggestions = []
        
        if weak_topics:
            suggestions.append(f"建议优先复习以下薄弱知识点: {', '.join(weak_topics[:3])}")
        
        # 基于学习目标建议
        if "web_development" in self.learning_goals and "python_basics" not in self.knowledge_mastery:
            suggestions.append("建议先学习Python基础，再学习Web开发")
            
        return suggestions