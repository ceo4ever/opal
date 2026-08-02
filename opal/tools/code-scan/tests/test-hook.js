/**
 * @header {
 *   "module": "test-hook",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `code-map-hook.js` PostToolUse fail-safe 계약(미설정·무효값·inline 모드 무출력 이탈, 조기 이탈 경로 stderr 0바이트, out_of_scope 파일 무출력, manifest 미갱신 경고 보존) + loadConfig 무종료 계약 산출물 검사 CLI 블랙박스 테스트 (F-005/F-002, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-2", "S-9"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 080은 `headerSource`를 전 명령 차단 게이트로 승격한다(D-5, exit 1). hook은 그 게이트의 **유일한
// 예외**다 — PostToolUse는 매 편집마다 실행되므로 미설정 프로젝트에서 에러를 뱉으면 세션 전체가
// 망가진다(TASK D-4·D-5 동반 필수 작업 ⑤, 077 PM-7).
// 따라서 아래 추가는 "덜 검사한다"가 아니라 **새로 생긴 실패 표면 3종(미설정 / 무효값 / inline)에
// 대해 무출력·exit 0을 새로 못 박는** 계약 신설이다. 동시에 077이 지키던 "미갱신 매니페스트에서는
// 경고가 정상 출력된다"(077 TS-038)를 TS-042로 **그대로 보존**한다 — 이것이 없으면 위 3종 무출력을
// "hook이 그냥 아무것도 안 한다"로 통과시킬 수 있고, 그 순간 hook의 존재 의의가 사라진다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다.
//
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.5.2/§3.5.5/§3.2.5, TEST-SCENARIO.md §3 S-2·S-9 / §4):
//
// | 케이스 프리픽스   | TS-ID                          | S-ID | 계층 | 검증 명제                                   |
// |-------------------|--------------------------------|------|------|--------------------------------------------|
// | [T080/L1-F12e]    | TS-040, TS-041, TS-042, TS-043 | S-2  | L1   | 미설정·무효값·inline 무출력 / manifest 경고 보존 |
// | [T080/L1-F12e]    | TS-076                         | S-2  | L1   | 조기 이탈 3종의 **stderr 0바이트**(무출력 = stdout+stderr) |
// | [T080/L1-F8c]     | TS-036                         | S-9  | L1   | out_of_scope 파일 무출력(`:136` 이탈 경로 보존) |
// | 077 TS-039/040/041/042 (승계)                  | —    | L1/L2 | 갱신 완료·code-map 부재·입력 이상 3종·배선 |
//
// [MUST] **TS-ID 네임스페이스** (PLAN §3.7.2 각주): 본 태스크(080) TS-040~043과 077 TS-040~042는
// **서로 다른 번호 체계**다(077 TS-040 = code-map 부재 이탈, 080 TS-040 = headerSource 미설정 이탈).
// 077 자산을 가리킬 때는 항상 `077 TS-NNN`으로 표기한다. 077 TS-038은 080 TS-042가 계승한다.
//
// hook fail-safe 3중 방어 (PLAN §3.5.2):
//   ① `loadConfig`가 **절대 종료하지 않는다**(§3.1.2 (B)) — hook은 `main()`을 거치지 않고
//      `loadConfig`를 직접 호출한다(`code-map-hook.js:120`). 여기서 종료하면 방어 ②③이 무의미하다.
//   ② hook이 ⑤.5단에서 명시적으로 조기 이탈한다(미설정·무효·inline).
//   ③ 전 경로 try/catch + 무조건 `process.exit(0)`(`code-map-hook.js:151-158`) — 그대로 유지.
//
// [MUST] red-first.md §4 — 실 subprocess(stdin 주입)의 exit code · stdout 바이트로만 검증한다.
// mock 금지. 예외는 loadConfig 무종료 산출물 검사 1건이며, 이것은 실행이 아니라 소스 텍스트 계약이다.
// 픽스처 커밋 상태는 수정하지 않는다 — 사전 조작은 전부 임시 복사본 오버레이로 한다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — headerSource 실패 표면 3종 무출력 계약 신설
//     (TS-040/041/043), 077 TS-038 → TS-042 계승, out_of_scope 무출력(TS-036) 추가,
//     loadConfig 무종료 산출물 검사 추가 (opal-test-agent mode:red)
//   v2.1 2026-08-02 KST: 태스크 080 추가 RED — TS-076 신설. 조기 이탈 3종의 **stderr 0바이트**를
//     단언한다(TS-040/041/043은 stdout만 봤다). 기존 단언 무수정·무삭제 (opal-test-agent mode:red)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const HOOK_JS = path.resolve(__dirname, '..', 'code-map-hook.js');
const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
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

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

function copyFixture(fixtureRelPath, tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t080-hook-${tag}-`));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureRelPath), dir);
  return dir;
}

function configPath(dir) { return path.join(dir, '.opal', 'code-scan.json'); }

/** 전역 `headerSource` **한 값만** 교체한다(픽스처 자산 무변경 — 조작은 임시 복사본에서만). */
function setGlobalHeaderSource(dir, value) {
  const cfg = JSON.parse(fs.readFileSync(configPath(dir), 'utf8'));
  cfg.headerSource = value;
  fs.writeFileSync(configPath(dir), JSON.stringify(cfg, null, 2) + '\n');
}

