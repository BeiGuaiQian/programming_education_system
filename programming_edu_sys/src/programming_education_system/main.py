# programming_education_system/main.py
"""
编程教育智能体系统主入口 - 修复导入版本
"""
import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径

from agents.user_agent import UserAgent
from agents.main_agent import MainAgent
from agents.qa_agent import QAAgent
from agents.exercise_agent import ExerciseGenerationAgent
from agents.evaluation_agent import AnswerEvaluationAgent
from agents.personal_agent import PersonalizedLearningAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ProgrammingEducationSystem:
    """编程教育智能体系统主类"""
    
    def __init__(self):
        self.logger = logging.getLogger("System")
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
        处理用户请求
        """
        self.logger.info(f"处理用户请求 - 类型: {request_type}, 用户: {user_id}")
        
        try:
            # 通过用户代理处理请求
            result = await self.user_agent.receive_user_request(request_type, content, user_id)
            return await self.user_agent.collect_and_return_results(result)
            
        except Exception as e:
            self.logger.error(f"处理用户请求时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "response": "系统处理请求时出现错误"
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
    """演示系统功能"""
    system = get_system()
    
    print("=" * 60)
    print("编程教育智能体系统演示")
    print("=" * 60)
    
    # 演示1: 答疑功能
    print("\n1. 演示答疑功能:")
    result1 = await system.process_user_request(
        "qa", 
        "Python中如何定义函数？", 
        "student_001"
    )
    print(f"答疑结果: {result1['response']}")
    
    # 演示2: 练习生成
    print("\n2. 演示练习生成:")
    result2 = await system.process_user_request(
        "exercise",
        "生成一个初级难度的Python练习",
        "student_001"
    )
    print(f"练习生成结果: {result2['response']}")
    
    # 演示3: 个性化建议
    print("\n3. 演示个性化建议:")
    result3 = await system.process_user_request(
        "personal",
        "给我一些学习建议",
        "student_001"
    )
    print(f"个性化建议: {result3['response']}")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)

if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo())