<template>
  <div class="admin-zabbix">
    <div class="page-header">
      <h2>
        <el-icon><Setting /></el-icon>
        Zabbix配置
      </h2>
      <el-button type="primary" @click="showConfigDialog()">
        <el-icon><Plus /></el-icon> 添加配置
      </el-button>
    </div>

    <el-card>
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="url" label="URL" show-overflow-tooltip />
        <el-table-column label="认证方式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.auth_type === 'token' ? 'primary' : 'info'">
              {{ row.auth_type === 'token' ? 'Token' : '账号密码' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="testConnection(row.id)">测试</el-button>
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑Zabbix配置' : '添加Zabbix配置'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="如：生产环境Zabbix" />
        </el-form-item>
        <el-form-item label="API地址" prop="url">
          <el-input v-model="form.url" placeholder="http://zabbix-server/api_jsonrpc.php" />
        </el-form-item>
        <el-form-item label="认证方式" prop="auth_type">
          <el-select v-model="form.auth_type" style="width: 100%">
            <el-option label="Token认证" value="token" />
            <el-option label="账号密码认证" value="password" />
          </el-select>
        </el-form-item>

        <!-- Token认证 -->
        <template v-if="form.auth_type === 'token'">
          <el-form-item label="API Token" prop="token">
            <el-input v-model="form.token" placeholder="输入Zabbix API Token" />
            <div v-if="isEdit" class="form-tip">留空则不修改</div>
          </el-form-item>
        </template>

        <!-- 账号密码认证 -->
        <template v-else>
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="Zabbix用户名" />
            <div v-if="isEdit" class="form-tip">留空则不修改</div>
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="Zabbix密码" show-password />
            <div v-if="isEdit" class="form-tip">留空则不修改</div>
          </el-form-item>
        </template>

        <el-form-item label="启用">
          <el-checkbox v-model="form.is_active">启用</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="info" @click="handleTest" :loading="testing">测试连接</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllConfigs, getConfig, createConfig, updateConfig, deleteConfig, testConnection as testConnectionApi } from '@/api/zabbixConfig'
import type { ZabbixConfig } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const configs = ref<ZabbixConfig[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editConfigId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  url: '',
  auth_type: 'token' as 'token' | 'password',
  token: '',
  username: '',
  password: '',
  is_active: true
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入Zabbix API地址', trigger: 'blur' }]
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

const showConfigDialog = async (config?: ZabbixConfig) => {
  isEdit.value = !!config
  editConfigId.value = config?.id || null

  if (config) {
    const detail = await getConfig(config.id)
    form.name = detail.name
    form.url = detail.url
    form.auth_type = detail.auth_type as 'token' | 'password'
    form.token = ''
    form.username = detail.username || ''
    form.password = ''
    form.is_active = detail.is_active
  } else {
    form.name = ''
    form.url = ''
    form.auth_type = 'token'
    form.token = ''
    form.username = ''
    form.password = ''
    form.is_active = true
  }

  dialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 额外验证
    if (form.auth_type === 'token' && !isEdit.value && !form.token) {
      ElMessage.error('请输入API Token')
      return
    }
    if (form.auth_type === 'password') {
      if (!isEdit.value && !form.username) {
        ElMessage.error('请输入用户名')
        return
      }
      if (!isEdit.value && !form.password) {
        ElMessage.error('请输入密码')
        return
      }
    }

    saving.value = true
    try {
      const data: any = {
        name: form.name,
        url: form.url,
        auth_type: form.auth_type,
        is_active: form.is_active
      }

      if (form.auth_type === 'token' && form.token) {
        data.token = form.token
      } else if (form.auth_type === 'password') {
        if (form.username) data.username = form.username
        if (form.password) data.password = form.password
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

const handleTest = async () => {
  if (!editConfigId.value) {
    ElMessage.warning('请先保存配置后再测试')
    return
  }

  testing.value = true
  try {
    const result = await testConnectionApi(editConfigId.value)
    if (result.success) {
      ElMessage.success('连接成功！Zabbix版本: ' + result.version)
    } else {
      ElMessage.error('连接失败: ' + result.error)
    }
  } catch (error) {
    console.error(error)
  } finally {
    testing.value = false
  }
}

const toggleConfigStatus = async (config: ZabbixConfig) => {
  try {
    await updateConfig(config.id, { is_active: !config.is_active })
    ElMessage.success(config.is_active ? '配置已禁用' : '配置已启用')
    loadConfigs()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const testConnection = async (id: number) => {
  try {
    const result = await testConnectionApi(id)
    if (result.success) {
      ElMessage.success('连接成功！Zabbix版本: ' + result.version)
    } else {
      ElMessage.error('连接失败: ' + result.error)
    }
  } catch (error) {
    console.error(error)
  }
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
