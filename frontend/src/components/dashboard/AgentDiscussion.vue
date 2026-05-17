<template>
  <el-card>
    <template #header>
      <div class="card-hd">
        <span>🤖 多Agent市场研判</span>
        <el-button size="small" text @click="$emit('refresh')" :loading="discussing">刷新讨论</el-button>
      </div>
    </template>
    <div class="discussion" v-if="messages.length">
      <div v-for="(msg, i) in messages" :key="i" class="msg-bubble" :class="msg.role">
        <div class="msg-meta">
          <span class="msg-agent">{{ msg.agent }}</span>
          <span class="msg-dim">{{ msg.dimension }}</span>
        </div>
        <div class="msg-content">{{ msg.content }}</div>
      </div>
    </div>
    <el-empty v-else description="点击刷新，AI多Agent将讨论当前市场" :image-size="60" />
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  messages: Array<{ role: string; agent: string; dimension: string; content: string }>
  discussing: boolean
}>()

defineEmits<{
  refresh: []
}>()
</script>

<style scoped>
.card-hd { display: flex; justify-content: space-between; align-items: center; }

.discussion { max-height: 400px; overflow-y: auto; }
.msg-bubble { margin-bottom: 10px; padding: 10px 12px; border-radius: 8px; border-left: 3px solid; }
.msg-bubble.tech { background: var(--claude-accent-light); border-color: var(--claude-accent); }
.msg-bubble.fund { background: var(--claude-blue-light); border-color: var(--claude-blue); }
.msg-bubble.catalyst { background: rgba(212,168,67,0.08); border-color: var(--color-warning); }
.msg-bubble.verdict { background: var(--claude-green-light); border-color: var(--claude-green); }
.msg-bubble.error { background: var(--claude-bg-raised); border-color: var(--claude-border); }
.msg-meta { display: flex; gap: 8px; margin-bottom: 4px; }
.msg-agent { font-family: var(--font-sans); font-size: 12px; font-weight: 600; }
.msg-dim { font-family: var(--font-sans); font-size: 11px; color: var(--claude-text-secondary); }
.msg-content { font-family: var(--font-body); font-size: 13px; line-height: 1.6; color: var(--claude-text); }

:global(.theme-dark) .msg-bubble.tech { background: var(--claude-accent-light); }
:global(.theme-dark) .msg-bubble.fund { background: var(--claude-blue-light); }
:global(.theme-dark) .msg-bubble.catalyst { background: rgba(212,168,67,0.08); }
:global(.theme-dark) .msg-bubble.verdict { background: var(--claude-green-light); }
</style>
