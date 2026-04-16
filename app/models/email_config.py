"""
邮件配置模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base


class EmailConfig(Base):
    """邮件配置表"""
    __tablename__ = "email_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, default="默认邮件配置")
    smtp_server = Column(String(100), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=465)
    smtp_user = Column(String(100), nullable=False)
    smtp_pass = Column(String(255), nullable=False)  # 加密存储
    use_ssl = Column(Boolean, default=True)
    mail_from = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<EmailConfig {self.name}>"
