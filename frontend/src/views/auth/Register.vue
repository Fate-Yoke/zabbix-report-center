<template>
  <div class="auth-page register-page">
    <el-link href="https://github.com/Fate-Yoke/zabbix-report-center" target="_blank" class="github-corner">
      <svg viewBox="0 0 1024 1024" width="24" height="24" fill="currentColor">
        <path d="M512 42.666667A464.64 464.64 0 0 0 42.666667 502.186667 465.92 465.92 0 0 0 363.52 938.666667c23.466667 4.266667 32-9.813333 32-22.186667v-78.08c-130.56 27.733333-158.293333-61.44-158.293333-61.44a122.026667 122.026667 0 0 0-52.053334-67.413333c-42.666667-28.16 3.413333-27.733333 3.413334-27.733334a98.56 98.56 0 0 1 71.68 47.36 101.12 101.12 0 0 0 136.533333 37.546667 99.413333 99.413333 0 0 1 29.866667-61.44c-104.106667-11.52-213.333333-50.773333-213.333334-226.986666a176.64 176.64 0 0 1 47.36-124.16 161.28 161.28 0 0 1 4.693334-121.173334s39.68-12.373333 128 46.933334a449.706667 449.706667 0 0 1 234.666666 0c89.6-59.306667 128-46.933333 128-46.933334a161.28 161.28 0 0 1 4.693334 121.173334 176.64 176.64 0 0 1 47.36 124.16c0 176.64-109.226667 215.466667-213.333334 226.986666a106.666667 106.666667 0 0 1 30.293334 81.92v126.293334c0 12.373333 8.533333 26.88 32 22.186666A465.92 465.92 0 0 0 981.333333 502.186667 464.64 464.64 0 0 0 512 42.666667"/>
      </svg>
    </el-link>
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h3>
            <el-icon :size="32"><UserFilled /></el-icon>
            创建新账户
          </h3>
          <p>加入 Zabbix Report Center</p>
        </div>
        <div class="auth-body">
          <div v-if="registrationClosed" class="registration-closed">
            <el-icon :size="48" color="#f56c6c"><CircleCloseFilled /></el-icon>
            <h4>系统已关闭注册功能</h4>
            <p>请联系管理员获取账户</p>
            <el-button type="primary" @click="router.push('/login')">
              返回登录
            </el-button>
          </div>

          <template v-else>
            <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon class="mb-4" />
            <el-alert v-if="successMsg" :title="successMsg" type="success" show-icon class="mb-4" />
            <el-alert v-if="requireActivation" type="info" show-icon class="mb-4">
              <template #title>注册后需要管理员启用账户才能登录</template>
            </el-alert>

            <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleRegister">
              <input type="hidden" v-model="form.captcha_key" />

              <el-form-item prop="username">
                <el-input
                  v-model="form.username"
                  placeholder="用户名"
                  :prefix-icon="User"
                  size="large"
                />
              </el-form-item>

              <el-form-item prop="email">
                <el-input
                  v-model="form.email"
                  placeholder="邮箱"
                  :prefix-icon="Message"
                  size="large"
                />
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="form.password"
                  type="password"
                  placeholder="密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>

              <el-form-item prop="confirm_password">
                <el-input
                  v-model="form.confirm_password"
                  type="password"
                  placeholder="确认密码"
                  :prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>

              <el-form-item prop="captcha_code">
                <div class="captcha-row">
                  <el-input
                    v-model="form.captcha_code"
                    placeholder="验证码"
                    :prefix-icon="Key"
                    size="large"
                    maxlength="4"
                  />
                  <img
                    :src="captchaUrl"
                    class="captcha-img"
                    @click="loadCaptcha"
                    title="点击刷新"
                    alt="验证码"
                  />
                </div>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" size="large" :loading="loading" @click="handleRegister" class="register-btn">
                  <el-icon><Plus /></el-icon> 注册
                </el-button>
              </el-form-item>
            </el-form>

            <div class="auth-footer">
              已有账号？<router-link to="/login">立即登录</router-link>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'
