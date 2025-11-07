# src/programming_education_system/utils/redis_context.py
"""
Redis上下文管理器
"""
import json
import pickle
from typing import Dict, Any, List, Optional
import redis
import logging
from datetime import datetime, timedelta
import time
logger = logging.getLogger(__name__)

class RedisContextManager:
    """Redis上下文管理器"""

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,  # 改为False，手动处理编码
            encoding='utf-8',
            socket_connect_timeout=5,
            socket_keepalive=True
        )
        self.context_ttl = 7 * 24 * 3600  # 上下文保存7天

    def _safe_serialize(self, data: Any) -> str:
        """安全序列化数据"""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            logger.warning(f"JSON序列化失败，使用pickle: {e}")
            return pickle.dumps(data).hex()

    def _safe_deserialize(self, data_str: str) -> Any:
        """安全反序列化数据"""
        if not data_str:
            return None

        try:
            # 先尝试JSON解析
            if isinstance(data_str, bytes):
                data_str = data_str.decode('utf-8')
            return json.loads(data_str)
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # 尝试pickle解析
                if isinstance(data_str, str):
                    data_bytes = bytes.fromhex(data_str)
                else:
                    data_bytes = data_str
                return pickle.loads(data_bytes)
            except Exception as e:
                logger.error(f"所有反序列化方法都失败: {e}")
                return None

    def save_conversation_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        """保存完整的对话上下文"""
        try:
            key = f"conversation:{user_id}"

            # 获取现有上下文并深度合并
            existing_context = self.get_conversation_context(user_id) or {}

            # 深度合并上下文（不是简单覆盖）
            merged_context = self._deep_merge_context(existing_context, context)
            merged_context['last_updated'] = datetime.now().isoformat()
            merged_context['update_count'] = merged_context.get('update_count', 0) + 1

            # 保存到Redis
            serialized_data = self._safe_serialize(merged_context)
            self.redis_client.setex(
                key,
                self.context_ttl,
                serialized_data
            )

            logger.debug(f"已保存用户 {user_id} 的完整上下文，大小: {len(serialized_data)} 字节")
            return True
        except Exception as e:
            logger.error(f"保存对话上下文失败: {e}")
            return False

    def _deep_merge_context(self, existing: Dict, new: Dict) -> Dict:
        """深度合并上下文数据"""
        result = existing.copy()

        for key, value in new.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = self._deep_merge_context(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # 合并列表（去重）
                result[key] = list(set(result[key] + value))
            else:
                # 直接覆盖
                result[key] = value

        return result

    def get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取完整的对话上下文"""
        try:
            key = f"conversation:{user_id}"
            context_data = self.redis_client.get(key)

            if context_data:
                context = self._safe_deserialize(context_data)
                logger.debug(f"已加载用户 {user_id} 的上下文，更新次数: {context.get('update_count', 0)}")
                return context
            return None
        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            return None

    def save_dialog_history(self, user_id: str, dialog: Dict[str, Any]) -> bool:
        """保存完整的对话历史记录"""
        try:
            key = f"dialog_history:{user_id}"

            # 构建完整的对话数据
            dialog_data = {
                'timestamp': datetime.now().isoformat(),
                'timestamp_epoch': time.time(),
                'user_input': dialog.get('user_input', ''),
                'agent_response': dialog.get('agent_response', ''),
                'intent': dialog.get('intent', 'unknown'),
                'topic': dialog.get('topic', 'general'),
                'question_id': dialog.get('question_id'),  # 新增：关联题目ID
                'session_id': dialog.get('session_id', f"session_{int(time.time())}")
            }

            # 使用列表保存最近的对话历史（最多保存100条）
            serialized_dialog = self._safe_serialize(dialog_data)
            self.redis_client.lpush(key, serialized_dialog)
            self.redis_client.ltrim(key, 0, 99)  # 只保留最近100条
            self.redis_client.expire(key, self.context_ttl)

            logger.debug(f"已保存用户 {user_id} 的对话历史，当前对话主题: {dialog_data['topic']}")
            return True
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")
            return False

    def get_dialog_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取完整的对话历史记录"""
        try:
            key = f"dialog_history:{user_id}"
            history_data = self.redis_client.lrange(key, 0, limit - 1)

            history = []
            for item in history_data:
                try:
                    dialog = self._safe_deserialize(item)
                    if dialog:
                        history.append(dialog)
                except Exception as e:
                    logger.warning(f"解析对话历史项失败: {e}")
                    continue

            # 按时间顺序排序（最旧的在前面）
            history.sort(key=lambda x: x.get('timestamp_epoch', 0))

            logger.debug(f"已加载用户 {user_id} 的 {len(history)} 条对话历史")
            return history
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []

    def get_recent_exercises(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的练习题目"""
        try:
            history = self.get_dialog_history(user_id, limit=50)  # 获取更多历史用于筛选
            exercises = []

            for dialog in history:
                if dialog.get('intent') == 'exercise' and 'question_id' in dialog:
                    exercises.append({
                        'question_id': dialog['question_id'],
                        'timestamp': dialog['timestamp'],
                        'topic': dialog.get('topic', 'general'),
                        'user_input': dialog.get('user_input', '')[:100]
                    })

            # 按时间倒序排列（最新的在前面）
            exercises.sort(key=lambda x: x.get('timestamp_epoch', 0), reverse=True)
            return exercises[:limit]
        except Exception as e:
            logger.error(f"获取最近练习失败: {e}")
            return []

    def save_learning_progress(self, user_id: str, progress: Dict[str, Any]) -> bool:
        """保存学习进度"""
        try:
            key = f"learning_progress:{user_id}"
            
            # 获取现有进度
            existing_progress = self.get_learning_progress(user_id) or {}
            
            # 合并进度数据
            merged_progress = {**existing_progress, **progress}
            merged_progress['last_updated'] = datetime.now().isoformat()
            
            # 保存到Redis
            self.redis_client.setex(
                key, 
                self.context_ttl, 
                json.dumps(merged_progress, ensure_ascii=False)
            )
            return True
        except Exception as e:
            logger.error(f"保存学习进度失败: {e}")
            return False
    
    def get_learning_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取学习进度"""
        try:
            key = f"learning_progress:{user_id}"
            progress_str = self.redis_client.get(key)
            if progress_str:
                return json.loads(progress_str)
            return None
        except Exception as e:
            logger.error(f"获取学习进度失败: {e}")
            return None
    
    def clear_user_data(self, user_id: str) -> bool:
        """清除用户所有数据"""
        try:
            keys = [
                f"conversation:{user_id}",
                f"dialog_history:{user_id}", 
                f"learning_progress:{user_id}"
            ]
            self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"清除用户数据失败: {e}")
            return False

# 全局上下文管理器实例
context_manager = RedisContextManager()