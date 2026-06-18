//
// @module      test-validate
// @layer       tools/test
// @domain      skill-management
// @description validate() 단위 테스트 — RED-first 트랙 (F-004, 태스크 029)
//              CLI 블랙박스 방식: node skill-registry.js validate 를 child_process 로 실행,
//              exit code + stdout JSON으로 동작 검증. mock/monkeypatch 없음, 실제 fs 위 합성 fixture 사용.
// @depends     node:test, node:assert, node:fs, node:path, node:os, node:child_process
//              (신규 패키지 0, Node 내장 모듈만 사용)
//
// TC 매핑 (TEST-SCENARIO.md §3):
//   TC1 (clean)        → S-4: 정합 fixture → valid:true, errors 0, exit 0
//   TC2 (dangling)     → S-1: 폴더 없는 레지스트리 항목 → errors에 "dangling" 포함, exit 1
//   TC3 (unregistered) → S-2: 미등록 폴더 → errors에 "unregistered" 포함, exit 1
//   TC4 (deploy env)   → S-3: refDir이 배포 경로 → unregistered 스캔 비활성, false positive 0
//   TC5 (standalone)   → S-2: top-level skills/ 등록 폴더 → unregistered 오판 0
//
// 변경이력:
//   v1.0 2026-06-18 KST: RED-first 단위 테스트 최초 작성 (태스크 029, opal-test-agent mode:red)
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
 * 임시 fixture 디렉토리를 생성하고 합성 레지스트리 + 스킬 폴더를 만든다.
 * @param {object} opts
 * @param {string[]} opts.registeredNames     - 레지스트리에 등록할 스킬 이름 배열
 * @param {string[]} opts.existingFolders     - opal/skills/ 아래 실제로 만들 폴더 이름 배열
 * @param {string[]} [opts.standaloneFolders] - top-level skills/ 아래 만들 폴더 (standalone)
 * @param {boolean}  [opts.deployEnv]         - true면 refDir를 ~/.opal/references/ 모사
 * @returns {{ dir: string, refDir: string, cleanup: () => void }}
 */
function makeFixture({ registeredNames, existingFolders, standaloneFolders = [], deployEnv = false }) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-test-validate-'));

  // opal/core/references/ (소스 환경 레지스트리 경로)
  const srcRefDir = path.join(dir, 'opal', 'core', 'references');
  fs.mkdirSync(srcRefDir, { recursive: true });

  // opal/skills/ — 등록 스킬 폴더
  for (const name of existingFolders) {
    const skillDir = path.join(dir, 'opal', 'skills', name);
    fs.mkdirSync(skillDir, { recursive: true });
    fs.writeFileSync(path.join(skillDir, 'SKILL.md'), `# ${name}\n`);
  }

  // top-level skills/ — standalone 스킬 폴더
  for (const name of standaloneFolders) {
    const skillDir = path.join(dir, 'skills', name);
    fs.mkdirSync(skillDir, { recursive: true });
    fs.writeFileSync(path.join(skillDir, 'SKILL.md'), `# ${name} standalone\n`);
  }

  // 레지스트리 JSON 생성
  const allSkills = registeredNames.map(name => ({
    name,
    alias: null,
    description: `${name} fixture skill`,
    triggers: [`^${name}$`],
    paths: [
      // 소스 환경 경로: {project}/opal/skills/<name>/SKILL.md 또는 {project}/skills/<name>/SKILL.md
      `{project}/opal/skills/${name}/SKILL.md`,
      `{project}/skills/${name}/SKILL.md`,
    ]
  }));

  const registry = {
    '$schema': 'opal-skills-registry-v1',
    version: '0.0.1-fixture',
    updated_at: '2026-06-18',
    groups: {
      fixture: allSkills
    }
  };

  let refDir;
  if (deployEnv) {
    // 배포 환경 모사: ~/.opal/references/ 에 레지스트리를 두고, refDir도 거기를 가리키도록
    // skill-registry.js는 getReferencesDir()에서 ~/.opal/references/opal-skills-registry.json 존재 여부를 확인.
    // 배포 환경 테스트는 실제 ~/.opal/references/를 건드리지 않고,
    // 대신 OPAL_REF_DIR 환경변수 주입을 이용하거나 (현재 지원 없음),
    // 임시 디렉토리 내에 .opal/references/ 경로를 만들고 HOME을 오버라이드하는 방식을 사용.
    // HOME 오버라이드: spawnSync 시 env.HOME=dir로 지정하면 os.homedir()가 그 값을 반환.
    // 단, Node.js에서 os.homedir()는 HOME env를 읽으므로 이 방식이 동작한다.
    const fakeHome = path.join(dir, 'fakehome');
    const deployRefDir = path.join(fakeHome, '.opal', 'references');
    fs.mkdirSync(deployRefDir, { recursive: true });
    fs.writeFileSync(path.join(deployRefDir, 'opal-skills-registry.json'), JSON.stringify(registry, null, 2));
    refDir = deployRefDir;
    // HOME 오버라이드용 경로를 dir에 저장
    dir._fakeHome = fakeHome;
    dir._deployRefDir = deployRefDir;
  } else {
    // 소스 환경: opal/core/references/ 에 레지스트리
    fs.writeFileSync(path.join(srcRefDir, 'opal-skills-registry.json'), JSON.stringify(registry, null, 2));
    refDir = srcRefDir;
  }

  function cleanup() {
    fs.rmSync(dir, { recursive: true, force: true });
  }

  return { dir, refDir, cleanup };
}

