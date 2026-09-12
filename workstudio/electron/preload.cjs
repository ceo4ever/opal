/**
 * @header {
 *   "module": "workstudio-electron-preload",
 *   "layer": "desktop",
 *   "domain": "workstudio",
 *   "description": "Renderer에 Node API 없이 OPAL WorkStudio typed IPC bridge를 노출하는 preload",
 *   "exports": []
 * }
 */

const { contextBridge, ipcRenderer } = require("electron");

const project = {
  chooseDirectory: () => ipcRenderer.invoke("workstudio:project:chooseDirectory"),
  inspectDirectory: (directoryPath) => ipcRenderer.invoke("workstudio:project:inspectDirectory", directoryPath),
  registerFromSelection: (selection) => ipcRenderer.invoke("workstudio:project:registerFromSelection", selection),
  listFiles: (scope) => ipcRenderer.invoke("workstudio:project:listFiles", scope),
};

contextBridge.exposeInMainWorld("opalWorkStudio", { project });
