#!/usr/bin/env node
/**
 * @header {
 *   "module": "code-scan",
 *   "layer": "util",
 *   "domain": "code-scan",
 *   "description": "OPAL @header 메타블록 스캐너 CLI — 코드 파일의 인라인/code-map @header를 파싱해 도메인·레이어·의존관계를 조회하고, discover/scaffold/target/validate/feature 5서브명령으로 code-map 헤더 작성층(외부 매니페스트 기반 5단 상속·워커 권한 경계 집행·uncovered 2분류)을 관리한다",
 *   "exports": ["mirrorPathForDir", "decideTarget", "loadCodeMap", "loadConfig", "findProjectRoot", "resolveScope", "matchLayerRule", "matchDomain", "resolveHeader", "extractHeader"],
 *   "note": "code-scan.js 자신은 프로젝트 .opal/code-map/index.json 부재로 인라인 전용 모드로 스캔됨 (태스크 077)"
 * }
 */
// code-scan — OPAL @header metadata scanner
//
// 코드 파일의 @header 메타블록을 스캔하여 프로젝트 코드 구조를 빠르게 파악한다.
// 프로젝트별 .opal/code-scan.json 설정으로 scope(be/fe 등)를 정의한다.
//
// 사용법: node code-scan.js <command> [options]
//   scan [path]          파일 스캔 (기본: 전체)
//   domain [name]        도메인별 조회 (인자 없으면 목록)
//   layer [name]         레이어별 조회 (인자 없으면 목록)
//   search <keyword>     헤더 내 키워드 검색
//   exports <keyword>    exports 필드 전용 검색
//   summary              도메인/레이어 요약
//   depends <module>     의존 관계 추적
//   missing              @header 없는 파일 목록

'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

// ═══════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════

const VERSION = '1.3.3';
const HEADER_READ_BYTES = 8192;

const DEFAULT_CONFIG = {
  scopes: {},
  extensions: ['.py', '.js', '.ts', '.vue', '.jsx', '.tsx', '.svelte', '.kt', '.kts', '.java', '.swift'],
  exclude: ['node_modules', '__pycache__', '.git', 'dist', 'build', '.venv', 'env', '.next', '.nuxt', '.output'],
  excludePatterns: [],
  headerSource: 'auto'
};

// ─────────────────────────────────────────────────────────────────────────
// code-map constants (F-001) — external @header source (2소스 중 두번째)
// ─────────────────────────────────────────────────────────────────────────

const CODE_MAP_DIR = '.opal/code-map';
const CODE_MAP_VERSION = 1;
const ROOT_MIRROR_NAME = '_root';
const MANAGED_FIELDS = ['dir', 'scope', 'version', 'module', 'layer', 'domain'];
const WORKER_FIELDS = ['description', 'exports', 'depends', 'note', 'feature'];
const BUILD_MANIFESTS = ['package.json', 'pom.xml', 'build.gradle', 'build.gradle.kts', 'pyproject.toml', 'setup.py', 'go.mod', 'Cargo.toml'];
const STRIP_CANDIDATES = ['src/main/java/', 'src/main/kotlin/', 'src/test/java/', 'app/src/main/java/', 'src/'];
const CODE_LAYER_STANDARD = ['router', 'controller', 'service', 'repository', 'model', 'schema', 'middleware', 'util', 'config', 'page', 'component', 'composable', 'store', 'hook', 'api-client', 'test'];

const USAGE = `
code-scan v${VERSION} — OPAL @header metadata scanner

Usage: node code-scan.js <command> [options]

Commands:
  scan [path]           Scan files for @header (default: all scopes)
  domain [name]         List domains, or filter by domain
  layer [name]          List layers, or filter by layer
  search <pattern>      Search within header content (regex, case-insensitive)
  exports <pattern>     Search within exports field only (regex, case-insensitive)
  summary               Project overview by domain/layer
  depends <module>      Show dependency relationships
  missing               List files without @header
  discover               Infer a draft .opal/code-map/index.json (--out, --dry-run)
  scaffold               Create/update package manifests under .opal/code-map/
  target <file>          Decide where a file's @header should be written
  validate               Check code-map integrity (5 violation kinds, coverage)
  feature <id>            Cross-scope lookup by feature tag

Options:
  --scope <name>        Scope filter (e.g., be, fe)
  --domain <name>       Filter by domain (combinable)
  --layer <name>        Filter by layer (combinable)
  --exclude <patterns>  Exclude file patterns (comma-separated)
                        e.g., --exclude "__init__.py,test_*,*.spec.ts"
  --out <path>          discover: draft output path (default: .opal/code-map/index.json)
  --dry-run             discover/scaffold: compute without writing
  --changed <csv|->     validate: limit to a comma list or stdin newline list
  --brief               One-line summary (default)
  --full                Full header JSON
  --json                Raw JSON for piping

Exclude patterns:
  Supports wildcards: * (any chars), ? (single char)
  Matched against filename by default, or path if pattern contains /
  Set in CLI (--exclude) or config (excludePatterns), both are merged

Exit codes (validate): 0 = no violations, 1 = usage/schema error, 2 = violations found

Config:
  {project}/.opal/code-scan.json
  {
    "scopes": { "be": "workspace/backend/", "fe": "workspace/frontend/src/" },
    "extensions": [".py", ".js", ".ts", ".vue"],
    "exclude": ["node_modules", "__pycache__"],
    "excludePatterns": ["__init__.py", "test_*", "*.spec.ts"],
    "headerSource": "auto"
  }
`.trim();

// ═══════════════════════════════════════════
// Colors (auto-detect TTY)
// ═══════════════════════════════════════════

const isTTY = process.stdout.isTTY;
const C = {
  reset: isTTY ? '\x1b[0m' : '',
  bold:  isTTY ? '\x1b[1m' : '',
  dim:   isTTY ? '\x1b[2m' : '',
  cyan:  isTTY ? '\x1b[36m' : '',
  green: isTTY ? '\x1b[32m' : '',
  yellow:isTTY ? '\x1b[33m' : '',
  gray:  isTTY ? '\x1b[90m' : '',
};

// ═══════════════════════════════════════════
// CLI Parsing
// ═══════════════════════════════════════════

function parseArgs(argv) {
  const args = argv.slice(2);
  const opts = {
    command: null,
    commandArg: null,
    scope: null,
    domain: null,
    layer: null,
    output: 'brief',
    targetPath: null,
    excludePatterns: [],
  };

  opts.discoverOut = null;
  opts.dryRun = false;
  opts.changed = null;

  let i = 0;
  while (i < args.length) {
    const a = args[i];
    if (a === '--scope'  && i + 1 < args.length) { opts.scope  = args[++i]; }
    else if (a === '--domain' && i + 1 < args.length) { opts.domain = args[++i]; }
    else if (a === '--layer'  && i + 1 < args.length) { opts.layer  = args[++i]; }
    else if (a === '--exclude' && i + 1 < args.length) {
      opts.excludePatterns.push(...args[++i].split(',').map(s => s.trim()).filter(Boolean));
    }
    else if (a === '--out' && i + 1 < args.length) { opts.discoverOut = args[++i]; }
    else if (a === '--dry-run') { opts.dryRun = true; }
    else if (a === '--changed' && i + 1 < args.length) { opts.changed = args[++i]; }
    else if (a === '--brief') { opts.output = 'brief'; }
    else if (a === '--full')  { opts.output = 'full';  }
    else if (a === '--json')  { opts.output = 'json';  }
    else if (a === '--help' || a === '-h') { opts.command = 'help'; }
    else if (a === '--version' || a === '-v') { opts.command = 'version'; }
    else if (!a.startsWith('-') && !opts.command) { opts.command = a; }
    else if (!a.startsWith('-') && !opts.commandArg) { opts.commandArg = a; }
    i++;
  }

  if (!opts.command) opts.command = 'help';
  if (opts.command === 'scan' && opts.commandArg) opts.targetPath = opts.commandArg;
  return opts;
}

// ═══════════════════════════════════════════
// Project & Config
// ═══════════════════════════════════════════

function findProjectRoot() {
  let dir = process.cwd();
  const root = path.parse(dir).root;
  while (dir !== root) {
    if (fs.existsSync(path.join(dir, '.git')) ||
        fs.existsSync(path.join(dir, '.opal')) ||
        fs.existsSync(path.join(dir, 'CLAUDE.md'))) {
      return dir;
    }
    dir = path.dirname(dir);
  }
  return process.cwd();
}

function loadConfig(projectRoot) {
  const configPath = path.join(projectRoot, '.opal', 'code-scan.json');
  if (fs.existsSync(configPath)) {
    try {
      const user = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      let headerSource = user.headerSource || 'auto';
      if (!['auto', 'inline', 'manifest'].includes(headerSource)) {
        process.stderr.write(`Warning: invalid headerSource "${headerSource}", falling back to "auto"\n`);
        headerSource = 'auto';
      }
      return {
        extensions: user.extensions || DEFAULT_CONFIG.extensions,
        exclude: user.exclude || DEFAULT_CONFIG.exclude,
        excludePatterns: user.excludePatterns || [],
        scopes: user.scopes || {},
        headerSource,
      };
    } catch { return DEFAULT_CONFIG; }
  }
  return DEFAULT_CONFIG;
}

