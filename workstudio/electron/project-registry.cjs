/**
 * @header {
 *   "module": "workstudio-project-registry",
 *   "layer": "desktop",
 *   "domain": "workstudio",
 *   "description": "Electron main이 소유하는 versioned Project Registry의 원자적 저장, 최근 접근 정렬, 유실 복구 계약",
 *   "exports": ["PROJECT_REGISTRY_SCHEMA_VERSION", "createProjectRegistry"]
 * }
 */

const crypto = require("node:crypto");
const fs = require("node:fs/promises");
const path = require("node:path");

const PROJECT_REGISTRY_SCHEMA_VERSION = 1;
const OPAL_AGENT_MARKER = ".opal/AGENT.md";

function ok(value) {
  return { ok: true, value };
}

function err(code, message) {
  return { ok: false, code, message };
}

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isRegistryProject(value) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.name === "string"
    && typeof value.path === "string"
    && typeof value.realPath === "string"
    && typeof value.isOpalProject === "boolean"
    && typeof value.createdAt === "string"
    && typeof value.lastAccessedAt === "string"
    && (value.status === "available" || value.status === "missing");
}

async function inspectProject(inputPath) {
  if (typeof inputPath !== "string" || inputPath.trim().length === 0) {
    return err("invalid_path", "Project path is required.");
  }
  try {
    const selectedPath = path.resolve(inputPath);
    const canonicalPath = await fs.realpath(selectedPath);
    const stat = await fs.stat(canonicalPath);
    if (!stat.isDirectory()) return err("invalid_path", "Selected path is not a directory.");
    const agentPath = path.join(selectedPath, ...OPAL_AGENT_MARKER.split("/"));
    let isOpalProject = false;
    try {
      await fs.access(agentPath);
      isOpalProject = true;
    } catch {
      // A normal directory remains a valid WorkStudio Project.
    }
    const name = path.basename(selectedPath) || selectedPath;
    return ok({
      name,
      path: selectedPath,
      realPath: selectedPath,
      canonicalPath,
      isOpalProject,
      agentPath: isOpalProject ? agentPath : undefined,
      pmName: isOpalProject ? `${name} PM` : undefined,
      status: "available",
    });
  } catch {
    return err("invalid_path", "Selected directory cannot be read.");
  }
}

