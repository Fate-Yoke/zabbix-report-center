"""
邮件配置管理API
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.email_config import EmailConfig
from app.schemas.email import (
    EmailConfigCreate, EmailConfigUpdate, EmailConfigResponse
)
from app.api.auth import get_admin_user, get_current_user_required
from app.services.email_service import EmailService
from app.services.encryption_service import encryption_service

router = APIRouter(prefix="/email-config", tags=["邮件配置"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[EmailConfigResponse])
async def list_configs(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取邮件配置列表"""
    print(f"[DEBUG] list_configs called by user: {user.username}, is_admin: {user.is_admin}")
    # 普通用户只能看到激活的配置
    if not user.is_admin:
        configs = db.query(EmailConfig).filter(EmailConfig.is_active == True).all()
    else:
        configs = db.query(EmailConfig).all()
    print(f"[DEBUG] Returning {len(configs)} email configs")
    return configs


@router.post("", response_model=EmailConfigResponse)
async def create_config(
    config_data: EmailConfigCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """创建邮件配置（管理员）"""
    # 检查名称是否已存在
    existing = db.query(EmailConfig).filter(EmailConfig.name == config_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置名称已存在")

    # 加密密码
    smtp_pass = encryption_service.encrypt(config_data.smtp_pass)

    config = EmailConfig(
        name=config_data.name,
        smtp_server=config_data.smtp_server,
        smtp_port=config_data.smtp_port,
        smtp_user=config_data.smtp_user,
        smtp_pass=smtp_pass,
        use_ssl=config_data.use_ssl,
        mail_from=config_data.mail_from
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    logger.info(f"管理员 {admin.username} 创建邮件配置: {config.name} (ID: {config.id}), SMTP: {config.smtp_server}:{config.smtp_port}")

    return config


@router.get("/{config_id}", response_model=EmailConfigResponse)
async def get_config(
    config_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取邮件配置详情（管理员）"""
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.put("/{config_id}", response_model=EmailConfigResponse)
async def update_config(
    config_id: int,
    config_data: EmailConfigUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """更新邮件配置（管理员）"""
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 检查名称是否被其他配置使用
    if config_data.name is not None and config_data.name != config.name:
        existing = db.query(EmailConfig).filter(
            EmailConfig.name == config_data.name,
            EmailConfig.id != config_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="配置名称已存在")

    if config_data.name is not None:
        config.name = config_data.name
    if config_data.smtp_server is not None:
        config.smtp_server = config_data.smtp_server
    if config_data.smtp_port is not None:
        config.smtp_port = config_data.smtp_port
    if config_data.smtp_user is not None:
        config.smtp_user = config_data.smtp_user
    if config_data.smtp_pass is not None:
        config.smtp_pass = encryption_service.encrypt(config_data.smtp_pass)
    if config_data.use_ssl is not None:
        config.use_ssl = config_data.use_ssl
    if config_data.mail_from is not None:
        config.mail_from = config_data.mail_from
    if config_data.is_active is not None:
        config.is_active = config_data.is_active

    db.commit()
    db.refresh(config)

    logger.info(f"管理员 {admin.username} 更新邮件配置: {config.name} (ID: {config.id})")

    return config


@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """删除邮件配置（管理员）"""
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config_name = config.name
    db.delete(config)
    db.commit()

    logger.info(f"管理员 {admin.username} 删除邮件配置: {config_name} (ID: {config_id})")

    return {"message": "删除成功"}


@router.get("/{config_id}/test")
async def test_config(
    config_id: int,
    to_addr: str = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """测试邮件配置（管理员）- 发送测试邮件"""
    config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 如果没有指定收件人，发给发件人自己
    recipient = to_addr if to_addr else config.mail_from

    email_service = EmailService.from_config(config)

    # 发送测试邮件
    from datetime import datetime
    subject = f"测试邮件 - {config.name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    body = f"""这是一封测试邮件。

邮件配置名称：{config.name}
SMTP服务器：{config.smtp_server}:{config.smtp_port}
发件人：{config.mail_from}
测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如果您收到此邮件，说明邮件配置正确。
"""

    result = email_service.send_email(
        to_addrs=[recipient],
        subject=subject,
        body=body
    )

    if result["success"]:
        logger.info(f"管理员 {admin.username} 发送测试邮件: 配置 {config.name}, 收件人 {recipient}")
    else:
        logger.warning(f"管理员 {admin.username} 发送测试邮件失败: 配置 {config.name}, 错误: {result.get('error', '未知错误')}")

    if result["success"]:
        return {
            "success": True,
            "message": f"测试邮件已发送至 {recipient}，请检查收件箱"
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "发送失败"),
            "message": f"发送失败: {result.get('error', '未知错误')}"
        }
