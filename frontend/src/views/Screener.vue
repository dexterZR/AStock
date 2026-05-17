<template>
  <div class="screener">
    <AIInput
      @parsed="onAIParsed"
      @picked="onAIPicked"
      @daily="onAIDaily"
    />

    <StrategyTemplates />

    <ConditionBuilder />

    <div class="ai-info-bar" v-if="screenerStore.aiExplanation || screenerStore.aiParsedConditions.length > 0 || screenerStore.aiMatchedIndustryGroups.length > 0">
      <div class="ai-info-left">
        <span class="ai-info-source">
          {{ screenerStore.aiSource === 'llm' ? '🤖 MiniMax AI' : '🔑 关键词匹配' }}
        </span>
        <span class="ai-info-explanation" v-if="screenerStore.aiExplanation">
          {{ screenerStore.aiExplanation }}
        </span>
      </div>
      <div class="ai-info-tags">
        <el-tag
          v-for="(ind, idx) in screenerStore.aiMatchedIndustryGroups"
          :key="'ind-' + idx"
          size="small"
          type="warning"
          closable
          @close="removeAIIndustryGroup(idx)"
          class="ai-tag"
        >
          🏭 {{ ind }}
        </el-tag>
        <el-tag
          v-for="(cond, idx) in screenerStore.aiParsedConditions"
          :key="'cond-' + idx"
          size="small"
          :type="getCondTagType(cond.category)"
          closable
          @close="removeAICondition(idx)"
          class="ai-tag"
        >
          {{ getCondLabel(cond) }}
        </el-tag>
        <el-button size="small" text type="primary" @click="applyAIConditions" class="ai-apply-btn">
          📋 应用到条件编辑器
        </el-button>
        <el-button size="small" text @click="screenerStore.clearAIState()" class="ai-clear-btn">
          ✕ 清除
        </el-button>
      </div>
    </div>

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
            <el-button size="small" @click="compareSelected" :disabled="selectedRows.length < 2" class="action-btn">
              ⚖️ 对比 ({{ selectedRows.length }})
            </el-button>
            <el-button size="small" @click="exportCSV" :disabled="screenerStore.results.length === 0" class="action-btn">
              📥 导出CSV
            </el-button>
          </div>
        </div>
      </div>

      <ResultTable
        v-if="screenerStore.viewMode === 'table'"
        @selection-change="onSelectionChange"
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

      <AIAnalysisPanel :analysis-data="analysisData" :has-results="screenerStore.results.length > 0" />
    </div>

    <el-dialog v-model="showCompare" title="⚖️ 股票对比" width="900px">
      <el-table :data="compareData" border size="small" v-loading="compareLoading">
        <el-table-column prop="label" label="指标" width="120" fixed />
        <el-table-column v-for="stock in compareStocks" :key="stock.ts_code" :label="stock.name">
          <template #default="scope">
            <span :style="getCompareStyle(scope.row, stock.ts_code)">{{ scope.row[stock.ts_code] || '--' }}</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showCompare = false">关闭</el-button>
      </template>
    </el-dialog>

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
import AIInput from '@/components/screener/AIInput.vue'
import StrategyTemplates from '@/components/screener/StrategyTemplates.vue'
import ConditionBuilder from '@/components/screener/ConditionBuilder.vue'
import ResultTable from '@/components/screener/ResultTable.vue'
import ResultCards from '@/components/screener/ResultCards.vue'
import AIAnalysisPanel from '@/components/screener/AIAnalysisPanel.vue'
import type { ScreenerCondition } from '@/types/screener'
import { CONDITION_OPTIONS } from '@/types/screener'

defineOptions({ name: 'Screener' })

const router = useRouter()
const screenerStore = useScreenerStore()

const analysisData = ref<any>(null)
const analyzing = ref(false)
const selectedRows = ref<any[]>([])
const showCompare = ref(false)
const compareLoading = ref(false)
const compareStocks = ref<any[]>([])
const compareData = ref<Array<{ label: string; [key: string]: any }>>([])
const showAIDaily = ref(false)

const viewModes = [
  { mode: 'table' as const, icon: '📋', label: '表格', disabled: false },
  { mode: 'cards' as const, icon: '🃏', label: '卡片', disabled: false },
  { mode: 'bubble' as const, icon: '🫧', label: '气泡图', disabled: true },
  { mode: 'heatmap' as const, icon: '🗺️', label: '热力图', disabled: true },
]

function onAIParsed(data: any) {
  const conds: ScreenerCondition[] = [...(data.conditions || [])]
  const industries: string[] = data.matched_industries || []
  if (industries.length > 0) {
    conds.push({ category: 'quote', field: 'industry', op: 'in_', values: industries })
  }
  screenerStore.conditions = conds
  screenerStore.executeScreener()
}

