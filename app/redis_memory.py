"""
Redis版对话记忆与心理画像管理模块
支持多轮对话历史存储、检索、分析
采用Redis高性能键值存储替代SQLite
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter

from redis_client import (
    get_redis_client, redis_set, redis_get, redis_exists, 
    redis_delete, redis_keys, safe_execute
)

# 配置日志
logger = logging.getLogger(__name__)

class RedisMemoryConfig:
    """Redis记忆配置"""
    # 数据保留策略
    MAX_HISTORY = 5  # 保留最近5轮对话
    MAX_TOKENS_PER_MSG = 200
    EMOTION_TREND_SIZE = 10  # 情绪趋势保留条数
    
    # Redis键名前缀
    USER_PROFILE_PREFIX = "user:{}:profile"
    USER_CONVERSATIONS_PREFIX = "user:{}:conversations"
    USER_TOPICS_PREFIX = "user:{}:topics"
    USER_EMOTIONS_PREFIX = "user:{}:emotions"
    
    # 过期时间设置（秒）
    PROFILE_EXPIRE = 86400 * 30  # 30天
    CONVERSATIONS_EXPIRE = 86400 * 7  # 7天
    TOPICS_EXPIRE = 86400 * 30  # 30天
    EMOTIONS_EXPIRE = 86400 * 30  # 30天

class RedisConversationMemory:
    """
    用户对话记忆管理器（Redis实现）
    高性能、支持高并发访问
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.config = RedisMemoryConfig()
        
        # 生成Redis键名
        self.profile_key = self.config.USER_PROFILE_PREFIX.format(user_id)
        self.conv_key = self.config.USER_CONVERSATIONS_PREFIX.format(user_id)
        self.topics_key = self.config.USER_TOPICS_PREFIX.format(user_id)
        self.emotions_key = self.config.USER_EMOTIONS_PREFIX.format(user_id)
        
        # 确保用户存在
        self._ensure_user_exists()
    
    def _ensure_user_exists(self):
        """确保用户记录在Redis中存在"""
        # 检查用户是否已存在（通过检查某个字段）
        def _check_user_exists(client):
            return client.hexists(self.profile_key, "user_id")
        
        user_exists = safe_execute(_check_user_exists)
        
        if not user_exists:
            # 新用户，创建记录
            def _create_user(client):
                pipe = client.pipeline()
                pipe.hset(self.profile_key, "user_id", self.user_id)
                pipe.hset(self.profile_key, "created_at", datetime.now().isoformat())
                pipe.hset(self.profile_key, "total_chats", 0)
                pipe.hset(self.profile_key, "total_risk_alerts", 0)
                pipe.hset(self.profile_key, "last_active", datetime.now().isoformat())
                pipe.expire(self.profile_key, self.config.PROFILE_EXPIRE)
                pipe.execute()
            
            safe_execute(_create_user)
            logger.info(f"创建新用户记录: {self.user_id}")
    
    def add_conversation(self, query: str, response: str, risk_level: str,
                        emotion_score: float = 0.0, references: int = 0):
        """添加一轮对话"""
        try:
            # 截断内容
            query = query[:self.config.MAX_TOKENS_PER_MSG]
            response = response[:self.config.MAX_TOKENS_PER_MSG * 2]
            
            # 准备对话记录
            conversation_record = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": response,
                "risk_level": risk_level,
                "emotion_score": emotion_score,
                "references_count": references
            }
            
            # 使用管道执行多个操作，提高性能
            def _add_conversation(client):
                pipe = client.pipeline()
                
                # 1. 添加对话记录到列表（左侧插入）
                pipe.lpush(self.conv_key, json.dumps(conversation_record, ensure_ascii=False))
                
                # 2. 修剪列表，只保留最近N条记录
                pipe.ltrim(self.conv_key, 0, self.config.MAX_HISTORY - 1)
                
                # 3. 更新用户统计数据
                pipe.hincrby(self.profile_key, "total_chats", 1)
                pipe.hset(self.profile_key, "last_active", datetime.now().isoformat())
                
                if risk_level in ["high", "medium"]:
                    pipe.hincrby(self.profile_key, "total_risk_alerts", 1)
                
                # 4. 更新情绪趋势
                self._update_emotion_trend_pipe(pipe, emotion_score, risk_level)
                
                # 5. 更新关键词
                self._update_keywords_pipe(pipe, query)
                
                # 6. 设置过期时间
                pipe.expire(self.conv_key, self.config.CONVERSATIONS_EXPIRE)
                pipe.expire(self.profile_key, self.config.PROFILE_EXPIRE)
                
                # 执行所有操作
                pipe.execute()
            
            safe_execute(_add_conversation)
            logger.debug(f"添加对话记录成功: user={self.user_id}")
            
        except Exception as e:
            logger.error(f"添加对话记录失败: {e}")
            raise
    
    def _update_emotion_trend_pipe(self, pipe, score: float, risk: str):
        """使用管道更新情绪趋势"""
        emotion_record = {
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "risk": risk
        }
        
        # 添加新的情绪记录
        pipe.lpush(self.emotions_key, json.dumps(emotion_record, ensure_ascii=False))
        # 只保留最近N条
        pipe.ltrim(self.emotions_key, 0, self.config.EMOTION_TREND_SIZE - 1)
        # 设置过期时间
        pipe.expire(self.emotions_key, self.config.EMOTIONS_EXPIRE)
    
    def _update_keywords_pipe(self, pipe, query: str):
        """使用管道更新关键词"""
        keywords = self._extract_keywords(query)
        if keywords:
            # 添加关键词到集合
            for keyword in keywords:
                pipe.sadd(self.topics_key, keyword)
            # 限制集合大小（保留最近的不同关键词）
            pipe.expire(self.topics_key, self.config.TOPICS_EXPIRE)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取心理关键词"""
        keyword_list = [
            "焦虑", "抑郁", "压力", "失眠", "工作", "学习", "家庭", "父母",
            "恋爱", "分手", "孤独", "自卑", "恐惧", "强迫", "社交", "人际",
            "考试", "失业", "离婚", "死亡", "痛苦", "绝望", "迷茫", "空虚"
        ]
        return [kw for kw in keyword_list if kw in text]
    
    def get_recent_context(self, max_turns: int = 3) -> str:
        """获取最近对话上下文"""
        try:
            def _get_context(client):
                # 获取最近几轮对话（右侧取，即最新的在前面）
                conv_data = client.lrange(self.conv_key, 0, max_turns - 1)
                return [json.loads(conv) for conv in conv_data] if conv_data else []
            
            conversations = safe_execute(_get_context)
            
            if not conversations:
                return ""
            
            # 按时间正序排列（最早的在前）
            conversations.reverse()
            
            context_parts = []
            for i, conv in enumerate(conversations, 1):
                timestamp = conv['timestamp'][:10]
                turn = f"第{i}轮（{timestamp}）：\n"
                turn += f"用户：{conv['query']}\n"
                turn += f"咨询师：{conv['response'][:100]}..."
                context_parts.append(turn)
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            return ""
    
    def get_profile_summary(self) -> str:
        """获取用户画像摘要"""
        try:
            profile = redis_get(self.profile_key)
            if not profile:
                return "新用户，暂无历史记录。"
            
            total_chats = profile.get("total_chats", 0)
            if total_chats == 0:
                return "新用户，暂无历史记录。"
            
            risk_count = profile.get("total_risk_alerts", 0)
            topics = profile.get("common_topics", [])
            emotions = profile.get("emotion_trend", [])
            
            summary = f"该用户已咨询{total_chats}次。"
            
            # 获取关键词
            def _get_topics(client):
                return list(client.smembers(self.topics_key))
            
            topic_list = safe_execute(_get_topics)
            if topic_list:
                summary += f"主要困扰领域：{', '.join(list(topic_list)[:5])}。"
            
            if risk_count > 0:
                summary += f"历史风险预警：{risk_count}次。"
            
            # 情绪趋势分析
            if len(emotions) >= 3:
                recent_emotions = emotions[-3:] if isinstance(emotions, list) else []
                recent_risks = [e for e in recent_emotions 
                              if isinstance(e, dict) and e.get('risk') in ['high', 'medium']]
                if len(recent_risks) >= 2:
                    summary += "近期情绪波动较大，需重点关注。"
            
            return summary
            
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
            return "获取用户信息失败。"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            def _get_stats(client):
                # 获取用户基本信息（HASH类型）
                profile_data = client.hgetall(self.profile_key)
                if not profile_data:
                    return {"user_id": self.user_id, "error": "User not found"}
                
                # 获取对话数量
                conv_count = client.llen(self.conv_key)
                
                # 获取关键词数量
                topic_count = client.scard(self.topics_key)
                
                # 获取情绪记录数量
                emotion_count = client.llen(self.emotions_key)
                
                return {
                    "user_id": profile_data.get("user_id", self.user_id),
                    "created_at": profile_data.get("created_at", ""),
                    "total_chats": int(profile_data.get("total_chats", 0)),
                    "total_risk_alerts": int(profile_data.get("total_risk_alerts", 0)),
                    "common_topics_count": topic_count,
                    "last_active": profile_data.get("last_active", ""),
                    "stored_conversations": conv_count,
                    "emotion_records": emotion_count
                }
            
            return safe_execute(_get_stats)
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"user_id": self.user_id, "error": str(e)}
    
    def clear_history(self):
        """清空用户历史记录"""
        try:
            def _clear_history(client):
                pipe = client.pipeline()
                pipe.delete(self.conv_key)
                pipe.delete(self.topics_key)
                pipe.delete(self.emotions_key)
                pipe.hset(self.profile_key, "total_chats", 0)
                pipe.hset(self.profile_key, "total_risk_alerts", 0)
                pipe.execute()
            
            safe_execute(_clear_history)
            logger.info(f"清空用户历史记录: {self.user_id}")
            
        except Exception as e:
            logger.error(f"清空历史记录失败: {e}")
            raise

def get_redis_user_memory(user_id: str) -> RedisConversationMemory:
    """Redis记忆管理器工厂函数"""
    if not user_id or user_id == "anonymous":
        today = datetime.now().strftime("%Y%m%d")
        uid = f"anon_{today}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        return RedisConversationMemory(uid)
    
    return RedisConversationMemory(user_id)

# 兼容性函数，保持与原SQLite版本接口一致
def get_user_memory(user_id: str):
    """获取用户记忆管理器（自动选择Redis版本）"""
    return get_redis_user_memory(user_id)