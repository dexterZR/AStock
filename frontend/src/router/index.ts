import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import StockDetail from '@/views/StockDetail.vue'
import Screener from '@/views/Screener.vue'
import Settings from '@/views/Settings.vue'
import Portfolio from '@/views/Portfolio.vue'
import Login from '@/views/Login.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { guest: true } },
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/stock', name: 'StockDetail', component: StockDetail },
  { path: '/screener', name: 'Screener', component: Screener },
  { path: '/portfolio', name: 'Portfolio', component: Portfolio },
  { path: '/settings', name: 'Settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('astock_token')
  if (to.meta.guest) {
    // 登录页：已登录则跳首页
    if (token) return next('/')
    return next()
  }
  // 非登录页：未登录则跳登录
  if (!token) return next('/login')
  next()
})

export default router
