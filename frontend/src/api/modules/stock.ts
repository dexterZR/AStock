import request from '../request'

export const stockApi = {
  list: (params?: { skip?: number; limit?: number }) => request.get('/stocks', { params }),
  detail: (ts_code: string) => request.get(`/stocks/${ts_code}`),
  search: (keyword: string, limit?: number) => request.get(`/stocks/search/${encodeURIComponent(keyword)}`, { params: { limit } }),
}
