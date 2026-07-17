//
// @module      test-migrate
// @layer       tools/test
// @domain      skill-management
// @task        064
// @description resolveCommunitySkillPath() 이중 탐지(vendor 우선→flat 폴백→null, F-001) +
//              migrate 서브커맨드(flat→vendor 이동·미등재/충돌 보존·dry-run·멱등, F-001) 단위 테스트
//              — RED-first 트랙 (태스크 064)
//              CLI 블랙박스 방식: node skill-registry.js <match|list|migrate> 를 child_process 로
//              실행, exit code + stdout JSON + 실 파일시스템 재확인으로 동작 검증.
//              mock/monkeypatch 없음, 실제 fs 위 합성 fixture(HOME 오버라이드) 사용.
// @depends     node:test, node:assert, node:fs, node:path, node:os, node:child_process
//              (신규 패키지 0, Node 내장 모듈만 사용)
// @scenarios   TEST-SCENARIO.md §3 S-1(F-1 경로탐지), S-2(F-1 이동·멱등), S-3(F-1 보존/142 D-4), S-4(F-1 회귀)
//
// TC 매핑 (TEST-SCENARIO.md §3, §4 AC 매핑 표):
//   [T101/L1-F1] → S-1: resolveCommunitySkillPath 3분기 — vendor 우선/flat 폴백/null
//                       (공개 인터페이스 부재이므로 match 출력의 installed/path 필드로 간접 검증)
//   [T102/L2-F1] → S-2: migrate — 등재 flat→vendor 이동, 이미 중첩 skip, dry-run 무부작용, 재실행 멱등
//   [T103/L2-F1] → S-3: migrate — 미등재·basename 충돌 flat 무이동 보존(142 D-4), errors 0
//   [T104/L2-F1] → S-4: migrate 후 `list --group=community` 전수 installed:true (회귀)
//
// 주의: 현행 CLI 라우터(`skill-registry.js:461-495`)에는 `migrate` 서브커맨드가 없다.
//       `node skill-registry.js migrate` 호출 시 default 분기로 빠져
//       `Unknown command: migrate` 를 stderr에 출력하고 exit 1 을 반환한다.
//       이 파일의 migrate 관련 테스트는 그 자체로 RED 증거(exit 1 / JSON 없음)이며,
//       구현 완료(GREEN) 후에는 실제 이동 결과 JSON(moved/preserved/skipped/errors)을 검증하도록
//       assert가 이미 작성되어 있다(§3.1.2(b) 시그니처 계약 기준).
//
// 변경이력:
//   v1.0 2026-07-17 KST: RED-first 단위 테스트 최초 작성 (태스크 064, opal-test-agent mode:red)
//

'use strict';

const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');

// ─── 유틸 ────────────────────────────────────────────────────────────────────

const SKILL_REGISTRY_JS = path.resolve(__dirname, '..', 'skill-registry.js');

/**
 * 배포 환경(모사) fixture — community-skills 디렉토리 레이아웃을 임의 구성한다.
 *
 * @param {object} opts
 * @param {object} opts.catalogGroups          - community-skills-registry.json groups
 * @param {string[]} [opts.flatDirs]            - `{basename}/SKILL.md` 형태로 만들 flat 디렉토리명
 * @param {{vendor:string, skill:string}[]} [opts.nestedDirs] - 이미 중첩된 `{vendor}/{skill}/SKILL.md`
 * @returns {{ dir: string, fakeHome: string, communityDir: string, refDir: string, cleanup: () => void }}
 */
