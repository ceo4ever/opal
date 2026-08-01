/**
 * @header {
 *   "module": "test-regression",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — 8커맨드 골든 회귀(제약②) + 픽스처 이중 격리(H-1) + .gitignore code-map 예외(H-18) + 문서 산출물 검사(F-011, S-21) + 신규 테스트 파일 @header 자산화(TS-057) 테스트 (태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-7", "S-19", "S-21", "S-23"]
 * }
 */
//
// TC ↔ TS-ID 매핑 표 (PLAN.md §3.11.5/§3.12.5, TEST-SCENARIO.md S-7/S-19/S-21/S-23):
//
// | TC                                                  | TS-ID       | 비고 |
// |--------------------------------------------------------|-------------|------|
// | golden-8-commands-byte-identical (legacy-repo, code-map 없음) | TS-006/TS-043 | **이 그룹만 지금 PASS 기대(기준선 유효성)** |
// | isolation-repo-root-excludes-fixtures                    | TS-052      | 지금 PASS 기대(Step 1 선결 완료) |
// | isolation-fixture-root-excludes-repo                     | TS-053      | 지금 PASS 기대(자기완결 픽스처) |
// | gitignore-codemap-exception                              | TS-055      | 지금 PASS 기대(Step 1 선결 완료) |
// | new-test-files-have-header-and-are-scanned                | TS-057      | 지금 PASS 기대(이 8개 파일 자체가 @header 보유) |
// | doc-changelog-rows (7문서 중 6개, manifest.json 제외)       | TS-047      | **RED 기대** (F-011 Step 15~18 미완료) |
// | doc-header-rules-no-legacy-phrase                         | TS-048      | **RED 기대** |
// | doc-header-rules-3-tables                                 | TS-049      | **RED 기대** |
// | doc-brain-tool-readme-1-sentence + opal-harness §9 정합    | TS-051      | **RED 기대** |
// | doc-pm-review-gate-8-14-updated                            | (S-21 고유) | **RED 기대** |
//
// 이 파일은 다른 7개 RED 파일과 성격이 다르다: "8커맨드 골든 회귀"·"픽스처 이중 격리"·"gitignore 예외"·
// "테스트 파일 자산화"는 이미 완료된 선결 작업(Step 1) 또는 골든 캡처(Step 3) 자체의 유효성을 검증하는
// 것이므로 **지금 시점에 PASS해야 정상**이다(PLAN §4.2 Step 4 완료 기준: "test-regression.js의 골든 대조는
// 이 시점에 통과해야 한다 — 기준선 유효성 확인"). 반면 F-011 문서 갱신(Step 15~18)은 아직 수행되지 않았으므로
// 문서 산출물 검사 그룹은 RED로 실패해야 정상이다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const TOOL_DIR = path.resolve(__dirname, '..');
const CODE_SCAN_JS = path.join(TOOL_DIR, 'code-scan.js');
const FIX = path.resolve(__dirname, 'fixtures');
const GOLDEN = path.join(FIX, 'golden');
const LEGACY_REPO = path.join(FIX, 'legacy-repo');
const REPO_ROOT = path.resolve(TOOL_DIR, '..', '..', '..'); // opal/tools/code-scan -> repo root
const CORE_REF = path.join(REPO_ROOT, 'opal', 'core', 'references');

function run(cwd, args) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], { cwd, encoding: 'utf8', timeout: 10000 });
  return { exitCode: result.status, stdout: result.stdout || '', stderr: result.stderr || '' };
}

// ─────────────────────────────────────────────────────────────────────────
// TS-006 / TS-043: 8커맨드 골든 회귀 — legacy-repo(code-map 없음)에서 바이트 동일
// ─────────────────────────────────────────────────────────────────────────

const GOLDEN_COMMANDS = [
  { args: ['scan', '--json'], golden: 'scan.json' },
  { args: ['domain'], golden: 'domain.txt' },
  { args: ['layer'], golden: 'layer.txt' },
  { args: ['search', 'auth', '--json'], golden: 'search.json' },
  { args: ['exports', 'token', '--json'], golden: 'exports.json' },
  { args: ['summary'], golden: 'summary.txt' },
  { args: ['depends', 'auth_service'], golden: 'depends.txt' },
  { args: ['missing'], golden: 'missing.txt' },
];

for (const c of GOLDEN_COMMANDS) {
  test(`TS-006/043: golden 회귀 — "${c.args.join(' ')}" 출력이 바이트 동일 (지금 PASS 기대 — 기준선 유효성)`, () => {
    const { exitCode, stdout } = run(LEGACY_REPO, c.args);
    assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
    const expected = fs.readFileSync(path.join(GOLDEN, c.golden), 'utf8');
    assert.strictEqual(stdout, expected,
      `골든과 바이트 동일해야 함(${c.golden}). 이 그룹은 code-map 부재 픽스처를 대상으로 하므로 GREEN 구현 후에도 계속 PASS해야 한다(제약②).`);
  });
}

