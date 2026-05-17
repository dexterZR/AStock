export interface AnalysisResult {
  ts_code: string
  name: string
  total_score: number
  verdict: { action: string; color: string; summary: string }
  technical: DimResult
  fundamental: DimResult
  catalyst: DimResult
  key_signals?: KeySignal[]
  bull_bear_analysis?: BullBearAnalysis
  operation_suggestion?: OperationSuggestion
  [key: string]: any  // Allow dynamic dimension access
}

export interface DimResult {
  dimension: string
  score: number
  reasons: string[]
  details?: string[]
  signals?: Signal[]
  support_resistance?: SupportResistance
  trend_strength?: string
  indicators_status?: Record<string, string>
  industry_analysis?: string
  cap_analysis?: string
  price_position?: number
  momentum_signals?: string[]
}

export interface KeySignal {
  type: string
  name: string
  importance?: string
  description: string
  strength?: string
}

export interface Signal {
  type: string
  name: string
  strength: string
}

export interface BullBearAnalysis {
  bullish: string[]
  bearish: string[]
  neutral: string[]
  bull_bear_balance: string
}

export interface SupportResistance {
  strong_support: number
  weak_support: number
  weak_resistance: number
  strong_resistance: number
}

export interface OperationSuggestion {
  position_suggestion: string
  entry_point?: number
  stop_loss?: number
  target_price?: number
  risk_level?: string
  suggestions?: string[]
}
