/**
 * @header {
 *   "module": "test-target",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `target` 서브명령의 모드 직결 판정(decideTarget: write_to 3값 × reason 3값), out_of_scope 신규 배선, readonly 무시 + 전역값 적용(양방향 고정) CLI 블랙박스 테스트 (F-003/F-004/F-008, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-8", "S-9", "S-13"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 077이 고정한 `decideTarget` 4단 판정(readonly_repo → inline_exists → new_file → legacy_no_header)은
// 이번 태스크의 설계 결정(전역 단일 `headerSource` 2택 · 스코프 예외 없음 · 실행당 1값, PLAN §3.3.2 (B))에
// 의해 **명제 자체가 바뀐다** — 파일 상태·스코프 속성은 더 이상 판정 근거가 아니다.
// 아래 재작성은 기대값을 느슨하게 바꿔 통과시키는 것이 아니라, 바뀐 계약을 **같은 강도(또는 더 강한
// 부정 단언)로 다시 고정**하는 계약 이전이다. 특히 TS-030(반전)·TS-033(재정의)은 077이 검증하던
// `readonly` 자산을 버리지 않고 "결과가 readonly가 아니라 전역값을 따른다"를 **두 방향으로** 고정한다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다.
//
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.3.5/§3.4.5/§3.2.5, TEST-SCENARIO.md §4):
//
// | 케이스 프리픽스   | TS-ID                  | S-ID | 계층 | AC     |
// |-------------------|------------------------|------|------|--------|
// | [T080/L1-F3]      | TS-020, TS-021, TS-022 | S-8  | L1   | F-3 AC |
// | [T080/L1-F6]      | TS-030, TS-031, TS-033, TS-034 | S-13 | L1 | F-6 AC |
// | [T080/L1-F8b]     | TS-035, TS-037         | S-9  | L1   | F-8 AC |
//
// 확정 도메인 (PLAN §3.3.2 (B) · §3.2.2 (C-bis) · §3.6.2 (2) 판정표):
//   ① 소속 스코프 include/exclude 필터 탈락 → write_to: 'none'     / reason: 'out_of_scope'
//   ② headerSource(CLI > 전역, 2층) = inline  → write_to: 'inline'   / reason: 'header_source_inline'
//   ③ headerSource = manifest                → write_to: 'manifest' / reason: 'header_source_manifest'
// 판정은 ①→②→③ 순으로 첫 매칭이 승리한다(①이 모드 판정보다 **먼저**).
//
// RED-first: 현행 code-scan.js의 decideTarget(`:755-791`)은 readonly → 인라인 존재 → 디스크 부재 →
// 그 외의 4단 판정이며 `out_of_scope`/`header_source_*` reason 자체가 존재하지 않는다. 따라서 아래
// 신 계약 케이스는 전부 실패해야 정상이다(이것이 RED 증거다). 구현(GREEN)은 op-dev-execute가
// Step 6~7에서 수행한다 — 작성자≠구현자(red-first.md §2).
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — 4단 판정 → 모드 직결 3값 도메인, out_of_scope 신규
//     배선(TS-035/037), readonly 무시 + 전역값 적용 양방향 고정(TS-030 반전 / TS-033 재정의),
//     판정 근거 잔존 0 산출물 검사(TS-034) (opal-test-agent mode:red)
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

/**
 * 커밋 픽스처를 임시 복사본으로 복제하고 `.opal/code-scan.json`의 최상위 `headerSource`만 교체한다.
 * 픽스처 자산은 절대 수정하지 않는다(PLAN §3.7.2 "픽스처 자산 무변경") — 사전 조작은 오버레이로만 한다.
 * 실 파일시스템 + 실 CLI subprocess만 사용한다(mock 금지).
 */
function overlayHeaderSource(fixtureName, value) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-target-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureName), dir);
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  cfg.headerSource = value;
  fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\n');
  return dir;
}

