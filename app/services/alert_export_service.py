"""
告警导出服务
"""
import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.alert_export_task import AlertExportTask
from app.models.zabbix_config import ZabbixConfig
from app.services.zabbix_service import ZabbixService
from app.config import BASE_DIR


# 导出目录
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def do_alert_export(task_id: int):
    """
    执行告警导出任务（后台任务）
    """
    db = SessionLocal()
    try:
        # 获取任务
        task = db.query(AlertExportTask).filter(AlertExportTask.id == task_id).first()
        if not task:
            return

        # 更新状态为处理中
        task.status = "processing"
        db.commit()

        # 获取Zabbix配置
        config = db.query(ZabbixConfig).filter(ZabbixConfig.id == task.zabbix_config_id).first()
        if not config:
            task.status = "failed"
            task.error_message = "Zabbix配置不存在"
            db.commit()
            return

        # 获取告警数据
        zabbix = ZabbixService.from_config(config)

        # 解析severity
        severity_list = None
        if task.severity:
            try:
                severity_list = [int(s.strip()) for s in task.severity.split(",")]
            except:
                severity_list = None

        # 解析recovered
        recovered_filter = None
        if task.recovered == "recovered":
            recovered_filter = True
        elif task.recovered == "unrecovered":
            recovered_filter = False

        alerts = zabbix.get_alerts(
            time_from=task.time_from,
            time_till=task.time_till,
            severity=severity_list,
            recovered=recovered_filter
        )

        if not alerts:
            task.status = "failed"
            task.error_message = "没有符合条件的告警数据"
            db.commit()
            return

        # 转换为DataFrame
        df_data = []
        for i, alert in enumerate(alerts, 1):
            df_data.append({
                "序号": i,
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
        file_path = os.path.join(EXPORT_DIR, filename)

        # 写入Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='告警信息')

        # 更新任务状态
        task.status = "completed"
        task.file_path = file_path
        task.filename = filename
        task.total_count = len(alerts)
        task.completed_at = datetime.now()
        db.commit()

    except Exception as e:
        # 更新任务状态为失败
        task = db.query(AlertExportTask).filter(AlertExportTask.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()
