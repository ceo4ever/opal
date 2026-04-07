# QA-PLAN: Harness Observability — 행위 주체 표시 + Gate 상태 추적

> 검증 대상: `tasks/096-opp-harness-observability/PLAN.md`
> 참조 TASK: `tasks/096-opp-harness-observability/TASK.md`
> 작성일: 2026-04-07 | 검증자: op-task-qa (워커)

---

## 판정: **Pass** (조건부 권고 사항 포함)

---

## GP-1 즉시 실행 가능성

**결과: Pass**

각 Step에 파일 경로, 변경 위치(줄 번호/섹션), Before/After 코드가 명시되어 있다.

| Step | 파일 경로 | 줄 번호/섹션 | Before/After |
|------|----------|------------|-------------|
| Step 1 | `opal/core/references/opal-harness.md` §5 | 섹션명 명시 | After 전체 마크다운 블록 제공 |
| Step 2 | `opal/core/references/opal-harness.md` §3 | L170, L139, L151~L153, L316, L318~L321 | 5개 변경 모두 Before/After 명시 |
| Step 3 | `opal/core/references/opal-harness-interactive.md` §3 | L72, L78, L65~L81 이후 | Before/After + 신설 표 전체 제공 |
| Step 4 | `opal/core/references/opal-pm.md` §3/§4 | 섹션명 + Before 상태 설명 | After 마크다운 블록 제공 |
| Step 5 | `opal/core/AGENT.md` 보고 형식 | L188 이후 | Before/After 명시 |

**실제 파일 검증**: PLAN의 Before 코드를 실제 파일 내용과 대조한 결과:
- `opal-harness.md` L139: `| 단계 완료 | 오케스트레이터 | 완료 산출물 갱신, 상태: 대기 중 | **필수** |` — 일치
- `opal-harness.md` L151~L153: `진행 중 → 대기 중 → 완료 → 추가작업중 → 추가작업완료` — 일치
- `opal-harness.md` L170: `상태: {진행 중 / 대기 중 / 블로커 / 완료 / 추가작업중 / 추가작업완료}` — 일치
- `opal-harness.md` L316: `(단계 완료: '대기 중' / 다음 단계 진입: '진행 중')` — 일치
- `opal-harness-interactive.md` L72, L78: `상태` 필드가 `대기 중`인지 확인한다 — 일치
- `opal-pm.md` §3 워커 컨텍스트 주입 이후 종료: 일치
- `opal/core/AGENT.md` L188 `비서 모드에서는 별도 표시 없이 기존 보고 형식을 따른다.` — 일치

모든 Before 코드가 실제 파일과 정확히 일치함. 즉시 실행 가능한 수준.

---

## GP-2 의존성 순서

**결과: Pass**

PLAN §4 실행 체크리스트의 Step 의존 관계:

| Step | 의존 선언 | 타당성 |
|------|----------|------|
| Step 1 (opal-harness.md §5 신설) | 없음 | 타당 — 독립 변경 |
| Step 2 (opal-harness.md §3 상태값) | 없음 (Step 1과 병렬 가능) | 타당 — 독립 변경 |
| Step 3 (opal-harness-interactive.md) | Step 2 완료 후 | 타당 — harness §3 상태값 확정이 선행 필요 |
| Step 4 (opal-pm.md) | Step 1 완료 후 | 타당 — harness §5 정의 후 참조 |
| Step 5 (AGENT.md) | Step 1 완료 후 | 타당 — harness §5 참조 포함 |

Step 1/2는 병렬 실행 가능하며 명시됨. Step 3은 Step 2 이후, Step 4/5는 Step 1 이후로 의존 관계가 논리적으로 타당하다.

---

## GP-3 TASK 반영

**결과: Pass**

TASK.md 요구사항과 PLAN Step의 1:1 매핑:

| TASK 요구사항 | PLAN Step | 매핑 |
|-------------|----------|------|
| [A] `harness §Observability 신설` — 3개 선언 형식 정의 | Step 1 (A-1) | 완전 매핑 |
| [A] `opal-pm.md 갱신` — Observability 규칙 | Step 4 (A-2) | 완전 매핑 |
| [A] `AGENT.md 보고 형식 갱신` | Step 5 (A-3) | 완전 매핑 |
| [B] `harness §3 상태값 확장` — 대기 중 → Gate별 세분화 | Step 2 (B-1) 변경1~3 | 완전 매핑 |
| [B] `harness §3 State Gate 강화` — 이전 단계 `완료` 확인 | Step 2 (B-1) 변경4~5 | 완전 매핑 |
| [B] `harness-interactive §3 강화` — Gate별 상태 전이 | Step 3 (B-2) | 완전 매핑 |

6개 요구사항 모두 대응 Step 존재. 누락 없음.

---

## GP-4 파일 목록 완전성

**결과: Pass**

| TASK.md 지정 파일 | PLAN §7 변경 파일 목록 |
|-----------------|---------------------|
| `opal/core/references/opal-harness.md` | 포함 |
| `opal/core/references/opal-harness-interactive.md` | 포함 |
| `opal/core/references/opal-pm.md` | 포함 |
| `opal/core/AGENT.md` | 포함 |

TASK.md가 지정한 4개 파일과 PLAN §7의 변경 파일 목록이 완전히 일치한다. 추가/누락 파일 없음.

---

## GP-5 설계 구체성

**결과: Pass (권고 사항 1건)**

### `대기 중` 제거 결정 근거

