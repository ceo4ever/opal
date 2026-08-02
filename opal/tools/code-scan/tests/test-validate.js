/**
 * @header {
 *   "module": "test-validate",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `validate` 서브명령의 모드별 단일 소스 커버리지(합산 폐기)·구조 패스 모드 분기·headerSource 결과 필드·스코프 필터 존중(오탐/미탐 양방향) + 077 위반 검출/git 2분류/--changed 필터 회귀 CLI 블랙박스 테스트 (F-005/F-009, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-7", "S-11"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 077은 커버리지를 "인라인 + 지도 **합산**"으로 고정했다(077 TS-025: `covered === inline + manifest`).
// 전역 단일 `headerSource` 2택 도입으로 한 실행은 **단일 소스만** 계상하므로 합산 명제는 폐기되고
// "모드별 단일 소스 + 반대 소스 0"이라는 **더 강한 등식**으로 대체된다(PLAN §3.3.2 (D)).
// 이는 완화가 아니다 — 077은 `covered === inline + manifest` 등식 1개만 걸었지만, 아래 TS-024는
// ① 반대 소스 = 0 ② covered = 해당 모드 값 ③ 같은 픽스처에서 두 모드의 covered가 실제로 갈린다
// 는 3중 단언으로 고정한다. 077이 검증하던 위반 검출·git 2분류·`--changed` 필터·exclude 대칭 계약은
// 전부 아래에 승계되며 삭제·완화한 단언은 없다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
//
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.3.5/§3.2.5, TEST-SCENARIO.md §4):
//
// | 케이스 프리픽스 | TS-ID                                  | S-ID | 계층 | AC     |
// |-----------------|----------------------------------------|------|------|--------|
// | [T080/L2-F5]    | TS-024, TS-025, TS-026, TS-027, TS-029 | S-11 | L2   | F-5 AC |
// | [T080/L2-F9]    | TS-014, TS-015                         | S-7  | L2   | F-9 AC |
// | [T077-승계]      | (077 위반검출·git 2분류·--changed·exclude 대칭) | — | — | 회귀 보존 |
//
// exit code 계약(불변): 0=차단 위반 0건 / 1=스키마·사용법 오류 / 2=차단 위반 ≥1건.
// `uncovered:pre_existing`만 비차단(`code-scan.js:1638-1641`)이라는 정책도 불변이다(TS-027).
//
// RED-first: 현행 cmdValidate(`code-scan.js:1448-1659`)는 headerSource를 전혀 조회하지 않는다 —
// 커버리지는 항상 인라인+매니페스트 합산이고, 구조 패스는 모드와 무관하게 항상 돌며, 결과 스키마에
// `headerSource` 필드가 없고, 스코프 `include`/`exclude` 필터는 존재하지도 않는다. 따라서 아래
// 신 계약 케이스는 전부 실패해야 정상이다. 구현(GREEN)은 op-dev-execute가 Step 5·7에서 수행한다
// (작성자≠구현자, red-first.md §2).
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v1.1 2026-07-28 KST: [재작업 — 결함 B] --changed exclude/excludePatterns 미적용 RED 추가 (077)
//   v1.2 2026-07-29 KST: [추가작업 — 결함 D] scaffold 열거 ↔ validate 구조 패스 비대칭 RED 추가 (077)
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — 합산 커버리지 폐기 → 모드별 단일 소스(TS-024),
//     구조 패스 모드 분기(TS-026), headerSource 결과 필드(TS-029), 스코프 필터 존중 양방향
//     (TS-014/TS-015), 차단 정책 불변 회귀(TS-027). 077 자산은 전량 승계 (opal-test-agent mode:red)
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

/**
 * 커밋 픽스처를 임시 복사본으로 복제하고 `.opal/code-scan.json`의 최상위 `headerSource`만 교체한다.
 * 픽스처 자산은 절대 수정하지 않는다(PLAN §3.7.2) — 사전 조작은 오버레이로만 수행한다.
 * @param {string|null} headerSource null이면 커밋값 유지(복사만)
 */