// ═══════════════════════════════════════════
// Exclude Pattern Matching
// ═══════════════════════════════════════════

function patternToRegex(pattern) {
  let re = '';
  for (let i = 0; i < pattern.length; i++) {
    const ch = pattern[i];
    if (ch === '*' && pattern[i + 1] === '*') {
      re += '.*'; i++;
      if (pattern[i + 1] === '/') i++;
    } else if (ch === '*') { re += '[^/]*'; }
    else if (ch === '?') { re += '.'; }
    else if ('.+^${}()|[]\\'.includes(ch)) { re += '\\' + ch; }
    else { re += ch; }
  }
  return new RegExp('^' + re + '$');
}

function isExcluded(relPath, fileName, patterns) {
  for (const p of patterns) {
    const re = patternToRegex(p);
    // Pattern with / → match against relative path, otherwise → match against filename
    if (p.includes('/') ? re.test(relPath) : re.test(fileName)) return true;
  }
  return false;
}

function mergeExcludePatterns(config, opts) {
  return [...(config.excludePatterns || []), ...(opts.excludePatterns || [])];
}

// validate --changed 경로 판정 전용: walkDir가 각 디렉토리 진입 시 수행하는
// `config.exclude.includes(e.name)` 세그먼트 매치와 동일한 판정을, 실제로 트리를
// 순회하지 않고 이미 알고 있는 relPath의 세그먼트들에 대해 재현한다(F-6 결함 수정).
function hasExcludedSegment(relPath, excludeDirs) {
  return relPath.split('/').some(seg => (excludeDirs || []).includes(seg));
}

// ═══════════════════════════════════════════
// File Discovery
// ═══════════════════════════════════════════

function walkDir(dir, config) {
  const files = [];
  if (!fs.existsSync(dir)) return files;

  function recurse(d) {
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); }
    catch { return; }
    for (const e of entries) {
      if (config.exclude.includes(e.name)) continue;
      const full = path.join(d, e.name);
      if (e.isDirectory()) recurse(full);
      else if (e.isFile() && config.extensions.includes(path.extname(e.name))) {
        files.push(full);
      }
    }
  }
  recurse(dir);
  return files;
}

function getSearchPaths(projectRoot, config, opts) {
  if (opts.scope) {
    const sp = config.scopes[opts.scope];
    if (!sp) {
      const avail = Object.keys(config.scopes).join(', ') || '(none)';
      process.stderr.write(`Error: Unknown scope "${opts.scope}". Available: ${avail}\n`);
      process.exit(1);
    }
    return [path.resolve(projectRoot, sp)];
  }
  if (opts.targetPath) {
    return [path.resolve(projectRoot, opts.targetPath)];
  }
  const scopes = Object.values(config.scopes);
  return scopes.length > 0
    ? scopes.map(s => path.resolve(projectRoot, s))
    : [projectRoot];
}

function discoverFiles(projectRoot, config, opts) {
  const paths = getSearchPaths(projectRoot, config, opts);
  const all = [];
  for (const p of paths) {
    if (fs.existsSync(p) && fs.statSync(p).isFile()) all.push(p);
    else all.push(...walkDir(p, config));
  }

  // Apply exclude patterns (config + CLI merged)
  const patterns = mergeExcludePatterns(config, opts);
  if (patterns.length === 0) return all.sort();

  return all.filter(f => {
    const rel = path.relative(projectRoot, f);
    return !isExcluded(rel, path.basename(f), patterns);
  }).sort();
}

// ═══════════════════════════════════════════
// Header Parsing
// ═══════════════════════════════════════════

function readFileHead(filePath) {
  try {
    const fd = fs.openSync(filePath, 'r');
    const buf = Buffer.alloc(HEADER_READ_BYTES);
    const n = fs.readSync(fd, buf, 0, HEADER_READ_BYTES, 0);
    fs.closeSync(fd);
    return buf.toString('utf8', 0, n);
  } catch { return null; }
}

