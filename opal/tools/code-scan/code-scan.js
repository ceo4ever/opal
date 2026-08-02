#!/usr/bin/env node
/**
 * @header {
 *   "module": "code-scan",
 *   "layer": "util",
 *   "domain": "code-scan",
 *   "description": "OPAL @header 메타블록 스캐너 CLI — 코드 파일의 인라인/code-map @header를 파싱해 도메인·레이어·의존관계를 조회하고, discover/scaffold/target/validate/feature 5서브명령으로 code-map 헤더 작성층(외부 매니페스트 기반 상속·워커 권한 경계 집행·uncovered 2분류)을 관리한다. headerSource는 inline|manifest 2택 전역 단일 키이며, resolveHeaderSource가 CLI --header-source > 전역 config 2층으로 실행당 1회 판정해 미설정·무효값이면 전 명령을 차단한다. 확정된 모드는 조회·작성·검증 전 경로를 직접 지배한다 — resolveHeader는 inline이면 인라인 단독, manifest면 files>package>layerRules>domains 4단만 보고(index.json 부재는 stderr 1줄 비차단), decideTarget은 파일 상태를 보지 않고 모드에서 write_to/reason을 직결하며, scaffold는 inline에서 매니페스트를 만들지 않고 skipped 사유만 보고하고, validate는 모드별 단일 소스 커버리지(합산 폐기)와 구조 패스 분기를 적용해 결과에 모드를 실어 보낸다. 두 스코프 레지스트리(code-scan.json의 path 축약·객체형 / code-map index.json의 root)는 normalizeConfigScope·normalizeIndexScope가 {root, include, exclude} 단일 내부 형태로 정규화하고, 파일 집합 필터 판정은 isInScope 1곳에, 소속 스코프 판정은 resolveScopeIn(최장 root > include 매칭 > 사전순, 동률 include 경합은 scope_ambiguous) 1곳에 봉인한다. 그 필터는 열거(discoverFiles)·scaffold 열거(collectDirsWithCodeFiles)·validate 구조 패스(listCodeFilesInDir)·validate --changed·target(decideTarget) 5지점에 배선되며, target은 isFilteredOutOfScope를 경유해 필터 탈락 파일에 {write_to:'none', reason:'out_of_scope'}를 exit 0으로 돌려준다. scan <file> 명시 경로만 필터 면제다",
 *   "exports": ["mirrorPathForDir", "decideTarget", "loadCodeMap", "loadConfig", "findProjectRoot", "resolveScope", "matchLayerRule", "matchDomain", "resolveHeader", "extractHeader"],
 *   "note": "code-scan.js 자신은 프로젝트 .opal/code-map/index.json 부재로 인라인 전용 모드로 스캔됨 (태스크 077). 모드 판정 지점은 resolveHeaderSource 1곳으로 봉인되며, 허용 3구간(resolveHeaderSource/loadConfig/parseArgs) 밖에서는 확정값을 ctx.headerSource 읽기·buildCtx 파라미터 전달 형태로만 다룬다 — 중간 전달 변수명은 mode다 (태스크 080 TS-070). 스코프 단위 모드 선언 키는 존재하지 않는다 — 두 레지스트리 모두 해당 키를 무시하고 deprecationOnce로 키별 실행당 1회만 stderr 안내한다 (태스크 080 F-002). index.json에서 폐기된 스코프 단위 쓰기금지 플래그도 같은 방식으로 무시 + 안내되며 다른 모드로 흡수하지 않는다 — 기록 소스는 오직 전역 headerSource가 결정하므로 스코프 단위 예외 판정 분기는 존재하지 않는다 (태스크 080 F-004). 두 소스는 모드에 의해 상호 배타이므로 '인라인 단독 승리' 같은 병합 규칙이 존재하지 않으며, decideTarget의 reason 도메인은 header_source_inline / header_source_manifest / out_of_scope 3값으로 닫힌다 — 파일 존재 여부·인라인 보유 여부는 판정에 관여하지 않는다 (태스크 080 F-003)"
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

const VERSION = '1.4.0';
const HEADER_READ_BYTES = 8192;

const DEFAULT_CONFIG = {
  scopes: {},
  extensions: ['.py', '.js', '.ts', '.vue', '.jsx', '.tsx', '.svelte', '.kt', '.kts', '.java', '.swift'],
  exclude: ['node_modules', '__pycache__', '.git', 'dist', 'build', '.venv', 'env', '.next', '.nuxt', '.output'],
  excludePatterns: [],
  headerSource: null
};

// headerSource 값 도메인 — 2택. 구형 값은 남기지 않는다 (080 D-3).
const HEADER_SOURCE_VALUES = ['inline', 'manifest'];
const HEADER_SOURCE_DOC = '~/.opal/references/header-standard.md §7';
// 제거된 구형 값. 마이그레이션 안내를 위해 **이 1개소에서만** 식별한다 (080 D-3 / TS-066).
const HEADER_SOURCE_LEGACY = 'auto';

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
  --header-source <inline|manifest>
                        Header write/read source for this run (overrides config).
                        Required for every command unless set in config.
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

Exit codes (all commands): 1 = usage/schema error, or header source unresolved
                           (header_source_unset | header_source_invalid | code_scan_config_invalid)
Exit codes (validate): 0 = no violations, 1 = usage/schema error, 2 = violations found

Config:
  {project}/.opal/code-scan.json
  {
    "headerSource": "inline",
    "scopes": { "be": "workspace/backend/", "fe": "workspace/frontend/src/" },
    "extensions": [".py", ".js", ".ts", ".vue"],
    "exclude": ["node_modules", "__pycache__"],
    "excludePatterns": ["__init__.py", "test_*", "*.spec.ts"]
  }

  "headerSource" is required (inline | manifest). It is a single project-wide
  key — it is not overridable per scope. See ~/.opal/references/header-standard.md §7
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
    headerSource: null,   // CLI 원문 그대로 담기만 한다 — 유효성 판정은 resolveHeaderSource가 한다
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
    else if (a === '--header-source' && i + 1 < args.length) { opts.headerSource = args[++i]; }
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

// 설정을 **싣기만** 한다 — headerSource 유효성은 판정하지 않고 원문 그대로 통과시킨다.
// [MUST] 이 함수는 process.exit / throw 하지 않는다: code-map-hook.js가 main()을 거치지 않고
// 직접 호출하므로 여기서 종료하면 PostToolUse fail-safe가 붕괴한다 (080 §3.1.2 (B), H-2).
function loadConfig(projectRoot) {
  const configPath = path.join(projectRoot, '.opal', 'code-scan.json');
  if (!fs.existsSync(configPath)) {
    return Object.assign({}, DEFAULT_CONFIG, { configPresent: false, configError: null });
  }

  let user;
  try { user = JSON.parse(fs.readFileSync(configPath, 'utf8')); }
  catch { user = undefined; }

  if (!user || typeof user !== 'object' || Array.isArray(user)) {
    return Object.assign({}, DEFAULT_CONFIG, { configPresent: true, configError: 'config_parse_failed' });
  }

  // scopes 정규화 — 문자열 축약형과 {path, include, exclude} 객체형을 하나의 내부 형태(root)로
  // 통일한다 (080 §3.2.2 (A)). 스키마 위반은 여기서 **종료하지 않고** configError로만 표면화한다.
  const scopes = {};
  let scopeErrorDetail = null;
  const rawScopes = (user.scopes && typeof user.scopes === 'object' && !Array.isArray(user.scopes))
    ? user.scopes : {};
  for (const [name, raw] of Object.entries(rawScopes)) {
    const n = normalizeConfigScope(raw, name);
    if (!n.ok) { scopeErrorDetail = n.detail; break; }
    scopes[name] = n.scope;
  }

  return {
    extensions: user.extensions || DEFAULT_CONFIG.extensions,
    exclude: user.exclude || DEFAULT_CONFIG.exclude,
    excludePatterns: user.excludePatterns || [],
    scopes,
    headerSource: user.headerSource === undefined ? null : user.headerSource,
    configPresent: true,
    configError: scopeErrorDetail ? 'config_scope_invalid' : null,
    configErrorDetail: scopeErrorDetail,
  };
}

/**
 * 이 실행의 headerSource를 확정한다 — 도구 전체에서 **유일한** 모드 판정 지점이다.
 * CLI 플래그 > 전역 config 순으로 병합하고 유효성을 판정한다 (2층, 080 §3.1.2 (C)).
 * 스코프 단위 오버라이드는 존재하지 않는다 — 파일 단위 재판정 함수를 만들지 않는다.
 *
 * @returns {{ok:true, value:'inline'|'manifest'} |
 *           {ok:false, error:string, detail:string, where:string, fix:string, migration?:string}}
 */
