<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { useZabbixConfigStore } from './stores/zabbixConfig'

const authStore = useAuthStore()
const zabbixConfigStore = useZabbixConfigStore()

onMounted(async () => {
  // 用户信息已在路由守卫中加载
  // 这里只需要加载 Zabbix 配置
  if (authStore.isLoggedIn) {
    await zabbixConfigStore.fetchConfigs()
  }
})
</script>

<template>
  <router-view />
</template>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
