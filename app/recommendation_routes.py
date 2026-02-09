"""
个性化建议路由模块
实现个性化心理咨询建议生成、行动计划制定、资源推荐等功能
采用技术：FastAPI + 多维度数据分析 + 智能推荐算法
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

# 创建路由实例
router = APIRouter(prefix="/api", tags=["recommendation"])

# 导入全局变量（在main.py中初始化）
recommendation_engine = None
personality_profiler = None
emotion_tracker = None
get_user_memory = None

class RecommendationRequest(BaseModel):
    user_id: str
    emotion_history: List[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]

@router.post("/recommendations/generate")
async def generate_recommendations(request: RecommendationRequest):
    """生成个性化心理咨询建议"""
    global recommendation_engine, personality_profiler
    
    try:
        # 获取用户人格画像
        personality_profile = personality_profiler.get_user_profile(request.user_id)
        if not personality_profile:
            # 如果没有画像，先生成一个
            trait_scores = personality_profiler.analyze_personality_traits(request.conversation_history)
            personality_profile = personality_profiler.generate_personality_report(
                request.user_id, trait_scores
            )
            personality_profiler.save_profile(request.user_id, personality_profile)
        
        # 确保传递正确的数据结构
        profile_data = personality_profile.get('profile', personality_profile) if isinstance(personality_profile, dict) else personality_profile
        
        # 生成个性化建议
        recommendations = recommendation_engine.generate_personalized_recommendations(
            request.user_id,
            request.emotion_history,
            profile_data,
            request.conversation_history
        )
        
        return {
            "status": "success",
            "recommendations": recommendations
        }
    except Exception as e:
        import traceback
        print(f"个性化建议生成错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/user/{user_id}")
async def get_user_recommendations(user_id: str):
    """获取用户历史建议记录"""
    global recommendation_engine, personality_profiler, emotion_tracker, get_user_memory
    
    try:
        # 这里可以扩展为从数据库获取历史建议
        # 目前返回基于当前数据的建议
        user_memory = get_user_memory(user_id)
        conversation_context = user_memory.get_recent_context(max_turns=10)
        
        # 获取情绪历史
        emotion_data = emotion_tracker.get_emotion_trend(user_id, limit=30)
        
        # 获取人格画像
        personality_profile = personality_profiler.get_user_profile(user_id)
        
        # 如果没有足够数据，创建最小化测试数据
        if not emotion_data:
            emotion_data = [
                {"timestamp": "2024-01-01T10:00:00", "emotion_score": 0.5, "emotion": "中性"},
                {"timestamp": "2024-01-02T10:00:00", "emotion_score": 0.6, "emotion": "快乐"}
            ]
        
        if not personality_profile:
            # 生成默认人格画像
            default_traits = {
                'openness': 50, 'conscientiousness': 50, 
                'extraversion': 50, 'agreeableness': 50, 'neuroticism': 50
            }
            personality_profile = {
                'profile': {
                    'personality_traits': {
                        trait: {'score': score, 'level': '中等'} 
                        for trait, score in default_traits.items()
                    }
                }
            }
        
        # 确保传递正确的数据结构
        profile_data = personality_profile.get('profile', personality_profile) if isinstance(personality_profile, dict) else personality_profile
        
        # 生成建议
        recommendations = recommendation_engine.generate_personalized_recommendations(
            user_id,
            emotion_data,
            profile_data,
            [{'content': conversation_context}] if conversation_context else [{"content": "用户正在寻求心理帮助"}]
        )
        
        return {
            "status": "success",
            "recommendations": recommendations
        }
    except Exception as e:
        import traceback
        print(f"用户建议获取错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))