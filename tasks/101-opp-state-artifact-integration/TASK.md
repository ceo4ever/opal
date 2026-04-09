# TASK: STATE.md 진행 현황 + 완료 산출물 통합

> 작성일: 2026-04-09 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

STATE.md의 진행 현황 테이블에 완료 산출물 추적을 통합하여, 워커가 산출물 생성을 건너뛰지 못하도록 순서를 강제한다.

## 배경

STATE.md는 현재 Gate 통과 여부(QA Gate ✅, Artifact Gate ✅ 등)를 진행 현황 테이블로 추적하지만, **어떤 산출물이 실제로 생성되었는지는 기록하지 않는다.** Artifact Gate(§2.5)는 파일 존재 여부를 사후에 점검하는 방식이지만, 이것만으로는 워커의 산출물 누락을 막기 어렵다.

## 배경 분석 (대화에서 도출)

### 현재 문제 3가지

1. **진행 현황 + 완료 산출물 분리**: STATE.md에 "완료 산출물" 섹션이 없어 게이트 통과 여부와 산출물 존재 여부가 분리되어 있음
2. **완료 산출물 누락 빈발**: PLAN.md, QA-PLAN.md, DONE.md 등 필수 산출물이 생성되지 않는 경우가 많음
3. **산출물 생성 무시**: 워커가 진행 현황 행은 ✅로 갱신하지만 실제 파일은 생성하지 않는 패턴이 반복됨

### 근본 원인

- 진행 현황 테이블은 "프로세스 단계" 관점으로 설계되어 있어, 산출물 파일 생성이 명시적 행으로 표현되지 않음
- Artifact Gate는 사후 점검이지만, 워커에게 "지금 파일을 만들어야 한다"는 신호가 순서 안에 없음
- 순서 강제 원칙(앞 행 ✅ 없이 다음 행 진행 불가)이 산출물 생성에 적용되지 않음

### 영향 범위

STATE.md 도메인 치환값(진행 현황 행 예시)을 가진 오케스트레이터 스킬:
- `opal/core/references/opal-harness.md` — 공통 템플릿 + 진행 현황 행 구성 규칙
- `opal/core/references/opal-harness-interactive.md` — Artifact Gate (§2.5)
- `opal/skills/opal-pilot-project/SKILL.md` (opp)
- `opal/skills/opal-pilot-dev-short/SKILL.md` (opds)
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md` (opdw)
- `opal/skills/opal-pilot-sdd/SKILL.md` (opsdd)

## 요구사항

- [x] **진행 현황 테이블에 산출물 행 통합**
  - 무엇을: 진행 현황 테이블에 "산출물 생성" 행을 추가하여, 각 단계/Gate 직후 필수 산출물 파일명을 명시
  - 어디에: `opal/core/references/opal-harness.md` → "진행 현황 행 구성 규칙" 섹션
  - 왜: 순서 강제 원칙에 산출물 생성을 포함시켜 건너뛰기 불가하게 만들기 위함
  - AC: 진행 현황 행 구성 규칙에 단계별 산출물 행이 명시되고, 예시 테이블에 산출물 행이 포함된다

- [x] **각 오케스트레이터 STATE.md 도메인 치환값 업데이트**
  - 무엇을: 각 스킬의 "STATE.md 도메인 치환값" 진행 현황 행 예시를 산출물 행 포함 버전으로 갱신
  - 어디에: opp / opds / opdw / opsdd 각 SKILL.md
  - 왜: 실제 태스크 생성 시 올바른 STATE.md 구조가 반영되도록
  - AC: 각 스킬의 진행 현황 행 예시에 해당 스킬의 필수 산출물 행이 포함된다

- [x] **Artifact Gate(§2.5) 조정 — 산출물 행과 역할 분리**
  - 무엇을: 산출물 행이 진행 현황 테이블에 통합됨에 따라 Artifact Gate의 역할을 "2중 안전장치"로 재정의하거나, 산출물 행과 중복되지 않도록 조정
  - 어디에: `opal/core/references/opal-harness-interactive.md` → §2.5
  - 왜: 산출물 행과 Artifact Gate 간 역할 충돌 방지
  - AC: 산출물 행과 Artifact Gate의 역할이 명확히 구분되고, 중복/충돌이 없다

- [x] **STATE.md 공통 템플릿 갱신**
  - 무엇을: 하네스 §3 STATE.md 템플릿에 산출물 행을 반영한 업데이트
  - 어디에: `opal/core/references/opal-harness.md` → §3 STATE.md 공통 템플릿
  - 왜: 신규 태스크에서 올바른 STATE.md 구조가 자동 적용되도록
  - AC: 공통 템플릿의 진행 현황 행 구성 규칙에 산출물 행 추가 지침이 포함된다

## 제약 조건

- `~/.opal/` 배포본 직접 수정 금지 — 소스(`opal/core/`, `opal/skills/`)에서만 수정
- 기존 진행 중인 태스크(예: 098)의 STATE.md는 소급 변경 대상 아님
- 하네스 변경이므로 파급 범위(모든 오케스트레이터) 사전 분석 후 적용

## 기술 스택

- Markdown 문서 (SKILL.md, harness.md)
- OPAL Harness 구조 (Guards, Gates, State)

## 관련 문서

- `opal/core/references/opal-harness.md` — §2 QA 산출물 표준 파일명, §3 State, 진행 현황 행 구성 규칙
- `opal/core/references/opal-harness-interactive.md` — §2 QA Gate, §2.5 Artifact Gate
- `opal/skills/opal-pilot-project/SKILL.md` — opp STATE.md 도메인 치환값
- `opal/skills/opal-pilot-dev-short/SKILL.md` — opds STATE.md 도메인 치환값
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md` — opdw STATE.md 도메인 치환값
- `opal/skills/opal-pilot-sdd/SKILL.md` — opsdd STATE.md 도메인 치환값
- 선행 태스크 `tasks/090-opp-artifact-gate/` — Artifact Gate 도입 배경 참조
