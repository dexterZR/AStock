<template>
  <span :class="['price-text', flashClass]">
    {{ formattedPrice }}
  </span>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

const props = defineProps<{ price: number; decimals?: number }>()
const flashClass = ref('')

const formattedPrice = computed(() => {
  return props.price.toFixed(props.decimals ?? 2)
})

watch(() => props.price, (newVal, oldVal) => {
  if (newVal > oldVal) {
    flashClass.value = 'flash-up'
  } else if (newVal < oldVal) {
    flashClass.value = 'flash-down'
  }
  setTimeout(() => { flashClass.value = '' }, 400)
})
</script>

<style scoped>
.price-text { transition: background-color 0.3s; padding: 2px 6px; border-radius: 4px; }
.flash-up { animation: flashRed 0.4s ease-out; }
.flash-down { animation: flashGreen 0.4s ease-out; }
@keyframes flashRed {
  0% { background: rgba(239, 83, 80, 0.3); }
  100% { background: transparent; }
}
@keyframes flashGreen {
  0% { background: rgba(38, 166, 154, 0.3); }
  100% { background: transparent; }
}
</style>