function overlay(fixtureName, headerSource, tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t080-${tag || 'val'}-`));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureName), dir);
  if (headerSource !== null) {
    const cfgPath = path.join(dir, '.opal', 'code-scan.json');
    const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
    cfg.headerSource = headerSource;
    fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\n');
  }
  return dir;
}

const CODEMAP_REPO = path.join(FIX, 'codemap-repo');   // 커밋값 headerSource: "manifest"

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F5] TS-024 / TS-025 / TS-026 / TS-027 / TS-029 (S-11): 모드별 커버리지 — 합산 폐기
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F5] TS-024 (S-11): 동일 픽스처를 두 모드로 validate — 커버리지 분자가 각 모드 소스만 반영(합산 폐기)', () => {
  const inlineDir = overlay('codemap-repo', 'inline', 'cov-inline');
  const manifestDir = overlay('codemap-repo', 'manifest', 'cov-manifest');

  const inl = run(inlineDir, ['validate', '--json']);
  const man = run(manifestDir, ['validate', '--json']);

  assert.ok(inl.json && inl.json.coverage, `[RED expect] inline 모드 coverage 객체 존재, raw="${inl.stdout}"`);
  assert.ok(man.json && man.json.coverage, `[RED expect] manifest 모드 coverage 객체 존재, raw="${man.stdout}"`);

  // ① 반대 소스는 0이어야 한다 — 현행은 두 값을 항상 함께 채운다(합산). 이것이 RED의 핵심 지점이다.
  assert.strictEqual(inl.json.coverage.manifest, 0,
    `[RED expect] inline 모드에서 coverage.manifest는 0이어야 함(매니페스트를 읽지 않는다), got ${JSON.stringify(inl.json.coverage)}`);
  assert.strictEqual(man.json.coverage.inline, 0,
    `[RED expect] manifest 모드에서 coverage.inline은 0이어야 함(인라인을 읽지 않는다), got ${JSON.stringify(man.json.coverage)}`);

  // ② covered는 해당 모드 값 그 자체다 — "covered = inline + manifest" 합산 등식은 폐기된다.
  assert.strictEqual(inl.json.coverage.covered, inl.json.coverage.inline,
    `[RED expect] inline 모드: covered === coverage.inline, got ${JSON.stringify(inl.json.coverage)}`);
  assert.strictEqual(man.json.coverage.covered, man.json.coverage.manifest,
    `[RED expect] manifest 모드: covered === coverage.manifest, got ${JSON.stringify(man.json.coverage)}`);

  // ③ 분모(열거 결과)는 모드와 무관하다 — 모드는 "무엇을 소스로 보는가"만 바꾼다.
  assert.strictEqual(inl.json.coverage.total, man.json.coverage.total,
    `[RED expect] total(분모)은 두 모드에서 동일해야 함, inline=${inl.json.coverage.total} manifest=${man.json.coverage.total}`);

  // ④ 같은 픽스처에서 두 모드의 covered가 실제로 갈린다 — 갈리지 않으면 모드가 무시되고 있다는 뜻이다.
  //    codemap-repo에서 인라인 @header를 가진 파일은 AdminHome.tsx 1건뿐이다(픽스처 실측).
  assert.strictEqual(inl.json.coverage.inline, 1,
    `[RED expect] codemap-repo의 인라인 보유 파일은 AdminHome.tsx 1건뿐이다, got ${JSON.stringify(inl.json.coverage)}`);
  assert.notStrictEqual(inl.json.coverage.covered, man.json.coverage.covered,
    `[RED expect] 두 모드의 covered가 같다면 모드가 커버리지 판정에 반영되지 않은 것이다, ` +
    `inline=${JSON.stringify(inl.json.coverage)} manifest=${JSON.stringify(man.json.coverage)}`);
});

test('[T080/L2-F5] TS-025 (S-11): manifest 모드 — 인라인 부재가 위반으로 집계되지 않는다', () => {
  const dir = overlay('codemap-repo', 'manifest', 'no-inline-violation');
  const { json, stdout } = run(dir, ['validate', '--json']);

  assert.ok(json && Array.isArray(json.violations), `[RED expect] violations 배열 존재, raw="${stdout}"`);

  // 매니페스트로 커버되는 파일이 "인라인이 없다"는 이유로 uncovered에 잡히면 안 된다.
  const manifestCoveredFiles = [
    'svc/order-api/src/main/java/com/acme/order/service/OrderService.java',
    'svc/order-api/src/main/java/com/acme/order/service/PriceCalc.java',
    'web/admin/pages/AdminList.tsx',
    'legacy/lib/legacy_util.py',
  ];
  for (const f of manifestCoveredFiles) {
    const hit = json.violations.find(v => v.code === 'uncovered' && v.file === f);
    assert.strictEqual(hit, undefined,
      `[RED expect] ${f}는 매니페스트로 커버되므로 인라인 부재를 이유로 uncovered가 되면 안 됨, got ${JSON.stringify(hit)}`);
  }

  // conflict/inline_shadowed는 **양 모드 공통 유지**다(PLAN §3.3.2 (D) 각주) — 이 검출까지 사라지면 과잉 완화다.
  assert.ok(json.counts && typeof json.counts.conflict === 'number',
    `[RED expect] conflict 카운트는 manifest 모드에서도 계속 보고되어야 함, got ${JSON.stringify(json.counts)}`);
});

test('[T080/L2-F5] TS-026 (S-11): inline 모드 — 구조 패스 스킵으로 매니페스트 무결성 위반이 집계되지 않는다', () => {
  // violations/orphan은 manifest 모드에서 orphan 3건 + worker_scope_violation 2건을 내는 트리다(실측).
  // inline 모드에서는 매니페스트를 만들지도 읽지도 않으므로 검사 대상 자체가 없다.
  const manifestDir = overlay(path.join('violations', 'orphan'), 'manifest', 'struct-manifest');
  const inlineDir = overlay(path.join('violations', 'orphan'), 'inline', 'struct-inline');

  const man = run(manifestDir, ['validate', '--json']);
  const inl = run(inlineDir, ['validate', '--json']);

  // 대조군 — manifest 모드에서는 구조 위반이 실제로 검출된다(검출기 자체가 무력화되지 않았음을 고정).
  assert.ok(man.json && man.json.counts && man.json.counts.orphan > 0,
    `대조군: manifest 모드에서는 orphan이 검출되어야 함, got ${JSON.stringify(man.json && man.json.counts)}`);

  assert.ok(inl.json && inl.json.counts, `[RED expect] inline 모드 counts 존재, raw="${inl.stdout}"`);
  assert.strictEqual(inl.json.counts.orphan, 0,
    `[RED expect] inline 모드는 구조 패스를 스킵하므로 orphan 0건이어야 함, got ${JSON.stringify(inl.json.counts)}`);
  assert.strictEqual(inl.json.counts.worker_scope_violation, 0,
    `[RED expect] inline 모드는 worker_scope_violation 0건이어야 함, got ${JSON.stringify(inl.json.counts)}`);

  // 스킵을 조용히 하지 않는다 — "설정과 자산이 어긋나 있다"는 사실은 stderr 안내 1줄로 노출한다.
  assert.ok(/code-map/.test(inl.stderr),
    `[RED expect] inline 모드인데 .opal/code-map/ 매니페스트가 존재하면 stderr 안내 1줄이 나가야 함, got stderr="${inl.stderr}"`);
  assert.ok(!/code-map/.test(inl.stdout),
    `[RED expect] 안내가 stdout JSON을 오염시키면 안 됨, got stdout="${inl.stdout}"`);
});

test('[T080/L2-F5] TS-027 (S-11) [회귀]: uncovered:pre_existing만 비차단 · 나머지 차단 · exit 2 정책 불변', () => {
  // (a) 차단 — draft 위반이 있으면 모드와 무관하게 exit 2
  const draftDir = overlay(path.join('violations', 'draft'), 'manifest', 'policy-block');
  const blocked = run(draftDir, ['validate', '--json']);
  assert.strictEqual(blocked.exitCode, 2,
    `[회귀] 차단 위반(draft) 존재 → exit 2 정책 불변, got ${blocked.exitCode} (stdout: ${blocked.stdout})`);
  assert.strictEqual(blocked.json && blocked.json.ok, false, `[회귀] ok:false, got ${JSON.stringify(blocked.json)}`);

  // (b) 비차단 — pre_existing만 있는 트리는 exit 0 (git 미사용 임시 트리는 전량 pre_existing)
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-policy-nonblock-'));
  cleanupDirs.push(dir);
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-scan.json'), JSON.stringify({
    headerSource: 'inline',
    scopes: { svc: 'svc/' },
    extensions: ['.java'],
    exclude: ['node_modules', '.git'],
    excludePatterns: [],
  }, null, 2) + '\n');
  fs.mkdirSync(path.join(dir, 'svc', 'mod'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'svc', 'mod', 'Bare.java'), 'package svc.mod;\npublic class Bare {}\n');

  const nonblocked = run(dir, ['validate', '--json']);
  assert.strictEqual(nonblocked.exitCode, 0,
    `[회귀] pre_existing만 존재하면 비차단 exit 0 정책 불변, got ${nonblocked.exitCode} (stdout: ${nonblocked.stdout})`);
  assert.strictEqual(nonblocked.json && nonblocked.json.ok, true,
    `[회귀] ok:true, got ${JSON.stringify(nonblocked.json)}`);
  const hit = ((nonblocked.json && nonblocked.json.violations) || []).find(v => v.code === 'uncovered');
  assert.strictEqual(hit && hit.sub, 'pre_existing',
    `[회귀] 비차단이어도 violations[]에는 노출되어야 함(sub:'pre_existing'), got ${JSON.stringify(hit)}`);
});

test('[T080/L2-F5] TS-029 (S-11): validate --json 결과에 headerSource 필드가 포함된다', () => {
  const inlineDir = overlay('codemap-repo', 'inline', 'hsfield-inline');

  const man = run(CODEMAP_REPO, ['validate', '--json']);   // 커밋값 manifest
  const inl = run(inlineDir, ['validate', '--json']);

  assert.strictEqual(man.json && man.json.headerSource, 'manifest',
    `[RED expect] result.headerSource === 'manifest' — 소비자가 "어느 소스 기준의 커버리지인가"를 ` +
    `추측하지 않아도 되게 만드는 필드다(PLAN §3.3.2 (D) 결과 스키마), got ${JSON.stringify(man.json && man.json.headerSource)}`);
  assert.strictEqual(inl.json && inl.json.headerSource, 'inline',
    `[RED expect] result.headerSource === 'inline', got ${JSON.stringify(inl.json && inl.json.headerSource)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F9] TS-014 / TS-015 (S-7): 위반 검출기의 스코프 필터 존중 — 오탐·미탐 양방향
//
// 사전 상태는 PLAN §3.7.2 "TS별 사전 상태 고정표"를 그대로 따른다:
//   TS-014 = mixed-scope **커밋 상태** + manifest 오버레이 + 매니페스트 사전 조작 **없음**
//   TS-015 = mixed-scope **임시 복사본** + manifest 오버레이 + ship-svc/_root.json의
//            files["ShipRepo.java"] **삭제**
// 두 케이스가 같은 트리에서 반대 방향(오탐 금지 / 미탐 금지)을 각각 막는다.
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F9] TS-014 (S-7): include로 걸러진 형제 파일은 매니페스트에 없어도 files_key_removed로 집계되지 않는다 (오탐 금지)', () => {
  const dir = overlay('mixed-scope', 'manifest', 'filter-ok');
  const { json, stdout } = run(dir, ['validate', '--json']);

  assert.ok(json && Array.isArray(json.violations), `[RED expect] violations 배열 존재, raw="${stdout}"`);

  // VendorLegacy.java는 디스크에 실재하고 어느 매니페스트에도 등재되어 있지 않다.
  // 그러나 두 스코프의 include("Order*.java" / "Ship*.java") 어느 쪽에도 매칭되지 않으므로
  // 애초에 관리 대상이 아니다 — 구조 패스가 이를 "워커가 키를 지웠다"로 오탐하면 안 된다.
  const falsePositive = json.violations.find(v => v.sub === 'files_key_removed' && v.key === 'VendorLegacy.java');
  assert.strictEqual(falsePositive, undefined,
    `[RED expect] out-of-scope 미등재 파일이 files_key_removed로 오탐되면 안 됨(현행 listCodeFilesInDir는 ` +
    `확장자만 보고 스코프 필터를 전혀 적용하지 않는다), got ${JSON.stringify(falsePositive)}`);
  assert.strictEqual(json.counts && json.counts.worker_scope_violation, 0,
    `[RED expect] 커밋 상태 mixed-scope는 구조 위반 0건이 기준선이어야 함, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts && json.counts.orphan, 0,
    `[RED expect] orphan 0건(무관한 잡음 배제), got ${JSON.stringify(json.counts)}`);
});

test('[T080/L2-F9] TS-015 (S-7): 필터에 걸리지 않는 in-scope 미등재 파일은 여전히 files_key_removed로 검출된다 (미탐 금지)', () => {
  const dir = overlay('mixed-scope', 'manifest', 'filter-miss');

  // 사전 조작 — ship-svc 매니페스트에서 ShipRepo.java 엔트리 1개만 삭제한다.
  // (커밋 픽스처는 정상 상태를 유지하고, 위반 상태는 임시 복사본에서만 만든다 — PLAN §3.7.2)
  const manifestPath = path.join(dir, '.opal', 'code-map', 'ship-svc', '_root.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  assert.ok(manifest.files['ShipRepo.java'], '사전 조건: 커밋 픽스처에 ShipRepo.java 엔트리가 존재해야 함');
  delete manifest.files['ShipRepo.java'];
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');

  const { exitCode, json, stdout } = run(dir, ['validate', '--json']);

  assert.ok(json && Array.isArray(json.violations), `[RED expect] violations 배열 존재, raw="${stdout}"`);
  const removed = json.violations.filter(v => v.sub === 'files_key_removed');
  assert.strictEqual(removed.length, 1,
    `[RED expect] in-scope 미등재는 정확히 1건 검출되어야 함(필터 도입이 검출기를 무력화하면 게이트가 죽는다), got ${JSON.stringify(removed)}`);
  assert.strictEqual(removed[0].key, 'ShipRepo.java',
    `[RED expect] 검출된 key는 ShipRepo.java여야 함, got ${JSON.stringify(removed[0])}`);
  assert.strictEqual(exitCode, 2,
    `[RED expect] 구조 위반은 차단 대상이므로 exit 2, got ${exitCode}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T077-승계] 위반 검출 5종 · exports 대조 · --changed 2형식 · draft 흐름 · 워커 권한 경계
