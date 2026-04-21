"""
FastAPI应用初始化
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import APP_NAME, DEBUG
from app.database import init_db
from app.api import (
    auth_router, users_router, monitor_router,
    zabbix_config_router, email_config_router, tasks_router,
    alerts_router
)
from app.api.system_settings import router as system_router
from app.api.logs import router as logs_router

# 创建应用
app = FastAPI(
    title=APP_NAME,
    debug=DEBUG
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:37201",  # Vue前端开发地址
        "http://127.0.0.1:37201",  # Vue前端开发地址（备用）
        "*",  # 生产环境允许所有来源（可根据需要限制）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vue 前端构建目录
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

# 挂载前端 assets 目录
assets_path = FRONTEND_DIST / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

# 注册 API 路由
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(monitor_router, prefix="/api")
app.include_router(zabbix_config_router, prefix="/api")
app.include_router(email_config_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(logs_router)
app.include_router(alerts_router)


# SPA fallback - 所有非 API/非静态路由返回 index.html
@app.get("/{path:path}")
async def spa_fallback(path: str):
    """
    SPA fallback: 对于所有非 API 路由，返回 Vue 前端的 index.html
    """
    # 尝试返回请求的静态文件（如 favicon.svg, icons.svg 等）
    file_path = FRONTEND_DIST / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)

    # 否则返回 index.html（SPA 入口）
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # 如果前端未构建，返回提示
    return {"error": "Frontend not built. Run 'npm run build' in frontend directory."}


# 初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
