# programming_education_system/llm_um_framework.py
"""
LLM-UM框架实现 - 基于大模型的用户认知建模
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class LLMUMRole(Enum):
    """LLM-UM角色定义"""
    PREDICTOR = "predictor"      # 预测用户特征
    ENHANCER = "enhancer"        # 增强用户数据
    CONTROLLER = "controller"    # 控制建模流程

class CognitiveDimension(Enum):
    """认知维度 - 基于Bloom分类学"""
    REMEMBER = "remember"
    UNDERSTAND = "understand" 
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"

@dataclass
class UserCognitiveProfile:
    """用户认知档案"""
    user_id: str
    timestamp: datetime
    overall_cognitive_level: float  # 总体认知水平 0-1
    
    # 认知维度得分
    cognitive_dimensions: Dict[CognitiveDimension, float]
    
    # 知识领域掌握度
    knowledge_domains: Dict[str, float]  # {domain: mastery_level}
    
    # 学习特征
    learning_characteristics: Dict[str, Any]
    
    # 个性化参数
    personalization_params: Dict[str, Any]
    
    # 元数据
    confidence: float  # 评估置信度
    data_points: int   # 基于的数据点数量
    version: str       # 模型版本

@dataclass
class InteractionAnalysis:
    """单次交互分析结果"""
    interaction_id: str
    user_id: str
    timestamp: datetime
    interaction_type: str
    
    # 分析结果
    cognitive_demand: float  # 认知需求 0-1
    knowledge_components: List[str]  # 涉及的知识组件
    performance_indicators: Dict[str, float]  # 表现指标
    inferred_state: Dict[str, Any]  # 推断的认知状态
    
    # LLM分析
    llm_analysis: Dict[str, Any]  # 原始LLM分析结果

class LLMUMFramework:
    """
    LLM-UM框架主类
    利用大模型构建和更新用户认知模型
    """
    
    def __init__(self, llm_client, storage_backend=None):
        self.llm = llm_client
        self.storage = storage_backend
        self.logger = logging.getLogger("LLM-UM")
        
        # 用户档案缓存
        self.user_profiles: Dict[str, UserCognitiveProfile] = {}
        
        # 分析历史
        self.analysis_history: Dict[str, List[InteractionAnalysis]] = {}
        
        # 初始化提示模板
        self.prompt_templates = self._init_prompt_templates()
    
    def _init_prompt_templates(self) -> Dict[str, str]:
        """初始化提示模板"""
        return {
            "enhancer_analysis": """
你是一个专业的编程教育认知分析专家。请分析以下用户交互数据，提取认知特征：

交互信息：
- 类型: {interaction_type}
- 内容: {content}
- 响应: {response}
- 处理时间: {processing_time}
- 正确性: {correctness}
- 复杂度: {complexity}

请从以下维度进行分析：
1. 认知需求：这次交互需要哪些认知能力？（记忆、理解、应用、分析、评价、创造）
2. 知识组件：涉及哪些具体的编程知识点？
3. 表现评估：用户的表现如何？有哪些优点和不足？
4. 学习特征：反映出什么学习特点？

请以JSON格式输出分析结果，包含以下字段：
- cognitive_demand: 各认知维度的需求强度(0-1)
- knowledge_components: 涉及的知识点列表
- performance_indicators: 表现指标
- learning_insights: 学习特征洞察
- inferred_state: 推断的认知状态
""",
            "predictor_profile": """
你是一个用户认知建模专家。基于以下交互分析历史，预测用户的认知档案：

用户交互分析历史：
{analysis_history}

请综合评估用户的：
1. 总体认知水平(0-1)
2. 各认知维度的能力得分
3. 各知识领域的掌握程度
4. 学习特征和模式
5. 个性化学习参数建议

请以JSON格式输出完整的用户认知档案。
""",
            "controller_decision": """
作为用户建模控制器，请决定如何处理新的交互数据：

当前用户档案：
{current_profile}

新交互分析：
{new_analysis}

更新策略选项：
1. 轻微更新：用户状态稳定，小幅调整
2. 中度更新：有明显变化，需要调整
3. 重大更新：状态显著改变，重新评估
4. 保持现状：数据不足或噪声

