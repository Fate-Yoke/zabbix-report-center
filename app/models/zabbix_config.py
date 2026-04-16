"""
Zabbix配置模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database import Base


class ZabbixConfig(Base):
    """Zabbix配置表"""
    __tablename__ = "zabbix_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    auth_type = Column(String(20), nullable=False)  # token / password
    token = Column(Text, nullable=True)  # 加密存储
    username = Column(String(100), nullable=True)  # 加密存储
    password = Column(String(255), nullable=True)  # 加密存储
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ZabbixConfig {self.name}>"
