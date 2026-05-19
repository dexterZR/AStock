export type ConditionCategory = 'technical' | 'fundamental' | 'pattern' | 'quote'
export type ConditionOp = 'eq' | 'gt' | 'gte' | 'lt' | 'lte' | 'range' | 'in_'

export interface ScreenerCondition {
  category: ConditionCategory
  field: string
  op: ConditionOp
  value?: any
  min?: number
  max?: number
  values?: any[]
}

export interface ScreenerResult {
  ts_code: string
  name: string
  industry: string
  market: string
  close: number
  close_raw?: number
  price?: number
  pct_change: number
  turnover_rate: number
  volume: number
  amount: number
  pe?: number
  pb?: number
  roe?: number
  total_mv?: number
  signals?: Record<string, boolean>
  ai_reason?: string
  match_score?: number
}

export interface StrategyTemplate {
  id: string
  name: string
  icon: string
  description: string
  conditions: ScreenerCondition[]
}

export interface AIParseResult {
  query: string
  matched_keywords: string[]
  conditions: ScreenerCondition[]
}

export interface AIPickResult {
  query: string
  matched_keywords: string[]
  stocks: ScreenerResult[]
}

export interface AIAnalyzeResult {
  overview: string
  stocks: any[]
}

export interface AIDailyRecommendation {
  date: string
  recommendations: {
    title: string
    description: string
    conditions: ScreenerCondition[]
    stocks: ScreenerResult[]
    reason: string
  }[]
}

export type ViewMode = 'table' | 'cards' | 'bubble' | 'heatmap'

export const CATEGORY_CONFIG: Record<ConditionCategory, { label: string; color: string; bgColor: string; borderColor: string }> = {
  technical: { label: '技术', color: 'var(--claude-accent)', bgColor: 'var(--claude-accent-light)', borderColor: 'rgba(217,119,87,0.3)' },
  fundamental: { label: '基本', color: 'var(--claude-blue)', bgColor: 'var(--claude-blue-light)', borderColor: 'rgba(106,155,204,0.3)' },
  pattern: { label: '形态', color: 'var(--claude-green)', bgColor: 'var(--claude-green-light)', borderColor: 'rgba(120,140,93,0.3)' },
  quote: { label: '行情', color: 'var(--claude-text-secondary)', bgColor: 'var(--claude-overlay)', borderColor: 'var(--claude-border)' },
}

export const CONDITION_OPTIONS: Record<ConditionCategory, { field: string; label: string; ops: ConditionOp[]; hasValue?: boolean; hasRange?: boolean }[]> = {
  technical: [
    { field: 'ma5_cross_ma10', label: 'MA5上穿MA10', ops: ['eq'], hasValue: true },
    { field: 'ma5_cross_ma20', label: 'MA5上穿MA20', ops: ['eq'], hasValue: true },
    { field: 'ma10_cross_ma20', label: 'MA10上穿MA20', ops: ['eq'], hasValue: true },
    { field: 'macd_cross', label: 'MACD金叉', ops: ['eq'], hasValue: true },
    { field: 'kdj_cross', label: 'KDJ金叉', ops: ['eq'], hasValue: true },
    { field: 'rsi_oversold', label: 'RSI超卖(<30)', ops: ['eq'], hasValue: true },
    { field: 'rsi_overbought', label: 'RSI超买(>70)', ops: ['eq'], hasValue: true },
    { field: 'boll_breakout_up', label: '突破布林上轨', ops: ['eq'], hasValue: true },
    { field: 'boll_breakout_down', label: '跌破布林下轨', ops: ['eq'], hasValue: true },
    { field: 'ma_bullish', label: '均线多头排列', ops: ['eq'], hasValue: true },
    { field: 'ma_bearish', label: '均线空头排列', ops: ['eq'], hasValue: true },
    { field: 'volume_surge', label: '放量(量比>2)', ops: ['eq'], hasValue: true },
    { field: 'volume_shrink', label: '缩量(量比<0.5)', ops: ['eq'], hasValue: true },
  ],
  pattern: [
    { field: 'breakout_20d_high', label: '突破20日新高', ops: ['eq'], hasValue: true },
    { field: 'breakout_60d_high', label: '突破60日新高', ops: ['eq'], hasValue: true },
    { field: 'drop_20d_low', label: '跌破20日新低', ops: ['eq'], hasValue: true },
    { field: 'v_shape_recovery', label: 'V型反转', ops: ['eq'], hasValue: true },
    { field: 'consolidation', label: '缩量盘整', ops: ['eq'], hasValue: true },
    { field: 'continuous_up_3d', label: '连续3日上涨', ops: ['eq'], hasValue: true },
    { field: 'continuous_volume_3d', label: '连续3日放量', ops: ['eq'], hasValue: true },
  ],
  fundamental: [
    { field: 'pe', label: 'PE(市盈率)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'pb', label: 'PB(市净率)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'roe', label: 'ROE(%)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'revenue_growth', label: '营收增长率(%)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'profit_growth', label: '净利润增长率(%)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'dividend_yield', label: '股息率(%)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'total_mv', label: '总市值(亿)', ops: ['range', 'gt', 'lt'], hasRange: true },
  ],
  quote: [
    { field: 'price', label: '价格', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'pct_change', label: '涨跌幅(%)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'turnover_rate', label: '换手率(%)', ops: ['range', 'gt', 'lt'], hasRange: true },
    { field: 'volume', label: '成交量', ops: ['range', 'gt', 'lt'], hasRange: true },
  ],
}
