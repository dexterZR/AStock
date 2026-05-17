export class SSEClient {
  private abortController: AbortController | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private baseDelay = 1000

  constructor(
    private url: string,
    private callbacks: {
      onMessage: (data: any) => void
      onError?: (err: Error) => void
      onReconnect?: (attempt: number) => void
    }
  ) {}

  async connect(params?: Record<string, string>) {
    this.abortController = new AbortController()
    const query = new URLSearchParams(params).toString()
    const fullUrl = `${this.url}${query ? '?' + query : ''}`

    try {
      const response = await fetch(fullUrl, {
        headers: { 'Accept': 'text/event-stream' },
        signal: this.abortController.signal,
      })

      if (!response.ok) throw new Error(`SSE HTTP ${response.status}`)
      if (!response.body) throw new Error('ReadableStream not supported')

      this.reconnectAttempts = 0
      const reader = response.body.getReader()
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
            const jsonStr = line.slice(6).trim()
            if (jsonStr === '[DONE]') return
            try {
              this.callbacks.onMessage(JSON.parse(jsonStr))
            } catch {
              // ignore
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return
      this.callbacks.onError?.(err)
      this.scheduleReconnect(params)
    }
  }

  private scheduleReconnect(params?: Record<string, string>) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    const delay = Math.min(this.baseDelay * Math.pow(2, this.reconnectAttempts), 30000)
    this.reconnectAttempts++
    this.callbacks.onReconnect?.(this.reconnectAttempts)
    setTimeout(() => this.connect(params), delay)
  }

  disconnect() {
    this.abortController?.abort()
  }
}