test('TS-006/043: golden 회귀 — scan --json 결과에 _source 키가 0건', () => {
  const { stdout } = run(LEGACY_REPO, ['scan', '--json']);
  const json = JSON.parse(stdout);
  const hasSourceKey = Object.values(json).some(h => Object.prototype.hasOwnProperty.call(h, '_source'));
  assert.strictEqual(hasSourceKey, false,
    'code-map 부재 프로젝트의 결과에는 _source 키가 절대 붙으면 안 된다(제약② 하위호환 보증 지점)');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-052/TS-053 (S-19): 픽스처 이중 격리
// ─────────────────────────────────────────────────────────────────────────

test('TS-052 (S-19): 저장소 루트 scan --json — fixtures/ 경로 0건 (지금 PASS 기대)', () => {
  const { exitCode, stdout } = run(REPO_ROOT, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  const json = JSON.parse(stdout);
  const badPaths = Object.keys(json).filter(p => p.includes('fixtures/'));
  assert.strictEqual(badPaths.length, 0, `fixtures/ 경로가 결과에 나타나면 안 됨: ${JSON.stringify(badPaths)}`);
});

test('TS-053 (S-19): 픽스처 루트 cwd 실행 — 저장소 파일 0건 (지금 PASS 기대)', () => {
  const { exitCode, stdout } = run(path.join(FIX, 'codemap-repo'), ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  const json = JSON.parse(stdout);
  const repoRootLeaks = Object.keys(json).filter(p => p.startsWith('opal/') || p.startsWith('tasks/'));
  assert.strictEqual(repoRootLeaks.length, 0, `저장소 파일이 결과에 나타나면 안 됨: ${JSON.stringify(repoRootLeaks)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-055 (S-23): .gitignore code-map 예외
// ─────────────────────────────────────────────────────────────────────────

test('TS-055 (S-23): git check-ignore — .opal/code-map/index.json 비무시, .opal/code-scan.json 무시 유지 (지금 PASS 기대)', () => {
  // 주의: `-v`(verbose)를 붙이면 negation 패턴이 매치되어도 exit 0을 반환하는 git 고유 동작이 있어
  // exit code만으로 무시 여부를 판별할 수 없다. exit code 판별은 반드시 `-v` 없이 수행하고, `-v`는
  // 진단 메시지 용도로만 별도 호출한다.
  const r1 = spawnSync('git', ['check-ignore', '.opal/code-map/index.json'], { cwd: REPO_ROOT, encoding: 'utf8' });
  const r1v = spawnSync('git', ['check-ignore', '-v', '.opal/code-map/index.json'], { cwd: REPO_ROOT, encoding: 'utf8' });
  assert.strictEqual(r1.status, 1,
    `.opal/code-map/index.json은 무시되지 않아야 함(exit 1 기대), got ${r1.status}, 매칭 패턴: ${r1v.stdout}`);

  const r2 = spawnSync('git', ['check-ignore', '.opal/code-scan.json'], { cwd: REPO_ROOT, encoding: 'utf8' });
  assert.strictEqual(r2.status, 0, `.opal/code-scan.json은 계속 무시되어야 함(exit 0 기대), got ${r2.status}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-057: 신규 테스트 파일 8종이 @header JSON 블록을 보유하고 scan에 잡힘 (지금 PASS 기대)
// ─────────────────────────────────────────────────────────────────────────

test('TS-057: 신규 RED 테스트 파일 8종이 @header를 보유하고 code-scan에 discoverable함', () => {
  const testFiles = [
    'test-resolve-header.js', 'test-discover.js', 'test-scaffold.js', 'test-target.js',
    'test-validate.js', 'test-feature.js', 'test-regression.js', 'test-hook.js',
  ];
  const { exitCode, stdout } = run(REPO_ROOT, ['scan', '--json']);
  assert.strictEqual(exitCode, 0);
  const json = JSON.parse(stdout);

  for (const f of testFiles) {
    const key = Object.keys(json).find(p => p.endsWith(`tests/${f}`));
    assert.ok(key, `${f}가 저장소 scan 결과에 잡혀야 함(header-standard.md §3 JSON @header 보유)`);
    assert.strictEqual(json[key].layer, 'test', `${f}의 layer는 "test"여야 함`);
    assert.strictEqual(json[key].task, '077', `${f}의 task 필드는 "077"이어야 함`);
    assert.ok(Array.isArray(json[key].scenarios) && json[key].scenarios.length > 0,
      `${f}의 scenarios 필드가 존재해야 함`);
  }
});

// ─────────────────────────────────────────────────────────────────────────
// S-21 (TS-047~051): 규칙 SSOT 7문서 산출물 검사 — F-011 Step 15~18 미완료이므로 RED 기대
// ─────────────────────────────────────────────────────────────────────────

const DOC_TARGETS = {
  headerRules: path.join(CORE_REF, 'harness', 'header-rules.md'),
  codeScanMgmt: path.join(CORE_REF, 'pm', 'code-scan-management.md'),
  pmReviewGate: path.join(CORE_REF, 'harness', 'pm-review-gate.md'),
  toolsMd: path.join(CORE_REF, 'tools.md'),
  brainReadme: path.join(REPO_ROOT, 'opal', 'tools', 'brain-tool', 'README.md'),
  opalHarness: path.join(CORE_REF, 'opal-harness.md'),
};

test('TS-048 (S-21): header-rules.md — "별도 도구 없음" 문구 잔존 0건', () => {
  const text = fs.readFileSync(DOC_TARGETS.headerRules, 'utf8');
  const hits = (text.match(/별도 도구 없음/g) || []).length;
  // [RED 기대] F-011 Step 미완료 — 현재 header-rules.md:12에 이 문구가 그대로 남아 있다(1건).
  assert.strictEqual(hits, 0, `[RED expect] "별도 도구 없음" 문구가 남아있으면 안 됨, got ${hits}건`);
});

test('TS-049 (S-21): header-rules.md — 4단 기록 위치 판정 / 3단 갱신 시점 / 워커 권한 경계 3표 존재', () => {
  const text = fs.readFileSync(DOC_TARGETS.headerRules, 'utf8');
  // [RED 기대] 신설 표 3종이 아직 없다.
  assert.ok(/readonly_repo/.test(text) && /inline_exists/.test(text) && /legacy_no_header/.test(text),
    '[RED expect] 4단 기록 위치 판정 표(reason 4종)가 존재해야 함');
  assert.ok(/CLOSE 진입 전/.test(text) || /PostToolUse hook/.test(text),
    '[RED expect] 3단 갱신 시점 표가 존재해야 함');
  assert.ok(/worker_scope_violation/.test(text),
    '[RED expect] 워커 권한 경계 표가 존재해야 함');
});

test('TS-047 (S-21): 6문서 변경이력 행에 태스크 (077) 표기 존재', () => {
  const targets = ['headerRules', 'codeScanMgmt', 'pmReviewGate', 'toolsMd', 'brainReadme', 'opalHarness'];
  const missing = [];
  for (const t of targets) {
    const text = fs.readFileSync(DOC_TARGETS[t], 'utf8');
    if (!/\(077\)/.test(text)) missing.push(t);
  }
  // [RED 기대] 6문서 전부 아직 (077) 변경이력 행이 없다.
  assert.strictEqual(missing.length, 0,
    `[RED expect] 변경이력에 (077) 표기가 없는 문서: ${JSON.stringify(missing)}`);
});

test('TS-051 (S-21): brain-tool/README.md — 2소스 의미 변화 1문장 + opal-harness.md §9 code-scan 서브명령 정합', () => {
  const brainText = fs.readFileSync(DOC_TARGETS.brainReadme, 'utf8');
  const harnessText = fs.readFileSync(DOC_TARGETS.opalHarness, 'utf8');

  // [RED 기대] brain-tool README에 아직 "인라인·code-map 2소스" 문언이 없다.
  assert.ok(/code-map/.test(brainText) && /인라인/.test(brainText),
    '[RED expect] brain-tool/README.md에 2소스(인라인+code-map) 의미 변화 문장이 추가되어야 함');
  assert.ok(/단방향/.test(brainText), '단방향 계약 문언 자체는 불변으로 유지되어야 함');

  // [RED 기대] opal-harness.md §9 code-scan 행에 신규 서브명령이 아직 열거되지 않았다.
  const codeScanLine = harnessText.split('\n').find(l => l.includes('| code-scan |'));
  assert.ok(codeScanLine && /discover/.test(codeScanLine) && /scaffold/.test(codeScanLine),
    `[RED expect] opal-harness.md §9 code-scan 행에 discover/scaffold 등 신규 서브명령이 열거되어야 함, got: ${codeScanLine}`);
});

test('S-21 고유: pm-review-gate.md — 8번/14번 항목에 2소스 판정·합산 커버리지·validate --changed 게이트 반영', () => {
  const text = fs.readFileSync(DOC_TARGETS.pmReviewGate, 'utf8');
  // [RED 기대] 아직 반영되지 않았다.
  assert.ok(/validate --changed/.test(text),
    '[RED expect] pm-review-gate.md에 "validate --changed" 게이트 절차 문구가 존재해야 함');
  assert.ok(/합산 커버리지|coverage/.test(text),
    '[RED expect] 합산 커버리지 언급이 존재해야 함');
});