// (전량 manifest 모드 픽스처 — 077이 고정한 계약이 신 계약에서도 그대로 유효함을 보증한다)
// ═════════════════════════════════════════════════════════════════════════

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
  test(`[T077-승계] violations/${c.dir} — ${c.code}${c.sub ? ':' + c.sub : ''} 검출 + exit 2`, () => {
    const cwd = path.join(FIX, 'violations', c.dir);
    const { exitCode, json } = run(cwd, ['validate', '--json']);

    assert.strictEqual(exitCode, 2, `위반 존재 → exit 2, got ${exitCode}`);
    assert.ok(json && Array.isArray(json.violations), 'violations 배열 존재');
    const hit = json && json.violations.find(v => v.code === c.code && (!c.sub || v.sub === c.sub));
    assert.ok(hit, `${c.code}${c.sub ? ':' + c.sub : ''} 위반이 검출되어야 함, got ${JSON.stringify(json && json.violations)}`);
  });
}

test('[T077-승계] exports 대조 — 존재(통과)/미존재(exports_not_found)/주석내존재(통과, 계약된 한계)', () => {
  const cwd = path.join(FIX, 'violations', 'exports-missing');
  const { exitCode, json } = run(cwd, ['validate', '--json']);

  assert.strictEqual(exitCode, 2, `exit 2 (Missing.java 위반 존재), got ${exitCode}`);
  const violations = (json && json.violations) || [];

  const missingHit = violations.find(v => v.code === 'exports_not_found' && (v.file || '').includes('Missing.java'));
  assert.ok(missingHit, `Missing.java의 ghostExport가 exports_not_found로 검출되어야 함, got ${JSON.stringify(violations)}`);

  const existsHit = violations.find(v => v.code === 'exports_not_found' && (v.file || '').includes('Exists.java'));
  assert.strictEqual(existsHit, undefined, 'Exists.java의 realExport는 통과해야 함(위반 없음)');

  const commentOnlyHit = violations.find(v => v.code === 'exports_not_found' && (v.file || '').includes('CommentOnly.java'));
  assert.strictEqual(commentOnlyHit, undefined,
    '주석 안에만 존재하는 commentedExport는 "통과"로 계약됨(문법 파서 미도입) — 위반으로 잡히면 안 됨');
});