PLAN §2에서 근거를 명시함:
- "`대기 중`은 '어떤 Gate를 기다리는 중인가'를 표현하지 못함"
- "Gate 세분화로 기존 역할이 `QA Gate 대기`로 대체됨"
- 기존 `완료 / 진행 중 / 블로커` 의미 유지
- `추가작업중 / 추가작업완료`는 독립 유지

근거가 명확하며 의사결정 맥락이 구체적으로 서술됨.

### Gate별 상태 전이 완결성

PLAN §2의 새 상태 전이 흐름:
```
진행 중 → QA Gate 대기 → PM Gate 대기 → 사용자 확인 대기 → 완료
완료 → 추가작업중 → 추가작업완료
```

harness-interactive.md §3 Step B-2에서 정의한 Gate 전이 표:
- QA Gate 통과: `QA Gate 대기` → `PM Gate 대기`
- PM Gate 통과: `PM Gate 대기` → `사용자 확인 대기`
- 사용자 확인 완료: `사용자 확인 대기` → `완료`

전이 체계가 완결하며 일관성 있음.

**권고 사항 (권고-1)**: PLAN에서 `단계 시작` 이벤트 시 상태값 `진행 중`으로 설정하는 것은 현재 이벤트 테이블(L138)에 이미 명시되어 있으나, `QA Gate 대기 → PM Gate 대기` 전이 트리거가 하네스 이벤트 테이블에 별도 행으로 추가되지 않음. Step 2 변경 2(이벤트 테이블 `단계 완료` 행 수정)만 다루며, QA Gate 통과/PM Gate 통과 이벤트가 이벤트 테이블에 추가되지 않는다. 실행 단계에서 검토 권장 (기능 차단 수준 아님).

---

## GP-6 리스크 처리

**결과: Pass (권고 사항 1건)**

### R1: 레거시 호환 (대기 중 → QA Gate 대기)

PLAN §6 R1에서 위험을 인지하고 있으며 대응 방안 2가지를 제시:
1. 하네스 State Gate에서 `대기 중`을 레거시 값으로 허용하는 호환 규칙 추가
2. 변경이력에 마이그레이션 안내 추가

**권고 사항 (권고-2)**: 두 대응 중 어느 쪽을 선택할지 PLAN에서 확정하지 않고 "권장"으로 열어둠. 실행 Step 2에도 레거시 허용 규칙 추가가 체크리스트 항목으로 포함되지 않음. 실행 워커가 이 결정을 누락할 수 있으므로, Step 2 체크리스트에 "레거시 허용 노트 추가" 항목을 명시하거나 설계를 확정할 것을 권장. (현재 진행 중인 태스크 094, 095의 STATE.md가 `대기 중` 상태일 경우 즉각적인 영향 가능성)

### R2: opsdd/opwt 범위 제외

PLAN §6 R2에서 "TASK.md 제약에서 명시적으로 제외되어 있음"으로 처리. opal-harness.md에 주석 추가 권장을 언급함. 기능 차단 위험 없음.

### R3: 행위 주체 선언 노이즈

PLAN §6 R3에서 연속 동종 툴 호출 시 허용 조항 추가 검토를 언급하나, 구현 시 결정으로 열어둠. Step 1 체크리스트에 항목 없음. Step 1 실행 시 판단이 필요한 사항이나 기능 영향 없음.

### R4: 변경이력 누락

PLAN §6 R4에서 대응을 QA 체크리스트에 반영함. QA 체크리스트 §5 "문서 품질" 항목에 "변경이력(opal-harness.md, opal-harness-interactive.md)이 v+1로 갱신되었는가"가 포함됨. 적절한 대응.

---

## 종합 지적 사항

### 경고 (실행 전 확인 권장)

| # | 지적 | 관련 항목 | 영향도 |
|---|------|---------|-------|
| 1 | R1 레거시 허용 규칙의 확정 미비: Step 2 체크리스트에 항목 없음. 진행 중인 태스크(094, 095)의 `대기 중` 상태 STATE.md가 즉각 영향받을 수 있음 | GP-6 R1, Step 2 | 중 |
| 2 | QA Gate 통과/PM Gate 통과 이벤트가 opal-harness.md 이벤트 테이블에 추가되지 않음. 상태 전이를 트리거하는 이벤트가 테이블에 미반영 | GP-5, Step 2 | 낮음 |

### 정보성 메모 (실행 차단 없음)

| # | 메모 | 관련 항목 |
|---|------|---------|
| 1 | R3 연속 호출 허용 조항은 Step 1 실행 시 판단. PLAN에서 열어둔 점은 의도적이며 수용 가능 | GP-6 R3 |
| 2 | opal-harness-interactive.md L65~L81의 "Gate별 상태 전이 표"를 삽입할 정확한 위치가 "State Gate 확인 섹션 뒤, 체크리스트 갱신 상태 확인 섹션 앞"으로 명시되어 있어 명확 | GP-1 |

---

## 검증 요약

| 항목 | 결과 |
|------|------|
| GP-1 즉시 실행 가능성 | Pass |
| GP-2 의존성 순서 | Pass |
| GP-3 TASK 반영 | Pass |
| GP-4 파일 목록 완전성 | Pass |
| GP-5 설계 구체성 | Pass (권고-1) |
| GP-6 리스크 처리 | Pass (권고-2) |

**최종 판정: Pass**

권고 사항 2건은 실행을 차단하지 않으나, 실행 워커에게 전달하면 품질을 높일 수 있다. 특히 권고-2(R1 레거시 허용 규칙 확정)는 현재 진행 중인 태스크에 즉각 영향이 있을 수 있으므로 실행 단계 초반에 결정할 것을 권장한다.
