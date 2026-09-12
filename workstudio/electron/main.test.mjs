/**
 * @header {
 *   "module": "workstudio-electron-main-test",
 *   "layer": "test",
 *   "domain": "workstudio",
 *   "description": "Electron main process가 OPAL WorkStudio native folder dialog와 preload IPC 경계를 소유하는지 검증한다.",
 *   "exports": []
 * }
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { mkdtemp, mkdir, rename, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { afterEach, describe, expect, it } from "vitest";

const temporaryRoots = [];

afterEach(async () => {
  await Promise.all(temporaryRoots.splice(0).map((root) => rm(root, { recursive: true, force: true })));
});

async function fixtureRoot() {
  const root = await mkdtemp(resolve(tmpdir(), "workstudio-registry-red-"));
  temporaryRoots.push(root);
  return root;
}

async function projectRegistryModule() {
  const modulePath = resolve(import.meta.dirname, "project-registry.cjs");
  expect(existsSync(modulePath), "Electron main must expose its persistent registry gateway as project-registry.cjs").toBe(true);
  return import(`${pathToFileURL(modulePath).href}?red=${Date.now()}-${Math.random()}`);
}

describe("Electron main native project folder bridge (S-4)", () => {
  it("limits folder picking to existing directories and keeps root-safe read-only listing", () => {
    const source = readFileSync(resolve(import.meta.dirname, "main.cjs"), "utf8");

    expect(source).toContain("preload");
    expect(source).toContain("showOpenDialog");
    expect(source).toContain("openDirectory");
    expect(source).not.toContain("createDirectory");
    expect(source).toContain("realpath");
    expect(source).toContain("outside_registered_root");
    expect(source).toContain("node_modules");
    expect(source).toContain(".git");
    expect(source).toContain("too_large");
    expect(source).not.toContain("nodeIntegration: true");
  });
});

describe("WorkStudio Project Registry RED contract", () => {
  it("S-1 persists a versioned project and reloads the same available identity", async () => {
    const root = await fixtureRoot();
    const projectPath = resolve(root, "opal-project");
    const registryPath = resolve(root, "project-registry.json");
    await mkdir(resolve(projectPath, ".opal"), { recursive: true });
    writeFileSync(resolve(projectPath, ".opal", "AGENT.md"), "# fixture PM\n", "utf8");

    const { createProjectRegistry, PROJECT_REGISTRY_SCHEMA_VERSION } = await projectRegistryModule();
    const first = createProjectRegistry({ registryPath, now: () => "2026-09-13T00:00:00.000Z" });
    const registered = await first.register(projectPath);
    expect(registered.ok).toBe(true);

    const stored = JSON.parse(readFileSync(registryPath, "utf8"));
    expect(stored.version).toBe(PROJECT_REGISTRY_SCHEMA_VERSION);
    const second = createProjectRegistry({ registryPath, now: () => "2026-09-13T00:01:00.000Z" });
    const reloaded = await second.list();
    expect(reloaded).toMatchObject({
      ok: true,
      value: {
        projects: [{ id: registered.value.id, realPath: projectPath, status: "available", isOpalProject: true }],
      },
    });
  });

  it("S-2 deduplicates realPath and sorts projects by the latest successful open", async () => {
    const root = await fixtureRoot();
    const firstPath = resolve(root, "first");
    const secondPath = resolve(root, "second");
    await mkdir(firstPath);
    await mkdir(secondPath);
    const times = [
      "2026-09-13T00:00:00.000Z",
      "2026-09-13T00:01:00.000Z",
      "2026-09-13T00:02:00.000Z",
      "2026-09-13T00:03:00.000Z",
    ];

    const { createProjectRegistry } = await projectRegistryModule();
    const registry = createProjectRegistry({ registryPath: resolve(root, "registry.json"), now: () => times.shift() });
    const first = await registry.register(firstPath);
    await registry.register(secondPath);
    const duplicate = await registry.register(resolve(firstPath, "."));
    expect(duplicate).toMatchObject({ ok: true, value: { id: first.value.id } });
    await registry.open(first.value.id);

    const listed = await registry.list();
    expect(listed.value.projects).toHaveLength(2);
    expect(listed.value.projects.map((project) => project.id)).toEqual([first.value.id, expect.any(String)]);
    expect(listed.value.projects[0].lastAccessedAt).toBe("2026-09-13T00:03:00.000Z");
  });

  it("S-3 blocks a missing project and repairs the same id with refreshed OPAL metadata", async () => {
    const root = await fixtureRoot();
    const originalPath = resolve(root, "original");
    const replacementPath = resolve(root, "replacement");
    await mkdir(originalPath);
    await mkdir(resolve(replacementPath, ".opal"), { recursive: true });
    writeFileSync(resolve(replacementPath, ".opal", "AGENT.md"), "# replacement PM\n", "utf8");

    const { createProjectRegistry } = await projectRegistryModule();
    const registry = createProjectRegistry({ registryPath: resolve(root, "registry.json") });
    const registered = await registry.register(originalPath);
    await rename(originalPath, resolve(root, "moved-away"));

    const missing = await registry.list();
    expect(missing.value.projects[0]).toMatchObject({ id: registered.value.id, status: "missing" });
    expect(await registry.open(registered.value.id)).toMatchObject({ ok: false, code: "missing_path" });

    const repaired = await registry.repair(registered.value.id, replacementPath);
    expect(repaired).toMatchObject({
      ok: true,
      value: { id: registered.value.id, realPath: replacementPath, status: "available", isOpalProject: true },
    });
    expect((await registry.list()).value.projects).toHaveLength(1);
  });

  it("S-4 removes only the registry entry and never deletes project data", async () => {
    const root = await fixtureRoot();
    const projectPath = resolve(root, "keep-on-disk");
    const sentinelPath = resolve(projectPath, "KEEP.txt");
    await mkdir(projectPath);
    writeFileSync(sentinelPath, "preserve me", "utf8");

    const { createProjectRegistry } = await projectRegistryModule();
    const registry = createProjectRegistry({ registryPath: resolve(root, "registry.json") });
    const registered = await registry.register(projectPath);
    expect(await registry.remove(registered.value.id)).toMatchObject({ ok: true });

    expect((await registry.list()).value.projects).toEqual([]);
    expect(readFileSync(sentinelPath, "utf8")).toBe("preserve me");
  });

  it.each([
    ["corrupt JSON", "{not-json", "corrupt_registry"],
    ["unsupported schema", JSON.stringify({ version: 999, projects: [] }), "unsupported_schema"],
  ])("S-5 recovers from %s without crashing or discarding the original bytes", async (_label, fixture, code) => {
    const root = await fixtureRoot();
    const registryPath = resolve(root, "registry.json");
    writeFileSync(registryPath, fixture, "utf8");

    const { createProjectRegistry } = await projectRegistryModule();
    const result = await createProjectRegistry({ registryPath }).list();
    expect(result).toMatchObject({ ok: true, value: { projects: [], recovery: { code } } });
    const recoveryPath = result.value.recovery.preservedPath ?? registryPath;
    expect(readFileSync(recoveryPath, "utf8")).toBe(fixture);
  });
});
