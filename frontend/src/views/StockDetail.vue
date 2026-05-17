<template>
  <div class="stock-detail">
    <!-- 搜索区 -->
    <div v-if="!currentStock" class="stock-finder" v-loading="loading">
      <div class="finder-box">
        <h3>{{ isIndex ? '📊 大盘指数' : '📈 个股行情' }}</h3>
        <p class="finder-desc">{{ isIndex ? '查看大盘指数K线走势' : '输入代码或名称查看详情' }}</p>
        <el-autocomplete
          v-model="finderKeyword"
          :fetch-suggestions="handleFinderSearch"
          :trigger-on-focus="false"
          placeholder="如 600519 茅台"
          style="width: 360px"
          @select="handleFinderSelect"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
          <template #default="{ item }">
            <span class="ac-code">{{ item.value }}</span>
            <span class="ac-name">{{ item.name }}</span>
          </template>
        </el-autocomplete>
        <div class="finder-quick">
          <span class="quick-label">热门：</span>
          <el-button v-for="s in quickStocks" :key="s.code" size="small" text @click="quickOpen(s.code)">{{ s.name }}</el-button>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div v-else v-loading="loading">
      <!-- 头部 -->
      <div class="detail-header">
        <div class="hd-left">
          <h2>{{ currentStock.name }}<span class="code stock-code">{{ currentStock.ts_code }}</span></h2>
          <div class="hd-tags">
            <el-tag size="small" type="info">{{ currentStock.industry || '--' }}</el-tag>
            <el-tag size="small" type="info">{{ currentStock.market || '--' }}</el-tag>
            <el-tag size="small" type="success" v-if="relatedData.current_sector" style="cursor:pointer">
              {{ relatedData.current_sector }}
            </el-tag>
          </div>
        </div>
        <div class="hd-right" v-if="latestPrice">
          <div class="hd-price price" :class="latestPrice.pct_change >= 0 ? 'up' : 'down'">
            {{ latestPrice.price?.toFixed(2) ?? latestPrice.close?.toFixed(2) }}
          </div>
          <div class="hd-change change" :class="latestPrice.pct_change >= 0 ? 'up' : 'down'">
            {{ latestPrice.pct_change >= 0 ? '+' : '' }}{{ latestPrice.pct_change?.toFixed(2) }}%
          </div>
          <div class="hd-change-amt change" :class="latestPrice.pct_change >= 0 ? 'up' : 'down'">
            {{ latestPrice.pre_close_price ? ((latestPrice.price ?? latestPrice.close) - latestPrice.pre_close_price).toFixed(2) : '--' }}
          </div>
          <el-button size="small" style="margin-top:8px" @click="showResearch = true" v-if="!isIndex">🔬 深度研究</el-button>
        </div>
      </div>

      <!-- K 线图 -->
      <el-card class="kline-card">
        <template #header>
          <div class="card-hd">
            <span>📊 K线图</span>
            <div class="kline-tabs">
              <el-button size="small" :type="klinePeriod === '30' ? 'primary' : ''" @click="changeKlinePeriod('30')">30天</el-button>
              <el-button size="small" :type="klinePeriod === '60' ? 'primary' : ''" @click="changeKlinePeriod('60')">60天</el-button>
              <el-button size="small" :type="klinePeriod === '120' ? 'primary' : ''" @click="changeKlinePeriod('120')">120天</el-button>
            </div>
          </div>
        </template>
        <KlineChart
          :data="chartData"
          :ma-data="maData"
          :volume-data="volumeData"
        />
      </el-card>

      <el-row :gutter="12" style="margin-top:16px;margin-bottom:16px">
        <el-col :span="4" v-for="m in metrics" :key="m.label">
          <div class="metric-card">
            <div class="met-label">{{ m.label }}</div>
            <div class="met-value price" :class="m.color">{{ m.value }}</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" v-if="!isIndex">
        <!-- 左栏：AI分析 + 同板块股票 -->
        <el-col :span="14">
          <!-- AI分析卡片 - 增强版 -->
          <el-card v-if="analysis" class="ai-card">
            <template #header><span>🤖 AI多Agent分析</span></template>
            <div v-if="analysis.data_insufficient" class="insufficient-tip">
              <el-empty :image-size="60" description="数据不足，无法进行AI分析">
                <template #description>
                  <p>该股票K线数据不足，暂时无法进行有效的AI分析</p>
                  <p style="color:var(--claude-text-tertiary);font-size:12px">{{ analysis.verdict?.summary }}</p>
                </template>
              </el-empty>
            </div>
            <template v-else>
            <div class="score-row">
              <div class="score-main">
                <div class="score-num" :style="{ color: analysis.verdict?.color }">{{ analysis.total_score }}</div>
                <div class="score-label">/ 100 · {{ analysis.verdict?.action }}</div>
              </div>
              <div class="score-summary">{{ analysis.verdict?.summary }}</div>
            </div>

            <!-- 关键信号 -->
            <div class="signals-box" v-if="analysis.key_signals?.length">
              <div class="signals-title">📡 关键信号</div>
              <div class="signals-list">
                <div v-for="(signal,i) in analysis.key_signals.slice(0,4)" :key="i" class="signal-item" :class="signal.type">
                  <div class="signal-name">{{ signal.name }}</div>
                  <div class="signal-desc">{{ signal.description }}</div>
                </div>
              </div>
            </div>

            <div style="margin-top:12px">
              <div v-for="dim in ['technical','fundamental','catalyst']" :key="dim" class="dim-bar">
                <span class="dim-name">{{ analysis[dim]?.dimension }}</span>
                <el-progress :percentage="analysis[dim]?.score" :color="dimColor(analysis[dim]?.score)" :stroke-width="8" style="flex:1;margin:0 12px" />
                <span class="dim-score">{{ analysis[dim]?.score }}分</span>
              </div>
            </div>

            <el-divider style="margin:12px 0" />

            <div class="bb-analysis">
              <div class="bb-title">🔍 多空对比</div>
              <div class="bb-grid">
                <div class="bb-col bull">
                  <div class="bb-col-title">看多理由</div>
                  <div v-if="!analysis.bull_bear_analysis?.bullish?.length" class="bb-empty">暂无</div>
                  <div v-else>
                    <div v-for="(r,i) in analysis.bull_bear_analysis.bullish.slice(0,4)" :key="i" class="bb-reason">
                      <span class="bb-dot">•</span>
                      <span class="bb-text">{{ r }}</span>
                    </div>
                  </div>
                </div>
                <div class="bb-col bear">
                  <div class="bb-col-title">看空理由</div>
                  <div v-if="!analysis.bull_bear_analysis?.bearish?.length" class="bb-empty">暂无</div>
                  <div v-else>
                    <div v-for="(r,i) in analysis.bull_bear_analysis.bearish.slice(0,4)" :key="i" class="bb-reason">
                      <span class="bb-dot">•</span>
                      <span class="bb-text">{{ r }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <el-divider style="margin:12px 0" />

            <div class="dim-details" v-if="analysis.technical?.details?.length">
              <div class="dim-d-title">📊 技术细节</div>
              <div class="dim-d-list">
                <div v-for="(d,i) in analysis.technical.details.slice(0,3)" :key="i" class="dim-d-item">• {{ d }}</div>
              </div>
            </div>

            <div class="dim-details" v-if="analysis.technical?.support_resistance">
              <div class="dim-d-title">🎯 支撑压力位</div>
              <div class="sr-grid">
                <div class="sr-item">
                  <div class="sr-label">强支撑</div>
                  <div class="sr-val price">{{ analysis.technical.support_resistance.strong_support.toFixed(2) }}</div>
                </div>
                <div class="sr-item">
                  <div class="sr-label">弱支撑</div>
                  <div class="sr-val price">{{ analysis.technical.support_resistance.weak_support.toFixed(2) }}</div>
                </div>
                <div class="sr-item">
                  <div class="sr-label">弱压力</div>
                  <div class="sr-val price">{{ analysis.technical.support_resistance.weak_resistance.toFixed(2) }}</div>
                </div>
                <div class="sr-item">
                  <div class="sr-label">强压力</div>
                  <div class="sr-val price">{{ analysis.technical.support_resistance.strong_resistance.toFixed(2) }}</div>
                </div>
              </div>
            </div>

            <el-divider style="margin:12px 0" />

            <!-- 操作建议 -->
            <div class="op-suggest" v-if="analysis.operation_suggestion">
              <div class="op-title">📋 操作建议</div>
              <div class="op-grid">
                <div class="op-item">
                  <div class="op-label">仓位建议</div>
                  <div class="op-val">{{ analysis.operation_suggestion.position_suggestion }}</div>
                </div>
                <div class="op-item" v-if="analysis.operation_suggestion.entry_point">
                  <div class="op-label">入场价位</div>
                  <div class="op-val price">{{ analysis.operation_suggestion.entry_point.toFixed(2) }}</div>
                </div>
                <div class="op-item" v-if="analysis.operation_suggestion.stop_loss">
                  <div class="op-label">止损价位</div>
                  <div class="op-val price down">{{ analysis.operation_suggestion.stop_loss.toFixed(2) }}</div>
                </div>
                <div class="op-item" v-if="analysis.operation_suggestion.target_price">
                  <div class="op-label">目标价位</div>
                  <div class="op-val price up">{{ analysis.operation_suggestion.target_price.toFixed(2) }}</div>
                </div>
              </div>
              <div class="op-list" v-if="analysis.operation_suggestion.suggestions?.length">
                <div v-for="(s,i) in analysis.operation_suggestion.suggestions" :key="i" class="op-s-item">• {{ s }}</div>
              </div>
            </div>
            </template>
          </el-card>

          <el-card v-if="relatedData.sector_stocks?.length" style="margin-top:16px">
            <template #header>
              <div class="card-hd">
                <span>🏭 同板块股票</span>
                <span class="card-hint">点击查看详情</span>
              </div>
            </template>
            <div class="sector-stocks">
              <div
                v-for="s in relatedData.sector_stocks.slice(0,8)"
                :key="s.ts_code"
                class="sector-stock"
                :class="{ focus: s.ts_code === currentStock?.ts_code }"
                @click="navigateToStock(s.ts_code)"
              >
                <div class="ss-name">
                  {{ s.name }}
                  <span class="ss-code stock-code">{{ s.ts_code }}</span>
                </div>
                <div class="ss-price price" v-if="s.close">{{ Number(s.close).toFixed(2) }}</div>
                <div class="ss-change change" :class="s.pct_change >= 0 ? 'up' : 'down'" v-if="s.pct_change">
                  {{ s.pct_change >= 0 ? '+' : '' }}{{ s.pct_change.toFixed(2) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 右栏：持仓 + 操作 + 风险事件 -->
        <el-col :span="10">
          <el-card v-if="costLine || editMode">
            <template #header>
              <div class="card-hd"><span>💰 持仓参考</span>
                <el-button size="small" text @click="editMode = !editMode">{{ editMode ? '取消' : '编辑' }}</el-button>
              </div>
            </template>
            <div class="pos-grid" v-if="!editMode">
              <div class="pos-cell">
                <span class="pos-label">成本</span>
                <span class="pos-val price up">{{ costLine?.cost_price?.toFixed(2) || '--' }}</span>
              </div>
              <div class="pos-cell">
                <span class="pos-label">止损</span>
                <span class="pos-val price down">{{ costLine?.stop_loss_price?.toFixed(2) || '--' }}</span>
              </div>
              <div class="pos-cell">
                <span class="pos-label">加仓</span>
                <span class="pos-val price">{{ costLine?.add_price?.toFixed(2) || '--' }}</span>
              </div>
              <div class="pos-cell">
                <span class="pos-label">减仓</span>
                <span class="pos-val price">{{ costLine?.reduce_price?.toFixed(2) || '--' }}</span>
              </div>
            </div>
            <el-form v-else :model="editForm" label-width="60px" size="small">
              <el-form-item label="成本"><el-input-number v-model="editForm.cost_price" :precision="3" controls-position="right" /></el-form-item>
              <el-form-item label="止损"><el-input-number v-model="editForm.stop_loss_price" :precision="3" controls-position="right" /></el-form-item>
              <el-form-item label="加仓"><el-input-number v-model="editForm.add_price" :precision="3" controls-position="right" /></el-form-item>
              <el-form-item label="减仓"><el-input-number v-model="editForm.reduce_price" :precision="3" controls-position="right" /></el-form-item>
              <el-form-item>
                <el-button type="primary" size="small" @click="saveCostLines" :loading="saving">保存</el-button>
                <el-button size="small" @click="editMode = false">取消</el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 快捷操作 -->
          <el-card style="margin-top:16px">
            <template #header><span>📋 快捷操作</span></template>
            <el-button style="width:100%;margin-bottom:8px" @click="handleAddWatchlist">{{ isInWatchlist ? '⭐ 已加入自选' : '⭐ 加入自选' }}</el-button>
            <el-button style="width:100%;margin-bottom:8px" type="warning" @click="showChecklist = true">📝 交易检查清单</el-button>
            <el-button style="width:100%" @click="goToPortfolio">💼 查看持仓</el-button>
          </el-card>

          <!-- 风险事件 -->
          <el-card style="margin-top:16px" v-if="events.length">
            <template #header><span>⚠️ 风险事件</span></template>
            <div v-for="e in events.slice(0,6)" :key="e._id" class="evt-row" :class="e.severity">
              <el-tag :type="e.severity==='critical'?'danger':e.severity==='warning'?'warning':'info'" size="small">{{ e.event_type }}</el-tag>
              <span class="evt-title">{{ e.title }}</span>
              <span class="evt-date">{{ formatEventDate(e.event_date) }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 研究抽屉 -->
    <ResearchDrawer v-model="showResearch" :ts-code="symbol + '.' + exchange" />
    <PreTradeChecklistModal v-model="showChecklist" :stock-code="symbol + '.' + exchange" :stock-name="currentStock?.name || ''" :current-price="latestPrice?.price ?? latestPrice?.close ?? 0" action="BUY" @done="showChecklist = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { useStockDetail } from '@/composables/useStockDetail'
import { useWatchlistStore } from '@/stores/watchlistStore'
import ResearchDrawer from '@/components/stock/ResearchDrawer.vue'
import PreTradeChecklistModal from '@/components/PreTradeChecklistModal.vue'
import KlineChart from '@/components/chart/KlineChart.vue'
import type { StockSearchResult } from '@/types/stock'

const {
  symbol, exchange, tsCode, currentStock, isIndex,
  loading, latestPrice, analysis, events, costLine, relatedData, klinePeriod,
  chartData, volumeData, maData, metrics,
  changeKlinePeriod, addToWatchlist, goToPortfolio, navigateToStock,
} = useStockDetail()

const watchlistStore = useWatchlistStore()
const isInWatchlist = computed(() => watchlistStore.isInWatchlist(tsCode.value))

watchlistStore.fetchWatchlist()

const showResearch = ref(false)
const showChecklist = ref(false)
const finderKeyword = ref('')
const editMode = ref(false)
const saving = ref(false)
const editForm = ref({
  cost_price: 0,
  stop_loss_price: 0,
  add_price: undefined as number | undefined,
  reduce_price: undefined as number | undefined,
})

const quickStocks = [
  { code: '600519.SH', name: '贵州茅台' }, { code: '000001.SZ', name: '平安银行' },
  { code: '600703.SH', name: '三安光电' }, { code: '002594.SZ', name: '比亚迪' },
  { code: '300750.SZ', name: '宁德时代' }, { code: '600036.SH', name: '招商银行' },
]

function dimColor(s: number) {
  return s >= 70 ? '#67c23a' : s >= 50 ? '#e6a23c' : '#f56c6c'
}

function formatEventDate(d: string) {
  if (!d || d.length !== 8) return d
  return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
}

function quickOpen(code: string) {
  navigateToStock(code)
}

let searchTimer: ReturnType<typeof setTimeout> | null = null

async function handleFinderSearch(q: string, cb: (results: StockSearchResult[]) => void) {
  if (!q?.trim()) { cb([]); return }
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const res: any = await request.get(`/stocks/search/${encodeURIComponent(q.trim())}?limit=8`)
      cb(((res || []) as any[]).map((s: any) => ({ value: s.ts_code, name: s.name, ts_code: s.ts_code })))
    } catch { cb([]) }
  }, 300)
}

function handleFinderSelect(item: StockSearchResult) {
  navigateToStock(item.value)
}

async function handleAddWatchlist() {
  await addToWatchlist()
}

watch(editMode, (v) => {
  if (v && costLine.value) {
    editForm.value = {
      cost_price: costLine.value.cost_price || 0,
      stop_loss_price: costLine.value.stop_loss_price || 0,
      add_price: costLine.value.add_price,
      reduce_price: costLine.value.reduce_price,
    }
  }
})

async function saveCostLines() {
  if (!tsCode.value) return
  if (editForm.value.stop_loss_price && editForm.value.stop_loss_price >= editForm.value.cost_price) {
    ElMessage.error('止损价应低于成本价'); return
  }
  saving.value = true
  try {
    await request.put(`/portfolio/cost-lines/${tsCode.value}`, editForm.value)
    costLine.value = { ...editForm.value, ts_code: tsCode.value } as any
    editMode.value = false
    ElMessage.success('已保存')
  } catch { ElMessage.error('保存失败') }
  saving.value = false
}
</script>

<style scoped>
.insufficient-tip { padding: 20px 0; text-align: center; }
.insufficient-tip p { margin: 4px 0; }
.stock-finder { display: flex; justify-content: center; align-items: center; min-height: 50vh; }
.finder-box { text-align: center; max-width: 460px; }
.finder-box h3 { font-family: var(--font-display); font-size: 22px; margin-bottom: 6px; }
.finder-desc { color: var(--claude-text-secondary); margin-bottom: 20px; font-size: 14px; }
.finder-quick { margin-top: 16px; display: flex; align-items: center; justify-content: center; gap: 2px; flex-wrap: wrap; }
.quick-label { font-size: 12px; color: var(--claude-text-secondary); margin-right: 2px; }
.ac-code { font-weight: 600; color: var(--claude-accent); margin-right: 12px; }
.ac-name { color: var(--claude-text-secondary); }

.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; padding: 20px 24px; background: var(--claude-card); border: 1px solid var(--claude-border); border-radius: var(--radius-md); }
.hd-left h2 { font-size: 24px; }
.code { font-size: 15px; color: var(--claude-text-secondary); font-weight: 400; margin-left: 6px; }
.hd-tags { margin-top: 8px; display: flex; gap: 6px; }
.hd-right { text-align: right; }
.hd-price { font-family: var(--font-display); font-size: 36px; font-weight: 800; letter-spacing: -0.02em; }
.hd-change { font-size: 16px; font-weight: 600; margin-top: 2px; }
.up { color: var(--color-up); }
.down { color: var(--color-down); }

