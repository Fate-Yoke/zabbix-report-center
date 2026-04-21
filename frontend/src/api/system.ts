import request from './index'
import type { SystemLog } from '@/types'

interface RegistrationSettings {
  allow_registration: boolean
  require_activation: boolean
  allowed: boolean
}

// 获取注册设置
export function getRegistrationSettings(): Promise<RegistrationSettings> {
  return request.get('/api/system/registration')
}

// 更新注册设置
export function updateRegistrationSettings(data: { allow_registration: boolean; require_activation: boolean }): Promise<{ message: string }> {
  return request.put('/api/system/registration', {
    allowed: data.allow_registration,
    require_activation: data.require_activation
  })
}

// 获取系统设置
export function getSettings() {
  return request.get('/api/system/settings')
}

// 获取系统日志
export function getLogs(params: { level?: string; limit?: number; offset?: number; start_time?: string; end_time?: string }): Promise<{ total: number; logs: SystemLog[] }> {
  return request.get('/api/logs/', { params })
}

// 清理日志
export function clearLogs(days: number): Promise<{ message: string; deleted: number }> {
  return request.delete('/api/logs/', { params: { days } })
}
