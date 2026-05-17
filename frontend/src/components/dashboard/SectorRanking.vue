<template>
  <el-card>
    <template #header>
      <div class="card-hd">
        <span>🔥 领涨板块</span>
        <div>
          <el-button size="small" text :type="tab === 'industry' ? 'primary' : ''" @click="$emit('update:tab', 'industry')">行业</el-button>
          <el-button size="small" text :type="tab === 'stocks' ? 'primary' : ''" @click="$emit('update:tab', 'stocks'); $emit('auto-select')">成分股</el-button>
        </div>
      </div>
    </template>
    <div class="sector-list" v-loading="loading">
      <template v-if="tab === 'industry'">
        <div
          v-for="(s, i) in sectors.slice(0, 8)"
          :key="i"
          class="sector-item"
          :class="{ active: selectedSector === (s.name || s.sector) }"
          @click="handleSectorClick(s)"
        >
          <div class="s-num font-number" :class="i < 3 ? 'top3' : ''">{{ i + 1 }}</div>
          <div class="s-info">
            <div class="s-name">{{ s.name || s.sector }}</div>
            <div class="s-meta">
              <span v-if="s.lead_stock" class="s-lead">领涨 {{ s.lead_stock }}</span>
              <span v-if="s.up_count != null" class="s-ud">{{ s.up_count }}↑ {{ s.down_count }}↓</span>
            </div>
          </div>
          <div class="s-right">
            <div class="s-change change" :class="s.change_pct >= 0 ? 'up' : 'down'">
              {{ s.change_pct >= 0 ? '+' : '' }}{{ s.change_pct?.toFixed(2) }}%
            </div>
            <div v-if="s.lead_stock_pct" class="s-lead-pct change" :class="s.lead_stock_pct >= 0 ? 'up' : 'down'">
              {{ s.lead_stock_pct >= 0 ? '+' : '' }}{{ s.lead_stock_pct?.toFixed(2) }}%
            </div>
          </div>
        </div>
        <el-empty v-if="sectors.length === 0" description="暂无数据" :image-size="40" />
      </template>
      <template v-else>
        <div v-if="stocks.length">
          <div class="stocks-header">
            <span>{{ selectedSector || '全部' }}成分股</span>
            <el-button size="small" text type="primary" @click="$emit('update:tab', 'industry')">← 返回</el-button>
          </div>
          <div v-for="(s, i) in stocks" :key="s.ts_code || i" class="sector-item stock-item" @click="handleStockClick(s)">
            <div class="s-num font-number">{{ i + 1 }}</div>
            <div class="s-info">
              <div class="s-name">{{ s.name }}</div>
              <div class="s-meta"><span class="s-code">{{ s.ts_code }}</span></div>
            </div>
            <div class="s-right">
              <div class="s-change change" :class="(s.pct_change || 0) >= 0 ? 'up' : 'down'">
                {{ (s.pct_change || 0) >= 0 ? '+' : '' }}{{ s.pct_change?.toFixed(2) }}%
              </div>
              <div v-if="s.close" class="s-price">¥{{ s.close?.toFixed(2) }}</div>
            </div>
          </div>
        </div>
        <el-empty v-else description="点击行业板块查看成分股" :image-size="40" />
      </template>
    </div>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  sectors: Array<{
    name?: string; sector?: string; change_pct: number; all_stocks?: any[]
    lead_stock?: string; lead_stock_pct?: number; up_count?: number; down_count?: number
  }>
  stocks: Array<{ ts_code: string; name: string; close?: number; pct_change?: number }>
  tab: 'industry' | 'stocks'
  selectedSector: string
  loading: boolean
}>()

const emit = defineEmits<{
  'update:tab': [value: 'industry' | 'stocks']
  select: [sector: any]
  'go-stock': [tsCode: string]
  'auto-select': []
}>()

function handleSectorClick(s: any) {
  emit('select', s)
}

function handleStockClick(s: any) {
  emit('go-stock', s.ts_code)
}
</script>

<style scoped>
.card-hd { display: flex; justify-content: space-between; align-items: center; }

.sector-list { max-height: 380px; overflow-y: auto; }
.sector-item { display: flex; align-items: center; gap: 10px; padding: 8px 4px; border-bottom: 1px solid var(--claude-border); cursor: pointer; transition: background 0.15s; border-radius: 4px; }
.sector-item:hover { background: var(--claude-overlay); }
.sector-item.active { background: var(--claude-accent-light); border-left: 3px solid var(--claude-accent); }
.sector-item.stock-item { cursor: pointer; }
.s-num { width: 20px; text-align: center; font-size: 12px; font-weight: 700; color: var(--claude-text-secondary); flex-shrink: 0; }
.s-num.top3 { color: var(--claude-accent); }
.s-info { flex: 1; min-width: 0; }
.s-name { font-family: var(--font-sans); font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.s-meta { display: flex; gap: 8px; margin-top: 2px; font-size: 11px; color: var(--claude-text-tertiary); }
.s-lead { color: var(--claude-text-secondary); }
.s-ud { color: var(--claude-text-tertiary); }
.s-code { font-family: var(--font-mono); font-size: 10px; }
.s-right { text-align: right; flex-shrink: 0; }
.s-change { font-family: var(--font-number); font-size: 13px; font-weight: 600; }
.s-lead-pct { font-family: var(--font-mono); font-size: 11px; opacity: 0.7; }
.s-price { font-family: var(--font-mono); font-size: 11px; color: var(--claude-text-tertiary); margin-top: 2px; }
.stocks-header { display: flex; justify-content: space-between; align-items: center; font-family: var(--font-sans); font-size: 12px; color: var(--claude-text-secondary); padding: 4px 0 8px; border-bottom: 1px solid var(--claude-border); margin-bottom: 4px; }
</style>