.metric-card { background: var(--claude-card); border: 1px solid var(--claude-border); border-radius: var(--radius-sm); padding: 12px; text-align: center; transition: box-shadow var(--transition-fast), transform var(--transition-fast); }
.metric-card:hover { box-shadow: var(--shadow-sm); transform: translateY(-1px); }
.met-label { font-size: 11px; color: var(--claude-text-secondary); margin-bottom: 4px; }
.met-value { font-family: var(--font-display); font-size: 17px; font-weight: 700; }

.score-row { display: flex; align-items: center; gap: 16px; }
.score-num { font-family: var(--font-display); font-size: 42px; font-weight: 800; line-height: 1; }
.score-main { text-align: center; min-width: 100px; }
.score-label { font-size: 12px; color: var(--claude-text-secondary); }
.score-summary { font-size: 13px; color: var(--claude-text-secondary); line-height: 1.6; }
.dim-bar { display: flex; align-items: center; margin-bottom: 6px; }
.dim-name { width: 50px; font-family: var(--font-sans); font-size: 12px; color: var(--claude-text-secondary); }
.dim-score { width: 40px; text-align: right; font-family: var(--font-sans); font-size: 12px; font-weight: 600; }
.reason-line { font-size: 12px; color: var(--claude-text-secondary); line-height: 1.8; }

