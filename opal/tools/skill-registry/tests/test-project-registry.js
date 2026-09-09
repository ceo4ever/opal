//
// @module      test-project-registry
// @layer       tools/test
// @domain      skill-management
// @task        114
// @description opal-skill-wizard 신설 태스크(114)의 F-001(프로젝트 스코프 registry 4번째 병합 소스)에
//              대한 RED-first 통합 테스트 — TS-001~TS-009 전건.
//              CLI 블랙박스 방식: node skill-registry.js <match|get|list|validate> 를
//              child_process(spawnSync)로 실행, exit code + stdout JSON으로 동작 검증.
//              mock/monkeypatch 없음 — 실 fs 위 합성 fixture(HOME + cwd 이중 오버라이드) 사용.
//              RED 작성 시점 기준 findProjectRoot()/loadProjectRegistry()/resolveProjectSkillPath()/
//              loadAllSkills() 4번째 병합/matchCommand() project 분기/getCommand() resolved_path
//              전건이 skill-registry.js에 아직 구현되어 있지 않다 — 아래 각 테스트의 [RED expect]
//              주석이 "구현되면 성립, 현재는 실패한다"를 설명한다.
// @depends     node:test, node:assert, node:fs, node:path, node:os, node:child_process
//              (신규 패키지 0, Node 내장 모듈만 사용)
// @scenarios   TEST-SCENARIO.md §2.2 데이터 흐름 표 / §3 L2 표 TS-001~TS-009
//
// TC 매핑 (TEST-SCENARIO.md §3 L2 표, §4 AC 매핑 표):
//   [T114/L2-001] TS-001 — 정상 registry + 본체 존재 → match found:true, scope:"project", installed:true
//   [T114/L2-002] TS-002 — registry 부재 → exit 0 + 전역 3소스 결과가 진짜 무프로젝트 기준선과 동일
//   [T114/L2-003] TS-003 — registry 파손(잘린 JSON) → exit 0 + project 유래 스킬 0건, 예외 전파 0건
//   [T114/L2-004] TS-004 — get 의 resolved_path 가 실제 SKILL.md 절대경로
//   [T114/L2-005] TS-005 — 등재됐으나 본체 미존재 → get resolved_path:null / match installed:false
//   [T114/L2-006] TS-006 — main 스킬 get → 기존 paths 배열 원형 보존 + resolved_path 추가(필드 삭제 0건)
//   [T114/L2-007] TS-007 — cwd = 프로젝트 루트 3단 하위(a/b/c) → match found:true (walk-up 도달)
//   [T114/L2-008] TS-008 — cwd = 가짜 HOME 하위, 홈 경계 정지 → 홈에 존재하는 registry가 병합되지 않음
//   [T114/L2-009] TS-009 — 전역·프로젝트 동일 name → 프로젝트 정의가 반환 (override, DEC-3)
//
// 변경이력:
//   v1.0 2026-09-04 KST: RED-first 통합 테스트 최초 작성 (태스크 114, opal-test-agent mode:red)
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

const cleanupFns = [];
after(() => {
  for (const fn of cleanupFns) {
    try { fn(); } catch (_) { /* ignore */ }
  }
});

/**
 * 전역(fakeHome) + 프로젝트(fakeProject) 이중 fixture를 만든다.
 *
 * 격리 설계 (PLAN.md §3.2.2):
 * - fakeHome: `mkdtempSync`로 생성한 가짜 HOME. `.opal/references/`에 main+community 전역
 *   카탈로그(최소 유효 JSON)를 둔다 — `getReferencesDir()` 2순위(배포 경로)가 선택되도록 한다.
 * - [MUST] `getReferencesDir()` 1순위 회피: 1순위는 `path.resolve(process.cwd(), 'opal','core','references')`
 *   이므로, fakeProject 안에는 **`opal/core/references/`를 절대 만들지 않는다** — 만들면 cwd=fakeProject로
 *   실행할 때 1순위가 먼저 걸려 fixture 전역 카탈로그(fakeHome)가 무시되고 실제 리포지토리 소스
 *   레이아웃을 참조하게 되어 fixture가 무의미해진다.
 * - fakeProject: `.opal/` 디렉토리 존재 자체가 **프로젝트 루트 탐색 마커**다(PM 교정 — 파일이 아니라
 *   디렉토리). `projectRegistryState`에 따라 `.opal/skills-registry.json`을 유/무/파손 3태로 만든다.
 * - 프로젝트 스킬 본체는 전역 설치 위치와 동형인 `.opal/community-skills/{vendor}/{skill}/SKILL.md`.
 *
 * @param {object} opts
 * @param {'absent'|'valid'|'corrupt'} [opts.projectRegistryState='valid']
 * @param {boolean} [opts.installMyskillBody=true]   - myvendor/myskill 본체 SKILL.md 생성 여부
 * @param {boolean} [opts.includeOverrideEntry=false] - sharedvendor/shared-skill 를 프로젝트 registry에도 등재(override 검증용)
 * @param {boolean} [opts.installOverrideBody=false]  - override 스킬 본체를 프로젝트 스코프에 생성
 * @param {boolean} [opts.homeLeakProbe=false]        - `{fakeHome}/.opal/skills-registry.json`에
 *        홈 경계 정지 검증용 "누출 탐지" 프로젝트 registry를 심는다 (TS-008 전용, §아래 설명 참조)
 * @returns {{ fakeHome:string, fakeProject:string, myskillBodyPath:string|null, cleanup:()=>void }}
 */
