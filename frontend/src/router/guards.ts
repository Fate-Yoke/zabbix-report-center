import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function setupRouterGuards(router: Router) {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore()

    // 设置页面标题
    document.title = to.meta?.title
      ? `${to.meta.title} - Zabbix Report Center`
      : 'Zabbix Report Center'

    // 不需要认证的页面直接放行
    if (to.meta?.requiresAuth === false) {
      // 已登录用户访问登录/注册页面，重定向到首页
      if (authStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
        return { path: '/' }
      }
      return true
    }

    // 检查是否有 token
    if (!authStore.token) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }

    // 如果有 token 但没有用户信息，先获取用户信息
    if (!authStore.user) {
      try {
        await authStore.fetchUser()
      } catch (error) {
        return { path: '/login', query: { redirect: to.fullPath } }
      }
    }

    // 需要管理员权限
    if (to.meta?.requiresAdmin && !authStore.isAdmin) {
      return { path: '/' }
    }

    return true
  })
}
