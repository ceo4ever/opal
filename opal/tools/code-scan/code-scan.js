#!/usr/bin/env node
/**
 * @header {
 *   "module": "code-scan",
 *   "layer": "util",
 *   "domain": "code-scan",
 *   "description": "OPAL @header 메타블록 스캐너 CLI — 코드 파일의 인라인/code-map @header를 파싱해 도메인·레이어·의존관계를 조회하고, discover/scaffold/target/validate/feature 5서브명령으로 code-map 헤더 작성층(외부 매니페스트 기반 상속·워커 권한 경계 집행·uncovered 2분류)을 관리한다. headerSource는 inline|manifest 2택 전역 단일 키이며, resolveHeaderSource가 CLI --header-source > 전역 config 2층으로 실행당 1회 판정해 미설정·무효값이면 전 명령을 차단한다. 확정된 모드는 조회·작성·검증 전 경로를 직접 지배한다 — resolveHeader는 inline이면 인라인 단독, manifest면 files>package>layerRules>domains 4단만 보고(index.json 부재는 stderr 1줄 비차단), decideTarget은 파일 상태를 보지 않고 모드에서 write_to/reason을 직결하며, scaffold는 inline에서 매니페스트를 만들지 않고 skipped 사유만 보고하고, validate는 모드별 단일 소스 커버리지(합산 폐기)와 구조 패스 분기를 적용해 결과에 모드를 실어 보낸다. 두 스코프 레지스트리(code-scan.json의 path 축약·객체형 / code-map index.json의 root)는 normalizeConfigScope·normalizeIndexScope가 {root, include, exclude} 단일 내부 형태로 정규화하고, 파일 집합 필터 판정은 isInScope 1곳에, 소속 스코프 판정은 resolveScopeIn(최장 root > include 매칭 > 사전순, 동률 include 경합은 scope_ambiguous) 1곳에 봉인한다. 그 필터는 열거(discoverFiles)·scaffold 열거(collectDirsWithCodeFiles)·validate 구조 패스(listCodeFilesInDir)·validate --changed·target(decideTarget) 5지점에 배선되며, target은 isFilteredOutOfScope를 경유해 필터 탈락 파일에 {write_to:'none', reason:'out_of_scope'}를 exit 0으로 돌려준다. scan <file> 명시 경로만 필터 면제다. 베이스 매니페스트는 예약 폴더 _shards/ 아래에 의미 단위 샤드로 분산될 수 있다 — 베이스가 shards 배열로 라벨을 선언하면 resolveShards 1곳이 조회·기록 위치·구조 검증 경로 전체의 샤드 해석(로딩·byKey 합집합·중복 판정)을 봉인하고, 미선언 자산에서는 null을 돌려 오늘과 동일하게 동작한다(하위호환). 분할 판정은 shardPolicy 2축(바이트 초과 AND 엔트리 수 이상)이며 resolveShardPolicy 1곳이 프로젝트 code-scan.json > 전역 setting.json > 코드 상수(10240/40) 3단을 셀 단위로 병합해 실행당 1회 확정한다 — 전면 비차단이고 초과 열거에 권고 조각 수·다음 명령을 실어 보낸다. split 서브명령이 분할을 제안(--plan: 5단 사다리 S1~S5 + 표준단어사전 대조, 무쓰기)하고 집행(--groups: 사전 불변식 → tmp 전량 작성 → rename 커밋 → 사후 재검증, 엔트리 유실 0건)하며, init 서브명령은 headerSource 미설정 순환을 끊는 비대화형 설정 초안 창구다",
 *   "exports": ["mirrorPathForDir", "decideTarget", "loadCodeMap", "loadConfig", "findProjectRoot", "resolveScope", "matchLayerRule", "matchDomain", "resolveHeader", "extractHeader"],
 *   "note": "code-scan.js 자신은 프로젝트 .opal/code-map/index.json 부재로 인라인 전용 모드로 스캔됨 (태스크 077). 모드 판정 지점은 resolveHeaderSource 1곳으로 봉인되며, 허용 3구간(resolveHeaderSource/loadConfig/parseArgs) 밖에서는 확정값을 ctx.headerSource 읽기·buildCtx 파라미터 전달 형태로만 다룬다 — 중간 전달 변수명은 mode다 (태스크 080 TS-070). 스코프 단위 모드 선언 키는 존재하지 않는다 — 두 레지스트리 모두 해당 키를 무시하고 deprecationOnce로 키별 실행당 1회만 stderr 안내한다 (태스크 080 F-002). index.json에서 폐기된 스코프 단위 쓰기금지 플래그도 같은 방식으로 무시 + 안내되며 다른 모드로 흡수하지 않는다 — 기록 소스는 오직 전역 headerSource가 결정하므로 스코프 단위 예외 판정 분기는 존재하지 않는다 (태스크 080 F-004). 두 소스는 모드에 의해 상호 배타이므로 '인라인 단독 승리' 같은 병합 규칙이 존재하지 않으며, decideTarget의 reason 도메인은 header_source_inline / header_source_manifest / out_of_scope 3값으로 닫힌다 — 파일 존재 여부·인라인 보유 여부는 판정에 관여하지 않는다 (태스크 080 F-003). 매니페스트 샤딩(태스크 082): 샤드 로딩·byKey 구성·중복 판정은 resolveShards 밖에 복제하지 않는다. CODE_MAP_VERSION은 1로 고정 유지되며(샤드 미선언 매니페스트 포맷 불변, 상향 시 기존 전 자산이 unsupported_version으로 차단됨), 샤드 라벨은 kebab 정규식으로 집행되어 경로 이탈을 차단한다(shard_declaration_invalid). 예약 폴더명과 겹치는 소스 디렉토리는 scaffold가 reserved_name_collision으로 거부한다. 크기 상한 초과는 validate/scaffold 모두 전면 비차단(열거·경고 1단)이다. 샤드 정책 확장(태스크 083): 정책 판정은 resolveShardPolicy 밖에 복제하지 않으며 DEFAULT_SHARD_POLICY·loadGlobalSetting도 그 함수 본문 밖에서 참조하지 않는다. 구 위치 index.json manifestMaxBytes는 폐기되어 값을 읽지 않고 deprecationOnce 안내만 한다(자동 변환 없음). 표준단어사전은 옵셔널이며 부재·파싱 실패·매칭 0건 3분기가 전부 비차단이다 — 부재는 침묵, 파손은 noticeOnce 1줄이고, loadWordDictionary 호출은 split --plan 경로 1곳뿐이라 조회 8커맨드의 출력 바이트가 흔들리지 않는다. split은 자산을 쓰는 유일한 명령이므로 실패 지점별로 쓰기 상태가 다른 에러 코드 7종(split_usage_invalid/split_inline_mode/split_target_invalid/split_groups_invalid/split_write_failed/split_rollback/split_verify_failed)을 갖고, 사후 재검증은 resolveShards를 비운 캐시로 다시 호출해 해석 로직을 복제하지 않는다. 의미 경계(그룹 라벨·파일 배분) 확정은 사람/워커의 몫이며 도구는 미분류를 임의 배분하거나 '기타' 그룹을 만들지 않는다"
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
const os = require('os');
const { spawnSync } = require('child_process');

// ═══════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════

const VERSION = '1.6.0';
const HEADER_READ_BYTES = 8192;

const DEFAULT_CONFIG = {
  scopes: {},
  extensions: ['.py', '.js', '.ts', '.vue', '.jsx', '.tsx', '.svelte', '.kt', '.kts', '.java', '.swift'],
  exclude: ['node_modules', '__pycache__', '.git', 'dist', 'build', '.venv', 'env', '.next', '.nuxt', '.output'],
  excludePatterns: [],
  headerSource: null,
  shardPolicy: {}
};

// headerSource 값 도메인 — 2택. 구형 값은 남기지 않는다 (080 D-3).
const HEADER_SOURCE_VALUES = ['inline', 'manifest'];
const HEADER_SOURCE_DOC = '~/.opal/references/header-standard.md §7';
// 제거된 구형 값. 마이그레이션 안내를 위해 **이 1개소에서만** 식별한다 (080 D-3 / TS-066).
const HEADER_SOURCE_LEGACY = 'auto';

// 복구 경로 안내 (083 F-012 (I)) — 차단 동작은 불변이고 문구만 보강한다.
// 도구는 명령 문자열을 제시할 뿐 자동 복구·자동 재실행을 하지 않는다.
const INIT_CREATE_FIX = ' 또는 code-scan init --header-source <inline|manifest> --write 로 설정 파일을 생성하세요';
const INIT_RECOVERY_FIX = ' 설정을 새로 만들려면: code-scan init --header-source <inline|manifest> --write --force';

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

// ── shard constants (082) ────────────────────────────────────────────────
const SHARDS_DIR = '_shards';                              // 예약 폴더명 (확정 방향 #2)
const SHARD_LABEL_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;       // 사람이 읽는 kebab 라벨 (확정 방향 #8)

// ── shard policy constants (083) ─────────────────────────────────────────
// [MUST] 이 상수는 resolveShardPolicy 본문 밖에서 참조하지 않는다 — 정책 판정 1곳 봉인(제약 ③).
const DEFAULT_SHARD_POLICY = Object.freeze({ maxBytes: 10240, minFiles: 40, dictPath: null });
// 키별 타입 — 값 타입이 섞이므로(정수 2 + 경로 1) 키 배열이 아니라 스키마 표로 둔다
const SHARD_POLICY_SCHEMA = Object.freeze({
  maxBytes: 'positiveInt',      // 바이트 상한
  minFiles: 'positiveInt',      // 엔트리 수 하한
  dictPath: 'nonEmptyString',   // 표준단어사전 명시 경로 (선택, 탐색 3단의 1순위)
});
const SHARD_POLICY_KEYS = Object.keys(SHARD_POLICY_SCHEMA);   // 알 수 없는 키는 무시
const SHARD_TARGET_RATIO = 0.75;                      // 조각 목표 = 상한 × 비율 (확정 방향 #9)
const OPAL_HOME_ENV = 'OPAL_HOME';                    // 홈 경로 주입 창구 (U-7)

// ── 용어사전 상수 (083 F-011) ─────────────────────────────────────────────
const DICT_FILENAME = '표준단어사전.md';
// [주의] op-data-dictionary/SKILL.md가 자기모순이다(H-19):
//   :21  → default `200.설계/210.사전/`
//   :72·:172 → `{설계}/사전/` (= `200.설계/사전/`)
// 어느 쪽이든 발견되도록 **두 후보를 순서대로** 본다. 새 규칙을 만드는 것이 아니라
// 문서가 말하는 두 경로를 모두 존중하는 것이다.
const DICT_DEFAULT_RELS = Object.freeze([
  `200.설계/사전/${DICT_FILENAME}`,
  `200.설계/210.사전/${DICT_FILENAME}`,
]);
const DICT_MAX_BYTES = 2 * 1024 * 1024;               // 거대 파일로 도구가 멈추지 않게 하는 상한 (H-17)

// ── 분할 제안 사다리 (083 F-004, U-2 (3)) — 내장 고정. 설정 노출은 후속 이관 ──
const SHARD_PLAN_LADDER = Object.freeze([
  Object.freeze({ id: 'S1', signal: 'first-token', dict: true,  accept: 2 }),
  Object.freeze({ id: 'S2', signal: 'first-two',   dict: true,  accept: 2 }),
  Object.freeze({ id: 'S3', signal: 'any-token',   dict: true,  accept: 2 }),
  Object.freeze({ id: 'S4', signal: 'last-token',  dict: false, accept: 3 }),
  Object.freeze({ id: 'S5', signal: 'depends',     dict: false, accept: 3 }),
]);
const SHARD_PLAN_STAGE_IDS = SHARD_PLAN_LADDER.map(s => s.id);
const SPLIT_TMP_SUFFIX = '.tmp-split';   // [MUST] '.json'으로 끝나지 않는다 — listManifestFiles 오인 방지

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
  init                   Draft .opal/code-scan.json (--header-source required; --write, --force)
  discover               Infer a draft .opal/code-map/index.json (--out, --dry-run)
  scaffold               Create/update package manifests under .opal/code-map/
  target <file>          Decide where a file's @header should be written
  validate               Check code-map integrity (5 violation kinds, coverage)
  split <manifest>       Propose (--plan) or apply (--groups) a manifest split
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
                        split --plan: groups document output path
  --dry-run             discover/scaffold/split: compute without writing
  --write               init: write .opal/code-scan.json (default: stdout draft only)
  --force               init: overwrite an existing config (backs it up to *.json.bak)
  --changed <csv|->     validate: limit to a comma list or stdin newline list
  --plan                split: propose shard groups (writes nothing but --out)
  --groups <path|->     split: apply a groups document (file path or stdin)
  --trace               split --plan: per-stage ladder table
  --stop-after <Sn>     split --plan: stop the ladder after S1..S5

Split (manifest mode only):
  code-scan split <manifest> --plan --out <groups.json>     1) propose
  (edit groups.json — labels/files are the owner's call)    2) decide
  code-scan split <manifest> --groups <groups.json> --dry-run   3) rehearse
  code-scan split <manifest> --groups <groups.json>             4) apply

  Shard policy (2-axis: bytes AND entry count) is read from
  {project}/.opal/code-scan.json "shardPolicy" > ~/.opal/setting.json > built-in
  defaults (maxBytes 10240, minFiles 40).
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

  // discover 초안 출력 경로이자 split --plan groups 문서 출력 경로 — 플래그를 새로 만들지 않는다 (083 F-004)
  opts.out = null;
  opts.dryRun = false;
  opts.changed = null;
  opts.write = false;    // init: 기본은 쓰기 0건 (안전 기본값)
  opts.force = false;    // init: 기존 파일 덮어쓰기 (1세대 .bak 백업)
  opts.plan = false;     // split: 제안 모드 (--groups와 배타)
  opts.groups = null;    // split: 집행 모드 groups 문서 경로 ('-'면 stdin)
  opts.trace = false;    // split --plan: 단계별 검토 표 (검토 장치 1)
  opts.stopAfter = null; // split --plan: 사다리 중단 지점 (검토 장치 2)

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
    else if (a === '--out' && i + 1 < args.length) { opts.out = args[++i]; }
    else if (a === '--dry-run') { opts.dryRun = true; }
    else if (a === '--write') { opts.write = true; }
    else if (a === '--force') { opts.force = true; }
    else if (a === '--plan') { opts.plan = true; }
    else if (a === '--groups' && i + 1 < args.length) { opts.groups = args[++i]; }
    else if (a === '--trace') { opts.trace = true; }
    else if (a === '--stop-after' && i + 1 < args.length) { opts.stopAfter = args[++i]; }
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

/**
 * shardPolicy 객체 정규화 — 두 소스(code-scan.json · setting.json)가 같은 함수를 공유한다.
 * 알 수 없는 키는 무시한다. 알려진 키는 존재하면 스키마 타입을 만족해야 한다 (083 F-001).
 * @param {*} raw
 * @returns {{ok:true, value:object} | {ok:false, detail:string}}
 */