.evt-row { display: flex; align-items: center; gap: 8px; padding: 8px; border-left: 3px solid; margin-bottom: 8px; border-radius: 0 6px 6px 0; background: var(--claude-bg); }
.evt-row.critical { border-color: var(--color-up); }
.evt-row.warning { border-color: var(--claude-accent); }
.evt-row.info { border-color: var(--claude-blue); }
.evt-title { flex: 1; font-family: var(--font-sans); font-size: 13px; }
.evt-date { font-size: 11px; color: var(--claude-text-secondary); }

.pos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.pos-cell { background: var(--claude-bg-raised); border-radius: var(--radius-sm); padding: 12px; text-align: center; }
.pos-label { font-size: 11px; color: var(--claude-text-secondary); display: block; margin-bottom: 2px; }
.pos-val { font-family: var(--font-display); font-size: 20px; font-weight: 700; }
.card-hd { display: flex; justify-content: space-between; align-items: center; }
.hd-change-amt { font-size: 12px; font-weight: 500; margin-top: 2px; opacity: 0.8; }

/* K线图卡片 */
.kline-card { margin-bottom: 16px; }
.kline-tabs { display: flex; gap: 4px; }
.kline-tabs .el-button { padding: 4px 10px; font-size: 12px; }

/* AI 分析增强 */
.signals-box { background: var(--claude-bg); border-radius: 8px; padding: 12px; margin-top: 12px; }
.signals-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.signals-list { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.signal-item { padding: 8px; border-radius: 6px; background: var(--claude-card); border: 1px solid var(--claude-border); }
.signal-item.bullish { border-left: 3px solid var(--color-down); }
.signal-item.bearish { border-left: 3px solid var(--color-up); }
.signal-item.important { border-left: 3px solid var(--claude-accent); }
.signal-name { font-family: var(--font-sans); font-size: 12px; font-weight: 600; margin-bottom: 2px; }
.signal-desc { font-family: var(--font-sans); font-size: 11px; color: var(--claude-text-secondary); }

/* 多空对比 */
.bb-analysis { margin-top: 8px; }
.bb-title { font-size: 13px; font-weight: 600; margin-bottom: 10px; }
.bb-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.bb-col { background: var(--claude-bg); border-radius: 8px; padding: 10px; }
.bb-col-title { font-family: var(--font-sans); font-size: 12px; font-weight: 600; margin-bottom: 6px; }
.bb-col.bull .bb-col-title { color: var(--color-down); }
.bb-col.bear .bb-col-title { color: var(--color-up); }
.bb-empty { font-size: 12px; color: var(--claude-text-secondary); text-align: center; padding: 8px; }
.bb-reason { display: flex; gap: 4px; margin-bottom: 4px; }
.bb-dot { font-size: 14px; line-height: 1; }
.bb-text { font-family: var(--font-sans); font-size: 12px; color: var(--claude-text-secondary); line-height: 1.5; }

/* 技术细节 */
.dim-details { margin-top: 8px; }
.dim-d-title { font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--claude-text-secondary); }
.dim-d-list { display: flex; flex-direction: column; gap: 4px; }
.dim-d-item { font-family: var(--font-sans); font-size: 12px; color: var(--claude-text-secondary); }

