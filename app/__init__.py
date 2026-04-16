"""
FastAPI应用初始化
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
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
from app.api.auth import get_current_user

# 创建应用
app = FastAPI(
    title=APP_NAME,
    debug=DEBUG
)

# 静态文件
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 模板
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# 注册路由
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(monitor_router, prefix="/api")
app.include_router(zabbix_config_router, prefix="/api")
app.include_router(email_config_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(logs_router)
app.include_router(alerts_router)


# 页面路由
@app.get("/")
async def index(request: Request, user=Depends(get_current_user)):
    """首页"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "current_user": user
    })


@app.get("/login")
async def login_page(request: Request, user=Depends(get_current_user)):
    """登录页面"""
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "current_user": None
    })


@app.get("/register")
async def register_page(request: Request, user=Depends(get_current_user)):
    """注册页面"""
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("auth/register.html", {
        "request": request,
        "current_user": None
    })


@app.get("/logout")
async def logout():
    """退出登录"""
    response = RedirectResponse(url="/login")
    # 清除cookie
    response.delete_cookie("access_token")
    return response


@app.get("/set-cookie")
async def set_cookie(token: str):
    """设置登录cookie"""
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,  # 24小时
        samesite="lax"
    )
    return response


@app.get("/monitor")
async def monitor_page(request: Request, user=Depends(get_current_user)):
    """监控信息页面"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("monitor/index.html", {
        "request": request,
        "current_user": user
    })


@app.get("/profile")
async def profile_page(request: Request, user=Depends(get_current_user)):
    """个人信息页面"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": user
    })


@app.get("/tasks")
async def tasks_page(request: Request, user=Depends(get_current_user)):
    """定时任务页面"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("tasks/index.html", {
        "request": request,
        "current_user": user
    })


@app.get("/alerts")
async def alerts_page(request: Request, user=Depends(get_current_user)):
    """告警信息页面"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("alerts/index.html", {
        "request": request,
        "current_user": user
    })


@app.get("/admin/users")
async def users_admin_page(request: Request, user=Depends(get_current_user)):
    """用户管理页面"""
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "current_user": user
    })


@app.get("/admin/zabbix-config")
async def zabbix_config_page(request: Request, user=Depends(get_current_user)):
    """Zabbix配置页面"""
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("admin/zabbix_config.html", {
        "request": request,
        "current_user": user
    })


@app.get("/admin/email-config")
async def email_config_page(request: Request, user=Depends(get_current_user)):
    """邮件配置页面"""
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("admin/email_config.html", {
        "request": request,
        "current_user": user
    })


@app.get("/admin/system")
async def system_settings_page(request: Request, user=Depends(get_current_user)):
    """系统设置页面"""
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("admin/system.html", {
        "request": request,
        "current_user": user
    })


@app.get("/admin/logs")
async def logs_page(request: Request, user=Depends(get_current_user)):
    """系统日志页面"""
    if not user or not user.is_admin:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("logs/index.html", {
        "request": request,
        "current_user": user
    })


# 初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
