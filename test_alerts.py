#!/usr/bin/env python3
"""测试脚本：验证Zabbix中是否有告警信息"""

import requests
import json
from datetime import datetime, timedelta

# Zabbix配置
# 请修改为你的Zabbix服务器地址和Token
ZABBIX_URL = "http://your-zabbix-server/api_jsonrpc.php"
ZABBIX_TOKEN = "your-zabbix-api-token-here"

def call_zabbix_api(method, params):
    """调用Zabbix API"""
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {ZABBIX_TOKEN}"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            print(f"[错误] API错误: {result['error']}")
            return None

        return result.get("result")
    except Exception as e:
        print(f"[错误] 请求失败: {e}")
        return None

def test_alerts():
    """测试获取告警信息"""
    print("=" * 60)
    print("测试Zabbix告警信息")
    print("=" * 60)

    # 计算最近24小时的时间戳
    now = datetime.now()
    time_from = int((now - timedelta(hours=24)).timestamp())
    time_till = int(now.timestamp())

    print(f"\n[时间范围] {datetime.fromtimestamp(time_from)} 到 {datetime.fromtimestamp(time_till)}")
    print(f"   时间戳: {time_from} 到 {time_till}")

    # 测试1: 获取最近24小时的所有告警
    print("\n" + "=" * 60)
    print("测试1: 获取最近24小时的所有告警")
    print("=" * 60)

    params = {
        "output": "extend",
        "selectHosts": ["hostid", "name"],
        "time_from": time_from,
        "time_till": time_till,
        "sortfield": ["clock"],
        "sortorder": "DESC",
        "limit": 10
    }

    events = call_zabbix_api("event.get", params)

    if events is not None:
        print(f"\n[成功] 获取 {len(events)} 条告警记录")

        if len(events) > 0:
            print("\n前10条告警详情:")
            print("-" * 60)
            for i, event in enumerate(events[:10], 1):
                event_time = datetime.fromtimestamp(int(event.get('clock', 0)))
                severity = event.get('severity', 'N/A')
                severity_names = {
                    '0': '未分类',
                    '1': '信息',
                    '2': '警告',
                    '3': '一般严重',
                    '4': '严重',
                    '5': '灾难'
                }
                severity_name = severity_names.get(str(severity), f'级别{severity}')

                hosts = event.get('hosts', [])
                host_name = hosts[0].get('name', 'N/A') if hosts else 'N/A'

                name = event.get('name', 'N/A')
                value = event.get('value', 'N/A')
                value_text = '已恢复' if value == '0' else '问题'

                print(f"\n{i}. 告警ID: {event.get('eventid')}")
                print(f"   时间: {event_time}")
                print(f"   主机: {host_name}")
                print(f"   级别: {severity_name}")
                print(f"   状态: {value_text}")
                print(f"   描述: {name}")
        else:
            print("\n[警告] 最近24小时没有告警记录")

    # 测试2: 获取所有未恢复的告警（不限时间）
    print("\n" + "=" * 60)
    print("测试2: 获取所有未恢复的告警（不限时间）")
    print("=" * 60)

    params = {
        "output": "extend",
        "selectHosts": ["hostid", "name"],
        "value": 1,  # 1表示问题状态，0表示已恢复
        "sortfield": ["clock"],
        "sortorder": "DESC",
        "limit": 10
    }

    events = call_zabbix_api("event.get", params)

    if events is not None:
        print(f"\n[成功] 获取 {len(events)} 条未恢复告警")

        if len(events) > 0:
            print("\n前10条未恢复告警:")
            print("-" * 60)
            for i, event in enumerate(events[:10], 1):
                event_time = datetime.fromtimestamp(int(event.get('clock', 0)))
                severity = event.get('severity', 'N/A')
                severity_names = {
                    '0': '未分类',
                    '1': '信息',
                    '2': '警告',
                    '3': '一般严重',
                    '4': '严重',
                    '5': '灾难'
                }
                severity_name = severity_names.get(str(severity), f'级别{severity}')

                hosts = event.get('hosts', [])
                host_name = hosts[0].get('name', 'N/A') if hosts else 'N/A'

                name = event.get('name', 'N/A')

                print(f"\n{i}. 告警ID: {event.get('eventid')}")
                print(f"   时间: {event_time}")
                print(f"   主机: {host_name}")
                print(f"   级别: {severity_name}")
                print(f"   描述: {name}")
        else:
            print("\n⚠️  当前没有未恢复的告警")

    # 测试3: 获取所有告警（不限时间和状态）
    print("\n" + "=" * 60)
    print("测试3: 获取所有告警（不限时间和状态，最多100条）")
    print("=" * 60)

    params = {
        "output": "extend",
        "selectHosts": ["hostid", "name"],
        "sortfield": ["clock"],
        "sortorder": "DESC",
        "limit": 100
    }

    events = call_zabbix_api("event.get", params)

    if events is not None:
        print(f"\n[成功] 获取 {len(events)} 条告警记录")

        if len(events) > 0:
            # 统计信息
            severity_count = {}
            status_count = {'问题': 0, '已恢复': 0}

            for event in events:
                severity = str(event.get('severity', '0'))
                severity_count[severity] = severity_count.get(severity, 0) + 1

                value = event.get('value', '1')
                if value == '0':
                    status_count['已恢复'] += 1
                else:
                    status_count['问题'] += 1

            print("\n[统计] 告警统计:")
            print("-" * 60)
            print(f"总计: {len(events)} 条")
            print(f"\n状态分布:")
            for status, count in status_count.items():
                print(f"  {status}: {count} 条")

            print(f"\n级别分布:")
            severity_names = {
                '0': '未分类',
                '1': '信息',
                '2': '警告',
                '3': '一般严重',
                '4': '严重',
                '5': '灾难'
            }
            for severity, count in sorted(severity_count.items()):
                severity_name = severity_names.get(severity, f'级别{severity}')
                print(f"  {severity_name}: {count} 条")

            # 显示最新的5条
            print("\n最新5条告警:")
            print("-" * 60)
            for i, event in enumerate(events[:5], 1):
                event_time = datetime.fromtimestamp(int(event.get('clock', 0)))
                severity = event.get('severity', 'N/A')
                severity_name = severity_names.get(str(severity), f'级别{severity}')

                hosts = event.get('hosts', [])
                host_name = hosts[0].get('name', 'N/A') if hosts else 'N/A'

                name = event.get('name', 'N/A')
                value = event.get('value', 'N/A')
                value_text = '已恢复' if value == '0' else '问题'

                print(f"\n{i}. {event_time} | {host_name} | {severity_name} | {value_text}")
                print(f"   {name}")
        else:
            print("\n⚠️  Zabbix中没有任何告警记录")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_alerts()
