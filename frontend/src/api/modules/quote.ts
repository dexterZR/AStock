import request from '../request'

export const quoteApi = {
  daily: (ts_code: string, start_date: string, end_date: string) =>
    request.get(`/quotes/daily/${ts_code}`, { params: { start_date, end_date } }),
  latest: (ts_code: string) => request.get(`/quotes/latest/${ts_code}`),
}
