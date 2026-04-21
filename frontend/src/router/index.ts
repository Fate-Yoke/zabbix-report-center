import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresAuth: false, title: '注册' }
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/monitor/Index.vue'),
        meta: { title: '监控信息' }
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('@/views/alerts/Index.vue'),
        meta: { title: '告警信息' }
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/tasks/Index.vue'),
        meta: { title: '定时任务' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Index.vue'),
        meta: { title: '个人信息' }
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      },
      {
        path: 'admin/zabbix-config',
        name: 'AdminZabbixConfig',
        component: () => import('@/views/admin/ZabbixConfig.vue'),
        meta: { title: 'Zabbix配置', requiresAdmin: true }
      },
      {
        path: 'admin/email-config',
        name: 'AdminEmailConfig',
        component: () => import('@/views/admin/EmailConfig.vue'),
        meta: { title: '邮件配置', requiresAdmin: true }
      },
      {
        path: 'admin/system',
        name: 'AdminSystem',
        component: () => import('@/views/admin/System.vue'),
        meta: { title: '系统设置', requiresAdmin: true }
      },
      {
        path: 'admin/logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/Logs.vue'),
        meta: { title: '系统日志', requiresAdmin: true }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