function extractHeaderFromContent(content) {
  if (!content) return null;

  // 근접 판정(findProximateHeaderIndex, code-scan.js 하단 정의·호이스팅으로 여기서 참조 가능)은
  // git HEAD 회귀 판정 경로(hasNearbyHeaderBlock/classifyUncovered)와 동일한 단일 함수를 공유한다
  // (결함 C 수정, PRINCIPLES §2 — 근접 판정 로직 중복 신설 금지). 문서 본문이 "@header"를 산문으로
  // 여러 번 언급하는 경우, 근접 조건(표준 포맷 "@header {" — 토큰 뒤 공백만 두고 "{")을 만족하는
  // 첫 번째 토큰을 헤더 시작으로 삼는다.
  const idx = findProximateHeaderIndex(content);
  if (idx === -1) return null;

  // Find opening brace (근접 검사로 idx+7~idx+12 윈도 내 "{" 존재가 이미 보장됨)
  const braceStart = content.indexOf('{', idx + 7);
  if (braceStart === -1) return null;

  // Match closing brace (string-aware)
  let depth = 0, inStr = false, esc = false, end = -1;
  for (let i = braceStart; i < content.length; i++) {
    const ch = content[i];
    if (esc) { esc = false; continue; }
    if (ch === '\\' && inStr) { esc = true; continue; }
    if (ch === '"') { inStr = !inStr; continue; }
    if (inStr) continue;
    if (ch === '{') depth++;
    else if (ch === '}') { depth--; if (depth === 0) { end = i; break; } }
  }
  if (end === -1) return null;

  const raw = content.substring(braceStart, end + 1);

  // Try direct parse (Python docstring, Vue HTML comment)
  try { return JSON.parse(raw); } catch {}

  // Clean comment prefixes and retry (JSDoc *, Python #, TS //)
  const cleaned = raw.split('\n').map(line =>
    line.replace(/^\s*\*\s?/, '')
        .replace(/^\s*#\s?/, '')
        .replace(/^\s*\/\/\s?/, '')
  ).join('\n');
  try { return JSON.parse(cleaned); } catch {}

  return null;
}

function extractHeader(filePath) {
  const content = readFileHead(filePath);
  if (!content) return null;
  return extractHeaderFromContent(content);
}

// ═══════════════════════════════════════════
// Git-based uncovered classification (F-006 rework, task 077 GREEN — 결함 A)
// ─────────────────────────────────────────────────────────────────────────
// 코드-맵 매니페스트가 이 디렉토리를 관리하지 않는(비관리) 파일에 한해, 'uncovered'
// 위반을 git 기준 newly_uncovered(신규/회귀 — 차단)와 pre_existing(레거시 — 비차단)로
// 재분류한다. 매니페스트가 관리하는 디렉토리에서 파일이 files{} 키에서 누락된 경우는
// 구조적 결손(no_entry)으로 git 상태와 무관하게 그대로 유지한다(worker_scope_violation:
// files_key_removed와 별도로 이중 검출되는 것이 정상 — PLAN §3.7.2).
// ═══════════════════════════════════════════

let _gitAvailable = null; // null=미확인, true/false=1회 확인 후 캐시(프로세스당 1회 validate 실행)
let _gitWarned = false;

function isGitUsable(cwd) {
  if (_gitAvailable !== null) return _gitAvailable;
  let ok = false;
  try {
    const r = spawnSync('git', ['rev-parse', '--is-inside-work-tree'], { cwd, encoding: 'utf8' });
    if (!r.error && r.status === 0 && String(r.stdout || '').trim() === 'true') {
      const h = spawnSync('git', ['rev-parse', '--verify', '--quiet', 'HEAD'], { cwd, encoding: 'utf8' });
      ok = !h.error && h.status === 0;
    }
  } catch { ok = false; }
  _gitAvailable = ok;
  return ok;
}

function readGitHeadContent(cwd, relPath) {
  try {
    const r = spawnSync('git', ['show', `HEAD:${relPath}`], { cwd, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
    if (r.error || r.status !== 0) return { exists: false };
    return { exists: true, content: r.stdout || '' };
  } catch { return { exists: false }; }
}

// 비-git/git無 환경 폴백 경고는 validate 실행당 1줄만 출력한다.
function warnGitUnavailableOnce() {
  if (_gitWarned) return;
  _gitWarned = true;
  process.stderr.write('Warning: git repository not detected (or git unavailable) — treating all uncovered files as pre_existing (non-blocking)\n');
}

// "@header" 토큰과 근접한 여는 "{"의 위치를 찾는다(표준 포맷 header-standard.md §3 — 토큰 바로
// 뒤에 공백만 두고 "{"가 와야 함, 전 언어 공통). 이 근접 제약이 없으면 "@header"라는 단어를
// 산문으로 설명하며 뒤에 무관한 JSON 예시 블록을(예: 이 문서 자신의 `.opal/code-scan.json` 설정
// 예시) 포함하는 문서 파일에서 그 무관 JSON을 헤더로 오인할 수 있다(결함 C). 문서 본문이
// "@header"를 여러 번 언급하는 경우, 근접 조건을 만족하는 첫 번째 토큰의 인덱스를 반환한다
// (만족하는 토큰이 없으면 -1). 라이브 스캔 경로(extractHeaderFromContent)와 git HEAD 회귀 판정
// 경로(hasNearbyHeaderBlock/classifyUncovered)가 이 단일 함수를 공유한다(PRINCIPLES §2 — 중복
// 근접 판정 로직 신설 금지).
function findProximateHeaderIndex(content) {
  if (!content) return -1;
  let from = 0;
  while (true) {
    const idx = content.indexOf('@header', from);
    if (idx === -1) return -1;
    if (content.slice(idx + 7, idx + 12).indexOf('{') !== -1) return idx;
    from = idx + 7;
  }
}

// HEAD 버전에 "진짜"(근접) @header 블록이 있었는지 판정한다(회귀 감지 전용) —
// findProximateHeaderIndex와 동일한 근접 판정 기준을 그대로 재사용하는 얇은 불리언 래퍼.
function hasNearbyHeaderBlock(content) {
  return findProximateHeaderIndex(content) !== -1;
}

// 매니페스트 비관리 파일의 'no_entry' 상태를 git 기준으로 재분류한다.
//   - git 자체를 쓸 수 없음(비git 트리·git 실행 불가) → 'pre_existing' + 경고 1회
//   - HEAD에 파일이 존재하지 않음(untracked/added — 신규) → 'newly_uncovered'
//   - HEAD에 파일이 존재하고, 그 HEAD 버전에 @header가 있었음(현재는 없음 — 회귀) → 'newly_uncovered'
//   - HEAD에 파일이 존재하고, 그 HEAD 버전에도 @header가 없었음(항상 레거시) → 'pre_existing'
function classifyUncovered(projectRoot, relPath) {
  if (!isGitUsable(projectRoot)) {
    warnGitUnavailableOnce();
    return 'pre_existing';
  }
  const head = readGitHeadContent(projectRoot, relPath);
  if (!head.exists) return 'newly_uncovered';
  const headSlice = head.content.slice(0, HEADER_READ_BYTES);
  // hasNearbyHeaderBlock과 extractHeaderFromContent는 이제 동일한 근접 판정 함수
  // (findProximateHeaderIndex)를 공유한다 — 결함 C 수정으로 중복 로직 신설 없이 정리됨.
  const headHeader = hasNearbyHeaderBlock(headSlice) ? extractHeaderFromContent(headSlice) : null;
  return headHeader !== null ? 'newly_uncovered' : 'pre_existing';
}

// ═══════════════════════════════════════════
// Code Map — external @header source (F-001/F-002)
// ═══════════════════════════════════════════

class CodeMapFatalError extends Error {
  constructor(code) { super(code); this.code = code; }
}

function codeMapErrorExit(code, extra) {
  console.log(JSON.stringify(Object.assign({ ok: false, error: code }, extra || {})));
  process.exit(1);
}

function hasOwn(obj, key) {
  return obj !== null && obj !== undefined && Object.prototype.hasOwnProperty.call(obj, key);
}

function deriveStem(basename) {
  const ext = path.extname(basename);
  return ext ? basename.slice(0, -ext.length) : basename;
}

function toPosixRel(base, target) {
  return path.relative(base, target).split(path.sep).join('/');
}

function posixDirname(relPath) {
  const p = (relPath || '').split(path.sep).join('/');
  const idx = p.lastIndexOf('/');
  return idx === -1 ? '' : p.slice(0, idx);
}

function normalizeRootNoSlash(root) {
  let r = (root || '').split(path.sep).join('/');
  if (r.endsWith('/')) r = r.slice(0, -1);
  return r;
}

// ── Loader (lazy, per-command) ──────────────────────────────────────────

function loadCodeMap(projectRoot) {
  const indexPath = path.join(projectRoot, CODE_MAP_DIR, 'index.json');
  if (!fs.existsSync(indexPath)) return { present: false };

  let raw;
  try { raw = fs.readFileSync(indexPath, 'utf8'); }
  catch { return { present: false }; }

  let index;
  try { index = JSON.parse(raw); }
  catch { return { present: true, error: 'invalid_index', index: null, manifests: new Map() }; }

  if (typeof index.version !== 'number') {
    return { present: true, error: 'invalid_index', index, manifests: new Map() };
  }
  if (index.version !== CODE_MAP_VERSION) {
    return { present: true, error: 'unsupported_version', index, manifests: new Map() };
  }
  if (!index.scopes || typeof index.scopes !== 'object' || Array.isArray(index.scopes)) {
    return { present: true, error: 'invalid_index', index, manifests: new Map() };
  }
  for (const scope of Object.values(index.scopes)) {
    if (!scope || typeof scope.root !== 'string' || scope.root.length === 0) {
      return { present: true, error: 'invalid_index', index, manifests: new Map() };
    }
  }
  return { present: true, index, manifests: new Map() };
}

function buildCtx(projectRoot, config) {
  const codeMap = loadCodeMap(projectRoot);
  if (codeMap.error) throw new CodeMapFatalError(codeMap.error);
  return { projectRoot, config, codeMap };
}

function loadManifest(manifestAbs, ctx) {
  const cache = ctx.codeMap.manifests;
  if (cache.has(manifestAbs)) return cache.get(manifestAbs);
  if (!fs.existsSync(manifestAbs)) { cache.set(manifestAbs, null); return null; }
  let raw;
  try { raw = fs.readFileSync(manifestAbs, 'utf8'); }
  catch { cache.set(manifestAbs, null); return null; }
  let parsed;
  try { parsed = JSON.parse(raw); }
  catch { throw new CodeMapFatalError('manifest_parse_failed'); }
  cache.set(manifestAbs, parsed);
  return parsed;
}

// ── Scope resolution (B) ────────────────────────────────────────────────

function resolveScope(relPath, index) {
  let best = null;
  for (const [name, scope] of Object.entries((index && index.scopes) || {})) {
    const root = normalizeRootNoSlash(scope.root);
    const isMatch = root === '' ? true : (relPath === root || relPath.startsWith(root + '/'));
    if (!isMatch) continue;
    const len = root.length;
    if (!best || len > best.len || (len === best.len && name < best.name)) {
      best = { name, scope, len };
    }
  }
  return best ? { name: best.name, scope: best.scope } : null;
}

// ── Mirror path mapping (C) — root → anchors → stripPrefix ──────────────

function mirrorPathForDir(dirRel, scopeName, scope) {
  const rel = (dirRel || '').split(path.sep).join('/');
  const root = normalizeRootNoSlash(scope.root);

  let sub;
  if (root === '') sub = rel;
  else if (rel === root) sub = '';
  else if (rel.startsWith(root + '/')) sub = rel.slice(root.length + 1);
  else return { skipped: 'out_of_scope' };

  let anchor = '';
  let afterAnchor = sub;
  const anchors = scope.anchors || [];
  if (anchors.length > 0) {
    let matched = null;
    for (const a of anchors) {
      if (sub === a || sub.startsWith(a + '/')) {
        if (matched === null || a.length > matched.length) matched = a;
      }
    }
    if (matched === null) return { skipped: 'no_anchor' };
    anchor = matched;
    afterAnchor = sub === matched ? '' : sub.slice(matched.length + 1);
  }

  const candidates = (scope.stripPrefix || [])
    .map(p => (p || '').replace(/\/$/, ''))
    .filter(p => p.length > 0)
    .sort((a, b) => (b.length - a.length) || (a < b ? -1 : a > b ? 1 : 0));

  let stripped = afterAnchor;
  for (const cand of candidates) {
    if (stripped === cand || stripped.startsWith(cand + '/')) {
      stripped = stripped === cand ? '' : stripped.slice(cand.length + 1);
      break;
    }
  }

  let mirrorRel;
  if (anchor) mirrorRel = stripped ? `${anchor}/${stripped}` : anchor;
  else mirrorRel = stripped;
  if (!mirrorRel) mirrorRel = ROOT_MIRROR_NAME;

  return { mirrorRel, anchor };
}

function resolveManifestContext(relPath, ctx) {
  const scoped = resolveScope(relPath, ctx.codeMap.index);
  if (!scoped) return null;
  const dirRel = posixDirname(relPath);
  const mp = mirrorPathForDir(dirRel, scoped.name, scoped.scope);
  if (mp.skipped) {
    return { scopeName: scoped.name, scope: scoped.scope, dirRel, mp: null, manifest: null, manifestRel: null, manifestAbs: null };
  }
  const manifestRel = `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`;
  const manifestAbs = path.join(ctx.projectRoot, manifestRel);
  const manifest = loadManifest(manifestAbs, ctx);
  return { scopeName: scoped.name, scope: scoped.scope, dirRel, mp, manifestRel, manifestAbs, manifest };
}

// ── layerRules / domains matching (F) — decisive specificity + tie-break ─

function patternSpecificity(pattern) {
  let literal = 0, tokens = 0, i = 0;
  while (i < pattern.length) {
    const ch = pattern[i];
    if (ch === '*' && pattern[i + 1] === '*') { tokens++; i += 2; continue; }
    if (ch === '*' || ch === '?') { tokens++; i++; continue; }
    if (ch !== '/') literal++;
    i++;
  }
  return { literal, tokens, length: pattern.length };
}

// returns 1 if a more specific than b, -1 if less, 0 if tie on literal/tokens/length
function specificityCompare(a, b) {
  if (a.literal !== b.literal) return a.literal > b.literal ? 1 : -1;
  if (a.tokens !== b.tokens) return a.tokens < b.tokens ? 1 : -1;
  if (a.length !== b.length) return a.length > b.length ? 1 : -1;
  return 0;
}

function matchLayerRule(relPath, layerRules) {
  let best = null;
  for (const rule of layerRules || []) {
    if (!rule || typeof rule.match !== 'string') continue;
    let re;
    try { re = patternToRegex(rule.match); } catch { continue; }
    if (!re.test(relPath)) continue;
    const spec = patternSpecificity(rule.match);
    if (!best) { best = { spec, rule }; continue; }
    const cmp = specificityCompare(spec, best.spec);
    if (cmp > 0 || (cmp === 0 && rule.match < best.rule.match)) best = { spec, rule };
  }
  return best ? { layer: best.rule.layer, rule: best.rule.match } : null;
}

function matchDomain(relPath, domains) {
  let best = null;
  for (const [domainName, def] of Object.entries(domains || {})) {
    for (const pattern of (def && def.paths) || []) {
      let re;
      try { re = patternToRegex(pattern); } catch { continue; }
      if (!re.test(relPath)) continue;
      const spec = patternSpecificity(pattern);
      if (!best) { best = { spec, domainName, pattern }; continue; }
      const cmp = specificityCompare(spec, best.spec);
      if (cmp > 0 || (cmp === 0 && domainName < best.domainName)) best = { spec, domainName, pattern };
    }
  }
  return best ? { domain: best.domainName, pattern: best.pattern } : null;
}

// ── 5-tier resolver (G) — single read-path entry point ──────────────────

function resolveHeader(filePath, ctx) {
  const config = ctx.config || {};
  const headerSource = config.headerSource || 'auto';

  let inline = null;
  if (headerSource !== 'manifest') {
    inline = extractHeader(filePath);
  }

  // code-map 부재 또는 inline-only 모드: extractHeader와 완전히 동일한 값을 그대로 반환한다
  // (_source 키를 붙이지 않는다) — 제약② 하위호환 보증 지점.
  if (!ctx.codeMap.present || headerSource === 'inline') {
    return inline;
  }

  if (inline !== null) {
    const sources = {};
    for (const k of Object.keys(inline)) sources[k] = 'inline';
    return Object.assign({}, inline, { _source: 'inline', _sources: sources });
  }

  const relPath = toPosixRel(ctx.projectRoot, filePath);
  const mctx = resolveManifestContext(relPath, ctx);
  if (!mctx) return null;

  const basename = path.basename(filePath);
  const fe = (mctx.manifest && mctx.manifest.files && mctx.manifest.files[basename]) || null;
  const pkg = (mctx.manifest && mctx.manifest.package) || null;
  const layerMatch = matchLayerRule(relPath, ctx.codeMap.index.layerRules || []);
  const domainMatch = matchDomain(relPath, ctx.codeMap.index.domains || {});

  const result = {};
  const sources = {};
  let contributed = false;

  for (const field of ['description', 'exports', 'depends', 'note', 'feature']) {
    if (hasOwn(fe, field)) { result[field] = fe[field]; sources[field] = 'file'; contributed = true; }
    else if (hasOwn(pkg, field)) { result[field] = pkg[field]; sources[field] = 'package'; contributed = true; }
  }
  if (hasOwn(fe, 'module')) { result.module = fe.module; sources.module = 'file'; contributed = true; }
  if (layerMatch) { result.layer = layerMatch.layer; sources.layer = 'rule'; contributed = true; }
  if (domainMatch) { result.domain = domainMatch.domain; sources.domain = 'domain'; contributed = true; }
  if (hasOwn(fe, 'draft')) result.draft = fe.draft;

  if (!contributed) return null;

  if (result.module === undefined) {
    result.module = deriveStem(basename);
    sources.module = 'rule';
  }

  const order = ['file', 'package', 'rule', 'domain'];
  const present = new Set();
  for (const [k, v] of Object.entries(sources)) {
    if (k === 'module' && v === 'rule' && !hasOwn(fe, 'module')) continue; // passive stem fallback — not a real contribution
    present.add(v);
  }
  let primary;
  for (const tier of order) { if (present.has(tier)) { primary = tier; break; } }

  result._source = primary;
  result._sources = sources;
  return result;
}

// ── Target — 4-tier write-location decision (F-005) ─────────────────────

function decideTarget(fileRel, ctx) {
  const relPath = (fileRel || '').split(path.sep).join('/');
  const absPath = path.resolve(ctx.projectRoot, relPath);

  const scoped = ctx.codeMap.present ? resolveScope(relPath, ctx.codeMap.index) : null;

  if (scoped && scoped.scope.readonly === true) {
    const out = { write_to: 'manifest', reason: 'readonly_repo' };
    const mp = mirrorPathForDir(posixDirname(relPath), scoped.name, scoped.scope);
    if (!mp.skipped) {
      out.scope = scoped.name;
      out.manifest = `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`;
      out.key = path.basename(relPath);
    }
    return out;
  }

  const inline = extractHeader(absPath) !== null;
  if (inline) return { write_to: 'inline', reason: 'inline_exists' };

  const exists = fs.existsSync(absPath);
  if (!exists) return { write_to: 'inline', reason: 'new_file' };

  if (scoped) {
    const mp = mirrorPathForDir(posixDirname(relPath), scoped.name, scoped.scope);
    if (!mp.skipped) {
      return {
        write_to: 'manifest',
        reason: 'legacy_no_header',
        scope: scoped.name,
        manifest: `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`,
        key: path.basename(relPath),
      };
    }
  }
  return { write_to: 'inline', reason: 'legacy_no_header' };
}

// ═══════════════════════════════════════════
// Scanning & Filtering
// ═══════════════════════════════════════════

function scanAll(projectRoot, config, opts) {
  const files = discoverFiles(projectRoot, config, opts);
  const ctx = buildCtx(projectRoot, config);
  const withHeader = [];
  const noHeader = [];

  for (const f of files) {
    const header = resolveHeader(f, ctx);
    const rel = path.relative(projectRoot, f);
    if (header) {
      withHeader.push({ path: rel, file: path.basename(f), header });
    } else {
      noHeader.push({ path: rel, file: path.basename(f) });
    }
  }
  return { withHeader, noHeader };
}

function scanHeaders(projectRoot, config, opts) {
  const { withHeader } = scanAll(projectRoot, config, opts);
  return withHeader.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
}

// ═══════════════════════════════════════════
// Output Formatting
// ═══════════════════════════════════════════

function fmtBrief(results) {
  if (results.length === 0) { console.log('No files found.'); return; }

  const maxLayer = Math.max(...results.map(r => (r.header.layer || '?').length));
  const maxFile  = Math.max(...results.map(r => r.file.length));

  for (const r of results) {
    const layer = (r.header.layer || '?').padEnd(maxLayer);
    const file  = r.file.padEnd(maxFile);
    const desc  = r.header.description || '';
    console.log(`${C.cyan}[${layer}]${C.reset}  ${C.bold}${file}${C.reset}  ${C.dim}—${C.reset} ${desc}`);
  }
  console.log(`${C.dim}\n${results.length} file(s)${C.reset}`);
}

function fmtFull(results) {
  if (results.length === 0) { console.log('No files found.'); return; }
  for (const r of results) {
    console.log(`\n${C.cyan}── ${r.path} ──${C.reset}`);
    console.log(JSON.stringify(r.header, null, 2));
  }
  console.log(`${C.dim}\n${results.length} file(s)${C.reset}`);
}

function fmtJson(results) {
  const out = {};
  for (const r of results) out[r.path] = r.header;
  console.log(JSON.stringify(out, null, 2));
}

function output(results, opts) {
  switch (opts.output) {
    case 'full': return fmtFull(results);
    case 'json': return fmtJson(results);
    default:     return fmtBrief(results);
  }
}

// ═══════════════════════════════════════════
// Commands
// ═══════════════════════════════════════════

function cmdScan(projectRoot, config, opts) {
  output(scanHeaders(projectRoot, config, opts), opts);
}

function cmdDomain(projectRoot, config, opts) {
  if (opts.commandArg) {
    opts.domain = opts.commandArg;
    return output(scanHeaders(projectRoot, config, opts), opts);
  }
  // List all domains grouped
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  if (results.length === 0) { console.log('No @header blocks found.'); return; }

  const groups = {};
  for (const r of results) {
    const d = r.header.domain || '(none)';
    if (!groups[d]) groups[d] = [];
    groups[d].push(r);
  }
  for (const [domain, files] of Object.entries(groups).sort()) {
    console.log(`\n${C.green}[${domain}]${C.reset}`);
    const ml = Math.max(...files.map(r => (r.header.layer || '?').length));
    const mf = Math.max(...files.map(r => r.file.length));
    for (const r of files) {
      const layer = (r.header.layer || '?').padEnd(ml);
      const file  = r.file.padEnd(mf);
      console.log(`  ${C.cyan}[${layer}]${C.reset}  ${file}  ${C.dim}—${C.reset} ${r.header.description || ''}`);
    }
  }
}

function cmdLayer(projectRoot, config, opts) {
  if (opts.commandArg) {
    opts.layer = opts.commandArg;
    return output(scanHeaders(projectRoot, config, opts), opts);
  }
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  if (results.length === 0) { console.log('No @header blocks found.'); return; }

  const groups = {};
  for (const r of results) {
    const l = r.header.layer || '(none)';
    if (!groups[l]) groups[l] = [];
    groups[l].push(r);
  }
  for (const [layer, files] of Object.entries(groups).sort()) {
    console.log(`\n${C.green}[${layer}]${C.reset}`);
    const md = Math.max(...files.map(r => (r.header.domain || '?').length));
    const mf = Math.max(...files.map(r => r.file.length));
    for (const r of files) {
      const domain = (r.header.domain || '?').padEnd(md);
      const file   = r.file.padEnd(mf);
      console.log(`  ${C.cyan}[${domain}]${C.reset}  ${file}  ${C.dim}—${C.reset} ${r.header.description || ''}`);
    }
  }
}

function cmdSearch(projectRoot, config, opts) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan search <pattern>'); process.exit(1); }

  let regex;
  try { regex = new RegExp(keyword, 'i'); }
  catch (err) {
    console.error(`Invalid regex: ${keyword} — ${err.message}`);
    process.exit(1);
  }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  const matches = all.filter(r => regex.test(JSON.stringify(r.header)));

  // Re-apply filters
  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}

function cmdExports(projectRoot, config, opts) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan exports <pattern>'); process.exit(1); }

  let regex;
  try { regex = new RegExp(keyword, 'i'); }
  catch (err) {
    console.error(`Invalid regex: ${keyword} — ${err.message}`);
    process.exit(1);
  }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  const matches = all.filter(r => {
    if (!r.header.exports || !Array.isArray(r.header.exports)) return false;
    return r.header.exports.some(e => regex.test(e));
  });

  // Re-apply domain/layer filters
  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}

function cmdSummary(projectRoot, config, opts) {
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  if (results.length === 0) { console.log('No @header blocks found.'); return; }

  const domains = {};
  for (const r of results) {
    const d = r.header.domain || '(none)';
    const l = r.header.layer || '(none)';
    if (!domains[d]) domains[d] = {};
    if (!domains[d][l]) domains[d][l] = 0;
    domains[d][l]++;
  }

  const scopeLabel = opts.scope ? ` (scope: ${opts.scope})` : '';
  console.log(`\n${C.bold}Code Header Summary${scopeLabel}${C.reset}`);
  console.log('─'.repeat(55));

  for (const [domain, layerMap] of Object.entries(domains).sort()) {
    const total = Object.values(layerMap).reduce((a, b) => a + b, 0);
    const detail = Object.entries(layerMap).sort()
      .map(([l, c]) => `${l}×${c}`).join(', ');
    console.log(`${C.green}${domain.padEnd(15)}${C.reset} : ${String(total).padStart(3)} files  ${C.dim}(${detail})${C.reset}`);
  }

  console.log('─'.repeat(55));
  console.log(`Total: ${C.bold}${results.length}${C.reset} files across ${Object.keys(domains).length} domains`);
}

function cmdDepends(projectRoot, config, opts) {
  const target = opts.commandArg;
  if (!target) { console.error('Usage: code-scan depends <module>'); process.exit(1); }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });

  // Find target file
  const targetResult = all.find(r =>
    r.header.module === target ||
    r.file === target ||
    r.file.replace(path.extname(r.file), '') === target
  );

  // Reverse deps: who depends on target
  const dependedBy = all.filter(r => {
    if (!r.header.depends) return false;
    return r.header.depends.some(d =>
      d.includes(target) || path.basename(d).replace(path.extname(d), '') === target
    );
  });

  // Forward deps: what target depends on
  const dependsOn = [];
  if (targetResult && targetResult.header.depends) {
    for (const dep of targetResult.header.depends) {
      const found = all.find(r => r.path.includes(dep) || r.path.endsWith(dep));
      dependsOn.push({ ref: dep, resolved: found || null });
    }
  }

  const label = targetResult
    ? `${C.bold}${targetResult.header.module}${C.reset} ${C.cyan}[${targetResult.header.layer}]${C.reset}`
    : `${C.bold}${target}${C.reset}`;
  console.log(`\n${label}`);

  console.log(`\n  ${C.yellow}depended by:${C.reset}`);
  if (dependedBy.length > 0) {
    for (const r of dependedBy) console.log(`    ← ${r.file} ${C.cyan}[${r.header.layer}]${C.reset}`);
  } else {
    console.log(`    ${C.dim}(none)${C.reset}`);
  }

  console.log(`\n  ${C.yellow}depends on:${C.reset}`);
  if (dependsOn.length > 0) {
    for (const d of dependsOn) {
      if (d.resolved) console.log(`    → ${d.resolved.file} ${C.cyan}[${d.resolved.header.layer}]${C.reset}`);
      else console.log(`    → ${d.ref} ${C.dim}(not found)${C.reset}`);
    }
  } else {
    console.log(`    ${C.dim}(none)${C.reset}`);
  }
}

