#!/usr/bin/env node
//
// @module      skill-registry
// @layer       tools
// @domain      skill-management
// @description OPAL 스킬 레지스트리 CLI — opal-skills-registry.json + community-skills-registry.json을 로드하여
//              // 커맨드 매칭, 스킬 조회, 목록 표시, 유효성 검증을 제공한다.
//              v2 스키마: community 스킬의 installed 동적 계산 + fetch 정보(source_repo/license/install_command) 노출.
//              커뮤니티 스킬 설치 절차의 1층 하드 필터 — clone 디렉토리 위험 패턴 스캔(scan-risk)도 제공한다.
// @exports     CLI: match <input> | get <name> | list [--group=X] [--domain=X] | validate |
//              migrate [--dry-run] | parse-source-repo <source_repo> | scan-risk <dir>
//
// 변경이력:
//   v1.4 2026-09-03 00:45 KST: scan-risk 서브명령 신설 — 위험 패턴 10종 상수 + 오탐 억제 4규칙 +
//                              읽기 전용 디렉토리 스캔. 기존 서브명령 6종·list 출력 계약·종료 코드
//                              규약은 무수정 (105)
//   v1.3 2026-07-17 KST: 커뮤니티 스킬 관리 워크플로우 통일 (태스크 064):
//                        - resolveCommunitySkillPath() 신설 — vendor 중첩 우선 → flat basename 폴백 → null.
//                          getCommunitySkillPath()는 canonical(설치 타깃) 경로 계산 용도로 시그니처·반환 유지.
//                        - matchCommand/validate의 community installed·path 계산을 resolveCommunitySkillPath 기반으로 교체.
//                        - matchByAlias() basename(vendor 무관) 매칭 확장 + 충돌 시 {__ambiguous, candidates} 반환.
//                          matchCommand에 ambiguous 분기 응답 추가.
//                        - loadUserRegistry() 신설 + loadAllSkills()가 ~/.opal/community-skills/user-registry.json을
//                          방어적으로 병합 로드(부재/파손 시 무시, 동일 name은 사용자 항목 override).
//                        - listCommand()의 --group=community 필터가 _source==='community' 스킬 전체를 반환하도록 수정
//                          + community 스킬 항목에 installed 필드 추가.
//                        - match 출력 install_command를 clone-copy 지시 문자열로 교체 + install_method:"clone-copy" 필드 추가.
//                        - migrateCommand(dryRun) 신설 — flat→vendor 중첩 1회 이동(등재 basename 유일 매칭만 이동,
//                          미등재/충돌은 preserved 보존, 142 D-4). CLI `migrate [--dry-run]` 서브커맨드 추가.
//                        - parseSourceRepo() 신설 — `owner/repo@subdir` 파싱(`@` 미포함 시 subdir=repo).
//                          CLI `parse-source-repo <source_repo>` 서브커맨드 추가.
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
//   v1.2 2026-06-18 KST: validate 확장 — dangling error 격상 + unregistered 역방향 감지 (태스크 029):
//                        - validate():379 no-SKILL.md warning → errors 격상 ("dangling" 레이블)
//                        - validateUnregistered(cwd, registeredNames) 신규 — opal/skills/+skills/ 양쪽 스캔
//                        - validate() 소스 환경 조건부 validateUnregistered 호출 (배포 환경 false positive 방지)
//                        - validate() 반환 객체에 unregistered 키 추가
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
  // 1순위: cwd 기준 opal/core/references/ — fixture cwd 격리 지원 (테스트 환경)
  //        cwd에 소스 레이아웃이 있으면 소스 환경으로 처리한다.
  const cwdSource = path.resolve(process.cwd(), 'opal', 'core', 'references');
  if (fs.existsSync(path.join(cwdSource, 'opal-skills-registry.json'))) return cwdSource;
  // 2순위: ~/.opal/references/ — 배포 환경 (HOME 오버라이드로 테스트 격리 지원)
  const deployed = path.join(os.homedir(), '.opal', 'references');
  if (fs.existsSync(path.join(deployed, 'opal-skills-registry.json'))) return deployed;
  // 3순위: opal/core/references/ — __dirname 기준 (개발 시 폴백)
  const source = path.resolve(__dirname, '..', '..', 'core', 'references');
  if (fs.existsSync(path.join(source, 'opal-skills-registry.json'))) return source;
  return deployed; // fallback
}

