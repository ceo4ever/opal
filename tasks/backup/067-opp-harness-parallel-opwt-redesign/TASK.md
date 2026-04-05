# TASK: 하네스 병렬 처리 원칙 추가 + opwt 재설계

> 작성일: 2026-04-01 | 작업 유형: 개선 | 적용 스킬: opp
> 입력: 캡틴 설계 지시
> 출력: opal-harness.md 수정, opal-pilot-write-tech/SKILL.md 재설계

## 작업 목표

1. `opal-harness.md`에 병렬 처리 원칙을 추가하여 모든 오케스트레이터가 공통 적용하도록 한다.
2. `opal-pilot-write-tech/SKILL.md`(opwt)를 하네스 표준 단계(TASK/ANALYSIS/PLAN/EXECUTE/QA)로 재설계한다.

## 배경

**하네스 병렬 원칙 부재**
현재 오케스트레이터들이 파일 읽기, 문서 작성, QA 검증 등을 순차 처리하고 있어 비효율적이다.
하네스에 공통 원칙을 추가하면 모든 오케스트레이터가 별도 수정 없이 자동 상속한다.

**opwt 구조적 갭**
opwt가 Phase 1-4로 독자 설계되어 하네스 표준을 위반하고 있으며 다음 문제가 있다:
- TASK 단계 없음 → TASK.md/STATE.md 미생성 → 세션 복원 불가
- 각 단계 STATE.md 갱신 지시 없음 → 진행 상태 추적 불가
- Phase 명칭이 하네스 표준(TASK/ANALYSIS/PLAN/EXECUTE/QA)과 불일치

## 요구사항

### T1. 하네스 병렬 처리 원칙

- [ ] 읽기(Read 툴콜): 독립 파일은 병렬 동시 호출 필수
- [ ] 실행(Agent 디스패치): 독립 작업은 병렬 서브에이전트 필수
- [ ] 의존관계 있는 작업은 순차 유지
- [ ] 읽기(툴콜 병렬)와 실행(서브에이전트 병렬)의 차이 명시
- [ ] 기존 Guards/State/TASK 구조와 충돌 없음

### T2. opwt 재설계

- [ ] Phase 1-4 → 하네스 표준 단계명 교체 (TASK/ANALYSIS/PLAN/EXECUTE/QA)
- [ ] TASK 단계 추가: TASK.md 작성, STATE.md 초기화
- [ ] 각 단계에 STATE.md 갱신 지시 명시 (단계 시작/완료)
- [ ] ANALYSIS: 기존 문서 병렬 Read → 워커 병렬 분석 (Case A+B 조합)
- [ ] EXECUTE: 배치 편성 유지, 독립 배치 병렬 / 의존 배치 순차
- [ ] 핵심 로직 유지: diagnosis.json, 배치 편성, network-guide/consistency-rules 참조

## 제약 조건

- `opal-harness.md` 변경은 모든 오케스트레이터에 영향 → 파급 범위 사전 분석
- 소스/배포 경로 동기화 필수 (install-mac.sh)
  - 소스: `opal/core/references/opal-harness.md`
  - 배포: `~/.opal/references/opal-harness.md`
  - 소스: `opal/skills/opal-pilot-write-tech/SKILL.md`
  - 배포: `~/.opal/skills/opal-pilot-write-tech/SKILL.md`
- opwt 핵심 로직(diagnosis.json, network-guide, consistency-rules) 보존

## 관련 문서

- `opal/core/references/opal-harness.md`
- `opal/skills/opal-pilot-write-tech/SKILL.md`
- `~/.opal/references/opal-harness-interactive.md`
- `~/.opal/references/opal-harness-agentic.md`
- `docs/ARCHITECTURE.md`
- `docs/CONVENTIONS.md`
