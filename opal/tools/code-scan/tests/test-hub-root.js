/**
 * @header {
 *   "module": "test-hub-root",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "task": "109",
 *   "scenarios": ["TS-011", "TS-012", "TS-022"],
 *   "description": "RED-first — hubRootFromPath 신설 계약: 골든 표(hub-root-cases.json) C-1~C-7 문자열 동치 + C-3·C-6 항등 케이스 바이트 동일(TS-012) + 실제 워크트리(.git 파일) cwd에서 CLI validate가 header_source_unset을 소거하는지 블랙박스 검증 + 리터럴 우선 음성 케이스: 어떤 조상에도 .opal/이 없으면 정규화가 위치를 발명하지 않고 header_source_unset이 남는다 (109)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"]
 * }
 */
//
// [MUST] red-first.md §2 — 이 파일은 opal-test-agent(mode:red)가 작성한다. GREEN 구현(hubRootFromPath
// 신설·findProjectRoot() 수정)은 이 워커의 책임이 아니다 — 별도 워커가 후속 Step에서 수행한다.
// [MUST] 골든 표(opal/core/references/hub-root-cases.json)를 이 파일에 복제하지 않는다(TS-060) —
// 표는 파일 1개이고 이 스위트는 그 파일을 읽기만 한다.
//
// 변경이력:
//   v1.0 2026-09-07 KST: RED-first 최초 작성 (태스크 109, opal-test-agent mode:red)
//   v1.1 2026-09-07 KST: 정정 3 TS-012(Node) 신설 + 정정 5 TS-022 음성 리터럴 우선 재설계 (109)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
// 골든 표 SSOT — Step 1(병렬 워커)의 소유물. 이 파일은 읽기만 한다.
const CASES_PATH = path.resolve(__dirname, '..', '..', '..', '..', 'opal', 'core', 'references', 'hub-root-cases.json');
// [MUST] 083부터 spawnSync 사용 테스트는 OPAL_HOME을 주입해 개발자 실제 홈 setting.json의
// 영향을 차단해야 한다(U-7, test-shard-policy.js TS-084).
const HOME_ABSENT = path.resolve(__dirname, 'fixtures', 'shard-policy', 'homes', 'absent');

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

