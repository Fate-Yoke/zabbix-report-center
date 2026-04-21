<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>
        <el-icon><HomeFilled /></el-icon>
        首页
      </h2>
      <div class="header-actions">
        <span class="update-time">{{ updateTimeText }}</span>
        <el-select v-model="cacheTime" size="small" style="width: 120px" @change="handleCacheTimeChange">
          <el-option label="手动刷新" value="manual" />
          <el-option label="缓存1分钟" :value="60" />
          <el-option label="缓存3分钟" :value="180" />
          <el-option label="缓存5分钟" :value="300" />
          <el-option label="缓存10分钟" :value="600" />
          <el-option label="不使用缓存" :value="0" />
        </el-select>
        <el-button type="primary" @click="refreshDashboard" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 提示信息 -->
    <el-alert v-if="!selectedConfigId" type="warning" show-icon class="mb-4">
      请在左上角选择具体的 Zabbix 配置以查看监控数据
    </el-alert>

    <!-- 加载提示 -->
    <el-alert v-else-if="loading" type="info" show-icon class="mb-4">
      正在后台加载数据，您可以继续其他操作...
    </el-alert>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="8">
        <el-card class="stat-card primary">
          <div class="stat-icon"><el-icon :size="32"><Monitor /></el-icon></div>
          <div class="stat-value">{{ dashboard.total }}</div>
          <div class="stat-label">设备总量</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card success">
          <div class="stat-icon"><el-icon :size="32"><CircleCheck /></el-icon></div>
          <div class="stat-value">{{ dashboard.online_count }}</div>
          <div class="stat-label">在线设备</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card danger">
          <div class="stat-icon"><el-icon :size="32"><CircleClose /></el-icon></div>
          <div class="stat-value">{{ dashboard.offline_count }}</div>
          <div class="stat-label">离线设备</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 离线设备列表 -->
    <el-card v-if="selectedConfigId" class="mb-4">
      <template #header>
        <div class="card-header danger">
          <el-icon><Warning /></el-icon>
          离线设备列表
        </div>
      </template>
      <div v-if="!dashboard.offline_hosts?.length" class="no-data">
        暂无离线设备
      </div>
      <template v-else>
        <el-table :data="offlineHostsPage" stripe :row-class-name="() => 'danger-row'">
          <el-table-column label="序号" width="80" align="center">
            <template #default="{ $index }">{{ (offlineCurrentPage - 1) * offlinePageSize + $index + 1 }}</template>
          </el-table-column>
          <el-table-column prop="name" label="设备名" />
          <el-table-column prop="ip" label="IP地址" />
          <el-table-column prop="groups" label="所属群组" />
        </el-table>
        <el-pagination
          v-if="dashboard.offline_hosts.length > offlinePageSize"
          v-model:current-page="offlineCurrentPage"
          v-model:page-size="offlinePageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="dashboard.offline_hosts.length"
          layout="total, sizes, prev, pager, next"
          class="pagination"
        />
      </template>
    </el-card>

    <!-- 在线设备列表 -->
    <el-card v-if="selectedConfigId">
      <template #header>
        <div class="card-header success">
          <el-icon><CircleCheck /></el-icon>
          在线设备列表
        </div>
      </template>
      <div v-if="!dashboard.online_hosts?.length" class="no-data">
        暂无在线设备
      </div>
      <template v-else>
        <el-table :data="onlineHostsPage" stripe>
          <el-table-column label="序号" width="80" align="center">
            <template #default="{ $index }">{{ (onlineCurrentPage - 1) * onlinePageSize + $index + 1 }}</template>
          </el-table-column>
          <el-table-column prop="name" label="设备名" />
          <el-table-column prop="ip" label="IP地址" />
          <el-table-column prop="groups" label="所属群组" />
        </el-table>
        <el-pagination
          v-if="dashboard.online_hosts.length > onlinePageSize"
          v-model:current-page="onlineCurrentPage"
          v-model:page-size="onlinePageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="dashboard.online_hosts.length"
          layout="total, sizes, prev, pager, next"
          class="pagination"
        />
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useZabbixConfigStore } from '@/stores/zabbixConfig'
import { createDashboardTask, getDashboardCache } from '@/api/monitor'
import type { DashboardData } from '@/types'

const zabbixConfigStore = useZabbixConfigStore()

const loading = ref(false)

// 初始化缓存时间，需要正确处理类型
const initCacheTime = () => {
  const saved = localStorage.getItem('dashboard_cache_time')
  if (saved === 'manual') {
    return 'manual'
  } else if (saved === null) {
    return 300 // 默认5分钟
  } else {
    const num = parseInt(saved, 10)
    return isNaN(num) ? 300 : num
  }
}
const cacheTime = ref<string | number>(initCacheTime())

const dashboard = ref<DashboardData>({
  total: 0,
  online_count: 0,
  offline_count: 0,
  online_hosts: [],
  offline_hosts: [],
  cached: false,
  cached_at: ''
})

const offlinePageSize = ref(20)
const offlineCurrentPage = ref(1)
const onlinePageSize = ref(20)
const onlineCurrentPage = ref(1)
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null

const selectedConfigId = computed(() => zabbixConfigStore.selectedConfigId)

