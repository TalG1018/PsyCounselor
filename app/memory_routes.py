"""
用户记忆管理路由模块
实现用户对话历史、记忆存储、统计分析等功能
支持动态切换存储后端（SQLite/Redis）
采用技术：FastAPI + 动态存储后端 + 用户行为分析
"""

from fastapi import APIRouter, HTTPException
import os
from storage_config import get_user_memory, get_current_backend

# 创建路由实例
router = APIRouter(prefix="/api", tags=["memory"])

@router.get("/memory/{user_id}")
async def get_user_history(user_id: str):
    """获取用户对话历史（调试/管理用）"""
    try:
        memory = get_user_memory(user_id)
        stats = memory.get_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/stats/all")
async def get_all_memory_stats():
    """获取所有用户记忆统计"""
    try:
        # 这里需要根据实际使用的存储后端来实现
        # 暂时返回存储后端信息
        return {
            "storage_backend": get_current_backend(),
            "message": "请根据实际存储后端实现具体的统计功能"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/backend")
async def get_storage_backend():
    """获取当前使用的存储后端信息"""
    return {
        "current_backend": get_current_backend(),
        "available_backends": ["SQLite", "Redis"],
        "status": "active"
    }