---
type: concept
title: 커뮤니티 스킬 사용자 레지스트리 — install 배포 경계 격리
tags: [architecture, community-skills, deploy, registry]
sources: [task:064]
related: [[community-skill-installation-architecture]]
created: 2026-07-17
updated: 2026-07-17
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

skill-registry `loadAllSkills()` 함수는 2개 파일을 모두 로드해 병합한다 (근거: `opal/tools/skill-registry/skill-registry.js:84-93`):

```js
// 1. 프레임워크 카탈로그 로드
const catalogSkills = loadJSON('~/.opal/references/community-skills-registry.json');

// 2. 사용자 레지스트리 로드 (부재/파손 시 방어적 대체)
const userSkills = loadJSON('~/.opal/community-skills/user-registry.json') || [];

// 3. 병합 (user가 catalog 덮어씀)
const allSkills = [...catalogSkills, ...userSkills];
```

**방어 규칙**: user-registry.json 부재 또는 파손 시 CLI 전체가 다운되면 안 됨 (safe=true 폴백).

### 기록 규칙 (설치/제거)

**설치 시** (근거: task:064 §2):
- registry 등재 스킬 → `~/.opal/references/community-skills-registry.json` 기존 항목에 `commit_sha` 갱신 가능
- 사용자 커스텀 스킬 → `~/.opal/community-skills/user-registry.json`에 신규 항목 추가

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
