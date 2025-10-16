# programming_education_system/cognition_assessment.py
"""
用户认知评估模型 - 基于Bloom认知分类学和知识空间理论
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from enum import Enum
import numpy as np
from dataclasses import dataclass
from datetime import datetime


class CognitiveDimension(Enum):
    """Bloom认知分类学维度"""
    REMEMBER = "remember"      # 记忆
    UNDERSTAND = "understand"  # 理解
    APPLY = "apply"           # 应用
    ANALYZE = "analyze"       # 分析
    EVALUATE = "evaluate"     # 评价
    CREATE = "create"         # 创造


class KnowledgeDomain(Enum):
    """编程知识领域"""
    SYNTAX = "syntax"           # 语法
    DATA_STRUCTURES = "data_structures"  # 数据结构
    ALGORITHMS = "algorithms"   # 算法
    OOP = "oop"                 # 面向对象
    FUNCTIONAL = "functional"   # 函数式编程
    CONCURRENCY = "concurrency" # 并发编程


@dataclass
class CognitiveProfile:
    """用户认知水平档案"""
    user_id: str
    overall_level: float  # 总体认知水平 (0-1)
    dimension_scores: Dict[CognitiveDimension, float]  # 各维度得分
    domain_knowledge: Dict[KnowledgeDomain, float]  # 领域知识掌握度
    learning_velocity: float  # 学习速度
    knowledge_gaps: List[str]  # 知识漏洞
    strengths: List[str]  # 优势领域
    last_updated: datetime
    confidence: float  # 评估置信度


class CognitiveAssessmentModel:
    """
    用户认知评估模型
    基于项目反应理论(IRT)和知识空间理论
    """
    
    def __init__(self):
        self.logger = logging.getLogger("CognitiveModel")
        self.user_profiles: Dict[str, CognitiveProfile] = {}
        
        # 认知维度权重 (基于Bloom分类学)
        self.cognitive_weights = {
            CognitiveDimension.REMEMBER: 0.1,
            CognitiveDimension.UNDERSTAND: 0.15,
            CognitiveDimension.APPLY: 0.2,
            CognitiveDimension.ANALYZE: 0.2,
            CognitiveDimension.EVALUATE: 0.2,
            CognitiveDimension.CREATE: 0.15
        }
        
        # 初始化基准参数
        self.difficulty_thresholds = {
            'easy': 0.3,
            'medium': 0.6,
            'hard': 0.8
        }

    async def assess_interaction(self, 
                               user_id: str, 
                               interaction_data: Dict[str, Any]) -> CognitiveProfile:
        """
        评估单次交互的认知表现
        """
        try:
            # 提取交互特征
            features = self._extract_features(interaction_data)
            
            # 计算认知维度得分
            dimension_scores = await self._calculate_dimension_scores(features)
            
            # 更新用户档案
            profile = await self._update_user_profile(user_id, dimension_scores, features)
            
            # 检测知识漏洞
            profile.knowledge_gaps = await self._detect_knowledge_gaps(profile, features)
            
            # 识别优势领域
            profile.strengths = await self._identify_strengths(profile)
            
            self.logger.info(f"认知评估完成 - 用户: {user_id}, 总体水平: {profile.overall_level:.3f}")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"认知评估失败: {e}")
            return await self._get_default_profile(user_id)

    def _extract_features(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """从交互数据中提取认知特征"""
        features = {
            'response_time': interaction_data.get('processing_time', 0),
            'correctness': interaction_data.get('correctness', 0.5),
            'complexity': interaction_data.get('complexity', 0.5),
            'domain': interaction_data.get('domain', KnowledgeDomain.SYNTAX),
            'cognitive_level': interaction_data.get('cognitive_level', CognitiveDimension.REMEMBER),
            'attempt_count': interaction_data.get('attempt_count', 1),
            'hints_used': interaction_data.get('hints_used', 0),
            'code_quality': interaction_data.get('code_quality', 0.5),
            'explanation_depth': interaction_data.get('explanation_depth', 0.5)
        }
        return features

    async def _calculate_dimension_scores(self, features: Dict[str, Any]) -> Dict[CognitiveDimension, float]:
        """计算各认知维度得分"""
        scores = {}
        
        # 基于IRT的项目反应计算
        base_score = self._irt_scoring(features)
        
        # 根据交互类型调整各维度权重
        for dimension in CognitiveDimension:
            weight = self._get_dimension_weight(dimension, features)
            adjustment = self._get_domain_adjustment(features['domain'], dimension)
            
            scores[dimension] = max(0, min(1, base_score * weight * adjustment))
        
        return scores

    def _irt_scoring(self, features: Dict[str, Any]) -> float:
        """基于项目反应理论的评分"""
        # 简化IRT模型: 能力 = 正确性 - 难度 * 时间惩罚
        correctness = features['correctness']
        difficulty = features['complexity']
        time_penalty = min(1, features['response_time'] / 300)  # 5分钟基准
        
        ability = correctness - (difficulty * 0.3) - (time_penalty * 0.2)
        return max(0, min(1, ability))

    def _get_dimension_weight(self, dimension: CognitiveDimension, features: Dict[str, Any]) -> float:
        """获取认知维度权重"""
        base_weight = self.cognitive_weights[dimension]
        
        # 根据交互特征调整权重
        if dimension == CognitiveDimension.CREATE and features.get('code_quality', 0) > 0.7:
            return base_weight * 1.3
        elif dimension == CognitiveDimension.ANALYZE and features.get('explanation_depth', 0) > 0.6:
            return base_weight * 1.2
            
        return base_weight

    def _get_domain_adjustment(self, domain: KnowledgeDomain, dimension: CognitiveDimension) -> float:
        """领域知识调整因子"""
        # 不同知识领域对认知维度的敏感性不同
        adjustments = {
            KnowledgeDomain.SYNTAX: {
                CognitiveDimension.REMEMBER: 1.2,
                CognitiveDimension.UNDERSTAND: 1.1
            },
            KnowledgeDomain.ALGORITHMS: {
                CognitiveDimension.APPLY: 1.3,
                CognitiveDimension.ANALYZE: 1.2
            },
            KnowledgeDomain.OOP: {
                CognitiveDimension.CREATE: 1.3,
                CognitiveDimension.EVALUATE: 1.2
            }
        }
        
        domain_adjustments = adjustments.get(domain, {})
        return domain_adjustments.get(dimension, 1.0)

    async def _update_user_profile(self, 
                                 user_id: str, 
                                 new_scores: Dict[CognitiveDimension, float],
                                 features: Dict[str, Any]) -> CognitiveProfile:
        """更新用户认知档案"""
        if user_id not in self.user_profiles:
            profile = await self._create_initial_profile(user_id)
        else:
            profile = self.user_profiles[user_id]
        
        # 指数加权移动平均更新
        alpha = 0.3  # 学习率
        for dimension, score in new_scores.items():
            old_score = profile.dimension_scores.get(dimension, 0.5)
            profile.dimension_scores[dimension] = (1 - alpha) * old_score + alpha * score
        
        # 更新总体水平
        profile.overall_level = self._calculate_overall_level(profile.dimension_scores)
        
        # 更新学习速度
        profile.learning_velocity = await self._calculate_learning_velocity(profile, features)
        
        # 更新领域知识
        await self._update_domain_knowledge(profile, features)
        
        profile.last_updated = datetime.now()
        profile.confidence = self._calculate_confidence(profile)
        
        self.user_profiles[user_id] = profile
        return profile

    def _calculate_overall_level(self, dimension_scores: Dict[CognitiveDimension, float]) -> float:
        """计算总体认知水平"""
        weighted_sum = 0
        total_weight = 0
        
        for dimension, score in dimension_scores.items():
            weight = self.cognitive_weights[dimension]
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5

    async def _calculate_learning_velocity(self, profile: CognitiveProfile, features: Dict[str, Any]) -> float:
        """计算学习速度"""
        # 基于响应时间、正确率提升、尝试次数等计算
        time_efficiency = 1.0 / (1.0 + features['response_time'] / 60)  # 时间效率
        mastery_speed = 1.0 / (1.0 + features['attempt_count'])  # 掌握速度
        
        return (time_efficiency + mastery_speed) / 2

    async def _update_domain_knowledge(self, profile: CognitiveProfile, features: Dict[str, Any]):
        """更新领域知识掌握度"""
        domain = features['domain']
        performance = features['correctness'] * 0.7 + features['code_quality'] * 0.3
        
        alpha = 0.4  # 领域知识更新率
        old_score = profile.domain_knowledge.get(domain, 0.5)
        profile.domain_knowledge[domain] = (1 - alpha) * old_score + alpha * performance

    async def _detect_knowledge_gaps(self, profile: CognitiveProfile, features: Dict[str, Any]) -> List[str]:
        """检测知识漏洞"""
        gaps = []
        
        # 低分认知维度
        for dimension, score in profile.dimension_scores.items():
            if score < 0.4:
                gaps.append(f"{dimension.value}能力需要加强")
        
        # 特定领域问题
        for domain, score in profile.domain_knowledge.items():
            if score < 0.3:
                gaps.append(f"{domain.value}领域基础薄弱")
            elif score < 0.6:
                gaps.append(f"{domain.value}领域需要巩固")
        
        return gaps

    async def _identify_strengths(self, profile: CognitiveProfile) -> List[str]:
        """识别优势领域"""
        strengths = []
        
        # 高分认知维度
        for dimension, score in profile.dimension_scores.items():
            if score > 0.8:
                strengths.append(f"优秀的{dimension.value}能力")
        
        # 优势知识领域
        for domain, score in profile.domain_knowledge.items():
            if score > 0.7:
                strengths.append(f"扎实的{domain.value}知识")
        
        return strengths

    def _calculate_confidence(self, profile: CognitiveProfile) -> float:
        """计算评估置信度"""
        # 基于数据量和一致性计算置信度
        interaction_count = len([k for k in profile.dimension_scores.keys()])
        consistency = 1.0 - np.std(list(profile.dimension_scores.values()))
        
        return min(1.0, interaction_count * 0.1 + consistency * 0.5)

    async def _create_initial_profile(self, user_id: str) -> CognitiveProfile:
        """创建初始认知档案"""
        initial_scores = {dim: 0.5 for dim in CognitiveDimension}
        initial_domains = {domain: 0.5 for domain in KnowledgeDomain}
        
        return CognitiveProfile(
            user_id=user_id,
            overall_level=0.5,
            dimension_scores=initial_scores,
            domain_knowledge=initial_domains,
            learning_velocity=0.5,
            knowledge_gaps=[],
            strengths=[],
            last_updated=datetime.now(),
            confidence=0.1
        )

    async def _get_default_profile(self, user_id: str) -> CognitiveProfile:
        """获取默认认知档案"""
        return await self._create_initial_profile(user_id)