const offlineHostsPage = computed(() => {
  const start = (offlineCurrentPage.value - 1) * offlinePageSize.value
  const end = start + offlinePageSize.value
  return dashboard.value.offline_hosts?.slice(start, end) || []
})

const onlineHostsPage = computed(() => {
  const start = (onlineCurrentPage.value - 1) * onlinePageSize.value
  const end = start + onlinePageSize.value
  return dashboard.value.online_hosts?.slice(start, end) || []
})

const updateTimeText = computed(() => {
  if (!dashboard.value.cached_at) return '-'
  const updateTime = new Date(dashboard.value.cached_at)
  const now = new Date()
  const diffSeconds = Math.floor((now.getTime() - updateTime.getTime()) / 1000)

  let timeText = ''
  if (diffSeconds < 60) {
    timeText = '刚刚更新'
  } else if (diffSeconds < 3600) {
    timeText = `${Math.floor(diffSeconds / 60)}分钟前更新`
  } else {
    timeText = `${Math.floor(diffSeconds / 3600)}小时前更新`
  }

  return timeText + (dashboard.value.cached ? ' (缓存)' : '')
})

// 加载 dashboard 数据（后台任务模式）
const loadDashboard = async (forceRefresh = false) => {
  if (!selectedConfigId.value) return

  // 先尝试从缓存获取（非强制刷新时）
  if (!forceRefresh) {
    try {
      const data = await getDashboardCache(Number(selectedConfigId.value))
      dashboard.value = data
      // 重置分页
      offlineCurrentPage.value = 1
      onlineCurrentPage.value = 1
      return
    } catch {
      // 缓存不存在，继续创建新任务
    }
  }

  loading.value = true
  try {
    // 创建后台查询任务
    await createDashboardTask(Number(selectedConfigId.value))
    // 开始轮询等待数据就绪
    pollDashboardData()
  } catch (error) {
    console.error('创建查询任务失败:', error)
    loading.value = false
    ElMessage.error('加载数据失败')
  }
}

// 轮询等待 dashboard 数据就绪
const pollDashboardData = async () => {
  let attempts = 0
  const maxAttempts = 30 // 最多等待30秒
  let lastCachedAt = dashboard.value.cached_at

  const checkData = async () => {
    attempts++
    try {
      const data = await getDashboardCache(Number(selectedConfigId.value))
      // 只有当缓存时间更新了才认为是新数据
      if (data.cached_at !== lastCachedAt) {
        dashboard.value = data
        // 重置分页
        offlineCurrentPage.value = 1
        onlineCurrentPage.value = 1
        loading.value = false
      } else if (attempts < maxAttempts) {
        // 数据未更新，继续轮询
        setTimeout(checkData, 1000)
      } else {
        loading.value = false
        ElMessage.warning('数据加载超时，请稍后重试')
      }
    } catch {
      // 数据未就绪，继续轮询
      if (attempts < maxAttempts) {
        setTimeout(checkData, 1000)
      } else {
        loading.value = false
        ElMessage.warning('数据加载超时，请稍后重试')
      }
    }
  }

  setTimeout(checkData, 1000)
}

const refreshDashboard = () => {
  loadDashboard(true)
}

const handleCacheTimeChange = () => {
  localStorage.setItem('dashboard_cache_time', String(cacheTime.value))
  stopAutoRefresh()

  // 如果选择手动刷新，不加载数据，不启动自动刷新
  if (cacheTime.value === 'manual') {
    return
  }

  // 不使用缓存时，强制刷新获取新数据；否则使用缓存
  if (selectedConfigId.value) {
    const forceRefresh = cacheTime.value === 0
    loadDashboard(forceRefresh)
  }

  // 启动自动刷新定时器（缓存时间大于0时）
  startAutoRefresh()
}

const startAutoRefresh = () => {
  const timeValue = typeof cacheTime.value === 'number' ? cacheTime.value : 0
  // 手动刷新模式或缓存时间为0时不启动自动刷新
  if (timeValue <= 0 || cacheTime.value === 'manual') return

  stopAutoRefresh()
  autoRefreshTimer = setInterval(() => {
    if (selectedConfigId.value) {
      // 自动刷新时强制刷新，获取新数据
      loadDashboard(true)
    }
  }, timeValue * 1000)
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

watch(selectedConfigId, () => {
  if (selectedConfigId.value) {
    loadDashboard()
    startAutoRefresh()
  }
})

onMounted(() => {
  if (selectedConfigId.value) {
    loadDashboard()
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.update-time {
  color: #909399;
  font-size: 0.875rem;
}

.stat-card {
  text-align: center;
}

.stat-card.primary {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
}

.stat-card.success {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
}

.stat-card.danger {
  background: linear-gradient(135deg, #f56c6c 0%, #f89898 100%);
  color: white;
}

.stat-icon {
  margin-bottom: 10px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1rem;
  font-weight: 600;
}

.card-header.danger {
  color: #f56c6c;
}

.card-header.success {
  color: #67c23a;
}

.pagination {
  margin-top: 15px;
  justify-content: flex-end;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}

:deep(.danger-row) {
  background-color: #fef0f0 !important;
}

:deep(.danger-row:hover > td) {
  background-color: #fde2e2 !important;
}

.mb-4 {
  margin-bottom: 1rem;
}
</style>
