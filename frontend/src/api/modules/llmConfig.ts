import request from '../request'

export interface LLMConfigData {
  name: string
  base_url: string
  api_key: string
  model: string
  is_active?: boolean
  updated_at?: string
}

export interface LLMTestResult {
  success: boolean
  message: string
}

export const llmConfigApi = {
  getConfig: () =>
    request.get('/llm-config') as Promise<LLMConfigData | null>,
  saveConfig: (data: LLMConfigData) =>
    request.put('/llm-config', data) as Promise<{ name: string }>,
  testConnection: () =>
    request.post('/llm-config/test') as Promise<LLMTestResult>,
}
