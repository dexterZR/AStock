<template>
  <div class="settings">
    <el-card>
      <template #header><span>系统设置</span></template>
      <el-form label-width="140px">
        <el-form-item label="暗色主题">
          <el-switch v-model="isDark" active-text="开启" inactive-text="关闭" @change="onThemeChange" />
        </el-form-item>
        <el-form-item label="实时推送">
          <el-switch v-model="enableSSE" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item label="数据刷新间隔">
          <el-input-number v-model="refreshInterval" :min="3" :max="60" />
          <span class="unit">秒</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="clearCache">清除缓存</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="llm-card">
      <template #header>
        <div class="llm-card-header">
          <span>LLM 配置</span>
          <span v-if="llmConnected" class="llm-status llm-status--connected">● 已连接</span>
          <span v-else-if="llmConfig.name" class="llm-status llm-status--disconnected">● 未连接</span>
          <span v-else class="llm-status llm-status--empty">● 未配置</span>
        </div>
      </template>
      <el-form label-width="140px">
        <el-form-item label="配置名称">
          <el-input v-model="llmConfig.name" placeholder="如：我的 DeepSeek" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="llmConfig.base_url" placeholder="如：https://api.deepseek.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="llmConfig.api_key" placeholder="输入 API Key" show-password />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="llmConfig.model" placeholder="如：deepseek-chat" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveLLMConfig">保存配置</el-button>
          <el-button @click="testLLMConnection" :loading="testing">测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { llmConfigApi } from '@/api/modules/llmConfig'
import type { LLMConfigData } from '@/api/modules/llmConfig'

const isDark = ref(false)
const enableSSE = ref(true)
const refreshInterval = ref(3)

const llmConfig = ref<LLMConfigData>({
  name: '',
  base_url: '',
  api_key: '',
  model: '',
})
const llmConnected = ref(false)
const testing = ref(false)

onMounted(async () => {
  isDark.value = document.documentElement.classList.contains('dark')
  const saved = localStorage.getItem('astock_settings')
  if (saved) {
    try {
      const s = JSON.parse(saved)
      enableSSE.value = s.enableSSE ?? true
      refreshInterval.value = s.refreshInterval ?? 3
    } catch {}
  }
  await loadLLMConfig()
})

function onThemeChange(val: boolean) {
  const root = document.documentElement
  if (val) {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
  localStorage.setItem('astock_theme', val ? 'dark' : 'light')
}

function saveSettings() {
  localStorage.setItem('astock_settings', JSON.stringify({
    isDark: isDark.value,
    enableSSE: enableSSE.value,
    refreshInterval: refreshInterval.value,
  }))
  ElMessage.success('设置已保存')
}

function clearCache() {
  ElMessageBox.confirm('确定要清除所有缓存数据吗？此操作不可撤销。', '确认清除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    localStorage.removeItem('astock_settings')
    localStorage.removeItem('astock_watchlist')
    ElMessage.success('缓存已清除')
  }).catch(() => {})
}

async function loadLLMConfig() {
  try {
    const data = await llmConfigApi.getConfig()
    if (data) {
      llmConfig.value = {
        name: data.name || '',
        base_url: data.base_url || '',
        api_key: data.api_key || '',
        model: data.model || '',
      }
      llmConnected.value = !!(data.api_key && data.base_url && data.model)
    }
  } catch {}
}

async function saveLLMConfig() {
  if (!llmConfig.value.base_url || !llmConfig.value.model) {
    ElMessage.warning('请填写 Base URL 和模型名称')
    return
  }
  try {
    await ElMessageBox.confirm('确认保存 LLM 配置？', '保存确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await llmConfigApi.saveConfig(llmConfig.value)
    ElMessage.success('LLM 配置已保存')
    llmConnected.value = !!(llmConfig.value.api_key && llmConfig.value.base_url && llmConfig.value.model)
  } catch {
    ElMessage.error('保存 LLM 配置失败')
  }
}

async function testLLMConnection() {
  if (!llmConfig.value.base_url || !llmConfig.value.model) {
    ElMessage.warning('请先填写并保存 Base URL 和模型名称')
    return
  }
  testing.value = true
  try {
    const result = await llmConfigApi.testConnection()
    if (result.success) {
      ElMessage.success(result.message || '连接成功')
      llmConnected.value = true
    } else {
      ElMessage.error(result.message || '连接失败')
      llmConnected.value = false
    }
  } catch {
    ElMessage.error('测试连接失败')
    llmConnected.value = false
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.settings { max-width: 600px; font-family: var(--font-sans); }
.unit { margin-left: 8px; color: var(--claude-text-secondary); }
.llm-card { margin-top: 16px; }
.llm-card-header { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.llm-status { font-size: 12px; font-family: var(--font-sans); }
.llm-status--connected { color: var(--claude-green, #4caf50); }
.llm-status--disconnected { color: var(--claude-red, #f44336); }
.llm-status--empty { color: var(--claude-text-secondary, #999); }
</style>
