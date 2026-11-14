import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
export default defineConfig({
  plugins: [react()],
  build: { outDir: '../backend/static', emptyOutDir: true, chunkSizeWarningLimit: 2500 },
  server: { proxy: { '/api': 'http://127.0.0.1:8000', '/geo': 'http://127.0.0.1:8000' } },
})
