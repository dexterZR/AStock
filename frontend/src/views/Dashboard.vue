<template>
  <div class="dashboard">
    <el-row :gutter="12">
      <el-col :span="8" v-for="idx in marketStore.indices" :key="idx.code">
        <div class="idx-card" @click="goToStock(idx.code)" style="cursor:pointer">
          <div class="idx-top"><span class="idx-name">{{ idx.name }}</span><span class="idx-code stock-code">{{ idx.code }}</span></div>
          <div class="idx-price price">{{ idx.close.toFixed(2) }}</div>
          <div class="idx-bottom">
            <span class="idx-change change" :class="idx.pct_change >= 0 ? 'up' : 'down'">{{ idx.pct_change >= 0 ? '▲' : '▼' }} {{ Math.abs(idx.pct_change).toFixed(2) }}%</span>
            <span class="idx-label">实时</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top:12px">
      <el-col :span="6">
        <el-card class="fill-card">
          <template #header><span>📊 市场情绪</span></template>
          <div v-loading="overviewLoading">
            <div v-if="overview" class="stat-grid">
              <div class="stat-item"><span class="stat-num font-number up">{{ overview.up_count || 0 }}</span><span class="stat-label">上涨</span></div>
              <div class="stat-item"><span class="stat-num font-number down">{{ overview.down_count || 0 }}</span><span class="stat-label">下跌</span></div>
              <div class="stat-item"><span class="stat-num font-number up">{{ overview.limit_up_count || 0 }}</span><span class="stat-label">涨停</span></div>
              <div class="stat-item"><span class="stat-num font-number down">{{ overview.limit_down_count || 0 }}</span><span class="stat-label">跌停</span></div>
            </div>
            <div v-if="overview" class="up-down-bar">
              <div class="bar-up" :style="{width: barUpWidth + '%'}">{{ overview.up_count || 0 }}</div>
              <div class="bar-flat" :style="{width: barFlatWidth + '%'}"></div>
              <div class="bar-down" :style="{width: barDownWidth + '%'}">{{ overview.down_count || 0 }}</div>
            </div>
          </div>
          <div v-if="extendedOverview.market_temperature != null" class="temp-box">
            <div class="temp-label">🌡️ 市场温度</div>
            <el-progress :percentage="Math.round(extendedOverview.market_temperature)" :color="tempColor" :stroke-width="8" />
            <div class="temp-desc">{{ tempDesc }}</div>
          </div>
        </el-card>
        <el-card class="fill-card" style="margin-top:12px">
          <template #header><span>💼 持仓</span></template>
          <div v-if="portfolio.length" class="port-mini">
            <div v-for="p in portfolio" :key="p.ts_code" class="port-row" @click="goToStock(p.ts_code)">
              <span class="port-name">{{ p.name }}</span>
              <span class="port-price">{{ p.latest_price?.toFixed(2) }}</span>
              <span class="port-pnl change" :class="p.pct_change >= 0 ? 'up' : 'down'">{{ p.pct_change >= 0 ? '+' : '' }}{{ p.pct_change?.toFixed(2) }}%</span>
            </div>
          </div>
          <el-empty v-else description="暂无持仓" :image-size="36" />
        </el-card>
        <el-card class="fill-card" style="margin-top:12px">
          <template #header>
            <div class="card-hd">
              <span>🔔 预警</span>
              <el-tag v-if="alerts.length" size="small" type="danger">{{ alerts.length }}</el-tag>
            </div>
          </template>
          <div v-if="alerts.length" class="alert-mini">
            <div v-for="a in displayAlerts" :key="a._id" class="alert-line" :class="a.alert_level" @click="openAlert(a)">
              <span class="alert-lvl">{{ a.alert_level === 'high' ? '🔴' : '🟡' }}</span>
              <span class="alert-txt">{{ a.title }}</span>
              <span class="alert-arrow">›</span>
            </div>
            <div v-if="!alertsExpanded && alerts.length > 5" class="load-more">
              <el-button text size="small" @click="alertsExpanded = true">展开更多 ({{ alerts.length - 5 }} 条)</el-button>
            </div>
          </div>
          <el-empty v-else description="暂无预警" :image-size="36" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <AgentDiscussion
          :messages="discussion"
          :discussing="discussing"
          @refresh="runDiscussion"
        />
        <SectorRanking
          :sectors="sectorRanking"
          :stocks="sectorStocks"
          :tab="sectorTab"
          :selected-sector="selectedSector"
          :loading="sectorsLoading"
          @update:tab="sectorTab = $event"
          @select="selectSector"
          @go-stock="goToStock"
          @auto-select="autoSelectSector"
          style="margin-top:12px"
        />
      </el-col>

      <el-col :span="6">
        <el-card class="fill-card">
          <template #header>
            <div class="card-hd">
              <span>🤖 AI精选</span>
              <el-tag size="small" type="danger" v-if="recommendedNews.length">推荐 {{ recommendedNews.length }}</el-tag>
            </div>
          </template>
          <div v-loading="newsLoading" class="ai-news-list">
            <div v-if="!newsLoading && recommendedNews.length === 0 && newsList.length === 0" class="empty-state">
              <el-empty description="暂无新闻" :image-size="60" />
            </div>
            <div v-for="item in recommendedNews" :key="item.id" class="ai-news-item recommended" @click="openNews(item)">
              <div class="ai-news-header">
                <el-tag size="small" type="danger" effect="dark">AI推荐</el-tag>
                <span class="ai-value-score">价值分 {{ item.value_score }}/10</span>
                <span class="ai-action-hint" :class="item.action_hint === '利好' ? 'up' : item.action_hint === '利空' ? 'down' : ''">{{ item.action_hint }}</span>
              </div>
              <div class="ai-news-title">{{ item.title }}</div>
              <div v-if="item.ai_brief" class="ai-brief">💡 {{ item.ai_brief }}</div>
              <div class="ai-news-footer">
                <span class="news-time">{{ formatNewsTime(item.pub_date) }}</span>
                <span v-if="item.source" class="news-source">{{ item.source }}</span>
                <span v-if="item.affected_sectors?.length" class="affected-sectors">影响：{{ item.affected_sectors.slice(0, 3).join('、') }}</span>
              </div>
            </div>
            <div v-for="item in normalNews" :key="item.id" class="ai-news-item" @click="openNews(item)">
              <div class="ai-news-header">
                <el-tag :type="getNewsTypeColor(item.type)" size="small">{{ getNewsTypeLabel(item.type) }}</el-tag>
                <span class="news-time">{{ formatNewsTime(item.pub_date) }}</span>
                <span v-if="item.source" class="news-source">{{ item.source }}</span>
              </div>
              <div class="ai-news-title">{{ item.title }}</div>
            </div>
          </div>
          <div v-if="!aiNewsExpanded && newsList.filter(n => !n.ai_recommended).length > 6" class="load-more">
            <el-button text size="small" @click="aiNewsExpanded = true">展开更多</el-button>
          </div>
          <div v-else-if="hasMoreNews" class="load-more">
            <el-button text size="small" @click="loadMoreNews" :loading="newsLoadingMore">加载更多</el-button>
          </div>
        </el-card>
        <el-card class="fill-card" style="margin-top:12px">
          <template #header>
            <div class="card-hd">
              <span>📰 资讯</span>
              <el-select v-model="newsTab" size="small" style="width:90px">
                <el-option label="全部" value="all" />
                <el-option label="AI推荐" value="recommended" />
                <el-option label="公告" value="official" />
                <el-option label="研报" value="research" />
                <el-option label="财务" value="financial" />
              </el-select>
            </div>
          </template>
          <div v-loading="newsLoading" class="news-list">
            <div v-for="item in displayNewsList" :key="item.id" class="news-item" :class="item.sentiment" @click="openNews(item)">
              <div class="news-header">
                <el-tag v-if="item.ai_recommended" size="small" type="danger" effect="dark">AI推荐</el-tag>
                <el-tag :type="getNewsTypeColor(item.type)" size="small">{{ getNewsTypeLabel(item.type) }}</el-tag>
                <span class="news-time">{{ formatNewsTime(item.pub_date) }}</span>
                <span v-if="item.value_score" class="value-badge">⭐{{ item.value_score }}</span>
              </div>
              <div class="news-title">{{ item.title }}</div>
              <div v-if="item.ai_brief" class="news-ai-brief">💡 {{ item.ai_brief }}</div>
              <div class="news-footer">
                <span class="heat-badge">🔥 {{ item.heat_score }}</span>
                <span v-if="item.affected_sectors?.length" class="affected-sectors">影响：{{ item.affected_sectors.slice(0, 3).join('、') }}</span>
                <span v-if="item.related_stocks?.length" class="related-stocks">相关：{{ item.related_stocks.join('、') }}</span>
              </div>
            </div>
          </div>
          <div v-if="hasMoreNews" class="load-more">
            <el-button text @click="loadMoreNews" :loading="newsLoadingMore">加载更多</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="data-timestamp" v-if="overview">
      📡 数据日期：{{ formatTradeDate(overview.trade_date) }} · 共 {{ overview.total_stocks }} 只股票
    </div>

    <el-dialog v-model="showNewsDetail" :title="currentNews?.title" width="700px">
      <div v-if="currentNews" class="news-detail">
        <div class="detail-meta">
          <el-tag v-if="currentNews.ai_recommended" size="small" type="danger" effect="dark">AI推荐</el-tag>
          <el-tag :type="getNewsTypeColor(currentNews.type)" size="small">{{ getNewsTypeLabel(currentNews.type) }}</el-tag>
          <span class="detail-source">{{ currentNews.source }}</span>
          <span class="detail-time">{{ currentNews.pub_date }}</span>
          <span v-if="currentNews.value_score" class="value-badge">⭐ 价值分 {{ currentNews.value_score }}/10</span>
        </div>
        <div v-if="currentNews.ai_brief" class="detail-ai-brief">
          <span class="ai-label">🤖 AI点评：</span>{{ currentNews.ai_brief }}
          <span v-if="currentNews.action_hint" class="action-hint" :class="currentNews.action_hint === '利好' ? 'up' : currentNews.action_hint === '利空' ? 'down' : ''">{{ currentNews.action_hint }}</span>
        </div>
        <div v-if="currentNews.affected_sectors?.length" class="detail-sectors">
          <span class="sectors-label">影响板块：</span>
          <el-tag v-for="s in currentNews.affected_sectors" :key="s" size="small" style="margin-right:6px">{{ s }}</el-tag>
        </div>
        <div class="detail-content">
          <p>{{ currentNews.summary }}</p>
        </div>
        <div v-if="currentNews.url" class="detail-link">
          <el-button type="primary" size="small" @click="openNewsUrl(currentNews.url!)">🔗 查看原文</el-button>
        </div>
        <div v-else class="detail-content">
          <p class="detail-tip">（详细内容请访问原文来源）</p>
        </div>
        <div v-if="currentNews.related_stocks?.length" class="detail-stocks">
          <span class="stocks-label">涉及股票：</span>
          <el-tag v-for="stock in currentNews.related_stocks" :key="stock" size="small" style="margin-right:8px;cursor:pointer" @click="goToStockByName(stock)">{{ stock }}</el-tag>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showAlertDetail" :title="currentAlert?.title" width="620px">
      <div v-if="currentAlert" class="alert-detail">
        <div class="alert-detail-meta">
          <el-tag :type="currentAlert.alert_level === 'high' ? 'danger' : 'warning'" effect="dark" size="small">{{ currentAlert.alert_level === 'high' ? '高风险' : '中风险' }}</el-tag>
          <span class="alert-detail-stock" @click="goToStock(currentAlert.ts_code); showAlertDetail = false" style="cursor:pointer;color:var(--claude-accent)">{{ currentAlert.name }}（{{ currentAlert.ts_code }}）</span>
          <span class="alert-detail-time">{{ currentAlert.triggered_at }}</span>
        </div>
        <div v-if="currentAlert.source" class="alert-detail-source">
          <span class="source-label">📰 来源：</span>
          <span class="source-name">{{ currentAlert.source }}</span>
        </div>
        <div class="alert-detail-desc">{{ currentAlert.description }}</div>
        <div v-if="alertNewsLoading" class="alert-news-loading">
          <el-icon class="is-loading"><Loading /></el-icon> 加载相关新闻...
        </div>
        <div v-else-if="alertNews.length" class="alert-detail-news">
          <div class="alert-news-header">📄 相关新闻</div>
          <div v-for="n in alertNews" :key="n.id" class="alert-news-item" @click="openNews(n); showAlertDetail = false">
            <div class="alert-news-title">{{ n.title }}</div>
            <div class="alert-news-meta">
              <span v-if="n.source" class="alert-news-source">{{ n.source }}</span>
              <span class="alert-news-time">{{ formatNewsTime(n.pub_date) }}</span>
              <el-tag v-if="n.ai_recommended" size="small" type="danger" effect="dark">AI推荐</el-tag>
              <span v-if="n.value_score" class="value-badge">⭐{{ n.value_score }}</span>
            </div>
          </div>
        </div>
        <div class="alert-detail-actions">
          <el-button type="primary" size="small" @click="goToStock(currentAlert.ts_code); showAlertDetail = false">查看股票</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { useDashboard } from '@/composables/useDashboard'
