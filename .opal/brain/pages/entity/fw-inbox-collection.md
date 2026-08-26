---
type: entity
title: fw-inbox (프레임워크 개선 수집소)
tags: [runtime-directory, improvement, collection, deployment]
sources: [task:058]
related: [improve-tool, opal-improve, pm-improvement-loop-two-tracks]
created: 2026-07-20
updated: 2026-07-20
status: active
---

## 개요

프레임워크 개선 제안을 수집하는 전역 런타임 디렉토리다. improve-tool record --scope fw로 쓰인 항목들을 호스트·프로젝트·상황·일시 출처메타와 함께 자기완결 형식으로 축적한다. 배포경계 준수(프로젝트 소스 수정 후 install 배포)의 차원에서, 프로젝트에 묻히지 않도록 `~/.opal/fw-inbox/`로 중앙 수집한다.

## 책임 (WHAT)

- **항목 수집**: improve-tool record --scope fw가 생성한 개선 제안 항목 축적
- **자기완결성**: 항목 본체(`markdown`)가 호스트·프로젝트·상황·생성일시의 출처메타 4종 포함하여 단독 해석 가능하도록 설계
- **멱등성**: install 재실행 시 fw-inbox 기존 항목 보존 — `mkdir -p`로만 초기화하고 `rm` 대상 제외
- **README 가이드**: install seed로 fw-inbox/README.md 배포 — 수집소 용도·항목 스키마·소비 워크플로우 안내

## 설계 배경 (WHY)

PM 개선은 로컬(프로젝트 `.opal/`)과 FW(프레임워크)로 분류되는데, FW 개선의 출처를 분산하면 설계 추적이 어려워진다. 따라서 **중앙 수집소** 아키텍처를 도입하여:
- 전역 `~/.opal/fw-inbox/`로 모든 프로젝트의 FW 개선 제안을 수집
- 출처메타(어느 PC·어느 프로젝트·어떤 맥락)를 포함하여 자기완결성 보증
- install 배포 경계(`~/.opal` 직접수정 금지) 준수 — improve-tool 도구만 write 권한

이는 "프레임워크-우선 원칙" (TASK.md 확정방향 §8): "에이전트 행동 개선은 개인 memory가 아니라 프레임워크 소스 SSOT 수정 → install 배포 대상"을 구현한 것이다.

## 구조

**위치**: `~/.opal/fw-inbox/`

**항목 파일명**: `{YYYYMMDD-HHmmss}-{host}-{slug}.md` (정렬 가능·충돌 회피)

**항목 frontmatter**:
```yaml
---
type: fw-improvement
title: <제안 제목>
created: <YYYY-MM-DD HH:mm KST>
host: <hostname>               # 출처 메타 — 어느 PC
project: <프로젝트명>          # 출처 메타 — 어느 프로젝트
project_root: <절대경로>
source_task: <NNN|task-path|"">
situation: <retrospective|feedback|conversation>
status: inbox
---

## 제안 요약
<1-2문장>

## 상황 (Context)
<궤적 신호>

## 제안 내용
<구체적 개선 — 어느 SSOT를 어떻게 바꿀 것인가>
```

**README 배포**: install이 `~/.opal/fw-inbox/README.md` seed 제공 (create-if-absent)

## 영향 범위

- **write 주체**: improve-tool record --scope fw 전용
- **소비 주체**: FW 소유자/PM이 주기적 검토 → ai-framework 소스 반영 (후속 태스크 후보)
- **배포 경계**: clean_dirs에 fw-inbox 미포함 (런타임 데이터 보존)

## 관련 페이지

- [[improve-tool]] — record --scope fw로 항목 write
- [[opal-improve]] — 온디맨드 스킬에서 분류 후 기록
- [[close-retrospective-hardstep]] — CLOSE 회고에서 분류 후 기록
- [[local-fw-improvement-classification]] — 로컬/FW 분류 기준
- [[pm-improvement-loop-two-tracks]]

