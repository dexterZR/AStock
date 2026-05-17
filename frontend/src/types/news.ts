export interface NewsItem {
  id: string
  title: string
  summary?: string
  type: NewsType
  source?: string
  pub_date: string
  heat_score: number
  sentiment: 'positive' | 'neutral' | 'negative'
  related_stocks?: string[]
  url?: string
  value_score?: number
  ai_recommended?: boolean
  ai_brief?: string
  affected_sectors?: string[]
  action_hint?: string
}

export type NewsType = 'financial' | 'research' | 'shareholder' | 'business' | 'dividend' | 'product' | 'official' | 'regulatory' | 'corporate'

export interface SentimentStats {
  positive: number
  neutral: number
  negative: number
}
