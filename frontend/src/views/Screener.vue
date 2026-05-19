<template>
  <div class="screener">
    <AIChat
      @apply-conditions="onAIApplyConditions"
      @view-stocks="onAIViewStocks"
      @daily="onAIDaily"
    />

    <ConditionBuilder />

    <div class="result-section">
      <div class="result-header">
        <div class="result-header-left">
          <span class="result-title">📊 筛选结果</span>
          <span class="result-count" v-if="screenerStore.results.length > 0">共 {{ screenerStore.results.length }} 只</span>
        </div>
        <div class="result-header-right">
          <div class="view-switcher">
            <span
              v-for="vm in viewModes"
              :key="vm.mode"
              class="view-btn"
              :class="{ active: screenerStore.viewMode === vm.mode, disabled: vm.disabled }"
              @click="!vm.disabled && screenerStore.setViewMode(vm.mode)"
            >{{ vm.icon }} {{ vm.label }}<sup v-if="vm.disabled" class="coming-soon">即将推出</sup></span>
          </div>
          <div class="result-actions">
            <el-button size="small" @click="runAIAnalysis" :loading="analyzing" class="action-btn ai-btn">
              🤖 AI解读
            </el-button>
            <el-button size="small" @click="exportCSV" :disabled="screenerStore.results.length === 0" class="action-btn">
              📥 导出CSV
            </el-button>
          </div>
        </div>
      </div>

      <ResultTable
        v-if="screenerStore.viewMode === 'table'"
        @go-stock="goToStock"
      />
      <ResultCards
        v-else-if="screenerStore.viewMode === 'cards'"
        @go-stock="goToStock"
      />
      <div v-else-if="screenerStore.viewMode === 'bubble'" class="view-placeholder">
        <el-empty description="气泡图视图开发中，敬请期待" :image-size="60" />
      </div>
      <div v-else-if="screenerStore.viewMode === 'heatmap'" class="view-placeholder">
        <el-empty description="热力图视图开发中，敬请期待" :image-size="60" />
      </div>

      <AIAnalysisPanel :analysis-data="analysisData" :has-results="screenerStore.results.length > 0" :analyzing="analyzing" @go-stock="goToStock" />
    </div>

    <el-dialog v-model="showAIDaily" title="📡 今日AI推荐" width="800px">
      <div v-if="screenerStore.aiDaily" class="ai-daily-content">
        <div v-for="rec in screenerStore.aiDaily.recommendations" :key="rec.title" class="ai-daily-item">
          <div class="ai-daily-title">{{ rec.title }}</div>
          <div class="ai-daily-desc">{{ rec.description }}</div>
          <div class="ai-daily-reason">{{ rec.reason }}</div>
          <div v-if="rec.stocks?.length" class="ai-daily-stocks">
            <el-tag
              v-for="s in rec.stocks.slice(0, 5)"
              :key="s.ts_code"
              size="small"
              style="margin: 2px 4px; cursor: pointer"
              @click="goToStock(s.ts_code)"
            >
              {{ s.name }}
            </el-tag>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无AI推荐" :image-size="60" />
      <template #footer>
        <el-button @click="showAIDaily = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useScreenerStore } from '@/stores/screenerStore'
import { screenerApi } from '@/api/modules/screener'
import { ElMessage } from 'element-plus'
import AIChat from '@/components/screener/AIChat.vue'
import ConditionBuilder from '@/components/screener/ConditionBuilder.vue'
import ResultTable from '@/components/screener/ResultTable.vue'
import ResultCards from '@/components/screener/ResultCards.vue'
import AIAnalysisPanel from '@/components/screener/AIAnalysisPanel.vue'
import type { ScreenerCondition } from '@/types/screener'

defineOptions({ name: 'Screener' })

const router = useRouter()
const screenerStore = useScreenerStore()

const analysisData = ref<any>(null)
const analyzing = ref(false)
const showAIDaily = ref(false)

const viewModes = [
  { mode: 'table' as const, icon: '📋', label: '表格', disabled: false },
  { mode: 'cards' as const, icon: '🃏', label: '卡片', disabled: false },
  { mode: 'bubble' as const, icon: '🫧', label: '气泡图', disabled: true },
  { mode: 'heatmap' as const, icon: '🗺️', label: '热力图', disabled: true },
]

