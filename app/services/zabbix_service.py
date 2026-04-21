"""
Zabbix API服务
"""
import re
import logging
from typing import List, Dict, Any, Optional
from statistics import mean
import requests

from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)


class ZabbixService:
    """Zabbix API服务类"""

    def __init__(self, url: str, auth_type: str, token: str = None, username: str = None, password: str = None):
        self.url = url
        self.auth_type = auth_type
        self.token = token
        self.username = username
        self.password = password
        self.headers = {"Content-Type": "application/json"}
        self._auth_token = None  # 用于存储登录后的auth token

    @classmethod
    def from_config(cls, config) -> "ZabbixService":
        """从配置对象创建实例"""
        # 解密敏感信息
        token = encryption_service.decrypt(config.token) if config.token else None
        username = encryption_service.decrypt(config.username) if config.username else None
        password = encryption_service.decrypt(config.password) if config.password else None

        return cls(
            url=config.url,
            auth_type=config.auth_type,
            token=token,
            username=username,
            password=password
        )

    def _login(self) -> str:
        """使用用户名密码登录，获取auth token"""
        if self._auth_token:
            return self._auth_token

        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "username": self.username,
                "password": self.password
            },
            "id": 1
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(data["error"].get("data", str(data["error"])))

            self._auth_token = data["result"]
            return self._auth_token
        except Exception as e:
            logger.error(f"Zabbix登录失败: {e}")
            raise

    def _get_auth_header(self) -> Dict[str, str]:
        """获取认证头（仅用于API Token方式）"""
        if self.auth_type == "token" and self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _call_api(self, method: str, params: Dict, use_auth: bool = True) -> Any:
        """调用Zabbix API"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        # 如果使用密码认证，或者token认证但token为空时使用密码
        if use_auth and (self.auth_type == "password" or (self.auth_type == "token" and not self.token)):
            if self.username and self.password:
                if not self._auth_token:
                    self._login()
                payload["auth"] = self._auth_token

        headers = self.headers.copy()
        # API Token方式使用Header认证（仅当token存在时）
        if use_auth and self.auth_type == "token" and self.token:
            headers.update(self._get_auth_header())

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(data["error"].get("data", str(data["error"])))

            return data["result"]
        except Exception as e:
            logger.error(f"Zabbix API调用失败: {method} - {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            # 测试API连通性
            version = self._call_api("apiinfo.version", {}, use_auth=False)

            # 测试鉴权
            if self.auth_type == "token" and self.token:
                self._call_api("host.get", {"limit": 1}, use_auth=True)
            elif self.auth_type == "password" and self.username and self.password:
                self._call_api("host.get", {"limit": 1}, use_auth=True)

            return {"success": True, "version": version}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_hosts(self) -> List[Dict]:
        """获取所有主机"""
        return self._call_api("host.get", {
            "output": ["hostid", "name"],
            "selectInterfaces": ["ip"],
            "selectGroups": ["name"]
        })

    def get_host_status(self, hostid: str) -> Dict[str, Any]:
        """获取主机在线状态(ICMP ping)"""
        try:
            # 获取ICMP监控项
            icmp_items = self._call_api("item.get", {
                "output": ["itemid", "value_type"],
                "hostids": hostid,
                "search": {"name": "ICMP ping"}
            })

            if not icmp_items:
                return {"status": "unknown", "has_icmp": False}

            icmp_item = icmp_items[0]
            value_type = int(icmp_item.get("value_type", 3))

            # 获取最新值
            history = self._call_api("history.get", {
                "history": value_type,
                "itemids": icmp_item["itemid"],
                "sortfield": "clock",
                "sortorder": "DESC",
                "limit": 1
            })

            if not history:
                return {"status": "offline", "has_icmp": True}

            value = str(history[0]["value"]).strip()
            status = "online" if value == "1" else "offline"

            return {"status": status, "has_icmp": True}
        except Exception as e:
            logger.error(f"获取主机状态失败: {e}")
            return {"status": "unknown", "has_icmp": False, "error": str(e)}

    def get_items(self, hostid: str, search: str = None) -> List[Dict]:
        """获取主机的监控项"""
        params = {
            "output": ["itemid", "name", "key_"],
            "hostids": hostid
        }
        if search:
            params["search"] = {"name": search}
            params["searchWildcardsEnabled"] = True

        return self._call_api("item.get", params)

    def get_item_history(self, itemid: str, history_type: int = 0,
                         time_from: int = None, time_till: int = None) -> List[Dict]:
        """获取监控项历史数据"""
        params = {
            "history": history_type,
            "itemids": itemid,
            "sortfield": "clock",
            "sortorder": "DESC"
        }
        if time_from:
            params["time_from"] = time_from
        if time_till:
            params["time_till"] = time_till

        return self._call_api("history.get", params)

    def get_item_stats(self, hostid: str, item_pattern: str,
                       history_type: int = 0, use_regex: bool = False,
                       is_network: bool = False, is_storage: bool = False,
                       time_from: int = None, time_till: int = None) -> List[Dict]:
        """
        获取监控项统计数据
        返回: [{"name": str, "current": float, "max": float, "min": float, "avg": float}]
        """
        try:
            # 获取所有监控项
            items = self._call_api("item.get", {
                "output": ["itemid", "name"],
                "hostids": hostid
            })

            # 匹配监控项
            matched_items = []
            for item in items:
                if use_regex:
                    if re.search(item_pattern, item["name"], re.IGNORECASE):
                        matched_items.append(item)
                else:
                    if item_pattern in item["name"]:
                        matched_items.append(item)

            results = []
            for item in matched_items:
                history = self.get_item_history(
                    item["itemid"], history_type, time_from, time_till
                )

                values = [float(h["value"]) for h in history if h["value"] is not None]
                if not values:
                    continue

                # 网络流量需要单位转换 (bps -> Mbps)
                if is_network:
                    values = [round(v / 1_000_000, 4) for v in values]

                # 存储需要单位转换 (B -> GB)
                if is_storage:
                    values = [round(v / 1_073_741_824, 6) for v in values]

                results.append({
                    "name": item["name"],
                    "current": round(values[0], 2),
                    "max": round(max(values), 2),
                    "min": round(min(values), 2),
                    "avg": round(mean(values), 2)
                })

            return results
        except Exception as e:
            logger.error(f"获取监控数据失败: {e}")
            return []

    def get_all_hosts_with_status(self) -> Dict[str, List[Dict]]:
        """获取所有主机及其状态"""
        hosts = self.get_hosts()
        online_hosts = []
        offline_hosts = []
        checked_count = 0

        for host in hosts:
            hostid = host["hostid"]
            hostname = host.get("name", "")
            ip = host.get("interfaces", [{}])[0].get("ip", "N/A") if host.get("interfaces") else "N/A"
            groups = ", ".join([g["name"] for g in host.get("groups", [])])

            status_info = self.get_host_status(hostid)

            host_data = {
                "hostid": hostid,
                "name": hostname,
                "ip": ip,
                "groups": groups
            }

            if not status_info.get("has_icmp"):
                continue  # 跳过没有ICMP监控的主机

            checked_count += 1

            if status_info["status"] == "online":
                online_hosts.append(host_data)
            else:
                offline_hosts.append(host_data)

        return {
            "total": checked_count,
            "online": online_hosts,
            "offline": offline_hosts
        }

    def get_alerts(self, time_from: int = None, time_till: int = None,
                   severity: List[int] = None, recovered: Optional[bool] = None) -> List[Dict]:
        """
        获取告警信息

        参数:
            time_from: 开始时间戳
            time_till: 结束时间戳
            severity: 告警级别列表 [0-5]
            recovered: None=全部, True=已恢复, False=未恢复

        返回:
            [{
                "eventid": str,
                "severity": int,  # 0=未分类,1=信息,2=警告,3=一般严重,4=严重,5=灾难
                "severity_name": str,
                "name": str,  # 告警信息
                "clock": int,  # 发生时间戳
                "r_clock": int,  # 恢复时间戳
                "acknowledged": int,  # 是否确认
                "host_name": str,  # 主机名
                "host_ip": str,  # 主机IP
                "host_groups": str,  # 主机群组
                "duration": int,  # 持续时间（秒）
                "recovered": bool  # 是否已恢复
            }]
        """
        try:
            logger.info(f"开始获取告警信息 - time_from: {time_from}, time_till: {time_till}, severity: {severity}, recovered: {recovered}")

            # 构建查询参数
            params = {
                "output": ["eventid", "name", "severity", "clock", "r_eventid", "acknowledged"],
                "selectHosts": ["hostid", "name", "host"],
                "selectRelatedObject": ["description"],
                "source": 0,  # 0=trigger事件
                "object": 0,  # 0=trigger
                "sortfield": ["clock"],
                "sortorder": "DESC",
                "limit": 1000
            }

            # 时间范围
            if time_from:
                params["time_from"] = time_from
            if time_till:
                params["time_till"] = time_till

            # 告警级别
            if severity:
                params["severities"] = severity

            logger.info(f"调用 event.get API，参数: {params}")

            # 获取事件
            events = self._call_api("event.get", params)

            logger.info(f"API返回 {len(events) if events else 0} 条事件")

            severity_map = {
                0: "未分类",
                1: "信息",
                2: "警告",
                3: "一般严重",
                4: "严重",
                5: "灾难"
            }

            # 批量收集所有需要的hostid和r_eventid
            hostids = set()
            r_eventids = []
            for event in events:
                hosts = event.get("hosts", [])
                if hosts:
                    hostids.add(hosts[0].get("hostid"))
                r_eventid = event.get("r_eventid", "0")
                if r_eventid != "0":
                    r_eventids.append(r_eventid)

            # 批量获取主机详情
            host_details_map = {}
            if hostids:
                try:
                    host_details = self._call_api("host.get", {
                        "output": ["hostid"],
                        "selectInterfaces": ["ip"],
                        "selectGroups": ["name"],
                        "hostids": list(hostids)
                    })
                    for host_detail in host_details:
                        hostid = host_detail.get("hostid")
                        host_ip = "N/A"
                        host_groups = "N/A"

                        interfaces = host_detail.get("interfaces", [])
                        if interfaces:
                            host_ip = interfaces[0].get("ip", "N/A")

                        groups = host_detail.get("groups", [])
                        if groups:
                            host_groups = ", ".join([g["name"] for g in groups])

                        host_details_map[hostid] = {
                            "ip": host_ip,
                            "groups": host_groups
                        }
                except Exception as e:
                    logger.warning(f"批量获取主机详情失败: {e}")

            # 批量获取恢复事件时间
            recovery_times_map = {}
            if r_eventids:
                try:
                    recovery_events = self._call_api("event.get", {
                        "output": ["eventid", "clock"],
                        "eventids": r_eventids
                    })
                    for recovery_event in recovery_events:
                        eventid = recovery_event.get("eventid")
                        clock = int(recovery_event.get("clock", 0))
                        recovery_times_map[eventid] = clock
                except Exception as e:
                    logger.warning(f"批量获取恢复事件时间失败: {e}")

            # 处理事件数据
            results = []
            import time
            current_time = int(time.time())

            for event in events:
                # 获取主机信息
                hosts = event.get("hosts", [])
                if not hosts:
                    continue

                host = hosts[0]
                hostid = host.get("hostid")
                host_name = host.get("name", "N/A")

                # 从缓存中获取主机详情
                host_detail = host_details_map.get(hostid, {})
                host_ip = host_detail.get("ip", "N/A")
                host_groups = host_detail.get("groups", "N/A")

                # 计算持续时间和恢复状态
                clock = int(event.get("clock", 0))
                r_eventid = event.get("r_eventid", "0")
                r_clock = recovery_times_map.get(r_eventid, 0) if r_eventid != "0" else 0

                if r_clock > 0:
                    duration = r_clock - clock
                    is_recovered = True
                else:
                    duration = current_time - clock
                    is_recovered = False

                # 根据恢复状态筛选
                if recovered is not None:
                    if recovered != is_recovered:
                        continue

                severity_level = int(event.get("severity", 0))

                results.append({
                    "eventid": event.get("eventid"),
                    "severity": severity_level,
                    "severity_name": severity_map.get(severity_level, "未知"),
                    "name": event.get("name", "N/A"),
                    "clock": clock,
                    "r_clock": r_clock if r_clock > 0 else None,
                    "acknowledged": int(event.get("acknowledged", 0)),
                    "host_name": host_name,
                    "host_ip": host_ip,
                    "host_groups": host_groups,
                    "duration": duration,
                    "recovered": is_recovered
                })

            return results

        except Exception as e:
            logger.error(f"获取告警信息失败: {e}")
            return []
