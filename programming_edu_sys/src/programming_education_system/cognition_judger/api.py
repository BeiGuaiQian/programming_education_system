# programming_education_system/cognition_api.py
"""
认知评估API服务 - 为智能体提供认知数据访问接口
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .cognition_assessment import CognitiveAssessmentModel, CognitiveProfile, CognitiveDimension, KnowledgeDomain


class CognitionAPI:
    """
    认知评估API服务
    提供标准化的接口供其他智能体调用
    """
    
    def __init__(self):
        self.assessment_model = CognitiveAssessmentModel()
        self.logger = logging.getLogger("CognitionAPI")
    
    async def record_interaction(self, 
                               user_id: str,
                               interaction_type: str,
                               interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录用户交互并更新认知评估
        """
        try:
            # 标准化交互数据
            standardized_data = self._standardize_interaction_data(interaction_type, interaction_data)
            
            # 进行认知评估
            profile = await self.assessment_model.assess_interaction(user_id, standardized_data)
            
            return {
                "success": True,
                "profile_updated": True,
                "cognitive_level": profile.overall_level,
                "assessment_confidence": profile.confidence
            }
            
        except Exception as e:
            self.logger.error(f"记录交互失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_cognitive_profile(self, user_id: str) -> Optional[CognitiveProfile]:
        """
        获取用户完整认知档案
        """
        return self.assessment_model.user_profiles.get(user_id)
    
    async def get_cognitive_level(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户认知水平摘要
        """
        profile = await self.get_cognitive_profile(user_id)
        
        if not profile:
            return {
                "overall_level": 0.5,
                "confidence": 0.1,
                "has_profile": False
            }
        
        return {
            "overall_level": profile.overall_level,
            "cognitive_dimensions": {
                dim.value: score for dim, score in profile.dimension_scores.items()
            },
            "knowledge_domains": {
                domain.value: score for domain, score in profile.domain_knowledge.items()
            },
            "learning_velocity": profile.learning_velocity,
            "knowledge_gaps": profile.knowledge_gaps,
            "strengths": profile.strengths,
            "confidence": profile.confidence,
            "last_updated": profile.last_updated.isoformat(),
            "has_profile": True
        }
    
    async def get_personalization_recommendations(self, 
                                                user_id: str,
                                                content_type: str) -> Dict[str, Any]:
        """
        基于认知水平获取个性化推荐
        """
        profile = await self.get_cognitive_profile(user_id)
        
        if not profile:
            return self._get_default_recommendations()
        
        recommendations = {
            "difficulty_level": self._recommend_difficulty(profile),
            "preferred_approach": self._recommend_approach(profile),
            "focus_areas": self._recommend_focus_areas(profile),
            "learning_strategy": self._recommend_strategy(profile),
            "content_complexity": self._recommend_complexity(profile)
        }
        
        return recommendations
    
    async def get_adaptive_content_parameters(self, user_id: str) -> Dict[str, Any]:
        """
        获取自适应内容参数
        """
        profile = await self.get_cognitive_profile(user_id)
        
        if not profile:
            return self._get_default_parameters()
        
        return {
            "explanation_depth": self._calculate_explanation_depth(profile),
            "example_complexity": self._calculate_example_complexity(profile),
            "hint_frequency": self._calculate_hint_frequency(profile),
            "scaffolding_level": self._calculate_scaffolding_level(profile),
            "challenge_threshold": self._calculate_challenge_threshold(profile)
        }
    
    def _standardize_interaction_data(self, 
                                    interaction_type: str, 
                                    data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化交互数据"""
        standardized = {
            'interaction_type': interaction_type,
            'timestamp': datetime.now(),
            'processing_time': data.get('processing_time', 0),
            'correctness': data.get('correctness', 0.5),
            'complexity': data.get('complexity', 0.5),
            'domain': data.get('domain', KnowledgeDomain.SYNTAX),
            'cognitive_level': data.get('cognitive_level', CognitiveDimension.REMEMBER),
            'attempt_count': data.get('attempt_count', 1),
            'hints_used': data.get('hints_used', 0),
            'code_quality': data.get('code_quality', 0.5),
            'explanation_depth': data.get('explanation_depth', 0.5)
        }
        
        # 根据交互类型调整参数
        if interaction_type == "exercise":
            standardized['cognitive_level'] = CognitiveDimension.APPLY
        elif interaction_type == "evaluation":
            standardized['cognitive_level'] = CognitiveDimension.EVALUATE
        elif interaction_type == "qa":
            standardized['cognitive_level'] = CognitiveDimension.UNDERSTAND
        
        return standardized
    
    def _recommend_difficulty(self, profile: CognitiveProfile) -> str:
        """推荐难度级别"""
        level = profile.overall_level
        
        if level < 0.3:
            return "beginner"
        elif level < 0.6:
            return "intermediate"
        else:
            return "advanced"
    
    def _recommend_approach(self, profile: CognitiveProfile) -> str:
        """推荐教学方法"""
        # 基于学习速度和认知偏好
        if profile.learning_velocity > 0.7:
            return "challenge_based"
        elif profile.dimension_scores[CognitiveDimension.CREATE] > 0.7:
            return "project_based"
        else:
            return "scaffolded"
    
    def _recommend_focus_areas(self, profile: CognitiveProfile) -> List[str]:
        """推荐重点学习领域"""
        return profile.knowledge_gaps[:3]  # 优先解决前3个知识漏洞
    
    def _recommend_strategy(self, profile: CognitiveProfile) -> str:
        """推荐学习策略"""
        if profile.dimension_scores[CognitiveDimension.ANALYZE] < 0.4:
            return "analytical_thinking"
        elif profile.dimension_scores[CognitiveDimension.APPLY] < 0.4:
            return "practical_application"
        else:
            return "comprehensive_development"
    
    def _recommend_complexity(self, profile: CognitiveProfile) -> float:
        """推荐内容复杂度"""
        return min(1.0, profile.overall_level + 0.1)  # 适度挑战
    
    def _calculate_explanation_depth(self, profile: CognitiveProfile) -> float:
        """计算解释深度"""
        understanding_level = profile.dimension_scores[CognitiveDimension.UNDERSTAND]
        return max(0.3, min(1.0, 1.0 - understanding_level + 0.2))
    
    def _calculate_example_complexity(self, profile: CognitiveProfile) -> float:
        """计算示例复杂度"""
        return profile.overall_level
    
    def _calculate_hint_frequency(self, profile: CognitiveProfile) -> float:
        """计算提示频率"""
        return max(0.1, min(1.0, 1.0 - profile.learning_velocity))
    
    def _calculate_scaffolding_level(self, profile: CognitiveProfile) -> float:
        """计算脚手架级别"""
        apply_level = profile.dimension_scores[CognitiveDimension.APPLY]
        return max(0.2, min(1.0, 1.0 - apply_level))
    
    def _calculate_challenge_threshold(self, profile: CognitiveProfile) -> float:
        """计算挑战阈值"""
        return min(0.9, profile.overall_level + 0.15)
    
    def _get_default_recommendations(self) -> Dict[str, Any]:
        """获取默认推荐"""
        return {
            "difficulty_level": "beginner",
            "preferred_approach": "scaffolded",
            "focus_areas": ["基础语法", "简单算法"],
            "learning_strategy": "foundation_building",
            "content_complexity": 0.3
        }
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """获取默认参数"""
        return {
            "explanation_depth": 0.8,
            "example_complexity": 0.3,
            "hint_frequency": 0.7,
            "scaffolding_level": 0.8,
            "challenge_threshold": 0.4
        }


# 全局API实例
_cognition_api_instance = None

def get_cognition_api():
    """获取认知API实例（单例模式）"""
    global _cognition_api_instance
    if _cognition_api_instance is None:
        _cognition_api_instance = CognitionAPI()
    return _cognition_api_instance