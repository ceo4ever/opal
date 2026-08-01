/**
 * @header {
 *   "module": "test-discover",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — `discover` 서브명령(초안 index.json 생성, 앵커 2종 탐지, --dry-run, 멱등 가드) CLI 블랙박스 테스트 (F-003, 태스크 077)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "077",
 *   "scenarios": ["S-9"]
 * }
 */
//
// TC ↔ TS-ID 매핑 표 (PLAN.md §3.3.5, TEST-SCENARIO.md S-9):
//
// | TC                                      | TS-ID  |
// |------------------------------------------|--------|
// | discover-basic (scopes/layerRules/exclude)| TS-011 |
// | discover-draft-marks (초안 표시 4필드)      | TS-012 |
// | discover-anchor-2-kinds                   | TS-013 |
// | discover-index-exists-rejects (+dry-run)  | TS-014 |
//
// RED-first: 현재 code-scan.js에는 discover 서브명령이 전혀 없다(commands 테이블 8개 고정). 아래 전 테스트는
// "Unknown command" exit 1로 실패해야 정상이다. 이 파일은 codemap-repo 정적 픽스처의 소스 트리(svc/web/legacy,
// .opal/code-map 제외)를 mkdtempSync 임시 디렉토리로 복사해 discover가 index.json을 새로 쓸 대상을 마련한다
// (committed 픽스처를 직접 mutate하지 않음).
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
  const stderr = result.stderr || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr, json };
}

/** codemap-repo의 소스 트리(svc/web/legacy)만 복사한 새 임시 디렉토리를 만든다 (.opal/code-map은 제외 — 부재 상태). */
function copyDirRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDirRecursive(s, d);
    else fs.copyFileSync(s, d);
  }
}

function makeBlankCodemapRepo() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-t077-discover-'));
  const srcRoot = path.join(FIX, 'codemap-repo');
  // 소스 트리만 복사 (svc/web/legacy) — .opal/code-map(기존 index/매니페스트)은 제외해 "index 미존재" 상태를 만든다.
  for (const name of ['svc', 'web', 'legacy']) {
    copyDirRecursive(path.join(srcRoot, name), path.join(dir, name));
  }
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  fs.copyFileSync(path.join(srcRoot, '.opal', 'code-scan.json'), path.join(dir, '.opal', 'code-scan.json'));
  return dir;
}

const cleanupDirs = [];
function cleanup() {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
}
process.on('exit', cleanup);

// ─────────────────────────────────────────────────────────────────────────
// TS-011: scopes ≥2 · layerRules ≥1 · exclude에 컴파일 산출물 디렉토리 포함된 초안 생성
// ─────────────────────────────────────────────────────────────────────────

