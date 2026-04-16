"""
定时任务模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey
from app.database import Base


class ScheduleTask(Base):
    """定时任务表"""
    __tablename__ = "schedule_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cron_expression = Column(String(50), nullable=False)  # cron表达式
    monitor_filter_ids = Column(JSON, nullable=False)  # 关联的监控筛选配置ID列表
    include_device_overview = Column(Boolean, default=False)  # 是否包含设备概览
    recipients = Column(JSON, nullable=False)  # 收件人邮箱列表
    zabbix_config_id = Column(Integer, ForeignKey("zabbix_configs.id"), nullable=False)
    email_config_id = Column(Integer, ForeignKey("email_configs.id"), nullable=True)
    time_range = Column(Integer, default=86400)  # 监控时间范围(秒)，默认24小时
    # 邮件标题和内容
    email_subject = Column(String(200), nullable=True)  # 邮件标题
    email_body = Column(Text, nullable=True)  # 邮件内容
    subject_suffix_config_name = Column(Boolean, default=False)  # 标题是否添加配置名称
    subject_suffix_timestamp = Column(Boolean, default=False)  # 标题是否添加时间戳
    # 邮件内容附加项
    email_include_device_overview = Column(Boolean, default=True)  # 邮件内容是否包含设备概览摘要
    email_include_monitor_summary = Column(Boolean, default=True)  # 邮件内容是否包含监控数据摘要
    email_include_alert_summary = Column(Boolean, default=False)  # 邮件内容是否包含告警数据摘要
    # Excel附件内容
    include_alert_data = Column(Boolean, default=False)  # Excel附件是否包含告警数据（工作簿）
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ScheduleTask {self.name}>"


class TaskLog(Base):
    """任务执行日志表"""
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("schedule_tasks.id"), nullable=False)
    status = Column(String(20), nullable=False)  # success / failed / running
    message = Column(Text, nullable=True)
    recipients = Column(JSON, nullable=True)  # 实际发送的收件人
    attachment_path = Column(String(255), nullable=True)
    attachment_filename = Column(String(200), nullable=True)  # 文件名
    started_at = Column(DateTime, default=datetime.now)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<TaskLog task_id={self.task_id} status={self.status}>"