const CODEMAP_REPO = path.join(FIX, 'codemap-repo');   // 커밋값 headerSource: "manifest"
const LEGACY_REPO = path.join(FIX, 'legacy-repo');     // 커밋값 headerSource: "inline", include/exclude 미사용
const MIXED_SCOPE = path.join(FIX, 'mixed-scope');     // 커밋값 headerSource: "inline", 생존 스코프 2 + out_of_scope 1

// codemap-repo 내 3상태 대표 파일 — 077 4단 판정이 서로 다른 reason을 주던 바로 그 파일들이다.
const F_INLINE_HELD = 'web/admin/pages/AdminHome.tsx';                                          // 인라인 @header 보유
const F_ON_DISK_NO_INLINE = 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java'; // 존재 + 인라인 없음
const F_NOT_ON_DISK = 'svc/order-api/src/main/java/com/acme/order/service/BrandNew.java';         // 디스크 부재(신규)
const F_READONLY_SCOPE = 'legacy/lib/legacy_util.py';                                            // legacy 스코프(readonly:true)

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F3] TS-020 / TS-021 / TS-022 (S-8): 모드 직결 — 파일 상태는 판정 근거가 아니다
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F3] TS-020 (S-8): manifest 모드 — 신규·인라인 보유·인라인 부재 3파일 전부 write_to:manifest / reason:header_source_manifest', () => {
  // 커밋값이 이미 manifest이므로 별도 오버레이 없이 커밋 상태를 그대로 관찰한다.
  const cases = [
    ['인라인 @header 보유 파일', F_INLINE_HELD],
    ['디스크 존재 + 인라인 없음', F_ON_DISK_NO_INLINE],
    ['디스크 부재(신규) 파일', F_NOT_ON_DISK],
  ];

  for (const [label, rel] of cases) {
    const { exitCode, json, stdout } = run(CODEMAP_REPO, ['target', rel, '--json']);
    assert.strictEqual(exitCode, 0, `${label}: target은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
    assert.strictEqual(json && json.write_to, 'manifest',
      `[RED expect] ${label}: manifest 모드에서는 파일 상태와 무관하게 write_to:'manifest'여야 함(F-3 AC), got ${JSON.stringify(json)}`);
    assert.strictEqual(json && json.reason, 'header_source_manifest',
      `[RED expect] ${label}: reason은 모드에서 직결된 'header_source_manifest' 1값이어야 함 — ` +
      `077의 inline_exists/new_file/legacy_no_header 3값은 모두 이 1값으로 병합된다(PLAN §3.3.2 (B)), got ${JSON.stringify(json)}`);
  }
});

test('[T080/L1-F3] TS-021 (S-8): inline 모드 — 같은 3파일 + readonly 스코프 파일까지 전부 write_to:inline / reason:header_source_inline', () => {
  const dir = overlayHeaderSource('codemap-repo', 'inline');
  const cases = [
    ['인라인 @header 보유 파일', F_INLINE_HELD],
    ['디스크 존재 + 인라인 없음', F_ON_DISK_NO_INLINE],
    ['디스크 부재(신규) 파일', F_NOT_ON_DISK],
    ['readonly:true 스코프 파일', F_READONLY_SCOPE],
  ];

  for (const [label, rel] of cases) {
    const { exitCode, json, stdout } = run(dir, ['target', rel, '--json']);
    assert.strictEqual(exitCode, 0, `${label}: target은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
    assert.strictEqual(json && json.write_to, 'inline',
      `[RED expect] ${label}: inline 모드에서는 항상 write_to:'inline'이어야 함(F-3 AC), got ${JSON.stringify(json)}`);
    assert.strictEqual(json && json.reason, 'header_source_inline',
      `[RED expect] ${label}: reason은 'header_source_inline' 1값이어야 함, got ${JSON.stringify(json)}`);
  }
});

