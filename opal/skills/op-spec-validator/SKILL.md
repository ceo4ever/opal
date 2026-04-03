---
name: op-spec-validator
description: |
  **SDD 명세 검증 워커 스킬**. PRD/TRD 문서를 읽고 체크리스트 기반으로 명세 완성도를 판정한다.
  오케스트레이터(oppd 1-1b 등)가 디스패치하여 사용한다. 사용자 직접 호출 불가.
  필수 입력: PRD 경로, TRD 경로, 검증 대상(PRD/TRD/ALL).
  보장 출력: 항목별 {item, result, reason, suggestion} 구조화 판정 결과.
---

# op-spec-validator — SDD 명세 검증 워커

## 실행 컨텍스트

이 스킬은 **오케스트레이터가 워커 에이전트로 디스패치**한다. 오케스트레이터가 직접 수행하지 않는다.
서브에이전트를 생성하지 않는다. 입력을 파싱하고, 문서를 Read하고, 체크리스트를 판정하여 결과를 반환한다.

**사용자 직접 호출 불가** — alias 및 triggers가 없으며, 오케스트레이터가 경로로 직접 로드한다.

## 입력 인터페이스

오케스트레이터가 아래 형식으로 전달한다:

```
검증 요청:
- PRD 경로: {path} (검증 대상이 PRD 또는 ALL일 때)
- TRD 경로: {path} (검증 대상이 TRD 또는 ALL일 때)
- 검증 대상: PRD | TRD | ALL
- (선택) 참조 문서: {추가 참조 경로 목록}
```

## 프로세스

### STEP 1. 입력 파싱

전달된 입력에서 아래 항목을 확인한다:
- PRD 경로 (검증 대상이 PRD 또는 ALL일 때 필수)
- TRD 경로 (검증 대상이 TRD 또는 ALL일 때 필수)
- 검증 대상 (PRD / TRD / ALL 중 하나)

경로가 누락된 경우 해당 항목 판정을 건너뛰고 결과에 명시한다.

### STEP 2. 대상 문서 Read

검증 대상에 따라 해당 문서를 Read한다:
- `PRD` → PRD 경로의 파일 Read
- `TRD` → TRD 경로의 파일 Read
- `ALL` → PRD 경로 + TRD 경로 모두 Read

### STEP 3. 체크리스트 판정 수행

검증 대상에 따라 해당 체크리스트를 실행한다.
각 항목에 대해 문서 내용을 근거로 Pass / Fail을 판정하고, 판정 근거(`reason`)와 Fail 시 수정 제안(`suggestion`)을 기록한다.

#### PRD 검증 체크리스트 (P1~P6)

검증 대상이 `PRD` 또는 `ALL`일 때 수행한다.

| # | 항목 | 검증 기준 |
|---|------|-----------|
| P1 | Non-goals 섹션 존재 | 섹션이 있고 내용이 비어 있지 않음 |
| P2 | 타깃 유저 시나리오 형식 | `As a ... I want ... so that ...` 형식, 최소 1개 |
| P3 | 핵심 요구사항 Must 분류 | Must/Should/Nice-to-have 구분이 명시됨 |
| P4 | Acceptance Criteria 존재 | Must 핵심 기능당 최소 1개, GIVEN/WHEN/THEN 형식 |
| P5 | 모호한 표현 없음 | "빠르게", "쉽게", "적절히" 등 수량화 불가 표현 없음 |
| P6 | Open Questions 섹션 존재 | 섹션이 있고 "없음" 또는 구체적 항목이 기재됨 |

> **PRD 통과 기준**: P1~P6 전항 Pass. 1개라도 Fail이면 PRD Fail.

**Fail 시 수정 제안 예시**:
- P5 Fail → `"빠르게" → "200ms 이내"와 같이 수치화된 표현으로 대체`
- P4 Fail → `Must 기능 "{기능명}"에 대한 GIVEN/WHEN/THEN 형식의 Acceptance Criteria 추가 필요`

#### TRD 검증 체크리스트 (T1~T5)

검증 대상이 `TRD` 또는 `ALL`일 때 수행한다.

| # | 항목 | 검증 기준 |
|---|------|-----------|
| T1 | 기술 스택 버전 명시 | 주요 라이브러리/프레임워크에 버전이 명시됨 |
| T2 | 성능 요구사항 수치화 | 응답시간, 처리량 등이 수치로 명시됨 (미결 허용: "[미결: 수치 확정 필요]"로 표시된 경우 Pass) |
| T3 | 보안 요구사항 명시 | 인증/인가 방식이 구체적으로 기술됨 |
| T4 | PRD Must 기능 커버리지 | PRD의 Must 기능이 모두 TRD에 반영됨 |
| T5 | Open Questions 섹션 존재 | 섹션이 있고 "없음" 또는 구체적 항목이 기재됨 |

> **TRD 통과 기준**: T1~T5 전항 Pass. 1개라도 Fail이면 TRD Fail.

**Fail 시 수정 제안 예시**:
- T4 Fail → `PRD Must 기능 "{기능명}"에 대한 TRD 구현 방안 섹션 추가 필요`
- T1 Fail → `{라이브러리명}에 버전 명시 필요 (예: React 18.2.0)`

### STEP 4. 결과 구조화

항목별 판정 결과를 아래 출력 형식으로 정리한다.

### STEP 5. 결과 반환

구조화된 판정 결과를 오케스트레이터에 반환한다.

## 출력 인터페이스

```markdown
## 검증 결과

### 종합 판정
- PRD: Pass | Fail | (해당 없음)
- TRD: Pass | Fail | (해당 없음)
- 종합: Pass | Fail

### 상세 결과

| # | 항목 | 결과 | 사유 | 수정 제안 |
|---|------|------|------|----------|
| P1 | Non-goals 섹션 존재 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| P2 | 타깃 유저 시나리오 형식 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| P3 | 핵심 요구사항 Must 분류 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| P4 | Acceptance Criteria 존재 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| P5 | 모호한 표현 없음 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| P6 | Open Questions 섹션 존재 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| T1 | 기술 스택 버전 명시 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| T2 | 성능 요구사항 수치화 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| T3 | 보안 요구사항 명시 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| T4 | PRD Must 기능 커버리지 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| T5 | Open Questions 섹션 존재 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |

### Fail 항목 요약 (Fail 존재 시)
- [P{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
- [T{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
```

검증 대상에 포함되지 않는 항목(예: TRD만 검증 시 P1~P6)은 상세 결과 표에서 생략한다.

## opsdd 연동 가이드

현 단계에서는 PRD/TRD 체크리스트(P1~P6, T1~T5)만 구현한다.

opsdd SPEC 단계에서 spec.md 검증 시 동일 에이전트 활용 가능:
- 입력의 PRD/TRD 경로 대신 spec.md 경로를 전달
- 검증 대상으로 `SPEC`을 추가 지원하거나, 커스텀 체크리스트를 입력으로 받는 확장 인터페이스 예약

opsdd용 체크리스트는 opsdd 스킬 구현 시 이 SKILL.md에 추가한다.