function normalizeShardPolicy(raw) {
  if (raw === undefined || raw === null) return { ok: true, value: {} };
  if (typeof raw !== 'object' || Array.isArray(raw)) {
    return { ok: false, detail: 'shardPolicy must be an object' };
  }
  const value = {};
  for (const k of SHARD_POLICY_KEYS) {
    if (!hasOwn(raw, k) || raw[k] === undefined || raw[k] === null) continue;
    const v = raw[k];
    if (SHARD_POLICY_SCHEMA[k] === 'positiveInt') {
      if (typeof v !== 'number' || !Number.isFinite(v) || !Number.isInteger(v) || v <= 0) {
        return { ok: false, detail: `shardPolicy.${k} must be a positive integer, got ${JSON.stringify(v)}` };
      }
    } else {   // 'nonEmptyString'
      if (typeof v !== 'string' || v.trim() === '') {
        return { ok: false, detail: `shardPolicy.${k} must be a non-empty string, got ${JSON.stringify(v)}` };
      }
    }
    value[k] = v;
  }
  return { ok: true, value };
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

  // shardPolicy 정규화 (083 F-001) — 위반은 configError로만 표면화하고 종료는 main()이 한다.
  const sp = normalizeShardPolicy(user.shardPolicy);

  return {
    extensions: user.extensions || DEFAULT_CONFIG.extensions,
    exclude: user.exclude || DEFAULT_CONFIG.exclude,
    excludePatterns: user.excludePatterns || [],
    scopes,
    headerSource: user.headerSource === undefined ? null : user.headerSource,
    shardPolicy: sp.ok ? sp.value : {},                      // 위반 시 빈 객체 → 하위 단계 폴백
    configPresent: true,
    configError: scopeErrorDetail ? 'config_scope_invalid'
               : (sp.ok ? null : 'shard_policy_invalid'),
    configErrorDetail: scopeErrorDetail || (sp.ok ? null : sp.detail),
  };
}

// [MUST] `opal/tools/state-tool/state_tool.py:236`: 경로는 OPAL_HOME env 우선(플랫폼 독립,
// ~/.opal 하드코딩 분기 금지). 같은 규칙을 code-scan에 적용한다 — 플랫폼 분기를 만들지 않는다.
function resolveOpalHome() {
  return process.env[OPAL_HOME_ENV] || path.join(os.homedir(), '.opal');
}

/**
 * ~/.opal/setting.json에서 **샤드 정책 키만** 읽는다 (083 F-002).
 * [MUST] 전역 설정 파일 부재·파싱 실패·키 부재는 모두 하위 단계로 폴백한다 —
 * headerSource식 전 명령 차단으로 승격하지 않는다. 이 함수는 throw/exit 하지 않는다.
 * 다른 키(bootstrap·models)는 읽지도 쓰지도 않는다.
 *
 * [MUST] 봉인 정적 검사는 소스 전체에서 이 이름 뒤에 여는 괄호가 붙은 등장 횟수를 1로 셈한다 —
 * 함수 선언문은 그 자체가 1회로 잡히므로 **함수 표현식**으로 정의해 호출 지점 1곳만 남긴다.
 *
 * @param {string} opalHome  주입 가능 — 테스트 격리 창구
 * @returns {{present:boolean, shardPolicy:object|null, error:string|null}}
 */
const loadGlobalSetting = function (opalHome) {
  const p = path.join(opalHome, 'setting.json');
  const miss = (error) => ({ present: true, shardPolicy: null, error });

  if (!fs.existsSync(p)) return { present: false, shardPolicy: null, error: null };   // 정상 — 침묵

  let parsed;
  try { parsed = JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch {
    noticeOnce('global_setting_unreadable',
      `${p}을 읽거나 파싱할 수 없습니다 — 샤드 정책은 하위 단계(코드 상수)로 폴백합니다`);
    return miss('global_setting_unreadable');
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    noticeOnce('global_setting_unreadable',
      `${p}이 JSON 객체가 아닙니다 — 샤드 정책은 하위 단계로 폴백합니다`);
    return miss('global_setting_unreadable');
  }
  if (!hasOwn(parsed, 'shardPolicy')) return { present: true, shardPolicy: null, error: null };  // 키 부재 — 침묵

  const n = normalizeShardPolicy(parsed.shardPolicy);
  if (!n.ok) {
    noticeOnce('global_shard_policy_invalid',
      `${p}의 shardPolicy가 무효입니다(${n.detail}) — 하위 단계로 폴백합니다. ` +
      `프로젝트 단위로 덮어쓰려면 {프로젝트}/.opal/code-scan.json의 shardPolicy를 사용하세요`);
    return miss('global_shard_policy_invalid');
  }
  return { present: true, shardPolicy: n.value, error: null };
};

// ── 용어사전 로더 (083 F-011) — 어떤 실패도 throw/exit 하지 않는다 ────────────

/**
 * docs/PROJECT.md에서 `{설계}` 변수(설계 산출물 루트) 등록을 찾는다.
 * [MUST] `opal/skills/op-data-dictionary/SKILL.md:21`: "사전 저장 경로는 하드코딩하지 않는다.
 * docs/PROJECT.md에 등록된 {설계} 변수(설계 산출물 루트)를 읽어 {설계}/사전/으로 해소한다."
 * 등록 포맷이 프로젝트마다 다르므로 관대하게 탐색하고, 못 찾으면 **null을 조용히** 돌려준다.
 * md 표 파싱은 parseMdTable 1곳에 봉인돼 있다 — 두 번째 표 파서를 만들지 않는다.
 * @returns {string|null} 후행 슬래시를 벗긴 상대 경로
 */
function readDesignRootFromProjectMd(projectRoot) {
  const p = path.join(projectRoot, 'docs', 'PROJECT.md');
  let md;
  try { md = fs.readFileSync(p, 'utf8'); } catch { return null; }

  const clean = (raw) => {
    const s = String(raw || '').split(',')[0].replace(/`/g, '').trim();
    if (!s || s === '-') return null;
    return s.replace(/\/+$/, '') || null;
  };

  // ① `| 요소 | 경로 |` 규약 표 (parseMdTable 공용 파서)
  for (const row of parseMdTable(md, ['요소', '경로'])) {
    if (String(row.cells['요소'] || '').replace(/`/g, '').trim() !== '{설계}') continue;
    const v = clean(row.cells['경로']);
    if (v) return v;
  }
  // ② `- {설계} = <경로>` / `{설계}: <경로>` 서술형
  const m1 = md.match(/^\s*[-*]\s*\{설계\}\s*=\s*(.+)$/m);
  if (m1) { const v = clean(m1[1]); if (v) return v; }
  const m2 = md.match(/\{설계\}\s*:\s*([^\s|]+)/);
  if (m2) { const v = clean(m2[1]); if (v) return v; }
  return null;
}

/**
 * 표준단어사전 경로를 해소한다 — 탐색 3단, 앞이 성공하면 뒤를 보지 않는다.
 * **어떤 실패도 throw하지 않는다.**
 * @returns {{abs:string|null, rel:string|null, source:'policy'|'project-var'|'default'|null, searched:string[]}}
 */
