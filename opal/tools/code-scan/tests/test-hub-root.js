/**
 * @header {
 *   "module": "test-hub-root",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "task": "118",
 *   "scenarios": ["S-18"],
 *   "description": "findProjectRoot() 착지 계약 회귀 스위트(D-7, W-8). (1) 자기완결(.opal 보유) 워크트리 cwd는 그 자신에 착지해 config가 해석되고(header_source_unset 미발생), (2) 자기완결이 아닌 워크트리 cwd는 허브에 착지해 허브 config가 해석되며, (3) 조상 어디에도 .opal이 없으면 위치를 발명하지 않아 header_source_unset이 그대로 남고, (4) 착지 판정은 findProjectRoot() 단일 경로이며 별도의 허브 수렴 헬퍼는 export되지 않는다.",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"]
 * }
 */
//
// 이 스위트는 findProjectRoot() 착지 계약만 검증한다(D-7, W-8). 허브 수렴 헬퍼와 그
// 골든 케이스 표는 제거됐으므로 골든표 문자열 동치 케이스(TS-011/012, 태스크 109)와
// 헬퍼 소비 블랙박스 케이스(TS-022 계열, 태스크 109)는 더 이상 존재하지 않는다.
// 착지·알림 계약 원문: opal/core/references/harness/worktree.md §task root와 allocator root 계약.
// 관련 블랙박스 회귀 가드(알림 stderr 포함): tests/test-scan-root-landing.js (S-18).
//
// 변경이력:
//   v1.0 2026-09-07 KST: RED-first 최초 작성 (태스크 109, opal-test-agent mode:red)
//   v1.1 2026-09-07 KST: 정정 3 TS-012(Node) 신설 + 정정 5 TS-022 음성 리터럴 우선 재설계 (109)
//   v2.0 2026-09-12 KST: 허브 수렴 헬퍼 제거(D-7)에 따라 골든표·블랙박스 케이스를
//     findProjectRoot() 착지 계약 테스트로 전량 교체 (118 W-8)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
// [MUST] 083부터 spawnSync 사용 테스트는 OPAL_HOME을 주입해 개발자 실제 홈 setting.json의
// 영향을 차단해야 한다(U-7, test-shard-policy.js TS-084).
const HOME_ABSENT = path.resolve(__dirname, 'fixtures', 'shard-policy', 'homes', 'absent');

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

