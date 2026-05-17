import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export const useChecklistStore = defineStore('checklist', () => {
  const lastChecklist = ref<Record<string, { timestamp: number; passed: boolean }>>({})

  function isChecklistValid(stockCode: string): boolean {
    const entry = lastChecklist.value[stockCode]
    if (!entry) return false
    const hours = (Date.now() - entry.timestamp) / 3600000
    return entry.passed && hours < 24
  }

  function markPassed(stockCode: string) {
    lastChecklist.value[stockCode] = { timestamp: Date.now(), passed: true }
  }

  async function submitChecklist(data: any) {
    const res: any = await request.post('/checklist/submit', data)
    if (res?.success) {
      markPassed(data.stock_code)
    }
    return res
  }

  async function validateChecklist(data: any) {
    const res: any = await request.post('/checklist/validate', data)
    return res
  }

  return { lastChecklist, isChecklistValid, markPassed, submitChecklist, validateChecklist }
})
