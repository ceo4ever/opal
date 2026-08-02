/**
 * @header {
 *   "module": "test-resolve-header",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — resolveHeader 2택 직결(inline 단독 / manifest 4단 상속)·manifest 모드 index 부재 fail-soft(TS-028)·경로 사상(mirrorPathForDir)·layerRules 결정론·스키마 검증·extractHeader 근접 제약 CLI 블랙박스 테스트 (F-003, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-4", "S-5", "S-6", "S-8", "S-12", "S-17", "S-20"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 077이 고정한 `resolveHeader`의 "5단 상속 + 인라인 단독 승리"는 **`auto` 모드의 서술**이었다
// (`header-standard.md:189-191`). 080은 `auto`를 제거하고 `headerSource`를 2택(inline|manifest)
// 전역 단일 키로 확정하므로(PLAN §3.3.2 (A)), tier①(인라인)과 tier②~⑤(매니페스트)는 **모드에 의해
// 상호 배타**가 되고 "두 소스 경합 → 인라인 승리"라는 병합 규칙 자체가 소멸한다.
// 아래 재작성은 기대값을 느슨하게 바꿔 통과시키는 것이 아니라, 같은 불변식("두 소스가 조용히
// 섞이지 않는다")을 **모드별로 분담시켜 같은 강도로 다시 고정**하는 계약 이전이다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다.
//
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.3.5/§3.7.2, TEST-SCENARIO.md §3 S-12 / §4):
//
// | 케이스 프리픽스 / 077 자산                   | TS-ID          | S-ID | 계층 |
// |----------------------------------------------|----------------|------|------|
// | [T080/L1-H12] manifest + index 부재 fail-soft | TS-028         | S-12 | L1   |
// | 077 TS-002 schema-unsupported-version         | 077 TS-002     | S-4  | L2   |
// | 077 TS-003 schema-invalid-index               | 077 TS-003     | S-4  | L2   |
// | 077 S-4 pt.2 manifest-parse-failed            | (077 S-4 pt.2) | S-4  | L2   |
// | 077 TS-004 그룹 A(tier②~⑤ 4케이스)            | 077 TS-004     | S-5  | L2   |
// | 077 TS-004 그룹 B(tier① 인라인)               | 077 TS-004     | S-5  | L2   |
// | 077 TS-007 단일 파일 역매핑                    | 077 TS-007     | S-8  | L2   |
// | 077 TS-008 mirrorPathForDir 5케이스            | 077 TS-008     | S-1  | L1   |
// | 077 TS-009 layerRules tie-break                | 077 TS-009     | S-2  | L1   |
// | 077 TS-044/045 모드별 무병합 불변식 (승계처)     | 077 TS-044/045 | S-17 | L2   |
// | 077 S-20 depends package 상속                  | (077 H-2)      | S-20 | L2   |
// | 077 결함 C extractHeader 근접 제약 (대조군 포함) | TS-077-C-1~4   | —    | L1   |
//
// [MUST] **TS-ID 네임스페이스** (PLAN §3.7.2 각주): 본 태스크(080)의 TS-ID와 077의 TS-ID는 서로 다른
// 번호 체계다. 077 자산을 가리킬 때는 항상 `077 TS-NNN`으로 표기한다 — 혼동하면 엉뚱한 테스트를 지운다.
//
// [MUST] red-first.md §4 — 공개 인터페이스(실 CLI subprocess의 exit code · stdout JSON · stderr)로만
// 검증한다. 예외는 077 TS-008 / TS-077-C-* 로, `module.exports`로 **공개된** mirrorPathForDir·
// extractHeader를 직접 호출하는 077 승계 자산이다(내부 private 결합 아님).
//
// mock 금지 — 전 케이스가 실 픽스처 + 실 파일시스템 + 실 subprocess로만 동작한다.
// 픽스처 커밋 상태는 수정하지 않는다. 사전 조작은 전부 임시 복사본 오버레이로 한다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v1.1 2026-07-29 KST: 결함 B/C 재작업 — headerSource 실 config 오버레이 검증 + extractHeader 근접 제약
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — manifest 모드 index 부재 fail-soft(TS-028) 신설,
//     077 TS-005 폐기(불변식은 077 TS-044/045로 분할 승계), 077 TS-046 폐기(auto 폴백 소멸 →
//     test-header-source.js TS-003이 승계), 077 TS-004/007/S-20을 모드 오버레이 위로 이전
//     (그룹 A/B, PLAN §3.7.2) (opal-test-agent mode:red)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
const FIX = path.resolve(__dirname, 'fixtures');

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
 * 임의 픽스처를 임시 복사본으로 복제하고 `.opal/code-scan.json`의 **최상위** `headerSource`만 교체한다.
 * 픽스처 자산은 절대 수정하지 않는다(PLAN §3.7.2 "픽스처 자산 무변경").
 */
function overlayHeaderSource(fixtureRelPath, value) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t080-headersource-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureRelPath), dir);
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  cfg.headerSource = value;
  fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\n');
  return dir;
}

