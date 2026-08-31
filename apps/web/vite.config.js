import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api/research': { target: process.env.RESEARCH_API_URL || 'http://127.0.0.1:8765', changeOrigin: false, rewrite: (path) => path.replace(/^\/api\/research/, '/v1') } } },
})
