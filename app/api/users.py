"""
用户管理API
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.auth import get_admin_user, auth_service

router = APIRouter(prefix="/users", tags=["用户管理"])
logger = logging.getLogger(__name__)


class AdminUserCreate(BaseModel):
    """管理员创建用户模型"""
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False
    is_active: bool = True
    allowed_zabbix_ids: List[int] = []


@router.get("", response_model=List[UserResponse])
async def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取用户列表（管理员）"""
    users = db.query(User).all()
    return users


@router.post("", response_model=UserResponse)
async def create_user(
    user_data: AdminUserCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """创建用户（管理员）"""
    # 检查用户名是否存在
    if auth_service.get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否存在
    if auth_service.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="邮箱已被使用")

    # 创建用户
    hashed_password = auth_service.hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        is_admin=user_data.is_admin,
        is_active=user_data.is_active,
        allowed_zabbix_ids=user_data.allowed_zabbix_ids
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"管理员 {admin.username} 创建用户: {user.username} (ID: {user.id}), 管理员: {user.is_admin}")

    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取用户详情（管理员）"""
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户（管理员）"""
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    if user_data.username is not None:
        # 检查用户名是否被其他用户使用
        existing = auth_service.get_user_by_username(db, user_data.username)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="用户名已被使用")
        user.username = user_data.username

    if user_data.email is not None:
        # 检查邮箱是否被其他用户使用
        existing = auth_service.get_user_by_email(db, user_data.email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = user_data.email

    if user_data.password is not None:
        user.password_hash = auth_service.hash_password(user_data.password)

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin

    if user_data.allowed_zabbix_ids is not None:
        user.allowed_zabbix_ids = user_data.allowed_zabbix_ids

    db.commit()
    db.refresh(user)

    logger.info(f"管理员 {admin.username} 更新用户: {user.username} (ID: {user.id})")

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """删除用户（管理员）"""
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能删除自己
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    # 不能删除最后一个管理员
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="不能删除最后一个管理员")

    username = user.username
    db.delete(user)
    db.commit()

    logger.info(f"管理员 {admin.username} 删除用户: {username} (ID: {user_id})")

    return {"message": "删除成功"}
