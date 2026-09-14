/**
 * @header {
 *   "module": "workstudio-ipc",
 *   "layer": "adapter",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio renderer가 preload를 통해 사용하는 영속 Project Registry와 read-only file tree IPC 타입",
 *   "exports": ["IpcErrorCode", "IpcResult", "ProjectDirectorySelection", "RecentProject", "RecentProjectList", "ProjectFileScope", "ProjectFileNode", "OpalWorkStudioApi", "getOpalWorkStudioApi"]
 * }
 */

export type IpcErrorCode =
  | "cancelled"
  | "invalid_path"
  | "duplicate_path"
  | "missing_path"
  | "not_found"
  | "storage_error"
  | "outside_registered_root"
  | "read_failed"
  | "too_large"
  | "not_supported";

export type IpcResult<T> =
  | { ok: true; value: T }
  | { ok: false; code: IpcErrorCode; message: string };

export interface ProjectDirectorySelection {
  id?: string;
  path: string;
  realPath: string;
  name: string;
  isOpalProject: boolean;
  agentPath?: string;
  pmName?: string;
}

export interface RecentProject extends ProjectDirectorySelection {
  id: string;
  createdAt: string;
  lastAccessedAt: string;
  status: "available" | "missing";
}

export interface RegistryRecovery {
  code: "corrupt_registry" | "unsupported_schema" | "read_failed";
  preservedPath?: string;
}

export interface RecentProjectList {
  projects: RecentProject[];
  recovery?: RegistryRecovery;
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
    registerFromSelection: (selection: ProjectDirectorySelection) => Promise<IpcResult<RecentProject>>;
    listRecent: () => Promise<IpcResult<RecentProjectList>>;
    openRecent: (id: string) => Promise<IpcResult<RecentProject>>;
    repairRecent: (id: string, path: string) => Promise<IpcResult<RecentProject>>;
    removeRecent: (id: string) => Promise<IpcResult<{ id: string }>>;
    listFiles: (scope: ProjectFileScope) => Promise<IpcResult<ProjectFileNode[]>>;
  };
}

export function getOpalWorkStudioApi(): OpalWorkStudioApi | undefined {
  return globalThis.opalWorkStudio;
}
