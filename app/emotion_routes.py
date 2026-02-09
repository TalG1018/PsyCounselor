"""
情绪分析路由模块
实现情绪识别、趋势分析、统计报表等功能
采用技术：FastAPI + RoBERTa-Chinese情绪模型 + 时间序列分析
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

# 创建路由实例
router = APIRouter(prefix="/api", tags=["emotion"])

# 导入全局变量（在main.py中初始化）
emotion_tracker = None

class EmotionRequest(BaseModel):
    user_id: str
    text: str

@router.post("/emotion/analyze")
async def analyze_emotion(request: EmotionRequest):
    """实时情绪分析接口"""
    global emotion_tracker
    try:
        result = emotion_tracker.track_user_emotion(request.user_id, request.text)
        return {
            "status": "success",
            "emotion": result["emotion"],
            "confidence": result["confidence"],
            "all_probabilities": result["all_probabilities"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotion/trend/{user_id}")
async def get_emotion_trend(user_id: str, limit: int = 20):
    """获取用户情绪趋势数据"""
    global emotion_tracker
    try:
        trend_data = emotion_tracker.get_emotion_trend(user_id, limit)
        summary = emotion_tracker.get_emotion_summary(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "trend": trend_data,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotion/statistics/{user_id}")
async def get_emotion_statistics(user_id: str, days: int = 7):
    """获取用户情绪统计分析"""
    global emotion_tracker
    try:
        stats = emotion_tracker.get_emotion_statistics(user_id, days)
        return {
            "status": "success",
            "user_id": user_id,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotion/chart/{user_id}")
async def get_emotion_chart_data(user_id: str, days: int = 7):
    """获取用户情绪图表数据（用于前端可视化）"""
    global emotion_tracker
    try:
        # 从情绪追踪器获取数据
        trend_data = emotion_tracker.get_emotion_trend(user_id, limit=30)
        summary = emotion_tracker.get_emotion_summary(user_id)
        
        if not trend_data:
            return {
                "status": "no_data",
                "message": "该用户暂无情绪记录",
                "data": [],
                "risk_alert": False
            }

        # 转换为图表友好的格式
        chart_data = []
        emotion_mapping = {
            '愤怒': 1, '厌恶': 2, '恐惧': 3, 
            '快乐': 4, '悲伤': 5, '惊讶': 6, '中性': 0
        }
        
        for i, record in enumerate(trend_data):
            emotion_value = emotion_mapping.get(record['emotion'], 0)
            chart_data.append({
                "x": i + 1,
                "y": emotion_value,
                "emotion": record['emotion'],
                "confidence": round(record['confidence'], 2),
                "timestamp": record['time'][:19]
            })

        # 分析趋势
        risk_alert = False
        trend_analysis = "平稳"
        
        if len(chart_data) >= 3:
            recent_values = [point['y'] for point in chart_data[-3:]]
            # 如果连续出现负面情绪（值为1,2,3,5）且置信度较高
            negative_emotions = [val for val in recent_values if val in [1, 2, 3, 5]]
            if len(negative_emotions) >= 2:
                trend_analysis = "情绪波动较大"
                # 检查是否有高置信度的负面情绪
                recent_high_confidence = [
                    point for point in chart_data[-3:] 
                    if point['y'] in [1, 2, 3, 5] and point['confidence'] > 0.7
                ]
                if len(recent_high_confidence) >= 2:
                    risk_alert = True
                    trend_analysis = "需要关注"
            elif all(val == 4 for val in recent_values[-2:]):
                trend_analysis = "情绪积极"

        return {
            "status": "success",
            "user_id": user_id,
            "data": chart_data,
            "trend_analysis": trend_analysis,
            "risk_alert": risk_alert,
            "latest_emotion": chart_data[-1]['emotion'] if chart_data else "未知",
            "total_records": len(chart_data),
            "emotion_legend": {
                0: "中性", 1: "愤怒", 2: "厌恶", 3: "恐惧", 
                4: "快乐", 5: "悲伤", 6: "惊讶"
            }
        }

    except Exception as e:
        import traceback
        print(f"❌ 情绪图表接口错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))