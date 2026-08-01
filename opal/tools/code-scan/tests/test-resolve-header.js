/**
 * @header {
 *   "module": "test-resolve-header",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — code-map 5단 상속 해석(resolveHeader)·경로 사상(mirrorPathForDir)·layerRules 결정론·headerSource 스위치·스키마 검증 CLI 블랙박스 테스트 (F-001/F-002/F-010, 태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-1", "S-2", "S-4", "S-5", "S-6", "S-7", "S-8", "S-17", "S-20"]
 * }
 */
//
// [재작업 — 결함 B] Step 19 검증에서 TS-044/TS-046이 픽스처 config에 headerSource를 실제로 설정하지
// 않고 auto 모드 결과만 확인해 공허하게 통과함이 드러났다(TS-045 "manifest" 케이스 자체도 부재).
// 아래에서 codemap-repo 픽스처를 임시 복사본에 복제해 `.opal/code-scan.json`에 headerSource 값을
// 실제로 오버레이한 뒤 검증하도록 강화한다 — 기존 기대값을 느슨하게 바꾸는 약화가 아니라
// 실제 config 오버레이를 추가하는 강화다(캡틴 승인, opal-test-agent mode:red 재작업).
//
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.1.5/§3.2.5/§3.10.5, TEST-SCENARIO.md §4):
//
// | TC 그룹                                | TS-ID          | S-ID | 계층 |
// |-----------------------------------------|----------------|------|------|
// | schema-unsupported-version              | TS-002         | S-4  | L2   |
// | schema-invalid-index (scopes/root 누락)  | TS-003         | S-4  | L2   |
// | schema-manifest-parse-failed            | (S-4 pt.2)     | S-4  | L2   |
// | resolve-5-tier-standalone (5케이스)       | TS-004         | S-5  | L2   |
// | resolve-inline-wins-no-merge             | TS-005         | S-6  | L2   |
// | resolve-single-file-reverse-mapping      | TS-007         | S-8  | L2   |
// | mirror-path-forward-mapping (5케이스)     | TS-008         | S-1  | L1   |
// | layer-rules-tiebreak-order-invariance    | TS-009         | S-2  | L1   |
// | header-source-switch (auto/inline/manifest/bogus) | TS-044~046 | S-17 | L2 |
// | depends-package-inheritance-snapshot    | (H-2)          | S-20 | L2   |
//
// RED-first 트랙: 이 파일은 opal-test-agent(mode:red)가 작성한다. 구현(GREEN)은 op-dev-execute 워커가
// 별도로 수행한다(작성자≠구현자, red-first.md §2). 현재 code-scan.js는 discover/scaffold/target/validate/
// feature 서브명령과 code-map 해석(resolveHeader/_source) 자체가 전혀 없으므로, 아래 전 테스트는
// 실패(exit code 불일치 또는 assertion 실패)해야 정상이다 — 이것이 RED 증거다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
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

// [재작업 — 결함 B] headerSource 실검증용 — codemap-repo 픽스처를 임시 복사본에 복제하고
// `.opal/code-scan.json`에 headerSource 값을 실제로 기재한다(실 파일시스템만 사용, 몽키패치 없음).
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

function makeHeaderSourceFixture(value) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-headersource-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'codemap-repo'), dir);
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  cfg.headerSource = value;
  fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\n');
  return dir;
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

// ─────────────────────────────────────────────────────────────────────────
// TS-002 (S-4): version:2 index → 모든 code-map 서브명령이 unsupported_version exit 1
// ─────────────────────────────────────────────────────────────────────────

