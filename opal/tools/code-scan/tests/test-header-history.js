/**
 * @header {
 *   "module": "test-header-history",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "`code-scan validate` 이력 누적 비차단 감지기(header_history) CLI 블랙박스 테스트 — 표기 6종 판정·distinct 임계값 경계·counts 가산성·exit code 불변·description/note 진입 가드·채택 end-to-end·특수문자 파싱을 검증한다",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "107",
 *   "scenarios": ["TS-010", "TS-011", "TS-012", "TS-013", "TS-014", "TS-015", "TS-016", "TS-017", "TS-018", "TS-019", "TS-041", "TS-042", "TS-043", "TS-052", "TS-053", "TS-054", "TS-055", "TS-056", "TS-057"]
 * }
 */
//
// [RED-first — 태스크 107 F-002]
// 이 파일 작성 시점에는 code-scan.js에 header_history 감지기가 존재하지 않는다(PLAN §3.2.1 신규
// 파일 목록, PLAN §3.2.2 설계는 아직 미구현). 따라서 아래 신 계약 케이스(countTaskTags 판정을
// 전제하는 테스트 전부)는 지금 FAIL해야 정상이다 — 구현(GREEN)은 op-dev-execute가 별도 Step에서
// 수행한다(작성자≠구현자, `~/.opal/references/harness/red-first.md` §2).
// [MUST] GREEN/fix 루핑 중 이 파일 수정 금지(동 문서 §3).
//
// TC ↔ TS-ID 매핑:
// | TC 묶음                                   | TS-ID  |
// |--------------------------------------------|--------|
// | 이력 패턴만 있는 프로젝트 — exit 0/counts>=1 | TS-010 |
// | 이력 패턴 + 실제 차단 위반 동시              | TS-011 |
// | violations[] 5키 형태                       | TS-012 |
// | 오탐 후보 세트 A (F-005 등)                  | TS-013 |
// | 오탐 후보 세트 B (400/127.0.0.1 등)          | TS-014 |
// | 진성 표기 4형태                              | TS-015 |
// | distinct 1/2 경계                            | TS-016 |
// | 기존 counts 9키 회귀                         | TS-017 |
// | --version 불변                               | TS-018 |
// | description 깨끗 + note만 이력               | TS-019 |
// | description/note 부재·공란 4종 가드          | TS-041 |
// | 채택 end-to-end (§4.2 기준 헤더 통과)        | TS-042 |
// | 특수문자(따옴표/역슬래시/개행/한글) 파싱     | TS-043 |

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');

function run(cwd, args, input) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 10000, input,
    env: { ...process.env, OPAL_HOME: path.join(os.tmpdir(), 'opal-t107-home-absent') },
  });
  const stdout = result.stdout || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr: result.stderr || '', json, error: result.error };
}

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

