import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  async function login(username: string, password: string, captchaKey: string, captchaCode: string) {
    const res = await authApi.login({
      username,
      password,
      captcha_key: captchaKey,
      captcha_code: captchaCode
    })
    if (res.success) {
      token.value = res.token
      user.value = res.user
      localStorage.setItem('token', res.token)
    }
    return res
  }

  async function fetchUser() {
    try {
      const userData = await authApi.getCurrentUser()
      user.value = userData
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  function canAccessZabbix(zabbixId: number): boolean {
    if (isAdmin.value) return true
    return user.value?.allowed_zabbix_ids?.includes(zabbixId) ?? false
  }

  return {
    user,
    token,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    fetchUser,
    canAccessZabbix
  }
})
