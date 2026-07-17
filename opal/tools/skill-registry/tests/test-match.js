//
// @module      test-match
// @layer       tools/test
// @domain      skill-management
// @task        064
// @description matchByAlias() basename 매칭·정식명 하위호환·ambiguous 충돌 정책(F-002) +
//              user-registry.json 병합 로드 방어성(F-006) + match 출력 clone-copy 전환·
//              source_repo 파싱(F-004) 단위 테스트 — RED-first 트랙 (태스크 064)
//              CLI 블랙박스 방식: node skill-registry.js <match|list|parse-source-repo> 를
//              child_process 로 실행, exit code + stdout JSON으로 동작 검증.
//              mock/monkeypatch 없음, 실제 fs 위 합성 fixture(HOME 오버라이드) 사용.
// @depends     node:test, node:assert, node:fs, node:path, node:os, node:child_process
//              (신규 패키지 0, Node 내장 모듈만 사용)
// @scenarios   TEST-SCENARIO.md §3 S-5(F-2), S-6(F-6), S-7(F-4)
//
// TC 매핑 (TEST-SCENARIO.md §3, §4 AC 매핑 표):
//   [T201/L1-F2] → S-5: `//pdf 문서 만들어줘` → basename 매칭 + cleanInput 추출
//   [T202/L1-F2] → S-5: `//brainstorming` → vendor 생략 basename 매칭
//   [T203/L1-F2] → S-5: `//anthropics/pdf` → 정식명 정확 매칭(하위호환, 단일 반환)
//   [T204/L1-F2] → S-5: basename 충돌(anthropics/pdf ↔ vendorx/pdf) → ambiguous:true + candidates 2건
//   [T401/L1-F4] → S-7: match 출력 install_method:"clone-copy" + install_command npx 문구 0
//   [T402/L1-F4] → S-7: source_repo `owner/repo@subdir` 파싱 3케이스
//                       (anthropics/skills@pdf / obra/superpowers@brainstorming / `@` 미포함 폴백)
//                       — 공개 인터페이스 부재 상태이므로 CLI 서브커맨드
//                       `parse-source-repo <source_repo>` 를 기대 인터페이스로 가정하여 RED 확인
//   [T601/L1-F6] → S-6: user-registry.json 부재(기존 동작 동일) / 정상(override+추가 병합)
//   [T602/L1-F6] → S-6: user-registry.json 파손 → CLI 다운 없이 무시(exit 0, 정상 응답)
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
 * 배포 환경(모사)을 위한 fixture를 생성한다.
 * - fakeHome/.opal/references/  : opal-skills-registry.json(빈 stub) + community-skills-registry.json(catalog)
 * - fakeHome/.opal/community-skills/ : user-registry.json (옵션, 상태에 따라 부재/정상/파손)
 *
 * getReferencesDir()의 3단계 폴백(1.cwd소스 2.HOME 배포 3.__dirname기준 소스) 중
 * 2번(HOME 배포)이 선택되도록 opal-skills-registry.json stub을 반드시 함께 써준다.
 * (stub이 없으면 3번 폴백이 실제 프로젝트 opal/core/references/를 가리켜 fixture가 무의미해진다.)
 *
 * @param {object} opts
 * @param {object} opts.communityGroups   - community-skills-registry.json groups 객체
 * @param {'absent'|'valid'|'corrupt'|object} [opts.userRegistry] - user-registry.json 상태
 * @returns {{ dir: string, fakeHome: string, communityDir: string, cleanup: () => void }}
 */
