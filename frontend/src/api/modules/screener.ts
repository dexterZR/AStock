import request from '../request'
import type { ScreenerCondition, AIParseResult, AIPickResult, AIAnalyzeResult, AIDailyRecommendation } from '@/types/screener'

const AI_TIMEOUT = 30000

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

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
  aiChat: (query: string, history: { role: string; content: string }[]) =>
    request.post('/screener/ai-chat', { query, history }, { timeout: AI_TIMEOUT }) as Promise<{
      text: string; conditions: any[]; industries: string[]; stocks: any[]; stock_count: number
    }>,

  /**
   * SSE 流式 AI 对话
   * @returns AbortController 用于中断连接
   */
  aiChatStream: (
    query: string,
    history: { role: string; content: string }[],
    callbacks: {
      onChunk: (text: string) => void
      onDone: (result: {
        text: string; conditions: any[]; industries: string[]
        stocks: any[]; stock_count: number
      }) => void
      onError: (message: string) => void
    },
  ): AbortController => {
    const controller = new AbortController()

    fetch(`${API_BASE}/screener/ai-chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      },
      body: JSON.stringify({ query, history }),
      signal: controller.signal,
    }).then(async (response) => {
      if (!response.ok) {
        callbacks.onError(`HTTP ${response.status}`)
        return
      }
      const reader = response.body?.getReader()
      if (!reader) {
        callbacks.onError('浏览器不支持流式读取')
        return
      }
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'chunk') {
                callbacks.onChunk(event.text)
              } else if (event.type === 'done') {
                callbacks.onDone(event)
              } else if (event.type === 'error') {
                callbacks.onError(event.text)
              }
            } catch {
              // 忽略解析错误
            }
          }
        }
      }
    }).catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(err.message || '网络错误')
      }
    })

    return controller
  },
}
