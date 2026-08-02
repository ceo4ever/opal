/**
 * @header {
 *   "module": "test-scaffold",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `scaffold` 서브명령의 inline 모드 no-op 계약(TS-023) + manifest 모드 골격 생성·멱등·pruned·mirror_collision 회귀 CLI 블랙박스 테스트 (F-004, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-10"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 077은 `scaffold`를 "항상 매니페스트를 만드는 명령"으로 고정했다. 전역 단일 `headerSource` 2택 도입으로
// `inline` 모드에서는 **매니페스트를 만들 이유 자체가 사라지므로** no-op + 사유 보고가 새 계약이다
// (PLAN §3.3.2 (C)). 077이 검증하던 생성·멱등·pruned·충돌 계약은 **`manifest` 모드에서 그대로 유효**하며
// 아래에 전부 승계된다 — 삭제·완화한 단언은 없고, `inline` 모드 no-op 단언이 **추가**된다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
//
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.3.5, TEST-SCENARIO.md §4):
//
// | 케이스 프리픽스 | TS-ID  | S-ID | 계층 | AC     |
// |-----------------|--------|------|------|--------|
// | [T080/L1-F4]    | TS-023 | S-10 | L1   | F-4 AC |
// | [T077-승계]      | (077 TS-015~019 · S-11) | — | — | manifest 모드 회귀 보존 |
//
// **no-op 판정 기준 (PLAN §3.7.2 TS-073 각주 — 반드시 이 기준으로 측정한다)**:
//   "생성 파일 수 0"이 **아니라** "`.opal/code-map/` 하위 **전 파일의 내용·mtime 무변화** +
//    `skipped[0].reason === 'header_source_inline'`". 커밋 픽스처에 매니페스트가 이미 있으므로
//    생성 수 0은 no-op의 증거가 되지 못한다(덮어써도 0으로 보고될 수 있다).
//
// RED-first: 현행 cmdScaffold(`code-scan.js:1313`)는 headerSource를 전혀 보지 않고 곧바로
// index.json 유무만 확인한 뒤 매니페스트를 쓴다 — `inline` 모드 분기와 `skipped` 사유 보고가 존재하지
// 않으므로 TS-023은 실패해야 정상이다. 구현(GREEN)은 op-dev-execute가 Step 7에서 수행한다.
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — inline 모드 no-op 계약(TS-023) 추가, 077 자산은
//     manifest 모드 회귀로 승계 (opal-test-agent mode:red)
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
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

/** 커밋 픽스처를 임시 복사본으로 복제한다 (커밋 자산 비변형 — PLAN §3.7.2). */
function copyFixture(fixtureName, tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t080-${tag}-`));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureName), dir);
  return dir;
}

/** 임시 복사본의 `.opal/code-scan.json` 최상위 `headerSource`만 교체한다. */
function setHeaderSource(dir, value) {
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  cfg.headerSource = value;
  fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\n');
}

/** codemap-repo(커밋값 manifest) 전체 복사본. */
function makeWorkingCodemapRepo() {
  return copyFixture('codemap-repo', 'scaffold');
}

/** 매니페스트가 전혀 없는(=최초 scaffold 대상) 복사본 — .opal/code-map은 index.json만 남긴다. */
function makeBlankManifestRepo() {
  const dir = makeWorkingCodemapRepo();
  const mapDir = path.join(dir, '.opal', 'code-map');
  const index = JSON.parse(fs.readFileSync(path.join(mapDir, 'index.json'), 'utf8'));
  fs.rmSync(mapDir, { recursive: true, force: true });
  fs.mkdirSync(mapDir, { recursive: true });
  fs.writeFileSync(path.join(mapDir, 'index.json'), JSON.stringify(index, null, 2) + '\n');
  return dir;
}

/** `.opal/code-map/` 하위 전 파일의 {상대경로 → {content, mtimeMs}} 스냅샷. */
function snapshotCodeMap(dir) {
  const mapDir = path.join(dir, '.opal', 'code-map');
  const snap = {};
  const walk = (d, prefix) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(d, e.name);
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      if (e.isDirectory()) walk(full, rel);
      else snap[rel] = { content: fs.readFileSync(full, 'utf8'), mtimeMs: fs.statSync(full).mtimeMs };
    }
  };
  if (fs.existsSync(mapDir)) walk(mapDir, '');
  return snap;
}

// ═════════════════════════════════════════════════════════════════════════
// [T080/L1-F4] TS-023 (S-10): `inline` 모드 scaffold no-op + 사유 보고
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L1-F4] TS-023 (S-10): inline 모드 scaffold — .opal/code-map/ 하위 전 파일 내용·mtime 무변화 + skipped[0].reason + exit 0', () => {
  // mixed-scope 커밋 상태는 headerSource:"inline"이며 매니페스트(index.json + 2 스코프 _root.json)를
  // 이미 완비하고 있다 — "생성 수 0"으로는 no-op을 측정할 수 없는 정확히 그 조건이다.
  const dir = copyFixture('mixed-scope', 'scaffold-inline');
  const before = snapshotCodeMap(dir);
  assert.ok(Object.keys(before).length >= 3,
    `사전 조건: mixed-scope 커밋 매니페스트가 최소 3개 존재해야 no-op 측정이 성립한다, got ${JSON.stringify(Object.keys(before))}`);

  const { exitCode, json, stdout } = run(dir, ['scaffold', '--json']);

  assert.strictEqual(exitCode, 0,
    `[RED expect] "설정대로 동작했다"이므로 실패가 아니라 exit 0이어야 함, got ${exitCode} (stdout: ${stdout})`);
  assert.ok(json, `[RED expect] --json 출력이 유효 JSON이어야 함, raw="${stdout}"`);
  assert.strictEqual(json && json.ok, true, `[RED expect] ok:true, got ${JSON.stringify(json)}`);

  // 사유 보고 — 신규 필드를 만들지 않고 기존 skipped 배열에 사유를 싣는다(PLAN §3.3.2 (C)).
  assert.ok(Array.isArray(json && json.skipped) && json.skipped.length >= 1,
    `[RED expect] skipped[]에 no-op 사유가 실려야 함, got ${JSON.stringify(json && json.skipped)}`);
  assert.strictEqual(json.skipped[0] && json.skipped[0].reason, 'header_source_inline',
    `[RED expect] skipped[0].reason === 'header_source_inline', got ${JSON.stringify(json.skipped[0])}`);

  // no-op 판정 본체 — 내용·mtime 무변화
  const after = snapshotCodeMap(dir);
  assert.deepStrictEqual(Object.keys(after).sort(), Object.keys(before).sort(),
    `[RED expect] inline 모드 scaffold는 .opal/code-map/ 하위에 파일을 추가·삭제하면 안 됨`);
  for (const rel of Object.keys(before)) {
    assert.strictEqual(after[rel].content, before[rel].content,
      `[RED expect] ${rel} 내용이 변하면 안 됨(inline 모드는 매니페스트를 쓰지 않는다)`);
    assert.strictEqual(after[rel].mtimeMs, before[rel].mtimeMs,
      `[RED expect] ${rel} mtime이 변하면 안 됨 — 동일 내용 재작성도 no-op 위반이다`);
  }
});

test('[T080/L1-F4] TS-023 (S-10): inline 모드 scaffold — index.json 부재여도 index_missing으로 실패하지 않는다', () => {
  // inline 모드는 매니페스트 체계를 쓰지 않으므로, 인덱스 부재를 이유로 차단하면 계약이 어긋난다.
  // 모드 분기가 `!ctx.codeMap.present` 검사보다 **먼저** 와야 성립한다(PLAN §3.3.2 (C) 순서).
  const dir = copyFixture('legacy-repo', 'scaffold-noindex');   // 커밋값 inline · code-map 부재
  const { exitCode, json, stdout } = run(dir, ['scaffold', '--json']);

  assert.strictEqual(exitCode, 0,
    `[RED expect] inline 모드에서는 index.json 부재가 차단 사유가 아니다(모드 분기가 선행), got ${exitCode} (stdout: ${stdout})`);
  assert.strictEqual(json && json.error, undefined,
    `[RED expect] index_missing 에러가 나오면 안 됨, got ${JSON.stringify(json)}`);
  assert.strictEqual(json && json.skipped && json.skipped[0] && json.skipped[0].reason, 'header_source_inline',
    `[RED expect] skipped[0].reason === 'header_source_inline', got ${JSON.stringify(json && json.skipped)}`);
  assert.strictEqual(fs.existsSync(path.join(dir, '.opal', 'code-map')), false,
    `[RED expect] inline 모드 scaffold는 .opal/code-map/ 디렉토리를 만들지도 않아야 함`);
});

test('[T080/L1-F4] TS-023 (S-10) [대조군]: 같은 트리를 manifest로 뒤집으면 scaffold가 실제로 매니페스트를 갱신한다', () => {
  // no-op이 "그냥 아무것도 못 하는 상태"가 아님을 대조로 고정한다 — 전역값 1개만 바꾸면 동작이 살아난다.
  const dir = copyFixture('mixed-scope', 'scaffold-manifest');
  setHeaderSource(dir, 'manifest');

  const { exitCode, json, stdout } = run(dir, ['scaffold', '--json']);

  assert.strictEqual(exitCode, 0, `대조군: exit 0 기대, got ${exitCode} (stdout: ${stdout})`);
  assert.ok(json, `대조군: 유효 JSON 기대, raw="${stdout}"`);
  const skippedReasons = ((json && json.skipped) || []).map(s => s && s.reason);
  assert.ok(!skippedReasons.includes('header_source_inline'),
    `[RED expect] 대조군: manifest 모드에서는 header_source_inline no-op이 발동하면 안 됨, got ${JSON.stringify(json.skipped)}`);
  assert.ok(typeof json.created === 'number' && typeof json.updated === 'number' && typeof json.unchanged === 'number',
    `대조군: created/updated/unchanged 카운트가 보고되어야 함, got ${JSON.stringify(json)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T077-승계] manifest 모드 회귀 — 077이 고정한 생성·멱등·보존·prune·불변성 계약은 그대로 유효하다.
// (codemap-repo 커밋값이 headerSource:"manifest"이므로 아래 케이스는 전량 manifest 모드에서 돈다.)
// ═════════════════════════════════════════════════════════════════════════

test('[T077-승계] (S-10): manifest 모드 scaffold — 코드 보유 디렉토리 수 = 생성 매니페스트 수', () => {
  const dir = makeBlankManifestRepo();

  const { exitCode, stdout } = run(dir, ['scaffold', '--json']);
  assert.strictEqual(exitCode, 0, `scaffold는 exit 0이어야 함, got ${exitCode} (${stdout})`);

  const manifestFiles = [];
  const mapDir = path.join(dir, '.opal', 'code-map');
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full);
      else if (e.name.endsWith('.json') && e.name !== 'index.json') manifestFiles.push(full);
    }
  };
  walk(mapDir);
  assert.ok(manifestFiles.length >= 6,
    `코드 보유 디렉토리 수만큼 매니페스트가 생성되어야 함 (>=6), got ${manifestFiles.length}: ${JSON.stringify(manifestFiles)}`);
});

