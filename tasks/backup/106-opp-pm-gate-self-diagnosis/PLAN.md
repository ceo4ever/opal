# PLAN: Artifact Gate 제거 + PM Gate 자가 진단 통합

> 태스크: 106 — opp-pm-gate-self-diagnosis
> 작성일: 2026-04-10

---

## §1 배경 분석

### 1.1 Artifact Gate 현재 위치 (파일별 라인번호)

#### opal-harness-interactive.md

| 라인 | 내용 |
|------|------|
| 40~67 | §2.5 Artifact Gate 전체 섹션 (28줄) |
| 35 | §2 QA Gate 완료 텍스트: "갱신 확인 후 Artifact Gate로 진입한다." (§3 PM Gate 진입 전 Artifact Gate 언급) |
| 63~65 | Artifact Gate 완료 후 State Gate + PM Gate 진입 지시 |

§2.5 섹션 제거 대상: 라인 40~67 (헤더 `## 2.5 Artifact Gate (2중 안전장치)`부터 `---`까지).

§2 QA Gate 완료 문구 변경 필요:
- 현재 (라인 35): `갱신 확인 후 Artifact Gate로 진입한다.`
- 변경 후: `갱신 확인 후 PM Gate로 진입한다.`

§5 Gate Fail 공통 처리 테이블에서 Artifact Gate 행 제거 필요:
- 라인 134: `| Artifact Gate | 산출물 파일 미존재/비어있음 | QA 에이전트 재소환 | 1회 |`

#### opal-harness.md

