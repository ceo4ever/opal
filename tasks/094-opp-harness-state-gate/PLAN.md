# PLAN: Harness State Gate — 상태 관리 강제화

> 작성일: 2026-04-07
> 입력: TASK.md
> 출력: PLAN.md

---

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 하네스 공통 — §3 State 관리 | ❌ 이미 완료 |
| `opal/core/references/opal-harness-interactive.md` | interactive 모드 Gate 정의 | ❌ 이미 완료 |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 | ❌ 이미 완료 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 오케스트레이터 | ❌ 이미 완료 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 오케스트레이터 | ❌ 이미 완료 |
| `opal/skills/opal-pilot-project/SKILL.md` | opp 오케스트레이터 | ❌ 이미 완료 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 오케스트레이터 | ❌ 이미 완료 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt 오케스트레이터 | ❌ 이미 완료 |
| `opal/skills/op-task/SKILL.md` | TASK.md 작성 단계 스킬 | ✅ 수정 필요 |

### 현재 상태

직접 파일을 읽어 확인한 결과:

**이미 완료된 항목 (이전 세션에서 구현됨)**:

- `opal-harness.md §3`: State Gate 섹션이 이미 존재함. 이벤트 테이블에 `[강제]` 명시 및 갱신 미수행 시 다음 단계 진입 금지 규칙 포함. 워커 1차 갱신 + PM 감독 모델 명시. Gate 위치(QA → Artifact → **State Gate** → PM) 표준 문구 정의됨.
- `opal-harness-interactive.md §2`: QA 도메인 테이블에 `opsdd`(Phase별 QA 스킬 혼합)와 `opwt`(기획 문서) 행 이미 추가됨 (v1.5). `§3 PM Gate`: State Gate 확인 서브섹션 이미 존재 — PLAN/EXECUTE PM Gate별 STATE.md 타임스탬프·단계·상태 확인 절차 및 미갱신 시 차단 원칙 명시됨.
- `opal-pilot-dev SKILL.md`: TASK/ANALYSIS/PLAN/EXECUTE 각 단계 Gate 순서에 `State Gate (하네스 §3 참조)` 이미 추가됨 (v2.2).
- `opal-pilot-dev-short SKILL.md`: TASK/PLAN/EXECUTE 각 단계 Gate 순서에 State Gate 이미 추가됨 (v2.3).
- `opal-pilot-dev-wireframe SKILL.md`: TASK/WIREFRAME/EXECUTE 각 단계 State Gate 이미 추가됨. Agentic Mode 섹션 이미 신설됨 (v1.6).
- `opal-pilot-project SKILL.md`: TASK/PLAN/EXECUTE 각 단계 State Gate 이미 추가됨 (v2.0).
- `opal-pilot-sdd SKILL.md`: Phase 1 SPEC, Phase 3 DESIGN Gate에 State Gate 참조 추가됨. Phase 4 EXECUTE-LOOP STATE.md 갱신에 State Gate 기준 명시됨 (v2.1).
- `opal-pilot-write-tech SKILL.md`: TASK/ANALYSIS/PLAN/EXECUTE/QA 각 단계 Gate에 State Gate 참조 추가됨 (v2.6).

**미완성 항목**:

- `op-task/SKILL.md`: TASK.md 요구사항 §7 항목 — "배경 분석/조사 결과" 캡처 기능이 없음. 현재는 "확정된 설계 방향 (대화에서 합의)" 섹션만 안내하고, 대화에서 선행 분석/조사가 있었던 경우의 "배경 분석 (대화에서 도출)" 섹션 캡처 가이드가 누락됨.

### 영향 범위

op-task SKILL.md 변경은 단계 스킬(단일 파일)에 국한됨. 하네스나 다른 오케스트레이터 동작에 영향 없음. 변경 이후 TASK.md 작성 시 분석 컨텍스트가 워커에게 전달되어 독립적 태스크 파악이 가능해짐.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