/** 077 승계 헬퍼 — codemap-repo 전용 축약형 (원 위치: test-resolve-header.js:74-83). */
function makeHeaderSourceFixture(value) {
  return overlayHeaderSource('codemap-repo', value);
}

/**
 * code-scan.js를 CLI 블랙박스로 실행한다. mock/monkeypatch 없음 — 실 subprocess + 실 파일시스템.
 * @param {string} cwd
 * @param {string[]} args
 * @param {object} [envOverride]
 */
function run(cwd, args, envOverride = {}) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd,
    env: { ...process.env, ...envOverride },
    encoding: 'utf8',
    timeout: 10000,
  });
  const stdout = result.stdout || '';
  const stderr = result.stderr || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON, or command not JSON-capable yet */ }
  return { exitCode: result.status, stdout, stderr, json };
}

/** stderr의 비공백 줄만 센다 — "경고 1줄" 계약을 정확히 측정하기 위한 것. */
function stderrLines(stderr) {
  return String(stderr).split('\n').map(l => l.trim()).filter(l => l.length > 0);
}

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-H12] TS-028 (S-12): `manifest` 모드 + `.opal/code-map/index.json` 부재 — fail-soft
// ═════════════════════════════════════════════════════════════════════════
//
// PLAN §3.3.2 (A): `manifest` 모드에서 index.json이 없으면 조회 결과가 전량 공백이 된다. 이때
// **차단(exit 1)하지 않고** stderr 경고 1줄로 사유를 노출한다 — 차단 조건을 늘리면 D-5 범위를
// 넘어서므로 의도적으로 fail-soft를 택한다(H-12). 핵심은 "조용한 전량 공백"이 아니라 "사유가
// 보이는 빈 결과"라는 것이다. 경고는 stderr 전용이어야 한다 — stdout은 `--json` 소비자
// (brain_tool.py:793 `json.loads(result.stdout)`)의 파이프이므로 오염되면 안 된다.
//
// 무대: legacy-repo(= code-map 부재 트리)에 전역 headerSource만 "manifest"로 오버레이한다.

test('[T080/L1-H12] TS-028 (S-12): manifest 모드 + index.json 부재 → exit 0 (비차단)', () => {
  const dir = overlayHeaderSource('legacy-repo', 'manifest');
  assert.strictEqual(fs.existsSync(path.join(dir, '.opal', 'code-map', 'index.json')), false,
    '전제: 이 트리에는 .opal/code-map/index.json이 없어야 한다');

  const { exitCode, stderr, stdout } = run(dir, ['scan', '--json']);
  assert.strictEqual(exitCode, 0,
    `[RED expect] index 부재는 차단 조건이 아니다 — exit 0 기대, got ${exitCode} (stderr: ${stderr}, stdout: ${stdout})`);
});

test('[T080/L1-H12] TS-028 (S-12): manifest 모드 + index.json 부재 → stderr 경고 정확히 1줄', () => {
  const dir = overlayHeaderSource('legacy-repo', 'manifest');
  const { stderr } = run(dir, ['scan', '--json']);
  const lines = stderrLines(stderr);

  assert.strictEqual(lines.length, 1,
    `[RED expect] 경고는 정확히 1줄이어야 한다(파일 수만큼 반복되면 안 됨 — warnOnce). got ${lines.length}줄: ${JSON.stringify(lines)}`);
  assert.ok(/index\.json/.test(lines[0]),
    `[RED expect] 경고 문구가 부재 자산(.opal/code-map/index.json)을 지목해야 한다, got "${lines[0]}"`);
  assert.ok(/manifest/.test(lines[0]),
    `[RED expect] 경고 문구가 현재 모드(manifest)를 밝혀야 한다 — 사유가 보이는 빈 결과, got "${lines[0]}"`);
});

test('[T080/L1-H12] TS-028 (S-12): manifest 모드 + index.json 부재 → stdout JSON 무오염 + 빈 결과', () => {
  const dir = overlayHeaderSource('legacy-repo', 'manifest');
  const { json, stdout } = run(dir, ['scan', '--json']);

  assert.ok(json !== null,
    `[RED expect] 경고가 stdout으로 새면 파이프 소비자(brain_tool.py:793)가 깨진다 — stdout은 유효 JSON이어야 함. raw: ${JSON.stringify(stdout)}`);
  assert.strictEqual(Object.keys(json).length, 0,
    `[RED expect] manifest 모드는 인라인을 읽지 않으므로 index 부재 시 결과가 0건이어야 한다, got ${JSON.stringify(Object.keys(json))}`);
});

