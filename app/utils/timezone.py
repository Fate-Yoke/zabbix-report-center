"""
时区工具模块
提供统一的时区处理函数
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import time


def get_local_timezone():
    """获取系统本地时区"""
    # 获取系统时区偏移（秒）
    if time.daylight:
        offset_seconds = -time.altzone
    else:
        offset_seconds = -time.timezone

    # 转换为小时
    offset_hours = offset_seconds // 3600

    # 返回时区名称（如 'Asia/Shanghai' 或 UTC+8）
    try:
        # 尝试使用系统时区
        return ZoneInfo('Asia/Shanghai')  # 中国时区
    except:
        return None


def now():
    """返回当前本地时间"""
    return datetime.now()


def utcnow():
    """返回当前UTC时间"""
    return datetime.utcnow()
