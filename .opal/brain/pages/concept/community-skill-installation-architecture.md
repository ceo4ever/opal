---
type: concept
title: 커뮤니티 스킬 설치 아키텍처 — vendor 중첩 + clone-copy
tags: [architecture, community-skills, install, deploy]
sources: [task:064]
related: [community-skill-user-registry]
created: 2026-07-17
updated: 2026-07-17
status: active
---

## 개요

커뮤니티 스킬의 설치 레이아웃을 vendor 중첩 구조(`~/.opal/community-skills/{vendor}/{skill}/`)로 표준화하고, 설치 방식을 git clone 기반 copy 단일로 통일했다. 이전 flat 레이아웃의 31개 잔재를 마이그레이션으로 정규화한다.

## 결정 배경 (WHY)

1. **레이아웃 불일치 오류** (근거: task:064 D1) — npx-시대 잔재 31개는 flat 구조(`~/.opal/community-skills/pdf/`)이나 registry 판정은 vendor 중첩(`anthropics/pdf/SKILL.md`)만 검사해 설치본을 미설치로 오판했다.

2. **경로 지정 불가능** (근거: task:064 F-4, D4 실측) — `npx skills add` CLI는 설치 경로 지정 옵션이 없어 `./.claude/skills/` 또는 `~/.claude/skills/`에만 설치되므로 OPAL 프로젝트 정책과 충돌.

3. **배포 경계 보호** (근거: task:064 F-6) — install 스크립트가 references를 덮어쓰기로 배포하는 와중 사용자 설치 등록분이 소실되는 리스크를 격리 필요.

## 결정 내용

### 레이아웃 표준

```
~/.opal/community-skills/
├── anthropics/
│   ├── pdf/
│   │   ├── SKILL.md
│   │   └── ...
│   └── brainstorming/
└── obra/
    └── ...
```

**canonical 경로**: `~/.opal/community-skills/{vendor}/{skill}/SKILL.md` (설치 타깃)

### 설치 방식 (clone-copy 단일)

```bash
# 1. git clone --depth 1 → 임시 디렉토리
git clone --depth 1 <source_repo_url> /tmp/skill-clone

# 2. 스킬 폴더 추출 (subdir가 있으면 해당 경로만)
# 예: anthropics/skills@pdf → /tmp/skill-clone/pdf 추출

# 3. vendor 중첩 경로로 복사
cp -r /tmp/skill-clone/pdf ~/.opal/community-skills/anthropics/pdf

# 4. commit SHA 기록
git -C /tmp/skill-clone rev-parse HEAD → registry commit_sha 필드 갱신

# 5. 정리
rm -rf /tmp/skill-clone
```

**근거**: `clone-copy` 방식은 git 메타데이터(commit SHA) 추출이 자동이고 경로 지정이 명확하다 (근거: task:064 C-2).

### 마이그레이션 규칙 (migrate 서브커맨드)

**실행 시점**: skill-manager 최초 호출 시 1회 자동 실행 (도구 자기완결, 사용자 인식 없음)

**동작**:
1. `~/.opal/community-skills/` 1-depth 스캔
2. registry 미등재 항목 → 보존 (142 D-4)
3. registry 등재 항목 + flat 구조 → vendor 중첩으로 이동
4. 마이그레이션 완료 후 registry 판정이 즉시 정상화

**멱등성**: 재실행 시 이미 중첩된 항목은 스킵

## 영향 범위

- registry 기준 경로 탐지: `getCommunitySkillPath`는 canonical 경로 반환, `resolveCommunitySkillPath`는 실제 존재 경로(vendor 우선, flat 폴백) 해석 (근거: `opal/tools/skill-registry/skill-registry.js:75-200`)
- skill-manager 설치/제거 절차: clone-copy 방식으로 통일, 제거 시 vendor 디렉토리 전체 삭제 (근거: `opal/skills/opal-skill-manager/SKILL.md`)
- install 스크립트: community-skills/ 절대 건드리지 않음 (근거: `scripts/install-mac.sh:1033`)

## 관련 페이지

- [[community-skill-user-registry]] — 사용자 설치 등록분 격리
- [[community-skill-basename-matching]] — basename alias 매칭 확장