test('[T080/L1-H12] TS-028 (S-12) [대조군]: 같은 트리를 inline으로 두면 경고 0줄 + 정상 결과', () => {
  const dir = overlayHeaderSource('legacy-repo', 'inline');
  const { exitCode, stderr, json } = run(dir, ['scan', '--json']);

  assert.strictEqual(exitCode, 0, `inline 모드는 exit 0이어야 함, got ${exitCode}`);
  assert.strictEqual(stderrLines(stderr).length, 0,
    `[RED expect] index 부재 경고는 manifest 모드 전용이다 — inline 모드에서 새어 나오면 안 됨, got ${JSON.stringify(stderr)}`);
  assert.ok(json && Object.keys(json).length > 0,
    `[RED expect] inline 모드에서는 인라인 @header 보유 파일이 결과에 나와야 한다, got ${JSON.stringify(json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-002 (S-4): version:2 index → 모든 code-map 서브명령이 unsupported_version exit 1
// ═════════════════════════════════════════════════════════════════════════

test('077 TS-002 (S-4): version:2 index — discover가 unsupported_version exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'version-mismatch');
  const { exitCode, json } = run(cwd, ['discover', '--dry-run', '--json']);

  assert.strictEqual(exitCode, 1,
    `[RED expect] version:2 index는 exit 1 기대, got ${exitCode}`);
  assert.ok(json !== null, '[RED expect] stdout이 JSON 에러 객체여야 함');
  assert.strictEqual(json && json.error, 'unsupported_version',
    `[RED expect] error 코드가 unsupported_version이어야 함, got ${JSON.stringify(json)}`);
});

test('077 TS-002 (S-4): version:2 index — scan(읽기 경로)도 unsupported_version exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'version-mismatch');
  const { exitCode, json } = run(cwd, ['scan', '--json']);

  assert.strictEqual(exitCode, 1,
    `[RED expect] scan도 code-map을 로드하는 순간 스키마를 검증해 exit 1이어야 함, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'unsupported_version',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-003 (S-4): scopes 누락 / root 누락 index → invalid_index exit 1
// ═════════════════════════════════════════════════════════════════════════

test('077 TS-003 (S-4): scopes 키 자체가 없는 index → invalid_index exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'missing-scopes');
  const { exitCode, json } = run(cwd, ['scan', '--json']);

  assert.strictEqual(exitCode, 1, `[RED expect] invalid_index → exit 1, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'invalid_index',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

test('077 TS-003 (S-4): 스코프의 root 키가 없는 index → invalid_index exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'missing-root');
  const { exitCode, json } = run(cwd, ['scan', '--json']);

  assert.strictEqual(exitCode, 1, `[RED expect] invalid_index → exit 1, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'invalid_index',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// 077 S-4 pt.2: 매니페스트 JSON 파싱 불가 → 조회 경로(scan)가 manifest_parse_failed exit 1
//               (부분 결과를 조용히 반환하지 않는다 — 게이트 관찰 보강)
// ═════════════════════════════════════════════════════════════════════════

test('077 S-4 pt.2: 매니페스트 파싱 실패 → scan이 manifest_parse_failed exit 1 (부분 결과 반환 금지)', () => {
  const cwd = path.join(FIX, 'schema', 'manifest-parse-failed');
  const { exitCode, json, stdout } = run(cwd, ['scan', '--json']);

  assert.strictEqual(exitCode, 1,
    `[RED expect] manifest_parse_failed → exit 1, got ${exitCode} (stdout: ${stdout})`);
  assert.strictEqual(json && json.error, 'manifest_parse_failed',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-004 (S-5) — 그룹 B: tier① 인라인 단독 (PLAN §3.7.2 그룹 B, 명제 교체 후 이전)
// ═════════════════════════════════════════════════════════════════════════
//
// [명제 교체 근거 — 약화가 아님] 077 원본은 `codemap-repo`(당시 auto 모드)에서 AdminHome.tsx의
// `_source === 'inline'`을 단언했다. 080의 `inline` 모드는 `extractHeader` 결과를 **그대로** 반환하며
// `_source` 키를 붙이지 않는다(PLAN §3.3.2 (A) — 조회 8커맨드 골든 보존 지점). 따라서 `_source ===
// 'inline'` 단언은 신 계약에서 **성립할 수 없는 명제**가 되었다.
// 같은 사실("이 파일은 인라인 소스로 해석된다")을 신 계약이 관찰 가능한 형태 — 인라인 값 반환 +
// `_source` 키 부재 — 로 재서술해 강도를 유지한다. `inline` 모드의 배타성(매니페스트 유래 0건)은
// 077 TS-044가 전담한다.

test('077 TS-004 (S-5) 그룹 B [명제 교체]: inline 모드 — AdminHome.tsx가 인라인 값으로 반환되고 _source 키가 없다', () => {
  const dir = makeHeaderSourceFixture('inline');
  const { exitCode, json } = run(dir, ['scan', '--json']);
  const key = 'web/admin/pages/AdminHome.tsx';

  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode}`);
  assert.ok(json && json[key], `[RED expect] ${key} 결과가 존재해야 함`);
  assert.strictEqual(json[key].module, 'AdminHome',
    `[RED expect] inline 모드는 인라인 @header 값을 그대로 반환해야 함, got ${JSON.stringify(json[key])}`);
  assert.deepStrictEqual(json[key].exports, ['AdminHome']);
  assert.ok(!Object.prototype.hasOwnProperty.call(json[key], '_source'),
    `[RED expect] inline 모드는 _source 키를 붙이지 않는다(골든 보존 계약, PLAN §3.3.2 (A)), got ${JSON.stringify(json[key])}`);
});

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-004 (S-5) — 그룹 A: tier②~⑤ 단독 4케이스 (PLAN §3.7.2 그룹 A, 기대값 동일 이전)
// ═════════════════════════════════════════════════════════════════════════
//
// [이전 근거] 이 4개 파일은 애초에 인라인 @header가 없으므로 `manifest` 모드에서 결과가 동일하다.
// 077 기대값(_source·description·exports·layer·domain)을 **그대로** 유지한 채 실행 무대만
// `makeHeaderSourceFixture('manifest')` 오버레이로 옮긴다 — 모드를 명시하지 않으면 이 4케이스가
// "어느 모드에서 성립하는 명제인지"가 코드에 남지 않는다.

test('077 TS-004 (S-5) 그룹 A: manifest 모드 file 단독 — OrderService.java의 _source는 file', () => {
  const dir = makeHeaderSourceFixture('manifest');
  const { json } = run(dir, ['scan', '--json']);
  const key = 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java';

  assert.ok(json && json[key],
    `[RED expect] ${key}가 code-map file tier로 커버되어 결과에 나타나야 함`);
  assert.strictEqual(json[key] && json[key]._source, 'file',
    `[RED expect] _source: file 기대, got ${JSON.stringify(json && json[key])}`);
  assert.strictEqual(json[key] && json[key].description, '주문 생성/조회 처리 서비스 (file tier 단독 예시)');
  assert.deepStrictEqual(json[key] && json[key].exports, ['OrderService', 'createOrder']);
});

test('077 TS-004 (S-5) 그룹 A: manifest 모드 package 단독 — ShipRepo.java의 _source는 package', () => {
  const dir = makeHeaderSourceFixture('manifest');
  const { json } = run(dir, ['scan', '--json']);
  const key = 'svc/ship-api/src/main/java/com/acme/ship/repository/ShipRepo.java';

  assert.ok(json && json[key], `[RED expect] ${key}가 package tier로 커버되어야 함`);
  assert.strictEqual(json[key] && json[key]._source, 'package',
    `[RED expect] _source: package 기대, got ${JSON.stringify(json && json[key])}`);
  assert.deepStrictEqual(json[key] && json[key].depends, ['ship-common'],
    '[RED expect] package.depends가 file tier 부재 시 그대로 상속되어야 함');
});

test('077 TS-004 (S-5) 그룹 A: manifest 모드 rule 단독 — AdminGuard.tsx의 _source는 rule (domain 불일치)', () => {
  const dir = makeHeaderSourceFixture('manifest');
  const { json } = run(dir, ['scan', '--json']);
  const key = 'web/admin/service/AdminGuard.tsx';

  assert.ok(json && json[key], `[RED expect] ${key}가 layerRules(tier④)로만 커버되어야 함`);
  assert.strictEqual(json[key] && json[key]._source, 'rule',
    `[RED expect] _source: rule 기대, got ${JSON.stringify(json && json[key])}`);
  assert.strictEqual(json[key] && json[key].layer, 'service',
    '[RED expect] "**/service/**" layerRule 매칭으로 layer=service');
  assert.strictEqual(json[key] && json[key].domain, undefined,
    '[RED expect] 좁혀진 admin domain(web/admin/pages/**)에 미매칭이므로 domain 없어야 함');
});

test('077 TS-004 (S-5) 그룹 A: manifest 모드 domain 단독 — OrderMisc.java의 _source는 domain', () => {
  const dir = makeHeaderSourceFixture('manifest');
  const { json } = run(dir, ['scan', '--json']);
  const key = 'svc/order-api/misc/OrderMisc.java';

  assert.ok(json && json[key], `[RED expect] ${key}가 domains(tier⑤)로만 커버되어야 함`);
  assert.strictEqual(json[key] && json[key]._source, 'domain',
    `[RED expect] _source: domain 기대, got ${JSON.stringify(json && json[key])}`);
  assert.strictEqual(json[key] && json[key].domain, 'order');
  assert.strictEqual(json[key] && json[key].layer, undefined,
    '[RED expect] 어떤 layerRule 패턴에도 매칭되지 않으므로 layer 없어야 함');
});

// ═════════════════════════════════════════════════════════════════════════
// [폐기 기록] 077 TS-005 (S-6) "혼재 파일 인라인 승리, 병합 없음" — 삭제 (PLAN §3.7.2 그룹 C)
// ═════════════════════════════════════════════════════════════════════════
//
// 원본: 구 `test-resolve-header.js:244-262` — `codemap-repo`를 `auto` 단일 실행으로 돌려
//       AdminHome.tsx(인라인 + 매니페스트 혼재 파일)에서 "인라인이 이긴다 + 매니페스트 전용
//       exports가 병합되지 않는다"를 단언했다.
//
// 폐기 사유: `auto`가 제거되면(D-3) **두 소스가 한 실행에서 공존해 우선순위가 적용되는 상황 자체가
//            발생하지 않는다.** 모드가 소스를 고르므로 경합이 없고, "인라인이 이긴다"는 명제는
//            참·거짓을 물을 수 없는 문장이 된다(PLAN §3.3.2 (A) "병합 규칙 자체가 소멸").
//
// [MUST] 불변식은 소실되지 않는다 — TS-005가 지키던 "두 소스가 조용히 섞이지 않는다"는
//        **077 TS-044(inline 방향)·077 TS-045(manifest 방향)로 분할 승계**된다(아래 두 케이스).
//        약화된 재정의 테스트를 새로 만들지 않는다 — 만들면 077 TS-044/045와 진짜 중복이 되어
//        [MUST] `opal/core/PRINCIPLES.md` §2(중복 제거)에 어긋난다.

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-007 (S-8): 단일 파일 역매핑 — 인라인 없음, 매니페스트만
//                   PM Gate 8번(`scan <file> --json`) 보호 — 결과 0건이면 안 됨
// ═════════════════════════════════════════════════════════════════════════
//
// [이전 근거 — 그룹 A] 대상 파일(legacy/lib/legacy_util.py)에는 인라인 @header가 없으므로
// `manifest` 모드에서 077 기대값이 그대로 성립한다. 077 원문의 "readonly 스코프" 표현은 080에서
// 판정 근거가 아니게 됐으므로(F-004: 무시 + 안내) 케이스명에서 제거했다 — 검증 명제는
// "매니페스트만 있는 단일 파일 조회가 0건이 아니다"이지 readonly가 아니다.

test('077 TS-007 (S-8): manifest 모드 scan <단일파일> --json — 매니페스트 헤더 반환 (PM Gate 8 보호)', () => {
  const dir = makeHeaderSourceFixture('manifest');
  const rel = 'legacy/lib/legacy_util.py';
  const { exitCode, json, stdout } = run(dir, ['scan', rel, '--json']);

  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  const keys = json ? Object.keys(json) : [];
  assert.strictEqual(keys.length, 1,
    `[RED expect] 결과가 정확히 1건이어야 함 (0건이면 PM Gate 8번 절차 파손), got ${keys.length} keys: ${JSON.stringify(json)}`);
  const header = json[keys[0]];
  assert.strictEqual(header && header._source, 'file',
    `[RED expect] _source: file 기대, got ${JSON.stringify(header)}`);
  assert.strictEqual(header && header.description,
    '레거시 유틸리티 헬퍼 (readonly 스코프 file tier 단독 예시 — S-8 PM Gate 8 보호)');
});

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-008 (S-1): mirrorPathForDir 정방향 사상 5케이스 — module.exports 공개 인터페이스
// ═════════════════════════════════════════════════════════════════════════

test('077 TS-008 (S-1): mirrorPathForDir이 module.exports로 노출되고 5케이스가 기대 문자열과 일치', () => {
  let mod;
  assert.doesNotThrow(() => {
    delete require.cache[CODE_SCAN_JS];
    mod = require(CODE_SCAN_JS);
  }, '[RED expect] code-scan.js가 require 가능해야 함 (require.main===module 가드 필요)');

  assert.strictEqual(typeof mod.mirrorPathForDir, 'function',
    '[RED expect] mirrorPathForDir가 module.exports로 노출되어야 함');

  const svcScope = { root: 'svc/', anchors: ['order-api', 'ship-api'], stripPrefix: ['src/main/java/com/acme/', 'src/main/java/'] };

  // 케이스 1: 깊은 경로 + stripPrefix 최장 승리
  const r1 = mod.mirrorPathForDir('svc/order-api/src/main/java/com/acme/order/service', 'svc', svcScope);
  assert.strictEqual(r1 && r1.mirrorRel, 'order-api/order/service');

  // 케이스 2: 앵커 없음(anchors:[])
  const legacyScope = { root: 'legacy/', anchors: [], stripPrefix: [] };
  const r2 = mod.mirrorPathForDir('legacy/lib', 'legacy', legacyScope);
  assert.strictEqual(r2 && r2.mirrorRel, 'lib');

  // 케이스 3: 루트 직속 → _root
  const r3 = mod.mirrorPathForDir('legacy', 'legacy', legacyScope);
  assert.strictEqual(r3 && r3.mirrorRel, '_root');

  // 케이스 4: 스코프 외 → skipped
  const r4 = mod.mirrorPathForDir('other/dir', 'legacy', legacyScope);
  assert.strictEqual(r4 && r4.skipped, 'out_of_scope');

  // 케이스 5: stripPrefix 최장 승리(2개 후보 중 더 긴 것)
  const r5 = mod.mirrorPathForDir('svc/order-api/src/main/java/other', 'svc', svcScope);
  assert.strictEqual(r5 && r5.mirrorRel, 'order-api/other');
});

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-009 (S-2): layerRules 동률 tie-break — 배열 순서 무관
// ═════════════════════════════════════════════════════════════════════════

test('077 TS-009 (S-2): 동률 layerRules — 배열 순서를 바꿔도 동일 layer 반환 (order-a vs order-b)', () => {
  const cwdA = path.join(FIX, 'tiebreak', 'order-a');
  const cwdB = path.join(FIX, 'tiebreak', 'order-b');

  const { json: jsonA } = run(cwdA, ['scan', '--json']);
  const { json: jsonB } = run(cwdB, ['scan', '--json']);

  const key = 'app/foo/goo/File.ts';

  assert.ok(jsonA && jsonA[key], `[RED expect] order-a에서 ${key} 결과가 존재해야 함`);
  assert.ok(jsonB && jsonB[key], `[RED expect] order-b에서 ${key} 결과가 존재해야 함`);

  assert.strictEqual(jsonA[key].layer, 'layer-foo',
    `[RED expect] order-a layer=layer-foo 기대, got ${JSON.stringify(jsonA[key])}`);
  assert.strictEqual(jsonB[key].layer, 'layer-foo',
    `[RED expect] order-b도 동일해야 함(배열 순서 무관), got ${JSON.stringify(jsonB[key])}`);
  assert.strictEqual(jsonA[key].layer, jsonB[key].layer,
    '두 index의 layer 결과가 반드시 동일해야 한다 (H-12)');
});

// ═════════════════════════════════════════════════════════════════════════
// 077 TS-044 / TS-045 (S-17): headerSource 2택 스위치 — 실 config 오버레이 검증
// ═════════════════════════════════════════════════════════════════════════
//
// [MUST] **TS-005(077)에서 승계**: 삭제된 테스트("혼재 파일 인라인 승리, 병합 없음",
//        구 `test-resolve-header.js:244-262`)의 불변식 — *두 소스가 조용히 섞이지 않는다* — 를
//        이 두 케이스가 **모드별로 분담**한다. 아래 두 케이스는 우연히 겹치는 중복이 아니라
//        TS-005의 정식 승계처이며, **정확히 같은 혼재 파일(`web/admin/pages/AdminHome.tsx`)을
//        대상으로 반대 방향 오염을 각각 막는다**(PLAN §3.7.2 그룹 C 결정표):
//          · 077 TS-044 (inline 방향)  — 매니페스트 유래 헤더가 결과에 0건임을 개별 단언
//          · 077 TS-045 (manifest 방향) — 인라인 전용 값이 결과에 섞이지 않음을 명시 단언
//        [MUST] 이 두 케이스의 부정 단언(반대 소스 0건)을 약화하면 TS-005의 방어가 실제로
//        소실된다. 승계 근거가 코드에 남아야 후속 워커가 "방어가 사라졌다"고 오판하지 않는다.

test('077 TS-044 (S-17) [TS-005 승계 — inline 방향]: headerSource:"inline" — 인라인 보유 파일만 반환, 매니페스트 유래 0건', () => {
  const dir = makeHeaderSourceFixture('inline');
  const { exitCode, json } = run(dir, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode}`);
  assert.ok(json, 'stdout이 유효 JSON이어야 함');

  const keys = Object.keys(json);
  assert.strictEqual(keys.length, 1,
    `headerSource:"inline"은 실제 인라인 @header를 가진 파일(AdminHome.tsx) 1건만 반환해야 함, got ${JSON.stringify(keys)}`);
  assert.ok(json['web/admin/pages/AdminHome.tsx'], 'AdminHome.tsx(인라인 보유) 결과가 존재해야 함');
  assert.strictEqual(json['web/admin/pages/AdminHome.tsx'].module, 'AdminHome');

  // [TS-005 승계] 매니페스트 전용 필드가 인라인 결과에 병합되면 안 된다.
  assert.ok(!(json['web/admin/pages/AdminHome.tsx'].exports || []).includes('ManifestOnlyExport'),
    '[TS-005 승계] 매니페스트 전용 exports가 inline 모드 결과에 병합되면 안 됨');

  // 매니페스트(file/package/rule/domain tier)로만 커버되는 파일은 inline 모드에서 결과에 나타나면 안 됨
  const manifestOnlyKeys = [
    'svc/order-api/src/main/java/com/acme/order/service/OrderService.java', // file tier
    'svc/ship-api/src/main/java/com/acme/ship/repository/ShipRepo.java',   // package tier
    'web/admin/service/AdminGuard.tsx',                                    // rule tier
    'svc/order-api/misc/OrderMisc.java',                                   // domain tier
    'legacy/lib/legacy_util.py',                                           // file tier
  ];
  for (const k of manifestOnlyKeys) {
    assert.strictEqual(json[k], undefined,
      `headerSource:"inline"에서는 지도 유래 헤더가 0건이어야 함 — ${k}가 결과에 나타나면 안 됨, got ${JSON.stringify(json[k])}`);
  }
});

test('077 TS-045 (S-17) [TS-005 승계 — manifest 방향]: headerSource:"manifest" — 인라인 무시, 매니페스트 필드로 대체', () => {
  const dir = makeHeaderSourceFixture('manifest');
  const { exitCode, json } = run(dir, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode}`);
  assert.ok(json, 'stdout이 유효 JSON이어야 함');

  const key = 'web/admin/pages/AdminHome.tsx';
  assert.ok(json[key], `headerSource:"manifest"에서도 ${key} 결과가 존재해야 함(다른 tier로 커버)`);
  assert.notStrictEqual(json[key]._source, 'inline',
    `[계약] manifest 모드에서는 인라인이 존재하는 파일도 _source가 "inline"이면 안 됨, got ${JSON.stringify(json[key])}`);
  assert.strictEqual(json[key].description,
    '매니페스트 전용 설명 — 인라인이 존재하므로 병합되면 안 됨 (S-6 혼재 검증)',
    `manifest 모드에서는 인라인 description이 아니라 매니페스트 description이 반환되어야 함, got ${JSON.stringify(json[key])}`);
  assert.deepStrictEqual(json[key].exports, ['ManifestOnlyExport'],
    `manifest 모드에서는 인라인 exports(["AdminHome"])가 아니라 매니페스트 exports가 반환되어야 함, got ${JSON.stringify(json[key].exports)}`);
  // [TS-005 승계] 인라인 전용 값이 manifest 모드 결과로 새면 안 된다.
  assert.ok(!(json[key].exports || []).includes('AdminHome'),
    '[TS-005 승계] 인라인 전용 exports("AdminHome")가 manifest 모드 결과에 섞이면 안 됨');
  // `module`은 부정 단언 대상이 아니다 — 매니페스트 엔트리에 module이 없으면 파일명 stem으로
  // 파생되므로(`deriveStem`) 값이 우연히 인라인과 같아진다. 인라인 유출과 구분 불가한 필드이므로
  // 여기서 단언하면 테스트 결함이 된다. 무병합 불변식은 description/exports/note 축으로 고정한다.
  assert.strictEqual(json[key].note, '매니페스트 전용 노트 (병합 금지 검증용)',
    `[TS-005 승계] manifest 모드 결과의 note는 매니페스트 값이어야 함, got ${JSON.stringify(json[key].note)}`);

  // file tier 파일(OrderService.java)은 manifest 모드에서 정상 커버되어야 함
  const orderKey = 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java';
  assert.ok(json[orderKey], `manifest 모드에서도 file tier 단독 파일(${orderKey})은 여전히 커버되어야 함`);
});

// ═════════════════════════════════════════════════════════════════════════
// [폐기 기록] 077 TS-046 (S-17) `headerSource:"bogus"` → `auto` 폴백 — 삭제
// ═════════════════════════════════════════════════════════════════════════
//
// 원본: 구 `test-resolve-header.js:406-419` — 무효값 "bogus"가 stderr 경고 후 `auto`로 **폴백**하고
//       stdout이 auto 모드 결과와 바이트 동일함(exit 0)을 단언했다.
//
// 폐기 사유: `auto` 폴백 자체가 제거됐다(PLAN §1.5 계약 변경표 · D-3/D-4). 폴백할 값이 없으므로
//            "bogus는 auto와 같은 결과를 낸다"는 명제는 **성립 불가**다 — 약화가 아니라 소멸이다.
//
// [MUST] 대체 검증은 **반전**되어 이미 존재한다 — 무효값은 `header_source_invalid` + `where:"config"`
//        + exit 1로 거부된다. 담당은 `tests/test-header-source.js`의 TS-003(`auto` 특례 경로)과
//        TS-065(임의 무효값 일반 경로)이며, CLI 무효값은 TS-009가 맡는다(PLAN §3.1.5 · TEST-SCENARIO
//        §4 "077 TS-046 반전 승계처"). 이 파일에 남기면 두 파일이 같은 명제를 중복 검증하게 된다.

// ═════════════════════════════════════════════════════════════════════════
// 077 S-20 (H-2): package tier depends 상속 — depends <module> 결과에 2파일 모두 포함
// ═════════════════════════════════════════════════════════════════════════
//
// [이전 근거 — 그룹 A] 대상 2파일에는 인라인 @header가 없다. `manifest` 모드 오버레이 위에서
// 077 기대값이 그대로 성립한다.

test('077 S-20 (H-2): manifest 모드 depends "ship-common" — package tier 상속이 2파일 모두에서 검출', () => {
  const dir = makeHeaderSourceFixture('manifest');
  const { exitCode, stdout } = run(dir, ['depends', 'ship-common']);

  assert.strictEqual(exitCode, 0, `depends는 exit 0이어야 함, got ${exitCode}`);
  assert.ok(stdout.includes('ShipRepo.java'),
    `[RED expect] package tier 상속 depends로 ShipRepo.java가 dependedBy에 나타나야 함. stdout: ${stdout}`);
  assert.ok(stdout.includes('ShipValidator.java'),
    `[RED expect] 같은 디렉토리의 두 번째 파일 ShipValidator.java도 함께 나타나야 함. stdout: ${stdout}`);
});

// ═════════════════════════════════════════════════════════════════════════
// 077 결함 C (TS-077-C-*): extractHeader 근접 제약 + 대조군 5종 (회귀 0)
// ═════════════════════════════════════════════════════════════════════════
//
// 계약: "@header" 토큰과 여는 "{"가 근접해야(표준 포맷 "@header {" — 같은 줄, 공백만) 헤더로
// 인정한다. 산문 언급 뒤 임의 위치의 무관 "{"는 헤더로 인정하지 않는다. 기존 정상 헤더
// (JSDoc/Python docstring/"//" 주석/Vue HTML 주석)는 계속 인식되어야 한다(회귀 0).
// 픽스처 `header-proximity/`의 커밋 headerSource는 "inline"이며 이 명제와 정합한다.

const HP_FIX = path.join(FIX, 'header-proximity');

test('TS-077-C-1 (결함 C): extractHeader — 산문 @header 언급 + 뒤따르는 무관 JSON 블록은 null 반환해야 함', () => {
  delete require.cache[CODE_SCAN_JS];
  const mod = require(CODE_SCAN_JS);
  const filePath = path.join(HP_FIX, 'prose-mention.md');

  const header = mod.extractHeader(filePath);
  assert.strictEqual(header, null,
    `[RED expect] 산문 @header 언급 뒤 무관 JSON 블록은 헤더로 인정되면 안 됨(근접 제약 필요), got ${JSON.stringify(header)}`);
});

test('TS-077-C-1 (결함 C): scan --json — 산문 언급 파일이 결과에 미등장 + missing에 등장', () => {
  const { exitCode: scanExit, json } = run(HP_FIX, ['scan', '--json']);
  assert.strictEqual(scanExit, 0, `scan은 exit 0이어야 함, got ${scanExit}`);
  assert.ok(json, 'stdout이 유효 JSON이어야 함');

  assert.strictEqual(json['prose-mention.md'], undefined,
    `[RED expect] prose-mention.md는 scan --json 결과에 등장하면 안 됨, got ${JSON.stringify(json['prose-mention.md'])}`);

  const { exitCode: missingExit, stdout: missingOut } = run(HP_FIX, ['missing']);
  assert.strictEqual(missingExit, 0, `missing은 exit 0이어야 함, got ${missingExit}`);
  assert.ok(missingOut.includes('prose-mention.md'),
    `[RED expect] prose-mention.md가 missing 목록에 등장해야 함, got stdout: ${missingOut}`);
});

test('TS-077-C-2 (대조군 — 회귀 0): 정상 JSDoc 헤더는 계속 인식되어야 함', () => {
  delete require.cache[CODE_SCAN_JS];
  const mod = require(CODE_SCAN_JS);
  const header = mod.extractHeader(path.join(HP_FIX, 'normal-header.js'));
  assert.ok(header, '정상 JSDoc 헤더는 null이면 안 됨');
  assert.strictEqual(header.module, 'normal-header-demo');
  assert.deepStrictEqual(header.exports, ['normalHeaderDemo']);
});

test('TS-077-C-3 (대조군 — 회귀 0): 정상 헤더 뒤에 무관한 { 블록이 와도 계속 인식되어야 함', () => {
  delete require.cache[CODE_SCAN_JS];
  const mod = require(CODE_SCAN_JS);
  const header = mod.extractHeader(path.join(HP_FIX, 'header-then-unrelated-brace.js'));
  assert.ok(header, '정상 헤더 + 뒤쪽 무관 {를 가진 파일도 null이면 안 됨');
  assert.strictEqual(header.module, 'trailing-brace-demo');
  assert.deepStrictEqual(header.exports, ['trailingBraceDemo']);
  assert.strictEqual(header.scopes, undefined, '뒤쪽 무관 { 블록의 필드가 헤더에 병합되면 안 됨');
  assert.strictEqual(header.extensions, undefined, '뒤쪽 무관 { 블록의 필드가 헤더에 병합되면 안 됨');
});

test('TS-077-C-4 (대조군 — 회귀 0): Python docstring 포맷 헤더는 계속 인식되어야 함', () => {
  delete require.cache[CODE_SCAN_JS];
  const mod = require(CODE_SCAN_JS);
  const header = mod.extractHeader(path.join(HP_FIX, 'python-docstring.py'));
  assert.ok(header, 'Python docstring 헤더는 null이면 안 됨');
  assert.strictEqual(header.module, 'python-docstring-demo');
});

test('TS-077-C-4 (대조군 — 회귀 0): "//" 라인 주석 포맷 헤더는 계속 인식되어야 함', () => {
  delete require.cache[CODE_SCAN_JS];
  const mod = require(CODE_SCAN_JS);
  const header = mod.extractHeader(path.join(HP_FIX, 'slash-comment.js'));
  assert.ok(header, '"//" 주석 헤더는 null이면 안 됨');
  assert.strictEqual(header.module, 'slash-comment-demo');
});

test('TS-077-C-4 (대조군 — 회귀 0): Vue HTML 주석 포맷 헤더는 계속 인식되어야 함', () => {
  delete require.cache[CODE_SCAN_JS];
  const mod = require(CODE_SCAN_JS);
  const header = mod.extractHeader(path.join(HP_FIX, 'html-comment.vue'));
  assert.ok(header, 'Vue HTML 주석 헤더는 null이면 안 됨');
  assert.strictEqual(header.module, 'html-comment-demo');
});
