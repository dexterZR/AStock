import { describe, it, expect } from 'vitest'
import type {
  ScreenerCondition,
  ScreenerResult,
  StrategyTemplate,
  ViewMode,
  ConditionCategory,
  ConditionOp,
} from '@/types/screener'
import { CATEGORY_CONFIG, CONDITION_OPTIONS } from '@/types/screener'

describe('Screener Types', () => {
  it('ScreenerCondition with range', () => {
    const condition: ScreenerCondition = {
      category: 'fundamental',
      field: 'pe',
      op: 'range',
      min: 5,
      max: 30,
    }
    expect(condition.category).toBe('fundamental')
    expect(condition.op).toBe('range')
    expect(condition.min).toBe(5)
    expect(condition.max).toBe(30)
  })

  it('ScreenerCondition with eq', () => {
    const condition: ScreenerCondition = {
      category: 'technical',
      field: 'macd_cross',
      op: 'eq',
      value: true,
    }
    expect(condition.value).toBe(true)
  })

  it('ScreenerResult', () => {
    const result: ScreenerResult = {
      ts_code: '000001.SZ',
      name: '平安银行',
      industry: '银行',
      market: 'SZSE',
      close: 12.5,
      pct_change: 2.3,
      turnover_rate: 1.5,
      volume: 1000000,
      amount: 12500000,
    }
    expect(result.ts_code).toBe('000001.SZ')
    expect(result.pe).toBeUndefined()
  })

  it('StrategyTemplate', () => {
    const template: StrategyTemplate = {
      id: 'test',
      name: '测试策略',
      icon: '📊',
      description: '测试用',
      conditions: [],
    }
    expect(template.id).toBe('test')
  })

  it('ViewMode type', () => {
    const modes: ViewMode[] = ['table', 'cards', 'bubble', 'heatmap']
    expect(modes).toHaveLength(4)
  })

  it('ConditionCategory type', () => {
    const categories: ConditionCategory[] = ['technical', 'fundamental', 'pattern', 'capital', 'quote']
    expect(categories).toHaveLength(5)
  })

  it('ConditionOp type', () => {
    const ops: ConditionOp[] = ['eq', 'gt', 'gte', 'lt', 'lte', 'range', 'in_']
    expect(ops).toHaveLength(7)
  })
})

describe('CATEGORY_CONFIG', () => {
  it('has all categories', () => {
    const categories = Object.keys(CATEGORY_CONFIG)
    expect(categories).toContain('technical')
    expect(categories).toContain('fundamental')
    expect(categories).toContain('pattern')
    expect(categories).toContain('capital')
    expect(categories).toContain('quote')
  })

  it('each category has required fields', () => {
    for (const [, config] of Object.entries(CATEGORY_CONFIG)) {
      expect(config).toHaveProperty('label')
      expect(config).toHaveProperty('color')
      expect(config).toHaveProperty('bgColor')
      expect(config).toHaveProperty('borderColor')
    }
  })
})

describe('CONDITION_OPTIONS', () => {
  it('has all categories', () => {
    const categories = Object.keys(CONDITION_OPTIONS)
    expect(categories).toHaveLength(5)
  })

  it('technical options include MACD', () => {
    const technical = CONDITION_OPTIONS.technical
    const macdOption = technical.find(o => o.field === 'macd_cross')
    expect(macdOption).toBeDefined()
    expect(macdOption!.label).toBe('MACD金叉')
  })

  it('fundamental options include PE', () => {
    const fundamental = CONDITION_OPTIONS.fundamental
    const peOption = fundamental.find(o => o.field === 'pe')
    expect(peOption).toBeDefined()
    expect(peOption!.ops).toContain('range')
  })

  it('each option has required fields', () => {
    for (const [, options] of Object.entries(CONDITION_OPTIONS)) {
      for (const option of options) {
        expect(option).toHaveProperty('field')
        expect(option).toHaveProperty('label')
        expect(option).toHaveProperty('ops')
        expect(option.ops.length).toBeGreaterThan(0)
      }
    }
  })
})
