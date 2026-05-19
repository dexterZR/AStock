<template>
  <div class="kline-wrapper">
    <div ref="chartContainer" class="kline-chart"></div>
    <div v-if="hoverInfo.visible" class="kline-tooltip" :style="{top: hoverInfo.y + 'px', left: hoverInfo.x + 'px'}">
      <div class="tt-date">{{ hoverInfo.date }}</div>
      <div class="tt-row">开 <span class="tt-val">{{ hoverInfo.open }}</span></div>
      <div class="tt-row">高 <span class="tt-val up">{{ hoverInfo.high }}</span></div>
      <div class="tt-row">低 <span class="tt-val down">{{ hoverInfo.low }}</span></div>
      <div class="tt-row">收 <span class="tt-val" :class="hoverInfo.close >= hoverInfo.open ? 'up' : 'down'">{{ hoverInfo.close }}</span></div>
      <div class="tt-row" v-if="hoverInfo.pctChange !== undefined">涨跌幅 <span class="tt-val" :class="hoverInfo.pctChange >= 0 ? 'up' : 'down'">{{ hoverInfo.pctChange >= 0 ? '+' : '' }}{{ hoverInfo.pctChange.toFixed(2) }}%</span></div>
      <div class="tt-row" v-if="hoverInfo.volume">量 <span class="tt-val">{{ formatVol(hoverInfo.volume) }}</span></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { createChart, type IChartApi, type ISeriesApi, type CandlestickData } from 'lightweight-charts'

interface KlineBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  pct_change?: number
}

interface CostLine {
  price: number
  color: string
  lineStyle: number
  lineWidth: number
  title: string
  visible: boolean
}

interface Props {
  data: KlineBar[]
  maData?: Record<string, { time: string; value: number }[]>
  volumeData?: { time: string; value: number; color: string }[]
  costLines?: CostLine[]
  range?: string
}

const props = defineProps<Props>()
const chartContainer = ref<HTMLElement>()
let chart: IChartApi | null = null
let candleSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
let maSeriesMap: Map<string, ISeriesApi<'Line'>> = new Map()
let resizeObserver: ResizeObserver | null = null
let priceLines: any[] = []
let pctChangeMap: Map<string, number> = new Map()

const hoverInfo = ref({
  visible: false, x: 0, y: 0,
  date: '', open: '', high: '', low: '', close: '', pctChange: undefined as number | undefined, volume: 0,
})

const isDark = computed(() => document.documentElement.classList.contains('dark'))

const maColors: Record<string, string> = {
  MA5: '#f9a825',
  MA10: '#7b1fa2',
  MA20: '#2196f3',
  MA60: '#e91e63',
}

function getThemeColors() {
  return isDark.value
    ? { bg: '#1e293b', text: '#e5e7eb', grid: '#334155', border: '#475569' }
    : { bg: '#ffffff', text: '#1a1a1a', grid: '#f0ede8', border: '#e8e5e0' }
}

function initChart() {
  if (!chartContainer.value) {
    console.warn('[KlineChart] chartContainer ref is null, cannot init')
    return
  }
  console.log('[KlineChart] initChart, container size:', chartContainer.value.clientWidth, 'x', chartContainer.value.clientHeight)
  const theme = getThemeColors()

  chart = createChart(chartContainer.value, {
    layout: {
      background: { color: theme.bg },
      textColor: theme.text,
      fontSize: 12,
    },
    grid: {
      vertLines: { color: theme.grid },
      horzLines: { color: theme.grid },
    },
    crosshair: {
      mode: 1,
      vertLine: { width: 1, color: isDark.value ? '#64748b' : '#c4b5a0', style: 2 },
      horzLine: { width: 1, color: isDark.value ? '#64748b' : '#c4b5a0', style: 2 },
    },
    rightPriceScale: {
      borderColor: theme.border,
      autoScale: true,
    },
    timeScale: {
      borderColor: theme.border,
      timeVisible: false,
      secondsVisible: false,
      rightOffset: 5,
      barSpacing: 14,
      minBarSpacing: 4,
    },
    width: chartContainer.value.clientWidth,
    height: 460,
  })

  candleSeries = chart.addCandlestickSeries({
    upColor: '#ef5350',
    downColor: '#26a69a',
    borderUpColor: '#ef5350',
    borderDownColor: '#26a69a',
    wickUpColor: '#ef5350',
    wickDownColor: '#26a69a',
  })

  volumeSeries = chart.addHistogramSeries({
    color: '#26a69a',
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
  })
  chart.priceScale('volume').applyOptions({
    scaleMargins: { top: 0.82, bottom: 0 },
  })

  chart.subscribeCrosshairMove((param) => {
    if (!param || !param.time || !param.seriesData) {
      hoverInfo.value.visible = false
      return
    }
    const candleData = param.seriesData.get(candleSeries!) as any
    const volData = param.seriesData.get(volumeSeries!) as any
    if (!candleData) {
      hoverInfo.value.visible = false
      return
    }
    hoverInfo.value = {
      visible: true,
      x: param.point?.x || 0,
      y: param.point?.y || 0,
      date: String(param.time),
      open: candleData.open?.toFixed(2) || '--',
      high: candleData.high?.toFixed(2) || '--',
      low: candleData.low?.toFixed(2) || '--',
      close: candleData.close?.toFixed(2) || '--',
      pctChange: pctChangeMap.get(String(param.time)),
      volume: volData?.value || 0,
    }
  })
}

