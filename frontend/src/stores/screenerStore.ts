import { defineStore } from 'pinia'
import { ref } from 'vue'
import { screenerApi } from '@/api/modules/screener'
import type { ScreenerCondition, ScreenerResult, StrategyTemplate, ViewMode, AIDailyRecommendation } from '@/types/screener'

export const useScreenerStore = defineStore('screener', () => {
  const conditions = ref<ScreenerCondition[]>([])
  const results = ref<ScreenerResult[]>([])
  const templates = ref<StrategyTemplate[]>([])
  const loading = ref(false)
  const viewMode = ref<ViewMode>('table')
  const aiDaily = ref<AIDailyRecommendation | null>(null)
  const aiExplanation = ref('')
  const aiSource = ref<'llm' | 'keyword'>('keyword')
  const aiParsedConditions = ref<ScreenerCondition[]>([])
  const aiMatchedIndustries = ref<string[]>([])
  const aiMatchedIndustryGroups = ref<string[]>([])

  function clearAIState() {
    aiExplanation.value = ''
    aiSource.value = 'keyword'
    aiParsedConditions.value = []
    aiMatchedIndustries.value = []
    aiMatchedIndustryGroups.value = []
  }

  async function executeScreener() {
    loading.value = true
    try {
      const data: any = await screenerApi.screen(conditions.value)
      results.value = (data || []).sort((a: any, b: any) => (b.pct_change || 0) - (a.pct_change || 0))
    } catch {
      results.value = []
    } finally {
      loading.value = false
    }
  }

  async function loadTemplates() {
    try {
      const data: any = await screenerApi.getTemplates()
      templates.value = data || []
    } catch {
      templates.value = []
    }
  }

  async function loadAIDaily() {
    try {
      const data: any = await screenerApi.aiDaily()
      aiDaily.value = data || null
    } catch {
      aiDaily.value = null
    }
  }

  function applyTemplate(template: StrategyTemplate) {
    if (template.conditions && template.conditions.length > 0) {
      conditions.value = [...template.conditions]
    }
  }

  function addCondition(condition: ScreenerCondition) {
    conditions.value.push(condition)
  }

  function removeCondition(index: number) {
    conditions.value.splice(index, 1)
  }

  function clearConditions() {
    conditions.value = []
  }

  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
  }

  return {
    conditions, results, templates, loading, viewMode, aiDaily, aiExplanation, aiSource, aiParsedConditions, aiMatchedIndustries, aiMatchedIndustryGroups,
    executeScreener, loadTemplates, loadAIDaily, clearAIState,
    applyTemplate, addCondition, removeCondition, clearConditions, setViewMode,
  }
})
