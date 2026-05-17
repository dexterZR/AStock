// ================================================================
// Sector-related TypeScript interfaces
// ================================================================

export interface SectorSummary {
  name: string
  sector: string
  change_pct: number
  stock_count?: number
  avg_volume?: number
  all_stocks?: SectorStockSummary[]
}

export interface SectorStockSummary {
  ts_code: string
  name: string
  close?: number
  pct_change?: number
  volume?: number
}
