<template>
  <div class="admin-email">
    <div class="page-header">
      <h2>
        <el-icon><Message /></el-icon>
        邮件配置
      </h2>
      <el-button type="primary" @click="showConfigDialog()">
        <el-icon><Plus /></el-icon> 添加配置
      </el-button>
    </div>

    <el-card>
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="smtp_server" label="SMTP服务器" />
        <el-table-column prop="smtp_port" label="端口" width="80" />
        <el-table-column prop="mail_from" label="发件人" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="sendTestEmail(row.id)">测试</el-button>
            <el-button size="small" type="info" @click="showConfigDialog(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleConfigStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 配置编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑邮件配置' : '添加邮件配置'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="配置名称" prop="name">
              <el-input v-model="form.name" placeholder="默认邮件配置" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="SSL加密">
              <el-select v-model="form.use_ssl" style="width: 100%">
                <el-option label="是" :value="true" />
                <el-option label="否" :value="false" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="14">
            <el-form-item label="SMTP服务器" prop="smtp_server">
              <el-input v-model="form.smtp_server" placeholder="smtp.example.com" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="端口" prop="smtp_port">
              <el-input-number v-model="form.smtp_port" :min="1" :max="65535" style="width: 100%" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="smtp_user">
              <el-input v-model="form.smtp_user" placeholder="your@email.com" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" prop="smtp_pass">
              <el-input v-model="form.smtp_pass" type="password" placeholder="留空则不修改" show-password />
              <div v-if="isEdit" class="form-tip">留空则不修改</div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="发件人地址" prop="mail_from">
          <el-input v-model="form.mail_from" placeholder="sender@email.com" />
        </el-form-item>

        <el-form-item label="启用">
          <el-checkbox v-model="form.is_active">启用</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button v-if="isEdit" type="info" @click="handleTestEmail" :loading="testing">发送测试邮件</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllConfigs, getConfig, createConfig, updateConfig, deleteConfig, testEmail } from '@/api/emailConfig'
import type { EmailConfig } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const configs = ref<EmailConfig[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editConfigId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '默认邮件配置',
  smtp_server: '',
  smtp_port: 465,
  smtp_user: '',
  smtp_pass: '',
  use_ssl: true,
  mail_from: '',
  is_active: true
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  smtp_server: [{ required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }],
  smtp_port: [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  smtp_user: [{ required: true, message: '请输入SMTP用户名', trigger: 'blur' }],
  mail_from: [
    { required: true, message: '请输入发件人地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const loadConfigs = async () => {
  loading.value = true
  try {
    configs.value = await getAllConfigs()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const showConfigDialog = async (config?: EmailConfig) => {
  isEdit.value = !!config
  editConfigId.value = config?.id || null

  if (config) {
    const detail = await getConfig(config.id)
    form.name = detail.name
    form.smtp_server = detail.smtp_server
    form.smtp_port = detail.smtp_port
    form.smtp_user = detail.smtp_user
    form.smtp_pass = ''
    form.use_ssl = detail.use_ssl
    form.mail_from = detail.mail_from
    form.is_active = detail.is_active
  } else {
    form.name = '默认邮件配置'
    form.smtp_server = ''
    form.smtp_port = 465
    form.smtp_user = ''
    form.smtp_pass = ''
    form.use_ssl = true
    form.mail_from = ''
    form.is_active = true
  }

  dialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 新建时密码必填
    if (!isEdit.value && !form.smtp_pass) {
      ElMessage.error('请输入SMTP密码')
      return
    }

    saving.value = true
    try {
      const data: any = {
        name: form.name,
        smtp_server: form.smtp_server,
        smtp_port: form.smtp_port,
        smtp_user: form.smtp_user,
        use_ssl: form.use_ssl,
        mail_from: form.mail_from,
        is_active: form.is_active
      }

      if (form.smtp_pass) {
        data.smtp_pass = form.smtp_pass
      }

      if (isEdit.value && editConfigId.value) {
        await updateConfig(editConfigId.value, data)
        ElMessage.success('保存成功')
      } else {
        await createConfig(data)
        ElMessage.success('添加成功')
      }

      dialogVisible.value = false
      loadConfigs()
    } catch (error: any) {
      const detail = error.response?.data?.detail
      ElMessage.error(detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

const sendTestEmail = async (id: number) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入接收测试邮件的邮箱地址（留空则发送给发件人自己）', '发送测试邮件', {
      inputPattern: /^$|^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      inputErrorMessage: '请输入有效的邮箱地址'
    })

    testing.value = true
    const result = await testEmail(id, value || undefined)
    testing.value = false

    if (result.success) {
      ElMessage.success(result.message || '测试邮件发送成功')
    } else {
      ElMessage.error(result.message || '发送失败')
    }
  } catch {
    // 用户取消
    testing.value = false
  }
}

// 弹窗内发送测试邮件
const handleTestEmail = async () => {
  if (!editConfigId.value) {
    ElMessage.warning('请先保存配置后再发送测试邮件')
    return
  }
  await sendTestEmail(editConfigId.value)
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此配置吗？', '提示', { type: 'warning' })
    await deleteConfig(id)
    ElMessage.success('删除成功')
    loadConfigs()
  } catch {
    // 用户取消
  }
}

const toggleConfigStatus = async (config: EmailConfig) => {
  try {
    await updateConfig(config.id, { is_active: !config.is_active })
    ElMessage.success(config.is_active ? '配置已禁用' : '配置已启用')
    loadConfigs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

onMounted(() => {
  loadConfigs()
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

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}
</style>
