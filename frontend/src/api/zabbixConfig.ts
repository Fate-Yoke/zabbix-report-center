import request from './index'
import type { ZabbixConfig } from '@/types'

interface TestConnectionResult {
  success: boolean
  version?: string
  error?: string
}

// 获取所有配置
export function getAllConfigs(): Promise<ZabbixConfig[]> {
  return request.get('/api/zabbix-config')
}

// 获取单个配置
export function getConfig(id: number): Promise<ZabbixConfig> {
  return request.get(`/api/zabbix-config/${id}`)
}

// 创建配置
export function createConfig(data: Partial<ZabbixConfig>): Promise<ZabbixConfig> {
  return request.post('/api/zabbix-config', data)
}

// 更新配置
export function updateConfig(id: number, data: Partial<ZabbixConfig>): Promise<ZabbixConfig> {
  return request.put(`/api/zabbix-config/${id}`, data)
}

// 删除配置
export function deleteConfig(id: number) {
  return request.delete(`/api/zabbix-config/${id}`)
}

// 测试连接
export function testConnection(id: number): Promise<TestConnectionResult> {
  return request.get(`/api/zabbix-config/${id}/test`)
}
