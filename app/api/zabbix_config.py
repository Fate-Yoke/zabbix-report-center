"""
Zabbix配置管理API
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.zabbix_config import ZabbixConfig
from app.schemas.zabbix import (
    ZabbixConfigCreate, ZabbixConfigUpdate, ZabbixConfigResponse
)
from app.api.auth import get_admin_user, get_current_user_required
from app.services.zabbix_service import ZabbixService
from app.services.encryption_service import encryption_service

router = APIRouter(prefix="/zabbix-config", tags=["Zabbix配置"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[ZabbixConfigResponse])
async def list_configs(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取Zabbix配置列表"""
    print(f"[DEBUG] list_configs called by user: {user.username}, is_admin: {user.is_admin}")
    print(f"[DEBUG] user.allowed_zabbix_ids: {user.allowed_zabbix_ids}")

    if user.is_admin:
        # 管理员可以看到所有配置
        configs = db.query(ZabbixConfig).all()
        print(f"[DEBUG] Admin user, returning {len(configs)} configs")
    else:
        # 普通用户只能看到被授权的配置
        allowed_ids = user.allowed_zabbix_ids or []
        print(f"[DEBUG] Regular user, allowed_ids: {allowed_ids}")
        if allowed_ids:
            configs = db.query(ZabbixConfig).filter(ZabbixConfig.id.in_(allowed_ids)).all()
        else:
            configs = []
        print(f"[DEBUG] Returning {len(configs)} configs")

    return configs


@router.post("", response_model=ZabbixConfigResponse)
async def create_config(
    config_data: ZabbixConfigCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """创建Zabbix配置（管理员）"""
    # 检查名称是否已存在
    existing = db.query(ZabbixConfig).filter(ZabbixConfig.name == config_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置名称已存在")

    # 加密敏感信息
    token = encryption_service.encrypt(config_data.token) if config_data.token else None
    username = encryption_service.encrypt(config_data.username) if config_data.username else None
    password = encryption_service.encrypt(config_data.password) if config_data.password else None

    config = ZabbixConfig(
        name=config_data.name,
        url=config_data.url,
        auth_type=config_data.auth_type,
        token=token,
        username=username,
        password=password
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    logger.info(f"管理员 {admin.username} 创建Zabbix配置: {config.name} (ID: {config.id}), URL: {config.url}")

    return config


@router.get("/{config_id}", response_model=ZabbixConfigResponse)
async def get_config(
    config_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取Zabbix配置详情（管理员）"""
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 解密用户名返回给前端显示
    response_data = {
        "id": config.id,
        "name": config.name,
        "url": config.url,
        "auth_type": config.auth_type,
        "username": encryption_service.decrypt(config.username) if config.username else None,
        "is_active": config.is_active,
        "created_at": config.created_at
    }
    return response_data


@router.put("/{config_id}", response_model=ZabbixConfigResponse)
async def update_config(
    config_id: int,
    config_data: ZabbixConfigUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """更新Zabbix配置（管理员）"""
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 检查名称是否被其他配置使用
    if config_data.name is not None and config_data.name != config.name:
        existing = db.query(ZabbixConfig).filter(
            ZabbixConfig.name == config_data.name,
            ZabbixConfig.id != config_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="配置名称已存在")

    if config_data.name is not None:
        config.name = config_data.name
    if config_data.url is not None:
        config.url = config_data.url
    if config_data.auth_type is not None:
        config.auth_type = config_data.auth_type
    if config_data.token is not None:
        config.token = encryption_service.encrypt(config_data.token)
    if config_data.username is not None:
        config.username = encryption_service.encrypt(config_data.username)
    if config_data.password is not None:
        config.password = encryption_service.encrypt(config_data.password)
    if config_data.is_active is not None:
        config.is_active = config_data.is_active

    db.commit()
    db.refresh(config)

    logger.info(f"管理员 {admin.username} 更新Zabbix配置: {config.name} (ID: {config.id})")

    return config


@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """删除Zabbix配置（管理员）"""
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config_name = config.name
    db.delete(config)
    db.commit()

    logger.info(f"管理员 {admin.username} 删除Zabbix配置: {config_name} (ID: {config_id})")

    return {"message": "删除成功"}


@router.get("/{config_id}/test")
async def test_config(
    config_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """测试Zabbix连接（管理员）"""
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    zabbix_service = ZabbixService.from_config(config)
    result = zabbix_service.test_connection()
    return result
