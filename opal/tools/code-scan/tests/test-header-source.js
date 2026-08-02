/**
 * @header {
 *   "module": "test-header-source",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — headerSource 전역 단일 키 계약: 전 명령 차단 게이트(header_source_unset)·무효값 3경로(auto 특례/CLI/config)·우선순위 2층(CLI > 전역)·스코프 오버라이드 부재 대칭 부정 단언 CLI 블랙박스 테스트 (F-001, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-1", "S-20", "S-21"]
 * }
 */
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.1.5, TEST-SCENARIO.md §4):
//
// | 케이스 프리픽스      | TS-ID            | S-ID | 계층 | 검증 명제                                        |
// |---------------------|------------------|------|------|-------------------------------------------------|
// | [T080/L2-F2]        | TS-001, TS-002   | S-1  | L2   | 13커맨드 전량 exit 1 + header_source_unset + stderr 3줄 |
// | [T080/L2-F2b]       | TS-007           | S-1  | L2   | --help/--version은 게이트 이전 처리 → exit 0      |
// | [T080/L2-F12b]      | TS-002, TS-008   | S-1, S-20 | L2 | 미설정 vs 깨진 설정 구분(code_scan_config_invalid) · USAGE 품질 |
// | [T080/L1-F1b]       | TS-003           | S-20 | L1   | auto 명시 거부 + 마이그레이션 힌트 특례            |
// | [T080/L1-F1c]       | TS-009, TS-065   | S-20 | L1   | 일반 무효값 — where: cli/config · 힌트 없음        |
// | [T080/L1-F1]        | TS-004, TS-006   | S-21 | L1   | CLI 플래그 단독 성립 · CLI > 전역 2층 우선순위      |
// | [T080/L1-F1d]       | TS-005, TS-069   | S-21 | L1   | 스코프 오버라이드 부재 — index.json/code-scan.json 대칭 쌍 |
//
// [MUST] red-first.md §4 — 공개 인터페이스(실 CLI subprocess의 exit code · stdout JSON · stderr)로만
// 검증한다. code-scan.js를 require하여 내부 함수를 직접 호출하지 않는다.
// [MUST] red-first.md §2 — 이 파일은 opal-test-agent(mode:red)가 작성한다. GREEN 구현은 별도 워커가
// Step 3~7에서 수행한다. 현재 code-scan.js에는 resolveHeaderSource·게이트·--header-source 플래그가
// 전혀 없고 loadConfig가 무효값을 'auto'로 조용히 폴백하므로(code-scan.js:196-201) 아래 전 테스트는
// 실패해야 정상이다 — 이것이 RED 증거다.
//
// 픽스처는 커밋 상태를 수정하지 않는다. 사전 조작이 필요한 케이스는 전부 임시 복사본 오버레이를 쓴다
// (makeHeaderSourceFixture 패턴, test-resolve-header.js:74-83).
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
const FIX = path.resolve(__dirname, 'fixtures');

// ─────────────────────────────────────────────────────────────────────────
// 공통 헬퍼 — 실 subprocess + 실 파일시스템만 사용(mock/monkeypatch 없음)
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

