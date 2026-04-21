<template>
  <div class="tasks">
    <div class="page-header">
      <h2>
        <el-icon><Clock /></el-icon>
        定时任务
      </h2>
      <el-button type="primary" @click="showTaskDialog()">
        <el-icon><Plus /></el-icon> 添加任务
      </el-button>
    </div>

    <el-card>
      <el-table :data="filteredTasks" v-loading="loading" stripe :row-class-name="getRowClassName">
        <el-table-column prop="name" label="任务名称" min-width="150">
          <template #default="{ row }">
            {{ row.name }}
            <el-tag v-if="!row.is_valid" type="warning" size="small" class="ml-1">配置失效</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Zabbix配置" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_valid" type="info" size="small">{{ getZabbixName(row.zabbix_config_id) }}</el-tag>
            <el-tag v-else type="warning" size="small">{{ getZabbixName(row.zabbix_config_id) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="Cron表达式" width="140">
          <template #default="{ row }">
            <code>{{ row.cron_expression }}</code>
          </template>
        </el-table-column>
        <el-table-column label="收件人" min-width="180">
          <template #default="{ row }">
            <span class="recipients-text">{{ (row.recipients || []).join(', ') || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上次执行" width="160">
          <template #default="{ row }">
            {{ formatTime(row.last_run) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="360" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="success" @click="runTask(row)" :disabled="!row.is_valid">
                <el-icon><VideoPlay /></el-icon> 执行
              </el-button>
              <el-button size="small" type="primary" @click="showTaskDialog(row)">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button
                size="small"
                :type="row.is_active ? 'warning' : 'success'"
                @click="toggleTask(row)"
                :disabled="!row.is_valid"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button size="small" type="info" @click="showLogsDialog(row)">
                <el-icon><Document /></el-icon> 日志
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row.id)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 任务编辑弹窗 -->
    <el-dialog v-model="taskDialogVisible" :title="isEdit ? '编辑任务' : '添加任务'" width="800px" destroy-on-close>
      <el-form :model="taskForm" :rules="taskRules" ref="taskFormRef" label-width="110px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" prop="name">
              <el-input v-model="taskForm.name" placeholder="任务名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Cron表达式" prop="cron_expression">
              <el-input v-model="taskForm.cron_expression" placeholder="0 0 * * * (每天0点执行)">
                <template #append>
                  <el-popover placement="top" :width="300" trigger="click">
                    <template #reference>
                      <el-button :icon="QuestionFilled" />
                    </template>
                    <div class="cron-help">
                      <p><strong>格式：</strong>分 时 日 月 周</p>
                      <p><strong>示例：</strong></p>
                      <ul>
                        <li><code>0 0 * * *</code> 每天0点</li>
                        <li><code>0 */2 * * *</code> 每2小时</li>
                        <li><code>30 8 * * 1-5</code> 工作日8:30</li>
                        <li><code>0 0 1 * *</code> 每月1号0点</li>
                      </ul>
                    </div>
                  </el-popover>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="2" placeholder="任务描述（可选）" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Zabbix配置" prop="zabbix_config_id">
              <el-select v-model="taskForm.zabbix_config_id" placeholder="选择Zabbix配置" style="width: 100%" @change="handleZabbixChange">
                <el-option v-for="config in zabbixConfigs" :key="config.id" :label="config.name" :value="config.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮件配置" prop="email_config_id">
              <el-select v-model="taskForm.email_config_id" placeholder="选择邮件配置" style="width: 100%">
                <el-option v-for="config in activeEmailConfigs" :key="config.id" :label="config.name" :value="config.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">
          <el-icon><Message /></el-icon> 邮件设置
        </el-divider>

        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="邮件标题" prop="email_subject">
              <el-input v-model="taskForm.email_subject" placeholder="例如：每日巡检报告" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="标题后缀">
              <el-checkbox v-model="taskForm.subject_suffix_config_name">添加配置名称</el-checkbox>
              <el-checkbox v-model="taskForm.subject_suffix_timestamp">添加时间戳</el-checkbox>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="邮件内容">
          <el-input v-model="taskForm.email_body" type="textarea" :rows="3" placeholder="邮件正文内容（可选）" />
          <div class="email-options">
            <el-checkbox v-model="taskForm.email_include_device_overview">附加设备概览摘要</el-checkbox>
            <el-checkbox v-model="taskForm.email_include_monitor_summary">附加监控数据摘要</el-checkbox>
            <el-checkbox v-model="taskForm.email_include_alert_summary">附加告警数据摘要</el-checkbox>
          </div>
        </el-form-item>

        <el-divider content-position="left">
          <el-icon><DataAnalysis /></el-icon> 监控内容
        </el-divider>

        <el-form-item label="Excel附件内容">
          <div class="excel-options">
            <el-checkbox v-model="taskForm.include_device_overview">包含设备概览（工作簿）</el-checkbox>
            <el-checkbox v-model="taskForm.include_alert_data">附加告警数据（工作簿）</el-checkbox>
          </div>
        </el-form-item>

        <el-form-item label="筛选配置" prop="monitor_filter_ids">
          <div class="filter-box" v-loading="filtersLoading">
            <el-checkbox-group v-model="taskForm.monitor_filter_ids">
              <el-checkbox v-for="filter in availableFilters" :key="filter.id" :value="filter.id">
                {{ filter.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div v-if="availableFilters.length === 0 && !filtersLoading" class="no-filters">
              {{ taskForm.zabbix_config_id ? '该配置暂无筛选配置' : '请先选择Zabbix配置' }}
            </div>
          </div>
        </el-form-item>

        <el-form-item label="收件人邮箱" prop="recipients">
          <el-select
            v-model="taskForm.recipients"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入邮箱地址后回车添加"
            style="width: 100%"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="时间范围" prop="time_range">
              <el-input-number v-model="taskForm.time_range" :min="60" :max="2592000" style="width: 100%" />
              <div class="form-tip">默认86400秒（24小时）</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用">
              <el-checkbox v-model="taskForm.is_active">启用任务</el-checkbox>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTask" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 日志弹窗 -->
    <el-dialog v-model="logsDialogVisible" :title="`${currentTask?.name || '任务'} - 执行日志`" width="800px">
      <el-table :data="taskLogs" v-loading="logsLoading" stripe>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getLogStatusType(row.status)" size="small">
              {{ getLogStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开始时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column label="结束时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.finished_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="message" label="信息" show-overflow-tooltip />
        <el-table-column label="附件" width="120">
          <template #default="{ row }">
            <el-button v-if="row.attachment_filename && row.status === 'success'" size="small" link type="primary" @click="downloadLog(row.id)">
              {{ row.attachment_filename }}
            </el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { QuestionFilled, Clock, Plus, Edit, Delete, Document, VideoPlay, VideoPause, Message, DataAnalysis } from '@element-plus/icons-vue'
import { getAllTasks, createTask, updateTask, deleteTask, runTask as runTaskApi, getTaskLogs, downloadLogFile } from '@/api/tasks'
import { getAllConfigs as getZabbixConfigs } from '@/api/zabbixConfig'
import { getAllConfigs as getEmailConfigs } from '@/api/emailConfig'
import { getFilters } from '@/api/monitor'
import { useZabbixConfigStore } from '@/stores/zabbixConfig'
import { useAuthStore } from '@/stores/auth'
import type { Task, TaskLog, ZabbixConfig, EmailConfig, MonitorFilter } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

interface TaskWithExtra extends Task {
  description?: string
  time_range?: number
  email_subject?: string
  email_body?: string
  subject_suffix_config_name?: boolean
  subject_suffix_timestamp?: boolean
  email_include_device_overview?: boolean
  email_include_monitor_summary?: boolean
  email_include_alert_summary?: boolean
  include_device_overview?: boolean
  include_alert_data?: boolean
  monitor_filter_ids?: number[]
  is_valid?: boolean
}

interface TaskLogExtra extends TaskLog {
  started_at?: string
  finished_at?: string
  attachment_filename?: string
}

const zabbixConfigStore = useZabbixConfigStore()
const authStore = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const filtersLoading = ref(false)
const logsLoading = ref(false)
const tasks = ref<TaskWithExtra[]>([])
const zabbixConfigs = ref<ZabbixConfig[]>([])
const emailConfigs = ref<EmailConfig[]>([])
const availableFilters = ref<MonitorFilter[]>([])
const taskDialogVisible = ref(false)
const logsDialogVisible = ref(false)
const isEdit = ref(false)
const editTaskId = ref<number | null>(null)
const taskFormRef = ref<FormInstance>()
const currentTask = ref<TaskWithExtra | null>(null)
const taskLogs = ref<TaskLogExtra[]>([])
const logRefreshTimer = ref<ReturnType<typeof setInterval> | null>(null)
let runningNotificationInstance: ReturnType<typeof ElNotification> | null = null

const taskForm = reactive({
  name: '',
  description: '',
  cron_expression: '',
  zabbix_config_id: null as number | null,
  email_config_id: null as number | null,
  monitor_filter_ids: [] as number[],
  recipients: [] as string[],
  time_range: 86400,
  email_subject: '',
  email_body: '',
  subject_suffix_config_name: false,
  subject_suffix_timestamp: false,
  email_include_device_overview: true,
  email_include_monitor_summary: true,
  email_include_alert_summary: false,
  include_device_overview: true,
  include_alert_data: false,
  is_active: true
})

const taskRules: FormRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  cron_expression: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }],
  zabbix_config_id: [{ required: true, message: '请选择Zabbix配置', trigger: 'change' }],
  email_config_id: [{ required: true, message: '请选择邮件配置', trigger: 'change' }],
  monitor_filter_ids: [{ required: true, message: '请选择筛选配置', trigger: 'change', type: 'array' }],
  recipients: [{ required: true, message: '请添加收件人邮箱', trigger: 'change', type: 'array' }],
  email_subject: [{ required: true, message: '请输入邮件标题', trigger: 'blur' }],
  time_range: [{ required: true, message: '请输入时间范围', trigger: 'blur' }]
}

const selectedConfigId = computed(() => zabbixConfigStore.selectedConfigId)

const activeEmailConfigs = computed(() => emailConfigs.value.filter(c => c.is_active))

// 根据选中的配置过滤任务
const filteredTasks = computed(() => {
  if (selectedConfigId.value === 'unconfigured') {
    // 显示未配置的任务（配置失效的任务）
    return tasks.value.filter(t => !t.is_valid)
  } else if (selectedConfigId.value) {
    // 显示选中配置的任务
    return tasks.value.filter(t => t.zabbix_config_id === Number(selectedConfigId.value))
  }
  // 未选择配置时显示全部
  return tasks.value
})

const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

const getZabbixName = (configId: number) => {
  const config = zabbixConfigs.value.find(c => c.id === configId)
  return config ? config.name : `ID: ${configId}`
}

const getRowClassName = ({ row }: { row: TaskWithExtra }): string => {
  if (!row.is_valid) {
    return 'warning-row'
  }
  return ''
}

const getLogStatusType = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'running': return 'warning'
    default: return 'danger'
  }
}

const getLogStatusText = (status: string) => {
  switch (status) {
    case 'success': return '成功'
    case 'running': return '运行中'
    default: return '失败'
  }
}

const loadTasks = async () => {
  loading.value = true
  try {
    tasks.value = await getAllTasks()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadConfigs = async () => {
  try {
    zabbixConfigs.value = await getZabbixConfigs()
    emailConfigs.value = await getEmailConfigs()
  } catch (error) {
    console.error(error)
  }
}

const loadFilters = async (zabbixConfigId: number) => {
  if (!zabbixConfigId) {
    availableFilters.value = []
    return
  }

  filtersLoading.value = true
  try {
    availableFilters.value = await getFilters(zabbixConfigId)
  } catch (error) {
    console.error(error)
    availableFilters.value = []
  } finally {
    filtersLoading.value = false
  }
}

const handleZabbixChange = (configId: number) => {
  taskForm.monitor_filter_ids = []
  loadFilters(configId)
}

const showTaskDialog = (task?: TaskWithExtra) => {
  isEdit.value = !!task
  editTaskId.value = task?.id || null

  if (task) {
    taskForm.name = task.name
    taskForm.description = task.description || ''
    taskForm.cron_expression = task.cron_expression
    taskForm.zabbix_config_id = task.zabbix_config_id
    taskForm.email_config_id = task.email_config_id
    taskForm.monitor_filter_ids = task.monitor_filter_ids || task.filter_ids || []
    taskForm.recipients = task.recipients || []
    taskForm.time_range = task.time_range || 86400
    taskForm.email_subject = task.email_subject || ''
    taskForm.email_body = task.email_body || ''
    taskForm.subject_suffix_config_name = task.subject_suffix_config_name || false
    taskForm.subject_suffix_timestamp = task.subject_suffix_timestamp || false
    taskForm.email_include_device_overview = task.email_include_device_overview !== false
    taskForm.email_include_monitor_summary = task.email_include_monitor_summary !== false
    taskForm.email_include_alert_summary = task.email_include_alert_summary || false
    taskForm.include_device_overview = task.include_device_overview !== false
    taskForm.include_alert_data = task.include_alert_data || false
    taskForm.is_active = task.is_active
    loadFilters(task.zabbix_config_id)
  } else {
    taskForm.name = ''
    taskForm.description = ''
    taskForm.cron_expression = ''
    taskForm.zabbix_config_id = selectedConfigId.value ? Number(selectedConfigId.value) : null
    taskForm.email_config_id = null
    taskForm.monitor_filter_ids = []
    taskForm.recipients = []
    taskForm.time_range = 86400
    taskForm.email_subject = ''
    taskForm.email_body = ''
    taskForm.subject_suffix_config_name = false
    taskForm.subject_suffix_timestamp = false
    taskForm.email_include_device_overview = true
    taskForm.email_include_monitor_summary = true
    taskForm.email_include_alert_summary = false
    taskForm.include_device_overview = true
    taskForm.include_alert_data = false
    taskForm.is_active = true
    if (taskForm.zabbix_config_id) {
      loadFilters(taskForm.zabbix_config_id)
    } else {
      availableFilters.value = []
    }
  }

  taskDialogVisible.value = true
}

const handleSaveTask = async () => {
  if (!taskFormRef.value) return

  await taskFormRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const data = {
        name: taskForm.name,
        description: taskForm.description,
        cron_expression: taskForm.cron_expression,
        zabbix_config_id: taskForm.zabbix_config_id,
        email_config_id: taskForm.email_config_id,
        monitor_filter_ids: taskForm.monitor_filter_ids,
        recipients: taskForm.recipients,
        time_range: taskForm.time_range,
        email_subject: taskForm.email_subject,
        email_body: taskForm.email_body || null,
        subject_suffix_config_name: taskForm.subject_suffix_config_name,
        subject_suffix_timestamp: taskForm.subject_suffix_timestamp,
        email_include_device_overview: taskForm.email_include_device_overview,
        email_include_monitor_summary: taskForm.email_include_monitor_summary,
        email_include_alert_summary: taskForm.email_include_alert_summary,
        include_device_overview: taskForm.include_device_overview,
        include_alert_data: taskForm.include_alert_data,
        is_active: taskForm.is_active
      }

      if (isEdit.value && editTaskId.value) {
        await updateTask(editTaskId.value, data)
        ElMessage.success('保存成功')
      } else {
        await createTask(data)
        ElMessage.success('添加成功')
      }

      taskDialogVisible.value = false
      loadTasks()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

// 执行任务
const runTask = async (task: TaskWithExtra) => {
  try {
    await ElMessageBox.confirm(
      '确定要立即执行此任务吗？这将发送邮件给配置的收件人。',
      '确认执行',
      { type: 'warning' }
    )
  } catch {
    return
  }

  // 记录任务开始执行
  const startTime = Date.now()
  addRunningTask(task.id, startTime)

  // 显示执行中的通知
  runningNotificationInstance = ElNotification({
    title: '执行中',
    message: `正在生成报告并发送邮件: ${task.name}`,
    type: 'info',
    duration: 0,
    offset: 60
  })

  try {
    await runTaskApi(task.id)
    // 开始轮询任务状态
    pollTaskStatus(task.id, startTime)
  } catch (error: any) {
    removeRunningTask(task.id)
    runningNotificationInstance?.close()
    ElMessage.error('执行失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId: number, startTime: number) => {
  let attempts = 0
  const maxAttempts = 60

  const checkStatus = async () => {
    attempts++

    try {
      const logs = await getTaskLogs(taskId)

      if (logs && logs.length > 0) {
        const latestLog = logs[0]
        const logTime = new Date(latestLog.started_at || latestLog.start_time).getTime()

        // 检查是否是本次执行的任务
        if (logTime >= startTime - 5000) {
          if (latestLog.finished_at) {
            removeRunningTask(taskId)
            runningNotificationInstance?.close()

            if (latestLog.status === 'success') {
              ElMessage.success('任务执行成功！邮件已发送')
            } else {
              ElMessage.error(`任务执行失败: ${latestLog.message || '未知错误'}`)
            }
            loadTasks()
            return
          }
        }
      }

      // 继续检查
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 1000)
      } else {
        runningNotificationInstance?.close()
        ElMessage.warning('任务执行时间较长，已转为后台执行，请稍后查看日志')
        loadTasks()
      }
    } catch (error) {
      console.error('检查任务状态失败:', error)
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 1000)
      }
    }
  }

  setTimeout(checkStatus, 1000)
}

// 切换任务状态
const toggleTask = async (task: TaskWithExtra) => {
  try {
    await updateTask(task.id, { is_active: !task.is_active })
    ElMessage.success(task.is_active ? '任务已禁用' : '任务已启用')
    loadTasks()
  } catch (error: any) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 显示日志弹窗
const showLogsDialog = async (task: TaskWithExtra) => {
  currentTask.value = task
  logsDialogVisible.value = true
  await refreshLogs(task.id)
}

// 刷新日志
const refreshLogs = async (taskId: number) => {
  logsLoading.value = true
  try {
    const logs = await getTaskLogs(taskId)
    taskLogs.value = logs

    // 检查是否有运行中的任务
    const hasRunning = logs.some((log: TaskLogExtra) => log.status === 'running')

    if (hasRunning && !logRefreshTimer.value) {
      logRefreshTimer.value = setInterval(() => {
        if (currentTask.value) {
          refreshLogs(currentTask.value.id)
        }
      }, 2000)
    } else if (!hasRunning && logRefreshTimer.value) {
      clearInterval(logRefreshTimer.value)
      logRefreshTimer.value = null
    }
  } catch (error) {
    console.error(error)
  } finally {
    logsLoading.value = false
  }
}

// 下载日志文件
const downloadLog = (logId: number) => {
  downloadLogFile(logId)
}

// 删除任务
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？', '提示', { type: 'warning' })
    await deleteTask(id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch {
    // 用户取消
  }
}

// localStorage 操作
const addRunningTask = (taskId: number, startTime: number) => {
  const runningTasks = JSON.parse(localStorage.getItem('runningTasks') || '[]')
  runningTasks.push({ taskId, startTime })
  localStorage.setItem('runningTasks', JSON.stringify(runningTasks))
}

const removeRunningTask = (taskId: number) => {
  const runningTasks = JSON.parse(localStorage.getItem('runningTasks') || '[]')
  const filtered = runningTasks.filter((task: { taskId: number }) => task.taskId !== taskId)
  localStorage.setItem('runningTasks', JSON.stringify(filtered))
}

// 检查并恢复正在执行的任务
const checkRunningTasks = () => {
  const runningTasks = JSON.parse(localStorage.getItem('runningTasks') || '[]')
  const now = Date.now()

  runningTasks.forEach((task: { taskId: number; startTime: number }) => {
    // 只恢复5分钟内启动的任务
    if (now - task.startTime < 300000) {
      console.log('恢复任务轮询:', task.taskId)
      runningNotificationInstance = ElNotification({
        title: '执行中',
        message: '正在生成报告并发送邮件，请稍候...',
        type: 'info',
        duration: 0,
        offset: 60
      })
      pollTaskStatus(task.taskId, task.startTime)
    }
  })

  // 清理过期的任务记录
  const validTasks = runningTasks.filter((task: { taskId: number; startTime: number }) => now - task.startTime < 300000)
  localStorage.setItem('runningTasks', JSON.stringify(validTasks))
}

// 监听日志弹窗关闭
watch(logsDialogVisible, (val) => {
  if (!val && logRefreshTimer.value) {
    clearInterval(logRefreshTimer.value)
    logRefreshTimer.value = null
  }
})

onMounted(() => {
  loadTasks()
  loadConfigs()
  checkRunningTasks()
})

onUnmounted(() => {
  if (logRefreshTimer.value) {
    clearInterval(logRefreshTimer.value)
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

.cron-help {
  font-size: 13px;
}

.cron-help ul {
  padding-left: 20px;
  margin: 10px 0;
}

.cron-help li {
  margin-bottom: 5px;
}

.cron-help code {
  background: #f5f5f5;
  padding: 2px 5px;
  border-radius: 3px;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.ml-1 {
  margin-left: 5px;
}

.recipients-text {
  font-size: 13px;
  color: #606266;
}

.filter-box {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  max-height: 150px;
  overflow-y: auto;
  min-height: 60px;
}

.filter-box :deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.no-filters {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 15px 0;
}

.email-options,
.excel-options {
  margin-top: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.email-options :deep(.el-checkbox),
.excel-options :deep(.el-checkbox) {
  display: block;
  margin-bottom: 8px;
}

.email-options :deep(.el-checkbox:last-child),
.excel-options :deep(.el-checkbox:last-child) {
  margin-bottom: 0;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.action-buttons .el-button {
  padding: 5px 8px;
  flex-shrink: 0;
}

:deep(.warning-row) {
  background-color: #fdf6ec !important;
}

:deep(.warning-row:hover > td) {
  background-color: #faecd8 !important;
}

.mb-4 {
  margin-bottom: 1rem;
}
</style>
