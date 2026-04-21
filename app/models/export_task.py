"""
导出任务模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from app.database import Base


class ExportTask(Base):
    """导出任务表"""
    __tablename__ = "export_tasks"

    id = Column(Integer, primary_key=True, index=True)
    zabbix_config_id = Column(Integer, nullable=False)
    zabbix_config_name = Column(String(100), nullable=True)  # 冗余存储，方便显示
    filter_ids = Column(JSON, nullable=False)  # 筛选配置ID列表
    filter_names = Column(JSON, nullable=True)  # 筛选配置名称列表
    include_device_overview = Column(Boolean, default=True)  # 是否包含设备概览
    status = Column(String(20), default="pending")  # pending/processing/completed/failed/cleaned
    file_path = Column(String(500), nullable=True)  # 生成的文件路径
    filename = Column(String(200), nullable=True)  # 文件名
    error_message = Column(Text, nullable=True)  # 错误信息
    task_type = Column(String(20), default="export")  # export(导出) / query(查询)
    created_by = Column(Integer, nullable=True)  # 创建用户ID
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ExportTask {self.id} - {self.status}>"