function cmdMissing(projectRoot, config, opts) {
  const { noHeader } = scanAll(projectRoot, config, opts);
  if (noHeader.length === 0) {
    console.log(`${C.green}All files have @header blocks.${C.reset}`);
    return;
  }
  for (const r of noHeader) {
    console.log(`${C.yellow}[missing]${C.reset}  ${r.path}`);
  }
  console.log(`${C.dim}\n${noHeader.length} file(s) without @header${C.reset}`);
}

// ═══════════════════════════════════════════
// Code Map — writer/inspector commands (F-003/F-004/F-005/F-006/F-008)
// ═══════════════════════════════════════════

function dirExistsSomewhereUnder(root, name) {
  let found = false;
  function walk(d, depth) {
    if (found || depth > 6) return;
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      if (e.name === name) { found = true; return; }
      if (e.name === 'node_modules' || e.name === '.git' || e.name === '.opal') continue;
      walk(path.join(d, e.name), depth + 1);
      if (found) return;
    }
  }
  walk(root, 0);
  return found;
}

// ── discover (F-003) ─────────────────────────────────────────────────────

function inferScopes(projectRoot, config) {
  const scopes = {};
  if (config.scopes && Object.keys(config.scopes).length > 0) {
    for (const [name, rel] of Object.entries(config.scopes)) {
      const root = rel.endsWith('/') ? rel : rel + '/';
      scopes[name] = { root, anchors: [], stripPrefix: [], readonly: false };
    }
    return scopes;
  }
  let entries;
  try { entries = fs.readdirSync(projectRoot, { withFileTypes: true }); } catch { entries = []; }
  for (const e of entries) {
    if (!e.isDirectory() || e.name.startsWith('.')) continue;
    if ((config.exclude || []).includes(e.name)) continue;
    scopes[e.name] = { root: e.name + '/', anchors: [], stripPrefix: [], readonly: false };
  }
  return scopes;
}

