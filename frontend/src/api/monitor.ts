import request from './index'
import type { MonitorFilter, DashboardData, ExportTask, Host } from '@/types'

// 获取 API 基础地址
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

// 创建 dashboard 查询任务（后台执行）
export function createDashboardTask(zabbixConfigId: number): Promise<{ status: string; zabbix_config_id: number }> {
  return request.post('/api/monitor/dashboard-task', { zabbix_config_id: zabbixConfigId })
}

// 获取缓存的 dashboard 数据
export function getDashboardCache(zabbixConfigId: number): Promise<DashboardData> {
  return request.get(`/api/monitor/dashboard-cache/${zabbixConfigId}`)
}

// 获取仪表盘数据（旧接口，保留兼容）
export function getDashboard(zabbixConfigId: number, forceRefresh = false, cacheTime = 300): Promise<DashboardData> {
  return request.get('/api/monitor/dashboard', {
    params: { zabbix_config_id: zabbixConfigId, force_refresh: forceRefresh, cache_time: cacheTime }
  })
}

// 获取主机列表
export function getHosts(zabbixConfigId: number): Promise<Host[]> {
  return request.get('/api/monitor/hosts', { params: { zabbix_config_id: zabbixConfigId } })
}

// 获取筛选配置列表
export function getFilters(zabbixConfigId?: number): Promise<MonitorFilter[]> {
  return request.get('/api/monitor/filters', {
    params: zabbixConfigId ? { zabbix_config_id: zabbixConfigId } : {}
  })
}

// 创建筛选配置
export function createFilter(data: Partial<MonitorFilter>): Promise<MonitorFilter> {
  return request.post('/api/monitor/filters', data)
}

// 更新筛选配置
export function updateFilter(id: number, data: Partial<MonitorFilter>): Promise<MonitorFilter> {
  return request.put(`/api/monitor/filters/${id}`, data)
}

// 删除筛选配置
export function deleteFilter(id: number) {
  return request.delete(`/api/monitor/filters/${id}`)
}

// 流式获取监控数据
export function streamMonitorData(data: { filter_ids: number[]; zabbix_config_id: number; time_range: number }) {
  const token = localStorage.getItem('token')
  return fetch(`${apiBaseUrl}/api/monitor/data-stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })
}

// 创建查询任务（后台执行，不阻塞前端）
export function createQueryTask(data: { filter_ids: number[]; zabbix_config_id: number; time_range?: number }): Promise<ExportTask> {
  return request.post('/api/monitor/query-task', data)
}

// 获取查询任务的数据结果
export async function getQueryTaskData(taskId: number) {
  return request.get(`/api/monitor/query-task/${taskId}/data`)
}

// 清除查询任务缓存
export function clearQueryTaskCache(taskId: number) {
  return request.delete(`/api/monitor/query-task/${taskId}`)
}

// 创建导出任务
export function createExportTask(data: { filter_ids: number[]; zabbix_config_id: number; include_device_overview: boolean }): Promise<ExportTask> {
  return request.post('/api/monitor/export', data)
}

// 获取导出任务列表
export function getExportTasks(limit = 20): Promise<ExportTask[]> {
  return request.get('/api/monitor/export/tasks', { params: { limit } })
}

// 下载导出文件
export async function downloadExportFile(taskId: number) {
  const token = localStorage.getItem('token')
  const response = await fetch(`${apiBaseUrl}/api/monitor/export/download/${taskId}`, {
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '下载失败' }))
    throw new Error(error.detail || '下载失败')
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `monitor_export_${taskId}.xlsx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

// 删除导出任务
export function deleteExportTask(taskId: number) {
  return request.delete(`/api/monitor/export/tasks/${taskId}`)
}