test('TS-002 (S-4): version:2 index — discover가 unsupported_version exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'version-mismatch');
  const { exitCode, json } = run(cwd, ['discover', '--dry-run', '--json']);

  // [RED 기대] 현행 code-scan.js에는 discover 서브명령 자체가 없다 → "Unknown command" exit 1이지만
  // error 코드가 unsupported_version이 아니므로 아래 json 검사에서 FAIL한다.
  assert.strictEqual(exitCode, 1,
    `[RED expect] version:2 index는 exit 1 기대, got ${exitCode}`);
  assert.ok(json !== null, '[RED expect] stdout이 JSON 에러 객체여야 함 (현행은 discover 명령 자체가 없어 stderr 텍스트만 출력)');
  assert.strictEqual(json && json.error, 'unsupported_version',
    `[RED expect] error 코드가 unsupported_version이어야 함, got ${JSON.stringify(json)}`);
});

test('TS-002 (S-4): version:2 index — scan(읽기 경로)도 unsupported_version exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'version-mismatch');
  const { exitCode, json } = run(cwd, ['scan', '--json']);

  // [RED 기대] 현행 scan은 code-map을 전혀 로드하지 않으므로 index version을 검증하지 않는다 → exit 0으로 정상 종료.
  assert.strictEqual(exitCode, 1,
    `[RED expect] scan도 code-map을 로드하는 순간 스키마를 검증해 exit 1이어야 함, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'unsupported_version',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-003 (S-4): scopes 누락 / root 누락 index → invalid_index exit 1
// ─────────────────────────────────────────────────────────────────────────

test('TS-003 (S-4): scopes 키 자체가 없는 index → invalid_index exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'missing-scopes');
  const { exitCode, json } = run(cwd, ['scan', '--json']);

  // [RED 기대] 현행은 index.json을 읽지 않으므로 scopes 부재를 감지할 수 없다.
  assert.strictEqual(exitCode, 1, `[RED expect] invalid_index → exit 1, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'invalid_index',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

test('TS-003 (S-4): 스코프의 root 키가 없는 index → invalid_index exit 1', () => {
  const cwd = path.join(FIX, 'schema', 'missing-root');
  const { exitCode, json } = run(cwd, ['scan', '--json']);

  assert.strictEqual(exitCode, 1, `[RED expect] invalid_index → exit 1, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'invalid_index',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// S-4 pt.2: 매니페스트 JSON 파싱 불가 → 조회 경로(scan)가 manifest_parse_failed exit 1
//           (부분 결과를 조용히 반환하지 않는다 — 게이트 관찰 보강)
// ─────────────────────────────────────────────────────────────────────────

test('S-4 pt.2: 매니페스트 파싱 실패 → scan이 manifest_parse_failed exit 1 (부분 결과 반환 금지)', () => {
  const cwd = path.join(FIX, 'schema', 'manifest-parse-failed');
  const { exitCode, json, stdout } = run(cwd, ['scan', '--json']);

  // [RED 기대] 현행은 code-map/매니페스트를 전혀 읽지 않으므로 exit 0 + Any.java 없는 빈 결과({})를 반환한다.
  assert.strictEqual(exitCode, 1,
    `[RED expect] manifest_parse_failed → exit 1, got ${exitCode} (stdout: ${stdout})`);
  assert.strictEqual(json && json.error, 'manifest_parse_failed',
    `[RED expect] error 코드 불일치, got ${JSON.stringify(json)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-004 (S-5): 5단 상속 단독 성립 5케이스 + _source 표기
// ─────────────────────────────────────────────────────────────────────────

test('TS-004 (S-5): inline 단독 — AdminHome.tsx의 _source는 inline', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { json } = run(cwd, ['scan', '--json']);
  const key = 'web/admin/pages/AdminHome.tsx';

  // [RED 기대] 현행 scan은 inline 헤더 자체는 반환하지만 _source 키가 존재하지 않는다.
  assert.ok(json && json[key], `[RED expect] ${key} 결과가 존재해야 함`);
  assert.strictEqual(json[key] && json[key]._source, 'inline',
    `[RED expect] _source: inline 기대, got ${JSON.stringify(json && json[key])}`);
});

test('TS-004 (S-5): file 단독 — OrderService.java의 _source는 file (code-map만으로 커버)', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { json } = run(cwd, ['scan', '--json']);
  const key = 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java';

  // [RED 기대] 현행 scan은 인라인 헤더가 없으므로 이 파일을 결과에 전혀 포함하지 않는다(withHeader 필터 탈락).
  assert.ok(json && json[key],
    `[RED expect] ${key}가 code-map file tier로 커버되어 결과에 나타나야 함 (현행은 결과 0건)`);
  assert.strictEqual(json[key] && json[key]._source, 'file',
    `[RED expect] _source: file 기대, got ${JSON.stringify(json && json[key])}`);
  assert.strictEqual(json[key] && json[key].description, '주문 생성/조회 처리 서비스 (file tier 단독 예시)');
  assert.deepStrictEqual(json[key] && json[key].exports, ['OrderService', 'createOrder']);
});

test('TS-004 (S-5): package 단독 — ShipRepo.java의 _source는 package', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { json } = run(cwd, ['scan', '--json']);
  const key = 'svc/ship-api/src/main/java/com/acme/ship/repository/ShipRepo.java';

  assert.ok(json && json[key], `[RED expect] ${key}가 package tier로 커버되어야 함 (현행은 결과 0건)`);
  assert.strictEqual(json[key] && json[key]._source, 'package',
    `[RED expect] _source: package 기대, got ${JSON.stringify(json && json[key])}`);
  assert.deepStrictEqual(json[key] && json[key].depends, ['ship-common'],
    '[RED expect] package.depends가 file tier 부재 시 그대로 상속되어야 함');
});

test('TS-004 (S-5): rule 단독 — AdminGuard.tsx의 _source는 rule (layerRules 매칭, domain 불일치)', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { json } = run(cwd, ['scan', '--json']);
  const key = 'web/admin/service/AdminGuard.tsx';

  assert.ok(json && json[key], `[RED expect] ${key}가 layerRules(tier④)로만 커버되어야 함 (현행은 결과 0건)`);
  assert.strictEqual(json[key] && json[key]._source, 'rule',
    `[RED expect] _source: rule 기대, got ${JSON.stringify(json && json[key])}`);
  assert.strictEqual(json[key] && json[key].layer, 'service',
    '[RED expect] "**/service/**" layerRule 매칭으로 layer=service');
  assert.strictEqual(json[key] && json[key].domain, undefined,
    '[RED expect] 좁혀진 admin domain(web/admin/pages/**)에 미매칭이므로 domain 없어야 함');
});

test('TS-004 (S-5): domain 단독 — OrderMisc.java의 _source는 domain (layerRules 불일치)', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { json } = run(cwd, ['scan', '--json']);
  const key = 'svc/order-api/misc/OrderMisc.java';

  assert.ok(json && json[key], `[RED expect] ${key}가 domains(tier⑤)로만 커버되어야 함 (현행은 결과 0건)`);
  assert.strictEqual(json[key] && json[key]._source, 'domain',
    `[RED expect] _source: domain 기대, got ${JSON.stringify(json && json[key])}`);
  assert.strictEqual(json[key] && json[key].domain, 'order');
  assert.strictEqual(json[key] && json[key].layer, undefined,
    '[RED expect] 어떤 layerRule 패턴에도 매칭되지 않으므로 layer 없어야 함');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-005 (S-6): 인라인 + 매니페스트 혼재 파일 — 인라인 단독 승리, 병합 없음
// ─────────────────────────────────────────────────────────────────────────

test('TS-005 (S-6): 혼재 파일(AdminHome.tsx) — 매니페스트 전용 필드가 병합되지 않음', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { json } = run(cwd, ['scan', '--json']);
  const key = 'web/admin/pages/AdminHome.tsx';

  assert.ok(json && json[key], `${key} 결과가 존재해야 함`);
  const header = json[key];

  // 인라인 값이 그대로 반환되어야 함
  assert.strictEqual(header.module, 'AdminHome');
  assert.deepStrictEqual(header.exports, ['AdminHome']);

  // [RED 기대] 매니페스트 전용 필드(exports:["ManifestOnlyExport"], note)가 절대 섞이면 안 됨.
  // 현재는 _source 키 자체가 없어 이 assert 통과 여부와 무관하게 상단 _source 체크가 먼저 깨진다.
  assert.strictEqual(header._source, 'inline',
    `[RED expect] _source: inline 기대, got ${JSON.stringify(header)}`);
  assert.ok(!header.exports.includes('ManifestOnlyExport'),
    '매니페스트 전용 exports가 인라인 결과에 병합되면 안 됨');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-007 (S-8): 단일 파일 역매핑 — readonly 스코프, 인라인 없음, 매니페스트만
//               PM Gate 8번(`scan <file> --json`) 보호 — 결과 0건이면 안 됨
// ─────────────────────────────────────────────────────────────────────────

test('TS-007 (S-8): scan <단일파일> --json — readonly 스코프 파일의 매니페스트 헤더 반환 (PM Gate 8 보호)', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const rel = 'legacy/lib/legacy_util.py';
  const { exitCode, json, stdout } = run(cwd, ['scan', rel, '--json']);

  // [RED 기대] 현행 scan <file>은 discoverFiles가 단일 파일 배열만 반환하고 extractHeader가 null이므로
  // 결과 0건({})을 반환한다 — PM Gate 8번이 파손되는 정확히 그 시나리오.
  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  const keys = json ? Object.keys(json) : [];
  assert.strictEqual(keys.length, 1,
    `[RED expect] 결과가 정확히 1건이어야 함 (0건이면 기존 PM Gate 8번 절차 파손), got ${keys.length} keys: ${JSON.stringify(json)}`);
  const header = json[keys[0]];
  assert.strictEqual(header && header._source, 'file',
    `[RED expect] _source: file 기대, got ${JSON.stringify(header)}`);
  assert.strictEqual(header && header.description,
    '레거시 유틸리티 헬퍼 (readonly 스코프 file tier 단독 예시 — S-8 PM Gate 8 보호)');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-008 (S-1): mirrorPathForDir 정방향 사상 5케이스 — 직접 함수 호출 (module.exports 노출 필요)
// ─────────────────────────────────────────────────────────────────────────

test('TS-008 (S-1): mirrorPathForDir이 module.exports로 노출되고 5케이스가 기대 문자열과 일치', () => {
  // [RED 기대] 현행 code-scan.js는 module.exports 자체가 없다(require 시 즉시 main()이 실행되어 버림).
  let mod;
  assert.doesNotThrow(() => {
    delete require.cache[CODE_SCAN_JS];
    mod = require(CODE_SCAN_JS);
  }, '[RED expect] code-scan.js가 require 가능해야 함 (require.main===module 가드 필요, 현행은 즉시 main() 실행)');

  assert.strictEqual(typeof mod.mirrorPathForDir, 'function',
    '[RED expect] mirrorPathForDir가 module.exports로 노출되어야 함');

  const svcScope = { root: 'svc/', anchors: ['order-api', 'ship-api'], stripPrefix: ['src/main/java/com/acme/', 'src/main/java/'], readonly: false };

  // 케이스 1: 깊은 경로 + stripPrefix 최장 승리
  const r1 = mod.mirrorPathForDir('svc/order-api/src/main/java/com/acme/order/service', 'svc', svcScope);
  assert.strictEqual(r1 && r1.mirrorRel, 'order-api/order/service');

  // 케이스 2: 앵커 없음(anchors:[])
  const legacyScope = { root: 'legacy/', anchors: [], stripPrefix: [], readonly: true };
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
  // "src/main/java/" 만 매칭(짧은 후보) — com/acme/ 세그먼트가 없으므로
  assert.strictEqual(r5 && r5.mirrorRel, 'order-api/other');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-009 (S-2): layerRules 동률 tie-break — 배열 순서 무관
// ─────────────────────────────────────────────────────────────────────────

test('TS-009 (S-2): 동률 layerRules — 배열 순서를 바꿔도 동일 layer 반환 (order-a vs order-b)', () => {
  const cwdA = path.join(FIX, 'tiebreak', 'order-a');
  const cwdB = path.join(FIX, 'tiebreak', 'order-b');

  const { json: jsonA } = run(cwdA, ['scan', '--json']);
  const { json: jsonB } = run(cwdB, ['scan', '--json']);

  const key = 'app/foo/goo/File.ts';

  // [RED 기대] 현행 scan은 인라인 헤더가 없는 이 파일을 결과에 포함하지 않는다(빈 {}).
  assert.ok(jsonA && jsonA[key], `[RED expect] order-a에서 ${key} 결과가 존재해야 함`);
  assert.ok(jsonB && jsonB[key], `[RED expect] order-b에서 ${key} 결과가 존재해야 함`);

  assert.strictEqual(jsonA[key].layer, 'layer-foo',
    `[RED expect] order-a layer=layer-foo 기대, got ${JSON.stringify(jsonA[key])}`);
  assert.strictEqual(jsonB[key].layer, 'layer-foo',
    `[RED expect] order-b도 동일해야 함(배열 순서 무관), got ${JSON.stringify(jsonB[key])}`);
  assert.strictEqual(jsonA[key].layer, jsonB[key].layer,
    '두 index의 layer 결과가 반드시 동일해야 한다 (H-12)');
});

// ─────────────────────────────────────────────────────────────────────────
// [재작업 — 결함 B] S-17 (TS-044~046): headerSource 스위치 4값 — 실 config 오버레이 검증
// (codemap-repo 임시 복사본의 .opal/code-scan.json에 headerSource 값을 실제로 기재한다)
// ─────────────────────────────────────────────────────────────────────────

test('S-17 / TS-044 (강화): headerSource:"inline" — 인라인 보유 파일만 반환, 매니페스트 유래 헤더 0건', () => {
  const dir = makeHeaderSourceFixture('inline');
  const { exitCode, json } = run(dir, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `scan은 exit 0이어야 함, got ${exitCode}`);
  assert.ok(json, 'stdout이 유효 JSON이어야 함');

  const keys = Object.keys(json);
  assert.strictEqual(keys.length, 1,
    `headerSource:"inline"은 실제 인라인 @header를 가진 파일(AdminHome.tsx) 1건만 반환해야 함, got ${JSON.stringify(keys)}`);
  assert.ok(json['web/admin/pages/AdminHome.tsx'], 'AdminHome.tsx(인라인 보유) 결과가 존재해야 함');
  assert.strictEqual(json['web/admin/pages/AdminHome.tsx'].module, 'AdminHome');

  // 매니페스트(file/package/rule/domain tier)로만 커버되는 파일은 inline 모드에서 결과에 나타나면 안 됨
  const manifestOnlyKeys = [
    'svc/order-api/src/main/java/com/acme/order/service/OrderService.java', // file tier
    'svc/ship-api/src/main/java/com/acme/ship/repository/ShipRepo.java',   // package tier
    'web/admin/service/AdminGuard.tsx',                                    // rule tier
    'svc/order-api/misc/OrderMisc.java',                                   // domain tier
    'legacy/lib/legacy_util.py',                                           // file tier (readonly)
  ];
  for (const k of manifestOnlyKeys) {
    assert.strictEqual(json[k], undefined,
      `headerSource:"inline"에서는 지도 유래 헤더가 0건이어야 함 — ${k}가 결과에 나타나면 안 됨, got ${JSON.stringify(json[k])}`);
  }
});

test('S-17 / TS-045 (신설): headerSource:"manifest" — 인라인 무시, AdminHome.tsx가 매니페스트 필드로 대체', () => {
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
  assert.ok(!(json[key].exports || []).includes('AdminHome'),
    '인라인 전용 exports("AdminHome")가 manifest 모드 결과에 섞이면 안 됨');

  // auto 모드와 대조 — file tier 파일(OrderService.java)은 manifest 모드에서도 정상 커버되어야 함
  const orderKey = 'svc/order-api/src/main/java/com/acme/order/service/OrderService.java';
  assert.ok(json[orderKey], `manifest 모드에서도 file tier 단독 파일(${orderKey})은 여전히 커버되어야 함`);
});

test('S-17 / TS-046 (강화): headerSource:"bogus" → auto 폴백 + stderr 경고 + stdout JSON 무오염', () => {
  const dir = makeHeaderSourceFixture('bogus');
  const auto = run(path.join(FIX, 'codemap-repo'), ['scan', '--json']);
  const bogus = run(dir, ['scan', '--json']);

  assert.strictEqual(bogus.exitCode, 0, `scan은 exit 0이어야 함, got ${bogus.exitCode}`);
  assert.ok(bogus.json !== null,
    `stdout이 항상 유효 JSON이어야 함(경고로 오염되면 안 됨). raw: ${bogus.stdout}`);
  assert.ok(/invalid headerSource/i.test(bogus.stderr) && /bogus/.test(bogus.stderr),
    `잘못된 headerSource 값에 대한 stderr 경고가 있어야 함("bogus" 언급 포함), got stderr="${bogus.stderr}"`);
  assert.strictEqual(bogus.stdout.trim(), auto.stdout.trim(),
    'headerSource:"bogus"는 auto로 폴백하므로 stdout 결과가 auto 모드와 바이트 동일해야 함');
});

// ─────────────────────────────────────────────────────────────────────────
// S-20 (H-2): package tier depends 상속 — depends <module> 결과에 2파일 모두 포함 (스냅샷 고정)
// ─────────────────────────────────────────────────────────────────────────

test('S-20 (H-2): depends "ship-common" — package tier 상속이 2개 파일 모두에서 dependedBy로 검출', () => {
  const cwd = path.join(FIX, 'codemap-repo');
  const { exitCode, stdout } = run(cwd, ['depends', 'ship-common']);

  // [RED 기대] depends는 scanHeaders(=인라인 전용)만 사용하므로 ShipRepo.java/ShipValidator.java는
  // 애초에 헤더가 없어(인라인 없음) 결과에 전혀 등장하지 않는다.
  assert.strictEqual(exitCode, 0, `depends는 exit 0이어야 함, got ${exitCode}`);
  assert.ok(stdout.includes('ShipRepo.java'),
    `[RED expect] package tier 상속 depends로 ShipRepo.java가 dependedBy에 나타나야 함. stdout: ${stdout}`);
  assert.ok(stdout.includes('ShipValidator.java'),
    `[RED expect] 같은 디렉토리의 두 번째 파일 ShipValidator.java도 함께 나타나야 함(그 디렉토리의 파일 2건). stdout: ${stdout}`);
});

// ─────────────────────────────────────────────────────────────────────────
// [재작업 — 결함 C, PM 실측 진단] extractHeader의 "@header 언급 이후 첫 { " 매칭이
// 근접 제약 없이 동작해, 산문으로 @header를 설명하고 뒤에 무관한 JSON 블록(설정 예시 등)이
// 오는 문서 파일을 자신의 헤더로 오인한다(예: code-scan-management.md가 자기 문서 안의
// `.opal/code-scan.json` 설정 예시를 헤더로 반환). 이 오탐이 `validate`의 uncovered 판정을
// 오염시켜 CLOSE 게이트를 차단한다. git HEAD 비교 경로(classifyUncovered)에는 이미
// hasNearbyHeaderBlock 근접 검사가 있으나(§417-428), 라이브 스캔 경로의 extractHeader
// 자체에는 적용되어 있지 않다 — 이것이 결함 C다.
//
// 계약: "@header" 토큰과 여는 "{"가 근접해야(표준 포맷 "@header {" — 같은 줄, 공백만)
// 헤더로 인정한다. 산문 언급 뒤 임의 위치의 무관 "{"는 헤더로 인정하지 않는다.
// 기존 정상 헤더(JSDoc/Python docstring/"//" 주석/Vue HTML 주석)와, 정상 헤더 뒤에
// 무관한 "{"가 오는 경우는 계속 인식되어야 한다(회귀 0).
//
// 픽스처: tests/fixtures/header-proximity/ (자기완결 신규 트리, 격리 원칙 준수)
//   - prose-mention.md              : 산문 @header 언급 + 뒤따르는 무관 JSON 블록 → 헤더 없음 기대
//   - normal-header.js              : 표준 JSDoc 헤더 → 인식 기대 (대조군)
//   - header-then-unrelated-brace.js: 정상 헤더 + 뒤쪽 무관 { → 인식 기대 (대조군)
//   - python-docstring.py           : Python docstring 포맷 → 인식 기대 (대조군)
//   - slash-comment.js              : "//" 라인 주석 포맷 → 인식 기대 (대조군)
//   - html-comment.vue              : Vue HTML 주석 포맷 → 인식 기대 (대조군)
//
// RED-first: 이 블록은 opal-test-agent(mode:red)가 작성한다. 구현(GREEN, extractHeader에
// 근접 검사 추가)은 별도 워커가 수행한다(작성자≠구현자, red-first.md §2).
// ─────────────────────────────────────────────────────────────────────────

const HP_FIX = path.join(FIX, 'header-proximity');

test('TS-077-C-1 (결함 C): extractHeader — 산문 @header 언급 + 뒤따르는 무관 JSON 블록은 null 반환해야 함', () => {
  delete require.cache[CODE_SCAN_JS];
  const mod = require(CODE_SCAN_JS);
  const filePath = path.join(HP_FIX, 'prose-mention.md');

  // [RED expect] 현행 extractHeader는 "@header" 이후 첫 "{"만 찾으므로, 산문 뒤 멀리 떨어진
  // 무관 JSON 설정 예시 블록을 그대로 헤더로 오인해 non-null(그 JSON 객체)을 반환한다.
  const header = mod.extractHeader(filePath);
  assert.strictEqual(header, null,
    `[RED expect] 산문 @header 언급 뒤 무관 JSON 블록은 헤더로 인정되면 안 됨(근접 제약 필요), got ${JSON.stringify(header)}`);
});

test('TS-077-C-1 (결함 C): scan --json — 산문 언급 파일이 결과에 미등장 + missing에 등장', () => {
  const { exitCode: scanExit, json } = run(HP_FIX, ['scan', '--json']);
  assert.strictEqual(scanExit, 0, `scan은 exit 0이어야 함, got ${scanExit}`);
  assert.ok(json, 'stdout이 유효 JSON이어야 함');

  // [RED expect] 현행은 prose-mention.md가 (오인된) 헤더를 가진 것으로 scan 결과에 등장한다.
  assert.strictEqual(json['prose-mention.md'], undefined,
    `[RED expect] prose-mention.md는 scan --json 결과에 등장하면 안 됨, got ${JSON.stringify(json['prose-mention.md'])}`);

  const { exitCode: missingExit, stdout: missingOut } = run(HP_FIX, ['missing']);
  assert.strictEqual(missingExit, 0, `missing은 exit 0이어야 함, got ${missingExit}`);
  // [RED expect] 현행은 "All files have @header blocks."를 출력한다(오인 때문에 missing 0건).
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
  // 뒤쪽 무관 객체(exampleConfig)의 키가 헤더에 섞여 들어오면 안 됨
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
