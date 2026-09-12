/**
 * @header {
 *   "module": "workstudio-vite-env",
 *   "layer": "types",
 *   "domain": "workstudio",
 *   "description": "Vite 환경 타입과 OPAL WorkStudio preload global 타입을 선언한다.",
 *   "exports": []
 * }
 */

/// <reference types="vite/client" />

import type { OpalWorkStudioApi } from "./workstudio/ipc";

declare global {
  var opalWorkStudio: OpalWorkStudioApi | undefined;

  interface Window {
    opalWorkStudio?: OpalWorkStudioApi;
  }
}

export {};