/** 전역 `headerSource` 키를 **삭제**해 "미설정" 상태를 만든다(TS-040 전제). */
function unsetGlobalHeaderSource(dir) {
  const cfg = JSON.parse(fs.readFileSync(configPath(dir), 'utf8'));
  delete cfg.headerSource;
  fs.writeFileSync(configPath(dir), JSON.stringify(cfg, null, 2) + '\n');
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

function editEvent(absPath) {
  return { tool_name: 'Edit', tool_input: { file_path: absPath } };
}

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
// [T080/L1-F12e] TS-042 (S-2) — 양성 대조군: manifest 모드 + 미갱신 매니페스트 → 경고 정상 출력
//                                (077 TS-038 계약 계승)
// ═════════════════════════════════════════════════════════════════════════
//
// [MUST] 이 케이스가 **먼저** 성립해야 TS-040/041/043의 "무출력"이 의미를 갖는다. 같은 픽스처
// (`violations/draft` — Draft.java의 description이 공백이고 draft:true)에서 headerSource만 바꾸는
// 대조 설계이므로, 무출력이 "hook이 원래 아무 일도 안 함" 때문일 가능성이 배제된다.

test('[T080/L1-F12e] TS-042 (S-2) [077 TS-038 계승]: manifest 모드 + 미갱신 매니페스트 → 경고 정상 출력, exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts042');
  setGlobalHeaderSource(dir, 'manifest');

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, editEvent(abs));

  assert.strictEqual(error, undefined, `hook이 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `hook은 항상 exit 0(fail-safe), got ${exitCode}`);
  assert.ok(stdout.trim().length > 0,
    '[계약 보존] manifest 모드 + 미갱신 매니페스트에서는 경고(additionalContext)가 반드시 출력되어야 한다 — 이것이 없으면 hook 자체가 무의미하다');

  const payload = JSON.parse(stdout);
  assert.strictEqual(payload.hookSpecificOutput && payload.hookSpecificOutput.hookEventName, 'PostToolUse',
    `경고 페이로드 스키마가 PostToolUse additionalContext여야 함, got ${stdout}`);
  assert.ok(typeof payload.hookSpecificOutput.additionalContext === 'string'
    && payload.hookSpecificOutput.additionalContext.length > 0,
    `additionalContext 본문이 있어야 함, got ${stdout}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F12e] TS-040 / TS-041 / TS-043 (S-2): headerSource 실패 표면 3종 → 무출력 exit 0
// ═════════════════════════════════════════════════════════════════════════
//
// 세 케이스 모두 TS-042와 **완전히 동일한 트리**(경고가 나오는 상태)에서 전역 headerSource 한 값만
// 바꾼다. 따라서 stdout 0바이트는 오직 ⑤.5단 조기 이탈(PLAN §3.5.2) 때문일 수밖에 없다.

