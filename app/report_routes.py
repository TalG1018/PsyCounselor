"""
报告管理路由模块
实现咨询报告生成、下载、管理等功能
采用技术：FastAPI + PDF生成 + 文件管理
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from typing import Dict, Any, List

# 创建路由实例
router = APIRouter(prefix="/api", tags=["report"])

def generate_session_report(user_id: str, history: List[Dict[str, Any]], risk_data: List[Dict[str, Any]]) -> bytes:
    """
    生成咨询会话报告PDF（使用中文版生成器）
    支持完整的中文字体显示和详细分析
    """
    # TODO: 重新实现报告生成功能
    # 调用智能报告生成器
    # return generate_smart_session_report(user_id, history, risk_data)
    return b"Report generation temporarily disabled"

@router.get("/reports/download/{filename}")
async def download_report(filename: str):
    """下载生成的报告"""
    filepath = f"/root/lanyun-tmp/heart/data/reports/{filename}"

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        filepath, 
        media_type="application/pdf",
        filename=f"PsyCounselor_Report_{filename}"
    )