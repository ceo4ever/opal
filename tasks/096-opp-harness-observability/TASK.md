# TASK: Harness Observability — 행위 주체 표시 + Gate 상태 추적

> 작성일: 2026-04-07 | 스킬: //opp

## 적용 스킬

`opal-pilot-project (opp)` — 문서 수정 태스크

## 배경

두 가지 가시성 문제가 있다.

**1. 행위 주체 불투명**: 현재 하네스는 `📋 알투[PM]: {NNN} {태스크명} | {단계}` 표시를 응답 첫 줄에만 제공한다. 실제 툴 호출(Edit, Write, Agent 디스패치 등) 수준에서는 행위 주체(PM 직접 / 워커)가 표시되지 않아 캡틴이 어느 에이전트가 어떤 작업을 수행하는지 파악할 수 없다.

**2. Gate 진행 상태 불추적**: QA Gate, Artifact Gate, State Gate, PM Gate의 통과 여부가 STATE.md에 기록되지 않아 세션 복원 시 Gate 진행 상황을 알 수 없고, 캡틴도 어느 Gate까지 통과됐는지 실시간으로 파악할 수 없다.

## 배경 분석 (대화에서 도출)

- STATE.md 갱신 시 PM이 직접 Edit한 건지 워커가 한 건지 캡틴 입장에서 구분 불가
- 워커 디스패치/완료도 Agent 툴 결과로만 표시되고 명시적 선언이 없음
- `📋 알투[PM]` 표시는 응답 단위이고, 툴 호출 단위의 주체 표시가 없음
- Gate 상태가 STATE.md에 없어서 세션 복원 시 "PLAN 완료 후 QA Gate까지 통과했는가?" 판단 불가
- 094에서 State Gate 강제화를 구현했지만 Gate 통과 이력 자체는 추적하지 않음

## 목표

1. 툴 호출 직전 한 줄 선언으로 행위 주체를 명시하여 캡틴이 PM/워커 구분을 실시간으로 파악할 수 있도록 한다.
2. 각 단계의 Gate 통과 상태를 STATE.md에 기록하여 세션 복원 및 캡틴의 진행 파악을 돕는다.

## 요구사항

### [A] 행위 주체 표시

- [x] **[harness §Observability 신설]** PM 직접 행위 / 워커 디스패치 / 워커 완료 선언 형식 정의
  - `📋 알투[PM] 직접:` — PM이 직접 툴을 호출하기 전 선언
  - `⚙️ 워커 디스패치:` — Agent 도구로 워커를 디스패치하기 전 선언
  - `⚙️ 워커 완료:` — 워커 결과 수신 후 선언
  - AC: 세 가지 형식이 하네스에 명시되고, 각 적용 시점이 정의되어 있다
- [x] **[opal-pm.md 갱신]** PM 행동 프로세스에 Observability 규칙 적용 의무 추가
  - AC: "디스패치 전 선언 / 완료 후 선언"이 PM 행동 절차에 포함된다
- [x] **[AGENT.md 보고 형식 갱신]** PM 모드 표시 섹션에 Observability 선언 규칙 참조 추가
  - AC: AGENT.md 보고 형식 섹션에서 하네스 Observability를 참조한다

### [B] 단계 상태 세분화로 Gate 강제

- [ ] **[harness §3 상태값 확장]** `상태` 필드 값을 Gate 단계로 세분화
  - 현재: `진행 중 / 대기 중 / 블로커 / 완료`
  - 변경: `진행 중 / QA Gate 대기 / PM Gate 대기 / 사용자 확인 대기 / 완료 / 블로커`
  - AC: 공통 STATE.md 템플릿의 상태값 목록이 갱신된다
- [ ] **[harness §3 State Gate 강화]** 이전 단계 상태가 `완료`가 아니면 다음 단계 진입 금지 규칙 추가
  - AC: State Gate 절차에 "이전 단계 STATE.md 상태가 `완료`인지 확인 → 아니면 차단" 규칙이 명시된다
- [ ] **[harness-interactive §3 강화]** 각 Gate 통과 시 STATE.md 상태값 갱신 의무 명시
  - QA Gate 통과 → 상태: `QA Gate 대기` → `PM Gate 대기`
  - PM Gate 통과 → 상태: `PM Gate 대기` → `사용자 확인 대기`
  - 사용자 확인 → 상태: `사용자 확인 대기` → `완료`
  - AC: 각 Gate 통과 시점과 대응하는 상태값 전이가 하네스에 명시된다

## 범위

- 수정 대상: `opal/core/references/opal-harness.md` — §3 상태값 확장 + State Gate 강화
- 수정 대상: `opal/core/references/opal-harness-interactive.md` — §3 Gate별 상태값 전이 명시
- 수정 대상: `opal/core/references/opal-pm.md` — Observability 규칙 적용 의무
- 수정 대상: `opal/core/AGENT.md` — 보고 형식 Observability 참조

## 제약

- `~/.opal/` 직접 수정 금지 — 모든 변경은 `opal/` 소스에서 수행
- 기존 `📋 알투[PM]: {NNN} {태스크명} | {단계}` 응답 첫 줄 표시 유지 (대체 아닌 추가)
- 행위 주체 선언은 간결해야 한다 — 한 줄을 초과하지 않는다
- 상태값 확장은 기존 `완료 / 진행 중 / 블로커` 의미를 유지하며 Gate 단계를 세분화
- opsdd/opwt는 Gate 구조가 다르므로 이번 범위에서 제외 (후속 태스크에서 별도 처리)