function mkTemp(tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t118-hubroot-${tag}-`));
  cleanupDirs.push(dir);
  return dir;
}

function writeCodeScanConfig(dir) {
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.writeFileSync(
    path.join(dir, '.opal', 'code-scan.json'),
    JSON.stringify({ headerSource: 'inline' }, null, 2) + '\n',
  );
}

/** code-scan.js CLI 블랙박스 실행 — 실 subprocess만 사용(mock/monkeypatch 없음). */
function run(cwd, args) {
  const r = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 20000, env: { ...process.env, OPAL_HOME: HOME_ABSENT },
  });
  const stdout = r.stdout || '';
  const stderr = r.stderr || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* 비-JSON 출력 */ }
  return { exitCode: r.status, stdout, stderr, json };
}

// ─────────────────────────────────────────────────────────────────────────
// findProjectRoot() 착지 계약 — 리터럴 우선: 자기완결 워크트리는 그 자신이 루트다
// ─────────────────────────────────────────────────────────────────────────

test('[T118/RootContract] 자기완결(.opal 보유) 워크트리 cwd는 그 자신에 착지해 config를 해석한다', () => {
  const hub = mkTemp('literal-hub');
  writeCodeScanConfig(hub);

  // 허브 아래 .opal-worktrees 하위에 놓였지만 자기 .opal/을 가진 자기완결 프로젝트(픽스처
  // 재현). 정규화가 이를 허브로 납치하면 안 되고, 자기 자신의 .opal/을 우선 발견해야 한다.
  const selfContainedDir = path.join(hub, '.opal-worktrees', 'task_003', 'nested-project');
  writeCodeScanConfig(selfContainedDir);

  const { json, stderr } = run(selfContainedDir, ['validate']);

  const errorCode = json && json.error;
  assert.notEqual(errorCode, 'header_source_unset',
    `자기 .opal/을 가진 자기완결 프로젝트는 리터럴 우선으로 그 자신이 루트여야 한다. ` +
    `json=${JSON.stringify(json)} stderr=${stderr}`);
});

// ─────────────────────────────────────────────────────────────────────────
// findProjectRoot() 착지 계약 — 자기완결이 아니면 허브로 착지한다
// ─────────────────────────────────────────────────────────────────────────

test('[T118/RootContract] 자기완결이 아닌(자기 .opal 없는) 워크트리 cwd는 허브로 착지해 허브 config를 해석한다', () => {
  const hub = mkTemp('bare-hub');
  writeCodeScanConfig(hub);

  const worktreeDir = path.join(hub, '.opal-worktrees', 'task_001');
  fs.mkdirSync(worktreeDir, { recursive: true });
  // [MUST] 실제 git worktree의 .git은 디렉터리가 아니라 gitdir 포인터를 담은 파일이다.
  // fs.existsSync는 파일/디렉터리를 구분하지 않으므로 이 재현이 판정의 핵심이다.
  fs.writeFileSync(
    path.join(worktreeDir, '.git'),
    `gitdir: ${path.join(hub, '.git', 'worktrees', 'task_001')}\n`,
  );
  assert.equal(fs.statSync(path.join(worktreeDir, '.git')).isFile(), true,
    '픽스처 전제 위반: .git이 디렉터리로 생성됨 — 워크트리 재현 실패');

  const { json, stderr } = run(worktreeDir, ['validate']);

  const errorCode = json && json.error;
  assert.notEqual(errorCode, 'header_source_unset',
    `findProjectRoot()가 워크트리 자신을 프로젝트 루트로 오인해 허브의 .opal/code-scan.json을 ` +
    `발견하지 못하면 header_source_unset이 난다. json=${JSON.stringify(json)} stderr=${stderr}`);
});

// ─────────────────────────────────────────────────────────────────────────
// findProjectRoot() 착지 계약 — 음성 케이스: 위치를 발명하지 않는다(리터럴 우선, 소유자 결정)
// ─────────────────────────────────────────────────────────────────────────
//
// [MUST] 소유자(캡틴) 결정(109): "워크트리 설정은 절대 읽지 않는다"는 절대 우선순위가 아니다.
// cwd에서 상향 탐색해 자기 .opal/을 가진 루트를 만나면 그것이 프로젝트 루트다(리터럴 우선).
// 보존해야 할 진짜 불변식은 "설정 위치를 발명하지 않는다" — cwd의 어떤 조상에도 .opal/이
// 없으면(허브 포함) header_source_unset이 그대로 나야 한다(다른 것으로 조용히 대체하지 않는다).

test('[T118/RootContract] 조상 어디에도 .opal/이 없으면 위치를 발명하지 않고 header_source_unset이 그대로 난다', () => {
  const hub = mkTemp('negative-hub');
  // 허브에도, 워크트리에도 .opal/을 두지 않는다 — 프로젝트 루트를 발명할 대상 자체가 없다.

  const worktreeDir = path.join(hub, '.opal-worktrees', 'task_002');
  fs.mkdirSync(worktreeDir, { recursive: true });
  fs.writeFileSync(
    path.join(worktreeDir, '.git'),
    `gitdir: ${path.join(hub, '.git', 'worktrees', 'task_002')}\n`,
  );
  assert.equal(fs.statSync(path.join(worktreeDir, '.git')).isFile(), true);

  const { json, stderr } = run(worktreeDir, ['validate']);

  const errorCode = json && json.error;
  assert.equal(errorCode, 'header_source_unset',
    `조상 어디에도 .opal/이 없으면 정규화가 다른 위치를 대신 발명해서는 안 되고 ` +
    `header_source_unset이 나야 한다. json=${JSON.stringify(json)} stderr=${stderr}`);
});

// ─────────────────────────────────────────────────────────────────────────
// 허브 수렴 헬퍼 부재 집행 — @header exports·module.exports 양쪽 정합
// ─────────────────────────────────────────────────────────────────────────

test('[T118/RootContract] hubRootFromPath는 더 이상 export되지 않고, findProjectRoot만 남는다', () => {
  // eslint-disable-next-line global-require
  const codeScan = require(CODE_SCAN_JS);
  assert.equal('hubRootFromPath' in codeScan, false,
    'hubRootFromPath()는 D-7에 따라 제거되어야 하며 module.exports에도 남아있으면 안 된다');
  assert.equal(typeof codeScan.findProjectRoot, 'function',
    'findProjectRoot는 계속 export되어야 한다');
});
