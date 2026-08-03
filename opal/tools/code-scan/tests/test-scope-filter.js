/**
 * @header {
 *   "module": "test-scope-filter",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — scopes 객체 형식 정규화·isInScope 단일 필터 계약(5개 적용 지점)·스코프 중복 우선순위(scope_ambiguous)·include/exclude 타입 검증, 그리고 목표달성 통합(두 스코프 동일 모드·4경로 일치·전역 1값 반전으로 5경로 동시 반전) CLI 블랙박스 테스트 (F-002/F-003, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-4", "S-5", "S-6", "S-19"]
 * }
 */
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.2.5/§3.3.5, TEST-SCENARIO.md §4):
//
// | 케이스 프리픽스   | TS-ID                  | S-ID | 계층 | 검증 명제                                              |
// |------------------|------------------------|------|------|-------------------------------------------------------|
// | [T080/L1-F7]     | TS-010, TS-011         | S-4  | L1   | 문자열 scopes 20종 무수정 동작 · 객체 형식 스키마 통과   |
// | [T080/L1-F7b]    | TS-075                 | S-4  | L1   | include/exclude 타입 위반 3케이스 × 두 레지스트리        |
// | [T080/L1-F10]    | TS-016, TS-017, TS-018 | S-5  | L1   | include 승리 · 양쪽 매칭 거부 · tiebreak 회귀 불변       |
// | [T080/L2-F8]     | TS-012, TS-013, TS-019 | S-6  | L2   | 5지점 동일 집합 · isInScope 봉인 · 명시 경로 필터 면제   |
// | [T080/L2-GOAL]   | TS-072, TS-073, TS-074 | S-19 | L2   | **목표달성** — 두 스코프 동일 모드 · 4경로 일치 · 전역 1값 반전 |
//
// [MUST] red-first.md §4 — 공개 인터페이스(실 CLI subprocess의 exit code · stdout JSON · stderr ·
// 파일시스템 상태)로만 검증한다. code-scan.js를 require하여 내부 함수를 직접 호출하지 않는다.
// 유일한 예외는 TS-013(산출물 검사)이며, 이것은 실행이 아니라 소스 텍스트에 대한 grep 계약이다.
//
// [MUST] red-first.md §2 — 이 파일은 opal-test-agent(mode:red)가 작성한다. GREEN 구현은 별도 워커가
// Step 4~7에서 수행한다. 현행 code-scan.js에는 normalizeConfigScope/isInScope/resolveScopeIn/
// isFilteredOutOfScope가 전혀 없고, getSearchPaths(:279-296)가 scopes 값을 문자열로만 다루므로
// 객체 형식 픽스처에서는 즉시 TypeError로 죽는다 → 아래 전 테스트는 실패해야 정상이다(RED 증거).
//
// 픽스처 커밋 상태는 수정하지 않는다. 쓰기 명령(scaffold)·사전 조작이 필요한 케이스는 전부 임시
// 복사본 오버레이를 쓴다(makeHeaderSourceFixture 패턴, test-resolve-header.js:74-83).
//
// 변경이력:
//   v1.0 2026-08-02 KST: RED-first 최초 작성 (태스크 080, opal-test-agent mode:red)
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
const FIX = path.resolve(__dirname, 'fixtures');

// mixed-scope 픽스처 계약 (PLAN §3.7.2 확정 구조)
const SURVIVORS = [
  'svc/shared/OrderRepo.java',
  'svc/shared/OrderService.java',
  'svc/shared/ShipRepo.java',
  'svc/shared/ShipService.java',
];
const OUT_OF_SCOPE_FILE = 'svc/shared/VendorLegacy.java';
const ALL_FIXTURE_FILES = [...SURVIVORS, OUT_OF_SCOPE_FILE].sort();

// ─────────────────────────────────────────────────────────────────────────
// 공통 헬퍼
// ─────────────────────────────────────────────────────────────────────────

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

function copyDirRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDirRecursive(s, d);
    else fs.copyFileSync(s, d);
  }
}

