import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/score': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/rank': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/leaderboard': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/batch_score': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/antigens': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/safety': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/recommend': { target: 'http://127.0.0.1:8001', changeOrigin: true },
    },
  },
})
