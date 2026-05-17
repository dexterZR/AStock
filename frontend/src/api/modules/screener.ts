import request from '../request'
import type { ScreenerCondition, AIParseResult, AIPickResult, AIAnalyzeResult, AIDailyRecommendation } from '@/types/screener'

const AI_TIMEOUT = 30000

export const screenerApi = {
  screen: (conditions: ScreenerCondition[], limit = 50) =>
    request.post('/screener', { conditions, limit }),
  getTemplates: () =>
    request.get('/screener/templates'),
  getIndustries: () =>
    request.get('/screener/industries'),
  aiParse: (query: string) =>
    request.post('/screener/ai-parse', { query }, { timeout: AI_TIMEOUT }) as Promise<AIParseResult>,
  aiPick: (query: string) =>
    request.post('/screener/ai-pick', { query }, { timeout: AI_TIMEOUT }) as Promise<AIPickResult>,
  aiAnalyze: (tsCodes: string[]) =>
    request.post('/screener/ai-analyze', { ts_codes: tsCodes }, { timeout: AI_TIMEOUT }) as Promise<AIAnalyzeResult>,
  aiDaily: () =>
    request.get('/screener/ai-daily', { timeout: AI_TIMEOUT }) as Promise<AIDailyRecommendation>,
}