test('[T077-승계] (S-10): manifest 모드 scaffold 2회 연속 실행 — 산출물 바이트 동일 (멱등)', () => {
  const dir = makeBlankManifestRepo();

  run(dir, ['scaffold', '--json']);
  const first = snapshotCodeMap(dir);
  const keys = Object.keys(first).filter(k => k !== 'index.json');
  assert.ok(keys.length > 0,
    'scaffold가 최소 1개 이상의 패키지 매니페스트(index.json 제외)를 생성해야 함');

  run(dir, ['scaffold', '--json']);
  const second = snapshotCodeMap(dir);

  for (const rel of keys) {
    assert.ok(second[rel], `2회차 후에도 ${rel}이 존재해야 함`);
    assert.strictEqual(second[rel].content, first[rel].content,
      `2회 연속 실행 결과가 바이트 단위로 동일해야 함(멱등) — ${rel}`);
  }
});

test('[T077-승계] (S-10): description 보존 + 신규 파일만 draft:true 빈 엔트리 추가', () => {
  const dir = makeBlankManifestRepo();

  run(dir, ['scaffold', '--json']);

  const manifestPath = path.join(dir, '.opal', 'code-map', 'svc', 'order-api', 'order', 'service.json');
  assert.ok(fs.existsSync(manifestPath), `${manifestPath}가 scaffold에 의해 생성되어야 함`);

  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.files['OrderService.java'].description = '워커가 채운 설명';
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');

  fs.writeFileSync(
    path.join(dir, 'svc', 'order-api', 'src', 'main', 'java', 'com', 'acme', 'order', 'service', 'NewFile.java'),
    'package com.acme.order.service;\npublic class NewFile {}\n'
  );
  run(dir, ['scaffold', '--json']);

  const after = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  assert.strictEqual(after.files['OrderService.java'].description, '워커가 채운 설명',
    'description 값이 재실행 후에도 보존되어야 함');
  assert.ok(after.files['NewFile.java'], '신규 파일 NewFile.java 엔트리가 추가되어야 함');
  assert.strictEqual(after.files['NewFile.java'].draft, true, '신규 파일 엔트리는 draft:true여야 함');
  assert.strictEqual(after.files['OrderService.java'].draft, undefined,
    '설명이 채워진 기존 엔트리는 draft 키가 제거되어야 함');
});

