import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiProxy = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Allow dev-server access through tunneled hosts (e.g. Cloudflare quick
    // tunnels) so the app can be shared publicly during local development.
    allowedHosts: ['.trycloudflare.com'],
    // Forward API calls to the FastAPI backend during local development.
    // This lets the frontend call relative "/api/..." URLs.
    proxy: apiProxy,
  },
  preview: {
    // Same host allowance and API proxy for the production build preview.
    allowedHosts: ['.trycloudflare.com'],
    proxy: apiProxy,
  },
})