test('[T080/L1-F3] TS-022 (S-8): manifest 모드 target 결과에 scope/manifest/key가 정확히 채워진다', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['target', F_ON_DISK_NO_INLINE, '--json']);

  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'manifest', `[RED expect] write_to:'manifest', got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.scope, 'svc', `[RED expect] scope:'svc', got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.key, 'OrderService.java',
    `[RED expect] key는 basename이어야 함, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.manifest, '.opal/code-map/svc/order-api/order/service.json',
    `[RED expect] manifest 경로가 실제 미러 경로와 일치해야 함(mirrorPathForDir 사상 불변), got ${JSON.stringify(json)}`);
});

test('[T080/L1-F3] TS-021 (S-8): inline 모드 target 결과에는 scope/manifest/key가 존재하지 않는다 (부정 단언)', () => {
  const dir = overlayHeaderSource('codemap-repo', 'inline');
  const { json } = run(dir, ['target', F_ON_DISK_NO_INLINE, '--json']);

  // inline 모드는 매니페스트를 읽지도 쓰지도 않으므로 기록 위치 부가 필드가 나가면 안 된다(§3.3.2 (B)).
  assert.strictEqual(json && json.write_to, 'inline', `[RED expect] write_to:'inline', got ${JSON.stringify(json)}`);
  for (const k of ['scope', 'manifest', 'key']) {
    assert.strictEqual(json && json[k], undefined,
      `[RED expect] inline 모드 결과에 '${k}' 필드가 있으면 안 됨(매니페스트 경로 지시는 manifest 모드 전용), got ${JSON.stringify(json)}`);
  }
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F6] TS-030 / TS-031 / TS-033 / TS-034 (S-13): readonly 무시 + 전역값 적용 (양방향 고정)
//
// 077은 `readonly: true` 스코프를 "무조건 manifest"로 흡수했다(`readonly_repo`). 전역 단일 키 결정으로
// **흡수할 자리 자체가 사라졌으므로**(PLAN §3.4.2) 이 키는 값과 무관하게 무시되고 전역값이 그대로
// 적용된다. TS-030(전역 inline → inline)과 TS-033(전역 manifest → manifest)이 **짝을 이루어야만**
// "결과가 readonly가 아니라 전역값을 따른다"가 증명된다 — 한 방향만 보면 우연 일치와 구분되지 않는다.
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F6] TS-030 (S-13) [반전]: readonly:true 스코프 + 전역 inline → write_to:inline (manifest가 아니다)', () => {
  const dir = overlayHeaderSource('codemap-repo', 'inline');
  const { exitCode, json } = run(dir, ['target', F_READONLY_SCOPE, '--json']);

  assert.strictEqual(exitCode, 0, `exit 0 기대(무시는 오류가 아니다), got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'inline',
    `[RED expect][반전] readonly:true는 **무시**되고 전역 inline이 그대로 적용되어야 함 — ` +
    `077의 write_to:'manifest'(readonly_repo)에서 뒤집힌다(PLAN §3.4.2), got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'header_source_inline',
    `[RED expect] reason:'header_source_inline' — 'readonly_repo'는 소멸한 값이다, got ${JSON.stringify(json)}`);
  assert.notStrictEqual(json && json.reason, 'readonly_repo',
    `[RED expect] 소멸한 reason 값 'readonly_repo'가 되살아나면 안 됨, got ${JSON.stringify(json)}`);
});

test('[T080/L1-F6] TS-033 (S-13) [재정의]: readonly:true 스코프 + 전역 manifest → write_to:manifest (TS-030과 양방향 쌍)', () => {
  // 커밋값이 manifest인 codemap-repo를 그대로 쓴다 — 같은 파일이 전역값에 따라 반대로 판정됨을 보인다.
  const { exitCode, json } = run(CODEMAP_REPO, ['target', F_READONLY_SCOPE, '--json']);

  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'manifest',
    `[RED expect] 전역 manifest이므로 write_to:'manifest', got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'header_source_manifest',
    `[RED expect] reason은 전역값 유래여야 하며 readonly 유래여서는 안 됨, got ${JSON.stringify(json)}`);
  assert.notStrictEqual(json && json.reason, 'readonly_repo',
    `[RED expect] 'readonly_repo'가 되살아나면 안 됨 — 같은 결과라도 근거가 달라야 한다, got ${JSON.stringify(json)}`);
});