function mkTemp(tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t080-${tag}-`));
  cleanupDirs.push(dir);
  return dir;
}

/** 커밋 픽스처를 임시 복사본으로 뜬다 — 원본은 절대 수정하지 않는다. */
function copyFixture(fixtureRelPath, tag) {
  const dir = mkTemp(tag);
  copyDirRecursive(path.join(FIX, fixtureRelPath), dir);
  return dir;
}

function readJsonFile(abs) { return JSON.parse(fs.readFileSync(abs, 'utf8')); }
function writeJsonFile(abs, obj) { fs.writeFileSync(abs, JSON.stringify(obj, null, 2) + '\n'); }

function configPath(dir) { return path.join(dir, '.opal', 'code-scan.json'); }
function indexPath(dir) { return path.join(dir, '.opal', 'code-map', 'index.json'); }

/** code-scan.js CLI 블랙박스 실행. */
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

function stderrLines(stderr) {
  return stderr.split('\n').map(s => s.trim()).filter(Boolean);
}

/** 에러 페이로드에서 "사람이 읽는 안내 문구"만 모은다 — detail(입력값 그대로)은 제외한다. */
function guidanceText(json) {
  if (!json || typeof json !== 'object') return '';
  return ['hint', 'fix', 'migration', 'doc'].map(k => (typeof json[k] === 'string' ? json[k] : '')).join(' ');
}

const SAMPLE_TS = [
  '/**',
  ' * @header {',
  ' *   "module": "sample",',
  ' *   "layer": "util",',
  ' *   "domain": "fixture",',
  ' *   "description": "임시 트리 샘플 — 게이트 검증용",',
  ' *   "exports": ["sample"]',
  ' * }',
  ' */',
  'export function sample() { return 1; }',
  '',
].join('\n');

/**
 * `.opal/` 마커만 있고 `.opal/code-scan.json`이 **없는** 프로젝트 트리.
 * findProjectRoot(code-scan.js:180-193)는 `.opal` 디렉토리를 루트 마커로 인식한다.
 */
function makeUnsetTree(tag = 'unset') {
  const dir = mkTemp(tag);
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'src'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'src', 'sample.ts'), SAMPLE_TS);
  return dir;
}

/** `.opal/code-scan.json`을 임의 내용(문자열 또는 객체)으로 두는 트리. */
function makeConfigTree(configContent, tag) {
  const dir = makeUnsetTree(tag);
  const body = typeof configContent === 'string' ? configContent : JSON.stringify(configContent, null, 2) + '\n';
  fs.writeFileSync(configPath(dir), body);
  return dir;
}

// code-scan의 13 서브명령 전량 (help/version은 커맨드가 아니라 메타 출력 — 게이트 이전 처리).
// 인자가 필수인 명령에는 인자를 준다. discover/scaffold는 --dry-run으로 부작용을 차단한다
// (게이트가 아직 없는 RED 상태에서도 임시 트리를 오염시키지 않기 위함).
const ALL_COMMANDS = [
  ['scan', '--json'],
  ['domain', '--json'],
  ['layer', '--json'],
  ['search', 'sample', '--json'],
  ['exports', 'sample', '--json'],
  ['summary'],
  ['depends', 'sample'],
  ['missing'],
  ['discover', '--dry-run', '--json'],
  ['scaffold', '--dry-run', '--json'],
  ['target', 'src/sample.ts', '--json'],
  ['validate', '--json'],
  ['feature', 'F-1', '--json'],
];

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F2] TS-001 · TS-002 (S-1) — 전 명령 차단 게이트
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F2] TS-001 (S-1): headerSource 미설정 트리 — 13커맨드 전량 exit 1 + header_source_unset', () => {
  const dir = makeUnsetTree('ts001');
  assert.strictEqual(ALL_COMMANDS.length, 13, '검사 대상은 code-scan 13 서브명령 전량이어야 한다');

  const failures = [];
  for (const args of ALL_COMMANDS) {
    const { exitCode, json, stdout } = run(dir, args);
    if (exitCode !== 1) failures.push(`${args[0]}: exit=${exitCode} (기대 1)`);
    else if (!json || json.ok !== false || json.error !== 'header_source_unset') {
      failures.push(`${args[0]}: stdout=${JSON.stringify(stdout.slice(0, 160))} (기대 {"ok":false,"error":"header_source_unset"})`);
    }
  }

  // [RED 기대] 현행 code-scan.js에는 main() 게이트가 없다 — 대부분의 명령이 exit 0으로 정상 수행된다.
  assert.deepStrictEqual(failures, [],
    `[RED expect] 13커맨드가 동일 에러·동일 exit code로 차단되어야 함. 위반:\n  ${failures.join('\n  ')}`);
});

test('[T080/L2-F2] TS-002 (S-1): 미설정 차단 시 stderr에 사유·해결·근거 문서 3줄이 나간다', () => {
  const dir = makeUnsetTree('ts002');
  const { exitCode, stderr, json } = run(dir, ['scan', '--json']);

  assert.strictEqual(exitCode, 1, `[RED expect] 미설정 트리의 scan은 exit 1, got ${exitCode}`);
  const lines = stderrLines(stderr);
  assert.ok(lines.length >= 3,
    `[RED expect] stderr는 사유·해결·근거 3줄 이상이어야 함(brain_tool.py:790-792가 stderr만 detail로 전달), got ${lines.length}줄: ${JSON.stringify(stderr)}`);
  assert.ok(stderr.includes('header_source_unset'),
    `[RED expect] stderr에 에러 코드가 포함되어야 함, got ${JSON.stringify(stderr)}`);
  assert.ok(stderr.includes('header-standard.md'),
    `[RED expect] stderr에 근거 문서 경로(~/.opal/references/header-standard.md §7)가 포함되어야 함, got ${JSON.stringify(stderr)}`);
  // stdout JSON 무오염 — 기계 소비자(brain_tool.py:793 json.loads) 보호
  assert.ok(json !== null && json.error === 'header_source_unset',
    '[RED expect] stdout은 순수 JSON 에러 객체여야 하고 stderr 문구가 섞이면 안 된다');
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F2b] TS-007 (S-1) — help/version은 게이트 이전
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F2b] TS-007 (S-1): --help / --version은 미설정 상태에서도 exit 0', () => {
  const dir = makeUnsetTree('ts007');

  const help = run(dir, ['--help']);
  assert.strictEqual(help.exitCode, 0, `[회귀] --help는 설정 없이도 exit 0, got ${help.exitCode}`);
  assert.ok(help.stdout.includes('code-scan'), '--help는 USAGE를 출력해야 한다');

  const version = run(dir, ['--version']);
  assert.strictEqual(version.exitCode, 0, `[회귀] --version은 설정 없이도 exit 0, got ${version.exitCode}`);
  assert.ok(/code-scan v\d+\.\d+\.\d+/.test(version.stdout),
    `--version은 버전 문자열을 출력해야 한다, got ${JSON.stringify(version.stdout)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F12b] TS-008 · TS-002 (S-1, S-20) — 미설정 vs 깨진 설정 구분
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F12b] TS-008 (S-20): 깨진 JSON 설정 → code_scan_config_invalid (미설정과 구분)', () => {
  const dir = makeConfigTree('{ "headerSource": ', 'ts008');   // 의도적 파싱 실패
  const { exitCode, json, stderr } = run(dir, ['scan', '--json']);

  // [RED 기대] 현행 loadConfig의 `catch { return DEFAULT_CONFIG; }`(code-scan.js:210)는 파싱 실패와
  // 파일 부재를 구분하지 못하고 조용히 기본값으로 진행한다 → exit 0.
  assert.strictEqual(exitCode, 1, `[RED expect] 깨진 설정은 exit 1, got ${exitCode}`);
  assert.ok(json !== null, `[RED expect] stdout이 JSON 에러 객체여야 함, got ${JSON.stringify(stderr)}`);
  assert.strictEqual(json && json.error, 'code_scan_config_invalid',
    `[RED expect] 깨진 설정은 header_source_unset이 아니라 code_scan_config_invalid로 구분되어야 함, got ${JSON.stringify(json)}`);
  assert.notStrictEqual(json && json.error, 'header_source_unset',
    '[RED expect] "미설정"과 "깨진 설정"이 같은 코드로 뭉개지면 안 된다');
});