function resolveHeaderSource(config, opts) {
  const cfg = config || {};
  const cli = (opts || {}).headerSource;

  // ① 설정 파일 자체가 깨졌다 — "미설정"과 구분한다
  if (cfg.configError === 'config_parse_failed') {
    return {
      ok: false,
      error: 'code_scan_config_invalid',
      detail: '.opal/code-scan.json을 JSON으로 파싱할 수 없습니다',
      where: 'config',
      fix: '.opal/code-scan.json의 JSON 문법을 고친 뒤 다시 실행하세요',
    };
  }

  // ②③ CLI 플래그 (최우선)
  if (cli !== null && cli !== undefined) {
    if (HEADER_SOURCE_VALUES.includes(cli)) return { ok: true, value: cli };
    return {
      ok: false,
      error: 'header_source_invalid',
      detail: String(cli),
      where: 'cli',
      fix: '--header-source 값은 ' + HEADER_SOURCE_VALUES.join(' 또는 ') + ' 중 하나여야 합니다',
    };
  }

  // ④ 전역 config 미설정
  const value = cfg.headerSource;
  if (value === null || value === undefined) {
    return {
      ok: false,
      error: 'header_source_unset',
      detail: '.opal/code-scan.json에 headerSource가 없습니다',
      where: 'config',
      fix: '"headerSource": "inline" 또는 "manifest"를 .opal/code-scan.json에 추가하거나 --header-source <inline|manifest>로 실행하세요',
    };
  }

  // ⑤ 무효값 — 구형 값은 전용 마이그레이션 안내를 덧붙인다
  if (!HEADER_SOURCE_VALUES.includes(value)) {
    const out = {
      ok: false,
      error: 'header_source_invalid',
      detail: String(value),
      where: 'config',
      fix: '.opal/code-scan.json의 headerSource는 ' + HEADER_SOURCE_VALUES.join(' 또는 ') + ' 중 하나여야 합니다',
    };
    if (value === HEADER_SOURCE_LEGACY) {
      out.migration = '구형 값 "' + HEADER_SOURCE_LEGACY + '"는 제거되었습니다 — 프로젝트 전체를 ' +
        HEADER_SOURCE_VALUES.join(' 또는 ') + ' 중 하나로 통일해 다시 지정하세요 (자동 변환하지 않습니다)';
    }
    return out;
  }

  // ⑥ 전역 config 유효값
  return { ok: true, value };
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

// 부정 의미를 이름에서 제거한 범용 패턴 매처 — include·exclude 양쪽이 같은 함수를 재사용한다
// (구 `isExcluded`의 개명, 080 §3.2.2 (B)).
// [MUST] opal/core/PRINCIPLES.md §2: "Remove a duplicated existing pattern before introducing a new one."
function matchesAnyPattern(relPath, fileName, patterns) {
  for (const p of patterns || []) {
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
// Scope normalization & filtering (080 F-002)
// ═══════════════════════════════════════════
//
// 두 레지스트리(.opal/code-scan.json · .opal/code-map/index.json)는 사용자 대면 키가 다르지만
// (`path` vs `root`) **내부 정규화 형태는 `root`로 통일**한다. 두 레지스트리 모두 모드 선언 키를
// 갖지 않는다 — include/exclude는 *파일 집합 필터*이지 *모드 선언*이 아니다 (080 §3.2.2 (A)).

// deprecated 안내는 **키별로 실행당 1회**다 (080 §3.2.2 (E) 안내 중복 계약).
// 전량 stderr — stdout JSON을 오염시키지 않는다 (brain_tool.py:793 json.loads 보호).
const _deprecationSeen = new Set();

function deprecationOnce(key, message) {
  if (_deprecationSeen.has(key)) return;
  _deprecationSeen.add(key);
  process.stderr.write('code-scan: [deprecated] ' + message + '\n');
}

// 폐기 안내가 아닌 **비차단 사유 노출**용 — 1회성·stderr 전용 계약은 deprecationOnce와 동일하고
// 접두만 다르다. "조용한 빈 결과 / 조용한 스킵"을 만들지 않기 위한 창구다 (080 §3.3.2 (A)(D)).
function noticeOnce(key, message) {
  if (_deprecationSeen.has(key)) return;
  _deprecationSeen.add(key);
  process.stderr.write('code-scan: ' + message + '\n');
}

// include/exclude 공통 스키마 검증 — 존재하면 string[]이어야 한다 (080 §3.2.2 (E), TS-075).
// 키 이름을 인자로 받아 두 필드가 같은 판정을 공유한다(중복 검증 로직 신설 없음).
function normalizePatternList(raw, key) {
  if (!hasOwn(raw, key) || raw[key] === undefined || raw[key] === null) return { ok: true, value: [] };
  const v = raw[key];
  if (!Array.isArray(v)) return { ok: false };
  for (const p of v) { if (typeof p !== 'string') return { ok: false }; }
  return { ok: true, value: v.slice() };
}

const SCOPE_MODE_KEY_HINT =
  'headerSource는 .opal/code-scan.json의 **최상위** 키 1개로만 설정합니다 (전역 단일 키, Task 080). ' +
  '근거: ' + HEADER_SOURCE_DOC;

/**
 * .opal/code-scan.json  scopes[name]: string | {path, include?, exclude?}
 *   "opal/"                               → { root: "opal/", include: [], exclude: [] }
 *   { path: "opal/", include: ["a/*.ts"] } → { root: "opal/", include: ["a/*.ts"], exclude: [] }
 * @returns {{ok:true, scope:{root:string, include:string[], exclude:string[]}} | {ok:false, detail:string}}
 */
function normalizeConfigScope(raw, scopeName) {
  const label = 'scopes."' + scopeName + '"';
  if (typeof raw === 'string') {
    if (raw.length === 0) return { ok: false, detail: label + '는 비어 있지 않은 문자열이어야 합니다' };
    return { ok: true, scope: { root: raw, include: [], exclude: [] } };
  }
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return { ok: false, detail: label + '는 문자열 또는 {path, include, exclude} 객체여야 합니다' };
  }
  if (typeof raw.path !== 'string' || raw.path.length === 0) {
    return { ok: false, detail: label + '.path는 비어 있지 않은 문자열이어야 합니다' };
  }
  const inc = normalizePatternList(raw, 'include');
  if (!inc.ok) return { ok: false, detail: label + '.include는 문자열 배열이어야 합니다' };
  const exc = normalizePatternList(raw, 'exclude');
  if (!exc.ok) return { ok: false, detail: label + '.exclude는 문자열 배열이어야 합니다' };

  // 사용자가 실제로 손대는 파일이 code-scan.json이므로 스코프 객체에 모드 키를 넣는 시도가
  // 가장 잦은 지점이다. 조용히 버리지 않고 안내한다 (080 §3.2.2 (A), TS-069).
  if (hasOwn(raw, 'headerSource')) {
    deprecationOnce('config_scope_header_source',
      label + '.headerSource는 지원하지 않습니다 — 이 키는 무시됩니다. ' + SCOPE_MODE_KEY_HINT);
  }

  return { ok: true, scope: { root: raw.path, include: inc.value, exclude: exc.value } };
}

/**
 * .opal/code-map/index.json  scopes[name]: {root, anchors?, stripPrefix?, include?, exclude?}
 * @returns {{ok:true, scope:object} | {ok:false}}
 */
function normalizeIndexScope(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return { ok: false };
  if (typeof raw.root !== 'string' || raw.root.length === 0) return { ok: false };
  const inc = normalizePatternList(raw, 'include');
  if (!inc.ok) return { ok: false };
  const exc = normalizePatternList(raw, 'exclude');
  if (!exc.ok) return { ok: false };

  // 모드 선언 키는 없다 — headerSource는 전역 1개뿐이다 (080 §3.1.2 (D), TS-005).
  if (hasOwn(raw, 'headerSource')) {
    deprecationOnce('index_scope_header_source',
      '.opal/code-map/index.json의 스코프 단위 headerSource는 지원하지 않습니다 — 이 키는 무시됩니다. ' +
      SCOPE_MODE_KEY_HINT);
  }

  // 제거된 키 — 값과 무관하게 **무시**한다. manifest로 흡수하지 않는다: 전역 단일 키 결정으로
  // 흡수할 자리 자체가 사라졌기 때문이다 (080 §3.4.2, F-6 AC). 흡수하면 스코프 예외가 되살아난다.
  // 이 안내 1줄이 동작 변화를 사용자에게 알리는 유일한 접점이므로 전역 설정 방법을 반드시 담는다.
  if (hasOwn(raw, 'readonly')) {
    deprecationOnce('index_scope_readonly',
      '.opal/code-map/index.json의 scopes[].readonly는 제거되었습니다 (Task 080) — 이 키는 무시됩니다. ' +
      '기록 소스는 .opal/code-scan.json의 전역 headerSource (inline 또는 manifest)로 설정하세요. ' +
      '근거: ' + HEADER_SOURCE_DOC);
  }

  return {
    ok: true,
    scope: {
      root: raw.root,
      anchors: Array.isArray(raw.anchors) ? raw.anchors.slice() : [],
      stripPrefix: Array.isArray(raw.stripPrefix) ? raw.stripPrefix.slice() : [],
      include: inc.value,
      exclude: exc.value,
    },
  };
}

/**
 * 스코프 필터의 유일한 판정 함수. 5개 적용 지점이 전부 이것만 호출한다 (080 §3.2.2 (B), F-8 AC).
 * @param {string} relPath   프로젝트 루트 기준 POSIX 파일 경로 (예: "opal/tools/x.js")
 * @param {{include: string[], exclude: string[]}} scopeDef  정규화된 스코프 정의
 * @returns {boolean}
 */
function isInScope(relPath, scopeDef) {
  const fileName = relPath.slice(relPath.lastIndexOf('/') + 1);
  const inc = (scopeDef && scopeDef.include) || [];
  if (inc.length > 0 && !matchesAnyPattern(relPath, fileName, inc)) return false;  // ① 화이트리스트 우선
  const exc = (scopeDef && scopeDef.exclude) || [];
  if (exc.length > 0 && matchesAnyPattern(relPath, fileName, exc)) return false;   // ② 그 다음 블랙리스트
  return true;
}

// root 매칭 판정 — resolveScopeIn과 isFilteredOutOfScope가 공유한다.
// 기존 resolveScope:561 로직을 그대로 보존한다.
function rootMatches(relPath, scope) {
  const root = normalizeRootNoSlash(scope && scope.root);
  if (root === '') return { matched: true, len: 0 };
  if (relPath === root || relPath.startsWith(root + '/')) return { matched: true, len: root.length };
  return { matched: false, len: -1 };
}

/**
 * root에는 속하지만 스코프 필터에서 탈락했는지 판정한다 (080 §3.2.2 (C-bis)).
 * 필터 판정 자체는 isInScope에만 위임하고 root 매칭은 resolveScopeIn과 동일한 rootMatches를
 * 공유한다 — 중복 판정 로직을 만들지 않는다 ([MUST] PRINCIPLES.md §2).
 *
 * 발동 조건: ① 레지스트리가 비어 있지 않고 ② root 매칭 스코프가 1개 이상 있으며
 *            ③ 그 전부가 isInScope 실패. root 밖 파일·스코프 미설정 프로젝트는 false를 돌려
 *            기존 동작(모드 직결)을 그대로 유지한다 (H-13, TS-037).
 *
 * @param {string} relPath  프로젝트 루트 기준 POSIX 경로
 * @param {Record<string, {root: string, include?: string[], exclude?: string[]}>} scopes
 * @returns {boolean}
 */
function isFilteredOutOfScope(relPath, scopes) {
  let rootHit = false;
  for (const scope of Object.values(scopes || {})) {
    if (!rootMatches(relPath, scope).matched) continue;
    rootHit = true;
    if (isInScope(relPath, scope)) return false;
  }
  return rootHit;
}

/**
 * 정규화된 스코프 레지스트리에서 relPath의 소속 스코프를 판정한다 (080 §3.2.2 (D)).
 * ① root 매칭 → ② isInScope 탈락 제외 → ③ 최장 root 승리 →
 * ④ 동률 + include 매칭 1개는 그 스코프 승리 → ⑤ 2개 이상은 scope_ambiguous → ⑥ 그 외 이름 사전순.
 * @param {string} relPath
 * @param {Record<string, {root: string, include?: string[], exclude?: string[]}>} scopes
 * @returns {{name: string, scope: object} | null}
 * @throws {CodeMapFatalError} 'scope_ambiguous'
 */
function resolveScopeIn(relPath, scopes) {
  const candidates = [];
  for (const [name, scope] of Object.entries(scopes || {})) {
    const rm = rootMatches(relPath, scope);              // ①
    if (!rm.matched) continue;
    if (!isInScope(relPath, scope)) continue;            // ②
    candidates.push({ name, scope, len: rm.len });
  }
  if (candidates.length === 0) return null;

  let maxLen = -1;                                        // ③
  for (const c of candidates) { if (c.len > maxLen) maxLen = c.len; }
  const tied = candidates.filter(c => c.len === maxLen);
  if (tied.length === 1) return { name: tied[0].name, scope: tied[0].scope };

  // 후보는 이미 ②를 통과했으므로 "include가 비어 있지 않다 = include가 매칭됐다"이다.
  const byInclude = tied.filter(c => ((c.scope && c.scope.include) || []).length > 0);
  if (byInclude.length === 1) return { name: byInclude[0].name, scope: byInclude[0].scope };  // ④
  if (byInclude.length > 1) {                                                                 // ⑤
    const names = byInclude.map(c => c.name).sort();
    throw new CodeMapFatalError('scope_ambiguous',
      relPath + '가 동률 root 스코프 ' + names.join(', ') + '의 include에 동시 매칭됩니다 — ' +
      '한쪽 include를 좁혀 소속을 1개로 확정하세요');
  }
  const sorted = tied.slice().sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));  // ⑥
  return { name: sorted[0].name, scope: sorted[0].scope };
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

/**
 * 열거 대상 경로와 그 경로에 적용할 스코프 필터를 함께 돌려준다 (080 §3.2.2 (C) ①).
 * `targetPath`(명시 경로 조회)는 사용자 의도가 필터보다 우선하므로 `scopeDef: null`로 면제한다
 * — 필터를 걸면 include 밖 파일이 "결과 없음 = @header 누락"으로 오판정된다 (TS-019, D-4).
 * @returns {Array<{abs: string, scopeDef: object|null}>}
 */
function getSearchPaths(projectRoot, config, opts) {
  if (opts.scope) {
    const sp = config.scopes[opts.scope];
    if (!sp) {
      const avail = Object.keys(config.scopes).join(', ') || '(none)';
      process.stderr.write(`Error: Unknown scope "${opts.scope}". Available: ${avail}\n`);
      process.exit(1);
    }
    return [{ abs: path.resolve(projectRoot, sp.root), scopeDef: sp }];
  }
  if (opts.targetPath) {
    return [{ abs: path.resolve(projectRoot, opts.targetPath), scopeDef: null }];
  }
  const scopes = Object.values(config.scopes);
  return scopes.length > 0
    ? scopes.map(s => ({ abs: path.resolve(projectRoot, s.root), scopeDef: s }))
    : [{ abs: projectRoot, scopeDef: null }];
}

function discoverFiles(projectRoot, config, opts) {
  const searchPaths = getSearchPaths(projectRoot, config, opts);
  const all = [];
  for (const sp of searchPaths) {
    const found = (fs.existsSync(sp.abs) && fs.statSync(sp.abs).isFile())
      ? [sp.abs]
      : walkDir(sp.abs, config);
    if (sp.scopeDef === null) { all.push(...found); continue; }
    for (const f of found) {
      // 스코프 필터 — 판정은 isInScope 1곳에만 있다 (080 §3.2.2 (B))
      if (isInScope(toPosixRel(projectRoot, f), sp.scopeDef)) all.push(f);
    }
  }

  // Apply exclude patterns (config + CLI merged)
  const patterns = mergeExcludePatterns(config, opts);
  if (patterns.length === 0) return all.sort();

  return all.filter(f => {
    const rel = path.relative(projectRoot, f);
    return !matchesAnyPattern(rel, path.basename(f), patterns);
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
  // detail은 선택 — 지정하면 main()이 errorExit payload에 그대로 실어 사람·기계 양쪽에 전달한다.
  constructor(code, detail) { super(code); this.code = code; this.detail = detail; }
}

// 사람이 읽는 실패 렌더 — brain_tool.py:790-792가 실패 detail로 **stderr만** 전달하므로
// stdout JSON과 별개로 반드시 stderr에도 사유·해결·근거를 내보낸다 (080 §3.1.2 (F), H-1).
function renderHumanError(payload) {
  const lines = [`code-scan: ${payload.error}${payload.detail ? ` — ${payload.detail}` : ''}`];
  if (payload.migration) lines.push(`  마이그레이션: ${payload.migration}`);
  if (payload.fix) lines.push(`  해결: ${payload.fix}`);
  if (payload.doc) lines.push(`  근거: ${payload.doc}`);
  return lines.join('\n');
}

function errorExit(code, extra) {
  const payload = Object.assign({ ok: false, error: code }, extra || {});
  console.log(JSON.stringify(payload));                    // 기계 소비자 (기존 codeMapErrorExit 계약 보존)
  process.stderr.write(renderHumanError(payload) + '\n');  // 사람 + brain-tool detail 전달 경로
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
  // 스코프 스키마 검증 + 내부 정규화 — root 필수(기존) · include/exclude는 존재하면 string[]
  // (080 §3.2.2 (E), TS-075). 이후 모든 소비자는 정규화된 형태만 본다.
  const normalizedScopes = {};
  for (const [name, scope] of Object.entries(index.scopes)) {
    const n = normalizeIndexScope(scope);
    if (!n.ok) return { present: true, error: 'invalid_index', index, manifests: new Map() };
    normalizedScopes[name] = n.scope;
  }
  index.scopes = normalizedScopes;
  return { present: true, index, manifests: new Map() };
}

// 확정된 모드(resolveHeaderSource의 1회 판정 결과)를 ctx에 실어 전 소비자에게 전달한다.
function buildCtx(projectRoot, config, headerSource) {
  const codeMap = loadCodeMap(projectRoot);
  if (codeMap.error) throw new CodeMapFatalError(codeMap.error);
  return { projectRoot, config, codeMap, headerSource };
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

// 공개 인터페이스(module.exports)이므로 시그니처를 유지하고 판정은 resolveScopeIn에 위임한다
// (080 §3.2.2 (D), H-4 회귀 방어).
function resolveScope(relPath, index) {
  return resolveScopeIn(relPath, (index && index.scopes) || {});
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

// ── Mode-direct resolver (G) — single read-path entry point ─────────────
//
// 모드가 소스를 고르므로 두 소스가 경합하지 않는다 — "인라인 단독 승리"라는 병합 규칙은 소멸했다
// (080 §3.3.2 (A) 상속 단수 재정의):
//   inline   → tier① 인라인 **단독** (_source 키 없음 — 조회 8커맨드 골든 보존 지점)
//   manifest → tier② files → ③ package → ④ layerRules → ⑤ domains **4단**, 인라인은 읽지 않는다

function resolveHeader(filePath, ctx) {
  const mode = ctx.headerSource;   // 확정값 읽기 전용 — 여기서 재판정하지 않는다 (080 §3.1.2 (D))

  // inline 모드: extractHeader와 완전히 동일한 값을 그대로 반환한다 — 제약② 하위호환 보증 지점.
  if (mode === 'inline') return extractHeader(filePath);

  // manifest 모드 + index.json 부재: 조회 결과가 전량 공백이 된다. 차단 조건을 늘리지 않고
  // (D-5 범위 밖) 사유만 stderr 1줄로 노출하는 fail-soft를 택한다 (080 §3.3.2 (A), H-12).
  if (!ctx.codeMap.present) {
    noticeOnce('manifest_index_missing',
      'manifest 모드이지만 .opal/code-map/index.json이 없습니다 — 조회 결과가 비어 있습니다 (비차단)');
    return null;
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

// ── Target — 필터 1단 + 모드 직결 2단 = 3값 도메인 (080 §3.3.2 (B)) ──────
//
// write_to 3값(inline|manifest|none) × reason 3값(header_source_inline|header_source_manifest|
// out_of_scope)이며 실제 조합은 3쌍으로 닫힌다. 파일 존재 여부·인라인 보유 여부·스코프 속성은
// **판정 근거가 아니다** — 077의 4단 판정(inline_exists/new_file/legacy_no_header + 스코프 예외)은
// 전부 소멸했다. 두 축은 서로 다르다: ①은 "쓸 자리가 있는가", ②③은 "어느 소스에 쓰는가"다.

function decideTarget(fileRel, ctx) {
  const relPath = (fileRel || '').split(path.sep).join('/');

  // ① 스코프 필터 탈락 — 모드 판정보다 **먼저** 평가된다. 관리 대상이 아닌 파일에는 기록 위치
  //    자체가 존재하지 않으므로 write_to는 'none'이고 scope/manifest/key를 싣지 않는다.
  //    오류가 아니라 정상 판정이므로 exit 0이다 (080 §3.2.2 (C-bis), TS-035).
  //    레지스트리는 그 프로젝트에서 실제로 파일 집합을 지배하는 쪽을 따른다.
  const filterScopes = ctx.codeMap.present ? ctx.codeMap.index.scopes : ctx.config.scopes;
  if (isFilteredOutOfScope(relPath, filterScopes)) {
    return { write_to: 'none', reason: 'out_of_scope' };
  }

  // ② 전역 모드가 inline — 매니페스트를 읽지도 쓰지도 않으므로 기록 위치 부가 필드도 싣지 않는다.
  const mode = ctx.headerSource;   // 확정값 읽기 전용 (080 §3.1.2 (D))
  if (mode === 'inline') return { write_to: 'inline', reason: 'header_source_inline' };

  // ③ 전역 모드가 manifest — 스코프 판정은 기록 위치(미러 경로) 산출에만 쓰인다.
  const out = { write_to: 'manifest', reason: 'header_source_manifest' };
  const scoped = ctx.codeMap.present ? resolveScope(relPath, ctx.codeMap.index) : null;
  if (scoped) {
    const mp = mirrorPathForDir(posixDirname(relPath), scoped.name, scoped.scope);
    if (!mp.skipped) {
      out.scope = scoped.name;
      out.manifest = `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`;
      out.key = path.basename(relPath);
    }
  }
  return out;
}

// ═══════════════════════════════════════════
// Scanning & Filtering
// ═══════════════════════════════════════════

function scanAll(projectRoot, config, opts, mode) {
  const files = discoverFiles(projectRoot, config, opts);
  const ctx = buildCtx(projectRoot, config, mode);
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

function scanHeaders(projectRoot, config, opts, mode) {
  const { withHeader } = scanAll(projectRoot, config, opts, mode);
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

function cmdScan(projectRoot, config, opts, mode) {
  output(scanHeaders(projectRoot, config, opts, mode), opts);
}

function cmdDomain(projectRoot, config, opts, mode) {
  if (opts.commandArg) {
    opts.domain = opts.commandArg;
    return output(scanHeaders(projectRoot, config, opts, mode), opts);
  }
  // List all domains grouped
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null }, mode);
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

function cmdLayer(projectRoot, config, opts, mode) {
  if (opts.commandArg) {
    opts.layer = opts.commandArg;
    return output(scanHeaders(projectRoot, config, opts, mode), opts);
  }
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null }, mode);
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

function cmdSearch(projectRoot, config, opts, mode) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan search <pattern>'); process.exit(1); }

  let regex;
  try { regex = new RegExp(keyword, 'i'); }
  catch (err) {
    console.error(`Invalid regex: ${keyword} — ${err.message}`);
    process.exit(1);
  }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null }, mode);
  const matches = all.filter(r => regex.test(JSON.stringify(r.header)));

  // Re-apply filters
  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}

function cmdExports(projectRoot, config, opts, mode) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan exports <pattern>'); process.exit(1); }

  let regex;
  try { regex = new RegExp(keyword, 'i'); }
  catch (err) {
    console.error(`Invalid regex: ${keyword} — ${err.message}`);
    process.exit(1);
  }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null }, mode);
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

function cmdSummary(projectRoot, config, opts, mode) {
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null }, mode);
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

function cmdDepends(projectRoot, config, opts, mode) {
  const target = opts.commandArg;
  if (!target) { console.error('Usage: code-scan depends <module>'); process.exit(1); }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null }, mode);

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

