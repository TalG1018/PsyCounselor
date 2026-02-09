import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # 使用中文情感分析模型
        self.model_name = "uer/roberta-base-finetuned-chinanews-chinese"
        
        # 优先使用关键词分析，模型作为增强
        self.use_keyword_first = True
        self.tokenizer = None
        self.model = None
        
        # 立即启用关键词分析（避免网络问题）
        logger.info("使用关键词优先的情绪分析模式")
        
        # 可选：在后台尝试加载模型（非阻塞）
        # 这里我们暂时不实现后台加载，保持简单稳定
            
        # 情绪标签映射
        self.emotion_labels = ['愤怒', '厌恶', '恐惧', '快乐', '悲伤', '惊讶']
        
    def analyze_emotion(self, text):
        """分析文本情绪"""
        # 优先使用关键词分析（更快更稳定）
        if self.use_keyword_first:
            return self._fallback_analysis(text)
        
        # 如果模型可用，使用模型分析
        if self.model and self.tokenizer:
            try:
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(self.device)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    predicted_class = torch.argmax(probabilities, dim=-1).item()
                    
                    return {
                        "emotion": self.emotion_labels[predicted_class],
                        "confidence": float(probabilities[0][predicted_class].item()),
                        "all_probabilities": {
                            label: float(prob) for label, prob in zip(self.emotion_labels, probabilities[0].tolist())
                        }
                    }
            except Exception as e:
                logger.warning(f"Model analysis failed, falling back to keyword analysis: {e}")
        
        # 备用方案
        return self._fallback_analysis(text)
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                
                return {
                    "emotion": self.emotion_labels[predicted_class],
                    "confidence": float(probabilities[0][predicted_class].item()),
                    "all_probabilities": {
                        label: float(prob) for label, prob in zip(self.emotion_labels, probabilities[0].tolist())
                    }
                }
        except Exception as e:
            logger.error(f"Error in emotion analysis: {e}")
            return self._fallback_analysis(text)
    
    def _fallback_analysis(self, text):
        """备用分析方法 - 基于关键词的情感分析"""
        # 更丰富的关键词词典
        emotion_keywords = {
            '愤怒': ['生气', '愤怒', '恼火', '暴怒', '愤慨', '气死我了', '火大', '怒火', '发火', '憋屈'],
            '厌恶': ['讨厌', '厌恶', '恶心', '反感', '嫌弃', '烦死了', '受不了', '厌烦', '腻烦', '作呕'],
            '恐惧': ['害怕', '恐惧', '担心', '焦虑', '恐慌', '紧张', '不安', '担忧', '忐忑', '胆怯'],
            '快乐': ['开心', '快乐', '高兴', '喜悦', '愉快', '兴奋', '满意', '欣喜', '欢乐', '舒畅', '心情不错'],
            '悲伤': ['伤心', '悲伤', '难过', '沮丧', '忧郁', '失望', '痛苦', '郁闷', '低落', '心酸'],
            '惊讶': ['惊讶', '震惊', '意外', '吃惊', '诧异', '没想到', '哇', '天哪', '不可思议', '惊呆']
        }
        
        scores = {emotion: 0 for emotion in emotion_keywords.keys()}
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    scores[emotion] += 1
        
        dominant_emotion = max(scores, key=scores.get)
        total_score = sum(scores.values())
        
        if total_score == 0:
            return {"emotion": "中性", "confidence": 0.5, "all_probabilities": {}}
        
        confidence = scores[dominant_emotion] / total_score
        
        return {
            "emotion": dominant_emotion,
            "confidence": confidence,
            "all_probabilities": {k: v/total_score if total_score > 0 else 0 for k, v in scores.items()}
        }

class EmotionTracker:
    def __init__(self, data_dir="/root/lanyun-tmp/heart/data"):
        self.analyzer = EmotionAnalyzer()
        self.data_dir = data_dir
        self.emotion_history_file = os.path.join(data_dir, "emotion_history.json")
        self.emotion_history = self.load_emotion_history()
    
    def load_emotion_history(self):
        """加载情绪历史数据"""
        try:
            if os.path.exists(self.emotion_history_file):
                import json
                with open(self.emotion_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading emotion history: {e}")
            return {}
    
    def save_emotion_history(self):
        """保存情绪历史数据"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            import json
            with open(self.emotion_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.emotion_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving emotion history: {e}")
    
    def track_user_emotion(self, user_id, text):
        """追踪用户情绪变化"""
        emotion_result = self.analyzer.analyze_emotion(text)
        
        if user_id not in self.emotion_history:
            self.emotion_history[user_id] = []
        
        self.emotion_history[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "emotion": emotion_result
        })
        
        # 保持历史记录在合理范围内
        if len(self.emotion_history[user_id]) > 100:
            self.emotion_history[user_id] = self.emotion_history[user_id][-100:]
        
        self.save_emotion_history()
        return emotion_result
    
    def get_emotion_trend(self, user_id, limit=20):
        """获取用户情绪趋势"""
        if user_id not in self.emotion_history:
            return []
        
        # 获取最近的记录
        recent_emotions = self.emotion_history[user_id][-limit:]
        
        trend_data = []
        for record in recent_emotions:
            trend_data.append({
                "time": record["timestamp"],
                "emotion": record["emotion"]["emotion"],
                "confidence": record["emotion"]["confidence"]
            })
        
        return trend_data
    
    def get_emotion_summary(self, user_id):
        """获取用户情绪总结"""
        if user_id not in self.emotion_history or not self.emotion_history[user_id]:
            return {"message": "暂无情绪数据"}
        
        emotions = [record["emotion"]["emotion"] for record in self.emotion_history[user_id]]
        confidences = [record["emotion"]["confidence"] for record in self.emotion_history[user_id]]
        
        # 统计最常见的几种情绪
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        most_common_emotion = max(emotion_counts, key=emotion_counts.get)
        avg_confidence = np.mean(confidences)
        
        return {
            "most_common_emotion": most_common_emotion,
            "emotion_frequency": emotion_counts,
            "average_confidence": float(avg_confidence),
            "total_interactions": len(emotions)
        }
    
    def get_emotion_statistics(self, user_id, days=7):
        """获取用户情绪统计数据"""
        if user_id not in self.emotion_history:
            return {"message": "暂无情绪数据"}
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_records = [
            record for record in self.emotion_history[user_id]
            if datetime.fromisoformat(record["timestamp"]) >= cutoff_date
        ]
        
        if not recent_records:
            return {"message": f"最近{days}天无情绪数据"}
        
        # 按情绪分组统计
        emotion_stats = {}
        daily_stats = {}
        
        for record in recent_records:
            emotion = record["emotion"]["emotion"]
            date = datetime.fromisoformat(record["timestamp"]).date().isoformat()
            
            # 情绪统计
            emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1
            
            # 日统计
            if date not in daily_stats:
                daily_stats[date] = {}
            daily_stats[date][emotion] = daily_stats[date].get(emotion, 0) + 1
        
        return {
            "period_days": days,
            "total_records": len(recent_records),
            "emotion_distribution": emotion_stats,
            "daily_trends": daily_stats
        }