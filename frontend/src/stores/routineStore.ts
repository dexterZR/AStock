import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export const useRoutineStore = defineStore('routine', () => {
  const templates = ref<any[]>([])
  const currentReport = ref('')
  const history = ref<any[]>([])
  const runningSteps = ref<any[]>([])
  const status = ref('')

  async function loadTemplates() {
    const data: any = await request.get('/routines/templates')
    templates.value = data || []
  }

  async function startRoutine(templateId: string, stockCode: string, stockName: string) {
    const data: any = await request.post('/routines/run', { template_id: templateId, stock_code: stockCode, stock_name: stockName })
    return data?.result_id || ''
  }

  async function pollResult(resultId: string): Promise<any> {
    const data: any = await request.get(`/routines/results/${resultId}`)
    if (data) {
      runningSteps.value = data.steps || []
      status.value = data.status || ''
      currentReport.value = data.report || ''
    }
    return data
  }

  async function loadHistory(stockCode: string) {
    const data: any = await request.get(`/routines/history?stock_code=${stockCode}&limit=10`)
    history.value = data || []
  }

  return { templates, currentReport, history, runningSteps, status, loadTemplates, startRoutine, pollResult, loadHistory }
})