// community 스킬 설치 경로 동적 계산 (P-1: paths 폐기, name에서 계산)
// canonical(vendor 중첩) 경로 — 설치 타깃 계산용 (기존 시그니처·반환 유지: 하위호환, 태스크 064)
function getCommunitySkillPath(skillName) {
  return path.join(os.homedir(), '.opal', 'community-skills', skillName, 'SKILL.md');
}

// 실제 존재 경로 해석 — vendor 우선, flat 폴백, 없으면 null (태스크 064 F-001, H-1)
function resolveCommunitySkillPath(skillName) {
  const home = os.homedir();
  const nested = path.join(home, '.opal', 'community-skills', skillName, 'SKILL.md'); // anthropics/pdf/SKILL.md
  if (fs.existsSync(nested)) return nested;
  const base = skillName.includes('/') ? skillName.split('/').pop() : skillName;
  const flat = path.join(home, '.opal', 'community-skills', base, 'SKILL.md');        // pdf/SKILL.md (레거시)
  if (fs.existsSync(flat)) return flat;
  return null;
}

// community 스킬 여부 판단 (_source 마커 기반)
function isCommunitySkill(skill) {
  return skill._source === 'community';
}

// 사용자 수동 설치 등록분 방어적 로드 (태스크 064 F-006, H-3)
// ~/.opal/community-skills/user-registry.json — install이 절대 건드리지 않는 위치.
// 부재/파손 시 null 반환 → CLI 전체 다운 방지.
function loadUserRegistry() {
  const p = path.join(os.homedir(), '.opal', 'community-skills', 'user-registry.json');
  try {
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    return null; // 파손 시 무시 — CLI 전체 다운 방지 (H-3)
  }
}

function loadAllSkills() {
  const refDir = getReferencesDir();
  const main = loadJsonFile(path.join(refDir, 'opal-skills-registry.json'));
  const community = loadJsonFile(path.join(refDir, 'community-skills-registry.json'));
  const userReg = loadUserRegistry();

  const skills = [];
  if (main) skills.push(...flattenGroups(main, 'main'));
  if (community) skills.push(...flattenGroups(community, 'community'));
  if (userReg) {
    // 사용자 항목 병합 — 동일 name은 사용자 항목 우선(override), 신규 name은 추가 (태스크 064 F-006)
    const userSkills = flattenGroups(userReg, 'community');
    for (const us of userSkills) {
      const idx = skills.findIndex(s => s.name === us.name);
      if (idx >= 0) skills[idx] = us; else skills.push(us);
    }
  }
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
  // 1순위: 정식명(vendor/skill) 또는 alias 필드 정확 매칭 (기존 계약 — 단일 반환, 하위호환)
  const exact = skills.find(s =>
    s.name.toLowerCase() === lower || (s.alias && s.alias.toLowerCase() === lower));
  if (exact) return exact;
  // 2순위: basename 매칭 (vendor 무관, 태스크 064 F-002)
  const byBase = skills.filter(s => {
    const base = s.name.includes('/') ? s.name.split('/').pop() : s.name;
    return base.toLowerCase() === lower;
  });
  if (byBase.length === 1) return byBase[0];
  if (byBase.length > 1) return { __ambiguous: true, candidates: byBase }; // 충돌 — 자동 선택 금지
  return null;
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
    // basename 충돌 — 자동 선택 금지, 후보 목록 반환 (태스크 064 F-002, H-2)
    if (skill && skill.__ambiguous) {
      return {
        found: true,
        ambiguous: true,
        alias,
        candidates: skill.candidates.map(s => ({
          name: s.name,
          source_repo: s.source_repo || null,
          license: s.license || 'Unknown',
          installed: isCommunitySkill(s) ? resolveCommunitySkillPath(s.name) !== null : true
        })),
        cleanInput
      };
    }
  }
  if (!skill) {
    skill = matchByTriggers(skills, cleanInput || input);
  }

  if (skill) {
    // community 스킬: v2 스키마 — installed 동적 계산 + fetch 정보 노출 (D-3, P-5)
    if (isCommunitySkill(skill)) {
      const skillPath = resolveCommunitySkillPath(skill.name); // vendor 우선 → flat 폴백 (태스크 064 F-001, H-1)
      const installed = skillPath !== null;
      const sourceRepo = skill.source_repo || null;
      const license = skill.license || 'Unknown';
      // npx add 제거 → clone-copy 절차 지시. source_repo가 clone 소스, 절차는 skill-manager §2/§6 (태스크 064 F-004, H-8)
      const installMethod = sourceRepo ? 'clone-copy' : null;
      const installCommand = sourceRepo ? `opal-skill-manager §설치 (clone-copy: ${sourceRepo})` : null;
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
        install_command: installCommand,
        install_method: installMethod
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
    if (options.group === 'community') {
      // community 유래 스킬 전체 반환 — _source 기반 (vendor 세분 그룹과 별개, 태스크 064)
      filtered = filtered.filter(s => s._source === 'community');
    } else {
      filtered = filtered.filter(s => s._group === options.group || s._group.startsWith(options.group + '/'));
    }
  }
  if (options.domain) {
    filtered = filtered.filter(s => s.domain === options.domain);
  }

  return filtered.map(s => {
    const item = {
      name: s.name,
      group: s._group,
      alias: s.alias,
      description: s.description,
      domain: s.domain || null
    };
    if (isCommunitySkill(s)) {
      item.installed = resolveCommunitySkillPath(s.name) !== null;
    }
    return item;
  });
}

