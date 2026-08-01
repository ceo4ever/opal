/**
 * @header {
 *   "module": "test-target",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `target` 서브명령(4단 기록 위치 판정 decideTarget, readonly 우선순위, code-map 부재 회귀) CLI 블랙박스 테스트 (F-005, 태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-12"]
 * }
 */
//
// TC ↔ TS-ID 매핑 표 (PLAN.md §3.5.5, TEST-SCENARIO.md S-12):
//
// | TC                                              | TS-ID  |
// |----------------------------------------------------|--------|
// | target-readonly-repo (legacy 스코프 신규/기존)       | TS-020, TS-022 |
// | target-inline-exists                                | TS-020 |
// | target-new-file                                     | TS-020 |
// | target-legacy-no-header                             | TS-020 |
// | target-manifest-path-key-scope-match                | TS-021 |
// | target-codemap-absent-always-inline (제약②)          | TS-023 |
//
// 판정 순서(확정 방향 6, PLAN §3.5.2 — 이 순서를 바꾸면 H-15 위반):
//   ① scope.readonly===true → manifest/readonly_repo
//   ② 인라인 존재 → inline/inline_exists
//   ③ 파일이 디스크에 없음 → inline/new_file
//   ④ 그 외(존재+인라인 없음) → manifest/legacy_no_header
//
// RED-first: 현행 code-scan.js에는 target 서브명령이 없다. 아래 전 테스트는 "Unknown command" exit 1로
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

function run(cwd, args) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], { cwd, encoding: 'utf8', timeout: 10000 });
  const stdout = result.stdout || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr: result.stderr || '', json };
}

const CODEMAP_REPO = path.join(FIX, 'codemap-repo');
const LEGACY_REPO = path.join(FIX, 'legacy-repo');

// ─────────────────────────────────────────────────────────────────────────
// TS-020 / TS-022: ① readonly_repo — legacy 스코프는 항상 manifest+readonly_repo
// ─────────────────────────────────────────────────────────────────────────

test('TS-020/022 (S-12): readonly 스코프(legacy) — 기존 파일도 manifest+readonly_repo', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['target', 'legacy/lib/legacy_util.py', '--json']);

  // [RED 기대] target 서브명령이 없으므로 "Unknown command" exit 1.
  assert.strictEqual(exitCode, 0, `[RED expect] target은 exit 0이어야 함, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'manifest', `[RED expect] write_to: manifest, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'readonly_repo', `[RED expect] reason: readonly_repo, got ${JSON.stringify(json)}`);
});

test('TS-020/022 (S-12): readonly 스코프(legacy) — 신규(디스크 부재) 파일도 readonly가 최우선', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['target', 'legacy/lib/NotYetCreated.py', '--json']);

  // [RED 기대] target 서브명령이 없다.
  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'manifest',
    `[RED expect] readonly가 신규 파일 여부보다 우선해야 함(판정 순서 ①이 ③보다 먼저), got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'readonly_repo', `got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-020: ② inline_exists — 인라인 헤더 보유 파일
// ─────────────────────────────────────────────────────────────────────────

test('TS-020 (S-12): 인라인 헤더 보유 파일(AdminHome.tsx) → inline/inline_exists', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['target', 'web/admin/pages/AdminHome.tsx', '--json']);

  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'inline', `[RED expect] write_to: inline, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'inline_exists', `[RED expect] reason: inline_exists, got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-020: ③ new_file — 디스크에 없는 신규 파일 (readonly 아닌 스코프)
// ─────────────────────────────────────────────────────────────────────────

test('TS-020 (S-12): 디스크에 없는 신규 파일(svc 스코프) → inline/new_file', () => {
  const { exitCode, json } = run(CODEMAP_REPO, ['target', 'svc/order-api/src/main/java/com/acme/order/service/BrandNew.java', '--json']);

  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'inline', `[RED expect] write_to: inline, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'new_file', `[RED expect] reason: new_file, got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-020/021: ④ legacy_no_header — 존재 + 인라인 없음 → manifest 경로/key/scope 동반
// ─────────────────────────────────────────────────────────────────────────

test('TS-020/021 (S-12): 존재+인라인없음(OrderService.java) → manifest/legacy_no_header + 경로 정합', () => {
  const rel = 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java';
  const { exitCode, json } = run(CODEMAP_REPO, ['target', rel, '--json']);

  assert.strictEqual(exitCode, 0, `[RED expect] exit 0, got ${exitCode}`);
  assert.strictEqual(json && json.write_to, 'manifest', `[RED expect] write_to: manifest, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.reason, 'legacy_no_header', `[RED expect] reason: legacy_no_header, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.scope, 'svc', `[RED expect] scope: svc, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.key, 'OrderService.java', `[RED expect] key: basename, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.manifest, '.opal/code-map/svc/order-api/order/service.json',
    `[RED expect] manifest 경로가 실제 미러 경로와 일치해야 함, got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-023 (제약②): code-map 부재 트리에서 target은 항상 inline
// ─────────────────────────────────────────────────────────────────────────

test('TS-023 (S-12): code-map 부재 트리(legacy-repo) — target은 항상 inline 반환', () => {
  const r1 = run(LEGACY_REPO, ['target', 'be/util/no_header.py', '--json']);
  const r2 = run(LEGACY_REPO, ['target', 'be/service/auth_service.py', '--json']); // 이미 인라인 보유
  const r3 = run(LEGACY_REPO, ['target', 'be/util/does_not_exist.py', '--json']);  // 신규

  // [RED 기대] target 서브명령이 없다.
  for (const [label, r] of [['legacy_no_header 후보', r1], ['inline 보유', r2], ['신규 파일', r3]]) {
    assert.strictEqual(r.exitCode, 0, `[RED expect] ${label}: exit 0, got ${r.exitCode}`);
    assert.strictEqual(r.json && r.json.write_to, 'inline',
      `[RED expect] code-map 부재 시 ${label} 케이스도 항상 inline이어야 함(제약②), got ${JSON.stringify(r.json)}`);
  }
});