import { useMarketStore } from '@/stores/marketStore'
import AgentDiscussion from '@/components/dashboard/AgentDiscussion.vue'
import SectorRanking from '@/components/dashboard/SectorRanking.vue'
const marketStore = useMarketStore()
const router = useRouter()

const {
  overview, overviewLoading, extendedOverview, sectorRanking, selectedSector, sectorStocks, sectorTab, sectorsLoading,
  barUpWidth, barDownWidth, barFlatWidth, tempColor, tempDesc,
  discussion, discussing,
  portfolio, alerts,
  newsList, newsTab, newsLoading, newsLoadingMore, showNewsDetail, currentNews, hasMoreNews,
  alertNews, alertNewsLoading,
  loadPortfolio, loadAlerts, loadNews, loadHotNews, loadMoreNews,
  openNews, loadAlertNews, goToStock, loadOverview, loadSectorRankings, selectSector, autoSelectSector, runDiscussion,
} = useDashboard()

const newsTypeMap: Record<string, string> = {
  financial: '财务', research: '研报', shareholder: '股东', business: '经营',
  dividend: '分红', product: '产品', official: '公告', regulatory: '监管', corporate: '公司',
}

function getNewsTypeLabel(type: string) { return newsTypeMap[type] || type }
function getNewsTypeColor(type: string) {
  const colors: Record<string, string> = { financial:'success', research:'primary', shareholder:'warning', business:'info', dividend:'success', product:'primary', official:'', regulatory:'danger', corporate:'info' }
  return colors[type] || 'info'
}

