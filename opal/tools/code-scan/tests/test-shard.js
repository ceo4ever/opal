/**
 * @header {
 *   "module": "test-shard",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — code-scan 매니페스트 샤딩(_shards/ 의미 단위 분산 + manifestMaxBytes 파일당 크기 상한) 계약 CLI 블랙박스 테스트. 샤드 합집합 해석·package 3단 상속·라벨 경로 안전·CODE_MAP_VERSION 불변·target 라우팅·validate 위반 4종·오탐 증폭 차단·scaffold 보존/멱등/중복가드/stale·크기 상한 열거+비차단·예약어 가드·하위호환 회귀·다중 스코프 격리·목표달성(분산 후 크기 하강+조회 무손실)을 검증한다 (F-1~F-8, 태스크 082)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "082",
 *   "scenarios": ["S-1","S-2","S-3","S-4","S-5","S-6","S-7","S-8","S-9","S-10","S-11","S-12","S-13","S-14","S-15","S-16","S-17","S-18","S-19","S-20","S-21","S-22","S-23","S-25","S-26"]
 * }
 */
//
// [RED-first — 작성자≠구현자]
// 본 파일은 opal-test-agent(mode:red)가 구현 전에 작성한다. 현행 code-scan.js v1.4.0에는 샤드
// 개념(`shards` 키·`_shards/` 예약 폴더·`resolveShards`·`manifestMaxBytes`)이 전혀 없으므로
// 아래 전 케이스는 실패(RED)해야 정상이다. 구현(GREEN)은 op-dev-execute(opal-task-agent)가
// PLAN.md §4.2 Step 4~9에서 수행한다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다 — 실패 이유가 "미구현"이어야 하며
// "테스트 자체 오류"여서는 안 된다.
//
// TC ↔ S-ID 매핑 표 (TEST-SCENARIO.md §3, §4 AC 매핑):
//
// | 케이스 프리픽스        | S-ID | 계층 | 대상                                              |
// |-------------------------|------|------|---------------------------------------------------|
// | [T082/L1-F1] 합집합      | S-1  | L1   | resolveShards 합집합 해석 — uncovered 0            |
// | [T082/L1-F1] package     | S-2  | L1   | package 3단 상속 + _sources 토큰 불변              |
// | [T082/L1-F1] 악성 라벨   | S-3  | L1   | SHARD_LABEL_RE — path traversal 차단               |
// | [T082/L1-F1] VERSION     | S-4  | L1   | CODE_MAP_VERSION===1 불변                          |
// | [T082/L1-F2] target      | S-5  | L1   | decideTarget 샤드 라우팅 2단                       |
// | [T082/L2-F2] hook        | S-6  | L2   | code-map-hook.js 자동 정합 + fail-safe              |
// | [T082/L2-F3] 무위반      | S-7  | L2   | 정상 구성 위반 0건 (full + --changed)              |
// | [T082/L1-F3] 위반 4종    | S-8  | L1   | shard_duplicate_key/shard_missing/undeclared/dir_mismatch |
// | [T082/L1-F3] dir_missing | S-9  | L1   | orphan:dir_missing 1건 (오탐 증폭 차단)            |
// | [T082/L1-F3] 침범 귀속   | S-10 | L1   | layer_in_manifest → 샤드 경로 귀속                  |
// | [T082/L2-F4] stale       | S-11 | L2   | scaffold stale 0건                                  |
// | [T082/L2-F4] 멱등        | S-12 | L2   | scaffold 2회 바이트 동일                            |
// | [T082/L2-F4] 신규삭제    | S-13 | L2   | 신규→베이스 added / 삭제→샤드 pruned                |
// | [T082/L2-F4] 중복 skip   | S-14 | L2   | 중복 키 디렉토리 skip + 샤드 무쓰기                 |
// | [T082/L1-F5] oversize    | S-15 | L1   | manifest_oversize 열거 + exit 0(비차단)             |
// | [T082/L1-F5] maxBytes    | S-16 | L1   | manifestMaxBytes 오버라이드 + 경계값                |
// | [T082/L1-F5] scaffold경고| S-17 | L1   | stderr 1줄 + stdout 무변경                          |
// | [T082/L1-F5] 샤드oversize| S-25 | L1   | 샤드 자신도 상한 측정 (게이트 G-1)                  |
// | [T082/L2-F6] 예약어      | S-18 | L2   | reserved_name_collision / reserved_name             |
// | [T082/L2-F7] 바이트 동일 | S-19 | L2   | 골든 8커맨드 + target/scaffold stdout 바이트 동일   |
// | [T082/L2-F7] inline 양축 | S-20 | L2   | inline 모드 stdout·stderr 무영향                    |
// | [T082/L1-F1] 봉인 grep   | S-21 | L1   | resolveShards 봉인 1곳 (정적 검사)                  |
// | [T082/L1-F8] 산출물      | S-22 | L1   | version/변경이력/문서 반영 (RED 정상 — 미구현)      |
// | [T082/L2-GOAL] 목표달성  | S-23 | L2   | 분산 6항 동시 충족                                  |
// | [T082/L2-F3] 다중 스코프 | S-26 | L2   | visitedShards/shardViews 스코프 격리                |
// | (S-24는 L3 [SUPERVISOR] — 본 파일에 작성하지 않는다. TEST-SCENARIO.md §3 S-24 참조, 수동 검증 대상) |
//
// 변경이력:
//   v1.0 2026-08-03 KST: RED-first 최초 작성 — S-1~S-23, S-25, S-26 전량 (S-24는 L3 수동, 미작성)
//     (Task 082, opal-test-agent mode:red)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
const HOOK_JS = path.resolve(__dirname, '..', 'code-map-hook.js');
const SRC = fs.readFileSync(CODE_SCAN_JS, 'utf8');
const FIX = path.resolve(__dirname, 'fixtures');

// ── 공통 헬퍼 (tests/test-validate.js:56-80 패턴 재사용) ────────────────────

function run(cwd, args, input) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 10000, input,
  });
  const stdout = result.stdout || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr: result.stderr || '', json };
}

function runHook(cwd, stdinPayload) {
  const result = spawnSync(process.execPath, [HOOK_JS], {
    cwd,
    input: typeof stdinPayload === 'string' ? stdinPayload : JSON.stringify(stdinPayload),
    encoding: 'utf8', timeout: 10000,
  });
  return { exitCode: result.status, stdout: result.stdout || '', stderr: result.stderr || '' };
}

function editEvent(absPath) {
  return { tool_name: 'Edit', tool_input: { file_path: absPath } };
}

function copyDirRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDirRecursive(s, d);
    else fs.copyFileSync(s, d);
  }
}

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