function onAIApplyConditions(conditions: any[], industries: string[]) {
  const allConditions: ScreenerCondition[] = [...(conditions || [])]
  if (industries && industries.length > 0) {
    allConditions.push({ category: 'quote', field: 'industry', op: 'in_', values: industries })
  }
  if (allConditions.length > 0) {
    screenerStore.conditions = allConditions
    screenerStore.aiParsedConditions = conditions || []
    screenerStore.aiMatchedIndustries = industries || []
    screenerStore.executeScreener()
    ElMessage.success(`已应用 ${allConditions.length} 个筛选条件`)
  } else {
    ElMessage.info('没有条件可应用')
  }
}

function onAIViewStocks(stocks: any[]) {
  if (stocks && stocks.length > 0) {
    screenerStore.results = stocks
    ElMessage.success(`找到 ${stocks.length} 只股票`)
    runAIAnalysis()
  }
}

function onAIDaily() {
  showAIDaily.value = true
}

async function runAIAnalysis() {
  if (screenerStore.results.length === 0) {
    ElMessage.warning('请先执行筛选')
    return
  }
  analyzing.value = true
  try {
    const codes = screenerStore.results.slice(0, 20).map(r => r.ts_code)
    const data: any = await screenerApi.aiAnalyze(codes)
    analysisData.value = data
  } catch {
    ElMessage.error('AI分析失败')
  } finally {
    analyzing.value = false
  }
}

function goToStock(ts_code: string) {
  router.push({ path: '/stock', query: { code: ts_code } })
}

function exportCSV() {
  const results = screenerStore.results
  if (!results.length) return
  const headers = ['代码', '名称', '行业', '现价', '涨跌幅(%)', '换手率(%)', 'PE', 'ROE(%)']
  const rows = results.map((r: any) => [
    r.ts_code, r.name, r.industry || '', r.close?.toFixed(2) || '',
    r.pct_change?.toFixed(2) || '', r.turnover_rate || '',
    r.pe?.toFixed(1) || '', r.roe?.toFixed(1) || '',
  ])
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `选股结果_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success(`已导出 ${results.length} 条记录`)
}
</script>

<style scoped>
.result-section {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 10px;
}
.result-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.result-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--claude-text);
  font-family: var(--font-sans);
}
.result-count {
  font-size: 12px;
  color: var(--claude-text-secondary);
  font-family: var(--font-sans);
}
.result-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.view-switcher {
  display: flex;
  gap: 4px;
  background: var(--claude-bg);
  border-radius: var(--radius-sm);
  padding: 3px;
}
.view-btn {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-sans);
  cursor: pointer;
  color: var(--claude-text-secondary);
  transition: all var(--transition-fast);
}
.view-btn.active {
  background: var(--claude-accent);
  color: #fff;
}
.view-btn:hover:not(.active) {
  background: var(--claude-overlay);
}
.view-btn.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.view-btn.disabled:hover {
  background: transparent;
}
.coming-soon {
  font-size: 9px;
  margin-left: 2px;
  color: var(--claude-text-tertiary);
  font-weight: 400;
}
.result-actions {
  display: flex;
  gap: 6px;
}
.action-btn {
  font-family: var(--font-sans);
}
.ai-btn {
  color: var(--claude-accent) !important;
  border-color: var(--claude-accent) !important;
}
.ai-btn:hover {
  background: var(--claude-accent-light) !important;
}
.view-placeholder {
  padding: 40px 0;
}
.ai-daily-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.ai-daily-item {
  padding: 14px;
  background: var(--claude-bg);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--claude-accent);
}
.ai-daily-title {
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font-sans);
  margin-bottom: 6px;
}
.ai-daily-desc {
  font-size: 13px;
  color: var(--claude-text-secondary);
  margin-bottom: 4px;
}
.ai-daily-reason {
  font-size: 12px;
  color: var(--claude-text-tertiary);
  margin-bottom: 8px;
}
.ai-daily-stocks {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
