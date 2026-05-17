import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export interface MarketIndex {
  code: string
  name: string
  close: number
  pct_change: number
}

export const useMarketStore = defineStore('market', () => {
  const indices = ref<MarketIndex[]>([])
  const loading = ref(false)

  async function fetchMarketOverview() {
    loading.value = true
    try {
      const data: any = await request.get('/market/overview')
      indices.value = data?.indices || []
    } finally {
      loading.value = false
    }
  }

  return { indices, loading, fetchMarketOverview }
})