test('[T080/L2-F12b] TS-002 (S-1): USAGE가 --header-source 옵션과 2택 값 도메인을 안내한다', () => {
  const dir = makeUnsetTree('ts002b');
  const { exitCode, stdout } = run(dir, ['--help']);

  // 미설정 사용자가 사용법을 볼 수 있어야 한다는 F-12② 취지 — 게이트 이전 처리(TS-007)와 짝이다.
  assert.strictEqual(exitCode, 0, `--help는 설정 없이도 exit 0, got ${exitCode}`);
  assert.ok(stdout.includes('--header-source'),
    '[RED expect] USAGE에 --header-source <inline|manifest> 옵션이 안내되어야 함');
  assert.ok(!/"headerSource"\s*:\s*"auto"/.test(stdout),
    `[RED expect] USAGE 설정 예시에 구형 값 auto가 남아 있으면 안 된다(code-scan.js:108), got ${JSON.stringify(stdout.slice(-500))}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F1b] TS-003 (S-20) — auto 명시 거부 + 마이그레이션 힌트 특례
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F1b] TS-003 (S-20): headerSource "auto" → header_source_invalid + detail "auto" + 마이그레이션 힌트', () => {
  const dir = makeConfigTree({ headerSource: 'auto', extensions: ['.ts'], scopes: {} }, 'ts003');
  const { exitCode, json } = run(dir, ['scan', '--json']);

  // [RED 기대] 현행 loadConfig(code-scan.js:196-201)는 'auto'를 유효값으로 허용한다 → exit 0.
  assert.strictEqual(exitCode, 1, `[RED expect] auto는 구형 값이므로 exit 1, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'header_source_invalid',
    `[RED expect] error === header_source_invalid, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.detail, 'auto',
    `[RED expect] detail에 입력값 "auto"가 실려야 함, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.where, 'config',
    `[RED expect] 값의 출처 where === "config", got ${JSON.stringify(json)}`);

  // 특례: auto만 전용 마이그레이션 안내를 갖는다(§3.1.4). detail 이외의 안내 문구에 auto가 언급된다.
  assert.ok(guidanceText(json).includes('auto'),
    `[RED expect] auto 전용 마이그레이션 힌트가 안내 문구(hint/fix)에 있어야 함, got ${JSON.stringify(json)}`);
  assert.ok(guidanceText(json).includes('inline') && guidanceText(json).includes('manifest'),
    `[RED expect] 힌트가 2택(inline/manifest) 중 하나로 통일하라고 안내해야 함, got ${JSON.stringify(json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F1c] TS-009 · TS-065 (S-20) — 일반 무효값 경로 (힌트 없음 + where 표기)
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F1c] TS-009 (S-20): --header-source bogus → header_source_invalid + where "cli" + 힌트 없음', () => {
  const dir = makeConfigTree({ headerSource: 'inline', extensions: ['.ts'], scopes: {} }, 'ts009');
  const { exitCode, json } = run(dir, ['scan', '--header-source', 'bogus', '--json']);

  // [RED 기대] 현행 parseArgs(code-scan.js:131-173)에 --header-source 플래그 자체가 없다 →
  // 미지 인자로 무시되고 전역 inline으로 정상 수행(exit 0)된다.
  assert.strictEqual(exitCode, 1, `[RED expect] CLI 무효값은 exit 1, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'header_source_invalid',
    `[RED expect] error === header_source_invalid, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.detail, 'bogus',
    `[RED expect] detail === "bogus", got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.where, 'cli',
    `[RED expect] 무효값의 출처가 CLI임을 where로 식별할 수 있어야 함, got ${JSON.stringify(json)}`);
  assert.ok(!guidanceText(json).includes('auto'),
    `[RED expect] 일반 무효값에는 auto 마이그레이션 힌트가 붙지 않는다(auto 특례와 구분), got ${JSON.stringify(json)}`);
});

