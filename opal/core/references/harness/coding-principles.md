---
module: coding-principles
role: 코드 생성·수정 시 적용하는 OPAL 실행 계약
load: EXECUTE 진입 또는 PM 직접 구현 진입 시
상속: opal/core/PRINCIPLES.md
---

# Coding Principles

행동 원칙은 `opal/core/PRINCIPLES.md`가 소유한다. 이 문서는 코드 변경 시 OPAL 산출물과
증거를 연결하는 계약만 정의한다.

## §4 EXECUTE 계약

### 입력

- sdlc-v2: 배정된 PLAN `Work items`, 관련 `Decisions and contracts`·`Risks`, TEST-SCENARIO의 관련 S
- legacy: 배정된 PLAN 실행 Step과 관련 기능·가설·시나리오
- PM이 PROJECT 레지스트리에서 선별한 프로젝트 문서와 런타임 capability

### 변경

- 배정된 변경 대상 안에서만 수정한다.
- 계획 밖 파일이나 계약 변경이 필요하면 임의로 확장하지 않고 PM에게 반환한다.
- 프로젝트 문서와 기존 공개 인터페이스를 따른다.
- 구현 결과로 사실이 달라지는 기획·설계·개발·운영 문서는 배정된 Work item에 포함된 경우 함께 갱신한다.
- 실제 연동 구현을 가짜 응답으로 대체하지 않는다. 테스트용 substitute는 허용하지만 실제 integration
  증거로 간주하지 않는다.

### 검증과 증거

- 관련 S가 판정하는 공개 인터페이스와 관찰 가능한 결과를 검증한다.
- 변경에 맞는 최소 테스트·정적 검사를 실행하고, 실패를 고친 뒤 같은 검사를 다시 실행한다.
- 시나리오 결과와 실행 증거는 `test-scenario.json`, pipeline 상태는 `state.json`에 기록한다.
- 문구 존재만 확인하는 검사를 실제 동작 증거로 사용하지 않는다.

### 완료

- 배정된 W/Step의 완료 기준이 실행 증거로 확인됨
- 변경 파일이 계획된 경계 안에 있음
- 필요한 프로젝트 문서 갱신이 완료됨
- 실제 환경 확인이 필요한 항목을 실행하지 못했으면 완료 대신 BLOCKED로 반환함

## 변경이력

| 버전 | 일시 | 변경내용 |
|---|---|---|
| v1.0 | 2026-05-12 11:16 | 단계별 Coding Principles 적용 체크리스트 신설 (001) |
| v1.3 | 2026-06-07 | PRINCIPLES 상속 구조와 동작 증거 계약 반영 (012) |
| v1.4 | 2026-06-07 | 문서 QA를 PM Gate에 통합 (014) |
| v1.5 | 2026-06-10 10:13 | 공개 인터페이스 검증 규율 추가 (016) |
| v1.6 | 2026-09-09 15:55 KST | sdlc-v2 Work items와 state/test evidence 소유권 반영 (111) |
| v2.0 | 2026-09-09 15:33 KST | 로드 시점과 무관한 TASK·PLAN·TEST-SCENARIO·PM Gate 체크리스트를 제거하고, 실행 범위·실연동·증거 연결 계약만 유지 (task 111/W-13) |
