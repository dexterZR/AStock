<template>
  <div class="chart-toolbar">
    <el-radio-group v-model="period" size="small">
      <el-radio-button value="day">日K</el-radio-button>
      <el-radio-button value="week">周K</el-radio-button>
      <el-radio-button value="5min">5分</el-radio-button>
      <el-radio-button value="15min">15分</el-radio-button>
      <el-radio-button value="60min">60分</el-radio-button>
    </el-radio-group>
    <el-checkbox v-model="showMA" size="small">MA均线</el-checkbox>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

defineProps<{
  periods?: string[]
}>()

const period = ref('day')
const showMA = ref(true)

const emit = defineEmits<{
  (e: 'change', period: string, showMA: boolean): void
}>()

watch([period, showMA], () => {
  emit('change', period.value, showMA.value)
})
</script>

<style scoped>
.chart-toolbar {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--claude-border);
  margin-bottom: 12px;
  font-family: var(--font-sans);
}
</style>
