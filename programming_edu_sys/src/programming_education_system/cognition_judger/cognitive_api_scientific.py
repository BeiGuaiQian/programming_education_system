# programming_education_system/cognitive_api_scientific.py
"""
科学认知评估API - 基于增强版LLM-UM框架
为其他智能体提供科学的认知数据分析
完整修复版本 - 确保所有方法都存在
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from programming_education_system.llm_um_framework_enhanced import (
    EnhancedLLMUMFramework, UserCognitiveProfile, InteractionAnalysis,CognitiveSnapshot,
)
from programming_education_system.utils.llm_utils import llm_client

logger = logging.getLogger(__name__)


class ScientificCognitiveAPI:
    """
    科学认知评估API
    基于增强版LLM-UM框架，提供科学的认知分析服务
    """

    def __init__(self):
        self.logger = logging.getLogger("ScientificCognitiveAPI")

        # 使用增强版框架
        self.framework = EnhancedLLMUMFramework(llm_client)

        # 用户会话跟踪
        self.user_sessions: Dict[str, Dict[str, Any]] = {}

        self.logger.info("科学认知评估API初始化完成")

    async def analyze_learning_interaction(self,
                                           user_id: str,
                                           interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析学习交互 - 主要API方法
        """
        try:
            self.logger.info(f"分析学习交互 - 用户: {user_id}")

            # 准备认知分析数据
            cognitive_data = {
                'type': interaction_data.get('type', 'learning'),
                'content': interaction_data.get('content', ''),
                'user_response': interaction_data.get('user_response', ''),
                'context': interaction_data.get('context', ''),
                'metadata': interaction_data.get('metadata', {})
            }

            # 使用增强框架进行科学认知分析
            analysis = await self.framework.analyze_interaction_cognitive(
                user_id, cognitive_data
            )

            # 获取更新后的认知状态
            cognitive_state = await self.get_cognitive_state(user_id)

            # 生成科学的学习建议
            recommendations = await self._generate_scientific_recommendations(
                user_id, analysis, cognitive_state
            )

            # 记录会话
            await self._record_learning_session(user_id, interaction_data, analysis)

            # 调试信息
            debug_info = await self.framework.debug_cognitive_state(user_id)
            self.logger.info(
                f"认知更新调试 - 用户: {user_id}, 交互次数: {debug_info['interaction_count']}, 是否有档案: {debug_info['has_profile']}")

            return {
                'success': True,
                'analysis_id': analysis.interaction_id,
                'cognitive_analysis': {
                    'performance_score': analysis.performance_score,
                    'cognitive_level_demonstrated': analysis.required_cognitive_level,
                    'knowledge_components_activated': analysis.knowledge_components,
                    'error_patterns_identified': analysis.error_patterns,
                    'analysis_confidence': analysis.analysis_confidence
                },
                'updated_cognitive_state': cognitive_state,
                'scientific_recommendations': recommendations,
                'debug_info': debug_info,  # 添加调试信息
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"学习交互分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_cognitive_state(self, user_id: str) -> Dict[str, Any]:
        """
        获取科学认知状态 - 供其他智能体调用
        """
        return await self.framework.get_cognitive_state(user_id)

    async def get_personalized_learning_parameters(self,
                                                   user_id: str,
                                                   learning_context: str = "general") -> Dict[str, Any]:
        """
        获取个性化学习参数 - 基于科学认知评估
        """
        cognitive_state = await self.get_cognitive_state(user_id)

        # 基于认知科学计算参数
        parameters = self._calculate_scientific_parameters(cognitive_state, learning_context)

        return {
            'user_id': user_id,
            'learning_context': learning_context,
            'parameters': parameters,
            'cognitive_basis': {
                'overall_level': cognitive_state['overall_cognitive_level'],
                'learning_style': cognitive_state['learning_characteristics']['learning_style'],
                'confidence_level': cognitive_state['learning_characteristics']['confidence_level']
            }
        }

    async def get_learning_progression_analysis(self, user_id: str) -> Dict[str, Any]:
        """
        获取学习进展分析 - 基于认知发展轨迹
        """
        cognitive_state = await self.get_cognitive_state(user_id)
        profile = await self.framework.get_user_profile(user_id)

        if not profile or len(profile.cognitive_history) < 2:
            return {
                'user_id': user_id,
                'has_sufficient_history': False,
                'message': '需要更多学习数据来分析进展'
            }

        # 分析认知发展轨迹
        progression = self._analyze_cognitive_progression(profile)

        return {
            'user_id': user_id,
            'has_sufficient_history': True,
            'current_state': cognitive_state,
            'progression_analysis': progression,
            'learning_trajectory': self._extract_learning_trajectory(profile)
        }

    async def get_cognitive_strengths_weaknesses(self, user_id: str) -> Dict[str, Any]:
        """
        获取认知强项和弱项分析
        """
        cognitive_state = await self.get_cognitive_state(user_id)

        strengths = self._identify_cognitive_strengths(cognitive_state)
        weaknesses = self._identify_cognitive_weaknesses(cognitive_state)

        return {
            'user_id': user_id,
            'cognitive_strengths': strengths,
            'cognitive_weaknesses': weaknesses,
            'development_priorities': self._prioritize_development_areas(strengths, weaknesses),
            'balance_assessment': self._assess_cognitive_balance(cognitive_state)
        }

    async def get_learning_recommendations(self,
                                           user_id: str,
                                           learning_goal: str = None) -> Dict[str, Any]:
        """
        获取学习推荐 - 供教学策略智能体调用
        """
        try:
            cognitive_state = await self.get_cognitive_state(user_id)
            overall_level = cognitive_state['overall_cognitive_level']
            knowledge_domains = cognitive_state['knowledge_domains']

            # 分析知识薄弱点
            weak_domains = self._identify_weak_domains(knowledge_domains)

            # 生成推荐
            recommendations = {
                'recommended_difficulty': self._recommend_difficulty(overall_level),
                'focus_areas': weak_domains[:2],
                'suggested_topics': self._suggest_topics(knowledge_domains, learning_goal),
                'learning_strategy': self._recommend_strategy(overall_level),
                'estimated_pace': cognitive_state['learning_characteristics'].get('learning_pace', 'moderate'),
                'confidence': cognitive_state['assessment_quality']['confidence']
            }

            return {
                'user_id': user_id,
                'learning_goal': learning_goal,
                'recommendations': recommendations,
                'cognitive_basis': {
                    'current_level': overall_level,
                    'weak_domains': weak_domains
                }
            }
        except Exception as e:
            self.logger.error(f"获取学习推荐失败: {e}")
            return self._get_default_learning_recommendations(user_id, learning_goal)

    def _get_default_learning_recommendations(self, user_id: str, learning_goal: str) -> Dict[str, Any]:
        """获取默认学习推荐"""
        return {
            'user_id': user_id,
            'learning_goal': learning_goal,
            'recommendations': {
                'recommended_difficulty': 'intermediate',
                'focus_areas': ['Python基础'],
                'suggested_topics': ['函数定义', '数据类型'],
                'learning_strategy': 'balanced_approach',
                'estimated_pace': 'moderate',
                'confidence': 0.5
            }
        }

    def _recommend_difficulty(self, level: float) -> str:
        """推荐难度级别"""
        if level < 0.3:
            return "beginner"
        elif level < 0.6:
            return "intermediate"
        else:
            return "advanced"

    def _suggest_topics(self, knowledge_domains: Dict[str, float], learning_goal: str) -> List[str]:
        """建议学习主题"""
        weak_domains = self._identify_weak_domains(knowledge_domains)

        topic_mapping = {
            'python_basics': ['变量和数据类型', '控制流程', '函数基础'],
            'data_structures': ['列表和元组', '字典和集合', '数据结构应用'],
            'algorithms': ['排序算法', '查找算法', '递归概念'],
            'oop': ['类和对象', '继承和多态', '封装特性'],
            'functional': ['lambda表达式', '高阶函数', '装饰器']
        }

        suggested_topics = []
        for domain in weak_domains[:2]:
            # 将中文域名映射回英文key
            domain_key = self._map_domain_to_key(domain)
            suggested_topics.extend(topic_mapping.get(domain_key, []))

        return suggested_topics[:3]

    def _map_domain_to_key(self, domain: str) -> str:
        """将显示名称映射回领域key"""
        mapping = {
            'Python基础': 'python_basics',
            '数据结构': 'data_structures',
            '算法': 'algorithms',
            '面向对象': 'oop',
            '函数式编程': 'functional'
        }
        return mapping.get(domain, 'python_basics')

    def _recommend_strategy(self, level: float) -> str:
        """推荐学习策略"""
        if level < 0.4:
            return "foundation_focused"
        elif level < 0.7:
            return "balanced_approach"
        else:
            return "challenge_based"

    def _identify_weak_domains(self, knowledge_domains: Dict[str, float]) -> List[str]:
        """识别薄弱知识领域"""
        weak_threshold = 0.4
        weak_domains = []

        for domain, score in knowledge_domains.items():
            if score < weak_threshold:
                domain_name = self._get_domain_display_name(domain)
                weak_domains.append(domain_name)

        # 按掌握程度排序
        weak_domains.sort(key=lambda x: knowledge_domains.get(
            self._map_domain_to_key(x), 0.5
        ))
        return weak_domains

    def _get_domain_display_name(self, domain: str) -> str:
        """获取知识领域的显示名称"""
        domain_names = {
            'python_basics': 'Python基础',
            'data_structures': '数据结构',
            'algorithms': '算法',
            'oop': '面向对象',
            'functional': '函数式编程',
            'concurrency': '并发编程'
        }
        return domain_names.get(domain, domain)

    def _calculate_scientific_parameters(self,
                                         cognitive_state: Dict[str, Any],
                                         learning_context: str) -> Dict[str, Any]:
        """基于认知科学计算个性化参数"""
        overall_level = cognitive_state['overall_cognitive_level']
        learning_style = cognitive_state['learning_characteristics']['learning_style']
        confidence = cognitive_state['learning_characteristics']['confidence_level']

        parameters = {
            # 内容呈现参数
            'explanation_depth': self._calculate_explanation_depth(overall_level, learning_context),
            'example_complexity': self._calculate_example_complexity(overall_level, confidence),
            'conceptual_scaffolding': self._calculate_scaffolding(overall_level, learning_context),

            # 交互支持参数
            'hint_strategy': self._determine_hint_strategy(overall_level, confidence),
            'feedback_granularity': self._determine_feedback_granularity(overall_level),
            'error_correction_level': self._determine_error_correction(overall_level, confidence),

            # 学习路径参数
            'progression_pace': self._determine_progression_pace(overall_level, learning_style),
            'practice_intensity': self._determine_practice_intensity(overall_level),
            'review_frequency': self._determine_review_frequency(overall_level),

            # 认知挑战参数
            'cognitive_challenge_level': self._calculate_challenge_level(overall_level),
            'problem_solving_support': self._calculate_problem_solving_support(overall_level),
            'creativity_encouragement': self._calculate_creativity_encouragement(overall_level)
        }

        return parameters

    def _calculate_explanation_depth(self, level: float, context: str) -> float:
        """计算解释深度"""
        base_depth = 0.8 - (level * 0.4)  # 水平越高，解释越简洁

        # 根据学习上下文调整
        if context in ["new_concept", "difficult_topic"]:
            base_depth += 0.2
        elif context in ["review", "practice"]:
            base_depth -= 0.1

        return max(0.3, min(1.0, base_depth))

    def _calculate_example_complexity(self, level: float, confidence: float) -> float:
        """计算示例复杂度"""
        base_complexity = 0.3 + (level * 0.5)

        # 基于自信心调整
        if confidence > 0.7:
            base_complexity += 0.1
        elif confidence < 0.4:
            base_complexity -= 0.1

        return max(0.2, min(1.0, base_complexity))

    def _calculate_scaffolding(self, level: float, context: str) -> float:
        """计算脚手架支持"""
        if level < 0.4:
            scaffolding = 0.8
        elif level < 0.7:
            scaffolding = 0.5
        else:
            scaffolding = 0.3

        # 新概念需要更多支持
        if context == "new_concept":
            scaffolding = min(0.9, scaffolding + 0.2)

        return scaffolding

    def _determine_hint_strategy(self, level: float, confidence: float) -> str:
        """确定提示策略"""
        if level < 0.4 and confidence < 0.4:
            return "guided"  # 详细引导
        elif level < 0.7:
            return "balanced"  # 平衡提示
        else:
            return "minimal"  # 最少提示

    def _determine_feedback_granularity(self, level: float) -> str:
        """确定反馈粒度"""
        if level < 0.4:
            return "detailed"  # 详细反馈
        elif level < 0.7:
            return "focused"  # 重点反馈
        else:
            return "strategic"  # 策略性反馈

    def _determine_error_correction(self, level: float, confidence: float) -> str:
        """确定错误纠正程度"""
        if confidence < 0.4:
            return "immediate"  # 立即纠正
        elif level < 0.6:
            return "guided"  # 引导发现
        else:
            return "reflective"  # 反思性纠正

    def _determine_progression_pace(self, level: float, learning_style: str) -> str:
        """确定学习进度节奏"""
        if level < 0.4:
            return "slow"
        elif level < 0.7:
            if learning_style == "fast":
                return "moderate_fast"
            else:
                return "moderate"
        else:
            return "adaptive"

    def _determine_practice_intensity(self, level: float) -> float:
        """确定练习强度"""
        if level < 0.4:
            return 0.8  # 高强度练习
        elif level < 0.7:
            return 0.6  # 中等强度
        else:
            return 0.4  # 低强度，更多探索

    def _determine_review_frequency(self, level: float) -> str:
        """确定复习频率"""
        if level < 0.4:
            return "frequent"  # 频繁复习
        elif level < 0.7:
            return "regular"  # 规律复习
        else:
            return "as_needed"  # 按需复习

    def _calculate_challenge_level(self, level: float) -> float:
        """计算认知挑战水平"""
        return min(1.0, level + 0.2)  # 适度挑战

    def _calculate_problem_solving_support(self, level: float) -> float:
        """计算问题解决支持"""
        return max(0.2, 0.8 - (level * 0.6))

    def _calculate_creativity_encouragement(self, level: float) -> float:
        """计算创造力鼓励程度"""
        return min(1.0, level * 1.2)

    async def _generate_scientific_recommendations(self,
                                                   user_id: str,
                                                   analysis: InteractionAnalysis,
                                                   cognitive_state: Dict[str, Any]) -> Dict[str, Any]:
        """生成基于认知科学的推荐"""
        overall_level = cognitive_state['overall_cognitive_level']
        performance = analysis.performance_score

        recommendations = {
            'immediate_focus': self._determine_immediate_focus(analysis),
            'learning_strategy': self._recommend_learning_strategy(overall_level, performance),
            'cognitive_development_priority': self._identify_development_priority(cognitive_state),
            'practice_recommendations': self._suggest_practice_activities(analysis, cognitive_state),
            'meta_cognitive_guidance': self._provide_metacognitive_guidance(analysis)
        }

        return recommendations

    def _determine_immediate_focus(self, analysis: InteractionAnalysis) -> str:
        """确定即时学习重点"""
        if analysis.performance_score < 0.4:
            return "foundation_reinforcement"
        elif analysis.error_patterns:
            return "error_pattern_address"
        elif analysis.performance_score > 0.8:
            return "extension_challenge"
        else:
            return "consolidation_practice"

    def _recommend_learning_strategy(self, level: float, performance: float) -> str:
        """推荐学习策略"""
        if level < 0.4 and performance < 0.5:
            return "scaffolded_learning"
        elif level < 0.7 and performance > 0.7:
            return "problem_based_learning"
        elif performance < 0.5:
            return "mastery_learning"
        else:
            return "exploratory_learning"

    def _identify_development_priority(self, cognitive_state: Dict[str, Any]) -> str:
        """识别发展优先级"""
        dimensions = cognitive_state['cognitive_dimensions']

        # 找到最弱的认知维度
        weakest_dimension = min(dimensions.items(), key=lambda x: x[1])

        priority_map = {
            'remember': 'conceptual_understanding',
            'understand': 'knowledge_application',
            'apply': 'analytical_thinking',
            'analyze': 'evaluative_skills',
            'evaluate': 'creative_synthesis'
        }

        return priority_map.get(weakest_dimension[0], 'balanced_development')

    def _suggest_practice_activities(self,
                                     analysis: InteractionAnalysis,
                                     cognitive_state: Dict[str, Any]) -> List[str]:
        """建议练习活动"""
        activities = []

        # 基于知识组件
        for component in analysis.knowledge_components[:3]:
            activities.append(f"练习{component}相关题目")

        # 基于认知维度
        weak_dims = [dim for dim, score in cognitive_state['cognitive_dimensions'].items()
                     if score < 0.6]
        for dim in weak_dims[:2]:
            activities.append(f"加强{self._get_dimension_display_name(dim)}训练")

        return activities

    def _provide_metacognitive_guidance(self, analysis: InteractionAnalysis) -> List[str]:
        """提供元认知指导"""
        guidance = []

        if analysis.error_patterns:
            guidance.append("注意识别和纠正常见的错误模式")

        if analysis.performance_score > 0.8:
            guidance.append("尝试反思和总结成功的学习策略")
        else:
            guidance.append("练习前先制定解决计划，执行后进行评估")

        return guidance

    def _analyze_cognitive_progression(self, profile: UserCognitiveProfile) -> Dict[str, Any]:
        """分析认知发展进程"""
        if len(profile.cognitive_history) < 2:
            return {'trend': 'insufficient_data'}

        history = profile.cognitive_history

        # 计算发展趋势
        recent_scores = [snapshot.overall_level for snapshot in history[-5:]]
        earlier_scores = [snapshot.overall_level for snapshot in history[-10:-5]]

        if not earlier_scores:
            trend = 'establishing_baseline'
        else:
            avg_recent = sum(recent_scores) / len(recent_scores)
            avg_earlier = sum(earlier_scores) / len(earlier_scores)

            if avg_recent > avg_earlier + 0.1:
                trend = 'significant_improvement'
            elif avg_recent > avg_earlier + 0.05:
                trend = 'moderate_improvement'
            elif avg_recent < avg_earlier - 0.1:
                trend = 'regression'
            else:
                trend = 'stable'

        return {
            'trend': trend,
            'progress_rate': self._calculate_progress_rate(history),
            'learning_consistency': profile.consistency_score,
            'development_trajectory': self._assess_development_trajectory(history)
        }

    def _calculate_progress_rate(self, history: List[CognitiveSnapshot]) -> float:
        """计算进步速率"""
        if len(history) < 2:
            return 0.0

        time_span = (history[-1].timestamp - history[0].timestamp).days
        if time_span == 0:
            return 0.0

        level_change = history[-1].overall_level - history[0].overall_level
        return level_change / time_span

    def _assess_development_trajectory(self, history: List[CognitiveSnapshot]) -> str:
        """评估发展轨迹"""
        if len(history) < 3:
            return 'initial_phase'

        levels = [snapshot.overall_level for snapshot in history]

        # 简单趋势分析
        if all(levels[i] <= levels[i + 1] for i in range(len(levels) - 1)):
            return 'steady_growth'
        elif levels[-1] > levels[0] + 0.2:
            return 'accelerated_growth'
        elif any(levels[i] > levels[i + 1] for i in range(len(levels) - 1)):
            return 'fluctuating_progress'
        else:
            return 'plateau'

    def _extract_learning_trajectory(self, profile: UserCognitiveProfile) -> List[Dict[str, Any]]:
        """提取学习轨迹"""
        trajectory = []

        for snapshot in profile.cognitive_history:
            trajectory.append({
                'timestamp': snapshot.timestamp.isoformat(),
                'overall_level': snapshot.overall_level,
                'key_strengths': self._extract_key_strengths(snapshot),
                'development_focus': self._identify_development_focus(snapshot)
            })

        return trajectory

    def _extract_key_strengths(self, snapshot: CognitiveSnapshot) -> List[str]:
        """提取关键强项"""
        strengths = []
        for dim, score in snapshot.dimension_scores.items():
            if score > 0.7:
                strengths.append(self._get_dimension_display_name(dim.value))
        return strengths[:3]

    def _identify_development_focus(self, snapshot: CognitiveSnapshot) -> str:
        """识别发展重点"""
        weak_dims = [(dim, score) for dim, score in snapshot.dimension_scores.items()
                     if score < 0.6]
        if not weak_dims:
            return 'advanced_application'

        weakest = min(weak_dims, key=lambda x: x[1])
        return f"develop_{weakest[0].value}"

    def _identify_cognitive_strengths(self, cognitive_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别认知强项"""
        strengths = []
        dimensions = cognitive_state['cognitive_dimensions']

        for dim, score in dimensions.items():
            if score > 0.7:
                strengths.append({
                    'dimension': dim,
                    'display_name': self._get_dimension_display_name(dim),
                    'strength_level': score,
                    'description': self._get_strength_description(dim, score)
                })

        return sorted(strengths, key=lambda x: x['strength_level'], reverse=True)[:3]

    def _identify_cognitive_weaknesses(self, cognitive_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别认知弱项"""
        weaknesses = []
        dimensions = cognitive_state['cognitive_dimensions']

        for dim, score in dimensions.items():
            if score < 0.5:
                weaknesses.append({
                    'dimension': dim,
                    'display_name': self._get_dimension_display_name(dim),
                    'weakness_level': score,
                    'improvement_priority': self._get_improvement_priority(score),
                    'suggested_activities': self._get_improvement_activities(dim)
                })

        return sorted(weaknesses, key=lambda x: x['weakness_level'])[:3]

    def _prioritize_development_areas(self, strengths: List[Dict], weaknesses: List[Dict]) -> List[str]:
        """优先发展领域"""
        priorities = []

        # 先解决严重弱项
        for weakness in weaknesses:
            if weakness['weakness_level'] < 0.4:
                priorities.append(f"紧急提升{weakness['display_name']}")

        # 然后平衡发展
        if len(strengths) > len(weaknesses) + 2:
            priorities.append("加强相对薄弱领域的发展")
        else:
            priorities.append("全面发展各认知维度")

        return priorities

    def _assess_cognitive_balance(self, cognitive_state: Dict[str, Any]) -> Dict[str, Any]:
        """评估认知平衡性"""
        dimensions = cognitive_state['cognitive_dimensions']
        scores = list(dimensions.values())

        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)

        balance_level = 1.0 / (1.0 + variance * 10)  # 方差越小，平衡性越高

        if balance_level > 0.8:
            balance_status = "well_balanced"
        elif balance_level > 0.6:
            balance_status = "moderately_balanced"
        else:
            balance_status = "needs_balancing"

        return {
            'balance_level': balance_level,
            'balance_status': balance_status,
            'most_developed': max(dimensions.items(), key=lambda x: x[1])[0],
            'least_developed': min(dimensions.items(), key=lambda x: x[1])[0]
        }

    def _get_dimension_display_name(self, dimension: str) -> str:
        """获取维度显示名称"""
        names = {
            'remember': '记忆能力',
            'understand': '理解能力',
            'apply': '应用能力',
            'analyze': '分析能力',
            'evaluate': '评价能力',
            'create': '创造能力'
        }
        return names.get(dimension, dimension)

    def _get_strength_description(self, dimension: str, score: float) -> str:
        """获取强项描述"""
        descriptions = {
            'remember': '能够有效回忆和识别编程概念和语法',
            'understand': '能够深入理解编程原理和概念关系',
            'apply': '能够熟练应用知识解决实际问题',
            'analyze': '能够分析代码结构和问题模式',
            'evaluate': '能够基于标准评价代码质量和解决方案',
            'create': '能够创造性地设计和实现新解决方案'
        }
        base_desc = descriptions.get(dimension, '认知能力突出')

        if score > 0.8:
            return f"非常强的{base_desc}"
        else:
            return base_desc

    def _get_improvement_priority(self, score: float) -> str:
        """获取改进优先级"""
        if score < 0.3:
            return "high"
        elif score < 0.5:
            return "medium"
        else:
            return "low"

    def _get_improvement_activities(self, dimension: str) -> List[str]:
        """获取改进活动建议"""
        activities_map = {
            'remember': ['概念记忆练习', '语法快速回忆', '知识点复述'],
            'understand': ['概念解释练习', '原理分析任务', '关系理解训练'],
            'apply': ['实际编程练习', '项目应用任务', '场景模拟训练'],
            'analyze': ['代码分析任务', '问题分解练习', '模式识别训练'],
            'evaluate': ['代码评审练习', '方案评估任务', '质量标准理解'],
            'create': ['创新设计任务', '项目构建练习', '解决方案设计']
        }
        return activities_map.get(dimension, ['综合能力训练'])

    async def _record_learning_session(self,
                                       user_id: str,
                                       interaction_data: Dict[str, Any],
                                       analysis: InteractionAnalysis):
        """记录学习会话"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'total_sessions': 0,
                'session_history': [],
                'learning_patterns': {}
            }

        session_record = {
            'timestamp': datetime.now().isoformat(),
            'interaction_type': interaction_data.get('type'),
            'content_topic': self._extract_content_topic(interaction_data),
            'performance_score': analysis.performance_score,
            'cognitive_level': analysis.required_cognitive_level,
            'analysis_confidence': analysis.analysis_confidence,
            'key_insights': analysis.llm_cognitive_analysis.get('cognitive_insights', {})
        }

        self.user_sessions[user_id]['session_history'].append(session_record)
        self.user_sessions[user_id]['total_sessions'] += 1

        # 保持最近50次会话
        if len(self.user_sessions[user_id]['session_history']) > 50:
            self.user_sessions[user_id]['session_history'] = \
                self.user_sessions[user_id]['session_history'][-50:]

    def _extract_content_topic(self, interaction_data: Dict[str, Any]) -> str:
        """提取内容主题"""
        content = interaction_data.get('content', '').lower()

        topic_keywords = {
            'python_basics': ['变量', '函数', '类', '语法', '基础'],
            'data_structures': ['列表', '字典', '元组', '集合', '数据结构'],
            'algorithms': ['算法', '排序', '查找', '递归', '复杂度'],
            'oop': ['面向对象', '继承', '多态', '封装', '类'],
            'web_development': ['网页', '网站', 'flask', 'django', '前端']
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                return topic

        return 'general_programming'


# 全局API实例
_scientific_cognitive_api = None


async def get_scientific_cognitive_api() -> ScientificCognitiveAPI:
    """获取科学认知API实例"""
    global _scientific_cognitive_api
    if _scientific_cognitive_api is None:
        _scientific_cognitive_api = ScientificCognitiveAPI()
    return _scientific_cognitive_api


def get_scientific_cognitive_api_sync() -> ScientificCognitiveAPI:
    """获取科学认知API实例（同步版本）"""
    global _scientific_cognitive_api
    if _scientific_cognitive_api is None:
        _scientific_cognitive_api = ScientificCognitiveAPI()
    return _scientific_cognitive_api