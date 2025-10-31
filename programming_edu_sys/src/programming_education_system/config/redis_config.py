# src/programming_education_system/config/redis_config.py
"""
Redis配置
"""
import os

# Redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', None),
    'decode_responses': True
}

# 上下文配置
CONTEXT_CONFIG = {
    'max_history_length': 50,
    'context_ttl': 7 * 24 * 3600,  # 7天
    'learning_progress_ttl': 30 * 24 * 3600  # 30天
}