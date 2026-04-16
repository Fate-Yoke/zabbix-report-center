"""
Zabbix配置相关Pydantic模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ZabbixConfigBase(BaseModel):
    """Zabbix配置基础模型"""
    name: str
    url: str
    auth_type: str  # token / password


class ZabbixConfigCreate(ZabbixConfigBase):
    """Zabbix配置创建模型"""
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ZabbixConfigUpdate(BaseModel):
    """Zabbix配置更新模型"""
    name: Optional[str] = None
    url: Optional[str] = None
    auth_type: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class ZabbixConfigResponse(ZabbixConfigBase):
    """Zabbix配置响应模型"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