function inferAnchors(scopeRootAbs) {
  const found = new Set();
  function walk(d, rel, depth) {
    if (depth > 3) return;
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    const hasManifest = entries.some(e => e.isFile() && BUILD_MANIFESTS.includes(e.name));
    if (hasManifest && rel) { found.add(rel); return; }
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      if (e.name === 'node_modules' || e.name === '.git' || e.name === '.opal') continue;
      walk(path.join(d, e.name), rel ? `${rel}/${e.name}` : e.name, depth + 1);
    }
  }
  if (fs.existsSync(scopeRootAbs)) walk(scopeRootAbs, '', 0);
  if (found.size > 0) return Array.from(found).sort();

  let entries;
  try { entries = fs.readdirSync(scopeRootAbs, { withFileTypes: true }); } catch { entries = []; }
  const dirs = entries.filter(e => e.isDirectory() && !e.name.startsWith('.')).map(e => e.name);
  if (dirs.length >= 1) return dirs.sort();
  return [];
}

function inferStripPrefix(scopeRootAbs, anchor) {
  const base = anchor ? path.join(scopeRootAbs, anchor) : scopeRootAbs;
  const found = [];
  for (const cand of STRIP_CANDIDATES) {
    const candNoSlash = cand.replace(/\/$/, '');
    if (fs.existsSync(path.join(base, candNoSlash))) found.push(cand);
  }
  return found;
}

function inferExclude(projectRoot, scopes) {
  const candidates = ['target', 'out', 'bin', 'obj', '.gradle', 'generated', 'coverage'];
  const extra = [];
  for (const cand of candidates) {
    let exists = false;
    for (const s of Object.values(scopes)) {
      const root = path.resolve(projectRoot, s.root);
      if (dirExistsSomewhereUnder(root, cand)) { exists = true; break; }
    }
    if (exists) extra.push(cand);
  }
  return Array.from(new Set([...DEFAULT_CONFIG.exclude, ...extra]));
}