function copyFixture(fixtureRelPath, tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t080-${tag}-`));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureRelPath), dir);
  return dir;
}

function configPath(dir) { return path.join(dir, '.opal', 'code-scan.json'); }
function indexPath(dir) { return path.join(dir, '.opal', 'code-map', 'index.json'); }
function readJsonFile(abs) { return JSON.parse(fs.readFileSync(abs, 'utf8')); }
function writeJsonFile(abs, obj) { fs.writeFileSync(abs, JSON.stringify(obj, null, 2) + '\n'); }

/** 전역 headerSource **한 값만** 교체한다 — TS-074의 "전역 1줄 뒤집기" 조작은 이것뿐이다. */
function setGlobalHeaderSource(dir, value) {
  const cfg = readJsonFile(configPath(dir));
  cfg.headerSource = value;
  writeJsonFile(configPath(dir), cfg);
}

function run(cwd, args) {
  const r = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 20000, env: { ...process.env },
  });
  const stdout = r.stdout || '';
  const stderr = r.stderr || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* 비-JSON 출력 */ }
  return { exitCode: r.status, stdout, stderr, json };
}

function runHook(cwd, payload) {
  const r = spawnSync(process.execPath, [HOOK_JS], {
    cwd, input: JSON.stringify(payload), encoding: 'utf8', timeout: 20000,
  });
  return { exitCode: r.status, stdout: r.stdout || '', stderr: r.stderr || '' };
}

/** `.opal/code-map/` 하위 전 파일의 (상대경로 → 내용+mtime) 스냅샷. scaffold no-op 측정용. */
function snapshotCodeMap(dir) {
  const root = path.join(dir, '.opal', 'code-map');
  const snap = {};
  function walk(d) {
    if (!fs.existsSync(d)) return;
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full);
      else snap[path.relative(root, full)] = {
        content: fs.readFileSync(full, 'utf8'),
        mtimeMs: fs.statSync(full).mtimeMs,
      };
    }
  }
  walk(root);
  return snap;
}

/** scan --json 결과(경로 → 헤더)에서 상대 경로 키 목록을 POSIX로 정규화해 정렬 반환. */
function scannedPaths(json) {
  if (!json || typeof json !== 'object') return [];
  return Object.keys(json).map(p => p.split(path.sep).join('/')).sort();
}

const INLINE_HEADER_JAVA = [
  '/**',
  ' * @header {',
  ' *   "module": "VendorLegacy",',
  ' *   "layer": "service",',
  ' *   "domain": "shared",',
  ' *   "description": "명시 경로 조회 면제 검증용 인라인 헤더 (TS-019)",',
  ' *   "exports": ["VendorLegacy"]',
  ' * }',
  ' */',
  'package svc.shared;',
  'public class VendorLegacy { public void legacyOp() {} }',
  '',
].join('\n');

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F7] TS-010 · TS-011 (S-4) — 문자열 하위호환 + 객체 형식 정규화
// ═════════════════════════════════════════════════════════════════════════

function listFixtureConfigs() {
  const out = [];
  (function walk(d) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full);
      else if (e.name === 'code-scan.json' && path.basename(path.dirname(full)) === '.opal') out.push(full);
    }
  })(FIX);
  return out.sort();
}

test('[T080/L1-F7] TS-010 (S-4): 문자열 scopes 픽스처 20종이 무수정으로 동작한다', () => {
  const configs = listFixtureConfigs();
  const stringScoped = configs.filter(c => {
    const scopes = (readJsonFile(c).scopes) || {};
    const values = Object.values(scopes);
    return values.length > 0 && values.every(v => typeof v === 'string');
  });

  assert.strictEqual(stringScoped.length, 37,
    `[전제] 기존 문자열 scopes 픽스처는 37종이어야 함(082 shard-package 추가 반영), got ${stringScoped.length}:\n  ${stringScoped.join('\n  ')}`);

  const failures = [];
  for (const cfgAbs of stringScoped) {
    const cwd = path.dirname(path.dirname(cfgAbs));           // {fixture}/.opal/code-scan.json → {fixture}
    const { exitCode, json } = run(cwd, ['scan', '--json']);
    const rel = path.relative(FIX, cwd);

    // 스코프 스키마 위반으로 죽으면 안 된다 — 문자열 형식은 그대로 정규화되어 통과해야 한다.
    if (json && json.error === 'code_scan_config_invalid') {
      failures.push(`${rel}: 문자열 scopes가 code_scan_config_invalid로 거부됨`);
      continue;
    }
    // schema/* 4종은 index.json 자체가 고의로 깨진 자산이므로 exit 1이 정상이다(077 TS-002/TS-003).
    if (rel.startsWith('schema' + path.sep) || rel.startsWith('schema/')) continue;
    // shard-violations/broken-base(매니페스트 파손 → manifest_parse_failed)·shard-violations/bad-label(샤드 라벨
    // 스키마 위반 → shard_declaration_invalid)는 고의로 파손된 자산이므로 exit 1이 정상이다 (082 S-3/S-6).
    if (rel.startsWith('shard-violations' + path.sep + 'broken-base') || rel.startsWith('shard-violations/broken-base')
      || rel.startsWith('shard-violations' + path.sep + 'bad-label') || rel.startsWith('shard-violations/bad-label')) continue;
    if (exitCode !== 0) failures.push(`${rel}: exit=${exitCode} (기대 0)`);
  }

  assert.deepStrictEqual(failures, [],
    `[RED expect] 문자열 scopes 픽스처는 정규화 도입 후에도 무수정 동작해야 함. 위반:\n  ${failures.join('\n  ')}`);
});

test('[T080/L1-F7] TS-011 (S-4): 객체 형식 {path, include, exclude}가 스키마 검증을 통과한다', () => {
  const dir = copyFixture('mixed-scope', 'ts011');
  const cfg = readJsonFile(configPath(dir));
  cfg.scopes['order-svc'].exclude = ['*.generated.java'];     // exclude까지 포함한 완전 형태
  writeJsonFile(configPath(dir), cfg);

  const { exitCode, json, stderr } = run(dir, ['scan', '--json']);

  // [RED 기대] getSearchPaths(code-scan.js:279-296)가 scopes 값을 문자열로 가정하고 path.resolve에
  // 객체를 넘기므로 TypeError로 죽는다.
  assert.strictEqual(exitCode, 0,
    `[RED expect] 객체 형식 scopes는 스키마 검증을 통과해 exit 0이어야 함, got ${exitCode} / stderr=${JSON.stringify(stderr.slice(0, 400))}`);
  assert.ok(json !== null,
    `[RED expect] stdout이 JSON이어야 함, got ${JSON.stringify(stderr.slice(0, 400))}`);
  assert.ok(!/code_scan_config_invalid|invalid_index/.test(stderr),
    `[RED expect] 객체 형식이 스키마 오류로 거부되면 안 됨, got ${JSON.stringify(stderr.slice(0, 400))}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F7b] TS-075 (S-4) — include/exclude 타입 위반 거부 (3케이스 × 2 레지스트리)
