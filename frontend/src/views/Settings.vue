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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const isDark = ref(false)
const enableSSE = ref(true)
const refreshInterval = ref(3)

onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark')
  const saved = localStorage.getItem('astock_settings')
  if (saved) {
    try {
      const s = JSON.parse(saved)
      enableSSE.value = s.enableSSE ?? true
      refreshInterval.value = s.refreshInterval ?? 3
    } catch {}
  }
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
</script>

<style scoped>
.settings { max-width: 600px; font-family: var(--font-sans); }
.unit { margin-left: 8px; color: var(--claude-text-secondary); }
</style>
