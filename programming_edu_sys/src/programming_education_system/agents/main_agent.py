# 修改 src/programming_education_system/agents/main_agent.py
"""
主代理 - 支持上下文感知的意图识别和增强处理
"""
from typing import Dict, Any, TYPE_CHECKING
import logging
import json
import re

from programming_education_system.agents.qa_agent import QAAgent
from programming_education_system.agents.exercise_agent import EnhancedExerciseGenerationAgent
from programming_education_system.agents.evaluation_agent import AnswerEvaluationAgent
from programming_education_system.agents.personal_agent import PersonalizedLearningAgent
from programming_education_system.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MainAgent(BaseAgent):
    """主代理 - 增强版，支持上下文感知和请求增强"""

    def __init__(self, qa_agent: 'QAAgent', exercise_agent: 'EnhancedExerciseGenerationAgent',
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

    async def enhance_request_with_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """使用上下文增强用户请求"""
        original_content = request["content"]
        context = request.get("context", {})

        # 如果没有上下文或内容已经很明确，直接返回
        if not context.get('recent_history') or len(original_content.strip()) > 50:
            return {
                **request,
                "enhancement_info": {
                    "was_enhanced": False,
                    "context_used": False,
                    "original_content": original_content
                }
            }

        try:
            system_prompt = """你是一个上下文理解助手。你的任务是根据对话历史，完善用户当前简短的输入，使其更加完整和明确。

请保持用户的原意，只是补充必要的上下文信息，使请求更加清晰。

请直接返回完善后的用户输入内容，不要添加任何解释。"""

            history_context = "\n对话历史：\n"
            for i, history in enumerate(context['recent_history'][-3:]):  # 只使用最近3条历史
                history_context += f"- 用户: {history.get('user_input', '')}\n"
                history_context += f"- 助手: {history.get('agent_response', '')[:100]}...\n"

            user_message = f"""用户当前输入：{original_content}
{history_context}

请根据对话历史，完善用户的当前输入："""

            llm_client = self._get_llm_client()
            enhanced_content = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=True
            )

            if enhanced_content and len(enhanced_content.strip()) > len(original_content.strip()):
                self.log_activity("请求增强完成", {
                    "original": original_content,
                    "enhanced": enhanced_content[:100] + "...",
                    "history_used": len(context['recent_history'])
                })

                return {
                    **request,
                    "content": enhanced_content.strip(),
                    "original_content": original_content,
                    "enhancement_info": {
                        "was_enhanced": True,
                        "context_used": True,
                        "original_content": original_content,
                        "enhancement_reason": "基于对话历史补充上下文"
                    }
                }

        except Exception as e:
            logger.warning(f"请求增强失败: {e}")

        return {
            **request,
            "enhancement_info": {
                "was_enhanced": False,
                "context_used": False,
                "original_content": original_content
            }
        }

    async def analyze_intent_with_context(self, content: str, context: Dict[str, Any]) -> str:
        """使用上下文分析用户意图"""
        system_prompt = """你是一个智能意图分析助手。你的任务是根据用户的输入和对话历史，判断用户的意图。

可用的意图类型：
1. "qa" - 答疑类：用户询问编程概念、语法、技术问题等
2. "exercise" - 练习类：用户请求生成编程练习、题目、测试等
3. "evaluation" - 评价类：用户请求评价代码、检查代码质量、分析代码问题等
4. "personal" - 个性化类：用户请求学习建议、学习路径、个性化推荐等

请结合对话历史来理解用户的当前意图，确保准确识别用户的真实需求。

请严格按照以下JSON格式返回结果：
{"intent": "qa|exercise|evaluation|personal", "confidence": 0.0-1.0, "reason": "简要说明判断理由"}

判断标准：
- 如果用户明确要求生成题目、练习、测试，选择"exercise"
- 如果用户提供代码并要求评价、检查、分析，选择"evaluation" 
- 如果用户询问学习方法、学习建议、学习路径，选择"personal"
- 其他编程相关问题选择"qa"

请确保只返回JSON格式，不要有其他内容。"""

        # 构建包含上下文的用户消息
        context_info = ""
        if context.get('recent_history'):
            context_info = "\n\n对话历史：\n"
            for i, history in enumerate(context['recent_history'][-10:]):  # 限制历史长度
                context_info += f"{i + 1}. 用户: {history.get('user_input', '')}\n"
                context_info += f"   助手: {history.get('agent_response', '')}...\n"

        user_message = f"""用户当前输入：{content}
{context_info}

请分析用户的当前意图："""

        try:
            llm_client = self._get_llm_client()
            response = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=True
            )

            intent_data = self._parse_llm_response(response)

            if intent_data and "intent" in intent_data:
                self.log_activity("上下文感知意图分析完成", {
                    "intent": intent_data["intent"],
                    "confidence": intent_data.get("confidence", 0),
                    "reason": intent_data.get("reason", ""),
                    "history_used": len(context.get('recent_history', [])) > 0
                })
                return intent_data["intent"]
            else:
                logger.warning(f"无法解析LLM意图分析结果: {response}")
                return await self._fallback_intent_analysis(content)

        except Exception as e:
            logger.error(f"上下文感知意图分析失败: {e}")
            return await self._fallback_intent_analysis(content)

    async def analyze_intent(self, request: Dict[str, Any]) -> str:
        """分析用户意图 - 使用上下文感知"""
        content = request["content"].strip()
        request_type = request.get("type", "auto")
        context = request.get("context", {})

        # 如果指定了类型且不是auto，直接使用
        if request_type != "auto" and request_type in ["qa", "exercise", "evaluation", "personal"]:
            self.log_activity("使用指定请求类型", {"type": request_type})
            return request_type

        # 使用上下文感知的智能意图识别
        self.log_activity("开始上下文感知意图识别", {
            "content": content[:50] + "...",
            "has_history": len(context.get('recent_history', [])) > 0
        })
        intent = await self.analyze_intent_with_context(content, context)

        return intent

    async def dispatch_to_sub_agent(self, intent: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """分发请求到子代理 - 传递上下文"""
        self.log_activity("分发请求到子代理", {
            "intent": intent,
            "has_context": len(request.get("context", {}).get("recent_history", [])) > 0,
            "was_enhanced": request.get("enhancement_info", {}).get("was_enhanced", False)
        })

        agents = {
            "qa": self.qa_agent,
            "exercise": self.exercise_agent,
            "evaluation": self.evaluation_agent,
            "personal": self.personal_agent
        }

        target_agent = agents.get(intent, self.qa_agent)

        # 确保请求中包含上下文信息
        if "context" not in request:
            request["context"] = {}

        # 处理请求并获取结果
        result = await target_agent.process(request)

        # 在结果中添加意图信息和增强信息
        result["detected_intent"] = intent
        result["enhancement_applied"] = request.get("enhancement_info", {}).get("was_enhanced", False)
        result["context_used"] = request.get("enhancement_info", {}).get("context_used", False)

        # 如果请求被增强过，在结果中保留原始内容
        if request.get("enhancement_info", {}).get("was_enhanced", False):
            result["original_content"] = request.get("enhancement_info", {}).get("original_content", request["content"])

        return result

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求 - 支持上下文增强和意图识别"""
        # 步骤1: 使用上下文增强请求（如果需要）
        enhanced_request = await self.enhance_request_with_context(request)

        # 步骤2: 分析意图（使用上下文）
        intent = await self.analyze_intent(enhanced_request)
        self.log_activity("意图分析完成", {
            "intent": intent,
            "content": enhanced_request["content"][:30] + "...",
            "context_used": len(enhanced_request.get("context", {}).get("recent_history", [])) > 0,
            "was_enhanced": enhanced_request.get("enhancement_info", {}).get("was_enhanced", False)
        })

        # 步骤3: 分发到对应代理
        result = await self.dispatch_to_sub_agent(intent, enhanced_request)

        # 步骤4: 记录用户行为
        behavior_data = {
            "user_id": enhanced_request["user_id"],
            "intent": intent,
            "content": enhanced_request["content"],
            "original_content": enhanced_request.get("original_content", enhanced_request["content"]),
            "was_enhanced": enhanced_request.get("enhancement_info", {}).get("was_enhanced", False),
            "context_used": enhanced_request.get("enhancement_info", {}).get("context_used", False),
            "timestamp": enhanced_request.get("timestamp", "unknown")
        }
        await self.personal_agent.track_user_behavior(behavior_data)

        return result

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM的JSON响应"""
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

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

        exercise_keywords = [
            "练习", "题目", "习题", "作业", "题", "exercise", "problem", "题目",
            "生成练习", "做练习", "练习题", "编程题", "算法题", "给我题", "出一道"
        ]

        evaluation_keywords = [
            "评价", "检查", "评审", "review", "evaluate", "代码", "代码评价",
            "检查代码", "代码检查", "代码评审", "运行结果", "测试代码", "分析代码"
        ]

        personal_keywords = [
            "建议", "推荐", "应该学", "学习路径", "suggestion", "advice",
            "学习建议", "下一步", "如何学习", "学习计划", "路径", "规划"
        ]

        has_code = "def " in content or "import " in content or ("=" in content and ":" in content)

        if any(keyword in content_lower for keyword in evaluation_keywords) or has_code:
            return "evaluation"

        if any(keyword in content_lower for keyword in exercise_keywords):
            return "exercise"

        if any(keyword in content_lower for keyword in personal_keywords):
            return "personal"

        return "qa"