// ═════════════════════════════════════════════════════════════════════════

const BAD_LIST_VALUES = [
  ['문자열 스칼라', 'a/*.ts'],
  ['원소에 비문자열 혼입', ['a', 1]],
  ['객체', {}],
];

for (const field of ['include', 'exclude']) {
  for (const [label, badValue] of BAD_LIST_VALUES) {
    test(`[T080/L1-F7b] TS-075 (S-4): index.json scopes[].${field} — ${label} → invalid_index`, () => {
      const dir = copyFixture('mixed-scope', 'ts075-idx');
      const idx = readJsonFile(indexPath(dir));
      idx.scopes['order-svc'][field] = badValue;
      writeJsonFile(indexPath(dir), idx);

      const { exitCode, json } = run(dir, ['scan', '--json']);
      assert.strictEqual(exitCode, 1,
        `[RED expect] index.json ${field} 타입 위반은 exit 1, got ${exitCode}`);
      assert.strictEqual(json && json.error, 'invalid_index',
        `[RED expect] index.json 측 위반은 invalid_index, got ${JSON.stringify(json)}`);
    });

    test(`[T080/L1-F7b] TS-075 (S-4): code-scan.json scopes[].${field} — ${label} → code_scan_config_invalid`, () => {
      const dir = copyFixture('mixed-scope', 'ts075-cfg');
      const cfg = readJsonFile(configPath(dir));
      cfg.scopes['order-svc'][field] = badValue;
      writeJsonFile(configPath(dir), cfg);

      const { exitCode, json } = run(dir, ['scan', '--json']);
      assert.strictEqual(exitCode, 1,
        `[RED expect] code-scan.json ${field} 타입 위반은 exit 1, got ${exitCode}`);
      assert.strictEqual(json && json.error, 'code_scan_config_invalid',
        `[RED expect] code-scan.json 측 위반은 code_scan_config_invalid, got ${JSON.stringify(json)}`);
    });
  }
}

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F10] TS-016 · TS-017 · TS-018 (S-5) — 스코프 중복 우선순위
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F10] TS-016 (S-5): root 동률 + include만 다른 두 스코프 — 파일이 자기 include 스코프로 귀속', () => {
  const dir = copyFixture('mixed-scope', 'ts016');
  setGlobalHeaderSource(dir, 'manifest');   // 귀속 스코프는 manifest 모드 target 결과에 드러난다

  const expected = {
    'svc/shared/OrderService.java': 'order-svc',
    'svc/shared/OrderRepo.java': 'order-svc',
    'svc/shared/ShipService.java': 'ship-svc',
    'svc/shared/ShipRepo.java': 'ship-svc',
  };

  const got = {};
  for (const rel of Object.keys(expected)) {
    const r = run(dir, ['target', rel, '--json']);
    assert.strictEqual(r.exitCode, 0, `[RED expect] target ${rel} exit 0, got ${r.exitCode} / ${JSON.stringify(r.stdout.slice(0, 200))}`);
    got[rel] = r.json && r.json.scope;
  }

  // [RED 기대] 현행 resolveScope(code-scan.js:557-569)는 root 동률에서 이름 사전순만 보므로
  // 4파일 전부가 order-svc로 귀속된다.
  assert.deepStrictEqual(got, expected,
    `[RED expect] 동률 root에서는 include 매칭 스코프가 승리해야 함, got ${JSON.stringify(got)}`);
});

test('[T080/L1-F10] TS-017 (S-5): 양쪽 include가 동시 매칭 → scope_ambiguous exit 1', () => {
  const cwd = path.join(FIX, 'mixed-scope-ambiguous');   // 읽기 전용 실행만 수행
  const { exitCode, json } = run(cwd, ['target', 'svc/shared/OrderService.java', '--header-source', 'manifest', '--json']);

  // [RED 기대] 현행에는 scope_ambiguous 판정 자체가 없다 — 사전순으로 order-svc가 조용히 승리한다.
  assert.strictEqual(exitCode, 1, `[RED expect] 양쪽 include 매칭은 exit 1, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'scope_ambiguous',
    `[RED expect] error === scope_ambiguous, got ${JSON.stringify(json)}`);
  const detail = JSON.stringify(json || {});
  assert.ok(detail.includes('order-svc') && detail.includes('ship-svc'),
    `[RED expect] detail에 경합 스코프 2개가 실려야 함, got ${detail}`);
});

test('[T080/L1-F10] TS-018 (S-5): include 미사용 tiebreak 픽스처 판정 결과 불변', () => {
  const a = run(path.join(FIX, 'tiebreak', 'order-a'), ['scan', '--json']);
  const b = run(path.join(FIX, 'tiebreak', 'order-b'), ['scan', '--json']);

  assert.strictEqual(a.exitCode, 0, `[회귀] order-a scan exit 0, got ${a.exitCode}`);
  assert.strictEqual(b.exitCode, 0, `[회귀] order-b scan exit 0, got ${b.exitCode}`);
  assert.deepStrictEqual(a.json, b.json,
    '[회귀] layerRules 배열 순서만 다른 두 픽스처의 판정 결과는 동일해야 한다(include 도입이 tiebreak를 흔들면 안 됨)');

  const layers = Object.values(a.json || {}).map(h => h.layer);
  assert.deepStrictEqual(layers, ['layer-foo'],
    `[회귀] 사전순 tie-break 결과(layer-foo)가 불변이어야 함, got ${JSON.stringify(a.json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F8] TS-012 · TS-013 · TS-019 (S-6) — 단일 필터 계약
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F8] TS-012 (S-6): 열거·scaffold 열거·validate 구조 패스·--changed·target 5지점이 동일 집합을 판정', () => {
  const dir = copyFixture('mixed-scope', 'ts012');
  setGlobalHeaderSource(dir, 'manifest');

  const problems = [];

  // ① 열거 (discoverFiles) — scan --json 결과 경로 집합
  const scan = run(dir, ['scan', '--json']);
  const scanned = scannedPaths(scan.json);
  if (JSON.stringify(scanned) !== JSON.stringify(SURVIVORS)) {
    problems.push(`①열거: ${JSON.stringify(scanned)} (기대 ${JSON.stringify(SURVIVORS)})`);
  }
  // 열거에서 빠진 것이지 "헤더가 없어서" 빠진 것이 아님을 확인한다
  const missing = run(dir, ['missing']);
  if (missing.stdout.includes('VendorLegacy.java')) {
    problems.push('①열거: VendorLegacy.java가 열거 대상에 남아 missing으로 보고됨');
  }

  // ② scaffold 열거 (collectDirsWithCodeFiles) — dry-run으로 부작용 없이 관찰
  const scaffold = run(dir, ['scaffold', '--dry-run', '--json']);
  const added = (scaffold.json && scaffold.json.added) || [];
  if (added.some(a => String(a).includes('VendorLegacy.java'))) {
    problems.push(`②scaffold열거: VendorLegacy.java가 매니페스트 등재 대상에 포함됨 — added=${JSON.stringify(added)}`);
  }
  const pruned = (scaffold.json && scaffold.json.pruned) || [];
  if (pruned.length !== 0) problems.push(`②scaffold열거: pruned가 비어야 함, got ${JSON.stringify(pruned)}`);

  // ③ validate 구조 패스 — 커버리지 분모(total)와 위반 목록
  const validate = run(dir, ['validate', '--json']);
  const v = validate.json;
  if (!v || !v.coverage || v.coverage.total !== SURVIVORS.length) {
    problems.push(`③구조패스: coverage.total === ${SURVIVORS.length} 기대, got ${JSON.stringify(v && v.coverage)}`);
  }
  const vendorViolations = ((v && v.violations) || []).filter(x => JSON.stringify(x).includes('VendorLegacy'));
  if (vendorViolations.length !== 0) {
    problems.push(`③구조패스: 필터 탈락 파일이 위반으로 집계됨 — ${JSON.stringify(vendorViolations)}`);
  }

  // ④ --changed
  const changed = run(dir, ['validate', '--changed', ALL_FIXTURE_FILES.join(','), '--json']);
  const skipped = (changed.json && changed.json.skipped) || [];
  const vendorSkip = skipped.find(s => s.file === OUT_OF_SCOPE_FILE);
  if (!vendorSkip || vendorSkip.reason !== 'out_of_scope') {
    problems.push(`④--changed: ${OUT_OF_SCOPE_FILE}가 {reason:'out_of_scope'}로 skip되어야 함, got ${JSON.stringify(skipped)}`);
  }
  const wronglySkipped = SURVIVORS.filter(f => skipped.some(s => s.file === f));
  if (wronglySkipped.length !== 0) problems.push(`④--changed: 생존 파일이 skip됨 — ${JSON.stringify(wronglySkipped)}`);

  // ⑤ target
  for (const f of SURVIVORS) {
    const r = run(dir, ['target', f, '--json']);
    if (!r.json || r.json.write_to !== 'manifest') {
      problems.push(`⑤target: ${f}는 관리 대상이므로 write_to manifest 기대, got ${JSON.stringify(r.json)}`);
    }
  }
  const outR = run(dir, ['target', OUT_OF_SCOPE_FILE, '--json']);
  if (!outR.json || outR.json.write_to !== 'none' || outR.json.reason !== 'out_of_scope') {
    problems.push(`⑤target: ${OUT_OF_SCOPE_FILE}는 {write_to:'none', reason:'out_of_scope'} 기대, got ${JSON.stringify(outR.json)}`);
  }

  assert.deepStrictEqual(problems, [],
    `[RED expect] 5개 적용 지점이 동일 파일 집합(생존 4)을 판정해야 함. 불일치:\n  ${problems.join('\n  ')}`);
});

test('[T080/L2-F8] TS-013 (S-6): 스코프 필터 판정 로직이 isInScope 외 0곳 (산출물 검사)', () => {
  const srcLines = fs.readFileSync(CODE_SCAN_JS, 'utf8').split('\n');

  /** 함수 본문의 [시작, 끝] 0-based 줄 범위를 중괄호 깊이로 확정한다(정규식 아님). */
  function functionRange(name) {
    const S = srcLines.findIndex(l => new RegExp('^\\s*function\\s+' + name + '\\s*\\(').test(l));
    if (S < 0) return null;
    let d = 0;
    for (let i = S; i < srcLines.length; i++) {
      const l = srcLines[i].replace(/\/\/.*$/, '').replace(/(["'`]).*?\1/g, '');
      for (const ch of l) { if (ch === '{') d++; else if (ch === '}') d--; }
      if (i > S && d === 0) return [S, i];
    }
    return [S, srcLines.length - 1];
  }

  // ① 필터 판정 함수는 정확히 1개다
  const defCount = srcLines.filter(l => /^\s*function\s+isInScope\s*\(/.test(l)).length;
  assert.strictEqual(defCount, 1,
    `[RED expect] isInScope는 code-scan.js에 정확히 1회 정의되어야 함, got ${defCount}`);

  // ② 5개 적용 지점이 이것만 호출한다 — 호출 지점이 5곳 이상이어야 한다
  const inScopeRange = functionRange('isInScope');
  const callSites = srcLines
    .map((l, i) => ({ l, i }))
    .filter(({ l, i }) => /\bisInScope\s*\(/.test(l) && !(i >= inScopeRange[0] && i <= inScopeRange[1]));
  assert.ok(callSites.length >= 5,
    `[RED expect] 5개 적용 지점(열거·scaffold열거·구조패스·--changed·target)이 isInScope를 호출해야 함, got ${callSites.length}곳`);

  // ③ 화이트리스트 밖에서 스코프 include 배열에 직접 접근하는 곳이 없다.
  //    허용 영역 = 판정 1곳(isInScope) + 스코프 객체를 만들거나 검증하는 곳(정규화/추론/스키마 검증) +
  //    include 매칭 개수로 동률을 가르는 resolveScopeIn(§3.2.2 (D) ④⑤).
  //    `.includes(`(Array.prototype)는 `\b` 경계로 자동 제외된다.
  const ALLOWED = ['isInScope', 'normalizeConfigScope', 'normalizeIndexScope', 'inferScopes',
                   'loadCodeMap', 'loadConfig', 'resolveScopeIn'];
  const allowedRanges = ALLOWED.map(functionRange).filter(Boolean);
  const inAllowed = i => allowedRanges.some(([s, e]) => i >= s && i <= e);

  const offenders = [];
  srcLines.forEach((raw, i) => {
    if (inAllowed(i)) return;
    const line = raw.replace(/\/\/.*$/, '').replace(/(["'`]).*?\1/g, '');   // 주석·문자열 리터럴 제외
    if (/\.include\b/.test(line)) offenders.push(`${i + 1}: ${raw.trim()}`);
  });

  assert.deepStrictEqual(offenders, [],
    `[RED expect] 스코프 필터 판정은 isInScope 1곳에 봉인되어야 함(중복 판정 로직 0). 위반 줄:\n  ${offenders.join('\n  ')}`);
});

test('[T080/L2-F8] TS-019 (S-6): scan <file> 명시 경로는 include 밖이어도 결과를 반환 (PM Gate 보호)', () => {
  const dir = copyFixture('mixed-scope', 'ts019');
  fs.writeFileSync(path.join(dir, OUT_OF_SCOPE_FILE), INLINE_HEADER_JAVA);   // 인라인 헤더를 실제로 부여

  // (a) 전체 열거에서는 include 필터로 제외된다
  const all = run(dir, ['scan', '--json']);
  assert.strictEqual(all.exitCode, 0, `[RED expect] scan exit 0, got ${all.exitCode} / ${JSON.stringify(all.stderr.slice(0, 300))}`);
  assert.ok(!scannedPaths(all.json).includes(OUT_OF_SCOPE_FILE),
    `[RED expect] 전체 열거에서는 include 밖 파일이 제외되어야 함, got ${JSON.stringify(scannedPaths(all.json))}`);

  // (b) 명시 지정은 사용자 의도이므로 필터보다 우선한다 (pm-review-gate.md:53 단일 파일 조회 보호)
  const one = run(dir, ['scan', OUT_OF_SCOPE_FILE, '--json']);
  assert.strictEqual(one.exitCode, 0, `[RED expect] 명시 경로 scan exit 0, got ${one.exitCode}`);
  assert.deepStrictEqual(scannedPaths(one.json), [OUT_OF_SCOPE_FILE],
    `[RED expect] 명시 경로는 include 밖이어도 결과를 반환해야 함(결과 없음 = @header 누락 오판정 방지), got ${JSON.stringify(one.json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-GOAL] TS-072 · TS-073 · TS-074 (S-19) — 목표달성 통합
//
// TASK 목표 문장("전역 headerSource 한 키가 전 경로를 지배 · 스코프 예외 없음 · 실행당 1값")을
// 반증 가능하게 고정한다. 셋 중 하나라도 깨지면 모드 결정권이 전역 키 1곳 밖으로 샌 것이다.
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-GOAL] TS-072 (S-19): 전역 inline 1회 실행 — 두 스코프 4파일이 모두 동일 모드를 보고', () => {
  const dir = copyFixture('mixed-scope', 'ts072');   // 커밋값 inline 그대로

  const results = SURVIVORS.map(f => ({ f, r: run(dir, ['target', f, '--json']) }));
  const seen = results.map(({ f, r }) => `${f} → ${r.json && r.json.write_to}/${r.json && r.json.reason}`);

  for (const { f, r } of results) {
    assert.strictEqual(r.exitCode, 0, `[RED expect] target ${f} exit 0, got ${r.exitCode}`);
  }
  const modes = new Set(results.map(({ r }) => r.json && r.json.write_to));
  assert.strictEqual(modes.size, 1,
    `[RED expect] 스코프가 다르다는 이유로 모드가 갈리는 파일이 0건이어야 함, got:\n  ${seen.join('\n  ')}`);
  assert.deepStrictEqual(
    results.map(({ r }) => [r.json && r.json.write_to, r.json && r.json.reason]),
    SURVIVORS.map(() => ['inline', 'header_source_inline']),
    `[RED expect] 4건 전부 inline/header_source_inline, got:\n  ${seen.join('\n  ')}`);
});

test('[T080/L2-GOAL] TS-073 (S-19): 같은 실행에서 target·scaffold·validate·scan 4경로의 모드가 일치', () => {
  const dir = copyFixture('mixed-scope', 'ts073');   // 커밋값 inline
  const problems = [];

  // ① target — 4건 전부 inline
  for (const f of SURVIVORS) {
    const r = run(dir, ['target', f, '--json']);
    if (!r.json || r.json.write_to !== 'inline' || r.json.reason !== 'header_source_inline') {
      problems.push(`①target ${f}: ${JSON.stringify(r.json)}`);
    }
  }

  // ② scaffold — no-op. 측정은 "생성 파일 수 0"이 아니라 `.opal/code-map/` 전 파일 무변화 + 사유 보고다
  //    (커밋 픽스처에 매니페스트가 이미 있어 개수로는 측정 불가 — PLAN §3.7.2 TS-073 행).
  const before = snapshotCodeMap(dir);
  const scaffold = run(dir, ['scaffold', '--json']);
  const after = snapshotCodeMap(dir);
  if (scaffold.exitCode !== 0) problems.push(`②scaffold: exit ${scaffold.exitCode} (기대 0 — 설정대로 동작한 것이지 실패가 아님)`);
  if (JSON.stringify(before) !== JSON.stringify(after)) {
    problems.push('②scaffold: inline 모드인데 .opal/code-map/ 하위 파일의 내용·mtime이 변했다');
  }
  const skipped = (scaffold.json && scaffold.json.skipped) || [];
  if (!skipped[0] || skipped[0].reason !== 'header_source_inline') {
    problems.push(`②scaffold: skipped[0].reason === 'header_source_inline' 기대, got ${JSON.stringify(skipped)}`);
  }

  // ③ validate — 결과에 모드가 실리고 커버리지가 인라인만 반영
  const validate = run(dir, ['validate', '--json']);
  const v = validate.json;
  if (!v || v.headerSource !== 'inline') problems.push(`③validate: result.headerSource === 'inline' 기대, got ${JSON.stringify(v && v.headerSource)}`);
  if (v && v.coverage) {
    if (v.coverage.manifest !== 0) problems.push(`③validate: inline 모드에서 coverage.manifest === 0 기대, got ${v.coverage.manifest}`);
    if (v.coverage.covered !== v.coverage.inline) problems.push(`③validate: 합산 폐기 — covered === inline 기대, got ${JSON.stringify(v.coverage)}`);
  } else {
    problems.push(`③validate: coverage 필드 부재, got ${JSON.stringify(v)}`);
  }

  // ④ scan — inline 모드는 _source 키를 붙이지 않는다(두 소스 혼재 0건)
  const scan = run(dir, ['scan', '--json']);
  const withSource = Object.entries(scan.json || {}).filter(([, h]) => h && Object.prototype.hasOwnProperty.call(h, '_source'));
  if (withSource.length !== 0) problems.push(`④scan: _source 키 0건 기대, got ${JSON.stringify(withSource)}`);

  assert.deepStrictEqual(problems, [],
    `[RED expect] 4경로가 보고하는 모드가 서로 일치해야 함(경로마다 갈리지 않는다). 불일치:\n  ${problems.join('\n  ')}`);
});

test('[T080/L2-GOAL] TS-074 (S-19): 전역값 한 줄만 뒤집으면 5경로가 함께 반전된다', () => {
  // 두 복사본은 `.opal/code-scan.json`의 headerSource 값 **한 줄**만 다르다.
  // 같은 트리에서 순차 실행하면 앞선 실행(scaffold)이 트리를 바꿔 대조가 오염되므로 복사본을 분리한다.
  const inlineDir = copyFixture('mixed-scope', 'ts074-i');    // 커밋값 inline
  const manifestDir = copyFixture('mixed-scope', 'ts074-m');
  setGlobalHeaderSource(manifestDir, 'manifest');             // ← 뒤집는 값은 이것 하나뿐

  const problems = [];

  // ① target — 4건이 통째로 반전. 두 스코프 중 어느 쪽도 예외가 되지 않는다.
  for (const f of SURVIVORS) {
    const i = run(inlineDir, ['target', f, '--json']);
    const m = run(manifestDir, ['target', f, '--json']);
    if (!i.json || i.json.write_to !== 'inline') problems.push(`①target(inline) ${f}: ${JSON.stringify(i.json)}`);
    if (!m.json || m.json.write_to !== 'manifest' || m.json.reason !== 'header_source_manifest') {
      problems.push(`①target(manifest) ${f}: ${JSON.stringify(m.json)}`);
    }
  }

  // ② scaffold — inline은 no-op, manifest는 매니페스트 갱신 수행
  const si = run(inlineDir, ['scaffold', '--json']);
  const sm = run(manifestDir, ['scaffold', '--json']);
  const skippedI = (si.json && si.json.skipped) || [];
  const skippedM = (sm.json && sm.json.skipped) || [];
  if (!skippedI[0] || skippedI[0].reason !== 'header_source_inline') {
    problems.push(`②scaffold(inline): skipped[0].reason === 'header_source_inline' 기대, got ${JSON.stringify(skippedI)}`);
  }
  if (sm.exitCode !== 0) problems.push(`②scaffold(manifest): exit 0 기대, got ${sm.exitCode}`);
  if (skippedM.some(s => s && s.reason === 'header_source_inline')) {
    problems.push(`②scaffold(manifest): header_source_inline skip이 남아 있음 — ${JSON.stringify(skippedM)}`);
  }
  const touched = sm.json ? (sm.json.created + sm.json.updated + sm.json.unchanged) : -1;
  if (!(touched >= 2)) problems.push(`②scaffold(manifest): 스코프 2개의 매니페스트를 갱신 대상으로 다뤄야 함, got ${JSON.stringify(sm.json)}`);

  // ③ validate — 모드와 커버리지 축이 함께 반전
  const vi = run(inlineDir, ['validate', '--json']).json;
  const vm = run(manifestDir, ['validate', '--json']).json;
  if (!vi || vi.headerSource !== 'inline') problems.push(`③validate(inline): headerSource 'inline' 기대, got ${JSON.stringify(vi && vi.headerSource)}`);
  if (!vm || vm.headerSource !== 'manifest') problems.push(`③validate(manifest): headerSource 'manifest' 기대, got ${JSON.stringify(vm && vm.headerSource)}`);
  if (vi && vi.coverage && vi.coverage.manifest !== 0) problems.push(`③validate(inline): coverage.manifest 0 기대, got ${vi.coverage.manifest}`);
  if (vm && vm.coverage) {
    if (vm.coverage.inline !== 0) problems.push(`③validate(manifest): coverage.inline 0 기대, got ${vm.coverage.inline}`);
    if (vm.coverage.manifest !== SURVIVORS.length) problems.push(`③validate(manifest): coverage.manifest ${SURVIVORS.length} 기대, got ${vm.coverage.manifest}`);
  }

  // ④ scan — 반대 소스 유래 필드 0건 (두 소스 혼재 0건)
  const scanI = run(inlineDir, ['scan', '--json']).json || {};
  const scanM = run(manifestDir, ['scan', '--json']).json || {};
  if (Object.keys(scanI).length !== 0) {
    problems.push(`④scan(inline): 픽스처에 인라인 @header가 없으므로 결과 0건 기대, got ${JSON.stringify(Object.keys(scanI))}`);
  }
  if (scannedPaths(scanM).join(',') !== SURVIVORS.join(',')) {
    problems.push(`④scan(manifest): 매니페스트 유래 헤더 4건 기대, got ${JSON.stringify(scannedPaths(scanM))}`);
  }
  const orderEntry = Object.entries(scanM).find(([p]) => p.endsWith('OrderService.java'));
  if (!orderEntry || orderEntry[1].description !== '주문 서비스') {
    problems.push(`④scan(manifest): 매니페스트 description이 반환되어야 함, got ${JSON.stringify(orderEntry && orderEntry[1])}`);
  }

  assert.deepStrictEqual(problems, [],
    `[RED expect] 전역 headerSource 한 값만 뒤집으면 target·scaffold·validate·scan이 함께 반전되어야 함. 불일치:\n  ${problems.join('\n  ')}`);
});

test('[T080/L2-GOAL] TS-074 (S-19): 5번째 경로 — hook도 전역값 한 줄에 따라 함께 반전된다', () => {
  // hook 경고 경로는 "관리 대상이지만 매니페스트가 아직 갱신되지 않은 파일"에서만 관측된다
  // (code-map-hook.js:136-139 ⑦⑧ 이탈). 커밋 4파일은 전부 description이 채워진 갱신 완료 상태이므로,
  // 두 복사본에 **동일하게** 미등재 in-scope 파일 1개를 추가한다 — 두 트리 사이의 유일한 차이는
  // 여전히 headerSource 한 줄이다.
  const inlineDir = copyFixture('mixed-scope', 'ts074h-i');
  const manifestDir = copyFixture('mixed-scope', 'ts074h-m');
  const extraRel = 'svc/shared/OrderExtra.java';
  const extraSrc = 'package svc.shared;\npublic class OrderExtra { public void extraOp() {} }\n';
  for (const d of [inlineDir, manifestDir]) fs.writeFileSync(path.join(d, extraRel), extraSrc);
  setGlobalHeaderSource(manifestDir, 'manifest');   // ← 뒤집는 값은 이것 하나뿐

  const payload = d => ({ tool_name: 'Edit', tool_input: { file_path: path.join(d, extraRel) } });

  const hi = runHook(inlineDir, payload(inlineDir));
  const hm = runHook(manifestDir, payload(manifestDir));

  assert.strictEqual(hi.exitCode, 0, `[fail-safe] hook은 항상 exit 0, got ${hi.exitCode}`);
  assert.strictEqual(hm.exitCode, 0, `[fail-safe] hook은 항상 exit 0, got ${hm.exitCode}`);

  // [RED 기대] 현행 hook은 ctx를 직접 조립하며(code-map-hook.js:127) headerSource를 싣지 않는다 —
  // 전역값이 무엇이든 decideTarget이 auto 경로로 판정하므로 두 실행이 갈리지 않는다.
  assert.strictEqual(hi.stdout, '',
    `[RED expect] inline 모드에서는 hook이 무출력 이탈해야 함(⑦ write_to inline), got ${JSON.stringify(hi.stdout.slice(0, 300))}`);
  assert.ok(hm.stdout.trim().length > 0,
    '[RED expect] manifest 모드에서는 hook이 매니페스트 경고 경로로 진입해야 함 (전역값 한 줄이 hook까지 지배)');
  assert.ok(hm.stdout.includes('header_source_manifest'),
    `[RED expect] hook 경고에 reason: header_source_manifest가 실려야 함, got ${JSON.stringify(hm.stdout.slice(0, 400))}`);
});
