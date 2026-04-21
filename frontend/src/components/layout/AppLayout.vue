<template>
  <el-container class="app-layout">
    <el-header class="app-header" height="60px">
      <div class="header-left">
        <span class="logo">Zabbix Report Center</span>
        <ZabbixSelector v-if="!isAdminPage" />
      </div>
      <div class="header-right">
        <el-link href="https://github.com/Fate-Yoke/zabbix-report-center" target="_blank" class="github-link">
          <svg viewBox="0 0 1024 1024" width="20" height="20" fill="currentColor">
            <path d="M512 42.666667A464.64 464.64 0 0 0 42.666667 502.186667 465.92 465.92 0 0 0 363.52 938.666667c23.466667 4.266667 32-9.813333 32-22.186667v-78.08c-130.56 27.733333-158.293333-61.44-158.293333-61.44a122.026667 122.026667 0 0 0-52.053334-67.413333c-42.666667-28.16 3.413333-27.733333 3.413334-27.733334a98.56 98.56 0 0 1 71.68 47.36 101.12 101.12 0 0 0 136.533333 37.546667 99.413333 99.413333 0 0 1 29.866667-61.44c-104.106667-11.52-213.333333-50.773333-213.333334-226.986666a176.64 176.64 0 0 1 47.36-124.16 161.28 161.28 0 0 1 4.693334-121.173334s39.68-12.373333 128 46.933334a449.706667 449.706667 0 0 1 234.666666 0c89.6-59.306667 128-46.933333 128-46.933334a161.28 161.28 0 0 1 4.693334 121.173334 176.64 176.64 0 0 1 47.36 124.16c0 176.64-109.226667 215.466667-213.333334 226.986666a106.666667 106.666667 0 0 1 30.293334 81.92v126.293334c0 12.373333 8.533333 26.88 32 22.186666A465.92 465.92 0 0 0 981.333333 502.186667 464.64 464.64 0 0 0 512 42.666667"/>
          </svg>
        </el-link>
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            {{ authStore.user?.username }}
            <el-tag v-if="authStore.isAdmin" type="warning" size="small">管理员</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon> 个人信息
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" class="app-aside">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409eff"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/monitor">
            <el-icon><TrendCharts /></el-icon>
            <span>监控信息</span>
          </el-menu-item>
          <el-menu-item index="/alerts">
            <el-icon><Bell /></el-icon>
            <span>告警信息</span>
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><Clock /></el-icon>
            <span>定时任务</span>
          </el-menu-item>

          <template v-if="authStore.isAdmin">
            <el-divider />
            <div class="menu-title">管理员</div>
            <el-menu-item index="/admin/users">
              <el-icon><UserFilled /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/zabbix-config">
              <el-icon><Setting /></el-icon>
              <span>Zabbix配置</span>
            </el-menu-item>
            <el-menu-item index="/admin/email-config">
              <el-icon><Message /></el-icon>
              <span>邮件配置</span>
            </el-menu-item>
            <el-menu-item index="/admin/system">
              <el-icon><Operation /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
            <el-menu-item index="/admin/logs">
              <el-icon><Document /></el-icon>
              <span>系统日志</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ZabbixSelector from './ZabbixSelector.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const isAdminPage = computed(() => route.path.startsWith('/admin/'))

const handleCommand = (command: string) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.logo {
  font-size: 1.25rem;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.github-link {
  color: white;
  font-size: 1.25rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: white;
}

.app-aside {
  background: #304156;
  overflow-y: auto;
}

.menu-title {
  color: #909399;
  font-size: 14px;
  font-weight: 500;
  padding: 12px 20px 8px;
  user-select: none;
  font-style: italic;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