请选择更新策略并说明理由。
"""
        }
    
    async def process_interaction(self, 
                                user_id: str,
                                interaction_data: Dict[str, Any]) -> InteractionAnalysis:
        """
        处理单次交互 - Enhancer角色
        从原始交互数据中提取认知特征
        """
        self.logger.info(f"处理用户交互 - 用户: {user_id}")
        
        try:
            # 1. 使用LLM进行深度分析
            llm_analysis = await self._enhancer_analysis(interaction_data)
            
            # 2. 构建交互分析对象
            analysis = InteractionAnalysis(
                interaction_id=f"{user_id}_{datetime.now().timestamp()}",
                user_id=user_id,
                timestamp=datetime.now(),
                interaction_type=interaction_data.get('type', 'unknown'),
                cognitive_demand=llm_analysis.get('cognitive_demand', {}),
                knowledge_components=llm_analysis.get('knowledge_components', []),
                performance_indicators=llm_analysis.get('performance_indicators', {}),
                inferred_state=llm_analysis.get('inferred_state', {}),
                llm_analysis=llm_analysis
            )
            
            # 3. 存储分析结果
            await self._store_analysis(analysis)
            
            # 4. 更新用户档案
            await self._update_user_profile(user_id, analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"交互处理失败: {e}")
            raise
    
    async def _enhancer_analysis(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhancer角色：使用LLM进行深度分析"""
        prompt = self.prompt_templates["enhancer_analysis"].format(
            interaction_type=interaction_data.get('type', 'unknown'),
            content=interaction_data.get('content', '')[:500],  # 限制长度
            response=interaction_data.get('response', '')[:500],
            processing_time=interaction_data.get('processing_time', 0),
            correctness=interaction_data.get('correctness', 0.5),
            complexity=interaction_data.get('complexity', 0.5)
        )
        
        response = await self.llm.generate_response(
            system_prompt="你是一个专业的编程教育认知分析专家",
            user_message=prompt
        )
        
        return self._parse_llm_response(response)
    
    async def _update_user_profile(self, user_id: str, new_analysis: InteractionAnalysis):
        """Controller角色：协调用户档案更新"""
        current_profile = self.user_profiles.get(user_id)
        
        # 决定更新策略
        update_strategy = await self._controller_decision(current_profile, new_analysis)
        
        # 执行更新
        if update_strategy == "major_update" or not current_profile:
            # 重大更新或初次创建
            new_profile = await self._predictor_generate_profile(user_id)
        else:
            # 渐进更新
            new_profile = await self._predictor_update_profile(current_profile, new_analysis)
        
        # 存储更新后的档案
        self.user_profiles[user_id] = new_profile
        await self._store_user_profile(new_profile)
    
    async def _controller_decision(self, 
                                 current_profile: Optional[UserCognitiveProfile],
                                 new_analysis: InteractionAnalysis) -> str:
        """Controller角色：决定更新策略"""
        if not current_profile:
            return "major_update"  # 初次创建
        
        prompt = self.prompt_templates["controller_decision"].format(
            current_profile=self._profile_to_text(current_profile),
            new_analysis=self._analysis_to_text(new_analysis)
        )
        
        response = await self.llm.generate_response(
            system_prompt="你是用户认知建模的决策控制器",
            user_message=prompt
        )
        
        # 解析决策结果
        if "重大更新" in response:
            return "major_update"
        elif "中度更新" in response:
            return "moderate_update" 
        elif "轻微更新" in response:
            return "minor_update"
        else:
            return "maintain"
    
    async def _predictor_generate_profile(self, user_id: str) -> UserCognitiveProfile:
        """Predictor角色：生成完整的用户档案"""
        analysis_history = self.analysis_history.get(user_id, [])
        
        if not analysis_history:
            return self._create_default_profile(user_id)
        
        prompt = self.prompt_templates["predictor_profile"].format(
            analysis_history=self._analysis_history_to_text(analysis_history)
        )
        
        response = await self.llm.generate_response(
            system_prompt="你是用户认知建模的预测专家",
            user_message=prompt
        )
        
        profile_data = self._parse_llm_response(response)
        return self._create_profile_from_data(user_id, profile_data)
    
    async def _predictor_update_profile(self, 
                                      current_profile: UserCognitiveProfile,
                                      new_analysis: InteractionAnalysis) -> UserCognitiveProfile:
        """Predictor角色：渐进更新用户档案"""
        # 基于新分析结果更新现有档案
        updated_data = {
            "overall_cognitive_level": self._update_level(
                current_profile.overall_cognitive_level,
                new_analysis.inferred_state.get('level', 0.5)
            ),
            "cognitive_dimensions": self._update_dimensions(
                current_profile.cognitive_dimensions,
                new_analysis.cognitive_demand
            ),
            "knowledge_domains": self._update_domains(
                current_profile.knowledge_domains,
                new_analysis.knowledge_components
            ),
            "learning_characteristics": self._update_learning_chars(
                current_profile.learning_characteristics,
                new_analysis.llm_analysis.get('learning_insights', {})
            )
        }
        
        return self._create_profile_from_data(current_profile.user_id, updated_data)
    
    def _update_level(self, current: float, new: float) -> float:
        """更新认知水平"""
        alpha = 0.3  # 学习率
        return (1 - alpha) * current + alpha * new
    
    def _update_dimensions(self, 
                          current: Dict[CognitiveDimension, float],
                          new_demand: Dict[str, float]) -> Dict[CognitiveDimension, float]:
        """更新认知维度"""
        updated = current.copy()
        
        for dim_str, demand in new_demand.items():
            try:
                dimension = CognitiveDimension(dim_str)
                current_score = current.get(dimension, 0.5)
                # 认知需求高的维度，如果表现好则加分
                updated[dimension] = min(1.0, current_score + demand * 0.1)
            except ValueError:
                continue
        
        return updated
    
    def _update_domains(self,
                       current: Dict[str, float],
                       new_components: List[str]) -> Dict[str, float]:
        """更新知识领域"""
        updated = current.copy()
        
        for component in new_components:
            domain = self._map_component_to_domain(component)
            if domain:
                current_score = current.get(domain, 0.5)
                # 每次涉及该领域就小幅提升（假设表现良好）
                updated[domain] = min(1.0, current_score + 0.05)
        
        return updated
    
    def _map_component_to_domain(self, component: str) -> Optional[str]:
        """将知识组件映射到领域"""
        domain_mapping = {
            # Python基础
            "变量": "python_basics", "函数": "python_basics", "类": "python_basics",
            "数据类型": "python_basics", "控制流": "python_basics",
            
            # 数据结构
            "列表": "data_structures", "字典": "data_structures", "集合": "data_structures",
            "元组": "data_structures", "数组": "data_structures",
            
            # 算法
            "排序": "algorithms", "查找": "algorithms", "递归": "algorithms",
            "复杂度": "algorithms", "算法": "algorithms",
            
            # OOP
            "面向对象": "oop", "继承": "oop", "多态": "oop", "封装": "oop",
            
            # 函数式编程
            "lambda": "functional", "高阶函数": "functional", "装饰器": "functional"
        }
        
        for key, domain in domain_mapping.items():
            if key in component:
                return domain
        
        return None
    
    def _update_learning_chars(self,
                             current: Dict[str, Any],
                             new_insights: Dict[str, Any]) -> Dict[str, Any]:
        """更新学习特征"""
        updated = current.copy()
        updated.update(new_insights)
        return updated
    
    def _create_default_profile(self, user_id: str) -> UserCognitiveProfile:
        """创建默认用户档案"""
        return UserCognitiveProfile(
            user_id=user_id,
            timestamp=datetime.now(),
            overall_cognitive_level=0.5,
            cognitive_dimensions={dim: 0.5 for dim in CognitiveDimension},
            knowledge_domains={
                "python_basics": 0.5,
                "data_structures": 0.5,
                "algorithms": 0.5,
                "oop": 0.5,
                "functional": 0.5
            },
            learning_characteristics={
                "learning_style": "unknown",
                "pace": "moderate",
                "preferred_difficulty": "medium"
            },
            personalization_params={
                "explanation_depth": 0.7,
                "example_complexity": 0.5,
                "hint_frequency": 0.5
            },
            confidence=0.1,
            data_points=0,
            version="1.0"
        )
    
    def _create_profile_from_data(self, user_id: str, data: Dict[str, Any]) -> UserCognitiveProfile:
        """从数据创建用户档案"""
        return UserCognitiveProfile(
            user_id=user_id,
            timestamp=datetime.now(),
            overall_cognitive_level=data.get('overall_cognitive_level', 0.5),
            cognitive_dimensions=self._parse_cognitive_dimensions(
                data.get('cognitive_dimensions', {})
            ),
            knowledge_domains=data.get('knowledge_domains', {}),
            learning_characteristics=data.get('learning_characteristics', {}),
            personalization_params=data.get('personalization_params', {}),
            confidence=data.get('confidence', 0.5),
            data_points=data.get('data_points', 1),
            version="1.0"
        )
    
    def _parse_cognitive_dimensions(self, dim_data: Dict) -> Dict[CognitiveDimension, float]:
        """解析认知维度数据"""
        dimensions = {}
        for dim_str, score in dim_data.items():
            try:
                dimension = CognitiveDimension(dim_str)
                dimensions[dimension] = min(1.0, max(0.0, float(score)))
            except (ValueError, TypeError):
                continue
        
        # 确保所有维度都有值
        for dim in CognitiveDimension:
            if dim not in dimensions:
                dimensions[dim] = 0.5
        
        return dimensions
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str, strict=False)
        except Exception as e:
            self.logger.warning(f"LLM响应解析失败: {e}")
        
        return {}
    
    def _profile_to_text(self, profile: UserCognitiveProfile) -> str:
        """将用户档案转换为文本"""
        return f"""
总体认知水平: {profile.overall_cognitive_level:.3f}
认知维度: {profile.cognitive_dimensions}
知识领域: {profile.knowledge_domains}
学习特征: {profile.learning_characteristics}
置信度: {profile.confidence:.3f}
"""
    
    def _analysis_to_text(self, analysis: InteractionAnalysis) -> str:
        """将交互分析转换为文本"""
        return f"""
交互类型: {analysis.interaction_type}
认知需求: {analysis.cognitive_demand}
知识组件: {analysis.knowledge_components}
表现指标: {analysis.performance_indicators}
推断状态: {analysis.inferred_state}
"""
    
    def _analysis_history_to_text(self, history: List[InteractionAnalysis]) -> str:
        """将分析历史转换为文本"""
        texts = []
        for i, analysis in enumerate(history[-10:]):  # 最近10次
            texts.append(f"交互{i+1}: {self._analysis_to_text(analysis)}")
        return "\n".join(texts)
    
    async def _store_analysis(self, analysis: InteractionAnalysis):
        """存储交互分析"""
        if self.storage:
            await self.storage.store_analysis(analysis)
        else:
            # 内存存储
            if analysis.user_id not in self.analysis_history:
                self.analysis_history[analysis.user_id] = []
            self.analysis_history[analysis.user_id].append(analysis)
    
    async def _store_user_profile(self, profile: UserCognitiveProfile):
        """存储用户档案"""
        if self.storage:
            await self.storage.store_profile(profile)
        else:
            self.user_profiles[profile.user_id] = profile
    
    # 公共API方法
    async def get_user_profile(self, user_id: str) -> Optional[UserCognitiveProfile]:
        """获取用户认知档案"""
        return self.user_profiles.get(user_id)
    
    async def get_user_cognitive_level(self, user_id: str) -> float:
        """获取用户认知水平"""
        profile = await self.get_user_profile(user_id)
        return profile.overall_cognitive_level if profile else 0.5
    
    async def get_personalization_params(self, user_id: str) -> Dict[str, Any]:
        """获取个性化参数"""
        profile = await self.get_user_profile(user_id)
        return profile.personalization_params if profile else {}
    
    async def get_learning_characteristics(self, user_id: str) -> Dict[str, Any]:
        """获取学习特征"""
        profile = await self.get_user_profile(user_id)
        return profile.learning_characteristics if profile else {}