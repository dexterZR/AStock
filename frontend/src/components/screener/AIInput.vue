<template>
  <div class="ai-input-section">
    <div class="ai-header">
      <span class="ai-badge">AI</span>
      <span class="ai-title">智能选股</span>
    </div>
    <div class="ai-input-row">
      <el-input
        v-model="query"
        placeholder="描述你想找什么样的股票，例如「近期放量突破的低价股」…"
        size="large"
        @keyup.enter="handlePick"
        clearable
        class="ai-text-input"
      >
        <template #prefix>
          <span style="font-size:16px">💬</span>
        </template>
      </el-input>
    </div>
    <div class="ai-actions">
      <el-button size="small" @click="handlePick" :loading="picking" class="ai-action-btn ai-pick-btn">
        🎯 AI帮我选
      </el-button>
      <el-button size="small" @click="handleParse" class="ai-action-btn ai-parse-btn">
        🔍 解析条件
      </el-button>
      <el-button size="small" @click="handleDaily" class="ai-action-btn ai-daily-btn">
        📡 今日AI推荐
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { screenerApi } from '@/api/modules/screener'
import { useScreenerStore } from '@/stores/screenerStore'
import { ElMessage } from 'element-plus'

const emit = defineEmits<{
  (e: 'parsed', data: any): void
  (e: 'picked', data: any): void
  (e: 'daily', data: any): void
}>()

const screenerStore = useScreenerStore()
const query = ref('')
const picking = ref(false)

async function handleParse() {
  if (!query.value.trim()) return
  try {
    const data: any = await screenerApi.aiParse(query.value)
    screenerStore.aiExplanation = data.explanation || ''
    screenerStore.aiSource = data.source || 'keyword'
    screenerStore.aiParsedConditions = data.conditions || []
    screenerStore.aiMatchedIndustries = data.matched_industries || []
    screenerStore.aiMatchedIndustryGroups = data.matched_industry_groups || []
    emit('parsed', data)
    const kwCount = data.matched_keywords?.length || 0
    const indCount = data.matched_industries?.length || 0
    const parts: string[] = []
    if (kwCount) parts.push(`${kwCount} 个关键词`)
    if (indCount) parts.push(`${indCount} 个行业`)
    ElMessage.success(parts.length ? `识别到 ${parts.join('、')}` : '未识别到条件')
  } catch {
    ElMessage.error('AI解析失败')
  }
}

async function handlePick() {
  if (!query.value.trim()) {
    ElMessage.warning('请先输入选股描述')
    return
  }
  picking.value = true
  try {
    const data: any = await screenerApi.aiPick(query.value)
    screenerStore.aiExplanation = data.explanation || ''
    screenerStore.aiSource = data.source || 'keyword'
    screenerStore.aiParsedConditions = data.conditions || []
    screenerStore.aiMatchedIndustries = data.matched_industries || []
    screenerStore.aiMatchedIndustryGroups = data.matched_industry_groups || []
    if (data.stocks && data.stocks.length > 0) {
      emit('picked', data)
      const sourceLabel = data.source === 'llm' ? '🤖 MiniMax AI' : '🔑 关键词'
      const msg = data.explanation
        ? `${sourceLabel}：${data.explanation}，找到 ${data.stocks.length} 只`
        : `找到 ${data.stocks.length} 只匹配股票`
      ElMessage.success(msg)
    } else {
      const keywords = data.matched_keywords || []
      if (keywords.length > 0) {
        ElMessage.info(`未找到匹配股票，已识别关键词：${keywords.join('、')}`)
      } else {
        ElMessage.info('未找到匹配股票，请尝试其他描述')
      }
      emit('parsed', data)
    }
  } catch {
    ElMessage.error('AI选股失败')
  } finally {
    picking.value = false
  }
}

async function handleDaily() {
  try {
    await screenerStore.loadAIDaily()
    emit('daily', screenerStore.aiDaily)
  } catch {
    ElMessage.error('获取AI推荐失败')
  }
}
</script>

<style scoped>
.ai-input-section {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-left: 3px solid var(--claude-accent);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  margin-bottom: 16px;
}
.ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.ai-badge {
  background: var(--claude-accent);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-sans);
}
.ai-title {
  color: var(--claude-accent);
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-sans);
}
.ai-input-row {
  margin-bottom: 10px;
}
.ai-text-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
}
.ai-actions {
  display: flex;
  gap: 8px;
}
.ai-action-btn {
  font-family: var(--font-sans);
}
.ai-pick-btn {
  color: var(--claude-accent) !important;
  border-color: var(--claude-accent) !important;
}
.ai-pick-btn:hover {
  background: var(--claude-accent-light) !important;
}
.ai-parse-btn {
  color: var(--claude-green) !important;
  border-color: var(--claude-green) !important;
}
.ai-parse-btn:hover {
  background: var(--claude-green-light) !important;
}
.ai-daily-btn {
  color: var(--claude-blue) !important;
  border-color: var(--claude-blue) !important;
}
.ai-daily-btn:hover {
  background: var(--claude-blue-light) !important;
}
</style>