없음.

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/skills/op-task/SKILL.md` | STEP 4 "대화 내용 반영" 절차에 "배경 분석" 섹션 캡처 가이드 추가. TASK.md 템플릿에 해당 섹션 추가. 작성 체크리스트에 관련 항목 추가. |

#### 삭제

없음.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | op-task SKILL.md — "배경 분석" 섹션 가이드 추가 | `opal/skills/op-task/SKILL.md` | 낮음 |

### 핵심 설계

#### op-task SKILL.md 변경 내용

**변경 위치 1**: `STEP 4. TASK.md 작성` > `#### 대화 내용 반영` 절 (현재 63~72줄 영역)

현재:
```
#### 대화 내용 반영

스킬 호출 전에 캡틴과 관련 대화가 있었을 경우, 확정된 설계 방향을 TASK.md에 기록한다.

- TASK.md 템플릿 "요구사항" 앞에 "확정된 설계 방향 (대화에서 합의)" 섹션을 추가한다
- 대화 없이 바로 스킬 호출된 경우 해당 없음 (섹션 생략)
```

변경 후:
```
#### 대화 내용 반영

스킬 호출 전에 캡틴과 관련 대화가 있었을 경우, 해당 내용을 TASK.md에 기록한다.

**배경 분석 (대화에서 도출)** — 대화에서 분석/조사/현황 파악이 먼저 수행된 경우:
- TASK.md 템플릿 "배경" 아래에 "배경 분석 (대화에서 도출)" 섹션을 추가한다
- 분석 결과, 조사 결과, 현황 파악 내용, 파일별 현재 상태 등을 기록한다
- 목적: 워커가 TASK.md만으로 컨텍스트를 독립적으로 파악할 수 있어야 한다

**확정된 설계 방향 (대화에서 합의)** — 대화에서 설계 방향이 합의된 경우:
- TASK.md 템플릿 "배경 분석" 아래(또는 "요구사항" 앞)에 "확정된 설계 방향 (대화에서 합의)" 섹션을 추가한다
- 대화 없이 바로 스킬 호출된 경우 두 섹션 모두 생략
```

**변경 위치 2**: TASK.md 템플릿 (현재 `## 배경` 아래)

현재:
```markdown
## 배경

{왜 이 작업이 필요한지, 현재 상태와 문제점}

## 확정된 설계 방향 (대화에서 합의)

{대화에서 합의된 내용. 스킬 호출 전 대화가 없었으면 이 섹션 생략}

## 요구사항
```

변경 후:
```markdown
## 배경

{왜 이 작업이 필요한지, 현재 상태와 문제점}

## 배경 분석 (대화에서 도출)

{대화에서 분석/조사/현황 파악이 수행된 경우 그 결과를 기록. 파일별 현재 상태, 누락/불일치 항목 등 포함. 분석이 없었으면 이 섹션 생략}

## 확정된 설계 방향 (대화에서 합의)

{대화에서 합의된 설계 방향. 스킬 호출 전 대화가 없었으면 이 섹션 생략}

## 요구사항
```

**변경 위치 3**: `## 작성 체크리스트` 절

현재:
```
- [ ] 스킬 호출 전 대화가 있었다면 "확정된 설계 방향" 섹션을 포함했는가 (대화 없으면 섹션 생략)
```

변경 후:
```
- [ ] 스킬 호출 전 대화에서 분석/조사가 선행되었다면 "배경 분석 (대화에서 도출)" 섹션을 포함했는가 (없으면 생략)
- [ ] 스킬 호출 전 대화에서 설계 방향이 합의되었다면 "확정된 설계 방향 (대화에서 합의)" 섹션을 포함했는가 (없으면 생략)
```

---

## 3. 실행 체크리스트

> 총 1개 Step