// === Validate Command ===

/**
 * @function    validateUnregistered
 * @layer       tools
 * @domain      skill-management
 * @description 소스 레포의 스킬 폴더(opal/skills/ + skills/)를 스캔하여
 *              레지스트리에 미등록된 폴더명을 감지한다.
 *              소스 환경 전용 — 배포 환경(~/.opal/)에서는 validate()가 호출하지 않는다.
 *              fs 접근은 cwd 하위로 한정 (path traversal 없음, CWE-22).
 * @param {string}      cwd             - 프로젝트 루트 경로
 * @param {Set<string>} registeredNames - 레지스트리 등록 스킬명 집합
 * @returns {string[]} 미등록 폴더명 목록
 */
function validateUnregistered(cwd, registeredNames) {
  const srcDirs = [
    path.resolve(cwd, 'opal', 'skills'),  // opal-pilot-*, op-*, opal-*
    path.resolve(cwd, 'skills'),           // standalone (api-analyzer 등) — H-3 false positive 방지
  ];
  const unregistered = [];
  for (const dir of srcDirs) {
    if (!fs.existsSync(dir)) continue;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      if (!fs.existsSync(path.join(dir, entry.name, 'SKILL.md'))) continue;
      if (!registeredNames.has(entry.name)) unregistered.push(entry.name);
    }
  }
  return unregistered;
}

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
        // 설치 여부 정보 (warning만, error 아님) — vendor 우선 → flat 폴백 (태스크 064 F-001, H-1)
        const skillPath = resolveCommunitySkillPath(skill.name);
        if (skillPath === null) {
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
      if (!found) errors.push(`${skill.name}: dangling — no SKILL.md found at any path`);
    }
  }

  // (c) unregistered 역방향 감지 — 소스 환경 전용 (배포 환경 false positive 방지, H-4)
  const refDirIsSource = refDir.includes(path.join('opal', 'core', 'references'));
  const unregistered = [];
  if (refDirIsSource) {
    const unreg = validateUnregistered(process.cwd(), names);
    for (const n of unreg) {
      errors.push(`${n}: unregistered — folder exists but not in registry`);
      unregistered.push(n);
    }
  }

  return {
    valid: errors.length === 0,
    total: skills.length,
    groups: mainRegistry ? Object.keys(mainRegistry.groups) : [],
    communityGroups: communityRegistry ? Object.keys(communityRegistry.groups) : [],
    communitySchema: communityRegistry ? communityRegistry['$schema'] : null,
    errors,
    warnings,
    unregistered
  };
}