/* 支撑压力 */
.sr-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.sr-item { background: var(--claude-card); border: 1px solid var(--claude-border); border-radius: var(--radius-sm); padding: 8px; text-align: center; }
.sr-label { font-family: var(--font-sans); font-size: 11px; color: var(--claude-text-secondary); margin-bottom: 2px; }
.sr-val { font-family: var(--font-display); font-size: 15px; font-weight: 700; }

/* 操作建议 */
.op-suggest { margin-top: 8px; }
.op-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.op-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
.op-item { background: var(--claude-card); border: 1px solid var(--claude-border); border-radius: var(--radius-sm); padding: 10px; text-align: center; }
.op-label { font-family: var(--font-sans); font-size: 11px; color: var(--claude-text-secondary); margin-bottom: 2px; }
.op-val { font-family: var(--font-display); font-size: 15px; font-weight: 700; }
.op-list { display: flex; flex-direction: column; gap: 4px; }
.op-s-item { font-family: var(--font-sans); font-size: 12px; color: var(--claude-text-secondary); }

/* 同板块股票 */
.sector-stocks { display: flex; flex-direction: column; gap: 4px; }
.sector-stock { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; border-radius: 6px; cursor: pointer; transition: background 0.15s; }
.sector-stock:hover { background: var(--claude-bg); }
.sector-stock.focus { background: var(--claude-accent-light); }
.ss-name { display: flex; align-items: center; gap: 6px; }
.ss-name div { font-weight: 500; font-size: 13px; }
.ss-code { font-size: 11px; color: var(--claude-text-secondary); font-family: monospace; }
.ss-price { font-size: 13px; font-family: monospace; font-weight: 600; margin-right: 8px; }
.ss-change { font-size: 12px; font-weight: 600; font-family: monospace; }

.card-hint { font-family: var(--font-sans); font-size: 11px; color: var(--claude-text-secondary); }
</style>
