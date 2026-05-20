<template>
  <div class="ai-chat" :class="{ collapsed }">
    <!-- Header -->
    <div class="chat-header" @click="collapsed = !collapsed">
      <div class="chat-header-left">
        <span class="chat-badge">AI</span>
        <span class="chat-title">智能选股对话</span>
        <span class="chat-status" v-if="loading">
          <span class="status-dot thinking"></span>思考中...
        </span>
      </div>
      <div class="chat-header-right">
        <el-button text size="small" class="header-btn" @click.stop="clearChat">✕ 清除对话</el-button>
        <span class="collapse-icon">{{ collapsed ? '▸' : '▾' }}</span>
      </div>
    </div>

    <!-- Messages Area -->
    <div class="chat-messages" ref="messagesRef" v-show="!collapsed">
      <!-- Welcome message -->
      <div v-if="messages.length === 0 && !loading" class="welcome">
        <div class="welcome-icon">💬</div>
        <div class="welcome-text">
          用自然语言描述你想找的股票，我可以帮你解析条件并筛选。
        </div>
        <div class="welcome-suggestions">
          <el-button
            v-for="(s, i) in suggestions"
            :key="i"
            size="small"
            class="suggestion-chip"
            @click="sendMessage(s)"
          >
            {{ s }}
          </el-button>
        </div>
      </div>

      <div v-for="(msg, idx) in messages" :key="idx" class="message-group">
        <!-- User message -->
        <div v-if="msg.role === 'user'" class="message user-message">
          <div class="msg-bubble user-bubble">{{ msg.content }}</div>
        </div>

        <!-- AI message -->
        <div v-if="msg.role === 'assistant'" class="message ai-message">
          <div class="ai-avatar">AI</div>
          <div class="ai-body">
            <div class="msg-bubble ai-bubble" :class="{ streaming: msg.streaming }" v-html="renderText(msg.content)"></div>
            <span v-if="msg.streaming" class="streaming-cursor">▌</span>

            <!-- Conditions inline -->
            <div v-if="msg.conditions && msg.conditions.length > 0" class="ai-conditions">
              <span class="ai-conditions-label">📋 识别到的条件：</span>
              <el-tag
                v-for="(cond, ci) in msg.conditions"
                :key="ci"
                size="small"
                :type="getCondTagType(cond.category)"
                class="cond-tag"
              >
                {{ getCondLabel(cond) }}
              </el-tag>
              <el-button size="small" text type="primary" @click="applyConditions(msg.conditions || [], msg.industries || [])">
                应用到筛选
              </el-button>
            </div>

            <!-- Industries inline -->
            <div v-if="msg.industries && msg.industries.length > 0 && (!msg.conditions || msg.conditions.length === 0)" class="ai-conditions">
              <span class="ai-conditions-label">🏭 行业：</span>
              <el-tag
                v-for="(ind, ci) in msg.industries"
                :key="ci"
                size="small"
                type="warning"
                class="cond-tag"
              >
                {{ ind }}
              </el-tag>
              <el-button size="small" text type="primary" @click="applyConditions([], msg.industries)">
                应用到筛选
              </el-button>
            </div>

            <!-- Stock count hint -->
            <div v-if="msg.stocks && msg.stocks.length > 0" class="ai-stock-hint">
              📊 找到 {{ msg.stock_count }} 只匹配股票
            </div>
          </div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="loading" class="message ai-message">
        <div class="ai-avatar">AI</div>
        <div class="ai-body">
          <div class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="chat-input" v-show="!collapsed">
      <el-input
        v-model="query"
        placeholder="描述你想找的股票，例如「近期放量突破的AI概念股」..."
        @keyup.enter="sendMessage()"
        :disabled="loading"
        clearable
        class="chat-text-input"
      >
        <template #prefix>
          <span style="font-size: 14px; opacity: 0.5">✏️</span>
        </template>
      </el-input>
      <el-button
        type="primary"
        :loading="loading"
        class="send-btn"
        @click="sendMessage()"
        :disabled="!query.trim()"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUnmounted } from 'vue'
import { screenerApi } from '@/api/modules/screener'
import { CONDITION_OPTIONS } from '@/types/screener'
import type { ScreenerCondition } from '@/types/screener'

defineOptions({ name: 'AIChat' })

