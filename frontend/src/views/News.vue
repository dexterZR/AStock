<template>
  <div class="news-page">
    <el-row :gutter="16">
      <!-- 左侧：新闻列表 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-hd">
              <span>📰 市场资讯</span>
              <el-select v-model="currentTab" size="small" style="width:120px">
                <el-option label="全部" value="all" />
                <el-option label="热点" value="hot" />
                <el-option label="公告" value="official" />
                <el-option label="研报" value="research" />
                <el-option label="财务" value="financial" />
              </el-select>
            </div>
          </template>
          
          <div v-loading="loading" class="news-list">
            <div v-if="!loading && newsList.length === 0" class="empty-state">
              <el-empty description="暂无相关新闻" :image-size="80" />
            </div>
            
            <div
              v-for="item in newsList"
              :key="item.id"
              class="news-item"
              :class="item.sentiment"
              @click="openNews(item)"
            >
              <div class="news-header">
                <el-tag :type="getNewsTypeColor(item.type)" size="small">
                  {{ getNewsTypeLabel(item.type) }}
                </el-tag>
                <span class="news-time">{{ formatTime(item.pub_date) }}</span>
                <span v-if="item.source" class="news-source">{{ item.source }}</span>
              </div>
              <div class="news-title">{{ item.title }}</div>
              <div class="news-footer">
                <span class="heat-badge">
                  🔥 {{ item.heat_score }}
                </span>
                <span v-if="item.related_stocks?.length" class="related-stocks">
                  相关：{{ item.related_stocks.join('、') }}
                </span>
              </div>
            </div>
          </div>
          
          <div v-if="newsList.length > 0" class="load-more">
            <el-button text @click="loadMore" :loading="loadingMore">
              加载更多
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：热点新闻 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>🔥 热点新闻</span>
          </template>
          <div v-loading="hotLoading" class="hot-list">
            <div
              v-for="(item, index) in hotNews"
              :key="item.id"
              class="hot-item"
              @click="openNews(item)"
            >
              <span class="hot-rank" :class="{ top: index < 3 }">{{ index + 1 }}</span>
              <div class="hot-content">
                <div class="hot-title">{{ item.title }}</div>
                <div class="hot-meta">
                  <span class="hot-score">{{ item.heat_score }}°</span>
                  <span class="hot-time">{{ formatTime(item.pub_date) }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
        
        <el-card style="margin-top:16px">
          <template #header>
            <span>💡 舆情摘要</span>
          </template>
          <div class="sentiment-summary">
            <div class="sentiment-item positive">
              <div class="sentiment-icon">📈</div>
              <div class="sentiment-info">
                <div class="sentiment-count">{{ sentimentStats.positive }}</div>
                <div class="sentiment-label">利好消息</div>
              </div>
            </div>
            <div class="sentiment-item neutral">
              <div class="sentiment-icon">📊</div>
              <div class="sentiment-info">
                <div class="sentiment-count">{{ sentimentStats.neutral }}</div>
                <div class="sentiment-label">中性消息</div>
              </div>
            </div>
            <div class="sentiment-item negative">
              <div class="sentiment-icon">📉</div>
              <div class="sentiment-info">
                <div class="sentiment-count">{{ sentimentStats.negative }}</div>
                <div class="sentiment-label">风险提示</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 新闻详情弹窗 -->
    <el-dialog v-model="showDetail" :title="currentNews?.title" width="700px">
      <div v-if="currentNews" class="news-detail">
        <div class="detail-meta">
          <el-tag :type="getNewsTypeColor(currentNews.type)" size="small">
            {{ getNewsTypeLabel(currentNews.type) }}
          </el-tag>
          <span class="detail-source">{{ currentNews.source }}</span>
          <span class="detail-time">{{ currentNews.pub_date }}</span>
        </div>
        <div class="detail-content">
          <p>{{ currentNews.summary }}</p>
          <p class="detail-tip">（详细内容请访问原文链接）</p>
        </div>
        <div v-if="currentNews.related_stocks?.length" class="detail-stocks">
          <span class="stocks-label">涉及股票：</span>
          <el-tag
            v-for="stock in currentNews.related_stocks"
            :key="stock"
            size="small"
            style="margin-right:8px;cursor:pointer"
            @click="goToStock(stock)"
          >
            {{ stock }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

const loading = ref(false)
const loadingMore = ref(false)
const hotLoading = ref(false)
const newsList = ref<any[]>([])
const hotNews = ref<any[]>([])
const currentTab = ref('all')
const page = ref(1)
const showDetail = ref(false)
const currentNews = ref<any>(null)

const newsTypeMap: Record<string, string> = {
  financial: '财务',
  research: '研报',
  shareholder: '股东',
  business: '经营',
  dividend: '分红',
  product: '产品',
  official: '公告',
  regulatory: '监管',
  corporate: '公司',
}

const sentimentStats = computed(() => {
  const stats = { positive: 0, neutral: 0, negative: 0 }
  newsList.value.forEach(n => {
    if (n.sentiment === 'positive') stats.positive++
    else if (n.sentiment === 'neutral') stats.neutral++
    else if (n.sentiment === 'negative') stats.negative++
  })
  return stats
})

function getNewsTypeLabel(type: string) {
  return newsTypeMap[type] || type
}

function getNewsTypeColor(type: string) {
  const colors: Record<string, string> = {
    financial: 'success',
    research: 'primary',
    shareholder: 'warning',
    business: 'info',
    dividend: 'success',
    product: 'primary',
    official: '',
    regulatory: 'danger',
    corporate: 'info',
  }
  return colors[type] || 'info'
}

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / 3600000)
  
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  return dateStr
}

