import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  // 서버 루트 고정. './'이면 2단 경로(/docs/skills)에서 자산을 /docs/assets/로
  // 해석해 SPA fallback HTML을 받고 모듈 로드가 실패한다(빈 화면).
  base: '/',
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
