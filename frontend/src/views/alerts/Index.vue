<template>
  <div class="alerts">
    <div class="page-header">
      <h2>
        <el-icon><Warning /></el-icon>
        告警信息
      </h2>
      <div class="header-actions">
        <el-button type="primary" size="small" @click="refreshAlerts" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button type="success" size="small" @click="showExportDialog" :disabled="!selectedConfigId">
          <el-icon><Download /></el-icon> 导出
        </el-button>
        <el-button type="info" size="small" @click="showExportHistoryDialog">
          <el-icon><Clock /></el-icon> 导出记录
        </el-button>
      </div>
    </div>

    <el-alert v-if="!selectedConfigId" type="warning" show-icon class="mb-4">
      请在左上角选择 Zabbix 配置
    </el-alert>

    <template v-else>
      <!-- 筛选条件 -->
      <el-card class="mb-4">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="告警级别">
              <el-select v-model="filterForm.severity" multiple placeholder="请选择" collapse-tags style="width: 100%" @change="handleSeverityChange">
                <el-option label="全选" value="all" />
                <el-option label="灾难" :value="5" />
                <el-option label="严重" :value="4" />
                <el-option label="一般严重" :value="3" />
                <el-option label="警告" :value="2" />
                <el-option label="信息" :value="1" />
                <el-option label="未分类" :value="0" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="恢复状态">
              <el-select v-model="filterForm.recovered" placeholder="全部" style="width: 100%" @change="refreshAlerts">
                <el-option label="全部" value="all" />
                <el-option label="未恢复" value="unrecovered" />
                <el-option label="已恢复" value="recovered" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="发生时间（从）">
              <el-date-picker
                v-model="filterForm.timeFrom"
                type="datetime"
                placeholder="开始时间"
                value-format="x"
                style="width: 100%"
                @change="refreshAlerts"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="发生时间（到）">
              <el-date-picker
                v-model="filterForm.timeTill"
                type="datetime"
                placeholder="结束时间"
                value-format="x"
                style="width: 100%"
                @change="refreshAlerts"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 统计信息 -->
      <el-alert v-if="alerts.length > 0 || dataLoadComplete" type="info" show-icon class="mb-4">
        共 <strong>{{ total }}</strong> 条告警，未恢复 <strong>{{ unrecoveredCount }}</strong> 条
        <span v-if="cachedAt" class="cached-info">（缓存于 {{ formatCachedTime(cachedAt) }}）</span>
      </el-alert>

      <!-- 告警列表 -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span>告警列表</span>
            <div class="header-right">
              <div v-if="loading" class="loading-info">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在后台加载数据...</span>
              </div>
              <el-button v-if="alerts.length > 0" size="small" type="danger" @click="clearAlerts">
                <el-icon><Delete /></el-icon> 清除数据
              </el-button>
            </div>
          </div>
        </template>

        <div v-if="!alerts.length && !loading" class="data-placeholder">
          <el-empty description="暂无告警数据" />
        </div>

        <template v-else-if="alerts.length">
          <el-table :data="displayAlerts" stripe border @sort-change="handleSortChange">
            <el-table-column label="序号" width="70" align="center">
              <template #default="{ $index }">{{ (currentPage - 1) * pageSize + $index + 1 }}</template>
            </el-table-column>
            <el-table-column label="告警级别" width="100" sortable="custom" prop="severity">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ row.severity_name }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="host_groups" label="主机群组" width="150" show-overflow-tooltip sortable="custom" />
            <el-table-column prop="host_name" label="主机名" width="150" show-overflow-tooltip sortable="custom" />
            <el-table-column prop="host_ip" label="主机IP" width="130" sortable="custom" />
            <el-table-column prop="name" label="告警信息" min-width="200" show-overflow-tooltip sortable="custom" />
            <el-table-column label="发生时间" width="180" sortable="custom" prop="clock">
              <template #default="{ row }">
                {{ formatTime(row.clock) }}
              </template>
            </el-table-column>
            <el-table-column label="恢复时间" width="180" sortable="custom" prop="r_clock">
              <template #default="{ row }">
                {{ row.r_clock ? formatTime(row.r_clock) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="持续时间" width="120" sortable="custom" prop="duration">
              <template #default="{ row }">
                {{ formatDuration(row.duration) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" sortable="custom" prop="recovered">
              <template #default="{ row }">
                <el-tag :type="row.recovered ? 'success' : 'danger'" size="small">
                  {{ row.recovered ? '已恢复' : '未恢复' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[20, 50, 100, 200]"
              :total="sortedAlerts.length"
              layout="total, sizes, prev, pager, next, jumper"
              background
            />
          </div>
        </template>
      </el-card>
    </template>

    <!-- 导出配置弹窗 -->
    <el-dialog v-model="exportDialogVisible" title="导出告警信息" width="500px">
      <el-form label-width="100px">
        <el-form-item label="时间范围">
          <el-col :span="11">
            <el-date-picker
              v-model="exportForm.timeFrom"
              type="datetime"
              placeholder="开始时间"
              value-format="x"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="2" style="text-align: center">-</el-col>
          <el-col :span="11">
            <el-date-picker
              v-model="exportForm.timeTill"
              type="datetime"
              placeholder="结束时间"
              value-format="x"
              style="width: 100%"
            />
          </el-col>
        </el-form-item>

        <el-form-item label="告警级别">
          <div>
            <el-checkbox v-model="exportSeverityAll" @change="toggleExportAllSeverities">全选</el-checkbox>
            <el-divider style="margin: 10px 0" />
            <el-checkbox-group v-model="exportForm.severity">
              <el-checkbox :value="5"><el-tag type="danger" size="small">灾难</el-tag></el-checkbox>
              <el-checkbox :value="4"><el-tag type="warning" size="small">严重</el-tag></el-checkbox>
              <el-checkbox :value="3"><el-tag type="info" size="small">一般严重</el-tag></el-checkbox>
              <el-checkbox :value="2"><el-tag type="primary" size="small">警告</el-tag></el-checkbox>
              <el-checkbox :value="1"><el-tag type="success" size="small">信息</el-tag></el-checkbox>
              <el-checkbox :value="0"><el-tag size="small">未分类</el-tag></el-checkbox>
            </el-checkbox-group>
          </div>
        </el-form-item>

        <el-form-item label="恢复状态">
          <el-select v-model="exportForm.recovered" placeholder="全部" style="width: 100%">
            <el-option label="全部" value="all" />
            <el-option label="未恢复" value="unrecovered" />
            <el-option label="已恢复" value="recovered" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExport" :loading="exporting">
          <el-icon><Download /></el-icon> 导出Excel
        </el-button>
      </template>
    </el-dialog>

    <!-- 导出历史弹窗 -->
    <el-dialog v-model="exportHistoryDialogVisible" title="导出历史" width="900px">
      <el-table :data="exportTasks" v-loading="tasksLoading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="zabbix_config_name" label="Zabbix配置" width="120" />
        <el-table-column label="时间范围" width="200">
          <template #default="{ row }">
            <span v-if="row.time_from && row.time_till">
              {{ formatTimestamp(row.time_from) }} ~ {{ formatTimestamp(row.time_till) }}
            </span>
            <span v-else>全部</span>
          </template>
        </el-table-column>
        <el-table-column label="告警级别" width="100">
          <template #default="{ row }">
            {{ row.severity || '全部' }}
          </template>
        </el-table-column>
        <el-table-column label="恢复状态" width="80">
          <template #default="{ row }">
            {{ row.recovered === 'recovered' ? '已恢复' : row.recovered === 'unrecovered' ? '未恢复' : '全部' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusType(row.status)" size="small">
              {{ getTaskStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_count" label="记录数" width="80" />
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTimeString(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="完成时间" width="160">
          <template #default="{ row }">
            {{ row.completed_at ? formatTimeString(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              size="small"
              type="success"
              @click="handleDownloadExport(row)"
            >
              <el-icon><Download /></el-icon> 下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="exportHistoryDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="loadExportTasks">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, shallowRef, triggerRef } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh, Clock, Delete, Loading } from '@element-plus/icons-vue'
import { useZabbixConfigStore } from '@/stores/zabbixConfig'
import { createAlertsQueryTask, getAlertsCache, createAlertExportTask, getAlertExportTasks, downloadExportFile } from '@/api/alerts'
import type { Alert, AlertExportTask } from '@/types'

const zabbixConfigStore = useZabbixConfigStore()

const loading = ref(false)
const exporting = ref(false)
const tasksLoading = ref(false)
const alerts = shallowRef<Alert[]>([])
const exportTasks = ref<AlertExportTask[]>([])
const total = ref(0)
const cachedAt = ref('')
const dataLoadComplete = ref(false)
const exportDialogVisible = ref(false)
const exportHistoryDialogVisible = ref(false)
const exportSeverityAll = ref(true)

// 分页
const currentPage = ref(1)
const pageSize = ref(50)

// 排序
const sortColumn = ref<string | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')

const allSeverities = [5, 4, 3, 2, 1, 0]

const filterForm = reactive({
  severity: [...allSeverities] as number[],
  recovered: 'all' as string,
  timeFrom: null as number | null,
  timeTill: null as number | null
})

// 是否全选状态
const isAllSeveritySelected = () => {
  return allSeverities.every(s => filterForm.severity.includes(s))
}

// 处理告警级别变化（包含全选逻辑）
const handleSeverityChange = (val: (number | string)[]) => {
  // 如果选择了"全选"
  if (val.includes('all')) {
    // 当前是否已经全选了
    if (isAllSeveritySelected()) {
      // 已经全选了，再次点击全选就是取消全选
      filterForm.severity = []
    } else {
      // 没有全选，点击全选就是全选
      filterForm.severity = [...allSeverities]
    }
    // 过滤掉 'all' 值
    filterForm.severity = filterForm.severity.filter(s => typeof s === 'number') as number[]
  }
  refreshAlerts()
}

const exportForm = reactive({
  timeFrom: null as number | null,
  timeTill: null as number | null,
  severity: [5, 4, 3, 2, 1, 0] as number[],
  recovered: 'all' as string
})

const selectedConfigId = computed(() => zabbixConfigStore.selectedConfigId)
const unrecoveredCount = computed(() => alerts.value.filter(a => !a.recovered).length)

// 排序后的数据
const sortedAlerts = computed(() => {
  if (!sortColumn.value) return alerts.value

  const data = [...alerts.value]
  const column = sortColumn.value
  const direction = sortDirection.value

  data.sort((a: any, b: any) => {
    let valA = a[column]
    let valB = b[column]

    if (typeof valA === 'number' && typeof valB === 'number') {
      return direction === 'asc' ? valA - valB : valB - valA
    } else {
      valA = String(valA || '').toLowerCase()
      valB = String(valB || '').toLowerCase()
      if (valA < valB) return direction === 'asc' ? -1 : 1
      if (valA > valB) return direction === 'asc' ? 1 : -1
      return 0
    }
  })

  return data
})

// 当前页数据
const displayAlerts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return sortedAlerts.value.slice(start, end)
})

const formatTime = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString()
}

const formatTimestamp = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTimeString = (timeStr: string) => {
  return new Date(timeStr).toLocaleString()
}

const formatCachedTime = (timeStr: string) => {
  const time = new Date(timeStr)
  const now = new Date()
  const diffSeconds = Math.floor((now.getTime() - time.getTime()) / 1000)
  if (diffSeconds < 60) return '刚刚'
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}分钟前`
  return `${Math.floor(diffSeconds / 3600)}小时前`
}

const formatDuration = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  const result: string[] = []
  if (days > 0) result.push(`${days}天`)
  if (hours > 0) result.push(`${hours}小时`)
  if (minutes > 0) result.push(`${minutes}分钟`)
  if (secs > 0 || result.length === 0) result.push(`${secs}秒`)

  return result.join(' ')
}

const getSeverityType = (severity: number): 'info' | 'warning' | 'danger' | 'primary' | 'success' => {
  const types: Record<number, 'info' | 'warning' | 'danger' | 'primary' | 'success'> = {
    0: 'info',
    1: 'success',
    2: 'primary',
    3: 'info',
    4: 'warning',
    5: 'danger'
  }
  return types[severity] || 'info'
}

const getTaskStatusType = (status: string): 'info' | 'warning' | 'danger' | 'primary' | 'success' => {
  const types: Record<string, 'info' | 'warning' | 'success' | 'danger' | 'primary'> = {
    pending: 'info',
    processing: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getTaskStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const toggleExportAllSeverities = (val: boolean) => {
  if (val) {
    exportForm.severity = [5, 4, 3, 2, 1, 0]
  } else {
    exportForm.severity = []
  }
}

// 加载告警数据（后台任务模式）
const loadAlerts = async (forceRefresh = false) => {
  if (!selectedConfigId.value) return

  // 如果不是强制刷新，先尝试从缓存获取
  if (!forceRefresh) {
    try {
      const response = await getAlertsCache(Number(selectedConfigId.value))
      alerts.value = response.alerts
      triggerRef(alerts)
      total.value = response.total
      cachedAt.value = response.cached_at || ''
      dataLoadComplete.value = true
      currentPage.value = 1
      return
    } catch {
      // 缓存不存在，继续创建新任务
    }
  }

  // 清除旧数据，显示加载状态
  alerts.value = []
  triggerRef(alerts)
  total.value = 0

  // 如果没有选择任何级别，不查询
  if (filterForm.severity.length === 0) {
    loading.value = false
    return
  }

  loading.value = true

  try {
    const params: any = {
      zabbix_config_id: Number(selectedConfigId.value)
    }

    params.severity = filterForm.severity.join(',')

    if (filterForm.recovered && filterForm.recovered !== 'all') {
      params.recovered = filterForm.recovered
    }

    if (filterForm.timeFrom) {
      params.time_from = Math.floor(filterForm.timeFrom / 1000)
    }

    if (filterForm.timeTill) {
      params.time_till = Math.floor(filterForm.timeTill / 1000)
    }

    await createAlertsQueryTask(params)
    pollAlertsData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建查询任务失败')
    loading.value = false
  }
}

// 刷新数据（强制重新查询）
const refreshAlerts = () => {
  loadAlerts(true)
}

// 轮询等待告警数据就绪
const pollAlertsData = async () => {
  let attempts = 0
  const maxAttempts = 30

  const checkData = async () => {
    attempts++
    try {
      const response = await getAlertsCache(Number(selectedConfigId.value))
      alerts.value = response.alerts
      triggerRef(alerts)
      total.value = response.total
      cachedAt.value = response.cached_at || ''
      dataLoadComplete.value = true
      loading.value = false
      currentPage.value = 1
      ElMessage.success(`数据加载完成！共 ${response.total} 条告警`)
    } catch {
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

// 清除数据
const clearAlerts = () => {
  alerts.value = []
  triggerRef(alerts)
  total.value = 0
  cachedAt.value = ''
  dataLoadComplete.value = false
  currentPage.value = 1
  sortColumn.value = null
  sortDirection.value = 'asc'
}

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  if (!order) {
    sortColumn.value = null
    sortDirection.value = 'asc'
  } else {
    sortColumn.value = prop
    sortDirection.value = order === 'ascending' ? 'asc' : 'desc'
  }
}

const showExportDialog = () => {
  exportForm.timeFrom = filterForm.timeFrom
  exportForm.timeTill = filterForm.timeTill
  exportForm.severity = [...filterForm.severity]
  exportForm.recovered = filterForm.recovered
  exportSeverityAll.value = exportForm.severity.length === 6
  exportDialogVisible.value = true
}

const handleExport = async () => {
  if (!selectedConfigId.value) return

  if (exportForm.severity.length === 0) {
    ElMessage.warning('请至少选择一个告警级别')
    return
  }

  exporting.value = true
  try {
    const data: any = {
      zabbix_config_id: Number(selectedConfigId.value)
    }

    if (exportForm.timeFrom) {
      data.time_from = Math.floor(exportForm.timeFrom / 1000)
    }

    if (exportForm.timeTill) {
      data.time_till = Math.floor(exportForm.timeTill / 1000)
    }

    if (exportForm.severity.length > 0) {
      data.severity = exportForm.severity
    }

    if (exportForm.recovered && exportForm.recovered !== 'all') {
      data.recovered = exportForm.recovered
    }

    await createAlertExportTask(data)
    ElMessage.success('导出任务已创建，请在导出历史中查看进度')
    exportDialogVisible.value = false

    if (exportHistoryDialogVisible.value) {
      loadExportTasks()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建导出任务失败')
  } finally {
    exporting.value = false
  }
}

const showExportHistoryDialog = () => {
  exportHistoryDialogVisible.value = true
  loadExportTasks()
}

const loadExportTasks = async () => {
  tasksLoading.value = true
  try {
    exportTasks.value = await getAlertExportTasks()
  } catch (error) {
    console.error(error)
  } finally {
    tasksLoading.value = false
  }
}

// 下载导出文件
const handleDownloadExport = async (row: AlertExportTask) => {
  try {
    await downloadExportFile(row.id, row.filename || undefined)
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 初始化默认时间范围为最近24小时
const initDefaultTimeRange = () => {
  const now = Date.now()
  const yesterday = now - 24 * 60 * 60 * 1000
  filterForm.timeFrom = yesterday
  filterForm.timeTill = now
}

watch(selectedConfigId, () => {
  if (selectedConfigId.value) {
    loadAlerts()
  }
})

onMounted(() => {
  initDefaultTimeRange()
  if (selectedConfigId.value) {
    loadAlerts()
  }
})
</script>

<style scoped>
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
  gap: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.loading-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #409eff;
  font-size: 14px;
}

.mb-4 {
  margin-bottom: 1rem;
}

.cached-info {
  margin-left: 10px;
  color: #909399;
}

.data-placeholder {
  padding: 40px 0;
  text-align: center;
  color: #909399;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