const emit = defineEmits<{
  (e: 'applyConditions', conditions: any[], industries: string[]): void
  (e: 'viewStocks', stocks: any[]): void
  (e: 'daily'): void
}>()

const messages = ref<{
  role: 'user' | 'assistant'
  content: string
  conditions?: any[]
  industries?: string[]
  stocks?: any[]
  stock_count?: number
  streaming?: boolean  // 是否正在流式接收
}[]>([])
const query = ref('')
const loading = ref(false)
const collapsed = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
let activeStreamController: AbortController | null = null

const suggestions = [
  '近期放量突破的股票',
  '低估值高ROE的蓝筹股',
  'MACD金叉的科技股',
  '今日主力资金流入的股票',
]

function renderText(text: string): string {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

function getCondTagType(category: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    technical: '', fundamental: 'success', pattern: 'info', quote: 'info',
  }
  return map[category] || 'info'
}

function getCondLabel(cond: ScreenerCondition): string {
  if (cond.field === 'industry') {
    const vals = cond.values || (Array.isArray(cond.value) ? cond.value : cond.value ? [cond.value] : [])
    return `🏭 ${vals.join('、')}`
  }
  const category = cond.category as keyof typeof CONDITION_OPTIONS
  const options = CONDITION_OPTIONS[category]
  if (options) {
    const found = options.find(o => o.field === cond.field)
    if (found) {
      let label = found.label
      if (cond.op === 'range' && cond.min != null && cond.max != null) {
        label += ` ${cond.min}~${cond.max}`
      } else if (cond.op === 'gt' && cond.value != null) {
        label += ` >${cond.value}`
      } else if (cond.op === 'lt' && cond.value != null) {
        label += ` <${cond.value}`
      } else if (cond.op === 'gte' && cond.value != null) {
        label += ` ≥${cond.value}`
      } else if (cond.op === 'eq' && cond.value === true) {
        label = '✓ ' + label
      }
      return label
    }
  }
  return `${cond.field} ${cond.op} ${cond.value ?? ''}`
}

async function sendMessage(text?: string) {
  const msg = (typeof text === 'string' ? text : query.value).trim()
  if (!msg) return

  query.value = ''
  messages.value.push({ role: 'user', content: msg })
  loading.value = true
  scrollToBottom()

  // 中断上一个流式请求（如果有）
  if (activeStreamController) {
    activeStreamController.abort()
    activeStreamController = null
  }

  const history = messages.value
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(-10, -1)
    .map(m => ({ role: m.role, content: m.content }))

  // 优先使用流式
  const streamMsgIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    streaming: true,
  })

  activeStreamController = screenerApi.aiChatStream(msg, history, {
    onChunk: (text: string) => {
      const target = messages.value[streamMsgIndex]
      if (target) {
        target.content += text
        scrollToBottom()
      }
    },
    onDone: (result: any) => {
      const target = messages.value[streamMsgIndex]
      if (target) {
        target.streaming = false
        target.content = result.text || target.content
        target.conditions = result.conditions || []
        target.industries = result.industries || []
        target.stocks = result.stocks || []
        target.stock_count = result.stock_count || 0
      }
      activeStreamController = null
      loading.value = false
      scrollToBottom()
      if (result.stocks && result.stocks.length > 0) {
        emit('viewStocks', result.stocks)
      }
    },
    onError: async (errorMsg: string) => {
      // 流式失败 → 降级到非流式
      console.warn('[AIChat] SSE流式失败，降级到普通请求:', errorMsg)
      messages.value.pop()  // 移除空的 streaming 消息
      activeStreamController = null

      try {
        const data: any = await screenerApi.aiChat(msg, history)
        const hasStocks = data.stocks && data.stocks.length > 0
        messages.value.push({
          role: 'assistant',
          content: data.text || '好的，已处理你的请求。',
          conditions: data.conditions || [],
          industries: data.industries || [],
          stocks: data.stocks || [],
          stock_count: data.stock_count || 0,
        })
        if (hasStocks) {
          emit('viewStocks', data.stocks)
        }
      } catch {
        messages.value.push({
          role: 'assistant',
          content: '抱歉，AI回复失败，请稍后重试。',
        })
      } finally {
        loading.value = false
        scrollToBottom()
      }
    },
  })
}

onUnmounted(() => {
  if (activeStreamController) {
    activeStreamController.abort()
  }
})

