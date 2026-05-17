import { ref, computed, watch } from 'vue'

export interface KlineBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface ChartOptions {
  showMA: boolean
  maPeriods: number[]
}

export type KlinePeriod = 'day' | 'week' | '5min' | '15min' | '60min'
export type TimeRange = '1M' | '3M' | '6M' | '1Y' | 'All'

export interface FetchKlineParams {
  period: KlinePeriod
  range: TimeRange
}

/** Minute-K data availability limits (trading days) */
export const MINUTE_K_LIMITS: Record<string, number> = {
  '5min': 5,
  '15min': 20,
  '60min': 60,
}

export function useChartData(fetchKline?: (params: FetchKlineParams) => Promise<KlineBar[]>) {
  const rawData = ref<KlineBar[]>([])
  const period = ref<KlinePeriod>('day')
  const range = ref<TimeRange>('6M')
  const loading = ref(false)

  const options = ref<ChartOptions>({
    showMA: true,
    maPeriods: [5, 10, 20, 60],
  })

  const candlestickData = computed(() => {
    return rawData.value.map(d => ({
      time: d.time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))
  })

  const volumeData = computed(() => {
    return rawData.value.map(d => ({
      time: d.time,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(239, 83, 80, 0.5)' : 'rgba(38, 166, 154, 0.5)',
    }))
  })

  function calculateMA(periodDays: number) {
    const data = rawData.value
    const result: { time: string; value: number }[] = []
    for (let i = periodDays - 1; i < data.length; i++) {
      const sum = data.slice(i - periodDays + 1, i + 1).reduce((s, d) => s + d.close, 0)
      result.push({ time: data[i].time, value: +(sum / periodDays).toFixed(2) })
    }
    return result
  }

  const maData = computed(() => {
    if (!options.value.showMA) return {}
    const result: Record<string, { time: string; value: number }[]> = {}
    for (const maPeriod of options.value.maPeriods) {
      result[`MA${maPeriod}`] = calculateMA(maPeriod)
    }
    return result
  })

  function setData(data: KlineBar[]) {
    rawData.value = data
  }

  function updateLastBar(bar: KlineBar) {
    if (rawData.value.length === 0) return
    const lastIdx = rawData.value.length - 1
    if (rawData.value[lastIdx].time === bar.time) {
      rawData.value[lastIdx] = bar
    } else {
      rawData.value.push(bar)
    }
  }

  /** Trigger a data re-fetch. Returns the fetched data. */
  async function refetch(): Promise<KlineBar[]> {
    if (!fetchKline) return rawData.value
    loading.value = true
    try {
      // Minute-K data: enforce availability limits
      const minuteLimit = MINUTE_K_LIMITS[period.value]
      const effectiveRange = minuteLimit ? capRange(range.value, minuteLimit) : range.value

      const data = await fetchKline({ period: period.value, range: effectiveRange })
      rawData.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  /**
   * Cap the range for minute-K data.
   * If requested range exceeds what's available, downgrade to the max available.
   */
  function capRange(requested: TimeRange, maxDays: number): TimeRange {
    const rangeDays: Record<string, number> = {
      '1M': 22,
      '3M': 66,
      '6M': 132,
      '1Y': 252,
      'All': 9999,
    }
    const requestedDays = rangeDays[requested] || 22
    if (requestedDays <= maxDays) return requested

    // Find the largest range that fits within the limit
    const ordered: TimeRange[] = ['1M', '3M', '6M', '1Y', 'All']
    let best: TimeRange = '1M'
    for (const r of ordered) {
      if ((rangeDays[r] || 0) <= maxDays) {
        best = r
      } else {
        break
      }
    }
    return best
  }

  // Auto-refetch when period or range changes
  if (fetchKline) {
    watch([period, range], () => {
      refetch()
    })
  }

  return {
    rawData,
    candlestickData,
    volumeData,
    maData,
    period,
    range,
    options,
    loading,
    setData,
    updateLastBar,
    calculateMA,
    refetch,
  }
}
