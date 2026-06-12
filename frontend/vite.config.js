import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: true,   // Bypasses the 400 host header check
    host: '0.0.0.0',      // Forces Vite to listen on all network interfaces
    cors: true            // Ensures cross-origin requests don't get blocked early
  }
})