function mkTemp(tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t109-${tag}-`));
  cleanupDirs.push(dir);
  return dir;
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
// ① 골든 표 C-1~C-7 문자열 동치 — hubRootFromPath (TS-011)
// ─────────────────────────────────────────────────────────────────────────

test('[T109/L1-F1] TS-011: hubRootFromPath가 골든 표 C-1~C-7 전건에서 §2.5(4) 기대값을 반환한다', () => {
  // eslint-disable-next-line global-require
  const codeScan = require(CODE_SCAN_JS);
  assert.equal(typeof codeScan.hubRootFromPath, 'function',
    '[RED expect] code-scan.js는 아직 hubRootFromPath를 export하지 않는다 — GREEN 구현 전 단계');

  const table = JSON.parse(fs.readFileSync(CASES_PATH, 'utf8'));
  assert.equal(table.version, 1);

  const PREFIX = path.sep === '\\' ? 'C:\\synthetic\\prefix' : '/synthetic/prefix';

  for (const c of table.cases) {
    const input = path.join(PREFIX, c.input_rel);
    const expected = c.expected_rel === '' ? PREFIX : path.join(PREFIX, c.expected_rel);
    const actual = codeScan.hubRootFromPath(input);
    assert.equal(actual, expected, `${c.id}: ${c.desc}`);
  }
});

// ─────────────────────────────────────────────────────────────────────────
// ①b 항등 케이스 바이트 동일 — C-3·C-6 (TS-012)
// ─────────────────────────────────────────────────────────────────────────

test('[T109/L1-F1b] TS-012: C-3·C-6 항등 케이스에서 hubRootFromPath 반환값이 입력과 바이트 동일하다', () => {
  // eslint-disable-next-line global-require
  const codeScan = require(CODE_SCAN_JS);
  assert.equal(typeof codeScan.hubRootFromPath, 'function',
    '[RED expect] code-scan.js는 아직 hubRootFromPath를 export하지 않는다 — GREEN 구현 전 단계');

  const table = JSON.parse(fs.readFileSync(CASES_PATH, 'utf8'));
  const IDENTITY_IDS = new Set(['C-3', 'C-6']);
  const PREFIX = path.sep === '\\' ? 'C:\\synthetic\\prefix' : '/synthetic/prefix';

  const identityCases = table.cases.filter((c) => IDENTITY_IDS.has(c.id));
  assert.equal(identityCases.length, 2, '골든 표에 C-3·C-6 항등 케이스가 모두 있어야 한다');

  for (const c of identityCases) {
    const input = path.join(PREFIX, c.input_rel);
    const actual = codeScan.hubRootFromPath(input);
    assert.equal(
      Buffer.compare(Buffer.from(String(actual)), Buffer.from(input)), 0,
      `${c.id}: ${c.desc} — actual=${JSON.stringify(actual)} input=${JSON.stringify(input)}`,
    );
  }
});

// ─────────────────────────────────────────────────────────────────────────
// ② CLI 블랙박스 — 워크트리(.git 파일) cwd에서 header_source_unset 소거 (TS-022)
// ─────────────────────────────────────────────────────────────────────────

test('[T109/L2-F2] TS-022: 워크트리 cwd에서 validate 실행 시 허브 .opal/code-scan.json을 발견해 header_source_unset이 나지 않는다', () => {
  const hub = mkTemp('hub');
  fs.mkdirSync(path.join(hub, '.opal'), { recursive: true });
  fs.writeFileSync(
    path.join(hub, '.opal', 'code-scan.json'),
    JSON.stringify({ headerSource: 'inline' }, null, 2) + '\n',
  );

  const worktreeDir = path.join(hub, '.opal-worktrees', 'task_001');
  fs.mkdirSync(worktreeDir, { recursive: true });
  // [MUST] 실제 git worktree의 .git은 디렉터리가 아니라 gitdir 포인터를 담은 78바이트 내외의
  // "파일"이다. fs.existsSync는 파일/디렉터리를 구분하지 않으므로 이 재현이 버그의 핵심이다.
  fs.writeFileSync(
    path.join(worktreeDir, '.git'),
    `gitdir: ${path.join(hub, '.git', 'worktrees', 'task_001')}\n`,
  );
  assert.equal(fs.statSync(path.join(worktreeDir, '.git')).isFile(), true,
    '픽스처 전제 위반: .git이 디렉터리로 생성됨 — 워크트리 재현 실패');

  const { json, stderr } = run(worktreeDir, ['validate']);

  const errorCode = json && json.error;
  assert.notEqual(errorCode, 'header_source_unset',
    `[RED expect] 현재는 findProjectRoot()가 워크트리 자신을 프로젝트 루트로 오인해 허브의 ` +
    `.opal/code-scan.json을 발견하지 못하고 header_source_unset이 난다. ` +
    `json=${JSON.stringify(json)} stderr=${stderr}`);
});

// ─────────────────────────────────────────────────────────────────────────
// ③ 음성 케이스 — 정규화는 설정 위치를 발명하지 않는다 (리터럴 우선, 소유자 결정)
// ─────────────────────────────────────────────────────────────────────────
//
// [MUST] 소유자(캡틴) 결정: "워크트리 설정은 절대 읽지 않는다"는 절대 우선순위가 아니다.
// cwd에서 상향 탐색해 자기 .opal/을 가진 루트를 만나면 그것이 프로젝트 루트다(리터럴 우선).
// 예: tests/fixtures/codemap-repo/는 .opal-worktrees 하위 경로라도 자기 .opal/을 가진
// 자기완결 프로젝트이므로 그 자신이 루트여야 한다 — 정규화가 이를 허브로 납치하면
// §2.5(4) 4항("정규화는 허브 고정 데이터 참조에만, 소스 트리 내용에는 적용하지 않는다") 위반.
// 보존해야 할 진짜 불변식은 "설정 위치를 발명하지 않는다" — 즉 cwd의 어떤 조상에도
// .opal/이 없으면(허브 포함) header_source_unset이 그대로 나야 한다(다른 것으로
// 조용히 대체하지 않는다).

test('[T109/L2-F2b] TS-022 음성(리터럴 우선): 어떤 조상에도 .opal/이 없으면 정규화가 위치를 발명하지 않고 header_source_unset이 그대로 난다', () => {
  const hub = mkTemp('hub-neg');
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

test('[T109/L2-F2c] TS-022 리터럴 우선: .opal-worktrees 하위라도 자기 .opal/을 가진 자기완결 프로젝트는 그 자신이 루트다', () => {
  const hub = mkTemp('hub-literal');
  fs.mkdirSync(path.join(hub, '.opal'), { recursive: true });
  fs.writeFileSync(
    path.join(hub, '.opal', 'code-scan.json'),
    JSON.stringify({ headerSource: 'inline' }, null, 2) + '\n',
  );

  // 허브 아래 .opal-worktrees 하위에 놓였지만 자기 .opal/을 가진 자기완결 프로젝트(픽스처
  // 재현). 정규화가 이를 허브로 납치하면 안 되고, 자기 자신의 .opal/을 우선 발견해야 한다.
  const selfContainedDir = path.join(hub, '.opal-worktrees', 'task_003', 'nested-project');
  fs.mkdirSync(path.join(selfContainedDir, '.opal'), { recursive: true });
  fs.writeFileSync(
    path.join(selfContainedDir, '.opal', 'code-scan.json'),
    JSON.stringify({ headerSource: 'inline' }, null, 2) + '\n',
  );

  const { json, stderr } = run(selfContainedDir, ['validate']);

  const errorCode = json && json.error;
  assert.notEqual(errorCode, 'header_source_unset',
    `자기 .opal/을 가진 자기완결 프로젝트는 리터럴 우선으로 그 자신이 루트여야 한다. ` +
    `json=${JSON.stringify(json)} stderr=${stderr}`);
});