function makeMatchFixture({ communityGroups, userRegistry = 'absent' }) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-test-match-'));
  const fakeHome = path.join(dir, 'fakehome');
  const refDir = path.join(fakeHome, '.opal', 'references');
  const communityDir = path.join(fakeHome, '.opal', 'community-skills');
  fs.mkdirSync(refDir, { recursive: true });
  fs.mkdirSync(communityDir, { recursive: true });

  // main registry stub — getReferencesDir()가 배포 경로를 선택하도록 존재만 시킴
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
    schema_notes: 'fixture — test-match.js',
    groups: communityGroups
  };
  fs.writeFileSync(path.join(refDir, 'community-skills-registry.json'), JSON.stringify(communityRegistry, null, 2));

  if (userRegistry === 'valid') {
    const userReg = {
      '$schema': 'opal-community-skills-registry-v2.1',
      version: '2.1.0-user',
      updated_at: '2026-07-17',
      groups: {
        // 기존 name override — 원본 description을 사용자 값으로 덮어씀
        obra: [
          {
            name: 'obra/brainstorming', alias: null,
            description: 'USER OVERRIDE', triggers: ['(?i)(brainstorm|브레인스토밍)'],
            source_repo: 'obra/superpowers@brainstorming', commit_sha: 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef',
            license: 'MIT'
          }
        ],
        // 신규 name 추가
        myvendor: [
          {
            name: 'myvendor/custom-skill', alias: null,
            description: 'user registered custom skill', triggers: ['(?i)(custom\\s*skill)'],
            source_repo: 'myvendor/myrepo@custom-skill', commit_sha: null,
            license: 'MIT'
          }
        ]
      }
    };
    fs.writeFileSync(path.join(communityDir, 'user-registry.json'), JSON.stringify(userReg, null, 2));
  } else if (userRegistry === 'corrupt') {
    fs.writeFileSync(path.join(communityDir, 'user-registry.json'), '{invalid json');
  }
  // 'absent' → 파일 미생성

  function cleanup() {
    fs.rmSync(dir, { recursive: true, force: true });
  }

  return { dir, fakeHome, communityDir, cleanup };
}

/**
 * skill-registry.js CLI 를 실행한다 (HOME 오버라이드로 fixture 격리).
 * @param {string[]} args        - ['match', '//pdf', ...] 형태
 * @param {string} fakeHome      - HOME 오버라이드 값
 * @param {string} [cwd]         - 프로세스 cwd (기본: os.tmpdir())
 * @returns {{ exitCode: number, stdout: string, stderr: string, result: object|null }}
 */
function runCli(args, fakeHome, cwd) {
  const env = { ...process.env, HOME: fakeHome };
  const result = spawnSync('node', [SKILL_REGISTRY_JS, ...args], {
    cwd: cwd || os.tmpdir(),
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

const cleanupFns = [];
after(() => {
  for (const fn of cleanupFns) {
    try { fn(); } catch (_) { /* ignore */ }
  }
});

// ─── 공용 catalog fixture (S-5/S-7 기본, 충돌 없음) ──────────────────────────

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

// 충돌 fixture: basename "pdf"가 anthropics/pdf ↔ vendorx/pdf 2벤더에 존재
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

// ─── [T201/L1-F2] //pdf 문서 만들어줘 → basename 매칭 + cleanInput (S-5) ─────

test('[T201/L1-F2] `//pdf 문서 만들어줘` → anthropics/pdf basename 매칭 + cleanInput 추출', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//pdf', '문서', '만들어줘'], fakeHome);

  // [RED expect] 현행 matchByAlias는 정식명/alias 정확 비교만 지원 — basename("pdf") 매칭 없음.
  // 정식명이 아닌 "pdf" alias는 matchByAlias에서 실패하고, cleanInput("문서 만들어줘")에는
  // "pdf" 키워드가 없어 trigger 폴백도 실패한다 → found:false 로 귀결되어 아래 assert가 FAIL한다.
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.found, true,
    `[RED expect] found should be true (basename 매칭) but got ${result.found}. result: ${JSON.stringify(result)}`);
  assert.strictEqual(result.name, 'anthropics/pdf',
    `[RED expect] name should be "anthropics/pdf" but got ${result && result.name}`);
  assert.strictEqual(result.cleanInput, '문서 만들어줘',
    `[RED expect] cleanInput should be "문서 만들어줘" but got ${result && result.cleanInput}`);
});

// ─── [T202/L1-F2] //brainstorming (vendor 생략) → basename 매칭 (S-5) ───────

test('[T202/L1-F2] `//brainstorming` → obra/brainstorming basename 매칭 (vendor 생략)', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//brainstorming'], fakeHome);

  // [RED expect] alias "brainstorming" != 정식명 "obra/brainstorming" → matchByAlias 실패.
  // cleanInput은 빈 문자열이 되어 matchByTriggers(cleanInput || input)가 원본 입력("//brainstorming")으로
  // 폴백하는데, 이 경우 trigger 정규식이 우연히 매칭될 수 있어 found:true가 나올 수도 있으나
  // basename 전용 매칭 경로(정식 계약)는 여전히 부재하다. 계약 확인을 위해 name을 직접 검증한다.
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.found, true,
    `[RED expect] found should be true but got ${result.found}. result: ${JSON.stringify(result)}`);
  assert.strictEqual(result.name, 'obra/brainstorming',
    `[RED expect] name should be "obra/brainstorming" but got ${result && result.name}`);
  // basename 매칭이 정식 구현되면 cleanInput은 "" (alias 전량 소비)여야 한다.
  assert.strictEqual(result.cleanInput, '',
    `[RED expect] cleanInput should be "" (alias consumed whole input) but got "${result && result.cleanInput}"`);
});

