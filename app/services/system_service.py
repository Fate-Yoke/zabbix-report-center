"""
系统设置服务
"""
from sqlalchemy.orm import Session
from app.models.system_settings import SystemSettings


class SystemService:
    """系统设置服务"""

    @staticmethod
    def get_setting(db: Session, key: str, default: str = None) -> str:
        """获取系统设置值"""
        setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if setting:
            return setting.value
        return default

    @staticmethod
    def set_setting(db: Session, key: str, value: str, description: str = None) -> SystemSettings:
        """设置系统设置值"""
        setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SystemSettings(key=key, value=value, description=description)
            db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

    @staticmethod
    def is_registration_allowed(db: Session) -> bool:
        """检查是否允许注册"""
        value = SystemService.get_setting(db, "allow_registration", "true")
        return value.lower() in ("true", "1", "yes")

    @staticmethod
    def is_activation_required(db: Session) -> bool:
        """检查注册后是否需要管理员手动启用"""
        value = SystemService.get_setting(db, "require_activation", "false")
        return value.lower() in ("true", "1", "yes")

    @staticmethod
    def set_activation_required(db: Session, required: bool) -> SystemSettings:
        """设置注册后是否需要管理员手动启用"""
        return SystemService.set_setting(
            db,
            "require_activation",
            "true" if required else "false",
            "注册后是否需要管理员手动启用账户"
        )

    @staticmethod
    def set_registration_allowed(db: Session, allowed: bool) -> SystemSettings:
        """设置是否允许注册"""
        return SystemService.set_setting(
            db,
            "allow_registration",
            "true" if allowed else "false",
            "是否允许新用户注册"
        )

    @staticmethod
    def get_all_settings(db: Session) -> list:
        """获取所有系统设置"""
        return db.query(SystemSettings).all()


# 全局实例
system_service = SystemService()
