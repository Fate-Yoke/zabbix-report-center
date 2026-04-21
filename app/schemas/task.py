"""
定时任务相关Pydantic模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ScheduleTaskBase(BaseModel):
    """定时任务基础模型"""
    name: str
    description: Optional[str] = None
    cron_expression: str  # cron表达式
    monitor_filter_ids: List[int]  # 关联的监控筛选配置ID列表
    include_device_overview: bool = True  # Excel是否包含设备概览工作簿
    include_alert_data: bool = False  # Excel是否包含告警数据工作簿
    recipients: List[str]  # 收件人邮箱列表
    zabbix_config_id: int
    email_config_id: Optional[int] = None
    time_range: int = 86400  # 监控时间范围(秒)，默认24小时
    email_subject: Optional[str] = None  # 邮件标题
    email_body: Optional[str] = None  # 邮件内容
    subject_suffix_config_name: bool = False  # 标题是否添加配置名称
    subject_suffix_timestamp: bool = False  # 标题是否添加时间戳
    email_include_device_overview: bool = True  # 邮件内容是否包含设备概览摘要
    email_include_monitor_summary: bool = True  # 邮件内容是否包含监控数据摘要
    email_include_alert_summary: bool = False  # 邮件内容是否包含告警数据摘要


class ScheduleTaskCreate(ScheduleTaskBase):
    """定时任务创建模型"""
    pass


class ScheduleTaskUpdate(BaseModel):
    """定时任务更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    monitor_filter_ids: Optional[List[int]] = None
    include_device_overview: Optional[bool] = None
    include_alert_data: Optional[bool] = None
    recipients: Optional[List[str]] = None
    zabbix_config_id: Optional[int] = None
    email_config_id: Optional[int] = None
    time_range: Optional[int] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    subject_suffix_config_name: Optional[bool] = None
    subject_suffix_timestamp: Optional[bool] = None
    email_include_device_overview: Optional[bool] = None
    email_include_monitor_summary: Optional[bool] = None
    email_include_alert_summary: Optional[bool] = None
    is_active: Optional[bool] = None


class ScheduleTaskResponse(BaseModel):
    """定时任务响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    cron_expression: str
    monitor_filter_ids: List[int]
    include_device_overview: bool = True
    include_alert_data: bool = False
    recipients: List[str]
    zabbix_config_id: int
    email_config_id: Optional[int] = None
    time_range: int = 86400
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    subject_suffix_config_name: bool = False
    subject_suffix_timestamp: bool = False
    email_include_device_overview: bool = True
    email_include_monitor_summary: bool = True
    email_include_alert_summary: bool = False
    is_active: bool
    is_valid: bool = True  # 配置是否有效（Zabbix配置和邮件配置都存在且激活）
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    """任务日志响应模型"""
    id: int
    task_id: int
    status: str
    message: Optional[str] = None
    recipients: Optional[List[str]] = None
    attachment_path: Optional[str] = None
    attachment_filename: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True
