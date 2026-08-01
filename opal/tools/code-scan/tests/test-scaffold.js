/**
 * @header {
 *   "module": "test-scaffold",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `scaffold` 서브명령(골격 매니페스트 생성, 멱등 보존 merge, pruned/added, mirror_collision 거부) CLI 블랙박스 테스트 (F-004, 태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-10", "S-11"]
 * }
 */
//
// TC ↔ TS-ID 매핑 표 (PLAN.md §3.4.5, TEST-SCENARIO.md S-10/S-11):
//
// | TC                                          | TS-ID  |
// |-----------------------------------------------|--------|
// | scaffold-count-matches-manifest-count          | TS-015 |
// | scaffold-idempotent-byte-identical (2회 연속)   | TS-016 |
// | scaffold-preserve-description-add-draft-only    | TS-017 |
// | scaffold-prune-deleted-file                     | TS-018 |
// | scaffold-source-untouched (mtime/내용 무변화)    | TS-019 |
// | scaffold-mirror-collision-rejects-all-writes    | TS-010/TS-011(F-4 충돌) |
//
// RED-first: 현행 code-scan.js에는 scaffold 서브명령이 없다. 아래 전 테스트는 "Unknown command" exit 1로
// 실패해야 정상이다. 각 테스트는 codemap-repo 소스 트리(또는 전용 충돌 픽스처)를 mkdtempSync 임시
// 디렉토리로 복사해 scaffold가 매니페스트를 새로 쓸 대상을 마련한다(committed 픽스처 비변형).
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

/** codemap-repo 전체(소스 + 이미 채워진 매니페스트 포함)를 통째로 복사한 임시 작업 디렉토리를 만든다. */
function makeWorkingCodemapRepo() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-scaffold-'));
  copyDirRecursive(path.join(FIX, 'codemap-repo'), dir);
  return dir;
}

/** 매니페스트가 전혀 없는(=최초 scaffold 대상) 임시 작업 디렉토리 — .opal/code-map은 index.json만 남긴다. */
function makeBlankManifestRepo() {
  const dir = makeWorkingCodemapRepo();
  const mapDir = path.join(dir, '.opal', 'code-map');
  const index = JSON.parse(fs.readFileSync(path.join(mapDir, 'index.json'), 'utf8'));
  fs.rmSync(mapDir, { recursive: true, force: true });
  fs.mkdirSync(mapDir, { recursive: true });
  fs.writeFileSync(path.join(mapDir, 'index.json'), JSON.stringify(index, null, 2) + '\n');
  return dir;
}

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

// ─────────────────────────────────────────────────────────────────────────
// TS-015: 코드 보유 소스 디렉토리 수 = 생성된 매니페스트 수
// ─────────────────────────────────────────────────────────────────────────

