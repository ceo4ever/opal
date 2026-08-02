/**
 * @header {
 *   "module": "test-discover",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `discover` 산출물 정합(제거된 readonly 키 0건·모드 선언 키 headerSource 0건·include 무추론) + 초안 생성/앵커 2종/멱등 가드 CLI 블랙박스 테스트 (F-004/F-002, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-9", "S-13"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 077의 `discover`는 스코프마다 `readonly: false`를 명시 기입했다(`code-scan.js:1098`, `:1107`).
// 080은 `readonly`를 제거하고(F-004) `headerSource`를 **전역 단일 키**로 확정하므로(D-2), 산출물
// `scopes[]`에는 두 키 어느 것도 나타나면 안 된다. 이는 단순 정리가 아니라 집행 장치다 —
// `discover`가 모드 키를 산출물에 심으면 **그 순간부터 스코프 오버라이드가 자산에 고정**되고,
// 이후 사람이 그 값을 편집하면서 전역 단일 키 결정이 조용히 되살아난다(PLAN §3.4.5 TS-071 근거).
// 아래 추가는 기존 케이스를 지우거나 완화하지 않는다 — 077 TS-011~TS-014는 전량 승계되고,
// 그 위에 **산출물 부정 단언 3종**이 얹힌다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다.
//
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.4.5/§3.2.2 (F), TEST-SCENARIO.md §3 S-13 / §4):
//
// | 케이스 프리픽스   | TS-ID          | S-ID | 계층 | 검증 명제                                          |
// |-------------------|----------------|------|------|---------------------------------------------------|
// | [T080/L1-F6b]     | TS-032         | S-13 | L1   | 산출물 `scopes[]`에 `readonly` 키 0건 + note 문구 갱신 |
// | [T080/L1-F6b]     | TS-071         | S-13 | L1   | 산출물 `scopes[]`에 `headerSource` 키 0건 (TS-032 대응물) |
// | [T080/L1-F6b]     | (§3.2.2 (F) 보강⑤) | S-13 | L1 | `include`는 **추론하지 않는다**(빈 배열) · 명시값은 승계 |
// | 077 TS-011~TS-014 (승계)          | —    | L1/L2 | 초안 생성·초안 표시 4필드·앵커 2종·멱등 가드          |
//
// [MUST] **TS-ID 네임스페이스** (PLAN §3.7.2 각주): 본 태스크(080)의 TS-011~TS-014와 077의
// TS-011~TS-014는 **서로 다른 번호 체계**다. 077 자산은 항상 `077 TS-NNN`으로 표기한다.
//
// [MUST] red-first.md §4 — 실 CLI subprocess의 exit code · stdout JSON · 실제로 쓰인 파일 내용으로만
// 검증한다. mock 금지. 픽스처 커밋 상태는 수정하지 않으며 모든 트리는 임시 복사본으로 만든다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — 산출물 readonly 0건(TS-032)·headerSource 0건
//     (TS-071)·include 무추론(보강⑤) 부정 단언 신설, note 문구 갱신 검증 추가, 077 자산 전량 승계
//     (opal-test-agent mode:red)
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

function run(cwd, args) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], { cwd, encoding: 'utf8', timeout: 10000 });
  const stdout = result.stdout || '';
  const stderr = result.stderr || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr, json };
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

/**
 * `codemap-repo`의 소스 트리(svc/web/legacy) + `.opal/code-scan.json`만 복사한 새 임시 디렉토리.
 * `.opal/code-map`(기존 index/매니페스트)은 제외해 "index 미존재" 상태를 만든다.
 * config의 `scopes`는 **문자열 축약형**이며 커밋 `headerSource`는 "manifest"다(게이트 통과 전제).
 */
function makeBlankCodemapRepo() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-discover-'));
  cleanupDirs.push(dir);
  const srcRoot = path.join(FIX, 'codemap-repo');
  for (const name of ['svc', 'web', 'legacy']) {
    copyDirRecursive(path.join(srcRoot, name), path.join(dir, name));
  }
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.copyFileSync(path.join(srcRoot, '.opal', 'code-scan.json'), path.join(dir, '.opal', 'code-scan.json'));
  return dir;
}

/**
 * `mixed-scope` 전체를 복사한 뒤 `.opal/code-map/`만 지운다.
 * config의 `scopes`는 **객체 형식 + 사람이 명시한 `include`**를 보유한다(보강⑤ "명시값 승계" 무대).
 */
function makeBlankMixedScope() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-discover-mixed-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'mixed-scope'), dir);
  fs.rmSync(path.join(dir, '.opal', 'code-map'), { recursive: true, force: true });
  return dir;
}

/** `--dry-run --json` 출력에서 초안 index 객체를 꺼낸다. */
function draftOf(json) {
  return json && (json.index || json);
}

