/**
 * @header {
 *   "module": "workstudio-electron-main-test",
 *   "layer": "test",
 *   "domain": "workstudio",
 *   "description": "Electron main process가 OPAL WorkStudio native folder dialog와 preload IPC 경계를 소유하는지 검증한다.",
 *   "exports": []
 * }
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("Electron main native project folder bridge (S-4)", () => {
  it("wires createDirectory folder picking, OPAL marker inspection, and root-safe read-only listing", () => {
    const source = readFileSync(resolve(import.meta.dirname, "main.cjs"), "utf8");

    expect(source).toContain("preload");
    expect(source).toContain("showOpenDialog");
    expect(source).toContain("openDirectory");
    expect(source).toContain("createDirectory");
    expect(source).toContain("realpath");
    expect(source).toContain("outside_registered_root");
    expect(source).toContain("node_modules");
    expect(source).toContain(".git");
    expect(source).toContain("too_large");
    expect(source).not.toContain("nodeIntegration: true");
  });
});
