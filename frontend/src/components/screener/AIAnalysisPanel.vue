<template>
  <div v-if="analyzing || analysisData || hasResults" class="ai-analysis">
    <el-divider />
    <template v-if="analyzing && !analysisData">
      <div class="analysis-loading">
        <el-icon class="loading-spin"><Loading /></el-icon>
        <span>AI 正在分析筛选结果…</span>
      </div>
    </template>
    <template v-else-if="analysisData">
      <div class="analysis-header">
        <span class="analysis-title">🤖 AI分析结果</span>
        <el-tag v-if="avgScore > 0" :type="avgScore >= 60 ? 'danger' : avgScore >= 40 ? 'warning' : 'success'">
          均分: {{ avgScore.toFixed(1) }}
        </el-tag>
      </div>
      <div v-if="analysisData.overview" class="analysis-overview">{{ analysisData.overview }}</div>
      <el-row :gutter="12">
        <el-col :span="8" v-for="item in analysisData.stocks?.slice(0, 6)" :key="item.ts_code">
          <div class="analysis-card" :style="{ borderLeftColor: item.verdict?.color || '#999', cursor: 'pointer' }" @click="goStock(item.ts_code)">
            <div class="analysis-card-header">
              <div>
                <strong>{{ item.name }}</strong>
                <span class="analysis-code stock-code">{{ item.ts_code }}</span>
              </div>
              <el-tag :color="item.verdict?.color" effect="dark" size="small">
                {{ item.total_score }}分
              </el-tag>
            </div>
            <div class="analysis-verdict" :style="{ color: item.verdict?.color }">
              {{ item.verdict?.action }}
            </div>
            <div class="analysis-dims">
              <div class="dim-row">
                <span class="dim-label">技术</span>
                <el-progress :percentage="item.technical?.score || 0" :color="getProgressColor(item.technical?.score)" :show-text="true" :stroke-width="6" />
              </div>
              <div class="dim-row">
                <span class="dim-label">基本</span>
                <el-progress :percentage="item.fundamental?.score || 0" :color="getProgressColor(item.fundamental?.score)" :show-text="true" :stroke-width="6" />
              </div>
              <div class="dim-row">
                <span class="dim-label">催化</span>
                <el-progress :percentage="item.catalyst?.score || 0" :color="getProgressColor(item.catalyst?.score)" :show-text="true" :stroke-width="6" />
              </div>
            </div>
            <div class="analysis-summary">{{ item.verdict?.summary }}</div>
          </div>
        </el-col>
      </el-row>
    </template>
    <div v-else class="ai-analysis-placeholder">
      <div class="placeholder-content">
        <span class="placeholder-icon">🤖</span>
        <span class="placeholder-text">点击上方「AI解读」按钮，获取筛选结果的智能分析</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const emit = defineEmits<{
  (e: 'go-stock', tsCode: string): void
}>()

const props = defineProps<{
  analysisData: any
  hasResults?: boolean
  analyzing?: boolean
}>()

const avgScore = computed(() => {
  if (!props.analysisData?.stocks?.length) return 0
  return props.analysisData.stocks.reduce((s: number, i: any) => s + (i.total_score || 0), 0) / props.analysisData.stocks.length
})

function getProgressColor(score?: number) {
  if (!score) return '#999'
  if (score >= 70) return '#dc2626'
  if (score >= 50) return '#d97706'
  return '#16a34a'
}

function goStock(tsCode: string) {
  emit('go-stock', tsCode)
}
</script>

<style scoped>
.ai-analysis {
  margin-top: 8px;
}
.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.analysis-title {
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font-sans);
}
.analysis-overview {
  font-size: 13px;
  color: var(--claude-text-secondary);
  margin-bottom: 16px;
  padding: 10px 14px;
  background: var(--claude-accent-light);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--claude-accent);
  font-family: var(--font-sans);
}
.analysis-card {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-left: 4px solid;
  border-radius: var(--radius-md);
  padding: 14px;
  margin-bottom: 12px;
  transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}
.analysis-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.analysis-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.analysis-card-header strong {
  font-family: var(--font-sans);
}
.analysis-code {
  font-size: 11px;
  margin-left: 6px;
}
.analysis-verdict {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 10px;
  font-family: var(--font-display), var(--font-sans);
}
.analysis-dims {
  margin-bottom: 8px;
}
.dim-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.dim-label {
  width: 30px;
  font-size: 11px;
  color: var(--claude-text-secondary);
  font-family: var(--font-sans);
}
.analysis-summary {
  font-size: 11px;
  color: var(--claude-text-secondary);
  border-top: 1px solid var(--claude-border);
  padding-top: 8px;
  font-family: var(--font-sans);
}
.ai-analysis-placeholder {
  padding: 20px 0;
}
.placeholder-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--claude-text-tertiary);
  font-size: 13px;
  font-family: var(--font-sans);
}
.placeholder-icon {
  font-size: 18px;
}
.analysis-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 0;
  color: var(--claude-accent);
  font-size: 14px;
  font-family: var(--font-sans);
}
.loading-spin {
  animation: spin 1s linear infinite;
  font-size: 18px;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
