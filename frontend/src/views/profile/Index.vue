<template>
  <div class="profile">
    <div class="page-header">
      <h2>
        <el-icon><User /></el-icon>
        个人信息
      </h2>
    </div>

    <el-card>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag :type="authStore.isAdmin ? 'warning' : 'info'">
            {{ authStore.isAdmin ? '管理员' : '普通用户' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="状态">
          <el-tag :type="authStore.user?.is_active ? 'success' : 'danger'">
            {{ authStore.user?.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-form-item>
        <el-form-item v-if="!authStore.isAdmin && authStore.user?.allowed_zabbix_ids?.length">
          <template #label>
            <span>Zabbix权限</span>
          </template>
          <div>
            <el-tag v-for="id in authStore.user?.allowed_zabbix_ids" :key="id" class="mr-1">
              {{ getZabbixName(id) }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleUpdateProfile" :loading="loading">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="mt-4">
      <template #header>
        <span>修改密码</span>
      </template>
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="当前密码" prop="current_password">
          <el-input v-model="passwordForm.current_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword" :loading="passwordLoading">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useZabbixConfigStore } from '@/stores/zabbixConfig'
import { updateProfile, changePassword } from '@/api/auth'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()
const zabbixConfigStore = useZabbixConfigStore()

const formRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const loading = ref(false)
const passwordLoading = ref(false)

const form = reactive({
  username: authStore.user?.username || '',
  email: authStore.user?.email || ''
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  current_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const getZabbixName = (id: number) => {
  const config = zabbixConfigStore.configs.find(c => c.id === id)
  return config?.name || `配置${id}`
}

const handleUpdateProfile = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await updateProfile({ email: form.email })
      ElMessage.success('保存成功')
      await authStore.fetchUser()
    } catch (error) {
      console.error(error)
    } finally {
      loading.value = false
    }
  })
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  const form = passwordFormRef.value
  await form.validate(async (valid) => {
    if (!valid) return

    passwordLoading.value = true
    try {
      await changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      })
      ElMessage.success('密码修改成功')
      form.resetFields()
    } catch (error) {
      console.error(error)
    } finally {
      passwordLoading.value = false
    }
  })
}

onMounted(() => {
  if (!zabbixConfigStore.configs.length) {
    zabbixConfigStore.fetchConfigs()
  }
})
</script>

<style scoped>
.page-header {
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

.mt-4 {
  margin-top: 1.5rem;
}

.mr-1 {
  margin-right: 0.5rem;
}
</style>
