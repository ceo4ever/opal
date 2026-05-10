#!/usr/bin/env node
//
// @module      skill-registry
// @layer       tools
// @domain      skill-management
// @description OPAL 스킬 레지스트리 CLI — opal-skills-registry.json + community-skills-registry.json을 로드하여
//              // 커맨드 매칭, 스킬 조회, 목록 표시, 유효성 검증을 제공한다.
//              v2 스키마: community 스킬의 installed 동적 계산 + fetch 정보(source_repo/license/install_command) 노출.
// @exports     CLI: match <input> | get <name> | list [--group=X] [--domain=X] | validate
//
// 변경이력:
//   v1.0 2026-05-10 17:00 KST: 초기 작성 시점 명시 (헤더 신설 — 142). community 스킬 v2 스키마 지원 추가:
//                              - getCommunitySkillPath / isCommunitySkill 헬퍼
//                              - loadAllSkills()에서 community 항목에 _source: 'community' 마커 부착
//                              - matchCommand 응답에 installed/source_repo/license/install_command 필드 추가 (미설치 시 path: null)
//                              - validate가 v2 스키마 인식 (paths 부재 정상, source_repo null은 warning)
//   v1.1 2026-05-10 21:00 KST: ReDoS 휴리스틱 + 입력 길이 제한 256자 + path 정규화 (144):
//                              - isUnsafeRegex() 함수 신설 (MAX_PATTERN_LENGTH=100 / MAX_DOTSTAR_COUNT>2 / nested quantifier)
//                              - matchByTriggers() 입력 길이 제한 + ReDoS 사전 검사
//                              - resolveFirstPath() path.resolve + homedir/cwd 하위 검증 (CWE-22)
//                              - validate()에 ReDoS 분석 warning 추가 + v2.1 스키마 인식
//
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// === Data Loading ===

function loadJsonFile(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(raw);
}

function flattenGroups(registry, source) {
  if (!registry || !registry.groups) return [];
  const skills = [];
  for (const [group, items] of Object.entries(registry.groups)) {
    if (Array.isArray(items)) {
      items.forEach(s => skills.push({ ...s, _group: group, _source: source || 'main' }));
    } else if (typeof items === 'object') {
      // nested groups (community)
      for (const [subgroup, subItems] of Object.entries(items)) {
        if (Array.isArray(subItems)) {
          subItems.forEach(s => skills.push({ ...s, _group: `${group}/${subgroup}`, _source: source || 'main' }));
        }
      }
    }
  }
  return skills;
}

function getReferencesDir() {
  // 배포 후: ~/.opal/references/
  const deployed = path.join(os.homedir(), '.opal', 'references');
  if (fs.existsSync(path.join(deployed, 'opal-skills-registry.json'))) return deployed;
  // 소스: opal/core/references/ (개발 시)
  const source = path.resolve(__dirname, '..', '..', 'core', 'references');
  if (fs.existsSync(path.join(source, 'opal-skills-registry.json'))) return source;
  return deployed; // fallback
}

// community 스킬 설치 경로 동적 계산 (P-1: paths 폐기, name에서 계산)
function getCommunitySkillPath(skillName) {
  return path.join(os.homedir(), '.opal', 'community-skills', skillName, 'SKILL.md');
}

// community 스킬 여부 판단 (_source 마커 기반)
function isCommunitySkill(skill) {
  return skill._source === 'community';
}

function loadAllSkills() {
  const refDir = getReferencesDir();
  const main = loadJsonFile(path.join(refDir, 'opal-skills-registry.json'));
  const community = loadJsonFile(path.join(refDir, 'community-skills-registry.json'));

  const skills = [];
  if (main) skills.push(...flattenGroups(main, 'main'));
  if (community) skills.push(...flattenGroups(community, 'community'));
  return skills;
}

// === ReDoS 방어 (GC-004) ===

