import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStockStore } from '@/stores/stockStore'
import { useWatchlistStore } from '@/stores/watchlistStore'
import request from '@/api/request'
import { ElMessage } from 'element-plus'
import type { QuoteData } from '@/types/stock'
import type { AnalysisResult } from '@/types/analysis'

export function useStockDetail() {
  const route = useRoute()
  const router = useRouter()
  const stockStore = useStockStore()
  const watchlistStore = useWatchlistStore()

  const symbol = computed(() =>
    (route.params.symbol as string) || route.query.code?.toString().split('.')[0] || ''
  )
  const exchange = computed(() =>
    (route.query.exchange as string) || (route.query.code?.toString().split('.')[1] || 'SH')
  )
  const tsCode = computed(() => `${symbol.value}.${exchange.value}`)

  const isIndex = computed(() => ['000001.SH', '399001.SZ', '399006.SZ'].includes(tsCode.value))

  const currentStock = ref<any>(null)  // Local ref for template reactivity
  const loading = ref(false)
  const error = ref('')
  const latestPrice = ref<QuoteData | null>(null)
  const analysis = ref<AnalysisResult | null>(null)
  const events = ref<any[]>([])
  const costLine = ref<Record<string, number> | null>(null)
  const relatedData = ref<Record<string, any>>({})
  const klinePeriod = ref('60')

  // K-line chart data
  function fmtDate(d: string) {
    if (!d || d.length !== 8) return d
    return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
  }

  const chartData = computed(() =>
    stockStore.klineData.map(k => ({
      time: fmtDate(k.trade_date),
      open: k.open,
      high: k.high,
      low: k.low,
      close: k.close,
      pct_change: k.pct_change,
    }))
  )

  const volumeData = computed(() =>
    stockStore.klineData.map((k, i) => ({
      time: fmtDate(k.trade_date),
      value: k.volume,
      color: k.close >= (stockStore.klineData[i - 1]?.close || k.close) ? '#ef5350' : '#26a69a',
    }))
  )

  const maData = computed<Record<string, { time: string; value: number }[]> | undefined>(() => {
    const data = stockStore.klineData
    if (data.length < 5) return undefined
    const calcMa = (period: number) => {
      const result: { time: string; value: number }[] = []
      for (let i = period - 1; i < data.length; i++) {
        const sum = data.slice(i - period + 1, i + 1).reduce((s, k) => s + k.close, 0)
        result.push({ time: fmtDate(data[i].trade_date), value: sum / period })
      }
      return result
    }
    return { MA5: calcMa(5), MA10: calcMa(10), MA20: calcMa(20) }
  })

  const metrics = computed(() => {
    if (!latestPrice.value) return []
    const p = latestPrice.value
    return [
      { label: '开盘', value: (p.open_price ?? p.open)?.toFixed(2) || '--' },
      { label: '最高', value: (p.high_price ?? p.high)?.toFixed(2) || '--', color: 'up' },
      { label: '最低', value: (p.low_price ?? p.low)?.toFixed(2) || '--', color: 'down' },
      { label: '昨收', value: (p.pre_close_price ?? p.pre_close)?.toFixed(2) || '--' },
      { label: '涨跌幅', value: p.pct_change != null ? `${p.pct_change >= 0 ? '+' : ''}${p.pct_change.toFixed(2)}%` : '--', color: (p.pct_change ?? 0) >= 0 ? 'up' : 'down' },
      { label: '成交量', value: formatVol(p.volume) },
      { label: '成交额', value: formatAmt(p.amount) },
    ]
  })

  async function changeKlinePeriod(period: string) {
    klinePeriod.value = period
    await loadKlineData(period)
  }

  /** 计算日期范围 */
  function calcDateRange(days: number) {
    const now = new Date()
    const endDate = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    const startDateObj = new Date()
    startDateObj.setDate(startDateObj.getDate() - days - 10)
    const startDate = `${startDateObj.getFullYear()}${String(startDateObj.getMonth() + 1).padStart(2, '0')}${String(startDateObj.getDate()).padStart(2, '0')}`
    return { startDate, endDate }
  }

  async function loadKlineData(period: string) {
    const days = parseInt(period)
    const { startDate, endDate } = calcDateRange(days)
    // 同时加载 K 线和最新报价
    const results = await Promise.allSettled([
      stockStore.fetchKline(tsCode.value, startDate, endDate),
      request.get(`/quotes/latest/${tsCode.value}`),
    ])
    if (results[1].status === 'fulfilled') {
      latestPrice.value = results[1].value as unknown as QuoteData
    }
  }

  async function loadAll() {
    loading.value = true
    error.value = ''
    try {
      await stockStore.fetchStockDetail(tsCode.value)
      currentStock.value = stockStore.currentStock

      if (isIndex.value) {
        const results = await Promise.allSettled([
          request.get(`/quotes/latest/${tsCode.value}`),
        ])
        if (results[0].status === 'fulfilled') latestPrice.value = results[0].value as unknown as QuoteData
        await loadKlineData(klinePeriod.value)
        return
      }

      const results = await Promise.allSettled([
        request.get(`/quotes/latest/${tsCode.value}`),
        request.get(`/analysis/${tsCode.value}`),
        request.get(`/portfolio/events?ts_code=${tsCode.value}&days=90`),
        request.get(`/portfolio/cost-lines/${tsCode.value}`),
        request.get(`/sector/related/${tsCode.value}`),
      ])

      const [qR, aR, eR, cR, rR] = results
      if (qR.status === 'fulfilled') latestPrice.value = qR.value as unknown as QuoteData
      if (aR.status === 'fulfilled') analysis.value = aR.value as unknown as AnalysisResult
      if (eR.status === 'fulfilled') events.value = (eR.value as unknown as any[]) || []
      if (cR.status === 'fulfilled') costLine.value = cR.value as unknown as Record<string, number> | null
      if (rR.status === 'fulfilled') relatedData.value = (rR.value as unknown as Record<string, any>) || {}

      await loadKlineData(klinePeriod.value)
    } catch (e: any) {
      error.value = e?.message || '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function addToWatchlist() {
    try {
      if (watchlistStore.isInWatchlist(tsCode.value)) {
        await watchlistStore.removeStock(tsCode.value)
        ElMessage.success('已移出自选')
      } else {
        await watchlistStore.addStock(tsCode.value)
        ElMessage.success('已加入自选')
      }
    } catch {
      ElMessage.error('操作失败')
    }
  }

  function goToPortfolio() {
    router.push('/portfolio')
  }

  function navigateToStock(code: string) {
    router.push({ path: '/stock', query: { code } })
  }

  // Auto-load on route change
  // Reset state and reload when route query changes
  watch(() => route.query.code, (newCode) => {
    currentStock.value = null
    stockStore.currentStock = null
    latestPrice.value = null
    analysis.value = null
    events.value = []
    costLine.value = null
    relatedData.value = {}
    if (newCode) loadAll()
  }, { immediate: true })

  if (route.query.code && !currentStock.value && !loading.value) {
    loadAll()
  }

  return {
    symbol,
    exchange,
    tsCode,
    isIndex,
    loading,
    error,
    latestPrice,
    analysis,
    events,
    costLine,
    relatedData,
    klinePeriod,
    chartData,
    volumeData,
    maData,
    metrics,
    changeKlinePeriod,
    loadAll,
    addToWatchlist,
    goToPortfolio,
    navigateToStock,
    currentStock,
  }
}

function formatVol(v: number): string {
  if (!v) return '--'
  if (v > 1e6) return (v / 1e6).toFixed(1) + 'M'
  return (v / 10000).toFixed(1) + '万'
}

function formatAmt(a: number): string {
  if (!a) return '--'
  if (a > 1e8) return (a / 1e8).toFixed(2) + '亿'
  return (a / 10000).toFixed(2) + '万'
}