function makeProjectFixture(opts = {}) {
  const {
    projectRegistryState = 'valid',
    installMyskillBody = true,
    includeOverrideEntry = false,
    installOverrideBody = false,
    homeLeakProbe = false
  } = opts;

  const fakeHome = fs.mkdtempSync(path.join(os.tmpdir(), 'osw-home-'));
  const fakeProject = fs.mkdtempSync(path.join(os.tmpdir(), 'osw-proj-'));

  // ── 전역(fakeHome) 카탈로그 — main + community 2종, 최소 유효 JSON ──────────
  const refDir = path.join(fakeHome, '.opal', 'references');
  fs.mkdirSync(refDir, { recursive: true });

  const mainRegistry = {
    '$schema': 'opal-skills-registry-v1',
    version: '0.0.1-fixture',
    updated_at: '2026-09-04',
    groups: {
      opal: [
        {
          name: 'opal/demo-skill',
          alias: 'demo',
          description: 'GLOBAL demo skill (main)',
          domain: 'test',
          triggers: ['(?i)(demo-skill)'],
          paths: ['{project}/opal/skills/demo-skill/SKILL.md']
        }
      ]
    }
  };
  fs.writeFileSync(path.join(refDir, 'opal-skills-registry.json'), JSON.stringify(mainRegistry, null, 2));

  const communityRegistry = {
    '$schema': 'opal-community-skills-registry-v2.1',
    version: '2.1.0-fixture',
    updated_at: '2026-09-04',
    schema_notes: 'fixture — test-project-registry.js (태스크 114)',
    groups: {
      sharedvendor: [
        {
          name: 'sharedvendor/shared-skill',
          alias: null,
          description: 'GLOBAL shared-skill (community)',
          triggers: ['(?i)(shared-skill)'],
          source_repo: 'sharedvendor/repo@shared-skill',
          commit_sha: null,
          license: 'MIT'
        }
      ]
    }
  };
  fs.writeFileSync(path.join(refDir, 'community-skills-registry.json'), JSON.stringify(communityRegistry, null, 2));
  // 전역 community-skills 본체 디렉토리는 의도적으로 만들지 않는다 — sharedvendor/shared-skill은
  // "전역에는 미설치" 상태로 두어 TS-009 override 판정(설치 경로가 project 쪽인지)을 결정적으로 만든다.

  // validate()의 "dangling path" 검사(main 스킬 paths 실존성, `:502-509`)가 오탐하지 않도록
  // demo-skill의 실제 SKILL.md 본체를 fakeProject 하위에도 둔다 — `{project}` 플레이스홀더는
  // 런타임 process.cwd()로 치환되므로, cwd=fakeProject로 CLI를 실행하는 시나리오(TS-002 등)에서
  // 이 경로가 실존해야 validate()가 허위 "dangling" 오류로 exit 1을 내지 않는다.
  const demoSkillBodyDir = path.join(fakeProject, 'opal', 'skills', 'demo-skill');
  fs.mkdirSync(demoSkillBodyDir, { recursive: true });
  fs.writeFileSync(path.join(demoSkillBodyDir, 'SKILL.md'), '# opal/demo-skill (main fixture body)\n');

  // ── 프로젝트(fakeProject) — `.opal/` 존재 자체가 루트 마커 ──────────────────
  const projectOpalDir = path.join(fakeProject, '.opal');
  fs.mkdirSync(projectOpalDir, { recursive: true });
  // [MUST] fakeProject 하위에 opal/core/references/ 를 두지 않는다 (getReferencesDir 1순위 회피, 위 주석 참조).

  const projectGroups = {
    project: [
      {
        name: 'myvendor/myskill',
        alias: 'mysk',
        description: 'PROJECT myskill',
        triggers: ['(?i)(myskill)'],
        source_repo: 'myvendor/myrepo@myskill',
        commit_sha: null,
        license: 'MIT'
      }
    ]
  };
  if (includeOverrideEntry) {
    projectGroups.project.push({
      name: 'sharedvendor/shared-skill',
      alias: null,
      description: 'PROJECT shared-skill (override)',
      triggers: ['(?i)(shared-skill)'],
      source_repo: 'sharedvendor/repo@shared-skill',
      commit_sha: null,
      license: 'MIT'
    });
  }
  const projectRegistry = {
    '$schema': 'opal-project-skills-registry-v1',
    version: '0.1.0-fixture',
    updated_at: '2026-09-04',
    groups: projectGroups
  };

  const projectRegistryPath = path.join(projectOpalDir, 'skills-registry.json');
  if (projectRegistryState === 'valid') {
    fs.writeFileSync(projectRegistryPath, JSON.stringify(projectRegistry, null, 2));
  } else if (projectRegistryState === 'corrupt') {
    fs.writeFileSync(projectRegistryPath, '{"$schema": "opal-project-skills-registry-v1", "groups": { "project": [ { "name": "trunc');
  }
  // 'absent' → 파일을 만들지 않는다 (`.opal/` 디렉토리 자체는 이미 존재 — 부재는 registry 파일 한정)

  let myskillBodyPath = null;
  if (installMyskillBody) {
    const dir = path.join(projectOpalDir, 'community-skills', 'myvendor', 'myskill');
    fs.mkdirSync(dir, { recursive: true });
    myskillBodyPath = path.join(dir, 'SKILL.md');
    fs.writeFileSync(myskillBodyPath, '# myvendor/myskill (project fixture)\n');
  }
  if (installOverrideBody) {
    const dir = path.join(projectOpalDir, 'community-skills', 'sharedvendor', 'shared-skill');
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'SKILL.md'), '# sharedvendor/shared-skill (project override fixture)\n');
  }

  // ── TS-008 전용: 홈 경계 정지 "누출 탐지" registry ──────────────────────────
  // findProjectRoot()의 [MUST] 종료 조건 ①(PLAN §3.1.2(a))은 "dir === os.homedir() 이면
  // *검사하지 않고* null을 반환"이다 — 즉 홈 디렉토리 자체에 `.opal/skills-registry.json`이
  // 실재하더라도 그것을 프로젝트 registry로 채택해서는 안 된다. 이를 CLI 블랙박스로 관측 가능하게
  // 만들기 위해, 절대 등장해선 안 될 고유한 이름(homeleak/should-not-appear)을 가진 registry를
  // fakeHome/.opal/ 에 직접 심어 둔다. 구현이 종료 조건①을 올바로 지키면 이 스킬은 어떤 CLI 응답에도
  // 나타나지 않는다 — 반대로 홈 디렉토리를 프로젝트 루트로 오인하면 이 이름이 누출되어 검출된다.
  if (homeLeakProbe) {
    const leakRegistry = {
      '$schema': 'opal-project-skills-registry-v1',
      version: '0.1.0-fixture-leak-probe',
      updated_at: '2026-09-04',
      groups: {
        project: [
          {
            name: 'homeleak/should-not-appear',
            alias: 'leakprobe',
            description: 'LEAK PROBE — 홈 디렉토리를 프로젝트 루트로 오인하면 노출됨',
            triggers: ['(?i)(leakprobe)'],
            source_repo: null,
            commit_sha: null,
            license: 'Unknown'
          }
        ]
      }
    };
    fs.writeFileSync(path.join(fakeHome, '.opal', 'skills-registry.json'), JSON.stringify(leakRegistry, null, 2));
  }

  function cleanup() {
    fs.rmSync(fakeHome, { recursive: true, force: true });
    fs.rmSync(fakeProject, { recursive: true, force: true });
  }

  return { fakeHome, fakeProject, myskillBodyPath, cleanup };
}

