import { describe, it, expect } from 'vitest'
import type { MarketIndex, MarketOverview, SectorRanking, SectorStock } from '@/types/market'

describe('Market Types', () => {
  it('MarketIndex', () => {
    const index: MarketIndex = {
      code: '000001.SH',
      name: '上证指数',
      close: 3100.5,
      pct_change: 0.85,
    }
    expect(index.code).toBe('000001.SH')
    expect(index.pct_change).toBe(0.85)
    expect(index.open).toBeUndefined()
  })

  it('MarketIndex with optional fields', () => {
    const index: MarketIndex = {
      code: '399001.SZ',
      name: '深证成指',
      close: 9800.0,
      pct_change: -0.5,
      open: 9850.0,
      high: 9900.0,
      low: 9750.0,
      volume: 5000000,
      amount: 6000000000,
    }
    expect(index.high).toBe(9900.0)
    expect(index.volume).toBe(5000000)
  })

  it('MarketOverview', () => {
    const overview: MarketOverview = {
      indices: [],
      up_count: 2000,
      down_count: 2500,
      flat_count: 500,
      limit_up_count: 30,
      limit_down_count: 10,
      turnover_total: 12000.5,
      total_stocks: 5000,
    }
    expect(overview.total_stocks).toBe(5000)
    expect(overview.up_count + overview.down_count + overview.flat_count).toBe(5000)
  })

  it('SectorRanking', () => {
    const sector: SectorRanking = {
      name: '白酒',
      sector: 'baijiu',
      change_pct: 3.5,
    }
    expect(sector.change_pct).toBe(3.5)
    expect(sector.all_stocks).toBeUndefined()
  })

  it('SectorStock', () => {
    const stock: SectorStock = {
      ts_code: '600519.SH',
      name: '贵州茅台',
      close: 1800.0,
      pct_change: 2.5,
    }
    expect(stock.ts_code).toBe('600519.SH')
  })
})
