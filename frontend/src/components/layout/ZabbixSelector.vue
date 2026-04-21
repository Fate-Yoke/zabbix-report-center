<template>
  <el-dropdown @command="handleSelect">
    <el-button type="primary" size="small">
      <el-icon><Monitor /></el-icon>
      {{ zabbixConfigStore.getSelectedConfigName() }}
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="">请选择配置</el-dropdown-item>
        <!-- 在监控信息和定时任务页面显示"未配置"选项，且只有管理员能看见 -->
        <el-dropdown-item v-if="showUnconfigured && authStore.isAdmin" command="unconfigured">
          未配置
        </el-dropdown-item>
        <el-dropdown-item
          v-for="config in zabbixConfigStore.activeConfigs"
          :key="config.id"
          :command="config.id.toString()"
        >
          {{ config.name }}
        </el-dropdown-item>
        <el-dropdown-item v-if="zabbixConfigStore.activeConfigs.length === 0" disabled>
          无可用配置
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useZabbixConfigStore } from '@/stores/zabbixConfig'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const zabbixConfigStore = useZabbixConfigStore()
const authStore = useAuthStore()

// 只在监控信息和定时任务页面显示"未配置"选项
const showUnconfigured = computed(() => {
  return route.path === '/monitor' || route.path === '/tasks'
})

// 监听路由变化，切换到其他页面时清除"未配置"选择
watch(() => route.path, (newPath) => {
  if (newPath !== '/monitor' && newPath !== '/tasks') {
    if (zabbixConfigStore.selectedConfigId === 'unconfigured') {
      zabbixConfigStore.selectConfig(null)
    }
  }
})

const handleSelect = (configId: string) => {
  zabbixConfigStore.selectConfig(configId || null)
}
</script>