/**
 * skill-registry.js CLI 를 실행한다 (HOME + cwd 이중 오버라이드로 fixture 격리).
 * `test-match.js:126-135` 의 `runCli` 패턴을 cwd 파라미터화하여 재사용.
 *
 * @param {string[]} args   - ['match', '//name', ...] 형태
 * @param {string} fakeHome - HOME 오버라이드 값
 * @param {string} cwd      - 프로세스 cwd 오버라이드 값 (walk-up 시작점)
 * @returns {{ exitCode: number, stdout: string, stderr: string, result: any }}
 */
function runCli(args, fakeHome, cwd) {
  const env = { ...process.env, HOME: fakeHome };
  const result = spawnSync(process.execPath, [SKILL_REGISTRY_JS, ...args], {
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
    // stdout이 JSON이 아닌 경우 (예: unknown command → stderr만 출력)
  }

  return { exitCode, stdout, stderr, result: parsed };
}

// ─── [T114/L2-001] TS-001: 정상 registry + 본체 존재 → match found/scope/installed ─

test('[T114/L2-001] TS-001: 프로젝트 registry 등재 + 본체 존재 → match found:true, scope:"project", installed:true', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({
    projectRegistryState: 'valid',
    installMyskillBody: true
  });
  cleanupFns.push(cleanup);

  const { exitCode, result, stderr } = runCli(['match', '//myvendor/myskill'], fakeHome, fakeProject);

  // [RED expect] 현재 loadAllSkills()는 프로젝트 registry를 전혀 읽지 않는다(4번째 병합 미구현) —
  // myvendor/myskill은 skills 배열에 존재하지 않아 matchByAlias/matchByTriggers 모두 실패하고
  // found:false 로 귀결된다. 아래 3개 assert가 전부 FAIL해야 정상(RED)이다.
  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.found, true,
    `[RED expect] found should be true but got ${result && result.found}. result: ${JSON.stringify(result)}`);
  assert.strictEqual(result.scope, 'project',
    `[RED expect] scope should be "project" (F-001 신규 필드) but got ${result && result.scope}`);
  assert.strictEqual(result.installed, true,
    `[RED expect] installed should be true (본체 SKILL.md 존재) but got ${result && result.installed}`);
});