// ─── [T203/L1-F2] //anthropics/pdf → 정식명 정확 매칭 (하위호환, 단일 반환) ──

test('[T203/L1-F2] `//anthropics/pdf` 정식명 정확 매칭 → 단일 반환 (하위호환)', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//anthropics/pdf'], fakeHome);

  // 정식명 정확 매칭은 현행 코드에서도 통과 가능(하위호환 회귀 가드) — RED 파일 내 baseline 케이스.
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.found, true, `found should be true. result: ${JSON.stringify(result)}`);
  assert.strictEqual(result.name, 'anthropics/pdf', `name should be "anthropics/pdf"`);
  assert.notStrictEqual(result.ambiguous, true, '정식명 단일 매칭은 ambiguous가 아니어야 함');
});

// ─── [T204/L1-F2] basename 충돌 → ambiguous:true + candidates 2건 (S-5) ─────

test('[T204/L1-F2] basename 충돌(anthropics/pdf ↔ vendorx/pdf) → ambiguous + candidates 2건', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: COLLISION_CATALOG });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//pdf'], fakeHome);

  // [RED expect] 현행 matchByAlias는 ambiguous 센티넬을 반환하지 않는다.
  // alias "pdf"는 정식명 정확 매칭에 실패하고, cleanInput=""이므로 matchByTriggers가
  // 원본 입력("//pdf")으로 폴백 → trigger 정규식(pdf)에 우연히 매칭되어 단일 skill이
  // 조용히 선택될 수 있다(어느 쪽이 선택될지는 registry groups 순회 순서에 의존) → ambiguous 필드 부재로 FAIL.
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.ambiguous, true,
    `[RED expect] ambiguous should be true but got ${result.ambiguous}. result: ${JSON.stringify(result)}`);
  assert.ok(Array.isArray(result.candidates),
    `[RED expect] candidates should be an array but got ${JSON.stringify(result && result.candidates)}`);
  assert.strictEqual(result.candidates && result.candidates.length, 2,
    `[RED expect] candidates.length should be 2 but got ${result.candidates && result.candidates.length}`);
});

// ─── [T401/L1-F4] match 출력 install_method:"clone-copy" + npx 문구 0 (S-7) ─

