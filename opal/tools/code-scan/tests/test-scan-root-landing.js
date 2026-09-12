/**
 * @header {
 *   "module": "test-scan-root-landing",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "task": "118",
 *   "scenarios": ["S-18"],
 *   "description": "D-7(code-scan 허브 수렴 헬퍼 제거) 계약의 블랙박스 착지·알림 테스트. (a) 허브 cwd 실행의 stdout·stderr 결정론 회귀 가드, (b) 워크트리 cwd 실행이 자기 완결(.opal 보유) 워크트리 루트에 착지하고 no-notice, 자기완결이 아니면 허브로 착지하고 stderr 1줄 알림이 나옴을 검증한다.",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"]
 * }
 */
//
// [기록 — 블랙박스 불변 계약, TASK.md C-1]
//   이 스위트는 D-7 전후로 **관측 결과가 바뀌지 않아야 한다**는 회귀 가드다. D-7이
//   제거한 것은 착지·알림 판정 로직 자체가 아니라 그 판정에 쓰이던 내부 허브 수렴
//   헬퍼이므로, 내부 구현을 걷어내도 아래 두 서브시나리오의 외부 관측은 동일하다.
//   S-18(a) test_hub_cwd_scan_is_deterministic_no_notice: 허브 cwd 실행은 stderr
//     알림이 없고 stdout이 결정론적이다.
//   S-18(b) test_worktree_landing_and_notice_matrix: 자기완결(.opal 보유) 워크트리는
//     자신에 착지하고 알림이 없으며, 비자기완결 워크트리는 허브에 착지하고 stderr
//     알림이 정확히 1줄 나온다.
//   착지 계약 원문: opal/core/references/harness/worktree.md §task root와 allocator root 계약.
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

function mkTemp(tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t118-s18-${tag}-`));
  cleanupDirs.push(dir);
  return dir;
}

function writeCodeScanConfig(opalDir) {
  fs.mkdirSync(opalDir, { recursive: true });
  fs.writeFileSync(
    path.join(opalDir, 'code-scan.json'),
    JSON.stringify({ headerSource: 'inline' }, null, 2) + '\n',
  );
}

/** code-scan.js CLI 블랙박스 실행 — 실 subprocess만 사용(mock/monkeypatch 없음). */
function run(cwd, args) {
  const r = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 20000,
  });
  return { exitCode: r.status, stdout: r.stdout || '', stderr: r.stderr || '' };
}

// ─────────────────────────────────────────────────────────────────────────
// S-18(a) — 허브 cwd 실행 회귀 보호
// ─────────────────────────────────────────────────────────────────────────

test('[T118/S-18a] 허브 cwd 실행은 stderr 워크트리 알림이 없고 반복 실행 시 stdout·stderr가 바이트 동일하다', () => {
  const hub = mkTemp('hub-a');
  writeCodeScanConfig(path.join(hub, '.opal'));

  const first = run(hub, ['scan']);
  const second = run(hub, ['scan']);

  assert.equal(first.exitCode, 0, `허브 scan이 비정상 종료했다: stderr=${first.stderr}`);
  assert.equal(first.stderr, '', `허브 cwd 실행에 예상치 못한 stderr가 있다: ${first.stderr}`);
  assert.equal(
    first.stdout, second.stdout,
    '[FIX-PIN S-18a] 같은 허브 cwd에서 반복 실행한 stdout이 바이트 동일하지 않다',
  );
  assert.equal(
    first.stderr, second.stderr,
    '[FIX-PIN S-18a] 같은 허브 cwd에서 반복 실행한 stderr가 바이트 동일하지 않다',
  );
});

// ─────────────────────────────────────────────────────────────────────────
// S-18(b) — 워크트리 cwd 착지·알림 매트릭스
// ─────────────────────────────────────────────────────────────────────────

test('[T118/S-18b] 자기완결(.opal 보유) 워크트리 cwd는 자신에 착지하고 알림이 없다', () => {
  const hub = mkTemp('hub-b1');
  writeCodeScanConfig(path.join(hub, '.opal'));

  const worktreeDir = path.join(hub, '.opal-worktrees', 'task_s18_selfcontained');
  writeCodeScanConfig(path.join(worktreeDir, '.opal'));
  fs.writeFileSync(
    path.join(worktreeDir, '.git'),
    `gitdir: ${path.join(hub, '.git', 'worktrees', 'task_s18_selfcontained')}\n`,
  );
  assert.equal(fs.statSync(path.join(worktreeDir, '.git')).isFile(), true,
    '픽스처 전제 위반: .git이 디렉터리로 생성됨 — 워크트리 재현 실패');

  const { stderr, exitCode } = run(worktreeDir, ['scan']);
  assert.equal(exitCode, 0, `worktree scan이 비정상 종료했다: stderr=${stderr}`);
  assert.equal(
    stderr, '',
    `[FIX-PIN S-18b] 자기완결 워크트리 실행인데 stderr 알림이 나왔다: ${stderr}`,
  );
});

test('[T118/S-18b] 자기완결이 아닌(자기 .opal 없는) 워크트리 cwd는 허브로 착지하고 stderr 알림이 정확히 1줄 나온다', () => {
  const hub = mkTemp('hub-b2');
  writeCodeScanConfig(path.join(hub, '.opal'));

  const worktreeDir = path.join(hub, '.opal-worktrees', 'task_s18_bare');
  fs.mkdirSync(worktreeDir, { recursive: true });
  fs.writeFileSync(
    path.join(worktreeDir, '.git'),
    `gitdir: ${path.join(hub, '.git', 'worktrees', 'task_s18_bare')}\n`,
  );

  const { stderr, exitCode } = run(worktreeDir, ['scan']);
  assert.equal(exitCode, 0, `worktree scan이 비정상 종료했다: stderr=${stderr}`);

  const lines = stderr.split('\n').filter((l) => l.length > 0);
  assert.equal(
    lines.length, 1,
    `[FIX-PIN S-18b] 허브 착지 알림은 정확히 1줄이어야 한다 — 실제: ${JSON.stringify(lines)}`,
  );
  assert.match(
    lines[0], /\[worktree\]/,
    `[FIX-PIN S-18b] 허브 착지 알림 문구가 없다: ${JSON.stringify(lines)}`,
  );
  assert.equal(
    lines[0].includes(hub), true,
    '[FIX-PIN S-18b] 알림 문구에 실제 착지한 허브 경로가 없다',
  );
});