function cmdDiscover(projectRoot, config, opts) {
  buildCtx(projectRoot, config); // surfaces schema errors on an existing (invalid) index

  const outPath = opts.discoverOut ? path.resolve(projectRoot, opts.discoverOut) : path.join(projectRoot, CODE_MAP_DIR, 'index.json');
  const dryRun = !!opts.dryRun;

  if (!dryRun && fs.existsSync(outPath)) {
    return codeMapErrorExit('index_exists');
  }

  const scopes = inferScopes(projectRoot, config);
  for (const scope of Object.values(scopes)) {
    const rootAbs = path.resolve(projectRoot, scope.root);
    scope.anchors = inferAnchors(rootAbs);
    const stripSet = new Set();
    if (scope.anchors.length > 0) {
      for (const a of scope.anchors) for (const sp of inferStripPrefix(rootAbs, a)) stripSet.add(sp);
    } else {
      for (const sp of inferStripPrefix(rootAbs, null)) stripSet.add(sp);
    }
    scope.stripPrefix = Array.from(stripSet);
  }

  const layerRules = [];
  for (const layer of CODE_LAYER_STANDARD) {
    let exists = false;
    for (const s of Object.values(scopes)) {
      if (dirExistsSomewhereUnder(path.resolve(projectRoot, s.root), layer)) { exists = true; break; }
    }
    if (exists) layerRules.push({ match: `**/${layer}/**`, layer });
  }

  const exclude = inferExclude(projectRoot, scopes);

  const draft = {
    version: CODE_MAP_VERSION,
    origin: 'discover',
    status: 'draft',
    generatedAt: new Date().toISOString(),
    note: 'OWNER REVIEW REQUIRED — readonly/anchors/stripPrefix 확인 후 status를 reviewed로 변경',
    scopes,
    domains: {},
    layerRules,
    exclude,
  };

  if (dryRun) {
    if (opts.output === 'json') console.log(JSON.stringify({ ok: true, dryRun: true, index: draft }));
    else console.log(`(dry-run) scopes=${Object.keys(scopes).length} layerRules=${layerRules.length} exclude=${exclude.length}`);
    return;
  }

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(draft, null, 2) + '\n');

  const summary = { ok: true, out: path.relative(projectRoot, outPath), scopes: Object.keys(scopes).length, counts: { scopes: Object.keys(scopes).length, layerRules: layerRules.length, exclude: exclude.length } };
  if (opts.output === 'json') console.log(JSON.stringify(summary));
  else console.log(`Created ${summary.out} — scopes=${summary.counts.scopes} layerRules=${summary.counts.layerRules} exclude=${summary.counts.exclude}`);
}

// ── scaffold (F-004) ─────────────────────────────────────────────────────

function collectDirsWithCodeFiles(scopeRootAbs, projectRoot, config, index) {
  const excludeDirs = new Set([...(config.exclude || []), ...((index && index.exclude) || [])]);
  const excludePatterns = config.excludePatterns || [];
  const results = [];
  function walk(d) {
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    const files = [];
    for (const e of entries) {
      if (e.isDirectory()) {
        if (excludeDirs.has(e.name)) continue;
        walk(path.join(d, e.name));
      } else if (e.isFile() && config.extensions.includes(path.extname(e.name))) {
        const rel = toPosixRel(projectRoot, path.join(d, e.name));
        if (isExcluded(rel, e.name, excludePatterns)) continue;
        files.push(e.name);
      }
    }
    if (files.length > 0) {
      results.push({ dirAbs: d, dirRel: toPosixRel(projectRoot, d), files: files.sort() });
    }
  }
  if (fs.existsSync(scopeRootAbs)) walk(scopeRootAbs);
  return results;
}

function orderFileEntry(entry) {
  const ordered = {};
  for (const f of WORKER_FIELDS) {
    if (hasOwn(entry, f)) ordered[f] = entry[f];
  }
  if (hasOwn(entry, 'module')) ordered.module = entry.module;
  if (hasOwn(entry, 'draft')) ordered.draft = entry.draft;
  for (const k of Object.keys(entry)) {
    if (!hasOwn(ordered, k)) ordered[k] = entry[k];
  }
  return ordered;
}

function orderFilesObject(filesObj) {
  const result = {};
  for (const basename of Object.keys(filesObj).sort()) {
    result[basename] = orderFileEntry(filesObj[basename]);
  }
  return result;
}

function mergeManifest(existing, entry) {
  const diskFiles = new Set(entry.files);
  const added = [];
  const pruned = [];
  const files = {};
  const existingFiles = (existing && existing.files) || {};

  for (const basename of entry.files) {
    if (hasOwn(existingFiles, basename)) {
      const prev = Object.assign({}, existingFiles[basename]);
      const hasDesc = typeof prev.description === 'string' && prev.description.trim() !== '';
      if (hasDesc) delete prev.draft; else prev.draft = true;
      files[basename] = prev;
    } else {
      files[basename] = { description: '', exports: [], draft: true };
      added.push(basename);
    }
  }
  for (const basename of Object.keys(existingFiles)) {
    if (!diskFiles.has(basename)) pruned.push(basename);
  }

  const manifest = { version: CODE_MAP_VERSION, scope: entry.scopeName, dir: entry.dirRel };
  if (existing && hasOwn(existing, 'package')) manifest.package = existing.package;
  manifest.files = orderFilesObject(files);

  return { manifest, pruned, added };
}

function listManifestFiles(dir) {
  const out = [];
  function walk(d) {
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full);
      else if (e.isFile() && e.name.endsWith('.json')) out.push(full);
    }
  }
  walk(dir);
  return out;
}

function cmdScaffold(projectRoot, config, opts) {
  const ctx = buildCtx(projectRoot, config);
  if (!ctx.codeMap.present) return codeMapErrorExit('index_missing');

  const index = ctx.codeMap.index;
  let scopeNames = Object.keys(index.scopes || {});
  if (opts.scope) {
    if (!index.scopes[opts.scope]) { process.stderr.write(`Error: Unknown scope "${opts.scope}"\n`); process.exit(1); }
    scopeNames = [opts.scope];
  }

  const perDir = [];
  const manifestOwner = new Map(); // manifestAbs -> dirRel (collision detection)
  const collisions = [];

  for (const scopeName of scopeNames) {
    const scope = index.scopes[scopeName];
    const scopeRootAbs = path.resolve(projectRoot, scope.root);
    const dirsWithFiles = collectDirsWithCodeFiles(scopeRootAbs, projectRoot, config, index);
    for (const d of dirsWithFiles) {
      const mp = mirrorPathForDir(d.dirRel, scopeName, scope);
      if (mp.skipped) continue;
      const manifestRel = `${CODE_MAP_DIR}/${scopeName}/${mp.mirrorRel}.json`;
      const manifestAbs = path.join(projectRoot, manifestRel);
      if (manifestOwner.has(manifestAbs)) {
        collisions.push({ manifest: manifestRel, a: manifestOwner.get(manifestAbs), b: d.dirRel });
      } else {
        manifestOwner.set(manifestAbs, d.dirRel);
      }
      perDir.push({ scopeName, dirRel: d.dirRel, files: d.files, manifestAbs, manifestRel });
    }
  }

  if (collisions.length > 0) {
    return codeMapErrorExit('mirror_collision', { collisions });
  }

  const created = [], updated = [], unchanged = [], addedAll = [], prunedAll = [];
  const dryRun = !!opts.dryRun;

  for (const entry of perDir) {
    let existing = null;
    if (fs.existsSync(entry.manifestAbs)) {
      try { existing = JSON.parse(fs.readFileSync(entry.manifestAbs, 'utf8')); } catch { existing = null; }
    }
    const { manifest, pruned, added } = mergeManifest(existing, entry);
    const serialized = JSON.stringify(manifest, null, 2) + '\n';
    const isNew = !fs.existsSync(entry.manifestAbs);
    const prevContent = isNew ? null : fs.readFileSync(entry.manifestAbs, 'utf8');
    const changed = isNew || prevContent !== serialized;

    if (changed && !dryRun) {
      fs.mkdirSync(path.dirname(entry.manifestAbs), { recursive: true });
      fs.writeFileSync(entry.manifestAbs, serialized);
    }

    if (isNew) created.push(entry.manifestRel);
    else if (changed) updated.push(entry.manifestRel);
    else unchanged.push(entry.manifestRel);
    addedAll.push(...added.map(f => `${entry.manifestRel}:${f}`));
    prunedAll.push(...pruned.map(f => `${entry.manifestRel}:${f}`));
  }

  const validManifestPaths = new Set(perDir.map(e => e.manifestAbs));
  const staleList = [];
  for (const scopeName of scopeNames) {
    const scopeMapDir = path.join(projectRoot, CODE_MAP_DIR, scopeName);
    if (!fs.existsSync(scopeMapDir)) continue;
    for (const manifestAbs of listManifestFiles(scopeMapDir)) {
      if (!validManifestPaths.has(manifestAbs)) staleList.push(toPosixRel(projectRoot, manifestAbs));
    }
  }

  const result = {
    ok: true,
    created: created.length, updated: updated.length, unchanged: unchanged.length,
    added: addedAll, pruned: prunedAll, stale: staleList, skipped: [],
  };
  if (opts.output === 'json') console.log(JSON.stringify(result));
  else console.log(`scaffold: created=${result.created} updated=${result.updated} unchanged=${result.unchanged} added=${addedAll.length} pruned=${prunedAll.length} stale=${staleList.length}`);
}

// ── target (F-005) ───────────────────────────────────────────────────────

function cmdTarget(projectRoot, config, opts) {
  const rel = opts.commandArg;
  if (!rel) { console.error('Usage: code-scan target <file>'); process.exit(1); }
  const ctx = buildCtx(projectRoot, config);
  const result = decideTarget(rel, ctx);
  if (opts.output === 'json') { console.log(JSON.stringify(result)); return; }
  console.log(`write_to: ${result.write_to}`);
  console.log(`reason:   ${result.reason}`);
  if (result.manifest) console.log(`manifest: ${result.manifest}`);
}

