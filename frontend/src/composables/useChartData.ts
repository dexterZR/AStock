import { ref, computed } from 'vue'

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

export function useChartData() {
  const rawData = ref<KlineBar[]>([])
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

  function calculateMA(period: number) {
    const data = rawData.value
    const result: { time: string; value: number }[] = []
    for (let i = period - 1; i < data.length; i++) {
      const sum = data.slice(i - period + 1, i + 1).reduce((s, d) => s + d.close, 0)
      result.push({ time: data[i].time, value: +(sum / period).toFixed(2) })
    }
    return result
  }

  const maData = computed(() => {
    if (!options.value.showMA) return {}
    const result: Record<string, { time: string; value: number }[]> = {}
    for (const period of options.value.maPeriods) {
      result[`MA${period}`] = calculateMA(period)
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

  return {
    rawData,
    candlestickData,
    volumeData,
    maData,
    options,
    setData,
    updateLastBar,
    calculateMA,
  }
}