// === Migrate Command (태스크 064 F-001) ===

/**
 * @function    migrateCommand
 * @layer       tools
 * @domain      skill-management
 * @description flat(`community-skills/{basename}/SKILL.md`) 레이아웃을 vendor 중첩
 *              (`community-skills/{vendor}/{basename}/SKILL.md`)으로 1회 이동한다.
 *              basename이 registry 전체 스킬명 중 정확히 1개와 매칭될 때만 이동한다.
 *              미등재(0개 매칭) 또는 충돌(2개 이상 매칭)은 이동하지 않고 preserved에 기록한다
 *              (142 D-4 — 사용자 데이터 삭제·오이동 금지). 도구 자기완결(CONVENTIONS §도구 우선).
 * @param {boolean} dryRun - true면 실제 이동 없이 계획만 반환
 * @returns {{ moved: {from:string,to:string}[], preserved: {dir:string,reason:string}[],
 *             skipped: {dir:string,reason:string}[], errors: {dir:string,reason:string}[] }}
 */
function migrateCommand(dryRun) {
  const communityDir = path.join(os.homedir(), '.opal', 'community-skills');
  const moved = [];
  const preserved = [];
  const skipped = [];
  const errors = [];

  if (!fs.existsSync(communityDir)) {
    return { moved, preserved, skipped, errors };
  }
  const communityDirResolved = path.resolve(communityDir);

  // registry 전체(카탈로그+사용자 등록분) basename → 후보(name, vendor) 맵
  const skills = loadAllSkills().filter(isCommunitySkill);
  const basenameMap = new Map();
  for (const s of skills) {
    if (!s.name || !s.name.includes('/')) continue;
    const parts = s.name.split('/');
    const vendor = parts[0];
    const basename = parts[parts.length - 1];
    if (!basenameMap.has(basename)) basenameMap.set(basename, []);
    basenameMap.get(basename).push({ name: s.name, vendor });
  }

  let entries;
  try {
    entries = fs.readdirSync(communityDir, { withFileTypes: true });
  } catch (e) {
    errors.push({ dir: communityDir, reason: e.message });
    return { moved, preserved, skipped, errors };
  }

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const entryPath = path.join(communityDir, entry.name);
    const directSkillMd = path.join(entryPath, 'SKILL.md');

    if (!fs.existsSync(directSkillMd)) {
      // SKILL.md가 직접 없음 → vendor 디렉토리(이미 중첩) 또는 관련 없는 디렉토리 → skip
      skipped.push({ dir: entry.name, reason: 'no_direct_skill_md' });
      continue;
    }

    // flat 스킬 디렉토리 판정 — basename을 registry와 대조
    const basename = entry.name;
    const candidates = basenameMap.get(basename) || [];
    if (candidates.length === 0) {
      preserved.push({ dir: entry.name, reason: 'unregistered' }); // [MUST] 142 D-4
      continue;
    }
    if (candidates.length > 1) {
      preserved.push({ dir: entry.name, reason: 'basename_collision' });
      continue;
    }

    const target = candidates[0];
    const toPath = path.resolve(path.join(communityDir, target.vendor, basename));
    // path traversal 방어 (CWE-22) — community-skills/ 하위인지 검증
    if (!toPath.startsWith(communityDirResolved)) {
      errors.push({ dir: entry.name, reason: 'path_traversal_blocked' });
      continue;
    }
    if (fs.existsSync(toPath)) {
      skipped.push({ dir: entry.name, reason: 'target_exists' });
      continue;
    }

    if (dryRun) {
      moved.push({ from: entryPath, to: toPath });
      continue;
    }

    try {
      fs.mkdirSync(path.dirname(toPath), { recursive: true });
      fs.renameSync(entryPath, toPath);
      moved.push({ from: entryPath, to: toPath });
    } catch (e) {
      errors.push({ dir: entry.name, reason: e.message });
    }
  }

  return { moved, preserved, skipped, errors };
}

