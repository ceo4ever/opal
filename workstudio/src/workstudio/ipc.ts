/**
 * @header {
 *   "module": "workstudio-ipc",
 *   "layer": "adapter",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio renderer가 preload를 통해 사용하는 Project directory와 read-only file tree IPC 타입",
 *   "exports": ["IpcErrorCode", "IpcResult", "ProjectDirectorySelection", "ProjectFileScope", "ProjectFileNode", "OpalWorkStudioApi", "getOpalWorkStudioApi"]
 * }
 */

export type IpcErrorCode =
  | "cancelled"
  | "invalid_path"
  | "duplicate_path"
  | "outside_registered_root"
  | "read_failed"
  | "too_large"
  | "not_supported";

export type IpcResult<T> =
  | { ok: true; value: T }
  | { ok: false; code: IpcErrorCode; message: string };

export interface ProjectDirectorySelection {
  path: string;
  realPath: string;
  name: string;
  isOpalProject: boolean;
  agentPath?: string;
  pmName?: string;
}

export interface ProjectFileScope {
  rootPath: string;
  path?: string;
  relativePath?: string;
}

export interface ProjectFileNode {
  id: string;
  name: string;
  path: string;
  kind: "file" | "folder";
  hasChildren?: boolean;
  readonly: true;
}

export interface OpalWorkStudioApi {
  project: {
    chooseDirectory: () => Promise<IpcResult<ProjectDirectorySelection>>;
    inspectDirectory: (path: string) => Promise<IpcResult<ProjectDirectorySelection>>;
    registerFromSelection: (selection: ProjectDirectorySelection) => Promise<IpcResult<ProjectDirectorySelection>>;
    listFiles: (scope: ProjectFileScope) => Promise<IpcResult<ProjectFileNode[]>>;
  };
}

export function getOpalWorkStudioApi(): OpalWorkStudioApi | undefined {
  return globalThis.opalWorkStudio;
}