const MAX_INPUT_LENGTH = 256;    // 입력 길이 제한
const MAX_PATTERN_LENGTH = 100;  // 패턴 길이 임계값
const MAX_DOTSTAR_COUNT = 2;     // .* / .+ 발생 횟수 임계값 — 3회 이상(> 2)만 reject

function isUnsafeRegex(pattern) {
  if (pattern.length > MAX_PATTERN_LENGTH) {
    return { unsafe: true, reason: `pattern length ${pattern.length} > ${MAX_PATTERN_LENGTH}` };
  }
  // .* 또는 .+ 발생 횟수 — 3회 이상(> MAX_DOTSTAR_COUNT)만 reject
  const dotStarCount = (pattern.match(/\.[*+]/g) || []).length;
  if (dotStarCount > MAX_DOTSTAR_COUNT) {
    return { unsafe: true, reason: `.* / .+ count ${dotStarCount} > ${MAX_DOTSTAR_COUNT} (catastrophic backtracking 위험)` };
  }
  // nested quantifier: (xxx+)+ / (xxx*)* / (xxx+)* 류
  if (/\([^)]*[+*]\)[+*]/.test(pattern)) {
    return { unsafe: true, reason: 'nested quantifier detected' };
  }
  return { unsafe: false };
}

// === Match Command ===

function extractAlias(input) {
  const match = input.match(/\/\/(\S+)/);
  if (match) {
    const alias = match[1];
    const cleanInput = input.replace(/\/\/\S+/, '').trim();
    return { alias, cleanInput };
  }
  return { alias: null, cleanInput: input.trim() };
}

function matchByAlias(skills, alias) {
  const lower = alias.toLowerCase();
  return skills.find(s =>
    s.name.toLowerCase() === lower ||
    (s.alias && s.alias.toLowerCase() === lower)
  ) || null;
}

function matchByTriggers(skills, input) {
  // 입력 길이 제한 — 256자 초과 시 매칭 skip (ReDoS 방어)
  if (input.length > MAX_INPUT_LENGTH) {
    return null;
  }
  for (const skill of skills) {
    if (!skill.triggers) continue;
    for (const pattern of skill.triggers) {
      try {
        let flags = '';
        let pat = pattern;
        if (pat.startsWith('(?i)')) {
          flags = 'i';
          pat = pat.slice(4);
        }
        // ReDoS 휴리스틱 사전 검사 — 위험 패턴은 skip
        const safety = isUnsafeRegex(pat);
        if (safety.unsafe) continue;
        const regex = new RegExp(pat, flags);
        if (regex.test(input)) {
          return skill;
        }
      } catch (e) {
        // invalid regex, skip
      }
    }
  }
  return null;
}

function resolveFirstPath(paths) {
  if (!paths) return null;
  const homeDir = os.homedir();
  const cwd = process.cwd();
  for (const p of paths) {
    let resolved = p
      .replace(/^~/, homeDir)
      .replace(/\{project\}/g, cwd);
    // path.resolve로 정규화 + homedir/cwd 하위 검증 (CWE-22 path traversal 방어)
    resolved = path.resolve(resolved);
    if (!resolved.startsWith(homeDir) && !resolved.startsWith(cwd)) {
      // homedir 또는 cwd 하위가 아니면 skip
      continue;
    }
    if (fs.existsSync(resolved)) {
      return resolved;
    }
  }
  // 폴백: 마지막 path (정규화 적용)
  if (paths.length === 0) return null;
  const fallback = paths[paths.length - 1]
    .replace(/^~/, homeDir)
    .replace(/\{project\}/g, cwd);
  return path.resolve(fallback);
}