// === source_repo 파싱 (태스크 064 F-004, H-6) ===

/**
 * @function    parseSourceRepo
 * @description registry `source_repo` 필드(`owner/repo@subdir`)를 clone 대상으로 파싱한다.
 *              `@` 미포함 시 subdir은 repo와 동일(폴백).
 * @param {string} sourceRepo
 * @returns {{ owner: string, repo: string, subdir: string } | null}
 */
function parseSourceRepo(sourceRepo) {
  if (!sourceRepo) return null;
  const atIdx = sourceRepo.indexOf('@');
  const ownerRepo = atIdx >= 0 ? sourceRepo.slice(0, atIdx) : sourceRepo;
  const subdirRaw = atIdx >= 0 ? sourceRepo.slice(atIdx + 1) : null;
  const parts = ownerRepo.split('/');
  const owner = parts[0] || null;
  const repo = parts[1] || null;
  const subdir = subdirRaw || repo;
  return { owner, repo, subdir };
}

// === 1층 하드 필터: scan-risk (태스크 105 F-002) ===
//
// scanRiskCommand(dir)는 clone된 스킬 후보 디렉토리를 읽기 전용으로 스캔하여
// 위험 패턴 매칭 결과(hits[])와 4단 verdict(SAFE/CAUTION/RISKY/UNKNOWN)를 반환한다.
// [scanned 정의] 확장자 화이트리스트·파일 크기(1MB)·바이너리(NUL) 검사를 통과하여
// 실제로 라인 단위 패턴 매칭을 수행한 파일 수 — skip된 파일은 포함하지 않는다.

const RISK_SCAN_EXTENSIONS = new Set(['.md', '.sh', '.bash', '.zsh', '.js', '.mjs', '.cjs', '.py', '.rb', '.ts']);
const RISK_EXCLUDED_DIRS = new Set(['.git', 'node_modules', 'dist', 'build']);
const RISK_MAX_FILE_SIZE = 1024 * 1024;  // 1MB
const RISK_MAX_LINE_LENGTH = 2000;       // ReDoS·성능 방어 (H-7)
const RISK_EXCERPT_MAX = 200;            // credential 등 장문 원문 노출 방지 (PLAN §5.4)

