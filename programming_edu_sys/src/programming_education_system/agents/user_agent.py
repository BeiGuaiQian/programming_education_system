# src/programming_education_system/agents/user_agent.py
"""
用户代理 - 完全上下文感知版本
始终使用上下文来理解和优化用户输入
"""
from typing import Dict, Any
import logging
import time
from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.utils.context_manager import context_manager

logger = logging.getLogger(__name__)


class UserAgent(BaseAgent):
    """用户代理 - 完全上下文感知版本"""

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

    def _parse_enhancement_response(self, response: str, original_content: str) -> str:
        """解析优化响应"""
        cleaned_response = response.strip()

        # 如果响应为空或与原始内容相同，返回原始内容
        if not cleaned_response or cleaned_response == original_content:
            return original_content

        return cleaned_response

    async def enhance_user_input_with_context(self, content: str, user_id: str) -> Dict[str, Any]:
        """使用上下文优化和理解用户输入"""
        # 获取对话历史和上下文
        dialog_history = context_manager.get_dialog_history(user_id, limit=5)
        conversation_context = context_manager.get_conversation_context(user_id) or {}

        system_prompt = """你是一个用户输入优化和理解助手。你的任务是结合对话历史来理解和优化用户的输入，确保准确理解用户的真实意图并生成清晰的提示词。

优化目标：
1. 结合对话历史澄清模糊的表述
2. 补充缺失的上下文信息
3. 明确代词和指代内容（如"这个"、"那个"、"它"等）
4. 结构化复杂问题
5. 保持用户原意不变

请特别注意：
- 如果用户使用代词或简短表达，请结合上下文明确具体指代
- 如果用户请求答案，请明确是针对哪个具体题目的
- 如果用户给出后续请求，请确保与之前对话的连贯性

请返回优化后的清晰提示词，不需要其他解释。"""

        # 构建包含历史上下文的用户消息
        history_context = ""
        if dialog_history:
            history_context = "\n\n对话历史：\n"
            for i, dialog in enumerate(dialog_history[-3:]):  # 只使用最近3条历史
                history_context += f"{i + 1}. 用户: {dialog.get('user_input', '')}\n"
                history_context += f"   助手: {dialog.get('agent_response', '')[:100]}...\n"

        user_message = f"""原始用户输入：{content}
{history_context}

请结合对话历史理解用户的真实意图，并返回优化后的清晰提示词："""

        try:
            llm_client = self._get_llm_client()
            response = await llm_client.generate_response(
                system_prompt,
                user_message,
                use_cache=True
            )

            enhanced_content = self._parse_enhancement_response(response, content)

            self.log_activity("上下文感知输入优化完成", {
                "original": content[:50] + "..." if len(content) > 50 else content,
                "enhanced": enhanced_content[:50] + "..." if len(enhanced_content) > 50 else enhanced_content,
                "history_used": len(dialog_history) > 0
            })

            return {
                "original_content": content,
                "enhanced_content": enhanced_content,
                "was_enhanced": enhanced_content != content,
                "context_used": len(dialog_history) > 0
            }

        except Exception as e:
            logger.error(f"上下文感知输入优化失败: {e}")
            return {
                "original_content": content,
                "enhanced_content": content,
                "was_enhanced": False,
                "context_used": False
            }

    async def receive_user_request(self, request_type: str, content: str, user_id: str) -> Dict[str, Any]:
        """接收用户请求，使用上下文理解后转发"""
        self.current_user_id = user_id

        # 记录原始请求
        self.log_activity("接收用户原始请求", {
            "user_id": user_id,
            "request_type": request_type,
            "original_content": content[:50] + "..." if len(content) > 50 else content
        })

        # 使用上下文优化用户输入
        enhancement_result = await self.enhance_user_input_with_context(content, user_id)

        # 获取对话上下文
        conversation_context = context_manager.get_conversation_context(user_id) or {}
        dialog_history = context_manager.get_dialog_history(user_id, limit=3)

        # 构建请求对象
        request = {
            "type": request_type,
            "content": enhancement_result["enhanced_content"],
            "original_content": enhancement_result["original_content"],
            "user_id": user_id,
            "timestamp": self._get_timestamp(),
            "enhancement_info": {
                "was_enhanced": enhancement_result["was_enhanced"],
                "context_used": enhancement_result["context_used"]
            },
            "context": {
                "conversation_context": conversation_context,
                "recent_history": dialog_history,
                "learning_progress": context_manager.get_learning_progress(user_id) or {}
            }
        }

        # 转发给主代理
        return await self.forward_to_main_agent(request)

    async def save_conversation_result(self, user_id: str, request: Dict[str, Any], result: Dict[str, Any]):
        """保存对话结果到上下文"""
        try:
            # 保存对话历史
            dialog_data = {
                'user_input': request.get('original_content', ''),
                'agent_response': result.get('response', ''),
                'intent': result.get('detected_intent', 'unknown'),
                'topic': result.get('details', {}).get('topic', 'general')
            }
            context_manager.save_dialog_history(user_id, dialog_data)

            # 更新对话上下文
            current_context = {
                'last_intent': result.get('detected_intent', 'unknown'),
                'last_topic': result.get('details', {}).get('topic', 'general'),
                'last_interaction_time': request.get('timestamp', ''),
                'interaction_count': context_manager.get_conversation_context(user_id).get('interaction_count', 0) + 1
            }

            # 保存练习相关信息（如果有）
            if result.get('detected_intent') == 'exercise' and 'details' in result:
                exercise_details = result['details']
                current_context['last_exercise_topic'] = exercise_details.get('topic', 'general')
                current_context['last_exercise_type'] = exercise_details.get('type', 'unknown')

                # 保存题目信息（如果可能）
                if 'questions' in exercise_details and exercise_details['questions']:
                    first_question = exercise_details['questions'][0]
                    current_context['last_question_preview'] = first_question.get('content', {}).get('description', '')[
                        :100]
                elif 'exercise' in exercise_details:
                    current_context['last_question_preview'] = exercise_details['exercise'].get('content', {}).get(
                        'description', '')[:100]

            context_manager.save_conversation_context(user_id, current_context)

            # 更新学习进度（如果有相关信息）
            if 'details' in result and 'cognitive_insights' in result['details']:
                learning_progress = {
                    'last_cognitive_level': result['details']['cognitive_insights'].get('current_level', 0.5),
                    'focus_areas': result['details']['cognitive_insights'].get('focus_areas', []),
                    'last_learning_tips': result['details'].get('learning_tips', [])
                }
                context_manager.save_learning_progress(user_id, learning_progress)

            self.log_activity("对话上下文保存完成", {"user_id": user_id})

        except Exception as e:
            logger.error(f"保存对话结果失败: {e}")

    async def forward_to_main_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """转发优化后的请求给主代理"""
        self.log_activity("转发优化后的请求给主代理", {
            "request_type": request["type"],
            "was_enhanced": request["enhancement_info"]["was_enhanced"],
            "has_context": len(request["context"]["recent_history"]) > 0
        })

        result = await self.main_agent.process(request)

        # 保存对话结果
        await self.save_conversation_result(request["user_id"], request, result)

        return result

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
                "input_enhanced": results.get("enhancement_applied", False),
                "context_used": results.get("context_used", False)
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
        result = await self.receive_user_request(
            request.get("type", "auto"),
            request.get("content", ""),
            request.get("user_id", "anonymous")
        )

        return await self.collect_and_return_results(result)

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        return str(time.time())