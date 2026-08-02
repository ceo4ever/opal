/**
 * @header {
 *   "module": "test-feature",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `feature` 서브명령(cross-scope 조회 기본 + --scope 제한, 077 PM-1) 077 자산 유지 + 080 신 계약 정합(픽스처 headerSource manifest 명시·전 명령 차단 게이트 포함·--header-source 플래그 인자 소비) CLI 블랙박스 테스트 (F-008/F-001, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-1", "S-16"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 077이 고정한 `feature`의 계약(cross-scope 기본 순회 · `--scope` 제한 · 미부여 태그 빈 결과 ·
// 인자 누락 Usage+exit 1)은 080에서 **방향이 바뀌지 않는다**. 그대로 승계해 회귀 가드로 남긴다.
// 바뀌는 것은 이 계약이 성립하는 **전제**다.
//   (1) 픽스처 계약 — `codemap-repo`는 이제 `headerSource: "manifest"`를 명시해야 한다(H-9). 명시가
//       빠지면 게이트 도입 즉시 이 파일의 전 케이스가 exit 1로 붕괴한다. 그래서 "왜 통과하는지"를
//       설정 단언으로 먼저 고정한다 — 통과의 근거가 픽스처에 있음을 검사로 못 박는다.
//   (2) `feature`는 조회 8커맨드가 아니지만 **전 명령 차단 게이트의 대상**이다(D-5, F-2 AC). 미설정
//       트리에서 조용히 동작하면 게이트가 "전 명령"이 아니게 된다.
//   (3) `--header-source <inline|manifest>`는 **인자를 소비하는 플래그**다. 현행 parseArgs는 이를
//       모르므로 값 `manifest`가 commandArg로 흘러들어 태그 인자를 덮어쓴다 — 그래서 플래그를 태그
//       **앞**에 두는 케이스가 RED가 된다. 플래그 뒤에 두면 우연히 통과하므로 검증이 되지 않는다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다.
//
// [MUST] **TS-ID 네임스페이스** (PLAN §3.7.2 각주): 077의 TS-035~037(`feature`)과 본 태스크(080)의
// TS-035~037(`target` 배선, `test-target.js`)은 서로 다른 번호 체계다. 077 자산은 `077 TS-NNN`으로
// 표기한다 — 혼동하면 엉뚱한 테스트를 지운다.
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.7.1 #13, TEST-SCENARIO.md §3 S-1/S-16):
//
// | 케이스                                        | TS-ID          | S-ID | 현 시점 기대 |
// |-----------------------------------------------|----------------|------|--------------|
// | [T080/L2-H9] 픽스처 headerSource manifest 명시  | (H-9 선결)      | S-16 | PASS(Step 1 완료) |
// | 077 TS-035 cross-scope 기본 순회                | 077 TS-035     | S-16 | PASS(회귀 가드) |
// | 077 TS-036 --scope 제한 2건                     | 077 TS-036     | S-16 | PASS(회귀 가드) |
// | 077 TS-037 미부여 태그 · 인자 누락               | 077 TS-037     | S-16 | PASS(회귀 가드) |
// | [T080/L2-F2] feature 게이트 포함                | (F-2 AC 정합)   | S-1  | **RED**(게이트 미구현) |
// | [T080/L1-F1] --header-source 인자 소비           | (F-1 AC 정합)   | S-1  | **RED**(플래그 미구현) |
//
// [MUST] red-first.md §4 — 공개 인터페이스(실 CLI subprocess의 exit code · stdout JSON · stderr)로만
// 검증한다. mock 금지 — 실 픽스처 + 실 파일시스템 + 실 subprocess로만 동작한다.
// 커밋된 픽스처는 수정하지 않는다. 사전 조작은 전부 임시 복사본 오버레이로 하고 종료 시 파기한다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — 077 자산 5건 승계(TS-ID 네임스페이스 표기 교정) +
//     픽스처 headerSource 명시 단언(H-9)·전 명령 차단 게이트 포함(F-2)·--header-source 인자 소비
//     (F-1) 3건 신설 (opal-test-agent mode:red)
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
const CODEMAP_REPO = path.join(FIX, 'codemap-repo');

function run(cwd, args) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], { cwd, encoding: 'utf8', timeout: 20000 });
  const stdout = result.stdout || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr: result.stderr || '', json };
}

/**
 * 커밋된 픽스처를 임시 복사본으로 떠서 `.opal/code-scan.json`만 바꾼다.
 * mutate(config) === null 이면 headerSource 키를 제거한 설정을 쓴다.
 */
