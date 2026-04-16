"""
数据库日志处理器
"""
import logging
from datetime import datetime
from app.database import SessionLocal
from app.models.system_log import SystemLog


class DatabaseLogHandler(logging.Handler):
    """将日志写入数据库的处理器"""

    def emit(self, record):
        """处理日志记录"""
        try:
            db = SessionLocal()
            try:
                log = SystemLog(
                    level=record.levelname,
                    logger_name=record.name,
                    message=self.format(record),
                    created_at=datetime.now()
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
        except Exception:
            # 避免日志处理器本身出错导致应用崩溃
            self.handleError(record)
