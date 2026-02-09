"""
危机识别与安全干预模块（中文情感增强版）
本地部署 uer/roberta-base-finetuned-jd-binary-chinese
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from transformers import pipeline


class CrisisConfig:
    """配置类"""
    LOG_FILE = "/root/lanyun-tmp/heart/data/crisis_alerts.log"
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # 本地模型路径
    LOCAL_BERT_PATH = "/root/lanyun-tmp/heart/models/crisis_bert"


class CrisisDetector:
    """
    双重危机检测器：关键词检测 + 中文BERT语义分析
    """
    
    # 高危关键词库
    HIGH_RISK_KEYWORDS = [
        "自杀", "想死", "不想活", "结束生命", "跳楼", "割腕", "安眠药",
        "活着没意义", "不如死了", "想消失", "不想存在", "自残", 
        "结束这一切", "了结", "上吊", "喝药", "跳河", "烧炭", "解脱",
        "再见了", "遗言", "处理后事"
    ]
    
    # 中危关键词库
    MEDIUM_RISK_KEYWORDS = [
        "很痛苦", "绝望", "活着好累", "看不到希望", "没人关心我",
        "想离开", "熬不下去了", "太难受了", "活着没意思",
        "迷茫", "无助", "孤独", "空虚", "厌世", "活不下去",
        "没人在乎", "没意义", "撑不住", "崩溃"
    ]
    
    def __init__(self, use_semantic: bool = True):  # 默认启用语义分析
        self.use_semantic = use_semantic
        self.emotion_analyzer = None
        self.logger = self._setup_logger()
        
        # 加载中文BERT情感分析模型（本地）
        if use_semantic and os.path.exists(CrisisConfig.LOCAL_BERT_PATH):
            try:
                print(f"正在加载本地中文情感模型: {CrisisConfig.LOCAL_BERT_PATH}")
                self.emotion_analyzer = pipeline(
                    "sentiment-analysis",
                    model=CrisisConfig.LOCAL_BERT_PATH,
                    tokenizer=CrisisConfig.LOCAL_BERT_PATH,
                    device="cpu",
                    trust_remote_code=True
                )
                print("✅ 中文BERT情感模型加载完成（本地CPU）")
            except Exception as e:
                print(f"⚠️ BERT模型加载失败，降级为纯关键词检测: {e}")
                self.use_semantic = False
        elif use_semantic:
            print(f"⚠️ 本地模型路径不存在: {CrisisConfig.LOCAL_BERT_PATH}")
            print("   将仅使用关键词检测（请确认模型已下载到该路径）")
            self.use_semantic = False
        else:
            print("✅ 危机检测模块就绪（纯关键词检测模式）")
    
    def _setup_logger(self) -> logging.Logger:
        """配置审计日志"""
        logger = logging.getLogger("CrisisDetector")
        logger.setLevel(logging.WARNING)
        
        if not logger.handlers:
            fh = logging.FileHandler(CrisisConfig.LOG_FILE, encoding='utf-8')
            fh.setLevel(logging.WARNING)
            ch = logging.StreamHandler()
            ch.setLevel(logging.WARNING)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            logger.addHandler(fh)
            logger.addHandler(ch)
            
        return logger
    
    def detect(self, text: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        执行危机检测
        """
        if not text or len(text.strip()) == 0:
            return {
                "level": "low",
                "score": 0.0,
                "reason": "空输入",
                "needs_intervention": False,
                "keywords_found": [],
                "semantic_score": 0.0
            }
        
        text_lower = text.lower()
        
        # ========== Level 1: 关键词快速检测 ==========
        high_matches = [kw for kw in self.HIGH_RISK_KEYWORDS if kw in text_lower]
        medium_matches = [kw for kw in self.MEDIUM_RISK_KEYWORDS if kw in text_lower]
        
        if high_matches:
            score = 0.9 + min(len(high_matches) * 0.02, 0.09)
            reason = f"检测到高危关键词: {', '.join(high_matches[:3])}"
            
            self.logger.warning(
                f"[高危检测] User: {user_id[:8]}... | "
                f"内容: {text[:50]}... | "
                f"关键词: {high_matches} | "
                f"时间: {datetime.now().isoformat()}"
            )
            
            return {
                "level": "high",
                "score": score,
                "reason": reason,
                "needs_intervention": True,
                "keywords_found": high_matches,
                "semantic_score": 0.0,
                "intervention_type": "immediate"
            }
        
        # ========== Level 2: BERT语义深度分析 ==========
        semantic_score = 0.0
        semantic_label = ""
        
        if self.use_semantic and self.emotion_analyzer:
            try:
                result = self.emotion_analyzer(text[:512])[0]
                label = result['label']
                confidence = result['score']
                
                # uer/roberta-base-finetuned-jd-binary-chinese 输出格式:
                # LABEL_0 = 负面(差评), LABEL_1 = 正面(好评)
                if '0' in label or 'negative' in label.lower():
                    semantic_score = confidence
                    semantic_label = "negative"
                else:
                    semantic_score = 1 - confidence
                
                print(f"🔍 BERT分析: {label} ({confidence:.3f}) -> 负面分数: {semantic_score:.3f}")
                
            except Exception as e:
                self.logger.error(f"BERT分析失败: {e}")
        
        # ========== Level 3: 综合判定 ==========
        # 如果BERT检测到强烈负面情绪 + 有风险词汇
        risk_patterns = ["死", "离开", "痛苦", "绝望", "结束", "消失", "活不下去"]
        pattern_bonus = sum(0.15 for p in risk_patterns if p in text)
        
        final_semantic_score = min(semantic_score + pattern_bonus, 1.0)
        
        # 中危判定：关键词 或 BERT负面程度高(>0.7)
        if medium_matches or final_semantic_score > 0.7:
            keyword_score = 0.6 + min(len(medium_matches) * 0.05, 0.2) if medium_matches else 0.0
            bert_score = final_semantic_score * 0.85 if final_semantic_score > 0.7 else 0.0
            
            score = max(keyword_score, bert_score, 0.6)
            
            reason_parts = []
            if medium_matches:
                reason_parts.append(f"关键词: {', '.join(medium_matches[:3])}")
            if final_semantic_score > 0.7:
                reason_parts.append(f"情感分析负面({final_semantic_score:.2f})")
            
            return {
                "level": "medium",
                "score": min(score, 0.89),
                "reason": " | ".join(reason_parts) if reason_parts else "综合风险评估",
                "needs_intervention": False,
                "keywords_found": medium_matches,
                "semantic_score": final_semantic_score
            }
        
        # 低风险
        return {
            "level": "low",
            "score": final_semantic_score * 0.3,
            "reason": "未检测到明显风险",
            "needs_intervention": False,
            "keywords_found": [],
            "semantic_score": final_semantic_score
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取危机检测统计信息"""
        try:
            if os.path.exists(CrisisConfig.LOG_FILE):
                with open(CrisisConfig.LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                high_count = sum(1 for line in lines if "[高危检测]" in line)
                total_lines = len(lines)
                
                return {
                    "total_alerts": high_count,
                    "total_logs": total_lines,
                    "log_file": CrisisConfig.LOG_FILE,
                    "last_updated": datetime.fromtimestamp(
                        os.path.getmtime(CrisisConfig.LOG_FILE)
                    ).isoformat(),
                    "semantic_enabled": self.use_semantic
                }
            else:
                return {
                    "total_alerts": 0,
                    "total_logs": 0,
                    "log_file": CrisisConfig.LOG_FILE,
                    "status": "no_logs_yet",
                    "semantic_enabled": self.use_semantic
                }
        except Exception as e:
            return {
                "error": str(e),
                "total_alerts": 0,
                "semantic_enabled": self.use_semantic
            }


# 危机干预话术库
CRISIS_RESPONSE = {
    "high": """## 🚨 心理危机干预

我注意到你现在可能处于非常困难的境地。**无论发生什么，你都不是一个人。**

### 请立即联系专业危机干预：

📞 **全国24小时心理援助热线：400-161-9995**

📞 **北京回龙观医院危机干预：800-810-1117 / 010-82951332**
📞 **四川省心理援助热线：96111**

📞 **成都心理危机干预热线：028-87577510**

### 紧急自救措施（此时此刻）：
1. **不要独处** —— 立刻联系信任的朋友或家人陪着你
2. **移除危险物品** —— 暂时把可能伤害自己的物品放到拿不到的地方
3. **前往安全场所** —— 最近的医院急诊科、派出所，或人多的公共场所

**你的生命非常宝贵，痛苦是暂时的，而帮助就在身边。❤️**

*此消息由系统自动触发，你的对话已被记录以便专业跟进。*""",
    
    "medium": """### 💙 关心你的心理健康

我注意到你现在的情绪可能比较低落。虽然我不知道你具体在经历什么，但想让你知道：

**你并不孤单。** 很多人都经历过类似的艰难时刻。

如果你感到持续的痛苦，这些资源可能帮到你：

📞 **心理援助热线：400-161-9995（24小时免费）**

记住：**情绪就像天气，阴晴都是暂时的。** 你现在的感受不会永远持续。

你愿意多说说现在的具体情况吗？我在这里倾听。"""
}