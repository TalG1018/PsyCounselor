"""
健康检查和系统状态路由模块
实现系统监控、健康检查、状态统计等功能
采用技术：FastAPI + 系统信息收集 + 性能监控
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from crisis_detector import CrisisDetector
from emotion_analyzer import EmotionTracker

# 创建路由实例
router = APIRouter(prefix="/api", tags=["health"])

# 导入全局变量（在main.py中初始化）
crisis_detector = None
emotion_tracker = None
index = None
embed_model = None
llm_pipe = None

@router.get("/health")
async def health():
    """系统健康检查"""
    global crisis_detector, emotion_tracker, index, embed_model, llm_pipe
    
    # 检查必需的全局变量是否存在
    if index is None:
        return {"status": "error", "message": "Vector database not initialized"}
    
    if crisis_detector is None:
        return {"status": "error", "message": "Crisis detector not initialized"}
    
    return {
        "status": "ok",
        "version": "2.0.0-crisis-aware",
        "crisis_detection": {
            "enabled": True,
            "mode": "keyword+semantic",
            "high_risk_keywords": len(CrisisDetector.HIGH_RISK_KEYWORDS),
            "medium_risk_keywords": len(CrisisDetector.MEDIUM_RISK_KEYWORDS)
        },
        "emotion_analysis": {
            "enabled": True,
            "model": "RoBERTa-Chinese",
            "emotions_supported": ["愤怒", "厌恶", "恐惧", "快乐", "悲伤", "惊讶"],
            "tracking_enabled": True
        },
        "rag": {
            "vector_db_size": index.ntotal,
            "embedding_model": "bge-large-zh-v1.5",
            "device": "cpu"
        },
        "llm": {
            "model": "Qwen3-32B-AWQ",
            "quantization": "4-bit",
            "device": "cuda",
            "engine": "LMDeploy"
        }
    }

@router.get("/crisis/stats")
async def get_crisis_statistics():
    """获取危机检测统计数据"""
    global crisis_detector
    stats = crisis_detector.get_stats()
    return {
        "status": "success",
        "data": stats
    }

@router.get("/crisis/test")
async def test_crisis_detection(text: str = "我觉得活着没意思"):
    """测试危机检测功能（调试用）"""
    global crisis_detector
    result = crisis_detector.detect(text, "test_user")
    return {
        "input": text,
        "detection_result": result,
        "action": "intervention" if result["needs_intervention"] else "normal_rag"
    }