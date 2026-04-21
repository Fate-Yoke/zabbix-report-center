import request from './index'
import type { EmailConfig } from '@/types'

interface TestEmailResult {
  success: boolean
  message?: string
}

// 获取所有配置
export function getAllConfigs(): Promise<EmailConfig[]> {
  return request.get('/api/email-config')
}

// 获取单个配置
export function getConfig(id: number): Promise<EmailConfig> {
  return request.get(`/api/email-config/${id}`)
}

// 创建配置
export function createConfig(data: Partial<EmailConfig>): Promise<EmailConfig> {
  return request.post('/api/email-config', data)
}

// 更新配置
export function updateConfig(id: number, data: Partial<EmailConfig>): Promise<EmailConfig> {
  return request.put(`/api/email-config/${id}`, data)
}

// 删除配置
export function deleteConfig(id: number) {
  return request.delete(`/api/email-config/${id}`)
}

// 测试邮件
export function testEmail(id: number, toAddr?: string): Promise<TestEmailResult> {
  const url = toAddr
    ? `/api/email-config/${id}/test?to_addr=${encodeURIComponent(toAddr)}`
    : `/api/email-config/${id}/test`
  return request.get(url)
}