test('[T080/L1-F12e] TS-040 (S-2): headerSource 미설정 트리 → stdout 0바이트 · exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts040');
  unsetGlobalHeaderSource(dir);
  assert.ok(!Object.prototype.hasOwnProperty.call(JSON.parse(fs.readFileSync(configPath(dir), 'utf8')), 'headerSource'),
    '전제: 이 트리의 code-scan.json에 headerSource 키가 없어야 한다');

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, editEvent(abs));

  assert.strictEqual(error, undefined, `hook이 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0,
    `[RED expect] 미설정은 전 명령 차단(exit 1) 대상이지만 hook만은 예외다 — exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '',
    `[RED expect] 미설정 트리에서 hook은 무출력이어야 한다 — 매 편집마다 출력이 뜨면 세션이 망가진다, got ${JSON.stringify(stdout)}`);
});

test('[T080/L1-F12e] TS-041 (S-2): headerSource:"auto"(무효값) 트리 → stdout 0바이트 · exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts041');
  setGlobalHeaderSource(dir, 'auto');

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, editEvent(abs));

  assert.strictEqual(error, undefined, `hook이 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `[RED expect] 무효값에서도 hook은 exit 0, got ${exitCode}`);
  assert.strictEqual(stdout, '',
    `[RED expect] 무효값(auto)은 2택 어디에도 속하지 않으므로 hook은 이탈해 무출력이어야 한다, got ${JSON.stringify(stdout)}`);
});

test('[T080/L1-F12e] TS-041 (S-2): headerSource:"bogus"(임의 무효값) 트리 → stdout 0바이트 · exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts041b');
  setGlobalHeaderSource(dir, 'bogus');

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout } = runHook(dir, editEvent(abs));

  assert.strictEqual(exitCode, 0, `[RED expect] exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '',
    `[RED expect] 이탈 조건은 "2택이 아닌 모든 값"이다(auto 특례가 아니다), got ${JSON.stringify(stdout)}`);
});

