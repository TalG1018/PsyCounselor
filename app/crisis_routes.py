"""
危机检测路由模块
实现心理危机识别、风险评估、紧急干预等功能
采用技术：FastAPI + 关键词检测 + BERT语义分析
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# 创建路由实例
router = APIRouter(prefix="/api", tags=["crisis"])

# 导入全局变量（在main.py中初始化）
crisis_detector = None

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