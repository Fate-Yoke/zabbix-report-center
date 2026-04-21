<template>
  <div class="admin-logs">
    <div class="page-header">
      <h2>
        <el-icon><Document /></el-icon>
        系统日志
      </h2>
    </div>

    <!-- 过滤器 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="日志级别">
          <el-select v-model="filters.levels" multiple placeholder="请选择" clearable collapse-tags collapse-tags-tooltip style="width: 180px">
            <el-option label="全选" value="all" />
            <el-option label="DEBUG" value="DEBUG" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
            <el-option label="CRITICAL" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="filters.start_time"
            type="datetime"
            placeholder="选择开始时间"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="filters.end_time"
            type="datetime"
            placeholder="选择结束时间"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button :type="isStreaming ? 'warning' : 'success'" @click="toggleStream">
            <el-icon><VideoPlay v-if="!isStreaming" /><VideoPause v-else /></el-icon>
            {{ isStreaming ? '停止实时' : '开启实时' }}
          </el-button>
          <el-button type="info" @click="clearFilters">
            <el-icon><Close /></el-icon> 清空筛选
          </el-button>
          <el-button type="danger" @click="showClearDialog">
            <el-icon><Delete /></el-icon> 清理日志
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志显示区域 -->
    <el-card class="log-card">
      <template #header>
        <div class="log-header">
          <span>日志列表</span>
          <div class="log-actions">
            <el-checkbox v-model="autoScroll">自动滚动</el-checkbox>
            <el-button size="small" type="warning" @click="clearLogDisplay">
              清空显示
            </el-button>
          </div>
        </div>
      </template>
      <div class="log-container" ref="logContainer">
        <div class="log-content">
          <div
            v-for="log in logs"
            :key="log.id"
            class="log-line"
          >
            <span class="log-time">{{ formatTime(log.created_at) }}</span>
            <span class="log-level" :style="{ color: getLevelColor(log.level) }">[{{ log.level }}]</span>
            <span class="log-source">{{ log.logger_name || log.source }}:</span>
            <span class="log-message">{{ escapeHtml(log.message) }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="log-count">共 {{ logs.length }} 条日志</span>
      </template>
    </el-card>

    <!-- 清理日志对话框 -->
    <el-dialog v-model="clearDialogVisible" title="清理旧日志" width="400px">
      <el-form>
        <el-form-item label="保留最近多少天的日志？">
          <el-input-number v-model="keepDays" :min="1" :max="365" />
        </el-form-item>
        <p class="form-tip">超过指定天数的日志将被永久删除</p>
      </el-form>
      <template #footer>
        <el-button @click="clearDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="executeClear">确认清理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getLogs, clearLogs } from '@/api/system'
import { Search, Delete, Close, VideoPlay, VideoPause, Document } from '@element-plus/icons-vue'
import type { SystemLog } from '@/types'

const logs = ref<SystemLog[]>([])
const loading = ref(false)
const isStreaming = ref(false)
const autoScroll = ref(true)
const clearDialogVisible = ref(false)
const keepDays = ref(30)
const logContainer = ref<HTMLElement | null>(null)
let streamInterval: number | null = null
let lastLogId = ref(0)

const allLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

const filters = reactive({
  levels: [...allLevels] as string[],
  start_time: null as Date | null,
  end_time: null as Date | null
})

// 日志级别颜色映射
const levelColors: Record<string, string> = {
  'DEBUG': '#808080',
  'INFO': '#4ec9b0',
  'WARNING': '#dcdcaa',
  'ERROR': '#f48771',
  'CRITICAL': '#ff0000'
}

const getLevelColor = (level: string): string => {
  return levelColors[level] || '#d4d4d4'
}

const formatTime = (time: string): string => {
  return new Date(time).toLocaleString()
}

// HTML转义，防止XSS
const escapeHtml = (text: string): string => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params: any = { limit: 500 }

    if (filters.start_time) params.start_time = new Date(filters.start_time).toISOString()
    if (filters.end_time) params.end_time = new Date(filters.end_time).toISOString()

    const result = await getLogs(params)

    // 前端过滤多级别
    let filteredLogs = result.logs
    // 如果没有选择任何级别，不显示日志
    if (filters.levels.length === 0) {
      filteredLogs = []
    } else {
      const isAllSelected = allLevels.every(level => filters.levels.includes(level))
      // 如果选择了部分级别（不是全选），则过滤
      if (!isAllSelected) {
        filteredLogs = result.logs.filter(log => filters.levels.includes(log.level))
      }
    }

    logs.value = [...filteredLogs].reverse()

    // 记录最后一条日志的 ID
    if (logs.value.length > 0) {
      lastLogId.value = logs.value[logs.value.length - 1].id
    }

    scrollToBottom()
  } catch (error) {
    console.error(error)
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const toggleStream = () => {
  if (isStreaming.value) {
    stopStream()
  } else {
    startStream()
  }
}

const startStream = () => {
  loadLatestLogs()
  streamInterval = window.setInterval(loadLatestLogs, 2000)
  isStreaming.value = true
}

const stopStream = () => {
  if (streamInterval) {
    clearInterval(streamInterval)
    streamInterval = null
  }
  isStreaming.value = false
}

const loadLatestLogs = async () => {
  try {
    const result = await getLogs({ limit: 100 })
    if (!result.logs || !Array.isArray(result.logs)) return

    // 如果没有选择任何级别，不显示新日志
    if (filters.levels.length === 0) {
      return
    }

    // 前端过滤多级别
    let filteredLogs = result.logs
    const isAllSelected = allLevels.every(level => filters.levels.includes(level))
    if (!isAllSelected) {
      filteredLogs = result.logs.filter(log => filters.levels.includes(log.level))
    }

    // 过滤出新日志
    const newLogs = filteredLogs.filter(log => log.id > lastLogId.value)

    if (newLogs.length > 0) {
      // 添加新日志
      logs.value.push(...[...newLogs].reverse())
      lastLogId.value = Math.max(...newLogs.map(log => log.id))
      scrollToBottom()
    }
  } catch (error) {
    console.error('轮询日志失败:', error)
  }
}

const scrollToBottom = () => {
  if (autoScroll.value && logContainer.value) {
    nextTick(() => {
      logContainer.value!.scrollTop = logContainer.value!.scrollHeight
    })
  }
}

const clearFilters = () => {
  filters.levels = [...allLevels]
  filters.start_time = null
  filters.end_time = null
}

// 是否全选状态
const isAllSelected = () => {
  return allLevels.every(level => filters.levels.includes(level))
}

// 监听日志级别选择，处理全选
watch(() => [...filters.levels], (newVal, oldVal) => {
  // 如果新选择了"全选"
  if (newVal.includes('all') && !oldVal.includes('all')) {
    // 当前是否已经全选了
    if (isAllSelected()) {
      // 已经全选了，再次点击全选就是取消全选
      filters.levels = []
    } else {
      // 没有全选，点击全选就是全选
      filters.levels = [...allLevels]
    }
  }
})

const clearLogDisplay = () => {
  logs.value = []
  lastLogId.value = 0
}

const showClearDialog = () => {
  clearDialogVisible.value = true
}

const executeClear = async () => {
  try {
    const result = await clearLogs(keepDays.value)
    ElMessage.success(result.message || `已删除 ${result.deleted} 条日志`)
    clearDialogVisible.value = false
    if (!isStreaming.value) {
      loadLogs()
    }
  } catch (error) {
    ElMessage.error('清理失败')
  }
}

onMounted(() => {
  loadLogs()
})

onUnmounted(() => {
  stopStream()
})
</script>

<style scoped>
.admin-logs {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
  overflow: hidden;
}

.page-header {
  margin-bottom: 15px;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.filter-card {
  margin-bottom: 15px;
}

.log-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.log-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.log-container {
  height: 100%;
  overflow-y: auto;
  background-color: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  padding: 10px;
}

.log-line {
  margin-bottom: 2px;
  line-height: 1.5;
}

.log-time {
  color: #808080;
  margin-right: 8px;
}

.log-level {
  font-weight: bold;
  margin-right: 8px;
}

.log-source {
  color: #569cd6;
  margin-right: 8px;
}

.log-message {
  word-break: break-all;
}

.log-count {
  color: #909399;
  font-size: 12px;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}
</style>