/** 커밋 픽스처(`tests/fixtures/<fixtureRel>`)를 임시 복사본으로 복제한다 — 픽스처 자산은 절대 수정하지 않는다. */
function copyFixture(fixtureRel, tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t082-${tag}-`));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureRel), dir);
  return dir;
}

function readJSON(absPath) { return JSON.parse(fs.readFileSync(absPath, 'utf8')); }
function writeJSON(absPath, obj) { fs.writeFileSync(absPath, JSON.stringify(obj, null, 2) + '\n'); }

/** dir 전체를 재귀 열거한 상대경로 목록(POSIX, 정렬됨). */
function listAllFiles(dir) {
  const out = [];
  function walk(d, prefix) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      if (e.isDirectory()) walk(full, rel);
      else out.push(rel);
    }
  }
  walk(dir, '');
  return out.sort();
}

/** `.opal/code-map/` 하위 전 파일의 {상대경로 → {content, mtimeMs}} 스냅샷 (tests/test-scaffold.js:111-125 패턴 재사용). */
function snapshotCodeMap(dir) {
  const mapDir = path.join(dir, '.opal', 'code-map');
  const snap = {};
  const walk = (d, prefix) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(d, e.name);
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      if (e.isDirectory()) walk(full, rel);
      else snap[rel] = { content: fs.readFileSync(full, 'utf8'), mtimeMs: fs.statSync(full).mtimeMs };
    }
  };
  if (fs.existsSync(mapDir)) walk(mapDir, '');
  return snap;
}

/** camelCase/PascalCase 스템 → kebab-case 라벨 (SHARD_LABEL_RE `/^[a-z0-9]+(?:-[a-z0-9]+)*$/` 호환). */
function toKebabLabel(stem) {
  return stem.replace(/(?!^)([A-Z])/g, '-$1').toLowerCase();
}

/**
 * `shard-goal/before`(상한 초과 베이스 1개, 6엔트리)에서 **스크립트로** 분산 후 트리를 파생한다
 * (게이트 gaps G-3 — 수작성 2벌 금지: ②의 동일성 단언이 도구가 아니라 픽스처 작성자를 시험하는
 * 것을 막기 위해, 분산 후 트리를 손으로 따로 만들지 않고 `before`에서 프로그램적으로 만든다).
 * 각 소스 파일을 **개별 샤드 1개**로 분리한다(라벨 = kebab(stem)) — manifestMaxBytes:400 아래에서
 * 2파일 묶음(예: pricing 2파일 402바이트)은 여전히 상한을 넘기므로, 상한을 실제로 만족시키는
 * 가장 단순한 분산은 파일당 샤드다. 베이스는 `shards` 선언만 남기고 `files`는 빈 객체가 된다.
 * @returns {{dir: string, labels: string[], base: object}}
 */
function deriveAfterTree(tag) {
  const dir = copyFixture(path.join('shard-goal', 'before'), tag);
  const baseManifestAbs = path.join(dir, '.opal', 'code-map', 'svc', 'mod.json');
  const base = readJSON(baseManifestAbs);
  const shardsDirAbs = path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards');
  fs.mkdirSync(shardsDirAbs, { recursive: true });

  const labels = [];
  for (const key of Object.keys(base.files)) {
    const stem = key.replace(/\.ts$/, '');
    const label = toKebabLabel(stem);
    labels.push(label);
    const shardManifest = {
      version: base.version, scope: base.scope, dir: base.dir,
      files: { [key]: base.files[key] },
    };
    writeJSON(path.join(shardsDirAbs, `${label}.json`), shardManifest);
  }

  const newBase = { version: base.version, scope: base.scope, dir: base.dir, shards: labels, files: {} };
  writeJSON(baseManifestAbs, newBase);

  return { dir, labels, base: newBase };
}

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-1: 샤드 합집합 해석 (H-1)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F1] S-1: scan --json — shard-repo 소스 4파일 전부의 헤더가 해석되고 exports가 정확하다', () => {
  const dir = copyFixture('shard-repo', 's1');
  const { exitCode, json, stdout } = run(dir, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);

  const expected = {
    'svc/mod/A.ts': ['A'],
    'svc/mod/B.ts': ['B'],
    'svc/mod/C.ts': ['C'],
    'svc/mod/D.ts': ['D'],
  };
  for (const [p, exportsExpected] of Object.entries(expected)) {
    assert.ok(json && Object.prototype.hasOwnProperty.call(json, p),
      `[RED expect] ${p}가 scan --json 결과에 존재해야 함(uncovered로 빠지면 안 됨), keys=${JSON.stringify(json && Object.keys(json))}`);
    assert.deepStrictEqual(json[p] && json[p].exports, exportsExpected,
      `[RED expect] ${p}.exports === ${JSON.stringify(exportsExpected)}, got ${JSON.stringify(json[p])}`);
  }
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-2: package 3단 상속 + 출처 토큰 불변 (H-4)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F1] S-2: package 3단 상속 — 샤드 package 우선, 베이스 package 대체, _sources 새 토큰 없음', () => {
  // 082 Step 9d: S-2(package 상속)와 S-7(위반 0건)이 한 픽스처에서 양립 불가 → 전용 픽스처 분리 (캡틴 승인)
  const dir = copyFixture('shard-package', 's2');
  const { exitCode, json, stdout } = run(dir, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);

  const a = json && json['svc/mod/A.ts'];
  assert.ok(a, `[RED expect] svc/mod/A.ts 헤더가 존재해야 함, keys=${JSON.stringify(json && Object.keys(json))}`);
  assert.strictEqual(a.description, 'core 샤드 패키지 설명 (package 3단 상속 검증용)',
    `[RED expect] description은 core 샤드 package에서 상속되어야 함, got ${JSON.stringify(a)}`);
  assert.strictEqual(a._sources && a._sources.description, 'package',
    `[RED expect] _sources.description === 'package'(새 토큰 없음), got ${JSON.stringify(a._sources)}`);
  assert.deepStrictEqual(a.depends, ['shared-utils'],
    `[RED expect] depends는 베이스 package에서 상속되어야 함(core 샤드엔 depends 없음), got ${JSON.stringify(a)}`);
  assert.strictEqual(a._sources && a._sources.depends, 'package',
    `[RED expect] _sources.depends === 'package'(두 티어 모두 동일 토큰), got ${JSON.stringify(a._sources)}`);

  // 출처 토큰 도메인 불변 — 'file'|'package'|'rule'|'domain' 4값 밖으로 새지 않는다
  const CLOSED = new Set(['file', 'package', 'rule', 'domain']);
  for (const v of Object.values(a._sources || {})) {
    assert.ok(CLOSED.has(v), `_sources 값이 폐쇄 도메인 밖임: ${v}`);
  }
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-3: 샤드 라벨 경로 안전 — path traversal 차단 (H-9)
// ═════════════════════════════════════════════════════════════════════════

for (const variant of ['escape', 'slash', 'uppercase']) {
  test(`[T082/L1-F1] S-3 (${variant}): 악성 샤드 라벨 — scan/validate exit 1 + shard_declaration_invalid + code-map 밖 신규 파일 0건`, () => {
    const dir = copyFixture(path.join('shard-violations', 'bad-label', variant), `s3-${variant}`);
    const before = listAllFiles(dir).filter(p => !p.startsWith('.opal/code-map/'));

    const scanRes = run(dir, ['scan', '--json']);
    assert.strictEqual(scanRes.exitCode, 1,
      `[RED expect] scan은 exit 1이어야 함, got ${scanRes.exitCode} (stdout: ${scanRes.stdout})`);
    assert.strictEqual(scanRes.json && scanRes.json.error, 'shard_declaration_invalid',
      `[RED expect] error === 'shard_declaration_invalid', got ${scanRes.stdout}`);

    const valRes = run(dir, ['validate', '--json']);
    assert.strictEqual(valRes.exitCode, 1,
      `[RED expect] validate는 exit 1이어야 함, got ${valRes.exitCode} (stdout: ${valRes.stdout})`);
    assert.strictEqual(valRes.json && valRes.json.error, 'shard_declaration_invalid',
      `[RED expect] error === 'shard_declaration_invalid', got ${valRes.stdout}`);

    const after = listAllFiles(dir).filter(p => !p.startsWith('.opal/code-map/'));
    assert.deepStrictEqual(after, before,
      `.opal/code-map/ 밖에 신규 파일이 생기면 안 됨(path traversal), before=${JSON.stringify(before)} after=${JSON.stringify(after)}`);
  });
}

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-4: CODE_MAP_VERSION 불변 (H-10)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F1] S-4: CODE_MAP_VERSION === 1 고정, 기존 자산이 unsupported_version으로 차단되지 않는다', () => {
  const m = SRC.match(/const\s+CODE_MAP_VERSION\s*=\s*(\d+)\s*;/);
  assert.ok(m, 'CODE_MAP_VERSION 상수 선언을 소스에서 찾을 수 없음');
  assert.strictEqual(Number(m[1]), 1, `CODE_MAP_VERSION은 1로 고정되어야 함(상향 시 기존 자산 전량 차단), got ${m[1]}`);

  const dir = copyFixture('shard-repo', 's4');
  const { exitCode, json, stdout } = run(dir, ['validate', '--json']);
  if (exitCode === 1) {
    assert.notStrictEqual(json && json.error, 'unsupported_version',
      `기존 샤드 자산이 unsupported_version으로 차단되면 안 됨, got ${stdout}`);
  }
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-5: 기록 위치 샤드 라우팅 (H-5, U-3 글롭 미채택)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F2] S-5: target — 샤드 보유 키는 샤드 경로+shard 라벨, 신규 파일은 베이스 경로+shard 키 없음', () => {
  const dir = copyFixture('shard-repo', 's5');

  const owned = run(dir, ['target', 'svc/mod/A.ts', '--json']);
  assert.strictEqual(owned.exitCode, 0, `target은 exit 0이어야 함, got ${owned.exitCode} (stdout: ${owned.stdout})`);
  assert.ok(owned.json, `--json 출력이 유효 JSON이어야 함, raw="${owned.stdout}"`);
  assert.strictEqual(owned.json.manifest, '.opal/code-map/svc/mod/_shards/core.json',
    `[RED expect] core 샤드 보유 파일은 manifest가 샤드 경로여야 함, got ${owned.stdout}`);
  assert.strictEqual(owned.json.shard, 'core',
    `[RED expect] shard 필드가 라벨 'core'를 실어야 함, got ${owned.stdout}`);
  assert.strictEqual(owned.json.reason, 'header_source_manifest',
    `reason 도메인 3값 유지 — header_source_manifest, got ${owned.stdout}`);

  const fresh = run(dir, ['target', 'svc/mod/New.ts', '--json']);
  assert.strictEqual(fresh.exitCode, 0, `target은 exit 0이어야 함, got ${fresh.exitCode} (stdout: ${fresh.stdout})`);
  assert.ok(fresh.json, `--json 출력이 유효 JSON이어야 함, raw="${fresh.stdout}"`);
  assert.strictEqual(fresh.json.manifest, '.opal/code-map/svc/mod.json',
    `[RED expect] 미보유 신규 파일은 manifest가 베이스 경로여야 함(U-3), got ${fresh.stdout}`);
  assert.strictEqual(fresh.json.shard, undefined,
    `[RED expect] 미보유 신규 파일은 shard 키가 없어야 함, got ${fresh.stdout}`);
  assert.strictEqual(fresh.json.reason, 'header_source_manifest',
    `reason 도메인 3값 유지 — header_source_manifest, got ${fresh.stdout}`);
});

// ── validate violations 배열에서 code(+sub) 개수를 세는 공용 헬퍼 ──────────
function countViolations(json, code, sub) {
  return (json && Array.isArray(json.violations) ? json.violations : [])
    .filter(v => v.code === code && (sub === undefined || v.sub === sub)).length;
}
function findViolation(json, code, sub) {
  return (json && Array.isArray(json.violations) ? json.violations : [])
    .find(v => v.code === code && (sub === undefined || v.sub === sub));
}

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-8: 샤드 고유 위반 4종 — 각 정확히 1건 (H-1)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F3] S-8 (duplicate-key): worker_scope_violation:shard_duplicate_key 정확히 1건', () => {
  const dir = copyFixture(path.join('shard-violations', 'duplicate-key'), 's8-dup');
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'worker_scope_violation', 'shard_duplicate_key'), 1,
    `[RED expect] shard_duplicate_key 정확히 1건, got ${JSON.stringify(json.violations)}`);
});

test('[T082/L1-F3] S-8 (shard-missing): orphan:shard_missing 정확히 1건', () => {
  const dir = copyFixture(path.join('shard-violations', 'shard-missing'), 's8-missing');
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'orphan', 'shard_missing'), 1,
    `[RED expect] orphan:shard_missing 정확히 1건, got ${JSON.stringify(json.violations)}`);
});

test('[T082/L1-F3] S-8 (undeclared): worker_scope_violation:shard_undeclared 정확히 1건', () => {
  const dir = copyFixture(path.join('shard-violations', 'undeclared'), 's8-undeclared');
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'worker_scope_violation', 'shard_undeclared'), 1,
    `[RED expect] shard_undeclared 정확히 1건, got ${JSON.stringify(json.violations)}`);
});

test('[T082/L1-F3] S-8 (dir-mismatch): worker_scope_violation:shard_dir_mismatch 1건, 기존 dir_mismatch는 0건', () => {
  const dir = copyFixture(path.join('shard-violations', 'dir-mismatch'), 's8-dirmismatch');
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'worker_scope_violation', 'shard_dir_mismatch'), 1,
    `[RED expect] shard_dir_mismatch 정확히 1건, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(countViolations(json, 'worker_scope_violation', 'dir_mismatch'), 0,
    `[RED expect] 샤드는 기존 dir_mismatch sub를 쓰면 안 됨(항상 위반이 되는 판정), got ${JSON.stringify(json.violations)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-9: 오탐 증폭 차단 — orphan:dir_missing 1건 (H-1)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F3] S-9: dir 부재 시 orphan:dir_missing이 샤드 수와 무관하게 1건', () => {
  const dir = copyFixture('shard-repo', 's9');
  fs.rmSync(path.join(dir, 'svc', 'mod'), { recursive: true, force: true });
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'orphan', 'dir_missing'), 1,
    `[RED expect] orphan:dir_missing이 베이스에서 1회만 집계되어야 함(샤드 2개가 있어도 1+N이 아님), got ${JSON.stringify(json.violations)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-10: 샤드 엔트리 침범 귀속
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F3] S-10: 샤드 엔트리에 layer 주입 시 layer_in_manifest가 샤드 경로에 귀속', () => {
  const dir = copyFixture('shard-repo', 's10');
  const pricingAbs = path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'pricing.json');
  const pricing = readJSON(pricingAbs);
  pricing.files['C.ts'].layer = 'util';
  writeJSON(pricingAbs, pricing);

  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const v = findViolation(json, 'worker_scope_violation', 'layer_in_manifest');
  assert.ok(v, `[RED expect] layer_in_manifest 위반이 존재해야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(v.manifest, '.opal/code-map/svc/mod/_shards/pricing.json',
    `[RED expect] manifest 필드가 샤드 경로를 가리켜야 함(베이스가 아님), got ${JSON.stringify(v)}`);
  // shard-repo는 이 layer 주입 1개를 제외하면 정상 구성(S-7)이므로, 정확한 샤드 정합 구현이라면
  // 위반이 이 1건뿐이어야 한다 — 현재는 dir_mismatch·files_key_removed 등 H-1 노이즈가 섞여 나온다.
  assert.strictEqual(json.violations.length, 1,
    `[RED expect] 정상 샤드 구성 + layer 주입 1건이므로 전체 위반은 정확히 1건이어야 함(H-1 노이즈 없음), got ${JSON.stringify(json.violations)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-15: 크기 상한 감지 + 비차단 (H-6, U-2)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F5] S-15: manifest_oversize 열거 + exit 0(비차단)', () => {
  const dir = copyFixture(path.join('shard-violations', 'oversize'), 's15');
  const size = fs.statSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json')).size;
  const { exitCode, json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const v = findViolation(json, 'manifest_oversize');
  assert.ok(v, `[RED expect] manifest_oversize 위반이 열거되어야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(v.manifest, '.opal/code-map/svc/mod.json', `manifest 필드가 경로여야 함, got ${JSON.stringify(v)}`);
  assert.strictEqual(v.detail, `${size}/200`, `detail이 '{bytes}/{limit}' 형식이어야 함, got ${JSON.stringify(v)}`);
  assert.strictEqual(json.counts && json.counts.manifest_oversize, countViolations(json, 'manifest_oversize'),
    `counts.manifest_oversize가 violations 집계와 일치해야 함, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.ok, true, `[RED expect] 다른 위반이 없으면 ok:true(비차단), got ${JSON.stringify(json)}`);
  assert.strictEqual(exitCode, 0, `[RED expect] manifest_oversize만 있으면 exit 0(비차단), got ${exitCode}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-16: 크기 상한 설정 오버라이드 + 경계값 (H-6, 게이트 gaps G-5)
// ═════════════════════════════════════════════════════════════════════════

function setManifestMaxBytes(dir, value) {
  const idxPath = path.join(dir, '.opal', 'code-map', 'index.json');
  const idx = readJSON(idxPath);
  if (value === undefined) delete idx.manifestMaxBytes;
  else idx.manifestMaxBytes = value;
  writeJSON(idxPath, idx);
}

test('[T082/L1-F5] S-16 (a) 작은 값): manifestMaxBytes를 더 작게 설정하면 검출된다', () => {
  const dir = copyFixture(path.join('shard-violations', 'oversize'), 's16-small');
  setManifestMaxBytes(dir, 50);
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.ok(countViolations(json, 'manifest_oversize') >= 1,
    `[RED expect] 더 작은 상한에서도 초과가 검출되어야 함, got ${JSON.stringify(json.violations)}`);
});

test('[T082/L1-F5] S-16 (b) 큰 값): manifestMaxBytes를 크게 설정하면 0건', () => {
  const dir = copyFixture(path.join('shard-violations', 'oversize'), 's16-large');
  setManifestMaxBytes(dir, 999999);
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'manifest_oversize'), 0,
    `[RED expect] 충분히 큰 상한에서는 0건이어야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(json.counts && json.counts.manifest_oversize, 0,
    `[RED expect] counts 스키마에 manifest_oversize 키가 숫자 0으로 존재해야 함, got ${JSON.stringify(json.counts)}`);
});

test('[T082/L1-F5] S-16 (c) 미지정): manifestMaxBytes 미설정 시 내장 기본값 20480 적용', () => {
  const dir = copyFixture(path.join('shard-violations', 'oversize'), 's16-default');
  setManifestMaxBytes(dir, undefined);
  const size = fs.statSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json')).size;
  assert.ok(size < 20480, '사전 조건: 픽스처 크기가 기본 상한보다 작아야 검증이 유의미함');
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'manifest_oversize'), 0,
    `[RED expect] 기본값(20480) 적용 시 0건이어야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(json.counts && json.counts.manifest_oversize, 0,
    `[RED expect] counts 스키마에 manifest_oversize 키가 숫자 0으로 존재해야 함, got ${JSON.stringify(json.counts)}`);
});

test('[T082/L1-F5] S-16 (d) 경계값 size==limit): 상한과 정확히 같은 크기는 초과가 아니다(off-by-one)', () => {
  const dir = copyFixture(path.join('shard-violations', 'oversize'), 's16-boundary-eq');
  const size = fs.statSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json')).size;
  setManifestMaxBytes(dir, size);
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'manifest_oversize'), 0,
    `[RED expect] size===limit은 초과가 아님(off-by-one), got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(json.counts && json.counts.manifest_oversize, 0,
    `[RED expect] counts 스키마에 manifest_oversize 키가 숫자 0으로 존재해야 함, got ${JSON.stringify(json.counts)}`);
});

test('[T082/L1-F5] S-16 (d2) 경계값 size==limit+1): 상한보다 1바이트라도 크면 검출된다', () => {
  const dir = copyFixture(path.join('shard-violations', 'oversize'), 's16-boundary-over');
  const size = fs.statSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json')).size;
  setManifestMaxBytes(dir, size - 1);
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'manifest_oversize'), 1,
    `[RED expect] size===limit+1은 초과여야 함, got ${JSON.stringify(json.violations)}`);
});