test('[T077-승계] --changed "csv" — 지정 파일만 판정, mode:"changed"', () => {
  const cwd = path.join(FIX, 'violations', 'draft');
  const { exitCode, json } = run(cwd, ['validate', '--changed', 'svc/mod/Draft.java', '--json']);

  assert.strictEqual(exitCode, 2, `지정 파일 자체가 draft 위반 → exit 2, got ${exitCode}`);
  assert.strictEqual(json && json.mode, 'changed', `mode: "changed", got ${JSON.stringify(json)}`);
});

test('[T077-승계] --changed - (stdin) — 개행 구분 목록 입력', () => {
  const cwd = path.join(FIX, 'violations', 'draft');
  const { exitCode, json } = run(cwd, ['validate', '--changed', '-', '--json'], 'svc/mod/Draft.java\n');

  assert.strictEqual(exitCode, 2, `exit 2, got ${exitCode}`);
  assert.strictEqual(json && json.mode, 'changed', `mode: "changed" (stdin 입력), got ${JSON.stringify(json)}`);
});

test('[T077-승계] violations/clean — 위반 0건, exit 0, ok:true', () => {
  const cwd = path.join(FIX, 'violations', 'clean');
  const { exitCode, json } = run(cwd, ['validate', '--json']);

  assert.strictEqual(exitCode, 0, `위반 0건 → exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `ok: true, got ${JSON.stringify(json)}`);
});

test('[T077-승계] draft 상태 exit 2 → description 채운 뒤 exit 0', () => {
  const dir = overlay(path.join('violations', 'draft'), null, 'draftflow');

  const before = run(dir, ['validate', '--json']);
  assert.strictEqual(before.exitCode, 2, `scaffold 직후(draft) → exit 2, got ${before.exitCode}`);

  const manifestPath = path.join(dir, '.opal', 'code-map', 'svc', 'mod.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.files['Draft.java'].description = '이제 채워진 설명';
  delete manifest.files['Draft.java'].draft;
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');

  const after = run(dir, ['validate', '--json']);
  assert.strictEqual(after.exitCode, 0, `채운 후 → exit 0, got ${after.exitCode}`);
});

test('[T077-승계] 워커 권한 경계 — 허용 필드만 수정된 매니페스트는 통과(exit 0)', () => {
  const cwd = path.join(FIX, 'violations', 'clean');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.counts && json.counts.worker_scope_violation, 0,
    `worker_scope_violation 0건, got ${JSON.stringify(json && json.counts)}`);
});

test('[T077-승계] 워커 권한 경계 — dir 조작 → worker_scope_violation:dir_mismatch, exit 2', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-dir');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `exit 2, got ${exitCode}`);
  const hit = json && json.violations && json.violations.find(v => v.code === 'worker_scope_violation' && v.sub === 'dir_mismatch');
  assert.ok(hit, `dir_mismatch 위반 검출, got ${JSON.stringify(json && json.violations)}`);
});

test('[T077-승계] 워커 권한 경계 — files 키 추가/삭제 → files_key_added / files_key_removed', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-files');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `exit 2, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'files_key_added'),
    `files_key_added 검출, got ${JSON.stringify(violations)}`);
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'files_key_removed'),
    `files_key_removed 검출, got ${JSON.stringify(violations)}`);
});

