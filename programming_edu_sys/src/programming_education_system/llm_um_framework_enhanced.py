# programming_education_system/llm_um_framework_enhanced.py
"""
增强版LLM-UM框架 - 基于大模型的科学认知评估
基于Bloom分类学和认知科学理论
完整修复版本 - 解决所有类型错误和更新问题
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np


class CognitiveDimension(Enum):
    """Bloom认知维度 - 完整版"""
    REMEMBER = "remember"  # 记忆：回忆事实和概念
    UNDERSTAND = "understand"  # 理解：解释概念和意义
    APPLY = "apply"  # 应用：在新情境中应用知识
    ANALYZE = "analyze"  # 分析：分解信息，理解结构
    EVALUATE = "evaluate"  # 评价：基于标准做出判断
    CREATE = "create"  # 创造：将元素组合成新模式


class KnowledgeDomain(Enum):
    """知识领域分类"""
    PYTHON_BASICS = "python_basics"
    DATA_STRUCTURES = "data_structures"
    ALGORITHMS = "algorithms"
    OOP = "oop"
    FUNCTIONAL = "functional"
    CONCURRENCY = "concurrency"
    DEBUGGING = "debugging"


@dataclass
class CognitiveSnapshot:
    """认知状态快照"""
    timestamp: datetime
    overall_level: float
    dimension_scores: Dict[CognitiveDimension, float]
    domain_mastery: Dict[KnowledgeDomain, float]
    confidence: float


@dataclass
class UserCognitiveProfile:
    """增强版用户认知档案"""
    user_id: str
    created_at: datetime
    updated_at: datetime

    # 核心认知能力
    cognitive_dimensions: Dict[CognitiveDimension, float]
    knowledge_domains: Dict[KnowledgeDomain, float]
    overall_cognitive_level: float

    # 学习特征分析
    learning_style: str  # visual, conceptual, practical, theoretical
    learning_pace: str  # slow, moderate, fast
    confidence_level: float  # 学习自信心

    # 元认知能力
    metacognitive_skills: Dict[str, float]  # 计划、监控、调节等

    # 历史轨迹
    cognitive_history: List[CognitiveSnapshot]
    interaction_count: int

    # 评估质量
    assessment_confidence: float
    data_sufficiency: float  # 数据充分性
    consistency_score: float  # 表现一致性

    # 个性化参数
    personalization_params: Dict[str, Any]


@dataclass
class InteractionAnalysis:
    """增强版交互分析"""
    interaction_id: str
    user_id: str
    timestamp: datetime
    interaction_type: str
    content: str
    user_response: str

    # 认知需求分析
    required_cognitive_level: float
    cognitive_demands: Dict[CognitiveDimension, float]
    knowledge_components: List[str]

    # 表现评估
    performance_score: float
    quality_indicators: Dict[str, float]  # 正确性、效率、创新性等
    error_patterns: List[str]

    # 认知状态推断
    demonstrated_abilities: Dict[CognitiveDimension, float]
    inferred_cognitive_state: Dict[str, Any]

    # LLM深度分析
    llm_cognitive_analysis: Dict[str, Any]
    analysis_confidence: float


class EnhancedLLMUMFramework:
    """
    增强版LLM-UM框架
    基于大模型的科学认知评估和动态更新
    """

    def __init__(self, llm_client, storage_backend=None):
        self.llm = llm_client
        self.storage = storage_backend
        self.logger = logging.getLogger("Enhanced-LLM-UM")

        # 用户档案存储
        self.user_profiles: Dict[str, UserCognitiveProfile] = {}
        self.interaction_history: Dict[str, List[InteractionAnalysis]] = {}

        # 初始化科学评估提示模板
        self.prompt_templates = self._init_scientific_prompts()

        # 认知评估参数
        self.learning_decay_rate = 0.95  # 知识遗忘率
        self.min_data_points = 5  # 最小有效数据点
        self.confidence_threshold = 0.7  # 置信度阈值

    def _init_scientific_prompts(self) -> Dict[str, str]:
        """初始化基于认知科学的提示模板"""
        return {
            "cognitive_analysis": """
你是一个认知科学专家，专门分析编程学习中的认知过程。请基于Bloom分类学对以下交互进行深度认知分析：

交互内容：{content}

用户响应：{response}

交互上下文：{context}

请从以下维度进行科学分析：

1. 认知需求分析（基于Bloom分类学）：
   - 记忆需求：需要回忆哪些事实、概念？
   - 理解需求：需要理解哪些原理、关系？
   - 应用需求：需要在什么情境中应用知识？
   - 分析需求：需要分析什么结构、模式？
   - 评价需求：需要基于什么标准进行评价？
   - 创造需求：需要创造什么新内容？

