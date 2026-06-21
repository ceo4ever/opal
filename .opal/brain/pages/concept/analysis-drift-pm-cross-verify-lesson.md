---
type: concept
title: ANALYSIS 드리프트 분석 환각 → PM 강화검토 패턴 (학습)
tags:
- analysis
- hallucination
- pm-gate
- lesson-learned
- drift
sources:
- task:031
- task:032
related:
- b7-action-completion-loop
- deploy-artifact-verification-lesson
- adapter-body-model-level-substitution
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개념 요약

ANALYSIS 드리프트 분석이 사실과 반대인 환각을 생성하고 PLAN이 이를 신뢰해 실행 오류로 이어진 사례 학습. "드리프트 분석은 PM이 직접 Read 교차검증"이 필수임을 확인한 패턴.

## 배경·문제 (WHY)

태스크 031 R-1 사례: ANALYSIS가 "배포본에 `model: opus` 인라인 없음"으로 분석(사실과 반대 — 배포본에 레벨명, 소스에 없음). PLAN이 이를 신뢰해 W6(배포본→소스 병합) 설계. W6 실행 결과 소스에 `model: opus`(Claude 전용 모델명) 하드코딩 → 플랫폼 독립성 위반 회귀. PM 강화검토(직접 Read 교차검증)로 검출 → fix 워커로 복원.

## 결정 내용 (HOW)

### 패턴: 드리프트 분석 PM 실측 교차검증

적용 시점: ANALYSIS가 소스/배포본 드리프트·차이를 분석 결과로 제시할 때.

검증 방법: PM이 EXECUTE 전 또는 PLAN 수립 시 해당 파일을 직접 Read해 ANALYSIS 주장을 교차검증. 단순 "분석 내용 인용"이 아닌 파일 실측 확인.

강화검토 필요 신호:
- 소스 vs 배포본 드리프트 분석
- "~에만 존재", "~에는 없음" 단정 분석
- 리스크 High 등급 분석(R-1 수준)

왜 ANALYSIS 단독 신뢰가 위험한가: "A에 있고 B에 없다" vs "A에 없고 B에 있다" 방향성 오류는 탐지 어렵고 실행 오류로 이어진다.

### 보강 사례 (032 R-3): 워커 decision_required도 PM 실측 교차검증

태스크 032에서 PLAN 워커가 "031이 task-action-agent 본문에 `model: opus`를 하드코딩했다"며 decision_required를 제기했다. PM이 grep으로 직접 반증(소스 `opus` 0건) → **오경보** 확정. 본 패턴은 ANALYSIS 단독뿐 아니라 **워커의 드리프트/하드코딩 주장**에도 동일하게 적용된다 — 드리프트 주장은 출처를 PM이 grep/Read로 실측 교차검증한 뒤에만 수용한다.

## 영향·관계

OPAL PM Gate 강화 패턴으로 oppd ANALYSIS 단계 후 PM 검수 체크리스트에 적용.

교차참조: [[b7-action-completion-loop]], [[deploy-artifact-verification-lesson]], [[adapter-body-model-level-substitution]]

## 근거 출처

task:031 — DONE.md §특이사항 "ANALYSIS R-1 환각", §회귀 1건 검출·교정
