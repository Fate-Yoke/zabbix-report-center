import request from './index'
import type { User, LoginRequest, LoginResponse, RegisterRequest, RegisterResponse } from '@/types'

// 获取 API 基础地址
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

// 获取验证码
export function getCaptcha() {
  return fetch(`${apiBaseUrl}/api/auth/captcha`).then(async res => {
    const key = res.headers.get('X-Captcha-Key')
    const blob = await res.blob()
    return { key, blob }
  })
}

// 登录
export function login(data: LoginRequest): Promise<LoginResponse> {
  return request.post('/api/auth/login', data)
}

// 注册
export function register(data: RegisterRequest): Promise<RegisterResponse> {
  return request.post('/api/auth/register', data)
}

// 获取当前用户信息
export function getCurrentUser(): Promise<User> {
  return request.get('/api/auth/me')
}

// 更新个人信息
export function updateProfile(data: { username?: string; email?: string }) {
  return request.put('/api/auth/me', data)
}

// 修改密码
export function changePassword(data: { current_password: string; new_password: string }) {
  return request.post('/api/auth/change-password', data)
}