| 라인 | 내용 |
|------|------|
| 157 | 이벤트 테이블: `| Artifact Gate 통과 | PM | Artifact Gate 행 → ✅ | - | **필수** |` |
| 158 | 이벤트 테이블: `| State Gate (Artifact 직후) | PM | State Gate 행 → ✅ | - | **필수** |` |
| 221 | 진행 현황 행 구성 규칙: `Artifact Gate`, `State Gate` 포함 |
| 232 | 산출물 행 규칙 5번: `QA 산출물 행: QA Gate 직후, Artifact Gate 직전에 위치` |
| 245, 254, 262 | opsdd 진행 현황 예시 중 Artifact Gate 행 (#7, #16, #24) |
| 405 | State Gate 섹션: `Gate 위치: QA Gate → Artifact Gate → **State Gate** → PM Gate` |
| 427 | 표준 Gate 순서 문구: `→ Artifact Gate (하네스 §2.5 참조)` |

#### opal-pilot-project/SKILL.md (opp)

| 라인 | 내용 |
|------|------|
| 44 | PLAN 완료 후 Gate 순서: `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` |
| 77 | EXECUTE 완료 후 Gate 순서: `2. **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` |
| 116~119 | 진행 현황 행 예시: PLAN Artifact Gate (#9), EXECUTE Artifact Gate (#18) |

#### opal-pilot-dev/SKILL.md (opd)

| 라인 | 내용 |
|------|------|
| 42 | ANALYSIS Gate 순서: `→ **Artifact Gate** (ANALYSIS.md 존재 확인) → **State Gate**` |
| 86 | PLAN Gate 순서: `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` |
| 172~175 | 진행 현황 행 예시: ANALYSIS Artifact Gate (#7), PLAN Artifact Gate (#20) |

> 주의: opd v2.6(태스크 107)에서 ANALYSIS Gate가 슬림화되어 State Gate + Artifact Gate만 유지됨. 그러나 태스크 106 범위에서는 해당 Artifact Gate 행도 제거한다.

#### opal-pilot-dev-short/SKILL.md (opds)

| 라인 | 내용 |
|------|------|
| 56 | PLAN Gate 순서: `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` |
| 169~173 | 진행 현황 행 예시: PLAN Artifact Gate (#12) |

#### opal-pilot-dev-wireframe/SKILL.md (opdw)

| 라인 | 내용 |
|------|------|
| 52 | WIREFRAME Gate 순서: `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` |
| 96~98 | 진행 현황 행 예시: WIREFRAME Artifact Gate (#9), EXECUTE에는 Artifact Gate 없음 |

> EXECUTE 단계 (라인 71~73)에는 이미 Artifact Gate가 없음 — 변경 불필요.

#### opal-pilot-write-tech/SKILL.md (opwt)

| 라인 | 내용 |
|------|------|
| 149 | PLAN 공통 게이트: `**Artifact Gate** (하네스 §2.5 참조) → **State Gate**` |
| 없음 | EXECUTE 배치 게이트에는 이미 Artifact Gate 없음 (v2.7에서 제거됨) |
| 없음 | STATE.md 도메인 치환값에 진행 현황 행 예시 없음 (네트워크 확장 섹션만 존재) |

> opwt는 STATE.md 진행 현황 행 예시가 없어 예시 테이블 수정은 불필요.
> ANALYSIS 게이트(라인 110)의 `Artifact Gate`는 PM 자가 체크 항목으로 별도 표현됨 → 이것은 자가 진단 방식이므로 제거 불필요. PLAN 공통 게이트의 `Artifact Gate`만 제거.

#### opal-pilot-sdd/SKILL.md (opsdd)

| 라인 | 내용 |
|------|------|
| 300~303 | 진행 현황 행: SPEC Artifact Gate (#7), REVIEW Artifact Gate (#16), DESIGN Artifact Gate (#24) |

> 105 태스크에서 Artifact Gate 행이 추가된 상태. 이번 태스크에서 제거 필요.

---

### 1.2 현재 Gate 패턴 (파일별)

| 파일 | 단계 | 현재 패턴 |
|------|------|----------|
| opp | PLAN/EXECUTE | QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate → 사용자 확인 |
| opd | ANALYSIS | State Gate → Artifact Gate → State Gate → PM Gate → State Gate |
| opd | PLAN | QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate |
| opds | PLAN | State Gate → QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate |
| opdw | WIREFRAME | QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate |
| opdw | EXECUTE | QA Gate → State Gate → PM Gate → State Gate (Artifact Gate 없음 — 정상) |
| opwt | PLAN | QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate |
| opwt | EXECUTE 배치 | QA Gate → State Gate → PM Gate → State Gate (Artifact Gate 없음 — 정상) |
| opsdd | SPEC/REVIEW/DESIGN | State Gate → Artifact Gate → State Gate → PM Gate → State Gate |

**목표 패턴 (Artifact Gate 제거 후)**:
- QA Gate 있는 단계: `작업 → 산출물 생성 → QA Gate → QA산출물 생성 → State Gate → PM Gate → State Gate → 사용자 확인`
- QA Gate 없는 단계: `작업 → 산출물 생성 → State Gate → PM Gate → State Gate → 사용자 확인`

---

### 1.3 opds TEST-SCENARIO 행 순서 이상

현재 opds SKILL.md 진행 현황 행 예시 (라인 155~185):

```
# 4 | PLAN | 작업
# 5 | PLAN | PLAN.md 생성
# 6 | TEST-SCENARIO | 작업
# 7 | TEST-SCENARIO | TEST-SCENARIO.md 생성
# 8 | TEST-SCENARIO | State Gate
# 9 | PLAN | QA Gate          ← PLAN이 TEST-SCENARIO 뒤에 등장
# 10 | PLAN | QA-PLAN.md 생성
# 11 | PLAN | State Gate
# 12 | PLAN | Artifact Gate   ← 제거 대상
# 13 | PLAN | State Gate
# 14 | PLAN | PM Gate
# 15 | PLAN | State Gate
# 16 | PLAN | 사용자 확인
```

이상 분석:
- PLAN 작업 (#4) 완료 후 PLAN.md 생성 (#5) → TEST-SCENARIO 작업 (#6) → TEST-SCENARIO.md 생성 (#7) → State Gate (#8) → PLAN QA Gate (#9) 순서
- 이는 opds 스킬 본문(라인 53~58)과 일치: "두 워커 완료 → State Gate → QA Gate → ..."
- 즉 TEST-SCENARIO State Gate(#8)가 PLAN QA Gate(#9) 앞에 위치하는 것이 정상 순서
- 단, 단계 레이블이 `TEST-SCENARIO | State Gate` → `PLAN | QA Gate`로 전환되어 혼란스러울 수 있으나, 실제 게이트 순서 자체는 맞음
- **실제 이상**: PLAN QA Gate가 있는데 QA-PLAN.md 생성 후 `Artifact Gate`(#12)가 존재함. 이 행을 제거하면 올바른 순서가 됨

---

### 1.4 opd ANALYSIS Gate 주의사항

opd v2.6(태스크 107) 변경이력에 "ANALYSIS Gate 슬림화 — QA·PM Gate 제거, State Gate + Artifact Gate만 유지" 기재됨. 현재 SKILL.md 라인 41~44 ANALYSIS Gate:

```
→ **State Gate**
→ **Artifact Gate** (ANALYSIS.md 존재 확인) → **State Gate**
→ **PM Gate** (분석 방향 종합 검토) → **State Gate**
```

v2.6 변경이력이 있으나 실제 파일에는 PM Gate가 여전히 존재함. 이 태스크(106)에서는 Artifact Gate만 제거하고, PM Gate는 유지한다.

---

## §2 구현 전략

### 2.1 적용 순서 (의존관계 고려)

1. **R-1** `opal-harness-interactive.md` — 하네스 핵심 문서 먼저 수정 (알고리즘 SSOT 확립)
   - §2 QA Gate 완료 문구 수정 (Artifact Gate → PM Gate)
   - §2.5 Artifact Gate 섹션 전체 제거
   - §3 PM Gate에 5단계 자가 진단 절차 추가 (알고리즘/데이터 분리 구조 — §2.3 완성 텍스트 사용)
   - §4 체크리스트 검증 게이트 섹션 전체 제거 (PM Gate 자가 진단 4단계에 통합됨 — R-1-3)
   - §5(→제거 후 §4) Gate Fail 공통 처리에서 Artifact Gate 행 제거
   - 변경이력 추가

2. **R-2** `opal-harness.md` — 공통 하네스 수정 + R-4 파이프라인 현황판 이름 변경
   - §3 `진행 현황 행 구성 규칙` → `파이프라인 현황판 행 구성 규칙` (R-4)
   - §3 파이프라인 현황판 행 구성 규칙에서 Artifact Gate 제거
   - §3 이벤트 테이블에서 Artifact Gate 행 2개 제거 + `진행 현황 행` → `파이프라인 현황판 행` (R-4)
   - §3 산출물 행 규칙 5번 수정 (Artifact Gate 언급 제거)
   - §3 opsdd 진행 현황 예시에서 Artifact Gate 행 제거 + 번호 재정렬
   - State Gate 섹션 Gate 위치 문구 수정
   - 표준 Gate 순서 문구 수정
   - 변경이력 추가

3. **R-3** 6개 SKILL.md — 각 스킬 수정 (순서 독립, 병렬 가능)
   - Artifact Gate 제거 + `## PM Gate 점검 목록` 섹션 추가 + `파이프라인 현황판` 이름 변경 (R-4)
   - opp, opd, opds, opdw, opwt, opsdd 순으로 적용

### 2.2 R-1 상세 변경 내용 (알고리즘/데이터 분리 구조)

**설계 원칙**:
- **하네스** = 알고리즘 SSOT (PM Gate 자가 진단 절차 — "어떻게 점검할 것인가")
- **SKILL.md** = 데이터 선언 (`## PM Gate 점검 목록` 섹션 — "무엇을 점검할 것인가")
- PM은 하네스에서 절차를 읽고, 하네스 절차가 SKILL.md Read를 강제하여 스킬별 데이터를 조회한다

#### harness-interactive.md §2 QA Gate 수정

- 라인 35: `갱신 확인 후 Artifact Gate로 진입한다.` → `갱신 확인 후 PM Gate로 진입한다.`

#### harness-interactive.md §2.5 제거

제거 범위:
```
## 2.5 Artifact Gate (2중 안전장치)
...
---
```
(라인 40~67, `---` 포함)

#### harness-interactive.md §3 PM Gate — 자가 진단 절차 교체

현재 §3 PM Gate 본문 (공통 Phase별 점검 테이블 방식):
```
`.opal/AGENT.md`가 존재하면 PM 검토 기준으로 산출물을 검토한다.
상세: `opal-pm.md` §4 "PM 검토 게이트" 참조.
AGENT.md 미존재 시 스킵.
```

변경 후: 위 내용 유지 + **알고리즘/데이터 분리 구조 기반 5단계 자가 진단 절차** 추가 (§2.3 완성 텍스트 사용).

핵심 차이점:
- **이전**: 하네스에 Phase별 점검 테이블 내장 + SKILL.md에 "오버라이드" 섹션 (예외 처리 방식)
- **변경**: 하네스에 절차(알고리즘)만 → SKILL.md의 `## PM Gate 점검 목록` 섹션을 Read하여 데이터 조회 (분리 구조)

#### harness-interactive.md §4 체크리스트 검증 게이트 처리 (R-1-3)

§4 내용(라인 102~115)을 검토한 결과:
- Artifact Gate 직접 언급은 없으나, TASK.md R-1-3에서 §4를 PM Gate(§3)로 통합하거나 제거할 것을 요구한다.
- §4의 내용(체크리스트 갱신 2단계 보장)은 §3 PM Gate 자가 진단 내의 4단계(체크리스트 위치 Read → `[ ]` 없음 확인)로 이미 통합된다.
- 따라서 **§4 섹션 전체 제거** (PM Gate 자가 진단에 체크리스트 확인이 통합되었으므로 별도 섹션 불필요).
- §4 제거 후 §5가 §4로 번호 재조정 필요.

#### harness-interactive.md §5(→제거 후 §4) Gate Fail 공통 처리

재소환·재지시 처리 테이블에서 Artifact Gate 행 제거:
```
| Artifact Gate | 산출물 파일 미존재/비어있음 | QA 에이전트 재소환 | 1회 |
```

§5 사용자 에스컬레이션 조건에서 Artifact Gate 관련 항목 제거:
```
- Artifact Gate 재소환 후 산출물 미생성
```

### 2.3 PM Gate 자가 진단 완성 텍스트 (실행 기준)

#### harness-interactive.md §3에 들어갈 절차

```markdown
### PM Gate 자가 진단 절차

PM Gate 진입 시 아래 순서로 자가 진단을 수행한다.

1. **STATE.md Read** → 현재 Phase 파악
2. **SKILL.md `## PM Gate 점검 목록` 섹션 Read** → 해당 Phase의 산출물·체크리스트 위치 확인
3. **각 산출물 Read** → 존재 여부 + 내용 비어있지 않음 확인
4. **체크리스트 Read → `[ ]` 발견 시 내용 기반 판단**:
   - 해당 항목과 관련된 산출물을 Read하여 실제 완료 여부를 내용으로 판단
   - 완료 확인 → `[x]`로 직접 갱신
   - 미완료 확인 → 미완료 항목 목록에 추가 (이유 포함)
5. **판정**:
   - 미완료 항목 없음 → PM 검토 기준(`opal-pm.md §4`) 수행으로 진행
   - 미완료 항목 있음 → 항목별 이유 명시 후 사용자 보고 (에이전트 재호출 없음)

> **설계 의도**: `[ ]` 발견 시 에이전트를 재호출하지 않는다. PM이 직접 내용을 읽고 판단하여 오탐을 걸러내고, 진짜 미완료 항목만 사용자에게 올린다.
```

**차단 원칙**: 점검 항목 중 하나라도 미완료이면 PM Gate 본 검토(AGENT.md 기준)로 진입하지 않는다.

#### 각 SKILL.md에 추가할 `## PM Gate 점검 목록` 섹션 (스킬별 데이터)

| 스킬 | Phase | 산출물 | 체크리스트 위치 |
|------|-------|-------|----------------|
| opp | PLAN | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
| opp | EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
| opd | ANALYSIS | ANALYSIS.md | - |
| opd | PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md §3, §4 |
| opd | EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
| opds | PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md §3, §4 |
| opds | EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
| opdw | WIREFRAME | wireframe.md, QA-WIREFRAME.md | - |
| opdw | EXECUTE | QA-EXECUTE.md | - |
| opwt | PLAN | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
| opwt | EXECUTE | QA-EXECUTE.md | - |
| opsdd | SPEC | SPEC.md, QA-SPEC.md | - |
| opsdd | DESIGN | SPEC-PLAN.md | - |
| opsdd | EXECUTE | QA-EXECUTE.md | PLAN.md §3 |

각 SKILL.md에 삽입할 섹션 형식 (opp 예시):

```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
```

> 체크리스트가 없는 Phase는 체크리스트 위치를 `-`로 표기.

**설계 근거**:
- Artifact Gate가 독립 §2.5로 분리되어 있어 "Gate 순서" 행이 STATE.md에 별도 추가됨 → 복잡도 증가의 원인
- PM Gate 내부 자가 진단으로 통합하면 Gate 행 수 감소 + PM Gate가 산출물 확인 책임까지 포함
- 하네스에 공통 Phase 테이블을 내장하던 이전 방식은 스킬별 예외(opwt ANALYSIS, opsdd REVIEW 등) 증가로 확장성 저하
- **알고리즘/데이터 분리**: 하네스 절차(알고리즘)는 변경 없이 SKILL.md 데이터(점검 목록)만 추가/수정하면 새 스킬에 즉시 대응 가능

### 2.4 R-2 harness.md §3 변경 위치 (Artifact Gate 제거 + 파이프라인 현황판 이름 변경)

#### Artifact Gate 제거

| 위치 | 변경 내용 |
|------|----------|
| 라인 157~158 | 이벤트 테이블에서 `Artifact Gate 통과` 행, `State Gate (Artifact 직후)` 행 제거 |
| 라인 221 | 진행 현황 행 구성 규칙에서 `Artifact Gate`, `State Gate` (Artifact 직후 한 개) 제거 |
| 라인 232 | 산출물 행 규칙 5번: `QA 산출물 행: QA Gate 직후, Artifact Gate 직전에 위치` → `QA 산출물 행: QA Gate 직후에 위치` |
| 라인 245 (#7), 254 (#16), 262 (#24) | opsdd 진행 현황 예시에서 각 Phase Artifact Gate 행 제거 + 이후 번호 재정렬 |
| 라인 405 | State Gate 위치 문구: `QA Gate → Artifact Gate → **State Gate** → PM Gate` → `QA Gate → **State Gate** → PM Gate` |
| 라인 427 | 표준 Gate 순서 문구: `→ Artifact Gate (하네스 §2.5 참조)` 줄 제거 |

#### R-4: `## 파이프라인 현황판` 이름 변경

**변경 범위**:
- 모든 STATE.md 템플릿의 `## 진행 현황` → `## 파이프라인 현황판`
- harness.md §3 섹션 제목/규칙명: `진행 현황 행 구성 규칙` → `파이프라인 현황판 행 구성 규칙`
- State Gate 및 이벤트 테이블 참조 문구: `진행 현황 행` → `파이프라인 현황판 행`

**적용 대상 파일**:

| 파일 | 변경 위치 | 변경 내용 |
|------|----------|----------|
| `opal-harness.md` | §3 섹션 헤더 및 규칙명 | `진행 현황` → `파이프라인 현황판` (제목·참조 모두) |
| `opal-harness.md` | 이벤트 테이블 `진행 현황 행` 컬럼값 | → `파이프라인 현황판 행` |
| `opal-harness.md` | STATE.md 템플릿 섹션 헤더 (라인 199) | `## 진행 현황` → `## 파이프라인 현황판` |
| `opal-harness-interactive.md` | 각 Gate 완료 즉시 문구 및 §5 순서 강제 원칙 내 `진행 현황 테이블` | → `파이프라인 현황판 테이블` |
| 각 SKILL.md | STATE.md 도메인 치환값 섹션 헤더 | `## 진행 현황` → `## 파이프라인 현황판` |

**이름 변경 근거**: "진행 현황"은 상태 모니터링 의미이지만, 이 섹션은 태스크 파이프라인의 각 단계(Phase·Gate·산출물)를 행 단위로 추적하는 현황판 역할을 수행한다. "파이프라인 현황판"이 실제 기능을 더 명확히 표현한다.

### 2.5 R-3 각 SKILL.md 변경 위치 (Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가)

#### opp (opal-pilot-project/SKILL.md)

**Artifact Gate 제거**:

| 위치 | 현재 | 변경 후 |
|------|------|---------|
| 라인 44 | `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` | 해당 줄 제거 |
| 라인 78 | `2. **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` | 해당 줄 제거, 번호 재조정 |
| 진행 현황 행 #9, #18 | `Artifact Gate` 행 | 해당 행 제거 + 이후 번호 재정렬 |

PLAN 진행 현황 (현재 → 변경 후):
```
현재: ... QA-PLAN.md 생성(#7) → State Gate(#8) → Artifact Gate(#9) → State Gate(#10) → PM Gate(#11) → State Gate(#12) → 사용자 확인(#13)
변경: ... QA-PLAN.md 생성(#7) → State Gate(#8) → PM Gate(#9) → State Gate(#10) → 사용자 확인(#11)
```

EXECUTE 진행 현황 (현재 → 변경 후):
```
현재: ... QA-EXECUTE.md 생성(#16) → State Gate(#17) → Artifact Gate(#18) → State Gate(#19) → PM Gate(#20) → DONE.md 생성(#21) → State Gate(#22) → 사용자 확인(#23)
변경: ... QA-EXECUTE.md 생성(#14) → State Gate(#15) → PM Gate(#16) → DONE.md 생성(#17) → State Gate(#18) → 사용자 확인(#19)
```

**PM Gate 점검 목록 섹션 추가**:

```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
```

#### opd (opal-pilot-dev/SKILL.md)

**Artifact Gate 제거**:

| 위치 | 현재 | 변경 후 |
|------|------|---------|
| 라인 42 | `→ **Artifact Gate** (ANALYSIS.md 존재 확인) → **State Gate**` | 해당 줄 제거 |
| 라인 86 | `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` | 해당 줄 제거 |
| 진행 현황 행 #7(ANALYSIS), #20(PLAN) | `Artifact Gate` 행 | 해당 행 제거 + 이후 번호 재정렬 |

ANALYSIS 진행 현황 (현재 → 변경 후):
```
현재: ANALYSIS.md 생성(#5) → State Gate(#6) → Artifact Gate(#7) → State Gate(#8) → PM Gate(#9) → State Gate(#10) → 사용자 확인(#11)
변경: ANALYSIS.md 생성(#5) → State Gate(#6) → PM Gate(#7) → State Gate(#8) → 사용자 확인(#9)
```

PLAN 진행 현황 (현재 → 변경 후):
```
현재: ... QA-PLAN.md 생성(#18) → State Gate(#19) → Artifact Gate(#20) → State Gate(#21) → PM Gate(#22) → State Gate(#23) → 사용자 확인(#24)
변경: ... QA-PLAN.md 생성(#16) → State Gate(#17) → PM Gate(#18) → State Gate(#19) → 사용자 확인(#20)
```

전체 번호 재정렬 후 최종 행 수: 기존 35행 → 33행 (ANALYSIS Artifact Gate 1개, PLAN Artifact Gate 1개 제거)

**PM Gate 점검 목록 섹션 추가**:

```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| ANALYSIS | ANALYSIS.md | - |
| PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
```

#### opds (opal-pilot-dev-short/SKILL.md)

**Artifact Gate 제거**:

| 위치 | 현재 | 변경 후 |
|------|------|---------|
| 라인 56 | `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` | 해당 줄 제거 |
| 진행 현황 행 #12 | `PLAN \| Artifact Gate` 행 | 해당 행 제거 + 이후 번호 재정렬 |

PLAN 진행 현황 (현재 → 변경 후):
```
현재: QA-PLAN.md 생성(#10) → State Gate(#11) → Artifact Gate(#12) → State Gate(#13) → PM Gate(#14) → State Gate(#15) → 사용자 확인(#16)
변경: QA-PLAN.md 생성(#10) → State Gate(#11) → PM Gate(#12) → State Gate(#13) → 사용자 확인(#14)
```

전체 번호 재정렬 후 최종 행 수: 기존 27행 → 26행 (PLAN Artifact Gate 1개 제거)

**PM Gate 점검 목록 섹션 추가**:

```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN+TEST-SCENARIO | PLAN.md, TEST-SCENARIO.md, QA-PLAN.md | PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
```

#### opdw (opal-pilot-dev-wireframe/SKILL.md)

**Artifact Gate 제거**:

| 위치 | 현재 | 변경 후 |
|------|------|---------|
| 라인 52 | `→ **Artifact Gate** (하네스 §2.5 참조) → **State Gate**` | 해당 줄 제거 |
| 진행 현황 행 #9 | `WIREFRAME \| Artifact Gate` 행 | 해당 행 제거 + 이후 번호 재정렬 |

WIREFRAME 진행 현황 (현재 → 변경 후):
```
현재: QA-WIREFRAME.md 생성(#7) → State Gate(#8) → Artifact Gate(#9) → State Gate(#10) → PM Gate(#11) → State Gate(#12) → 사용자 확인(#13)
변경: QA-WIREFRAME.md 생성(#7) → State Gate(#8) → PM Gate(#9) → State Gate(#10) → 사용자 확인(#11)
```

전체 번호 재정렬 후 최종 행 수: 기존 21행 → 20행 (WIREFRAME Artifact Gate 1개 제거)

> EXECUTE 단계에 이미 Artifact Gate 없음 → 변경 불필요.

**PM Gate 점검 목록 섹션 추가**:

```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| WIREFRAME | wireframe.md, QA-WIREFRAME.md | - |
| EXECUTE | QA-EXECUTE.md | - |
```

#### opwt (opal-pilot-write-tech/SKILL.md)

**Artifact Gate 제거**:

| 위치 | 현재 | 변경 후 |
|------|------|---------|
| 라인 149 | `**Artifact Gate** (하네스 §2.5 참조) → **State Gate**` | 해당 줄 제거 |

> STATE.md 도메인 치환값에 진행 현황 행 예시 없음 → 예시 테이블 수정 불필요.
> ANALYSIS 게이트(라인 110): `Artifact Gate: ANALYSIS.md 파일이 존재하고 내용이 있는지 확인한다` — 이는 PM 자가 체크 항목 내부의 서브체크이므로 제거하지 않음. (별도 Gate 행이 아닌 PM 자가 점검 항목)

**PM Gate 점검 목록 섹션 추가**:

```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN | PLAN.md, QA-PLAN.md | PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | - |
```

#### opsdd (opal-pilot-sdd/SKILL.md)

**Artifact Gate 제거**:

| 위치 | 현재 | 변경 후 |
|------|------|---------|
| 진행 현황 행 #7 | `SPEC \| Artifact Gate` | 해당 행 제거 |
| 진행 현황 행 #16 | `REVIEW \| Artifact Gate` | 해당 행 제거 |
| 진행 현황 행 #24 | `DESIGN \| Artifact Gate` | 해당 행 제거 |

SPEC 진행 현황 (현재 → 변경 후):
```
현재: SPEC.md 생성(#5) → State Gate(#6) → Artifact Gate(#7) → State Gate(#8) → PM Gate(#9) → State Gate(#10) → 사용자 확인(#11)
변경: SPEC.md 생성(#5) → State Gate(#6) → PM Gate(#7) → State Gate(#8) → 사용자 확인(#9)
```

전체 번호 재정렬 후 최종 행 수: 기존 43행 → 40행 (각 Phase Artifact Gate 3개 제거)

> opsdd SKILL.md에는 Gate 순서 문구(본문)에 Artifact Gate 언급 없음 — 진행 현황 테이블만 수정.

**PM Gate 점검 목록 섹션 추가**:

```markdown
## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| SPEC | SPEC.md, QA-SPEC.md | - |
| DESIGN | SPEC-PLAN.md | - |
| EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
```

---

## §3 실행 체크리스트

### R-1: opal-harness-interactive.md

- [x] §2 QA Gate 완료 문구: `Artifact Gate로 진입한다` → `PM Gate로 진입한다`
- [x] §2.5 Artifact Gate 섹션 전체 제거 (라인 40~67, `---` 포함)
- [x] §3 PM Gate에 5단계 자가 진단 절차 추가 (§2.3 완성 텍스트 사용 — 알고리즘/데이터 분리 구조)
- [x] §4 체크리스트 검증 게이트 섹션 전체 제거 (PM Gate 자가 진단 4단계에 통합 — R-1-3)
- [x] §5(→제거 후 §4) 재소환·재지시 처리 테이블에서 `Artifact Gate` 행 제거
- [x] §5(→제거 후 §4) 사용자 에스컬레이션 조건에서 `Artifact Gate 재소환 후 산출물 미생성` 항목 제거
- [x] R-4: 각 Gate 완료 즉시 문구 + §5 순서 강제 원칙 내 `진행 현황 테이블` → `파이프라인 현황판 테이블` (§2.4 적용 대상 파일 테이블 참조)
- [x] 변경이력 추가 (v2.2)

### R-2: opal-harness.md

- [x] §3 이벤트 테이블 `Artifact Gate 통과` 행 제거
- [x] §3 이벤트 테이블 `State Gate (Artifact 직후)` 행 제거
- [x] §3 `진행 현황 행 구성 규칙` → `파이프라인 현황판 행 구성 규칙` 이름 변경 (R-4)
- [x] §3 파이프라인 현황판 행 구성 규칙에서 `Artifact Gate`, `State Gate` (Artifact 직후) 제거
- [x] §3 산출물 행 규칙 5번 수정 (`Artifact Gate 직전` → `QA Gate 직후`)
- [x] §3 이벤트 테이블 참조 문구 `진행 현황 행` → `파이프라인 현황판 행` (R-4)
- [x] §3 opsdd 진행 현황 예시 SPEC #7 Artifact Gate 행 제거 + 이후 번호 재정렬
- [x] §3 opsdd 진행 현황 예시 REVIEW #16 Artifact Gate 행 제거 + 이후 번호 재정렬
- [x] §3 opsdd 진행 현황 예시 DESIGN #24 Artifact Gate 행 제거 + 이후 번호 재정렬
- [x] State Gate 섹션 Gate 위치 문구 수정 (`Artifact Gate →` 제거)
- [x] 표준 Gate 순서 문구에서 `→ Artifact Gate (하네스 §2.5 참조)` 줄 제거
- [x] R-4: STATE.md 템플릿 섹션 헤더 `## 진행 현황` → `## 파이프라인 현황판` (라인 199)
- [x] 변경이력 추가

### R-3: SKILL.md 6개 (Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경)

#### opp
- [x] PLAN 완료 후 Gate 순서에서 Artifact Gate 줄 제거
- [x] EXECUTE 완료 후 Gate 순서에서 Artifact Gate 줄 제거 + 번호 재조정
- [x] 진행 현황 행 예시 PLAN #9 Artifact Gate 제거 + 이후 번호 재정렬
- [x] 진행 현황 행 예시 EXECUTE #18 Artifact Gate 제거 + 이후 번호 재정렬
- [x] STATE.md 도메인 치환값 섹션: `## 진행 현황` → `## 파이프라인 현황판` (R-4)
- [x] `## PM Gate 점검 목록` 섹션 추가 (PLAN/EXECUTE — §2.5 완성 텍스트 사용)
- [x] 변경이력 추가 (v2.3)

#### opd
- [x] ANALYSIS Gate 순서에서 Artifact Gate 줄 제거
- [x] PLAN Gate 순서에서 Artifact Gate 줄 제거
- [x] 진행 현황 행 예시 ANALYSIS #7 Artifact Gate 제거 + 이후 번호 재정렬
- [x] 진행 현황 행 예시 PLAN #20 Artifact Gate 제거 + 전체 번호 재정렬
- [x] STATE.md 도메인 치환값 섹션: `## 진행 현황` → `## 파이프라인 현황판` (R-4)
- [x] `## PM Gate 점검 목록` 섹션 추가 (ANALYSIS/PLAN+TEST-SCENARIO/EXECUTE — §2.5 완성 텍스트 사용)
- [x] 변경이력 추가 (v2.7)

#### opds
- [x] PLAN Gate 순서에서 Artifact Gate 줄 제거
- [x] 진행 현황 행 예시 PLAN #12 Artifact Gate 제거 + 이후 번호 재정렬
- [x] STATE.md 도메인 치환값 섹션: `## 진행 현황` → `## 파이프라인 현황판` (R-4)
- [x] `## PM Gate 점검 목록` 섹션 추가 (PLAN+TEST-SCENARIO/EXECUTE — §2.5 완성 텍스트 사용)
- [x] 변경이력 추가 (v2.7)

#### opdw
- [x] WIREFRAME Gate 순서에서 Artifact Gate 줄 제거
- [x] 진행 현황 행 예시 WIREFRAME #9 Artifact Gate 제거 + 이후 번호 재정렬
- [x] STATE.md 도메인 치환값 섹션: `## 진행 현황` → `## 파이프라인 현황판` (R-4)
- [x] `## PM Gate 점검 목록` 섹션 추가 (WIREFRAME/EXECUTE — §2.5 완성 텍스트 사용)
- [x] 변경이력 추가 (v1.9)

#### opwt
- [x] PLAN 공통 게이트에서 Artifact Gate 줄 제거
- [x] STATE.md 도메인 치환값 섹션: `## 진행 현황` → `## 파이프라인 현황판` (R-4, 있으면)
- [x] `## PM Gate 점검 목록` 섹션 추가 (PLAN/EXECUTE — §2.5 완성 텍스트 사용)
- [x] 변경이력 추가 (v2.8)

#### opsdd
- [x] 진행 현황 행 예시 SPEC #7 Artifact Gate 제거 + 이후 번호 재정렬
- [x] 진행 현황 행 예시 REVIEW #16 Artifact Gate 제거
- [x] 진행 현황 행 예시 DESIGN #24 Artifact Gate 제거
- [x] 전체 번호 재정렬 (43행 → 40행)
- [x] STATE.md 도메인 치환값 섹션: `## 진행 현황` → `## 파이프라인 현황판` (R-4)
- [x] `## PM Gate 점검 목록` 섹션 추가 (SPEC/DESIGN/EXECUTE — §2.5 완성 텍스트 사용)
- [x] 변경이력 추가 (v2.6.0)

---

## §4 QA 체크리스트

### Q-1. TASK.md 요구사항 완전성

- [x] R-1(harness-interactive.md): §2.5 Artifact Gate 섹션 제거 반영되었는가
- [x] R-1(harness-interactive.md): §3 PM Gate에 5단계 알고리즘/데이터 분리 절차가 명시되어 있는가
- [x] R-1(harness-interactive.md): §4 체크리스트 검증 게이트 섹션 제거 반영되었는가
- [x] R-1(harness-interactive.md): §5(→§4) Gate Fail 테이블 Artifact Gate 행 제거 반영되었는가
- [x] R-2(harness.md): Artifact Gate 행 제거 반영되었는가
- [x] R-2(harness.md): R-4 파이프라인 현황판 이름 변경 반영되었는가 (§2.4 테이블 포함)
- [x] R-3(6개 SKILL.md): Artifact Gate 행 제거 반영되었는가
- [x] R-3(6개 SKILL.md): `## PM Gate 점검 목록` 섹션 추가가 스킬별로 명시되었는가
- [x] R-4(이름 변경): `진행 현황` → `파이프라인 현황판` 전반 반영 범위가 명시되었는가

### Q-2. 알고리즘/데이터 분리 설계 반영

- [x] harness-interactive.md §3에 5단계 절차가 명시되어 있는가 (§2.3)
- [x] 각 SKILL.md에 `## PM Gate 점검 목록` 섹션 추가가 명시되어 있는가 (§2.5 각 스킬)
- [x] 스킬별 점검 목록 차이(Phase별 산출물·체크리스트 위치)가 §2.3 테이블과 §2.5에 반영되어 있는가
- [x] 이전 방식(하네스 내장 Phase 테이블 + SKILL.md 오버라이드)과의 차이가 §2.2에 명시되었는가

### Q-3. 구현 전략 타당성

- [x] 실행 Step 순서가 harness → SKILL.md 순으로 논리적인가 (§2.1)
- [x] opwt 예외(ANALYSIS 서브체크 유지) 주의사항이 §5에 명시되어 있는가
- [x] `~/.opal/` 직접 수정 금지가 §5에 명시되어 있는가
- [x] 번호 재정렬 정확성 주의사항이 §5에 명시되어 있는가

### Q-4. 실행 체크리스트 충분성

- [x] R-1 체크리스트에 5단계 절차 추가 항목이 포함되어 있는가
- [x] R-2 체크리스트에 R-4 파이프라인 현황판 이름 변경 항목이 포함되어 있는가
- [x] R-3 각 SKILL.md 체크리스트에 `PM Gate 점검 목록` 섹션 추가 항목이 포함되어 있는가
- [x] R-3 각 SKILL.md 체크리스트에 `파이프라인 현황판` 이름 변경 항목이 포함되어 있는가

---

## §5 주의 사항

1. **opsdd — 105 태스크 Artifact Gate 행 추가**: v2.5.0에서 43행 구조로 교체하면서 Artifact Gate 행이 포함됨. 이번 태스크에서 제거 필요. 제거 후 40행.

2. **opwt — 모드별 가변 구조**: opwt는 ANALYSIS/PLAN/EXECUTE/QA 단계별로 게이트 구조가 다름.
   - ANALYSIS 게이트(라인 106~111): PM 자가 체크 내부의 `Artifact Gate` 서브체크 → **제거 금지** (별도 Gate 행이 아님)
   - PLAN 공통 게이트(라인 149): `**Artifact Gate** (하네스 §2.5 참조)` → **제거**
   - EXECUTE 배치 게이트(라인 176~179): 이미 Artifact Gate 없음 → 변경 불필요
   - STATE.md 도메인 치환값: 진행 현황 행 예시 없음 → 변경 불필요 (단 섹션 헤더 `## 진행 현황`이 있으면 R-4 이름 변경 적용)

3. **opd ANALYSIS Gate — v2.6 주의**: opd 변경이력 라인 243에 "v2.6 — ANALYSIS Gate 슬림화 — QA·PM Gate 제거, State Gate + Artifact Gate만 유지" 기재. 그러나 실제 파일(라인 41~44)에는 PM Gate가 여전히 존재. 이 태스크(106)에서는 Artifact Gate만 제거하고 PM Gate는 유지함.

4. **`~/.opal/` 직접 수정 금지**: 수정 대상은 모두 `/Volumes/Data/AiStudio/workspace/opal/opal/` 경로의 파일.

5. **번호 재정렬 정확성**: STATE.md 파이프라인 현황판 행 번호는 연속 정수여야 하므로 Artifact Gate 행 제거 후 이후 모든 행의 번호를 1씩 감산 처리. 특히 opsdd는 3개 Phase에서 각 1개씩 총 3개 제거 → 매 Phase 제거 후 이후 번호를 누적 감산.

6. **변경이력 버전 규칙**: 각 파일의 최신 버전 +0.1 또는 마이너 버전 증가 적용. 태스크 번호 (106) 괄호 표기.

7. **`## PM Gate 점검 목록` 섹션 삽입 위치**: 각 SKILL.md에서 기존 Gate 설명 섹션 직후, 변경이력 직전에 삽입한다. 섹션이 이미 존재하면 내용을 §2.5 데이터 기준으로 교체한다.

8. **R-4 이름 변경 적용 범위**: `진행 현황` → `파이프라인 현황판` 변경은 섹션 헤더(`## 진행 현황`)와 참조 문구(`진행 현황 행`) 모두에 적용한다. 이미 다른 이름으로 쓰이고 있는 경우 그대로 둔다.

9. **PM Gate Fail 처리: 에이전트 재호출 없음** — `[ ]` 발견 시 에이전트를 재소환하거나 재지시하지 않는다. token 낭비 및 루프 위험이 있기 때문이다. PM이 직접 산출물 내용을 읽고 판단하여 완료 확인 시 `[x]`로 갱신하고, 미완료 확인 시 이유를 포함한 항목 목록을 사용자에게 보고한다. 사용자가 보고를 받아 재지시, 무시, 또는 진행 중 하나를 직접 결정한다.

---

## §6 파일 목록 요약

| 파일 | 경로 | 변경 유형 |
|------|------|----------|
| opal-harness-interactive.md | `/Volumes/Data/AiStudio/workspace/opal/opal/core/references/opal-harness-interactive.md` | §2.5 제거, §3 추가, §4 제거, §5→§4 수정, `진행 현황 테이블` → `파이프라인 현황판 테이블` |
| opal-harness.md | `/Volumes/Data/AiStudio/workspace/opal/opal/core/references/opal-harness.md` | §3 규칙/테이블/예시 수정 |
| opal-pilot-project/SKILL.md | `/Volumes/Data/AiStudio/workspace/opal/opal/skills/opal-pilot-project/SKILL.md` | Gate 순서 + 진행 현황 행 수정 |
| opal-pilot-dev/SKILL.md | `/Volumes/Data/AiStudio/workspace/opal/opal/skills/opal-pilot-dev/SKILL.md` | Gate 순서 + 진행 현황 행 수정 |
| opal-pilot-dev-short/SKILL.md | `/Volumes/Data/AiStudio/workspace/opal/opal/skills/opal-pilot-dev-short/SKILL.md` | Gate 순서 + 진행 현황 행 수정 |
| opal-pilot-dev-wireframe/SKILL.md | `/Volumes/Data/AiStudio/workspace/opal/opal/skills/opal-pilot-dev-wireframe/SKILL.md` | Gate 순서 + 진행 현황 행 수정 |
| opal-pilot-write-tech/SKILL.md | `/Volumes/Data/AiStudio/workspace/opal/opal/skills/opal-pilot-write-tech/SKILL.md` | PLAN 게이트 수정 |
| opal-pilot-sdd/SKILL.md | `/Volumes/Data/AiStudio/workspace/opal/opal/skills/opal-pilot-sdd/SKILL.md` | 진행 현황 행 수정 |