test('[T080/L1-F1c] TS-065 (S-20): config headerSource "bogus" → header_source_invalid + where "config" + stdout 무오염', () => {
  const dir = makeConfigTree({ headerSource: 'bogus', extensions: ['.ts'], scopes: {} }, 'ts065');
  const { exitCode, json, stdout } = run(dir, ['scan', '--json']);

  // [RED 기대] 077 TS-046(test-resolve-header.js:406-419)은 bogus → auto 폴백 + exit 0을 단언했다.
  // 그 계약이 여기서 반전된다 — 조용한 폴백은 사라지고 명시 거부가 된다.
  assert.strictEqual(exitCode, 1, `[RED expect] config 무효값은 폴백하지 않고 exit 1, got ${exitCode}`);
  assert.ok(json !== null, `[RED expect] stdout이 순수 JSON이어야 함(경고 문구 혼입 금지), got ${JSON.stringify(stdout)}`);
  assert.strictEqual(json && json.error, 'header_source_invalid',
    `[RED expect] error === header_source_invalid, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.detail, 'bogus',
    `[RED expect] detail === "bogus", got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.where, 'config',
    `[RED expect] where === "config", got ${JSON.stringify(json)}`);
  assert.ok(!guidanceText(json).includes('auto'),
    `[RED expect] 임의 무효값에는 마이그레이션 힌트가 붙지 않는다, got ${JSON.stringify(json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F1] TS-004 · TS-006 (S-21) — 우선순위 2층 (CLI > 전역)
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F1] TS-004 (S-21): 미설정 프로젝트 + --header-source inline → scan exit 0', () => {
  const dir = makeUnsetTree('ts004');
  const { exitCode, json, stderr } = run(dir, ['scan', '--header-source', 'inline', '--json']);

  // [RED 기대] --header-source 플래그가 없으므로 현행에서는 우연히 exit 0이 되지만,
  // 아래 결과 단언(인라인 헤더 1건 반환)까지 함께 만족해야 한다.
  assert.strictEqual(exitCode, 0,
    `[RED expect] CLI 플래그가 전역 config 부재를 대체해 게이트를 통과해야 함, got ${exitCode} / stderr=${JSON.stringify(stderr)}`);
  assert.ok(json !== null && Object.keys(json).length === 1,
    `[RED expect] inline 모드에서 인라인 @header 보유 1파일이 반환되어야 함, got ${JSON.stringify(json)}`);
  const only = json && Object.values(json)[0];
  assert.strictEqual(only && only.module, 'sample',
    `[RED expect] 인라인 헤더 값이 그대로 반환되어야 함, got ${JSON.stringify(json)}`);
  assert.ok(!(only && Object.prototype.hasOwnProperty.call(only, '_source')),
    '[RED expect] inline 모드는 _source 키를 붙이지 않는다(조회 8커맨드 골든 보존)');
});

test('[T080/L1-F1] TS-006 (S-21): 전역 manifest + --header-source inline → CLI 승리, 두 스코프 4파일이 동일 모드', () => {
  const dir = copyFixture('mixed-scope', 'ts006');
  const cfg = readJsonFile(configPath(dir));
  cfg.headerSource = 'manifest';                 // 전역은 manifest
  writeJsonFile(configPath(dir), cfg);

  const files = [
    'svc/shared/OrderService.java', 'svc/shared/OrderRepo.java',
    'svc/shared/ShipService.java',  'svc/shared/ShipRepo.java',
  ];

  // (a) CLI 플래그가 이긴다 — 서로 다른 스코프의 4파일이 모두 inline
  const withFlag = files.map(f => run(dir, ['target', f, '--header-source', 'inline', '--json']));
  const modes = withFlag.map(r => r.json && r.json.write_to);
  assert.deepStrictEqual(modes, ['inline', 'inline', 'inline', 'inline'],
    `[RED expect] CLI 플래그가 전역 config를 이기고 실행 전체가 inline이어야 함, got ${JSON.stringify(withFlag.map(r => r.json))}`);
  for (const r of withFlag) {
    assert.strictEqual(r.exitCode, 0, `[RED expect] target은 exit 0, got ${r.exitCode} / ${JSON.stringify(r.stdout)}`);
    assert.strictEqual(r.json && r.json.reason, 'header_source_inline',
      `[RED expect] reason === header_source_inline, got ${JSON.stringify(r.json)}`);
  }

  // (b) 플래그를 빼면 전역값(manifest)이 적용된다 — (a)의 승리가 플래그 때문임을 대조로 고정한다
  const noFlag = files.map(f => run(dir, ['target', f, '--json']));
  assert.deepStrictEqual(noFlag.map(r => r.json && r.json.write_to), ['manifest', 'manifest', 'manifest', 'manifest'],
    `[RED expect] 플래그 부재 시 전역 manifest가 적용되어야 함, got ${JSON.stringify(noFlag.map(r => r.json))}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F1d] TS-005 · TS-069 (S-21) — 스코프 오버라이드 부재 (대칭 쌍 부정 단언)
//
// 두 케이스는 같은 명제를 서로 다른 파일에서 고정한다. 어느 한쪽만 막으면 전역 단일 키 결정이
// 다른 문으로 조용히 되살아난다 — PLAN §3.2.2 (E) "code-scan.json 행이 필수인 이유".
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F1d] TS-005 (S-21): index.json scopes[].headerSource는 무시 — 전역 inline 적용 + 안내 1줄', () => {
  const dir = copyFixture('mixed-scope', 'ts005');
  const idx = readJsonFile(indexPath(dir));
  idx.scopes['order-svc'].headerSource = 'manifest';   // 스코프 오버라이드 시도(양쪽 모두)
  idx.scopes['ship-svc'].headerSource = 'manifest';
  writeJsonFile(indexPath(dir), idx);
  // 전역은 커밋값 inline 그대로 — config는 손대지 않는다

  const a = run(dir, ['target', 'svc/shared/OrderService.java', '--json']);
  const b = run(dir, ['target', 'svc/shared/ShipService.java', '--json']);

  // [RED 기대] 현행 decideTarget은 auto 모드로 파일 상태를 보고 판정하므로 write_to/reason 도메인 자체가 다르다.
  for (const [name, r] of [['order-svc', a], ['ship-svc', b]]) {
    assert.strictEqual(r.exitCode, 0, `[RED expect] ${name}: target exit 0, got ${r.exitCode}`);
    assert.strictEqual(r.json && r.json.write_to, 'inline',
      `[RED expect] ${name}: 스코프 headerSource는 무시되고 전역 inline이 적용되어야 함, got ${JSON.stringify(r.json)}`);
    assert.strictEqual(r.json && r.json.reason, 'header_source_inline',
      `[RED expect] ${name}: reason === header_source_inline, got ${JSON.stringify(r.json)}`);
  }

  // 조용히 버리지 않는다 — 실행당 1회 안내(스코프 2개여도 1줄). stdout은 오염되지 않는다.
  const noticed = stderrLines(a.stderr).filter(l => l.includes('headerSource'));
  assert.strictEqual(noticed.length, 1,
    `[RED expect] index.json 스코프 headerSource 안내는 실행당 정확히 1줄(deprecationOnce), got ${noticed.length}줄: ${JSON.stringify(a.stderr)}`);
  assert.ok(a.json !== null, '[RED expect] 안내는 stderr로만 나가고 stdout JSON을 오염시키지 않는다');
});