function makeMigrateFixture({ catalogGroups, flatDirs = [], nestedDirs = [] }) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-test-migrate-'));
  const fakeHome = path.join(dir, 'fakehome');
  const refDir = path.join(fakeHome, '.opal', 'references');
  const communityDir = path.join(fakeHome, '.opal', 'community-skills');
  fs.mkdirSync(refDir, { recursive: true });
  fs.mkdirSync(communityDir, { recursive: true });

  // main registry stub — getReferencesDir()가 배포 경로(fakeHome)를 선택하도록 존재만 시킴.
  // (stub이 없으면 __dirname 기준 폴백이 실제 프로젝트 opal/core/references/를 가리켜 fixture가 무의미해진다.)
  const mainRegistry = {
    '$schema': 'opal-skills-registry-v1',
    version: '0.0.1-fixture',
    updated_at: '2026-07-17',
    groups: {}
  };
  fs.writeFileSync(path.join(refDir, 'opal-skills-registry.json'), JSON.stringify(mainRegistry, null, 2));

  const communityRegistry = {
    '$schema': 'opal-community-skills-registry-v2.1',
    version: '2.1.0-fixture',
    updated_at: '2026-07-17',
    schema_notes: 'fixture — test-migrate.js',
    groups: catalogGroups
  };
  fs.writeFileSync(path.join(refDir, 'community-skills-registry.json'), JSON.stringify(communityRegistry, null, 2));

  for (const base of flatDirs) {
    const skillDir = path.join(communityDir, base);
    fs.mkdirSync(skillDir, { recursive: true });
    fs.writeFileSync(path.join(skillDir, 'SKILL.md'), `# ${base} (flat fixture)\n`);
  }
  for (const { vendor, skill } of nestedDirs) {
    const skillDir = path.join(communityDir, vendor, skill);
    fs.mkdirSync(skillDir, { recursive: true });
    fs.writeFileSync(path.join(skillDir, 'SKILL.md'), `# ${vendor}/${skill} (nested fixture)\n`);
  }

  function cleanup() {
    fs.rmSync(dir, { recursive: true, force: true });
  }

  return { dir, fakeHome, communityDir, refDir, cleanup };
}

/**
 * skill-registry.js CLI 를 실행한다 (HOME 오버라이드로 fixture 격리).
 * @param {string[]} args
 * @param {string} fakeHome
 * @returns {{ exitCode: number, stdout: string, stderr: string, result: object|null }}
 */
function runCli(args, fakeHome) {
  const env = { ...process.env, HOME: fakeHome };
  const proc = spawnSync('node', [SKILL_REGISTRY_JS, ...args], {
    cwd: os.tmpdir(),
    env,
    encoding: 'utf8',
    timeout: 10000
  });

  const stdout = proc.stdout || '';
  const stderr = proc.stderr || '';
  const exitCode = proc.status;

  let parsed = null;
  try {
    parsed = JSON.parse(stdout.trim());
  } catch (_) {
    // unknown command → stderr만 출력, stdout은 JSON이 아닐 수 있음
  }

  return { exitCode, stdout, stderr, result: parsed };
}

const cleanupFns = [];
after(() => {
  for (const fn of cleanupFns) {
    try { fn(); } catch (_) { /* ignore */ }
  }
});

// ─── 공용 catalog: pdf(basename 유일 등재) / obra-brainstorming(이미 중첩) ──

const BASE_CATALOG = {
  anthropics: [
    {
      name: 'anthropics/pdf', alias: null,
      description: 'PDF 생성/편집/추출', triggers: ['(?i)(pdf|\\.pdf)'],
      source_repo: 'anthropics/skills@pdf', commit_sha: null, license: 'Apache-2.0'
    }
  ],
  obra: [
    {
      name: 'obra/brainstorming', alias: null,
      description: '아이디어→설계/스펙 브레인스토밍', triggers: ['(?i)(brainstorm|브레인스토밍)'],
      source_repo: 'obra/superpowers@brainstorming', commit_sha: 'd884ae04edebef577e82ff7c4e143debd0bbec99',
      license: 'MIT'
    }
  ]
};

// 충돌 fixture용: basename "pdf"가 anthropics/pdf ↔ vendorx/pdf 2벤더에 등재
const COLLISION_CATALOG = {
  ...BASE_CATALOG,
  vendorx: [
    {
      name: 'vendorx/pdf', alias: null,
      description: '충돌 검증용 합성 스킬', triggers: ['(?i)(vendorx\\s*pdf)'],
      source_repo: 'vendorx/repo@pdf', commit_sha: null, license: 'Unknown'
    }
  ]
};

// ─── [T101/L1-F1] 경로 탐지 3분기: vendor 우선 → flat 폴백 → null (S-1) ─────

