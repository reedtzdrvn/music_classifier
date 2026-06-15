import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// В dev-режиме /api проксируется на backend (docker compose service «backend»).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
