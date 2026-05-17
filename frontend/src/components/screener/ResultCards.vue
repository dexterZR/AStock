<template>
  <div class="cards-grid" v-loading="screenerStore.loading">
    <div v-for="stock in screenerStore.results" :key="stock.ts_code" class="stock-card" @click="emit('go-stock', stock.ts_code)">
      <div class="card-header">
        <div>
          <div class="card-name">{{ stock.name }}</div>
          <div class="card-code stock-code">{{ stock.ts_code }}</div>
        </div>
        <span class="card-change change" :class="stock.pct_change >= 0 ? 'up' : 'down'">
          {{ stock.pct_change >= 0 ? '+' : '' }}{{ stock.pct_change?.toFixed(2) }}%
        </span>
      </div>
      <div class="card-price price">{{ stock.close?.toFixed(2) }}</div>
      <div class="card-metrics">
        <div class="metric">
          <span class="metric-label">PE</span>
          <span class="metric-value font-number">{{ stock.pe?.toFixed(1) || '--' }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">PB</span>
          <span class="metric-value font-number">{{ stock.pb?.toFixed(2) || '--' }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">换手</span>
          <span class="metric-value font-number">{{ stock.turnover_rate != null ? stock.turnover_rate.toFixed(1) + '%' : '--' }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">市值</span>
          <span class="metric-value font-number">{{ stock.total_mv != null ? (stock.total_mv / 10000).toFixed(0) + '亿' : '--' }}</span>
        </div>
        <div class="metric">
          <span class="metric-label">行业</span>
          <span class="metric-value">{{ stock.industry || '--' }}</span>
        </div>
      </div>
      <div class="card-signals" v-if="stock.signals">
        <span v-for="sig in getActiveSignals(stock.signals)" :key="sig" class="signal-tag">{{ sig }}</span>
      </div>
      <div class="card-ai-reason" v-if="stock.ai_reason">
        <span class="ai-score" v-if="stock.match_score">⭐{{ stock.match_score }}</span>
        <span class="ai-reason-text">{{ stock.ai_reason }}</span>
      </div>
    </div>
  </div>
  <el-empty v-if="!screenerStore.loading && screenerStore.results.length === 0" description="暂无数据" />
</template>

<script setup lang="ts">
import { useScreenerStore } from '@/stores/screenerStore'

const screenerStore = useScreenerStore()
const emit = defineEmits<{
  (e: 'go-stock', code: string): void
}>()

const SIGNAL_LABELS: Record<string, string> = {
  ma5_cross_ma10: 'MA金叉', ma5_cross_ma20: 'MA穿20', ma10_cross_ma20: 'MA穿20',
  macd_cross: 'MACD金叉', kdj_cross: 'KDJ金叉',
  rsi_oversold: 'RSI超卖', rsi_overbought: 'RSI超买',
  boll_breakout_up: '布林突破', boll_breakout_down: '布林破下',
  ma_bullish: '多头', ma_bearish: '空头',
  volume_surge: '放量', volume_shrink: '缩量',
  breakout_20d_high: '20日新高', breakout_60d_high: '60日新高',
  drop_20d_low: '20日新低',
  v_shape_recovery: 'V型', consolidation: '缩量盘整',
  continuous_up_3d: '连涨', continuous_volume_3d: '连续放量',
}

function getActiveSignals(signals?: Record<string, boolean>): string[] {
  if (!signals) return []
  return Object.entries(signals).filter(([, v]) => v === true).map(([k]) => SIGNAL_LABELS[k] || k).slice(0, 3)
}
</script>

<style scoped>
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.stock-card {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-radius: var(--radius-md);
  padding: 14px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.stock-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--claude-accent);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}
.card-name {
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-sans);
  color: var(--claude-text);
}
.card-code {
  font-size: 11px;
  margin-top: 2px;
}
.card-change {
  font-size: 14px;
  font-weight: 600;
}
.card-price {
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-display);
  margin-bottom: 10px;
}
.card-metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}
.metric {
  display: flex;
  flex-direction: column;
}
.metric-label {
  font-size: 10px;
  color: var(--claude-text-tertiary);
  font-family: var(--font-sans);
}
.metric-value {
  font-size: 12px;
  font-weight: 500;
  color: var(--claude-text);
}
.card-signals {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.signal-tag {
  background: var(--claude-accent-light);
  color: var(--claude-accent);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-family: var(--font-sans);
}
.card-ai-reason {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed var(--claude-border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ai-score {
  font-size: 11px;
  font-weight: 600;
  color: var(--claude-accent);
}
.ai-reason-text {
  font-size: 10px;
  color: var(--claude-text-secondary);
  font-family: var(--font-sans);
  line-height: 1.3;
}
</style>
