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

router.beforeEach(() => {})

export default router
