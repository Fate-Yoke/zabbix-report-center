import request from './index'
import type { AlertExportTask, AlertsResponse } from '@/types'

// 获取 API 基础地址
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

// 创建告警查询任务（后台执行）
export function createAlertsQueryTask(params: {
  zabbix_config_id: number
  time_from?: number
  time_till?: number
  severity?: string
  recovered?: string
}): Promise<{ status: string; zabbix_config_id: number }> {
  return request.post('/api/alerts/query-task', params)
}

// 获取缓存的告警数据
export function getAlertsCache(zabbixConfigId: number): Promise<AlertsResponse> {
  return request.get(`/api/alerts/cache/${zabbixConfigId}`)
}

// 获取告警列表（旧接口，保留兼容）
export function getAlerts(params: {
  zabbix_config_id: number
  time_from?: number
  time_till?: number
  severity?: string
  recovered?: string
  limit?: number
}): Promise<AlertsResponse> {
  return request.get('/api/alerts/', { params })
}

// 创建告警导出任务
export function createAlertExportTask(data: {
  zabbix_config_id: number
  time_from?: number
  time_till?: number
  severity?: number[]
  recovered?: string
}): Promise<AlertExportTask> {
  return request.post('/api/alerts/export-tasks', data)
}

// 获取告警导出任务列表
export function getAlertExportTasks(): Promise<AlertExportTask[]> {
  return request.get('/api/alerts/export-tasks')
}

// 下载导出文件
export async function downloadExportFile(taskId: number, filename?: string) {
  const token = localStorage.getItem('token')
  const response = await fetch(`${apiBaseUrl}/api/alerts/export-tasks/${taskId}/download`, {
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '下载失败' }))
    throw new Error(error.detail || '下载失败')
  }

  // 从响应头获取文件名，如果没有则使用参数或默认名称
  const contentDisposition = response.headers.get('Content-Disposition')
  let downloadFilename = filename
  if (!downloadFilename && contentDisposition) {
    const match = contentDisposition.match(/filename="?([^";\n]+)"?/)
    if (match) {
      downloadFilename = match[1]
    }
  }
  if (!downloadFilename) {
    downloadFilename = `alerts_export_${taskId}.xlsx`
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = downloadFilename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}