2. 表现评估：
   - 回答质量：准确性、完整性、深度
   - 思维过程：逻辑性、系统性、创新性
   - 知识应用：概念理解、技能运用、问题解决

3. 认知状态推断：
   - 展示的认知能力水平
   - 认知强项和弱项
   - 学习策略有效性
   - 元认知能力表现

请以严格的JSON格式输出，确保所有数值都是0-1之间的浮点数：

{{
  "cognitive_demands": {{
    "remember": 0.5,
    "understand": 0.5,
    "apply": 0.5,
    "analyze": 0.5,
    "evaluate": 0.5,
    "create": 0.5
  }},
  "demonstrated_abilities": {{
    "remember": 0.5,
    "understand": 0.5,
    "apply": 0.5,
    "analyze": 0.5,
    "evaluate": 0.5,
    "create": 0.5
  }},
  "performance_quality": 0.5,
  "quality_indicators": {{
    "accuracy": 0.5,
    "completeness": 0.5,
    "depth": 0.5,
    "logical_coherence": 0.5,
    "systematic_approach": 0.5,
    "innovative_thinking": 0.5
  }},
  "knowledge_application": 0.5,
  "error_analysis": [],
  "cognitive_insights": {{}},
  "confidence": 0.5
}}

注意：所有数值必须在0-1之间，quality_indicators中的每个指标都是单独的数值。
""",
            "profile_synthesis": """
你是一个用户认知建模专家。基于用户的历史交互数据，合成完整的认知档案：

历史交互分析：{analysis_history}

请基于认知科学理论，综合评估：

1. 总体认知发展水平
2. 各Bloom认知维度的能力发展
3. 各知识领域的掌握程度
4. 学习特征和认知风格
5. 元认知能力发展
6. 学习轨迹和进步模式

考虑以下因素：
- 表现一致性
- 学习曲线
- 认知发展模式
- 个性化学习特征

请输出完整的科学认知档案。
""",
            "update_strategy": """
作为认知建模控制器，请基于认知科学原则决定更新策略：

当前认知状态：{current_state}

新交互分析：{new_analysis}

历史表现趋势：{performance_trend}

基于以下认知科学原则决策：
1. 显著变化检测：认知状态是否有显著变化？
2. 学习一致性：新表现是否与历史模式一致？
3. 数据充分性：是否有足够数据支持更新？
4. 置信度评估：分析结果的可靠性如何？

