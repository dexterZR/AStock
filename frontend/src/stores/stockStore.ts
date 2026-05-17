import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api/request'

export interface StockInfo {
  ts_code: string
  name: string
  symbol: string
  industry?: string
  market?: string
}

export interface KlineData {
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  pct_change?: number
  turnover_rate?: number
}

export const useStockStore = defineStore('stock', () => {
  const currentStock = ref<StockInfo | null>(null)
  const klineData = ref<KlineData[]>([])
  const loading = ref(false)
  const error = ref('')

  const searchResults = ref<StockInfo[]>([])

  async function searchStocks(keyword: string) {
    try {
      const data: any = await request.get(`/stocks/search/${encodeURIComponent(keyword)}`)
      searchResults.value = data || []
    } catch (e) {
      searchResults.value = []
    }
  }

  async function fetchStockDetail(ts_code: string) {
    loading.value = true
    try {
      const data: any = await request.get(`/stocks/${ts_code}`)
      currentStock.value = data
    } catch (e: any) {
      error.value = e.message || '获取股票详情失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchKline(ts_code: string, start: string, end: string) {
    loading.value = true
    try {
      const data: any = await request.get(`/quotes/daily/${ts_code}?start_date=${start}&end_date=${end}`)
      klineData.value = data || []
    } catch (e: any) {
      error.value = e.message || '获取K线失败'
    } finally {
      loading.value = false
    }
  }

  return {
    currentStock,
    klineData,
    loading,
    error,
    searchResults,
    searchStocks,
    fetchStockDetail,
    fetchKline,
  }
})
