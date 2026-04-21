"""
用户相关Pydantic模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """用户创建模型"""
    password: str
    captcha_key: str
    captcha_code: str


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str
    captcha_key: str
    captcha_code: str


class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    allowed_zabbix_ids: Optional[List[int]] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    is_admin: bool
    is_active: bool
    allowed_zabbix_ids: List[int] = []
    created_at: datetime

    @field_validator('allowed_zabbix_ids', mode='before')
    @classmethod
    def validate_allowed_zabbix_ids(cls, v):
        """确保 allowed_zabbix_ids 始终是列表"""
        if v is None:
            return []
        return v

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据模型"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    is_admin: bool = False