// ─── [T114/L2-002] TS-002: registry 부재 → 전역 3소스 결과가 "진짜 무프로젝트" 기준선과 동일 ─

test('[T114/L2-002] TS-002: 프로젝트 registry 부재(.opal/ 마커만 존재) → match/get/list/validate 결과가 무프로젝트 기준선과 완전 동일 + exit 0', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({ projectRegistryState: 'absent' });
  cleanupFns.push(cleanup);

  // "진짜 무프로젝트" 기준선 — .opal/ 마커조차 없는 완전히 별개의 빈 디렉토리에서 동일 HOME으로 실행.
  const baselineDir = fs.mkdtempSync(path.join(os.tmpdir(), 'osw-baseline-'));
  cleanupFns.push(() => fs.rmSync(baselineDir, { recursive: true, force: true }));
  // fakeProject와 동일하게 demo-skill 본체를 실존시켜 validate() dangling 오탐을 양쪽 다 방지한다
  // (§makeProjectFixture 주석 참조 — baselineDir는 공용 fixture 밖에서 만들어지므로 별도 생성 필요).
  const baselineDemoDir = path.join(baselineDir, 'opal', 'skills', 'demo-skill');
  fs.mkdirSync(baselineDemoDir, { recursive: true });
  fs.writeFileSync(path.join(baselineDemoDir, 'SKILL.md'), '# opal/demo-skill (baseline fixture body)\n');

  const commands = [
    ['match', '//demo'],
    ['get', 'opal/demo-skill'],
    ['list'],
    ['validate']
  ];

  // main 스킬의 `path`/`paths` 값은 `{project}` 플레이스홀더를 **호출 시점의 cwd 문자열**로
  // 치환한 뒤 계산된다(resolveFirstPath). project-side(cwd=fakeProject)와 baseline(cwd=baselineDir)은
  // 물리적으로 서로 다른 임시 디렉토리이므로, 이 필드는 "프로젝트 registry 유무"와 무관하게 항상
  // cwd 문자열 차이만큼 달라진다 — 이는 H-1이 검증하려는 병합 로직과 무관한 confound이므로,
  // 비교 전에 각자의 cwd 절대경로 문자열을 공통 플레이스홀더로 정규화한다.
  function normalizeCwd(value, cwdAbs) {
    return JSON.parse(JSON.stringify(value).split(cwdAbs).join('<CWD>'));
  }

  for (const args of commands) {
    const a = runCli(args, fakeHome, fakeProject);
    const b = runCli(args, fakeHome, baselineDir);

    assert.strictEqual(a.exitCode, 0, `[${args.join(' ')}] project-side exit code should be 0 but got ${a.exitCode}. stderr: ${a.stderr}`);
    assert.strictEqual(b.exitCode, 0, `[${args.join(' ')}] baseline exit code should be 0 but got ${b.exitCode}. stderr: ${b.stderr}`);
    assert.ok(a.result !== null, `[${args.join(' ')}] project-side stdout should be valid JSON`);
    assert.ok(b.result !== null, `[${args.join(' ')}] baseline stdout should be valid JSON`);

    const aNorm = normalizeCwd(a.result, fakeProject);
    const bNorm = normalizeCwd(b.result, baselineDir);
    assert.deepStrictEqual(aNorm, bNorm,
      `[RED-guard][${args.join(' ')}] registry 부재 시 결과가 무프로젝트 기준선과 동일해야 함(H-1 무회귀, cwd 경로차는 정규화 후 비교). ` +
      `project-side: ${JSON.stringify(a.result)} / baseline: ${JSON.stringify(b.result)}`);
  }
});

