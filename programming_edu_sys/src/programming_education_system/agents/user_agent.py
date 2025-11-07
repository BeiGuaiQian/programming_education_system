# src/programming_education_system/agents/user_agent.py
"""
用户代理 - 简化版，直接使用大模型分析历史对话
"""
from typing import Dict, Any, List, Optional
import logging
import time
import re
from datetime import datetime
import json
from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.utils.context_manager import context_manager

logger = logging.getLogger(__name__)


class SimpleContextAnalyzer:
    """简化版上下文分析器 - 直接使用大模型分析历史对话"""

    def __init__(self):
        self.max_history_analysis = 20  # 减少历史分析数量

    def analyze_context(self, user_id: str, current_input: str) -> Dict[str, Any]:
        """使用大模型分析上下文"""
        try:
            # 获取历史对话
            history = context_manager.get_dialog_history(user_id, limit=self.max_history_analysis)

            # 构建给大模型的提示
            analysis_prompt = self._build_analysis_prompt(current_input, history)

            return {
                'success': True,
                'history_count': len(history),
                'analysis_prompt': analysis_prompt,
                'raw_history': history
            }
        except Exception as e:
            logger.error(f"上下文分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'history_count': 0
            }

    def _build_analysis_prompt(self, current_input: str, history: List[Dict[str, Any]]) -> str:
        """构建分析提示"""
        # 安全地构建历史对话部分
        history_text = "对话历史：\n"

        # 添加历史对话，限制数量并安全处理字符串
        recent_history = history[-10:] if len(history) > 10 else history
        for i, dialog in enumerate(recent_history):
            user_msg = str(dialog.get('user_input', ''))  # 确保是字符串并限制长度
            agent_msg = str(dialog.get('agent_response', ''))  # 确保是字符串并限制长度

            history_text += f"\n{i + 1}. 用户: {user_msg}"
            if agent_msg:
                history_text += f"\n   助手: {agent_msg}"

        # 安全构建完整提示
        prompt = f"""你是一个智能对话分析助手。请分析以下对话历史和当前用户输入，理解用户真实意图，并提取关键信息。

{history_text}

当前用户输入: {current_input}

请分析并返回JSON格式的结果：
{{
  "user_intent": "用户的主要意图（exercise/answer/explanation/concept/example/general）",
  "needs_context": true/false,
  "key_points": ["从历史中提取的关键点1", "关键点2", ...],
  "exercise_reference": {{
    "has_exercise": true/false,
    "exercise_content": "题目内容",
    "exercise_topic": "题目主题"
  }},
  "suggested_enhancement": "建议如何优化当前输入"
}}

请确保准确理解用户意图，特别是：
1. 如果用户请求答案，请从历史中找出对应的题目
2. 如果用户引用历史内容，比如说上一个，再说一次，这个，那个等等，你需要确保正确判断用户的指代，使得引用的历史内容是合理的
3. 保持对话的连贯性

直接返回JSON，不要其他内容："""

        return prompt


