import request from './index'
import type { Task, TaskLog } from '@/types'

// 获取所有任务
export function getAllTasks(): Promise<Task[]> {
  return request.get('/api/tasks')
}

// 获取单个任务
export function getTask(id: number): Promise<Task> {
  return request.get(`/api/tasks/${id}`)
}

// 创建任务
export function createTask(data: Partial<Task>): Promise<Task> {
  return request.post('/api/tasks', data)
}

// 更新任务
export function updateTask(id: number, data: Partial<Task>): Promise<Task> {
  return request.put(`/api/tasks/${id}`, data)
}

// 删除任务
export function deleteTask(id: number) {
  return request.delete(`/api/tasks/${id}`)
}

// 立即执行任务
export function runTask(id: number) {
  return request.post(`/api/tasks/${id}/run`)
}

// 获取任务日志
export function getTaskLogs(taskId: number): Promise<TaskLog[]> {
  return request.get(`/api/tasks/${taskId}/logs`)
}

// 下载日志文件
export function downloadLogFile(logId: number) {
  window.location.href = `/api/tasks/logs/${logId}/download`
}
