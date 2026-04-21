<template>
  <div class="admin-users">
    <div class="page-header">
      <h2>
        <el-icon><UserFilled /></el-icon>
        用户管理
      </h2>
      <el-button type="primary" @click="showUserDialog()">
        <el-icon><Plus /></el-icon> 添加用户
      </el-button>
    </div>

    <el-card>
      <el-table :data="users" v-loading="loading" stripe :row-class-name="getRowClassName">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="用户名">
          <template #default="{ row }">
            {{ row.username }}
            <el-tag v-if="!row.is_active" type="warning" size="small" class="ml-1">待启用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'warning' : 'info'">
              {{ row.is_admin ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Zabbix权限">
          <template #default="{ row }">
            <template v-if="row.is_admin">
              <el-tag type="info">全部</el-tag>
            </template>
            <template v-else-if="row.allowed_zabbix_ids?.length">
              <el-tag v-for="id in row.allowed_zabbix_ids" :key="id" type="info" size="small" class="mr-1">
                {{ getZabbixName(id) }}
              </el-tag>
            </template>
            <template v-else>
              <span class="text-muted">无权限</span>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="showUserDialog(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '添加用户'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="留空则不修改密码" show-password />
          <div v-if="isEdit" class="form-tip">留空则不修改密码</div>
        </el-form-item>
        <el-form-item label="管理员">
          <el-checkbox v-model="form.is_admin">管理员（可访问所有Zabbix配置）</el-checkbox>
        </el-form-item>
        <el-form-item label="启用">
          <el-checkbox v-model="form.is_active">启用</el-checkbox>
        </el-form-item>
        <el-form-item v-if="!form.is_admin" label="Zabbix权限">
          <div class="zabbix-permissions">
            <el-checkbox-group v-model="form.allowed_zabbix_ids">
              <el-checkbox v-for="config in zabbixConfigs" :key="config.id" :label="config.id">
                {{ config.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div v-if="zabbixConfigs.length === 0" class="text-muted">暂无Zabbix配置</div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllUsers, createUser, updateUser, deleteUser } from '@/api/users'
import { getAllConfigs } from '@/api/zabbixConfig'
import type { User, ZabbixConfig } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const users = ref<User[]>([])
const zabbixConfigs = ref<ZabbixConfig[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editUserId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  email: '',
  password: '',
  is_admin: false,
  is_active: true,
  allowed_zabbix_ids: [] as number[]
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度3-50个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    {
      validator: (_rule, value, callback) => {
        if (!isEdit.value && !value) {
          callback(new Error('请输入密码'))
        } else if (value && value.length < 6) {
          callback(new Error('密码至少6个字符'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const getZabbixName = (id: number) => {
  const config = zabbixConfigs.value.find((c: ZabbixConfig) => c.id === id)
  return config?.name || `配置${id}`
}

const getRowClassName = ({ row }: { row: User }) => {
  if (!row.is_active) {
    return 'warning-row'
  }
  return ''
}

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await getAllUsers()
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

const showUserDialog = (user?: User) => {
  isEdit.value = !!user
  editUserId.value = user?.id || null

  if (user) {
    form.username = user.username
    form.email = user.email
    form.password = ''
    form.is_admin = user.is_admin
    form.is_active = user.is_active
    form.allowed_zabbix_ids = user.allowed_zabbix_ids || []
  } else {
    form.username = ''
    form.email = ''
    form.password = ''
    form.is_admin = false
    form.is_active = true
    form.allowed_zabbix_ids = []
  }

  dialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const data: any = {
        username: form.username,
        email: form.email,
        is_admin: form.is_admin,
        is_active: form.is_active
      }

      if (form.password) {
        data.password = form.password
      }

      if (!form.is_admin) {
        data.allowed_zabbix_ids = form.allowed_zabbix_ids
      }

      if (isEdit.value && editUserId.value) {
        await updateUser(editUserId.value, data)
        ElMessage.success('保存成功')
      } else {
        await createUser(data)
        ElMessage.success('添加成功')
      }

      dialogVisible.value = false
      loadUsers()
    } catch (error: any) {
      const detail = error.response?.data?.detail
      if (typeof detail === 'object') {
        ElMessage.error('保存失败: ' + JSON.stringify(detail))
      } else {
        ElMessage.error(detail || '保存失败')
      }
    } finally {
      saving.value = false
    }
  })
}

const toggleUserStatus = async (user: User) => {
  // 如果是禁用管理员，需要核验
  if (user.is_active && user.is_admin) {
    try {
      await ElMessageBox.confirm(
        '确定要禁用此管理员吗？如果这是唯一的管理员，禁用后将无法登录管理系统！',
        '警告',
        { type: 'warning', confirmButtonText: '确定禁用', cancelButtonText: '取消' }
      )
    } catch {
      return // 用户取消
    }
  }

  try {
    await updateUser(user.id, { is_active: !user.is_active })
    ElMessage.success(user.is_active ? '用户已禁用' : '用户已启用')
    loadUsers()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此用户吗？', '提示', { type: 'warning' })
    await deleteUser(id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadUsers()
  loadZabbixConfigs()
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

.zabbix-permissions {
  max-height: 150px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.form-tip {
  color: #909399;
  font-size: 12px;
}

.ml-1 {
  margin-left: 0.25rem;
}

.mr-1 {
  margin-right: 0.25rem;
}

.text-muted {
  color: #909399;
}

:deep(.warning-row) {
  background-color: #fdf6ec !important;
}

:deep(.warning-row:hover > td) {
  background-color: #faecd8 !important;
}
</style>