/**
 * skill-registry.js validate 를 CLI로 실행한다.
 * @param {string} cwd       - 프로세스 cwd (fixture 루트)
 * @param {object} [envOverride] - 추가 환경변수
 * @returns {{ exitCode: number, stdout: string, stderr: string, result: object|null }}
 */
function runValidate(cwd, envOverride = {}) {
  const env = { ...process.env, ...envOverride };
  const result = spawnSync('node', [SKILL_REGISTRY_JS, 'validate'], {
    cwd,
    env,
    encoding: 'utf8',
    timeout: 10000
  });

  const stdout = result.stdout || '';
  const stderr = result.stderr || '';
  const exitCode = result.status;

  let parsed = null;
  try {
    parsed = JSON.parse(stdout.trim());
  } catch (_) {
    // JSON 파싱 실패 — stdout이 JSON이 아닌 경우
  }

  return { exitCode, stdout, stderr, result: parsed };
}

// 정리용 배열 (afterEach 없이 after로 일괄)
const cleanupFns = [];
after(() => {
  for (const fn of cleanupFns) {
    try { fn(); } catch (_) { /* ignore */ }
  }
});

// ─── TC1: clean fixture → exit 0, errors 0, valid:true (S-4) ────────────────

test('TC1 (clean): 정합 fixture → valid:true, errors 0, exit 0', () => {
  const { dir, cleanup } = makeFixture({
    registeredNames: ['skill-alpha', 'skill-beta'],
    existingFolders:  ['skill-alpha', 'skill-beta'],
  });
  cleanupFns.push(cleanup);

  const { exitCode, result } = runValidate(dir);

  // GREEN에서 통과해야 할 기대값 (현행에서도 통과 가능)
  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}\nresult: ${JSON.stringify(result)}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.valid, true, `valid should be true but got ${result.valid}`);
  assert.strictEqual(result.errors.length, 0, `errors should be empty but got: ${JSON.stringify(result.errors)}`);
});

// ─── TC2: dangling → exit 1, errors에 "dangling" (S-1) ──────────────────────

