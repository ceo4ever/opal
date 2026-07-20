---
type: concept
title: PM 개선 루프 2트랙 구조 (회고/온디맨드)
tags: [pm-loop, architecture-decision, improvement, process]
sources: [task:058]
related: [[close-retrospective-hardstep], [opal-improve], [op-brain-ingest]]
created: 2026-07-20
updated: 2026-07-20
status: active
---

## 개요

PM 개선 루프(자기 개선)를 정의만 있고 호출 0건인 prose 프로토콜에서 벗어나 tool-gated 2트랙 구조로 재설계했다. **트랙 A(회고)**: CLOSE 하드스텝으로 자동 enforce — 태스크/세션 궤적 신호(워커 재시도, PM 피드백, PLAN 재진입 로그) 입력. **트랙 B(온디맨드)**: PM 명시 호출로 대화·L2 피드백 처리. 두 트랙은 improve-tool을 통해 동일한 기록 계약을 따른다.

## 결정 배경 (WHY)

기존 PM 학습 루프(`pm-learning-loop.md` / `self-improvement.md`)는 PRINCIPLES를 위반했다 — "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." 실제로 호출 지점이 없어 작동하지 않았다 (근거: TASK.md 배경 분석 호출 지점 0건). op-brain-ingest의 성공 패턴(CLOSE 하드연결 + 도구 집행 + 증거 산출)을 관찰하고, 동일한 3요소를 답습하되 **입력 신호 특성에 따라 2트랙으로 분리**하기로 결정했다 (근거: TASK.md 확정방향 §1, PLAN.md §F-003).

- **회고 트랙 (자동 enforce)**: CLOSE 단계에 회고 하드스텝 삽입 → op-brain-ingest 직후 오케스트레이터 인라인 실행. 입력은 **오케스트레이터만 보유**한 세션 궤적 신호(STATE.md 검증/재설계 로그, 워커 폴백, PM Gate 피드백). 산출 = 프로세스·규칙 개선점.
- **온디맨드 트랙 (명시 호출)**: `//opim` 스킬로 PM이 대화·L2 중 명시 호출. 입력은 일반 대화·피드백·nudge. 동일 기록 계약으로 improve-tool에 위임.

이 분리는 **입력 신호의 소유권**을 명확히 한다 — 회고 신호는 파이프라인(세션 로그)이 유일한 출처이므로 하드스텝으로 자동 enforce하고, 대화 신호는 PM 판단 필요(피드백 nudge)이므로 온디맨드로 설계했다 (근거: PLAN.md §F-003 3.4.2 설계 결정 D-R1).

## 영향 범위

- **CLOSE 파이프라인**: 4 pilot(opd·opwt·opgc·oppd) CLOSE 단계에 회고 하드스텝 삽입 (`file_path:opal/skills/opal-pilot-dev/SKILL.md:248`)
- **온디맨드 스킬**: opal-improve(//opim) 신설 (`file_path:opal/skills/opal-improve/SKILL.md`)
- **도구 집행**: improve-tool record 호출로 결정론 기록 (`file_path:opal/tools/improve-tool/improve_tool.py`)
- **SSOT 통합**: pm-improvement-loop.md 단일 SSOT에 두 트랙 명확 분리 (`file_path:opal/core/references/harness/pm-improvement-loop.md`)

## 관련 페이지

- [[close-retrospective-hardstep]] — CLOSE 회고 하드스텝 실행 계약
- [[opal-improve]] — 온디맨드 스킬 5단계 프로세스
- [[improve-tool]] — 기록 집행 도구
- [[local-fw-improvement-classification]] — 로컬/FW 2원화 분류 기준
