"""Recall AI 后端入口。

启动:
    uvicorn app.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import ai, analytics, questions, review
from app.api.v1 import settings as settings_api
from app.config import get_settings
from app.database import init_db

settings = get_settings()
logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期:启动建表。"""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

# CORS:允许本地前端(运行版 5173 + 静态版 file:// 的 null Origin)
# 本地单用户工具,放开跨域以支持静态 HTML 直连后端(OCR/AI/错题)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 v1 路由
api_v1 = settings.API_V1_PREFIX
app.include_router(questions.router, prefix=api_v1)
app.include_router(review.router, prefix=api_v1)
app.include_router(ai.router, prefix=api_v1)
app.include_router(analytics.router, prefix=api_v1)
app.include_router(settings_api.router, prefix=api_v1)


@app.get("/")
def root() -> dict:
    """健康检查。"""
    return {"service": settings.APP_NAME, "status": "ok", "docs": "/docs"}
