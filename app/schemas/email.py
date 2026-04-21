"""
邮件配置相关Pydantic模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EmailConfigBase(BaseModel):
    """邮件配置基础模型"""
    name: str = "默认邮件配置"
    smtp_server: str
    smtp_port: int = 465
    smtp_user: str
    smtp_pass: str
    use_ssl: bool = True
    mail_from: str


class EmailConfigCreate(EmailConfigBase):
    """邮件配置创建模型"""
    pass


class EmailConfigUpdate(BaseModel):
    """邮件配置更新模型"""
    name: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    use_ssl: Optional[bool] = None
    mail_from: Optional[str] = None
    is_active: Optional[bool] = None


class EmailConfigResponse(EmailConfigBase):
    """邮件配置响应模型"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