function resolveDictPath(ctx, policy) {
  const searched = [];
  const tryPath = (rel, source) => {
    if (!rel) return null;
    const norm = String(rel).split(path.sep).join('/').replace(/^\.\//, '');
    const abs = path.resolve(ctx.projectRoot, norm);
    // 경로 제한 (H-17) — 프로젝트 루트 밖은 읽지 않고 다음 후보로 넘어간다
    if (abs !== ctx.projectRoot && !abs.startsWith(ctx.projectRoot + path.sep)) {
      searched.push(`${norm}(프로젝트 밖 — 거부)`);
      return null;
    }
    searched.push(norm);
    let st;
    try { st = fs.statSync(abs); } catch { return null; }
    if (!st.isFile()) return null;
    if (st.size > DICT_MAX_BYTES) {
      noticeOnce('shard_dict_too_large',
        `${norm}이 사전 크기 상한(${DICT_MAX_BYTES} bytes)을 초과합니다 — "사전 없음"으로 취급하고 ` +
        `사전 대조 단계(S1~S3)를 건너뜁니다 (비차단)`);
      return null;
    }
    return { abs, rel: norm, source, searched };
  };

  // ① shardPolicy.dictPath 명시값 (3단 해석을 이미 거친 값)
  if (policy && policy.dictPath) { const r = tryPath(policy.dictPath, 'policy'); if (r) return r; }
  else searched.push('shardPolicy.dictPath(미설정)');

  // ② docs/PROJECT.md의 {설계} 변수 해소 → {설계}/사전/표준단어사전.md
  const designRoot = readDesignRootFromProjectMd(ctx.projectRoot);
  if (designRoot) { const r = tryPath(`${designRoot}/사전/${DICT_FILENAME}`, 'project-var'); if (r) return r; }
  else searched.push('docs/PROJECT.md {설계}(미등록)');

  // ③ 기본 경로 — SKILL.md 자기모순(H-19) 흡수: 두 후보를 순서대로 본다
  for (const rel of DICT_DEFAULT_RELS) { const r = tryPath(rel, 'default'); if (r) return r; }

  return { abs: null, rel: null, source: null, searched };
}

/**
 * 표준단어사전.md를 파싱한다. **컬럼 위치를 가정하지 않는다** (H-15).
 * 같은 문서 안에 컬럼 수가 다른 표 2개(수식어 6열 · 분류어 5열)가 존재하므로 위치 기반 파서는
 * 분류어 표에서 `약어` 자리에 `도메인` 값을 읽어 조용히 오분류한다.
 * md 표 훑기 자체는 공용 parseMdTable에 위임한다 — 이 함수는 헤더 이름 → 필드 사상만 한다.
 * @returns {{ok:true, rows:Array<{ko,en,abbr,index}>} | {ok:false, detail:string}}
 */
function parseWordDictionary(md) {
  const cell = (v) => {
    const s = v === null || v === undefined ? '' : String(v).replace(/`/g, '').trim();
    return (s === '' || s === '-') ? null : s;
  };
  const rows = [];
  for (const r of parseMdTable(md, ['한글', '영문', '약어'])) {
    const en = cell(r.cells['영문']);
    const abbr = cell(r.cells['약어']);
    if (!en && !abbr) continue;              // 매칭에 쓸 수 없는 행은 채택하지 않는다
    rows.push({ ko: cell(r.cells['한글']), en, abbr, index: rows.length });
  }
  if (rows.length === 0) return { ok: false, detail: 'no table with 한글/영문/약어 header' };
  return { ok: true, rows };
}

/**
 * 사전 폴백 3분기 (U-2 (4)) — 부재는 침묵, 파손은 noticeOnce 1줄, 둘 다 비차단이다.
 * [MUST] throw도 process.exit도 하지 않는다.
 * [MUST] 지연 로딩 — split --plan 경로에서만 호출된다. 조회 8커맨드에 새 I/O를 만들지 않는다(H-13).
 * @returns {{found:boolean, path:string|null, source:string|null, rows:Array|null, searched:string[]}}
 */
function loadWordDictionary(ctx, policy) {
  if (ctx._wordDict) return ctx._wordDict;                     // 실행당 1회
  const p = resolveDictPath(ctx, policy);
  let out;
  if (!p.abs) {
    out = { found: false, path: null, source: null, rows: null, searched: p.searched };   // 침묵
  } else {
    let md = null;
    try { md = fs.readFileSync(p.abs, 'utf8'); } catch { md = null; }
    const parsed = md === null ? { ok: false, detail: 'unreadable' } : parseWordDictionary(md);
    if (!parsed.ok) {
      noticeOnce('shard_dict_unparsable',
        `${p.rel}을 표준단어사전으로 읽을 수 없습니다(${parsed.detail}) — 사전 대조 단계(S1~S3)를 건너뜁니다 (비차단). ` +
        `형식: | 한글 | 영문 | 약어 | … (opal/skills/op-data-dictionary/SKILL.md Step 3)`);
      out = { found: false, path: p.rel, source: p.source, rows: null, searched: p.searched };
    } else {
      out = { found: true, path: p.rel, source: p.source, rows: parsed.rows, searched: p.searched };
    }
  }
  ctx._wordDict = out;
  return out;
}

/**
 * 이 실행의 샤드 정책을 확정한다 — 도구 전체에서 **유일한** 정책 판정 지점이다 (083 F-001).
 * 우선순위(셀 단위): {프로젝트}/.opal/code-scan.json > ~/.opal/setting.json > DEFAULT_SHARD_POLICY
 * 파생값 targetBytes는 설정 키가 아니다 — 여기서만 만든다.
 * [MUST] 이 함수 밖에서 DEFAULT_SHARD_POLICY / loadGlobalSetting을 참조하지 않는다.
 * @param {object} ctx {projectRoot, config, codeMap, headerSource}
 * @returns {{maxBytes:number, minFiles:number, dictPath:string|null, targetBytes:number}}
 */
function resolveShardPolicy(ctx) {
  if (ctx._shardPolicy) return ctx._shardPolicy;                  // 실행당 1회
  const project = (ctx.config && ctx.config.shardPolicy) || {};
  const global_ = loadGlobalSetting(resolveOpalHome()).shardPolicy || {};   // 지연 로딩 (F-002)
  const out = {};
  for (const k of SHARD_POLICY_KEYS) {
    out[k] = hasOwn(project, k) ? project[k]
           : hasOwn(global_, k) ? global_[k]
           : DEFAULT_SHARD_POLICY[k];
  }
  out.targetBytes = Math.max(1, Math.floor(out.maxBytes * SHARD_TARGET_RATIO));
  ctx._shardPolicy = out;
  return out;
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
      fix: '"headerSource": "inline" 또는 "manifest"를 .opal/code-scan.json에 추가하거나 --header-source <inline|manifest>로 실행하세요' +
        INIT_CREATE_FIX,
    };
  }

  // ⑤ 무효값 — 구형 값은 전용 마이그레이션 안내를 덧붙인다
  if (!HEADER_SOURCE_VALUES.includes(value)) {
    const out = {
      ok: false,
      error: 'header_source_invalid',
      detail: String(value),
      where: 'config',
      fix: '.opal/code-scan.json의 headerSource는 ' + HEADER_SOURCE_VALUES.join(' 또는 ') + ' 중 하나여야 합니다' +
        INIT_CREATE_FIX,
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
  // 구 위치 manifestMaxBytes는 폐기됐다 (083 F-007). 값을 읽지 않고 실행당 1회 안내만 한다 —
  // 무시할 키를 타입 검증해 차단하는 것은 "무시한다"와 모순이다 (080 F-002 선례).
  if (hasOwn(index, 'manifestMaxBytes')) {
    deprecationOnce('index_manifest_max_bytes',
      '.opal/code-map/index.json의 manifestMaxBytes는 폐기되었습니다 — ' +
      '{프로젝트}/.opal/code-scan.json의 "shardPolicy": {"maxBytes": <바이트>} 로 이전하세요 ' +
      '(자동 변환하지 않습니다)');
  }
  return { present: true, index, manifests: new Map(), shardViews: new Map() };
}

// ── 2축 판정식 (083 F-003) — 판정 로직을 소비 지점에 복제하지 않는다 ─────────

// 해당 매니페스트 **자신의** 엔트리 수. 합집합이 아니다 — 판정 대상은 "이 파일이 쪼갤 만한가"이므로
// 베이스는 베이스의 files만, 샤드는 샤드의 files만 센다.
function manifestEntryCount(manifest) {
  return manifest && manifest.files ? Object.keys(manifest.files).length : 0;
}

// 2축 판정 — 바이트 초과 **AND** 엔트리 수 이상. 경계: size===maxBytes는 초과 아님
// (082 off-by-one 계약 보존), entries===minFiles는 **대상**(하한은 "이상").
function isOversizeManifest(bytes, entryCount, policy) {
  return bytes > policy.maxBytes && entryCount >= policy.minFiles;
}

// 권고 조각 수 — 트리거가 아니라 targetBytes로 나눈다 (확정 방향 #9). 최소 2조각.
function recommendedShardCount(bytes, policy) {
  return Math.max(2, Math.ceil(bytes / policy.targetBytes));
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
    return { scopeName: scoped.name, scope: scoped.scope, dirRel, mp: null, manifest: null, manifestRel: null, manifestAbs: null, shardView: null };
  }
  const manifestRel = `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`;
  const manifestAbs = path.join(ctx.projectRoot, manifestRel);
  const manifest = loadManifest(manifestAbs, ctx);
  const shardView = resolveShards(manifestAbs, manifestRel, manifest, ctx);
  return { scopeName: scoped.name, scope: scoped.scope, dirRel, mp, manifestRel, manifestAbs, manifest, shardView };
}

// ── Shard resolution (082 F-001) — 봉인 지점 1곳 ─────────────────────────
//
// 샤드 경로 조립·로딩·byKey 구성·중복 판정은 이 함수 밖에 존재하지 않는다
// (080 resolveHeaderSource/isInScope 선례 — PLAN §3.1.2 (D)).

// 샤드 파일 := 직속 부모 디렉토리 이름이 SHARDS_DIR인 .json
function isShardManifestPath(manifestAbs) {
  return path.basename(path.dirname(manifestAbs)) === SHARDS_DIR;
}

// 샤드 → 소유 베이스 매니페스트 절대 경로 (…/{stem}/_shards/{label}.json → …/{stem}.json)
function baseManifestAbsForShard(shardAbs) {
  return path.dirname(path.dirname(shardAbs)) + '.json';
}

/**
 * 샤드 해석의 **유일한** 지점. 샤드 로딩·byKey 구성·중복 판정은 이 함수 밖에 존재하지 않는다.
 * @param {string} baseManifestAbs  베이스 매니페스트 절대 경로 (mirrorPathForDir 산출 경로)
 * @param {string} baseManifestRel  프로젝트 루트 기준 POSIX 상대 경로
 * @param {object|null} baseManifest
 * @param {object} ctx  {projectRoot, config, codeMap, headerSource}
 * @returns {object|null} ShardView { baseRel, shards, byKey, duplicates }
 * @throws {CodeMapFatalError} 'shard_declaration_invalid'
 */
function resolveShards(baseManifestAbs, baseManifestRel, baseManifest, ctx) {
  // null 반환 4조건 (= 옵트인·바이트 동일성의 구조적 보증)
  if (ctx.headerSource !== 'manifest') return null;      // ① inline 모드 무영향 게이트
  if (!baseManifest) return null;                          // ②
  if (!hasOwn(baseManifest, 'shards')) return null;         // ③
  if (Array.isArray(baseManifest.shards) && baseManifest.shards.length === 0) return null; // ④

  const cache = ctx.codeMap.shardViews || (ctx.codeMap.shardViews = new Map());
  if (cache.has(baseManifestAbs)) return cache.get(baseManifestAbs);

  if (!Array.isArray(baseManifest.shards)) {
    throw new CodeMapFatalError('shard_declaration_invalid', `${baseManifestRel}: shards must be an array`);
  }

  const seenLabels = new Set();
  const shards = [];
  for (const label of baseManifest.shards) {
    if (typeof label !== 'string' || !SHARD_LABEL_RE.test(label)) {
      throw new CodeMapFatalError('shard_declaration_invalid', `${baseManifestRel}: invalid shard label "${label}"`);
    }
    if (seenLabels.has(label)) {
      throw new CodeMapFatalError('shard_declaration_invalid', `${baseManifestRel}: duplicate shard label "${label}"`);
    }
    seenLabels.add(label);

    const dir = path.dirname(baseManifestAbs);
    const stem = path.basename(baseManifestAbs, '.json');
    const manifestAbs = path.join(dir, stem, SHARDS_DIR, label + '.json');
    const manifestRel = toPosixRel(ctx.projectRoot, manifestAbs);
    const manifest = loadManifest(manifestAbs, ctx);
    shards.push({ label, manifestRel, manifestAbs, manifest });
  }

  // 합집합 구성 순서 (U-4: 선언 순서 우선 + 첫 승리)
  const byKey = new Map();
  const duplicates = [];

  if (baseManifest.files) {
    for (const key of Object.keys(baseManifest.files)) {
      byKey.set(key, {
        owner: 'base',
        label: null,
        manifestRel: baseManifestRel,
        entry: baseManifest.files[key],
        shardPackage: null
      });
    }
  }

  for (const s of shards) {
    if (!s.manifest || !s.manifest.files) continue;
    for (const key of Object.keys(s.manifest.files)) {
      if (byKey.has(key)) {
        const winner = byKey.get(key);
        let dup = duplicates.find(d => d.key === key);
        if (!dup) { dup = { key, winner: winner.manifestRel, losers: [] }; duplicates.push(dup); }
        dup.losers.push(s.manifestRel);
        continue;
      }
      byKey.set(key, {
        owner: 'shard',
        label: s.label,
        manifestRel: s.manifestRel,
        entry: s.manifest.files[key],
        shardPackage: s.manifest.package || null
      });
    }
  }

  const view = { baseRel: baseManifestRel, shards, byKey, duplicates };
  cache.set(baseManifestAbs, view);
  return view;
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
  const basePkg = (mctx.manifest && mctx.manifest.package) || null;
  const owned = mctx.shardView ? mctx.shardView.byKey.get(basename) : null;

  const fe = owned
    ? owned.entry
    : ((mctx.manifest && mctx.manifest.files && mctx.manifest.files[basename]) || null);

  // package 3단: files > 소유 샤드 package > 베이스 package (082 F-001, PLAN §3.1.2 (G))
  // 샤드 미선언 시 pkgChain === [basePkg]이므로 아래 루프는 기존 else-if와 의미상 동일하다.
  const pkgChain = (owned && owned.shardPackage) ? [owned.shardPackage, basePkg] : [basePkg];

  const layerMatch = matchLayerRule(relPath, ctx.codeMap.index.layerRules || []);
  const domainMatch = matchDomain(relPath, ctx.codeMap.index.domains || {});

  const result = {};
  const sources = {};
  let contributed = false;

  for (const field of WORKER_FIELDS) {
    if (hasOwn(fe, field)) { result[field] = fe[field]; sources[field] = 'file'; contributed = true; continue; }
    for (const p of pkgChain) {
      if (hasOwn(p, field)) { result[field] = p[field]; sources[field] = 'package'; contributed = true; break; }
    }
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
      const baseRel = `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`;
      const baseAbs = path.join(ctx.projectRoot, baseRel);
      const key     = path.basename(relPath);

      out.scope = scoped.name;
      out.key   = key;

      // 샤드 라우팅 2단 (U-3: 글롭 미채택) — 보유 샤드 → 없으면 베이스 (082 F-002, PLAN §3.2.2)
      const view  = resolveShards(baseAbs, baseRel, loadManifest(baseAbs, ctx), ctx);
      const owned = view ? view.byKey.get(key) : null;
      if (owned && owned.owner === 'shard') {
        out.manifest = owned.manifestRel;   // ① 보유 샤드
        out.shard    = owned.label;         // 샤드 라우팅 시에만 부여
      } else {
        out.manifest = baseRel;             // ② 베이스 보유 · ③ 미보유 신규 파일
      }
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

  const outPath = opts.out ? path.resolve(projectRoot, opts.out) : path.join(projectRoot, CODE_MAP_DIR, 'index.json');
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

// ── init (083 F-012) ─────────────────────────────────────────────────────

// 규약 예시(`pm/code-scan-management.md`)의 exclude 10종 — init 초안과 init의 디렉토리 스캔
// 필터가 공유한다. config.exclude를 쓰지 않는다 — init은 깨진 config에서도 동작해야 한다.
// init 초안이 **쓰는** 설정 키 이름 — 모드 판정이 아니라 산출물의 필드명이다.
// 판정은 전적으로 resolveHeaderSource 1곳에 있고, 여기서는 값을 그대로 실어 나르기만 한다.
const CONFIG_KEY_HEADER_SOURCE = 'headerSource';

const INIT_EXCLUDE = Object.freeze([
  'node_modules', '__pycache__', '.git', 'dist', 'build', '.venv',
  'backup', '.pytest_cache', '.next', '.nuxt',
]);

/**
 * md 본문에서 required 헤더를 **모두** 가진 표를 찾아 행을 뽑는다. 위치를 가정하지 않는다.
 * 표준단어사전 파서와 PROJECT.md 프로젝트 구성 파서가 공유한다 — md 표 파서는 이것 1개뿐이다.
 * @param {string} md
 * @param {string[]} requiredHeaders  예: ['한글','영문','약어'] / ['요소','경로']
 * @returns {Array<{cells:Object<string,string|null>, index:number}>}  매칭 표가 없으면 []
 */
function parseMdTable(md, requiredHeaders) {
  const lines = String(md || '').split(/\r?\n/);
  const cellsOf = (line) => {
    let s = line.trim();
    if (s.startsWith('|')) s = s.slice(1);
    if (s.endsWith('|')) s = s.slice(0, -1);
    return s.split('|').map(c => c.trim());
  };
  const rows = [];
  let index = 0;
  for (let i = 0; i + 1 < lines.length; i++) {
    if (!/^\s*\|/.test(lines[i])) continue;
    if (!/^\s*\|[\s:|-]+\|?\s*$/.test(lines[i + 1])) continue;   // 헤더 다음 줄이 구분행인가
    const headers = cellsOf(lines[i]);
    if (!requiredHeaders.every(h => headers.includes(h))) continue;
    for (let j = i + 2; j < lines.length && /^\s*\|/.test(lines[j]); j++) {
      const cells = cellsOf(lines[j]);
      const obj = {};
      headers.forEach((h, k) => { obj[h] = cells[k] === undefined ? null : cells[k]; });
      rows.push({ cells: obj, index: index++ });
    }
  }
  return rows;
}

// docs/PROJECT.md의 `## 프로젝트 구성` 절 아래 표에서 행을 읽는다 — 컬럼은 이름으로 찾는다.
function readProjectStructureTable(projectRoot) {
  const p = path.join(projectRoot, 'docs', 'PROJECT.md');
  if (!fs.existsSync(p)) return [];
  let md;
  try { md = fs.readFileSync(p, 'utf8'); } catch { return []; }
  const lines = md.split(/\r?\n/);
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    if (/^#{1,6}\s+.*프로젝트 구성/.test(lines[i])) { start = i + 1; break; }
  }
  if (start === -1) return [];
  let end = lines.length;
  for (let i = start; i < lines.length; i++) {
    if (/^#{1,6}\s/.test(lines[i])) { end = i; break; }
  }
  return parseMdTable(lines.slice(start, end).join('\n'), ['요소', '경로']);
}

function toScopeName(raw) {
  return String(raw || '').trim().toLowerCase()
    .replace(/[_\s]+/g, '-').replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-').replace(/^-|-$/g, '');
}

// 경로 컬럼: 백틱을 벗기고 **첫 경로만** 채택하며 끝에 `/`를 보정한다.
function toScopeRoot(raw) {
  const first = String(raw || '').split(',')[0].replace(/`/g, '').trim();
  if (!first) return null;
  return first.endsWith('/') ? first : first + '/';
}

// scopes 추론 — 규약 소스는 PROJECT.md 표, 부재 시 루트 1-depth 디렉토리 스캔으로 대체한다.
function inferProjectScopes(projectRoot) {
  const scopes = {};
  for (const row of readProjectStructureTable(projectRoot)) {
    const name = toScopeName(row.cells['요소']);
    const root = toScopeRoot(row.cells['경로']);
    if (!name || !root) continue;
    scopes[name] = root;
  }
  if (Object.keys(scopes).length > 0) return scopes;
  // 폴백 — inferScopes의 디렉토리 스캔 경로를 재사용한다(두 번째 스캐너를 만들지 않는다).
  const scanned = inferScopes(projectRoot, { scopes: {}, exclude: INIT_EXCLUDE });
  const out = {};
  for (const [name, def] of Object.entries(scanned)) out[name] = def.root;
  return out;
}

// 스코프 루트를 순회해 **실재하는** 코드 확장자만 수집한다. `.md`는 감지와 무관하게 항상 포함한다.
function detectExtensions(projectRoot, scopes) {
  const candidates = DEFAULT_CONFIG.extensions.concat(['.md']);
  const candSet = new Set(candidates);
  const found = new Set();
  const walk = (dirAbs, depth) => {
    if (depth > 8 || found.size === candSet.size) return;
    let entries;
    try { entries = fs.readdirSync(dirAbs, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (found.size === candSet.size) return;
      if (e.name.startsWith('.') || INIT_EXCLUDE.includes(e.name)) continue;
      if (e.isDirectory()) walk(path.join(dirAbs, e.name), depth + 1);
      else { const ext = path.extname(e.name); if (candSet.has(ext)) found.add(ext); }
    }
  };
  for (const root of Object.values(scopes)) walk(path.resolve(projectRoot, root), 0);
  const out = candidates.filter(x => found.has(x));
  if (!out.includes('.md')) out.push('.md');
  return out;
}

/**
 * `.opal/code-scan.json` 초안을 만든다 — 대화형 프롬프트는 없다(비대화형 계약).
 * headerSource는 **추론하지 않는다**: 2택은 소유자가 확인해 확정하는 값이므로 CLI 인자로 강제한다.
 * 깨진 config에서도 동작해야 하는 복구 창구이므로 config의 어떤 필드도 참조하지 않는다.
 */
function cmdInit(projectRoot, config, opts) {
  // 인자 유무 판정도 값 도메인 판정도 resolveHeaderSource 1곳에 봉인돼 있다 — 빈 config를 주면
  // CLI 인자만 보는 경로가 되며, 미지정은 unset으로 돌아온다. 재검증 로직을 새로 쓰지 않는다.
  const hs = resolveHeaderSource({ configError: null }, opts);
  if (!hs.ok) {
    if (hs.error === 'header_source_unset') {
      return errorExit('init_header_source_required', {
        detail: '--header-source가 필요합니다',
        where: 'cli',
        fix: 'code-scan init --header-source <inline|manifest> [--write] — 도구는 이 2택을 추론하지 않습니다',
        doc: HEADER_SOURCE_DOC,
      });
    }
    const extra = { detail: hs.detail, where: hs.where, fix: hs.fix, doc: HEADER_SOURCE_DOC };
    if (hs.migration) extra.migration = hs.migration;
    return errorExit(hs.error, extra);
  }

  const scopes = inferProjectScopes(projectRoot);
  // 키 순서는 규약 예시와 동일하다. shardPolicy는 **넣지 않는다** — 넣으면 3단 폴백의
  // 2·3단(전역 설정·코드 상수)이 영원히 도달 불가가 된다 (083 F-012 (E)).
  const draft = {
    [CONFIG_KEY_HEADER_SOURCE]: hs.value,
    scopes,
    extensions: detectExtensions(projectRoot, scopes),
    exclude: INIT_EXCLUDE.slice(),
    excludePatterns: [],
  };

  const cfgPath = path.join(projectRoot, '.opal', 'code-scan.json');
  const cfgRel = toPosixRel(projectRoot, cfgPath);

  const emit = (written, backup) => {
    if (opts.output === 'json') {
      console.log(JSON.stringify({ ok: true, command: 'init', written, path: cfgRel, backup, draft }));
    } else {
      console.log(JSON.stringify(draft, null, 2));   // 파이프 친화 — 초안 JSON 그대로
    }
  };

  if (!opts.write) { emit(false, null); return; }

  if (fs.existsSync(cfgPath) && !opts.force) {
    return errorExit('config_exists', {
      detail: `${cfgRel}이 이미 존재합니다`,
      where: 'config',
      fix: '덮어쓰려면 --force를 함께 주세요: code-scan init --header-source <inline|manifest> --write --force ' +
           `(기존 파일은 ${cfgRel}.bak으로 백업됩니다)`,
    });
  }

  let backup = null;
  fs.mkdirSync(path.dirname(cfgPath), { recursive: true });
  if (fs.existsSync(cfgPath)) { fs.copyFileSync(cfgPath, cfgPath + '.bak'); backup = cfgRel + '.bak'; }
  fs.writeFileSync(cfgPath, JSON.stringify(draft, null, 2) + '\n');

  // 생성 보고 — stdout JSON을 오염시키지 않는다.
  process.stderr.write(
    `📂 code-scan.json 자동 생성: headerSource=${hs.value} · ` +
    `scopes=${Object.keys(scopes).length}종 · extensions=[${draft.extensions.join(', ')}] · ` +
    `exclude=[${draft.exclude.join(', ')}]\n`);
  emit(true, backup);
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
  if (existing && hasOwn(existing, 'shards')) manifest.shards = existing.shards;
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
  const reserved = [];             // 소스 디렉토리가 _shards 예약어와 충돌 (082 F-006)

  for (const scopeName of scopeNames) {
    const scope = index.scopes[scopeName];
    const scopeRootAbs = path.resolve(projectRoot, scope.root);
    const dirsWithFiles = collectDirsWithCodeFiles(scopeRootAbs, projectRoot, config, index, scope);
    for (const d of dirsWithFiles) {
      const mp = mirrorPathForDir(d.dirRel, scopeName, scope);
      if (mp.skipped) continue;
      const manifestRel = `${CODE_MAP_DIR}/${scopeName}/${mp.mirrorRel}.json`;
      if (mp.mirrorRel.split('/').includes(SHARDS_DIR)) {
        reserved.push({ dir: d.dirRel, manifest: manifestRel });
        continue;
      }
      const manifestAbs = path.join(projectRoot, manifestRel);
      if (manifestOwner.has(manifestAbs)) {
        collisions.push({ manifest: manifestRel, a: manifestOwner.get(manifestAbs), b: d.dirRel });
      } else {
        manifestOwner.set(manifestAbs, d.dirRel);
      }
      perDir.push({ scopeName, dirRel: d.dirRel, files: d.files, manifestAbs, manifestRel });
    }
  }

  if (reserved.length > 0) {
    return errorExit('reserved_name_collision', { reserved });
  }

  if (collisions.length > 0) {
    return errorExit('mirror_collision', { collisions });
  }

  const created = [], updated = [], unchanged = [], addedAll = [], prunedAll = [], skippedAll = [];
  const dryRun = !!opts.dryRun;
  const policy = resolveShardPolicy(ctx);

  for (const entry of perDir) {
    let existingBase = null;
    if (fs.existsSync(entry.manifestAbs)) {
      try { existingBase = JSON.parse(fs.readFileSync(entry.manifestAbs, 'utf8')); } catch { existingBase = null; }
    }
    const view = resolveShards(entry.manifestAbs, entry.manifestRel, existingBase, ctx);
    entry.view = view; // stale 집합 계산에서 재사용 (082 F-004 §3.4.2 (C))

    // 가드 1: 중복 키 (U-4 파생 결정) — 자동 해소 금지, 디렉토리 전체를 쓰지 않는다
    if (view && view.duplicates.length > 0) {
      skippedAll.push({
        reason: 'shard_duplicate_key', manifest: entry.manifestRel,
        detail: view.duplicates.map(d => d.key).join(','),
      });
      continue;
    }

    // 가드 2: 선언됐으나 파일 없는 샤드 — skipped 기록, 빈 샤드 파일을 새로 만들지 않는다
    for (const s of (view ? view.shards : [])) {
      if (!s.manifest) {
        skippedAll.push({ reason: 'shard_missing', manifest: s.manifestRel, detail: s.label });
      }
    }

    // 버킷 분배 (U-3: 보유 샤드 → 없으면 베이스) — manifestRel 기준(byKey 엔트리가 abs를 싣지 않는다)
    const buckets = new Map();
    buckets.set(entry.manifestRel, { manifestAbs: entry.manifestAbs, existing: existingBase, files: [] });
    for (const s of (view ? view.shards : [])) {
      if (s.manifest) buckets.set(s.manifestRel, { manifestAbs: s.manifestAbs, existing: s.manifest, files: [] });
    }
    for (const bn of entry.files) {
      const o = view ? view.byKey.get(bn) : null;
      if (o && o.owner === 'shard' && buckets.has(o.manifestRel)) {
        buckets.get(o.manifestRel).files.push(bn);
      } else {
        buckets.get(entry.manifestRel).files.push(bn);
      }
    }

    for (const [manifestRel, bucket] of buckets) {
      const manifestAbs = bucket.manifestAbs;
      const bucketEntry = { scopeName: entry.scopeName, dirRel: entry.dirRel, files: bucket.files };
      const { manifest, pruned, added } = mergeManifest(bucket.existing, bucketEntry);
      const serialized = JSON.stringify(manifest, null, 2) + '\n';
      const isNew = !fs.existsSync(manifestAbs);
      const prevContent = isNew ? null : fs.readFileSync(manifestAbs, 'utf8');
      const changed = isNew || prevContent !== serialized;

      if (changed && !dryRun) {
        fs.mkdirSync(path.dirname(manifestAbs), { recursive: true });
        fs.writeFileSync(manifestAbs, serialized);
      }

      if (isNew) created.push(manifestRel);
      else if (changed) updated.push(manifestRel);
      else unchanged.push(manifestRel);
      addedAll.push(...added.map(f => `${manifestRel}:${f}`));
      prunedAll.push(...pruned.map(f => `${manifestRel}:${f}`));

      // 크기 상한 알림 — stdout JSON은 건드리지 않는다 (082 F-005 §3.5.2 (C), TS-023/S-17)
      const bytes = Buffer.byteLength(serialized);
      const entries = manifestEntryCount(manifest);
      if (isOversizeManifest(bytes, entries, policy)) {
        process.stderr.write(
          `code-scan: [oversize] ${manifestRel} — ${bytes} bytes > ${policy.maxBytes} 상한, ` +
          `엔트리 ${entries}개(하한 ${policy.minFiles}). 권고 ${recommendedShardCount(bytes, policy)}조각 — ` +
          `code-scan split ${manifestRel} --plan\n`);
      }
    }
  }

  // stale 집합 — 선언된 샤드(파일 존재 여부 무관)를 포함해 오탐을 없앤다.
  // 미선언 샤드는 그대로 stale로 남는다 — validate의 shard_undeclared와 신호가 일치한다 (082 §9 R-2/H-2).
  const validManifestPaths = new Set();
  for (const e of perDir) {
    validManifestPaths.add(e.manifestAbs);
    for (const s of (e.view ? e.view.shards : [])) {
      validManifestPaths.add(s.manifestAbs);
    }
  }
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
    added: addedAll, pruned: prunedAll, stale: staleList, skipped: skippedAll,
  };
  if (opts.output === 'json') console.log(JSON.stringify(result));
  else console.log(`scaffold: created=${result.created} updated=${result.updated} unchanged=${result.unchanged} added=${addedAll.length} pruned=${prunedAll.length} stale=${staleList.length}`);
}

// ═══════════════════════════════════════════
// split — 분할 제안(사다리 엔진) + 분할 집행 (083 F-004/F-005)
// ═══════════════════════════════════════════

// 엔트리 1건이 매니페스트에서 차지하는 대략 바이트 (직렬화 후 키 + 값 + 구두점)
function entryBytes(key, entry) {
  return Buffer.byteLength(JSON.stringify({ [key]: entry }, null, 2)) + 2;
}

// 파일명 → 소문자 토큰 배열. 확장자 제거 → camel/Pascal 경계 + `_`·`-`·`.` 분해 → 소문자.
// 'PricingCalculator.ts' → ['pricing','calculator'] / 'order_repo.py' → ['order','repo']
function splitTokens(key) {
  return String(key).replace(/\.[^.]+$/, '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_\-.]+/g, ' ')
    .split(/\s+/)
    .map(t => t.toLowerCase().replace(/[^a-z0-9]/g, ''))
    .filter(Boolean);
}

// 라벨 정규형 — SHARD_LABEL_RE(kebab)를 만족하는 형태로 깎는다. 경로 이탈 문자는 여기서 소멸한다.
function toShardLabel(raw) {
  return String(raw || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

// 사전 대조용 정규형 — 토큰 스팬(공백 없이 이어붙인 소문자)과 같은 축으로 맞춘다.
function normalizeDictForm(raw) {
  return String(raw || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

// 기존 라벨과 충돌하면 `-2`, `-3`… 접미. usedLabels 갱신은 호출자가 한다.
function uniqueShardLabel(base, usedLabels) {
  let label = toShardLabel(base);
  if (!label || !SHARD_LABEL_RE.test(label)) label = 'group';
  if (!usedLabels.has(label)) return label;
  let n = 2;
  while (usedLabels.has(`${label}-${n}`)) n++;
  return `${label}-${n}`;
}

/**
 * 토큰 스팬 ↔ 사전 매칭. 대소문자 무시, 영문·약어 두 컬럼 후보.
 * 다중 매칭 시 ① 스팬 토큰 수 내림차순 → ② 사전 등재 순서(row.index) 오름차순 (U-2 (3)).
 * @returns {{canonical:string, from:number, to:number, index:number, span:number}|null}
 */
function dictMatchSpan(tokens, dict, fromIdx, maxSpanTokens) {
  if (!dict || !Array.isArray(dict.rows) || dict.rows.length === 0) return null;
  const max = Math.min(maxSpanTokens, tokens.length - fromIdx);
  for (let span = max; span >= 1; span--) {           // 긴 스팬 우선 (longest-match)
    const joined = tokens.slice(fromIdx, fromIdx + span).join('');
    if (!joined) continue;
    let cand = null;
    for (const row of dict.rows) {
      const forms = [];
      if (row.en) forms.push(normalizeDictForm(row.en));
      if (row.abbr) forms.push(normalizeDictForm(row.abbr));
      if (!forms.includes(joined)) continue;
      if (cand === null || row.index < cand.index) cand = row;   // 동률이면 등재 순서
    }
    if (cand) {
      return {
        canonical: toShardLabel(cand.en || cand.abbr),
        from: fromIdx, to: fromIdx + span - 1, index: cand.index, span,
      };
    }
  }
  return null;
}

/**
 * 한 단계의 그룹핑 키를 돌려준다. null이면 이 단계에서 배정하지 않는다.
 * @returns {string|null} 그룹핑 키 (= 라벨 후보)
 */
function stageKeyFor(stage, key, entry, dict, freq) {
  const tokens = splitTokens(key);
  if (tokens.length === 0) return null;
  switch (stage.signal) {
    case 'first-token': {
      const m = dictMatchSpan(tokens, dict, 0, 1);
      return m ? m.canonical : null;
    }
    case 'first-two': {
      const m = dictMatchSpan(tokens, dict, 0, 2);
      if (m && m.span >= 2) return m.canonical;        // 사전 행 1개가 2토큰을 통째로 덮은 경우
      // 두 토큰이 각각 다른 행에 매칭되면 `{c0}-{c1}` 결합. 첫 토큰 단독 매칭은 S1의 신호이므로 제외.
      const a = dictMatchSpan(tokens, dict, 0, 1);
      const b = tokens.length > 1 ? dictMatchSpan(tokens, dict, 1, 1) : null;
      if (a && b) return toShardLabel(`${a.canonical}-${b.canonical}`);
      return null;
    }
    case 'any-token': {
      let best = null;
      for (let i = 0; i < tokens.length; i++) {
        const m = dictMatchSpan(tokens, dict, i, tokens.length - i);
        if (!m) continue;
        if (best === null || m.span > best.span || (m.span === best.span && m.index < best.index)) best = m;
      }
      return best ? best.canonical : null;
    }
    case 'last-token': {
      // 토큰이 1개뿐이면 null — S1과 같은 신호를 두 번 세지 않는다
      if (tokens.length < 2) return null;
      return toShardLabel(tokens[tokens.length - 1]) || null;
    }
    case 'depends': {
      const d = entry && Array.isArray(entry.depends) ? entry.depends : null;
      if (!d || d.length === 0) return null;
      let bestKey = null;
      let bestFreq = -1;
      for (const raw of d) {
        const lab = toShardLabel(raw);
        if (!lab) continue;
        const f = (freq && freq.get(lab)) || 0;
        if (f > bestFreq || (f === bestFreq && bestKey !== null && lab < bestKey)) { bestFreq = f; bestKey = lab; }
      }
      return bestKey;
    }
    default:
      return null;
  }
}

/**
 * 그룹 후보를 산출한다 — **파일을 쓰지 않는다**. 결정론적이다(H-10).
 * @param {Map<string,object>} baseEntries  베이스에 남아 있는 엔트리만 (샤드 보유분 제외)
 * @param {Set<string>} usedLabels          기존 샤드 라벨 (충돌 회피) — 호출자 소유, 여기서 갱신된다
 * @param {{maxBytes,minFiles,targetBytes}} policy
 * @param {{rows:Array}|null} dict          rows가 없으면 dict:true 단계 자동 skip (U-2 (4))
 * @param {{stopAfter:string|null, shardOverheadBytes:number}} opts
 * @returns {{groups, unassigned, coverage, assignments, trace, ladder}}
 */
function planShardGroups(baseEntries, usedLabels, policy, dict, opts) {
  const stopAfter = (opts && opts.stopAfter) || null;
  const overhead = (opts && opts.shardOverheadBytes) || 0;
  const total = baseEntries.size;
  const remaining = new Map(baseEntries);
  const groups = [];
  const assignments = {};
  const trace = [];
  const ladder = [];
  const byStage = {};
  let stopped = false;

  for (const stage of SHARD_PLAN_LADDER) {
    const input = remaining.size;
    let skipped = false;
    let reason = null;
    if (stopped) { skipped = true; reason = 'stopped'; }
    else if (stage.dict && !(dict && Array.isArray(dict.rows) && dict.rows.length > 0)) {
      skipped = true; reason = 'dict_absent';
    }

    let assigned = 0;
    let groupCount = 0;
    if (!skipped) {
      // S5의 freq는 **그 단계 진입 시점의 remaining** 기준으로 1회 계산한다 — 배정 중 빈도가 변하면
      // 순서 의존이 생겨 결정론이 깨진다.
      let freq = null;
      if (stage.signal === 'depends') {
        freq = new Map();
        for (const entry of remaining.values()) {
          const d = entry && Array.isArray(entry.depends) ? entry.depends : [];
          const seen = new Set();
          for (const raw of d) {
            const lab = toShardLabel(raw);
            if (!lab || seen.has(lab)) continue;
            seen.add(lab);
            freq.set(lab, (freq.get(lab) || 0) + 1);
          }
        }
      }

      const buckets = new Map();
      for (const [key, entry] of remaining) {
        const k = stageKeyFor(stage, key, entry, dict, freq);
        if (!k) continue;                              // 이 단계에서 손대지 않는다
        if (!buckets.has(k)) buckets.set(k, []);
        buckets.get(k).push(key);
      }
      // 채택: 버킷 크기 >= accept. 미달 버킷은 remaining에 그대로 남아 **다음 단계로 흘러간다**.
      const adopted = [...buckets.entries()]
        .filter(([, files]) => files.length >= stage.accept)
        .sort((a, b) => (b[1].length - a[1].length) || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
      for (const [bucketKey, files] of adopted) {
        const label = uniqueShardLabel(bucketKey, usedLabels);
        usedLabels.add(label);
        const sorted = files.slice().sort();
        for (const f of sorted) { assignments[f] = stage.id; remaining.delete(f); }
        assigned += sorted.length;
        groupCount++;
        groups.push({ label, stage: stage.id, files: sorted, estimatedBytes: 0, oversizeGroup: false });
      }
    }

    byStage[stage.id] = assigned;
    ladder.push({ id: stage.id, signal: stage.signal, dict: stage.dict, accept: stage.accept, skipped });
    trace.push({ stage: stage.id, dict: stage.dict, input, assigned, groups: groupCount, remaining: remaining.size, skipped, reason });
    if (!stopped && stopAfter === stage.id) stopped = true;
  }

  // 크기 목표 점검 — 초과는 **표시만** 한다. 도구가 강제 재분할하지 않는다 (U-2 (6) 규칙 2).
  for (const g of groups) {
    let b = overhead;
    for (const f of g.files) b += entryBytes(f, baseEntries.get(f));
    g.estimatedBytes = b;
    g.oversizeGroup = b > policy.targetBytes;
  }

  // 결정론 정렬 — 단계 순서 우선 → 엔트리 수 내림차순 → 라벨 사전순
  const stageOrder = {};
  SHARD_PLAN_STAGE_IDS.forEach((id, i) => { stageOrder[id] = i; });
  groups.sort((a, b) =>
    (stageOrder[a.stage] - stageOrder[b.stage]) ||
    (b.files.length - a.files.length) ||
    (a.label < b.label ? -1 : a.label > b.label ? 1 : 0));

  // 잔여 확정 — 임의 배분·"기타" 그룹 생성 금지 (brain 승계 #3)
  const unassigned = [...remaining.keys()].sort();
  return {
    groups, unassigned, assignments, trace, ladder,
    coverage: { assigned: total - unassigned.length, unassigned: unassigned.length, total, byStage },
  };
}

// ── split 집행 (F-005) — 자산을 쓰는 유일한 명령. 원자성이 계약이다 ────────

function shardDirForBase(baseManifestAbs) {
  return path.join(path.dirname(baseManifestAbs), path.basename(baseManifestAbs, '.json'), SHARDS_DIR);
}

/**
 * 디스크 기준 총 엔트리 수 — 베이스 + `_shards/` 아래 **실재하는 모든** 샤드 파일.
 * 미선언 샤드 파일의 내용도 자산이므로 유실 판정(사후 검증)에 포함한다.
 * @returns {number} 읽기·파싱 실패 시 -1 (= 검증 실패로 취급)
 */
function diskTotalEntries(baseManifestAbs) {
  let total;
  try { total = manifestEntryCount(JSON.parse(fs.readFileSync(baseManifestAbs, 'utf8'))); } catch { return -1; }
  const sd = shardDirForBase(baseManifestAbs);
  let names;
  try { names = fs.readdirSync(sd); } catch { return total; }
  for (const n of names.sort()) {
    if (!n.endsWith('.json')) continue;
    try { total += manifestEntryCount(JSON.parse(fs.readFileSync(path.join(sd, n), 'utf8'))); } catch { return -1; }
  }
  return total;
}

/**
 * 분할 대상을 검증한다 — 대상은 항상 **베이스** 매니페스트다.
 * @returns {{abs:string, rel:string, manifest:object}}
 * @throws {CodeMapFatalError} 'split_target_invalid' | 'manifest_parse_failed' | 'unsupported_version'
 */
function resolveSplitTarget(manifestArg, ctx) {
  const codeMapRoot = path.join(ctx.projectRoot, ...CODE_MAP_DIR.split('/'));
  const abs = path.resolve(ctx.projectRoot, manifestArg);
  const bad = (detail) => { throw new CodeMapFatalError('split_target_invalid', detail); };

  if (abs !== codeMapRoot && !abs.startsWith(codeMapRoot + path.sep)) bad(`${manifestArg}은 ${CODE_MAP_DIR}/ 하위 경로가 아닙니다`);
  if (!abs.endsWith('.json')) bad(`${manifestArg}은 매니페스트(.json)가 아닙니다`);
  // 샤드의 샤드는 존재하지 않는다 — 재분할도 베이스에서 시작한다 (082 shard_undeclared 계약)
  if (isShardManifestPath(abs)) bad(`${manifestArg}은 샤드입니다 — 분할 대상은 언제나 베이스 매니페스트입니다`);
  if (!fs.existsSync(abs)) bad(`${manifestArg}이 존재하지 않습니다`);

  const manifest = loadManifest(abs, ctx);   // 파싱 실패는 기존 manifest_parse_failed로 흐른다
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) bad(`${manifestArg}이 매니페스트 객체가 아닙니다`);
  if (manifest.version !== CODE_MAP_VERSION) {
    throw new CodeMapFatalError('unsupported_version', `${manifestArg}: version=${manifest.version}`);
  }
  return { abs, rel: toPosixRel(ctx.projectRoot, abs), manifest };
}

/**
 * groups 문서를 검증·정규화한다 — 스키마 검증은 이 함수 1곳에만 존재한다 (U-1).
 * [MUST] 왕복 불변식(H-18): `groups[].label`·`groups[].files` 2필드만 읽는다. 그 외 키는
 * 최상위·그룹 내를 막론하고 존재를 허용하고 무시한다 — 검토 장치가 늘어도 왕복 계약은 확장되지 않는다.
 * @returns {{ok:true, groups:Array<{label,files:string[]}>} | {ok:false, detail:string}}
 */
function parseGroupsDoc(raw, targetRel, base) {
  let doc;
  try { doc = JSON.parse(raw); } catch { return { ok: false, detail: 'groups document is not valid JSON' }; }
  if (!doc || typeof doc !== 'object' || Array.isArray(doc)) return { ok: false, detail: 'groups document must be a JSON object' };
  if (!Array.isArray(doc.groups) || doc.groups.length === 0) return { ok: false, detail: 'groups must be a non-empty array' };

  if (hasOwn(doc, 'manifest') && doc.manifest !== null && doc.manifest !== undefined) {
    const docRel = String(doc.manifest).split(path.sep).join('/').replace(/^\.\//, '');
    if (docRel !== targetRel) return { ok: false, detail: `manifest mismatch: doc=${docRel} arg=${targetRel}` };
  }

  const baseFiles = (base && base.files) || {};
  const seenLabels = new Set();
  const seenKeys = new Set();
  const out = [];
  for (let i = 0; i < doc.groups.length; i++) {
    const g = doc.groups[i];
    if (!g || typeof g !== 'object' || Array.isArray(g)) return { ok: false, detail: `groups[${i}] must be an object` };
    if (typeof g.label !== 'string') return { ok: false, detail: `groups[${i}].label must be a string` };
    if (!Array.isArray(g.files) || g.files.length === 0) return { ok: false, detail: `groups[${i}].files must be a non-empty array` };
    if (!SHARD_LABEL_RE.test(g.label)) return { ok: false, detail: `invalid shard label "${g.label}"` };
    // 기존 샤드와 같은 라벨은 허용한다 — 그 샤드에 엔트리를 추가하는 정당한 조작이다. 문서 내 중복만 거부.
    if (seenLabels.has(g.label)) return { ok: false, detail: `duplicate label "${g.label}"` };
    seenLabels.add(g.label);

    const files = [];
    for (const f of g.files) {
      if (typeof f !== 'string') return { ok: false, detail: `groups[${i}].files must contain strings only` };
      if (!hasOwn(baseFiles, f)) return { ok: false, detail: `unknown entry key(s): ${f}` };
      if (seenKeys.has(f)) return { ok: false, detail: `entry assigned to multiple groups: ${f}` };
      seenKeys.add(f);
      files.push(f);
    }
    out.push({ label: g.label, files });
  }
  return { ok: true, groups: out };
}

/**
 * 쓰기 전에 최종 상태 전부를 메모리에서 만들고 불변식을 검증한다 (U-4 ①).
 * [MUST] `TASK.md` §제약 조건: "엔트리 유실 0건 — 실행 전후 엔트리 총합이 반드시 같아야 하며,
 * 실패 시 부분 상태를 남기지 않는다."
 * 키 순서는 mergeManifest와 동일하게 고정한다 — 다르면 scaffold가 no-op이 되지 않는다(F-3 AC).
 * @returns {{ok:true, writes, base, shards, before} | {ok:false, detail:string}}
 */
function composeSplitPlan(baseAbs, baseRel, base, groups, ctx) {
  const view = resolveShards(baseAbs, baseRel, base, ctx);
  const declared = new Map();
  for (const s of (view ? view.shards : [])) declared.set(s.label, s);

  let composedBefore = manifestEntryCount(base);
  for (const s of declared.values()) composedBefore += manifestEntryCount(s.manifest);

  const remainingBase = Object.assign({}, base.files || {});
  const shardDir = shardDirForBase(baseAbs);
  const shardLabels = (Array.isArray(base.shards) ? base.shards.slice() : []);   // 기존 선언 순서 불변
  const writes = [];
  const shardSummary = [];
  const allKeys = new Set();
  let composedAfter = 0;
  let duplicateKey = null;
  const takeKeys = (obj) => {
    for (const k of Object.keys(obj)) {
      if (allKeys.has(k)) { duplicateKey = duplicateKey || k; continue; }
      allKeys.add(k);
    }
  };

  for (const g of groups) {
    const s = declared.get(g.label) || null;
    const shardAbs = s ? s.manifestAbs : path.join(shardDir, g.label + '.json');
    const existing = s ? s.manifest : null;
    const files = Object.assign({}, (existing && existing.files) || {});
    for (const key of g.files) {
      files[key] = remainingBase[key];
      delete remainingBase[key];
    }
    const m = { version: CODE_MAP_VERSION, scope: base.scope, dir: base.dir };
    if (existing && hasOwn(existing, 'package')) m.package = existing.package;   // 3단 상속 입력 보존
    m.files = orderFilesObject(files);

    const content = JSON.stringify(m, null, 2) + '\n';
    const isNew = !fs.existsSync(shardAbs);
    writes.push({ abs: shardAbs, rel: toPosixRel(ctx.projectRoot, shardAbs), content, isNew });
    if (!shardLabels.includes(g.label)) shardLabels.push(g.label);   // 신규 라벨은 선언 순서 말미에
    composedAfter += Object.keys(m.files).length;
    takeKeys(m.files);
    shardSummary.push({
      label: g.label, manifest: toPosixRel(ctx.projectRoot, shardAbs),
      entries: Object.keys(m.files).length, bytes: Buffer.byteLength(content), created: isNew,
    });
  }

  // 이번 문서가 손대지 않은 기존 샤드도 총합에 산입한다 (무변경 — writes에 넣지 않는다)
  const touched = new Set(groups.map(g => g.label));
  for (const [label, s] of declared) {
    if (touched.has(label)) continue;
    composedAfter += manifestEntryCount(s.manifest);
    takeKeys((s.manifest && s.manifest.files) || {});
  }

  const nb = { version: CODE_MAP_VERSION, scope: base.scope, dir: base.dir };
  if (shardLabels.length > 0) nb.shards = shardLabels;
  if (hasOwn(base, 'package')) nb.package = base.package;
  nb.files = orderFilesObject(remainingBase);
  composedAfter += Object.keys(nb.files).length;
  takeKeys(nb.files);
  const baseContent = JSON.stringify(nb, null, 2) + '\n';
  writes.push({ abs: baseAbs, rel: baseRel, content: baseContent, isNew: false });

  if (duplicateKey) return { ok: false, detail: `entry key would exist in two manifests: ${duplicateKey}` };
  if (composedAfter !== composedBefore) {
    return { ok: false, detail: `entry total mismatch: ${composedBefore} → ${composedAfter}` };
  }
  return {
    ok: true, writes,
    base: { entries: Object.keys(nb.files).length, bytes: Buffer.byteLength(baseContent) },
    shards: shardSummary,
    before: { entries: composedBefore },
  };
}

/**
 * 2-phase commit + 롤백 (U-4 ②③). 실패 시 부분 상태를 남기지 않는다.
 * @param {Array<{abs, rel, content, isNew}>} writes
 * @returns {Array<{abs, prev:string|null}>} 사후 검증 실패 시 복원용 백업 (U-4 ④)
 * @throws {CodeMapFatalError} 'split_write_failed' | 'split_rollback'
 */
function commitSplit(writes) {
  const tmps = [];
  // Phase 1 — tmp 전량 작성. 여기서 실패하면 원본은 한 바이트도 변하지 않는다.
  try {
    for (const w of writes) {
      fs.mkdirSync(path.dirname(w.abs), { recursive: true });
      const tmp = w.abs + SPLIT_TMP_SUFFIX;
      fs.writeFileSync(tmp, w.content);
      tmps.push(tmp);
    }
  } catch (e) {
    for (const t of tmps) { try { fs.unlinkSync(t); } catch { /* best effort */ } }
    throw new CodeMapFatalError('split_write_failed', String(e && e.message));
  }
  // Phase 2 — 백업 확보 후 rename 커밋 (동일 디렉토리 rename은 POSIX 원자적)
  const backups = writes.map(w => ({ abs: w.abs, prev: w.isNew ? null : fs.readFileSync(w.abs, 'utf8') }));
  const done = new Set();
  try {
    for (const w of writes) { fs.renameSync(w.abs + SPLIT_TMP_SUFFIX, w.abs); done.add(w.abs); }
  } catch (e) {
    for (const b of backups) {
      if (!done.has(b.abs)) continue;
      try { if (b.prev === null) fs.unlinkSync(b.abs); else fs.writeFileSync(b.abs, b.prev); } catch { /* best effort */ }
    }
    for (const t of tmps) { try { if (fs.existsSync(t)) fs.unlinkSync(t); } catch { /* best effort */ } }
    throw new CodeMapFatalError('split_rollback', String(e && e.message));
  }
  return backups;
}

function restoreSplitBackups(backups) {
  for (const b of backups) {
    try { if (b.prev === null) fs.unlinkSync(b.abs); else fs.writeFileSync(b.abs, b.prev); }
    catch { /* best effort — 실패해도 사유는 이미 split_verify_failed로 보고된다 */ }
  }
}

// ── split 사람용 출력 (U-3: 다음 2단 명령을 그대로 싣는다) ─────────────────

function renderSplitPlanHuman(doc, opts) {
  const lines = [];
  lines.push(`split --plan: ${doc.manifest} (${doc.current.bytes} bytes, ${doc.current.entries} entries)`);
  lines.push(`  policy: maxBytes=${doc.policy.maxBytes} minFiles=${doc.policy.minFiles} targetBytes=${doc.policy.targetBytes} → 권고 ${doc.recommendedShards}조각`);
  if (doc.dict.found) lines.push(`  dict:   ${doc.dict.path} (${doc.dict.rows}행, ${doc.dict.source})`);
  else {
    lines.push('  dict:   사전 미발견 — S1~S3 건너뜀');
    lines.push(`          탐색: ${doc.dict.searched.join(' → ')}`);
  }
  lines.push(`  groups (${doc.groups.length}):`);
  for (const g of doc.groups) {
    lines.push(`    ${g.label.padEnd(14)}[${g.stage}] ${String(g.files.length).padStart(4)} entries  ~${g.estimatedBytes} bytes${g.oversizeGroup ? '  (목표 초과)' : ''}`);
  }
  lines.push(`  unassigned: ${doc.unassigned.length} entries — 라벨을 직접 지정하거나 베이스에 남깁니다`);
  if (opts.trace && Array.isArray(doc.trace)) {
    lines.push('  trace:');
    lines.push('    stage  dict  입력   걷음   그룹   잔여   비고');
    for (const t of doc.trace) {
      const cell = (v) => (t.skipped ? '-' : String(v));
      lines.push(`    ${t.stage.padEnd(6)} ${(t.dict ? 'yes' : 'no').padEnd(4)} ${cell(t.input).padStart(5)} ${cell(t.assigned).padStart(6)} ${cell(t.groups).padStart(6)} ${cell(t.remaining).padStart(6)}   ${t.reason ? (t.reason === 'dict_absent' ? 'skipped (사전 미발견)' : 'skipped (stopped)') : ''}`);
    }
  }
  lines.push(`  다음: code-scan split ${doc.manifest} --plan --out /tmp/groups.json`);
  lines.push(`        (파일을 편집한 뒤) code-scan split ${doc.manifest} --groups /tmp/groups.json --dry-run`);
  console.log(lines.join('\n'));
}

function cmdSplit(projectRoot, config, opts, mode) {
  const isJson = opts.output === 'json';
  const hasPlan = !!opts.plan;
  const hasGroups = opts.groups !== null && opts.groups !== undefined;
  const usageFix = 'Usage: code-scan split <manifest-path> --plan [--out <path>] [--trace] [--stop-after <S1..S5>]' +
                   ' | code-scan split <manifest-path> --groups <path|-> [--dry-run]';

  // ① CLI 계약 — 모호한 기본 동작을 만들지 않는다
  if (hasPlan && hasGroups) return errorExit('split_usage_invalid', { detail: '--plan and --groups are mutually exclusive', fix: usageFix });
  if (!hasPlan && !hasGroups) return errorExit('split_usage_invalid', { detail: 'one of --plan or --groups is required', fix: usageFix });
  if (!opts.commandArg) return errorExit('split_usage_invalid', { detail: 'manifest path argument is required', fix: usageFix });
  if (opts.stopAfter !== null && opts.stopAfter !== undefined) {
    const norm = String(opts.stopAfter).toUpperCase();
    if (!SHARD_PLAN_STAGE_IDS.includes(norm)) {
      return errorExit('split_usage_invalid', {
        detail: `unknown ladder stage "${opts.stopAfter}"`,
        fix: `--stop-after 값은 ${SHARD_PLAN_STAGE_IDS.join(' | ')} 중 하나여야 합니다`,
      });
    }
    opts.stopAfter = norm;
  }

  // ② 모드 게이트 — inline에는 매니페스트가 없어 대상이 존재하지 않는다. "성공적으로 아무것도
  //    안 함"은 거짓 신호다(H-14). scaffold와 달리 split은 소유자가 특정 파일을 지목한 명령이다.
  if (mode !== 'manifest') {
    return errorExit('split_inline_mode', {
      detail: `headerSource=${mode}`,
      fix: 'split은 매니페스트 자산을 분할하는 명령입니다 — headerSource가 manifest인 프로젝트에서 실행하세요',
      doc: HEADER_SOURCE_DOC,
    });
  }

  const ctx = buildCtx(projectRoot, config, mode);
  const target = resolveSplitTarget(opts.commandArg, ctx);
  const policy = resolveShardPolicy(ctx);

  if (hasPlan) {
    // [MUST] 사전 로딩은 이 경로 1곳뿐이다 — 조회 8커맨드에 새 I/O를 만들지 않는다 (H-13/H-17)
    const dict = loadWordDictionary(ctx, policy);
    const base = target.manifest;
    const baseEntries = new Map(Object.entries(base.files || {}));
    const usedLabels = new Set(Array.isArray(base.shards) ? base.shards.filter(l => typeof l === 'string') : []);
    const shardOverheadBytes = Buffer.byteLength(
      JSON.stringify({ version: CODE_MAP_VERSION, scope: base.scope, dir: base.dir, files: {} }, null, 2) + '\n');
    const planned = planShardGroups(
      baseEntries, usedLabels, policy,
      (dict.found && dict.rows) ? dict : null,
      { stopAfter: opts.stopAfter, shardOverheadBytes });

    const bytes = fs.statSync(target.abs).size;
    const doc = {
      ok: true, command: 'split', mode: 'plan',
      manifest: target.rel,
      policy: { maxBytes: policy.maxBytes, minFiles: policy.minFiles, targetBytes: policy.targetBytes },
      current: { bytes, entries: manifestEntryCount(base) },
      recommendedShards: recommendedShardCount(bytes, policy),
      // 사전 미발견을 침묵하지 않는다 — 탐색 경로가 항상 출력에 실린다 (H-16)
      dict: {
        found: dict.found, path: dict.path, source: dict.source,
        rows: dict.rows ? dict.rows.length : 0, searched: dict.searched,
      },
      ladder: planned.ladder,
      groups: planned.groups,
      unassigned: planned.unassigned,
      assignments: planned.assignments,
      coverage: planned.coverage,
    };
    if (opts.trace) doc.trace = planned.trace;

    // 쓰기 경계 — --plan은 매니페스트를 쓰지 않는다. --out이 있으면 groups 문서 1개만 쓴다.
    if (opts.out) {
      const outAbs = path.resolve(projectRoot, opts.out);
      fs.mkdirSync(path.dirname(outAbs), { recursive: true });
      fs.writeFileSync(outAbs, JSON.stringify(doc, null, 2) + '\n');
    }
    if (isJson) console.log(JSON.stringify(doc));
    else renderSplitPlanHuman(doc, opts);
    return;
  }

  // ── 집행 모드 ──────────────────────────────────────────────────────────
  let raw;
  if (opts.groups === '-') {
    try { raw = fs.readFileSync(0, 'utf8'); }
    catch (e) { return errorExit('split_groups_invalid', { detail: `stdin을 읽을 수 없습니다: ${e && e.message}` }); }
  } else {
    const p = path.resolve(projectRoot, opts.groups);
    try { raw = fs.readFileSync(p, 'utf8'); }
    catch { return errorExit('split_groups_invalid', { detail: `${opts.groups}을 읽을 수 없습니다` }); }
  }

  const groupsFix = 'groups 문서는 {"manifest": "<대상 경로>", "groups": [{"label": "<kebab>", "files": ["<엔트리 키>"]}]} 형식이어야 합니다 ' +
                    `(code-scan split ${target.rel} --plan --out <path> 로 초안을 만드세요)`;
  const parsed = parseGroupsDoc(raw, target.rel, target.manifest);
  if (!parsed.ok) return errorExit('split_groups_invalid', { detail: parsed.detail, fix: groupsFix });

  const beforeEntries = diskTotalEntries(target.abs);
  const beforeBytes = fs.statSync(target.abs).size;
  const composed = composeSplitPlan(target.abs, target.rel, target.manifest, parsed.groups, ctx);
  if (!composed.ok) return errorExit('split_groups_invalid', { detail: composed.detail, fix: groupsFix });

  const result = {
    ok: true, command: 'split', mode: 'apply', dryRun: !!opts.dryRun,
    manifest: target.rel,
    moved: parsed.groups.reduce((n, g) => n + g.files.length, 0),
    base: composed.base,
    shards: composed.shards,
    before: { entries: beforeEntries, bytes: beforeBytes },
    after: { totalEntries: beforeEntries },
  };

  const emit = () => {
    if (isJson) console.log(JSON.stringify(result));
    else {
      console.log(`split${result.dryRun ? ' --dry-run' : ''}: ${result.manifest} — moved=${result.moved} ` +
                  `base=${result.base.entries} shards=${result.shards.length} ` +
                  `entries ${result.before.entries} → ${result.after.totalEntries}`);
    }
  };

  if (opts.dryRun) { emit(); return; }

  const backups = commitSplit(composed.writes);

  // 사후 재검증 (U-4 ④) — 캐시를 비우고 **같은 resolveShards로** 다시 읽는다.
  // 해석 로직을 복제하지 않는다 (082 봉인 제약).
  ctx.codeMap.manifests.clear();
  if (ctx.codeMap.shardViews) ctx.codeMap.shardViews.clear();
  let afterEntries = -1;
  let duplicates = 0;
  try {
    const after = loadManifest(target.abs, ctx);
    const view = resolveShards(target.abs, target.rel, after, ctx);
    duplicates = view ? view.duplicates.length : 0;
    afterEntries = diskTotalEntries(target.abs);
  } catch { afterEntries = -1; }

  if (afterEntries !== beforeEntries || duplicates > 0) {
    restoreSplitBackups(backups);
    return errorExit('split_verify_failed', {
      detail: `entries ${beforeEntries} → ${afterEntries}${duplicates > 0 ? `, duplicates=${duplicates}` : ''}`,
      fix: '자산은 실행 전 상태로 복원했습니다 — code-scan validate 로 현재 상태를 확인한 뒤 groups 문서를 조정하세요',
    });
  }

  result.after = { totalEntries: afterEntries };
  process.stderr.write('code-scan: split 완료 — code-scan validate 로 확인하세요\n');
  emit();
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
    const mctx  = ctx.codeMap.present ? resolveManifestContext(relPath, ctx) : null;
    const owned = (mctx && mctx.shardView) ? mctx.shardView.byKey.get(basename) : null;
    const fe = owned ? owned.entry
                     : ((mctx && mctx.manifest && mctx.manifest.files && mctx.manifest.files[basename]) || null);
    // 위반의 manifest 필드가 "고치러 갈 파일"을 가리키게 한다 (082 F-003, PLAN §3.3.2 (A))
    const ownerRel = owned ? owned.manifestRel : (mctx ? mctx.manifestRel : undefined);

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
      violations.push({ code: 'conflict', sub: 'inline_shadowed', file: relPath, manifest: ownerRel, key: basename, detail: '' });
    }

    // draft는 매니페스트 전용 개념이므로 inline 모드에서는 적용하지 않는다 (080 §3.3.2 (D)).
    if (!isInlineMode && inlineHeader === null && fe !== null) {
      const blank = typeof fe.description === 'string' && fe.description.trim() === '';
      if (fe.draft === true || blank) {
        violations.push({ code: 'draft', file: relPath, manifest: ownerRel, key: basename, detail: '' });
      }
    }

    if (resolved && Array.isArray(resolved.exports) && resolved.exports.length > 0) {
      let text = null;
      for (const idRaw of resolved.exports) {
        const id = normalizeExportId(idRaw);
        if (!id) continue;
        if (text === null) { try { text = fs.readFileSync(fileAbs, 'utf8'); } catch { text = ''; } }
        if (!text.includes(id)) {
          violations.push({ code: 'exports_not_found', file: relPath, manifest: ownerRel, key: basename, detail: idRaw });
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
  // 매니페스트 엔트리(package/files)의 layer·domain·module 침범 검사 — 베이스·샤드 공통 (082 F-003 §3.3.2 (C) 검사 11)
  function checkEntryViolations(manifest, manifestRel) {
    const manifestFiles = manifest.files || {};
    const pkg = manifest.package || null;
    if (pkg && hasOwn(pkg, 'layer')) {
      violations.push({ code: 'worker_scope_violation', sub: 'layer_in_manifest', manifest: manifestRel, detail: '' });
    }
    if (pkg && hasOwn(pkg, 'domain')) {
      violations.push({ code: 'worker_scope_violation', sub: 'domain_in_manifest', manifest: manifestRel, detail: '' });
    }
    for (const [key, entryFe] of Object.entries(manifestFiles)) {
      if (entryFe && hasOwn(entryFe, 'layer')) {
        violations.push({ code: 'worker_scope_violation', sub: 'layer_in_manifest', manifest: manifestRel, key, detail: '' });
      }
      if (entryFe && hasOwn(entryFe, 'domain')) {
        violations.push({ code: 'worker_scope_violation', sub: 'domain_in_manifest', manifest: manifestRel, key, detail: '' });
      }
      if (entryFe && hasOwn(entryFe, 'module')) {
        const stem = deriveStem(key);
        if (entryFe.module !== stem) {
          violations.push({ code: 'worker_scope_violation', sub: 'module_override', manifest: manifestRel, key, detail: String(entryFe.module) });
        }
      }
    }
  }

  // 크기 상한 열거 — 비차단 (082 F-005 유지). 2축 판정 + 유도 페이로드 (083 F-003).
  // 베이스·샤드 양쪽에서 호출된다 (082 S-25).
  function checkOversize(manifestAbs, manifestRel, manifest) {
    const size = fs.statSync(manifestAbs).size;
    const policy = resolveShardPolicy(ctx);
    const entries = manifestEntryCount(manifest);
    if (!isOversizeManifest(size, entries, policy)) return;
    violations.push({
      code: 'manifest_oversize',
      manifest: manifestRel,
      detail: `${size}/${policy.maxBytes}`,          // [MUST] 포맷 불변 — 082 S-15가 정확 단언
      entries,
      minFiles: policy.minFiles,
      recommendedShards: recommendedShardCount(size, policy),
      next: `code-scan split ${manifestRel} --plan`,
    });
  }

  if (!isInlineMode && ctx.codeMap.present) {
    const index = ctx.codeMap.index;
    const scopeNames = opts.scope ? [opts.scope] : Object.keys(index.scopes || {});
    for (const scopeName of scopeNames) {
      const scopeObj = index.scopes[scopeName];
      if (!scopeObj) continue;
      const scopeMapDir = path.join(projectRoot, CODE_MAP_DIR, scopeName);
      if (!fs.existsSync(scopeMapDir)) continue;

      // Phase A — 분류 (082 F-003 §3.3.2 (B))
      const allManifests = listManifestFiles(scopeMapDir);
      const bases = allManifests.filter(p => !isShardManifestPath(p));
      const shardPaths = allManifests.filter(p => isShardManifestPath(p));
      const visitedShards = new Set();

      const structExcludeDirs = [...(config.exclude || []), ...((index && index.exclude) || [])];
      const structExcludePatterns = mergeExcludePatterns(config, opts);

      // Phase B — 베이스 그룹 단위 검사 (082 F-003 §3.3.2 (C))
      for (const manifestAbs of bases) {
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
          } else if (expected.split('/').includes(SHARDS_DIR)) {
            // 3b: 실제 미러 경로에 _shards 세그먼트 포함 — 소스 디렉토리 예약어 충돌 (082 F-006)
            violations.push({ code: 'worker_scope_violation', sub: 'reserved_name', manifest: manifestRel, detail: String(manifest.dir) });
          }
        }

        const dirAbs = path.resolve(projectRoot, manifest.dir || '');
        const dirExists = fs.existsSync(dirAbs) && fs.statSync(dirAbs).isDirectory();
        if (!dirExists) {
          // 베이스에서 1회만 — 샤드마다 반복하면 1건이 1+N건으로 부푼다 (082 §9 R-2, S-9)
          violations.push({ code: 'orphan', sub: 'dir_missing', manifest: manifestRel, file: manifest.dir, detail: '' });
        }

        checkOversize(manifestAbs, manifestRel, manifest);

        const view = resolveShards(manifestAbs, manifestRel, manifest, ctx);

        for (const s of (view ? view.shards : [])) {
          visitedShards.add(s.manifestAbs);
          if (!s.manifest) {
            violations.push({ code: 'orphan', sub: 'shard_missing', manifest: manifestRel, detail: s.label });
            continue;
          }
          if (typeof s.manifest.version !== 'number' || s.manifest.version !== CODE_MAP_VERSION) {
            throw new CodeMapFatalError('unsupported_version');
          }
          if (s.manifest.scope !== scopeName) {
            violations.push({ code: 'worker_scope_violation', sub: 'scope_mismatch', manifest: s.manifestRel, detail: String(s.manifest.scope) });
          }
          if (s.manifest.dir !== manifest.dir) {
            // 기존 dir_mismatch를 재사용하지 않는다 — 그 판정은 미러 경로를 역산하는데 샤드는
            // 미러 경로가 베이스이므로 항상 위반이 된다 (082 §9 H-1, S-8/S-15)
            violations.push({ code: 'worker_scope_violation', sub: 'shard_dir_mismatch', manifest: s.manifestRel, detail: String(s.manifest.dir) });
          }
          checkOversize(s.manifestAbs, s.manifestRel, s.manifest);
        }

        for (const dup of (view ? view.duplicates : [])) {
          violations.push({
            code: 'worker_scope_violation', sub: 'shard_duplicate_key',
            manifest: dup.winner, key: dup.key, detail: `${dup.winner} → ${dup.losers.join(',')}`,
          });
        }

        // (D) 합집합 ↔ 디스크 대조 — 그룹당 1회 (082 §9 R-2, H-1 해소)
        const diskBasenames = dirExists
          ? listCodeFilesInDir(dirAbs, manifest.dir || '', config, structExcludeDirs, structExcludePatterns, scopeObj)
          : [];
        const diskSet = new Set(diskBasenames);
        const unionKeys = view ? view.byKey
          : new Map(Object.keys(manifest.files || {}).map(k => [k, { manifestRel, entry: manifest.files[k] }]));

        for (const [key, o] of unionKeys) {
          if (!diskSet.has(key)) {
            violations.push({ code: 'orphan', sub: 'file_missing', manifest: o.manifestRel, key, file: `${manifest.dir}/${key}`, detail: '' });
            violations.push({ code: 'worker_scope_violation', sub: 'files_key_added', manifest: o.manifestRel, key, detail: '' });
          }
        }
        for (const bn of diskBasenames) {
          if (!unionKeys.has(bn)) {
            // 미보유 파일의 라우팅 대상은 베이스다 (U-3) → 베이스에 귀속
            violations.push({ code: 'worker_scope_violation', sub: 'files_key_removed', manifest: manifestRel, key: bn, detail: '' });
          }
        }

        // 침범 검사 — 베이스 + 각 샤드에 반복 적용
        checkEntryViolations(manifest, manifestRel);
        for (const s of (view ? view.shards : [])) {
          if (s.manifest) checkEntryViolations(s.manifest, s.manifestRel);
        }
      }

      // Phase C — 미방문 샤드 스윕 (082 F-003 §3.3.2 (E))
      // 베이스 부재 / shards 미선언 / 라벨 누락 / 중첩 _shards 4상황을 이 1개 규칙이 전부 덮는다.
      for (const shardAbs of shardPaths) {
        if (visitedShards.has(shardAbs)) continue;
        violations.push({
          code: 'worker_scope_violation', sub: 'shard_undeclared',
          manifest: toPosixRel(projectRoot, shardAbs),
          detail: toPosixRel(projectRoot, baseManifestAbsForShard(shardAbs)),
        });
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
    manifest_oversize: violations.filter(v => v.code === 'manifest_oversize').length,
  };
  const covered = inlineCount + manifestCount;
  const percent = totalCount === 0 ? 100 : Math.round((covered / totalCount) * 1000) / 10;
  // 'uncovered:pre_existing'과 'manifest_oversize'는 비차단(U-2) — 나머지는 차단 불변.
  const blockingViolations = violations.filter(v =>
    !(v.code === 'uncovered' && v.sub === 'pre_existing') &&
    v.code !== 'manifest_oversize');
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

  // ── init 게이트 예외 (083 F-012) ───────────────────────────────────────
  // [MUST] init은 headerSource가 **없는 상태를 고치는** 명령이다. 아래 전 명령 차단 게이트
  // 뒤에 두면 "설정이 없어서 init이 거부되고, init을 못 돌려 설정을 못 만드는" 순환이 생겨
  // 기능이 통째로 무용지물이 된다. 게이트를 무력화하는 것이 아니라, **게이트가 요구하는 값을
  // CLI 인자로 직접 받는다** — 나머지 명령의 차단 동작은 조금도 완화되지 않는다.
  if (opts.command === 'init') { return cmdInit(projectRoot, config, opts); }
  // ──────────────────────────────────────────────────────────────────────

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

  // ── config 스키마 게이트 (080 scopes + 083 shardPolicy) ────────────────
  // loadConfig는 종료하지 않으므로(hook fail-safe) 여기서 exit 1로 표면화한다.
  // 신규 에러 코드를 만들지 않고 기존 code_scan_config_invalid 창구에 합류한다.
  if (config.configError === 'config_scope_invalid' || config.configError === 'shard_policy_invalid') {
    return errorExit('code_scan_config_invalid', {
      detail: config.configErrorDetail,
      where: 'config',
      fix: (config.configError === 'shard_policy_invalid'
        ? '.opal/code-scan.json의 shardPolicy는 {"maxBytes": <양의 정수>, "minFiles": <양의 정수>} 형식이어야 합니다'
        : '.opal/code-scan.json의 scopes 항목은 문자열 또는 {path, include, exclude} 형식이어야 합니다 ' +
          '(include/exclude는 문자열 배열)') + INIT_RECOVERY_FIX,
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
    init:     cmdInit,      // 실제 진입은 위 게이트 예외 분기 — 여기 등재는 명령 목록의 SSOT 유지용
    discover: cmdDiscover,
    scaffold: cmdScaffold,
    target:   cmdTarget,
    validate: cmdValidate,
    split:    cmdSplit,
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
// v1.5.0 — 2026-08-03 13:20 (082) — 매니페스트 샤딩 도입: 베이스 매니페스트가 shards 배열로 예약
//                       폴더 _shards/ 하위 샤드를 선언하면 resolveShards 1곳이 로딩·byKey 합집합(첫
//                       승리)·중복 판정을 봉인하고, 미선언 자산은 null을 돌려받아 전 경로가 오늘과
//                       바이트 동일하게 동작한다(하위호환). decideTarget은 보유 샤드로 라우팅하고
//                       (reason 3값 도메인 불변, 신규 선택 필드 shard만 추가), validate는 베이스+샤드
//                       합집합 기준 구조 패스로 재구성되어 orphan:shard_missing·worker_scope_violation:
//                       shard_dir_mismatch|shard_duplicate_key|reserved_name 서브를 신설했으며,
//                       scaffold는 샤드 보존·버킷 분배·예약어 충돌(reserved_name_collision, exit 1)을
//                       집행한다. index.json 최상위 manifestMaxBytes(기본 20480바이트)로 매니페스트
//                       바이트 상한을 감지하며 전면 비차단(counts.manifest_oversize 열거)이다.
//                       CODE_MAP_VERSION은 1로 고정 유지 (082)
// v1.6.0 — 2026-08-04 (083) — 샤드 정책 2축화 + split 서브명령 신설. 분할 판정이 "바이트 초과 AND
//                       엔트리 수 이상"의 2축이 되고, resolveShardPolicy 1곳이 프로젝트 code-scan.json
//                       shardPolicy > 전역 ~/.opal/setting.json > 코드 상수(maxBytes 10240 / minFiles 40)
//                       3단을 셀 단위로 병합해 실행당 1회 확정한다(전역 설정 부재·파손·타입 위반은
//                       전부 비차단 폴백). 구 위치 index.json manifestMaxBytes는 폐기되어 값을 읽지
//                       않고 deprecationOnce 안내만 한다(자동 변환 없음). manifest_oversize 위반에
//                       entries·minFiles·recommendedShards·next 4필드가 추가되고 scaffold 경고에도
//                       다음 명령이 병기되나 detail의 {bytes}/{maxBytes} 포맷은 불변이다. split은
//                       --plan(제안)과 --groups(집행) 2모드로, 제안은 5단 사다리(S1 첫토큰·S2 첫2토큰·
//                       S3 임의토큰 = 표준단어사전 대조 / S4 마지막토큰·S5 depends 빈도)를 잔여만
//                       흘려보내며 돌리고 --trace·--stop-after·stage 3종 검토 장치와 함께 결정론적
//                       groups 문서를 낸다(무쓰기, --out 사용 시 문서 1개만). 표준단어사전은 옵셔널로
//                       shardPolicy.dictPath > docs/PROJECT.md {설계} 변수 > 기본 2후보 순으로 탐색하며
//                       부재는 침묵·파손은 noticeOnce 1줄이고 사전 없으면 S1~S3을 건너뛴다. 집행은
//                       사전 불변식 검증 → *.tmp-split 전량 작성 → renameSync 커밋 → 캐시를 비우고
//                       resolveShards로 재검증하는 4단이며, 총합 불일치·중복 발생 시 백업으로 원복해
//                       엔트리 유실 0건을 보증한다(신규 에러 코드 7종). init 서브명령이 headerSource
//                       미설정 순환을 끊는 비대화형 설정 초안 창구로 추가됐고, discover 전용이던
//                       opts.discoverOut은 opts.out으로 개명되어 split --plan과 공유한다 (083)
