/**
 * @header {
 *   "module": "workstudio-ipc-test",
 *   "layer": "test",
 *   "domain": "workstudio",
 *   "description": "OPAL WorkStudio renderer가 Node 직접 접근 없이 typed preload IPC만 사용하는 공개 계약을 RED-first로 고정한다.",
 *   "exports": []
 * }
 */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const appRoot = resolve(__dirname, "../..");
const ipcPath = resolve(appRoot, "src/workstudio/ipc.ts");
const preloadPath = resolve(appRoot, "electron/preload.cjs");
const mainPath = resolve(appRoot, "electron/main.cjs");

describe("WorkStudio typed preload IPC contract (S-4)", () => {
  it("ships renderer IPC types and a preload bridge without exposing Node APIs", () => {
    expect(existsSync(ipcPath), "workstudio/src/workstudio/ipc.ts must define renderer-facing IPC types").toBe(true);
    expect(existsSync(preloadPath), "workstudio/electron/preload.cjs must expose window.opalWorkStudio").toBe(true);

    const ipcSource = existsSync(ipcPath) ? readFileSync(ipcPath, "utf8") : "";
    const preloadSource = existsSync(preloadPath) ? readFileSync(preloadPath, "utf8") : "";

    expect(ipcSource).toContain("OpalWorkStudioApi");
    expect(ipcSource).toContain("chooseDirectory");
    expect(ipcSource).toContain("inspectDirectory");
    expect(ipcSource).toContain("registerFromSelection");
    expect(ipcSource).toContain("listFiles");
    expect(ipcSource).toContain("duplicate_path");
    expect(ipcSource).toContain("outside_registered_root");
    expect(ipcSource).toContain("too_large");

    expect(preloadSource).toContain("contextBridge.exposeInMainWorld");
    expect(preloadSource).toContain("opalWorkStudio");
    expect(preloadSource).not.toMatch(/require\(["']fs["']\)|require\(["']node:fs["']\)/);
  });

  it("configures Electron main with preload, secure webPreferences, and file IPC handlers", () => {
    const mainSource = readFileSync(mainPath, "utf8");

    expect(mainSource).toContain("preload");
    expect(mainSource).toContain("contextIsolation: true");
    expect(mainSource).toContain("nodeIntegration: false");
    expect(mainSource).toContain("sandbox: true");
    expect(mainSource).toContain("dialog.showOpenDialog");
    expect(mainSource).toContain(".opal/AGENT.md");
    expect(mainSource).toContain("ipcMain.handle");
    expect(mainSource).toContain("chooseDirectory");
    expect(mainSource).toContain("listFiles");
  });

  it("S-1 through S-5 expose persistent recent-project operations only through the typed preload bridge", () => {
    const ipcSource = readFileSync(ipcPath, "utf8");
    const preloadSource = readFileSync(preloadPath, "utf8");
    const mainSource = readFileSync(mainPath, "utf8");

    for (const operation of ["listRecent", "openRecent", "repairRecent", "removeRecent"]) {
      expect(ipcSource).toContain(operation);
      expect(preloadSource).toContain(operation);
    }
    expect(ipcSource).toContain('"available" | "missing"');
    expect(ipcSource).toContain("lastAccessedAt");
    expect(ipcSource).toContain("recovery");
    expect(mainSource).toContain('app.getPath("userData")');
    expect(mainSource).not.toMatch(/nodeIntegration:\s*true/);
  });
});
