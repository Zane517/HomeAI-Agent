"""
HomeAI Agent — 基于小米 MiMo 的全模态智能家居管家中控系统

启动方式:
    python main.py
    或
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

API 文档 (启动后访问):
    http://localhost:8000/docs     (Swagger UI)
    http://localhost:8000/redoc    (ReDoc)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from utils.helpers import setup_logging

# 初始化日志
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 50)
    logger.info("  HomeAI Agent 启动中...")
    logger.info(f"  MiMo API: {settings.mimo_base_url}")
    logger.info(f"  视觉模型: {settings.mimo_vision_model}")
    logger.info(f"  推理模型: {settings.mimo_reasoning_model}")
    logger.info(f"  编排模型: {settings.mimo_orchestrator_model}")
    logger.info(f"  TTS 模型: {settings.mimo_tts_model}")
    logger.info(f"  关注房间: {settings.active_rooms}")
    logger.info("=" * 50)

    # 可选：启动定时抓拍
    # from services.camera_service import camera_service
    # await camera_service.start_periodic_capture()

    yield

    logger.info("HomeAI Agent 关闭")


# ==================== 创建应用 ====================

app = FastAPI(
    title="HomeAI Agent",
    description="基于小米 MiMo-V2.5 系列模型的全模态智能家居管家中控系统",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================

from routers import scene, control, tts

app.include_router(scene.router)
app.include_router(control.router)
app.include_router(tts.router)


# ==================== 根路由 / 健康检查 ====================

@app.get("/")
async def root():
    return {
        "name": "HomeAI Agent",
        "version": "0.1.0",
        "description": "基于小米 MiMo 的全模态智能家居管家中控系统",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# ==================== 对话式交互 ====================

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    """对话式智能家居问答"""
    from agents.core_agent import core_agent

    try:
        reply = await core_agent.chat(request.message)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"对话失败: {e}")
        return {"reply": f"抱歉，处理您的请求时出现错误：{str(e)}"}


# ==================== 入口 ====================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting HomeAI Agent on http://0.0.0.0:8000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
