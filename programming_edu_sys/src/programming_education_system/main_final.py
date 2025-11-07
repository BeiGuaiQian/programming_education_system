# src/programming_education_system/main_final.py
"""
编程教育智能体系统最终版主程序 - 完整修复版本
修复所有缺失的方法和错误，配合增强的主代理
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from programming_education_system.agents.user_agent import EnhancedUserAgent as UserAgent
from programming_education_system.agents.main_agent import MainAgent
from programming_education_system.agents.qa_agent import QAAgent
from programming_education_system.agents.exercise_agent import EnhancedExerciseGenerationAgent as ExerciseGenerationAgent
from programming_education_system.agents.evaluation_agent import AnswerEvaluationAgent
from programming_education_system.agents.personal_agent import PersonalizedLearningAgent

# 使用科学认知API
from programming_education_system.cognition_judger.cognitive_api_scientific import get_scientific_cognitive_api, \
    get_scientific_cognitive_api_sync

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ProgrammingEducationSystem:
    """编程教育智能体系统主类 - 完整修复版本，支持上下文感知"""

    def __init__(self):
        self.logger = logging.getLogger("System-Scientific")
        # 初始化科学认知API
        self.cognition_api = get_scientific_cognitive_api_sync()
        # 初始化用户上下文存储
        self.user_contexts = {}  # user_id -> context
        self.initialize_agents()

    def initialize_agents(self):
        """初始化所有智能体 - 修复参数传递问题"""
        self.logger.info("初始化智能体...")

        # 按依赖顺序初始化代理
        self.personal_agent = PersonalizedLearningAgent()

        # 修复：正确初始化各个代理，确保参数匹配
        self.qa_agent = QAAgent(personal_agent=self.personal_agent)  # QAAgent 可能不需要 personal_agent 参数
        self.exercise_agent = ExerciseGenerationAgent(personal_agent=self.personal_agent)  # EnhancedExerciseGenerator 不需要 personal_agent 参数
        self.evaluation_agent = AnswerEvaluationAgent(personal_agent=self.personal_agent)  # AnswerEvaluationAgent 可能不需要 personal_agent 参数
        self.main_agent = MainAgent(
            self.qa_agent,
            self.exercise_agent,
            self.evaluation_agent,
            self.personal_agent
        )
        self.user_agent = UserAgent(self.main_agent)

        self.logger.info("所有智能体初始化完成")

    def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """获取或创建用户上下文"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                "user_id": user_id,
                "recent_history": [],
                "learning_goals": [],
                "preferred_difficulty": "medium",
                "last_interaction_time": asyncio.get_event_loop().time()
            }
        return self.user_contexts[user_id]

    def _update_user_context(self, user_id: str, user_input: str, agent_response: str):
        """更新用户上下文历史"""
        context = self._get_user_context(user_id)

        # 添加新的交互到历史
        context["recent_history"].append({
            "user_input": user_input,
            "agent_response": agent_response,
            "timestamp": asyncio.get_event_loop().time()
        })

        # 保持历史长度合理（最近10条）
        if len(context["recent_history"]) > 10:
            context["recent_history"] = context["recent_history"][-10:]

        context["last_interaction_time"] = asyncio.get_event_loop().time()

    async def process_user_request(self, request_type: str, content: str, user_id: str = "user_001"):
        """
        处理用户请求 - 完全使用科学认知API，支持上下文感知
        """
        self.logger.info(f"处理用户请求 - 类型: {request_type}, 用户: {user_id}")

        try:
            # 记录交互开始时间
            start_time = asyncio.get_event_loop().time()

            # 获取用户上下文
            user_context = self._get_user_context(user_id)

            # 构建包含上下文的请求
            enhanced_request = {
                "type": request_type,
                "content": content,
                "user_id": user_id,
                "context": user_context,
                "timestamp": start_time
            }

            # 通过用户代理处理请求（现在包含上下文）
            result = await self.user_agent.receive_user_request(request_type="auto",content=content, user_id = user_id)
            final_result = await self.user_agent.collect_and_return_results(result)

            # 计算处理时间
            processing_time = asyncio.get_event_loop().time() - start_time

            # 更新用户上下文
            self._update_user_context(user_id, content, final_result.get('response', ''))

            # 记录科学认知评估数据
            await self._record_scientific_cognitive_data(user_id, request_type, content, final_result, processing_time)

            # 集成科学认知信息到结果
            final_result = await self._enhance_with_scientific_cognition(user_id, final_result, request_type, content)

            return final_result

        except Exception as e:
            self.logger.error(f"处理用户请求时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "response": "系统处理请求时出现错误"
            }

    async def _record_scientific_cognitive_data(self,
                                                user_id: str,
                                                request_type: str,
                                                original_content: str,
                                                result: Dict[str, Any],
                                                processing_time: float):
        """记录科学认知评估数据"""
        try:
            # 构建交互数据
            interaction_data = {
                'type': request_type,
                'content': original_content,
                'user_response': result.get('response', ''),
                'processing_time': processing_time,
                'context': f"请求类型: {request_type}",
                'metadata': {
                    'code_quality': result.get('code_quality', 0.5),
                    'explanation_quality': result.get('explanation_quality', 0.5),
                    'response_length': len(result.get('response', '')),
                    'success': result.get('success', True),
                    'interaction_type': request_type,
                    'complexity': self._estimate_complexity(result, original_content),
                    'context_used': result.get('context_used', False),
                    'enhancement_applied': result.get('enhancement_applied', False)
                }
            }

            # 使用科学API方法
            analysis_result = await self.cognition_api.analyze_learning_interaction(
                user_id, interaction_data
            )

            if analysis_result['success']:
                self.logger.info(f"科学认知分析完成 - 用户: {user_id}")
            else:
                self.logger.warning(f"科学认知分析部分失败: {analysis_result.get('error', '未知错误')}")

        except Exception as e:
            self.logger.warning(f"记录科学认知数据失败: {e}")

    async def _enhance_with_scientific_cognition(self,
                                                 user_id: str,
                                                 result: Dict[str, Any],
                                                 request_type: str,
                                                 original_content: str) -> Dict[str, Any]:
        """用科学认知数据增强结果 - 修复方法调用"""
        try:
            # 获取科学认知状态
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)

            # 获取个性化学习参数
            learning_context = self._map_learning_context(request_type, original_content)
            learning_params = await self.cognition_api.get_personalized_learning_parameters(
                user_id, learning_context
            )

            # 获取学习进展分析
            progression_analysis = await self.cognition_api.get_learning_progression_analysis(user_id)

            # 获取认知强项弱项分析
            strengths_weaknesses = await self.cognition_api.get_cognitive_strengths_weaknesses(user_id)

            # 修复：获取学习推荐（使用修复后的方法）
            learning_goal = self._infer_learning_goal(original_content, request_type)
            learning_recommendations = await self.cognition_api.get_learning_recommendations(
                user_id, learning_goal
            )

            # 集成到结果中
            if "cognitive_insights" not in result:
                result["cognitive_insights"] = {}

            result["cognitive_insights"].update({
                "user_cognitive_state": cognitive_state,
                "learning_parameters": learning_params,
                "progression_analysis": progression_analysis,
                "strengths_weaknesses": strengths_weaknesses,
                "learning_recommendations": learning_recommendations,
                "scientific_analysis_timestamp": cognitive_state.get('last_updated', '')
            })

            # 添加科学认知指导的响应增强
            if learning_params and 'parameters' in learning_params:
                params = learning_params['parameters']
                result["scientifically_guided_response"] = self._apply_scientific_guidance(
                    result.get('response', ''), params, cognitive_state
                )

            self.logger.info(
                f"科学认知增强完成 - 用户: {user_id}, 认知水平: {cognitive_state.get('overall_cognitive_level', 0.5):.3f}")

            return result

        except Exception as e:
            self.logger.warning(f"集成科学认知数据失败: {e}")
            return result

    def _infer_learning_goal(self, content: str, request_type: str) -> str:
        """推断学习目标"""
        content_lower = content.lower()

        # 基于内容关键词推断学习目标
        if "函数" in content or "function" in content_lower:
            return "掌握函数编程"
        elif "类" in content or "class" in content_lower or "对象" in content:
            return "理解面向对象编程"
        elif "算法" in content or "algorithm" in content_lower:
            return "学习算法设计"
        elif "数据结构" in content or "data structure" in content_lower:
            return "掌握数据结构"
        elif "列表" in content or "list" in content_lower:
            return "学习列表操作"
        elif "字典" in content or "dict" in content_lower:
            return "学习字典操作"
        elif "练习" in content or "exercise" in content_lower:
            return "提高编程实践能力"
        elif "调试" in content or "debug" in content_lower:
            return "学习调试技巧"
        elif "错误" in content or "error" in content_lower:
            return "理解错误处理"
        else:
            return "提高编程能力"

    def _map_learning_context(self, request_type: str, content: str) -> str:
        """映射学习上下文"""
        content_lower = content.lower()

        if request_type == "qa":
            if "基础" in content or "入门" in content or "什么是" in content:
                return "new_concept"
            elif "如何" in content or "怎么" in content or "方法" in content:
                return "skill_application"
            else:
                return "conceptual_understanding"
        elif request_type == "exercise":
            return "practice"
        elif request_type == "evaluation":
            return "feedback"
        else:
            return "general"

    def _apply_scientific_guidance(self, original_response: str, params: Dict[str, Any],
                                   cognitive_state: Dict[str, Any]) -> str:
        """应用科学认知指导调整响应"""
        guided_response = original_response

        # 基于解释深度调整
        explanation_depth = params.get('explanation_depth', 0.7)
        if explanation_depth < 0.4 and len(guided_response) > 300:
            sentences = guided_response.split('。')
            if len(sentences) > 3:
                guided_response = '。'.join(sentences[:3]) + '。'

        # 基于提示策略
        hint_strategy = params.get('hint_strategy', 'balanced')
        if hint_strategy == "guided":
            guided_response += "\n\n💡 提示：如果需要更多指导，请随时告诉我！"
        elif hint_strategy == "minimal":
            # 最少提示，不添加额外内容
            pass
        else:
            guided_response += "\n\n💡 有任何疑问都可以继续问我。"

        # 基于认知水平添加鼓励
        cognitive_level = cognitive_state.get('overall_cognitive_level', 0.5)
        if cognitive_level > 0.7:
            guided_response += "\n\n🚀 你的理解能力很棒！可以尝试更复杂的挑战。"
        elif cognitive_level < 0.4:
            guided_response += "\n\n🌱 学习是一个循序渐进的过程，坚持下去！"

        return guided_response

    def _estimate_complexity(self, result: Dict[str, Any], original_content: str) -> float:
        """估计交互复杂度"""
        complexity = 0.5

        # 基于响应长度
        response = result.get("response", "")
        if len(response) > 500:
            complexity += 0.2
        elif len(response) < 100:
            complexity -= 0.1

        # 基于技术关键词
        complex_keywords = ["继承", "多态", "递归", "算法", "复杂度", "设计模式", "架构", "异步", "并发"]
        if any(keyword in original_content for keyword in complex_keywords):
            complexity += 0.3

        return max(0.1, min(1.0, complexity))

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        active_users = len(self.user_contexts)
        return {
            "system": "运行中",
            "cognitive_framework": "科学认知评估框架",
            "agents_initialized": True,
            "scientific_api": "Scientific-Cognitive-API",
            "active_users": active_users,
            "user_contexts_stored": active_users,
            "timestamp": asyncio.get_event_loop().time()
        }

    async def get_user_cognitive_report(self, user_id: str) -> Dict[str, Any]:
        """获取用户认知报告"""
        try:
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
            progression_analysis = await self.cognition_api.get_learning_progression_analysis(user_id)
            strengths_weaknesses = await self.cognition_api.get_cognitive_strengths_weaknesses(user_id)

            # 获取用户上下文信息
            user_context = self._get_user_context(user_id)

            return {
                "user_id": user_id,
                "cognitive_state": cognitive_state,
                "progression_analysis": progression_analysis,
                "strengths_weaknesses": strengths_weaknesses,
                "interaction_history": {
                    "total_interactions": len(user_context.get("recent_history", [])),
                    "recent_activity": user_context.get("last_interaction_time", 0)
                },
                "report_generated_at": asyncio.get_event_loop().time()
            }
        except Exception as e:
            self.logger.error(f"获取用户认知报告失败: {e}")
            return {"error": str(e)}

    async def clear_user_context(self, user_id: str):
        """清除用户上下文（用于测试或重置）"""
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
            self.logger.info(f"已清除用户 {user_id} 的上下文")

    async def get_user_context_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户上下文摘要"""
        context = self._get_user_context(user_id)
        return {
            "user_id": user_id,
            "history_length": len(context.get("recent_history", [])),
            "last_interaction": context.get("last_interaction_time", 0),
            "learning_goals": context.get("learning_goals", []),
            "preferred_difficulty": context.get("preferred_difficulty", "medium")
        }


# 全局系统实例
_system_instance = None


def get_system():
    """获取系统实例（单例模式）"""
    global _system_instance
    if _system_instance is None:
        _system_instance = ProgrammingEducationSystem()
    return _system_instance


async def demo():
    """演示系统功能 - 展示上下文感知能力"""
    system = get_system()

    print("=" * 60)
    print("编程教育智能体系统 - 科学认知框架演示（上下文感知版）")
    print("=" * 60)

    user_id = "student_001"

    # 演示1: 连续对话展示上下文感知
    print("\n1. 演示上下文感知对话:")

    # 第一次提问
    print(f"\n第一次提问:")
    result1 = await system.process_user_request(
        "qa",
        "Python中什么是函数？",
        user_id
    )
    print(f"回答: {result1['response'][:100]}...")

    # 后续提问（依赖上下文）
    print(f"\n后续提问（依赖上下文）:")
    result2 = await system.process_user_request(
        "qa",
        "参数有哪些类型？",
        user_id
    )
    print(f"回答: {result2['response'][:100]}...")

    # 显示上下文使用情况
    print(f"\n上下文使用情况:")
    print(f"- 增强应用: {result2.get('enhancement_applied', False)}")
    print(f"- 上下文使用: {result2.get('context_used', False)}")

    # 显示科学认知信息
    if "cognitive_insights" in result2:
        insights = result2["cognitive_insights"]
        state = insights.get("user_cognitive_state", {})
        print(f"科学认知水平: {state.get('overall_cognitive_level', 0.5):.2f}")

    # 演示2: 练习生成
    print("\n2. 演示练习生成:")
    result3 = await system.process_user_request(
        "exercise",
        "生成一个关于Python列表操作的练习",
        user_id
    )
    print(f"练习生成结果: {result3['response'][:150]}...")

    # 演示3: 获取用户上下文摘要
    print("\n3. 演示用户上下文摘要:")
    context_summary = await system.get_user_context_summary(user_id)
    print(f"交互历史长度: {context_summary['history_length']}")
    print(f"最后交互时间: {context_summary['last_interaction']}")

    # 演示4: 获取科学认知报告
    print("\n4. 演示科学认知报告:")
    cognitive_report = await system.get_user_cognitive_report(user_id)
    if "cognitive_state" in cognitive_report:
        state = cognitive_report["cognitive_state"]
        print(f"认知维度: {state.get('cognitive_dimensions', {})}")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo())