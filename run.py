#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zabbix Report Center启动脚本
"""
import os
import sys
import time
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.database import init_db, engine
from app.services.scheduler_service import scheduler_service
from app.utils.db_log_handler import DatabaseLogHandler
from sqlalchemy import text

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

# 添加数据库日志处理器
db_handler = DatabaseLogHandler()
db_handler.setLevel(logging.INFO)
db_handler.setFormatter(logging.Formatter("%(message)s"))

# 为根日志记录器添加数据库处理器
root_logger = logging.getLogger()
root_logger.addHandler(db_handler)

# 为uvicorn和fastapi的日志也添加数据库处理器
for logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error', 'fastapi']:
    logger_instance = logging.getLogger(logger_name)
    logger_instance.addHandler(db_handler)


def wait_for_db(max_retries=30, retry_interval=2):
    """等待数据库连接可用（Docker 环境下 MySQL 启动可能较慢）"""
    from app.config import DATABASE_URL

    # 只有 MySQL 需要等待
    if "mysql" not in DATABASE_URL.lower():
        return True

    print(f"等待数据库连接... (最多等待 {max_retries * retry_interval} 秒)")

    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("数据库连接成功！")
            return True
        except Exception as e:
            print(f"数据库连接失败 ({i + 1}/{max_retries}): {e}")
            if i < max_retries - 1:
                time.sleep(retry_interval)

    print("数据库连接超时，请检查数据库是否正常运行")
    return False


def main():
    """主函数"""
    # 等待数据库连接
    if not wait_for_db():
        sys.exit(1)

    # 初始化数据库
    print("初始化数据库...")
    init_db()

    # 初始化调度器
    print("初始化调度器...")
    scheduler_service.init_scheduler()
    scheduler_service.load_all_tasks()

    # 启动Web服务
    print("启动Web服务...")
    print("访问地址: http://localhost:37201")
    print("首次注册的用户将自动成为管理员")

    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=37201,
            reload=False
        )
    finally:
        scheduler_service.shutdown()


if __name__ == "__main__":
    main()
