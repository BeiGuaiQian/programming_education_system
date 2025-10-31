# src/programming_education_system/utils/context_manager.py
"""
统一的上下文管理器选择器
"""
import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

def get_context_manager():
    """根据环境选择上下文管理器"""
    use_redis = os.getenv('USE_REDIS', 'true').lower() == 'true'
    
    if use_redis:
        try:
            from .redis_context import RedisContextManager
            manager = RedisContextManager(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=os.getenv('REDIS_PASSWORD', None)
            )
            # 测试连接
            manager.redis_client.ping()
            logger.info("✅ Redis上下文管理器已启用并连接成功")
            return manager
        except Exception as e:
            logger.error(f"❌ Redis连接失败，回退到SQLite: {e}")
    
    # 回退到SQLite
    try:
        from .sqlite_context import SQLiteContextManager
        logger.info("✅ SQLite上下文管理器已启用")
        return SQLiteContextManager()
    except Exception as e:
        logger.warning(f"❌ SQLite不可用，回退到内存: {e}")
        from .memory_context import MemoryContextManager
        logger.info("✅ 内存上下文管理器已启用")
        return MemoryContextManager()

# 全局上下文管理器
context_manager = get_context_manager()