import { getRegistrationSettings } from '@/api/system'
import { useAuthStore } from '@/stores/auth'
import { User, Lock, Key, Plus, Message, UserFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const captchaUrl = ref('')
const requireActivation = ref(false)
const registrationClosed = ref(false)

const form = ref({
  username: '',
  email: '',
  password: '',
  confirm_password: '',
  captcha_key: '',
  captcha_code: ''
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== form.value.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

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
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  captcha_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

const loadCaptcha = async () => {
  try {
    const res = await fetch('/api/auth/captcha')
    form.value.captcha_key = res.headers.get('X-Captcha-Key') || ''
    const blob = await res.blob()
    captchaUrl.value = URL.createObjectURL(blob)
  } catch {
    console.error('加载验证码失败')
  }
}

const checkRegistration = async () => {
  try {
    const settings = await getRegistrationSettings()
    if (!settings.allowed) {
      registrationClosed.value = true
      return false
    }
    requireActivation.value = settings.require_activation
    return true
  } catch {
    return true
  }
}

const handleRegister = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    errorMsg.value = ''
    successMsg.value = ''

    try {
      const res = await register({
        username: form.value.username,
        email: form.value.email,
        password: form.value.password,
        captcha_key: form.value.captcha_key,
        captcha_code: form.value.captcha_code
      })

      if (res.success) {
        if (res.require_activation) {
          successMsg.value = '注册成功！请等待管理员启用账户后再登录。'
          setTimeout(() => {
            router.push('/login')
          }, 3000)
        } else {
          // 自动登录
          if (res.token && res.user) {
            localStorage.setItem('token', res.token)
            authStore.user = res.user
            authStore.token = res.token
            router.push('/')
          } else {
            router.push('/login')
          }
        }
      } else {
        errorMsg.value = res.detail || '注册失败'
        loadCaptcha()
      }
    } catch (error: any) {
      errorMsg.value = error.response?.data?.detail || '网络错误，请重试'
      loadCaptcha()
    } finally {
      loading.value = false
    }
  })
}

onMounted(async () => {
  const allowed = await checkRegistration()
  if (allowed) {
    loadCaptcha()
  }
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.register-page {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.register-page .auth-header {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.register-page .auth-footer a {
  color: #f093fb;
}

.register-page .auth-footer a:hover {
  color: #f5576c;
}

.github-corner {
  position: absolute;
  top: 1rem;
  right: 1rem;
  color: white;
  opacity: 0.8;
}

.auth-container {
  width: 100%;
  max-width: 500px;
  padding: 1rem;
}

.auth-card {
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.auth-header {
  padding: 2.5rem 2rem;
  text-align: center;
  color: white;
}

.auth-header h3 {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.auth-header p {
  margin: 0.5rem 0 0;
  opacity: 0.9;
}

.auth-body {
  padding: 2.5rem 2rem;
}

.captcha-row {
  display: flex;
  gap: 1rem;
  width: 100%;
}

.captcha-img {
  height: 40px;
  width: 120px;
  border-radius: 0.5rem;
  cursor: pointer;
  object-fit: contain;
  border: 2px solid #dcdfe6;
}

.register-btn {
  width: 100%;
}

.auth-footer {
  text-align: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e4e7ed;
}

.auth-footer a {
  font-weight: 600;
}

.auth-footer a:hover {
  text-decoration: underline;
}

.mb-4 {
  margin-bottom: 1rem;
}

.registration-closed {
  text-align: center;
  padding: 2rem 0;
}

.registration-closed h4 {
  margin: 1rem 0 0.5rem;
  font-size: 1.25rem;
  color: #303133;
}

.registration-closed p {
  color: #909399;
  margin-bottom: 1.5rem;
}
</style>
