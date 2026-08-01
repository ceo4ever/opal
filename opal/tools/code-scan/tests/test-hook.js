/**
 * @header {
 *   "module": "test-hook",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `code-map-hook.js` PostToolUse hook(조기 이탈 9단, fail-safe, claude-hooks.json 배선 공존) 테스트 (F-009, 태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-18"]
 * }
 */
//
// TC ↔ TS-ID 매핑 표 (PLAN.md §3.9.5, TEST-SCENARIO.md S-18):
//
// | TC                                              | TS-ID  |
// |-----------------------------------------------|--------|
// | hook-warns-on-unupdated-manifest                | TS-038 |
// | hook-silent-on-updated-manifest                 | TS-039 |
// | hook-silent-codemap-absent                       | TS-040 |
// | hook-silent-broken-json / bash-tool / missing-path | TS-041 |
// | claude-hooks-json-additive-entry                 | TS-042 |
//
// 조기 이탈 9단(PLAN §3.9.2(C)): ①JSON파싱실패 ②tool_name불일치 ③file_path부재 ④projectRoot탐색실패
// ⑤index.json부재 ⑥확장자불일치 ⑦write_to:inline ⑧매니페스트갱신완료 ⑨그외(경고)
//
// RED-first: `opal/tools/code-scan/code-map-hook.js` 파일 자체가 아직 존재하지 않는다. 아래 전 테스트는
// "파일 없음(spawnSync 실패 또는 MODULE_NOT_FOUND)"으로 실패해야 정상이다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const HOOK_JS = path.resolve(__dirname, '..', 'code-map-hook.js');
const FIX = path.resolve(__dirname, 'fixtures');
const CLAUDE_HOOKS_JSON = path.resolve(__dirname, '..', '..', '..', 'core', 'hooks', 'claude-hooks.json');

function copyDirRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDirRecursive(s, d);
    else fs.copyFileSync(s, d);
  }
}

function runHook(cwd, stdinPayload) {
  const result = spawnSync(process.execPath, [HOOK_JS], {
    cwd,
    input: typeof stdinPayload === 'string' ? stdinPayload : JSON.stringify(stdinPayload),
    encoding: 'utf8',
    timeout: 10000,
  });
  return { exitCode: result.status, stdout: result.stdout || '', stderr: result.stderr || '', error: result.error };
}

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

// ─────────────────────────────────────────────────────────────────────────
// TS-038: 대상 파일 수정 + 매니페스트 미갱신 → 경고 출력, exit 0
// ─────────────────────────────────────────────────────────────────────────

test('TS-038 (S-18): 매니페스트 미갱신 대상 파일 이벤트 → additionalContext 경고 출력, exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-hook-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'draft'), dir); // Draft.java는 description 공백(미갱신 상태)

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Edit', tool_input: { file_path: abs } });

  // [RED 기대] code-map-hook.js 파일 자체가 없으므로 spawnSync가 ENOENT 에러를 반환한다.
  assert.strictEqual(error, undefined, `[RED expect] code-map-hook.js가 존재하고 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `[RED expect] hook은 항상 exit 0(fail-safe), got ${exitCode}`);
  assert.ok(stdout.trim().length > 0, '[RED expect] 미갱신 상태이므로 경고(additionalContext)가 출력되어야 함');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-039: 매니페스트 갱신 완료 상태 → stdout 0바이트, exit 0
// ─────────────────────────────────────────────────────────────────────────

test('TS-039 (S-18): 매니페스트 갱신 완료 상태 이벤트 → stdout 0바이트, exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-hook-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'clean'), dir); // Clean.java는 description 채워진 정상 상태

  const abs = path.join(dir, 'svc', 'mod', 'Clean.java');
  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Write', tool_input: { file_path: abs } });

  assert.strictEqual(error, undefined, `[RED expect] hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `[RED expect] 갱신 완료 상태는 무출력이어야 함, got: ${JSON.stringify(stdout)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-040: code-map 부재 트리 이벤트 → stdout 0바이트, exit 0 (5번 이탈)
// ─────────────────────────────────────────────────────────────────────────

test('TS-040 (S-18): code-map 부재 트리 이벤트 → stdout 0바이트, exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-hook-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'legacy-repo'), dir);

  const abs = path.join(dir, 'be', 'util', 'no_header.py');
  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Edit', tool_input: { file_path: abs } });

  assert.strictEqual(error, undefined, `[RED expect] hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `[RED expect] code-map 부재 시 무출력이어야 함(5번 이탈), got: ${JSON.stringify(stdout)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-041: 깨진 JSON / tool_name:Bash / file_path 부재 — 전부 무출력 exit 0
// ─────────────────────────────────────────────────────────────────────────

test('TS-041 (S-18): 깨진 stdin JSON → 무출력 exit 0 (fail-safe)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-hook-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'draft'), dir);

  const { exitCode, stdout, error } = runHook(dir, '{ this is not valid json');
  assert.strictEqual(error, undefined, `[RED expect] hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `무출력 기대, got: ${JSON.stringify(stdout)}`);
});

test('TS-041 (S-18): tool_name:"Bash" 이벤트 → 무출력 exit 0 (matcher 이중 방어)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-hook-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'draft'), dir);

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Bash', tool_input: { command: `cat ${abs}` } });
  assert.strictEqual(error, undefined, `[RED expect] hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `무출력 기대, got: ${JSON.stringify(stdout)}`);
});

test('TS-041 (S-18): file_path 부재 이벤트 → 무출력 exit 0', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-hook-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'draft'), dir);

  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Edit', tool_input: {} });
  assert.strictEqual(error, undefined, `[RED expect] hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `무출력 기대, got: ${JSON.stringify(stdout)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-042: claude-hooks.json — 기존 Bash 엔트리 + 신규 엔트리 공존
// ─────────────────────────────────────────────────────────────────────────

test('TS-042 (S-18): claude-hooks.json — PostToolUse 배열에 Bash 엔트리 + code-map-hook 엔트리 공존', () => {
  // [RED 기대] 신규 엔트리가 아직 배선되지 않았으므로 code-map-hook.js를 참조하는 엔트리가 없다.
  assert.ok(fs.existsSync(CLAUDE_HOOKS_JSON), `${CLAUDE_HOOKS_JSON} 파일이 존재해야 함`);
  const config = JSON.parse(fs.readFileSync(CLAUDE_HOOKS_JSON, 'utf8'));
  const postToolUse = config.PostToolUse || [];
  assert.ok(Array.isArray(postToolUse) && postToolUse.length > 0, 'PostToolUse 배열이 존재해야 함');

  const hasBash = postToolUse.some(e => e.matcher === 'Bash');
  assert.ok(hasBash, '기존 Bash matcher 엔트리가 보존되어야 함');

  const hasCodeMapHook = postToolUse.some(e =>
    (e.hooks || []).some(h => typeof h.command === 'string' && h.command.includes('code-map-hook.js'))
  );
  assert.ok(hasCodeMapHook,
    '[RED expect] code-map-hook.js를 가리키는 신규 PostToolUse 엔트리가 additive로 추가되어야 함');
});
