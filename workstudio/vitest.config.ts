/**
 * @header {
 *   "module": "workstudio-vitest-config",
 *   "layer": "config",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio Vitest 설정 — happy-dom 환경, globals, setupFiles, @vitejs/plugin-react, 앱 내부 @ alias",
 *   "exports": ["default config"]
 * }
 */
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