function mkProject(tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t107-hh-${tag}-`));
  cleanupDirs.push(dir);
  fs.mkdirSync(path.join(dir, 'src'), { recursive: true });
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-scan.json'), JSON.stringify({
    headerSource: 'inline',
    scopes: { app: 'src/' },
    extensions: ['.js'],
    exclude: ['node_modules', '.git'],
    excludePatterns: [],
  }, null, 2) + '\n');
  return dir;
}

/** 표준 포맷(header-standard.md §3)의 @header JSONDoc 블록을 만든다. 필드는 obj 그대로 직렬화한다. */
function buildHeaderBlock(obj) {
  const json = JSON.stringify(obj, null, 2);
  const body = json.split('\n').map(l => ' * ' + l).join('\n');
  return '/**\n * @header ' + body.replace(/^ \* /, '') + '\n */\n';
}

/**
 * src/ 아래 파일 1개를 작성한다. header가 null이면 @header 블록 자체를 생략한다(uncovered 유발용).
 * header 객체에 description/note 키가 없으면 그 필드를 아예 쓰지 않는다(부재 재현, TS-041).
 */
function writeSrcFile(dir, relName, header) {
  const abs = path.join(dir, 'src', relName);
  const mod = path.basename(relName, '.js');
  let content = '';
  if (header !== null) content += buildHeaderBlock(header);
  content += `function ${mod}() { return '${mod}'; }\nmodule.exports = { ${mod} };\n`;
  fs.writeFileSync(abs, content);
  return abs;
}

function baseHeader(extra) {
  return Object.assign({
    module: 'sample-mod',
    layer: 'util',
    domain: 'demo',
    description: '기본 설명 — 태스크 번호를 포함하지 않는다',
    exports: ['sample-mod'],
  }, extra || {});
}

/**
 * manifest 모드 프로젝트를 mkdtempSync로 런타임 생성한다(GC-C004, TS-057 — 커밋 픽스처를
 * 늘리지 않기 위해 tests/fixtures/violations/draft와 동형 구조를 코드로 재현한다).
 * fileEntry는 `.opal/code-map/svc/mod.json`의 `files["Target.java"]` 값이다.
 */
function mkManifestProject(tag, fileEntry) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t107-hh-manifest-${tag}-`));
  cleanupDirs.push(dir);
  fs.mkdirSync(path.join(dir, 'svc', 'mod'), { recursive: true });
  fs.mkdirSync(path.join(dir, '.opal', 'code-map', 'svc'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-scan.json'), JSON.stringify({
    headerSource: 'manifest',
    scopes: { svc: 'svc/' },
    extensions: ['.java'],
    exclude: ['node_modules', '.git'],
    excludePatterns: [],
  }, null, 2) + '\n');
  fs.writeFileSync(path.join(dir, '.opal', 'code-map', 'index.json'), JSON.stringify({
    version: 1, status: 'reviewed',
    scopes: { svc: { root: 'svc/', anchors: [], stripPrefix: [] } },
    domains: { demo: { paths: ['svc/**'] } },
    layerRules: [{ match: '**/mod/**', layer: 'util' }],
    exclude: [],
  }, null, 2) + '\n');
  fs.writeFileSync(path.join(dir, '.opal', 'code-map', 'svc', 'mod.json'), JSON.stringify({
    version: 1, scope: 'svc', dir: 'svc/mod',
    files: { 'Target.java': fileEntry },
  }, null, 2) + '\n');
  fs.writeFileSync(path.join(dir, 'svc', 'mod', 'Target.java'),
    'package svc.mod;\npublic class Target {}\n');
  return dir;
}

function git(cwd, args) { return spawnSync('git', args, { cwd, encoding: 'utf8' }); }
function initGitRepo(dir) {
  git(dir, ['init', '-q']);
  git(dir, ['config', 'user.email', 'red-test@example.invalid']);
  git(dir, ['config', 'user.name', 'RED Test']);
  git(dir, ['config', 'commit.gpgsign', 'false']);
  const r = git(dir, ['commit', '-q', '--allow-empty', '-m', 'init']);
  if (r.status !== 0) throw new Error(`git init commit failed: ${r.stderr}`);
}

