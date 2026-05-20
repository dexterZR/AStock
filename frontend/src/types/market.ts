// ================================================================
// Market-related TypeScript interfaces
// ================================================================

export interface MarketIndex {
  code: string
  name: string
  close: number
  pct_change: number
  open?: number
  high?: number
  low?: number
  volume?: number
  amount?: number
}

export interface MarketOverview {
  trade_date: string
  indices: MarketIndex[]
  up_count: number
  down_count: number
  flat_count: number
  limit_up_count: number
  limit_down_count: number
  turnover_total: number
  total_stocks: number
}

export interface MarketTemperature {
  market_temperature: number
  market_sentiment?: string
  trading_volume_ratio?: number
}

export interface SectorRanking {
  name: string
  sector: string
  change_pct: number
  all_stocks?: SectorStock[]
}

export interface SectorStock {
  ts_code: string
  name: string
  close?: number
  pct_change?: number
}