// ── validate (F-006/F-007) ───────────────────────────────────────────────

function isBlank(v) {
  if (v === undefined || v === null) return true;
  if (typeof v === 'string') return v.trim() === '';
  if (Array.isArray(v)) return v.length === 0;
  return false;
}

function hasSubstantiveContent(entry) {
  if (!entry) return false;
  return WORKER_FIELDS.some(f => hasOwn(entry, f) && !isBlank(entry[f]));
}

function normalizeExportId(raw) {
  if (typeof raw !== 'string') return '';
  const trimmed = raw.trim();
  if (!trimmed) return '';
  const parts = trimmed.split(/\s+/);
  return parts[parts.length - 1];
}

// dirRel: 이 디렉토리(manifest.dir)의 프로젝트 루트 기준 상대 경로 — scaffold 열거
// (collectDirsWithCodeFiles)와 동일한 판정을 구조 패스에도 적용하기 위해 필요하다
// (config.exclude ∪ index.exclude 세그먼트 + excludePatterns, 077 결함 D).
function listCodeFilesInDir(dirAbs, dirRel, config, excludeDirs, excludePatterns) {
  if (hasExcludedSegment(dirRel || '', excludeDirs)) return [];
  let entries;
  try { entries = fs.readdirSync(dirAbs, { withFileTypes: true }); } catch { return []; }
  const out = [];
  for (const e of entries) {
    if (e.isFile() && config.extensions.includes(path.extname(e.name))) {
      const rel = dirRel ? `${dirRel}/${e.name}` : e.name;
      if (isExcluded(rel, e.name, excludePatterns)) continue;
      out.push(e.name);
    }
  }
  return out;
}

function cmdValidate(projectRoot, config, opts) {
  const ctx = buildCtx(projectRoot, config);

  const changedMode = opts.changed !== null && opts.changed !== undefined;
  const skipped = [];
  let fileList;

  if (changedMode) {
    let rawList;
    if (opts.changed === '-') {
      const stdinRaw = fs.readFileSync(0, 'utf8');
      rawList = stdinRaw.split('\n').map(s => s.trim()).filter(Boolean);
    } else {
      rawList = opts.changed.split(',').map(s => s.trim()).filter(Boolean);
    }
    const excludeDirs = config.exclude || [];
    const excludePatterns = mergeExcludePatterns(config, opts);
    fileList = [];
    for (const raw of rawList) {
      const abs = path.isAbsolute(raw) ? raw : path.resolve(projectRoot, raw);
      const rel = toPosixRel(projectRoot, abs);
      if (!fs.existsSync(abs)) { skipped.push({ file: rel, reason: 'not_found' }); continue; }
      if (!fs.statSync(abs).isFile()) { skipped.push({ file: rel, reason: 'not_file' }); continue; }
      if (!config.extensions.includes(path.extname(abs))) { skipped.push({ file: rel, reason: 'unsupported_extension' }); continue; }
      // 전체 스캔(walkDir/isExcluded)과 동일한 제외 규칙 — exclude 디렉토리 세그먼트 우선,
      // 그 다음 excludePatterns(와일드카드). 둘 중 하나라도 매치되면 판정에서 제외한다.
      if (hasExcludedSegment(rel, excludeDirs)) { skipped.push({ file: rel, reason: 'excluded_dir' }); continue; }
      if (isExcluded(rel, path.basename(abs), excludePatterns)) { skipped.push({ file: rel, reason: 'excluded_pattern' }); continue; }
      fileList.push(abs);
    }
  } else {
    if (opts.scope && ctx.codeMap.present && ctx.codeMap.index.scopes && !ctx.codeMap.index.scopes[opts.scope] && !config.scopes[opts.scope]) {
      process.stderr.write(`Error: Unknown scope "${opts.scope}"\n`); process.exit(1);
    }
    fileList = discoverFiles(projectRoot, config, { scope: opts.scope || null, targetPath: null, excludePatterns: [] });
  }

  const violations = [];
  let totalCount = 0, inlineCount = 0, manifestCount = 0;

  for (const fileAbs of fileList) {
    totalCount++;
    const relPath = toPosixRel(projectRoot, fileAbs);
    const basename = path.basename(fileAbs);
    const inlineHeader = extractHeader(fileAbs);
    const mctx = ctx.codeMap.present ? resolveManifestContext(relPath, ctx) : null;
    const fe = (mctx && mctx.manifest && mctx.manifest.files && mctx.manifest.files[basename]) || null;

    const covered = inlineHeader !== null || fe !== null;
    if (!covered) {
      // 매니페스트가 이 디렉토리를 관리 중(scaffold됨)인데 files{}에 키가 없는 경우는
      // 구조적 결손 — git 상태와 무관하게 'no_entry'(항상 차단, 기존 동작 불변).
      // 그 외(관리 매니페스트 자체가 없음 — 순수 인라인 트랙)는 git 기준 2분류.
      const managedByManifest = !!(mctx && mctx.manifest);
      const sub = managedByManifest ? 'no_entry' : classifyUncovered(projectRoot, relPath);
      violations.push({ code: 'uncovered', sub, file: relPath, detail: '' });
      continue;
    }
    if (inlineHeader !== null) inlineCount++; else manifestCount++;

    const resolved = resolveHeader(fileAbs, ctx);
    const required = ['module', 'layer', 'domain', 'description', 'exports'];
    const missingFields = required.filter(f => !resolved || resolved[f] === undefined);
    if (missingFields.length > 0) {
      violations.push({ code: 'uncovered', sub: 'incomplete', file: relPath, detail: missingFields.join(',') });
    }

    if (inlineHeader !== null && fe !== null && hasSubstantiveContent(fe)) {
      violations.push({ code: 'conflict', sub: 'inline_shadowed', file: relPath, manifest: mctx.manifestRel, key: basename, detail: '' });
    }

    if (inlineHeader === null && fe !== null) {
      const blank = typeof fe.description === 'string' && fe.description.trim() === '';
      if (fe.draft === true || blank) {
        violations.push({ code: 'draft', file: relPath, manifest: mctx.manifestRel, key: basename, detail: '' });
      }
    }

    if (resolved && Array.isArray(resolved.exports) && resolved.exports.length > 0) {
      let text = null;
      for (const idRaw of resolved.exports) {
        const id = normalizeExportId(idRaw);
        if (!id) continue;
        if (text === null) { try { text = fs.readFileSync(fileAbs, 'utf8'); } catch { text = ''; } }
        if (!text.includes(id)) {
          violations.push({ code: 'exports_not_found', file: relPath, manifest: mctx ? mctx.manifestRel : undefined, key: basename, detail: idRaw });
        }
      }
    }
  }

  // Manifest-structural pass (orphan/dir_missing, worker_scope_violation) — full scope regardless of --changed
  if (ctx.codeMap.present) {
    const index = ctx.codeMap.index;
    const scopeNames = opts.scope ? [opts.scope] : Object.keys(index.scopes || {});
    for (const scopeName of scopeNames) {
      const scopeObj = index.scopes[scopeName];
      if (!scopeObj) continue;
      const scopeMapDir = path.join(projectRoot, CODE_MAP_DIR, scopeName);
      if (!fs.existsSync(scopeMapDir)) continue;

      for (const manifestAbs of listManifestFiles(scopeMapDir)) {
        const manifest = loadManifest(manifestAbs, ctx);
        if (!manifest) continue;
        const manifestRel = toPosixRel(projectRoot, manifestAbs);

        if (typeof manifest.version !== 'number' || manifest.version !== CODE_MAP_VERSION) {
          throw new CodeMapFatalError('unsupported_version');
        }

        const actualMirrorRel = toPosixRel(scopeMapDir, manifestAbs).replace(/\.json$/, '');
        const scopeMismatch = manifest.scope !== scopeName;
        if (scopeMismatch) {
          violations.push({ code: 'worker_scope_violation', sub: 'scope_mismatch', manifest: manifestRel, detail: String(manifest.scope) });
        } else {
          const mp = mirrorPathForDir(manifest.dir || '', scopeName, scopeObj);
          const expected = mp.skipped ? null : mp.mirrorRel;
          if (expected === null || expected !== actualMirrorRel) {
            violations.push({ code: 'worker_scope_violation', sub: 'dir_mismatch', manifest: manifestRel, detail: String(manifest.dir) });
          }
        }

        const dirAbs = path.resolve(projectRoot, manifest.dir || '');
        const dirExists = fs.existsSync(dirAbs) && fs.statSync(dirAbs).isDirectory();
        if (!dirExists) {
          violations.push({ code: 'orphan', sub: 'dir_missing', manifest: manifestRel, file: manifest.dir, detail: '' });
        }

        const manifestFiles = manifest.files || {};
        const manifestKeys = Object.keys(manifestFiles);
        // scaffold 열거(collectDirsWithCodeFiles)와 동일한 필터(config.exclude ∪ index.exclude
        // 세그먼트 + excludePatterns)를 적용해 정당히 제외된 파일이 files_key_removed로
        // 오탐되지 않도록 한다(077 결함 D).
        const structExcludeDirs = [...(config.exclude || []), ...((index && index.exclude) || [])];
        const structExcludePatterns = mergeExcludePatterns(config, opts);
        const diskBasenames = dirExists
          ? listCodeFilesInDir(dirAbs, manifest.dir || '', config, structExcludeDirs, structExcludePatterns)
          : [];
        const diskSet = new Set(diskBasenames);
        const keySet = new Set(manifestKeys);

        for (const key of manifestKeys) {
          if (!diskSet.has(key)) {
            violations.push({ code: 'orphan', sub: 'file_missing', manifest: manifestRel, key, file: `${manifest.dir}/${key}`, detail: '' });
            violations.push({ code: 'worker_scope_violation', sub: 'files_key_added', manifest: manifestRel, key, detail: '' });
          }
        }
        for (const bn of diskBasenames) {
          if (!keySet.has(bn)) {
            violations.push({ code: 'worker_scope_violation', sub: 'files_key_removed', manifest: manifestRel, key: bn, detail: '' });
          }
        }

        const pkg = manifest.package || null;
        if (pkg && hasOwn(pkg, 'layer')) {
          violations.push({ code: 'worker_scope_violation', sub: 'layer_in_manifest', manifest: manifestRel, detail: '' });
        }
        if (pkg && hasOwn(pkg, 'domain')) {
          violations.push({ code: 'worker_scope_violation', sub: 'domain_in_manifest', manifest: manifestRel, detail: '' });
        }
        for (const [key, fe] of Object.entries(manifestFiles)) {
          if (fe && hasOwn(fe, 'layer')) {
            violations.push({ code: 'worker_scope_violation', sub: 'layer_in_manifest', manifest: manifestRel, key, detail: '' });
          }
          if (fe && hasOwn(fe, 'domain')) {
            violations.push({ code: 'worker_scope_violation', sub: 'domain_in_manifest', manifest: manifestRel, key, detail: '' });
          }
          if (fe && hasOwn(fe, 'module')) {
            const stem = deriveStem(key);
            if (fe.module !== stem) {
              violations.push({ code: 'worker_scope_violation', sub: 'module_override', manifest: manifestRel, key, detail: String(fe.module) });
            }
          }
        }
      }
    }
  }

  const counts = {
    orphan: violations.filter(v => v.code === 'orphan').length,
    uncovered: violations.filter(v => v.code === 'uncovered').length,
    conflict: violations.filter(v => v.code === 'conflict').length,
    draft: violations.filter(v => v.code === 'draft').length,
    exports_not_found: violations.filter(v => v.code === 'exports_not_found').length,
    worker_scope_violation: violations.filter(v => v.code === 'worker_scope_violation').length,
    newly_uncovered: violations.filter(v => v.code === 'uncovered' && v.sub === 'newly_uncovered').length,
    pre_existing: violations.filter(v => v.code === 'uncovered' && v.sub === 'pre_existing').length,
  };
  const covered = inlineCount + manifestCount;
  const percent = totalCount === 0 ? 100 : Math.round((covered / totalCount) * 1000) / 10;
  // 'uncovered:pre_existing'만 비차단 — 나머지 5종(orphan/conflict/draft/exports_not_found/
  // worker_scope_violation) + 'uncovered'의 no_entry/incomplete/newly_uncovered 서브는 차단 불변.
  const blockingViolations = violations.filter(v => !(v.code === 'uncovered' && v.sub === 'pre_existing'));
  const ok = blockingViolations.length === 0;

  const result = {
    ok,
    command: 'validate',
    mode: changedMode ? 'changed' : 'full',
    coverage: { total: totalCount, inline: inlineCount, manifest: manifestCount, covered, percent },
    counts,
    violations,
    skipped,
  };

  if (opts.output === 'json') console.log(JSON.stringify(result));
  else console.log(`validate: ${ok ? 'OK' : blockingViolations.length + ' violation(s)'} — coverage ${percent}% (${covered}/${totalCount})`);

  process.exit(ok ? 0 : 2);
}