function overlay(fixtureDir, mutate) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 't080-feature-'));
  const dest = path.join(root, path.basename(fixtureDir));
  fs.cpSync(fixtureDir, dest, { recursive: true });
  const cfgPath = path.join(dest, '.opal', 'code-scan.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  fs.writeFileSync(cfgPath, JSON.stringify(mutate(cfg), null, 2) + '\n');
  return { root, dest };
}

// ─────────────────────────────────────────────────────────────────────────
// [T080/L2-H9] 픽스처 계약 — 이 파일의 전 케이스가 통과하는 근거
// ─────────────────────────────────────────────────────────────────────────

test('[T080/L2-H9] (S-16): codemap-repo 픽스처가 전역 headerSource "manifest"를 명시한다', () => {
  const cfg = JSON.parse(fs.readFileSync(path.join(CODEMAP_REPO, '.opal', 'code-scan.json'), 'utf8'));
  assert.strictEqual(cfg.headerSource, 'manifest',
    'auto 제거 후 매니페스트 검증 자산은 모드를 명시해야 한다 — 미명시면 게이트가 전 케이스를 차단한다 (H-9, PLAN §3.7.2)');
});

// ─────────────────────────────────────────────────────────────────────────
// 077 자산 유지 — feature 계약 회귀 가드 (077 PM-1)
//
// codemap-repo의 `feature: order-create` 태그는 svc 스코프
// (svc/order-api/order/service.json → OrderService.java)에만 부여되어 있다. cross-scope 순회의
// "다른 스코프 배제"는 --scope 제한 케이스로 확인한다.
// ─────────────────────────────────────────────────────────────────────────

test('077 TS-035 (S-16): feature <id> — 기본 전체 스코프 순회, svc 스코프에서 order-create 태그 검출', () => {
  const { exitCode, json, stderr } = run(CODEMAP_REPO, ['feature', 'order-create', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode} | stderr: ${stderr.slice(0, 200)}`);
  assert.ok(json && json.svc, `svc 스코프 그룹이 결과에 존재해야 함, got ${JSON.stringify(json)}`);
  const svcPaths = Object.keys(json.svc);
  assert.ok(svcPaths.some(p => p.includes('OrderService.java')),
    `OrderService.java(feature:order-create)가 svc 그룹에 있어야 함, got ${JSON.stringify(svcPaths)}`);
});

test('077 TS-036 (S-16): feature <id> --scope web — web 그룹만 반환(svc 미포함)', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['feature', 'order-create', '--scope', 'web', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(json && json.svc, undefined,
    `--scope web 제한 시 svc 그룹이 결과에 나타나면 안 됨, got ${JSON.stringify(json)}`);
});

test('077 TS-036 (S-16): feature <id> --scope svc — svc 그룹만 반환', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['feature', 'order-create', '--scope', 'svc', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.ok(json && json.svc, `svc 그룹이 존재해야 함, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.web, undefined, '--scope svc 제한 시 web 그룹은 나타나면 안 됨');
});

test('077 TS-037 (S-16): 태그 미부여 인자로 feature 호출 시 빈 결과', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['feature', 'no-such-feature-tag', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  const groups = json ? Object.keys(json) : [];
  assert.deepStrictEqual(groups, [], `존재하지 않는 태그 조회는 빈 결과여야 함, got ${JSON.stringify(json)}`);
});

test('077 TS-037 (S-16): feature 인자 누락 → Usage 안내 + exit 1', () => {
  const { exitCode, stderr } = run(CODEMAP_REPO, ['feature']);
  assert.strictEqual(exitCode, 1, `인자 누락 시 exit 1 기대, got ${exitCode}`);
  assert.ok(/usage/i.test(stderr) || /feature/i.test(stderr), `Usage 안내 메시지 출력, got stderr: ${stderr}`);
});

