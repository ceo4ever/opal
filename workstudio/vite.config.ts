/**
 * @header {
 *   "module": "workstudio-vite-config",
 *   "layer": "config",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio Vite 설정. React, Tailwind, 앱 내부 @ alias를 독립 앱 루트 기준으로 구성한다.",
 *   "exports": ["default config"]
 * }
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  base: './',
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