// ── feature (F-008) ──────────────────────────────────────────────────────

function cmdFeature(projectRoot, config, opts) {
  const id = opts.commandArg;
  if (!id) { console.error('Usage: code-scan feature <id>'); process.exit(1); }

  const configuredScopes = Object.keys(config.scopes || {});
  const scopeNames = opts.scope ? [opts.scope] : (configuredScopes.length > 0 ? configuredScopes : [null]);

  const result = {};
  for (const scopeName of scopeNames) {
    const scopeOpts = Object.assign({}, opts, { scope: scopeName, domain: null, layer: null });
    const all = scanHeaders(projectRoot, config, scopeOpts);
    const matches = all.filter(r => r.header.feature === id);
    if (matches.length > 0) {
      const groupKey = scopeName || '(root)';
      const group = {};
      for (const m of matches) group[m.path] = m.header;
      result[groupKey] = group;
    }
  }

  if (opts.output === 'json') { console.log(JSON.stringify(result)); return; }
  const keys = Object.keys(result);
  if (keys.length === 0) { console.log('No matches.'); return; }
  for (const scopeName of keys) {
    console.log(`\n${C.green}[${scopeName}]${C.reset}`);
    for (const [p, h] of Object.entries(result[scopeName])) {
      console.log(`  ${p} ${C.dim}—${C.reset} ${h.description || ''}`);
    }
  }
}

// ═══════════════════════════════════════════
// Main
// ═══════════════════════════════════════════

function main() {
  const opts = parseArgs(process.argv);

  if (opts.command === 'help')    { console.log(USAGE); return; }
  if (opts.command === 'version') { console.log(`code-scan v${VERSION}`); return; }

  const projectRoot = findProjectRoot();
  const config = loadConfig(projectRoot);

  const commands = {
    scan:     cmdScan,
    domain:   cmdDomain,
    layer:    cmdLayer,
    search:   cmdSearch,
    exports:  cmdExports,
    summary:  cmdSummary,
    depends:  cmdDepends,
    missing:  cmdMissing,
    discover: cmdDiscover,
    scaffold: cmdScaffold,
    target:   cmdTarget,
    validate: cmdValidate,
    feature:  cmdFeature,
  };

  const fn = commands[opts.command];
  if (!fn) {
    console.error(`Unknown command: "${opts.command}". Run with --help for usage.`);
    process.exit(1);
  }

  try {
    fn(projectRoot, config, opts);
  } catch (err) {
    if (err instanceof CodeMapFatalError) { codeMapErrorExit(err.code); return; }
    throw err;
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  mirrorPathForDir,
  decideTarget,
  loadCodeMap,
  loadConfig,
  findProjectRoot,
  resolveScope,
  matchLayerRule,
  matchDomain,
  resolveHeader,
  extractHeader,
};

// 변경이력
// v1.0.0 — 초기 작성 — scan/domain/layer/search/summary/depends/missing 커맨드
// v1.1.0 — 2026-04-12 — exports 커맨드 추가 — exports 필드 전용 검색 (109)
// v1.2.0 — 2026-04-15 — search/exports 커맨드 정규식 기반 전환 (default regex, case-insensitive) (118)
// v1.3.0 — 2026-07-28 — code-map 헤더 작성층 신설: discover/scaffold/target/validate/feature 5서브명령 +
//                       5단 상속 해석(resolveHeader)·경로 사상(mirrorPathForDir)·headerSource 스위치 +
//                       require.main 가드·module.exports 추가 (code-map 부재 프로젝트 동작 무변화) (077)
// v1.3.1 — 2026-07-28 — validate --changed 경로 판정에 config.exclude(디렉토리 세그먼트)·
//                       excludePatterns(와일드카드) 필터를 전체 스캔과 동일하게 적용 —
//                       제외 경로는 skipped[]에 {file, reason:'excluded_dir'|'excluded_pattern'}로
//                       기록되고 counts/coverage에서 빠짐. 기존 skipped[] 3항목(존재/파일/확장자)도
//                       동일한 {file, reason} 표기로 정비 (077 F-6)
// v1.3.2 — 2026-07-28 — extractHeaderFromContent가 "@header" 토큰과 여는 "{" 사이 근접성을
//                       요구하도록 수정 — 산문으로 "@header"를 언급한 문서가 뒤따르는 무관한
//                       JSON 블록을 자신의 헤더로 오인하던 결함 C 수정. 근접 판정은 신규
//                       findProximateHeaderIndex로 단일화하고 기존 hasNearbyHeaderBlock(git HEAD
//                       회귀 판정 경로)도 동일 함수를 공유하도록 정리(중복 로직 신설 없음) (077 결함 C)
// v1.3.3 — 2026-07-29 — validate 구조 패스(listCodeFilesInDir)가 scaffold 열거
//                       (collectDirsWithCodeFiles)와 동일한 config.exclude ∪ index.exclude
//                       (디렉토리 세그먼트) + excludePatterns 필터를 적용하도록 수정 — scaffold가
//                       정당히 제외한 파일이 files_key_removed로 오탐되던 결함 D 수정
//                       (오탐 제거로 validate 위반 수가 감소하는 방향, 기존 hasExcludedSegment·
//                       isExcluded·mergeExcludePatterns 재사용, 신규 로직 없음) (077 결함 D)
