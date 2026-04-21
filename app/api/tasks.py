"""
定时任务API
"""
import os
import logging
import threading
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.schedule_task import ScheduleTask, TaskLog
from app.models.zabbix_config import ZabbixConfig
from app.models.email_config import EmailConfig
from app.schemas.task import (
    ScheduleTaskCreate, ScheduleTaskUpdate, ScheduleTaskResponse, TaskLogResponse
)
from app.api.auth import get_current_user_required
from app.services.scheduler_service import scheduler_service, execute_task

router = APIRouter(prefix="/tasks", tags=["定时任务"])
logger = logging.getLogger(__name__)


def check_zabbix_access(user: User, zabbix_config_id: int) -> None:
    """检查用户是否有权限访问指定的Zabbix配置"""
    if not user.can_access_zabbix(zabbix_config_id):
        raise HTTPException(status_code=403, detail="您没有权限访问此Zabbix配置")


@router.get("", response_model=List[ScheduleTaskResponse])
async def list_tasks(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取定时任务列表"""
    all_tasks = db.query(ScheduleTask).all()

    # 获取所有有效的 Zabbix 配置ID
    valid_zabbix_ids = set(db.query(ZabbixConfig.id).filter(ZabbixConfig.is_active == True).all())
    valid_zabbix_ids = {id[0] for id in valid_zabbix_ids}

    # 获取所有有效的邮件配置ID
    valid_email_ids = set(db.query(EmailConfig.id).filter(EmailConfig.is_active == True).all())
    valid_email_ids = {id[0] for id in valid_email_ids}

    print(f"[DEBUG] Valid Zabbix IDs: {valid_zabbix_ids}")
    print(f"[DEBUG] Valid Email IDs: {valid_email_ids}")

    # 为每个任务添加 is_valid 标记
    result_tasks = []
    for task in all_tasks:
        # 检查任务是否有效
        is_valid = True

        print(f"[DEBUG] Task {task.id}: zabbix_config_id={task.zabbix_config_id}, email_config_id={task.email_config_id}")

        # 检查 Zabbix 配置是否有效
        if task.zabbix_config_id not in valid_zabbix_ids:
            print(f"[DEBUG] Task {task.id}: Zabbix config {task.zabbix_config_id} not in valid list")
            is_valid = False

        # 检查邮件配置是否有效（如果设置了邮件配置）
        if task.email_config_id and task.email_config_id not in valid_email_ids:
            print(f"[DEBUG] Task {task.id}: Email config {task.email_config_id} not in valid list")
            is_valid = False

        print(f"[DEBUG] Task {task.id}: is_valid={is_valid}")

        # 管理员可以看到所有任务
        if user.is_admin:
            # 创建响应对象并设置 is_valid
            task_response = ScheduleTaskResponse.model_validate(task)
            task_response.is_valid = is_valid
            result_tasks.append(task_response)
        else:
            # 普通用户只能看到有权限且配置有效的任务
            allowed_ids = user.allowed_zabbix_ids or []
            if is_valid and task.zabbix_config_id in allowed_ids:
                task_response = ScheduleTaskResponse.model_validate(task)
                task_response.is_valid = is_valid
                result_tasks.append(task_response)

    return result_tasks


@router.post("", response_model=ScheduleTaskResponse)
async def create_task(
    task_data: ScheduleTaskCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """创建定时任务"""
    # 检查Zabbix配置权限
    check_zabbix_access(user, task_data.zabbix_config_id)

    task = ScheduleTask(
        name=task_data.name,
        description=task_data.description,
        cron_expression=task_data.cron_expression,
        monitor_filter_ids=task_data.monitor_filter_ids,
        include_device_overview=task_data.include_device_overview,
        recipients=task_data.recipients,
        zabbix_config_id=task_data.zabbix_config_id,
        email_config_id=task_data.email_config_id,
        time_range=task_data.time_range,
        email_subject=task_data.email_subject,
        email_body=task_data.email_body,
        subject_suffix_config_name=task_data.subject_suffix_config_name,
        subject_suffix_timestamp=task_data.subject_suffix_timestamp,
        email_include_device_overview=task_data.email_include_device_overview,
        email_include_monitor_summary=task_data.email_include_monitor_summary,
        email_include_alert_summary=task_data.email_include_alert_summary,
        include_alert_data=task_data.include_alert_data,
        created_by=user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 添加到调度器
    scheduler_service.add_task(task)

    logger.info(f"用户 {user.username} 创建定时任务: {task.name} (ID: {task.id}), Cron: {task.cron_expression}")

    return task


@router.get("/{task_id}", response_model=ScheduleTaskResponse)
async def get_task(
    task_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取定时任务详情"""
    task = db.query(ScheduleTask).filter(ScheduleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}", response_model=ScheduleTaskResponse)
async def update_task(
    task_id: int,
    task_data: ScheduleTaskUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """更新定时任务"""
    print(f"[DEBUG] 更新任务 {task_id}, 收到的数据: email_include_alert_summary={task_data.email_include_alert_summary}, include_alert_data={task_data.include_alert_data}")

    task = db.query(ScheduleTask).filter(ScheduleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 如果要更改Zabbix配置，检查权限
    if task_data.zabbix_config_id is not None:
        check_zabbix_access(user, task_data.zabbix_config_id)

    if task_data.name is not None:
        task.name = task_data.name
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.cron_expression is not None:
        task.cron_expression = task_data.cron_expression
    if task_data.monitor_filter_ids is not None:
        task.monitor_filter_ids = task_data.monitor_filter_ids
    if task_data.include_device_overview is not None:
        task.include_device_overview = task_data.include_device_overview
    if task_data.recipients is not None:
        task.recipients = task_data.recipients
    if task_data.zabbix_config_id is not None:
        task.zabbix_config_id = task_data.zabbix_config_id
    if task_data.email_config_id is not None:
        task.email_config_id = task_data.email_config_id
    if task_data.time_range is not None:
        task.time_range = task_data.time_range
    if task_data.email_subject is not None:
        task.email_subject = task_data.email_subject
    if task_data.email_body is not None:
        task.email_body = task_data.email_body
    if task_data.subject_suffix_config_name is not None:
        task.subject_suffix_config_name = task_data.subject_suffix_config_name
    if task_data.subject_suffix_timestamp is not None:
        task.subject_suffix_timestamp = task_data.subject_suffix_timestamp
    if task_data.email_include_device_overview is not None:
        task.email_include_device_overview = task_data.email_include_device_overview
    if task_data.email_include_monitor_summary is not None:
        task.email_include_monitor_summary = task_data.email_include_monitor_summary
    if task_data.email_include_alert_summary is not None:
        task.email_include_alert_summary = task_data.email_include_alert_summary
    if task_data.include_alert_data is not None:
        task.include_alert_data = task_data.include_alert_data
    if task_data.is_active is not None:
        task.is_active = task_data.is_active

    print(f"[DEBUG] 更新后任务字段值: email_include_alert_summary={task.email_include_alert_summary}, include_alert_data={task.include_alert_data}")

    db.commit()
    db.refresh(task)

    print(f"[DEBUG] 提交后任务字段值: email_include_alert_summary={task.email_include_alert_summary}, include_alert_data={task.include_alert_data}")

    # 更新调度器
    scheduler_service.update_task(task)

    logger.info(f"用户 {user.username} 更新定时任务: {task.name} (ID: {task.id})")

    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """删除定时任务"""
    task = db.query(ScheduleTask).filter(ScheduleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_name = task.name
    # 从调度器移除
    scheduler_service.remove_task(task_id)

    db.delete(task)
    db.commit()

    logger.info(f"用户 {user.username} 删除定时任务: {task_name} (ID: {task_id})")

    return {"message": "删除成功"}


@router.post("/{task_id}/run")
async def run_task_now(
    task_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """立即执行任务（后台线程执行，不阻塞）"""
    task = db.query(ScheduleTask).filter(ScheduleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 使用独立线程执行任务，完全不阻塞
    thread = threading.Thread(target=execute_task, args=(task_id,))
    thread.daemon = True
    thread.start()

    logger.info(f"用户 {user.username} 手动执行定时任务: {task.name} (ID: {task_id})")

    return {"message": "任务已触发执行", "task_id": task_id}


@router.get("/{task_id}/logs", response_model=List[TaskLogResponse])
async def get_task_logs(
    task_id: int,
    limit: int = 20,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取任务执行日志"""
    task = db.query(ScheduleTask).filter(ScheduleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    logs = db.query(TaskLog).filter(
        TaskLog.task_id == task_id
    ).order_by(TaskLog.started_at.desc()).limit(limit).all()

    return logs


@router.get("/logs/{log_id}/download")
async def download_task_attachment(
    log_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """下载任务执行生成的附件"""
    log = db.query(TaskLog).filter(TaskLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志记录不存在")

    if log.status != "success":
        raise HTTPException(status_code=400, detail="任务未成功执行，无法下载")

    if not log.attachment_path or not os.path.exists(log.attachment_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=log.attachment_path,
        filename=log.attachment_filename or "report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