test('[T080/L1-F12e] TS-043 (S-2): headerSource:"inline" 모드 → stdout 0바이트 · exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts043');
  setGlobalHeaderSource(dir, 'inline');

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, editEvent(abs));

  assert.strictEqual(error, undefined, `hook이 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '',
    `[RED expect] inline 모드는 경고할 대상 자체가 없다 — 매니페스트가 미갱신이어도 무출력이어야 한다, got ${JSON.stringify(stdout)}`);
});

test('[T080/L1-F12e] TS-040/043 (S-2): 깨진 code-scan.json 트리에서도 hook은 무출력 exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts040c');
  fs.writeFileSync(configPath(dir), '{ this is not valid json');

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, editEvent(abs));

  assert.strictEqual(error, undefined, `hook이 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0,
    `[RED expect] config_parse_failed는 CLI에서 exit 1이지만 hook은 예외 — exit 0, got ${exitCode}`);
  assert.strictEqual(stdout, '',
    `[RED expect] 깨진 설정에서도 hook은 무출력이어야 한다, got ${JSON.stringify(stdout)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F12e] TS-076 (S-2): 조기 이탈 3종은 stderr도 0바이트여야 한다 (무출력 = stdout + stderr)
// ═════════════════════════════════════════════════════════════════════════
//
// [왜 신설인가 — TS-040/041/043과 무엇이 다른가]
// TS-040/041/043은 **stdout만** 단언한다. 그러나 hook의 명시 계약은 "무출력"이다
// (`code-map-hook.js` @header note / PLAN §3.5.2 — "즉시 무관 판정·무출력·exit 0").
// 무출력은 stdout 0바이트만을 뜻하지 않는다. PostToolUse는 **매 편집마다** 실행되므로 stderr로
// 새는 한 줄도 세션 전체를 오염시킨다 — 스트림이 stdout이 아니라는 이유로 면제되지 않는다.
//
// [결함 재현 조건] 조기 이탈 게이트(⑤.5 `code-map-hook.js:125-128`)가 `loadCodeMap`(⑤ `:116`)
// **뒤에** 있다. `loadCodeMap` → `normalizeIndexScope`는 index.json 스코프에 폐기 키 `readonly`가
// **존재하기만 하면**(값 무관) `deprecationOnce('index_scope_readonly')`로 stderr 1건을 뱉는다
// (`code-scan.js:454-456`). 따라서 조용히 이탈해야 할 트리에서도 stderr가 먼저 나간다.
// 실프로젝트 실측(`headerSource:"auto"` + index.json에 readonly 보유): stdout 0 / **stderr 295바이트**.
// 기존 케이스가 이를 못 잡은 이유는 하나뿐이다 — 아무도 stderr를 보지 않았다.
//
// [무대] TS-040/041/043과 **완전히 동일한 트리·파일·이벤트**(`violations/draft` + Draft.java)를 쓴다.
// 이 픽스처의 index.json은 이미 `scopes.svc.readonly`를 보유하므로 새 픽스처가 필요 없다
// (값이 false여도 **키 존재**만으로 발화한다 — `hasOwn(raw,'readonly')`). 트리가 같으므로
// TS-076의 실패는 오직 stderr 축에서만 온다 — 기존 케이스와의 차이가 변수 1개로 격리된다.
//
// [양성 대조군] 신설하지 않는다. 위 **TS-042**가 같은 트리·같은 파일에서 manifest 모드일 때
// stdout 경고가 나옴을 이미 못 박고 있으므로(실측 stdout 398바이트), "stderr 0"이 "hook이 죽어서"가
// 아님은 TS-042가 담보한다. 중복 대조군은 만들지 않는다.
//
// [MUST] 이 3케이스는 TS-040/041/043을 대체하지 않는다 — stdout 축은 그쪽이, stderr 축은 이쪽이
// 각각 담당한다. 통과를 위해 어느 쪽 기대값도 완화하지 말 것(red-first.md §3).

/** 이 트리의 index.json 스코프가 폐기 키 `readonly`를 보유함을 확인한다 — TS-076 재현 전제. */
function assertIndexHasReadonlyKey(dir) {
  const idx = JSON.parse(fs.readFileSync(path.join(dir, '.opal', 'code-map', 'index.json'), 'utf8'));
  const owners = Object.entries(idx.scopes || {})
    .filter(([, s]) => s && typeof s === 'object' && Object.prototype.hasOwnProperty.call(s, 'readonly'))
    .map(([name]) => name);
  assert.ok(owners.length > 0,
    '전제: 이 트리의 index.json 스코프가 폐기 키 readonly를 보유해야 deprecationOnce가 발화해 결함이 재현된다');
  return owners;
}

/** 조기 이탈 3축 단언: exit 0 · stdout 0바이트 · stderr 0바이트. */
function assertSilentEarlyExit({ exitCode, stdout, stderr, error }, why) {
  assert.strictEqual(error, undefined, `hook이 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `[RED expect] 조기 이탈에서도 hook은 exit 0(fail-safe), got ${exitCode}`);
  assert.strictEqual(stdout, '',
    `[RED expect] ${why} — stdout 0바이트여야 한다, got ${JSON.stringify(stdout)}`);
  assert.strictEqual(stderr, '',
    `[RED expect] ${why} — hook 계약은 "무출력"이며 stderr도 0바이트여야 한다. ` +
    `실제 stderr ${Buffer.byteLength(stderr, 'utf8')}바이트가 새고 있다(매 편집마다 반복 → 세션 오염). ` +
    `원인: 조기 이탈 게이트(⑤.5 code-map-hook.js:125-128)가 loadCodeMap(⑤ :116)보다 아래에 있어 ` +
    `normalizeIndexScope의 deprecationOnce('index_scope_readonly')가 먼저 발화한다.\n--- 실제 stderr ---\n${stderr}`);
}

test('[T080/L1-F12e] TS-076 (S-2): headerSource 미설정 + readonly 보유 index 트리 → stdout 0 · stderr 0 · exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts076a');
  unsetGlobalHeaderSource(dir);
  assertIndexHasReadonlyKey(dir);

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  assertSilentEarlyExit(runHook(dir, editEvent(abs)),
    'headerSource 미설정은 ⑤.5 조기 이탈 대상이다');
});

