<template>
  <div class="portfolio">
    <el-tabs v-model="mainTab" class="main-tabs">
      <!-- Tab 1: 持仓 -->
      <el-tab-pane label="💼 持仓" name="holdings">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-card v-loading="pageLoading">
              <template #header>
                <div class="card-header">
                  <span>我的持仓</span>
                  <el-button type="primary" size="small" @click="showAddTrade = true">+ 记录交易</el-button>
                </div>
              </template>
              <el-table :data="holdings" style="width:100%" size="small">
                <el-table-column label="股票" min-width="110">
                  <template #default="scope">
                    <div><strong>{{ scope.row.name }}</strong><div class="code stock-code">{{ scope.row.ts_code }}</div></div>
                    <el-tag v-if="scope.row.risk_level==='critical'" type="danger" size="small" style="margin-top:2px">⚠</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="持仓" width="80" align="right">
                  <template #default="scope">
                    <span v-if="editingShares !== scope.row.ts_code" @dblclick="startEditShares(scope.row)" class="shares-val font-number">{{ scope.row.total_shares }}</span>
                    <el-input-number v-else v-model="editSharesVal" :min="1" size="small" style="width:70px" @keyup.enter="saveShares(scope.row)" />
                  </template>
                </el-table-column>
                <el-table-column label="成本" width="65" align="right">
                  <template #default="scope"><span class="price">{{ scope.row.avg_cost?.toFixed(3) }}</span></template>
                </el-table-column>
                <el-table-column label="现价" width="65" align="right">
                  <template #default="scope"><span class="price">{{ scope.row.latest_price?.toFixed(2) }}</span></template>
                </el-table-column>
                <el-table-column label="浮盈" width="100" align="right">
                  <template #default="scope">
                    <div :class="scope.row.unrealized_pnl >= 0 ? 'up' : 'down'">
                      <div class="pnl-pct change">{{ scope.row.unrealized_pnl >= 0 ? '+' : '' }}{{ scope.row.unrealized_pnl_pct?.toFixed(1) }}%</div>
                      <div class="pnl-amt price">{{ formatNumber(scope.row.unrealized_pnl) }}</div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="市值" width="75" align="right">
                  <template #default="scope"><span class="price">{{ formatNumber(scope.row.market_value) }}</span></template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                  <template #default="scope">
                    <el-button size="small" @click="viewDetails(scope.row.ts_code)">详情</el-button>
                    <el-button size="small" type="danger" @click="showSellDialog(scope.row)">卖</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <template #header>
                <div class="card-header"><span>🔔 风险预警</span><el-button size="small" @click="fetchAlerts">刷新</el-button></div>
              </template>
              <div v-if="alerts.length === 0"><el-empty description="暂无未确认预警" /></div>
              <div v-else class="alert-list">
                <div v-for="alert in alerts" :key="alert._id" class="alert-item" :class="alert.alert_level">
                  <div class="alert-title">
                    <el-tag :type="getAlertType(alert.alert_level)" size="small">{{ getAlertLabel(alert.alert_level) }}</el-tag>
                    <span>{{ alert.title }}</span>
                  </div>
                  <div class="alert-desc">{{ alert.description }}</div>
                  <div class="alert-time">{{ formatTime(alert.triggered_at) }}</div>
                  <el-button size="small" @click="ackAlert(alert._id)">确认</el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row style="margin-top: 20px">
          <el-col :span="24">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>📋 持仓事件时间线</span>
                  <el-select v-model="eventFilter" size="small" style="width: 120px">
                    <el-option label="全部" value="all" /><el-option label="未解决" value="unresolved" /><el-option label="严重" value="critical" />
                  </el-select>
                </div>
              </template>
              <el-timeline>
                <el-timeline-item v-for="event in filteredEvents" :key="event._id" :type="getTimelineType(event.severity)" :timestamp="formatDate(event.event_date)">
                  <div class="event-card">
                    <div class="event-header">
                      <el-tag :type="getEventType(event.event_type)" size="small">{{ event.event_type }}</el-tag>
                      <strong>{{ event.name }}</strong>
                    </div>
                    <div class="event-title">{{ event.title }}</div>
                    <div class="event-content">{{ event.content }}</div>
                    <div v-if="event.impact_assessment" class="event-impact">💡 {{ event.impact_assessment }}</div>
                    <div v-if="!event.is_resolved" class="event-unresolved">⚠️ 未解决</div>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Tab 2: 巡检 -->
      <el-tab-pane label="🔍 巡检" name="routine">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-card>
              <template #header><span>选择股票</span></template>
              <el-select v-model="selectedStock" placeholder="选择持仓股票" style="width:100%">
                <el-option v-for="h in holdings" :key="h.ts_code" :label="h.name" :value="h.ts_code" />
              </el-select>
              <el-button type="primary" style="margin-top:12px;width:100%" @click="startInspection" :loading="running" :disabled="!selectedStock">
                🔍 开始巡检
              </el-button>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <template #header><span>步骤进度</span></template>
              <div v-if="runningSteps.length">
                <div v-for="s in runningSteps" :key="s.step_id" class="step-item">
                  <span class="step-icon">{{ s.status === 'success' ? '✅' : s.status === 'running' ? '🔄' : s.status === 'failed' ? '❌' : '⏳' }}</span>
                  <span class="step-name">{{ s.name }}</span>
                  <span class="step-time">{{ s.duration_ms }}ms</span>
                </div>
              </div>
              <el-empty v-else description="尚未执行巡检" />
            </el-card>
          </el-col>
          <el-col :span="10">
            <el-card>
              <template #header>
                <div class="card-header"><span>巡检报告</span>
                  <el-button size="small" v-if="currentReport" @click="downloadReport">导出 .md</el-button>
                </div>
              </template>
              <div v-if="currentReport" class="report-preview" v-html="renderedReport"></div>
              <el-empty v-else description="巡检完成后此处显示报告" />
            </el-card>
            <el-card style="margin-top:12px">
              <template #header><span>历史记录</span></template>
              <el-table :data="routineStore.history" size="small" max-height="200" empty-text="暂无数据">
                <el-table-column prop="created_at" label="时间" width="160">
                  <template #default="s">{{ formatTime(s.row.created_at) }}</template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="s">
                    <el-tag :type="s.row.status === 'completed' ? 'success' : 'warning'" size="small">{{ s.row.status === 'completed' ? '已完成' : s.row.status === 'failed' ? '失败' : '进行中' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="s">
                    <el-button size="small" @click="viewReport(s.row)">查看</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showAddTrade" title="记录交易" width="500px">
      <el-form :model="tradeForm" label-width="100px">
        <el-form-item label="股票代码"><el-input v-model="tradeForm.ts_code" placeholder="如: 600703.SH" /></el-form-item>
        <el-form-item label="股票名称"><el-input v-model="tradeForm.name" /></el-form-item>
        <el-form-item label="操作"><el-radio-group v-model="tradeForm.action"><el-radio-button value="buy">买入</el-radio-button><el-radio-button value="sell">卖出</el-radio-button></el-radio-group></el-form-item>
        <el-form-item label="价格"><el-input-number v-model="tradeForm.price" :precision="3" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="tradeForm.shares" :min="1" /></el-form-item>
        <el-form-item label="交易日期"><el-date-picker v-model="tradeForm.trade_date" type="date" value-format="YYYYMMDD" /></el-form-item>
        <el-form-item label="决策逻辑"><el-input v-model="tradeForm.decision_logic" type="textarea" :rows="3" placeholder="为什么买/卖？必须填写" /></el-form-item>
        <el-form-item label="情绪"><el-select v-model="tradeForm.emotion"><el-option label="冷静" value="calm" /><el-option label="贪婪" value="greedy" /><el-option label="恐惧" value="fearful" /><el-option label="冲动" value="impulsive" /></el-select></el-form-item>
        <el-form-item label="目标价"><el-input-number v-model="tradeForm.target_price" :precision="2" /></el-form-item>
        <el-form-item label="止损价"><el-input-number v-model="tradeForm.stop_loss" :precision="2" /></el-form-item>
        <el-form-item label="标签"><el-select v-model="tradeForm.tags" multiple allow-create placeholder="请选择"><el-option label="追高" value="追高" /><el-option label="PE过高" value="PE过高" /><el-option label="全仓" value="全仓" /><el-option label="超跌" value="超跌" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="showAddTrade = false">取消</el-button><el-button type="primary" @click="submitTrade">确认</el-button></template>
    </el-dialog>

    <PreTradeChecklistModal
      v-model="showChecklist"
      :stock-code="checklistStockCode"
      :stock-name="checklistStockName"
      :current-price="checklistPrice"
      :action="checklistAction"
      @done="onChecklistDone"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { ElMessage } from 'element-plus'
import PreTradeChecklistModal from '@/components/PreTradeChecklistModal.vue'
import { useRoutineStore } from '@/stores/routineStore'

const router = useRouter()
const holdings = ref<any[]>([])
const pageLoading = ref(false)
const pageError = ref('')
const alerts = ref<any[]>([])
const routineStore = useRoutineStore()

const mainTab = ref('holdings')
const showChecklist = ref(false)
const checklistStockCode = ref('')
const checklistStockName = ref('')
const checklistPrice = ref(0)
const checklistAction = ref('BUY')
const editingShares = ref('')
const editSharesVal = ref(0)

const selectedStock = ref('')
const running = ref(false)
const runningSteps = ref<any[]>([])
const currentReport = ref('')
const runningId = ref('')

const renderedReport = computed(() => {
  if (!currentReport.value) return ''
  const translations: Record<string, string> = {
    'flat': '横盘', 'uptrend': '上升趋势', 'downtrend': '下降趋势',
    'bullish': '看多', 'bearish': '看空', 'neutral': '中性',
    'HIGH': '高', 'MEDIUM': '中', 'LOW': '低',
    'high': '高', 'medium': '中', 'low': '低',
  }
  let text = currentReport.value
  for (const [en, zh] of Object.entries(translations)) {
    text = text.replace(new RegExp(`\\b${en}\\b`, 'g'), zh)
  }
  return text
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^- (.+)$/gm, '• $1')
    .replace(/^\s{2}- (.+)$/gm, '  ◦ $1')
    .replace(/\n/g, '<br>')
    .replace(/---/g, '<hr>')
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
})

function startEditShares(row: any) {
  editingShares.value = row.ts_code
  editSharesVal.value = row.total_shares
}
async function saveShares(row: any) {
  try {
    await request.put(`/portfolio/shares/${row.ts_code}`, { shares: editSharesVal.value })
    ElMessage.success('股数已更新')
    editingShares.value = ''
    fetchData()
  } catch { ElMessage.error('更新失败') }
}
const events = ref<any[]>([])
const eventFilter = ref('all')
const showAddTrade = ref(false)

const tradeForm = ref({ ts_code:'', name:'', action:'buy', price:0, shares:0, trade_date:'', decision_logic:'', emotion:'calm', market_view:'', target_price:undefined as any, stop_loss:undefined as any, tags:[] as string[] })

const filteredEvents = computed(() => {
  let list = events.value
  if (eventFilter.value === 'unresolved') list = list.filter((e: any) => !e.is_resolved)
  else if (eventFilter.value === 'critical') list = list.filter((e: any) => e.severity === 'critical')
  return list
})

function getAlertType(l: string) { const m: Record<string,string>={low:'info',medium:'warning',high:'danger',urgent:'danger'}; return m[l]||'info' }
function getAlertLabel(l: string) { const m: Record<string,string>={low:'低',medium:'中',high:'高',urgent:'紧急'}; return m[l]||l }
function getTimelineType(s: string) { const m: Record<string,any>={info:'primary',warning:'warning',critical:'danger'}; return m[s]||'primary' }
function getEventType(t: string) { const m: Record<string,any>={'减持':'danger','增持':'success','冻结':'danger','留置':'danger','大订单':'success','业绩':'warning','监管':'danger','重组':'warning'}; return m[t]||'info' }
function formatNumber(n: number) { if (n == null) return '-'; if (Math.abs(n) >= 10000) return (n/10000).toFixed(2)+'万'; return n.toFixed(2) }
function formatTime(t: string) { return new Date(t).toLocaleString() }
function formatDate(d: string) { if (!d || d.length !== 8) return d; return `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}` }

async function fetchData() {
  pageLoading.value = true
  pageError.value = ''
  try {
  const [h,a,e]: any[] = await Promise.all([request.get('/portfolio/holdings'),request.get('/portfolio/alerts?acknowledged=false'),request.get('/portfolio/events?days=90')])
  holdings.value = h || []; alerts.value = a || []; events.value = e || []
  } catch (e: any) {
    pageError.value = e.message || '加载失败'
  } finally {
    pageLoading.value = false
  }
}
async function ackAlert(id: string) { await request.post(`/portfolio/alerts/${id}/ack`); ElMessage.success('已确认'); fetchAlerts() }
async function fetchAlerts() { const a: any = await request.get('/portfolio/alerts?acknowledged=false'); alerts.value = a || [] }
async function submitTrade() {
  const f = tradeForm.value
  if (!f.ts_code?.trim()) { ElMessage.warning('请填写股票代码'); return }
  if (!f.name?.trim()) { ElMessage.warning('请填写股票名称'); return }
  if (!f.price || f.price <= 0) { ElMessage.warning('请填写有效的价格'); return }
  if (!f.shares || f.shares <= 0) { ElMessage.warning('请填写有效的数量'); return }
  if (!f.decision_logic?.trim()) { ElMessage.warning('请填写决策逻辑'); return }
  await request.post('/portfolio/trades', tradeForm.value); ElMessage.success('已保存'); showAddTrade.value = false; fetchData()
}
function viewDetails(ts_code: string) { router.push({ path:'/stock', query:{ code: ts_code }}) }
function showSellDialog(row: any) { tradeForm.value = { ts_code:row.ts_code, name:row.name, action:'sell', price:row.latest_price, shares:row.total_shares, trade_date:new Date().toISOString().slice(0,10).replace(/-/g,''), decision_logic:'', emotion:'calm', market_view:'', target_price:undefined, stop_loss:undefined, tags:[] }; showAddTrade.value = true }

function onChecklistDone() {
  ElMessage.success('检查通过，可以继续记录交易')
  showAddTrade.value = true
}

async function startInspection() {
  if (!selectedStock.value) return
  running.value = true
  runningSteps.value = []
  currentReport.value = ''
  const stock = holdings.value.find((h: any) => h.ts_code === selectedStock.value)
  try {
    runningId.value = await routineStore.startRoutine('default', selectedStock.value, stock?.name || '')
    let done = false
    let retries = 0
    while (!done && retries < 60) {
      await new Promise(r => setTimeout(r, 1500))
      retries++
      const data: any = await routineStore.pollResult(runningId.value)
      runningSteps.value = data?.steps || []
      if (data?.status === 'completed' || data?.status === 'failed') {
        done = true
        currentReport.value = data?.report || ''
        if (data?.status === 'completed') ElMessage.success('巡检完成')
      }
    }
    if (!done) ElMessage.warning('巡检超时，请稍后查看结果')
    routineStore.loadHistory(selectedStock.value)
  } catch (e) {
    ElMessage.error('巡检失败')
  }
  running.value = false
}

function downloadReport() {
  const blob = new Blob([currentReport.value], { type: 'text/markdown' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `巡检报告_${selectedStock.value}_${new Date().toISOString().slice(0,10)}.md`
  a.click()
}

function viewReport(result: any) {
  currentReport.value = result.report || ''
  runningSteps.value = result.steps || []
}

onMounted(() => { fetchData(); routineStore.loadTemplates() })
</script>

<style scoped>
.main-tabs { margin-bottom: 0; }
.main-tabs :deep(.el-tabs__header) { margin-bottom: 16px; }

.code { font-size: 12px; color: var(--claude-text-secondary); }
.up { color: var(--color-up); } .down { color: var(--color-down); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.warning-count { font-size: 11px; color: var(--claude-accent); margin-top: 2px; }
.alert-list { max-height: 500px; overflow-y: auto; }
.alert-item { padding: 12px; border-bottom: 1px solid var(--claude-border); border-left: 3px solid; }
.alert-item.high { border-left-color: var(--color-up); }
.alert-item.medium { border-left-color: var(--claude-accent); }
.alert-item.low { border-left-color: var(--claude-blue); }
.alert-title { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-family: var(--font-sans); }
.alert-desc { font-size: 13px; color: var(--claude-text-secondary); margin-bottom: 4px; font-family: var(--font-sans); }
.alert-time { font-size: 11px; color: var(--claude-text-secondary); margin-bottom: 8px; }
.event-card { padding: 8px 0; }
.event-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.event-title { font-weight: 600; margin-bottom: 4px; font-family: var(--font-sans); }
.event-content { font-size: 13px; color: var(--claude-text-secondary); margin-bottom: 6px; font-family: var(--font-sans); }
.event-impact { font-size: 12px; color: var(--claude-accent); margin-bottom: 4px; font-family: var(--font-sans); }
.event-unresolved { font-size: 12px; color: var(--color-up); font-family: var(--font-sans); }
.pnl-pct { font-size: 14px; font-weight: 600; }
.pnl-amt { font-size: 11px; opacity: 0.8; }
.shares-val { cursor: pointer; border-bottom: 1px dashed var(--claude-border); }
.shares-val:hover { color: var(--claude-accent); }

/* Routine styles */
.step-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--claude-border); }
.step-icon { font-size: 16px; width: 24px; }
.step-name { flex: 1; font-family: var(--font-sans); }
.step-time { font-size: 12px; color: var(--claude-text-secondary); }
.report-preview { font-size: 13px; line-height: 1.8; max-height: 500px; overflow-y: auto; }
.report-preview h2 { font-size: 17px; margin: 12px 0 6px; font-family: var(--font-sans); }
.report-preview h3 { font-size: 14px; margin: 10px 0 4px; color: var(--claude-accent); font-family: var(--font-sans); }
</style>
