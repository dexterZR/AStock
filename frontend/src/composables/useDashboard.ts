import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import type { MarketOverview, SectorRanking, SectorStock, MarketTemperature } from '@/types/market'
import type { NewsItem, SentimentStats } from '@/types/news'

function logError(context: string, error: unknown) {
  if (import.meta.env.DEV) {
    console.error(`[Dashboard] ${context}:`, error)
  }
}

export function useDashboard() {
  const router = useRouter()

  // Market state
  const overview = ref<MarketOverview | null>(null)
  const overviewLoading = ref(false)
  const extendedOverview = ref<MarketTemperature>({ market_temperature: 0 })
  const sectorRanking = ref<SectorRanking[]>([])
  const selectedSector = ref('')
  const sectorStocks = ref<SectorStock[]>([])
  const sectorTab = ref<'industry' | 'stocks'>('industry')
  const sectorsLoading = ref(false)

  // AI Discussion state
  const discussion = ref<any[]>([])
  const discussing = ref(false)

  // Portfolio mini state
  const portfolio = ref<any[]>([])
  const alerts = ref<any[]>([])

  // News state
  const newsList = ref<NewsItem[]>([])
  const hotNews = ref<NewsItem[]>([])
  const newsTab = ref('all')
  const newsLoading = ref(false)
  const newsLoadingMore = ref(false)
  const hotNewsLoading = ref(false)
  const newsPage = ref(1)
  const hasMoreNews = ref(true)
  const showNewsDetail = ref(false)
  const currentNews = ref<NewsItem | null>(null)

  const alertNews = ref<NewsItem[]>([])
  const alertNewsLoading = ref(false)

  // Computed
  const barUpWidth = computed(() => {
    if (!overview.value) return 50
    const { up_count = 0, down_count = 0, flat_count = 0 } = overview.value
    const total = up_count + down_count + flat_count
    return total > 0 ? Math.round(up_count / total * 100) : 50
  })

  const barDownWidth = computed(() => {
    if (!overview.value) return 50
    const { up_count = 0, down_count = 0, flat_count = 0 } = overview.value
    const total = up_count + down_count + flat_count
    return total > 0 ? Math.round(down_count / total * 100) : 50
  })

  const barFlatWidth = computed(() => {
    if (!overview.value) return 0
    const { flat_count = 0, up_count = 0, down_count = 0 } = overview.value
    const total = up_count + down_count + flat_count
    return total > 0 ? Math.round(flat_count / total * 100) : 0
  })

  const sentimentStats = computed<SentimentStats>(() => {
    const stats: SentimentStats = { positive: 0, neutral: 0, negative: 0 }
    newsList.value.forEach(n => {
      if (n.sentiment === 'positive') stats.positive++
      else if (n.sentiment === 'neutral') stats.neutral++
      else if (n.sentiment === 'negative') stats.negative++
    })
    return stats
  })

  const tempColor = computed(() => {
    const t = extendedOverview.value.market_temperature || 0
    if (t >= 70) return '#67c23a'
    if (t >= 50) return '#e6a23c'
    return '#409eff'
  })

  const tempDesc = computed(() => {
    const t = extendedOverview.value.market_temperature || 0
    if (t >= 80) return '🔥 火热'
    if (t >= 60) return '☀️ 温暖'
    if (t >= 40) return '🌤️ 温和'
    if (t >= 20) return '☁️ 偏冷'
    return '❄️ 冰冻'
  })

  // Actions
  function fmtAmt(n: number) { return n != null ? n.toFixed(1) : '--' }

  async function loadOverview() {
    overviewLoading.value = true
    try {
      const d: any = await request.get('/stocks/overview')
      if (d) overview.value = d
    } catch (e) {
      logError('loadOverview failed', e)
    }
    overviewLoading.value = false
  }

  async function loadSectorRankings() {
    sectorsLoading.value = true
    try {
      const industry: any = await request.get('/sector/ranking')
      sectorRanking.value = industry || []
    } catch (e) {
      logError('sector/ranking failed', e)
    }
    try {
      const extended: any = await request.get('/sector/market-overview-extended')
      extendedOverview.value = extended || { market_temperature: 0 }
    } catch (e) {
      logError('market-overview-extended failed', e)
    }
    sectorsLoading.value = false
  }

  async function selectSector(s: SectorRanking) {
    const sectorName = s.name || s.sector
    if (!sectorName) return
    selectedSector.value = sectorName
    sectorTab.value = 'stocks'
    if (s.all_stocks && s.all_stocks.length > 0) {
      sectorStocks.value = [...s.all_stocks].sort((a, b) => (b.pct_change || 0) - (a.pct_change || 0))
      return
    }
    sectorsLoading.value = true
    try {
      const res: any = await request.get(`/sector/cons/${encodeURIComponent(sectorName)}`)
      sectorStocks.value = (res && Array.isArray(res)) ? res : []
    } catch (e) {
      logError('selectSector failed', e)
      sectorStocks.value = []
    } finally {
      sectorsLoading.value = false
    }
  }

  function autoSelectSector() {
    if (!selectedSector.value && sectorRanking.value.length > 0) {
      selectSector(sectorRanking.value[0])
    }
  }

  async function runDiscussion() {
    discussing.value = true
    discussion.value = []
    try {
      let stocks = portfolio.value.map((p: any) => p.ts_code).filter(Boolean)
      if (!stocks.length) stocks = ['600519.SH', '000001.SZ']
      const codes = stocks.slice(0, 3)
      const res: any = await request.post('/analysis/batch', codes)
      const results = res || []
      const msgs: any[] = []
      for (const r of results.slice(0, 2)) {
        const { technical: tech, fundamental: fund, catalyst } = r
        msgs.push({ role: 'tech', agent: '🔧 技术面Agent', dimension: r.name, content: `${tech?.reasons?.[0] || '无特别信号'}。评分${tech?.score}分，${r.verdict?.summary || ''}` })
        msgs.push({ role: 'fund', agent: '📊 基本面Agent', dimension: r.name, content: `${fund?.reasons?.[0] || '基本面平稳'}。评分${fund?.score}分，${fund?.reasons?.[1] || ''}` })
        msgs.push({ role: 'catalyst', agent: '🚀 催化剂Agent', dimension: r.name, content: `${catalyst?.reasons?.[0] || '暂无催化剂事件'}。评分${catalyst?.score}分` })
        msgs.push({ role: 'verdict', agent: '🎯 综合研判', dimension: r.name, content: `综合评分${r.total_score}分，建议【${r.verdict?.action}】。${r.verdict?.summary || ''}` })
      }
      discussion.value = msgs
    } catch (e) {
      logError('runDiscussion failed', e)
      discussion.value = [{ role: 'error', agent: '系统', dimension: '', content: '讨论生成失败，请稍后重试' }]
    }
    discussing.value = false
  }

  async function loadPortfolio() {
    try {
      const h: any = await request.get('/portfolio/holdings')
      portfolio.value = h || []
    } catch (e) {
      logError('loadPortfolio failed', e)
    }
  }

  async function loadAlerts() {
    try {
      const a: any = await request.get('/portfolio/alerts?acknowledged=false')
      alerts.value = a || []
    } catch (e) {
      logError('loadAlerts failed', e)
    }
  }

  async function loadNews(reset = false) {
    if (reset) {
      newsPage.value = 1
      newsList.value = []
      hasMoreNews.value = true
    }
    newsLoading.value = newsPage.value === 1
    try {
      const params: any = { limit: 10, page: newsPage.value }
      if (newsTab.value !== 'all') params.news_type = newsTab.value
      const data: any = await request.get('/news/market', { params })
      const newNews = (data || []) as NewsItem[]
      if (reset) {
        newsList.value = newNews
      } else {
        const existingIds = new Set(newsList.value.map(n => n.id))
        newsList.value.push(...newNews.filter(n => !existingIds.has(n.id)))
      }
      if (newNews.length >= 10) {
        newsPage.value++
      } else {
        hasMoreNews.value = false
      }
    } catch (e) {
      logError('loadNews failed', e)
    } finally {
      newsLoading.value = false
    }
  }

  async function loadHotNews() {
    hotNewsLoading.value = true
    try {
      const data: any = await request.get('/news/hot', { params: { limit: 8 } })
      hotNews.value = (data || []) as NewsItem[]
    } catch (e) {
      logError('loadHotNews failed', e)
    } finally {
      hotNewsLoading.value = false
    }
  }

  async function loadMoreNews() {
    newsLoadingMore.value = true
    await loadNews()
    newsLoadingMore.value = false
  }

  function openNews(item: NewsItem) {
    currentNews.value = item
    showNewsDetail.value = true
  }

  async function loadAlertNews(tsCode: string) {
    alertNewsLoading.value = true
    alertNews.value = []
    try {
      const data: any = await request.get(`/news/stock/${tsCode}`, { params: { limit: 5 } })
      alertNews.value = (data || []) as NewsItem[]
    } catch (e) {
      logError('loadAlertNews failed', e)
    } finally {
      alertNewsLoading.value = false
    }
  }

  function goToStock(code: string) {
    router.push({ path: '/stock', query: { code } })
  }

  return {
    // Market
    overview, overviewLoading, extendedOverview, sectorRanking, selectedSector, sectorStocks, sectorTab, sectorsLoading,
    barUpWidth, barDownWidth, barFlatWidth, tempColor, tempDesc,
    // Discussion
    discussion, discussing,
    // Portfolio mini
    portfolio, alerts,
    // News
    newsList, hotNews, newsTab, newsLoading, newsLoadingMore, hotNewsLoading, newsPage, hasMoreNews, showNewsDetail, currentNews, sentimentStats,
    alertNews, alertNewsLoading,
    // Actions
    fmtAmt, loadOverview, loadSectorRankings, selectSector, autoSelectSector, runDiscussion,
    loadPortfolio, loadAlerts, loadNews, loadHotNews, loadMoreNews,
    openNews, loadAlertNews, goToStock,
  }
}
