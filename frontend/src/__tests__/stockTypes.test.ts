import { describe, it, expect } from 'vitest'
import type { StockInfo, KlineData, QuoteData, IndicatorData, StockSearchResult } from '@/types/stock'

describe('Stock Types', () => {
  it('StockInfo', () => {
    const stock: StockInfo = {
      ts_code: '000001.SZ',
      name: '平安银行',
      symbol: '000001',
      industry: '银行',
      market: 'SZSE',
    }
    expect(stock.ts_code).toBe('000001.SZ')
    expect(stock.industry).toBe('银行')
  })

  it('StockInfo with optional fields', () => {
    const stock: StockInfo = {
      ts_code: '600519.SH',
      name: '贵州茅台',
      symbol: '600519',
      list_date: '20010827',
      total_cap: 20000,
    }
    expect(stock.list_date).toBe('20010827')
    expect(stock.total_cap).toBe(20000)
  })

  it('KlineData', () => {
    const kline: KlineData = {
      trade_date: '20240101',
      open: 10.0,
      high: 11.0,
      low: 9.5,
      close: 10.5,
      volume: 1000000,
      amount: 10500000,
    }
    expect(kline.close).toBe(10.5)
    expect(kline.pct_change).toBeUndefined()
  })

  it('QuoteData', () => {
    const quote: QuoteData = {
      ts_code: '000001.SZ',
      trade_date: '20240101',
      open: 10.0,
      high: 11.0,
      low: 9.5,
      close: 10.5,
      pre_close: 10.0,
      volume: 1000000,
      amount: 10500000,
      pct_change: 5.0,
    }
    expect(quote.pct_change).toBe(5.0)
  })

  it('IndicatorData', () => {
    const indicator: IndicatorData = {
      ts_code: '000001.SZ',
      trade_date: '20240101',
      macd_dif: 0.15,
      macd_dea: 0.10,
      macd_bar: 0.05,
      rsi_6: 65.0,
      ma5: 10.5,
    }
    expect(indicator.macd_dif).toBe(0.15)
    expect(indicator.ma5).toBe(10.5)
    expect(indicator.kdj_k).toBeUndefined()
  })

  it('StockSearchResult', () => {
    const result: StockSearchResult = {
      value: '000001.SZ',
      name: '平安银行',
      ts_code: '000001.SZ',
      industry: '银行',
    }
    expect(result.value).toBe('000001.SZ')
  })
})
