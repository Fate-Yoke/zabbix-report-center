"""
应用入口
"""
import logging
from contextlib import asynccontextmanager

from app import app
from app.database import init_db
from app.services.scheduler_service import scheduler_service
from app.utils.db_log_handler import DatabaseLogHandler

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别以记录更多日志
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# 添加数据库日志处理器
db_handler = DatabaseLogHandler()
db_handler.setLevel(logging.INFO)  # 数据库只记录INFO及以上级别
db_handler.setFormatter(logging.Formatter("%(message)s"))

# 为根日志记录器添加数据库处理器
root_logger = logging.getLogger()
root_logger.addHandler(db_handler)

# 为uvicorn和fastapi的日志也添加数据库处理器
for logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error', 'fastapi']:
    logger = logging.getLogger(logger_name)
    logger.addHandler(db_handler)


@asynccontextmanager
async def lifespan(app):
    """应用生命周期"""
    # 启动时
    logging.info("应用启动中...")
    init_db()
    scheduler_service.init_scheduler()
    scheduler_service.load_all_tasks()

    yield

    # 关闭时
    logging.info("应用关闭中...")
    scheduler_service.shutdown()


# 将lifespan绑定到app
app.router.lifespan_context = lifespan


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