// ─── [T114/L2-003] TS-003: registry 파손(잘린 JSON) → exit 0 + project 유래 스킬 0건 ─

test('[T114/L2-003] TS-003: 프로젝트 registry 파손(잘린 JSON) → exit 0 + 예외 전파 0건 + project 유래 스킬 0건', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({ projectRegistryState: 'corrupt' });
  cleanupFns.push(cleanup);

  const listRes = runCli(['list'], fakeHome, fakeProject);
  assert.strictEqual(listRes.exitCode, 0,
    `파손 JSON이 있어도 exit 0 이어야 함(CLI 다운 금지, H-2) but got ${listRes.exitCode}. stderr: ${listRes.stderr}`);
  assert.ok(listRes.result !== null, `stdout은 여전히 유효한 JSON 이어야 함. got stdout=${listRes.stdout}`);
  assert.ok(Array.isArray(listRes.result), 'list 결과는 배열이어야 함');
  assert.ok(!/SyntaxError|Unexpected end of JSON/i.test(listRes.stderr),
    `stderr에 미처리 JSON 파싱 예외가 노출되면 안 됨. stderr: ${listRes.stderr}`);

  // myvendor/myskill 은 파손된 registry에만 등재되어 있으므로, 파손 내성이 성립하면 어디에도 나타나지 않는다.
  const names = listRes.result.map(s => s.name);
  assert.ok(!names.includes('myvendor/myskill'),
    `[가드] 파손 registry의 스킬명이 병합 결과에 노출되면 안 됨. got: ${JSON.stringify(names)}`);

  const matchRes = runCli(['match', '//myvendor/myskill'], fakeHome, fakeProject);
  assert.strictEqual(matchRes.exitCode, 0, `match 도 exit 0 이어야 함 but got ${matchRes.exitCode}. stderr: ${matchRes.stderr}`);
  assert.strictEqual(matchRes.result && matchRes.result.found, false,
    `파손 registry 항목은 매칭되면 안 됨. result: ${JSON.stringify(matchRes.result)}`);
});

// ─── [T114/L2-004] TS-004: get 의 resolved_path 가 실제 SKILL.md 절대경로 ─

test('[T114/L2-004] TS-004: 본체 존재하는 프로젝트 스킬 get → resolved_path 가 실제 SKILL.md 절대경로와 일치', () => {
  const { fakeHome, fakeProject, myskillBodyPath, cleanup } = makeProjectFixture({
    projectRegistryState: 'valid',
    installMyskillBody: true
  });
  cleanupFns.push(cleanup);

  const { exitCode, result, stderr } = runCli(['get', 'myvendor/myskill'], fakeHome, fakeProject);

  // [RED expect] 현재 getCommand()는 프로젝트 스킬 자체를 loadAllSkills()에서 찾지 못해
  // `{ error: 'Skill not found: myvendor/myskill' }`를 반환한다 — resolved_path 필드 부재로 FAIL.
  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.ok(!result.error,
    `[RED expect] get 이 스킬을 찾아야 함(에러 없음) but got error="${result && result.error}"`);
  // [태스크 114] macOS에서 /var 는 /private/var 심볼릭 링크다 — 자식 프로세스(spawnSync)의
  // process.cwd()는 커널 getcwd(3)가 해석한 canonical 경로(/private/... 접두)를 반환하므로,
  // fakeProject 기준 원본 문자열과 접두사만 다를 뿐 물리적으로 동일한 파일이다. 비교 직전 양측을
  // realpathSync로 정규화해 canonical 형태로 맞춘 뒤에도 여전히 strictEqual로 정확한 일치를 요구한다.
  assert.strictEqual(fs.realpathSync(result.resolved_path), fs.realpathSync(myskillBodyPath),
    `[RED expect] resolved_path should equal actual SKILL.md path "${myskillBodyPath}" but got ${result && result.resolved_path}`);
  assert.ok(fs.existsSync(result.resolved_path || ''),
    'resolved_path가 가리키는 파일이 실제로 존재해야 함(sanity check)');
});

