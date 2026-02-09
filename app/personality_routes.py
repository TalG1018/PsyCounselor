"""
人格画像路由模块
实现人格特征分析、画像生成、报告展示等功能
采用技术：FastAPI + 大五人格理论 + 文本分析算法
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

# 创建路由实例
router = APIRouter(prefix="/api", tags=["personality"])

# 导入全局变量（在main.py中初始化）
personality_profiler = None

class PersonalityRequest(BaseModel):
    user_id: str
    conversation_history: List[str]

@router.post("/personality/analyze")
async def analyze_personality(request: PersonalityRequest):
    """人格画像分析接口"""
    global personality_profiler
    try:
        # 分析人格特质
        trait_scores = personality_profiler.analyze_personality_traits(request.conversation_history)
        personality_profile = personality_profiler.generate_personality_report(
            request.user_id, trait_scores
        )
        
        # 保存画像
        personality_profiler.save_profile(request.user_id, personality_profile)
        
        return {
            "status": "success",
            "profile": personality_profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personality/profile/{user_id}")
async def get_personality_profile(user_id: str):
    """获取用户人格画像"""
    global personality_profiler
    try:
        profile = personality_profiler.get_user_profile(user_id)
        if profile:
            return {
                "status": "success",
                "profile": profile
            }
        else:
            raise HTTPException(status_code=404, detail="未找到用户画像数据")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))