async function loadNews(reset = false) {
  if (reset) {
    page.value = 1
    newsList.value = []
  }
  
  loading.value = page.value === 1
  
  try {
    const params: any = { limit: 10 }
    if (currentTab.value !== 'all') {
      params.news_type = currentTab.value
    }
    
    const data: any = await request.get('/news/market', { params })
    const newNews = data || []
    
    if (reset) {
      newsList.value = newNews
    } else {
      newsList.value.push(...newNews)
    }
    page.value++
  } catch (e) {
    console.error('加载新闻失败', e)
  } finally {
    loading.value = false
  }
}

async function loadHotNews() {
  hotLoading.value = true
  try {
    const data: any = await request.get('/news/hot', { params: { limit: 8 } })
    hotNews.value = data || []
  } catch (e) {
    console.error('加载热点失败', e)
  } finally {
    hotLoading.value = false
  }
}

async function loadMore() {
  loadingMore.value = true
  await loadNews()
  loadingMore.value = false
}

function openNews(item: any) {
  currentNews.value = item
  showDetail.value = true
}

function goToStock(name: string) {
  showDetail.value = false
  router.push({ path: '/stock', query: { code: name } })
}

watch(currentTab, () => {
  loadNews(true)
  loadHotNews()
})

onMounted(() => {
  loadNews()
  loadHotNews()
})
</script>

<style scoped>
.news-page {
  max-width: 1400px;
}

.card-hd {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  padding: 40px 0;
}

.news-list {
  max-height: 700px;
  overflow-y: auto;
}

.news-item {
  padding: 16px;
  border-bottom: 1px solid var(--claude-border);
  cursor: pointer;
  transition: background 0.15s;
}

.news-item:hover {
  background: var(--claude-bg);
}

.news-item:last-child {
  border-bottom: none;
}

.news-item.positive .news-title { border-left-color: #67c23a; }
.news-item.negative .news-title { border-left-color: #f56c6c; }

.news-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.news-time {
  font-size: 12px;
  color: var(--claude-text-secondary);
}

.news-source {
  font-size: 12px;
  color: var(--claude-text-secondary);
}

.news-title {
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 2px solid var(--claude-accent);
}

.news-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.heat-badge {
  font-size: 12px;
  color: var(--color-up);
  font-weight: 600;
}

.related-stocks {
  font-size: 12px;
  color: var(--claude-text-secondary);
}

.load-more {
  text-align: center;
  padding: 16px;
}

.hot-list {
  max-height: 500px;
  overflow-y: auto;
}

.hot-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--claude-border);
  cursor: pointer;
  transition: background 0.15s;
}

.hot-item:hover {
  background: var(--claude-bg);
}

.hot-item:last-child {
  border-bottom: none;
}

.hot-rank {
  width: 20px;
  height: 20px;
  background: var(--claude-bg);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--claude-text-secondary);
  flex-shrink: 0;
}

.hot-rank.top {
  background: var(--claude-accent);
  color: #fff;
}

.hot-content {
  flex: 1;
  min-width: 0;
}

.hot-title {
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.4;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hot-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hot-score {
  font-size: 11px;
  color: var(--color-up);
  font-weight: 600;
}

.hot-time {
  font-size: 11px;
  color: var(--claude-text-secondary);
}

.sentiment-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sentiment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--claude-bg);
}

.sentiment-icon {
  font-size: 24px;
}

.sentiment-info {
  flex: 1;
}

.sentiment-count {
  font-family: var(--font-display), var(--font-sans);
  font-size: 20px;
  font-weight: 700;
}

.sentiment-label {
  font-family: var(--font-sans);
  font-size: 12px;
  color: var(--claude-text-secondary);
}

.sentiment-item.positive .sentiment-count { color: var(--color-down); }
.sentiment-item.negative .sentiment-count { color: var(--color-up); }

.news-detail {
  line-height: 1.8;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--claude-border);
}

.detail-source, .detail-time {
  font-size: 13px;
  color: var(--claude-text-secondary);
}

.detail-content {
  margin-bottom: 16px;
}

.detail-content p {
  margin-bottom: 12px;
}

.detail-tip {
  font-size: 12px;
  color: var(--claude-text-secondary);
  font-style: italic;
}

.detail-stocks {
  padding-top: 12px;
  border-top: 1px solid var(--claude-border);
}

.stocks-label {
  font-size: 13px;
  color: var(--claude-text-secondary);
}
</style>
