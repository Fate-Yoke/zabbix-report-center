"""
导出任务相关Pydantic模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ExportTaskCreate(BaseModel):
    """导出任务创建模型"""
    zabbix_config_id: int
    filter_ids: List[int]
    include_device_overview: bool = True


class ExportTaskResponse(BaseModel):
    """导出任务响应模型"""
    id: int
    zabbix_config_id: int
    zabbix_config_name: Optional[str] = None
    filter_ids: List[int]
    filter_names: Optional[List[str]] = None
    include_device_overview: bool = True
    status: str
    file_path: Optional[str] = None
    filename: Optional[str] = None
    error_message: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
