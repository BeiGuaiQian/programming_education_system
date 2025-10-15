# src/programming_education_system/agents/user_agent.py
"""
用户代理 - 专注于优化用户输入
"""
from typing import Dict, Any
import logging
import re
from programming_education_system.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class UserAgent(BaseAgent):
    """用户代理，专注于优化用户输入"""

    def __init__(self, main_agent):
        super().__init__("UserAgent")
        self.main_agent = main_agent
        self.current_user_id = None
        self.llm_client = None

    def _get_llm_client(self):
        """延迟获取LLM客户端"""
        if self.llm_client is None:
            from programming_education_system.utils.llm_utils import llm_client
            self.llm_client = llm_client
        return self.llm_client

    async def enhance_user_input(self, content: str) -> Dict[str, Any]:
        """使用大模型优化用户输入，生成更清晰的提示词"""
        system_prompt = """你是一个用户输入优化助手。你的任务是优化用户的输入，使其更清晰、具体、适合AI处理。

优化目标：
1. 澄清模糊的表述
2. 补充缺失的上下文
3. 结构化复杂问题
4. 明确具体需求
5. 保持用户原意不变

请专注于编程教育领域，确保优化后的提示词能够帮助AI更好地理解用户的学习需求。

请返回优化后的提示词，不需要其他解释。"""

        user_message = f"""原始用户输入：{content}

请优化这个输入，使其更清晰、具体："""

        try:
            llm_client = self._get_llm_client()
            response = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=True
            )

            # 解析优化结果
            enhanced_content = self._parse_enhancement_response(response, content)

            self.log_activity("用户输入优化完成", {
                "original": content[:50] + "..." if len(content) > 50 else content,
                "enhanced": enhanced_content[:50] + "..." if len(enhanced_content) > 50 else enhanced_content
            })

            return {
                "original_content": content,
                "enhanced_content": enhanced_content,
                "was_enhanced": enhanced_content != content
            }

        except Exception as e:
            logger.error(f"用户输入优化失败: {e}")
            # 如果优化失败，返回原始内容
            return {
                "original_content": content,
                "enhanced_content": content,
                "was_enhanced": False
            }

    def _parse_enhancement_response(self, response: str, original_content: str) -> str:
        """解析优化响应"""
        # 清理响应，去除可能的格式标记
        cleaned_response = response.strip()

        # 如果响应为空或与原始内容相同，返回原始内容
        if not cleaned_response or cleaned_response == original_content:
            return original_content

        return cleaned_response

    async def receive_user_request(self, request_type: str, content: str, user_id: str) -> Dict[str, Any]:
        """
        接收用户请求，优化输入后转发

        Args:
            request_type: 请求类型 (qa, exercise, evaluation, personal, auto)
            content: 请求内容
            user_id: 用户ID

        Returns:
            处理结果
        """
        self.current_user_id = user_id

        # 记录原始请求
        self.log_activity("接收用户原始请求", {
            "user_id": user_id,
            "request_type": request_type,
            "original_content": content[:50] + "..." if len(content) > 50 else content
        })

        # 优化用户输入（不依赖请求类型）
        enhancement_result = await self.enhance_user_input(content)

        # 构建请求对象
        request = {
            "type": request_type,
            "content": enhancement_result["enhanced_content"],
            "original_content": enhancement_result["original_content"],
            "user_id": user_id,
            "timestamp": self._get_timestamp(),
            "enhancement_info": {
                "was_enhanced": enhancement_result["was_enhanced"]
            }
        }

        # 转发给主代理
        return await self.forward_to_main_agent(request)

    async def forward_to_main_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """转发优化后的请求给主代理"""
        self.log_activity("转发优化后的请求给主代理", {
            "request_type": request["type"],
            "was_enhanced": request["enhancement_info"]["was_enhanced"]
        })
        return await self.main_agent.process(request)

    async def collect_and_return_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """收集并返回结果给用户"""
        self.log_activity("返回结果给用户", {
            "result_type": type(results).__name__,
            "detected_intent": results.get("detected_intent", "unknown")
        })

        # 格式化返回结果
        formatted_result = {
            "success": True,
            "user_id": self.current_user_id,
            "response": results.get("response", "请求处理完成"),
            "details": results.get("details", {}),
            "suggestions": results.get("suggestions", []),
            "request_type": results.get("detected_intent", "unknown"),
            "processing_info": {
                "input_enhanced": results.get("enhancement_applied", False)
            }
        }

        # 添加错误信息（如果有）
        if "error" in results:
            formatted_result.update({
                "success": False,
                "error": results["error"]
            })

        return formatted_result

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求（BaseAgent要求实现）"""
        return await self.receive_user_request(
            request.get("type", "auto"),
            request.get("content", ""),
            request.get("user_id", "anonymous")
        )

    def _get_timestamp(self) -> str:
        """获取时间戳（简化版本）"""
        import time
        return str(time.time())