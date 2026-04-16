"""
监控服务
"""
import time
import logging
from typing import Dict, List, Any

from sqlalchemy.orm import Session

from app.models.monitor_filter import MonitorFilter
from app.services.zabbix_service import ZabbixService

logger = logging.getLogger(__name__)


class MonitorService:
    """监控服务类"""

    def __init__(self, zabbix_service: ZabbixService):
        self.zabbix_service = zabbix_service

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        hosts_data = self.zabbix_service.get_all_hosts_with_status()
        return {
            "total": hosts_data["total"],
            "online_count": len(hosts_data["online"]),
            "offline_count": len(hosts_data["offline"]),
            "online_hosts": hosts_data["online"],
            "offline_hosts": hosts_data["offline"]
        }

    def get_monitor_data(self, filter_config: MonitorFilter, time_range: int = 86400) -> List[Dict]:
        """
        根据筛选配置获取监控数据
        """
        # 获取所有在线主机
        hosts_data = self.zabbix_service.get_all_hosts_with_status()
        online_hosts = hosts_data["online"]

        # 计算时间范围
        time_till = int(time.time())
        time_from = time_till - time_range

        results = []
        for host in online_hosts:
            hostid = host["hostid"]
            hostname = host["name"]
            ip = host["ip"]
            groups = host["groups"]

            # 判断使用哪种匹配模式
            if filter_config.use_regex:
                # 正则表达式模式
                pattern = filter_config.regex_pattern
                if pattern:
                    items_data = self.zabbix_service.get_item_stats(
                        hostid=hostid,
                        item_pattern=pattern,
                        history_type=filter_config.history_type,
                        use_regex=True,
                        is_network=filter_config.is_network,
                        time_from=time_from,
                        time_till=time_till
                    )

                    for item in items_data:
                        results.append({
                            "hostid": hostid,
                            "hostname": hostname,
                            "ip": ip,
                            "groups": groups,
                            "item_name": item["name"],
                            "current": item["current"],
                            "max": item["max"],
                            "min": item["min"],
                            "avg": item["avg"]
                        })
            else:
                # 列表模式：对每个监控项模式获取数据
                for pattern_obj in filter_config.item_patterns:
                    # 兼容新旧格式
                    if isinstance(pattern_obj, dict):
                        pattern = pattern_obj.get('pattern', '')
                        match_type = pattern_obj.get('match_type', 'exact')
                    else:
                        # 旧格式：字符串
                        pattern = pattern_obj
                        match_type = 'exact'

                    if not pattern:
                        continue

                    # match_type: 'exact' 精确匹配, 'fuzzy' 模糊匹配（支持通配符）
                    use_regex = (match_type == 'fuzzy')

                    # 如果是模糊匹配，将通配符转换为正则表达式
                    if use_regex:
                        # 转义正则特殊字符，但保留 * 和 ?
                        import re
                        # 先转义所有正则特殊字符
                        pattern = re.escape(pattern)
                        # 然后将通配符转换为正则表达式
                        pattern = pattern.replace(r'\*', '.*')  # * 匹配任意字符
                        pattern = pattern.replace(r'\?', '.')   # ? 匹配单个字符

                    items_data = self.zabbix_service.get_item_stats(
                        hostid=hostid,
                        item_pattern=pattern,
                        history_type=filter_config.history_type,
                        use_regex=use_regex,
                        is_network=filter_config.is_network,
                        time_from=time_from,
                        time_till=time_till
                    )

                    for item in items_data:
                        results.append({
                            "hostid": hostid,
                            "hostname": hostname,
                            "ip": ip,
                            "groups": groups,
                            "item_name": item["name"],
                            "current": item["current"],
                            "max": item["max"],
                            "min": item["min"],
                            "avg": item["avg"]
                        })

        return results

    def get_multiple_filters_data(self, db: Session, filter_ids: List[int],
                                   time_range: int = 86400) -> Dict[str, List[Dict]]:
        """获取多个筛选配置的数据"""
        result = {}
        for filter_id in filter_ids:
            filter_config = db.query(MonitorFilter).filter(MonitorFilter.id == filter_id).first()
            if filter_config:
                result[filter_config.name] = self.get_monitor_data(filter_config, time_range)
        return result

    def get_all_items_for_host(self, hostid: str, search: str = None) -> List[Dict]:
        """获取主机的所有监控项（用于配置筛选）"""
        return self.zabbix_service.get_items(hostid, search)
