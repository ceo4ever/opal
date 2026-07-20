---
type: entity
title: opal-improve (//opim)
tags: [skill, operator, improvement, pm-loop, tool-gated]
sources: [task:058]
related: [[improve-tool], [pm-improvement-loop-two-tracks], [local-fw-improvement-classification]]
created: 2026-07-20
updated: 2026-07-20
status: active
---

## 개요

PM 개선 루프의 온디맨드 실행 스킬이다. 관찰·분류·기록·보고·승인의 5단계 프로세스로 개선 후보를 수집하고, improve-tool을 통해 결정론적으로 기록한다. 로컬 PM 개선(프로젝트 `.opal/`)과 FW 개선(전역 `~/.opal/fw-inbox/`)을 2원화하여 분류한다.

## 책임 (WHAT)

- **관찰**: 개선 대상 발견 — 대화·L2 피드백, 태스크·세션 궤적 신호 (파이프라인 로그·STATE.md)
- **분류 (로컬 vs FW)**: 개선 대상의 scope를 2단계로 판단
  - 1차 결정론 게이트: 대상(프레임워크 소스/코드/도구 vs 프로젝트 고유 영역)로 즉시 판별
  - 2차 루브릭: 경계 사례에서 재사용성·프로젝트독립성·귀속SSOT로 채점하여 과반 scope 확정, 동점이면 소유자 질의(에스컬레이션)
- **기록**: improve-tool record 호출 — `--scope <local|fw>` 분기 → 로컬은 `.opal/MEMORY.md` 추가, FW는 `~/.opal/fw-inbox/` 항목 생성
- **보고**: "개선 후보 N건 기록" 간략 요약 → 소유자에게 전달
- **승인**: 소유자 이의 없으면 확정. 기존 확정 기준 수정/삭제·금지사항 추가는 소유자 승인 필수 (`file_path:opal/skills/opal-improve/SKILL.md`)

## 설계 배경 (WHY)

PM 학습 루프/자기 개선이 정의만 존재하고 실제 호출·집행 지점이 없었다 (근거: TASK.md 배경 분석). op-brain-ingest의 성공 패턴(CLOSE 하드연결 + 도구 집행 + 산출물 증거)을 답습하여, 태스크 CLOSE 회고(자동)와 온디맨드 피드백(수동)의 2트랙으로 분리하고, improve-tool을 통해 집행을 도구화했다 (근거: TASK.md 확정방향 §1, §7). 로컬/FW 분류는 개선이 반영될 **대상**을 명확히 하기 위해 2단계(결정론→루브릭)로 설계했다 (근거: PLAN.md §F-003 2.3.2 H-2).

## 관계 (HOW)

- **depend**: [[improve-tool]] — record/list/show 서브명령 호출로 기록 집행
- **depend**: [[pm-improvement-loop-two-tracks]] — SSOT 프로세스 정의
- **depend**: [[local-fw-improvement-classification]] — 2원화 분류 판단 기준
- **used-by**: CLOSE 회고 하드스텝 [[close-retrospective-hardstep]] — 태스크 경로 회고
- **used-by**: PM 온디맨드 명시 호출

## 소스 커버리지

| 항목 | 경로:줄번호 | 설명 |
|------|-----------|------|
| 스킬명 | `opal/skills/opal-improve/SKILL.md:1` | 5단계 프로세스 정의, 로컬/FW 분류 분기 |
| registry 엔트리 | `opal/core/references/opal-skills-registry.json:groups.opal` | `opim` alias 등록 |
| improve-tool 호출 계약 | `opal/skills/opal-improve/SKILL.md:3` | `record --scope <local\|fw>` 서브명령 |