/** 초안 index를 **실제로 쓰인 파일**에서 읽는다 — dry-run과 write 경로가 갈라지지 않았음을 보장한다. */
function writeDraftAndRead(dir) {
  const { exitCode, stdout } = run(dir, ['discover', '--json']);
  const outPath = path.join(dir, '.opal', 'code-map', 'index.json');
  return { exitCode, stdout, outPath, exists: fs.existsSync(outPath),
    index: fs.existsSync(outPath) ? JSON.parse(fs.readFileSync(outPath, 'utf8')) : null };
}

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F6b] TS-032 (S-13): 산출물 `scopes[]`에 `readonly` 키 0건 + note 문구 갱신
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F6b] TS-032 (S-13): discover --dry-run 산출물의 scopes[]에 readonly 키 0건', () => {
  const dir = makeBlankCodemapRepo();
  const { exitCode, json, stdout } = run(dir, ['discover', '--dry-run', '--json']);

  assert.strictEqual(exitCode, 0, `discover --dry-run은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  const draft = draftOf(json);
  assert.ok(draft && draft.scopes && Object.keys(draft.scopes).length > 0,
    `[RED expect] scopes가 산출되어야 함, got ${JSON.stringify(draft && draft.scopes)}`);

  const offenders = Object.entries(draft.scopes)
    .filter(([, s]) => Object.prototype.hasOwnProperty.call(s, 'readonly'))
    .map(([name, s]) => `${name}: readonly=${JSON.stringify(s.readonly)}`);
  assert.deepStrictEqual(offenders, [],
    `[RED expect] readonly는 제거된 키다(F-004) — 현행 inferScopes(code-scan.js:1098,:1107)는 readonly:false를 명시 기입한다.\n잔존:\n${offenders.join('\n')}`);
});

test('[T080/L1-F6b] TS-032 (S-13): 실제로 쓰인 index.json에도 readonly 키 0건 (dry-run과 write 경로 동일)', () => {
  const dir = makeBlankCodemapRepo();
  const { exitCode, index, exists, outPath, stdout } = writeDraftAndRead(dir);

  assert.strictEqual(exitCode, 0, `discover는 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  assert.ok(exists, `${outPath} 파일이 생성되어야 함`);

  const offenders = Object.entries(index.scopes || {})
    .filter(([, s]) => Object.prototype.hasOwnProperty.call(s, 'readonly'))
    .map(([name]) => name);
  assert.deepStrictEqual(offenders, [],
    `[RED expect] 디스크에 기록된 산출물에도 readonly가 남으면 안 된다 — 자산에 고정되면 사람이 그 값을 편집한다. 잔존 스코프: ${JSON.stringify(offenders)}`);
});

