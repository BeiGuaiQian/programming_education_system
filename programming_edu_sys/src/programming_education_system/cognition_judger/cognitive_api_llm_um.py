# src/programming_education_system/cognition_judger/cognitive_api_llm_um.py
"""
基于LLM-UM框架的认知评估API
替换原有的认知评估API，使用LLM-UM框架
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 导入LLM-UM框架
from programming_education_system.llm_um_framework import (
    LLMUMFramework, UserCognitiveProfile, InteractionAnalysis
)


class MockLLMClient:
    """模拟LLM客户端 - 用于测试"""
    
    async def generate_response(self, system_prompt: str, user_message: str) -> str:
        """模拟LLM响应生成"""
        # 模拟处理时间
        await asyncio.sleep(0.1)
        
        # 基于用户消息内容生成模拟响应
        if "认知分析" in user_message:
            return """
{
    "cognitive_demand": {
        "remember": 0.3,
        "understand": 0.7,
        "apply": 0.6,
        "analyze": 0.4,
        "evaluate": 0.2,
        "create": 0.1
    },
    "knowledge_components": ["python_basics", "function_definition"],
    "performance_indicators": {
        "correctness": 0.8,
        "efficiency": 0.6,
        "completeness": 0.9
    },
    "learning_insights": {
        "learning_style": "conceptual",
        "confidence_level": 0.7
    },
    "inferred_state": {
        "engagement": 0.8,
        "confusion": 0.2,
        "level": 0.65
    }
}
"""
        elif "用户认知建模" in user_message:
            return """
{
    "overall_cognitive_level": 0.65,
    "cognitive_dimensions": {
        "remember": 0.7,
        "understand": 0.8,
        "apply": 0.6,
        "analyze": 0.5,
        "evaluate": 0.4,
        "create": 0.3
    },
    "knowledge_domains": {
        "python_basics": 0.8,
        "data_structures": 0.6,
        "algorithms": 0.4,
        "oop": 0.5,
        "functional": 0.3
    },
    "learning_characteristics": {
        "learning_style": "conceptual",
        "pace": "moderate",
        "preferred_difficulty": "medium"
    },
    "personalization_params": {
        "explanation_depth": 0.7,
        "practice_intensity": 0.6,
        "hint_frequency": 0.4
    },
    "confidence": 0.8,
    "data_points": 5
}
"""
        else:
            return """
{
    "update_strategy": "minor_update",
    "reason": "用户表现稳定，小幅调整认知模型"
}
"""


class CognitiveAPILLMUM:
    """
    基于LLM-UM框架的认知评估API
    替换原有的认知评估API
    """
    
    def __init__(self):
        self.logger = logging.getLogger("CognitiveAPI-LLMUM")
        self.llm_client = MockLLMClient()
        self.llm_um_framework = LLMUMFramework(self.llm_client)
        self.logger.info("LLM-UM认知评估API初始化完成")
    
    async def record_interaction(self, user_id: str, interaction_type: str, 
                               interaction_data: Dict[str, Any]) -> bool:
        """
        记录用户交互数据 - 使用LLM-UM框架处理
        """
        try:
            # 构建LLM-UM框架需要的交互数据格式
            llm_um_interaction_data = {
                'type': interaction_type,
                'content': '',  # 内容在process_interaction中会用到
                'response': '',
                'processing_time': interaction_data.get('processing_time', 0),
                'correctness': interaction_data.get('correctness', 0.5),
                'complexity': interaction_data.get('complexity', 0.5),
                'domain': interaction_data.get('domain', 'syntax'),
                'cognitive_level': interaction_data.get('cognitive_level', 'understand')
            }
            
            # 使用LLM-UM框架处理交互
            analysis = await self.llm_um_framework.process_interaction(
                user_id, llm_um_interaction_data
            )
            
            self.logger.info(f"LLM-UM交互记录成功 - 用户: {user_id}, 分析ID: {analysis.interaction_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"记录交互数据失败: {e}")
            return False
    
    async def get_cognitive_level(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户认知水平 - 使用LLM-UM框架
        """
        try:
            profile = await self.llm_um_framework.get_user_profile(user_id)
            
            if profile:
                return {
                    'overall_level': profile.overall_cognitive_level,
                    'cognitive_levels': {
                        dim.value: score 
                        for dim, score in profile.cognitive_dimensions.items()
                    },
                    'knowledge_domains': profile.knowledge_domains,
                    'confidence': profile.confidence,
                    'data_points': profile.data_points,
                    'timestamp': profile.timestamp.isoformat()
                }
            else:
                # 返回默认认知水平
                return {
                    'overall_level': 0.5,
                    'cognitive_levels': {
                        'remember': 0.5,
                        'understand': 0.5,
                        'apply': 0.5,
                        'analyze': 0.5,
                        'evaluate': 0.5,
                        'create': 0.5
                    },
                    'knowledge_domains': {
                        'python_basics': 0.5,
                        'data_structures': 0.5,
                        'algorithms': 0.5,
                        'oop': 0.5,
                        'functional': 0.5
                    },
                    'confidence': 0.1,
                    'data_points': 0,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"获取认知水平失败: {e}")
            return {
                'overall_level': 0.5,
                'cognitive_levels': {},
                'knowledge_domains': {},
                'confidence': 0.0,
                'data_points': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_personalization_recommendations(self, user_id: str, 
                                                request_type: str) -> Dict[str, Any]:
        """
        获取个性化推荐 - 使用LLM-UM框架
        """
        try:
            profile = await self.llm_um_framework.get_user_profile(user_id)
            learning_chars = await self.llm_um_framework.get_learning_characteristics(user_id)
            
            if profile:
                # 基于认知水平和学习特征生成推荐
                level = profile.overall_cognitive_level
                
                if level < 0.3:
                    difficulty = "beginner"
                    next_topics = ["变量", "数据类型", "基本语法"]
                elif level < 0.6:
                    difficulty = "intermediate" 
                    next_topics = ["函数", "控制流", "数据结构"]
                else:
                    difficulty = "advanced"
                    next_topics = ["面向对象", "算法", "设计模式"]
                
                # 基于请求类型调整推荐
                if request_type == "exercise":
                    strategy = "practice_focused"
                elif request_type == "qa":
                    strategy = "concept_explanation"
                else:
                    strategy = "balanced"
                
                return {
                    'difficulty_level': difficulty,
                    'next_topics': next_topics,
                    'learning_strategy': strategy,
                    'pace_recommendation': learning_chars.get('pace', 'moderate'),
                    'confidence': profile.confidence
                }
            else:
                return {
                    'difficulty_level': 'beginner',
                    'next_topics': ['Python基础'],
                    'learning_strategy': 'balanced',
                    'pace_recommendation': 'moderate',
                    'confidence': 0.1
                }
                
        except Exception as e:
            self.logger.error(f"获取个性化推荐失败: {e}")
            return {
                'difficulty_level': 'beginner',
                'next_topics': ['Python基础'],
                'learning_strategy': 'balanced',
                'pace_recommendation': 'moderate',
                'confidence': 0.0
            }
    
    async def get_adaptive_content_parameters(self, user_id: str) -> Dict[str, Any]:
        """
        获取自适应内容参数 - 使用LLM-UM框架
        """
        try:
            personalization_params = await self.llm_um_framework.get_personalization_params(user_id)
            profile = await self.llm_um_framework.get_user_profile(user_id)
            
            # 使用LLM-UM框架的参数，如果不存在则使用默认值
            base_params = {
                'explanation_depth': 0.7,
                'example_complexity': 0.5,
                'hint_frequency': 0.5,
                'practice_intensity': 0.6,
                'feedback_detail': 0.8
            }
            
            # 更新为LLM-UM框架计算出的参数
            base_params.update(personalization_params)
            
            # 基于认知水平微调参数
            if profile:
                level = profile.overall_cognitive_level
                if level > 0.7:
                    base_params['explanation_depth'] = 0.9  # 高级用户需要更深入解释
                    base_params['hint_frequency'] = 0.2     # 减少提示
                elif level < 0.3:
                    base_params['explanation_depth'] = 0.9  # 新手也需要详细解释
                    base_params['hint_frequency'] = 0.8     # 更多提示
            
            return base_params
            
        except Exception as e:
            self.logger.error(f"获取自适应参数失败: {e}")
            return {
                'explanation_depth': 0.7,
                'example_complexity': 0.5,
                'hint_frequency': 0.5,
                'practice_intensity': 0.6,
                'feedback_detail': 0.8
            }


# 全局实例
_cognitive_api_instance = None


def get_cognition_api():
    """获取认知评估API实例（单例模式）"""
    global _cognitive_api_instance
    if _cognitive_api_instance is None:
        _cognitive_api_instance = CognitiveAPILLMUM()
    return _cognitive_api_instance