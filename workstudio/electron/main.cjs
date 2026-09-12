/**
 * @header {
 *   "module": "workstudio-electron-main",
 *   "layer": "desktop",
 *   "domain": "workstudio",
 *   "description": "보안 격리된 BrowserWindow와 OPAL WorkStudio project/file IPC를 소유하는 Electron main",
 *   "exports": ["createWindow", "inspectDirectory", "listFiles", "registerProjectRoot"]
 * }
 */

const { app, BrowserWindow, dialog, ipcMain } = require("electron");
const fs = require("node:fs/promises");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const WORKSTUDIO_WINDOW_TITLE = "OPAL WorkStudio";
const OPAL_AGENT_MARKER = ".opal/AGENT.md";
const MAX_CHILDREN_PER_DIRECTORY = 200;
const EXCLUDED_DIRECTORY_NAMES = new Set([
  ".git",
  ".hg",
  ".svn",
  ".turbo",
  ".next",
  ".nuxt",
  ".cache",
  ".parcel-cache",
  ".venv",
  "node_modules",
  "dist",
  "build",
  "coverage",
]);
const registeredRoots = new Map();

function ok(value) {
  return { ok: true, value };
}

function err(code, message) {
  return { ok: false, code, message };
}

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

async function realpathDirectory(inputPath) {
  if (typeof inputPath !== "string" || inputPath.trim().length === 0) {
    return err("invalid_path", "Project path is required.");
  }
  try {
    const absolutePath = path.resolve(inputPath);
    const realPath = await fs.realpath(absolutePath);
    const stat = await fs.stat(realPath);
    if (!stat.isDirectory()) {
      return err("invalid_path", "Selected path is not a directory.");
    }
    return ok(realPath);
  } catch {
    return err("invalid_path", "Selected directory cannot be read.");
  }
}

function toProjectSelection(realPath, hasAgent) {
  const agentPath = path.join(realPath, ...OPAL_AGENT_MARKER.split("/"));
  const name = path.basename(realPath) || realPath;
  return {
    path: realPath,
    realPath,
    name,
    isOpalProject: hasAgent,
    agentPath: hasAgent ? agentPath : undefined,
    pmName: hasAgent ? `${name} PM` : undefined,
  };
}

async function hasOpalAgent(realPath) {
  try {
    await fs.access(path.join(realPath, ...OPAL_AGENT_MARKER.split("/")));
    return true;
  } catch {
    return false;
  }
}

async function inspectDirectory(inputPath) {
  const resolved = await realpathDirectory(inputPath);
  if (!resolved.ok) return resolved;
  if (registeredRoots.has(resolved.value)) {
    return err("duplicate_path", "This Project path is already registered.");
  }
  return ok(toProjectSelection(resolved.value, await hasOpalAgent(resolved.value)));
}

async function registerProjectRoot(selection) {
  if (!isRecord(selection)) {
    return err("invalid_path", "Project selection is invalid.");
  }
  const resolved = await realpathDirectory(selection.realPath ?? selection.path);
  if (!resolved.ok) return resolved;
  if (registeredRoots.has(resolved.value)) {
    return err("duplicate_path", "This Project path is already registered.");
  }
  const hasAgent = await hasOpalAgent(resolved.value);
  const value = {
    ...toProjectSelection(resolved.value, hasAgent),
    name: typeof selection.name === "string" && selection.name.trim() ? selection.name.trim() : path.basename(resolved.value),
  };
  registeredRoots.set(resolved.value, value);
  return ok(value);
}

function findRegisteredRoot(realTargetPath) {
  for (const [rootPath] of registeredRoots) {
    if (realTargetPath === rootPath || realTargetPath.startsWith(`${rootPath}${path.sep}`)) {
      return rootPath;
    }
  }
  return undefined;
}

function coerceListScope(scope) {
  if (!isRecord(scope)) return {};
  return {
    rootPath: typeof scope.rootPath === "string" ? scope.rootPath : undefined,
    path: typeof scope.path === "string" ? scope.path : undefined,
    relativePath: typeof scope.relativePath === "string" ? scope.relativePath : undefined,
  };
}