function createProjectRegistry({ registryPath, now = () => new Date().toISOString() }) {
  if (typeof registryPath !== "string" || registryPath.trim().length === 0) {
    throw new TypeError("registryPath is required");
  }

  async function preserveInvalidRegistry(code) {
    const preservedPath = `${registryPath}.recovery-${Date.now()}-${crypto.randomUUID()}`;
    try {
      await fs.copyFile(registryPath, preservedPath);
      return { code, preservedPath };
    } catch {
      return { code, preservedPath: registryPath };
    }
  }

  async function readRegistry() {
    let source;
    try {
      source = await fs.readFile(registryPath, "utf8");
    } catch (error) {
      if (error?.code === "ENOENT") return { projects: [] };
      return { projects: [], recovery: { code: "read_failed", preservedPath: registryPath } };
    }

    let parsed;
    try {
      parsed = JSON.parse(source);
    } catch {
      return { projects: [], recovery: await preserveInvalidRegistry("corrupt_registry") };
    }
    if (!isRecord(parsed) || parsed.version !== PROJECT_REGISTRY_SCHEMA_VERSION) {
      return { projects: [], recovery: await preserveInvalidRegistry("unsupported_schema") };
    }
    if (!Array.isArray(parsed.projects) || !parsed.projects.every(isRegistryProject)) {
      return { projects: [], recovery: await preserveInvalidRegistry("corrupt_registry") };
    }
    return { projects: parsed.projects.map((project) => ({ ...project })) };
  }

  async function writeRegistry(projects) {
    const directory = path.dirname(registryPath);
    const temporaryPath = `${registryPath}.tmp-${process.pid}-${crypto.randomUUID()}`;
    await fs.mkdir(directory, { recursive: true });
    try {
      await fs.writeFile(temporaryPath, `${JSON.stringify({ version: PROJECT_REGISTRY_SCHEMA_VERSION, projects }, null, 2)}\n`, {
        encoding: "utf8",
        mode: 0o600,
      });
      await fs.rename(temporaryPath, registryPath);
    } catch (error) {
      await fs.rm(temporaryPath, { force: true }).catch(() => undefined);
      throw error;
    }
  }

  async function refreshAvailability(project) {
    try {
      const realPath = await fs.realpath(project.path);
      const stat = await fs.stat(realPath);
      if (!stat.isDirectory()) return { ...project, status: "missing" };
      return { ...project, status: "available" };
    } catch {
      return { ...project, status: "missing" };
    }
  }

  async function list() {
    const loaded = await readRegistry();
    const projects = await Promise.all(loaded.projects.map(refreshAvailability));
    projects.sort((left, right) => right.lastAccessedAt.localeCompare(left.lastAccessedAt));
    return ok({ projects, ...(loaded.recovery ? { recovery: loaded.recovery } : {}) });
  }

  async function register(inputPath) {
    const inspected = await inspectProject(inputPath);
    if (!inspected.ok) return inspected;
    const loaded = await readRegistry();
    const stamp = now();
    const duplicate = loaded.projects.find((project) => (project.canonicalPath ?? project.realPath) === inspected.value.canonicalPath);
    const project = duplicate
      ? { ...duplicate, ...inspected.value, id: duplicate.id, createdAt: duplicate.createdAt, lastAccessedAt: stamp }
      : { ...inspected.value, id: crypto.randomUUID(), createdAt: stamp, lastAccessedAt: stamp };
    const projects = duplicate
      ? loaded.projects.map((item) => item.id === duplicate.id ? project : item)
      : [...loaded.projects, project];
    try {
      await writeRegistry(projects);
      return ok(project);
    } catch {
      return err("storage_error", "Project registry could not be saved.");
    }
  }

  async function open(id) {
    const loaded = await readRegistry();
    const project = loaded.projects.find((item) => item.id === id);
    if (!project) return err("not_found", "Recent Project was not found.");
    const refreshed = await refreshAvailability(project);
    if (refreshed.status === "missing") return err("missing_path", "Project path no longer exists.");
    const opened = { ...refreshed, lastAccessedAt: now() };
    try {
      await writeRegistry(loaded.projects.map((item) => item.id === id ? opened : item));
      return ok(opened);
    } catch {
      return err("storage_error", "Project registry could not be saved.");
    }
  }

  async function repair(id, inputPath) {
    const loaded = await readRegistry();
    const existing = loaded.projects.find((item) => item.id === id);
    if (!existing) return err("not_found", "Recent Project was not found.");
    const inspected = await inspectProject(inputPath);
    if (!inspected.ok) return inspected;
    const duplicate = loaded.projects.find((item) => item.id !== id && (item.canonicalPath ?? item.realPath) === inspected.value.canonicalPath);
    if (duplicate) return err("duplicate_path", "This Project path is already registered.");
    const repaired = {
      ...existing,
      ...inspected.value,
      id: existing.id,
      createdAt: existing.createdAt,
      lastAccessedAt: now(),
    };
    try {
      await writeRegistry(loaded.projects.map((item) => item.id === id ? repaired : item));
      return ok(repaired);
    } catch {
      return err("storage_error", "Project registry could not be saved.");
    }
  }

  async function remove(id) {
    const loaded = await readRegistry();
    if (!loaded.projects.some((item) => item.id === id)) return err("not_found", "Recent Project was not found.");
    try {
      await writeRegistry(loaded.projects.filter((item) => item.id !== id));
      return ok({ id });
    } catch {
      return err("storage_error", "Project registry could not be saved.");
    }
  }

  return { list, open, register, repair, remove };
}

module.exports = { PROJECT_REGISTRY_SCHEMA_VERSION, createProjectRegistry };