test('[T080/L1-F6b] TS-032 (S-13): note 문구에 readonly 언급 0건 + 검토 대상 키(headerSource/include) 안내 포함', () => {
  const dir = makeBlankCodemapRepo();
  const { json } = run(dir, ['discover', '--dry-run', '--json']);
  const draft = draftOf(json);

  assert.ok(draft && typeof draft.note === 'string' && draft.note.length > 0,
    `[RED expect] note 문자열이 존재해야 함, got ${JSON.stringify(draft && draft.note)}`);
  assert.ok(!/readonly/i.test(draft.note),
    `[RED expect] note는 제거된 키를 검토 대상으로 안내하면 안 된다(F-11 AC "readonly를 판정 근거로 서술하는 문장 잔존 0건"), got "${draft.note}"`);
  assert.ok(/headerSource/.test(draft.note),
    `[RED expect] note는 갱신된 검토 대상(headerSource)을 안내해야 한다(PLAN §3.4.2 신규 note 문자열), got "${draft.note}"`);
  assert.ok(/include/.test(draft.note),
    `[RED expect] note는 사람이 채워야 할 필드(include)를 안내해야 한다(보강⑤), got "${draft.note}"`);
  assert.ok(/OWNER REVIEW REQUIRED/.test(draft.note),
    `[RED expect] 소유자 검토 요구 표지는 유지되어야 함(077 승계), got "${draft.note}"`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F6b] TS-071 (S-13): 산출물 `scopes[]`에 `headerSource` 키 0건 — TS-032의 대응물
// ═════════════════════════════════════════════════════════════════════════
//
// `headerSource`는 **전역 단일 키**다(D-2). `discover`가 스코프마다 모드 키를 심으면 그 순간부터
// 스코프 오버라이드가 자산에 고정되고, 전역 단일 키 결정이 조용히 되살아난다. 산출물 검사로 막는다.
// [MUST] `opal/core/PRINCIPLES.md`: "Enforce, don't just advise."

test('[T080/L1-F6b] TS-071 (S-13): discover --dry-run 산출물의 scopes[]에 headerSource 키 0건', () => {
  const dir = makeBlankCodemapRepo();
  const { json } = run(dir, ['discover', '--dry-run', '--json']);
  const draft = draftOf(json);

  assert.ok(draft && draft.scopes, `[RED expect] scopes가 산출되어야 함, got ${JSON.stringify(draft)}`);
  const offenders = Object.entries(draft.scopes)
    .filter(([, s]) => Object.prototype.hasOwnProperty.call(s, 'headerSource'))
    .map(([name, s]) => `${name}: headerSource=${JSON.stringify(s.headerSource)}`);
  assert.deepStrictEqual(offenders, [],
    `[RED expect] 스코프 단위 모드 선언은 존재하지 않는다 — discover가 심으면 오버라이드가 자산에 고정된다.\n잔존:\n${offenders.join('\n')}`);
});

test('[T080/L1-F6b] TS-071 (S-13): 실제로 쓰인 index.json 전체에 스코프 단위 headerSource 0건', () => {
  const dir = makeBlankCodemapRepo();
  const { index, exists } = writeDraftAndRead(dir);
  assert.ok(exists, '[RED expect] discover가 index.json을 생성해야 함');

  const offenders = Object.entries(index.scopes || {})
    .filter(([, s]) => Object.prototype.hasOwnProperty.call(s, 'headerSource'))
    .map(([name]) => name);
  assert.deepStrictEqual(offenders, [],
    `[RED expect] 디스크 산출물에도 스코프 단위 headerSource가 없어야 함. 잔존 스코프: ${JSON.stringify(offenders)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F6b] (§3.2.2 (F) 보강⑤): `include`는 추론하지 않는다 — 빈 배열 · 명시값은 승계
// ═════════════════════════════════════════════════════════════════════════
//
// [MUST] TASK.md §개선 A 보강 ⑤: "`discover`는 `include`를 추론하지 않는다 — 빈 배열로 두고 사람이
// 채우는 필드로 규정" — 어느 파일이 우리 것인지는 도메인 지식이며, 도구 추측은 **오탐을 자산에
// 고정시킨다**. 반대로 사람이 `code-scan.json`에 명시한 값의 승계는 추론이 아니므로 허용된다.

test('[T080/L1-F6b] (보강⑤): config에 include가 없는 프로젝트 → 산출물 include/exclude가 빈 배열(추론 0건)', () => {
  const dir = makeBlankCodemapRepo();
  const { json } = run(dir, ['discover', '--dry-run', '--json']);
  const draft = draftOf(json);

  assert.ok(draft && draft.scopes, `[RED expect] scopes가 산출되어야 함, got ${JSON.stringify(draft)}`);
  for (const [name, scope] of Object.entries(draft.scopes)) {
    assert.deepStrictEqual(scope.include, [],
      `[RED expect] 스코프 "${name}"의 include는 추론 없이 빈 배열이어야 한다, got ${JSON.stringify(scope.include)}`);
    assert.deepStrictEqual(scope.exclude, [],
      `[RED expect] 스코프 "${name}"의 exclude도 빈 배열이어야 한다, got ${JSON.stringify(scope.exclude)}`);
  }
});

test('[T080/L1-F6b] (보강⑤): config에 사람이 명시한 include는 그대로 승계된다 (추론이 아니라 보존)', () => {
  const dir = makeBlankMixedScope();
  const { exitCode, json, stdout } = run(dir, ['discover', '--dry-run', '--json']);

  assert.strictEqual(exitCode, 0,
    `[RED expect] 객체 형식 scopes에서도 discover는 exit 0이어야 함 — 현행 inferScopes(:1096)는 값을 문자열로 가정해 TypeError로 죽는다, got ${exitCode} (stdout: ${stdout})`);
  const draft = draftOf(json);
  assert.ok(draft && draft.scopes, `[RED expect] scopes가 산출되어야 함, got ${JSON.stringify(draft)}`);

  assert.deepStrictEqual(draft.scopes['order-svc'] && draft.scopes['order-svc'].include, ['Order*.java'],
    `[RED expect] code-scan.json에 명시된 include는 그대로 승계되어야 함, got ${JSON.stringify(draft.scopes['order-svc'])}`);
  assert.deepStrictEqual(draft.scopes['ship-svc'] && draft.scopes['ship-svc'].include, ['Ship*.java'],
    `[RED expect] 두 번째 스코프도 동상, got ${JSON.stringify(draft.scopes['ship-svc'])}`);
  assert.strictEqual(draft.scopes['order-svc'].root, 'svc/shared/',
    `[RED expect] 객체 형식의 사용자 대면 키 path는 내부 정규화 형태 root로 승격되어야 함(§3.2.2 (A)), got ${JSON.stringify(draft.scopes['order-svc'])}`);

  for (const [name, scope] of Object.entries(draft.scopes)) {
    assert.ok(!Object.prototype.hasOwnProperty.call(scope, 'readonly'),
      `[RED expect] 승계 경로에서도 readonly가 붙으면 안 됨 — 스코프 "${name}"`);
    assert.ok(!Object.prototype.hasOwnProperty.call(scope, 'headerSource'),
      `[RED expect] 승계 경로에서도 headerSource가 붙으면 안 됨 — 스코프 "${name}"`);
  }
});

// ═════════════════════════════════════════════════════════════════════════
// 077 승계 자산 — 초안 생성·앵커 탐지·멱등 가드 (계약 불변)
// ═════════════════════════════════════════════════════════════════════════

test('077 TS-011 (S-9): discover --dry-run — scopes ≥2, layerRules ≥1, exclude에 target 포함', () => {
  const dir = makeBlankCodemapRepo();

  const { exitCode, json, stdout } = run(dir, ['discover', '--dry-run', '--json']);

  assert.strictEqual(exitCode, 0, `discover --dry-run은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  assert.ok(json !== null, '--json 출력이 유효 JSON이어야 함');
  const draft = draftOf(json);
  assert.ok(draft && draft.scopes && Object.keys(draft.scopes).length >= 2,
    `scopes ≥2 기대, got ${JSON.stringify(draft && draft.scopes)}`);
  assert.ok(Array.isArray(draft && draft.layerRules) && draft.layerRules.length >= 1,
    'layerRules ≥1 기대');
  assert.ok(Array.isArray(draft && draft.exclude) && draft.exclude.includes('target'),
    `exclude에 컴파일 산출물 디렉토리(target)가 포함되어야 함, got ${JSON.stringify(draft && draft.exclude)}`);
});

test('077 TS-012 (S-9): discover(실제 쓰기) — 초안 표시 4필드가 index.json에 존재', () => {
  const dir = makeBlankCodemapRepo();

  const { exitCode, index, exists, outPath } = writeDraftAndRead(dir);

  assert.strictEqual(exitCode, 0, `discover는 exit 0이어야 함, got ${exitCode}`);
  assert.ok(exists, `${outPath} 파일이 생성되어야 함`);

  assert.strictEqual(index.origin, 'discover', 'origin: "discover"');
  assert.strictEqual(index.status, 'draft', 'status: "draft"');
  assert.strictEqual(typeof index.generatedAt, 'string', 'generatedAt 존재');
  assert.strictEqual(typeof index.note, 'string', 'note 존재');
  assert.ok(index.note.length > 0, 'note가 OWNER REVIEW REQUIRED 안내를 포함해야 함');
});

test('077 TS-013 (S-9): 앵커 2종 — svc(pom.xml 기반) + web(1-depth 디렉토리) 각각 검출', () => {
  const dir = makeBlankCodemapRepo();

  const { json } = run(dir, ['discover', '--dry-run', '--json']);
  const draft = draftOf(json);

  assert.ok(draft && draft.scopes, 'scopes 존재');
  assert.ok(draft.scopes.svc && Array.isArray(draft.scopes.svc.anchors) && draft.scopes.svc.anchors.includes('order-api'),
    `svc 스코프에서 pom.xml 기반 앵커 order-api가 검출되어야 함, got ${JSON.stringify(draft.scopes.svc)}`);
  assert.ok(draft.scopes.web && Array.isArray(draft.scopes.web.anchors) && draft.scopes.web.anchors.includes('admin'),
    `web 스코프에서 단순 디렉토리 앵커 admin이 검출되어야 함, got ${JSON.stringify(draft.scopes.web)}`);
});

test('077 TS-014 (S-9): 기존 index 존재 → index_exists exit 1', () => {
  const dir = makeBlankCodemapRepo();
  fs.mkdirSync(path.join(dir, '.opal', 'code-map'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-map', 'index.json'), JSON.stringify({ version: 1, scopes: {} }));

  const { exitCode, json } = run(dir, ['discover', '--json']);

  assert.strictEqual(exitCode, 1, `index_exists → exit 1 기대, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'index_exists',
    `error: index_exists 기대, got ${JSON.stringify(json)}`);
});

test('077 TS-014 (S-9): --dry-run은 파일을 쓰지 않는다', () => {
  const dir = makeBlankCodemapRepo();

  run(dir, ['discover', '--dry-run', '--json']);
  const outPath = path.join(dir, '.opal', 'code-map', 'index.json');

  assert.strictEqual(fs.existsSync(outPath), false, '--dry-run 실행 후 index.json이 생성되면 안 됨');
});
