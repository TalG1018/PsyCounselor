"""
PsyCounselor - 心理咨询 RAG 系统（主应用）
集成危机检测、RAG检索、大模型生成
重构版本：采用模块化路由设计，便于维护和扩展
"""

import os
import sys
import numpy as np
import pickle
import faiss
import json
import torch
from datetime import datetime
from io import BytesIO

# 添加当前目录到路径（确保能导入所有模块）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入FastAPI相关
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入各个功能模块
from memory import get_user_memory, ConversationMemory
from transformers import AutoTokenizer, AutoModel
from lmdeploy import pipeline as lmdeploy_pipeline, TurbomindEngineConfig

# 导入自定义模块
from crisis_detector import CrisisDetector, CRISIS_RESPONSE
from emotion_analyzer import EmotionTracker
from personality_profiler import PersonalityProfiler
from recommendation_engine import RecommendationEngine

# 导入路由模块
from chat_routes import router as chat_router
from health_routes import router as health_router
from crisis_routes import router as crisis_router
from memory_routes import router as memory_router
from emotion_routes import router as emotion_router
from personality_routes import router as personality_router
from recommendation_routes import router as recommendation_router
from report_routes import router as report_router

# ========== FastAPI 应用实例 ==========
app = FastAPI(
    title="PsyCounselor API - 安全增强版",
    description="基于 Qwen3-32B + RAG 的心理咨询系统，集成危机识别与安全干预",
    version="2.0.0"
)

# 添加CORS中间件以支持跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 配置路径 ==========
MODEL_PATH = "/root/lanyun-tmp/heart/models/bge_large_zh_v1.5"
INDEX_PATH = "/root/lanyun-tmp/heart/data/psydt_index"
LLM_PATH = "/root/lanyun-tmp/heart/models/qwen3_32b_awq"

print("=" * 60)
print("🚀 正在启动 PsyCounselor 安全增强版...")
print("=" * 60)

# ========== 初始化所有组件 ==========
print("\n[1/4] 加载危机检测模块...")
crisis_detector = CrisisDetector(use_semantic=True)
print("✅ 危机检测模块就绪（关键词+BERT双重检测）")

print("\n[1.5/4] 加载情绪分析模块...")
emotion_tracker = EmotionTracker()
print("✅ 情绪分析模块就绪")

print("\n[1.7/4] 加载人格画像分析模块...")
personality_profiler = PersonalityProfiler()
print("✅ 人格画像分析模块就绪")

print("\n[1.8/4] 加载个性化建议引擎...")
recommendation_engine = RecommendationEngine()
print("✅ 个性化建议引擎就绪")

print("\n[2/4] 加载 BGE 嵌入模型（CPU）...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
embed_model = AutoModel.from_pretrained(MODEL_PATH, trust_remote_code=True).to("cpu")
embed_model.eval()
print("✅ BGE 模型就绪")

print("\n[3/4] 加载 FAISS 向量库...")
index = faiss.read_index(os.path.join(INDEX_PATH, "index.faiss"))
with open(os.path.join(INDEX_PATH, "texts.pkl"), "rb") as f:
    texts = pickle.load(f)
print(f"✅ 向量库就绪，共 {index.ntotal} 条心理咨询对话")

print("\n[4/4] 加载 LMDeploy pipeline（GPU，需要1-2分钟）...")
engine_config = TurbomindEngineConfig(
    model_format='awq',
    quant_policy=4,
    tp=1,
    max_batch_size=1,
    cache_max_entry_count=0.8
)
pipe = lmdeploy_pipeline(LLM_PATH, backend_config=engine_config)
print("✅ Qwen3-32B-AWQ 模型就绪")
print("=" * 60)

# ========== 设置全局变量供路由模块使用 ==========
# 为所有路由模块设置全局变量
import chat_routes, health_routes, crisis_routes, memory_routes, emotion_routes, personality_routes, recommendation_routes, report_routes

# 聊天路由
chat_routes.llm_pipe = pipe
chat_routes.embed_model = embed_model
chat_routes.tokenizer = tokenizer
chat_routes.index = index
chat_routes.texts = texts
chat_routes.emotion_tracker = emotion_tracker
chat_routes.crisis_detector = crisis_detector

# 健康检查路由
health_routes.crisis_detector = crisis_detector
health_routes.emotion_tracker = emotion_tracker
health_routes.index = index
health_routes.embed_model = embed_model
health_routes.llm_pipe = pipe

# 危机检测路由
crisis_routes.crisis_detector = crisis_detector

# 情绪分析路由
emotion_routes.emotion_tracker = emotion_tracker

# 个性化建议路由
recommendation_routes.recommendation_engine = recommendation_engine
recommendation_routes.personality_profiler = personality_profiler
recommendation_routes.emotion_tracker = emotion_tracker
recommendation_routes.get_user_memory = get_user_memory

# 人格画像路由
personality_routes.personality_profiler = personality_profiler

# ========== 注册所有路由 ==========
app.include_router(chat_router)
app.include_router(health_router)
app.include_router(crisis_router)
app.include_router(memory_router)
app.include_router(emotion_router)
app.include_router(personality_router)
app.include_router(recommendation_router)
app.include_router(report_router)

# ========== 启动信息 ==========
@app.on_event("startup")
async def startup_event():
    print("\n🎯 PsyCounselor API 服务启动完成!")
    print("📚 可用接口:")
    print("   POST /api/ask                 - 心理咨询对话")
    print("   GET  /api/health              - 系统健康检查")
    print("   POST /api/emotion/analyze     - 情绪分析")
    print("   POST /api/personality/analyze - 人格画像分析")
    print("   POST /api/recommendations/generate - 个性化建议生成")
    print("   更多接口请查看API文档...")

if __name__ == "__main__":
    import uvicorn
    print("\n🎯 启动 FastAPI 服务...")
    uvicorn.run(app, host="0.0.0.0", port=8001)