const recommendedNews = computed(() => newsList.value.filter(n => n.ai_recommended))
const normalNews = computed(() => {
  const items = newsList.value.filter(n => !n.ai_recommended)
  return aiNewsExpanded.value ? items : items.slice(0, 6)
})
const aiNewsExpanded = ref(false)
const alertsExpanded = ref(false)
const showAlertDetail = ref(false)
const currentAlert = ref<any>(null)

const displayAlerts = computed(() => {
  if (alertsExpanded.value) return alerts.value
  return alerts.value.slice(0, 5)
})

function openAlert(a: any) {
  currentAlert.value = a
  showAlertDetail.value = true
  if (a.ts_code) loadAlertNews(a.ts_code)
}
const displayNewsList = computed(() => {
  if (newsTab.value === 'recommended') return newsList.value.filter(n => n.ai_recommended)
  return newsList.value
})

function goToStockByName(name: string) {
  showNewsDetail.value = false
  router.push({ path: '/stock', query: { code: name } })
}

function openNewsUrl(url: string) {
  window.open(url, '_blank')
}

function formatNewsTime(dateStr: string) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  return dateStr.slice(5, 16)
}

function formatTradeDate(dateStr: string) {
  if (!dateStr) return '未知'
  const s = String(dateStr)
  if (s.length === 8) return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`
  return s.slice(0, 10)
}

watch(newsTab, () => { loadNews(true); loadHotNews() })

let _refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  marketStore.fetchMarketOverview()
  loadOverview()
  loadSectorRankings()
  loadPortfolio()
  loadAlerts()
  loadNews()
  loadHotNews()
  setTimeout(() => runDiscussion(), 500)
  _refreshTimer = setInterval(() => {
    loadAlerts()
    loadPortfolio()
  }, 60000)
})

onUnmounted(() => {
  if (_refreshTimer) {
    clearInterval(_refreshTimer)
    _refreshTimer = null
  }
})
</script>

<style scoped>
.idx-card { background:var(--claude-card); border:1px solid var(--claude-border); border-radius:var(--radius-md); padding:16px 18px; transition:transform 0.2s,box-shadow 0.2s; }
.idx-card:hover { transform:translateY(-2px); box-shadow:0 4px 16px rgba(0,0,0,0.06); border-left:3px solid var(--claude-accent); }
.idx-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.idx-name { font-size:13px; font-weight:600; font-family:var(--font-sans); }
.idx-code { font-size:11px; color:var(--claude-text-secondary); font-family:monospace; }
.idx-price { font-size:28px; font-weight:800; letter-spacing:-0.02em; margin-bottom:4px; font-family:var(--font-display); }
.idx-bottom { display:flex; justify-content:space-between; align-items:center; }
.idx-change { font-size:14px; font-weight:600; }
.idx-label { font-size:11px; color:var(--claude-text-secondary); }
.up { color:var(--color-up); }
.down { color:var(--color-down); }

.fill-card :deep(.el-card__body) { flex:1; display:flex; flex-direction:column; }

.stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:var(--space-2); }
.stat-item { text-align:center; padding:6px; border-radius:var(--radius-sm); }
.stat-num { font-size:16px; font-weight:700; display:block; font-family:var(--font-display); }
.stat-label { font-size:10px; color:var(--claude-text-secondary); margin-top:1px; }

.temp-box { margin-top:10px; padding-top:10px; border-top:1px solid var(--claude-border); }
.temp-label { font-size:11px; color:var(--claude-text-secondary); margin-bottom:4px; }
.temp-desc { font-size:10px; color:var(--claude-text-secondary); margin-top:3px; text-align:center; }

.up-down-bar { display:flex; height:18px; border-radius:4px; overflow:hidden; margin-top:8px; font-size:10px; font-weight:600; color:#fff; line-height:18px; text-align:center; }
.bar-up { background:var(--color-up); transition:width 0.5s; min-width:20px; }
.bar-flat { background:var(--claude-border); transition:width 0.5s; }
.bar-down { background:var(--color-down); transition:width 0.5s; min-width:20px; }

.card-hd { display:flex; justify-content:space-between; align-items:center; }

.port-mini { max-height:160px; overflow-y:auto; }
.port-row { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid var(--claude-border); cursor:pointer; font-size:12px; }
.port-row:hover { background:var(--claude-accent-light); }
.port-name { font-weight:500; flex:1; }
.port-price { color:var(--claude-text-secondary); margin-right:8px; }
.port-pnl { font-weight:600; min-width:60px; text-align:right; }

.alert-mini { max-height:160px; overflow-y:auto; }
.alert-line { display:flex; align-items:center; gap:6px; padding:5px 0; border-bottom:1px solid var(--claude-border); font-size:12px; cursor:pointer; }
.alert-line:hover { background:var(--claude-accent-light); }
.alert-lvl { font-size:14px; }
.alert-txt { flex:1; line-height:1.4; }
.alert-arrow { color:var(--claude-text-secondary); font-size:16px; }

.alert-detail-meta { display:flex; align-items:center; gap:10px; margin-bottom:16px; flex-wrap:wrap; }
.alert-detail-stock { font-weight:600; font-size:14px; }
.alert-detail-time { font-size:12px; color:var(--claude-text-secondary); }
.alert-detail-desc { font-size:14px; line-height:1.8; padding:12px 16px; background:var(--claude-bg); border-radius:8px; margin-bottom:16px; }
.alert-detail-source { display:flex; align-items:center; gap:4px; margin-bottom:12px; font-size:13px; }
.source-label { color:var(--claude-text-secondary); }
.source-name { font-weight:600; color:var(--claude-accent); }
.alert-news-loading { text-align:center; padding:16px; color:var(--claude-text-secondary); font-size:13px; }
.alert-detail-news { margin-bottom:16px; }
.alert-news-header { font-size:13px; font-weight:600; margin-bottom:8px; color:var(--claude-text-secondary); }
.alert-news-item { padding:10px 12px; border:1px solid var(--claude-border); border-radius:6px; margin-bottom:8px; cursor:pointer; transition:background 0.15s; }
.alert-news-item:hover { background:var(--claude-accent-light); }
.alert-news-title { font-size:13px; font-weight:500; line-height:1.5; margin-bottom:4px; }
.alert-news-meta { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.alert-news-source { font-size:11px; color:var(--claude-accent); font-weight:500; }
.alert-news-time { font-size:11px; color:var(--claude-text-secondary); }
.alert-detail-actions { text-align:right; }

.ai-news-list { max-height:320px; overflow-y:auto; }
.ai-news-item { padding:10px; border-bottom:1px solid var(--claude-border); cursor:pointer; transition:background 0.15s; }
.ai-news-item:hover { background:var(--claude-accent-light); }
.ai-news-item:last-child { border-bottom:none; }
.ai-news-item.recommended { background:rgba(245,108,108,0.04); border-left:3px solid #f56c6c; }
.ai-news-item.recommended:hover { background:rgba(245,108,108,0.08); }
.ai-news-header { display:flex; align-items:center; gap:6px; margin-bottom:4px; flex-wrap:wrap; }
.ai-value-score { font-size:11px; color:#e6a23c; font-weight:600; }
.ai-action-hint { font-size:11px; font-weight:600; padding:1px 6px; border-radius:3px; background:var(--claude-bg); }
.ai-news-title { font-size:13px; font-weight:500; line-height:1.5; margin-bottom:4px; font-family:var(--font-sans); }
.ai-brief { font-size:12px; color:#e6a23c; line-height:1.4; margin-bottom:4px; padding:4px 8px; background:rgba(230,162,60,0.06); border-radius:4px; }
.ai-news-footer { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.affected-sectors { font-size:11px; color:var(--claude-accent); }

.news-list { max-height:400px; overflow-y:auto; }
.news-item { padding:10px; border-bottom:1px solid var(--claude-border); cursor:pointer; transition:background 0.15s; }
.news-item:hover { background:var(--claude-accent-light); }
.news-item:last-child { border-bottom:none; }
.news-header { display:flex; align-items:center; gap:6px; margin-bottom:4px; flex-wrap:wrap; }
.news-time, .news-source { font-size:11px; color:var(--claude-text-secondary); }
.news-title { font-size:13px; font-weight:500; line-height:1.5; margin-bottom:4px; padding-left:8px; border-left:2px solid var(--claude-accent); font-family:var(--font-sans); }
.news-ai-brief { font-size:12px; color:#e6a23c; line-height:1.4; margin-bottom:4px; padding-left:8px; }
.news-footer { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.heat-badge { font-size:11px; color:var(--color-up); font-weight:600; }
.related-stocks { font-size:11px; color:var(--claude-text-secondary); }
.value-badge { font-size:11px; color:#e6a23c; font-weight:600; }
.load-more { text-align:center; padding:10px; }
.empty-state { padding:30px 0; }

.news-detail { line-height:1.8; }
.detail-meta { display:flex; align-items:center; gap:10px; margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid var(--claude-border); flex-wrap:wrap; }
.detail-source, .detail-time { font-size:12px; color:var(--claude-text-secondary); }
.detail-ai-brief { padding:10px 12px; background:rgba(230,162,60,0.06); border-radius:6px; margin-bottom:12px; font-size:14px; line-height:1.6; }
.ai-label { font-weight:600; color:#e6a23c; }
.action-hint { font-size:12px; font-weight:600; margin-left:8px; padding:1px 8px; border-radius:3px; background:var(--claude-bg); }
.detail-sectors { margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid var(--claude-border); }
.sectors-label { font-size:12px; color:var(--claude-text-secondary); margin-right:6px; }
.detail-content { margin-bottom:12px; }
.detail-content p { margin-bottom:10px; font-size:14px; }
.detail-tip { font-size:11px; color:var(--claude-text-secondary); font-style:italic; }
.detail-link { margin-bottom:12px; }
.detail-stocks { padding-top:10px; border-top:1px solid var(--claude-border); }
.stocks-label { font-size:12px; color:var(--claude-text-secondary); }

.data-timestamp {
  text-align:center;
  padding:12px 0 6px;
  font-size:var(--text-xs);
  color:var(--claude-text-tertiary);
}
</style>