test('[T077-승계] (S-10): 소스 파일 삭제 → 재실행 시 엔트리 제거 + pruned 보고', () => {
  const dir = makeBlankManifestRepo();

  run(dir, ['scaffold', '--json']);
  const filePath = path.join(dir, 'svc', 'order-api', 'src', 'main', 'java', 'com', 'acme', 'order', 'service', 'PriceCalc.java');
  fs.rmSync(filePath);

  const { json } = run(dir, ['scaffold', '--json']);
  const manifestPath = path.join(dir, '.opal', 'code-map', 'svc', 'order-api', 'order', 'service.json');

  assert.ok(fs.existsSync(manifestPath), `${manifestPath} 존재해야 함`);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  assert.strictEqual(manifest.files['PriceCalc.java'], undefined,
    '삭제된 파일의 매니페스트 엔트리가 제거되어야 함');
  assert.ok(json && Array.isArray(json.pruned) && json.pruned.some(p => p.includes('PriceCalc.java')),
    `pruned 배열에 PriceCalc.java가 보고되어야 함, got ${JSON.stringify(json && json.pruned)}`);
});

test('[T077-승계] (S-10): scaffold 실행 후 소스 파일 mtime·내용 무변화', () => {
  const dir = makeBlankManifestRepo();

  const filePath = path.join(dir, 'svc', 'order-api', 'src', 'main', 'java', 'com', 'acme', 'order', 'service', 'OrderService.java');
  const before = { content: fs.readFileSync(filePath, 'utf8'), mtime: fs.statSync(filePath).mtimeMs };

  run(dir, ['scaffold', '--json']);

  const after = { content: fs.readFileSync(filePath, 'utf8'), mtime: fs.statSync(filePath).mtimeMs };
  assert.strictEqual(after.content, before.content, '소스 파일 내용이 변화하면 안 됨(scaffold는 .opal/code-map/ 외부에 쓰지 않는다)');
  assert.strictEqual(after.mtime, before.mtime, '소스 파일 mtime이 변화하면 안 됨');
});

test('[T077-승계] (S-11): mirror_collision — scaffold가 exit 1로 거부하고 어떤 매니페스트도 쓰지 않음', () => {
  const dir = copyFixture(path.join('violations', 'conflict-mirror-collision'), 'collision');

  const { exitCode, json } = run(dir, ['scaffold', '--json']);

  assert.strictEqual(exitCode, 1, `mirror_collision → exit 1 기대, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'mirror_collision',
    `error: mirror_collision 기대, got ${JSON.stringify(json)}`);

  const mapDir = path.join(dir, '.opal', 'code-map');
  const written = fs.existsSync(mapDir)
    ? fs.readdirSync(mapDir, { recursive: true }).filter(f => typeof f === 'string' && f.endsWith('.json') && f !== 'index.json')
    : [];
  assert.strictEqual(written.length, 0,
    `충돌 시 어떤 매니페스트 파일도 쓰이면 안 됨(2-pass 사전 검사), got: ${JSON.stringify(written)}`);
});