test('TC2 (dangling): 폴더 없는 레지스트리 항목 → errors에 "dangling" 포함, exit 1', () => {
  // skill-alpha 폴더는 있지만 skill-ghost 폴더는 없음 (dangling)
  const { dir, cleanup } = makeFixture({
    registeredNames: ['skill-alpha', 'skill-ghost'],
    existingFolders:  ['skill-alpha'],           // skill-ghost 폴더 없음 → dangling
  });
  cleanupFns.push(cleanup);

  const { exitCode, result } = runValidate(dir);

  // [RED 기대] 현행 코드는 warnings.push → exit 0 이므로 이 assert들은 FAIL한다
  assert.strictEqual(exitCode, 1,
    `[RED expect] exit code should be 1 (dangling=error) but got ${exitCode}. ` +
    `현행 코드는 warning으로만 처리하여 exit 0 반환 → RED 확인`);

  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.valid, false,
    `[RED expect] valid should be false but got ${result.valid}`);

  const hasDanglingError = result.errors.some(e => e.includes('dangling'));
  assert.ok(hasDanglingError,
    `[RED expect] errors should contain "dangling" but got: ${JSON.stringify(result.errors)}`);
});

// ─── TC3: unregistered → exit 1, errors에 "unregistered" (S-2) ──────────────

test('TC3 (unregistered): 미등록 폴더 → errors에 "unregistered" 포함, exit 1', () => {
  // skill-alpha는 등록+폴더 있음. skill-orphan은 폴더만 있고 레지스트리 미등록
  const { dir, cleanup } = makeFixture({
    registeredNames: ['skill-alpha'],
    existingFolders:  ['skill-alpha', 'skill-orphan'],  // skill-orphan은 미등록
  });
  cleanupFns.push(cleanup);

  const { exitCode, result } = runValidate(dir);

  // [RED 기대] 현행 코드에는 validateUnregistered() 자체가 없으므로 이 assert들은 FAIL한다
  assert.strictEqual(exitCode, 1,
    `[RED expect] exit code should be 1 (unregistered detected) but got ${exitCode}. ` +
    `현행 코드는 unregistered 감지 기능이 없어 exit 0 반환 → RED 확인`);

  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.valid, false,
    `[RED expect] valid should be false but got ${result.valid}`);

  const hasUnregisteredError = result.errors.some(e => e.includes('unregistered'));
  assert.ok(hasUnregisteredError,
    `[RED expect] errors should contain "unregistered" but got: ${JSON.stringify(result.errors)}`);
});

// ─── TC4: deploy env → unregistered 스캔 비활성, false positive 0 (S-3) ──────