function matchCommand(input) {
  const skills = loadAllSkills();
  const { alias, cleanInput } = extractAlias(input);

  let skill = null;
  if (alias) {
    skill = matchByAlias(skills, alias);
  }
  if (!skill) {
    skill = matchByTriggers(skills, cleanInput || input);
  }

  if (skill) {
    // community 스킬: v2 스키마 — installed 동적 계산 + fetch 정보 노출 (D-3, P-5)
    if (isCommunitySkill(skill)) {
      const skillPath = getCommunitySkillPath(skill.name);
      const installed = fs.existsSync(skillPath);
      const sourceRepo = skill.source_repo || null;
      const license = skill.license || 'Unknown';
      const installCommand = sourceRepo ? `npx skills add ${sourceRepo}` : null;
      return {
        found: true,
        name: skill.name,
        group: skill._group,
        alias: skill.alias,
        description: skill.description,
        path: installed ? skillPath : null,  // 미설치 시 null (D-3)
        domain: skill.domain || null,
        cleanInput,
        // community 전용 필드 (P-5)
        installed,
        source_repo: sourceRepo,
        license,
        install_command: installCommand
      };
    }

    // main(opal) 스킬: 기존 응답 형식 유지 (호환성 보장)
    return {
      found: true,
      name: skill.name,
      group: skill._group,
      alias: skill.alias,
      description: skill.description,
      path: resolveFirstPath(skill.paths),
      domain: skill.domain || null,
      cleanInput
    };
  }
  return { found: false, input };
}

// === Get Command ===

function getCommand(name) {
  const skills = loadAllSkills();
  const lower = name.toLowerCase();
  const skill = skills.find(s =>
    s.name === name ||
    s.name.toLowerCase() === lower ||
    (s.alias && s.alias.toLowerCase() === lower)
  );
  if (skill) {
    const { _group, _source, ...rest } = skill;
    return { ...rest, group: _group };
  }
  return { error: `Skill not found: ${name}` };
}

// === List Command ===

function listCommand(options) {
  const skills = loadAllSkills();
  let filtered = skills;

  if (options.group) {
    filtered = filtered.filter(s => s._group === options.group || s._group.startsWith(options.group + '/'));
  }
  if (options.domain) {
    filtered = filtered.filter(s => s.domain === options.domain);
  }

  return filtered.map(s => ({
    name: s.name,
    group: s._group,
    alias: s.alias,
    description: s.description,
    domain: s.domain || null
  }));
}

// === Validate Command ===

