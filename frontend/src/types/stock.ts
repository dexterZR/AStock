// ================================================================
// Stock-related TypeScript interfaces
// ================================================================

export interface StockInfo {
  ts_code: string
  name: string
  symbol: string
  industry?: string
  market?: string
  list_date?: string
  total_cap?: number
}

export interface KlineData {
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  pct_change?: number
  turnover_rate?: number
}

export interface QuoteData {
  ts_code: string
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  pre_close: number
  volume: number
  amount: number
  pct_change: number
  turnover_rate?: number
  close_raw?: number
  open_raw?: number
  high_raw?: number
  low_raw?: number
  pre_close_raw?: number
  price?: number
  open_price?: number
  high_price?: number
  low_price?: number
  pre_close_price?: number
}

export interface IndicatorData {
  ts_code: string
  trade_date: string
  macd_dif?: number
  macd_dea?: number
  macd_bar?: number
  rsi_6?: number
  rsi_12?: number
  rsi_24?: number
  kdj_k?: number
  kdj_d?: number
  kdj_j?: number
  ma5?: number
  ma10?: number
  ma20?: number
  ma60?: number
}

export interface StockSearchResult {
  value: string
  name: string
  ts_code: string
  industry?: string
}