// ─── [T114/L2-005] TS-005: 등재됐으나 본체 미존재 → get resolved_path:null / match installed:false ─

test('[T114/L2-005] TS-005: 등재됐으나 본체 미존재 → get resolved_path:null, match found:true/installed:false', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({
    projectRegistryState: 'valid',
    installMyskillBody: false // 본체 SKILL.md 를 만들지 않는다
  });
  cleanupFns.push(cleanup);

  const getRes = runCli(['get', 'myvendor/myskill'], fakeHome, fakeProject);
  // [RED expect] 현재는 project 스킬 등재 자체가 로드되지 않아 error 객체가 반환된다.
  assert.strictEqual(getRes.exitCode, 0, `exit code should be 0 but got ${getRes.exitCode}. stderr: ${getRes.stderr}`);
  assert.ok(getRes.result !== null, 'stdout should be valid JSON');
  assert.ok(!getRes.result.error,
    `[RED expect] get 이 등재된 스킬을 찾아야 함(미설치와 미등재는 다름) but got error="${getRes.result && getRes.result.error}"`);
  assert.strictEqual(getRes.result.resolved_path, null,
    `[RED expect] resolved_path should be null (본체 미존재) but got ${getRes.result && getRes.result.resolved_path}`);

  const matchRes = runCli(['match', '//myvendor/myskill'], fakeHome, fakeProject);
  assert.strictEqual(matchRes.exitCode, 0, `exit code should be 0 but got ${matchRes.exitCode}. stderr: ${matchRes.stderr}`);
  assert.strictEqual(matchRes.result && matchRes.result.found, true,
    `[RED expect] found should be true(등재됨) but got ${matchRes.result && matchRes.result.found}`);
  assert.strictEqual(matchRes.result && matchRes.result.scope, 'project',
    `[RED expect] scope should be "project" but got ${matchRes.result && matchRes.result.scope}`);
  assert.strictEqual(matchRes.result && matchRes.result.installed, false,
    `[RED expect] installed should be false(본체 미존재) but got ${matchRes.result && matchRes.result.installed}`);
});

// ─── [T114/L2-006] TS-006: main 스킬 get → 기존 paths 원형 보존 + resolved_path additive ─

test('[T114/L2-006] TS-006: main 스킬 get → 기존 paths 배열 원형 보존(필드 삭제·타입변경 0건) + resolved_path 추가', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({ projectRegistryState: 'absent' });
  cleanupFns.push(cleanup);

  const { exitCode, result, stderr } = runCli(['get', 'opal/demo-skill'], fakeHome, fakeProject);

  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.ok(!result.error, `get 이 main 스킬을 찾아야 함 but got error="${result && result.error}"`);

  // 기존 필드 원형 보존 — 삭제·타입 변경 0건 (H-3)
  assert.strictEqual(result.name, 'opal/demo-skill', 'name 필드 보존');
  assert.strictEqual(result.alias, 'demo', 'alias 필드 보존');
  assert.strictEqual(result.description, 'GLOBAL demo skill (main)', 'description 필드 보존');
  assert.strictEqual(result.domain, 'test', 'domain 필드 보존');
  assert.strictEqual(result.group, 'opal', 'group 필드(구 _group) 보존');
  assert.ok(Array.isArray(result.paths), `[회귀 가드] paths 는 배열 타입이어야 함(변경 0건) but got ${JSON.stringify(result.paths)}`);
  assert.deepStrictEqual(result.paths, ['{project}/opal/skills/demo-skill/SKILL.md'],
    `[회귀 가드] paths 배열 내용이 원형 그대로여야 함. got: ${JSON.stringify(result.paths)}`);

  // additive 신규 필드 — [RED expect] 현재 getCommand()에는 resolved_path 필드가 전혀 없다(undefined).
  assert.ok(Object.prototype.hasOwnProperty.call(result, 'resolved_path'),
    `[RED expect] resolved_path 필드가 응답에 존재해야 함(DEC-5 additive) but result keys: ${JSON.stringify(Object.keys(result))}`);
  assert.strictEqual(typeof result.resolved_path, 'string',
    `[RED expect] resolved_path 는 string 이어야 함(paths 존재 시 항상 계산됨) but got ${typeof result.resolved_path} (${result.resolved_path})`);
});

// ─── [T114/L2-007] TS-007: cwd = 프로젝트 루트 3단 하위 → match found:true (walk-up 도달) ─

