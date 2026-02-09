"""
对话记忆与心理画像管理模块（SQLite版）
支持多轮对话历史存储、检索、分析
"""

import sqlite3
import json
import hashlib
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter


class MemoryConfig:
    """记忆配置"""
    DB_PATH = "/root/lanyun-tmp/heart/data/memories.db"
    MAX_HISTORY = 5  # 保留最近5轮对话
    MAX_TOKENS_PER_MSG = 200
    
    @classmethod
    def ensure_dir(cls):
        import os
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)


class ConversationMemory:
    """
    用户对话记忆管理器（SQLite实现）
    线程安全，支持并发访问
    """
    
    _local = threading.local()
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        MemoryConfig.ensure_dir()
        self._init_db()
        self._ensure_user_exists()
    
    def _get_conn(self):
        """获取线程本地连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(MemoryConfig.DB_PATH, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 用户表（画像信息）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                total_chats INTEGER DEFAULT 0,
                total_risk_alerts INTEGER DEFAULT 0,
                common_topics TEXT DEFAULT '[]',  -- JSON数组
                last_active TEXT,
                emotion_trend TEXT DEFAULT '[]'   -- JSON数组，最近10次情绪
            )
        ''')
        
        # 对话表（历史记录）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                risk_level TEXT DEFAULT 'low',
                emotion_score REAL DEFAULT 0.0,
                references_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # 创建索引加速查询
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conv_user_time 
            ON conversations(user_id, timestamp DESC)
        ''')
        
        conn.commit()
    
    def _ensure_user_exists(self):
        """确保用户记录在数据库中存在"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (self.user_id,)
        )
        
        if cursor.fetchone() is None:
            # 新用户，创建记录
            cursor.execute('''
                INSERT INTO users (user_id, created_at, last_active)
                VALUES (?, ?, ?)
            ''', (
                self.user_id,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def add_conversation(self, query: str, response: str, risk_level: str,
                        emotion_score: float = 0.0, references: int = 0):
        """添加一轮对话"""
        # 截断内容
        query = query[:MemoryConfig.MAX_TOKENS_PER_MSG]
        response = response[:MemoryConfig.MAX_TOKENS_PER_MSG * 2]
        
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # 插入对话记录
        cursor.execute('''
            INSERT INTO conversations 
            (user_id, timestamp, query, response, risk_level, emotion_score, references_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (self.user_id, now, query, response, risk_level, emotion_score, references))
        
        # 更新用户统计
        cursor.execute('''
            UPDATE users 
            SET total_chats = total_chats + 1,
                last_active = ?,
                total_risk_alerts = total_risk_alerts + ?
            WHERE user_id = ?
        ''', (now, 1 if risk_level in ["high", "medium"] else 0, self.user_id))
        
        # 更新情绪趋势（JSON操作）
        self._update_emotion_trend(cursor, emotion_score, risk_level)
        
        # 更新关键词
        self._update_keywords(cursor, query)
        
        # 清理旧记录（只保留最近MAX_HISTORY条）
        self._cleanup_old_records(cursor)
        
        conn.commit()
    
    def _update_emotion_trend(self, cursor, score: float, risk: str):
        """更新情绪趋势（保留最近10次）"""
        cursor.execute(
            "SELECT emotion_trend FROM users WHERE user_id = ?",
            (self.user_id,)
        )
        row = cursor.fetchone()
        trend = json.loads(row[0]) if row and row[0] else []
        
        trend.append({
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "risk": risk
        })
        
        # 只保留最近10次
        if len(trend) > 10:
            trend = trend[-10:]
        
        cursor.execute(
            "UPDATE users SET emotion_trend = ? WHERE user_id = ?",
            (json.dumps(trend), self.user_id)
        )
    
    def _update_keywords(self, cursor, query: str):
        """提取并更新关键词"""
        keywords = self._extract_keywords(query)
        if not keywords:
            return
        
        cursor.execute(
            "SELECT common_topics FROM users WHERE user_id = ?",
            (self.user_id,)
        )
        row = cursor.fetchone()
        existing = json.loads(row[0]) if row and row[0] else []
        
        # 合并去重，保留最近10个
        new_topics = list(dict.fromkeys(existing + keywords))[:10]
        
        cursor.execute(
            "UPDATE users SET common_topics = ? WHERE user_id = ?",
            (json.dumps(new_topics), self.user_id)
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取心理关键词"""
        keyword_list = [
            "焦虑", "抑郁", "压力", "失眠", "工作", "学习", "家庭", "父母",
            "恋爱", "分手", "孤独", "自卑", "恐惧", "强迫", "社交", "人际",
            "考试", "失业", "离婚", "死亡", "痛苦", "绝望", "迷茫", "空虚"
        ]
        return [kw for kw in keyword_list if kw in text]
    
    def _cleanup_old_records(self, cursor):
        """只保留最近 N 条对话"""
        cursor.execute('''
            DELETE FROM conversations 
            WHERE id NOT IN (
                SELECT id FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ) AND user_id = ?
        ''', (self.user_id, MemoryConfig.MAX_HISTORY, self.user_id))
    
    def get_recent_context(self, max_turns: int = 3) -> str:
        """获取最近对话上下文"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query, response, timestamp 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (self.user_id, max_turns))
        
        rows = cursor.fetchall()
        if not rows:
            return ""
        
        # 按时间正序排列（最早的在前）
        rows = reversed(rows)
        
        context_parts = []
        for i, row in enumerate(rows, 1):
            turn = f"第{i}轮（{row['timestamp'][:10]}）：\n"
            turn += f"用户：{row['query']}\n"
            turn += f"咨询师：{row['response'][:100]}..."
            context_parts.append(turn)
        
        return "\n\n".join(context_parts)
    
    def get_profile_summary(self) -> str:
        """获取用户画像摘要"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT total_chats, total_risk_alerts, common_topics, emotion_trend
            FROM users WHERE user_id = ?
        ''', (self.user_id,))
        
        row = cursor.fetchone()
        if not row:
            return "新用户，暂无历史记录。"
        
        total, risk_count, topics_json, trend_json = row
        topics = json.loads(topics_json) if topics_json else []
        trend = json.loads(trend_json) if trend_json else []
        
        if total == 0:
            return "新用户，暂无历史记录。"
        
        summary = f"该用户已咨询{total}次。"
        if topics:
            summary += f"主要困扰领域：{', '.join(topics)}。"
        
        if risk_count > 0:
            summary += f"历史风险预警：{risk_count}次。"
        
        # 情绪趋势分析
        if len(trend) >= 3:
            recent_risks = [t for t in trend[-3:] if t['risk'] in ['high', 'medium']]
            if len(recent_risks) >= 2:
                summary += "近期情绪波动较大，需重点关注。"
        
        return summary
    
    def get_stats(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, COUNT(c.id) as conv_count
            FROM users u
            LEFT JOIN conversations c ON u.user_id = c.user_id
            WHERE u.user_id = ?
            GROUP BY u.user_id
        ''', (self.user_id,))
        
        row = cursor.fetchone()
        if not row:
            return {"user_id": self.user_id, "error": "User not found"}
        
        return {
            "user_id": self.user_id,
            "created_at": row['created_at'],
            "total_chats": row['total_chats'],
            "total_risk_alerts": row['total_risk_alerts'],
            "common_topics": json.loads(row['common_topics'] or '[]'),
            "last_active": row['last_active'],
            "stored_conversations": row['conv_count']
        }
    
    def close(self):
        """关闭连接（线程安全）"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


def get_user_memory(user_id: str) -> ConversationMemory:
    """工厂函数"""
    if not user_id or user_id == "anonymous":
        today = datetime.now().strftime("%Y%m%d")
        uid = f"anon_{today}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        return ConversationMemory(uid)
    
    return ConversationMemory(user_id)