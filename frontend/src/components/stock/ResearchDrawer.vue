<template>
  <el-drawer v-model="visible" :title="title" direction="rtl" size="400px" :before-close="onClose">
    <div class="drawer-body" v-if="data">
      <!-- 综合评分 -->
      <div class="section">
        <div class="section-title">🤖 AI综合评分</div>
        <div class="score-big" :style="{ color: data.verdict?.color }">
          {{ data.total_score }}<span class="score-unit">/100</span>
        </div>
        <el-tag :color="data.verdict?.color" effect="dark" size="small" style="margin-top:4px">
          {{ data.verdict?.action }}
        </el-tag>
        <div class="score-summary">{{ data.verdict?.summary }}</div>
      </div>

      <el-divider />

      <!-- 三维度 -->
      <div class="section">
        <div class="section-title">📊 维度分析</div>
        <div class="dim-item" v-if="data.technical">
          <div class="dim-header">
            <span>技术面</span>
            <span class="dim-score" :style="{ color: getDimColor(data.technical.score) }">{{ data.technical.score }}分</span>
          </div>
          <el-progress :percentage="data.technical.score" :color="getDimColor(data.technical.score)" :stroke-width="6" />
          <div class="dim-reasons">
            <div v-for="(r,i) in data.technical.reasons?.slice(0,3)" :key="i">• {{ r }}</div>
          </div>
        </div>
        <div class="dim-item" v-if="data.fundamental">
          <div class="dim-header"><span>基本面</span><span class="dim-score" :style="{ color: getDimColor(data.fundamental.score) }">{{ data.fundamental.score }}分</span></div>
          <el-progress :percentage="data.fundamental.score" :color="getDimColor(data.fundamental.score)" :stroke-width="6" />
          <div class="dim-reasons"><div v-for="(r,i) in data.fundamental.reasons?.slice(0,3)" :key="i">• {{ r }}</div></div>
        </div>
        <div class="dim-item" v-if="data.catalyst">
          <div class="dim-header"><span>催化剂</span><span class="dim-score" :style="{ color: getDimColor(data.catalyst.score) }">{{ data.catalyst.score }}分</span></div>
          <el-progress :percentage="data.catalyst.score" :color="getDimColor(data.catalyst.score)" :stroke-width="6" />
          <div class="dim-reasons"><div v-for="(r,i) in data.catalyst.reasons?.slice(0,3)" :key="i">• {{ r }}</div></div>
        </div>
      </div>

      <el-divider />

      <!-- 风险事件 -->
      <div class="section" v-if="events.length">
        <div class="section-title">⚠️ 风险事件 ({{ events.length }})</div>
        <div v-for="e in events.slice(0,5)" :key="e._id" class="event-mini" :class="e.severity">
          <div class="evt-tag">{{ e.event_type }}</div>
          <div class="evt-title">{{ e.title }}</div>
          <div class="evt-date">{{ e.event_date }}</div>
        </div>
      </div>

      <el-divider />

      <!-- 持仓相关 -->
      <div class="section" v-if="costLine">
        <div class="section-title">💰 持仓参考</div>
        <div class="position-grid">
          <div class="pos-item"><span class="pos-label">成本</span><span class="pos-val up">{{ costLine.cost_price?.toFixed(2) }}</span></div>
          <div class="pos-item"><span class="pos-label">止损</span><span class="pos-val down">{{ costLine.stop_loss_price?.toFixed(2) }}</span></div>
          <div class="pos-item" v-if="costLine.add_price"><span class="pos-label">加仓</span><span class="pos-val">{{ costLine.add_price.toFixed(2) }}</span></div>
          <div class="pos-item" v-if="costLine.reduce_price"><span class="pos-label">减仓</span><span class="pos-val">{{ costLine.reduce_price.toFixed(2) }}</span></div>
        </div>
      </div>
    </div>
    <el-empty v-else description="加载中..." />
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import request from '@/api/request'

const props = defineProps<{
  modelValue: boolean
  tsCode: string
}>()

const emit = defineEmits(['update:modelValue'])
const visible = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })
const data = ref<any>(null)
const events = ref<any[]>([])
const costLine = ref<any>(null)

const title = computed(() => props.tsCode ? `🔬 个股研究 · ${props.tsCode}` : '个股研究')

function getDimColor(score: number) { return score >= 70 ? '#67c23a' : score >= 50 ? '#e6a23c' : '#f56c6c' }

async function load() {
  if (!props.tsCode) return
  try {
    const [analysis, evts, cl]: any[] = await Promise.all([
      request.get(`/analysis/${props.tsCode}`),
      request.get(`/portfolio/events?ts_code=${props.tsCode}&days=90`),
      request.get(`/portfolio/cost-lines/${props.tsCode}`),
    ])
    data.value = analysis
    events.value = evts || []
    costLine.value = cl
  } catch {}
}

watch(() => props.modelValue, (v) => { if (v) load() })
function onClose() { emit('update:modelValue', false) }
</script>

<style scoped>
.section { margin-bottom: 8px; }
.section-title { font-family: var(--font-sans); font-size: 14px; font-weight: 600; margin-bottom: 12px; color: var(--claude-text); }
.score-big { font-family: var(--font-display); font-size: 42px; font-weight: 800; letter-spacing: -0.02em; }
.score-unit { font-size: 18px; font-weight: 400; opacity: 0.6; }
.score-summary { font-size: 12px; color: var(--claude-text-secondary); margin-top: 8px; line-height: 1.6; }
.dim-item { margin-bottom: 16px; }
.dim-header { display: flex; justify-content: space-between; margin-bottom: 4px; font-family: var(--font-sans); font-size: 13px; font-weight: 500; }
.dim-score { font-weight: 700; font-size: 14px; }
.dim-reasons { margin-top: 6px; font-family: var(--font-sans); font-size: 12px; color: var(--claude-text-secondary); line-height: 1.7; }
.event-mini { padding: 8px; border-left: 3px solid; margin-bottom: 8px; border-radius: 4px; background: var(--claude-bg); }
.event-mini.critical { border-color: var(--color-up); }
.event-mini.warning { border-color: var(--claude-accent); }
.event-mini.info { border-color: var(--claude-blue); }
.evt-tag { font-size: 10px; color: var(--claude-text-secondary); text-transform: uppercase; margin-bottom: 2px; }
.evt-title { font-family: var(--font-sans); font-size: 13px; font-weight: 500; }
.evt-date { font-size: 11px; color: var(--claude-text-secondary); }
.position-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.pos-item { background: var(--claude-bg-raised); border-radius: var(--radius-sm); padding: 10px; text-align: center; }
.pos-label { font-size: 11px; color: var(--claude-text-secondary); display: block; margin-bottom: 2px; }
.pos-val { font-family: var(--font-display); font-size: 18px; font-weight: 700; }
.up { color: var(--color-up); }
.down { color: var(--color-down); }
</style>