test('[T077-승계] 워커 권한 경계 — layer/domain/module 침범 거부 + 해석 결과 무시', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-layer');
  const { exitCode, json } = run(cwd, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `exit 2, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'layer_in_manifest'),
    `layer_in_manifest 검출, got ${JSON.stringify(violations)}`);
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'domain_in_manifest'),
    `domain_in_manifest 검출, got ${JSON.stringify(violations)}`);
  assert.ok(violations.some(v => v.code === 'worker_scope_violation' && v.sub === 'module_override'),
    `module_override 검출, got ${JSON.stringify(violations)}`);

  const scanResult = run(cwd, ['scan', '--json']);
  const key = 'svc/mod/Tampered.java';
  assert.ok(scanResult.json && scanResult.json[key], `${key} scan 결과 존재`);
  assert.strictEqual(scanResult.json[key] && scanResult.json[key].layer, 'util',
    `침범된 package.layer("service")가 무시되고 layerRules(util)가 적용되어야 함, got ${JSON.stringify(scanResult.json && scanResult.json[key])}`);
});

// ─────────────────────────────────────────────────────────────────────────
// [T077-승계] uncovered 2분류 — newly_uncovered(차단) / pre_existing(비차단)
// 실 파일시스템 + 실 git 임시 트리만 사용한다(mock 금지). 이 저장소의 git 상태는 건드리지 않는다.
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

/** 게이트 통과를 위해 headerSource를 명시한다 — 이 그룹의 검증 대상은 uncovered 분류이지 게이트가 아니다. */
function writeGitClassConfig(dir, extra) {
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-scan.json'), JSON.stringify(Object.assign({
    headerSource: 'inline',
    scopes: { svc: 'svc/' },
    extensions: ['.java'],
    exclude: ['node_modules', '.git'],
    excludePatterns: [],
  }, extra || {}), null, 2) + '\n');
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

test('[T077-승계] 신규(untracked) 헤더 없는 파일 → uncovered:newly_uncovered + exit 2', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-gituncov-new-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/BrandNew.java', { withHeader: false });

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `untracked 신규 헤더 없는 파일 → exit 2, got ${exitCode}`);
  const hit = ((json && json.violations) || []).find(v => v.code === 'uncovered' && v.file === 'svc/mod/BrandNew.java');
  assert.ok(hit, `BrandNew.java uncovered 위반이 검출되어야 함, got ${JSON.stringify(json && json.violations)}`);
  assert.strictEqual(hit.sub, 'newly_uncovered', `sub:'newly_uncovered', got ${JSON.stringify(hit)}`);
  assert.strictEqual(json.counts.newly_uncovered, 1, `counts.newly_uncovered === 1, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.pre_existing, 0, `counts.pre_existing === 0, got ${JSON.stringify(json.counts)}`);
});