// ─────────────────────────────────────────────────────────────────────────
// [T080/L2-F2] 신 계약 정합 — feature도 전 명령 차단 게이트의 대상이다 (D-5, S-1)
// ─────────────────────────────────────────────────────────────────────────

test('[T080/L2-F2] (S-1): headerSource 미설정 오버레이에서 feature가 header_source_unset으로 차단된다', () => {
  const { root, dest } = overlay(CODEMAP_REPO, (cfg) => { delete cfg.headerSource; return cfg; });
  try {
    const { exitCode, stdout, stderr, json } = run(dest, ['feature', 'order-create', '--json']);
    // [RED 기대] 게이트가 없으므로 현재는 exit 0 + 정상 조회 결과가 나온다.
    assert.strictEqual(exitCode, 1,
      `[RED expect] 차단 범위는 code-scan 전 명령이다 — feature만 예외가 되면 게이트가 "전 명령"이 아니게 된다 (D-5). ` +
      `exit 1 기대, got ${exitCode} | stdout: ${stdout.slice(0, 200)}`);
    assert.ok(json && json.ok === false && json.error === 'header_source_unset',
      `[RED expect] stdout에 {"ok":false,"error":"header_source_unset",...} 기대, got ${stdout.slice(0, 200)}`);
    assert.ok(/header_source_unset/.test(stderr),
      `[RED expect] stderr 병기가 없으면 subprocess 소비자에게 사유가 도달하지 않는다 (§3.1.2 (F)), got stderr: ${stderr.slice(0, 200)}`);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

// ─────────────────────────────────────────────────────────────────────────
// [T080/L1-F1] 신 계약 정합 — `--header-source`는 인자를 소비하는 플래그다 (S-1, 우선순위 2층)
// ─────────────────────────────────────────────────────────────────────────

test('[T080/L1-F1] (S-1): feature --header-source manifest <tag> — 플래그가 값을 소비하고 태그 인자를 덮어쓰지 않는다', () => {
  const baseline = run(CODEMAP_REPO, ['feature', 'order-create', '--json']);
  assert.strictEqual(baseline.exitCode, 0, `기준선 exit 0 기대, got ${baseline.exitCode}`);

  const { exitCode, stdout, json } = run(CODEMAP_REPO, ['feature', '--header-source', 'manifest', 'order-create', '--json']);
  // [RED 기대] 현행 parseArgs는 --header-source를 모르므로 값 "manifest"가 commandArg로 흘러들어
  // 태그가 "manifest"로 조회되고 빈 결과가 나온다.
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode} | stdout: ${stdout.slice(0, 200)}`);
  assert.deepStrictEqual(json, baseline.json,
    '[RED expect] --header-source는 값을 소비하는 플래그이며, 전역 config와 동일한 값을 주면 결과가 기준선과 같아야 한다 ' +
    '(우선순위 2층 — CLI > 전역, 모드는 실행당 1값)');
});

test('[T080/L1-F1] (S-1): 미설정 오버레이 + --header-source manifest — CLI 지정만으로 feature가 동작한다', () => {
  const { root, dest } = overlay(CODEMAP_REPO, (cfg) => { delete cfg.headerSource; return cfg; });
  try {
    const { exitCode, stdout, json } = run(dest, ['feature', '--header-source', 'manifest', 'order-create', '--json']);
    // [RED 기대] 플래그 미구현 → 태그가 "manifest"로 조회되어 빈 결과가 된다(게이트 도입 전).
    assert.strictEqual(exitCode, 0, `CLI 지정 시 미설정 프로젝트도 통과해야 함. exit 0 기대, got ${exitCode} | stdout: ${stdout.slice(0, 200)}`);
    assert.ok(json && json.svc && Object.keys(json.svc).some(p => p.includes('OrderService.java')),
      `[RED expect] CLI 플래그가 미설정 상태를 해소하는 비대화형 1회 지정 수단이다 (D-1), got ${stdout.slice(0, 200)}`);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
