import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 获取 API 基础地址
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

const instance: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const { response } = error

    if (response) {
      const isLoginPage = window.location.pathname === '/login' || window.location.pathname === '/register'

      switch (response.status) {
        case 401:
          // 只在已登录状态下才跳转登录页（有token说明是登录状态）
          const token = localStorage.getItem('token')
          if (token && !isLoginPage) {
            localStorage.removeItem('token')
            ElMessage.error('登录已过期，请重新登录')
            router.push('/login')
          }
          break
        case 403:
        case 404:
        case 500:
          // 这些错误让具体业务处理
          break
        default:
          // 其他错误也不全局处理
          break
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

// 创建带类型的请求方法
const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return instance.get(url, config) as Promise<T>
  },
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return instance.post(url, data, config) as Promise<T>
  },
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return instance.put(url, data, config) as Promise<T>
  },
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return instance.delete(url, config) as Promise<T>
  }
}

export default request