test('TS-011 (S-9): discover --dry-run — scopes ≥2, layerRules ≥1, exclude에 target 포함', () => {
  const dir = makeBlankCodemapRepo();
  cleanupDirs.push(dir);

  const { exitCode, json, stdout } = run(dir, ['discover', '--dry-run', '--json']);

  // [RED 기대] 현행에는 discover 서브명령이 없다 — "Unknown command" exit 1.
  assert.strictEqual(exitCode, 0, `[RED expect] discover --dry-run은 exit 0이어야 함, got ${exitCode} (stderr/stdout: ${stdout})`);
  assert.ok(json !== null, '[RED expect] --json 출력이 유효 JSON이어야 함');
  const draft = json && (json.index || json);
  assert.ok(draft && draft.scopes && Object.keys(draft.scopes).length >= 2,
    `[RED expect] scopes ≥2 기대, got ${JSON.stringify(draft && draft.scopes)}`);
  assert.ok(Array.isArray(draft && draft.layerRules) && draft.layerRules.length >= 1,
    '[RED expect] layerRules ≥1 기대');
  assert.ok(Array.isArray(draft && draft.exclude) && draft.exclude.includes('target'),
    `[RED expect] exclude에 컴파일 산출물 디렉토리(target)가 포함되어야 함, got ${JSON.stringify(draft && draft.exclude)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-012: 초안 파일에 origin/status:"draft"/generatedAt/note 표시 존재 (산출물 검사)
// ─────────────────────────────────────────────────────────────────────────

test('TS-012 (S-9): discover(실제 쓰기) — 초안 표시 4필드가 index.json에 존재', () => {
  const dir = makeBlankCodemapRepo();
  cleanupDirs.push(dir);

  const { exitCode } = run(dir, ['discover', '--json']);
  const outPath = path.join(dir, '.opal', 'code-map', 'index.json');

  // [RED 기대] discover 서브명령이 없으므로 index.json 자체가 생성되지 않는다.
  assert.strictEqual(exitCode, 0, `[RED expect] discover는 exit 0이어야 함, got ${exitCode}`);
  assert.ok(fs.existsSync(outPath), `[RED expect] ${outPath} 파일이 생성되어야 함`);

  const draft = JSON.parse(fs.readFileSync(outPath, 'utf8'));
  assert.strictEqual(draft.origin, 'discover', '[RED expect] origin: "discover"');
  assert.strictEqual(draft.status, 'draft', '[RED expect] status: "draft"');
  assert.strictEqual(typeof draft.generatedAt, 'string', '[RED expect] generatedAt 존재');
  assert.strictEqual(typeof draft.note, 'string', '[RED expect] note 존재');
  assert.ok(draft.note.length > 0, '[RED expect] note가 OWNER REVIEW REQUIRED 안내를 포함해야 함');
});

// ─────────────────────────────────────────────────────────────────────────
// TS-013: 앵커 2종(빌드 매니페스트 기반 / 단순 디렉토리) 각각 검출
// ─────────────────────────────────────────────────────────────────────────

test('TS-013 (S-9): 앵커 2종 — svc(pom.xml 기반) + web(1-depth 디렉토리) 각각 검출', () => {
  const dir = makeBlankCodemapRepo();
  cleanupDirs.push(dir);

  const { json } = run(dir, ['discover', '--dry-run', '--json']);
  const draft = json && (json.index || json);

  // [RED 기대] discover 미구현 — json이 애초에 null.
  assert.ok(draft && draft.scopes, '[RED expect] scopes 존재');
  assert.ok(draft && draft.scopes.svc && Array.isArray(draft.scopes.svc.anchors) && draft.scopes.svc.anchors.includes('order-api'),
    `[RED expect] svc 스코프에서 pom.xml 기반 앵커 order-api가 검출되어야 함, got ${JSON.stringify(draft && draft.scopes && draft.scopes.svc)}`);
  assert.ok(draft && draft.scopes.web && Array.isArray(draft.scopes.web.anchors) && draft.scopes.web.anchors.includes('admin'),
    `[RED expect] web 스코프에서 단순 디렉토리 앵커 admin이 검출되어야 함, got ${JSON.stringify(draft && draft.scopes && draft.scopes.web)}`);
});

// ─────────────────────────────────────────────────────────────────────────
// TS-014: index 존재 시 index_exists exit 1, --dry-run은 파일 미생성
// ─────────────────────────────────────────────────────────────────────────

test('TS-014 (S-9): 기존 index 존재 → index_exists exit 1', () => {
  const dir = makeBlankCodemapRepo();
  cleanupDirs.push(dir);
  fs.mkdirSync(path.join(dir, '.opal', 'code-map'), { recursive: true });
  fs.writeFileSync(path.join(dir, '.opal', 'code-map', 'index.json'), JSON.stringify({ version: 1, scopes: {} }));

  const { exitCode, json } = run(dir, ['discover', '--json']);

  // [RED 기대] 현행은 discover 자체가 없으므로 "Unknown command" exit 1이지만 error 코드가 다르다.
  assert.strictEqual(exitCode, 1, `index_exists → exit 1 기대, got ${exitCode}`);
  assert.strictEqual(json && json.error, 'index_exists',
    `[RED expect] error: index_exists 기대, got ${JSON.stringify(json)}`);
});

test('TS-014 (S-9): --dry-run은 파일을 쓰지 않는다', () => {
  const dir = makeBlankCodemapRepo();
  cleanupDirs.push(dir);

  run(dir, ['discover', '--dry-run', '--json']);
  const outPath = path.join(dir, '.opal', 'code-map', 'index.json');

  // [RED 기대] 현행은 discover가 없으므로 애초에 아무것도 쓰지 않는다 — 이 assert 자체는 우연히 통과할 수
  // 있으나(파일 없음=참), TS-011/012에서 실제 쓰기 동작이 검증되므로 이 케이스는 대조군으로 유지한다.
  assert.strictEqual(fs.existsSync(outPath), false, '--dry-run 실행 후 index.json이 생성되면 안 됨');
});
