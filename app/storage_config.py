"""
存储后端配置模块
支持动态切换SQLite和Redis存储后端
"""

import os
from enum import Enum
from typing import Type

class StorageBackend(Enum):
    """存储后端枚举"""
    SQLITE = "sqlite"
    REDIS = "redis"

class StorageConfig:
    """存储配置类"""
    # 默认使用Redis（如果可用）
    DEFAULT_BACKEND = StorageBackend.REDIS
    
    # 环境变量配置
    BACKEND_ENV_VAR = "MEMORY_STORAGE_BACKEND"
    REDIS_HOST_ENV_VAR = "REDIS_HOST"
    REDIS_PORT_ENV_VAR = "REDIS_PORT"
    
    @classmethod
    def get_backend(cls) -> StorageBackend:
        """获取当前配置的存储后端"""
        backend_str = os.getenv(cls.BACKEND_ENV_VAR, cls.DEFAULT_BACKEND.value)
        try:
            return StorageBackend(backend_str.lower())
        except ValueError:
            return cls.DEFAULT_BACKEND
    
    @classmethod
    def is_redis_available(cls) -> bool:
        """检查Redis是否可用"""
        try:
            import redis
            # 尝试连接测试
            client = redis.Redis(
                host=os.getenv(cls.REDIS_HOST_ENV_VAR, "localhost"),
                port=int(os.getenv(cls.REDIS_PORT_ENV_VAR, 6379)),
                socket_connect_timeout=2,
                socket_timeout=2
            )
            client.ping()
            return True
        except Exception:
            return False

# 存储后端工厂
class MemoryManagerFactory:
    """记忆管理器工厂类"""
    
    @staticmethod
    def get_memory_class() -> Type:
        """根据配置获取对应的记忆管理类"""
        backend = StorageConfig.get_backend()
        
        if backend == StorageBackend.REDIS:
            if StorageConfig.is_redis_available():
                from redis_memory import RedisConversationMemory
                return RedisConversationMemory
            else:
                print("警告: Redis不可用，回退到SQLite")
                from memory import ConversationMemory
                return ConversationMemory
        else:
            from memory import ConversationMemory
            return ConversationMemory
    
    @staticmethod
    def get_memory_instance(user_id: str):
        """获取记忆管理器实例"""
        memory_class = MemoryManagerFactory.get_memory_class()
        return memory_class(user_id)

# 便捷函数
def get_user_memory(user_id: str):
    """获取用户记忆管理器实例"""
    return MemoryManagerFactory.get_memory_instance(user_id)

def get_current_backend() -> str:
    """获取当前使用的存储后端"""
    memory_class = MemoryManagerFactory.get_memory_class()
    if "Redis" in memory_class.__name__:
        return "Redis"
    else:
        return "SQLite"