function onAIPicked(data: any) {
  if (data.stocks) {
    screenerStore.results = data.stocks
    ElMessage.success(`AI选出 ${data.stocks.length} 只股票`)
  }
}

function onAIDaily() {
  showAIDaily.value = true
}

function removeAIIndustryGroup(idx: number) {
  screenerStore.aiMatchedIndustryGroups.splice(idx, 1)
  screenerStore.aiMatchedIndustries = []
}

function removeAICondition(idx: number) {
  screenerStore.aiParsedConditions.splice(idx, 1)
}

function applyAIConditions() {
  const conds = [...screenerStore.aiParsedConditions]
  const industries = screenerStore.aiMatchedIndustries
  if (industries.length > 0) {
    conds.push({ category: 'quote', field: 'industry', op: 'in_', values: industries })
  }
  screenerStore.conditions = conds
  screenerStore.executeScreener()
}

function getCondTagType(category: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    technical: '', fundamental: 'success', pattern: 'info', capital: 'warning', quote: 'info',
  }
  return map[category] || 'info'
}

function getCondLabel(cond: ScreenerCondition): string {
  if (cond.field === 'industry') {
    const vals = cond.values || (Array.isArray(cond.value) ? cond.value : cond.value ? [cond.value] : [])
    return `🏭 ${vals.join('、')}`
  }
  const options = CONDITION_OPTIONS[cond.category as keyof typeof CONDITION_OPTIONS]
  if (options) {
    const found = options.find(o => o.field === cond.field)
    if (found) {
      let label = found.label
      if (cond.op === 'range' && cond.min != null && cond.max != null) {
        label += ` ${cond.min}~${cond.max}`
      } else if (cond.op === 'gt' && cond.value != null) {
        label += ` >${cond.value}`
      } else if (cond.op === 'lt' && cond.value != null) {
        label += ` <${cond.value}`
      } else if (cond.op === 'gte' && cond.value != null) {
        label += ` ≥${cond.value}`
      } else if (cond.op === 'eq' && cond.value === true) {
        label = '✓ ' + label
      }
      return label
    }
  }
  return `${cond.field} ${cond.op} ${cond.value ?? ''}`
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

function onSelectionChange(rows: any[]) {
  selectedRows.value = rows
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

async function compareSelected() {
  if (selectedRows.value.length < 2) {
    ElMessage.warning('请至少选择2只股票进行对比')
    return
  }
  showCompare.value = true
  compareLoading.value = true
  compareStocks.value = selectedRows.value.slice(0, 5)
  try {
    const codes = compareStocks.value.map(s => s.ts_code)
    const data: any = await screenerApi.aiAnalyze(codes)
    const results = data?.stocks || []
    const rows: Array<{ label: string; [key: string]: any }> = [
      { label: '综合评分' },
      { label: '技术面评分' },
      { label: '基本面评分' },
      { label: '催化剂评分' },
      { label: '操作建议' },
    ]
    for (const r of results) {
      const code = r.ts_code
      rows[0][code] = r.total_score + '分'
      rows[1][code] = r.technical?.score + '分'
      rows[2][code] = r.fundamental?.score + '分'
      rows[3][code] = r.catalyst?.score + '分'
      rows[4][code] = r.verdict?.action || '--'
    }
    compareData.value = rows
  } catch {
    ElMessage.error('对比分析失败')
  }
  compareLoading.value = false
}

function getCompareStyle(row: { label: string; [key: string]: any }, tsCode: string) {
  const val = row[tsCode]
  if (typeof val === 'string' && val.endsWith('%')) {
    const num = parseFloat(val)
    if (num > 0) return { color: 'var(--color-up)', fontWeight: 600 }
    if (num < 0) return { color: 'var(--color-down)', fontWeight: 600 }
  }
  return {}
}
</script>

<style scoped>
.ai-info-bar {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-left: 3px solid var(--claude-accent);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-info-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.ai-info-source {
  background: var(--claude-accent);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-sans);
  white-space: nowrap;
}
.ai-info-explanation {
  font-size: 13px;
  color: var(--claude-text);
  font-family: var(--font-sans);
}
.ai-info-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.ai-tag {
  font-family: var(--font-sans);
}
.ai-apply-btn {
  font-family: var(--font-sans);
  font-size: 12px;
}
.ai-clear-btn {
  font-family: var(--font-sans);
  font-size: 12px;
  color: var(--claude-text-tertiary) !important;
}
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
