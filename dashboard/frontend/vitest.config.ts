/**
 * @header {
 *   "module": "vitest-config",
 *   "layer": "config",
 *   "domain": "test",
 *   "description": "Vitest 설정 — happy-dom 환경, globals, setupFiles, @vitejs/plugin-react, alias",
 *   "exports": ["default config"]
 * }
 */
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: { '@': '/src' },
  },
})