test('[T077-승계] HEAD엔 헤더 있었으나 현재 제거(회귀) → uncovered:newly_uncovered + exit 2', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-gituncov-regress-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  const abs = writeJavaFile(dir, 'svc/mod/HadHeader.java', { withHeader: true });
  git(dir, ['add', '.']);
  const c = git(dir, ['commit', '-q', '-m', 'add HadHeader with header']);
  if (c.status !== 0) throw new Error(`git commit failed: ${c.stderr}`);

  fs.writeFileSync(abs, 'package svc.mod;\npublic class HadHeader {}\n');

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `HEAD 대비 헤더 회귀 → exit 2, got ${exitCode}`);
  const hit = ((json && json.violations) || []).find(v => v.code === 'uncovered' && v.file === 'svc/mod/HadHeader.java');
  assert.ok(hit, `HadHeader.java uncovered 위반 검출, got ${JSON.stringify(json && json.violations)}`);
  assert.strictEqual(hit.sub, 'newly_uncovered', `sub:'newly_uncovered', got ${JSON.stringify(hit)}`);
});

test('[T077-승계] HEAD에도 헤더 없던 기존 파일 → uncovered:pre_existing + exit 0(비차단)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-gituncov-legacy-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/AlwaysBare.java', { withHeader: false });
  git(dir, ['add', '.']);
  const c = git(dir, ['commit', '-q', '-m', 'add AlwaysBare without header (pre-existing legacy state)']);
  if (c.status !== 0) throw new Error(`git commit failed: ${c.stderr}`);

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `기존 파일은 회귀가 아니므로 비차단 exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `ok:true, got ${JSON.stringify(json)}`);
  const hit = ((json && json.violations) || []).find(v => v.code === 'uncovered' && v.file === 'svc/mod/AlwaysBare.java');
  assert.strictEqual(hit && hit.sub, 'pre_existing', `sub:'pre_existing', got ${JSON.stringify(hit)}`);
  assert.strictEqual(json.counts.pre_existing, 1, `counts.pre_existing === 1, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.newly_uncovered, 0, `counts.newly_uncovered === 0, got ${JSON.stringify(json.counts)}`);
});