test('[T080/L1-F12e] TS-076 (S-2): headerSource:"auto"(무효값) + readonly 보유 index 트리 → stdout 0 · stderr 0 · exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts076b');
  setGlobalHeaderSource(dir, 'auto');
  assertIndexHasReadonlyKey(dir);

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  assertSilentEarlyExit(runHook(dir, editEvent(abs)),
    '무효값(auto)은 2택 어디에도 속하지 않아 ⑤.5 조기 이탈 대상이다');
});

test('[T080/L1-F12e] TS-076 (S-2): headerSource:"inline" + readonly 보유 index 트리 → stdout 0 · stderr 0 · exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 'ts076c');
  setGlobalHeaderSource(dir, 'inline');
  assertIndexHasReadonlyKey(dir);

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  assertSilentEarlyExit(runHook(dir, editEvent(abs)),
    'inline 모드는 경고 대상 자체가 없어 ⑤.5 조기 이탈 대상이다');
});

test('[T080/L1-F12e] (S-2) [산출물 검사]: loadConfig 본문에 process.exit·throw 0건 (fail-safe 1차 방어)', () => {
  const src = fs.readFileSync(CODE_SCAN_JS, 'utf8').split('\n');
  const range = functionLineRange(src, 'loadConfig');
  assert.ok(range, 'loadConfig 함수가 code-scan.js 최상위에 존재해야 함');

  const offenders = [];
  for (let i = range[0] - 1; i <= range[1] - 1; i++) {
    const line = src[i].replace(/\/\/.*$/, '');
    if (/\bprocess\s*\.\s*exit\b/.test(line)) offenders.push(`${i + 1}: ${src[i].trim()}`);
    if (/\bthrow\b/.test(line)) offenders.push(`${i + 1}: ${src[i].trim()}`);
    if (/\berrorExit\s*\(|\bcodeMapErrorExit\s*\(/.test(line)) offenders.push(`${i + 1}: ${src[i].trim()}`);
  }

  assert.deepStrictEqual(offenders, [],
    `[MUST] PLAN §3.1.2 (B): "loadConfig는 절대 process.exit / throw 하지 않는다". hook은 main()을 거치지 않고 ` +
    `loadConfig를 직접 호출하므로(code-map-hook.js:120) 여기서 종료하면 PostToolUse fail-safe가 붕괴한다(H-2).\n잔존:\n${offenders.join('\n')}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F8c] TS-036 (S-9): 스코프 필터 탈락 파일 → hook 무출력 (`code-map-hook.js:136` 이탈 보존)
// ═════════════════════════════════════════════════════════════════════════
//
// `decideTarget`이 `{write_to:'none', reason:'out_of_scope'}`를 반환하면(PLAN §3.2.2 (C-bis)),
// hook의 ⑦단 `decision.write_to !== 'manifest'` 이탈이 **로직 변경 0으로** 이를 흡수해야 한다.
// 무대는 `mixed-scope`를 manifest로 뒤집은 오버레이다 — inline이면 ⑤.5에서 먼저 이탈해 :136
// 경로를 지나가지 않으므로, 이 명제를 검증하려면 반드시 manifest 모드여야 한다.

test('[T080/L1-F8c] TS-036 (S-9): manifest 모드 + out_of_scope 파일(VendorLegacy.java) → stdout 0바이트 · exit 0', () => {
  const dir = copyFixture('mixed-scope', 'ts036');
  setGlobalHeaderSource(dir, 'manifest');

  const abs = path.join(dir, 'svc', 'shared', 'VendorLegacy.java');
  assert.ok(fs.existsSync(abs), '전제: VendorLegacy.java가 디스크에 존재한다(어느 include에도 미매칭 · 양쪽 매니페스트 미등재)');

  const { exitCode, stdout, error } = runHook(dir, editEvent(abs));

  assert.strictEqual(error, undefined, `hook이 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '',
    `[RED expect] out_of_scope 파일은 기록 위치가 없으므로 경고 대상이 아니다 — write_to !== 'manifest' 이탈(:136)로 무출력이어야 한다, got ${JSON.stringify(stdout)}`);
});

test('[T080/L1-F8c] TS-036 (S-9) [양성 대조군]: 같은 트리·같은 모드에서 in-scope 미등재 파일은 경고가 나온다', () => {
  const dir = copyFixture('mixed-scope', 'ts036b');
  setGlobalHeaderSource(dir, 'manifest');

  // ship-svc 매니페스트에서 ShipRepo.java 엔트리 1개만 삭제 → in-scope 미갱신 상태를 만든다.
  const shipManifest = path.join(dir, '.opal', 'code-map', 'ship-svc', '_root.json');
  const m = JSON.parse(fs.readFileSync(shipManifest, 'utf8'));
  delete m.files['ShipRepo.java'];
  fs.writeFileSync(shipManifest, JSON.stringify(m, null, 2) + '\n');

  const abs = path.join(dir, 'svc', 'shared', 'ShipRepo.java');
  const { exitCode, stdout } = runHook(dir, editEvent(abs));

  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.ok(stdout.trim().length > 0,
    '[대조군] 같은 트리·같은 모드에서 in-scope 미등재 파일은 경고가 나와야 한다 — 나오지 않으면 위 TS-036의 무출력이 "이 트리가 원래 조용함" 때문이라는 뜻이 되어 검증이 공허해진다');
});

// ═════════════════════════════════════════════════════════════════════════
// 077 승계 자산 — 조기 이탈 회귀 (계약 불변)
// ═════════════════════════════════════════════════════════════════════════

test('077 TS-039 (S-18): 매니페스트 갱신 완료 상태 이벤트 → stdout 0바이트, exit 0', () => {
  const dir = copyFixture(path.join('violations', 'clean'), 't077-039'); // Clean.java는 description 채워진 정상 상태

  const abs = path.join(dir, 'svc', 'mod', 'Clean.java');
  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Write', tool_input: { file_path: abs } });

  assert.strictEqual(error, undefined, `hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `갱신 완료 상태는 무출력이어야 함, got: ${JSON.stringify(stdout)}`);
});

test('077 TS-040 (S-18): code-map 부재 트리 이벤트 → stdout 0바이트, exit 0 (⑤단 이탈)', () => {
  const dir = copyFixture('legacy-repo', 't077-040');

  const abs = path.join(dir, 'be', 'util', 'no_header.py');
  const { exitCode, stdout, error } = runHook(dir, editEvent(abs));

  assert.strictEqual(error, undefined, `hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `code-map 부재 시 무출력이어야 함(⑤단 이탈), got: ${JSON.stringify(stdout)}`);
});

test('077 TS-041 (S-18): 깨진 stdin JSON → 무출력 exit 0 (fail-safe)', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 't077-041a');

  const { exitCode, stdout, error } = runHook(dir, '{ this is not valid json');
  assert.strictEqual(error, undefined, `hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `무출력 기대, got: ${JSON.stringify(stdout)}`);
});

test('077 TS-041 (S-18): tool_name:"Bash" 이벤트 → 무출력 exit 0 (matcher 이중 방어)', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 't077-041b');

  const abs = path.join(dir, 'svc', 'mod', 'Draft.java');
  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Bash', tool_input: { command: `cat ${abs}` } });
  assert.strictEqual(error, undefined, `hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `무출력 기대, got: ${JSON.stringify(stdout)}`);
});

test('077 TS-041 (S-18): file_path 부재 이벤트 → 무출력 exit 0', () => {
  const dir = copyFixture(path.join('violations', 'draft'), 't077-041c');

  const { exitCode, stdout, error } = runHook(dir, { tool_name: 'Edit', tool_input: {} });
  assert.strictEqual(error, undefined, `hook 파일 실행 가능해야 함 (error: ${error})`);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  assert.strictEqual(stdout, '', `무출력 기대, got: ${JSON.stringify(stdout)}`);
});

test('077 TS-042 (S-18): claude-hooks.json — PostToolUse 배열에 Bash 엔트리 + code-map-hook 엔트리 공존', () => {
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
    'code-map-hook.js를 가리키는 PostToolUse 엔트리가 additive로 유지되어야 함');
});
