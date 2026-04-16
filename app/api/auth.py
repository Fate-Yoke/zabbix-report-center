"""
认证相关API
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import auth_service
from app.services.captcha_service import captcha_service
from app.services.system_service import system_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    current_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    """更新个人信息请求"""
    username: Optional[str] = None
    email: Optional[str] = None


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户"""
    # 优先从cookie获取token
    if access_token:
        token = access_token

    if not token:
        return None

    payload = auth_service.decode_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    user = auth_service.get_user_by_id(db, user_id)
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """获取当前用户（必须登录）"""
    print(f"[DEBUG] get_current_user_required called, user: {user.username if user else None}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期"
        )
    return user


async def get_admin_user(
    user: User = Depends(get_current_user_required)
) -> User:
    """获取管理员用户"""
    print(f"[DEBUG] get_admin_user called, user: {user.username}, is_admin: {user.is_admin}")
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


@router.get("/captcha")
async def get_captcha():
    """获取验证码"""
    captcha_key, image_bytes = captcha_service.generate()
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"X-Captcha-Key": captcha_key}
    )


@router.post("/register")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查是否允许注册
    if not system_service.is_registration_allowed(db):
        raise HTTPException(status_code=403, detail="系统已关闭注册功能")

    # 验证验证码
    if not captcha_service.verify(user_data.captcha_key, user_data.captcha_code):
        raise HTTPException(status_code=400, detail="验证码错误")

    # 检查用户名是否存在
    if auth_service.get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否存在
    if auth_service.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 判断是否是第一个用户（自动成为管理员）
    is_first = auth_service.is_first_user(db)

    # 检查注册后是否需要管理员手动启用
    require_activation = system_service.is_activation_required(db)
    # 第一个用户（管理员）不需要等待启用
    is_active = not require_activation or is_first

    # 创建用户
    user = auth_service.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        is_admin=is_first,
        is_active=is_active
    )

    logger.info(f"用户注册: {user.username} (ID: {user.id}), 首个用户: {is_first}, 自动启用: {is_active}")

    # 如果需要管理员启用，不自动登录
    if require_activation and not is_first:
        return {
            "success": True,
            "require_activation": True,
            "message": "注册成功，请等待管理员启用账户后再登录"
        }

    # 自动登录，设置cookie
    token = auth_service.create_access_token(user)

    return {
        "success": True,
        "require_activation": False,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        },
        "token": token
    }


@router.post("/login")
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 验证验证码
    if not captcha_service.verify(user_data.captcha_key, user_data.captcha_code):
        raise HTTPException(status_code=400, detail="验证码错误")

    # 验证用户
    user = auth_service.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    logger.info(f"用户登录: {user.username} (ID: {user.id})")

    # 创建token
    token = auth_service.create_access_token(user)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        },
        "token": token
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user_required)
):
    """获取当前用户信息"""
    return user


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 更新用户名
    if request.username is not None:
        # 检查用户名是否被其他用户使用
        existing = auth_service.get_user_by_username(db, request.username)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=400, detail="用户名已被使用")
        user.username = request.username

    # 更新邮箱
    if request.email is not None:
        # 检查邮箱是否被其他用户使用
        existing = auth_service.get_user_by_email(db, request.email)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = request.email

    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证当前密码
    if not auth_service.verify_password(request.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")

    # 验证新密码长度
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6位")

    # 更新密码
    user.password_hash = auth_service.hash_password(request.new_password)
    db.commit()

    logger.info(f"用户修改密码: {user.username} (ID: {user.id})")

    return {"success": True, "message": "密码修改成功"}

