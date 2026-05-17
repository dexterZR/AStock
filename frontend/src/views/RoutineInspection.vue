<template>
  <div class="routine-page">
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
          <el-table :data="routineStore.history" size="small" max-height="200">
            <el-table-column prop="created_at" label="时间" width="160"><template #default="s">{{ formatTime(s.row.created_at) }}</template></el-table-column>
            <el-table-column prop="status" label="状态" width="80"><template #default="s"><el-tag :type="s.row.status==='completed'?'success':'warning'" size="small">{{ s.row.status }}</el-tag></template></el-table-column>
            <el-table-column label="操作" width="80"><template #default="s"><el-button size="small" @click="viewReport(s.row)">查看</el-button></template></el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import request from '@/api/request'
import { useRoutineStore } from '@/stores/routineStore'
import { ElMessage } from 'element-plus'

const routineStore = useRoutineStore()
const holdings = ref<any[]>([])
const selectedStock = ref('')
const running = ref(false)
const runningSteps = ref<any[]>([])
const currentReport = ref('')
const runningId = ref('')

const renderedReport = computed(() => {
  if (!currentReport.value) return ''
  return currentReport.value
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^- (.+)$/gm, '• $1')
    .replace(/^\s{2}- (.+)$/gm, '  ◦ $1')
    .replace(/\n/g, '<br>')
    .replace(/---/g, '<hr>')
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
})

function formatTime(t: string) { return new Date(t).toLocaleString() }

async function loadHoldings() {
  const data: any = await request.get('/portfolio/holdings')
  holdings.value = data || []
}

async function startInspection() {
  if (!selectedStock.value) return
  running.value = true
  runningSteps.value = []
  currentReport.value = ''
  const stock = holdings.value.find((h: any) => h.ts_code === selectedStock.value)
  try {
    runningId.value = await routineStore.startRoutine('default', selectedStock.value, stock?.name || '')
    // 轮询直到完成
    let done = false
    while (!done) {
      await new Promise(r => setTimeout(r, 1500))
      const data: any = await routineStore.pollResult(runningId.value)
      runningSteps.value = data?.steps || []
      if (data?.status === 'completed' || data?.status === 'failed') {
        done = true
        currentReport.value = data?.report || ''
        if (data?.status === 'completed') ElMessage.success('巡检完成')
      }
    }
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

onMounted(() => { loadHoldings(); routineStore.loadTemplates() })
</script>

<style scoped>
.step-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--claude-border); }
.step-icon { font-size: 16px; width: 24px; }
.step-name { flex: 1; font-family: var(--font-sans); }
.step-time { font-size: 12px; color: var(--claude-text-secondary); }
.report-preview { font-size: 13px; line-height: 1.8; max-height: 500px; overflow-y: auto; }
.report-preview h2 { font-size: 17px; margin: 12px 0 6px; font-family: var(--font-sans); }
.report-preview h3 { font-size: 14px; margin: 10px 0 4px; color: var(--claude-accent); font-family: var(--font-sans); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
