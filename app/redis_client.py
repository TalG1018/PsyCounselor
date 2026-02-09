"""
Redis配置和连接管理模块
提供Redis连接池和基础操作封装
"""

import redis
import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

class RedisConfig:
    """Redis配置类"""
    HOST = "localhost"
    PORT = 6379
    DB = 0
    PASSWORD = None
    DECODE_RESPONSES = True
    SOCKET_CONNECT_TIMEOUT = 5
    SOCKET_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 30
    
    # 连接池配置
    MAX_CONNECTIONS = 20
    CONNECTION_TIMEOUT = 10

class RedisManager:
    """Redis连接管理器（单例模式）"""
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._connect()
    
    def _connect(self):
        """建立Redis连接池"""
        try:
            self._pool = redis.ConnectionPool(
                host=RedisConfig.HOST,
                port=RedisConfig.PORT,
                db=RedisConfig.DB,
                password=RedisConfig.PASSWORD,
                decode_responses=RedisConfig.DECODE_RESPONSES,
                socket_connect_timeout=RedisConfig.SOCKET_CONNECT_TIMEOUT,
                socket_timeout=RedisConfig.SOCKET_TIMEOUT,
                health_check_interval=RedisConfig.HEALTH_CHECK_INTERVAL,
                max_connections=RedisConfig.MAX_CONNECTIONS
            )
            logger.info("Redis连接池初始化成功")
            
            # 测试连接
            self.test_connection()
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    def get_client(self) -> redis.Redis:
        """获取Redis客户端实例"""
        if not self._pool:
            self._connect()
        return redis.Redis(connection_pool=self._pool)
    
    def test_connection(self) -> bool:
        """测试Redis连接"""
        try:
            client = self.get_client()
            client.ping()
            logger.info("Redis连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Redis连接测试失败: {e}")
            return False
    
    def close(self):
        """关闭连接池"""
        if self._pool:
            self._pool.disconnect()
            logger.info("Redis连接池已关闭")

# 全局Redis管理器实例
redis_manager = RedisManager()

def get_redis_client() -> redis.Redis:
    """获取Redis客户端的便捷函数"""
    return redis_manager.get_client()

def serialize_data(data: Any) -> str:
    """序列化数据为JSON字符串"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"数据序列化失败: {e}")
        return str(data)

def deserialize_data(data: str) -> Any:
    """反序列化JSON字符串为Python对象"""
    try:
        if isinstance(data, str):
            return json.loads(data)
        return data
    except Exception as e:
        logger.error(f"数据反序列化失败: {e}")
        return data

def safe_execute(func, *args, **kwargs):
    """安全执行Redis操作，包含错误处理"""
    try:
        client = get_redis_client()
        return func(client, *args, **kwargs)
    except redis.ConnectionError as e:
        logger.error(f"Redis连接错误: {e}")
        raise Exception("无法连接到Redis服务，请检查Redis是否正在运行")
    except redis.TimeoutError as e:
        logger.error(f"Redis操作超时: {e}")
        raise Exception("Redis操作超时")
    except Exception as e:
        logger.error(f"Redis操作异常: {e}")
        raise Exception(f"Redis操作失败: {str(e)}")

# 便捷的Redis操作函数
def redis_set(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """设置键值对"""
    def _set(client, k, v, exp):
        serialized_value = serialize_data(v)
        result = client.set(k, serialized_value)
        if result and exp:
            client.expire(k, exp)
        return result
    return safe_execute(_set, key, value, expire)

def redis_get(key: str) -> Any:
    """获取键值"""
    def _get(client, k):
        value = client.get(k)
        if value is not None:
            return deserialize_data(value)
        return None
    return safe_execute(_get, key)

def redis_delete(key: str) -> bool:
    """删除键"""
    return safe_execute(lambda client, k: client.delete(k) > 0, key)

def redis_exists(key: str) -> bool:
    """检查键是否存在"""
    return safe_execute(lambda client, k: client.exists(k) > 0, key)

def redis_keys(pattern: str) -> List[str]:
    """根据模式查找键"""
    return safe_execute(lambda client, p: client.keys(p), pattern)