test('[T114/L2-007] TS-007: cwd가 프로젝트 루트 3단 하위(a/b/c)여도 match found:true (walk-up 상향 탐색 도달)', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({
    projectRegistryState: 'valid',
    installMyskillBody: true
  });
  cleanupFns.push(cleanup);

  const deepCwd = path.join(fakeProject, 'a', 'b', 'c');
  fs.mkdirSync(deepCwd, { recursive: true });

  const { exitCode, result, stderr } = runCli(['match', '//myvendor/myskill'], fakeHome, deepCwd);

  // [RED expect] walk-up 자체가 미구현 — cwd(3단 하위)에서 findProjectRoot()가 존재하지 않으므로
  // 프로젝트 registry는 어차피 읽히지 않는다(TS-001과 동일 사유로 FAIL).
  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.found, true,
    `[RED expect] found should be true (walk-up 으로 프로젝트 루트 도달) but got ${result && result.found}. result: ${JSON.stringify(result)}`);
  assert.strictEqual(result.scope, 'project',
    `[RED expect] scope should be "project" but got ${result && result.scope}`);
});

// ─── [T114/L2-008] TS-008: 홈 경계 정지 — 홈에 존재하는 registry가 병합되지 않음 ─

test('[T114/L2-008] TS-008: cwd가 가짜 HOME 하위 + 홈에 registry 실재해도 홈 경계 정지로 병합 0건 (P0)', () => {
  const { fakeHome, cleanup } = makeProjectFixture({
    projectRegistryState: 'absent', // fakeProject 쪽은 이 테스트에서 사용하지 않음
    installMyskillBody: false,
    homeLeakProbe: true // {fakeHome}/.opal/skills-registry.json 에 누출 탐지용 registry 심음
  });
  cleanupFns.push(cleanup);

  const cwdUnderHome = path.join(fakeHome, 'somewhere');
  fs.mkdirSync(cwdUnderHome, { recursive: true });

  const { exitCode, result, stderr } = runCli(['list'], fakeHome, cwdUnderHome);

  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(Array.isArray(result), 'list 결과는 배열이어야 함');

  const names = result.map(s => s.name);
  // [RED expect] 현재는 프로젝트 registry 병합 자체가 없어 이 assert는 이미 성립한다(회귀 가드) —
  // 다만 findProjectRoot() 구현 시 종료 조건①(homedir 도달 시 검사 없이 null)을 지키지 않으면
  // "homeleak/should-not-appear"가 여기 나타나 REGRESSION으로 검출된다.
  assert.ok(!names.includes('homeleak/should-not-appear'),
    `[P0 가드] 홈 디렉토리를 프로젝트 루트로 오인하면 안 됨(H-4) — leak probe 스킬이 노출됨. got: ${JSON.stringify(names)}`);
  // 전역 카탈로그 2건(main 1 + community 1)만 존재해야 한다 — 그 이상은 홈 오인 누출.
  assert.strictEqual(result.length, 2,
    `[P0 가드] list 결과는 전역 2건(main+community)만 있어야 함(project 유래 0건) but got ${result.length}: ${JSON.stringify(names)}`);
});

// ─── [T114/L2-009] TS-009: 전역·프로젝트 동일 name → 프로젝트 정의가 반환 (override) ─

test('[T114/L2-009] TS-009: 전역·프로젝트에 동일 name 존재 → get 이 프로젝트 정의를 반환(override, DEC-3)', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({
    projectRegistryState: 'valid',
    installMyskillBody: true,
    includeOverrideEntry: true,
    installOverrideBody: true
  });
  cleanupFns.push(cleanup);

  const overrideBodyPath = path.join(fakeProject, '.opal', 'community-skills', 'sharedvendor', 'shared-skill', 'SKILL.md');

  const { exitCode, result, stderr } = runCli(['get', 'sharedvendor/shared-skill'], fakeHome, fakeProject);

  // [RED expect] 현재 loadAllSkills()는 프로젝트 registry를 병합하지 않으므로 get은 전역
  // community 정의(description:"GLOBAL shared-skill (community)")를 반환한다 — override 미성립으로 FAIL.
  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.ok(!result.error, `get 이 스킬을 찾아야 함 but got error="${result && result.error}"`);
  assert.strictEqual(result.description, 'PROJECT shared-skill (override)',
    `[RED expect] 동일 name 충돌 시 프로젝트 정의가 우선해야 함(DEC-3) but got description="${result && result.description}"`);
  // [태스크 114] macOS /var→/private/var 심볼릭 링크로 자식 프로세스 process.cwd()가 canonical
  // 경로를 반환한다 — TS-004와 동일 사유로 비교 직전 양측을 realpathSync 정규화한다.
  assert.strictEqual(fs.realpathSync(result.resolved_path), fs.realpathSync(overrideBodyPath),
    `[RED expect] resolved_path 도 프로젝트 스코프 본체를 가리켜야 함 but got ${result && result.resolved_path}`);
});

