---
type: entity
title: opal-workspace-sync (alias opws)
module: opal-workspace-sync
layer: skill
domain: workspace
exports: [opws]
source_ref: 'opal/skills/opal-workspace-sync/SKILL.md'
header_synced: 2026-07-02
tags:
- skill
- workspace
- git
- operator
sources:
- task:052
related:
- git-sync-tool
- skill-registry-index-registration-required-for-discovery
created: '2026-07-02'
updated: '2026-07-02'
status: active
---

## 개요

워크스페이스 단위로 여러 git 저장소를 안전하게 일괄 최신화하고 싶을 때 호출하는 오케스트레이션 스킬이다 (alias `opws`). 결정론적인 저장소 순회·pull 자체는 [[git-sync-tool]]에 위임하고, 이 스킬은 "어느 경로를 대상으로 할지 결정", "결과를 사람이 읽을 보고서로 정리", "문제 저장소의 후속 조치를 승인받는 것"만 책임진다 (근거: task:052 TASK§확정 설계 방향).

## 책임 (WHAT)

- 대상 결정 3분기 — `(프로젝트)/workspace` 존재 시 그 경로, 없고 받은 경로가 단일 git 루트면 그 경로, 둘 다 아니면 사용자에게 경로를 질의한다 (`opal/skills/opal-workspace-sync/SKILL.md` STEP 1).
- git-sync-tool을 호출해 JSON 결과를 받는다 (STEP 2).
- 결과를 5섹션 보고서(요약/최신화/Skip/실패/조치 제안)로 렌더링한다 (STEP 3).
- 문제 저장소(dirty/diverged/detached/no-upstream/fetch-failed)에 대해서만 사유별 제안 조치를 제시하고, 사용자 승인 후에만 실행한다 — 승인 전 자동 실행은 절대 금지 (STEP 4, 근거: task:052 TASK§제약 "헌법 user sovereignty").

## 설계 배경 (WHY)

- 신규 스킬은 skill-creator 프로세스(Capture Intent→Interview→Draft→Test→Evaluate→Iterate→Optimize Description→Package)로 생성했다 — 프로젝트 피드백 메모리에 따라 새 스킬 생성 시 dev-task-pilot 대신 skill-creator를 우선 사용하는 관례를 따른 것이다 (근거: task:052 PLAN§2.2.2(c)).
- clean+ff 저장소의 pull은 스킬의 정상 동작으로 자동 수행하되(매 저장소 승인 불요), 문제 저장소만 승인 게이트를 거치도록 경계를 나눈 것은 — 안전한 작업까지 매번 승인받게 하면 도구의 효용이 사라지고, 위험한 작업만 승인받아야 헌법 원칙과 실용성이 함께 지켜지기 때문이다 (근거: task:052 TASK§확정 설계 방향 "자동 수행 경계").
- 이 스킬은 신설 직후 `//opws` 호출이 발견되지 않는 배포 갭을 겪었다 — 상세는 [[skill-registry-index-registration-required-for-discovery]] 참조 (근거: task:052 AGENTIC-LOG #11·#12).

## 관계 (HOW)

- [[git-sync-tool]] — 이 스킬이 호출하는 결정론 도구.
- opal-brain 스킬의 operator 타입 템플릿(파이프라인 없는 단일 동작, frontmatter 구조)을 참조해 작성했다 (`opal/skills/opal-brain/SKILL.md` 참조 원본).

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `SKILL.md` | `opal/skills/opal-workspace-sync/SKILL.md` | frontmatter + 4-STEP 프로세스 |
| alias | `opal/core/references/opal-skills-registry.json` | 레지스트리 등록 트리거 별칭 `opws` |
