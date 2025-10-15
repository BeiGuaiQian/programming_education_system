# src/programming_education_system/agents/main_agent.py
"""
主代理 - 专注于意图识别和请求分发
"""
from typing import Dict, Any, TYPE_CHECKING
import logging
import json
import re

from programming_education_system.agents.qa_agent import QAAgent
from programming_education_system.agents.exercise_agent import ExerciseGenerationAgent
from programming_education_system.agents.evaluation_agent import AnswerEvaluationAgent
from programming_education_system.agents.personal_agent import PersonalizedLearningAgent
from programming_education_system.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MainAgent(BaseAgent):
    """主代理，专注于意图识别和请求分发"""

    def __init__(self, qa_agent: 'QAAgent', exercise_agent: 'ExerciseGenerationAgent',
                 evaluation_agent: 'AnswerEvaluationAgent', personal_agent: 'PersonalizedLearningAgent'):
        super().__init__("MainAgent")
        self.qa_agent = qa_agent
        self.exercise_agent = exercise_agent
        self.evaluation_agent = evaluation_agent
        self.personal_agent = personal_agent
        self.llm_client = None

    def _get_llm_client(self):
        """延迟获取LLM客户端"""
        if self.llm_client is None:
            from programming_education_system.utils.llm_utils import llm_client
            self.llm_client = llm_client
        return self.llm_client

    async def receive_from_user_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """接收用户代理请求"""
        enhancement_info = request.get("enhancement_info", {})
        self.log_activity("接收用户代理请求", {
            "content": request["content"][:50] + "...",
            "was_enhanced": enhancement_info.get("was_enhanced", False)
        })
        return await self.process(request)

    async def analyze_intent_with_llm(self, content: str) -> str:
        """使用大模型分析用户意图"""
        system_prompt = """你是一个智能意图分析助手。你的任务是根据用户的输入，判断用户的意图属于以下哪种类型：

可用的意图类型：
1. "qa" - 答疑类：用户询问编程概念、语法、技术问题等
2. "exercise" - 练习类：用户请求生成编程练习、题目、测试等
3. "evaluation" - 评价类：用户请求评价代码、检查代码质量、分析代码问题等
4. "personal" - 个性化类：用户请求学习建议、学习路径、个性化推荐等

请严格按照以下JSON格式返回结果：
{"intent": "qa|exercise|evaluation|personal", "confidence": 0.0-1.0, "reason": "简要说明判断理由"}

判断标准：
- 如果用户明确要求生成题目、练习、测试，选择"exercise"
- 如果用户提供代码并要求评价、检查、分析，选择"evaluation" 
- 如果用户询问学习方法、学习建议、学习路径，选择"personal"
- 其他编程相关问题选择"qa"

请确保只返回JSON格式，不要有其他内容。"""

        try:
            llm_client = self._get_llm_client()
            response = await llm_client.generate_response(
                system_prompt,
                f"用户输入：{content}",
                use_cache=True
            )

            # 解析JSON响应
            intent_data = self._parse_llm_response(response)

            if intent_data and "intent" in intent_data:
                self.log_activity("LLM意图分析完成", {
                    "intent": intent_data["intent"],
                    "confidence": intent_data.get("confidence", 0),
                    "reason": intent_data.get("reason", "")
                })
                return intent_data["intent"]
            else:
                logger.warning(f"无法解析LLM意图分析结果: {response}")
                return "qa"  # 默认回退到答疑

        except Exception as e:
            logger.error(f"LLM意图分析失败: {e}")
            return await self._fallback_intent_analysis(content)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的JSON响应"""
        try:
            # 尝试直接解析JSON
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        # 如果JSON解析都失败，尝试基于文本内容推断
        response_lower = response.lower()
        if '"intent": "qa"' in response_lower or "'intent': 'qa'" in response_lower:
            return {"intent": "qa", "confidence": 0.7, "reason": "从文本中提取"}
        elif '"intent": "exercise"' in response_lower or "'intent': 'exercise'" in response_lower:
            return {"intent": "exercise", "confidence": 0.7, "reason": "从文本中提取"}
        elif '"intent": "evaluation"' in response_lower or "'intent': 'evaluation'" in response_lower:
            return {"intent": "evaluation", "confidence": 0.7, "reason": "从文本中提取"}
        elif '"intent": "personal"' in response_lower or "'intent': 'personal'" in response_lower:
            return {"intent": "personal", "confidence": 0.7, "reason": "从文本中提取"}

        return None

    async def _fallback_intent_analysis(self, content: str) -> str:
        """LLM失败时的回退意图分析（基于规则）"""
        content_lower = content.lower()

        # 练习相关关键词
        exercise_keywords = [
            "练习", "题目", "习题", "作业", "题", "exercise", "problem", "题目",
            "生成练习", "做练习", "练习题", "编程题", "算法题", "给我题", "出一道"
        ]

        # 评价相关关键词
        evaluation_keywords = [
            "评价", "检查", "评审", "review", "evaluate", "代码", "代码评价",
            "检查代码", "代码检查", "代码评审", "运行结果", "测试代码", "分析代码"
        ]

        # 个性化相关关键词
        personal_keywords = [
            "建议", "推荐", "应该学", "学习路径", "suggestion", "advice",
            "学习建议", "下一步", "如何学习", "学习计划", "路径", "规划"
        ]

        # 检测代码片段
        has_code = "def " in content or "import " in content or ("=" in content and ":" in content)

        # 优先级：评价 > 练习 > 个性化 > 答疑
        if any(keyword in content_lower for keyword in evaluation_keywords) or has_code:
            return "evaluation"

        if any(keyword in content_lower for keyword in exercise_keywords):
            return "exercise"

        if any(keyword in content_lower for keyword in personal_keywords):
            return "personal"

        # 默认为答疑
        return "qa"

    async def analyze_intent(self, request: Dict[str, Any]) -> str:
        """分析用户意图 - 使用大模型"""
        content = request["content"].strip()
        request_type = request.get("type", "auto")

        # 如果指定了类型且不是auto，直接使用
        if request_type != "auto" and request_type in ["qa", "exercise", "evaluation", "personal"]:
            self.log_activity("使用指定请求类型", {"type": request_type})
            return request_type

        # 使用大模型进行智能意图识别
        self.log_activity("开始智能意图识别", {"content": content[:50] + "..."})
        intent = await self.analyze_intent_with_llm(content)

        return intent

    async def dispatch_to_sub_agent(self, intent: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """分发请求到子代理"""
        self.log_activity("分发请求到子代理", {"intent": intent})

        agents = {
            "qa": self.qa_agent,
            "exercise": self.exercise_agent,
            "evaluation": self.evaluation_agent,
            "personal": self.personal_agent
        }

        target_agent = agents.get(intent, self.qa_agent)
        result = await target_agent.process(request)

        # 在结果中添加意图信息和增强信息
        result["detected_intent"] = intent
        result["enhancement_applied"] = request.get("enhancement_info", {}).get("was_enhanced", False)

        return result

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        # 分析意图
        intent = await self.analyze_intent(request)
        self.log_activity("意图分析完成", {"intent": intent, "content": request["content"][:30] + "..."})

        # 分发到对应代理
        result = await self.dispatch_to_sub_agent(intent, request)

        # 记录用户行为
        behavior_data = {
            "user_id": request["user_id"],
            "intent": intent,
            "content": request["content"],
            "original_content": request.get("original_content", request["content"]),
            "was_enhanced": request.get("enhancement_info", {}).get("was_enhanced", False),
            "timestamp": request.get("timestamp", "unknown")
        }
        await self.personal_agent.track_user_behavior(behavior_data)

        return result