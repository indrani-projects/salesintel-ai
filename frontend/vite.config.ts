import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Allow requests proxied in via a Cloudflare/ngrok tunnel host (demo sharing).
    allowedHosts: true,
    // When the frontend calls VITE_API_URL=/api (shared-demo mode), forward those
    // to the local backend so everything is same-origin (no CORS, one tunnel URL).
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
