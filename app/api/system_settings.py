"""
系统设置API
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.system_settings import SystemSettings
from app.api.auth import get_admin_user
from app.services.system_service import system_service

router = APIRouter(prefix="/system", tags=["系统设置"])
logger = logging.getLogger(__name__)


class SettingUpdate(BaseModel):
    """设置更新模型"""
    value: str


class SettingResponse(BaseModel):
    """设置响应模型"""
    id: int
    key: str
    value: str
    description: str = None

    class Config:
        from_attributes = True


class RegistrationStatus(BaseModel):
    """注册状态响应"""
    allowed: bool
    require_activation: bool


class ActivationStatus(BaseModel):
    """启用状态响应"""
    require_activation: bool


@router.get("/registration", response_model=RegistrationStatus)
async def get_registration_status(
    db: Session = Depends(get_db)
):
    """获取注册状态（公开接口）"""
    allowed = system_service.is_registration_allowed(db)
    require_activation = system_service.is_activation_required(db)
    return {"allowed": allowed, "require_activation": require_activation}


@router.put("/registration")
async def set_registration_status(
    data: RegistrationStatus,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """设置注册状态（管理员）"""
    system_service.set_registration_allowed(db, data.allowed)
    if hasattr(data, 'require_activation'):
        system_service.set_activation_required(db, data.require_activation)

    logger.info(f"管理员 {admin.username} 修改注册设置: 允许注册={data.allowed}, 需要激活={data.require_activation}")

    return {"message": f"注册功能已{'开启' if data.allowed else '关闭'}"}


@router.put("/activation")
async def set_activation_status(
    data: ActivationStatus,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """设置注册后是否需要管理员启用（管理员）"""
    system_service.set_activation_required(db, data.require_activation)

    logger.info(f"管理员 {admin.username} 修改激活设置: 需要激活={data.require_activation}")

    return {"message": f"注册后{'需要' if data.require_activation else '不需要'}管理员启用账户"}


@router.get("/settings", response_model=List[SettingResponse])
async def list_settings(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有系统设置（管理员）"""
    settings = system_service.get_all_settings(db)
    return settings


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    data: SettingUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """更新系统设置（管理员）"""
    setting = system_service.set_setting(db, key, data.value)

    logger.info(f"管理员 {admin.username} 修改系统设置: {key}={data.value}")

    return setting