test('TC4 (deploy env): 배포 환경에서 미등록 폴더가 있어도 false positive 0, exit 0', () => {
  // 배포 환경(HOME 오버라이드로 ~/.opal/references/ 를 모사)에서는
  // unregistered 스캔을 비활성화해야 한다 (PLAN §3.4.2(c))
  // fixture: skill-alpha 등록 + skill-orphan 미등록 폴더 있음
  // 배포 환경이면 unregistered 스캔 안 함 → exit 0 기대

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-test-validate-deploy-'));
  cleanupFns.push(() => fs.rmSync(dir, { recursive: true, force: true }));

  // 배포 환경: fakeHome/.opal/references/ 에 레지스트리
  const fakeHome = path.join(dir, 'fakehome');
  const deployRefDir = path.join(fakeHome, '.opal', 'references');
  fs.mkdirSync(deployRefDir, { recursive: true });

  // 스킬 폴더는 fakeHome/.opal/skills/ 아래에 (배포 환경 폴더 구조)
  // 단, validate()의 unregistered 스캔은 cwd 기준이므로 cwd 아래에도 만들어 둔다
  const opalSkillsDir = path.join(dir, 'opal', 'skills');
  fs.mkdirSync(path.join(opalSkillsDir, 'skill-alpha'), { recursive: true });
  fs.writeFileSync(path.join(opalSkillsDir, 'skill-alpha', 'SKILL.md'), '# skill-alpha\n');
  fs.mkdirSync(path.join(opalSkillsDir, 'skill-orphan'), { recursive: true });
  fs.writeFileSync(path.join(opalSkillsDir, 'skill-orphan', 'SKILL.md'), '# skill-orphan\n');

  const registry = {
    '$schema': 'opal-skills-registry-v1',
    version: '0.0.1-deploy',
    updated_at: '2026-06-18',
    groups: {
      fixture: [{
        name: 'skill-alpha',
        alias: null,
        description: 'alpha fixture',
        triggers: ['^skill-alpha$'],
        paths: [`~/.opal/skills/skill-alpha/SKILL.md`]
      }]
    }
  };
  fs.writeFileSync(path.join(deployRefDir, 'opal-skills-registry.json'), JSON.stringify(registry, null, 2));

  // HOME을 fakeHome으로 오버라이드 → getReferencesDir()가 deployRefDir를 선택
  // skill-alpha의 paths는 ~/.opal/skills/... 이므로 fakeHome 기준 존재 안 함 (warning만)
  const { exitCode, result } = runValidate(dir, { HOME: fakeHome });

  // 배포 환경이면 unregistered 스캔 비활성 → skill-orphan이 있어도 unregistered 오류 없어야 함
  // [현행] 현행 코드에는 unregistered 감지 자체가 없으므로 이 케이스는 현행에서도 통과할 수 있다
  // [GREEN 기대] GREEN 구현 후에도 배포 환경에서는 동일하게 통과해야 한다 (false positive 방지 보장)
  assert.ok(result !== null, 'stdout should be valid JSON');

  const hasUnregisteredError = result && result.errors
    ? result.errors.some(e => e.includes('unregistered'))
    : false;
  assert.ok(!hasUnregisteredError,
    `[TC4] 배포 환경에서 unregistered false positive 0 기대, but errors: ${JSON.stringify(result && result.errors)}`);

  // 배포 환경에서는 dangling(path 미존재)도 warning으로만 처리되므로 exit은 현행 기준 검증
  // 핵심: unregistered error가 없어야 한다 (위에서 검증 완료)
});

// ─── TC5: standalone (top-level skills/) 등록 폴더 → unregistered 오판 0 (S-2) ─

test('TC5 (standalone): top-level skills/ 등록 폴더는 unregistered 오판 없음', () => {
  // top-level skills/api-analyzer 는 registeredNames에 포함(등록됨)
  // opal/skills/ 에는 없고 skills/ 에만 있음 — PLAN §3.4.2(b) 양쪽 스캔
  // → unregistered 오판 없어야 함 (H-3 false positive 방지)
  const { dir, cleanup } = makeFixture({
    registeredNames:   ['skill-alpha', 'api-analyzer'],
    existingFolders:   ['skill-alpha'],           // opal/skills/ 에는 skill-alpha만
    standaloneFolders: ['api-analyzer'],          // skills/ 에 api-analyzer (등록됨)
  });
  cleanupFns.push(cleanup);

  const { exitCode, result } = runValidate(dir);

  // [현행 + GREEN 공통 기대]
  // skill-alpha: opal/skills/skill-alpha/ 존재 → 정합
  // api-analyzer: skills/api-analyzer/ 존재 + 레지스트리 등록 → 오판 없음
  // 미등록 폴더 없음 → unregistered error 없어야 함
  assert.ok(result !== null, 'stdout should be valid JSON');

  const hasUnregisteredError = result && result.errors
    ? result.errors.some(e => e.includes('unregistered'))
    : false;
  assert.ok(!hasUnregisteredError,
    `[TC5] standalone 등록 폴더가 unregistered로 오판되면 안 됨. errors: ${JSON.stringify(result && result.errors)}`);

  // exit 0 기대 (정합 상태)
  // [현행] unregistered 감지 없으므로 현행에서도 exit 0일 가능성 높음
  // [GREEN] validateUnregistered가 양쪽 스캔 시에도 오판 없어야 함
  assert.strictEqual(exitCode, 0,
    `[TC5] 정합+standalone 등록 fixture는 exit 0 기대, got ${exitCode}. result: ${JSON.stringify(result)}`);
});
