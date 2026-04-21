<template>
  <div class="admin-system">
    <div class="page-header">
      <h2>
        <el-icon><Operation /></el-icon>
        系统设置
      </h2>
    </div>

    <el-card v-loading="loading">
      <el-form :model="form" label-width="150px">
        <el-form-item label="开放注册">
          <el-switch v-model="form.allow_registration" @change="handleSave" />
        </el-form-item>
        <el-form-item label="注册后需要启用">
          <el-switch v-model="form.require_activation" @change="handleSave" />
          <div class="form-tip">开启后，新注册用户需要管理员手动启用才能登录</div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getRegistrationSettings, updateRegistrationSettings } from '@/api/system'

const loading = ref(false)

const form = reactive({
  allow_registration: false,
  require_activation: false
})

const loadSettings = async () => {
  loading.value = true
  try {
    const settings = await getRegistrationSettings()
    form.allow_registration = settings.allowed
    form.require_activation = settings.require_activation
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  try {
    await updateRegistrationSettings({
      allow_registration: form.allow_registration,
      require_activation: form.require_activation
    })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  loadSettings()
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

.form-tip {
  color: #909399;
  font-size: 0.875rem;
  margin-top: 5px;
}
</style>