// ═══════════════════════════════════════════════════════════════════════
// TS-010: 이력 패턴만 있는 프로젝트 — exit 0 · ok:true · counts.header_history >= 1
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-010: description 이력 누적(distinct2) 단독 위반 — exit 0 + ok:true + counts.header_history>=1', () => {
  const dir = mkProject('ts010');
  writeSrcFile(dir, 'HistOnly.js', baseHeader({
    module: 'hist-only',
    exports: ['hist-only'],
    description: '이 파일은 [T088] 최초 도입되고 [T104] 개정되었다',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.ok(json, `validate --json 출력이 파싱 가능해야 함, stdout=${JSON.stringify(json)}`);
  assert.strictEqual(exitCode, 0, `이력 위반은 비차단이므로 exit 0, got ${exitCode}`);
  assert.strictEqual(json.ok, true, `ok:true, got ${JSON.stringify(json && json.ok)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number',
    `counts.header_history가 number 키로 존재해야 함(현재 미구현이면 undefined), got ${JSON.stringify(json.counts)}`);
  assert.ok(json.counts.header_history >= 1, `counts.header_history >= 1, got ${JSON.stringify(json.counts)}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/HistOnly.js');
  assert.ok(hit, `header_history 위반이 검출되어야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(hit.sub, 'description', `sub:'description', got ${JSON.stringify(hit)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-011: 이력 패턴 + 실제 차단 위반(uncovered:newly_uncovered) 동시 —
//   exit 2이되 사유는 차단 위반이며 header_history는 blockingViolations에 없다.
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-011: header_history + uncovered:newly_uncovered 혼재 — exit 2는 uncovered 때문이지 header_history 때문이 아니다', () => {
  const dir = mkProject('ts011');
  initGitRepo(dir);
  writeSrcFile(dir, 'HistOnly.js', baseHeader({
    module: 'hist-only', exports: ['hist-only'],
    description: '이 파일은 [T088] 최초 도입되고 [T104] 개정되었다',
  }));
  // 커밋해 두어 HistOnly.js는 uncovered로 잡히지 않게 한다(이력 위반만 순수하게 남긴다).
  git(dir, ['add', '.']);
  git(dir, ['commit', '-q', '-m', 'add HistOnly']);
  // 실제 차단 위반: untracked + 헤더 없는 신규 파일 → uncovered:newly_uncovered
  writeSrcFile(dir, 'BrandNew.js', null);

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `newly_uncovered가 있으면 전체 exit 2, got ${exitCode}`);
  assert.strictEqual(json.ok, false, `ok:false, got ${JSON.stringify(json && json.ok)}`);
  const uncoveredHit = json.violations.find(v => v.code === 'uncovered' && v.file === 'src/BrandNew.js');
  assert.ok(uncoveredHit, `BrandNew.js uncovered 위반 검출, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(uncoveredHit.sub, 'newly_uncovered', `sub:'newly_uncovered', got ${JSON.stringify(uncoveredHit)}`);
  const histHit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/HistOnly.js');
  assert.ok(histHit, `HistOnly.js header_history 위반도 함께 검출, got ${JSON.stringify(json.violations)}`);
  // header_history 자체는 비차단임을 대조 검증한다: HistOnly.js 단독(TS-010, 이력 위반만 있는 상태)은
  // exit 0이었다 — 즉 이 케이스의 exit 2는 오로지 newly_uncovered에서 온다.
  const onlyHistDir = mkProject('ts011-control');
  writeSrcFile(onlyHistDir, 'HistOnly.js', baseHeader({
    module: 'hist-only', exports: ['hist-only'],
    description: '이 파일은 [T088] 최초 도입되고 [T104] 개정되었다',
  }));
  const control = run(onlyHistDir, ['validate', '--json']);
  assert.strictEqual(control.exitCode, 0, `대조군(이력 위반만) exit 0 — header_history가 blockingViolations에 없음을 증명, got ${control.exitCode}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-012: violations[]의 header_history 항목이 code·sub·file·detail·tasks 5키를 갖는다
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-012: header_history violation 항목이 code·sub·file·detail·tasks 5키를 갖는다', () => {
  const dir = mkProject('ts012');
  writeSrcFile(dir, 'HistOnly.js', baseHeader({
    module: 'hist-only', exports: ['hist-only'],
    description: '이 파일은 [T088] 최초 도입되고 [T104] 개정되었다',
  }));
  const { json } = run(dir, ['validate', '--json']);
  const hit = json && json.violations && json.violations.find(v => v.code === 'header_history');
  assert.ok(hit, `header_history 위반 검출 필요, got ${JSON.stringify(json && json.violations)}`);
  for (const key of ['code', 'sub', 'file', 'detail', 'tasks']) {
    assert.ok(Object.prototype.hasOwnProperty.call(hit, key), `키 '${key}' 존재해야 함, got ${JSON.stringify(hit)}`);
  }
  assert.strictEqual(hit.code, 'header_history');
  assert.strictEqual(typeof hit.tasks, 'number', `tasks는 number, got ${JSON.stringify(hit)}`);
  assert.ok(hit.tasks >= 2, `tasks >= 2(임계값), got ${JSON.stringify(hit)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-013: 오탐 후보 세트 A — 기능번호/시나리오id/범위 나열 → 전건 미탐지
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-013: 기능번호·시나리오id·범위나열(F-005 등) 전건 미탐지 — distinct는 단발 출처(080) 1개뿐', () => {
  const dir = mkProject('ts013');
  writeSrcFile(dir, 'FalsePosA.js', baseHeader({
    module: 'false-pos-a', exports: ['false-pos-a'],
    description: '(F-005/F-006/F-007, 태스크 080) 정리 완료. 관련 항목 TS-024/025/026 및 TS-201~209, R-16, QA-018 참고.',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `오탐 후보만 있으면 exit 0, got ${exitCode}`);
  assert.strictEqual(typeof json.counts.header_history, 'number',
    `counts.header_history가 number로 존재(미구현이면 undefined), got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.header_history, 0, `counts.header_history === 0, got ${JSON.stringify(json.counts)}`);
  const hit = json.violations.find(v => v.code === 'header_history');
  assert.ok(!hit, `header_history 위반이 없어야 함, got ${JSON.stringify(json.violations)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-014: 오탐 후보 세트 B — HTTP상태/IP/경로:줄번호/수량표기 → 전건 미탐지
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-014: HTTP상태·IP·경로:줄번호·수량표기(400/127.0.0.1/*.js:455/340 passed) 전건 미탐지', () => {
  const dir = mkProject('ts014');
  writeSrcFile(dir, 'FalsePosB.js', baseHeader({
    module: 'false-pos-b', exports: ['false-pos-b'],
    description: '빈값이면 400 응답. 서버 127.0.0.1:7823에서 code-scan.js:455 확인. 결과 340 passed.',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `오탐 후보만 있으면 exit 0, got ${exitCode}`);
  assert.strictEqual(typeof json.counts.header_history, 'number',
    `counts.header_history가 number로 존재(미구현이면 undefined), got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.header_history, 0, `counts.header_history === 0, got ${JSON.stringify(json.counts)}`);
  const hit = json.violations.find(v => v.code === 'header_history');
  assert.ok(!hit, `header_history 위반이 없어야 함, got ${JSON.stringify(json.violations)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-015: 진성 표기 4형태 — 전건 탐지
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-015: 진성 표기 4형태(대괄호 마커/콜론 나열/TASK 표기/맨숫자 나열) 전건 탐지', () => {
  const dir = mkProject('ts015');
  const cases = [
    { file: 'GenuineA.js', description: '[T061] 최초 도입. [T103] 리팩터. [T103/R-16] 후속 보강.' },
    { file: 'GenuineB.js', description: '014 Phase 4: 최초 작업. 016: 개선 진행. 017: 마무리.' },
    { file: 'GenuineC.js', description: 'TASK 077 / TASK 080 동시 적용.' },
    { file: 'GenuineD.js', description: '077 자산 유지 및 088 정리 완료.' },
  ];
  for (const c of cases) {
    writeSrcFile(dir, c.file, baseHeader({ module: c.file.replace('.js', ''), exports: [c.file.replace('.js', '')], description: c.description }));
  }
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `이력 위반은 전부 비차단이므로 exit 0, got ${exitCode}`);
  for (const c of cases) {
    const hit = json.violations.find(v => v.code === 'header_history' && v.file === `src/${c.file}`);
    assert.ok(hit, `${c.file} — header_history 탐지되어야 함("${c.description}"), got ${JSON.stringify(json.violations)}`);
  }
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.header_history, cases.length, `counts.header_history === ${cases.length}, got ${JSON.stringify(json.counts)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-016: distinct 1 → 미탐지 / distinct 2 → 탐지 (양방향 임계값 경계)
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-016: distinct 1(단발 출처) 미탐지 / distinct 2 탐지 — 임계값 2 양방향', () => {
  const dir = mkProject('ts016');
  writeSrcFile(dir, 'Distinct1.js', baseHeader({
    module: 'distinct1', exports: ['distinct1'], description: '[T103] 단일 변경 기록.',
  }));
  writeSrcFile(dir, 'Distinct2.js', baseHeader({
    module: 'distinct2', exports: ['distinct2'], description: '[T061] 최초 도입. [T103] 갱신.',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `이력 위반은 비차단, got ${exitCode}`);
  const hit1 = json.violations.find(v => v.code === 'header_history' && v.file === 'src/Distinct1.js');
  assert.ok(!hit1, `distinct1(단발 출처)은 미탐지여야 함, got ${JSON.stringify(json.violations)}`);
  const hit2 = json.violations.find(v => v.code === 'header_history' && v.file === 'src/Distinct2.js');
  assert.ok(hit2, `distinct2는 탐지되어야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.header_history, 1, `counts.header_history === 1(Distinct2.js만), got ${JSON.stringify(json.counts)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-017: 기존 counts 9키 회귀 — additive 확장 전제(값·키셋 불변)
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-017 (baseline PASS 기대): 기존 counts 9키가 전건 존재하고 clean 프로젝트에서 값이 전부 0이다', () => {
  const dir = mkProject('ts017');
  writeSrcFile(dir, 'Clean.js', baseHeader({ module: 'clean', exports: ['clean'], description: '태스크 번호가 없는 깨끗한 설명.' }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `clean 프로젝트는 exit 0, got ${exitCode}`);
  const EXISTING_9_KEYS = [
    'orphan', 'uncovered', 'conflict', 'draft', 'exports_not_found',
    'worker_scope_violation', 'newly_uncovered', 'pre_existing', 'manifest_oversize',
  ];
  for (const k of EXISTING_9_KEYS) {
    assert.ok(Object.prototype.hasOwnProperty.call(json.counts, k), `counts.${k} 존재해야 함, got ${JSON.stringify(json.counts)}`);
    assert.strictEqual(json.counts[k], 0, `clean 프로젝트에서 counts.${k} === 0, got ${JSON.stringify(json.counts)}`);
  }
});

// ═══════════════════════════════════════════════════════════════════════
// TS-018: `code-scan --version` 불변 (핀 2건 통과 전제 — VERSION 상향 금지)
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-018 (baseline PASS 기대): code-scan --version === "code-scan v1.6.0" (VERSION 상수 불변)', () => {
  const dir = mkProject('ts018');
  const { exitCode, stdout } = run(dir, ['--version']);
  assert.strictEqual(exitCode, 0, `--version exit 0, got ${exitCode}`);
  assert.strictEqual(stdout.trim(), 'code-scan v1.6.0', `버전 문자열 불변, got ${JSON.stringify(stdout)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-019: description 깨끗 + note에만 이력 — sub:'note'만 검출, sub:'description' 없음
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-019: description 깨끗 + note만 이력 누적 — sub:"note"로만 검출된다', () => {
  const dir = mkProject('ts019');
  writeSrcFile(dir, 'NoteOnly.js', baseHeader({
    module: 'note-only', exports: ['note-only'],
    description: '설정 파일을 읽어 검증 규칙을 적용한다.',
    note: '[T061] 최초 작성 [T103] 개정.',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `이력 위반은 비차단, got ${exitCode}`);
  const noteHit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/NoteOnly.js' && v.sub === 'note');
  assert.ok(noteHit, `sub:'note' 위반이 검출되어야 함, got ${JSON.stringify(json.violations)}`);
  const descHit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/NoteOnly.js' && v.sub === 'description');
  assert.ok(!descHit, `sub:'description' 항목은 없어야 함, got ${JSON.stringify(json.violations)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-041: [경계] description/note 부재·공란 4종 — 예외·크래시 0건
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-041 (a): description 키 부재 — 크래시 없음 + header_history 미탐지(unrelated incomplete 위반은 별개)', () => {
  const dir = mkProject('ts041a');
  // description 키를 아예 쓰지 않는다 — 기존 required-field 검사('incomplete')는 F-002 범위 밖의
  // 별개 로직이라 이 케이스에서 별도로 트리거될 수 있으나, 여기서 검증하는 것은 오직
  // countTaskTags 진입 가드가 undefined 입력에서 예외 없이 동작하는지다.
  const header = { module: 'no-desc', layer: 'util', domain: 'demo', exports: ['no-desc'] };
  writeSrcFile(dir, 'NoDesc.js', header);
  const { exitCode, json, stderr, error } = run(dir, ['validate', '--json']);
  assert.strictEqual(error, undefined, `spawnSync 자체 에러 없음, got ${error}`);
  assert.ok(exitCode === 0 || exitCode === 2, `크래시(비정상 종료) 없이 0 또는 2로 종료, got ${exitCode}`);
  assert.ok(json, `JSON 출력이 파싱 가능해야 함(크래시 시 미출력), stdout 존재 여부와 무관하게 실패 시 근거 첨부, stderr=${stderr}`);
  assert.ok(!/TypeError|Cannot read|is not a function/.test(stderr), `크래시 신호(TypeError 등) 없음, stderr=${stderr}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/NoDesc.js');
  assert.ok(!hit, `description 부재 시 header_history 미탐지, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
});

test('[T107/F-002] TS-041 (b): description: "" — 크래시 없음 + header_history 미탐지 + exit 0', () => {
  const dir = mkProject('ts041b');
  writeSrcFile(dir, 'EmptyDesc.js', baseHeader({ module: 'empty-desc', exports: ['empty-desc'], description: '' }));
  const { exitCode, json, stderr } = run(dir, ['validate', '--json']);
  assert.ok(!/TypeError|Cannot read|is not a function/.test(stderr), `크래시 신호 없음, stderr=${stderr}`);
  assert.strictEqual(exitCode, 0, `description:"" 은 required 통과(''!==undefined) — 다른 위반 없으면 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/EmptyDesc.js');
  assert.ok(!hit, `header_history 미탐지, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
});

test('[T107/F-002] TS-041 (c): note 키 부재 — 크래시 없음 + header_history 미탐지 + exit 0', () => {
  const dir = mkProject('ts041c');
  writeSrcFile(dir, 'NoNote.js', baseHeader({ module: 'no-note', exports: ['no-note'] })); // note 필드 자체 없음
  const { exitCode, json, stderr } = run(dir, ['validate', '--json']);
  assert.ok(!/TypeError|Cannot read|is not a function/.test(stderr), `크래시 신호 없음, stderr=${stderr}`);
  assert.strictEqual(exitCode, 0, `note는 선택 필드 — 부재는 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/NoNote.js');
  assert.ok(!hit, `header_history 미탐지, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
});

test('[T107/F-002] TS-041 (d): note: "" — 크래시 없음 + header_history 미탐지 + exit 0', () => {
  const dir = mkProject('ts041d');
  writeSrcFile(dir, 'EmptyNote.js', baseHeader({ module: 'empty-note', exports: ['empty-note'], note: '' }));
  const { exitCode, json, stderr } = run(dir, ['validate', '--json']);
  assert.ok(!/TypeError|Cannot read|is not a function/.test(stderr), `크래시 신호 없음, stderr=${stderr}`);
  assert.strictEqual(exitCode, 0, `note:"" 은 위반 아님 — exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/EmptyNote.js');
  assert.ok(!hit, `header_history 미탐지, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-042: [채택 end-to-end] §4.2 기준대로 쓴 헤더가 감지기를 통과한다
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-042: §4.2 기준(「담는 것」만 채운) @header — header_history 미탐지 + exit 0 + description 태스크 번호 0개', () => {
  const dir = mkProject('ts042');
  writeSrcFile(dir, 'Compliant.js', baseHeader({
    module: 'compliant', exports: ['compliant'],
    // 「담는 것」: 파일의 현재 역할 한 줄. 「담지 않는 것」: 변경 이력·태스크 번호.
    description: '설정 파일을 읽어 스코프별 검증 규칙을 계산하고 결과를 반환하는 순수 유틸리티',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `기준 준수 헤더는 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/Compliant.js');
  assert.ok(!hit, `header_history 미탐지, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.header_history, 0, `counts.header_history === 0, got ${JSON.stringify(json.counts)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-043: [경계] 한글 따옴표·역슬래시·개행이 든 description이 파싱된다
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-043: 큰따옴표·역슬래시·이스케이프 개행·한글이 섞인 description이 예외 없이 파싱된다', () => {
  const dir = mkProject('ts043');
  const tricky = '설정에서 "기본값"을 읽고 경로\\구분자를 정규화한다.\n두 번째 줄: 특수문자 검증용.';
  writeSrcFile(dir, 'Tricky.js', baseHeader({ module: 'tricky', exports: ['tricky'], description: tricky }));
  const { exitCode, json, stderr } = run(dir, ['validate', '--json']);
  assert.ok(!/TypeError|Cannot read|is not a function/.test(stderr), `크래시 신호 없음, stderr=${stderr}`);
  assert.strictEqual(exitCode, 0, `특수문자 description도 정상 파싱되어 exit 0, got ${exitCode}, stderr=${stderr}`);
  const uncoveredHit = json.violations.find(v => v.code === 'uncovered' && v.sub === 'newly_uncovered' && v.file === 'src/Tricky.js');
  assert.ok(!uncoveredHit, `파싱 성공 시 newly_uncovered가 나면 안 됨(파싱 실패의 대리 신호), got ${JSON.stringify(json.violations)}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/Tricky.js');
  assert.ok(!hit, `태스크 번호가 없는 특수문자 description은 header_history 미탐지, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-052: changelog 엔트리 1개만 있어도 탐지 — countTaskTags 임계값 미적용, 비차단(exit 0)
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-052: changelog 엔트리 1개 — sub:"changelog" 탐지 + counts.header_history>=1 + exit 0', () => {
  const dir = mkProject('ts052');
  writeSrcFile(dir, 'ChangelogOne.js', baseHeader({
    module: 'changelog-one', exports: ['changelog-one'],
    changelog: ['[T107] 최초 도입'],
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `changelog 위반은 비차단이므로 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/ChangelogOne.js');
  assert.ok(hit, `changelog 엔트리 1개도 위반으로 검출되어야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(hit.sub, 'undeclared_field', `sub:'undeclared_field', got ${JSON.stringify(hit)}`);
  assert.strictEqual(typeof json.counts.header_history, 'number', `counts.header_history number, got ${JSON.stringify(json.counts)}`);
  assert.ok(json.counts.header_history >= 1, `counts.header_history >= 1, got ${JSON.stringify(json.counts)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-053: changelog 키 부재 / 빈 배열 — 미탐지
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-053 (a): changelog 키 부재 — header_history(changelog) 미탐지', () => {
  const dir = mkProject('ts053a');
  writeSrcFile(dir, 'NoChangelog.js', baseHeader({ module: 'no-changelog', exports: ['no-changelog'] }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `위반 없으므로 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.sub === 'undeclared_field' && v.file === 'src/NoChangelog.js');
  assert.ok(!hit, `changelog 키 부재 시 미탐지, got ${JSON.stringify(json.violations)}`);
});

test('[T107/F-002] TS-053 (b): changelog: [] — header_history(changelog) 미탐지', () => {
  const dir = mkProject('ts053b');
  writeSrcFile(dir, 'EmptyChangelog.js', baseHeader({ module: 'empty-changelog', exports: ['empty-changelog'], changelog: [] }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `위반 없으므로 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.sub === 'undeclared_field' && v.file === 'src/EmptyChangelog.js');
  assert.ok(!hit, `changelog:[] 시 미탐지, got ${JSON.stringify(json.violations)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-054: description/note는 깨끗하고 changelog만 있음 — sub:'changelog'만 검출
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-054: description/note 깨끗 + changelog만 이력 — sub:"changelog"로만 검출된다', () => {
  const dir = mkProject('ts054');
  writeSrcFile(dir, 'ChangelogOnly.js', baseHeader({
    module: 'changelog-only', exports: ['changelog-only'],
    description: '설정 파일을 읽어 검증 규칙을 적용한다.',
    note: '',
    changelog: ['[T061] 최초 작성', '[T103] 개정'],
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `changelog 위반은 비차단, got ${exitCode}`);
  const clHit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/ChangelogOnly.js' && v.sub === 'undeclared_field');
  assert.ok(clHit, `sub:'changelog' 위반이 검출되어야 함, got ${JSON.stringify(json.violations)}`);
  const descHit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/ChangelogOnly.js' && v.sub === 'description');
  assert.ok(!descHit, `sub:'description' 항목은 없어야 함, got ${JSON.stringify(json.violations)}`);
  const noteHit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/ChangelogOnly.js' && v.sub === 'note');
  assert.ok(!noteHit, `sub:'note' 항목은 없어야 함, got ${JSON.stringify(json.violations)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-055: "이름을 불문한다" 실증 — changelog·history·revisions·임의 이름(updates) 각각 탐지
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-055: history/revisions/updates 등 임의 이름의 이력 필드도 sub:"undeclared_field"로 탐지된다', () => {
  for (const fieldName of ['changelog', 'history', 'revisions', 'updates']) {
    const dir = mkProject(`ts055-${fieldName}`);
    writeSrcFile(dir, 'NamedField.js', baseHeader({
      module: `named-${fieldName}`, exports: [`named-${fieldName}`],
      [fieldName]: ['[T107] 최초 도입'],
    }));
    const { exitCode, json } = run(dir, ['validate', '--json']);
    assert.strictEqual(exitCode, 0, `${fieldName}: 비차단이므로 exit 0, got ${exitCode}`);
    const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/NamedField.js');
    assert.ok(hit, `${fieldName}: 이름 불문 탐지되어야 함, got ${JSON.stringify(json.violations)}`);
    assert.strictEqual(hit.sub, 'undeclared_field', `${fieldName}: sub:'undeclared_field', got ${JSON.stringify(hit)}`);
    assert.strictEqual(hit.detail, fieldName, `${fieldName}: detail에 필드명이 실려야 함, got ${JSON.stringify(hit)}`);
  }
});

// ═══════════════════════════════════════════════════════════════════════
// TS-056: task/scenarios는 §2 예외 — 미탐지. 선언 8필드만 있는 깨끗한 헤더도 미탐지.
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-056 (a): task/scenarios만 있는 헤더 — header_history 미탐지(§2 예외)', () => {
  const dir = mkProject('ts056a');
  writeSrcFile(dir, 'TaskScenarios.js', baseHeader({
    module: 'task-scenarios', exports: ['task-scenarios'],
    task: '107',
    scenarios: ['TS-001', 'TS-002'],
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `위반 없으므로 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/TaskScenarios.js');
  assert.ok(!hit, `task/scenarios는 예외이므로 미탐지, got ${JSON.stringify(json.violations)}`);
});

test('[T107/F-002] TS-056 (b): 선언 8필드만 있는 깨끗한 헤더 — header_history 미탐지', () => {
  const dir = mkProject('ts056b');
  writeSrcFile(dir, 'CleanHeader.js', baseHeader({
    module: 'clean-header', layer: 'util', domain: 'demo',
    description: '이력 없는 깨끗한 설명',
    exports: ['clean-header'], depends: [], note: '', feature: 'F-001',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `위반 없으므로 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/CleanHeader.js');
  assert.ok(!hit, `선언 8필드만 있으면 미탐지, got ${JSON.stringify(json.violations)}`);
});

// ═══════════════════════════════════════════════════════════════════════
// TS-057: manifest 모드 §7.2 전용 필드 draft — undeclared_field 오탐 방지 (GC-C004)
// ═══════════════════════════════════════════════════════════════════════

test('[T107/F-002] TS-057 (a): manifest 모드 draft:true — header_history/undeclared_field 미탐지(draft 위반은 그대로 발생)', () => {
  const dir = mkManifestProject('ts057a', { description: '', exports: [], draft: true });
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `draft는 차단 위반이므로 exit 2 (header_history는 비차단이지만 draft가 남아있음), got ${exitCode}`);
  const hhHit = json.violations.find(v => v.code === 'header_history' && v.file === 'svc/mod/Target.java');
  assert.ok(!hhHit, `draft는 §7.2 도구 관할 필드이므로 undeclared_field 미탐지, got ${JSON.stringify(json.violations)}`);
  const draftHit = json.violations.find(v => v.code === 'draft' && v.file === 'svc/mod/Target.java');
  assert.ok(draftHit, `draft 위반 자체는 별개 계약으로 그대로 발생해야 함, got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(json.counts.draft, 1, `counts.draft === 1, got ${json.counts.draft}`);
  assert.strictEqual(json.counts.header_history, 0, `counts.header_history === 0, got ${json.counts.header_history}`);
});

// TS-057 (b): manifest 모드 resolveHeader()는 WORKER_FIELDS(description/exports/depends/note/
// feature) + module/layer/domain/draft만 `fe`에서 `resolved`로 복사한다(code-scan.js:1552-1561) —
// 화이트리스트 밖 임의 키(예: changelog)는 files[] 엔트리에 적어도 애초에 `resolved`에 실리지 않으므로
// undeclared_field 판정 대상 자체가 되지 않는다(이 기제는 GC-C004와 무관한 기존 동작이며, 판정 루프
// 수정으로 새로 생기거나 없어지지 않는다 — resolveHeader를 고치는 것은 금지 범위 밖이다). 따라서
// "manifest 엔트리에 진짜 미정의 필드를 넣으면 탐지된다"는 시나리오는 이 구조에서 실행 불가능하다.
// 대신 예외가 "draft라는 값" 전체가 아니라 "manifest 모드"로 정확히 게이트되어 있음을, 같은 이름의
// 필드를 **inline** 모드 @header에 직접 써서 증명한다: mode 조건(`!isInlineMode`)이 없다면 inline
// 모드의 임의 필드명 `draft`도 그냥 통과했을 것이나, 실제로는 undeclared_field로 탐지되어야 한다.
test('[T107/F-002] TS-057 (b): inline 모드에서 임의 필드명 "draft"는 예외 미적용 — undeclared_field로 그대로 탐지된다 (mode 게이트 정밀도 증명)', () => {
  const dir = mkProject('ts057b');
  writeSrcFile(dir, 'InlineDraftField.js', baseHeader({
    module: 'inline-draft-field', exports: ['inline-draft-field'],
    draft: '[T107] 임의로 붙인 draft라는 이름의 인라인 필드 — 매니페스트 draft와 무관',
  }));
  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `header_history는 비차단이므로 exit 0, got ${exitCode}`);
  const hit = json.violations.find(v => v.code === 'header_history' && v.file === 'src/InlineDraftField.js');
  assert.ok(hit, `inline 모드에서는 draft 예외가 적용되지 않아야 함(mode 게이트), got ${JSON.stringify(json.violations)}`);
  assert.strictEqual(hit.sub, 'undeclared_field', `sub:'undeclared_field', got ${JSON.stringify(hit)}`);
  assert.strictEqual(hit.detail, 'draft', `detail:'draft', got ${JSON.stringify(hit)}`);
});