test('[T080/L1-F1d] TS-069 (S-21): code-scan.json scopes[].headerSource는 무시 — 전역 inline 적용 + 안내 1줄', () => {
  const dir = copyFixture('mixed-scope', 'ts069');
  const cfg = readJsonFile(configPath(dir));
  cfg.scopes['order-svc'].headerSource = 'manifest';   // 사용자가 실제로 편집하는 파일 측 시도
  cfg.scopes['ship-svc'].headerSource = 'manifest';
  writeJsonFile(configPath(dir), cfg);                 // 최상위 headerSource는 inline 유지

  const a = run(dir, ['target', 'svc/shared/OrderService.java', '--json']);
  const b = run(dir, ['target', 'svc/shared/ShipService.java', '--json']);

  for (const [name, r] of [['order-svc', a], ['ship-svc', b]]) {
    assert.strictEqual(r.exitCode, 0, `[RED expect] ${name}: target exit 0, got ${r.exitCode}`);
    assert.strictEqual(r.json && r.json.write_to, 'inline',
      `[RED expect] ${name}: code-scan.json 스코프 headerSource는 무시되고 전역 inline이 적용되어야 함, got ${JSON.stringify(r.json)}`);
    assert.strictEqual(r.json && r.json.reason, 'header_source_inline',
      `[RED expect] ${name}: reason === header_source_inline, got ${JSON.stringify(r.json)}`);
  }

  const noticed = stderrLines(a.stderr).filter(l => l.includes('headerSource'));
  assert.strictEqual(noticed.length, 1,
    `[RED expect] code-scan.json 스코프 headerSource 안내는 실행당 정확히 1줄(config_scope_header_source), got ${noticed.length}줄: ${JSON.stringify(a.stderr)}`);
  assert.ok(a.json !== null, '[RED expect] 안내는 stderr로만 나가고 stdout JSON을 오염시키지 않는다');
});
