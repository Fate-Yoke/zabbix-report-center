"""
认证服务
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User


class AuthService:
    """认证服务类"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """加密密码"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "user_id": user.id,
            "username": user.username,
            "is_admin": user.is_admin,
            "exp": expire
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> Optional[dict]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()

    def create_user(self, db: Session, username: str, email: str, password: str, is_admin: bool = False, is_active: bool = True) -> User:
        """创建用户"""
        hashed_password = self.hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            is_admin=is_admin,
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate_user(self, db: Session, username_or_email: str, password: str) -> Optional[User]:
        """验证用户登录（支持用户名或邮箱）"""
        # 先尝试用户名
        user = self.get_user_by_username(db, username_or_email)
        # 如果用户名找不到，尝试邮箱
        if not user:
            user = self.get_user_by_email(db, username_or_email)

        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    def is_first_user(self, db: Session) -> bool:
        """检查是否是第一个用户"""
        return db.query(User).count() == 0


# 全局实例
auth_service = AuthService()
