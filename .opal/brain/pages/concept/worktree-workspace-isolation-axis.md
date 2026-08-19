---
type: concept
title: 워크트리 격리 축 — 문서는 허브 고정, 코드만 분기
tags:
- architecture
- workspace
- worktree
- git
- isolation
sources:
- task:092
related:
- worktree-tool
- worktree-slot-existence-to-occupancy-judgment
created: '2026-08-15'
updated: '2026-08-15'
status: draft
---
## 개요

OPAL 태스크 파이프라인에 실행 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교하는** 별도의 작업공간 축(`--worktree`/`--wt`)을 신설했다. 플래그를 쓰지 않으면 현행 동작이 그대로 유지되고, 쓰면 태스크별 코드 작업본이 `{프로젝트}/.opal-worktrees/task_{NNN}/`에 git worktree로 격리된다.

## 결정 배경 (WHY)

- 병렬 태스크에서 실제로 충돌하는 것은 코드 레이어(빌드 캐시·의존성·포트·컨테이너)이고, 태스크 문서(`tasks/`)와 프로젝트 메모리(`.opal/MEMORY.json`)·브레인(`.opal/brain/`)은 오히려 공유돼야 한다 — 채번 중복을 막고 메모리·브레인 SSOT를 유지하기 위함이다(근거: task:092 DONE §1).
- 이 관찰에서 핵심 격리 경계 원칙이 나온다: **문서는 허브에 고정하고 코드만 분기한다.** 두 축(모드/워크스페이스)이 직교하므로 어떤 모드에서도 `--wt` 유무만으로 코드 작업본 위치가 결정된다.
- 새 디렉토리를 `.opal/` 하위가 아니라 `.opal-worktrees/`로 둔 이유는 `.opal/`이 커밋 추적 대상(revup 430·mams 168·opal 261 파일 실측)이기 때문이다 — 커밋 추적 디렉토리 안에 대용량·비추적 코드 파생물을 섞으면 `.gitignore` 예외 처리가 뒤엉킨다. 경로명은 소유자가 3안(현행 유지/`.opal-worktrees/` 개명/`.opal/worktree/` 이동) 중 직접 확정했다(근거: task:092 AGENTIC-LOG #27).
- 의존성 설치(`setup[]`)는 생성 시점에 실행하지 않고 열거만 한다(lazy) — 편집만 하고 끝나는 슬롯의 설치 **시간**을 0으로 만드는 것이 목적이며, 락 해시 비교 후 심볼릭 링크로 재사용하는 대안은 폐기했다. APFS CoW(Copy-on-Write)와 pnpm store가 이미 동일 볼륨에 있어 재설치 디스크 비용이 0에 수렴하므로, 파일시스템이 이미 해결한 문제에 추상화를 얹지 않는다는 판단이다(근거: task:092 TASK §C-7).
- `UV_CACHE_DIR`을 시스템 볼륨에서 프로젝트 볼륨(`/Volumes/Data`)으로 이전하는 것을 소유자가 이번 범위에 포함하도록 승인했다 — 캐시가 다른 볼륨에 있으면 하드링크·클론이 불가능해 슬롯마다 의존성이 실복사되기 때문이다(근거: task:092 TASK §C-8).

## 결정 내용

- 경로 계약: `tasks/{NNN}-...`(문서, 분기 없음) · `.opal-worktrees/task_{NNN}/`(코드 작업본, 격리) · `workspace/`(`--wt` 미사용 시 현행 기본 작업본). worktree 내부 레이아웃은 메인 프로젝트와 동일하게 미러링해 상대경로 스크립트·compose 볼륨 경로가 그대로 동작한다.
- 유형 2종을 `.opal/worktree.json`의 `layout` 키 하나로 흡수한다 — multi-repo(레포마다 개별 worktree)와 monorepo(루트 레포 1개 + sparse-checkout).
- 브랜치 네이밍 규칙은 두 SSOT로 나뉜다: OPAL 저장소 자체는 `feat/{NNN}-{스킬약어}-{설명}`(예외적 분리), worktree 대상 프로젝트는 `worktree.json`의 `branchTemplate`(기본 `feat/OP-TASK-{NNN}`). 두 규칙은 충돌이 아니라 애초에 적용 대상이 다르다.
- `.gitignore` 보장은 3계층(도구 자동/opi 프로젝트 초기화·최신화/수동)으로 겹겹이 보장한다.
- CLOSE에서 worktree를 자동 제거하지 않는다 — 커밋 규칙상 PM이 머지를 자동 수행할 수 없어 CLOSE 시점에는 미머지 커밋이 남기 때문이며, "머지 대기"로 안내만 하고 소유자가 머지 후 `remove`로 회수한다.
- 실측 성과: `UV_CACHE_DIR` 이전 후 슬롯당 `.venv` 실복사가 263MB → 8.7MB(약 30배 절감)로 줄었고, monorepo(mams) 유형의 sparse 슬롯은 13MB(메인 1.9GB 대비)에 그쳤다(근거: task:092 DONE §4 실환경 검증).

## 영향 범위

- 신규: [[worktree-tool]](도구 본체), `.opal/worktree.json` 스키마·유형 A/B 템플릿.
- 수정: 하네스 SSOT(`opal-harness.md` §2.5 워크스페이스 축), 오케스트레이터 공통 후처리(`task-process.md` 스텝 4.5), 워커 디스패치 경로 계약(`dispatch-process.md`), `state-tool`(`init --worktree` 영속화), `opal-pilot-dev`(CLOSE 안내, pilot 10종 중 유일 변경), `opal-project-init`(`.gitignore` 멱등), `.opal/code-scan.json`(exclude 1행).
- pilot 나머지 9종은 SKILL.md 산문을 복제하지 않는다 — 축 정의를 하네스 SSOT 1곳에 두고 집행은 도구가 전담하는 원칙(태스크 091 "산문 규칙을 도구 집행으로" 기조와 일치)을 유지했기 때문이다.

## 관련 페이지

- [[worktree-tool]]
- [[worktree-slot-existence-to-occupancy-judgment]]
