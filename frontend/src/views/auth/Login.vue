<template>
  <div class="auth-page">
    <el-link href="https://github.com/Fate-Yoke/zabbix-report-center" target="_blank" class="github-corner">
      <svg viewBox="0 0 1024 1024" width="24" height="24" fill="currentColor">
        <path d="M512 42.666667A464.64 464.64 0 0 0 42.666667 502.186667 465.92 465.92 0 0 0 363.52 938.666667c23.466667 4.266667 32-9.813333 32-22.186667v-78.08c-130.56 27.733333-158.293333-61.44-158.293333-61.44a122.026667 122.026667 0 0 0-52.053334-67.413333c-42.666667-28.16 3.413333-27.733333 3.413334-27.733334a98.56 98.56 0 0 1 71.68 47.36 101.12 101.12 0 0 0 136.533333 37.546667 99.413333 99.413333 0 0 1 29.866667-61.44c-104.106667-11.52-213.333333-50.773333-213.333334-226.986666a176.64 176.64 0 0 1 47.36-124.16 161.28 161.28 0 0 1 4.693334-121.173334s39.68-12.373333 128 46.933334a449.706667 449.706667 0 0 1 234.666666 0c89.6-59.306667 128-46.933333 128-46.933334a161.28 161.28 0 0 1 4.693334 121.173334 176.64 176.64 0 0 1 47.36 124.16c0 176.64-109.226667 215.466667-213.333334 226.986666a106.666667 106.666667 0 0 1 30.293334 81.92v126.293334c0 12.373333 8.533333 26.88 32 22.186666A465.92 465.92 0 0 0 981.333333 502.186667 464.64 464.64 0 0 0 512 42.666667"/>
      </svg>
    </el-link>
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h3>
            <el-icon :size="32"><Lock /></el-icon>
            Zabbix Report Center
          </h3>
          <p>欢迎回来，请登录您的账户</p>
        </div>
        <div class="auth-body">
          <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon class="mb-4" />

          <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
            <input type="hidden" v-model="form.captcha_key" />

            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名/邮箱"
                :prefix-icon="User"
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
              <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="login-btn">
                <el-icon><Right /></el-icon> 登录
              </el-button>
            </el-form-item>
          </el-form>

          <div class="auth-footer">
            还没有账号？<router-link to="/register">立即注册</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock, Key, Right } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMsg = ref('')
const captchaUrl = ref('')
const captchaKey = ref('')

const form = ref({
  username: '',
  password: '',
  captcha_key: '',
  captcha_code: ''
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

const loadCaptcha = async () => {
  try {
    const res = await fetch('/api/auth/captcha')
    captchaKey.value = res.headers.get('X-Captcha-Key') || ''
    form.value.captcha_key = captchaKey.value
    const blob = await res.blob()
    captchaUrl.value = URL.createObjectURL(blob)
  } catch {
    console.error('加载验证码失败')
  }
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    errorMsg.value = ''

    try {
      const res = await authStore.login(
        form.value.username,
        form.value.password,
        form.value.captcha_key,
        form.value.captcha_code
      )

      if (res.success) {
        const redirect = route.query.redirect as string || '/'
        router.push(redirect)
      } else {
        errorMsg.value = res.detail || '登录失败'
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

onMounted(() => {
  loadCaptcha()
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
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
  max-width: 450px;
  padding: 1rem;
}

.auth-card {
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.auth-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.captcha-img:hover {
  border-color: #409eff;
}

.login-btn {
  width: 100%;
}

.auth-footer {
  text-align: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e4e7ed;
}

.auth-footer a {
  color: #667eea;
  font-weight: 600;
}

.auth-footer a:hover {
  color: #764ba2;
  text-decoration: underline;
}

.mb-4 {
  margin-bottom: 1rem;
}
</style>
