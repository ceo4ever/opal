/**
 * @header {
 *   "module": "vite-env",
 *   "layer": "config",
 *   "domain": "core",
 *   "description": "Vite 클라이언트 타입 참조 + ImportMetaEnv 선언 병합 — VITE_API_BASE_URL을 string | undefined로 승격한다(기존 vite/client의 Record<string, any> any 폴백 대신 명시 타입). T01 W-1 (MV-25).",
 *   "exports": [],
 *   "task": "127-260912-oppl-E2E-하네스-구현"
 * }
 */

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}