test('TS-015 (S-10): scaffold — 대상 스코프의 코드 보유 디렉토리 수 = 생성 매니페스트 수', () => {
  const dir = makeBlankManifestRepo();
  cleanupDirs.push(dir);

  const { exitCode, json, stdout } = run(dir, ['scaffold', '--json']);

  // [RED 기대] scaffold 서브명령 자체가 없다 — "Unknown command" exit 1.
  assert.strictEqual(exitCode, 0, `[RED expect] scaffold는 exit 0이어야 함, got ${exitCode} (${stdout})`);

  // svc/order-api/order/service (2 files) + svc/ship-api/ship/repository (2 files) +
  // svc/order-api/misc(1) + web/admin/pages(2) + web/admin/service(1) + legacy/lib(1) = 6개 디렉토리
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
    `[RED expect] 코드 보유 디렉토리 수만큼 매니페스트가 생성되어야 함 (>=6), got ${manifestFiles.length}: ${JSON.stringify(manifestFiles)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-016: 2회 연속 실행 산출물 바이트 동일 (멱등)
// ─────────────────────────────────────────────────────────────────────────

test('TS-016 (S-10): scaffold 2회 연속 실행 — 산출물 바이트 동일 (멱등)', () => {
  const dir = makeBlankManifestRepo();
  cleanupDirs.push(dir);

  run(dir, ['scaffold', '--json']);
  const mapDir = path.join(dir, '.opal', 'code-map');
  const snapshot1 = fs.existsSync(mapDir)
    ? fs.readdirSync(mapDir, { recursive: true }).filter(f => typeof f === 'string' && f.endsWith('.json') && f !== 'index.json').sort()
    : [];
  const contents1 = {};
  for (const rel of snapshot1) {
    const full = path.join(mapDir, rel);
    if (fs.existsSync(full) && fs.statSync(full).isFile()) contents1[rel] = fs.readFileSync(full, 'utf8');
  }

  run(dir, ['scaffold', '--json']);
  const contents2 = {};
  for (const rel of snapshot1) {
    const full = path.join(mapDir, rel);
    if (fs.existsSync(full) && fs.statSync(full).isFile()) contents2[rel] = fs.readFileSync(full, 'utf8');
  }

  // [RED 기대] scaffold 미구현 — index.json을 제외하면 실제 생성된 매니페스트가 0개이므로 아래에서 실패해야 한다.
  assert.ok(Object.keys(contents1).length > 0,
    '[RED expect] scaffold가 최소 1개 이상의 패키지 매니페스트(index.json 제외)를 생성해야 함(현행은 0개)');
  assert.deepStrictEqual(contents2, contents1, '2회 연속 실행 결과가 바이트 단위로 동일해야 함(멱등)');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-017: description 채운 뒤 재실행 → 값 유지 + 신규 파일만 draft:true 추가
// ─────────────────────────────────────────────────────────────────────────

test('TS-017 (S-10): description 보존 + 신규 파일만 draft:true 빈 엔트리 추가', () => {
  const dir = makeBlankManifestRepo();
  cleanupDirs.push(dir);

  run(dir, ['scaffold', '--json']);

  const manifestPath = path.join(dir, '.opal', 'code-map', 'svc', 'order-api', 'order', 'service.json');
  // [RED 기대] scaffold 미구현이므로 이 매니페스트 자체가 존재하지 않아 아래에서 즉시 실패한다.
  assert.ok(fs.existsSync(manifestPath),
    `[RED expect] ${manifestPath}가 scaffold에 의해 생성되어야 함`);

  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.files['OrderService.java'].description = '워커가 채운 설명';
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');

  // 새 파일 추가 후 재실행
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

// ─────────────────────────────────────────────────────────────────────────
// TS-018: 소스 파일 삭제 후 재실행 → 엔트리 제거 + pruned 보고
// ─────────────────────────────────────────────────────────────────────────

test('TS-018 (S-10): 소스 파일 삭제 → 재실행 시 엔트리 제거 + pruned 보고', () => {
  const dir = makeBlankManifestRepo();
  cleanupDirs.push(dir);

  run(dir, ['scaffold', '--json']);
  const filePath = path.join(dir, 'svc', 'order-api', 'src', 'main', 'java', 'com', 'acme', 'order', 'service', 'PriceCalc.java');
  fs.rmSync(filePath);

  const { json } = run(dir, ['scaffold', '--json']);
  const manifestPath = path.join(dir, '.opal', 'code-map', 'svc', 'order-api', 'order', 'service.json');

  // [RED 기대] scaffold 미구현 — manifestPath 자체가 없어 실패.
  assert.ok(fs.existsSync(manifestPath), `[RED expect] ${manifestPath} 존재해야 함`);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  assert.strictEqual(manifest.files['PriceCalc.java'], undefined,
    '[RED expect] 삭제된 파일의 매니페스트 엔트리가 제거되어야 함');
  assert.ok(json && Array.isArray(json.pruned) && json.pruned.some(p => p.includes('PriceCalc.java')),
    `[RED expect] pruned 배열에 PriceCalc.java가 보고되어야 함, got ${JSON.stringify(json && json.pruned)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-019: scaffold 실행 후 소스 파일 mtime·내용 변화 0건 (PM-5 --inline 미채택)
// ─────────────────────────────────────────────────────────────────────────

test('TS-019 (S-10): scaffold 실행 후 소스 파일 mtime·내용 무변화', () => {
  const dir = makeBlankManifestRepo();
  cleanupDirs.push(dir);

  const filePath = path.join(dir, 'svc', 'order-api', 'src', 'main', 'java', 'com', 'acme', 'order', 'service', 'OrderService.java');
  const before = { content: fs.readFileSync(filePath, 'utf8'), mtime: fs.statSync(filePath).mtimeMs };

  run(dir, ['scaffold', '--json']);

  const after = { content: fs.readFileSync(filePath, 'utf8'), mtime: fs.statSync(filePath).mtimeMs };
  assert.strictEqual(after.content, before.content, '소스 파일 내용이 변화하면 안 됨(scaffold는 .opal/code-map/ 외부에 쓰지 않는다)');
  assert.strictEqual(after.mtime, before.mtime, '소스 파일 mtime이 변화하면 안 됨');
});

// ─────────────────────────────────────────────────────────────────────────
// mirror_collision: 충돌 시 exit 1 + 아무 파일도 쓰지 않음 (2-pass, H-11)
// ─────────────────────────────────────────────────────────────────────────

test('S-11: mirror_collision — scaffold가 exit 1로 거부하고 어떤 매니페스트도 쓰지 않음', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-collision-'));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, 'violations', 'conflict-mirror-collision'), dir);

  const { exitCode, json } = run(dir, ['scaffold', '--json']);

  // [RED 기대] scaffold 서브명령이 없으므로 "Unknown command" exit 1이지만 error 코드가 mirror_collision이 아니다.
  assert.strictEqual(exitCode, 1, `mirror_collision → exit 1 기대, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'mirror_collision',
    `[RED expect] error: mirror_collision 기대, got ${JSON.stringify(json)}`);

  const mapDir = path.join(dir, '.opal', 'code-map');
  const written = fs.existsSync(mapDir)
    ? fs.readdirSync(mapDir, { recursive: true }).filter(f => typeof f === 'string' && f.endsWith('.json') && f !== 'index.json')
    : [];
  assert.strictEqual(written.length, 0,
    `[RED expect] 충돌 시 어떤 매니페스트 파일도 쓰이면 안 됨(2-pass 사전 검사), got: ${JSON.stringify(written)}`);
});