function cmdMissing(projectRoot, config, opts, mode) {
  const { noHeader } = scanAll(projectRoot, config, opts, mode);
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
  // config.scopes 파생 경로 — 값은 loadConfig가 이미 정규화한 {root, include, exclude}다.
  // 사람이 code-scan.json에 **명시한** include/exclude는 그대로 승계한다(추론이 아니라 보존).
  if (config.scopes && Object.keys(config.scopes).length > 0) {
    for (const [name, normalized] of Object.entries(config.scopes)) {
      const r = normalized.root;
      scopes[name] = {
        root: r.endsWith('/') ? r : r + '/',
        anchors: [], stripPrefix: [],
        include: (normalized.include || []).slice(),
        exclude: (normalized.exclude || []).slice(),
      };
    }
    return scopes;
  }
  // 디렉토리 스캔 파생 경로 — [MUST] TASK.md §개선 A 보강 ⑤: discover는 include를 **추론하지 않는다**.
  // 어느 파일이 우리 것인지는 도메인 지식이며, 도구 추측은 오탐을 자산에 고정시킨다.
  let entries;
  try { entries = fs.readdirSync(projectRoot, { withFileTypes: true }); } catch { entries = []; }
  for (const e of entries) {
    if (!e.isDirectory() || e.name.startsWith('.')) continue;
    if ((config.exclude || []).includes(e.name)) continue;
    scopes[e.name] = { root: e.name + '/', anchors: [], stripPrefix: [], include: [], exclude: [] };
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

function cmdDiscover(projectRoot, config, opts, mode) {
  buildCtx(projectRoot, config, mode); // surfaces schema errors on an existing (invalid) index

  const outPath = opts.discoverOut ? path.resolve(projectRoot, opts.discoverOut) : path.join(projectRoot, CODE_MAP_DIR, 'index.json');
  const dryRun = !!opts.dryRun;

  if (!dryRun && fs.existsSync(outPath)) {
    return errorExit('index_exists');
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
    note: 'OWNER REVIEW REQUIRED — headerSource/anchors/stripPrefix/include 확인 후 status를 reviewed로 변경',
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

// scopeDef: 이 스코프의 정규화된 정의 — 열거에 스코프 필터를 적용한다 (080 §3.2.2 (C) ②).
function collectDirsWithCodeFiles(scopeRootAbs, projectRoot, config, index, scopeDef) {
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
        if (matchesAnyPattern(rel, e.name, excludePatterns)) continue;
        if (!isInScope(rel, scopeDef)) continue;
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

function cmdScaffold(projectRoot, config, opts, mode) {
  const ctx = buildCtx(projectRoot, config, mode);

  // inline 모드 no-op — 매니페스트를 만들 이유 자체가 없다. index 부재 검사보다 **먼저** 이탈해야
  // "인덱스가 없다"는 이유로 차단되지 않는다 (080 §3.3.2 (C), TS-023). 설정대로 동작한 것이므로
  // 실패가 아니라 exit 0이며, 사유는 기존 skipped 배열에 실어 보낸다(신규 필드 없음).
  if (ctx.headerSource === 'inline') {
    const noop = {
      ok: true, created: 0, updated: 0, unchanged: 0, added: [], pruned: [], stale: [],
      skipped: [{
        reason: 'header_source_inline',
        detail: '전역 헤더 소스가 inline이므로 매니페스트를 생성하지 않습니다',
      }],
    };
    if (opts.output === 'json') console.log(JSON.stringify(noop));
    else console.log('scaffold: skipped — 전역 헤더 소스가 inline이므로 매니페스트를 생성하지 않습니다');
    return;
  }

  if (!ctx.codeMap.present) return errorExit('index_missing');

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
    const dirsWithFiles = collectDirsWithCodeFiles(scopeRootAbs, projectRoot, config, index, scope);
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
    return errorExit('mirror_collision', { collisions });
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

function cmdTarget(projectRoot, config, opts, mode) {
  const rel = opts.commandArg;
  if (!rel) { console.error('Usage: code-scan target <file>'); process.exit(1); }
  const ctx = buildCtx(projectRoot, config, mode);
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
// scopeDef: 이 매니페스트가 속한 스코프의 정규화된 정의 — scaffold 열거와 동일한 스코프 필터를
// 구조 패스에도 적용한다 (080 §3.2.2 (C) ③). 없으면 필터 없음과 동일하다.
function listCodeFilesInDir(dirAbs, dirRel, config, excludeDirs, excludePatterns, scopeDef) {
  if (hasExcludedSegment(dirRel || '', excludeDirs)) return [];
  let entries;
  try { entries = fs.readdirSync(dirAbs, { withFileTypes: true }); } catch { return []; }
  const out = [];
  for (const e of entries) {
    if (e.isFile() && config.extensions.includes(path.extname(e.name))) {
      const rel = dirRel ? `${dirRel}/${e.name}` : e.name;
      if (matchesAnyPattern(rel, e.name, excludePatterns)) continue;
      if (!isInScope(rel, scopeDef)) continue;
      out.push(e.name);
    }
  }
  return out;
}

function cmdValidate(projectRoot, config, opts, mode) {
  const ctx = buildCtx(projectRoot, config, mode);
  // 이 실행이 어느 소스를 유일한 진실로 보는가 — 커버리지 분자·uncovered 분류·draft·구조 패스가
  // 전부 이 1값에서 갈린다 (080 §3.3.2 (D)). 합산 커버리지는 폐기됐다.
  const isInlineMode = ctx.headerSource === 'inline';

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
      // 전체 스캔(walkDir/matchesAnyPattern)과 동일한 제외 규칙 — exclude 디렉토리 세그먼트 우선,
      // 그 다음 excludePatterns(와일드카드). 둘 중 하나라도 매치되면 판정에서 제외한다.
      if (hasExcludedSegment(rel, excludeDirs)) { skipped.push({ file: rel, reason: 'excluded_dir' }); continue; }
      if (matchesAnyPattern(rel, path.basename(abs), excludePatterns)) { skipped.push({ file: rel, reason: 'excluded_pattern' }); continue; }
      // 스코프 root에는 속하지만 include/exclude 필터에 탈락한 파일 — 관리 대상이 아니므로
      // 커버리지 분모에서 빼고 사유를 남긴다 (080 §3.2.2 (C) ④, TS-012 ④).
      if (isFilteredOutOfScope(rel, config.scopes)) { skipped.push({ file: rel, reason: 'out_of_scope' }); continue; }
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

    // 커버 판정은 **해당 모드의 소스만** 본다 — 반대 소스는 계상하지 않는다 (080 §3.3.2 (D)).
    const covered = isInlineMode ? inlineHeader !== null : fe !== null;
    if (!covered) {
      // inline 모드에는 "관리 매니페스트" 개념이 없으므로 항상 git 2분류다.
      // manifest 모드에서 매니페스트가 이 디렉토리를 관리 중(scaffold됨)인데 files{}에 키가 없는
      // 경우는 구조적 결손 — git 상태와 무관하게 'no_entry'(항상 차단, 기존 동작 불변).
      // 그 외(관리 매니페스트 자체가 없음)는 git 기준 2분류.
      const managedByManifest = !isInlineMode && !!(mctx && mctx.manifest);
      const sub = managedByManifest ? 'no_entry' : classifyUncovered(projectRoot, relPath);
      violations.push({ code: 'uncovered', sub, file: relPath, detail: '' });
      continue;
    }
    if (isInlineMode) inlineCount++; else manifestCount++;

    const resolved = resolveHeader(fileAbs, ctx);
    const required = ['module', 'layer', 'domain', 'description', 'exports'];
    const missingFields = required.filter(f => !resolved || resolved[f] === undefined);
    if (missingFields.length > 0) {
      violations.push({ code: 'uncovered', sub: 'incomplete', file: relPath, detail: missingFields.join(',') });
    }

    if (inlineHeader !== null && fe !== null && hasSubstantiveContent(fe)) {
      violations.push({ code: 'conflict', sub: 'inline_shadowed', file: relPath, manifest: mctx.manifestRel, key: basename, detail: '' });
    }

    // draft는 매니페스트 전용 개념이므로 inline 모드에서는 적용하지 않는다 (080 §3.3.2 (D)).
    if (!isInlineMode && inlineHeader === null && fe !== null) {
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
  //
  // orphan·worker_scope_violation은 전부 **매니페스트 무결성** 위반이다. inline 모드는 매니페스트를
  // 만들지도 읽지도 않으므로 검사 대상 자체가 없다 — 패스를 통째로 스킵한다 (080 §3.3.2 (D)).
  // 조용히 스킵하지는 않는다: 설정과 자산이 어긋나 있다는 사실만 stderr 1줄로 노출한다.
  if (isInlineMode && ctx.codeMap.present) {
    noticeOnce('inline_mode_structural_skip',
      'inline 모드이므로 매니페스트 구조 검사를 건너뜁니다 — .opal/code-map/ 자산이 존재하지만 이 실행에서는 사용되지 않습니다');
  }
  if (!isInlineMode && ctx.codeMap.present) {
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
        // 세그먼트 + excludePatterns + 스코프 필터)를 적용해 정당히 제외된 파일이
        // files_key_removed로 오탐되지 않도록 한다(077 결함 D · 080 §3.2.2 (C) ③, TS-014/TS-015).
        const structExcludeDirs = [...(config.exclude || []), ...((index && index.exclude) || [])];
        const structExcludePatterns = mergeExcludePatterns(config, opts);
        const diskBasenames = dirExists
          ? listCodeFilesInDir(dirAbs, manifest.dir || '', config, structExcludeDirs, structExcludePatterns, scopeObj)
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
  // 소비자가 "어느 소스 기준의 커버리지인가"를 추측하지 않아도 되게 만드는 필드 (080 §3.3.2 (D)).
  // 키 이름은 문자열로만 다룬다 — 모드 판정 지점 봉인 화이트리스트(TS-070) 밖이기 때문이다.
  result['headerSource'] = ctx.headerSource;

  if (opts.output === 'json') console.log(JSON.stringify(result));
  else console.log(`validate: ${ok ? 'OK' : blockingViolations.length + ' violation(s)'} — coverage ${percent}% (${covered}/${totalCount})`);

  process.exit(ok ? 0 : 2);
}

// ── feature (F-008) ──────────────────────────────────────────────────────

function cmdFeature(projectRoot, config, opts, mode) {
  const id = opts.commandArg;
  if (!id) { console.error('Usage: code-scan feature <id>'); process.exit(1); }

  const configuredScopes = Object.keys(config.scopes || {});
  const scopeNames = opts.scope ? [opts.scope] : (configuredScopes.length > 0 ? configuredScopes : [null]);

  const result = {};
  for (const scopeName of scopeNames) {
    const scopeOpts = Object.assign({}, opts, { scope: scopeName, domain: null, layer: null });
    const all = scanHeaders(projectRoot, config, scopeOpts, mode);
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

  // ── 전 명령 차단 게이트 (080 D-5) ─────────────────────────────────────
  // help/version은 커맨드가 아니라 메타 출력이므로 위에서 이미 반환되었다.
  const hs = resolveHeaderSource(config, opts);
  if (!hs.ok) {
    const extra = { detail: hs.detail, where: hs.where, fix: hs.fix, doc: HEADER_SOURCE_DOC };
    if (hs.migration) extra.migration = hs.migration;
    return errorExit(hs.error, extra);
  }
  const mode = hs.value;   // 이 실행의 모드 — 이후 변하지 않는다 (ctx로 전파)
  // ──────────────────────────────────────────────────────────────────────

  // ── scopes 스키마 게이트 (080 §3.2.2 (E), TS-075) ─────────────────────
  // loadConfig는 종료하지 않으므로(hook fail-safe) 여기서 exit 1로 표면화한다.
  if (config.configError === 'config_scope_invalid') {
    return errorExit('code_scan_config_invalid', {
      detail: config.configErrorDetail,
      where: 'config',
      fix: '.opal/code-scan.json의 scopes 항목은 문자열 또는 {path, include, exclude} 형식이어야 합니다 ' +
           '(include/exclude는 문자열 배열)',
    });
  }

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
    fn(projectRoot, config, opts, mode);
  } catch (err) {
    if (err instanceof CodeMapFatalError) { errorExit(err.code, err.detail ? { detail: err.detail } : null); return; }
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
// v1.4.0 — 2026-08-02 — 전역 단일 headerSource 2택(inline|manifest) 확정값이 조회·작성·검증 전 경로를
//                       직접 지배하도록 전환. resolveHeaderSource 1곳이 CLI > 전역 2층으로 실행당 1회
//                       판정하고 미설정·무효값은 전 명령 차단(exit 1). resolveHeader는 2택 직결로
//                       재작성되어 병합 규칙이 소멸했고(manifest 모드 index.json 부재는 stderr 1줄
//                       비차단), decideTarget은 4단 판정을 걷어내고 필터 1단 + 모드 직결 2단의
//                       3값 도메인(write_to inline|manifest|none × reason header_source_inline|
//                       header_source_manifest|out_of_scope)으로 닫혔다. scaffold는 inline 모드에서
//                       no-op + skipped 사유 보고(exit 0), validate는 모드별 단일 소스 커버리지
//                       (합산 폐기)·uncovered 분류·draft·구조 패스를 분기하고 결과에 헤더 소스를
//                       실어 보낸다. 스코프 단위 모드 선언 키와 폐기된 쓰기금지 플래그는 무시 +
//                       실행당 1회 안내이며, 스코프 include/exclude 파일 집합 필터가 열거·scaffold·
//                       validate 구조 패스·--changed·target 5지점에 배선됐다. 차단 정책
//                       (uncovered:pre_existing만 비차단, 그 외 exit 2)은 불변 (080)
