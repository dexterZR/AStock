<template>
  <el-dialog v-model="visible" :title="title" width="580px" :close-on-click-modal="false">
    <el-form :model="form" label-width="110px" size="small">
      <el-form-item label="操作类型">
        <el-radio-group v-model="form.action"><el-radio-button value="BUY">买入</el-radio-button><el-radio-button value="ADD">加仓</el-radio-button></el-radio-group>
      </el-form-item>
      <el-form-item label="当前股价">
        <el-input :model-value="currentPrice?.toFixed(2)" readonly />
      </el-form-item>
      <el-form-item label="买入理由" :error="buyReasonError">
        <el-input v-model="form.buy_reason" type="textarea" :rows="3" placeholder="至少写10个字：为什么现在买？基于什么信号？" @input="onReasonChange" />
        <span class="char-count">{{ form.buy_reason.length }}/10字</span>
      </el-form-item>
      <el-form-item label="止损价位" :error="stopLossError">
        <el-input-number v-model="form.stop_loss_price" :precision="3" placeholder="跌破这个价必须卖出" />
      </el-form-item>
      <el-form-item label="目标价位">
        <el-input-number v-model="form.target_price" :precision="2" placeholder="预期涨到多少（可选）" />
      </el-form-item>
      <el-form-item label="本次仓位">
        <el-slider v-model="form.position_ratio" :min="0" :max="50" :step="5" show-input />
        <span v-if="form.position_ratio > 30" class="warn-text">⚠ 仓位偏重</span>
      </el-form-item>
      <el-form-item label="持有周期">
        <el-select v-model="form.expected_period">
          <el-option label="短线(1周内)" value="short" /><el-option label="中线(1月内)" value="medium" /><el-option label="长线(3月+)" value="long" />
        </el-select>
      </el-form-item>
      <el-form-item label="风险自评">
        <el-radio-group v-model="form.risk_level"><el-radio-button value="low">低</el-radio-button><el-radio-button value="medium">中</el-radio-button><el-radio-button value="high">高</el-radio-button></el-radio-group>
      </el-form-item>
      <el-form-item label="市场环境">
        <el-radio-group v-model="form.market_env"><el-radio-button value="bull">牛市</el-radio-button><el-radio-button value="oscillation">震荡</el-radio-button><el-radio-button value="bear">熊市</el-radio-button></el-radio-group>
      </el-form-item>
      <el-form-item>
        <el-checkbox v-model="form.contrarian_check">我确认本次交易不是冲动追高/抄底，已充分考虑风险</el-checkbox>
      </el-form-item>
    </el-form>

    <div v-if="errors.length" class="error-box">
      <div v-for="(e,i) in errors" :key="i">❌ {{ e }}</div>
    </div>
    <div v-if="warnings.length" class="warn-box">
      <div v-for="(w,i) in warnings" :key="i">⚠️ {{ w }}</div>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :disabled="!canSubmit" :loading="submitting" @click="handleSubmit">确认买入</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useChecklistStore } from '@/stores/checklistStore'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  stockCode: string
  stockName: string
  currentPrice: number
  action: string
}>()

const emit = defineEmits(['update:modelValue', 'done'])
const store = useChecklistStore()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const title = computed(() => `${props.stockName}(${props.stockCode}) - 交易纪律检查`)

function onReasonChange() { /* input event */ }

const form = ref({
  action: 'BUY', buy_reason: '', stop_loss_price: 0,
  target_price: undefined as number | undefined, position_ratio: 15,
  expected_period: 'medium', risk_level: 'medium', market_env: 'oscillation',
  contrarian_check: false, stock_code: '', stock_name: '', current_price: 0,
})

const errors = ref<string[]>([])
const warnings = ref<string[]>([])
const submitting = ref(false)

const buyReasonError = computed(() => form.value.buy_reason.length < 10 && form.value.buy_reason.length > 0 ? '至少10字' : '')
const stopLossError = computed(() => form.value.stop_loss_price > 0 && form.value.stop_loss_price >= props.currentPrice ? '止损价应低于当前价' : '')
const canSubmit = computed(() =>
  form.value.buy_reason.length >= 10 &&
  form.value.stop_loss_price > 0 &&
  form.value.stop_loss_price < props.currentPrice &&
  form.value.contrarian_check
)

watch(() => props.modelValue, (v) => {
  if (v) {
    form.value = {
      ...form.value,
      action: props.action,
      stock_code: props.stockCode,
      stock_name: props.stockName,
      current_price: props.currentPrice,
      buy_reason: '', stop_loss_price: 0, target_price: undefined,
      position_ratio: 15, expected_period: 'medium', risk_level: 'medium',
      market_env: 'oscillation', contrarian_check: false,
    }
    errors.value = []
    warnings.value = []
  }
})

async function handleSubmit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const v: any = await store.validateChecklist(form.value)
    if (v?.errors?.length) { errors.value = v.errors; submitting.value = false; return }
    warnings.value = v?.warnings || []
    const r = await store.submitChecklist(form.value)
    if (r?.success) {
      ElMessage.success('检查通过，决策日志已记录')
      emit('done')
      visible.value = false
    } else {
      errors.value = r?.errors || ['提交失败']
    }
  } catch { errors.value = ['网络错误'] }
  submitting.value = false
}
</script>

<style scoped>
.char-count { font-size: 11px; color: var(--claude-text-secondary); }
.warn-text { color: var(--claude-accent); font-size: 12px; margin-left: 8px; }
.error-box { background: var(--claude-accent-light); border: 1px solid var(--claude-accent); border-radius: 8px; padding: 10px; margin-bottom: 12px; color: var(--color-up); font-size: 13px; }
.warn-box { background: rgba(212,168,67,0.08); border: 1px solid var(--color-warning); border-radius: 8px; padding: 10px; margin-bottom: 12px; color: var(--claude-accent); font-size: 13px; }
</style>
