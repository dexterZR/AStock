import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useScreenerStore } from '@/stores/screenerStore'
import type { ScreenerCondition, StrategyTemplate } from '@/types/screener'

vi.mock('@/api/modules/screener', () => ({
  screenerApi: {
    screen: vi.fn(),
    getTemplates: vi.fn(),
    aiDaily: vi.fn(),
  },
}))

import { screenerApi } from '@/api/modules/screener'

describe('useScreenerStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial state', () => {
    const store = useScreenerStore()
    expect(store.conditions).toEqual([])
    expect(store.results).toEqual([])
    expect(store.templates).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.viewMode).toBe('table')
  })

  it('addCondition', () => {
    const store = useScreenerStore()
    const condition: ScreenerCondition = {
      category: 'fundamental',
      field: 'pe',
      op: 'range',
      min: 5,
      max: 30,
    }
    store.addCondition(condition)
    expect(store.conditions).toHaveLength(1)
    expect(store.conditions[0].field).toBe('pe')
  })

  it('removeCondition', () => {
    const store = useScreenerStore()
    store.addCondition({ category: 'fundamental', field: 'pe', op: 'range', min: 5, max: 30 })
    store.addCondition({ category: 'technical', field: 'macd_cross', op: 'eq', value: true })
    store.removeCondition(0)
    expect(store.conditions).toHaveLength(1)
    expect(store.conditions[0].field).toBe('macd_cross')
  })

  it('clearConditions', () => {
    const store = useScreenerStore()
    store.addCondition({ category: 'fundamental', field: 'pe', op: 'range', min: 5, max: 30 })
    store.clearConditions()
    expect(store.conditions).toEqual([])
  })

  it('setViewMode', () => {
    const store = useScreenerStore()
    store.setViewMode('cards')
    expect(store.viewMode).toBe('cards')
    store.setViewMode('heatmap')
    expect(store.viewMode).toBe('heatmap')
  })

  it('applyTemplate', () => {
    const store = useScreenerStore()
    const template: StrategyTemplate = {
      id: 'breakout',
      name: '突破策略',
      icon: '🚀',
      description: '突破20日新高',
      conditions: [
        { category: 'pattern', field: 'breakout_20d_high', op: 'eq', value: true },
        { category: 'fundamental', field: 'pe', op: 'range', min: 0, max: 50 },
      ],
    }
    store.applyTemplate(template)
    expect(store.conditions).toHaveLength(2)
    expect(store.conditions[0].field).toBe('breakout_20d_high')
  })

  it('applyTemplate with empty conditions does not clear', () => {
    const store = useScreenerStore()
    store.addCondition({ category: 'technical', field: 'macd_cross', op: 'eq', value: true })
    store.applyTemplate({ id: 'empty', name: '', icon: '', description: '', conditions: [] })
    expect(store.conditions).toHaveLength(1)
  })

  it('clearAIState', () => {
    const store = useScreenerStore()
    store.aiExplanation = 'test explanation'
    store.aiSource = 'llm'
    store.aiParsedConditions = [{ category: 'technical', field: 'rsi_oversold', op: 'eq', value: true }]
    store.aiMatchedIndustries = ['银行']
    store.clearAIState()
    expect(store.aiExplanation).toBe('')
    expect(store.aiSource).toBe('keyword')
    expect(store.aiParsedConditions).toEqual([])
    expect(store.aiMatchedIndustries).toEqual([])
  })

  it('executeScreener success', async () => {
    const mockResults = [
      { ts_code: '000001.SZ', name: '平安银行', pct_change: 3.5 },
      { ts_code: '600519.SH', name: '贵州茅台', pct_change: -1.2 },
    ]
    vi.mocked(screenerApi.screen).mockResolvedValue(mockResults as any)
    const store = useScreenerStore()
    store.addCondition({ category: 'fundamental', field: 'pe', op: 'range', min: 5, max: 30 })
    await store.executeScreener()
    expect(store.results).toHaveLength(2)
    expect(store.results[0].pct_change).toBe(3.5)
    expect(store.loading).toBe(false)
  })

  it('executeScreener failure clears results', async () => {
    vi.mocked(screenerApi.screen).mockRejectedValue(new Error('Network error'))
    const store = useScreenerStore()
    await store.executeScreener()
    expect(store.results).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('loadTemplates success', async () => {
    const mockTemplates = [
      { id: '1', name: '策略1', icon: '📊', description: 'desc', conditions: [] },
    ]
    vi.mocked(screenerApi.getTemplates).mockResolvedValue(mockTemplates as any)
    const store = useScreenerStore()
    await store.loadTemplates()
    expect(store.templates).toHaveLength(1)
  })
})
