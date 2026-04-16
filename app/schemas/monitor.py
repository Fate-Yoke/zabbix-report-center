"""
监控筛选配置相关Pydantic模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator


class ItemPattern(BaseModel):
    """监控项匹配模式"""
    pattern: str  # 匹配模式字符串
    match_type: str  # 匹配类型: "exact" 精确匹配, "fuzzy" 模糊匹配


class MonitorFilterBase(BaseModel):
    """监控筛选配置基础模型"""
    name: str
    description: Optional[str] = None
    use_regex: bool = False  # 是否使用正则匹配
    regex_pattern: Optional[str] = None  # 正则表达式（use_regex=True时使用）
    item_patterns: Optional[List[ItemPattern]] = None  # 监控项列表（use_regex=False时使用）
    history_type: int = 0
    is_network: bool = False
    thresholds: Optional[Dict[str, Any]] = None  # {"green": 75, "yellow": 85}
    zabbix_config_ids: List[int] = []  # 关联的Zabbix配置ID列表


class MonitorFilterCreate(MonitorFilterBase):
    """监控筛选配置创建模型"""
    pass


class MonitorFilterUpdate(BaseModel):
    """监控筛选配置更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    use_regex: Optional[bool] = None
    regex_pattern: Optional[str] = None
    item_patterns: Optional[List[ItemPattern]] = None
    history_type: Optional[int] = None
    is_network: Optional[bool] = None
    thresholds: Optional[Dict[str, Any]] = None
    zabbix_config_ids: Optional[List[int]] = None


class MonitorFilterResponse(MonitorFilterBase):
    """监控筛选配置响应模型"""
    id: int
    created_by: Optional[int] = None
    created_at: datetime

    @field_validator('zabbix_config_ids', mode='before')
    @classmethod
    def validate_zabbix_config_ids(cls, v):
        """确保 zabbix_config_ids 始终是列表"""
        if v is None:
            return []
        return v

    class Config:
        from_attributes = True
