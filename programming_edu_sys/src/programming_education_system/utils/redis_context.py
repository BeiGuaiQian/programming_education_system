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

logger = logging.getLogger(__name__)

class RedisContextManager:
    """Redis上下文管理器"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.redis_client = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            password=password,
            decode_responses=True
        )
        self.context_ttl = 7 * 24 * 3600  # 上下文保存7天
    
    def save_conversation_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        """保存对话上下文"""
        try:
            key = f"conversation:{user_id}"
            
            # 获取现有上下文
            existing_context = self.get_conversation_context(user_id) or {}
            
            # 合并上下文
            merged_context = {**existing_context, **context}
            merged_context['last_updated'] = datetime.now().isoformat()
            
            # 保存到Redis
            self.redis_client.setex(
                key, 
                self.context_ttl, 
                json.dumps(merged_context, ensure_ascii=False)
            )
            return True
        except Exception as e:
            logger.error(f"保存对话上下文失败: {e}")
            return False
    
    def get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取对话上下文"""
        try:
            key = f"conversation:{user_id}"
            context_str = self.redis_client.get(key)
            if context_str:
                return json.loads(context_str)
            return None
        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            return None
    
    def save_dialog_history(self, user_id: str, dialog: Dict[str, Any]) -> bool:
        """保存对话历史记录"""
        try:
            key = f"dialog_history:{user_id}"
            
            # 序列化对话数据
            dialog_data = {
                'timestamp': datetime.now().isoformat(),
                'user_input': dialog.get('user_input', ''),
                'agent_response': dialog.get('agent_response', ''),
                'intent': dialog.get('intent', 'unknown'),
                'topic': dialog.get('topic', 'general')
            }
            
            # 使用列表保存最近的对话历史（最多保存50条）
            self.redis_client.lpush(key, json.dumps(dialog_data, ensure_ascii=False))
            self.redis_client.ltrim(key, 0, 49)  # 只保留最近50条
            self.redis_client.expire(key, self.context_ttl)
            
            return True
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")
            return False
    
    def get_dialog_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取对话历史记录"""
        try:
            key = f"dialog_history:{user_id}"
            history_data = self.redis_client.lrange(key, 0, limit - 1)
            
            history = []
            for item in history_data:
                try:
                    history.append(json.loads(item))
                except json.JSONDecodeError:
                    continue
            
            return history
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
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