function formatVol(v: number) {
  if (!v) return '--'
  if (v >= 1e8) return (v / 1e8).toFixed(2) + '亿'
  if (v >= 1e4) return (v / 1e4).toFixed(0) + '万'
  return String(v)
}

function updateData() {
  console.log('[KlineChart] updateData called, data length:', props.data.length, 'maData:', !!props.maData, 'volumeData:', !!props.volumeData)
  if (!candleSeries || !chart) {
    console.warn('[KlineChart] chart not initialized, skipping update')
    return
  }
  if (props.data.length === 0) {
    console.warn('[KlineChart] no data to display')
    return
  }

  // Clean up old MA series
  maSeriesMap.forEach(series => {
    try { chart!.removeSeries(series) } catch {}
  })
  maSeriesMap.clear()

  const cData: CandlestickData[] = props.data.map(d => ({
    time: d.time as any,
    open: d.open,
    high: d.high,
    low: d.low,
    close: d.close,
  } as any))
  pctChangeMap.clear()
  props.data.forEach(d => {
    if (d.pct_change !== undefined) {
      pctChangeMap.set(d.time, d.pct_change)
    }
  })
  candleSeries.setData(cData)

  if (volumeSeries && props.volumeData) {
    volumeSeries.setData(props.volumeData.map(d => ({
      time: d.time as any,
      value: d.value,
      color: d.color,
    })))
  }

  if (props.maData) {
    for (const [name, data] of Object.entries(props.maData)) {
      if (!data || data.length === 0) continue
      const series = chart!.addLineSeries({
        color: maColors[name] || '#888',
        lineWidth: 1,
        priceScaleId: 'right',
        title: name,
        crosshairMarkerVisible: false,
      })
      series.setData(data.map(d => ({ time: d.time as any, value: d.value })))
      maSeriesMap.set(name, series)
    }
  }

  chart.timeScale().fitContent()
  applyRange()
  updateCostLines()
}

function applyRange() {
  if (!chart || !props.data || props.data.length === 0) return
  if (!props.range || props.range === 'All') {
    chart.timeScale().fitContent()
    return
  }
  const data = props.data
  const lastTime = data[data.length - 1].time

  // Calculate range in business days
  const rangeDays: Record<string, number> = {
    '1M': 22,
    '3M': 66,
    '6M': 132,
    '1Y': 252,
  }
  const days = rangeDays[props.range] || 0
  if (days <= 0) {
    chart.timeScale().fitContent()
    return
  }

  const startIdx = Math.max(0, data.length - days - 10) // add buffer
  const fromTime = data[startIdx].time

  try {
    chart.timeScale().setVisibleRange({ from: fromTime as any, to: lastTime as any })
  } catch {
    // fallback: setVisibleRange may fail if range is too small
    chart.timeScale().fitContent()
  }
}

function updateCostLines() {
  if (!chart) return
  const c = chart as any
  priceLines.forEach(pl => c.removePriceLine(pl))
  priceLines = []
  if (!props.costLines) return
  props.costLines.forEach(cl => {
    if (!cl.visible) return
    const pl = c.createPriceLine({
      price: cl.price,
      color: cl.color,
      lineWidth: cl.lineWidth,
      lineStyle: cl.lineStyle as any,
      axisLabelVisible: true,
      title: cl.title,
    })
    priceLines.push(pl)
  })
}

function applyTheme() {
  if (!chart) return
  const theme = getThemeColors()
  chart.applyOptions({
    layout: {
      background: { color: theme.bg },
      textColor: theme.text,
    },
    grid: {
      vertLines: { color: theme.grid },
      horzLines: { color: theme.grid },
    },
    rightPriceScale: { borderColor: theme.border },
    timeScale: { borderColor: theme.border },
  })
}

let themeObserver: MutationObserver | null = null

onMounted(() => {
  initChart()
  if (props.data.length > 0) updateData()

  resizeObserver = new ResizeObserver(() => {
    if (chart && chartContainer.value) {
      chart.applyOptions({ width: chartContainer.value.clientWidth })
    }
  })
  if (chartContainer.value) {
    resizeObserver.observe(chartContainer.value)
  }

  themeObserver = new MutationObserver(() => {
    applyTheme()
  })
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })
})

onUnmounted(() => {
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null }
  if (themeObserver) { themeObserver.disconnect(); themeObserver = null }
  priceLines.forEach(pl => { try { (chart as any)?.removePriceLine(pl) } catch {} })
  priceLines = []
  if (chart) {
    chart.remove()
    chart = null
  }
})

watch(() => props.costLines, updateCostLines, { deep: true })
watch(() => props.data, updateData, { deep: true })
watch(() => props.maData, updateData, { deep: true })
</script>

<style scoped>
.kline-wrapper { position: relative; }
.kline-chart {
  width: 100%;
  height: 460px;
}
.kline-tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  font-size: 11px;
  line-height: 1.6;
  z-index: 10;
  box-shadow: var(--shadow-md);
  min-width: 120px;
  color: var(--claude-text);
  transition: background var(--transition-theme), border-color var(--transition-theme), color var(--transition-theme);
}
.tt-date { font-weight: 600; margin-bottom: 4px; }
.tt-row { display: flex; justify-content: space-between; gap: 12px; }
.tt-val { font-family: var(--font-mono); font-weight: 500; }
.tt-val.up { color: var(--color-up); }
.tt-val.down { color: var(--color-down); }
</style>