class EnhancedUserAgent(BaseAgent):
    """增强版用户代理 - 使用大模型直接分析历史对话"""

    def __init__(self, main_agent):
        super().__init__("EnhancedUserAgent")
        self.main_agent = main_agent
        self.current_user_id = None
        self.llm_client = None
        self.context_analyzer = SimpleContextAnalyzer()

    def _get_llm_client(self):
        """延迟获取LLM客户端"""
        if self.llm_client is None:
            from programming_education_system.utils.llm_utils import llm_client
            self.llm_client = llm_client
        return self.llm_client

    async def enhance_user_input_with_context(self, content: str, user_id: str) -> Dict[str, Any]:
        """使用大模型分析上下文并优化用户输入"""
        try:
            # 使用大模型分析上下文
            context_analysis = self.context_analyzer.analyze_context(user_id, content)

            if not context_analysis['success']:
                logger.warning("上下文分析失败，使用基础优化")
                return await self._fallback_enhancement(content, user_id)

            # 使用大模型分析上下文并获取优化建议
            llm_client = self._get_llm_client()
            analysis_response = await llm_client.generate_response(
                "",
                context_analysis['analysis_prompt'],
                use_cache=False
            )

            # 解析大模型的分析结果
            analysis_result = self._parse_analysis_result(analysis_response, content)

            # 基于分析结果构建优化后的输入
            enhanced_content = self._build_enhanced_input(content, analysis_result, context_analysis['raw_history'])

            # 安全地记录日志
            original_preview = content[:50] + "..." if len(content) > 50 else content
            enhanced_preview = enhanced_content[:50] + "..." if len(enhanced_content) > 50 else enhanced_content

            self.log_activity("大模型上下文分析优化完成", {
                "original": original_preview,
                "enhanced": enhanced_preview,
                "history_used": context_analysis['history_count'],
                "user_intent": analysis_result.get('user_intent', 'unknown'),
                "needs_context": analysis_result.get('needs_context', False)
            })

            return {
                "original_content": content,
                "enhanced_content": enhanced_content,
                "was_enhanced": enhanced_content != content,
                "context_analysis": {
                    'success': True,
                    'llm_analysis': analysis_result,
                    'history_count': context_analysis['history_count']
                },
                "analysis_confidence": 0.8,
                "target_exercise": analysis_result.get('exercise_reference')
            }

        except Exception as e:
            logger.error(f"大模型上下文分析优化失败: {str(e)}")
            return await self._fallback_enhancement(content, user_id)

    def _parse_analysis_result(self, analysis_response: str, original_input: str) -> Dict[str, Any]:
        """解析大模型的分析结果"""
        try:
            # 清理响应文本
            cleaned_response = analysis_response.strip()

            # 尝试解析JSON
            if cleaned_response.startswith('{'):
                result = json.loads(cleaned_response)
                return result
            else:
                # 如果不是JSON，尝试提取JSON部分
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"解析大模型分析结果失败: {str(e)}")
            logger.debug(f"原始响应: {analysis_response}")

        # 如果解析失败，返回默认结果
        return {
            "user_intent": "general",
            "needs_context": False,
            "key_points": [],
            "exercise_reference": {
                "has_exercise": False,
                "exercise_content": "",
                "exercise_topic": ""
            },
            "suggested_enhancement": "直接回应用户输入"
        }

    def _build_enhanced_input(self, original_input: str, analysis_result: Dict[str, Any],
                              history: List[Dict[str, Any]]) -> str:
        """基于分析结果构建优化后的输入"""
        user_intent = analysis_result.get('user_intent', 'general')
        needs_context = analysis_result.get('needs_context', False)
        key_points = analysis_result.get('key_points', [])
        exercise_ref = analysis_result.get('exercise_reference', {})

        # 如果是答案请求且有题目引用，直接构建包含题目的请求
        if user_intent == 'answer' and exercise_ref.get('has_exercise', False):
            return self._build_exercise_answer_request(original_input, exercise_ref)

        # 如果需要上下文但没有特定题目，构建包含关键点的请求
        elif needs_context and key_points:
            return self._build_context_aware_request(original_input, key_points)

        # 否则，使用大模型建议的优化或直接返回原输入
        suggested_enhancement = analysis_result.get('suggested_enhancement', '')
        if suggested_enhancement and suggested_enhancement != "直接回应用户输入":
            return suggested_enhancement

        return original_input

    def _build_exercise_answer_request(self, original_input: str, exercise_ref: Dict[str, Any]) -> str:
        """构建包含题目的答案请求"""
        exercise_content = str(exercise_ref.get('exercise_content', ''))
        exercise_topic = str(exercise_ref.get('exercise_topic', ''))

        if not exercise_content:
            return original_input

        enhanced_request = f"""
用户请求：{original_input}

需要解答的题目：
主题：{exercise_topic}
内容：
{exercise_content}

请针对以上题目提供完整的解答。
"""
        logger.info(f"已构建包含题目的答案请求，题目主题: {exercise_topic}")
        return enhanced_request.strip()

    def _build_context_aware_request(self, original_input: str, key_points: List[str]) -> str:
        """构建包含关键点的上下文感知请求"""
        if not key_points:
            return original_input

        # 安全处理关键点
        safe_key_points = [str(point) for point in key_points[:3]]
        context_summary = "\n".join([f"- {point}" for point in safe_key_points])

        enhanced_request = f"""
用户请求：{original_input}

相关上下文：
{context_summary}

请基于以上上下文回应用户请求。
"""
        return enhanced_request.strip()

    async def _fallback_enhancement(self, content: str, user_id: str) -> Dict[str, Any]:
        """回退到基础优化"""
        try:
            # 获取基础对话历史
            dialog_history = context_manager.get_dialog_history(user_id, limit=5)

            system_prompt = """请基于以下对话历史理解用户输入，并返回优化后的提示词。"""

            user_message = f"用户输入：{content}\n"
            if dialog_history:
                user_message += "\n最近对话：\n"
                for i, history in enumerate(dialog_history[-3:]):
                    user_input = str(history.get('user_input', ''))
                    agent_response = str(history.get('agent_response', ''))[:100]
                    user_message += f"{i + 1}. 用户: {user_input}\n"
                    user_message += f"   助手: {agent_response}...\n"

            user_message += "\n请优化用户输入："

            llm_client = self._get_llm_client()
            response = await llm_client.generate_response(system_prompt, user_message)

            enhanced_content = response.strip() if response and response.strip() else content

            return {
                "original_content": content,
                "enhanced_content": enhanced_content,
                "was_enhanced": enhanced_content != content,
                "context_analysis": {'success': False, 'error': 'fallback_used'},
                "analysis_confidence": 0.3,
                "target_exercise": None
            }

        except Exception as e:
            logger.error(f"回退优化也失败: {str(e)}")
            return {
                "original_content": content,
                "enhanced_content": content,
                "was_enhanced": False,
                "context_analysis": {'success': False, 'error': str(e)},
                "analysis_confidence": 0.1,
                "target_exercise": None
            }

    async def receive_user_request(self, request_type: str, content: str, user_id: str) -> Dict[str, Any]:
        """接收用户请求，使用大模型分析上下文"""
        self.current_user_id = user_id

        # 安全地记录日志
        original_preview = content[:50] + "..." if len(content) > 50 else content
        self.log_activity("接收用户原始请求", {
            "user_id": user_id,
            "request_type": request_type,
            "original_content": original_preview
        })

        # 使用大模型分析上下文并优化用户输入
        enhancement_result = await self.enhance_user_input_with_context(content, user_id)

        # 获取对话上下文
        conversation_context = context_manager.get_conversation_context(user_id) or {}
        dialog_history = context_manager.get_dialog_history(user_id, limit=10)

        # 构建请求对象
        request = {
            "type": request_type,
            "content": enhancement_result["enhanced_content"],
            "original_content": enhancement_result["original_content"],
            "user_id": user_id,
            "timestamp": self._get_timestamp(),
            "enhancement_info": {
                "was_enhanced": enhancement_result["was_enhanced"],
                "analysis_confidence": enhancement_result.get("analysis_confidence", 0.5),
                "context_analysis": enhancement_result.get("context_analysis", {})
            },
            "context": {
                "conversation_context": conversation_context,
                "recent_history": dialog_history,
                "learning_progress": context_manager.get_learning_progress(user_id) or {}
            },
            "target_exercise": enhancement_result.get("target_exercise")
        }

        # 转发给主代理
        return await self.forward_to_main_agent(request)

    async def save_conversation_result(self, user_id: str, request: Dict[str, Any], result: Dict[str, Any]):
        """保存对话结果到上下文"""
        try:
            question_id = None
            details = result.get('details', {})

            if 'questions' in details and details['questions']:
                first_question = details['questions'][0]
                question_id = first_question.get('question_id')
            elif 'exercise' in details:
                question_id = details['exercise'].get('question_id')

            # 保存对话历史
            dialog_data = {
                'user_input': str(request.get('original_content', '')),
                'agent_response': str(result.get('response', '')),
                'intent': str(result.get('detected_intent', 'unknown')),
                'topic': str(result.get('details', {}).get('topic', 'general')),
                'question_id': question_id,
                'session_id': f"session_{int(time.time())}"
            }
            context_manager.save_dialog_history(user_id, dialog_data)

            # 更新对话上下文
            current_context = context_manager.get_conversation_context(user_id) or {}

            current_context.update({
                'last_intent': str(result.get('detected_intent', 'unknown')),
                'last_topic': str(result.get('details', {}).get('topic', 'general')),
                'last_interaction_time': str(request.get('timestamp', '')),
                'interaction_count': current_context.get('interaction_count', 0) + 1
            })

            # 保存学习进度相关信息
            if result.get('detected_intent') == 'exercise' and 'details' in result:
                exercise_details = result['details']
                current_context['last_exercise_topic'] = str(exercise_details.get('topic', 'general'))
                current_context['last_exercise_type'] = str(exercise_details.get('type', 'unknown'))
                current_context['last_exercise_time'] = str(request.get('timestamp', ''))

                if 'questions' in exercise_details and exercise_details['questions']:
                    first_question = exercise_details['questions'][0]
                    description = first_question.get('content', {}).get('description', '')
                    current_context['last_question_preview'] = str(description)[:100]
                    current_context['last_question_id'] = first_question.get('question_id')
                elif 'exercise' in exercise_details:
                    description = exercise_details['exercise'].get('content', {}).get('description', '')
                    current_context['last_question_preview'] = str(description)[:100]
                    current_context['last_question_id'] = exercise_details['exercise'].get('question_id')

            context_manager.save_conversation_context(user_id, current_context)

            self.log_activity("对话上下文保存完成", {
                "user_id": user_id,
                "question_id": str(question_id) if question_id else "None",
                "intent": str(result.get('detected_intent', 'unknown'))
            })

        except Exception as e:
            logger.error(f"保存对话结果失败: {str(e)}")

    async def forward_to_main_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """转发优化后的请求给主代理"""
        self.log_activity("转发优化后的请求给主代理", {
            "request_type": str(request.get("type", "")),
            "was_enhanced": request["enhancement_info"]["was_enhanced"],
            "analysis_confidence": request["enhancement_info"].get("analysis_confidence", 0.5),
            "target_exercise_found": request.get("target_exercise") is not None
        })

        result = await self.main_agent.process(request)

        # 保存对话结果
        await self.save_conversation_result(request["user_id"], request, result)

        return result

    async def collect_and_return_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """收集并返回结果给用户"""
        self.log_activity("返回结果给用户", {
            "result_type": type(results).__name__,
            "detected_intent": str(results.get("detected_intent", "unknown"))
        })

        # 格式化返回结果
        formatted_result = {
            "success": True,
            "user_id": self.current_user_id,
            "response": str(results.get("response", "请求处理完成")),
            "details": results.get("details", {}),
            "suggestions": results.get("suggestions", []),
            "request_type": str(results.get("detected_intent", "unknown")),
            "processing_info": {
                "input_enhanced": results.get("enhancement_applied", False),
                "context_used": results.get("context_used", False),
                "analysis_confidence": results.get("enhancement_info", {}).get("analysis_confidence", 0.5),
                "target_exercise_used": results.get("target_exercise") is not None
            }
        }

        if "error" in results:
            formatted_result.update({
                "success": False,
                "error": str(results["error"])
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
        return datetime.now().isoformat()