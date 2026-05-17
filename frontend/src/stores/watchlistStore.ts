import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export const useWatchlistStore = defineStore('watchlist', () => {
  const stocks = ref<string[]>([])
  const loading = ref(false)

  async function fetchWatchlist() {
    loading.value = true
    try {
      const data: any = await request.get('/watchlist')
      stocks.value = data?.stocks || []
    } finally {
      loading.value = false
    }
  }

  function isInWatchlist(ts_code: string) {
    return stocks.value.includes(ts_code)
  }

  async function addStock(ts_code: string) {
    await request.post(`/watchlist/${ts_code}`)
    if (!stocks.value.includes(ts_code)) {
      stocks.value.push(ts_code)
    }
  }

  async function removeStock(ts_code: string) {
    await request.delete(`/watchlist/${ts_code}`)
    stocks.value = stocks.value.filter(s => s !== ts_code)
  }

  return { stocks, loading, fetchWatchlist, isInWatchlist, addStock, removeStock }
})
