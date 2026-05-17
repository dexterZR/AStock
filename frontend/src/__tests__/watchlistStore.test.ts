import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWatchlistStore } from '@/stores/watchlistStore'

vi.mock('@/api/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

import request from '@/api/request'

describe('useWatchlistStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial state', () => {
    const store = useWatchlistStore()
    expect(store.stocks).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('isInWatchlist returns true for existing stock', () => {
    const store = useWatchlistStore()
    store.stocks = ['000001.SZ', '600519.SH']
    expect(store.isInWatchlist('000001.SZ')).toBe(true)
  })

  it('isInWatchlist returns false for non-existing stock', () => {
    const store = useWatchlistStore()
    store.stocks = ['000001.SZ']
    expect(store.isInWatchlist('600519.SH')).toBe(false)
  })

  it('fetchWatchlist success', async () => {
    const mockData = { stocks: ['000001.SZ', '600519.SH'] }
    vi.mocked(request.get).mockResolvedValue(mockData)
    const store = useWatchlistStore()
    await store.fetchWatchlist()
    expect(store.stocks).toEqual(['000001.SZ', '600519.SH'])
    expect(store.loading).toBe(false)
  })

  it('fetchWatchlist handles empty data', async () => {
    vi.mocked(request.get).mockResolvedValue(null)
    const store = useWatchlistStore()
    await store.fetchWatchlist()
    expect(store.stocks).toEqual([])
  })

  it('addStock adds to list', async () => {
    vi.mocked(request.post).mockResolvedValue({})
    const store = useWatchlistStore()
    store.stocks = ['000001.SZ']
    await store.addStock('600519.SH')
    expect(store.stocks).toContain('600519.SH')
    expect(request.post).toHaveBeenCalledWith('/watchlist/600519.SH')
  })

  it('addStock does not add duplicate', async () => {
    vi.mocked(request.post).mockResolvedValue({})
    const store = useWatchlistStore()
    store.stocks = ['000001.SZ']
    await store.addStock('000001.SZ')
    expect(store.stocks).toEqual(['000001.SZ'])
  })

  it('removeStock removes from list', async () => {
    vi.mocked(request.delete).mockResolvedValue({})
    const store = useWatchlistStore()
    store.stocks = ['000001.SZ', '600519.SH']
    await store.removeStock('000001.SZ')
    expect(store.stocks).toEqual(['600519.SH'])
    expect(request.delete).toHaveBeenCalledWith('/watchlist/000001.SZ')
  })
})