test('[T401/L1-F4] match 출력 install_method:"clone-copy" + install_command에 npx 문구 없음', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);

  const { result } = runCli(['match', '//anthropics/pdf'], fakeHome);

  // [RED expect] 현행 install_command = `npx skills add ${sourceRepo}` (npx 문구 포함),
  // install_method 필드 자체가 부재 → 아래 두 assert 모두 FAIL한다.
  assert.ok(result !== null, 'stdout should be valid JSON');
  assert.strictEqual(result.install_method, 'clone-copy',
    `[RED expect] install_method should be "clone-copy" but got ${result.install_method}`);
  const installCommandStr = String(result.install_command || '');
  assert.ok(!installCommandStr.toLowerCase().includes('npx'),
    `[RED expect] install_command should not contain "npx" but got "${installCommandStr}"`);
});

// ─── [T402/L1-F4] source_repo `owner/repo@subdir` 파싱 3케이스 (S-7) ────────
//
// PLAN §3.4.2(b)는 clone-copy 절차(파싱 포함)를 opal-skill-manager SKILL.md 수행 절차로
// 기술하며, skill-registry.js에는 파싱 전용 공개 함수/서브커맨드가 아직 정의되어 있지 않다.
// 공개 인터페이스로만 검증하기 위해 CLI 서브커맨드 `parse-source-repo <source_repo>`가
// 향후 추가될 공개 인터페이스라고 가정하고 호출한다 — 현재는 unknown command로 처리되어
// exit 1을 반환하므로 아래 각 케이스가 RED로 확인된다. 실제 구현 시 서브커맨드명은
// GREEN 단계 설계자가 재조정할 수 있다(본 파일은 계약 확정 근거가 아니라 RED 증거 목적).

function assertParseSourceRepoCase(t, fakeHome, sourceRepo, expected) {
  const { result, exitCode, stderr } = runCli(['parse-source-repo', sourceRepo], fakeHome);

  // [RED expect] 현행 CLI는 'parse-source-repo'를 인식하지 못해 default 분기로 빠져
  // `Unknown command: parse-source-repo` 를 stderr에 출력하고 exit 1 반환 → JSON 파싱 실패(null).
  assert.strictEqual(exitCode, 0,
    `[RED expect][${sourceRepo}] exitCode should be 0 but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(result !== null,
    `[RED expect][${sourceRepo}] stdout should be valid JSON but was not. stderr: ${stderr}`);
  if (result) {
    assert.strictEqual(result.owner, expected.owner, `[${sourceRepo}] owner mismatch`);
    assert.strictEqual(result.repo, expected.repo, `[${sourceRepo}] repo mismatch`);
    assert.strictEqual(result.subdir, expected.subdir, `[${sourceRepo}] subdir mismatch`);
  }
}

test('[T402/L1-F4] source_repo 파싱: anthropics/skills@pdf → (anthropics, skills, pdf)', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);
  assertParseSourceRepoCase(null, fakeHome, 'anthropics/skills@pdf',
    { owner: 'anthropics', repo: 'skills', subdir: 'pdf' });
});

test('[T402/L1-F4] source_repo 파싱: obra/superpowers@brainstorming → (obra, superpowers, brainstorming)', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);
  assertParseSourceRepoCase(null, fakeHome, 'obra/superpowers@brainstorming',
    { owner: 'obra', repo: 'superpowers', subdir: 'brainstorming' });
});

test('[T402/L1-F4] source_repo 파싱: `@` 미포함 → subdir=repo 폴백 (myorg/myrepo)', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG });
  cleanupFns.push(cleanup);
  assertParseSourceRepoCase(null, fakeHome, 'myorg/myrepo',
    { owner: 'myorg', repo: 'myrepo', subdir: 'myrepo' });
});

// ─── [T601/L1-F6] user-registry 부재 → 기존 동작 동일 (baseline, S-6) ───────

test('[T601/L1-F6] user-registry.json 부재 → 기존 응답과 동일 (RED — --group=community 필터 자체 미동작 확인 포함)', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG, userRegistry: 'absent' });
  cleanupFns.push(cleanup);

  const { exitCode, result } = runCli(['list', '--group=community'], fakeHome);

  // [RED expect] 현행 listCommand()의 `--group=` 필터는 s._group(벤더명, 예:"anthropics")만 비교하며
  // "community"라는 가상 그룹명과 매칭되지 않는다(_source 기반 필터 부재) → 실측 결과 항상 빈 배열([]).
  // TASK.md/TEST-SCENARIO.md가 `list --group=community`를 명시적 검증 커맨드로 지정하므로,
  // 이 필터 동작 자체도 F-6(및 F-1 회귀, S-4) 구현 범위에 포함되어야 함을 여기서 RED로 확인한다.
  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}`);
  assert.ok(Array.isArray(result), 'list 결과는 배열이어야 함');
  const names = result.map(s => s.name);
  assert.ok(names.includes('obra/brainstorming'),
    `[RED expect] obra/brainstorming should be listed via --group=community. got: ${JSON.stringify(names)}`);
  assert.ok(!names.includes('myvendor/custom-skill'), 'user-registry 부재 시 사용자 등록분은 존재하지 않아야 함');
});

