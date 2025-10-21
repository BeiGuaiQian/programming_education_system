# src/programming_education_system/main_final.py
"""
编程教育智能体系统最终版主程序
集成LLM-UM框架，保持所有原有功能
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from programming_education_system.agents.user_agent import UserAgent
from programming_education_system.agents.main_agent import MainAgent
from programming_education_system.agents.qa_agent import QAAgent
from programming_education_system.agents.exercise_agent import ExerciseGenerationAgent
from programming_education_system.agents.evaluation_agent import AnswerEvaluationAgent
from programming_education_system.agents.personal_agent import PersonalizedLearningAgent

# 使用LLM-UM框架的认知评估API
from programming_education_system.cognition_judger.cognitive_api_llm_um import get_cognition_api
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ProgrammingEducationSystem:
    """编程教育智能体系统主类 - 最终版"""

    def __init__(self):
        self.logger = logging.getLogger("System-Final")
        # 初始化LLM-UM认知评估API
        self.cognition_api = get_cognition_api()
        self.initialize_agents()

    def initialize_agents(self):
        """初始化所有智能体"""
        self.logger.info("初始化智能体...")

        # 按依赖顺序初始化代理
        self.personal_agent = PersonalizedLearningAgent()
        self.qa_agent = QAAgent(self.personal_agent)
        self.exercise_agent = ExerciseGenerationAgent(self.personal_agent)
        self.evaluation_agent = AnswerEvaluationAgent(self.personal_agent)
        self.main_agent = MainAgent(
            self.qa_agent,
            self.exercise_agent,
            self.evaluation_agent,
            self.personal_agent
        )
        self.user_agent = UserAgent(self.main_agent)

        self.logger.info("所有智能体初始化完成")

    async def process_user_request(self, request_type: str, content: str, user_id: str = "user_001"):
        """
        处理用户请求 - 集成LLM-UM框架
        """
        self.logger.info(f"处理用户请求 - 类型: {request_type}, 用户: {user_id}")

        try:
            # 记录交互开始时间（用于认知评估）
            start_time = asyncio.get_event_loop().time()

            # 通过用户代理处理请求（保持原有功能不变）
            result = await self.user_agent.receive_user_request(request_type, content, user_id)
            final_result = await self.user_agent.collect_and_return_results(result)

            # 计算处理时间（用于认知评估）
            processing_time = asyncio.get_event_loop().time() - start_time

            # 记录认知评估数据（使用LLM-UM框架）
            await self._record_cognitive_data(user_id, request_type, final_result, processing_time, content)

            # 集成认知信息到结果（使用LLM-UM框架）
            final_result = await self._enhance_with_cognition(user_id, final_result, request_type)

            return final_result

        except Exception as e:
            self.logger.error(f"处理用户请求时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "response": "系统处理请求时出现错误"
            }

    async def _record_cognitive_data(self,
                                     user_id: str,
                                     request_type: str,
                                     result: Dict[str, Any],
                                     processing_time: float,
                                     original_content: str):
        """记录认知评估数据 - 使用LLM-UM框架"""
        try:
            interaction_data = {
                "processing_time": processing_time,
                "correctness": result.get("correctness", 0.5),
                "complexity": self._estimate_complexity(result, original_content),
                "domain": self._extract_knowledge_domain(result, original_content),
                "cognitive_level": self._map_to_cognitive_level(request_type),
                "code_quality": result.get("code_quality", 0.5),
                "explanation_depth": result.get("explanation_quality", 0.5),
                "response_length": len(result.get("response", "")),
                "success": result.get("success", True)
            }

            await self.cognition_api.record_interaction(
                user_id, request_type, interaction_data
            )

            self.logger.info(f"LLM-UM认知数据记录完成 - 用户: {user_id}")

        except Exception as e:
            self.logger.warning(f"记录认知数据失败: {e}")

    async def _enhance_with_cognition(self, user_id: str, result: Dict[str, Any], request_type: str) -> Dict[str, Any]:
        """用认知数据增强结果 - 使用LLM-UM框架"""
        try:
            # 获取认知档案（来自LLM-UM框架）
            cognitive_profile = await self.cognition_api.get_cognitive_level(user_id)

            # 获取个性化推荐（来自LLM-UM框架）
            recommendations = await self.cognition_api.get_personalization_recommendations(
                user_id, request_type
            )

            # 获取自适应参数（来自LLM-UM框架）
            adaptive_params = await self.cognition_api.get_adaptive_content_parameters(user_id)

            # 集成到结果中，不影响原有结构
            if "cognitive_insights" not in result:
                result["cognitive_insights"] = {}

            result["cognitive_insights"].update({
                "user_profile": cognitive_profile,
                "recommendations": recommendations,
                "personalization_parameters": adaptive_params
            })

            self.logger.info(
                f"LLM-UM认知增强完成 - 用户: {user_id}, 认知水平: {cognitive_profile.get('overall_level', 0.5):.3f}")

            return result

        except Exception as e:
            self.logger.warning(f"集成认知数据失败: {e}")
            return result

    def _estimate_complexity(self, result: Dict[str, Any], original_content: str) -> float:
        """估计交互复杂度"""
        complexity = 0.5

        # 基于响应长度
        response = result.get("response", "")
        if len(response) > 500:
            complexity += 0.2
        elif len(response) < 100:
            complexity -= 0.1

        # 基于原始内容长度
        if len(original_content) > 200:
            complexity += 0.2

        # 基于结果中的详细信息
        details = result.get("details", {})
        if "exercises" in details and len(details["exercises"]) > 0:
            complexity += 0.2
        if "code_analysis" in details:
            complexity += 0.3
        if "learning_tips" in details:
            complexity += 0.1

        return max(0.1, min(1.0, complexity))

    def _extract_knowledge_domain(self, result: Dict[str, Any], original_content: str) -> str:
        """提取知识领域"""
        # 首先尝试从结果中提取
        details = result.get("details", {})
        if "topic" in details:
            topic = details["topic"]
            domain_mapping = {
                "python_basics": "syntax",
                "data_structures": "data_structures",
                "algorithms": "algorithms",
                "oop": "oop",
                "web_development": "syntax",
                "data_science": "algorithms",
                "general_programming": "syntax"
            }
            return domain_mapping.get(topic, "syntax")

        # 基于响应内容分析知识领域
        response = result.get("response", "").lower()
        content = original_content.lower()

        combined_text = response + " " + content

        if any(word in combined_text for word in ["class", "object", "inheritance", "多态", "封装"]):
            return "oop"
        elif any(word in combined_text for word in ["function", "lambda", "map", "filter", "reduce"]):
            return "functional"
        elif any(word in combined_text for word in ["algorithm", "sort", "search", "递归", "算法"]):
            return "algorithms"
        elif any(word in combined_text for word in ["list", "dict", "tuple", "set", "数据结构"]):
            return "data_structures"
        elif any(word in combined_text for word in ["thread", "process", "async", "并发", "多线程"]):
            return "concurrency"
        else:
            return "syntax"

    def _map_to_cognitive_level(self, request_type: str) -> str:
        """映射到认知水平"""
        mapping = {
            "qa": "understand",
            "exercise": "apply",
            "evaluation": "evaluate",
            "personal": "analyze",
            "auto": "understand"  # 默认类型
        }
        return mapping.get(request_type, "remember")

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "system": "运行中",
            "llm_um_framework": "已集成",
            "agents_initialized": True,
            "cognitive_api": "LLM-UM",
            "timestamp": asyncio.get_event_loop().time()
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
    """演示系统功能 - 集成LLM-UM框架"""
    system = get_system()

    print("=" * 60)
    print("编程教育智能体系统 - 最终版演示 (LLM-UM集成)")
    print("=" * 60)

    # 演示1: 答疑功能
    print("\n1. 演示答疑功能:")
    result1 = await system.process_user_request(
        "qa",
        "Python中如何定义函数？",
        "student_001"
    )
    print(f"答疑结果: {result1['response']}")

    # 显示认知信息（来自LLM-UM）
    if "cognitive_insights" in result1:
        insights = result1["cognitive_insights"]
        profile = insights.get("user_profile", {})
        print(f"LLM-UM认知水平: {profile.get('overall_level', 0.5):.2f}")

    # 演示2: 练习生成
    print("\n2. 演示练习生成:")
    result2 = await system.process_user_request(
        "exercise",
        "生成一个初级难度的Python练习",
        "student_001"
    )
    print(f"练习生成结果: {result2['response']}")

    # 显示认知信息（来自LLM-UM）
    if "cognitive_insights" in result2:
        insights = result2["cognitive_insights"]
        recommendations = insights.get("recommendations", {})
        print(f"LLM-UM推荐难度: {recommendations.get('difficulty_level', 'unknown')}")

    # 演示3: 个性化建议
    print("\n3. 演示个性化建议:")
    result3 = await system.process_user_request(
        "personal",
        "给我一些学习建议",
        "student_001"
    )
    print(f"个性化建议: {result3['response']}")

    # 显示认知信息（来自LLM-UM）
    if "cognitive_insights" in result3:
        insights = result3["cognitive_insights"]
        params = insights.get("personalization_parameters", {})
        print(f"LLM-UM个性化参数 - 解释深度: {params.get('explanation_depth', 0.5):.2f}")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo())