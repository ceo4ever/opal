/**
 * @header {
 *   "module": "test-validate",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `validate` 서브명령(5종 위반 검출, 합산 커버리지, --changed, exports 텍스트 대조, draft 정책, 워커 권한 경계) CLI 블랙박스 테스트 (F-006/F-007, 태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-3", "S-13", "S-14", "S-15"]
 * }
 */
//
// [재작업 — 결함 A] Step 19 검증에서 `validate --changed`가 이 저장소 기준선(`missing` 231건)에 막혀
// 모든 태스크가 CLOSE에서 차단되는 구조적 결함이 드러났다. 게이트 목적은 회귀 방지이지 레거시 소급
// 부여가 아니므로, uncovered 위반을 git 기준 newly_uncovered(차단)/pre_existing(비차단) 2종으로
// 분류하는 계약을 아래 TS-077-A-1~5에 RED로 추가한다(캡틴 승인, opal-test-agent mode:red 재작업).
//
//
// TC ↔ TS-ID 매핑 표 (PLAN.md §3.6.5/§3.7.5, TEST-SCENARIO.md S-3/S-13/S-14/S-15):
//
// | TC                                              | TS-ID  |
// |-----------------------------------------------|--------|
// | validate-orphan (file_missing/dir_missing)      | TS-024 |
// | validate-uncovered (no_entry/incomplete)         | TS-024 |
// | validate-conflict (inline_shadowed/mirror_collision) | TS-024 |
// | validate-draft                                   | TS-024, TS-029 |
// | validate-exports-not-found + 3케이스 계약         | TS-024, TS-027 |
// | validate-coverage-sum-no-double-count            | TS-025 |
// | validate-changed-csv-and-stdin                   | TS-026 |
// | validate-clean-exit0-ok-true                      | TS-028 |
// | validate-draft-then-fill-exit0                    | TS-029 |
// | validate-worker-scope (허용/dir/files/layer-domain-module) | TS-030~034 |
//
// exit code 계약(§3.6.2(E)): 0=위반 0건 / 1=스키마·사용법 오류 / 2=위반 ≥1건
//
// RED-first: 현행 code-scan.js에는 validate 서브명령이 없다. 아래 전 테스트는 "Unknown command" exit 1로
// 실패해야 정상이다(exit 2 기대 케이스는 특히 명확히 어긋난다).
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v1.1 2026-07-28 KST: [재작업 — 결함 B] TS-077-B-1~3 추가 — `--changed`가 `exclude`/
//     `excludePatterns`를 적용하지 않는 결함의 RED 증거 (태스크 077, opal-test-agent mode:red)
//   v1.2 2026-07-29 KST: [추가작업 — 결함 D] TS-077-D-1~3 추가 — `scaffold` 열거(`collectDirsWithCodeFiles`,
//     `config.exclude ∪ index.exclude` + `excludePatterns` 적용)와 `validate` 구조 패스 열거
//     (`listCodeFilesInDir`, 확장자만 확인·필터 0건) 간 비대칭으로 인해 scaffold가 정당히 제외한
//     파일이 `files_key_removed`로 오탐되는 결함의 RED 증거 (태스크 077, opal-test-agent mode:red).
//     구현(GREEN)은 이 커밋에 포함하지 않는다 — op-dev-execute 담당.
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
const FIX = path.resolve(__dirname, 'fixtures');

function run(cwd, args, input) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 10000, input,
  });
  const stdout = result.stdout || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr: result.stderr || '', json };
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

// ─────────────────────────────────────────────────────────────────────────
// TS-024: 5종 위반 유형별 검출 + exit 2
// ─────────────────────────────────────────────────────────────────────────

const VIOLATION_CASES = [
  { dir: 'orphan', code: 'orphan', sub: 'file_missing' },
  { dir: 'orphan', code: 'orphan', sub: 'dir_missing' },
  { dir: 'uncovered', code: 'uncovered', sub: 'no_entry' },
  { dir: 'uncovered', code: 'uncovered', sub: 'incomplete' },
  { dir: 'conflict-inline-shadowed', code: 'conflict', sub: 'inline_shadowed' },
  { dir: 'draft', code: 'draft', sub: null },
  { dir: 'exports-missing', code: 'exports_not_found', sub: null },
];

for (const c of VIOLATION_CASES) {
  test(`TS-024 (S-13): violations/${c.dir} — ${c.code}${c.sub ? ':' + c.sub : ''} 검출 + exit 2`, () => {
    const cwd = path.join(FIX, 'violations', c.dir);
    const { exitCode, json } = run(cwd, ['validate', '--json']);

    // [RED 기대] validate 서브명령이 없으므로 "Unknown command" exit 1.
    assert.strictEqual(exitCode, 2, `[RED expect] 위반 존재 → exit 2, got ${exitCode}`);
    assert.ok(json && Array.isArray(json.violations), '[RED expect] violations 배열 존재');
    const hit = json && json.violations.find(v => v.code === c.code && (!c.sub || v.sub === c.sub));
    assert.ok(hit, `[RED expect] ${c.code}${c.sub ? ':' + c.sub : ''} 위반이 검출되어야 함, got ${JSON.stringify(json && json.violations)}`);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// TS-027 (S-3): exports 텍스트 대조 3케이스 계약 (존재/미존재/주석내존재)
// ─────────────────────────────────────────────────────────────────────────

test('TS-027 (S-3): exports 대조 — 존재(통과)/미존재(exports_not_found)/주석내존재(통과, H-14 계약된 한계)', () => {
  const cwd = path.join(FIX, 'violations', 'exports-missing');
  const { exitCode, json } = run(cwd, ['validate', '--json']);

  assert.strictEqual(exitCode, 2, `[RED expect] exit 2 (Missing.java 위반 존재), got ${exitCode}`);
  const violations = (json && json.violations) || [];

  const missingHit = violations.find(v => v.code === 'exports_not_found' && (v.file || '').includes('Missing.java'));
  assert.ok(missingHit, `[RED expect] Missing.java의 ghostExport가 exports_not_found로 검출되어야 함, got ${JSON.stringify(violations)}`);

  const existsHit = violations.find(v => v.code === 'exports_not_found' && (v.file || '').includes('Exists.java'));
  assert.strictEqual(existsHit, undefined, 'Exists.java의 realExport는 통과해야 함(위반 없음)');

  const commentOnlyHit = violations.find(v => v.code === 'exports_not_found' && (v.file || '').includes('CommentOnly.java'));
  assert.strictEqual(commentOnlyHit, undefined,
    '[H-14 계약] 주석 안에만 존재하는 commentedExport는 "통과"로 계약됨(문법 파서 미도입) — 위반으로 잡히면 안 됨');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-025: 커버리지 %가 인라인+지도 합산, 이중 계상 0
// ─────────────────────────────────────────────────────────────────────────

test('TS-025 (S-13): 커버리지 = 인라인 + 지도 합산 (이중 계상 없음)', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { json } = run(cwd, ['validate', '--json']);

  // [RED 기대] validate 서브명령이 없으므로 json이 null이거나 coverage 키가 없다.
  assert.ok(json && json.coverage, '[RED expect] coverage 객체가 존재해야 함');
  assert.strictEqual(typeof json.coverage.total, 'number');
  assert.strictEqual(json.coverage.covered, json.coverage.inline + json.coverage.manifest,
    '[RED expect] covered = inline + manifest (이중 계상 없이 정확히 합)');
  assert.ok(json.coverage.covered <= json.coverage.total,
    '이중 계상이 있다면 covered가 total을 초과할 수 있음 — 초과 금지');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-026: --changed "a,b" / --changed - (stdin) 두 형식, skipped[] 기록
// ─────────────────────────────────────────────────────────────────────────

test('TS-026 (S-13): --changed "csv" — 지정 파일만 판정, 범위 밖은 skipped[]', () => {
  const cwd = path.join(FIX, 'violations', 'draft');
  const { exitCode, json } = run(cwd, ['validate', '--changed', 'svc/mod/Draft.java', '--json']);

  // [RED 기대] validate/--changed 옵션 파싱 자체가 없다.
  assert.strictEqual(exitCode, 2, `[RED expect] 지정 파일 자체가 draft 위반 → exit 2, got ${exitCode}`);
  assert.strictEqual(json && json.mode, 'changed', `[RED expect] mode: "changed", got ${JSON.stringify(json)}`);
});

test('TS-026 (S-13): --changed - (stdin) — 개행 구분 목록 입력', () => {
  const cwd = path.join(FIX, 'violations', 'draft');
  const { exitCode, json } = run(cwd, ['validate', '--changed', '-', '--json'], 'svc/mod/Draft.java\n');

  assert.strictEqual(exitCode, 2, `[RED expect] exit 2, got ${exitCode}`);
  assert.strictEqual(json && json.mode, 'changed', `[RED expect] mode: "changed" (stdin 입력), got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-028: 위반 0 픽스처 → exit 0, ok:true
// ─────────────────────────────────────────────────────────────────────────

test('TS-028 (S-13): violations/clean — 위반 0건, exit 0, ok:true', () => {
  const cwd = path.join(FIX, 'violations', 'clean');
  const { exitCode, json } = run(cwd, ['validate', '--json']);

  // [RED 기대] validate 서브명령이 없으므로 "Unknown command" exit 1 (0이 아님).
  assert.strictEqual(exitCode, 0, `[RED expect] 위반 0건 → exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `[RED expect] ok: true, got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-029 (S-14): scaffold 직후 exit 2(draft N) → 채움 후 exit 0
// ─────────────────────────────────────────────────────────────────────────

test('TS-029 (S-14): draft 상태 exit 2 → description 채운 뒤 exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-draftflow-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'draft'), dir);

  const before = run(dir, ['validate', '--json']);
  // [RED 기대] validate 미구현 — exit 1(Unknown command)로 실패.
  assert.strictEqual(before.exitCode, 2, `[RED expect] scaffold 직후(draft) → exit 2, got ${before.exitCode}`);

  const manifestPath = path.join(dir, '.opal', 'code-map', 'svc', 'mod.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.files['Draft.java'].description = '이제 채워진 설명';
  delete manifest.files['Draft.java'].draft;
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');

  const after = run(dir, ['validate', '--json']);
  assert.strictEqual(after.exitCode, 0, `[RED expect] 채운 후 → exit 0, got ${after.exitCode}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-030~034 (F-007): 워커 권한 경계 집행
// ─────────────────────────────────────────────────────────────────────────

test('TS-030: 허용 필드만 수정된 매니페스트 → 통과(exit 0)', () => {
  const cwd = path.join(FIX, 'violations', 'clean');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.counts && json.counts.worker_scope_violation, 0,
    `[RED expect] worker_scope_violation 0건, got ${JSON.stringify(json && json.counts)}`);
});

test('TS-031: dir 조작 매니페스트 → worker_scope_violation:dir_mismatch, exit 2', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-dir');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `[RED expect] exit 2, got ${exitCode}`);
  const hit = json && json.violations && json.violations.find(v => v.code === 'worker_scope_violation' && v.sub === 'dir_mismatch');
  assert.ok(hit, `[RED expect] dir_mismatch 위반 검출, got ${JSON.stringify(json && json.violations)}`);
});

test('TS-032: files 키 추가/삭제 → files_key_added / files_key_removed', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-files');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `[RED expect] exit 2, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'files_key_added'),
    `[RED expect] files_key_added 검출, got ${JSON.stringify(violations)}`);
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'files_key_removed'),
    `[RED expect] files_key_removed 검출, got ${JSON.stringify(violations)}`);
});

test('TS-033/034: layer/domain/module 침범 매니페스트 — 전용 detail 거부 + 해석 결과 무시', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-layer');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `[RED expect] exit 2, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'layer_in_manifest'),
    `[RED expect] layer_in_manifest 검출, got ${JSON.stringify(violations)}`);
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'domain_in_manifest'),
    `[RED expect] domain_in_manifest 검출, got ${JSON.stringify(violations)}`);
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'module_override'),
    `[RED expect] module_override 검출, got ${JSON.stringify(violations)}`);

  // TS-034: 침범된 package.layer("service")가 scan 결과의 layer를 바꾸면 안 된다 — layerRules(util)가 이겨야 함.
  const scanResult = run(cwd, ['scan', '--json']);
  const key = 'svc/mod/Tampered.java';
  assert.ok(scanResult.json && scanResult.json[key], `[RED expect] ${key} scan 결과 존재`);
  assert.strictEqual(scanResult.json[key] && scanResult.json[key].layer, 'util',
    `[RED expect] 침범된 package.layer("service")가 무시되고 layerRules(util)가 적용되어야 함, got ${JSON.stringify(scanResult.json && scanResult.json[key])}`);
});

// ─────────────────────────────────────────────────────────────────────────
// [재작업 — 결함 A] TS-077-A-1~5: uncovered 2분류 — newly_uncovered(차단)/pre_existing(비차단)
//
// 계약: 파일이 git 기준 신규(untracked/added) 이거나 HEAD 버전엔 @header가 있었는데 현재 없음(회귀) →
//       newly_uncovered — 차단(exit 2). HEAD 버전에도 헤더가 없던 기존 파일 → pre_existing — 비차단
//       (exit 0, 카운트·목록만 보고). git 미사용 환경은 전량 pre_existing + stderr 경고 1줄.
//
// RED-first: 현행 cmdValidate는 git 상태를 전혀 조회하지 않는다. uncovered 위반은 항상
// sub:'no_entry'|'incomplete'로만 분류되고 존재 즉시 무조건 exit 2로 차단한다 — newly_uncovered/
// pre_existing 분류 자체가 없으므로 아래 전 테스트는 실패해야 정상이다(이것이 RED 증거다).
//
// 실 파일시스템 + 실 git 임시 트리만 사용한다(PRINCIPLES §4 "Don't fake it") — 대역 객체/몽키패치 없음.
// 각 테스트는 os.tmpdir() 하위 임시 디렉토리에 독립적으로 `git init`하며, 이 저장소(ai-framework) 자체의
// git 상태는 건드리지 않는다. 임시 디렉토리는 process.on('exit')에서 정리한다(상단 cleanupDirs 재사용).
// ─────────────────────────────────────────────────────────────────────────

function git(cwd, args, input) {
  return spawnSync('git', args, { cwd, encoding: 'utf8', input });
}

function initGitRepo(dir) {
  fs.mkdirSync(dir, { recursive: true });
  git(dir, ['init', '-q']);
  git(dir, ['config', 'user.email', 'red-test@example.invalid']);
  git(dir, ['config', 'user.name', 'RED Test']);
  git(dir, ['config', 'commit.gpgsign', 'false']);
  const r = git(dir, ['commit', '-q', '--allow-empty', '-m', 'init']);
  if (r.status !== 0) throw new Error(`git init commit failed: ${r.stderr}`);
}

function writeGitClassConfig(dir) {
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-scan.json'), JSON.stringify({
    scopes: { svc: 'svc/' },
    extensions: ['.java'],
    exclude: ['node_modules', '.git'],
    excludePatterns: [],
  }, null, 2) + '\n');
}

function headerBlock(mod) {
  return `/**\n * @header {\n *   "module": "${mod}",\n *   "layer": "util",\n *   "domain": "demo",\n *   "description": "테스트용 헤더",\n *   "exports": ["${mod}"]\n * }\n */\n`;
}

function writeJavaFile(dir, relPath, opts) {
  const abs = path.join(dir, relPath);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  const mod = path.basename(relPath, '.java');
  const body = `package svc.mod;\npublic class ${mod} {}\n`;
  fs.writeFileSync(abs, (opts && opts.withHeader ? headerBlock(mod) : '') + body);
  return abs;
}

test('TS-077-A-1 (결함 A 재작업): 신규(untracked) 헤더 없는 파일 → uncovered:newly_uncovered + exit 2', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-gituncov-new-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/BrandNew.java', { withHeader: false });
  // git add 하지 않음 — untracked 상태 유지

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `[RED expect] untracked 신규 헤더 없는 파일 → exit 2, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  const hit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/BrandNew.java');
  assert.ok(hit, `[RED expect] BrandNew.java uncovered 위반이 검출되어야 함, got ${JSON.stringify(violations)}`);
  assert.strictEqual(hit.sub, 'newly_uncovered',
    `[RED expect] untracked 신규 파일은 sub:'newly_uncovered'여야 함(현행은 'no_entry'), got ${JSON.stringify(hit)}`);
  assert.strictEqual(json && json.counts && json.counts.newly_uncovered, 1,
    `[RED expect] counts.newly_uncovered === 1, got ${JSON.stringify(json && json.counts)}`);
  assert.strictEqual(json && json.counts && json.counts.pre_existing, 0,
    `[RED expect] counts.pre_existing === 0, got ${JSON.stringify(json && json.counts)}`);
});

test('TS-077-A-2 (결함 A 재작업): HEAD엔 헤더 있었으나 현재 제거(회귀) → uncovered:newly_uncovered + exit 2', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-gituncov-regress-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  const abs = writeJavaFile(dir, 'svc/mod/HadHeader.java', { withHeader: true });
  git(dir, ['add', '.']);
  const c = git(dir, ['commit', '-q', '-m', 'add HadHeader with header']);
  if (c.status !== 0) throw new Error(`git commit failed: ${c.stderr}`);

  // 헤더 제거(작업트리만 변경, 커밋하지 않음 — HEAD 버전에는 여전히 헤더가 남아 있음)
  fs.writeFileSync(abs, 'package svc.mod;\npublic class HadHeader {}\n');

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `[RED expect] HEAD 대비 헤더 회귀 → exit 2, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  const hit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/HadHeader.java');
  assert.ok(hit, `[RED expect] HadHeader.java uncovered 위반이 검출되어야 함, got ${JSON.stringify(violations)}`);
  assert.strictEqual(hit.sub, 'newly_uncovered',
    `[RED expect] HEAD 대비 헤더 회귀는 sub:'newly_uncovered'여야 함, got ${JSON.stringify(hit)}`);
  assert.strictEqual(json && json.counts && json.counts.newly_uncovered, 1,
    `[RED expect] counts.newly_uncovered === 1, got ${JSON.stringify(json && json.counts)}`);
});

test('TS-077-A-3 (결함 A 재작업): HEAD에도 헤더 없던 기존 파일 → uncovered:pre_existing + exit 0(비차단)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-gituncov-legacy-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/AlwaysBare.java', { withHeader: false });
  git(dir, ['add', '.']);
  const c = git(dir, ['commit', '-q', '-m', 'add AlwaysBare without header (pre-existing legacy state)']);
  if (c.status !== 0) throw new Error(`git commit failed: ${c.stderr}`);
  // 커밋 후 작업트리 변경 없음 — clean 상태

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0,
    `[RED expect] HEAD에도 헤더가 없던 기존 파일은 회귀가 아니므로 비차단 exit 0이어야 함(현행은 무조건 exit 2), got ${exitCode}`);
  assert.strictEqual(json && json.ok, true,
    `[RED expect] pre_existing만 존재할 때 ok:true여야 함, got ${JSON.stringify(json)}`);
  const violations = (json && json.violations) || [];
  const hit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/AlwaysBare.java');
  assert.ok(hit, `[RED expect] AlwaysBare.java가 violations[]에 보고(비차단이지만 노출)되어야 함, got ${JSON.stringify(violations)}`);
  assert.strictEqual(hit.sub, 'pre_existing',
    `[RED expect] sub:'pre_existing'이어야 함(현행은 'no_entry'), got ${JSON.stringify(hit)}`);
  assert.strictEqual(json && json.counts && json.counts.pre_existing, 1,
    `[RED expect] counts.pre_existing === 1, got ${JSON.stringify(json && json.counts)}`);
  assert.strictEqual(json && json.counts && json.counts.newly_uncovered, 0,
    `[RED expect] counts.newly_uncovered === 0, got ${JSON.stringify(json && json.counts)}`);
});

test('TS-077-A-4 (결함 A 재작업): 두 분류 혼재 — newly_uncovered 1건 + pre_existing 1건 → exit 2 + counts 양쪽 노출', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-gituncov-mixed-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/AlwaysBare2.java', { withHeader: false });
  git(dir, ['add', '.']);
  const c = git(dir, ['commit', '-q', '-m', 'add AlwaysBare2 without header']);
  if (c.status !== 0) throw new Error(`git commit failed: ${c.stderr}`);
  writeJavaFile(dir, 'svc/mod/NewOne.java', { withHeader: false });
  // NewOne.java는 git add 하지 않음 — untracked 신규

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2,
    `[RED expect] newly_uncovered가 1건이라도 있으면 전체 exit 2여야 함, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  const newHit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/NewOne.java');
  const oldHit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/AlwaysBare2.java');
  assert.strictEqual(newHit && newHit.sub, 'newly_uncovered',
    `[RED expect] NewOne.java sub:'newly_uncovered', got ${JSON.stringify(newHit)}`);
  assert.strictEqual(oldHit && oldHit.sub, 'pre_existing',
    `[RED expect] AlwaysBare2.java sub:'pre_existing', got ${JSON.stringify(oldHit)}`);
  assert.strictEqual(json && json.counts && json.counts.newly_uncovered, 1,
    `[RED expect] counts.newly_uncovered === 1, got ${JSON.stringify(json && json.counts)}`);
  assert.strictEqual(json && json.counts && json.counts.pre_existing, 1,
    `[RED expect] counts.pre_existing === 1, got ${JSON.stringify(json && json.counts)}`);
});

test('TS-077-A-5 (결함 A 재작업): 비git 트리 — 전량 pre_existing + exit 0 + stderr 경고 1줄', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-gituncov-nogit-'));
  cleanupDirs.push(dir);
  // git init 하지 않음 — 순수 비-git 트리
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/NoGit.java', { withHeader: false });

  const { exitCode, json, stderr } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0,
    `[RED expect] git 미사용 환경은 전량 pre_existing으로 비차단 exit 0이어야 함(현행은 무조건 exit 2), got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `[RED expect] ok:true, got ${JSON.stringify(json)}`);
  const violations = (json && json.violations) || [];
  const hit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/NoGit.java');
  assert.strictEqual(hit && hit.sub, 'pre_existing',
    `[RED expect] 비git 트리는 sub:'pre_existing', got ${JSON.stringify(hit)}`);
  assert.strictEqual(json && json.counts && json.counts.newly_uncovered, 0,
    `[RED expect] counts.newly_uncovered === 0, got ${JSON.stringify(json && json.counts)}`);
  assert.ok(stderr && /git/i.test(stderr),
    `[RED expect] 비git 환경 경고가 stderr에 1줄 이상 출력되어야 함(git 언급 포함), got stderr="${stderr}"`);
});

// ─────────────────────────────────────────────────────────────────────────
// [재작업 — 결함 B] TS-077-B-1~3: `--changed`가 `exclude`/`excludePatterns` 미적용
//
// 실측 근거(PM): 저장소 `.opal/code-scan.json`의 `exclude`에 `fixtures`가 있음에도
// `--changed`에 `.../fixtures/*.md` 등을 넘기면 전체 스캔(walkDir 경유)과 달리 exclude
// 필터가 적용되지 않아 `uncovered:newly_uncovered`로 오판정 → exit 2로 차단된다.
//
// 계약(TASK.md F-6 AC / TEST-SCENARIO S-13): `--changed` 목록 중 (a) 경로 세그먼트 중
// 하나가 `exclude` 디렉토리명과 일치 — `skipped[]`에 사유 `excluded_dir`로 기록,
// (b) `excludePatterns`(와일드카드)에 매치 — 사유 `excluded_pattern`으로 기록. 두 경우
// 모두 counts의 어떤 위반에도 집계되지 않고 exit 0(다른 위반이 없는 한)이어야 한다.
// 대조군(TS-077-B-3): exclude에 걸리지 않는 헤더 없는 신규 파일은 기존 동작대로
// newly_uncovered + exit 2가 유지되어야 한다(회귀 없음 확인용 — 이 케이스는 PASS 기대).
//
// RED-first: 현행 cmdValidate의 --changed 파싱(code-scan.js:1421-1438)은
// `fs.existsSync`·`isFile`·`config.extensions`만 검사하고 `config.exclude`/
// `excludePatterns`를 전혀 조회하지 않는다. 따라서 TS-077-B-1/2는 exit 2로 실패해야
// 정상이다(이것이 RED 증거다). TS-077-B-3은 이미 성립하는 기존 동작이므로 PASS 기대.
// ─────────────────────────────────────────────────────────────────────────

function writeGitClassConfigWithExclude(dir, exclude, excludePatterns) {
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-scan.json'), JSON.stringify({
    scopes: { svc: 'svc/' },
    extensions: ['.java'],
    exclude,
    excludePatterns: excludePatterns || [],
  }, null, 2) + '\n');
}

test('TS-077-B-1 (결함 B): exclude 디렉토리명(fixtures) 하위 --changed 파일 → skipped[excluded_dir] + counts 무영향 + exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-changed-excldir-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfigWithExclude(dir, ['node_modules', '.git', 'fixtures'], []);
  writeJavaFile(dir, 'svc/mod/fixtures/Sample.java', { withHeader: false });
  // git add 하지 않음 — untracked. exclude 디렉토리 세그먼트 매치가 git 분류보다 선행해야 한다.

  const { exitCode, json } = run(dir, ['validate', '--changed', 'svc/mod/fixtures/Sample.java', '--json']);

  assert.strictEqual(exitCode, 0,
    `[RED expect] exclude 디렉토리(fixtures) 하위 경로는 판정에서 제외되어 exit 0이어야 함(현행은 uncovered로 오판정되어 exit 2), got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `[RED expect] ok:true, got ${JSON.stringify(json)}`);
  const violations = (json && json.violations) || [];
  const badHit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/fixtures/Sample.java');
  assert.strictEqual(badHit, undefined,
    `[RED expect] exclude된 경로는 violations[]에 uncovered로 나타나면 안 됨, got ${JSON.stringify(badHit)}`);
  assert.strictEqual(json && json.counts && json.counts.uncovered, 0,
    `[RED expect] counts.uncovered === 0 (exclude된 파일은 어떤 위반에도 집계되지 않음), got ${JSON.stringify(json && json.counts)}`);
  assert.strictEqual(json && json.counts && json.counts.newly_uncovered, 0,
    `[RED expect] counts.newly_uncovered === 0, got ${JSON.stringify(json && json.counts)}`);

  const skipped = (json && json.skipped) || [];
  const skipHit = skipped.find(s => (typeof s === 'object' && s !== null) && s.file === 'svc/mod/fixtures/Sample.java');
  assert.ok(skipHit,
    `[RED expect] skipped[]에 { file: 'svc/mod/fixtures/Sample.java', reason: 'excluded_dir' } 형태 항목이 기록되어야 함(현행 skipped는 존재 여부/확장자/스코프만 체크하고 exclude는 전혀 반영하지 않음), got ${JSON.stringify(skipped)}`);
  assert.strictEqual(skipHit && skipHit.reason, 'excluded_dir',
    `[RED expect] 사유는 'excluded_dir'이어야 함, got ${JSON.stringify(skipHit)}`);
});

test('TS-077-B-2 (결함 B): excludePatterns 매치 --changed 파일 → skipped[excluded_pattern] + counts 무영향 + exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-changed-exclpat-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfigWithExclude(dir, ['node_modules', '.git'], ['*.generated.java']);
  const abs = path.join(dir, 'svc', 'mod', 'Sample.generated.java');
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, 'package svc.mod;\npublic class Sample {}\n'); // 헤더 없음
  // git add 하지 않음 — untracked.

  const { exitCode, json } = run(dir, ['validate', '--changed', 'svc/mod/Sample.generated.java', '--json']);

  assert.strictEqual(exitCode, 0,
    `[RED expect] excludePatterns(*.generated.java) 매치 경로는 판정에서 제외되어 exit 0이어야 함(현행은 uncovered로 오판정되어 exit 2), got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `[RED expect] ok:true, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.counts && json.counts.uncovered, 0,
    `[RED expect] counts.uncovered === 0, got ${JSON.stringify(json && json.counts)}`);

  const skipped = (json && json.skipped) || [];
  const skipHit = skipped.find(s => (typeof s === 'object' && s !== null) && s.file === 'svc/mod/Sample.generated.java');
  assert.ok(skipHit,
    `[RED expect] skipped[]에 { file: 'svc/mod/Sample.generated.java', reason: 'excluded_pattern' } 형태 항목이 기록되어야 함, got ${JSON.stringify(skipped)}`);
  assert.strictEqual(skipHit && skipHit.reason, 'excluded_pattern',
    `[RED expect] 사유는 'excluded_pattern'이어야 함, got ${JSON.stringify(skipHit)}`);
});

test('TS-077-B-3 (대조군 — 회귀 없음 확인, PASS 기대): exclude에 걸리지 않는 --changed 신규 헤더 없는 파일 → 기존대로 newly_uncovered + exit 2', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-changed-control-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfigWithExclude(dir, ['node_modules', '.git'], ['*.generated.java']);
  writeJavaFile(dir, 'svc/mod/Control.java', { withHeader: false });
  // git add 하지 않음 — untracked, exclude/excludePatterns 어느 쪽에도 매치되지 않음.

  const { exitCode, json } = run(dir, ['validate', '--changed', 'svc/mod/Control.java', '--json']);

  assert.strictEqual(exitCode, 2,
    `대조군: exclude 미매치 신규 헤더 없는 파일은 여전히 차단되어야 함(회귀 없음 확인), got ${exitCode}`);
  const violations = (json && json.violations) || [];
  const hit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/Control.java');
  assert.ok(hit, `대조군: Control.java가 uncovered로 검출되어야 함, got ${JSON.stringify(violations)}`);
  assert.strictEqual(hit && hit.sub, 'newly_uncovered',
    `대조군: sub:'newly_uncovered'여야 함(기존 결함 A 계약 불변), got ${JSON.stringify(hit)}`);
  assert.strictEqual(json && json.counts && json.counts.newly_uncovered, 1,
    `대조군: counts.newly_uncovered === 1, got ${JSON.stringify(json && json.counts)}`);
  const skipped = (json && json.skipped) || [];
  assert.strictEqual(skipped.length, 0,
    `대조군: exclude 미매치 파일은 skipped[]에 나타나면 안 됨, got ${JSON.stringify(skipped)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// [추가작업 — 결함 D] TS-077-D-1~3: scaffold 열거 vs validate 구조 패스 필터 비대칭
//
// 결함(PM 확인): `scaffold`의 `collectDirsWithCodeFiles`(code-scan.js:1223-1239)는 디렉토리
// 제외 `config.exclude ∪ index.exclude` + 파일 제외 `config.excludePatterns`를 모두 적용해
// 매니페스트 `files{}`를 만드는데, `validate` 구조 패스의 `listCodeFilesInDir`(code-scan.js:1430-1438)는
// 확장자만 확인하고 이 세 필터를 전혀 적용하지 않는다. 그 결과 scaffold가 정당하게 제외한
// 디스크 파일이 `worker_scope_violation/files_key_removed`(code-scan.js:1580-1584)로 오탐된다.
//
// 픽스처 `fixtures/violations/worker-scope-exclude-symmetry/`(자기완결 트리, 매니페스트 3종을
// 정적으로 배치 — 실제 `scaffold` CLI를 구동하지 않고 "scaffold가 만들었을 상태"를 직접 재현):
//   - svc/mod    : Normal.java(매니페스트 키 존재, 정상) + Excluded.generated.java
//                  (`excludePatterns: ["*.generated.java"]` 매치, 키 없음 — req1)
//   - svc/vendor : Nested.java, 매니페스트 files:{}. "vendor"는 `index.json`의 `exclude`에만
//                  존재(`config.exclude`에는 없음) — index.exclude 단독 격리(req3, union 검증)
//   - svc/thirdparty : Old.java, 매니페스트 files:{}. "thirdparty"는 `config.exclude`에만
//                  존재(`index.exclude`에는 없음) — config.exclude 단독 격리(req2)
// Nested.java/Old.java는 인라인 `@header`로 자기완결시켜 무관한 `uncovered` 잡음을 배제했다
// (구조 위반 3종만 격리 관측하기 위함 — `uncovered`는 이 결함의 검증 대상이 아니다).
//
// 실측(RED 확인, PM 검증 시점): 위 픽스처에서 `validate --json` → `exit 2`,
// `counts.worker_scope_violation: 3`, `violations`에 `files_key_removed`가 정확히
// Excluded.generated.java(svc/mod.json)/Old.java(svc/thirdparty.json)/Nested.java(svc/vendor.json)
// 3건 — 전부 오탐이어야 정상인데 현재 코드는 3건 모두 진짜 위반으로 보고한다(RED).
// ─────────────────────────────────────────────────────────────────────────

test('TS-077-D-1 (결함 D 신규, Case A — 대칭 불변식): scaffold가 exclude 3종(excludePatterns/config.exclude/index.exclude)으로 정당히 제외한 파일은 files_key_removed로 오탐되면 안 됨(구조 위반 0건)', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-exclude-symmetry');
  const { json } = run(cwd, ['validate', '--json']);

  const violations = (json && json.violations) || [];
  const orphanHits = violations.filter(v => v.code === 'orphan');
  const addedHits = violations.filter(v => v.sub === 'files_key_added');
  const removedHits = violations.filter(v => v.sub === 'files_key_removed');

  assert.strictEqual(orphanHits.length, 0, `orphan은 0건이어야 함(무관한 잡음), got ${JSON.stringify(orphanHits)}`);
  assert.strictEqual(addedHits.length, 0, `files_key_added는 0건이어야 함(무관한 잡음), got ${JSON.stringify(addedHits)}`);
  assert.strictEqual(removedHits.length, 0,
    `[RED expect] excludePatterns/config.exclude/index.exclude로 정당히 제외된 3개 파일 모두 ` +
    `files_key_removed 오탐 없이 통과해야 함(현행 listCodeFilesInDir는 필터 0건 적용이라 3건 전부 오탐), ` +
    `got ${JSON.stringify(removedHits)}`);
});

test('TS-077-D-2 (결함 D 신규, Case C — 요구계약 3 전용): index.exclude로만 제외되는 디렉토리(svc/vendor)의 파일은 files_key_removed로 오탐되지 않아야 함(config.exclude와의 union 여부 검증)', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-exclude-symmetry');
  const { json } = run(cwd, ['validate', '--json']);

  const violations = (json && json.violations) || [];
  const hit = violations.find(v =>
    v.sub === 'files_key_removed' && v.key === 'Nested.java' && v.manifest === '.opal/code-map/svc/vendor.json');

  assert.strictEqual(hit, undefined,
    `[RED expect] "vendor"는 index.exclude 전용(config.exclude에는 없음)이므로 scaffold ∪ 규약상 ` +
    `제외 대상 — files_key_removed가 발생하면 안 됨(현행은 index.exclude를 전혀 조회하지 않아 오탐), ` +
    `got ${JSON.stringify(hit)}`);
});

test('TS-077-D-3 (결함 D 신규, Case B — 대조군, PASS 기대): 제외 대상 아닌 신규 미등재 파일은 여전히 files_key_removed로 정상 검출된다(게이트 무력화 방지)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-exclsym-control-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'worker-scope-exclude-symmetry'), dir);
  fs.writeFileSync(path.join(dir, 'svc', 'mod', 'Rogue.java'), 'package svc.mod;\npublic class Rogue {}\n');
  // Rogue.java는 excludePatterns/config.exclude/index.exclude 어느 것에도 매치되지 않는 순수 신규 파일.

  const { exitCode, json } = run(dir, ['validate', '--json']);

  assert.strictEqual(exitCode, 2, `대조군: 위반이 존재하므로 exit 2여야 함, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  const hit = violations.find(v =>
    v.sub === 'files_key_removed' && v.key === 'Rogue.java' && v.manifest === '.opal/code-map/svc/mod.json');
  assert.ok(hit,
    `대조군: 제외 대상이 아닌 신규 파일 Rogue.java는 files_key_removed로 정상 검출되어야 함(검출기 자체가 ` +
    `무력화되지 않았음을 확인 — 게이트 무력화 방지), got ${JSON.stringify(violations)}`);
});