test('[T101/L1-F1] 경로 탐지: flat만 존재 → installed:true + flat 경로 반환 (vendor→flat 폴백)', () => {
  // "anthropics/pdf"가 registry에는 정식명(vendor 포함)으로 등재되어 있으나,
  // 실제 파일은 flat 레이아웃(`community-skills/pdf/SKILL.md`, vendor 중첩 없음)에 존재하는 케이스.
  const { fakeHome, communityDir, cleanup } = makeMigrateFixture({
    catalogGroups: BASE_CATALOG,
    flatDirs: ['pdf']
  });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//anthropics/pdf'], fakeHome);

  // [RED expect] 현행 getCommunitySkillPath(skillName)은 skillName("anthropics/pdf")을 그대로
  // 디렉토리 세그먼트로 사용해 `community-skills/anthropics/pdf/SKILL.md`만 확인한다.
  // flat 레이아웃(`community-skills/pdf/SKILL.md`)은 폴백 탐지가 없어 installed:false로 오판된다.
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.installed, true,
    `[RED expect] flat 레이아웃이어도 installed:true 여야 함(vendor→flat 폴백) but got ${result.installed}`);
  const expectedFlatPath = path.join(communityDir, 'pdf', 'SKILL.md');
  assert.strictEqual(result.path, expectedFlatPath,
    `[RED expect] path should resolve to flat path "${expectedFlatPath}" but got "${result.path}"`);
});

test('[T101/L1-F1] 경로 탐지: vendor 중첩 존재 → installed:true + nested 경로 반환 (baseline)', () => {
  // obra/brainstorming은 이미 vendor 중첩 레이아웃 — 현행 getCommunitySkillPath도 정확히 이 경로를
  // 계산하므로(스킬명 자체에 vendor가 포함) 이 케이스는 baseline(회귀 가드)이다.
  const { fakeHome, communityDir, cleanup } = makeMigrateFixture({
    catalogGroups: BASE_CATALOG,
    nestedDirs: [{ vendor: 'obra', skill: 'brainstorming' }]
  });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//obra/brainstorming'], fakeHome);

  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.installed, true, `installed should be true but got ${result.installed}`);
  const expectedNestedPath = path.join(communityDir, 'obra', 'brainstorming', 'SKILL.md');
  assert.strictEqual(result.path, expectedNestedPath,
    `path should resolve to nested path "${expectedNestedPath}" but got "${result.path}"`);
});

