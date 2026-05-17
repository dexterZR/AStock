import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截：自动带 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('astock_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data && typeof data.success === 'boolean' && !data.success) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    if (data && typeof data.success === 'boolean' && data.success) {
      return data.data
    }
    return data
  },
  (error) => {
    const status = error.response?.status

    if (status === 401) {
      localStorage.removeItem('astock_token')
      localStorage.removeItem('astock_user')
      // Only redirect if on a protected page
      const isProtectedPage = window.location.pathname === '/portfolio'
      if (isProtectedPage) {
        window.location.href = '/login'
      }
    } else if (status === 403) {
      ElMessage.error('没有权限执行此操作')
    } else if (status === 429) {
      ElMessage.warning('请求过于频繁，请稍后再试')
    } else if (status && status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
      ElMessage.error('网络连接失败，请检查网络')
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试')
    }

    return Promise.reject(error)
  }
)

export default request
