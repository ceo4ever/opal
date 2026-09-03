---
type: concept
title: 커뮤니티 스킬 사용자 레지스트리 — install 배포 경계 격리
tags: [architecture, community-skills, deploy, registry]
sources: [task:064, task:105]
related: [community-skill-installation-architecture]
created: 2026-07-17
updated: 2026-09-03
status: active
---

## 개요

사용자가 PC에서 직접 설치한 커뮤니티 스킬을 `~/.opal/community-skills/user-registry.json`에 별도 기록하여, install 배포 시 `~/.opal/references/`의 덮어쓰기로부터 보호한다. 프레임워크 카탈로그와 사용자 등록분을 이원화하여 배포 경계를 명확히 한다.

## 결정 배경 (WHY)

1. **배포 경계 충돌** (근거: task:064 F-6, 실측) — install 스크립트가 `references/` 전체를 `rm -Rf` 후 `cp -R`로 덮어쓰는데(`scripts/install-mac.sh:1034,1362`), 사용자 설치 등록분을 `references/community-skills-registry.json`에 저장하면 재설치 시 소실.

2. **사용자 데이터 보존 정책** (근거: task:064 C-1, 142 D-4) — community-skills 디렉토리는 install이 절대 건드리지 않는 불가침 영역으로 지정됨 — 데이터 저장소도 이에 맞춰야 함.

3. **레지스트리 이원화 필요** — 프레임워크 카탈로그(배포)와 사용자 설치분(PC 로컬)을 분리해 SSOT 역할을 명확히.

## 결정 내용

### 레지스트리 이원 구조

| 항목 | 경로 | 관리 주체 | 배포 | 용도 |
|------|------|----------|------|------|
| 카탈로그 | `~/.opal/references/community-skills-registry.json` | 프로젝트 소스 → install | YES (덮어쓰기) | 공식 커뮤니티 스킬 |
| 사용자 등록분 | `~/.opal/community-skills/user-registry.json` | skill-manager | NO (절대 건드리지 않음) | 사용자 개인 설치 스킬 |

### 로드 규칙 (병합)

skill-registry `loadAllSkills()` 함수는 2개 파일(및 main 카탈로그)을 모두 로드해 병합한다. **[정정, task:105]** 아래는 개념 설명을 위한 단순화 의사코드다 — 실제 구현은 flat 배열이 아니라 `groups[vendor][]` 중첩 구조를 유지하며 `flattenGroups()`로 평탄화한 뒤 `name` 기준 override 병합을 수행한다(실제 코드: `opal/tools/skill-registry/skill-registry.js:129-147`).

```js
// 1. 프레임워크 카탈로그 로드 (main + community, 각각 groups[vendor][] 구조)
const catalogSkills = [...flattenGroups(main, 'main'), ...flattenGroups(community, 'community')];

// 2. 사용자 레지스트리 로드 (부재/파손 시 방어적 대체) — 역시 groups[vendor][] 구조
const userSkills = flattenGroups(loadUserRegistry() || {}, 'community');

// 3. 병합 — 동일 name은 사용자 항목이 override, 신규 name은 추가
for (const us of userSkills) {
  const idx = catalogSkills.findIndex(s => s.name === us.name);
  if (idx >= 0) catalogSkills[idx] = us; else catalogSkills.push(us);
}
```

**[MUST, task:105]** user-registry.json에 기록할 때도 `groups[vendor][] = [...]` 형상을 유지해야 한다 — flat 배열 등 다른 형상은 `loadAllSkills()`의 병합 로직에서 조용히 무시되어 설치 이력이 유실된다(근거: `opal-skill-manager/SKILL.md:219`).

**방어 규칙**: user-registry.json 부재 또는 파손 시 CLI 전체가 다운되면 안 됨 (safe=true 폴백).

### 기록 규칙 (설치/제거)

**설치 시** (근거: task:064 §2; **정정** task:105 실측 — `opal-skill-manager/SKILL.md:203,276`):
- **[정정, task:105]** 프레임워크 카탈로그(`~/.opal/references/community-skills-registry.json`)는 설치·삭제 시 **일절 수정하지 않는다** — install이 배포 시 항상 덮어쓰는 파일이므로 여기에 `commit_sha` 등을 기록하면 다음 install 재실행 때 소실된다. 위 §2.2행 "관리 주체: 프로젝트 소스 → install"·"배포: YES(덮어쓰기)"는 여전히 유효하나, 이 표가 처음 작성된 시점(task:064)에 함께 서술됐던 "기존 항목에 `commit_sha` 갱신 가능"은 이후(task:105) `opal-skill-manager/SKILL.md` `[MUST]`로 명시적으로 금지됐다 — **카탈로그는 무수정, `commit_sha`를 포함한 판정 3필드(trust/capabilities/scanned_at)는 user-registry.json에만 기록**한다.
- 사용자 커스텀 스킬 → `~/.opal/community-skills/user-registry.json`에 신규 항목 추가. 등재 스킬을 사용자가 clone-copy로 설치한 경우도 이 파일에 `commit_sha`·`trust`·`capabilities`·`scanned_at`을 기록한다(근거: task:105 `opal-skill-manager/SKILL.md:207,220`).

**제거 시**:
- 카탈로그 스킬 → `~/.opal/references/`에서 제거 금지 (프로젝트 소스이므로)
- 사용자 스킬 → `~/.opal/community-skills/user-registry.json`에서 항목 제거 + 디렉토리 삭제

## 영향 범위

- skill-manager 설치 절차 § 2 (근거: task:064 SKILL.md §2)
- skill-manager 제거 절차 § 4 (근거: task:064 SKILL.md §4)
- registry `loadAllSkills()` 병합 로직 (근거: task:064 F-006)
- ARCHITECTURE.md / CONVENTIONS.md 이원 경계 명시 (근거: task:064 §3)

## 관련 페이지

- [[community-skill-installation-architecture]] — vendor 중첩 레이아웃 및 clone-copy 설치
