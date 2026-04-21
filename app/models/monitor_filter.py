"""
监控筛选配置模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


class MonitorFilter(Base):
    """监控筛选配置表"""
    __tablename__ = "monitor_filters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 如 "CPU使用率"
    description = Column(Text, nullable=True)

    # 监控项匹配配置
    use_regex = Column(Boolean, default=False)  # 是否使用正则匹配
    regex_pattern = Column(String(500), nullable=True)  # 正则表达式（use_regex=True时使用）
    item_patterns = Column(JSON, nullable=True)  # 监控项列表（use_regex=False时使用）
    # item_patterns 格式: [{"pattern": "CPU usage", "match_type": "exact"}, {"pattern": "Memory", "match_type": "fuzzy"}]
    # match_type: "exact" 精确匹配, "fuzzy" 模糊匹配

    history_type = Column(Integer, default=0)  # 历史数据类型
    is_network = Column(Boolean, default=False)  # 是否网络流量(需单位转换 bps→Mbps)
    is_storage = Column(Boolean, default=False)  # 是否存储(需单位转换 B→GB)
    thresholds = Column(JSON, nullable=True)  # 阈值配置 {"green": 75, "yellow": 85}
    zabbix_config_ids = Column(JSON, default=list)  # 关联的Zabbix配置ID列表
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<MonitorFilter {self.name}>"
