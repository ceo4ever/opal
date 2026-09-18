//
// @module      test-verify-bundle
// @layer       tools/test
// @domain      skill-management
// @description verify-bundle 서브커맨드 RED 테스트 — RED-first 트랙 (PLAN DEC-3, 태스크 140)
//              CLI 블랙박스 방식: node skill-registry.js verify-bundle 을 child_process 로 실행,
//              exit code + stdout JSON으로 동작 검증. mock/monkeypatch 없음, 임시 fixture(DI) 사용.
//              실 배포본(~/.opal/)은 읽지 않는다 (TEST-SCENARIO.md §Setup).
// @depends     node:test, node:assert, node:fs, node:path, node:os, node:child_process
//              (신규 패키지 0, Node 내장 모듈만 사용)
//
// TC 매핑 (TEST-SCENARIO.md S-1, PLAN DEC-3):
//   TC1 (match)     → registry canonical set = 폴더 set → ok:true, missing_source:[], unregistered:[], exit 0
//   TC2 (missing)   → registry에만 있는 엔트리 → missing_source에 해당 엔트리, exit != 0
//   TC3 (unreg)     → 폴더에만 있는 스킬 → unregistered에 해당 폴더, exit != 0
//   TC4 (ambiguous) → 같은 alias가 두 canonical을 가리킴 → ambiguous_alias에 충돌 alias, exit != 0
//
// RED mode 계약: 이 배치는 verify-bundle 서브커맨드 구현(W-4)을 하지 않는다.
// 아래 4개 테스트는 현재 skill-registry.js에 verify-bundle이 없으므로 전부 실패해야 정상이다
// (Unknown command 분기로 stdout이 단일 라인 JSON이 아니게 되거나, exit code가 기대와 어긋난다).
//
// 변경이력:
//   v1.0 2026-09-18 KST: RED-first 단위 테스트 최초 작성 (태스크 140, opal-test-agent mode:red, W-1)
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

const createdDirs = [];

/**
 * 임시 fixture 디렉토리를 생성한다: registry JSON 1개 + skills-root 폴더 1개.
 *
 * registry JSON은 실제 opal-skills-registry.json과 같은 최상위 키 구조
 * ($schema/version/updated_at/groups/changelog)를 갖는다. `groups`는
 * 그룹명 → 엔트리 배열의 객체이며, 평탄 `skills` 배열은 사용하지 않는다
 * (정본 처리기: skill-registry.js flattenGroups()).
 *
 * @param {object} opts
 * @param {Array<{name:string, alias?:string|null, group?:string}>} opts.registryEntries
 *   - registry JSON에 실릴 스킬 엔트리. `group` 생략 시 기본 그룹('opal-pilot')에 담긴다.
 *     엔트리별로 다른 group을 지정하면 2개 이상의 그룹으로 나뉜 fixture가 만들어진다.
 * @param {string[]} opts.skillFolders - skills-root 아래 실제로 만들 폴더 이름 배열
 * @returns {{ registryPath: string, skillsRoot: string, dir: string }}
 */
function makeFixture({ registryEntries, skillFolders }) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'opal-test-verify-bundle-'));
  createdDirs.push(dir);

  const skillsRoot = path.join(dir, 'skills-root');
  fs.mkdirSync(skillsRoot, { recursive: true });
  for (const name of skillFolders) {
    const skillDir = path.join(skillsRoot, name);
    fs.mkdirSync(skillDir, { recursive: true });
    fs.writeFileSync(path.join(skillDir, 'SKILL.md'), `# ${name}\n`);
  }

  const groups = {};
  for (const entry of registryEntries) {
    const group = entry.group || 'opal-pilot';
    if (!groups[group]) groups[group] = [];
    groups[group].push({
      name: entry.name,
      alias: entry.alias === undefined ? null : entry.alias,
      description: `${entry.name} fixture skill`,
      triggers: [`^${entry.name}$`],
      paths: [
        `{project}/opal/skills/${entry.name}/SKILL.md`,
        `{project}/skills/${entry.name}/SKILL.md`,
      ],
      domain: 'fixture',
      pipeline: 'FIXTURE',
    });
  }

  const registry = {
    '$schema': 'opal-skills-registry-v2',
    version: '0.0.1-fixture',
    updated_at: '2026-09-18T00:00:00+09:00',
    groups,
    changelog: [],
  };

  const registryPath = path.join(dir, 'opal-skills-registry.json');
  fs.writeFileSync(registryPath, JSON.stringify(registry, null, 2));

  return { registryPath, skillsRoot, dir };
}

/**
 * skill-registry.js verify-bundle CLI를 실행한다.
 * @param {string} registryPath
 * @param {string[]} skillsRoots
 * @returns {{ exitCode: number|null, stdout: string, stderr: string }}
 */
function runVerifyBundle(registryPath, skillsRoots) {
  const args = ['verify-bundle', `--registry=${registryPath}`];
  for (const root of skillsRoots) {
    args.push(`--skills-root=${root}`);
  }
  const result = spawnSync('node', [SKILL_REGISTRY_JS, ...args], {
    cwd: os.tmpdir(),
    encoding: 'utf8',
    timeout: 15000,
  });
  return { exitCode: result.status, stdout: result.stdout || '', stderr: result.stderr || '' };
}