test('[T077-승계] 두 분류 혼재 — newly_uncovered 1건 + pre_existing 1건 → exit 2 + counts 양쪽 노출', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-gituncov-mixed-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/AlwaysBare2.java', { withHeader: false });
  git(dir, ['add', '.']);
  const c = git(dir, ['commit', '-q', '-m', 'add AlwaysBare2 without header']);
  if (c.status !== 0) throw new Error(`git commit failed: ${c.stderr}`);
  writeJavaFile(dir, 'svc/mod/NewOne.java', { withHeader: false });

  const { exitCode, json } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 2, `newly_uncovered가 1건이라도 있으면 전체 exit 2, got ${exitCode}`);
  const violations = (json && json.violations) || [];
  const newHit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/NewOne.java');
  const oldHit = violations.find(v => v.code === 'uncovered' && v.file === 'svc/mod/AlwaysBare2.java');
  assert.strictEqual(newHit && newHit.sub, 'newly_uncovered', `NewOne.java sub, got ${JSON.stringify(newHit)}`);
  assert.strictEqual(oldHit && oldHit.sub, 'pre_existing', `AlwaysBare2.java sub, got ${JSON.stringify(oldHit)}`);
  assert.strictEqual(json.counts.newly_uncovered, 1, `counts.newly_uncovered === 1, got ${JSON.stringify(json.counts)}`);
  assert.strictEqual(json.counts.pre_existing, 1, `counts.pre_existing === 1, got ${JSON.stringify(json.counts)}`);
});

test('[T077-승계] 비git 트리 — 전량 pre_existing + exit 0 + stderr 경고 1줄', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-gituncov-nogit-'));
  cleanupDirs.push(dir);
  writeGitClassConfig(dir);
  writeJavaFile(dir, 'svc/mod/NoGit.java', { withHeader: false });

  const { exitCode, json, stderr } = run(dir, ['validate', '--json']);
  assert.strictEqual(exitCode, 0, `git 미사용 환경은 전량 pre_existing으로 비차단 exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `ok:true, got ${JSON.stringify(json)}`);
  const hit = ((json && json.violations) || []).find(v => v.code === 'uncovered' && v.file === 'svc/mod/NoGit.java');
  assert.strictEqual(hit && hit.sub, 'pre_existing', `sub:'pre_existing', got ${JSON.stringify(hit)}`);
  assert.ok(stderr && /git/i.test(stderr), `비git 환경 경고가 stderr에 출력되어야 함, got stderr="${stderr}"`);
});

// ─────────────────────────────────────────────────────────────────────────
// [T077-승계] `--changed`가 exclude / excludePatterns를 존중한다
// ─────────────────────────────────────────────────────────────────────────

test('[T077-승계] --changed: exclude 디렉토리명 하위 파일 → skipped[excluded_dir] + counts 무영향 + exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-changed-excldir-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir, { exclude: ['node_modules', '.git', 'fixtures'] });
  writeJavaFile(dir, 'svc/mod/fixtures/Sample.java', { withHeader: false });

  const { exitCode, json } = run(dir, ['validate', '--changed', 'svc/mod/fixtures/Sample.java', '--json']);

  assert.strictEqual(exitCode, 0, `exclude 디렉토리 하위 경로는 판정에서 제외 → exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.ok, true, `ok:true, got ${JSON.stringify(json)}`);
  assert.strictEqual(json.counts.uncovered, 0, `counts.uncovered === 0, got ${JSON.stringify(json.counts)}`);
  const skipHit = ((json && json.skipped) || []).find(s => s && s.file === 'svc/mod/fixtures/Sample.java');
  assert.ok(skipHit, `skipped[]에 기록되어야 함, got ${JSON.stringify(json && json.skipped)}`);
  assert.strictEqual(skipHit.reason, 'excluded_dir', `사유는 'excluded_dir', got ${JSON.stringify(skipHit)}`);
});

