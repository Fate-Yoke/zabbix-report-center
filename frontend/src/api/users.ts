import request from './index'
import type { User } from '@/types'

// 获取所有用户
export function getAllUsers(): Promise<User[]> {
  return request.get('/api/users')
}

// 获取单个用户
export function getUser(id: number): Promise<User> {
  return request.get(`/api/users/${id}`)
}

// 创建用户
export function createUser(data: Partial<User> & { password: string }): Promise<User> {
  return request.post('/api/users', data)
}

// 更新用户
export function updateUser(id: number, data: Partial<User>): Promise<User> {
  return request.put(`/api/users/${id}`, data)
}

// 删除用户
export function deleteUser(id: number) {
  return request.delete(`/api/users/${id}`)
}