function toRelativeRootPath(rootPath, realTargetPath) {
  const relativePath = path.relative(rootPath, realTargetPath);
  return relativePath === "" ? "." : relativePath.split(path.sep).join("/");
}

async function listFiles(scope) {
  const listScope = coerceListScope(scope);
  const rootResolved = await realpathDirectory(listScope.rootPath);
  if (!rootResolved.ok) return rootResolved;
  const rootPath = rootResolved.value;
  if (!registeredRoots.has(rootPath)) {
    return err("outside_registered_root", "File listing is limited to registered Project roots.");
  }

  const requestedRelativePath = listScope.relativePath ?? listScope.path ?? ".";
  const targetPath = path.resolve(rootPath, requestedRelativePath);
  let realTargetPath;
  try {
    realTargetPath = await fs.realpath(targetPath);
  } catch {
    return err("read_failed", "Directory cannot be read.");
  }
  const ownerRoot = findRegisteredRoot(realTargetPath);
  if (ownerRoot !== rootPath) {
    return err("outside_registered_root", "Requested path is outside the registered Project root.");
  }

  let entries;
  try {
    entries = await fs.readdir(realTargetPath, { withFileTypes: true });
  } catch {
    return err("read_failed", "Directory cannot be read.");
  }
  const visibleEntries = entries.filter((entry) => !entry.isDirectory() || !EXCLUDED_DIRECTORY_NAMES.has(entry.name));
  if (visibleEntries.length > MAX_CHILDREN_PER_DIRECTORY) {
    return err("too_large", "Directory has too many children to render safely.");
  }

  const nodes = await Promise.all(visibleEntries.map(async (entry) => {
    const absolutePath = path.join(realTargetPath, entry.name);
    const kind = entry.isDirectory() ? "folder" : "file";
    let hasChildren = false;
    if (kind === "folder") {
      try {
        const childEntries = await fs.readdir(absolutePath, { withFileTypes: true });
        hasChildren = childEntries.some((child) => !child.isDirectory() || !EXCLUDED_DIRECTORY_NAMES.has(child.name));
      } catch {
        hasChildren = false;
      }
    }
    const relativePath = toRelativeRootPath(rootPath, absolutePath);
    return {
      id: relativePath,
      name: entry.name,
      path: relativePath,
      kind,
      hasChildren,
      readonly: true,
    };
  }));
  return ok(nodes.sort((left, right) => {
    if (left.kind !== right.kind) return left.kind === "folder" ? -1 : 1;
    return left.name.localeCompare(right.name);
  }));
}

async function chooseDirectory(browserWindow) {
  const result = await dialog.showOpenDialog(browserWindow, {
    title: "Project folder",
    properties: ["openDirectory", "createDirectory"],
  });
  if (result.canceled || result.filePaths.length === 0) {
    return err("cancelled", "Directory selection was cancelled.");
  }
  return inspectDirectory(result.filePaths[0]);
}

function registerIpcHandlers() {
  ipcMain.handle("workstudio:project:chooseDirectory", (event) => chooseDirectory(BrowserWindow.fromWebContents(event.sender)));
  ipcMain.handle("workstudio:project:inspectDirectory", (_event, directoryPath) => inspectDirectory(directoryPath));
  ipcMain.handle("workstudio:project:registerFromSelection", (_event, selection) => registerProjectRoot(selection));
  ipcMain.handle("workstudio:project:listFiles", (_event, scope) => listFiles(scope));
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 760,
    title: WORKSTUDIO_WINDOW_TITLE,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  // Electron은 페이지 title이 로드되면 창 제목을 덮어쓰므로 WorkStudio 제품명으로 고정한다.
  window.on("page-title-updated", (event) => { event.preventDefault(); });
  const devUrl = process.env.OPAL_WORKSTUDIO_DEV_URL;
  if (devUrl) {
    void window.loadURL(devUrl);
    return;
  }
  const indexUrl = pathToFileURL(path.join(__dirname, "../dist/index.html"));
  void window.loadURL(indexUrl.toString());
}

app.whenReady().then(() => {
  registerIpcHandlers();
  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });

module.exports = {
  createWindow,
  inspectDirectory,
  listFiles,
  registerProjectRoot,
};