### Step 1: op-task SKILL.md — "배경 분석" 캡처 가이드 추가
- [ ] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**:
  1. `STEP 4. TASK.md 작성` > `#### 대화 내용 반영` 절을 수정하여 "배경 분석" 섹션과 "확정된 설계 방향" 섹션 두 가지를 구분하여 안내
  2. TASK.md 템플릿(`## 배경` 아래)에 `## 배경 분석 (대화에서 도출)` 섹션 추가
  3. 작성 체크리스트에서 기존 "확정된 설계 방향" 항목을 두 항목(배경 분석 / 확정된 설계 방향)으로 분리
  4. 변경이력 테이블에 버전 추가 (v1.1)
- **완료 기준**:
  - "배경 분석 (대화에서 도출)" 섹션이 템플릿과 대화 내용 반영 절차 양쪽에 모두 기술되어 있다
  - 체크리스트에 배경 분석 항목이 별도로 존재한다
  - 기존 "확정된 설계 방향" 기능이 유지된다 (삭제가 아닌 추가)
- **테스트**: 수정된 SKILL.md를 읽고 — (1) "배경 분석" 섹션 가이드가 존재하는가, (2) TASK.md 템플릿에 해당 섹션이 있는가, (3) 체크리스트에 두 항목이 분리되어 있는가 확인
- **의존**: 없음

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] "배경 분석 (대화에서 도출)" 섹션이 TASK.md 템플릿에 포함되었는가
- [ ] "대화 내용 반영" 절에 배경 분석과 확정 방향 두 가지가 구분되어 안내되었는가
- [ ] 배경 분석이 없을 경우 섹션 생략이 명시되었는가 (필수가 아님을 명시)

### 일관성 테스트
- [ ] 기존 "확정된 설계 방향" 섹션 기능이 그대로 유지되는가 (삭제/변경 없음)
- [ ] 체크리스트 항목이 배경 분석 / 확정 방향 두 항목으로 올바르게 분리되었는가
- [ ] 변경이력이 갱신되었는가

### 문서 품질
- [ ] 섹션 이름이 직관적인가 (워커가 이해할 수 있는 수준)
- [ ] "목적: 워커가 TASK.md만으로 컨텍스트를 독립적으로 파악할 수 있어야 한다" 문구 또는 동등한 설명이 포함되었는가
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| "배경 분석" 섹션을 필수로 오해 | TASK.md가 불필요하게 길어짐 | 섹션 설명에 "분석이 없었으면 이 섹션 생략" 명시 |
| 기존 TASK.md 형식과 불일치 | 기존 태스크 파일 재작업 필요 | 기존 파일은 소급 적용 불필요. 신규 태스크부터 적용 |

---

## 참고: 이미 완료된 항목 (실행 불필요)

이전 세션에서 이미 구현 완료된 항목들로, 이번 EXECUTE에서 수행하지 않는다.

| 항목 | 파일 | 완료 버전 |
|------|------|----------|
| harness §3 State Gate 신설 + 이벤트 테이블 강제 명시 | `opal-harness.md` | (확인됨) |
| harness-interactive §2 opsdd/opwt 행 추가 | `opal-harness-interactive.md` | v1.5 |
| harness-interactive §3 PM Gate State Gate 연동 | `opal-harness-interactive.md` | v1.5 |
| opd 각 단계 State Gate 추가 | `opal-pilot-dev/SKILL.md` | v2.2 |
| opds 각 단계 State Gate 추가 | `opal-pilot-dev-short/SKILL.md` | v2.3 |
| opdw 각 단계 State Gate 추가 + Agentic Mode 신설 | `opal-pilot-dev-wireframe/SKILL.md` | v1.6 |
| opp 각 단계 State Gate 추가 | `opal-pilot-project/SKILL.md` | v2.0 |
| opsdd Phase Gate State Gate 참조 | `opal-pilot-sdd/SKILL.md` | v2.1 |
| opwt 각 단계 State Gate 참조 | `opal-pilot-write-tech/SKILL.md` | v2.6 |