test('[T082/L1-F5] S-16 (e) 타입 위반): manifestMaxBytes가 문자열/음수면 invalid_index 처리', () => {
  const dirStr = copyFixture(path.join('shard-violations', 'oversize'), 's16-badtype-str');
  setManifestMaxBytes(dirStr, 'not-a-number');
  const r1 = run(dirStr, ['validate', '--json']);
  assert.strictEqual(r1.exitCode, 1, `[RED expect] 문자열 manifestMaxBytes는 exit 1, got ${r1.exitCode} (${r1.stdout})`);
  assert.strictEqual(r1.json && r1.json.error, 'invalid_index', `[RED expect] error==='invalid_index', got ${r1.stdout}`);

  const dirNeg = copyFixture(path.join('shard-violations', 'oversize'), 's16-badtype-neg');
  setManifestMaxBytes(dirNeg, -1);
  const r2 = run(dirNeg, ['validate', '--json']);
  assert.strictEqual(r2.exitCode, 1, `[RED expect] 음수 manifestMaxBytes는 exit 1, got ${r2.exitCode} (${r2.stdout})`);
  assert.strictEqual(r2.json && r2.json.error, 'invalid_index', `[RED expect] error==='invalid_index', got ${r2.stdout}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-17: scaffold 상한 알림 — stdout 계약 보존 (H-6)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F5] S-17: scaffold — stderr 1줄 경고, stdout JSON은 초과 없을 때와 바이트 동일', () => {
  const withLimit = copyFixture(path.join('shard-violations', 'oversize'), 's17-with');
  const withoutLimit = copyFixture(path.join('shard-violations', 'oversize'), 's17-without');
  setManifestMaxBytes(withoutLimit, undefined); // 기본값 20480 — 이 픽스처 크기로는 초과 없음

  const withRes = run(withLimit, ['scaffold', '--json']);
  const withoutRes = run(withoutLimit, ['scaffold', '--json']);

  assert.strictEqual(withRes.stdout, withoutRes.stdout,
    `[RED expect] stdout JSON은 초과 유무와 무관하게 바이트 동일해야 함, with="${withRes.stdout}" without="${withoutRes.stdout}"`);
  assert.ok(withRes.stderr.trim().length > 0,
    `[RED expect] 초과 시 stderr에 경고가 있어야 함, got stderr="${withRes.stderr}"`);
  assert.strictEqual(withoutRes.stderr.trim(), '',
    `초과가 없으면 stderr가 비어 있어야 함(대조군), got stderr="${withoutRes.stderr}"`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-25: 상한 검사가 샤드 파일 자신도 측정하는가 ⭐ (H-6b, 게이트 gaps G-1)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F5] S-25: 베이스는 상한 이하·샤드만 초과 — manifest_oversize 1건 + manifest 필드가 샤드 경로', () => {
  const dir = copyFixture(path.join('shard-violations', 'oversize-shard'), 's25');
  const baseSize = fs.statSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json')).size;
  assert.ok(baseSize <= 200, `사전 조건: 베이스는 상한(200) 이하여야 함, got ${baseSize}`);

  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(countViolations(json, 'manifest_oversize'), 1,
    `[RED expect] 베이스만 순회하면 0건이 되어 FAIL — 샤드도 측정해 1건이어야 함, got ${JSON.stringify(json.violations)}`);
  const v = findViolation(json, 'manifest_oversize');
  assert.strictEqual(v && v.manifest, '.opal/code-map/svc/mod/_shards/core.json',
    `[RED expect] manifest 필드가 샤드 경로를 가리켜야 함(베이스가 아님), got ${JSON.stringify(v)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-21: 봉인 지점 1곳 유지 (H-12, 정적 검사)
// ═════════════════════════════════════════════════════════════════════════

/**
 * `function <name>(` 로 시작하는 최상위 함수의 줄 범위를 중괄호 깊이로 확정한다(0-based, [start,end) 반쪽열림).
 * 문자열 리터럴·라인 주석 안의 중괄호는 세지 않는다 (tests/test-hook.js:122-135 패턴 재사용).
 */
function functionLineSpan(srcLines, name) {
  const S = srcLines.findIndex(l => new RegExp('^function\\s+' + name + '\\s*\\(').test(l));
  if (S < 0) return null;
  let d = 0;
  for (let i = S; i < srcLines.length; i++) {
    const l = srcLines[i].replace(/\/\/.*$/, '').replace(/(["'`]).*?\1/g, '');
    for (const ch of l) { if (ch === '{') d++; else if (ch === '}') d--; }
    if (i > S && d === 0) return [S, i + 1];
  }
  return [S, srcLines.length];
}

test('[T082/L1-F1] S-21: resolveShards 봉인 — _shards 경로 조립·byKey 구성이 함수 밖에 0건', () => {
  const lines = SRC.split('\n');
  const span = functionLineSpan(lines, 'resolveShards');
  assert.ok(span, `[RED expect] resolveShards 함수가 소스에 존재해야 함(아직 미구현)`);

  const inSpan = (i) => i >= span[0] && i < span[1];

  // `.byKey` Map 접근/구성은 resolveShards 함수 본문 밖에 있으면 안 된다
  // (decideTarget·resolveHeader 등 소비처는 view.byKey.get(...)만 읽으므로 이 문자열 자체가
  // 소비처 코드에도 나타난다 — 그래서 별도로 "구성"이 아니라 최소 접근 패턴 전체를 봉인 함수
  // 안에서만 두지 않고, 대신 byKey Map을 **만드는** 리터럴 `new Map()`이 이 함수 밖에 없는지를 본다).
  lines.forEach((l, i) => {
    if (/byKey\s*:\s*new Map\(\)|byKey\.set\(/.test(l) && !inSpan(i)) {
      assert.fail(`byKey Map 구성이 resolveShards 밖(${i + 1}행)에 있음: ${l}`);
    }
  });

  // 모드 판정 함수는 resolveHeaderSource 1개뿐이어야 한다 — 봉인 지점을 늘리지 않는다
  const modeJudgeFns = lines.filter(l => /^function\s+resolve\w*Mode\w*\s*\(/.test(l)
    || /^function\s+resolve\w*HeaderSource\w*\s*\(/.test(l));
  assert.strictEqual(modeJudgeFns.length, 1,
    `모드 판정 함수는 resolveHeaderSource 1개여야 함, got ${JSON.stringify(modeJudgeFns)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L1 — S-22: 버전·문서 산출물 검사 (H-12, 문서-코드 정합) — 구현·문서 전 RED가 정상
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L1-F8] S-22 (version): code-scan version === v1.5.0, 변경이력에 (082) 행 존재', () => {
  const dir = copyFixture('shard-repo', 's22-version');
  const { exitCode, stdout } = run(dir, ['--version']);
  assert.strictEqual(exitCode, 0, `--version은 exit 0이어야 함, got ${exitCode}`);
  assert.strictEqual(stdout.trim(), 'code-scan v1.5.0',
    `[RED expect] 버전이 v1.5.0으로 상향되어야 함, got "${stdout.trim()}"`);

  assert.match(SRC, /\(082\)/, `[RED expect] 소스 하단 변경이력에 (082) 표기가 있어야 함`);
  assert.match(SRC, /\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}.*\(082\)|\(082\).*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}/,
    `[RED expect] 변경이력이 YYYY-MM-DD HH:mm (KST) + (082) 포맷이어야 함`);
});

test('[T082/L1-F8] S-22 (tools.md): _shards·manifestMaxBytes·신규 에러 코드 2종 반영', () => {
  const toolsMd = fs.readFileSync(path.resolve(__dirname, '..', '..', '..', 'core', 'references', 'tools.md'), 'utf8');
  assert.match(toolsMd, /_shards/, `[RED expect] tools.md에 _shards 반영 필요`);
  assert.match(toolsMd, /manifestMaxBytes/, `[RED expect] tools.md에 manifestMaxBytes 반영 필요`);
  assert.match(toolsMd, /shard_declaration_invalid/, `[RED expect] tools.md 에러 코드 표에 shard_declaration_invalid 반영 필요`);
  assert.match(toolsMd, /reserved_name_collision/, `[RED expect] tools.md 에러 코드 표에 reserved_name_collision 반영 필요`);
});

test('[T082/L1-F8] S-22 (header-rules.md): 워커 권한 경계 금지 필드에 shards 추가 + 변경이력 KST/(082) 포맷', () => {
  const hrMd = fs.readFileSync(
    path.resolve(__dirname, '..', '..', '..', 'core', 'references', 'harness', 'header-rules.md'), 'utf8');
  const forbiddenLine = hrMd.split('\n').find(l => l.includes('금지 (도구 관할)'));
  assert.ok(forbiddenLine, 'header-rules.md에 "금지 (도구 관할)" 행을 찾을 수 없음');
  assert.match(forbiddenLine, /`shards`/, `[RED expect] 금지 필드 목록에 shards 추가 필요, got: ${forbiddenLine}`);
  assert.match(hrMd, /\(082\)/, `[RED expect] 변경이력에 (082) 표기 필요`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-6: hook 자동 정합 + 파손 fail-safe (H-5)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F2] S-6 (a): shard-repo 청결 엔트리(C.ts, pricing 샤드) — hook 무출력 exit 0', () => {
  const dir = copyFixture('shard-repo', 's6a');
  const abs = path.join(dir, 'svc', 'mod', 'C.ts');
  const { exitCode, stdout, stderr } = runHook(dir, editEvent(abs));
  assert.strictEqual(exitCode, 0, `hook은 항상 exit 0(fail-safe), got ${exitCode}`);
  assert.strictEqual(stdout, '', `[RED expect] 청결한 샤드 엔트리는 stdout 0바이트여야 함, got "${stdout}"`);
  assert.strictEqual(stderr, '', `[RED expect] 청결한 샤드 엔트리는 stderr 0바이트여야 함, got "${stderr}"`);
});

test('[T082/L2-F2] S-6 (b): shard-repo 미갱신 엔트리(A.ts, core 샤드) — 경고에 샤드 경로 포함', () => {
  // 082 Step 9e: S-6(a)(청결)와 S-6(b)(미갱신)가 같은 A.ts를 요구 → 미갱신 픽스처로 분리 (캡틴 승인)
  const dir = copyFixture('shard-package', 's6b');
  const abs = path.join(dir, 'svc', 'mod', 'A.ts');
  const { exitCode, stdout } = runHook(dir, editEvent(abs));
  assert.strictEqual(exitCode, 0, `hook은 항상 exit 0(fail-safe), got ${exitCode}`);
  assert.ok(stdout.trim().length > 0, `[RED expect] 미갱신 엔트리는 경고가 출력되어야 함, got "${stdout}"`);
  const payload = JSON.parse(stdout);
  const ctx = payload.hookSpecificOutput && payload.hookSpecificOutput.additionalContext;
  assert.ok(typeof ctx === 'string' && ctx.includes('.opal/code-map/svc/mod/_shards/core.json'),
    `[RED expect] 경고 본문에 core 샤드 경로가 포함되어야 함, got "${ctx}"`);
});

test('[T082/L2-F2] S-6 (c): 파손 베이스(broken-base) — hook 무출력 exit 0 (try/catch 흡수)', () => {
  const dir = copyFixture(path.join('shard-violations', 'broken-base'), 's6c');
  const abs = path.join(dir, 'svc', 'mod', 'A.ts');
  const { exitCode, stdout, stderr } = runHook(dir, editEvent(abs));
  assert.strictEqual(exitCode, 0, `hook은 항상 exit 0(fail-safe), got ${exitCode}`);
  assert.strictEqual(stdout, '', `[RED expect] 파손 베이스에서도 stdout 0바이트여야 함(흡수), got "${stdout}"`);
  assert.strictEqual(stderr, '', `[RED expect] 파손 베이스에서도 stderr 0바이트여야 함(흡수), got "${stderr}"`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-7: 정상 샤드 구성 — 위반 0건 (H-1 직접 반증)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F3] S-7 (full): shard-repo validate --json — 위반 0건 exit 0', () => {
  const dir = copyFixture('shard-repo', 's7-full');
  const { exitCode, json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(json.violations.length, 0,
    `[RED expect] 정상 샤드 구성은 위반 0건이어야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
});

test('[T082/L2-F3] S-7 (--changed): shard-repo validate --changed --json — 위반 0건 exit 0', () => {
  const dir = copyFixture('shard-repo', 's7-changed');
  const changedList = ['svc/mod/A.ts', 'svc/mod/B.ts', 'svc/mod/C.ts', 'svc/mod/D.ts'].join(',');
  const { exitCode, json, stdout } = run(dir, ['validate', '--changed', changedList, '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(json.violations.length, 0,
    `[RED expect] --changed 모드도 정상 샤드 구성은 위반 0건이어야 함(커버 판정 파일 루프 경유), got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-11: stale 오탐 차단 (H-2)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F4] S-11: shard-repo scaffold — 선언된 _shards/*.json이 stale 0건', () => {
  const dir = copyFixture('shard-repo', 's11');
  const { json, stdout } = run(dir, ['scaffold', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const shardStale = (json.stale || []).filter(p => p.includes('/_shards/'));
  assert.strictEqual(shardStale.length, 0,
    `[RED expect] 선언된 샤드는 stale 0건이어야 함, got ${JSON.stringify(json.stale)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-12: scaffold 멱등 + 샤드 자산 보존 (H-3)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F4] S-12: scaffold 2회 연속 — shards 선언 보존 + 베이스 files 무오염 + 2회차 created/updated=0', () => {
  const dir = copyFixture('shard-repo', 's12');
  const baseAbs = path.join(dir, '.opal', 'code-map', 'svc', 'mod.json');

  const r1 = run(dir, ['scaffold', '--json']);
  assert.ok(r1.json, `1회차 --json 출력이 유효해야 함, raw="${r1.stdout}"`);

  const afterRun1 = readJSON(baseAbs);
  assert.deepStrictEqual(afterRun1.shards, ['core', 'pricing'],
    `[RED expect] scaffold 후에도 베이스의 shards 선언이 보존되어야 함, got ${JSON.stringify(afterRun1.shards)}`);
  assert.deepStrictEqual(Object.keys(afterRun1.files).sort(), ['D.ts'],
    `[RED expect] 베이스 files는 샤드 소유 키(A/B/C)로 오염되면 안 됨, got ${JSON.stringify(Object.keys(afterRun1.files))}`);

  const snap1 = snapshotCodeMap(dir);
  const r2 = run(dir, ['scaffold', '--json']);
  assert.ok(r2.json, `2회차 --json 출력이 유효해야 함, raw="${r2.stdout}"`);
  assert.strictEqual(r2.json.created, 0, `2회차 created===0(멱등), got ${r2.json.created}`);
  assert.strictEqual(r2.json.updated, 0, `2회차 updated===0(멱등), got ${r2.json.updated}`);
  const snap2 = snapshotCodeMap(dir);
  for (const key of Object.keys(snap1)) {
    assert.strictEqual(snap2[key] && snap2[key].content, snap1[key].content,
      `${key} 내용이 1회차·2회차 사이 바이트 동일해야 함`);
  }
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-13: 신규·삭제 파일 처리 (H-3)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F4] S-13 (a) 신규 파일: 베이스 files에 draft:true 추가 + added[]가 베이스 경로, 샤드 무변화', () => {
  const dir = copyFixture('shard-repo', 's13-new');
  const shardsSnapBefore = {
    core: fs.readFileSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'core.json'), 'utf8'),
    pricing: fs.readFileSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'pricing.json'), 'utf8'),
  };
  fs.writeFileSync(path.join(dir, 'svc', 'mod', 'New.ts'), 'export const New = 1;\n');

  const { json, stdout } = run(dir, ['scaffold', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.deepStrictEqual(json.added, ['.opal/code-map/svc/mod.json:New.ts'],
    `[RED expect] added[]가 베이스 경로:New.ts 단 1건이어야 함(A/B/C는 샤드 소유이므로 added에 없어야 함), got ${JSON.stringify(json.added)}`);

  const baseAfter = readJSON(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json'));
  assert.strictEqual(baseAfter.files['New.ts'] && baseAfter.files['New.ts'].draft, true,
    `[RED expect] 베이스 files에 New.ts가 draft:true로 추가되어야 함, got ${JSON.stringify(baseAfter.files['New.ts'])}`);

  const coreAfter = fs.readFileSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'core.json'), 'utf8');
  const pricingAfter = fs.readFileSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'pricing.json'), 'utf8');
  assert.strictEqual(coreAfter, shardsSnapBefore.core, `core 샤드는 신규 파일과 무관하게 무변화여야 함`);
  assert.strictEqual(pricingAfter, shardsSnapBefore.pricing, `pricing 샤드는 신규 파일과 무관하게 무변화여야 함`);
});

test('[T082/L2-F4] S-13 (b) 삭제 파일: 샤드 소유 키의 소스 삭제 시 해당 샤드에서 pruned, 베이스 무변화', () => {
  const dir = copyFixture('shard-repo', 's13-del');
  const baseBefore = fs.readFileSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json'), 'utf8');
  fs.rmSync(path.join(dir, 'svc', 'mod', 'B.ts'));

  const { json, stdout } = run(dir, ['scaffold', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const prunedCore = (json.pruned || []).find(p => p.includes('_shards/core.json') && p.endsWith(':B.ts'));
  assert.ok(prunedCore, `[RED expect] pruned[]에 core 샤드:B.ts 항목이 있어야 함, got ${JSON.stringify(json.pruned)}`);

  const coreAfter = readJSON(path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'core.json'));
  assert.ok(!Object.prototype.hasOwnProperty.call(coreAfter.files, 'B.ts'),
    `[RED expect] core 샤드 files에서 B.ts가 제거되어야 함, got ${JSON.stringify(coreAfter.files)}`);

  const baseAfter = fs.readFileSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json'), 'utf8');
  assert.strictEqual(baseAfter, baseBefore, `베이스는 샤드 소유 파일 삭제와 무관하게 무변화여야 함`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-14: 중복 키 무쓰기 가드 (H-3, U-4 파생)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F4] S-14: duplicate-key — 디렉토리 skip + skipped[shard_duplicate_key] + 샤드 파일 mtime·내용 무변화', () => {
  const dir = copyFixture(path.join('shard-violations', 'duplicate-key'), 's14');
  const coreAbs = path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'core.json');
  const before = { content: fs.readFileSync(coreAbs, 'utf8'), mtimeMs: fs.statSync(coreAbs).mtimeMs };

  const { json, stdout } = run(dir, ['scaffold', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const skip = (json.skipped || []).find(s => s.reason === 'shard_duplicate_key');
  assert.ok(skip, `[RED expect] skipped[]에 shard_duplicate_key 사유가 있어야 함, got ${JSON.stringify(json.skipped)}`);

  const after = { content: fs.readFileSync(coreAbs, 'utf8'), mtimeMs: fs.statSync(coreAbs).mtimeMs };
  assert.strictEqual(after.content, before.content, `core 샤드 내용은 중복 검출 시 무변화여야 함(패자 서술 보존)`);
  assert.strictEqual(after.mtimeMs, before.mtimeMs, `core 샤드 mtime은 중복 검출 시 무변화여야 함(쓰기 자체가 없어야 함)`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-18: `_shards` 예약어 거부 (H-7)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F6] S-18 (scaffold): reserved-name — reserved_name_collision exit 1 + code-map 트리 바이트 동일(미기록)', () => {
  const dir = copyFixture(path.join('shard-violations', 'reserved-name'), 's18-scaffold');
  const before = snapshotCodeMap(dir);

  const { exitCode, json, stdout } = run(dir, ['scaffold', '--json']);
  assert.strictEqual(exitCode, 1, `[RED expect] reserved_name_collision은 exit 1이어야 함, got ${exitCode} (stdout: ${stdout})`);
  assert.strictEqual(json && json.error, 'reserved_name_collision',
    `[RED expect] error==='reserved_name_collision', got ${stdout}`);

  const after = snapshotCodeMap(dir);
  assert.deepStrictEqual(Object.keys(after).sort(), Object.keys(before).sort(),
    `[RED expect] 매니페스트를 쓰면 안 됨 — 파일 목록이 무변화여야 함`);
  for (const key of Object.keys(before)) {
    assert.strictEqual(after[key] && after[key].content, before[key].content,
      `[RED expect] ${key} 내용이 무변화여야 함(매니페스트 미기록)`);
  }
});

test('[T082/L2-F6] S-18 (validate): reserved-name — worker_scope_violation:reserved_name 검출', () => {
  const dir = copyFixture(path.join('shard-violations', 'reserved-name'), 's18-validate');
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.ok(countViolations(json, 'worker_scope_violation', 'reserved_name') >= 1,
    `[RED expect] reserved_name 위반이 검출되어야 함, got ${JSON.stringify(json.violations)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-19: 하위호환 — 샤드 미선언 자산 바이트 동일 (H-4, 회귀 가드)
// ═════════════════════════════════════════════════════════════════════════
//
// [참고] 아래 단언들은 "샤드 미선언 자산은 변경 전과 바이트 동일해야 한다"는 **회귀 방지** 계약이다.
// 기능이 아직 없는 v1.4.0에서는 이 불변식이 이미 자명하게 성립한다(S-4의 CODE_MAP_VERSION 불변
// 검사와 같은 성격) — 그래서 이 절의 일부 단언은 오늘도 이미 PASS일 수 있다. 이는 테스트 결함이
// 아니라 "회귀 가드는 구현 전후 모두 성립해야 한다"는 계약의 정상적 성질이다.

const GOLDEN_DIR = path.join(FIX, 'golden');
const LEGACY_REPO_DIR = path.join(FIX, 'legacy-repo');
const GOLDEN_COMMANDS = [
  { args: ['scan', '--json'], golden: 'scan.json' },
  { args: ['domain'], golden: 'domain.txt' },
  { args: ['layer'], golden: 'layer.txt' },
  { args: ['search', 'auth', '--json'], golden: 'search.json' },
  { args: ['exports', 'token', '--json'], golden: 'exports.json' },
  { args: ['summary'], golden: 'summary.txt' },
  { args: ['depends', 'auth_service'], golden: 'depends.txt' },
  { args: ['missing'], golden: 'missing.txt' },
];

for (const c of GOLDEN_COMMANDS) {
  test(`[T082/L2-F7] S-19: 골든 8커맨드 재확인 — "${c.args.join(' ')}" 바이트 동일(회귀 가드)`, () => {
    const { exitCode, stdout } = run(LEGACY_REPO_DIR, c.args);
    assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
    const expected = fs.readFileSync(path.join(GOLDEN_DIR, c.golden), 'utf8');
    assert.strictEqual(stdout, expected, `골든과 바이트 동일해야 함(${c.golden})`);
  });
}

test('[T082/L2-F7] S-19: 샤드 미선언 매니페스트 자산 — 빈 shards:[] 추가가 scan/target/scaffold 출력에 영향 없음', () => {
  const plain = copyFixture('codemap-repo', 's19-plain');
  const withEmpty = copyFixture('codemap-repo', 's19-empty-shards');
  const serviceAbs = path.join(withEmpty, '.opal', 'code-map', 'svc', 'order-api', 'order', 'service.json');
  const manifest = readJSON(serviceAbs);
  manifest.shards = [];
  writeJSON(serviceAbs, manifest);

  const scanPlain = run(plain, ['scan', '--json']);
  const scanEmpty = run(withEmpty, ['scan', '--json']);
  assert.strictEqual(scanEmpty.stdout, scanPlain.stdout,
    `[회귀 가드] shards:[] 추가는 scan --json 출력에 영향이 없어야 함(null 반환 조건 4)`);

  const tgtPlain = run(plain, ['target', 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java', '--json']);
  const tgtEmpty = run(withEmpty, ['target', 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java', '--json']);
  assert.strictEqual(tgtEmpty.stdout, tgtPlain.stdout,
    `[회귀 가드] shards:[] 추가는 target --json 출력에 영향이 없어야 함`);

  const scfPlain = run(plain, ['scaffold', '--json', '--dry-run']);
  const scfEmpty = run(withEmpty, ['scaffold', '--json', '--dry-run']);
  assert.strictEqual(scfEmpty.stdout, scfPlain.stdout,
    `[회귀 가드] shards:[] 추가는 scaffold --json 출력에 영향이 없어야 함`);
});

test('[T082/L2-F7] S-19: 기존 테스트 10종 전량 GREEN(무수정)', () => {
  const otherFiles = fs.readdirSync(__dirname)
    .filter(f => f.startsWith('test-') && f.endsWith('.js') && f !== 'test-shard.js');
  assert.ok(otherFiles.length >= 10, `기존 테스트 파일이 최소 10종 있어야 함, got ${otherFiles.length}: ${JSON.stringify(otherFiles)}`);
  // 082 Step 9e: NODE_TEST_CONTEXT를 자식에 그대로 물려주면 재귀 가드로 자식이 no-op(fail=-1)한다.
  // test-regression.js:581-584와 동일하게 제거해 자식이 실제로 테스트를 돌리게 한다.
  const childEnv = { ...process.env };
  delete childEnv.NODE_TEST_CONTEXT;
  const result = spawnSync(process.execPath, ['--test', ...otherFiles.map(f => path.join(__dirname, f))],
    { encoding: 'utf8', timeout: 120000, env: childEnv });
  const summary = (result.stdout || '') + (result.stderr || '');
  // 082 Step 9e: 리포터 포맷 종속(/# fail/ ↔ 실제 'ℹ fail') 계측 버그 → exit status 판정으로 교체 (캡틴 승인)
  const tail = summary.split('\n').filter(l => /^ℹ (tests|pass|fail|skipped)/.test(l)).join(' | ');
  assert.strictEqual(result.status, 0,
    `기존 테스트 10종은 무수정 GREEN이어야 함(재캡처·완화 금지), exit ${result.status} | ${tail}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-20: inline 모드 무영향 (양축) (H-8)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F7] S-20: shard-repo + --header-source inline — stdout·stderr 양축이 샤드 미도입 시와 동일', () => {
  const withShard = copyFixture('shard-repo', 's20-with');
  const withoutShard = copyFixture('shard-repo', 's20-without');
  // 샤드 자산을 걷어낸 대조군 — base에서 shards 선언 제거 + _shards 디렉토리 삭제 + 샤드 소유 파일도
  // 베이스로 흡수(그래야 inline 모드에서 두 트리의 노출 파일 집합이 같아진다).
  const baseAbs = path.join(withoutShard, '.opal', 'code-map', 'svc', 'mod.json');
  const base = readJSON(baseAbs);
  const core = readJSON(path.join(withoutShard, '.opal', 'code-map', 'svc', 'mod', '_shards', 'core.json'));
  const pricing = readJSON(path.join(withoutShard, '.opal', 'code-map', 'svc', 'mod', '_shards', 'pricing.json'));
  delete base.shards;
  Object.assign(base.files, core.files, pricing.files);
  writeJSON(baseAbs, base);
  fs.rmSync(path.join(withoutShard, '.opal', 'code-map', 'svc', 'mod', '_shards'), { recursive: true, force: true });

  for (const args of [['scan', '--json', '--header-source', 'inline'],
                       ['validate', '--json', '--header-source', 'inline'],
                       ['scaffold', '--json', '--dry-run', '--header-source', 'inline']]) {
    const a = run(withShard, args);
    const b = run(withoutShard, args);
    assert.strictEqual(a.stdout, b.stdout, `[RED expect] inline 강제 시 stdout이 샤드 유무와 무관하게 동일해야 함 (args: ${args.join(' ')})`);
    assert.strictEqual(a.stderr, b.stderr, `[RED expect] inline 강제 시 stderr가 샤드 유무와 무관하게 동일해야 함 (args: ${args.join(' ')})`);
  }
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-23: 목표달성 — 분산으로 크기가 실제로 내려가고 조회가 온전한가 ⭐ (H-11)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-GOAL] S-23 ①②③④: shard-goal 분산 전/후 — oversize 하강 + 헤더값 동일 + 라우팅 + 위반 0건', () => {
  const before = copyFixture(path.join('shard-goal', 'before'), 's23-before');
  const { dir: after, labels } = deriveAfterTree('s23-after');

  // ① 분산 전에는 manifest_oversize가 최소 1건, 분산 후에는 0건
  const valBefore = run(before, ['validate', '--json']);
  assert.ok(valBefore.json, `분산 전 --json 출력이 유효해야 함, raw="${valBefore.stdout}"`);
  assert.ok(countViolations(valBefore.json, 'manifest_oversize') >= 1,
    `사전 조건(대조군): 분산 전 베이스는 상한을 초과해야 함, got ${JSON.stringify(valBefore.json.violations)}`);

  const valAfter = run(after, ['validate', '--json']);
  assert.ok(valAfter.json, `분산 후 --json 출력이 유효해야 함, raw="${valAfter.stdout}"`);
  assert.strictEqual(countViolations(valAfter.json, 'manifest_oversize'), 0,
    `[RED expect] ① 분산 후에는 manifest_oversize가 0건이어야 함, got ${JSON.stringify(valAfter.json.violations)}`);

  // ② 분산 전후 scan --json 엔트리 집합·헤더 필드 값 완전 동일(description/exports)
  const scanBefore = run(before, ['scan', '--json']);
  const scanAfter = run(after, ['scan', '--json']);
  assert.ok(scanBefore.json && scanAfter.json, `scan --json 출력이 유효해야 함`);
  const keysBefore = Object.keys(scanBefore.json).sort();
  const keysAfter = Object.keys(scanAfter.json).sort();
  assert.deepStrictEqual(keysAfter, keysBefore,
    `[RED expect] ② 분산 전후 scan 엔트리 집합이 동일해야 함, before=${JSON.stringify(keysBefore)} after=${JSON.stringify(keysAfter)}`);
  for (const key of keysBefore) {
    assert.strictEqual(scanAfter.json[key].description, scanBefore.json[key].description,
      `[RED expect] ② ${key}.description이 분산 전후 동일해야 함`);
    assert.deepStrictEqual(scanAfter.json[key].exports, scanBefore.json[key].exports,
      `[RED expect] ② ${key}.exports가 분산 전후 동일해야 함`);
  }

  // ③ 분산 후 모든 파일이 target --json에서 자기 소유 샤드로 라우팅
  for (const key of Object.keys(scanBefore.json)) {
    const rel = key; // 'svc/mod/CoreA.ts' 형태
    const stem = path.basename(rel).replace(/\.ts$/, '');
    const label = toKebabLabel(stem);
    assert.ok(labels.includes(label), `사전 조건: 파생 라벨 ${label}이 shards 선언에 있어야 함`);
    const tgt = run(after, ['target', rel, '--json']);
    assert.ok(tgt.json, `target --json 출력이 유효해야 함, raw="${tgt.stdout}"`);
    assert.strictEqual(tgt.json.manifest, `.opal/code-map/svc/mod/_shards/${label}.json`,
      `[RED expect] ③ ${rel}이 자기 소유 샤드(${label})로 라우팅되어야 함, got ${tgt.stdout}`);
  }

  // ④ 분산 후 validate 위반 0건 + exit 0
  assert.strictEqual(valAfter.json.violations.length, 0,
    `[RED expect] ④ 분산 후 위반은 0건이어야 함, got ${JSON.stringify(valAfter.json.violations)}`);
  assert.strictEqual(valAfter.exitCode, 0, `[RED expect] ④ 분산 후 exit 0, got ${valAfter.exitCode}`);
});

test('[T082/L2-GOAL] S-23 ⑤: 중간 상태 (a) 선언 누락 — scan이 엔트리를 누락하지 않고 validate가 shard_undeclared로 드러냄', () => {
  const dir = copyFixture(path.join('shard-goal', 'mid-undeclared'), 's23-mid-undeclared');
  const scanRes = run(dir, ['scan', '--json']);
  assert.ok(scanRes.json, `scan --json 출력이 유효해야 함, raw="${scanRes.stdout}"`);
  assert.ok(Object.prototype.hasOwnProperty.call(scanRes.json, 'svc/mod/CoreA.ts'),
    `[사전 안전망] CoreA.ts가 scan 결과에서 조용히 사라지면 안 됨(서술 유실 방지), keys=${JSON.stringify(Object.keys(scanRes.json))}`);

  const valRes = run(dir, ['validate', '--json']);
  assert.ok(valRes.json, `validate --json 출력이 유효해야 함, raw="${valRes.stdout}"`);
  assert.ok(countViolations(valRes.json, 'worker_scope_violation', 'shard_undeclared') >= 1,
    `[RED expect] ⑤ 베이스 shards 선언 누락은 shard_undeclared로 드러나야 함, got ${JSON.stringify(valRes.json.violations)}`);
});

test('[T082/L2-GOAL] S-23 ⑥: 중간 상태 (b) 중복 — 조회는 승자(베이스)로 동작하고 validate가 shard_duplicate_key로 드러냄', () => {
  const dir = copyFixture(path.join('shard-goal', 'mid-duplicate'), 's23-mid-duplicate');
  const scanRes = run(dir, ['scan', '--json']);
  assert.ok(scanRes.json, `scan --json 출력이 유효해야 함, raw="${scanRes.stdout}"`);
  const entry = scanRes.json['svc/mod/CoreA.ts'];
  assert.ok(entry, `svc/mod/CoreA.ts 헤더가 존재해야 함`);
  assert.strictEqual(entry.description, 'core 그룹 파일 A — 샤드로 옮겼으나 베이스에서 미제거 (중복)',
    `[승자=베이스] 조회는 베이스(선언 순서 우선)의 서술로 동작해야 함, got ${JSON.stringify(entry)}`);

  const valRes = run(dir, ['validate', '--json']);
  assert.ok(valRes.json, `validate --json 출력이 유효해야 함, raw="${valRes.stdout}"`);
  assert.ok(countViolations(valRes.json, 'worker_scope_violation', 'shard_duplicate_key') >= 1,
    `[RED expect] ⑥ 중복은 shard_duplicate_key로 드러나야 함, got ${JSON.stringify(valRes.json.violations)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// L2 — S-26: 다중 스코프 상태 격리 (H-13, 게이트 gaps G-4)
// ═════════════════════════════════════════════════════════════════════════

test('[T082/L2-F3] S-26 ①: 전체 validate — shard_undeclared가 svc-b에만 귀속, svc-a로 번지지 않음', () => {
  const dir = copyFixture('shard-multi-scope', 's26-full');
  const { json, stdout } = run(dir, ['validate', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const undeclared = (json.violations || []).filter(v => v.code === 'worker_scope_violation' && v.sub === 'shard_undeclared');
  assert.strictEqual(undeclared.length, 1,
    `[RED expect] shard_undeclared는 정확히 1건(svc-b/mod/_shards/orphan.json)이어야 함, got ${JSON.stringify(undeclared)}`);
  assert.ok(undeclared[0] && undeclared[0].manifest && undeclared[0].manifest.includes('svc-b'),
    `[RED expect] shard_undeclared가 svc-b에 귀속되어야 함, got ${JSON.stringify(undeclared[0])}`);
  const svcAPolluted = (json.violations || []).some(v => v.manifest && v.manifest.includes('svc-a') && v.sub === 'shard_undeclared');
  assert.strictEqual(svcAPolluted, false, `svc-a로 shard_undeclared가 번지면 안 됨`);
});

test('[T082/L2-F3] S-26 ②: --scope svc-a — svc-a만 검사되고 svc-b 위반이 나타나지 않음', () => {
  const dir = copyFixture('shard-multi-scope', 's26-scoped');
  const { json, stdout } = run(dir, ['validate', '--scope', 'svc-a', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const svcBLeaked = (json.violations || []).some(v => v.manifest && v.manifest.includes('svc-b'));
  assert.strictEqual(svcBLeaked, false,
    `[RED expect] --scope svc-a 지정 시 svc-b 위반이 나타나면 안 됨, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(json.violations.length, 0,
    `[RED expect] svc-a는 그 자체로 정상 구성이므로 위반 0건이어야 함, got ${JSON.stringify(json.violations)}`);
});

test('[T082/L2-F3] S-26 ③: 동일 basename(A.ts) 캐시 교차 오염 없음 — 스코프별 정확한 description', () => {
  const dir = copyFixture('shard-multi-scope', 's26-cache');
  const { json, stdout } = run(dir, ['scan', '--json']);
  assert.ok(json, `--json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  const a = json['svc-a/mod/A.ts'];
  const b = json['svc-b/mod/A.ts'];
  assert.ok(a && b, `svc-a·svc-b 양쪽 A.ts 헤더가 모두 존재해야 함, keys=${JSON.stringify(Object.keys(json))}`);
  assert.strictEqual(a.description, 'svc-a core 샤드 소유 파일',
    `[RED expect] svc-a/A.ts는 svc-a 자신의 description이어야 함(교차 오염 없음), got ${JSON.stringify(a)}`);
  assert.strictEqual(b.description, 'svc-b core 샤드 소유 파일',
    `[RED expect] svc-b/A.ts는 svc-b 자신의 description이어야 함(교차 오염 없음), got ${JSON.stringify(b)}`);
});