请选择科学的更新策略。
"""
        }

    async def analyze_interaction_cognitive(self,
                                            user_id: str,
                                            interaction_data: Dict[str, Any]) -> InteractionAnalysis:
        """
        基于认知科学的交互分析 - 修复更新问题
        """
        self.logger.info(f"科学认知分析 - 用户: {user_id}")

        try:
            # 使用LLM进行深度认知分析
            cognitive_analysis = await self._perform_cognitive_analysis(interaction_data)

            # 构建科学分析结果
            analysis = self._create_analysis_from_cognitive_data(
                user_id, interaction_data, cognitive_analysis
            )

            # 存储分析结果
            await self._store_analysis(analysis)

            # 基于科学原则更新认知档案 - 确保这个步骤执行
            await self._scientific_profile_update(user_id, analysis)

            self.logger.info(
                f"认知分析完成 - 表现得分: {analysis.performance_score:.2f}, 分析置信度: {analysis.analysis_confidence:.2f}")

            return analysis

        except Exception as e:
            self.logger.error(f"认知分析失败: {e}")
            # 创建默认分析并尝试更新
            default_analysis = self._create_default_analysis(user_id, interaction_data)
            await self._store_analysis(default_analysis)
            await self._scientific_profile_update(user_id, default_analysis)
            return default_analysis

    def _create_analysis_from_cognitive_data(self,
                                             user_id: str,
                                             interaction_data: Dict[str, Any],
                                             cognitive_analysis: Dict[str, Any]) -> InteractionAnalysis:
        """从认知分析数据创建分析对象 - 修复类型问题"""
        # 从LLM分析中提取关键信息，确保所有值都是正确的类型
        performance_score = self._extract_performance_from_analysis(cognitive_analysis)
        analysis_confidence = self._ensure_float(cognitive_analysis.get('confidence', 0.3))
        required_level = self._ensure_float(cognitive_analysis.get('required_level', 0.5))

        # 确保认知维度数据有效
        cognitive_demands = self._parse_cognitive_dimensions(
            cognitive_analysis.get('cognitive_demands', {})
        )
        demonstrated_abilities = self._parse_cognitive_dimensions(
            cognitive_analysis.get('demonstrated_abilities', {})
        )

        # 确保知识组件是列表
        knowledge_components = self._ensure_list(cognitive_analysis.get('knowledge_components', []))

        # 确保质量指标是字典
        quality_indicators = self._ensure_quality_indicators(cognitive_analysis.get('quality_indicators', {}))

        # 确保错误模式是列表
        error_patterns = self._ensure_list(cognitive_analysis.get('error_analysis', []))

        # 确保推断状态是字典
        inferred_state = self._ensure_dict(cognitive_analysis.get('cognitive_insights', {}))

        return InteractionAnalysis(
            interaction_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            timestamp=datetime.now(),
            interaction_type=interaction_data.get('type', 'unknown'),
            content=self._safe_to_string(interaction_data.get('content', '')),
            user_response=self._safe_to_string(interaction_data.get('user_response', '')),
            required_cognitive_level=required_level,
            cognitive_demands=cognitive_demands,
            knowledge_components=knowledge_components,
            performance_score=performance_score,
            quality_indicators=quality_indicators,
            error_patterns=error_patterns,
            demonstrated_abilities=demonstrated_abilities,
            inferred_cognitive_state=inferred_state,
            llm_cognitive_analysis=cognitive_analysis,
            analysis_confidence=analysis_confidence
        )

    def _extract_performance_from_analysis(self, cognitive_analysis: Dict[str, Any]) -> float:
        """从认知分析中提取表现得分"""
        try:
            # 首先尝试 performance_quality
            if 'performance_quality' in cognitive_analysis:
                return self._ensure_float(cognitive_analysis['performance_quality'], 0.5)

            # 然后尝试从 quality_indicators 计算
            if 'quality_indicators' in cognitive_analysis:
                quality_indicators = cognitive_analysis['quality_indicators']
                if isinstance(quality_indicators, dict):
                    return self._calculate_score_from_quality_indicators(quality_indicators)

            # 最后尝试 knowledge_application
            if 'knowledge_application' in cognitive_analysis:
                return self._ensure_float(cognitive_analysis['knowledge_application'], 0.5)

            # 如果都没有，使用默认值
            return 0.5

        except Exception as e:
            self.logger.warning(f"从认知分析提取表现得分失败: {e}")
            return 0.5

    def _calculate_score_from_quality_indicators(self, quality_indicators: Dict[str, Any]) -> float:
        """从质量指标字典计算综合表现得分"""
        try:
            # 定义关键指标及其权重
            key_indicators = {
                'accuracy': 0.3,  # 准确性
                'completeness': 0.2,  # 完整性
                'depth': 0.15,  # 深度
                'logical_coherence': 0.2,  # 逻辑连贯性
                'systematic_approach': 0.1,  # 系统性
                'innovative_thinking': 0.05  # 创新性
            }

            total_score = 0.0
            total_weight = 0.0

            for indicator, weight in key_indicators.items():
                if indicator in quality_indicators:
                    score = self._ensure_float(quality_indicators[indicator], 0.5)
                    total_score += score * weight
                    total_weight += weight

            # 如果没有找到任何指标，返回默认值
            if total_weight == 0:
                return 0.5

            return total_score / total_weight

        except Exception as e:
            self.logger.warning(f"从质量指标计算得分失败: {e}")
            return 0.5

    def _ensure_quality_indicators(self, value: Any) -> Dict[str, float]:
        """确保质量指标是有效的字典"""
        if not isinstance(value, dict):
            return {}

        # 清理字典，确保所有值都是浮点数
        cleaned_indicators = {}
        for key, val in value.items():
            try:
                cleaned_indicators[key] = self._ensure_float(val, 0.5)
            except Exception as e:
                self.logger.warning(f"清理质量指标失败 {key}: {val}, 错误: {e}")
                continue

        return cleaned_indicators

    async def _perform_cognitive_analysis(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行基于认知科学的深度分析"""
        try:
            content = self._safe_to_string(interaction_data.get('content', ''), 500)
            response = self._safe_to_string(interaction_data.get('user_response', ''), 500)
            context = self._safe_to_string(interaction_data.get('context', ''), 200)

            prompt = self.prompt_templates["cognitive_analysis"].format(
                content=content,
                response=response,
                context=context
            )

            llm_response = await self.llm.generate_response(
                system_prompt="你是认知科学和编程教育专家",
                user_message=prompt
            )

            return self._parse_llm_response(llm_response)
        except Exception as e:
            self.logger.error(f"LLM分析失败: {e}")
            return self._get_default_cognitive_analysis()

    def _safe_to_string(self, value: Any, max_length: int = None) -> str:
        """安全地将任何值转换为字符串"""
        try:
            if value is None:
                return ""
            elif isinstance(value, (dict, list)):
                import json
                result = json.dumps(value, ensure_ascii=False)
            else:
                result = str(value)

            if max_length and len(result) > max_length:
                result = result[:max_length] + "..."
            return result
        except:
            return str(value)[:max_length] if max_length else str(value)

    def _get_default_cognitive_analysis(self) -> Dict[str, Any]:
        """获取默认认知分析结果"""
        return {
            'cognitive_demands': {dim.value: 0.5 for dim in CognitiveDimension},
            'demonstrated_abilities': {dim.value: 0.5 for dim in CognitiveDimension},
            'performance_quality': 0.5,
            'quality_indicators': {
                'accuracy': 0.5,
                'completeness': 0.5,
                'depth': 0.5,
                'logical_coherence': 0.5,
                'systematic_approach': 0.5,
                'innovative_thinking': 0.5
            },
            'knowledge_application': 0.5,
            'error_analysis': [],
            'cognitive_insights': {'level': 0.5},
            'confidence': 0.3
        }

    def _parse_cognitive_dimensions(self, dim_data: Dict) -> Dict[CognitiveDimension, float]:
        """解析认知维度数据 - 修复类型问题"""
        dimensions = {}

        # 如果dim_data不是字典，返回默认值
        if not isinstance(dim_data, dict):
            self.logger.warning(f"认知维度数据不是字典: {type(dim_data)}")
            return {dim: 0.5 for dim in CognitiveDimension}

        for dim_str, score in dim_data.items():
            try:
                dimension = CognitiveDimension(dim_str.lower())
                safe_score = self._ensure_float(score, 0.5)
                dimensions[dimension] = min(1.0, max(0.0, safe_score))
            except Exception as e:
                self.logger.warning(f"解析认知维度失败: {dim_str}={score}, 错误: {e}")
                continue

        # 确保所有维度都有值
        for dim in CognitiveDimension:
            if dim not in dimensions:
                dimensions[dim] = 0.5

        return dimensions

    def _ensure_float(self, value: Any, default: float = 0.5) -> float:
        """确保值是浮点数"""
        try:
            if value is None:
                return default
            elif isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                return float(value)
            else:
                self.logger.warning(f"无法将值转换为浮点数: {value}, 类型: {type(value)}")
                return default
        except (ValueError, TypeError) as e:
            self.logger.warning(f"值转换失败: {e}, 使用默认值: {default}")
            return default

    def _ensure_list(self, value: Any) -> List[Any]:
        """确保值是列表"""
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        elif isinstance(value, (str, int, float)):
            return [value]
        else:
            try:
                return list(value)
            except:
                return []

    def _ensure_dict(self, value: Any) -> Dict[str, Any]:
        """确保值是字典"""
        if value is None:
            return {}
        elif isinstance(value, dict):
            return value
        else:
            try:
                return dict(value)
            except:
                return {}

    async def _scientific_profile_update(self, user_id: str, new_analysis: InteractionAnalysis):
        """基于科学原则更新认知档案 - 修复更新逻辑"""
        try:
            current_profile = self.user_profiles.get(user_id)

            if not current_profile:
                # 初次创建档案
                new_profile = await self._synthesize_cognitive_profile(user_id)
                self.logger.info(f"创建新用户认知档案 - 用户: {user_id}")
            else:
                # 渐进更新现有档案
                new_profile = await self._incremental_scientific_update(current_profile, new_analysis)
                self.logger.info(
                    f"更新用户认知档案 - 用户: {user_id}, 原水平: {current_profile.overall_cognitive_level:.3f}, 新水平: {new_profile.overall_cognitive_level:.3f}")

            # 存储更新后的档案
            self.user_profiles[user_id] = new_profile
            await self._store_user_profile(new_profile)

        except Exception as e:
            self.logger.error(f"认知档案更新失败: {e}")
            # 即使更新失败，也要确保有档案存在
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = self._create_initial_profile(user_id)

    async def _incremental_scientific_update(self,
                                             current_profile: UserCognitiveProfile,
                                             new_analysis: InteractionAnalysis) -> UserCognitiveProfile:
        """基于认知科学的渐进更新 """
        try:
            # 安全获取表现得分 - 处理可能的字典类型
            performance_score = self._extract_performance_score(new_analysis)
            analysis_confidence = self._ensure_float(new_analysis.analysis_confidence, 0.3)

            # 计算学习率（基于表现和置信度）
            base_learning_rate = 0.3
            learning_rate = base_learning_rate * performance_score * analysis_confidence

            # 更新认知维度
            updated_dimensions = {}
            for dimension in CognitiveDimension:
                current_score = self._ensure_float(
                    current_profile.cognitive_dimensions.get(dimension, 0.5), 0.5
                )

                # 安全获取展示的能力分数
                demonstrated_score = self._ensure_float(
                    new_analysis.demonstrated_abilities.get(dimension, current_score),
                    current_score
                )

                # 基于展示能力和学习率更新
                ability_gap = demonstrated_score - current_score
                update_amount = ability_gap * learning_rate
                updated_dimensions[dimension] = max(0.0, min(1.0, current_score + update_amount))

            # 更新知识领域
            updated_domains = {}
            for domain in KnowledgeDomain:
                current_mastery = self._ensure_float(
                    current_profile.knowledge_domains.get(domain, 0.5), 0.5
                )

                # 检查是否有相关的知识组件
                domain_components = self._get_components_for_domain(
                    new_analysis.knowledge_components, domain
                )

                if domain_components:
                    # 基于表现更新掌握度
                    performance_impact = (performance_score - 0.5) * learning_rate * 0.5
                    updated_domains[domain] = max(0.0, min(1.0, current_mastery + performance_impact))
                else:
                    # 没有相关组件，保持原样
                    updated_domains[domain] = current_mastery

            # 计算新的总体认知水平
            new_overall = self._calculate_overall_level(updated_dimensions, updated_domains)

            # 更新学习特征（简化的更新逻辑）
            current_confidence = self._ensure_float(current_profile.confidence_level, 0.5)
            new_confidence = self._update_confidence(current_confidence, performance_score)

            # 创建认知快照
            snapshot = CognitiveSnapshot(
                timestamp=new_analysis.timestamp,
                overall_level=new_overall,
                dimension_scores=updated_dimensions.copy(),
                domain_mastery=updated_domains.copy(),
                confidence=analysis_confidence
            )

            # 构建更新后的档案
            return UserCognitiveProfile(
                user_id=current_profile.user_id,
                created_at=current_profile.created_at,
                updated_at=datetime.now(),
                cognitive_dimensions=updated_dimensions,
                knowledge_domains=updated_domains,
                overall_cognitive_level=new_overall,
                learning_style=current_profile.learning_style,
                learning_pace=current_profile.learning_pace,
                confidence_level=new_confidence,
                metacognitive_skills=self._update_metacognitive_skills(
                    current_profile.metacognitive_skills, new_analysis, performance_score
                ),
                cognitive_history=current_profile.cognitive_history + [snapshot],
                interaction_count=current_profile.interaction_count + 1,
                assessment_confidence=analysis_confidence,
                data_sufficiency=self._calculate_data_sufficiency(current_profile.interaction_count + 1),
                consistency_score=self._calculate_consistency(current_profile.cognitive_history + [snapshot]),
                personalization_params=self._update_personalization_params(
                    current_profile, new_analysis, new_overall
                )
            )

        except Exception as e:
            self.logger.error(f"渐进更新失败: {e}")
            # 返回原始档案作为回退
            return current_profile

    def _extract_performance_score(self, analysis: InteractionAnalysis) -> float:
        """从分析中提取表现得分 - 处理字典类型的 quality_indicators"""
        try:
            # 首先尝试直接使用 performance_score
            if hasattr(analysis, 'performance_score') and analysis.performance_score is not None:
                return self._ensure_float(analysis.performance_score, 0.5)

            # 如果 performance_score 不可用，从 quality_indicators 计算
            if (hasattr(analysis, 'quality_indicators') and
                    analysis.quality_indicators and
                    isinstance(analysis.quality_indicators, dict)):
                return self._calculate_score_from_quality_indicators(analysis.quality_indicators)

            # 如果都没有，使用默认值
            return 0.5

        except Exception as e:
            self.logger.warning(f"提取表现得分失败: {e}")
            return 0.5

    def _get_components_for_domain(self, components: List[str], domain: KnowledgeDomain) -> List[str]:
        """获取指定领域的相关组件"""
        domain_keywords = {
            KnowledgeDomain.PYTHON_BASICS: ['变量', '函数', '类', '语法', '基础', 'python'],
            KnowledgeDomain.DATA_STRUCTURES: ['列表', '字典', '元组', '集合', '数组', '链表', '栈', '队列'],
            KnowledgeDomain.ALGORITHMS: ['算法', '排序', '查找', '递归', '复杂度', '二分', '动态规划'],
            KnowledgeDomain.OOP: ['面向对象', '继承', '多态', '封装', '类', '对象'],
            KnowledgeDomain.FUNCTIONAL: ['lambda', '高阶函数', '装饰器', '函数式'],
            KnowledgeDomain.CONCURRENCY: ['线程', '进程', '异步', '并发'],
            KnowledgeDomain.DEBUGGING: ['调试', '错误', '异常', 'bug']
        }

        keywords = domain_keywords.get(domain, [])
        return [comp for comp in components if any(kw in comp.lower() for kw in keywords)]

    def _update_confidence(self, current_confidence: float, performance_score: float) -> float:
        """更新学习自信心"""
        confidence_change = (performance_score - 0.5) * 0.1
        return max(0.1, min(1.0, current_confidence + confidence_change))

    def _update_metacognitive_skills(self,
                                     current_skills: Dict[str, float],
                                     analysis: InteractionAnalysis,
                                     performance_score: float) -> Dict[str, float]:
        """更新元认知技能"""
        updated_skills = current_skills.copy()

        # 基于错误分析和表现更新元认知
        if analysis.error_patterns:
            # 有系统性错误，监控能力可能需要提升
            updated_skills['monitoring'] = max(0.1, updated_skills.get('monitoring', 0.5) - 0.05)

        if performance_score > 0.8:
            # 优秀表现，自我调节能力可能较强
            updated_skills['regulation'] = min(1.0, updated_skills.get('regulation', 0.5) + 0.05)
            updated_skills['evaluation'] = min(1.0, updated_skills.get('evaluation', 0.5) + 0.03)
        elif performance_score < 0.4:
            # 较差表现，规划和监控可能需要加强
            updated_skills['planning'] = max(0.1, updated_skills.get('planning', 0.5) - 0.05)
            updated_skills['monitoring'] = max(0.1, updated_skills.get('monitoring', 0.5) - 0.03)

        return updated_skills

    def _update_personalization_params(self,
                                       profile: UserCognitiveProfile,
                                       analysis: InteractionAnalysis,
                                       new_cognitive_level: float) -> Dict[str, Any]:
        """更新个性化参数"""
        current_params = profile.personalization_params.copy()

        # 基于新的认知水平调整参数
        current_params['explanation_depth'] = 0.9 - (new_cognitive_level * 0.4)
        current_params['example_complexity'] = 0.3 + (new_cognitive_level * 0.6)

        # 基于表现调整提示频率
        if analysis.performance_score < 0.4:
            current_params['hint_frequency'] = min(1.0, current_params.get('hint_frequency', 0.5) + 0.1)
        elif analysis.performance_score > 0.8:
            current_params['hint_frequency'] = max(0.1, current_params.get('hint_frequency', 0.5) - 0.1)

        return current_params

    def _calculate_data_sufficiency(self, interaction_count: int) -> float:
        """计算数据充分性"""
        sufficient_count = 10
        return min(1.0, interaction_count / sufficient_count)

    def _calculate_consistency(self, history: List[CognitiveSnapshot]) -> float:
        """计算表现一致性"""
        if len(history) < 2:
            return 0.5

        levels = [snapshot.overall_level for snapshot in history]
        if not levels:
            return 0.5

        # 计算方差（简化版）
        mean = sum(levels) / len(levels)
        variance = sum((level - mean) ** 2 for level in levels) / len(levels)

        # 方差越小，一致性越高
        consistency = 1.0 / (1.0 + variance * 10)
        return max(0.1, min(1.0, consistency))

    def _calculate_overall_level(self,
                                 dimensions: Dict[CognitiveDimension, float],
                                 domains: Dict[KnowledgeDomain, float]) -> float:
        """计算总体认知水平"""
        # 认知维度加权平均
        dimension_weights = {
            CognitiveDimension.REMEMBER: 0.1,
            CognitiveDimension.UNDERSTAND: 0.15,
            CognitiveDimension.APPLY: 0.2,
            CognitiveDimension.ANALYZE: 0.2,
            CognitiveDimension.EVALUATE: 0.2,
            CognitiveDimension.CREATE: 0.15
        }

        dimension_score = sum(
            score * dimension_weights[dim]
            for dim, score in dimensions.items()
        )

        # 知识领域平均
        domain_score = sum(domains.values()) / len(domains) if domains else 0.5

        # 综合得分
        return (dimension_score * 0.7 + domain_score * 0.3)

    async def _synthesize_cognitive_profile(self, user_id: str) -> UserCognitiveProfile:
        """基于历史数据合成认知档案"""
        analysis_history = self.interaction_history.get(user_id, [])

        if not analysis_history:
            return self._create_initial_profile(user_id)

        # 简化的合成逻辑
        return self._create_initial_profile(user_id)

    def _create_initial_profile(self, user_id: str) -> UserCognitiveProfile:
        """创建初始认知档案"""
        return UserCognitiveProfile(
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            cognitive_dimensions={dim: 0.5 for dim in CognitiveDimension},
            knowledge_domains={domain: 0.5 for domain in KnowledgeDomain},
            overall_cognitive_level=0.5,
            learning_style="balanced",
            learning_pace="moderate",
            confidence_level=0.5,
            metacognitive_skills={
                'planning': 0.5,
                'monitoring': 0.5,
                'evaluation': 0.5,
                'regulation': 0.5
            },
            cognitive_history=[],
            interaction_count=0,
            assessment_confidence=0.1,
            data_sufficiency=0.1,
            consistency_score=0.5,
            personalization_params={
                'explanation_depth': 0.7,
                'example_complexity': 0.5,
                'hint_frequency': 0.6,
                'scaffolding_level': 0.7,
                'feedback_detail': 0.6
            }
        )

    def _create_default_analysis(self, user_id: str, interaction_data: Dict[str, Any]) -> InteractionAnalysis:
        """创建默认分析结果"""
        return InteractionAnalysis(
            interaction_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            timestamp=datetime.now(),
            interaction_type=interaction_data.get('type', 'unknown'),
            content=self._safe_to_string(interaction_data.get('content', '')),
            user_response=self._safe_to_string(interaction_data.get('user_response', '')),
            required_cognitive_level=0.5,
            cognitive_demands={dim: 0.5 for dim in CognitiveDimension},
            knowledge_components=[],
            performance_score=0.5,
            quality_indicators={
                'accuracy': 0.5,
                'completeness': 0.5,
                'depth': 0.5,
                'logical_coherence': 0.5,
                'systematic_approach': 0.5,
                'innovative_thinking': 0.5
            },
            error_patterns=[],
            demonstrated_abilities={dim: 0.5 for dim in CognitiveDimension},
            inferred_cognitive_state={'level': 0.5},
            llm_cognitive_analysis={},
            analysis_confidence=0.3
        )

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str, strict=False)
        except Exception as e:
            self.logger.warning(f"LLM响应解析失败: {e}")

        return {}

    def _map_component_to_domain(self, component: str) -> Optional[KnowledgeDomain]:
        """将知识组件映射到领域"""
        mapping = {
            # Python基础
            "变量": KnowledgeDomain.PYTHON_BASICS,
            "函数": KnowledgeDomain.PYTHON_BASICS,
            "类": KnowledgeDomain.PYTHON_BASICS,
            "数据类型": KnowledgeDomain.PYTHON_BASICS,
            "控制流": KnowledgeDomain.PYTHON_BASICS,
            "模块": KnowledgeDomain.PYTHON_BASICS,

            # 数据结构
            "列表": KnowledgeDomain.DATA_STRUCTURES,
            "字典": KnowledgeDomain.DATA_STRUCTURES,
            "集合": KnowledgeDomain.DATA_STRUCTURES,
            "元组": KnowledgeDomain.DATA_STRUCTURES,
            "数组": KnowledgeDomain.DATA_STRUCTURES,
            "链表": KnowledgeDomain.DATA_STRUCTURES,

            # 算法
            "排序": KnowledgeDomain.ALGORITHMS,
            "查找": KnowledgeDomain.ALGORITHMS,
            "递归": KnowledgeDomain.ALGORITHMS,
            "复杂度": KnowledgeDomain.ALGORITHMS,
            "算法": KnowledgeDomain.ALGORITHMS,
            "动态规划": KnowledgeDomain.ALGORITHMS,

            # OOP
            "面向对象": KnowledgeDomain.OOP,
            "继承": KnowledgeDomain.OOP,
            "多态": KnowledgeDomain.OOP,
            "封装": KnowledgeDomain.OOP,
            "抽象": KnowledgeDomain.OOP,

            # 函数式编程
            "lambda": KnowledgeDomain.FUNCTIONAL,
            "高阶函数": KnowledgeDomain.FUNCTIONAL,
            "装饰器": KnowledgeDomain.FUNCTIONAL,
            "函数式": KnowledgeDomain.FUNCTIONAL,

            # 并发
            "线程": KnowledgeDomain.CONCURRENCY,
            "进程": KnowledgeDomain.CONCURRENCY,
            "异步": KnowledgeDomain.CONCURRENCY,
            "并发": KnowledgeDomain.CONCURRENCY,

            # 调试
            "调试": KnowledgeDomain.DEBUGGING,
            "错误": KnowledgeDomain.DEBUGGING,
            "异常": KnowledgeDomain.DEBUGGING
        }

        for key, domain in mapping.items():
            if key in component.lower():
                return domain

        return KnowledgeDomain.PYTHON_BASICS  # 默认

    async def _store_analysis(self, analysis: InteractionAnalysis):
        """存储交互分析"""
        if analysis.user_id not in self.interaction_history:
            self.interaction_history[analysis.user_id] = []
        self.interaction_history[analysis.user_id].append(analysis)

    async def _store_user_profile(self, profile: UserCognitiveProfile):
        """存储用户档案"""
        self.user_profiles[profile.user_id] = profile

    # 公共API方法
    async def get_user_profile(self, user_id: str) -> Optional[UserCognitiveProfile]:
        """获取用户认知档案"""
        return self.user_profiles.get(user_id)

    async def get_cognitive_state(self, user_id: str) -> Dict[str, Any]:
        """获取认知状态（供其他智能体使用）"""
        profile = await self.get_user_profile(user_id)

        if not profile:
            return self._get_default_cognitive_state(user_id)

        return {
            'user_id': user_id,
            'overall_cognitive_level': profile.overall_cognitive_level,
            'cognitive_dimensions': {
                dim.value: score for dim, score in profile.cognitive_dimensions.items()
            },
            'knowledge_domains': {
                domain.value: mastery for domain, mastery in profile.knowledge_domains.items()
            },
            'learning_characteristics': {
                'learning_style': profile.learning_style,
                'learning_pace': profile.learning_pace,
                'confidence_level': profile.confidence_level
            },
            'metacognitive_skills': profile.metacognitive_skills,
            'assessment_quality': {
                'confidence': profile.assessment_confidence,
                'data_sufficiency': profile.data_sufficiency,
                'consistency': profile.consistency_score
            },
            'personalization_params': profile.personalization_params,
            'interaction_count': profile.interaction_count,
            'last_updated': profile.updated_at.isoformat()
        }

    def _get_default_cognitive_state(self, user_id: str) -> Dict[str, Any]:
        """获取默认认知状态"""
        return {
            'user_id': user_id,
            'overall_cognitive_level': 0.5,
            'cognitive_dimensions': {dim.value: 0.5 for dim in CognitiveDimension},
            'knowledge_domains': {domain.value: 0.5 for domain in KnowledgeDomain},
            'learning_characteristics': {
                'learning_style': 'balanced',
                'learning_pace': 'moderate',
                'confidence_level': 0.5
            },
            'metacognitive_skills': {
                'planning': 0.5,
                'monitoring': 0.5,
                'evaluation': 0.5,
                'regulation': 0.5
            },
            'assessment_quality': {
                'confidence': 0.1,
                'data_sufficiency': 0.1,
                'consistency': 0.5
            },
            'personalization_params': {
                'explanation_depth': 0.7,
                'example_complexity': 0.5,
                'hint_frequency': 0.6,
                'scaffolding_level': 0.7,
                'feedback_detail': 0.6
            },
            'interaction_count': 0,
            'last_updated': datetime.now().isoformat()
        }

    async def debug_cognitive_state(self, user_id: str) -> Dict[str, Any]:
        """调试认知状态"""
        profile = await self.get_user_profile(user_id)
        history = self.interaction_history.get(user_id, [])

        debug_info = {
            'user_id': user_id,
            'has_profile': profile is not None,
            'interaction_count': len(history),
            'recent_performance': [],
            'profile_details': {}
        }

        if profile:
            debug_info['profile_details'] = {
                'overall_level': profile.overall_cognitive_level,
                'interaction_count': profile.interaction_count,
                'last_updated': profile.updated_at.isoformat(),
                'assessment_confidence': profile.assessment_confidence,
                'data_sufficiency': profile.data_sufficiency
            }

        # 记录最近几次交互的表现
        for analysis in history[-5:]:
            debug_info['recent_performance'].append({
                'timestamp': analysis.timestamp.isoformat(),
                'performance_score': analysis.performance_score,
                'analysis_confidence': analysis.analysis_confidence,
                'type': analysis.interaction_type
            })

        return debug_info

    async def debug_analysis_data(self, user_id: str) -> Dict[str, Any]:
        """调试分析数据"""
        history = self.interaction_history.get(user_id, [])
        profile = await self.get_user_profile(user_id)

        debug_info = {
            'user_id': user_id,
            'profile_exists': profile is not None,
            'interaction_count': len(history),
            'recent_analyses': []
        }

        for i, analysis in enumerate(history[-3:]):  # 最近3次分析
            analysis_debug = {
                'interaction_id': analysis.interaction_id,
                'type': analysis.interaction_type,
                'performance_score': analysis.performance_score,
                'analysis_confidence': analysis.analysis_confidence,
                'quality_indicators_type': type(analysis.quality_indicators).__name__,
                'quality_indicators_value': analysis.quality_indicators,
                'demonstrated_abilities_type': type(analysis.demonstrated_abilities).__name__,
                'demonstrated_abilities_sample': dict(
                    list(analysis.demonstrated_abilities.items())[:2]) if analysis.demonstrated_abilities else {}
            }
            debug_info['recent_analyses'].append(analysis_debug)

        return debug_info