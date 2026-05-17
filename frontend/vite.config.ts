import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'chart-lw': ['lightweight-charts'],
          'chart-echarts': ['echarts'],
          'element-plus': ['element-plus'],
        },
      },
    },
  },
  test: {
    environment: 'happy-dom',
    globals: true,
  },
})