function applyConditions(conditions: any[], industries: string[]) {
  emit('applyConditions', conditions, industries)
}

function clearChat() {
  messages.value = []
}

function scrollToBottom() {
  nextTick(() => {
    const el = messagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
</script>

<style scoped>
.ai-chat {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-left: 3px solid var(--claude-accent);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color var(--transition-theme), box-shadow var(--transition-fast);
}

.ai-chat:not(.collapsed) {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.ai-chat.collapsed {
  border-left-color: var(--claude-border);
  opacity: 0.7;
}

.ai-chat.collapsed:hover {
  opacity: 1;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
  border-bottom: 1px solid transparent;
}

.ai-chat:not(.collapsed) .chat-header {
  border-bottom-color: var(--claude-border);
}

.chat-header:hover {
  background: var(--claude-overlay);
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-badge {
  background: var(--claude-accent);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-sans);
}

.chat-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--claude-text);
  font-family: var(--font-sans);
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--claude-text-tertiary);
  font-family: var(--font-sans);
}

.status-dot.thinking {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--claude-accent);
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.chat-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-btn {
  font-size: 11px !important;
  color: var(--claude-text-tertiary) !important;
}

.collapse-icon {
  font-size: 12px;
  color: var(--claude-text-tertiary);
}

.chat-messages {
  max-height: 420px;
  overflow-y: auto;
  padding: 12px 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--claude-border);
  border-radius: 2px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: var(--claude-text-tertiary);
}

.welcome {
  text-align: center;
  padding: 24px 8px 16px;
}

.welcome-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.welcome-text {
  font-size: 13px;
  color: var(--claude-text-secondary);
  font-family: var(--font-sans);
  margin-bottom: 16px;
  line-height: 1.6;
}

.welcome-suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.suggestion-chip {
  font-family: var(--font-sans) !important;
  font-size: 12px !important;
  border-color: var(--claude-border) !important;
  color: var(--claude-text-secondary) !important;
  border-radius: 16px !important;
}

.suggestion-chip:hover {
  border-color: var(--claude-accent) !important;
  color: var(--claude-accent) !important;
  background: var(--claude-accent-light) !important;
}

.message-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message {
  display: flex;
  gap: 8px;
  max-width: 85%;
}

.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.ai-message {
  align-self: flex-start;
}

.msg-bubble {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.6;
  font-family: var(--font-sans);
}

.user-bubble {
  background: var(--claude-accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-bubble {
  background: var(--claude-bg);
  color: var(--claude-text);
  border: 1px solid var(--claude-border);
  border-bottom-left-radius: 4px;
}

.ai-bubble.streaming {
  border-color: var(--claude-accent);
  border-left: 2px solid var(--claude-accent);
}

.streaming-cursor {
  display: inline-block;
  color: var(--claude-accent);
  font-weight: bold;
  animation: blink 1s step-end infinite;
  margin-left: 2px;
  font-size: 14px;
  line-height: 1;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.ai-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--claude-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-display);
  flex-shrink: 0;
  margin-top: 2px;
}

.ai-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ai-conditions {
  background: var(--claude-overlay);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.ai-conditions-label {
  font-size: 11px;
  color: var(--claude-text-secondary);
  font-family: var(--font-sans);
  margin-right: 4px;
}

.cond-tag {
  font-family: var(--font-sans) !important;
}

.ai-stock-hint {
  background: var(--claude-accent-light);
  color: var(--claude-accent);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-sans);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 4px;
  align-items: center;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--claude-text-tertiary);
  animation: typingBounce 1.4s ease-in-out infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.3;
  }
  30% {
    transform: translateY(-4px);
    opacity: 0.8;
  }
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--claude-border);
  align-items: center;
  background: var(--claude-card);
}

.chat-text-input {
  flex: 1;
}

.chat-text-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  background: var(--claude-bg);
  transition: box-shadow var(--transition-fast), background var(--transition-fast);
}

.chat-text-input :deep(.el-input__wrapper:hover),
.chat-text-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--claude-accent) inset !important;
}

.send-btn {
  flex-shrink: 0;
  font-family: var(--font-sans);
  border-radius: 8px !important;
  height: 36px !important;
  line-height: 36px !important;
  padding: 0 18px !important;
}

.header-btn:hover {
  color: var(--claude-danger, #e74c3c) !important;
}
</style>
