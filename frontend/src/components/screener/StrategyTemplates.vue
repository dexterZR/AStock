<template>
  <div class="strategy-section">
    <div class="strategy-header">
      <span class="strategy-title">📋 策略模板</span>
      <span class="strategy-hint">选择模板自动填充条件 →</span>
    </div>
    <div class="template-list">
      <div
        v-for="t in screenerStore.templates"
        :key="t.id"
        class="template-tag"
        @click="applyTemplate(t)"
      >
        {{ t.icon }} {{ t.name }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useScreenerStore } from '@/stores/screenerStore'
import type { StrategyTemplate } from '@/types/screener'

const screenerStore = useScreenerStore()

const emit = defineEmits<{ applied: [] }>()

function applyTemplate(template: StrategyTemplate) {
  screenerStore.applyTemplate(template)
  if (screenerStore.conditions.length > 0) {
    screenerStore.executeScreener()
  }
  emit('applied')
}

onMounted(() => {
  screenerStore.loadTemplates()
})
</script>

<style scoped>
.strategy-section {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-radius: var(--radius-md);
  padding: 14px 20px;
  margin-bottom: 16px;
}
.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.strategy-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--claude-text);
  font-family: var(--font-sans);
}
.strategy-hint {
  font-size: 11px;
  color: var(--claude-text-tertiary);
}
.template-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.template-tag {
  padding: 5px 14px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--claude-bg);
  border: 1px solid var(--claude-border);
  color: var(--claude-text);
}
.template-tag:hover {
  border-color: var(--claude-accent);
  color: var(--claude-accent);
  background: var(--claude-accent-light);
  transform: translateY(-1px);
}
</style>
