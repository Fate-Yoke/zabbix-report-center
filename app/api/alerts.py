"""
告警信息API
"""
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import json
import asyncio
import io
import pandas as pd
import os

from app.database import get_db
from app.models.user import User
from app.models.zabbix_config import ZabbixConfig
from app.models.alert_export_task import AlertExportTask
from app.api.auth import get_current_user_required
from app.services.zabbix_service import ZabbixService
from app.services.alert_export_service import do_alert_export
from app.schemas.alert_export import AlertExportTaskCreate, AlertExportTaskResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)


@router.get("/")
async def get_alerts(
    zabbix_config_id: int = Query(..., description="Zabbix配置ID"),
    time_from: Optional[int] = Query(None, description="开始时间戳"),
    time_till: Optional[int] = Query(None, description="结束时间戳"),
    severity: Optional[str] = Query(None, description="告警级别，逗号分隔，如: 3,4,5"),
    recovered: Optional[str] = Query(None, description="恢复状态: recovered/unrecovered/all"),
    limit: int = Query(50, description="返回数量限制，默认50"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取告警信息"""
    # 检查权限
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    if not user.is_admin and zabbix_config_id not in user.allowed_zabbix_ids:
        raise HTTPException(status_code=403, detail="无权访问此Zabbix配置")

    # 解析参数
    severity_list = None
    if severity:
        try:
            severity_list = [int(s.strip()) for s in severity.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="告警级别格式错误")

    recovered_filter = None
    if recovered == "recovered":
        recovered_filter = True
    elif recovered == "unrecovered":
        recovered_filter = False

    # 获取告警数据
    try:
        zabbix = ZabbixService.from_config(config)
        alerts = zabbix.get_alerts(
            time_from=time_from,
            time_till=time_till,
            severity=severity_list,
            recovered=recovered_filter
        )

        # 应用limit限制
        total = len(alerts)
        limited_alerts = alerts[:limit] if limit > 0 else alerts

        return {
            "total": total,
            "returned": len(limited_alerts),
            "alerts": limited_alerts,
            "zabbix_config_name": config.name,
            "has_more": total > len(limited_alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警信息失败: {str(e)}")


@router.get("/stream")
async def stream_alerts(
    zabbix_config_id: int = Query(..., description="Zabbix配置ID"),
    severity: Optional[str] = Query(None, description="告警级别，逗号分隔"),
    recovered: Optional[str] = Query(None, description="恢复状态"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """流式返回告警信息"""
    # 检查权限
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    if not user.is_admin and zabbix_config_id not in user.allowed_zabbix_ids:
        raise HTTPException(status_code=403, detail="无权访问此Zabbix配置")

    # 解析参数
    severity_list = None
    if severity:
        try:
            severity_list = [int(s.strip()) for s in severity.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="告警级别格式错误")

    recovered_filter = None
    if recovered == "recovered":
        recovered_filter = True
    elif recovered == "unrecovered":
        recovered_filter = False

    async def generate():
        """生成告警数据流"""
        try:
            zabbix = ZabbixService.from_config(config)
            alerts = zabbix.get_alerts(
                severity=severity_list,
                recovered=recovered_filter
            )

            # 发送配置信息
            yield f"data: {json.dumps({'type': 'config', 'name': config.name})}\n\n"

            # 逐条发送告警
            for alert in alerts:
                yield f"data: {json.dumps({'type': 'alert', 'data': alert})}\n\n"
                await asyncio.sleep(0.01)  # 避免发送过快

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'total': len(alerts)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/export")
async def export_alerts(
    zabbix_config_id: int = Query(..., description="Zabbix配置ID"),
    time_from: Optional[int] = Query(None, description="开始时间戳"),
    time_till: Optional[int] = Query(None, description="结束时间戳"),
    severity: Optional[str] = Query(None, description="告警级别，逗号分隔"),
    recovered: Optional[str] = Query(None, description="恢复状态"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """导出告警信息为Excel"""
    # 检查权限
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    if not user.is_admin and zabbix_config_id not in user.allowed_zabbix_ids:
        raise HTTPException(status_code=403, detail="无权访问此Zabbix配置")

    # 解析参数
    severity_list = None
    if severity:
        try:
            severity_list = [int(s.strip()) for s in severity.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="告警级别格式错误")

    recovered_filter = None
    if recovered == "recovered":
        recovered_filter = True
    elif recovered == "unrecovered":
        recovered_filter = False

    # 获取告警数据
    try:
        zabbix = ZabbixService.from_config(config)
        alerts = zabbix.get_alerts(
            time_from=time_from,
            time_till=time_till,
            severity=severity_list,
            recovered=recovered_filter
        )

        if not alerts:
            raise HTTPException(status_code=404, detail="没有符合条件的告警数据")

        # 转换为DataFrame
        df_data = []
        for alert in alerts:
            df_data.append({
                "告警级别": alert["severity_name"],
                "主机群组": alert["host_groups"],
                "主机名": alert["host_name"],
                "主机IP": alert["host_ip"],
                "告警信息": alert["name"],
                "发生时间": datetime.fromtimestamp(alert["clock"]).strftime("%Y-%m-%d %H:%M:%S"),
                "恢复时间": datetime.fromtimestamp(alert["r_clock"]).strftime("%Y-%m-%d %H:%M:%S") if alert["r_clock"] else "未恢复",
                "持续时间(秒)": alert["duration"],
                "是否恢复": "是" if alert["recovered"] else "否"
            })

        df = pd.DataFrame(df_data)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{config.name}_alerts_{timestamp}.xlsx"

        # 写入Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='告警信息')

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/export-tasks", response_model=AlertExportTaskResponse)
async def create_alert_export_task(
    task_data: AlertExportTaskCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    创建告警导出任务
    """
    try:
        import traceback
        print(f"[DEBUG] create_alert_export_task called, user: {user.username}, is_admin: {user.is_admin}")
        print(f"[DEBUG] task_data: {task_data}")

        # 检查配置权限
        config = db.query(ZabbixConfig).filter(ZabbixConfig.id == task_data.zabbix_config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Zabbix配置不存在")

        print(f"[DEBUG] config found: {config.name}")

        # 权限检查：管理员可以访问所有配置，普通用户只能访问自己的配置
        if not user.is_admin and not user.can_access_zabbix(task_data.zabbix_config_id):
            raise HTTPException(status_code=403, detail="无权访问此配置")

        print(f"[DEBUG] permission check passed")

        # 创建导出任务
        task = AlertExportTask(
            zabbix_config_id=task_data.zabbix_config_id,
            zabbix_config_name=config.name,
            time_from=task_data.time_from,
            time_till=task_data.time_till,
            severity=",".join(map(str, task_data.severity)) if task_data.severity else None,
            recovered=task_data.recovered,
            status="pending",
            created_by=user.id
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # 添加后台任务
        background_tasks.add_task(do_alert_export, task.id)

        logger.info(f"用户 {user.username} 创建告警导出任务 (ID: {task.id}), 配置: {config.name}")

        return task

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] create_alert_export_task failed: {str(e)}")
        print(f"[ERROR] traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建导出任务失败: {str(e)}")


@router.get("/export-tasks", response_model=List[AlertExportTaskResponse])
async def get_alert_export_tasks(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    获取告警导出任务列表
    """
    try:
        # 管理员可以看到所有任务
        if user.is_admin:
            tasks = db.query(AlertExportTask).order_by(AlertExportTask.created_at.desc()).all()
        else:
            # 普通用户只能看到自己有权限的配置的任务
            user_config_ids = user.allowed_zabbix_ids if user.allowed_zabbix_ids else []
            tasks = db.query(AlertExportTask).filter(
                AlertExportTask.zabbix_config_id.in_(user_config_ids)
            ).order_by(AlertExportTask.created_at.desc()).all()

        return tasks

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导出任务列表失败: {str(e)}")


@router.get("/export-tasks/{task_id}/download")
async def download_alert_export_file(
    task_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    下载告警导出文件
    """
    try:
        # 获取任务
        task = db.query(AlertExportTask).filter(AlertExportTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="导出任务不存在")

        # 权限检查
        if not user.is_admin and not user.can_access_zabbix(task.zabbix_config_id):
            raise HTTPException(status_code=403, detail="无权下载此文件")

        # 检查任务状态
        if task.status != "completed":
            raise HTTPException(status_code=400, detail="任务未完成")

        # 检查文件是否存在
        if not task.file_path or not os.path.exists(task.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            path=task.file_path,
            filename=task.filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")
