"""
聊天对话路由模块
实现心理咨询对话核心功能
采用技术：FastAPI + Qwen3-32B大语言模型 + RAG检索增强 + 情绪分析
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import time
from datetime import datetime
import json as json_module
from fastapi.responses import JSONResponse

from memory import get_user_memory
from emotion_analyzer import EmotionTracker
from crisis_detector import CrisisDetector, CRISIS_RESPONSE
from context_manager import ContextManager

# 创建路由实例
router = APIRouter(prefix="/api", tags=["chat"])

# 导入全局变量（在main.py中初始化）
llm_pipe = None
embed_model = None
tokenizer = None
index = None
texts = None
emotion_tracker = None
crisis_detector = None

# 上下文管理器字典（按用户ID存储）
context_managers = {}

class QueryRequest(BaseModel):
    query: str
    user_id: str = "anonymous"
    skip_crisis_check: bool = False

class QueryResponse(BaseModel):
    answer: str
    risk_level: str = "low"
    is_crisis: bool = False
    intervention_triggered: bool = False
    confidence: float = 0.0
    reason: str = ""
    reference_count: int = 0
    processing_time: float = 0.0

def embed_query(query: str):
    """将查询文本编码为向量（CPU运行）"""
    import torch
    inputs = tokenizer([query], padding=True, truncation=True, 
                      return_tensors="pt", max_length=512)
    with torch.no_grad():
        outputs = embed_model(**inputs)
        embedding = outputs.last_hidden_state[:, 0]
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
    return embedding.numpy().astype('float32')

@router.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    """心理咨询对话主接口"""
    global llm_pipe, embed_model, tokenizer, index, texts, emotion_tracker, crisis_detector
    
    # 确保响应使用UTF-8编码
    start_time = time.time()
    user_query = request.query.strip()
    user_id = request.user_id

    if not user_query:
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用户 {user_id[:8]}...: {user_query[:40]}...")

    # 初始化用户记忆
    user_memory = get_user_memory(user_id)

    try:
        # ========== 第1步：情绪分析 ==========
        emotion_result = emotion_tracker.track_user_emotion(user_id, user_query)
        print(f"😊 情绪分析: {emotion_result['emotion']} (置信度: {emotion_result['confidence']:.2f})")
        
        # ========== 第2步：危机检测 ==========
        if not request.skip_crisis_check:
            risk_result = crisis_detector.detect(user_query, user_id)
            print(f"🔍 风险评估: {risk_result['level']} (score: {risk_result['score']:.2f})")

            if risk_result["level"] == "high":
                # 记录到记忆
                user_memory.add_conversation(
                    user_query, 
                    CRISIS_RESPONSE["high"], 
                    "high",
                    risk_result["score"],
                    0
                )

                return QueryResponse(
                    answer=CRISIS_RESPONSE["high"],
                    risk_level="high",
                    is_crisis=True,
                    intervention_triggered=True,
                    confidence=risk_result["score"],
                    reason=risk_result["reason"],
                    reference_count=0,
                    processing_time=time.time() - start_time
                )
        else:
            risk_result = {"level": "low", "score": 0.0, "reason": "检测已跳过"}

        # ========== 第3步：获取记忆上下文（使用智能上下文管理）==========
        # 获取或创建该用户的上下文管理器
        if user_id not in context_managers:
            context_managers[user_id] = ContextManager(max_tokens=128000)  # 128K token限制
        
        context_manager = context_managers[user_id]
        
        # 从用户记忆中获取更多历史对话用于初始化
        memory_context_raw = user_memory.get_recent_context(max_turns=10)
        profile_summary = user_memory.get_profile_summary()
        
        # 如果是新会话，可以从历史记忆初始化上下文管理器
        if len(context_manager.context_window) == 0 and memory_context_raw:
            # 解析历史对话并添加到上下文管理器
            # 这里可以添加更复杂的解析逻辑
            pass
        
        # 获取格式化的上下文
        memory_context = context_manager.get_formatted_context(max_turns=5)  # 最多取5轮
        
        if memory_context:
            stats = context_manager.get_statistics()
            print(f"📚 上下文管理: {stats['total_turns']} 轮, {stats['total_tokens']} tokens, "
                  f"利用率: {stats['utilization_rate']}%")

        # ========== 第4步：RAG检索 ==========
        query_embedding = embed_query(user_query)
        distances, indices = index.search(query_embedding, k=3)

        contexts = [texts[idx] for idx in indices[0]]
        context = "\n\n---\n".join(contexts)

        # ========== 第5步：构造增强Prompt ==========
        memory_section = ""
        if profile_summary and "新用户" not in profile_summary:
            memory_section = f"""【用户画像】{profile_summary}\n"""
            if memory_context:
                memory_section += f"""【近期对话历史】\n{memory_context}\n\n"""

        safety_hint = ""
        if risk_result["level"] == "medium":
            safety_hint = "（注意：用户情绪较低落，请特别给予温暖支持）\n"

        # 后台深度思考（消耗token但不展示）
        thinking_prompt = f"""你是一位专业心理咨询师AI助手。请分析：

用户问题：{user_query}
历史背景：{memory_context if memory_context else '新用户'}
参考案例：{context[:200]}...

分析维度：问题核心、情绪状态、建议要点"""
        
        # 执行后台思考
        thinking_result = llm_pipe(thinking_prompt, max_new_tokens=100, temperature=0.3)
        thinking_analysis = thinking_result.text.strip()
        print(f"🧠 后台思考完成 ({len(thinking_analysis)}字符)")
        
        # 面向用户的正式回复prompt
        prompt = f"""{safety_hint}{memory_section}你是一位专业且富有同理心的心理咨询师。

用户问题：{user_query}

重要要求：
1. 必须使用纯中文回复，不要夹杂英文
2. 语气温暖、专业、共情
3. 直接回应用户核心关切
4. 提供具体可行的建议

请用中文给出简洁、温暖、实用的回复："""

        # ========== 第6步：生成回答 ==========
        response = llm_pipe(prompt, max_new_tokens=512, temperature=0.7, top_p=0.9)
        answer = response.text.strip()
        print(f"🤖 大模型生成完成，回复长度: {len(answer)} 字符")
        print(f"🤖 回复预览: {answer[:100]}...")

        if risk_result["level"] == "medium":
            answer += "\n\n---\n💙 温馨提示：如果你感到持续的情绪困扰，可随时拨打 **400-161-9995** 。"

        # ========== 第7步：保存到记忆和上下文管理器 ==========
        user_memory.add_conversation(
            user_query,
            answer,
            risk_result["level"],
            risk_result.get("semantic_score", 0.0),
            len(contexts)
        )
        
        # 添加到智能上下文管理器
        context_manager.add_turn(
            user_message=user_query,
            ai_response=answer,
            emotion_score=emotion_result["confidence"],
            keywords=emotion_result.get("keywords", [])
        )

        processing_time = time.time() - start_time
        print(f"✅ 完成 ({processing_time:.2f}s)")

        # 返回完整响应
        response_data = {
            "answer": answer,
            "risk_level": risk_result["level"],
            "is_crisis": risk_result["level"] in ["high", "medium"],
            "intervention_triggered": False,
            "confidence": risk_result["score"],
            "reason": risk_result["reason"],
            "reference_count": len(contexts),
            "processing_time": processing_time,
            "emotion": emotion_result["emotion"],
            "emotion_confidence": emotion_result["confidence"],
            "emotion_details": emotion_result["all_probabilities"]
        }
        return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
