<template>
  <div class="monitor">
    <div class="page-header">
      <h2>
        <el-icon><TrendCharts /></el-icon>
        监控信息
      </h2>
      <div class="header-actions">
        <el-button type="success" @click="createExportTask" :disabled="!selectedConfigId || selectedFilters.length === 0">
          <el-icon><Download /></el-icon> 导出Excel
        </el-button>
        <el-button type="info" @click="showExportHistoryDialog">
          <el-icon><Clock /></el-icon> 导出记录
        </el-button>
        <el-button type="primary" @click="showFilterDialog()">
          <el-icon><Plus /></el-icon> 新建筛选配置
        </el-button>
      </div>
    </div>

    <el-alert v-if="!selectedConfigId" type="warning" show-icon class="mb-4">
      请在左上角选择 Zabbix 配置
    </el-alert>

    <template v-else>
      <!-- 筛选配置列表 -->
      <el-card class="mb-4">
        <template #header>
          <div class="card-header">
            <span>筛选配置</span>
            <el-checkbox v-model="selectAllFilters" @change="handleSelectAll">全选</el-checkbox>
          </div>
        </template>

        <el-row :gutter="20" v-loading="loading">
          <el-col :span="6" v-for="filter in filters" :key="filter.id">
            <el-card class="filter-card" :class="{ 'disabled': !isFilterValid(filter) }">
              <div class="filter-header">
                <el-checkbox
                  v-model="selectedFilters"
                  :value="filter.id"
                  :disabled="!isFilterValid(filter)"
                >
                  <span class="filter-name">{{ filter.name }}</span>
                </el-checkbox>
              </div>
              <p class="description">{{ filter.description || '无描述' }}</p>
              <div class="patterns">
                <strong>监控项:</strong>
                <span v-if="filter.use_regex">{{ filter.regex_pattern }}</span>
                <span v-else>
                  <el-tag v-for="(p, idx) in filter.item_patterns?.slice(0, 2)" :key="idx" size="small" class="mr-1">
                    {{ p.pattern }}
                  </el-tag>
                  <span v-if="filter.item_patterns?.length > 2">...</span>
                </span>
              </div>
              <div class="config-badge">
                <el-tag v-if="isFilterValid(filter)" type="info" size="small">
                  应用到 {{ filter.zabbix_config_ids?.length || 0 }} 个配置
                </el-tag>
                <el-tag v-else type="warning" size="small">配置失效</el-tag>
              </div>
              <div class="actions">
                <el-button size="small" type="primary" :disabled="!isFilterValid(filter)" @click="viewData(filter)">
                  查看
                </el-button>
                <el-button size="small" type="info" @click="showFilterDialog(filter)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(filter.id)">删除</el-button>
              </div>
            </el-card>
          </el-col>
          <el-col :span="24" v-if="filters.length === 0">
            <el-empty v-if="selectedConfigId === 'unconfigured'" description="暂无未配置的筛选配置" />
            <el-empty v-else-if="loading" description="加载中..." />
            <el-empty v-else description="暂无筛选配置，请先创建" />
          </el-col>
        </el-row>
      </el-card>

      <!-- 监控数据区域 -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span>监控数据{{ currentFilterName ? `（${currentFilterName}）` : '' }}<span v-if="monitorCachedAt" class="cache-time-inline">（{{ cacheTimeText }}）</span></span>
            <div class="header-right">
              <div v-if="dataLoading" class="loading-info">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>{{ loadProgressText }}</span>
                <el-progress :percentage="loadProgress" :stroke-width="6" class="inline-progress" />
              </div>
              <el-button v-if="monitorData.length > 0" size="small" type="danger" @click="clearMonitorData">
                <el-icon><Delete /></el-icon> 清除数据
              </el-button>
            </div>
          </div>
        </template>
        <div v-if="!monitorData.length && !dataLoading" class="data-placeholder">
          <el-empty description="请选择筛选配置查看数据" />
        </div>
        <div v-else-if="monitorData.length">
          <el-alert v-if="dataLoadComplete" type="success" show-icon class="mb-4" closable>
            数据加载完成！共查询到 {{ monitorData.length }} 条监控数据
          </el-alert>
          <el-table :data="displayMonitorData" stripe border @sort-change="handleTableSort">
            <el-table-column label="序号" width="70" align="center">
              <template #default="{ $index }">{{ $index + 1 }}</template>
            </el-table-column>
            <el-table-column prop="groups" label="所属群组" width="150" show-overflow-tooltip sortable="custom" />
            <el-table-column prop="hostname" label="设备名" width="150" show-overflow-tooltip sortable="custom" />
            <el-table-column prop="ip" label="IP地址" width="130" sortable="custom" />
            <el-table-column prop="item_name" label="监控项" min-width="150" show-overflow-tooltip sortable="custom" />
            <el-table-column prop="current" label="当前值" width="100" sortable="custom" />
            <el-table-column prop="max" label="最大值" width="100" sortable="custom" />
            <el-table-column prop="min" label="最小值" width="100" sortable="custom" />
            <el-table-column prop="avg" label="平均值" width="100" sortable="custom" />
          </el-table>
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[20, 50, 100, 200]"
              :total="sortedMonitorData.length"
              layout="total, sizes, prev, pager, next, jumper"
              background
            />
          </div>
        </div>
      </el-card>
    </template>

    <!-- 筛选配置编辑弹窗 -->
    <el-dialog v-model="filterDialogVisible" :title="isEdit ? '编辑筛选配置' : '新建筛选配置'" width="700px">
      <el-form :model="filterForm" :rules="filterRules" ref="filterFormRef" label-width="120px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="filterForm.name" placeholder="如：CPU使用率" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="filterForm.description" type="textarea" rows="2" placeholder="配置描述" />
        </el-form-item>

        <el-form-item label="匹配方式">
          <el-checkbox v-model="filterForm.use_regex">使用正则表达式匹配</el-checkbox>
        </el-form-item>

        <!-- 正则表达式输入 -->
        <el-form-item v-if="filterForm.use_regex" label="正则表达式" prop="regex_pattern">
          <el-input v-model="filterForm.regex_pattern" placeholder="例如：CPU.*utilization|Memory.*usage" />
          <div class="form-tip">输入正则表达式来匹配监控项名称</div>
        </el-form-item>

        <!-- 监控项列表 -->
        <el-form-item v-else label="监控项列表" prop="item_patterns">
          <div class="pattern-list">
            <div v-for="(pattern, idx) in filterForm.item_patterns" :key="idx" class="pattern-item">
              <el-input v-model="pattern.pattern" placeholder="监控项名称" style="flex: 1" />
              <el-select v-model="pattern.match_type" style="width: 120px">
                <el-option label="精确匹配" value="exact" />
                <el-option label="模糊匹配" value="fuzzy" />
              </el-select>
              <el-button type="danger" :icon="Delete" circle size="small" @click="removePattern(idx)" />
            </div>
            <el-button type="primary" size="small" @click="addPattern">
              <el-icon><Plus /></el-icon> 添加监控项
            </el-button>
            <div class="form-tip">
              <strong>精确匹配</strong>：完全匹配监控项名称<br>
              <strong>模糊匹配</strong>：支持通配符 * 和 ?
            </div>
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="历史数据类型">
              <el-select v-model="filterForm.history_type" style="width: 100%">
                <el-option label="数值(浮点)" :value="0" />
                <el-option label="字符" :value="1" />
                <el-option label="日志" :value="2" />
                <el-option label="数值(无符号)" :value="3" />
                <el-option label="文本" :value="4" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位转换">
              <el-select v-model="unitConversion" style="width: 100%">
                <el-option label="否" value="none" />
                <el-option label="网络(bps→Mbps)" value="network" />
                <el-option label="存储(B→GB)" value="storage" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="Zabbix配置" prop="zabbix_config_ids">
          <div class="zabbix-permissions">
            <p class="form-tip">勾选要应用此筛选配置的Zabbix配置（至少选择一个）</p>
            <el-checkbox-group v-model="filterForm.zabbix_config_ids">
              <el-checkbox v-for="config in zabbixConfigs" :key="config.id" :value="config.id">
                {{ config.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div v-if="zabbixConfigs.length === 0" class="text-muted">暂无Zabbix配置</div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="filterDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveFilter" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 导出确认对话框 -->
    <el-dialog v-model="exportConfirmVisible" title="导出选项" width="450px">
      <p>是否在导出的Excel中包含"设备概览"工作簿？</p>
      <el-alert type="info" show-icon class="mt-4">
        <strong>设备概览</strong>：包含所有在线设备的基本信息（主机名、IP、所属群组等）
      </el-alert>
      <template #footer>
        <el-button @click="exportConfirmVisible = false">取消</el-button>
        <el-button type="primary" plain @click="executeExport(false)">
          <el-icon><Document /></el-icon> 不包含
        </el-button>
        <el-button type="primary" @click="executeExport(true)">
          <el-icon><Document /></el-icon> 包含设备概览
        </el-button>
      </template>
    </el-dialog>

    <!-- 导出历史弹窗 -->
    <el-dialog v-model="exportHistoryVisible" title="导出记录" width="800px">
      <el-table :data="exportTasks" v-loading="tasksLoading" stripe>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTimeString(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="zabbix_config_name" label="配置名称" width="120" />
        <el-table-column label="筛选配置" width="150">
          <template #default="{ row }">
            {{ (row.filter_names || []).join(', ') || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusType(row.status)" size="small">
              {{ getTaskStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button v-if="row.status === 'completed'" size="small" type="primary" @click="downloadExport(row.id)">
              下载
            </el-button>
            <el-button v-if="row.status === 'completed' || row.status === 'failed'" size="small" type="danger" @click="deleteExportTask(row.id)">
              删除
            </el-button>
            <span v-if="row.status === 'pending' || row.status === 'processing'" class="text-muted">处理中...</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="exportHistoryVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, onUnmounted, shallowRef, triggerRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus, Download, Clock, ArrowDown, Document, Loading } from '@element-plus/icons-vue'
import { useZabbixConfigStore } from '@/stores/zabbixConfig'
import { useAuthStore } from '@/stores/auth'
import { getFilters, createFilter, updateFilter, deleteFilter, createQueryTask, getQueryTaskData, clearQueryTaskCache, createExportTask as createExportTaskApi, getExportTasks, downloadExportFile, deleteExportTask as deleteExportTaskApi } from '@/api/monitor'
import { getAllConfigs } from '@/api/zabbixConfig'
import type { MonitorFilter, ZabbixConfig } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

// 获取 API 基础地址
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

const zabbixConfigStore = useZabbixConfigStore()
const authStore = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const tasksLoading = ref(false)
const filters = ref<MonitorFilter[]>([])
const zabbixConfigs = ref<ZabbixConfig[]>([])
const selectedFilters = ref<number[]>([])
const selectAllFilters = ref(false)
const filterDialogVisible = ref(false)
const exportConfirmVisible = ref(false)
const exportHistoryVisible = ref(false)
const isEdit = ref(false)
const editFilterId = ref<number | null>(null)
const filterFormRef = ref<FormInstance>()

// 监控数据 - 使用 shallowRef 避免深度响应式，提升大数据性能
const monitorData = shallowRef<any[]>([])
const currentFilterName = ref<string>('')  // 当前查询的筛选配置名称
const monitorCachedAt = ref<string>('')  // 缓存时间
const currentPage = ref(1)
const pageSize = ref(50)
const dataLoadComplete = ref(false)
const dataLoading = ref(false)
const loadProgress = ref(0)
const loadProgressText = ref('正在初始化...')
const totalHosts = ref(0)
const processedHosts = ref(0)

// 排序状态
const sortColumn = ref<string | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')

// 导出任务
const exportTasks = ref<any[]>([])

const selectedConfigId = computed(() => zabbixConfigStore.selectedConfigId)

// 排序函数
const sortMonitorData = (column: string) => {
  if (sortColumn.value === column) {
    // 点击同一列，切换排序方向
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    // 点击新列，默认升序
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
}

// 排序后的数据
const sortedMonitorData = computed(() => {
  if (!sortColumn.value) return monitorData.value

  const data = [...monitorData.value]
  const column = sortColumn.value
  const direction = sortDirection.value

  // 数值列（当前值、最大值、最小值、平均值）
  const numericColumns = ['current', 'max', 'min', 'avg']

  data.sort((a, b) => {
    let valA = a[column]
    let valB = b[column]

    if (numericColumns.includes(column)) {
      // 提取数值部分进行比较
      valA = parseFloat(valA) || 0
      valB = parseFloat(valB) || 0
    } else {
      // 字符串列，转为小写比较
      valA = String(valA || '').toLowerCase()
      valB = String(valB || '').toLowerCase()
    }

    if (valA < valB) return direction === 'asc' ? -1 : 1
    if (valA > valB) return direction === 'asc' ? 1 : -1
    return 0
  })

  return data
})

const displayMonitorData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return sortedMonitorData.value.slice(start, end)
})

// 缓存时间文本
const cacheTimeText = computed(() => {
  if (!monitorCachedAt.value) return ''
  const updateTime = new Date(monitorCachedAt.value)
  const now = new Date()
  const diffSeconds = Math.floor((now.getTime() - updateTime.getTime()) / 1000)

  if (diffSeconds < 60) {
    return '刚刚更新'
  } else if (diffSeconds < 3600) {
    return `${Math.floor(diffSeconds / 60)}分钟前`
  } else {
    return `${Math.floor(diffSeconds / 3600)}小时前`
  }
})

const unitConversion = ref('none')

const filterForm = reactive({
  name: '',
  description: '',
  use_regex: false,
  regex_pattern: '',
  item_patterns: [{ pattern: '', match_type: 'fuzzy' }] as { pattern: string; match_type: string }[],
  history_type: 0,
  zabbix_config_ids: [] as number[]
})

const filterRules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  zabbix_config_ids: [{ required: true, message: '请至少选择一个Zabbix配置', trigger: 'change', type: 'array' }]
}

const handleSelectAll = (val: boolean) => {
  if (val) {
    selectedFilters.value = filters.value
      .filter(f => isFilterValid(f))
      .map(f => f.id)
  } else {
    selectedFilters.value = []
  }
}

const formatTimeString = (timeStr: string) => {
  return new Date(timeStr).toLocaleString()
}

const getTaskStatusType = (status: string): 'info' | 'warning' | 'danger' | 'primary' | 'success' => {
  const types: Record<string, 'info' | 'warning' | 'success' | 'danger' | 'primary'> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getTaskStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '完成',
    failed: '失败'
  }
  return texts[status] || status
}

const loadFilters = async () => {
  if (!selectedConfigId.value) return

  loading.value = true
  try {
    const configId = selectedConfigId.value

    if (configId === 'unconfigured') {
      // 选择"未配置"时，获取所有筛选配置，然后过滤出未配置的
      const allFilters = await getFilters()
      const activeConfigIds = zabbixConfigs.value.filter(c => c.is_active).map(c => c.id)
      filters.value = allFilters.filter(f => {
        // 没有关联任何配置
        if (!f.zabbix_config_ids || f.zabbix_config_ids.length === 0) {
          return true
        }
        // 所有关联的配置都已被删除或不可访问
        const accessibleConfigs = f.zabbix_config_ids.filter(id => activeConfigIds.includes(id))
        return accessibleConfigs.length === 0
      })
    } else {
      // 选择具体配置时，按配置ID过滤
      filters.value = await getFilters(Number(configId))
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadZabbixConfigs = async () => {
  try {
    zabbixConfigs.value = await getAllConfigs()
  } catch (error) {
    console.error(error)
  }
}

// 判断筛选配置是否有效（有关联的有效 Zabbix 配置）
const isFilterValid = (filter: MonitorFilter): boolean => {
  if (!filter.zabbix_config_ids || filter.zabbix_config_ids.length === 0) {
    return false
  }
  // 检查是否有关联的配置还有效（启用状态）
  const activeConfigIds = zabbixConfigs.value.filter(c => c.is_active).map(c => c.id)
  const accessibleConfigs = filter.zabbix_config_ids.filter(id => activeConfigIds.includes(id))
  return accessibleConfigs.length > 0
}

const showFilterDialog = (filter?: MonitorFilter) => {
  isEdit.value = !!filter
  editFilterId.value = filter?.id || null

  if (filter) {
    filterForm.name = filter.name
    filterForm.description = filter.description || ''
    filterForm.use_regex = filter.use_regex || false
    filterForm.regex_pattern = filter.regex_pattern || ''
    filterForm.item_patterns = filter.item_patterns?.length
      ? [...filter.item_patterns] as { pattern: string; match_type: string }[]
      : [{ pattern: '', match_type: 'fuzzy' }]
    filterForm.history_type = filter.history_type || 0
    filterForm.zabbix_config_ids = filter.zabbix_config_ids || []

    if (filter.is_storage) {
      unitConversion.value = 'storage'
    } else if (filter.is_network) {
      unitConversion.value = 'network'
    } else {
      unitConversion.value = 'none'
    }
  } else {
    filterForm.name = ''
    filterForm.description = ''
    filterForm.use_regex = false
    filterForm.regex_pattern = ''
    filterForm.item_patterns = [{ pattern: '', match_type: 'fuzzy' }]
    filterForm.history_type = 0
    filterForm.zabbix_config_ids = selectedConfigId.value ? [Number(selectedConfigId.value)] : []
    unitConversion.value = 'none'
  }

  filterDialogVisible.value = true
}

const addPattern = () => {
  filterForm.item_patterns.push({ pattern: '', match_type: 'fuzzy' })
}

const removePattern = (idx: number) => {
  if (filterForm.item_patterns.length > 1) {
    filterForm.item_patterns.splice(idx, 1)
  } else {
    ElMessage.warning('至少需要保留一个监控项')
  }
}

const handleSaveFilter = async () => {
  if (!filterFormRef.value) return

  await filterFormRef.value.validate(async (valid) => {
    if (!valid) return

    // 验证监控项或正则
    if (!filterForm.use_regex && !filterForm.item_patterns.some(p => p.pattern)) {
      ElMessage.error('请至少添加一个监控项')
      return
    }
    if (filterForm.use_regex && !filterForm.regex_pattern) {
      ElMessage.error('请输入正则表达式')
      return
    }

    saving.value = true
    try {
      const data: any = {
        name: filterForm.name,
        description: filterForm.description,
        use_regex: filterForm.use_regex,
        history_type: filterForm.history_type,
        is_network: unitConversion.value === 'network',
        is_storage: unitConversion.value === 'storage',
        zabbix_config_ids: filterForm.zabbix_config_ids
      }

      if (filterForm.use_regex) {
        data.regex_pattern = filterForm.regex_pattern
        data.item_patterns = null
      } else {
        data.item_patterns = filterForm.item_patterns.filter(p => p.pattern)
        data.regex_pattern = null
      }

      if (isEdit.value && editFilterId.value) {
        await updateFilter(editFilterId.value, data)
        ElMessage.success('保存成功')
      } else {
        await createFilter(data)
        ElMessage.success('添加成功')
      }

      filterDialogVisible.value = false
      loadFilters()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此配置吗？', '提示', { type: 'warning' })
    await deleteFilter(id)
    ElMessage.success('删除成功')
    loadFilters()
  } catch {
    // 用户取消
  }
}

// 查询任务ID（用于轮询）
const currentQueryTaskId = ref<number | null>(null)

// 保存查询状态到 localStorage
const saveQueryState = (taskId: number, zabbixConfigId: number, filterName: string) => {
  localStorage.setItem('monitor_query_task', JSON.stringify({
    taskId,
    zabbixConfigId,
    filterName,
    createdAt: Date.now()
  }))
}

// 清除保存的查询状态
const clearQueryState = () => {
  localStorage.removeItem('monitor_query_task')
}

// 恢复查询状态
const restoreQueryState = async () => {
  const saved = localStorage.getItem('monitor_query_task')
  if (!saved) return

  try {
    const { taskId, zabbixConfigId, filterName, createdAt } = JSON.parse(saved)

    // 如果超过30分钟，清除状态
    if (Date.now() - createdAt > 30 * 60 * 1000) {
      clearQueryState()
      return
    }

    // 只有当前选中的配置与保存的一致时才恢复
    if (zabbixConfigId !== Number(selectedConfigId.value)) {
      return
    }

    // 检查任务状态
    const response = await fetch(`${apiBaseUrl}/api/monitor/export/tasks/${taskId}`, {
      headers: {
        ...(localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {})
      }
    })

    if (!response.ok) {
      clearQueryState()
      return
    }

    const task = await response.json()

    if (task.status === 'completed') {
      // 任务已完成，尝试获取数据
      try {
        const result = await getQueryTaskData(taskId)
        console.log('恢复数据:', result)
        if (result && result.data) {
          monitorData.value = result.data
          triggerRef(monitorData)
          dataLoadComplete.value = true
          loadProgress.value = 100
          loadProgressText.value = '加载完成'
          currentFilterName.value = filterName || ''
          monitorCachedAt.value = result.completed_at || ''
          ElMessage.success(`数据已恢复！共 ${result.count} 条数据`)
        } else {
          console.error('数据格式无效:', result)
          clearQueryState()
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        clearQueryState()
      }
    } else if (task.status === 'processing' || task.status === 'pending') {
      // 任务还在进行中，继续轮询
      currentQueryTaskId.value = taskId
      dataLoading.value = true
      loadProgressText.value = '正在恢复查询任务...'
      currentFilterName.value = filterName || ''
      pollQueryTask(taskId)
    } else {
      // 任务失败或不存在
      clearQueryState()
    }
  } catch (error) {
    console.error('恢复查询状态失败:', error)
    clearQueryState()
  }
}

const viewData = async (filter: MonitorFilter) => {
  // 如果正在查询，提示用户
  if (dataLoading.value) {
    try {
      await ElMessageBox.confirm(
        '当前有查询任务正在进行中，是否取消并开始新查询？',
        '提示',
        { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
      )
    } catch {
      // 用户取消
      return
    }
  }

  // 重置加载状态
  currentPage.value = 1
  dataLoadComplete.value = false
  dataLoading.value = true
  loadProgress.value = 0
  loadProgressText.value = '正在后台查询数据，您可以继续其他操作...'
  totalHosts.value = 0
  processedHosts.value = 0
  sortColumn.value = null
  sortDirection.value = 'asc'
  currentFilterName.value = filter.name  // 保存当前筛选配置名称

  // 取消之前的轮询
  currentQueryTaskId.value = null

  try {
    // 创建后台查询任务
    const task = await createQueryTask({
      filter_ids: [filter.id],
      zabbix_config_id: Number(selectedConfigId.value),
      time_range: 86400
    })

    currentQueryTaskId.value = task.id
    loadProgressText.value = '查询任务已创建，正在后台处理...'

    // 保存任务状态到 localStorage
    saveQueryState(task.id, Number(selectedConfigId.value), filter.name)

    // 开始轮询任务状态
    pollQueryTask(task.id)
  } catch (error: any) {
    console.error('创建查询任务失败:', error)
    ElMessage.error('创建查询任务失败')
    dataLoading.value = false
  }
}

// 轮询查询任务状态
const pollQueryTask = async (taskId: number) => {
  const checkStatus = async () => {
    try {
      // 检查任务是否已被取消（用户点击了清除）
      if (currentQueryTaskId.value !== taskId) {
        return
      }

      const response = await fetch(`${apiBaseUrl}/api/monitor/export/tasks/${taskId}`, {
        headers: {
          ...(localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {})
        }
      })

      if (!response.ok) {
        dataLoading.value = false
        clearQueryState()
        return
      }

      const task = await response.json()

      if (task.status === 'completed') {
        // 任务完成，获取数据
        loadProgressText.value = '正在加载数据...'
        try {
          const result = await getQueryTaskData(taskId)
          console.log('查询完成数据:', result)
          if (result && result.data) {
            monitorData.value = result.data
            triggerRef(monitorData)
            dataLoadComplete.value = true
            loadProgress.value = 100
            loadProgressText.value = '加载完成'
            monitorCachedAt.value = result.completed_at || ''
            ElMessage.success(`数据加载完成！共获取 ${result.count} 条数据`)
          } else {
            console.error('数据格式无效:', result)
            ElMessage.error('数据格式无效')
          }
        } catch (error) {
          console.error('获取数据失败:', error)
          ElMessage.error('获取数据失败')
        } finally {
          dataLoading.value = false
          currentQueryTaskId.value = null
        }
      } else if (task.status === 'failed') {
        ElMessage.error('查询失败: ' + (task.error_message || '未知错误'))
        dataLoading.value = false
        currentQueryTaskId.value = null
        clearQueryState()
      } else {
        // 继续轮询（每2秒）
        setTimeout(checkStatus, 2000)
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
      dataLoading.value = false
      currentQueryTaskId.value = null
      clearQueryState()
    }
  }

  setTimeout(checkStatus, 1000)
}

// 处理表格排序
const handleTableSort = ({ prop, order }: { prop: string; order: string | null }) => {
  if (!order) {
    sortColumn.value = null
    sortDirection.value = 'asc'
  } else {
    sortColumn.value = prop
    sortDirection.value = order === 'ascending' ? 'asc' : 'desc'
  }
}

// 清除监控数据
const clearMonitorData = async () => {
  // 如果有缓存的任务ID，调用后端删除缓存文件
  const saved = localStorage.getItem('monitor_query_task')
  if (saved) {
    try {
      const { taskId } = JSON.parse(saved)
      await clearQueryTaskCache(taskId)
    } catch (error) {
      console.error('清除缓存失败:', error)
    }
  }

  monitorData.value = []
  triggerRef(monitorData)
  currentPage.value = 1
  dataLoadComplete.value = false
  dataLoading.value = false
  loadProgress.value = 0
  loadProgressText.value = ''
  totalHosts.value = 0
  monitorCachedAt.value = ''
  processedHosts.value = 0
  sortColumn.value = null
  sortDirection.value = 'asc'
  currentFilterName.value = ''  // 清除筛选名称
  // 取消正在进行的查询任务
  currentQueryTaskId.value = null
  // 清除保存的查询状态
  clearQueryState()
  ElMessage.success('数据已清除')
}

const createExportTask = () => {
  if (selectedFilters.value.length === 0) {
    ElMessage.warning('请勾选要导出的筛选配置')
    return
  }
  exportConfirmVisible.value = true
}

const executeExport = async (includeDeviceOverview: boolean) => {
  exportConfirmVisible.value = false

  try {
    const task = await createExportTaskApi({
      filter_ids: selectedFilters.value,
      zabbix_config_id: Number(selectedConfigId.value),
      include_device_overview: includeDeviceOverview
    })
    ElMessage.success('导出任务已创建，请在导出记录中查看进度')
    // 开始轮询任务状态
    pollExportTask(task.id)
  } catch (error) {
    console.error(error)
    ElMessage.error('创建导出任务失败')
  }
}

const showExportHistoryDialog = async () => {
  exportHistoryVisible.value = true
  tasksLoading.value = true
  try {
    await loadExportTasks()
  } catch (error) {
    console.error(error)
  } finally {
    tasksLoading.value = false
  }
}

const downloadExport = async (taskId: number) => {
  try {
    await downloadExportFile(taskId)
  } catch (error: any) {
    ElMessage.error(error.message || '下载失败')
  }
}

const deleteExportTask = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条导出记录吗？', '提示', { type: 'warning' })
    await deleteExportTaskApi(taskId)
    ElMessage.success('删除成功')
    exportTasks.value = await getExportTasks(20)
  } catch {
    // 用户取消
  }
}

// 导出历史自动刷新定时器
let exportHistoryRefreshTimer: ReturnType<typeof setInterval> | null = null

// 轮询导出任务状态
const pollExportTask = async (taskId: number) => {
  const checkStatus = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/monitor/export/tasks/${taskId}`, {
        headers: {
          ...(localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {})
        }
      })
      if (!response.ok) return

      const task = await response.json()

      if (task.status === 'completed') {
        ElMessage.success('导出完成，可前往导出记录下载')
        // 如果导出历史弹窗已打开，刷新列表
        if (exportHistoryVisible.value) {
          loadExportTasks()
        }
      } else if (task.status === 'failed') {
        ElMessage.error('导出失败: ' + (task.error_message || '未知错误'))
      } else {
        // 继续轮询
        setTimeout(checkStatus, 2000)
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
  }

  setTimeout(checkStatus, 2000)
}

// 加载导出任务列表（带自动刷新）
const loadExportTasks = async () => {
  try {
    exportTasks.value = await getExportTasks(20)
  } catch (error) {
    console.error(error)
  }

  // 检查是否有处理中的任务
  const hasProcessing = exportTasks.value.some(t => t.status === 'pending' || t.status === 'processing')

  if (hasProcessing) {
    // 如果有处理中的任务，启动自动刷新（每3秒）
    if (!exportHistoryRefreshTimer) {
      exportHistoryRefreshTimer = setInterval(() => {
        loadExportTasks()
      }, 3000)
    }
  } else {
    // 如果没有处理中的任务，停止自动刷新
    if (exportHistoryRefreshTimer) {
      clearInterval(exportHistoryRefreshTimer)
      exportHistoryRefreshTimer = null
    }
  }
}

// 监听导出历史弹窗关闭
watch(exportHistoryVisible, (visible) => {
  if (!visible && exportHistoryRefreshTimer) {
    clearInterval(exportHistoryRefreshTimer)
    exportHistoryRefreshTimer = null
  }
})

watch(selectedConfigId, () => {
  if (selectedConfigId.value) {
    loadFilters()
  }
})

watch(selectedFilters, () => {
  selectAllFilters.value = selectedFilters.value.length === filters.value.filter(f => isFilterValid(f)).length
})

onMounted(async () => {
  loadZabbixConfigs()
  if (selectedConfigId.value) {
    loadFilters()
    // 恢复之前的查询状态
    await restoreQueryState()
  }
})

onUnmounted(() => {
  // 清理定时器
  if (exportHistoryRefreshTimer) {
    clearInterval(exportHistoryRefreshTimer)
    exportHistoryRefreshTimer = null
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

.cache-time-inline {
  color: #909399;
  font-size: 0.875rem;
  font-weight: normal;
  margin-left: 5px;
}

.loading-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #409eff;
  font-size: 14px;
}

.inline-progress {
  width: 100px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-card.disabled {
  opacity: 0.6;
}

.filter-header {
  margin-bottom: 10px;
}

.filter-name {
  font-weight: 600;
}

.filter-card .description {
  color: #909399;
  font-size: 13px;
  margin-bottom: 10px;
}

.filter-card .patterns {
  margin-bottom: 10px;
  font-size: 13px;
}

.filter-card .config-badge {
  margin-bottom: 10px;
}

.filter-card .actions {
  display: flex;
  gap: 10px;
}

.pattern-list {
  width: 100%;
}

.pattern-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.zabbix-permissions {
  max-height: 150px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.data-placeholder {
  padding: 40px 0;
  text-align: center;
  color: #909399;
}

.data-loading {
  padding: 40px 0;
  text-align: center;
  color: #409eff;
}

.data-loading p {
  margin: 10px 0;
}

.progress-bar {
  max-width: 400px;
  margin: 0 auto;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}

.mb-4 {
  margin-bottom: 1rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.mr-1 {
  margin-right: 0.25rem;
}

.text-muted {
  color: #909399;
}
</style>
