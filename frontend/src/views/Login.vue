<template>
  <div class="login-wrapper">
    <div class="login-bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    <div class="login-card">
      <div class="login-brand">
        <span class="brand-mark">A</span>
        <span class="brand-name font-display">AStock</span>
      </div>
      <p class="login-desc">AI多Agent驱动的智能A股分析平台</p>
      <div class="login-divider">
        <span class="divider-text font-sans">登录以继续</span>
      </div>
      <el-form :model="form" label-position="top" @keyup.enter="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" @click="handleLogin">登录</el-button>
        </el-form-item>
      </el-form>
      <div class="login-switch">
        <el-button text size="small" @click="isRegister = !isRegister">
          {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

interface LoginForm {
  username: string
  password: string
}

interface AuthResponse {
  access_token: string
  username: string
}

const form = ref<LoginForm>({ username: '', password: '' })
const loading = ref(false)
const isRegister = ref(false)

async function handleLogin() {
  const { username, password } = form.value
  if (!username || !password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  if (password.length < 4) {
    ElMessage.warning('密码至少4位')
    return
  }
  loading.value = true
  try {
    const endpoint = isRegister.value ? '/auth/register' : '/auth/login'
    const res = await request.post<AuthResponse>(endpoint, form.value)

    if (isRegister.value) {
      ElMessage.success('注册成功，请登录')
      isRegister.value = false
    } else {
      const data = res as unknown as AuthResponse
      localStorage.setItem('astock_token', data.access_token)
      localStorage.setItem('astock_user', data.username)
      ElMessage.success('登录成功')
      window.location.href = '/'
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--claude-bg);
  position: relative;
  overflow: hidden;
}

.login-bg-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}

.shape-1 {
  width: 400px;
  height: 400px;
  background: var(--claude-accent-light);
  top: -10%;
  left: -5%;
  animation: float1 20s ease-in-out infinite;
}

.shape-2 {
  width: 300px;
  height: 300px;
  background: var(--claude-blue-light);
  bottom: -10%;
  right: -5%;
  animation: float2 25s ease-in-out infinite;
}

.shape-3 {
  width: 200px;
  height: 200px;
  background: var(--claude-green-light);
  top: 50%;
  left: 60%;
  animation: float3 18s ease-in-out infinite;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(40px, 30px); }
}

@keyframes float2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-30px, -40px); }
}

@keyframes float3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-20px, 20px); }
}

.login-card {
  position: relative;
  z-index: 1;
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-radius: var(--radius-xl);
  padding: var(--space-10) var(--space-10);
  width: 420px;
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.3s ease both;
}

.login-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 8px;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--claude-accent);
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  font-family: var(--font-display);
  border-radius: var(--radius-sm);
  letter-spacing: -0.02em;
}

.brand-name {
  font-size: 26px;
  font-weight: 700;
  color: var(--claude-text);
  letter-spacing: -0.03em;
}

.login-desc {
  text-align: center;
  color: var(--claude-text-secondary);
  font-size: var(--text-sm);
  margin-bottom: var(--space-6);
  font-family: var(--font-body);
}

.login-divider {
  position: relative;
  text-align: center;
  margin-bottom: var(--space-6);
  border-top: 1px solid var(--claude-border);
}

.divider-text {
  position: relative;
  top: -10px;
  background: var(--claude-card);
  padding: 0 16px;
  font-size: var(--text-xs);
  color: var(--claude-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.login-switch {
  text-align: center;
  margin-top: var(--space-4);
}
</style>
