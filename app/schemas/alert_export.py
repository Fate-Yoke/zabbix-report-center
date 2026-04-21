"""
告警导出任务Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AlertExportTaskCreate(BaseModel):
    """创建告警导出任务"""
    zabbix_config_id: int
    time_from: Optional[int] = None
    time_till: Optional[int] = None
    severity: Optional[List[int]] = None
    recovered: Optional[str] = None


class AlertExportTaskResponse(BaseModel):
    """告警导出任务响应"""
    id: int
    zabbix_config_id: int
    zabbix_config_name: Optional[str]
    time_from: Optional[int]
    time_till: Optional[int]
    severity: Optional[str]
    recovered: Optional[str]
    status: str
    file_path: Optional[str]
    filename: Optional[str]
    error_message: Optional[str]
    total_count: int
    created_by: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
