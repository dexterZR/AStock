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

    const token = localStorage.getItem('astock_token')
    const fullUrl = token ? `${url}?token=${token}` : url

    eventSource = new EventSource(fullUrl)

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

      if (retryCount < maxRetries) {
        retryCount++
        const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)
        reconnectTimer = setTimeout(connect, delay)
      }
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

