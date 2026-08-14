import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteSingleFile } from 'vite-plugin-singlefile'
import path from 'node:path'

export default defineConfig(({ mode }) => ({
  plugins: [vue(), viteSingleFile()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  define: {
    // 构建静态演示版时 VITE_OFFLINE=true,注入离线模拟数据开关
    __OFFLINE__: JSON.stringify(mode === 'offline'),
  },
}))
