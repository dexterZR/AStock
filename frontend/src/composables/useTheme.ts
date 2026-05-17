import { ref, onMounted } from 'vue'

const THEME_KEY = 'astock_theme'

export function useTheme() {
  const isDark = ref(false)

  function applyTheme(dark: boolean) {
    isDark.value = dark
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light')
  }

  function toggleTheme() {
    applyTheme(!isDark.value)
  }

  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY)
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const dark = saved === 'dark' || (!saved && prefersDark)
    applyTheme(dark)
  }

  onMounted(() => {
    initTheme()
  })

  return {
    isDark,
    toggleTheme,
    applyTheme,
  }
}