test('[T101/L1-F1] 경로 탐지: 둘 다 없음 → installed:false + path:null (baseline)', () => {
  const { fakeHome, cleanup } = makeMigrateFixture({ catalogGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//anthropics/pdf'], fakeHome);

  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.installed, false, `installed should be false but got ${result.installed}`);
  assert.strictEqual(result.path, null, `path should be null but got ${result.path}`);
});

// ─── [T102/L2-F1] migrate: 등재 flat 이동 + 중첩 skip + dry-run + 멱등 (S-2) ─

test('[T102/L2-F1] migrate --dry-run: 무부작용(계획만 반환, 실 이동 없음)', () => {
  const { fakeHome, communityDir, cleanup } = makeMigrateFixture({
    catalogGroups: BASE_CATALOG,
    flatDirs: ['pdf'],
    nestedDirs: [{ vendor: 'obra', skill: 'brainstorming' }]
  });
  cleanupFns.push(cleanup);

  const flatPdfPath = path.join(communityDir, 'pdf');
  const before = fs.existsSync(flatPdfPath);

  const { exitCode, result, stderr } = runCli(['migrate', '--dry-run'], fakeHome);

  // [RED expect] 현행 CLI 라우터에는 'migrate' 케이스가 없어 default 분기(Unknown command)로
  // 빠지며 exit 1을 반환한다 → JSON 결과 부재.
  assert.strictEqual(exitCode, 0,
    `[RED expect] migrate --dry-run exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null,
    `[RED expect] migrate --dry-run stdout should be valid JSON but was not. stderr: ${stderr}`);

  // dry-run은 실제 이동을 하지 않아야 한다 — flat 디렉토리가 그대로 남아 있어야 함
  assert.strictEqual(fs.existsSync(flatPdfPath), before,
    'dry-run은 실 파일시스템을 변경하면 안 됨(무부작용)');
  if (result) {
    assert.ok(Array.isArray(result.moved), '[RED expect] result.moved should be an array (계획)');
  }
});

test('[T102/L2-F1] migrate 본실행: 등재 flat→vendor 이동, 이미 중첩 skip', () => {
  const { fakeHome, communityDir, cleanup } = makeMigrateFixture({
    catalogGroups: BASE_CATALOG,
    flatDirs: ['pdf'],
    nestedDirs: [{ vendor: 'obra', skill: 'brainstorming' }]
  });
  cleanupFns.push(cleanup);

  const { exitCode, result, stderr } = runCli(['migrate'], fakeHome);

  // [RED expect] 'migrate' 서브커맨드 미구현 → exit 1, JSON 없음
  assert.strictEqual(exitCode, 0,
    `[RED expect] migrate exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null,
    `[RED expect] migrate stdout should be valid JSON but was not. stderr: ${stderr}`);

  // 실 파일시스템 재확인: pdf/ → anthropics/pdf/ 로 이동되어야 함
  const oldFlatPath = path.join(communityDir, 'pdf');
  const newNestedPath = path.join(communityDir, 'anthropics', 'pdf', 'SKILL.md');
  assert.strictEqual(fs.existsSync(oldFlatPath), false,
    `[RED expect] 이동 후 flat 경로(${oldFlatPath})는 더 이상 존재하지 않아야 함`);
  assert.strictEqual(fs.existsSync(newNestedPath), true,
    `[RED expect] 이동 후 vendor 중첩 경로(${newNestedPath})가 존재해야 함`);

  // 이미 중첩된 obra/brainstorming은 skip(그대로 유지)
  const nestedUnchanged = path.join(communityDir, 'obra', 'brainstorming', 'SKILL.md');
  assert.strictEqual(fs.existsSync(nestedUnchanged), true,
    '이미 중첩된 obra/brainstorming은 skip되어 그대로 존재해야 함');

  if (result) {
    assert.ok(Array.isArray(result.moved), 'result.moved should be an array');
    const movedPdf = (result.moved || []).some(m => m && String(m.to || '').includes(path.join('anthropics', 'pdf')));
    assert.ok(movedPdf, `[RED expect] result.moved에 anthropics/pdf 이동 기록이 있어야 함. got: ${JSON.stringify(result.moved)}`);
  }
});

test('[T102/L2-F1] migrate 재실행: 멱등 — moved 0건 (2회차)', () => {
  const { fakeHome, communityDir, cleanup } = makeMigrateFixture({
    catalogGroups: BASE_CATALOG,
    flatDirs: ['pdf'],
    nestedDirs: [{ vendor: 'obra', skill: 'brainstorming' }]
  });
  cleanupFns.push(cleanup);

  // 1회차 실행
  runCli(['migrate'], fakeHome);
  // 2회차 실행 (멱등 검증)
  const { exitCode, result, stderr } = runCli(['migrate'], fakeHome);

  assert.strictEqual(exitCode, 0,
    `[RED expect] 2회차 migrate exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null,
    `[RED expect] 2회차 migrate stdout should be valid JSON but was not. stderr: ${stderr}`);
  if (result) {
    assert.strictEqual((result.moved || []).length, 0,
      `[RED expect] 재실행 시 moved는 0건(멱등)이어야 함. got: ${JSON.stringify(result.moved)}`);
  }

  // 실 파일시스템: 이미 이동된 anthropics/pdf/SKILL.md가 여전히 존재해야 함
  const nestedPdf = path.join(communityDir, 'anthropics', 'pdf', 'SKILL.md');
  assert.strictEqual(fs.existsSync(nestedPdf), true, '재실행 후에도 이미 이동된 경로는 그대로 존재해야 함');
});

// ─── [T103/L2-F1] migrate: 미등재·basename 충돌 보존 (142 D-4, S-3) ─────────

test('[T103/L2-F1] migrate: 미등재 flat 디렉토리 무이동 보존(preserved reason:"unregistered"), errors 0', () => {
  const { fakeHome, communityDir, cleanup } = makeMigrateFixture({
    catalogGroups: BASE_CATALOG,
    flatDirs: ['pdf', 'my-private']   // my-private는 registry 미등재
  });
  cleanupFns.push(cleanup);

  const myPrivatePath = path.join(communityDir, 'my-private');
  const myPrivateSkillMd = path.join(myPrivatePath, 'SKILL.md');
  const beforeContent = fs.readFileSync(myPrivateSkillMd, 'utf8');

  const { exitCode, result, stderr } = runCli(['migrate'], fakeHome);

  // [RED expect] 'migrate' 미구현 → exit 1
  assert.strictEqual(exitCode, 0,
    `[RED expect] migrate exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null,
    `[RED expect] migrate stdout should be valid JSON but was not. stderr: ${stderr}`);

  // 142 D-4: 미등재 디렉토리는 절대 이동·삭제되지 않아야 함 — 데이터 소실 0
  assert.strictEqual(fs.existsSync(myPrivatePath), true,
    '미등재 flat 디렉토리(my-private)는 원위치에 그대로 존재해야 함 (142 D-4)');
  assert.strictEqual(fs.readFileSync(myPrivateSkillMd, 'utf8'), beforeContent,
    '미등재 디렉토리 내용은 변형되면 안 됨');

  if (result) {
    assert.strictEqual((result.errors || []).length, 0,
      `errors는 0건이어야 함(미등재는 보존 대상이지 오류가 아님). got: ${JSON.stringify(result.errors)}`);
    const preservedUnregistered = (result.preserved || []).some(p => p && p.reason === 'unregistered');
    assert.ok(preservedUnregistered,
      `[RED expect] preserved에 reason:"unregistered" 항목이 있어야 함. got: ${JSON.stringify(result.preserved)}`);
  }
});

test('[T103/L2-F1] migrate: basename 충돌 flat 디렉토리 무이동 보존(preserved reason:"basename_collision"), errors 0', () => {
  // basename "pdf"가 anthropics/pdf ↔ vendorx/pdf 2벤더에 등재된 상태에서 flat "pdf/" 디렉토리 존재
  // → 어느 vendor로 이동해야 할지 결정 불가 → 이동 금지, preserved 기록
  const { fakeHome, communityDir, cleanup } = makeMigrateFixture({
    catalogGroups: COLLISION_CATALOG,
    flatDirs: ['pdf']
  });
  cleanupFns.push(cleanup);

  const flatPdfPath = path.join(communityDir, 'pdf');
  const flatPdfSkillMd = path.join(flatPdfPath, 'SKILL.md');
  const beforeContent = fs.readFileSync(flatPdfSkillMd, 'utf8');

  const { exitCode, result, stderr } = runCli(['migrate'], fakeHome);

  assert.strictEqual(exitCode, 0,
    `[RED expect] migrate exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null,
    `[RED expect] migrate stdout should be valid JSON but was not. stderr: ${stderr}`);

  // 충돌 시 무이동 — 데이터 손실 0
  assert.strictEqual(fs.existsSync(flatPdfPath), true,
    'basename 충돌 시 flat 디렉토리(pdf)는 원위치에 그대로 존재해야 함');
  assert.strictEqual(fs.readFileSync(flatPdfSkillMd, 'utf8'), beforeContent,
    '충돌 디렉토리 내용은 변형되면 안 됨');

  if (result) {
    assert.strictEqual((result.errors || []).length, 0,
      `errors는 0건이어야 함(충돌은 보존 대상이지 오류가 아님). got: ${JSON.stringify(result.errors)}`);
    const preservedCollision = (result.preserved || []).some(p => p && p.reason === 'basename_collision');
    assert.ok(preservedCollision,
      `[RED expect] preserved에 reason:"basename_collision" 항목이 있어야 함. got: ${JSON.stringify(result.preserved)}`);
  }
});

// ─── [T104/L2-F1] migrate 후 list --group=community 전수 installed:true (S-4, 회귀) ─

test('[T104/L2-F1] migrate 후 `list --group=community` catalog 등재 전수 installed:true', () => {
  const { fakeHome, cleanup } = makeMigrateFixture({
    catalogGroups: BASE_CATALOG,
    flatDirs: ['pdf'],
    nestedDirs: [{ vendor: 'obra', skill: 'brainstorming' }]
  });
  cleanupFns.push(cleanup);

  // migrate 선행 실행 (현행: unknown command → 아무 이동도 일어나지 않음, RED 전제)
  runCli(['migrate'], fakeHome);

  const { exitCode, result } = runCli(['list', '--group=community'], fakeHome);

  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}`);
  assert.ok(Array.isArray(result), 'list 결과는 배열이어야 함');

  // [RED expect] 이중 RED: (1) 현행 listCommand()의 `--group=` 필터는 s._group(벤더명)만 비교하여
  // "community"라는 가상 그룹명과 매칭되지 않아 결과가 항상 빈 배열([])이다(test-match.js T601 baseline과 동일 원인).
  // (2) migrate 미구현으로 pdf/ 도 여전히 flat 상태 → installed 필드조차 listCommand에 없다.
  assert.ok(result.length > 0, `[RED expect] catalog 등재 스킬이 1개 이상 목록에 있어야 함. got: ${JSON.stringify(result)}`);
  const allInstalled = result.every(s => s.installed === true);
  assert.ok(allInstalled,
    `[RED expect] catalog 등재 전수 installed:true 여야 함. got: ${JSON.stringify(result.map(s => ({ name: s.name, installed: s.installed })))}`);
});
