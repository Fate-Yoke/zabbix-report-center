"""
API路由导出
"""
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.monitor import router as monitor_router
from app.api.zabbix_config import router as zabbix_config_router
from app.api.email_config import router as email_config_router
from app.api.tasks import router as tasks_router
from app.api.alerts import router as alerts_router

__all__ = [
    "auth_router", "users_router", "monitor_router",
    "zabbix_config_router", "email_config_router", "tasks_router",
    "alerts_router"
]