function validate() {
  const errors = [];
  const warnings = [];

  const refDir = getReferencesDir();
  const mainPath = path.join(refDir, 'opal-skills-registry.json');
  const communityPath = path.join(refDir, 'community-skills-registry.json');

  let mainRegistry, communityRegistry;
  try {
    mainRegistry = loadJsonFile(mainPath);
    if (!mainRegistry) errors.push('opal-skills-registry.json not found');
  } catch (e) {
    errors.push(`opal-skills-registry.json parse error: ${e.message}`);
  }

  try {
    communityRegistry = loadJsonFile(communityPath);
    if (!communityRegistry) warnings.push('community-skills-registry.json not found (optional)');
  } catch (e) {
    errors.push(`community-skills-registry.json parse error: ${e.message}`);
  }

  // community registry 스키마 버전 확인 (v2 + v2.1 모두 인식)
  const communitySchema = communityRegistry && communityRegistry['$schema'];
  const isV2Community = communitySchema === 'opal-community-skills-registry-v2' ||
                        communitySchema === 'opal-community-skills-registry-v2.1';
  if (communityRegistry && !isV2Community) {
    warnings.push('community-skills-registry.json: v1 스키마 — v2 마이그레이션 권장 (paths → source_repo/license)');
  }

  const skills = loadAllSkills();
  const names = new Set();
  const aliases = new Set();

  for (const skill of skills) {
    if (!skill.name) errors.push('Skill missing "name" field');

    // community v2 스킬: paths 부재 정상 — source_repo/license 필드 검증
    if (isCommunitySkill(skill)) {
      if (isV2Community) {
        // v2: paths 없어도 OK, source_repo null이면 warning
        if (!skill.source_repo) {
          warnings.push(`${skill.name}: source_repo 미정 — 수동 설치 안내 필요`);
        }
        if (!skill.license || skill.license === 'Unknown') {
          warnings.push(`${skill.name}: license Unknown — 사용자 동의 prompt에 "라이선스 미확인" 표시`);
        }
        // 설치 여부 정보 (warning만, error 아님)
        const skillPath = getCommunitySkillPath(skill.name);
        if (!fs.existsSync(skillPath)) {
          // 미설치 상태는 정상 (신규 사용자 기본 상태)
        }
      } else {
        // v1: paths 필드 필수
        if (!skill.paths || !Array.isArray(skill.paths)) {
          errors.push(`${skill.name}: missing "paths" array (v1 스키마)`);
        }
      }
    } else {
      // main(opal) 스킬: paths 필드 필수
      if (!skill.paths || !Array.isArray(skill.paths)) {
        errors.push(`${skill.name}: missing "paths" array`);
      }
    }

    // name uniqueness
    if (names.has(skill.name)) errors.push(`Duplicate name: ${skill.name}`);
    names.add(skill.name);

    // alias uniqueness
    if (skill.alias) {
      if (aliases.has(skill.alias)) errors.push(`Duplicate alias: ${skill.alias}`);
      aliases.add(skill.alias);
    }

    // regex compilation test + ReDoS 휴리스틱 분석
    if (skill.triggers) {
      for (const pattern of skill.triggers) {
        try {
          let pat = pattern;
          let flags = '';
          if (pat.startsWith('(?i)')) { flags = 'i'; pat = pat.slice(4); }
          new RegExp(pat, flags);
          // ReDoS 안전성 분석
          const safety = isUnsafeRegex(pat);
          if (safety.unsafe) {
            warnings.push(`${skill.name}: trigger ReDoS 위험 — ${safety.reason} (pattern: ${pattern})`);
          }
        } catch (e) {
          errors.push(`${skill.name}: invalid regex "${pattern}": ${e.message}`);
        }
      }
    }

    // main 스킬 path existence check (community v2는 동적 계산이므로 생략)
    if (!isCommunitySkill(skill) && skill.paths) {
      let found = false;
      for (const p of skill.paths) {
        const resolved = p.replace(/^~/, os.homedir()).replace(/\{project\}/g, process.cwd());
        if (fs.existsSync(resolved)) { found = true; break; }
      }
      if (!found) warnings.push(`${skill.name}: no SKILL.md found at any path`);
    }
  }

  return {
    valid: errors.length === 0,
    total: skills.length,
    groups: mainRegistry ? Object.keys(mainRegistry.groups) : [],
    communityGroups: communityRegistry ? Object.keys(communityRegistry.groups) : [],
    communitySchema: communityRegistry ? communityRegistry['$schema'] : null,
    errors,
    warnings
  };
}

// === CLI Router ===

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command) {
    console.error('Usage: skill-registry.js <match|get|list|validate> [args]');
    console.error('  match <input>          Match skill from user input');
    console.error('  get <name>             Get skill metadata');
    console.error('  list [--group=X] [--domain=X]  List skills');
    console.error('  validate               Validate registries');
    process.exit(1);
  }

  let result;

  switch (command) {
    case 'match':
      if (!args[1]) {
        console.error('Usage: skill-registry.js match <input>');
        process.exit(1);
      }
      result = matchCommand(args.slice(1).join(' '));
      break;

    case 'get':
      if (!args[1]) {
        console.error('Usage: skill-registry.js get <name>');
        process.exit(1);
      }
      result = getCommand(args[1]);
      break;

    case 'list': {
      const options = {};
      for (let i = 1; i < args.length; i++) {
        if (args[i].startsWith('--group=')) options.group = args[i].split('=')[1];
        if (args[i].startsWith('--domain=')) options.domain = args[i].split('=')[1];
      }
      result = listCommand(options);
      break;
    }

    case 'validate':
      result = validate();
      break;

    default:
      console.error(`Unknown command: ${command}`);
      process.exit(1);
  }

  console.log(JSON.stringify(result, null, 2));
  if (result.error || (result.valid === false)) {
    process.exit(1);
  }
}

main();