const RISK_FIXTURE_PATH_RE = /(^|\/)(tests|test|fixtures|__fixtures__|examples)\//;
const RISK_COMMENT_LINE_RE = /^\s*(#|\/\/|\*)/;
const RISK_NEGATION_TOKENS = ['절대', '금지', '하지 마', 'never', 'do not', "don't", 'avoid', 'must not', 'should not', '無'];

// 위험 패턴 10종(RP-01~RP-10). 전건 선형(비-nested quantifier), .* / .+ ≤2회, 길이 ≤100자
// — isUnsafeRegex() 기준(:151-165)과 동일 규율 (H-7).
const RISK_PATTERNS = [
  { id: 'RP-01', severity: 'high',   capability: 'fs:destructive',      regex: /\brm\s+-[a-zA-Z]{1,4}\s+["'`]?(\/|~|\$HOME|\*)/ },
  { id: 'RP-02', severity: 'high',   capability: 'system:privilege',    regex: /(^|[;&|]\s*)sudo\b/ },
  { id: 'RP-03', severity: 'high',   capability: 'exec:remote',         regex: /\b(curl|wget)\b[^\n]{0,60}\|\s*(sudo\s+)?(sh|bash|zsh)\b/ },
  { id: 'RP-04', severity: 'high',   capability: 'secret:credential',   regex: /~\/\.(ssh\/id_(rsa|ed25519|ecdsa|dsa)|aws\/credentials|netrc|npmrc)/ },
  { id: 'RP-05', severity: 'medium', capability: 'secret:env',          regex: /\.env\b/ },
  { id: 'RP-06', severity: 'medium', capability: 'exec:dynamic',        regex: /\beval\s*["('`]/ },
  { id: 'RP-07', severity: 'medium', capability: 'obfuscation:base64',  regex: /\bbase64\s+(-d|-D|--decode)\b/ },
  { id: 'RP-08', severity: 'medium', capability: 'network:outbound',    regex: /\bcurl\b[^\n]{0,60}(-X\s*POST|--data\b|-d\s)/ },
  { id: 'RP-09', severity: 'medium', capability: 'fs:permission',       regex: /\bchmod\s+(-R\s+)?777\b/ },
  { id: 'RP-10', severity: 'medium', capability: 'system:persistence',  regex: /\b(crontab\s+-|launchctl\s+load\b|~\/Library\/LaunchAgents)/ }
];

function riskHasNegation(line) {
  const lower = line.toLowerCase();
  return RISK_NEGATION_TOKENS.some(tok => lower.includes(tok.toLowerCase()));
}

/** 코드 영역(비-md 전체, md 코드펜스 내부, md 인라인 코드 스팬)의 context 분류 — 억제-3·4. */
function riskClassifyCodeContext(line, relFile) {
  if (riskHasNegation(line)) return 'negated';
  if (RISK_COMMENT_LINE_RE.test(line)) return 'comment';
  if (RISK_FIXTURE_PATH_RE.test(relFile)) return 'fixture';
  return 'active';
}

function riskTruncateExcerpt(line) {
  return line.length > RISK_EXCERPT_MAX ? line.slice(0, RISK_EXCERPT_MAX) : line;
}

/** 백틱으로 감싼 인라인 코드 스팬의 [start,end) 구간 목록. */
function riskFindBacktickSpans(line) {
  const spans = [];
  const re = /`[^`]*`/g;
  let m;
  while ((m = re.exec(line)) !== null) {
    spans.push([m.index, m.index + m[0].length]);
  }
  return spans;
}

function riskIndexInSpans(idx, spans) {
  return spans.some(([s, e]) => idx >= s && idx < e);
}

/**
 * @function    scanRiskCommand
 * @description clone 디렉토리를 읽기 전용으로 스캔하여 위험 패턴 hits[] + 4단 verdict를 반환한다
 *              (커뮤니티 스킬 설치 절차 1층 하드 필터, 태스크 105 F-002).
 * @param {string} dir - 스캔 대상 디렉토리(clone 임시 경로)
 * @returns {{ok:boolean, verdict:string, dir:string, scanned?:number, hits?:Array, skipped?:Array, error?:string}}
 */
function scanRiskCommand(dir) {
  let realDir;
  try {
    realDir = fs.realpathSync(dir);
    if (!fs.statSync(realDir).isDirectory()) {
      return { ok: false, verdict: 'UNKNOWN', dir, error: `Not a directory: ${dir}` };
    }
  } catch (e) {
    return { ok: false, verdict: 'UNKNOWN', dir, error: `Directory not found or inaccessible: ${dir}` };
  }

  const hits = [];
  const skipped = [];
  let scanned = 0;

  const stack = [realDir];
  while (stack.length) {
    const cur = stack.pop();
    let entries;
    try {
      entries = fs.readdirSync(cur, { withFileTypes: true });
    } catch (e) {
      continue;
    }
    for (const entry of entries) {
      const abs = path.join(cur, entry.name);
      if (entry.isDirectory()) {
        if (RISK_EXCLUDED_DIRS.has(entry.name)) continue;
        stack.push(abs);
        continue;
      }
      if (!entry.isFile()) continue;

      const relFile = path.relative(realDir, abs).split(path.sep).join('/');
      const ext = path.extname(entry.name).toLowerCase();
      if (!RISK_SCAN_EXTENSIONS.has(ext)) {
        skipped.push({ file: relFile, reason: `extension not scanned: ${ext || '(none)'}` });
        continue;
      }

      let stat;
      try {
        stat = fs.statSync(abs);
      } catch (e) {
        skipped.push({ file: relFile, reason: `stat failed: ${e.message}` });
        continue;
      }
      if (stat.size > RISK_MAX_FILE_SIZE) {
        skipped.push({ file: relFile, reason: `file size ${stat.size} > ${RISK_MAX_FILE_SIZE}` });
        continue;
      }

      let buf;
      try {
        buf = fs.readFileSync(abs);
      } catch (e) {
        skipped.push({ file: relFile, reason: `read failed: ${e.message}` });
        continue;
      }
      if (buf.includes(0)) {
        skipped.push({ file: relFile, reason: 'binary file (NUL byte)' });
        continue;
      }

      scanned++;
      const isMd = ext === '.md';
      let inFence = false;
      const lines = buf.toString('utf8').split('\n');

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const lineNo = i + 1;

        if (line.length > RISK_MAX_LINE_LENGTH) {
          skipped.push({ file: relFile, reason: `line ${lineNo} length ${line.length} > ${RISK_MAX_LINE_LENGTH}` });
          continue;
        }

        if (isMd && /^\s*(```|~~~)/.test(line)) {
          inFence = !inFence;
          continue;
        }

        if (isMd && !inFence) {
          // 억제-2: 산문 라인 — 코드펜스·인라인 코드 스팬(백틱) 안쪽 매칭만 code-region 취급
          const spans = riskFindBacktickSpans(line);
          for (const pat of RISK_PATTERNS) {
            const m = pat.regex.exec(line);
            if (!m) continue;
            const context = riskIndexInSpans(m.index, spans)
              ? riskClassifyCodeContext(line, relFile)
              : 'prose';
            hits.push({
              id: pat.id, severity: pat.severity, capability: pat.capability,
              file: relFile, line: lineNo, excerpt: riskTruncateExcerpt(line), context
            });
          }
          continue;
        }

        // 코드 영역: 비-md 파일 전체 라인, 또는 md 코드펜스 내부 라인
        for (const pat of RISK_PATTERNS) {
          const m = pat.regex.exec(line);
          if (!m) continue;
          hits.push({
            id: pat.id, severity: pat.severity, capability: pat.capability,
            file: relFile, line: lineNo, excerpt: riskTruncateExcerpt(line),
            context: riskClassifyCodeContext(line, relFile)
          });
        }
      }
    }
  }

  const activeHigh = hits.some(h => h.context === 'active' && h.severity === 'high');
  const activeMedium = hits.some(h => h.context === 'active' && h.severity === 'medium');
  const verdict = activeHigh ? 'RISKY' : (activeMedium ? 'CAUTION' : 'SAFE');

  return { ok: true, verdict, dir: realDir, scanned, hits, skipped };
}

// === CLI Router ===

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command) {
    console.error('Usage: skill-registry.js <match|get|list|validate|migrate|parse-source-repo|scan-risk> [args]');
    console.error('  match <input>          Match skill from user input');
    console.error('  get <name>             Get skill metadata');
    console.error('  list [--group=X] [--domain=X]  List skills');
    console.error('  validate               Validate registries');
    console.error('  migrate [--dry-run]    flat→vendor 중첩 레이아웃 이동 (멱등)');
    console.error('  parse-source-repo <source_repo>  owner/repo@subdir 파싱');
    console.error('  scan-risk <dir>        clone 디렉토리 위험 패턴 스캔 (1층 하드 필터)');
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

    case 'migrate': {
      const dryRun = args.includes('--dry-run');
      result = migrateCommand(dryRun);
      break;
    }

    case 'parse-source-repo':
      if (!args[1]) {
        console.error('Usage: skill-registry.js parse-source-repo <source_repo>');
        process.exit(1);
      }
      result = parseSourceRepo(args[1]);
      break;

    case 'scan-risk':
      if (!args[1]) {
        console.error('Usage: skill-registry.js scan-risk <dir>');
        process.exit(1);
      }
      result = scanRiskCommand(args[1]);
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