test('[T077-승계] --changed: excludePatterns 매치 파일 → skipped[excluded_pattern] + counts 무영향 + exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-changed-exclpat-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir, { excludePatterns: ['*.generated.java'] });
  const abs = path.join(dir, 'svc', 'mod', 'Sample.generated.java');
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, 'package svc.mod;\npublic class Sample {}\n');

  const { exitCode, json } = run(dir, ['validate', '--changed', 'svc/mod/Sample.generated.java', '--json']);

  assert.strictEqual(exitCode, 0, `excludePatterns 매치 경로는 판정에서 제외 → exit 0, got ${exitCode}`);
  assert.strictEqual(json.counts.uncovered, 0, `counts.uncovered === 0, got ${JSON.stringify(json.counts)}`);
  const skipHit = ((json && json.skipped) || []).find(s => s && s.file === 'svc/mod/Sample.generated.java');
  assert.ok(skipHit, `skipped[]에 기록되어야 함, got ${JSON.stringify(json && json.skipped)}`);
  assert.strictEqual(skipHit.reason, 'excluded_pattern', `사유는 'excluded_pattern', got ${JSON.stringify(skipHit)}`);
});

test('[T077-승계] --changed 대조군: exclude 미매치 신규 헤더 없는 파일은 여전히 newly_uncovered + exit 2', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-changed-control-'));
  cleanupDirs.push(dir);
  initGitRepo(dir);
  writeGitClassConfig(dir, { excludePatterns: ['*.generated.java'] });
  writeJavaFile(dir, 'svc/mod/Control.java', { withHeader: false });

  const { exitCode, json } = run(dir, ['validate', '--changed', 'svc/mod/Control.java', '--json']);

  assert.strictEqual(exitCode, 2, `대조군: exclude 미매치 신규 헤더 없는 파일은 여전히 차단, got ${exitCode}`);
  const hit = ((json && json.violations) || []).find(v => v.code === 'uncovered' && v.file === 'svc/mod/Control.java');
  assert.strictEqual(hit && hit.sub, 'newly_uncovered', `대조군 sub:'newly_uncovered', got ${JSON.stringify(hit)}`);
  assert.strictEqual(((json && json.skipped) || []).length, 0,
    `대조군: exclude 미매치 파일은 skipped[]에 나타나면 안 됨, got ${JSON.stringify(json && json.skipped)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// [T077-승계] scaffold 열거 ↔ validate 구조 패스 필터 대칭 (결함 D 재발 방지)
// ─────────────────────────────────────────────────────────────────────────

test('[T077-승계] exclude 3종으로 정당히 제외된 파일은 files_key_removed로 오탐되지 않는다 (대칭 불변식)', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-exclude-symmetry');
  const { json } = run(cwd, ['validate', '--json']);

  const violations = (json && json.violations) || [];
  assert.strictEqual(violations.filter(v => v.code === 'orphan').length, 0,
    `orphan은 0건이어야 함(무관한 잡음), got ${JSON.stringify(violations.filter(v => v.code === 'orphan'))}`);
  assert.strictEqual(violations.filter(v => v.sub === 'files_key_added').length, 0,
    `files_key_added는 0건이어야 함, got ${JSON.stringify(violations.filter(v => v.sub === 'files_key_added'))}`);
  assert.strictEqual(violations.filter(v => v.sub === 'files_key_removed').length, 0,
    `excludePatterns/config.exclude/index.exclude로 정당히 제외된 파일은 오탐 없이 통과해야 함, ` +
    `got ${JSON.stringify(violations.filter(v => v.sub === 'files_key_removed'))}`);
});

test('[T077-승계] index.exclude 전용 디렉토리(svc/vendor)의 파일도 오탐되지 않는다 (union 검증)', () => {
  const cwd = path.join(FIX, 'violations', 'worker-scope-exclude-symmetry');
  const { json } = run(cwd, ['validate', '--json']);

  const hit = ((json && json.violations) || []).find(v =>
    v.sub === 'files_key_removed' && v.key === 'Nested.java' && v.manifest === '.opal/code-map/svc/vendor.json');
  assert.strictEqual(hit, undefined,
    `"vendor"는 index.exclude 전용이므로 제외 대상 — files_key_removed가 발생하면 안 됨, got ${JSON.stringify(hit)}`);
});

test('[T077-승계] 대조군: 제외 대상 아닌 신규 미등재 파일은 여전히 files_key_removed로 검출된다', () => {
  const dir = overlay(path.join('violations', 'worker-scope-exclude-symmetry'), null, 'exclsym-control');
  fs.writeFileSync(path.join(dir, 'svc', 'mod', 'Rogue.java'), 'package svc.mod;\npublic class Rogue {}\n');

  const { exitCode, json } = run(dir, ['validate', '--json']);

  assert.strictEqual(exitCode, 2, `대조군: 위반이 존재하므로 exit 2, got ${exitCode}`);
  const hit = ((json && json.violations) || []).find(v =>
    v.sub === 'files_key_removed' && v.key === 'Rogue.java' && v.manifest === '.opal/code-map/svc/mod.json');
  assert.ok(hit,
    `대조군: 제외 대상이 아닌 Rogue.java는 files_key_removed로 정상 검출되어야 함(게이트 무력화 방지), got ${JSON.stringify(json && json.violations)}`);
});
