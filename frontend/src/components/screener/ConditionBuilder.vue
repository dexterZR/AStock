<template>
  <div class="condition-section">
    <div class="condition-header">
      <span class="condition-title">🔧 筛选条件</span>
      <div class="condition-actions">
        <el-button size="small" type="primary" @click="showPicker = true">+ 添加条件</el-button>
        <el-button size="small" @click="screenerStore.clearConditions()" :disabled="screenerStore.conditions.length === 0">清空</el-button>
      </div>
    </div>
    <div class="condition-tags" v-if="screenerStore.conditions.length > 0">
      <div
        v-for="(cond, idx) in screenerStore.conditions"
        :key="idx"
        class="condition-tag"
        :style="getTagStyle(cond.category)"
      >
        <span class="tag-category">{{ getCategoryLabel(cond.category) }}</span>
        <span class="tag-text">{{ getConditionLabel(cond) }}</span>
        <span class="tag-remove" @click="screenerStore.removeCondition(idx)">×</span>
      </div>
    </div>
    <div v-else class="condition-empty">
      暂无筛选条件，点击"添加条件"或选择策略模板
    </div>
    <div class="condition-footer">
      <el-button type="primary" @click="screenerStore.executeScreener()" :loading="screenerStore.loading">
        执行筛选
      </el-button>
      <span class="condition-count" v-if="screenerStore.conditions.length > 0">
        已选 {{ screenerStore.conditions.length }} 个条件
      </span>
    </div>

    <el-dialog v-model="showPicker" title="添加筛选条件" width="600px" :append-to-body="true">
      <el-tabs v-model="pickerTab">
        <el-tab-pane v-for="cat in categories" :key="cat" :label="getCategoryLabel(cat)" :name="cat">
          <div class="picker-options">
            <div
              v-for="opt in CONDITION_OPTIONS[cat]"
              :key="opt.field"
              class="picker-option"
              @click="selectOption(cat, opt)"
            >
              <span class="picker-option-label">{{ opt.label }}</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <el-dialog v-model="showParamInput" title="设置条件参数" width="400px" :append-to-body="true">
      <div v-if="selectedOption" class="param-form">
        <div class="param-label">{{ selectedOption.label }}</div>
        <template v-if="selectedOption.hasRange">
          <div class="param-range">
            <el-input-number v-model="paramMin" placeholder="最小值" :precision="2" size="small" />
            <span class="param-sep">~</span>
            <el-input-number v-model="paramMax" placeholder="最大值" :precision="2" size="small" />
          </div>
        </template>
        <template v-else-if="selectedOption.hasValue">
          <el-switch v-model="paramBool" active-text="是" inactive-text="否" />
        </template>
      </div>
      <template #footer>
        <el-button @click="showParamInput = false">取消</el-button>
        <el-button type="primary" @click="confirmParam">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useScreenerStore } from '@/stores/screenerStore'
import { CATEGORY_CONFIG, CONDITION_OPTIONS } from '@/types/screener'
import type { ConditionCategory, ScreenerCondition, ConditionOp } from '@/types/screener'

const screenerStore = useScreenerStore()
const showPicker = ref(false)
const showParamInput = ref(false)
const pickerTab = ref<ConditionCategory>('technical')
const selectedOption = ref<{ field: string; label: string; ops: ConditionOp[]; hasValue?: boolean; hasRange?: boolean } | null>(null)
const selectedCategory = ref<ConditionCategory>('technical')
const paramMin = ref<number | undefined>(undefined)
const paramMax = ref<number | undefined>(undefined)
const paramBool = ref(true)

const categories: ConditionCategory[] = ['technical', 'fundamental', 'pattern', 'capital', 'quote']

function getCategoryLabel(cat: ConditionCategory): string {
  return CATEGORY_CONFIG[cat].label
}

function getTagStyle(cat: ConditionCategory) {
  const cfg = CATEGORY_CONFIG[cat]
  return {
    background: cfg.bgColor,
    borderColor: cfg.borderColor,
    borderLeft: `3px solid ${cfg.color}`,
  }
}