test('[T080/L1-F6] TS-031 (S-13): readonly 보유 index 실행 — stderr deprecated 안내 1줄(중복 0) + 전역 설정 방법 포함 + stdout JSON 무오염', () => {
  const dir = overlayHeaderSource('codemap-repo', 'inline');
  const { exitCode, stdout, stderr, json } = run(dir, ['target', F_READONLY_SCOPE, '--json']);

  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);

  // ① 안내가 실제로 나간다 + ② 실행당 정확히 1회 (codemap-repo index에는 readonly 키를 가진 스코프가 3개
  //    — legacy(true)/svc(false)/web(false) — 이므로 "스코프마다 1줄"이면 3줄이 나간다. 1줄이어야 한다.)
  const deprecatedReadonlyLines = stderr.split('\n').filter(l => /\[deprecated\]/.test(l) && /readonly/.test(l));
  assert.strictEqual(deprecatedReadonlyLines.length, 1,
    `[RED expect] readonly deprecated 안내는 실행당 정확히 1줄이어야 함(deprecationOnce 키 'index_scope_readonly'), ` +
    `got ${deprecatedReadonlyLines.length}줄. stderr="${stderr}"`);

  // ③ 안내 문구가 사용자에게 "무엇을 어디에 설정해야 하는지"를 알려준다 — 이 안내가 동작 변화를 알리는 유일한 접점이다.
  const line = deprecatedReadonlyLines[0] || '';
  assert.ok(/headerSource/.test(line),
    `[RED expect] 안내 문구에 전역 headerSource 설정 방법이 포함되어야 함, got "${line}"`);
  assert.ok(/code-scan\.json/.test(line),
    `[RED expect] 안내 문구에 설정 파일 경로(.opal/code-scan.json)가 포함되어야 함, got "${line}"`);

  // ④ stdout JSON 무오염 — brain_tool.py:793 json.loads(result.stdout) 보호 지점
  assert.ok(json !== null, `[RED expect] stdout이 유효 JSON이어야 함(안내가 stdout으로 새면 안 됨). raw="${stdout}"`);
  assert.ok(!/deprecated/i.test(stdout),
    `[RED expect] stdout에 deprecated 안내 문구가 섞이면 안 됨, got "${stdout}"`);
});

test('[T080/L1-F6] TS-034 (S-13) [산출물 검사]: code-scan.js에 readonly를 판정 근거로 쓰는 코드 0건 (note 문자열 포함 잔존 0)', () => {
  const src = fs.readFileSync(CODE_SCAN_JS, 'utf8').split('\n');

  // 허용 영역은 `normalizeIndexScope` 본문 1곳뿐이다 — 여기서만 키 존재를 감지하고 deprecated 안내를
  // 출력한다(PLAN §3.4.1 #1 · §3.4.2 스텁 ①). 그 밖의 어디에도 readonly가 남아 있으면 안 된다:
  // `decideTarget` 분기(§3.4.1 #2) · `inferScopes`의 readonly:false 기입(#3) · `cmdDiscover` note 문자열(#4).
  const range = functionLineRange(src, 'normalizeIndexScope');
  assert.ok(range,
    `[RED expect] normalizeIndexScope 함수가 신설되어야 함(PLAN §3.2.2 (A)) — 현행 code-scan.js에는 존재하지 않는다`);

  const offenders = [];
  for (let i = 0; i < src.length; i++) {
    const lineNo = i + 1;
    if (lineNo >= range[0] && lineNo <= range[1]) continue;   // 허용 영역
    if (/\breadonly\b/i.test(src[i])) offenders.push(`${lineNo}: ${src[i].trim()}`);
  }

  assert.deepStrictEqual(offenders, [],
    `[RED expect] normalizeIndexScope 밖에 readonly 잔존 0건이어야 함(F-6 AC "판정 근거로 서술/사용 0건"). ` +
    `deprecated 안내 문자열의 키 이름 언급은 그 함수 안에 있으므로 예외로 허용된다.\n잔존:\n${offenders.join('\n')}`);
});

