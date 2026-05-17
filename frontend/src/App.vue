<template>
  <div class="app-wrapper" :class="themeClass">
    <el-config-provider>
      <el-container class="layout-container">
        <el-aside width="220px" class="sidebar">
          <div class="logo" @click="$router.push('/')">
            <span class="logo-mark">A</span>
            <span class="logo-text">AStock</span>
            <span class="logo-dot"></span>
          </div>
          <el-menu
            :default-active="$route.path"
            router
            class="sidebar-menu"
            background-color="transparent"
            text-color="var(--claude-text-secondary)"
            active-text-color="var(--claude-accent)"
          >
            <el-menu-item v-for="item in navItems" :key="item.path" :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
              <span class="nav-shortcut">{{ item.shortcut }}</span>
            </el-menu-item>
          </el-menu>

          <div class="sidebar-footer">
            <div class="user-info" v-if="user">
              <span class="user-avatar">{{ user[0] }}</span>
              <span class="user-name">{{ user }}</span>
            </div>
            <el-button v-if="user" size="small" text class="logout-btn" @click="logout">退出登录</el-button>
          </div>
        </el-aside>

        <el-container>
          <el-header class="header">
            <div class="header-left">
              <span class="header-breadcrumb font-sans">AStock</span>
              <span class="header-separator">/</span>
              <h2 class="page-title font-sans">{{ pageTitle }}</h2>
            </div>
            <div class="header-right">
              <el-tooltip :content="isDark ? '⌘J 浅色主题' : '⌘J 深色主题'" placement="bottom">
                <el-button circle size="small" class="theme-toggle" @click="toggleTheme">
                  <el-icon :size="16"><Sunny v-if="isDark" /><Moon v-else /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </el-header>
          <el-main class="main-content">
            <router-view v-slot="{ Component }">
              <transition name="page" mode="out-in">
                <keep-alive :include="['Screener']">
                  <component :is="Component" />
                </keep-alive>
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>
    </el-config-provider>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataLine, TrendCharts, Filter, Setting, Wallet, Sunny, Moon } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const user = ref(localStorage.getItem('astock_user') || '')
const isDark = ref(false)

const themeClass = computed(() => isDark.value ? 'theme-dark' : 'theme-light')

const navItems = [
  { path: '/', label: '行情资讯', icon: DataLine, shortcut: '⌘1' },
  { path: '/stock', label: '个股详情', icon: TrendCharts, shortcut: '⌘2' },
  { path: '/screener', label: '选股器', icon: Filter, shortcut: '⌘3' },
  { path: '/portfolio', label: '持仓管理', icon: Wallet, shortcut: '⌘4' },
  { path: '/settings', label: '设置', icon: Setting, shortcut: '⌘5' },
]

const pageTitles: Record<string, string> = {
  '/': '行情资讯',
  '/stock': '个股详情',
  '/screener': '选股器',
  '/settings': '设置',
  '/portfolio': '持仓管理',
}
const pageTitle = computed(() => pageTitles[route.path] || 'A股行情分析平台')

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('astock_theme', isDark.value ? 'dark' : 'light')
  document.documentElement.classList.toggle('dark', isDark.value)
}

function logout() {
  localStorage.removeItem('astock_token')
  localStorage.removeItem('astock_user')
  window.location.href = '/login'
}

function handleKeydown(e: KeyboardEvent) {
  const meta = e.metaKey || e.ctrlKey
  if (!meta) return

  switch (e.key) {
    case '1': e.preventDefault(); if (route.path !== '/') router.push('/'); break
    case '2': e.preventDefault(); router.push('/stock'); break
    case '3': e.preventDefault(); router.push('/screener'); break
    case '4': e.preventDefault(); router.push('/portfolio'); break
    case '5': e.preventDefault(); router.push('/settings'); break
    case 'j': case 'J': e.preventDefault(); toggleTheme(); break
    case 'k': case 'K': e.preventDefault(); router.push('/stock'); break
    case '/': e.preventDefault(); document.querySelector<HTMLInputElement>('.global-search')?.focus(); break
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('astock_theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  isDark.value = savedTheme === 'dark' || (!savedTheme && prefersDark)
  document.documentElement.classList.toggle('dark', isDark.value)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style>
@import '@/styles/global.css';
</style>

<style scoped>
.app-wrapper {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  background: var(--claude-bg);
  transition: background var(--transition-theme);
}

.layout-container {
  min-height: 100vh;
}

.sidebar {
  background: var(--claude-sidebar);
  border-right: 1px solid var(--claude-border);
  display: flex;
  flex-direction: column;
  transition: background var(--transition-theme), border-color var(--transition-theme);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 60px;
  padding: 0 24px;
  border-bottom: 1px solid var(--claude-border);
  cursor: pointer;
  transition: border-color var(--transition-theme);
}

.logo-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: var(--claude-accent);
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  font-family: var(--font-display);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  letter-spacing: -0.02em;
}

.logo-text {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--claude-text);
  letter-spacing: -0.03em;
}

.logo-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--claude-blue);
  margin-left: auto;
}

.sidebar-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
}

.sidebar-menu .el-menu-item {
  margin: 2px 10px;
  border-radius: var(--radius-sm);
  height: 40px;
  line-height: 40px;
  font-size: var(--text-sm);
  font-family: var(--font-sans);
  font-weight: 450;
  transition: background var(--transition-fast), color var(--transition-fast);
  display: flex;
  align-items: center;
}

.sidebar-menu .el-menu-item:hover {
  background: var(--claude-overlay) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--claude-accent-light) !important;
  color: var(--claude-accent) !important;
  font-weight: 600;
}

.sidebar-menu .el-menu-item .el-icon {
  margin-right: 10px;
}

.nav-shortcut {
  margin-left: auto;
  font-size: var(--text-xs);
  color: var(--claude-text-tertiary);
  font-family: var(--font-mono);
  opacity: 0.5;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--claude-border);
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color var(--transition-theme);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--claude-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-display);
  flex-shrink: 0;
}

.user-name {
  font-size: var(--text-sm);
  color: var(--claude-text);
  font-weight: 500;
  font-family: var(--font-sans);
}

.logout-btn {
  color: var(--claude-text-secondary) !important;
  font-size: var(--text-xs) !important;
  font-family: var(--font-sans) !important;
  width: 100%;
  justify-content: flex-start;
  padding-left: 38px !important;
}

.header {
  background: rgba(250, 249, 245, 0.8);
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
  border-bottom: 1px solid var(--claude-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px !important;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 10;
  transition: background var(--transition-theme), border-color var(--transition-theme);
}

.theme-dark .header {
  background: rgba(20, 20, 19, 0.82);
  border-bottom: 1px solid var(--claude-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-breadcrumb {
  font-size: var(--text-sm);
  color: var(--claude-text-tertiary);
  font-weight: 500;
}

.header-separator {
  font-size: var(--text-sm);
  color: var(--claude-text-tertiary);
  margin: 0 2px;
}

.page-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--claude-text);
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle {
  border: 1px solid var(--claude-border) !important;
  background: var(--claude-card) !important;
  color: var(--claude-text-secondary) !important;
  transition: all var(--transition-fast) !important;
}

.theme-toggle:hover {
  border-color: var(--claude-accent) !important;
  color: var(--claude-accent) !important;
}

.main-content {
  background: var(--claude-bg);
  padding: 28px 32px;
  transition: background var(--transition-theme);
  max-width: 1440px;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