// ─── [T601/L1-F6] user-registry 정상 → override + 신규 추가 병합 (S-6) ──────

test('[T601/L1-F6] user-registry.json 정상 → 동일 name override + 신규 name 추가 병합', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG, userRegistry: 'valid' });
  cleanupFns.push(cleanup);

  const { exitCode, result } = runCli(['list', '--group=community'], fakeHome);

  // [RED expect] 현행 loadAllSkills()는 user-registry.json을 전혀 읽지 않는다.
  // → myvendor/custom-skill이 목록에 없고, obra/brainstorming의 description도 원본 그대로다.
  assert.strictEqual(exitCode, 0, `exit code should be 0 but got ${exitCode}`);
  assert.ok(Array.isArray(result), 'list 결과는 배열이어야 함');

  const custom = result.find(s => s.name === 'myvendor/custom-skill');
  assert.ok(custom,
    `[RED expect] user-registry 신규 name(myvendor/custom-skill)이 병합되어야 함. got: ${JSON.stringify(result.map(s => s.name))}`);

  const brainstorming = result.find(s => s.name === 'obra/brainstorming');
  assert.ok(brainstorming, 'obra/brainstorming은 카탈로그에 존재해야 함');
  assert.strictEqual(brainstorming.description, 'USER OVERRIDE',
    `[RED expect] user-registry override가 반영되어야 함(description="USER OVERRIDE") but got "${brainstorming.description}"`);
});

// ─── [T602/L1-F6] user-registry 파손 → CLI 다운 없이 무시 (defensive, S-6) ──

test('[T602/L1-F6] user-registry.json 파손 → CLI 다운 없이 무시, exit 0 정상 응답', () => {
  const { fakeHome, cleanup } = makeMatchFixture({ communityGroups: BASE_CATALOG, userRegistry: 'corrupt' });
  cleanupFns.push(cleanup);

  const { exitCode, result, stderr } = runCli(['list', '--group=community'], fakeHome);

  // 방어적 요구사항: 파손된 user-registry.json이 있어도 CLI가 예외로 죽으면 안 된다(H-3).
  // 현행 코드는 user-registry.json을 아예 읽지 않으므로 이 케이스는 이미 통과 가능(회귀 가드).
  // GREEN 구현 후에도 loadUserRegistry()의 try/catch가 파손 JSON을 무시해야 이 assert가 유지된다.
  assert.strictEqual(exitCode, 0,
    `user-registry 파손 시에도 exit 0 이어야 함(CLI 다운 금지) but got ${exitCode}. stderr: ${stderr}`);
  assert.ok(Array.isArray(result), `stdout은 여전히 유효한 JSON 배열이어야 함. got: ${JSON.stringify(result)}`);
});