/**
 * `function <name>(` 로 시작하는 최상위 함수의 줄 범위를 중괄호 깊이로 확정한다(1-based, 양끝 포함).
 * 문자열 리터럴·라인 주석 안의 중괄호는 세지 않는다. PLAN §3.1.5 TS-070 절차 ①과 동일한 방식이다.
 * @returns {[number, number] | null}
 */
function functionLineRange(srcLines, name) {
  const S = srcLines.findIndex(l => new RegExp('^function\\s+' + name + '\\s*\\(').test(l));
  if (S < 0) return null;
  let d = 0;
  for (let i = S; i < srcLines.length; i++) {
    const l = srcLines[i].replace(/\/\/.*$/, '').replace(/(["'`]).*?\1/g, '');
    for (const ch of l) { if (ch === '{') d++; else if (ch === '}') d--; }
    if (i > S && d === 0) return [S + 1, i + 1];
  }
  return [S + 1, srcLines.length];
}

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F8b] TS-035 / TS-037 (S-9): `target` 스코프 필터 탈락 반환 계약 (신규 배선)
//
// `decideTarget`은 077에서 필터 유틸을 **한 번도 호출하지 않던** 유일한 공백 지점이다
// (PLAN §3.2.2 (C-bis)). 여기서 `out_of_scope`는 "쓸 자리가 없다"를 표현하는 3번째 값이며,
// 모드 판정보다 **먼저** 평가된다. TS-037은 그 신규 판정이 기존 프로젝트로 **번지지 않음**을 고정한다.
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F8b] TS-035 (S-9): 스코프 필터 탈락 파일 → {write_to:"none", reason:"out_of_scope"} + exit 0 + 부가 필드 없음', () => {
  // mixed-scope: order-svc(include ["Order*.java"]) · ship-svc(include ["Ship*.java"]) 어느 쪽에도
  // 매칭되지 않는 VendorLegacy.java — root(svc/shared/)에는 속하지만 필터에서 탈락한다.
  const { exitCode, json, stdout } = run(MIXED_SCOPE, ['target', 'svc/shared/VendorLegacy.java', '--json']);

  assert.strictEqual(exitCode, 0,
    `[RED expect] 필터 탈락은 오류가 아니라 정상 판정이므로 exit 0이어야 함(에러 exit 1은 header_source_* 계열 전용), got ${exitCode} (stdout: ${stdout})`);
  assert.strictEqual(json && json.write_to, 'none',
    `[RED expect] write_to는 신규 3번째 값 'none'이어야 함 — inline 폴백은 manifest 모드에서 소스 혼재를 재발시키고, ` +
    `manifest는 존재하지 않는 기록 위치를 지시한다(PLAN §3.2.2 (C-bis) 반환 계약 결정표), got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'out_of_scope',
    `[RED expect] reason:'out_of_scope', got ${JSON.stringify(json)}`);

  for (const k of ['scope', 'manifest', 'key']) {
    assert.strictEqual(json && json[k], undefined,
      `[RED expect] 관리 대상이 아니므로 기록 위치 필드 '${k}'가 존재하면 안 됨, got ${JSON.stringify(json)}`);
  }
});

test('[T080/L1-F8b] TS-035 (S-9): out_of_scope는 모드 판정보다 먼저 평가된다 — 전역값을 manifest로 뒤집어도 결과 불변', () => {
  const dir = overlayHeaderSource('mixed-scope', 'manifest');
  const { exitCode, json } = run(dir, ['target', 'svc/shared/VendorLegacy.java', '--json']);

  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'none',
    `[RED expect] 판정 순서 ①(out_of_scope)이 ②③(모드 직결)보다 먼저이므로 전역값과 무관하게 'none'이어야 함, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'out_of_scope',
    `[RED expect] 전역 manifest에서도 reason:'out_of_scope', got ${JSON.stringify(json)}`);
});

