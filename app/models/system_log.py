"""
系统日志模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class SystemLog(Base):
    """系统日志"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, DEBUG
    logger_name = Column(String(100), nullable=False, index=True)  # 日志记录器名称
    message = Column(Text, nullable=False)  # 日志消息
    created_at = Column(DateTime, default=datetime.now, index=True)  # 创建时间

    def to_dict(self):
        return {
            "id": self.id,
            "level": self.level,
            "logger_name": self.logger_name,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
