import { ref, onMounted, onUnmounted } from 'vue'

interface SSEMessage {
  type: string
  data: Record<string, unknown>
}

export function useSSE(url: string) {
  const connected = ref(false)
  const lastMessage = ref<SSEMessage | null>(null)
  let eventSource: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let retryCount = 0
  const maxRetries = 5

  function connect() {
    if (eventSource) return

    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      connected.value = true
      retryCount = 0
    }

    eventSource.onmessage = (event) => {
      try {
        lastMessage.value = JSON.parse(event.data)
      } catch {
        lastMessage.value = { type: 'raw', data: { content: event.data } }
      }
    }

    eventSource.addEventListener('quote', (event: MessageEvent) => {
      try {
        lastMessage.value = { type: 'quote', data: JSON.parse(event.data) }
      } catch { /* ignore malformed */ }
    })

    eventSource.addEventListener('alert', (event: MessageEvent) => {
      try {
        lastMessage.value = { type: 'alert', data: JSON.parse(event.data) }
      } catch { /* ignore malformed */ }
    })

    eventSource.onerror = () => {
      connected.value = false
      eventSource?.close()
      eventSource = null

      // 避免对认证失败无限重试
      if (retryCount >= maxRetries) {
        if (import.meta.env.DEV) {
          console.warn('[SSE] 已达最大重试次数，停止重连')
        }
        return
      }
      retryCount++
      const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)
      reconnectTimer = setTimeout(connect, delay)
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    eventSource?.close()
    eventSource = null
    connected.value = false
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    lastMessage,
    disconnect,
    reconnect: connect,
  }
}