test('[T080/L1-F8b] TS-035 (S-9): 같은 트리의 include 통과 파일 4건은 out_of_scope로 오발동하지 않는다 (대조군)', () => {
  const survivors = ['OrderService.java', 'OrderRepo.java', 'ShipService.java', 'ShipRepo.java'];

  for (const name of survivors) {
    const { exitCode, json } = run(MIXED_SCOPE, ['target', `svc/shared/${name}`, '--json']);
    assert.strictEqual(exitCode, 0, `${name}: exit 0 기대, got ${exitCode}`);
    assert.notStrictEqual(json && json.reason, 'out_of_scope',
      `[RED expect] ${name}은 include에 매칭되므로 out_of_scope가 아니어야 함, got ${JSON.stringify(json)}`);
    assert.strictEqual(json && json.write_to, 'inline',
      `[RED expect] ${name}: 커밋값 전역 inline이 적용되어야 함, got ${JSON.stringify(json)}`);
  }
});

test('[T080/L1-F8b] TS-037 (S-9) [회귀]: include/exclude 미사용 프로젝트(legacy-repo)에서 out_of_scope 오발동 0건', () => {
  // legacy-repo는 scopes가 문자열 축약형(be/, fe/)이고 include/exclude가 없다 → 필터는 항상 통과해야 한다.
  // 마지막 케이스는 어떤 스코프 root에도 속하지 않는 경로 — 이 경우도 기존 동작(모드 직결)을 유지한다.
  const cases = [
    ['인라인 없는 기존 파일', 'be/util/no_header.py'],
    ['인라인 보유 파일', 'be/service/auth_service.py'],
    ['디스크 부재 신규 파일', 'be/util/does_not_exist.py'],
    ['스코프 root 밖 파일', 'docs/outside_any_scope.md'],
  ];

  for (const [label, rel] of cases) {
    const { exitCode, json, stdout } = run(LEGACY_REPO, ['target', rel, '--json']);
    assert.strictEqual(exitCode, 0, `${label}: exit 0 기대, got ${exitCode} (stdout: ${stdout})`);
    assert.notStrictEqual(json && json.reason, 'out_of_scope',
      `[RED expect] ${label}: 스코프 미설정/필터 미사용 프로젝트에서 out_of_scope가 발동하면 골든·회귀가 깨진다(H-13), got ${JSON.stringify(json)}`);
    assert.strictEqual(json && json.write_to, 'inline',
      `[RED expect] ${label}: 커밋값 전역 inline이 그대로 적용되어야 함, got ${JSON.stringify(json)}`);
    assert.strictEqual(json && json.reason, 'header_source_inline',
      `[RED expect] ${label}: reason:'header_source_inline', got ${JSON.stringify(json)}`);
  }
});

test('[T080/L1-F8b] TS-037 (S-9) [회귀]: 스코프 미설정 codemap-repo 계열도 out_of_scope 오발동 0건', () => {
  // codemap-repo의 index.scopes에는 include/exclude가 전혀 없다 — 발동 조건 ③(전부 isInScope 실패)이
  // 성립할 수 없으므로 어떤 파일도 out_of_scope가 되면 안 된다.
  for (const rel of [F_INLINE_HELD, F_ON_DISK_NO_INLINE, F_NOT_ON_DISK, F_READONLY_SCOPE]) {
    const { json } = run(CODEMAP_REPO, ['target', rel, '--json']);
    assert.notStrictEqual(json && json.reason, 'out_of_scope',
      `[RED expect] ${rel}: include/exclude 미사용 스코프에서 out_of_scope 오발동 0건이어야 함, got ${JSON.stringify(json)}`);
  }
});
