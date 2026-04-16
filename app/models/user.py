"""
用户模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    allowed_zabbix_ids = Column(JSON, default=list)  # 允许访问的Zabbix配置ID列表，None或空列表表示无权限
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<User {self.username}>"

    def can_access_zabbix(self, zabbix_id: int) -> bool:
        """检查用户是否有权限访问指定的Zabbix配置"""
        # 管理员可以访问所有配置
        if self.is_admin:
            return True
        # 检查是否在允许列表中
        if self.allowed_zabbix_ids:
            return zabbix_id in self.allowed_zabbix_ids
        return False