function getConditionLabel(cond: ScreenerCondition): string {
  const opts = CONDITION_OPTIONS[cond.category]
  const opt = opts?.find(o => o.field === cond.field)
  const name = opt?.label || cond.field
  if (cond.op === 'in_' && cond.values) return `${name}: ${cond.values.join('、')}`
  if (cond.op === 'in_' && Array.isArray(cond.value)) return `${name}: ${cond.value.join('、')}`
  if (cond.op === 'eq') return `${name}`
  if (cond.op === 'range') return `${name} ${cond.min ?? ''}~${cond.max ?? ''}`
  if (cond.op === 'gt') return `${name} > ${cond.value}`
  if (cond.op === 'lt') return `${name} < ${cond.value}`
  if (cond.op === 'gte') return `${name} ≥ ${cond.value}`
  if (cond.op === 'lte') return `${name} ≤ ${cond.value}`
  return name
}

function selectOption(cat: ConditionCategory, opt: any) {
  selectedCategory.value = cat
  selectedOption.value = opt
  paramMin.value = undefined
  paramMax.value = undefined
  paramBool.value = true
  if (opt.hasRange || opt.hasValue) {
    showPicker.value = false
    setTimeout(() => { showParamInput.value = true }, 150)
  } else {
    addSimpleCondition(cat, opt)
  }
}

function addSimpleCondition(cat: ConditionCategory, opt: any) {
  screenerStore.addCondition({
    category: cat,
    field: opt.field,
    op: 'eq',
    value: true,
  })
  showPicker.value = false
}

function confirmParam() {
  if (!selectedOption.value) return
  const cat = selectedCategory.value
  const opt = selectedOption.value
  if (opt.hasRange) {
    if (paramMin.value === undefined && paramMax.value === undefined) {
      ElMessage.warning('请至少填写一个值')
      return
    }
    const op: ConditionOp = (paramMin.value !== undefined && paramMax.value !== undefined) ? 'range' : paramMin.value !== undefined ? 'gte' : 'lte'
    screenerStore.addCondition({
      category: cat,
      field: opt.field,
      op,
      min: paramMin.value,
      max: paramMax.value,
      value: paramMin.value ?? paramMax.value,
    })
  } else if (opt.hasValue) {
    screenerStore.addCondition({
      category: cat,
      field: opt.field,
      op: 'eq',
      value: paramBool.value,
    })
  }
  showParamInput.value = false
  showPicker.value = false
}
</script>

<style scoped>
.condition-section {
  background: var(--claude-card);
  border: 1px solid var(--claude-border);
  border-radius: var(--radius-md);
  padding: 14px 20px;
  margin-bottom: 16px;
}
.condition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.condition-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--claude-text);
  font-family: var(--font-sans);
}
.condition-actions {
  display: flex;
  gap: 6px;
}
.condition-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.condition-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid;
  font-size: 12px;
  font-family: var(--font-sans);
  transition: all var(--transition-fast);
}
.condition-tag:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.tag-category {
  font-size: 11px;
  font-weight: 600;
}
.tag-text {
  color: var(--claude-text);
}
.tag-remove {
  cursor: pointer;
  color: var(--claude-text-tertiary);
  font-size: 14px;
  margin-left: 4px;
}
.tag-remove:hover {
  color: var(--claude-accent);
}
.condition-empty {
  text-align: center;
  padding: 20px;
  color: var(--claude-text-tertiary);
  font-size: 13px;
  font-family: var(--font-sans);
}
.condition-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}
.condition-count {
  font-size: 12px;
  color: var(--claude-text-secondary);
  font-family: var(--font-sans);
}
.picker-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.picker-option {
  padding: 10px 14px;
  border: 1px solid var(--claude-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-family: var(--font-sans);
  transition: all var(--transition-fast);
}
.picker-option:hover {
  border-color: var(--claude-accent);
  background: var(--claude-accent-light);
  color: var(--claude-accent);
}
.param-form {
  padding: 10px 0;
}
.param-label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  font-family: var(--font-sans);
}
.param-range {
  display: flex;
  align-items: center;
  gap: 8px;
}
.param-sep {
  color: var(--claude-text-tertiary);
}
</style>