/**
 * stdout이 단일 라인 JSON으로 파싱되는지 확인하고 파싱 결과를 반환한다.
 * 계약(tool-output-contract.md): 성공 exit 0 / 실패 exit != 0, stdout에 JSON 하나만 출력.
 */
function parseSingleLineJson(stdout) {
  const trimmed = stdout.trim();
  const lines = trimmed.split('\n').filter(l => l.length > 0);
  assert.equal(lines.length, 1,
    `stdout은 단일 라인이어야 한다. got ${lines.length}줄: ${JSON.stringify(lines)}`);
  return JSON.parse(lines[0]);
}

after(() => {
  for (const dir of createdDirs) {
    try {
      fs.rmSync(dir, { recursive: true, force: true });
    } catch {
      // best-effort cleanup
    }
  }
});

// ─── TC1: registry canonical set = 폴더 set → ok:true, exit 0 ───────────────

test('TC1 (match): canonical set과 폴더 set이 일치하면 ok:true, missing_source:[], unregistered:[], exit 0', () => {
  // 엔트리를 2개 이상의 그룹(opal-pilot / op-dev)에 나눠 담아 flattenGroups()가
  // 여러 그룹을 실제로 평탄화하는지 함께 고정한다.
  const { registryPath, skillsRoot } = makeFixture({
    registryEntries: [
      { name: 'skill-alpha', group: 'opal-pilot' },
      { name: 'skill-beta', group: 'op-dev' },
    ],
    skillFolders: ['skill-alpha', 'skill-beta'],
  });

  const { exitCode, stdout } = runVerifyBundle(registryPath, [skillsRoot]);
  const result = parseSingleLineJson(stdout);

  assert.equal(result.ok, true, `ok:true 기대. got ${JSON.stringify(result)}`);
  assert.deepEqual(result.missing_source, [], 'missing_source는 빈 배열이어야 한다');
  assert.deepEqual(result.unregistered, [], 'unregistered는 빈 배열이어야 한다');
  assert.equal(exitCode, 0, `exit 0 기대. got ${exitCode}`);
});

// ─── TC2: registry에만 있는 엔트리 → missing_source, exit != 0 ──────────────

test('TC2 (missing): registry에만 있는 엔트리는 missing_source에 나타나고 exit != 0', () => {
  const { registryPath, skillsRoot } = makeFixture({
    registryEntries: [{ name: 'skill-alpha' }, { name: 'skill-ghost' }],
    skillFolders: ['skill-alpha'],
  });

  const { exitCode, stdout } = runVerifyBundle(registryPath, [skillsRoot]);
  const result = parseSingleLineJson(stdout);

  assert.ok(Array.isArray(result.missing_source), 'missing_source는 배열이어야 한다');
  assert.ok(result.missing_source.includes('skill-ghost'),
    `missing_source에 skill-ghost 기대. got ${JSON.stringify(result.missing_source)}`);
  assert.notEqual(exitCode, 0, `exit != 0 기대. got ${exitCode}`);
});

// ─── TC3: 폴더에만 있는 스킬 → unregistered, exit != 0 ──────────────────────

test('TC3 (unregistered): 폴더에만 있는 스킬은 unregistered에 나타나고 exit != 0', () => {
  const { registryPath, skillsRoot } = makeFixture({
    registryEntries: [{ name: 'skill-alpha' }],
    skillFolders: ['skill-alpha', 'skill-orphan'],
  });

  const { exitCode, stdout } = runVerifyBundle(registryPath, [skillsRoot]);
  const result = parseSingleLineJson(stdout);

  assert.ok(Array.isArray(result.unregistered), 'unregistered는 배열이어야 한다');
  assert.ok(result.unregistered.includes('skill-orphan'),
    `unregistered에 skill-orphan 기대. got ${JSON.stringify(result.unregistered)}`);
  assert.notEqual(exitCode, 0, `exit != 0 기대. got ${exitCode}`);
});

// ─── TC4: 같은 alias가 두 canonical을 가리킴 → ambiguous_alias, exit != 0 ───

test('TC4 (ambiguous): 같은 alias가 두 canonical을 가리키면 ambiguous_alias에 충돌 alias가 나타나고 exit != 0', () => {
  const { registryPath, skillsRoot } = makeFixture({
    registryEntries: [
      { name: 'skill-alpha', alias: 'shared-alias' },
      { name: 'skill-beta', alias: 'shared-alias' },
    ],
    skillFolders: ['skill-alpha', 'skill-beta'],
  });

  const { exitCode, stdout } = runVerifyBundle(registryPath, [skillsRoot]);
  const result = parseSingleLineJson(stdout);

  assert.ok(Array.isArray(result.ambiguous_alias), 'ambiguous_alias는 배열이어야 한다');
  assert.ok(result.ambiguous_alias.includes('shared-alias'),
    `ambiguous_alias에 shared-alias 기대. got ${JSON.stringify(result.ambiguous_alias)}`);
  assert.notEqual(exitCode, 0, `exit != 0 기대. got ${exitCode}`);
});
