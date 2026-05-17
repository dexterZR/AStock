<template>
  <el-table :data="screenerStore.results" v-loading="screenerStore.loading" style="width: 100%" @selection-change="emit('selection-change', $event)" empty-text="暂无数据">
    <el-table-column type="selection" width="45" />
    <el-table-column prop="ts_code" label="代码" width="120">
      <template #default="{ row }">
        <span class="stock-code">{{ row.ts_code }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="name" label="名称" min-width="100" />
    <el-table-column prop="industry" label="行业" width="80" />
    <el-table-column prop="close" label="现价" width="90" sortable>
      <template #default="{ row }">
        <span class="price">{{ row.close?.toFixed(2) }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="pct_change" label="涨跌幅" width="90" sortable>
      <template #default="{ row }">
        <span class="change" :class="row.pct_change >= 0 ? 'up' : 'down'">
          {{ row.pct_change >= 0 ? '+' : '' }}{{ row.pct_change?.toFixed(2) }}%
        </span>
      </template>
    </el-table-column>
    <el-table-column prop="turnover_rate" label="换手率" width="80" sortable>
      <template #default="{ row }">{{ row.turnover_rate != null ? row.turnover_rate.toFixed(2) + '%' : '--' }}</template>
    </el-table-column>
    <el-table-column prop="pe" label="PE" width="70" sortable>
      <template #default="{ row }">
        <span class="font-number">{{ row.pe?.toFixed(1) || '--' }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="pb" label="PB" width="70" sortable>
      <template #default="{ row }">
        <span class="font-number">{{ row.pb?.toFixed(2) || '--' }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="total_mv" label="总市值" width="90" sortable>
      <template #default="{ row }">
        <span class="font-number">{{ row.total_mv != null ? (row.total_mv / 10000).toFixed(1) + '亿' : '--' }}</span>
      </template>
    </el-table-column>
    <el-table-column label="AI推荐" width="160" v-if="hasAIReason">
      <template #default="{ row }">
        <div class="ai-reason" v-if="row.ai_reason">
          <span class="ai-score" v-if="row.match_score">⭐{{ row.match_score }}</span>
          <span class="ai-reason-text">{{ row.ai_reason }}</span>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="信号" width="120">
      <template #default="{ row }">
        <div class="signal-tags">
          <span v-for="sig in getActiveSignals(row.signals)" :key="sig" class="signal-tag">{{ sig }}</span>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="80" fixed="right">
      <template #default="{ row }">
        <el-button size="small" text type="primary" @click="emit('go-stock', row.ts_code)">查看</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useScreenerStore } from '@/stores/screenerStore'

const screenerStore = useScreenerStore()
const emit = defineEmits<{
  (e: 'selection-change', rows: any[]): void
  (e: 'go-stock', code: string): void
}>()

const hasAIReason = computed(() => screenerStore.results.some((r: any) => r.ai_reason))

const SIGNAL_LABELS: Record<string, string> = {
  ma5_cross_ma10: 'MA金叉',
  ma5_cross_ma20: 'MA穿20',
  ma10_cross_ma20: 'MA穿20',
  macd_cross: 'MACD金叉',
  kdj_cross: 'KDJ金叉',
  rsi_oversold: 'RSI超卖',
  rsi_overbought: 'RSI超买',
  boll_breakout_up: '布林突破',
  boll_breakout_down: '布林破下',
  ma_bullish: '多头',
  ma_bearish: '空头',
  volume_surge: '放量',
  volume_shrink: '缩量',
  breakout_20d_high: '20日新高',
  breakout_60d_high: '60日新高',
  drop_20d_low: '20日新低',
  v_shape_recovery: 'V型',
  consolidation: '缩量盘整',
  continuous_up_3d: '连涨',
  continuous_volume_3d: '连续放量',
}

function getActiveSignals(signals?: Record<string, boolean>): string[] {
  if (!signals) return []
  return Object.entries(signals)
    .filter(([, v]) => v === true)
    .map(([k]) => SIGNAL_LABELS[k] || k)
    .slice(0, 3)
}
</script>

<style scoped>
.signal-tags {
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
.ai-reason {
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