// ─── [T114/L2-015] TS-015: 스키마 준수(PLAN.md §3.4.2 12필드) registry → validate error 0건 ─

test('[T114/L2-015] TS-015: PLAN.md §3.4.2 스키마 12필드를 따르는 프로젝트 registry → validate error 0건 (R-7 AC / H-9)', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({
    projectRegistryState: 'absent', // 아래에서 12필드 스키마를 직접 심는다 (기본 fixture는 축약 필드만 가짐)
    installMyskillBody: false
  });
  cleanupFns.push(cleanup);

  // PLAN.md §3.4.2 "항목 필드" 표 12필드 전건 — 표를 그대로 읽어 씀(추측 금지):
  // name / alias / description / triggers / domain / source_repo / commit_sha / license /
  // trust / capabilities / scanned_at / installed_at
  const schemaCompliantEntry = {
    name: 'myvendor/schema-skill',
    alias: 'schsk',
    description: 'PROJECT schema-compliant skill (TS-015)',
    triggers: ['(?i)(schema-skill)'],
    domain: 'test',
    source_repo: 'myvendor/repo@schema-skill',
    commit_sha: 'abc1234',
    license: 'MIT',
    trust: 'SAFE',
    capabilities: ['read-only'],
    scanned_at: '2026-09-04T00:00:00Z',
    installed_at: '2026-09-04T00:00:00Z'
  };

  const projectRegistryPath = path.join(fakeProject, '.opal', 'skills-registry.json');
  fs.writeFileSync(projectRegistryPath, JSON.stringify({
    '$schema': 'opal-project-skills-registry-v1',
    version: '0.1.0-fixture',
    updated_at: '2026-09-04',
    groups: { project: [schemaCompliantEntry] }
  }, null, 2));

  const { exitCode, result, stderr } = runCli(['validate'], fakeHome, fakeProject);

  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.ok(Array.isArray(result.errors), 'validate 결과에 errors 배열이 있어야 함');
  assert.strictEqual(result.errors.length, 0,
    `[R-7 AC] §3.4.2 스키마를 준수하는 프로젝트 registry는 validate error 0건이어야 함 but got: ${JSON.stringify(result.errors)}`);
});

// ─── [T114/L2-029] TS-029: 미지 필드 포함 registry → validate error 0건 (additive 안전성) ─

test('[T114/L2-029] TS-029: 스키마 12필드 + 미지 필드(some_future_field) 포함 registry → validate error 0건 (R-7 / 미지 필드 무시)', () => {
  const { fakeHome, fakeProject, cleanup } = makeProjectFixture({
    projectRegistryState: 'absent',
    installMyskillBody: false
  });
  cleanupFns.push(cleanup);

  // §3.4.2 12필드 + 스키마에 없는 미지 필드 1개 이상(some_future_field) — validate()가 미지 필드를
  // 무시하는 현행 성질(docs/ARCHITECTURE.md §커뮤니티 스킬)이 프로젝트 registry에도 그대로
  // 적용되는지 확인한다.
  const entryWithUnknownField = {
    name: 'myvendor/future-skill',
    alias: 'futsk',
    description: 'PROJECT skill with unknown field (TS-029)',
    triggers: ['(?i)(future-skill)'],
    domain: 'test',
    source_repo: 'myvendor/repo@future-skill',
    commit_sha: 'def5678',
    license: 'MIT',
    trust: 'CAUTION',
    capabilities: ['network'],
    scanned_at: '2026-09-04T00:00:00Z',
    installed_at: '2026-09-04T00:00:00Z',
    some_future_field: 'unknown-value-should-be-ignored'
  };

  const projectRegistryPath = path.join(fakeProject, '.opal', 'skills-registry.json');
  fs.writeFileSync(projectRegistryPath, JSON.stringify({
    '$schema': 'opal-project-skills-registry-v1',
    version: '0.1.0-fixture',
    updated_at: '2026-09-04',
    groups: { project: [entryWithUnknownField] }
  }, null, 2));

  const { exitCode, result, stderr } = runCli(['validate'], fakeHome, fakeProject);

  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.ok(Array.isArray(result.errors), 'validate 결과에 errors 배열이 있어야 함');
  assert.strictEqual(result.errors.length, 0,
    `[R-7] 미지 필드(some_future_field)가 있어도 validate error 0건이어야 함(스키마 교체 없이 미지 필드 무시하는 현행 동작 재확인) but got: ${JSON.stringify(result.errors)}`);
});
