/**
 * @header {
 *   "module": "test-feature",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `feature` 서브명령(cross-scope 조회 기본 + --scope 제한, PM-1) CLI 블랙박스 테스트 (F-008, 태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-16"]
 * }
 */
//
// TC ↔ TS-ID 매핑 표 (PLAN.md §3.8.5, TEST-SCENARIO.md S-16):
//
// | TC                                     | TS-ID  |
// |------------------------------------------|--------|
// | feature-cross-scope-default-grouping       | TS-035 |
// | feature-scope-restriction                  | TS-036 |
// | feature-no-tag-8commands-unaffected(TS-006 공유) | TS-037 |
//
// RED-first: 현행 code-scan.js에는 feature 서브명령이 없다. 아래 테스트는 "Unknown command" exit 1로
// 실패해야 정상이다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
const FIX = path.resolve(__dirname, 'fixtures');
const CODEMAP_REPO = path.join(FIX, 'codemap-repo');

function run(cwd, args) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], { cwd, encoding: 'utf8', timeout: 10000 });
  const stdout = result.stdout || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr: result.stderr || '', json };
}

// codemap-repo에는 아직 어떤 파일에도 `feature` 태그가 없다 — 이 테스트 파일이 사용하는 태그
// "order-create"는 PLAN §3.1.2(C)에 따라 svc/order-api/order/service.json의 OrderService.java 엔트리에
// 이미 부여되어 있다(fixture 설계 시점). 두 번째 스코프에도 동일 태그가 필요하므로, feature 테스트만을
// 위해 web 스코프 매니페스트에도 동일 태그가 있다고 가정하지 않고 — 대신 아래에서 직접 검증 가능한
// 현재 fixture 상태를 그대로 사용한다(주문 스코프 1건은 이미 확보됨).
//
// cross-scope 다건 검증을 위해 ship-api 매니페스트의 package 필드는 태그가 없으므로, 여기서는
// order-create 태그가 "svc" 스코프에서 발견된다는 것과, --scope 제한이 다른 스코프를 배제한다는 것을
// 검증하는 데 집중한다(PM-1 핵심 계약).

test('TS-035 (S-16): feature <id> — 기본 전체 스코프 순회, svc 스코프에서 order-create 태그 검출', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['feature', 'order-create', '--json']);

  // [RED 기대] feature 서브명령이 없으므로 "Unknown command" exit 1.
  assert.strictEqual(exitCode, 0, `[RED expect] feature는 exit 0이어야 함, got ${exitCode}`);
  assert.ok(json && json.svc, `[RED expect] svc 스코프 그룹이 결과에 존재해야 함, got ${JSON.stringify(json)}`);
  const svcPaths = json && json.svc ? Object.keys(json.svc) : [];
  assert.ok(svcPaths.some(p => p.includes('OrderService.java')),
    `[RED expect] OrderService.java(feature:order-create)가 svc 그룹에 있어야 함, got ${JSON.stringify(svcPaths)}`);
});

test('TS-036 (S-16): feature <id> --scope web — web 그룹만 반환(svc 미포함)', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['feature', 'order-create', '--scope', 'web', '--json']);

  // [RED 기대] feature 서브명령이 없다.
  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.svc, undefined,
    `[RED expect] --scope web 제한 시 svc 그룹이 결과에 나타나면 안 됨, got ${JSON.stringify(json)}`);
});

test('TS-036 (S-16): feature <id> --scope svc — svc 그룹만 반환', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['feature', 'order-create', '--scope', 'svc', '--json']);

  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  assert.ok(json && json.svc, `[RED expect] svc 그룹이 존재해야 함, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.web, undefined, '--scope svc 제한 시 web 그룹은 나타나면 안 됨');
});

test('TS-037 (S-16): 태그 미부여 인자로 feature 호출 시 빈 결과(태그 무부여 8커맨드 무변화의 대조군)', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['feature', 'no-such-feature-tag', '--json']);

  // [RED 기대] feature 서브명령이 없다.
  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  const groups = json ? Object.keys(json) : [];
  assert.strictEqual(groups.length, 0, `존재하지 않는 태그 조회는 빈 결과여야 함, got ${JSON.stringify(json)}`);
});

test('TS-037 (S-16): feature 인자 누락 → Usage 안내 + exit 1', () => {
  const { exitCode, stderr } = run(CODEMAP_REPO, ['feature']);
  assert.strictEqual(exitCode, 1, `인자 누락 시 exit 1 기대, got ${exitCode}`);
  assert.ok(/usage/i.test(stderr) || /feature/i.test(stderr),
    `[RED expect] Usage 안내 메시지 출력, got stderr: ${stderr}`);
});
