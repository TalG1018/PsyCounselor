"""
上下文长度管理器
实现128K token限制的智能上下文压缩和管理
支持滑动窗口、重要性评分、摘要压缩等多种策略
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import heapq
import logging

logger = logging.getLogger(__name__)

@dataclass
class ContextTurn:
    """对话轮次数据结构"""
    turn_id: int
    user_message: str
    ai_response: str
    timestamp: str
    importance_score: float = 0.0
    emotion_intensity: float = 0.0
    keywords: List[str] = None
    
    def get_total_length(self) -> int:
        """获取该轮次的总字符长度"""
        return len(self.user_message) + len(self.ai_response)
    
    def estimate_tokens(self, avg_chars_per_token: int = 4) -> int:
        """估算token数量（简化计算）"""
        return math.ceil(self.get_total_length() / avg_chars_per_token)

class ContextManager:
    """智能上下文管理器"""
    
    def __init__(self, 
                 max_tokens: int = 128000,  # 128K tokens
                 avg_chars_per_token: int = 4,
                 preserve_system_prompt: bool = True):
        """
        初始化上下文管理器
        
        Args:
            max_tokens: 最大token限制
            avg_chars_per_token: 平均每个token的字符数（中文约3-4个字符）
            preserve_system_prompt: 是否保留系统提示词
        """
        self.max_tokens = max_tokens
        self.avg_chars_per_token = avg_chars_per_token
        self.preserve_system_prompt = preserve_system_prompt
        self.context_window: List[ContextTurn] = []
        self.system_prompt_tokens = 200  # 系统提示词大约token数
        
    def add_turn(self, 
                 user_message: str, 
                 ai_response: str,
                 emotion_score: float = 0.0,
                 keywords: List[str] = None) -> None:
        """
        添加新的对话轮次
        
        Args:
            user_message: 用户消息
            ai_response: AI回复
            emotion_score: 情绪强度分数(0-1)
            keywords: 关键词列表
        """
        turn = ContextTurn(
            turn_id=len(self.context_window) + 1,
            user_message=user_message,
            ai_response=ai_response,
            timestamp=datetime.now().isoformat(),
            emotion_intensity=emotion_score,
            keywords=keywords or []
        )
        
        # 计算重要性分数
        turn.importance_score = self._calculate_importance(turn)
        
        self.context_window.append(turn)
        logger.debug(f"添加对话轮次 {turn.turn_id}，当前总轮次: {len(self.context_window)}")
        
        # 自动管理上下文长度
        self._manage_context_length()
    
    def _calculate_importance(self, turn: ContextTurn) -> float:
        """
        计算对话轮次的重要性分数
        综合考虑时间因素、情绪强度、关键词匹配度
        """
        # 时间衰减因子（越新的对话越重要）
        time_factor = 1.0
        
        # 情绪强度因子
        emotion_factor = 1.0 + turn.emotion_intensity * 0.5
        
        # 关键词重要性因子
        keyword_factor = 1.0
        important_keywords = ["危机", "自杀", "伤害", "紧急", "痛苦", "绝望"]
        if any(keyword in turn.user_message or keyword in turn.ai_response 
               for keyword in important_keywords):
            keyword_factor = 2.0
            
        # 长度因子（避免过短的无效对话占位）
        length_factor = min(turn.get_total_length() / 100, 2.0)
        
        return time_factor * emotion_factor * keyword_factor * length_factor
    
    def _manage_context_length(self) -> None:
        """管理上下文长度，确保不超过token限制"""
        if not self.context_window:
            return
            
        current_tokens = self.get_current_token_count()
        max_allowed_tokens = self._get_available_tokens()
        
        if current_tokens <= max_allowed_tokens:
            return  # 当前长度在限制内
            
        logger.info(f"上下文超出限制: {current_tokens} > {max_allowed_tokens} tokens")
        
        # 策略1: 移除最不重要的轮次
        self._remove_low_importance_turns(max_allowed_tokens)
        
        # 策略2: 如果还不够，进行摘要压缩
        if self.get_current_token_count() > max_allowed_tokens:
            self._compress_context_with_summarization(max_allowed_tokens)
    
    def _get_available_tokens(self) -> int:
        """获取可用于对话历史的token数量"""
        available = self.max_tokens
        if self.preserve_system_prompt:
            available -= self.system_prompt_tokens
        return available
    
    def get_current_token_count(self) -> int:
        """获取当前上下文的总token数"""
        if not self.context_window:
            return 0
        return sum(turn.estimate_tokens(self.avg_chars_per_token) 
                  for turn in self.context_window)
    
    def _remove_low_importance_turns(self, target_tokens: int) -> None:
        """移除低重要性的对话轮次"""
        if len(self.context_window) <= 2:  # 至少保留2轮
            return
            
        # 按重要性排序（升序）
        sorted_turns = sorted(self.context_window, key=lambda x: x.importance_score)
        
        # 移除低重要性的轮次直到满足token限制
        removed_count = 0
        for turn in sorted_turns[:-2]:  # 保留至少最后2轮
            if self.get_current_token_count() <= target_tokens:
                break
                
            self.context_window.remove(turn)
            removed_count += 1
            
        if removed_count > 0:
            logger.info(f"移除了 {removed_count} 个低重要性对话轮次")
            # 重新编号剩余轮次
            self._renumber_turns()
    
    def _compress_context_with_summarization(self, target_tokens: int) -> None:
        """使用摘要压缩策略"""
        if len(self.context_window) <= 3:  # 至少保留3轮不压缩
            return
            
        # 按时间顺序获取较早的轮次进行压缩
        early_turns = self.context_window[:-3]  # 保留最近3轮不压缩
        
        # 将早期轮次合并为摘要
        if early_turns:
            summary = self._create_summary_from_turns(early_turns)
            compressed_turn = ContextTurn(
                turn_id=0,  # 特殊标记为压缩轮次
                user_message="[历史对话摘要]",
                ai_response=summary,
                timestamp=early_turns[0].timestamp,
                importance_score=0.5,  # 较低重要性
                emotion_intensity=0.0
            )
            
            # 替换原来的早期轮次
            self.context_window = self.context_window[-3:]  # 保留最近3轮
            self.context_window.insert(0, compressed_turn)  # 在开头插入摘要
            
            logger.info("创建了历史对话摘要以节省token空间")
    
    def _create_summary_from_turns(self, turns: List[ContextTurn]) -> str:
        """从多个对话轮次创建摘要"""
        if not turns:
            return ""
            
        # 简单的摘要策略：提取关键词和主要情绪
        all_messages = []
        all_emotions = []
        all_keywords = []
        
        for turn in turns:
            all_messages.extend([turn.user_message, turn.ai_response])
            all_emotions.append(turn.emotion_intensity)
            if turn.keywords:
                all_keywords.extend(turn.keywords)
        
        # 创建摘要文本
        avg_emotion = sum(all_emotions) / len(all_emotions) if all_emotions else 0
        unique_keywords = list(set(all_keywords))[:5]  # 最多5个关键词
        
        summary = f"此前共{len(turns)}轮对话，"
        if unique_keywords:
            summary += f"主要涉及{', '.join(unique_keywords)}等话题，"
        summary += f"整体情绪倾向为{'积极' if avg_emotion > 0.5 else '消极'}。"
        
        return summary
    
    def _renumber_turns(self) -> None:
        """重新编号对话轮次"""
        for i, turn in enumerate(self.context_window):
            turn.turn_id = i + 1
    
    def get_formatted_context(self, max_turns: Optional[int] = None) -> str:
        """
        获取格式化的上下文字符串
        
        Args:
            max_turns: 最大返回轮次数（可选）
            
        Returns:
            格式化的上下文字符串
        """
        if not self.context_window:
            return ""
            
        # 如果指定了最大轮次数，则只取最近的轮次
        turns_to_use = self.context_window[-max_turns:] if max_turns else self.context_window
        
        context_parts = []
        for turn in turns_to_use:
            if turn.turn_id == 0:  # 压缩轮次
                context_parts.append(f"[历史摘要] {turn.ai_response}")
            else:
                context_parts.append(
                    f"第{turn.turn_id}轮（{turn.timestamp[:10]}）：\n"
                    f"用户：{turn.user_message}\n"
                    f"咨询师：{turn.ai_response}"
                )
        
        return "\n\n".join(context_parts)
    
    def get_statistics(self) -> Dict:
        """获取上下文统计信息"""
        if not self.context_window:
            return {
                "total_turns": 0,
                "total_tokens": 0,
                "compressed_turns": 0,
                "utilization_rate": 0.0
            }
            
        total_tokens = self.get_current_token_count()
        available_tokens = self._get_available_tokens()
        utilization = min(total_tokens / available_tokens, 1.0) if available_tokens > 0 else 0
        
        compressed_count = sum(1 for turn in self.context_window if turn.turn_id == 0)
        
        return {
            "total_turns": len(self.context_window),
            "total_tokens": total_tokens,
            "compressed_turns": compressed_count,
            "available_tokens": available_tokens,
            "utilization_rate": round(utilization * 100, 2),
            "max_limit": self.max_tokens
        }
    
    def clear_context(self) -> None:
        """清空上下文"""
        self.context_window.clear()
        logger.info("上下文已清空")

# 兼容性函数
def create_context_manager(max_tokens: int = 128000) -> ContextManager:
    """创建上下文管理器的工厂函数"""
    return ContextManager(max_tokens=max_tokens)

# 使用示例和测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建管理器
    cm = ContextManager(max_tokens=1000)  # 使用较小限制便于测试
    
    # 添加一些测试对话
    test_conversations = [
        ("我最近感觉很焦虑", "理解您的感受，焦虑是很常见的情绪反应。能具体说说是什么让您感到焦虑吗？"),
        ("工作压力很大，经常失眠", "工作压力确实会影响睡眠质量。您提到的失眠具体表现为怎样的情况？"),
        ("晚上总是睡不着，脑子里想很多事情", "失眠伴随思维活跃是典型的焦虑症状。这种情况持续多久了？"),
        ("大概有两个月了", "两个月的持续时间需要重视。除了睡眠问题，还有其他身体或情绪上的不适吗？"),
        ("食欲也不好，经常感到疲惫", "这些症状表明您的身心状态都需要关注。建议您考虑寻求专业的帮助。"),
    ]
    
    # 添加对话轮次
    for i, (user_msg, ai_resp) in enumerate(test_conversations):
        emotion_score = 0.3 + (i * 0.1)  # 逐步增加情绪强度
        cm.add_turn(user_msg, ai_resp, emotion_score=emotion_score)
        
        stats = cm.get_statistics()
        print(f"轮次 {i+1}: {stats['total_tokens']} tokens, "
              f"利用率: {stats['utilization_rate']}%")
    
    # 显示最终上下文
    print("\n=== 最终上下文 ===")
    print(cm.get_formatted_context())
    print(f"\n统计信息: {cm.get_statistics()}")
