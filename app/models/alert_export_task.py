"""
告警导出任务模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from app.database import Base


class AlertExportTask(Base):
    """告警导出任务表"""
    __tablename__ = "alert_export_tasks"

    id = Column(Integer, primary_key=True, index=True)
    zabbix_config_id = Column(Integer, nullable=False)
    zabbix_config_name = Column(String(100), nullable=True)  # 冗余存储，方便显示
    time_from = Column(Integer, nullable=True)  # 开始时间戳
    time_till = Column(Integer, nullable=True)  # 结束时间戳
    severity = Column(String(50), nullable=True)  # 告警级别，逗号分隔，如: "3,4,5"
    recovered = Column(String(20), nullable=True)  # 恢复状态: recovered/unrecovered/all
    status = Column(String(20), default="pending")  # pending/processing/completed/failed
    file_path = Column(String(500), nullable=True)  # 生成的文件路径
    filename = Column(String(200), nullable=True)  # 文件名
    error_message = Column(Text, nullable=True)  # 错误信息
    total_count = Column(Integer, default=0)  # 导出的告警总数
    created_by = Column(Integer, nullable=True)  # 创建用户ID
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AlertExportTask {self.id} - {self.status}>"
