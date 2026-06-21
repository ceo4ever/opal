# ANALYSIS: oppd 개선 — 프로세스(문서 승격) + WBS 세분화(BE/FE) + 액션 완성도 루프(B7)

> 작성일: 2026-06-21
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | oppd SKILL | `opal/skills/opal-pilot-project-dev/SKILL.md` | Phase 1~3 프로세스 변경 대상 (#1, F-001~F-003, F-024) |
| D-2 | 소스 | wbs-guide | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 세분화 기준 변경 대상 (#2, F-010~F-018) |
| D-3 | 소스 | 액션 에이전트 | `opal/agents/opal-task-action-agent/AGENT.md` | B7 루프 변경 대상 (F-020~F-025) |
| D-4 | 소스 | verification-loop-guide | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | triage·QA 0회 재조정 (F-021, F-027) |
| D-5 | 소스 | parallel-execution-guide | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬=파생 재서술 (F-014) |
| D-6 | 소스 | 하네스 SSOT | `opal/core/references/opal-harness.md` | 자동 루핑 제약 상한 행 (F-026) |
| D-7 | 소스 | FE 에이전트 | `opal/agents/opal-fe-agent/AGENT.md` | FE 3계층 역할 (F-017) |
| D-8 | 소스 | roadmap-guide | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | "1~3일" 및 "병렬 식별" 구서술 존재 — F-010/F-014 영향 범위 |
| D-9 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력·하네스 SSOT 제약 |
| D-10 | 설계 | 프로젝트 정의 | `docs/PROJECT.md` | 문서 레지스트리, 영역 매핑 |
| D-11 | 설계 | 코드·문서 컨벤션 | `docs/CONVENTIONS.md` | 변경이력 의무, @header, Citation 규칙 |
| D-12 | 설계 | citation-rules | `opal/core/references/harness/citation-rules.md` | 인라인 인용 포맷 규칙 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 파이프라인 본체 (Phase 1~3) | 필수 | `D-1:105-106` (docs/ 직접 기재), `D-1:276` (1~3일), `D-1:322` (WBS 등록), `D-1:621-627` (문서 등록 프로토콜) |
| `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | WBS 수립 기준 및 구조 정의 | 필수 | `D-2:24` (1~3일), `D-2:22` (병렬 식별 1차 목표), `D-2:127-140` (액션 목록 컬럼), `D-2:214-230` (PM 검수 체크리스트) |
| `opal/agents/opal-task-action-agent/AGENT.md` | oppd Phase 3 액션 자율 실행 에이전트 | 필수 | `D-3:33-62` (선형 6단계), `D-3:108-113` (VERIFY 재시도 한도 표), `D-3:154-200` (결과 반환 형식) |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | VERIFY 루프 전략 및 에스컬레이션 | 필수 | `D-4:291-299` (§3-5 "0회 즉시 에스컬레이션"), `D-4:487-497` (§7 정합성 표) |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬 실행 전략 | 필수 | `D-5:8-15` (§1 개요 — 병렬을 속도 향상 목적으로 서술) |
| `opal/core/references/opal-harness.md` | 하네스 SSOT — 자동 루핑 제약 표 | 필수 | `D-6:44-57` (§1 자동 루핑 제약 표 — PLAN 재진입 행 없음) |
| `opal/agents/opal-fe-agent/AGENT.md` | FE 전문 워커 에이전트 | 필수 | `D-7:1-104` (T0/T1/T2 계층·컴포넌트 API 계약 역할 미기재) |
| `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 구 로드맵 수립 가이드 | 간접 영향 | `D-8:24` (1~3일), `D-8:22-23` (병렬 식별), `D-8:173` (크기 조정 1~3일) — TASK 범위 밖이나 정합 리스크 |

### 1.2 F-ID별 변경 지점 정밀 매핑

| F-ID | 변경 파일 | 현재 위치 | 현재 값(요약) | 변경 방향 |
|------|----------|---------|-------------|----------|
| F-001 | D-1 | `D-1:105`, `D-1:163-175` §1-1, `D-1:218-232` §1-2 | `docs/PRD.md`, `docs/TRD.md` 직접 작성 | 태스크 폴더 경로로 변경 |
| F-002 | D-1 | `D-1:240-248` §1-3 후속 조치 | 2항목(PRD/TRD docs/ 등록) — 승격 단계 없음 | 승격(greenfield/반복 분기) 단계 신설 |
| F-003 | D-1 | `D-1:322` §2-5 후속 조치 #1, `D-1:621-627` §문서 등록 프로토콜 | `docs/WBS.md` 등록 행 존재 | WBS docs/ 승격/등록 제거 |
| F-010 | D-2 | `D-2:24` §태스크 분할 원칙 #5, `D-2:206` §태스크 분할 프로세스 #6 | "하나의 태스크는 1~3일 분량이 적정" | 단일 책임 + 단일 수용 시나리오로 교체 |
| F-010 | D-1 | `D-1:276` §2-2 분할 원칙 #4 | "하나의 태스크는 1~3일 분량이 적정하다" | 동일 교체 (D-1·D-2 동시 변경) |
| F-011 | D-2 | §태스크 분할 원칙 (해당 내용 없음) | 너무 큼/작음 판정 기준 미존재 | 신규 기준 추가 |
| F-012 | D-2 | `D-2:127-140` §WBS 구조 액션 목록 컬럼, `D-2:228` §PM 검수 체크리스트 | generic 검증 명령 허용, 수용 시나리오 컬럼 없음 | 수용 시나리오 컬럼 추가 + generic 금지 + TEST-SCENARIO 연결 |
| F-013 | D-2 | §액션 구조 (해당 내용 없음) | 통합 액션 타입 없음 | 통합 액션 타입 신규 추가 |
| F-014 | D-2 | `D-2:22-23` §태스크 분할 원칙 #3, `D-2:177-190` §병렬 실행 전략 | 병렬이 1차 목표처럼 서술 | 세분화 DAG의 산출로 재서술 |
| F-014 | D-5 | `D-5:8-15` §1 개요 §목적 | "개발 속도를 향상" — 세분화 결과 서술 아님 | 도입부 재서술 |
| F-015 | D-2 | `D-2:214-230` §PM 검수 체크리스트, `D-2:189` | 단일 책임·수용 시나리오·통합 액션 항목 없음 | 4종 항목 추가 |
| F-015 | D-1 | `D-1:292-297` §2-3 PM 검수 | 기존 5항목 — F-010~F-013 대조 없음 | 갱신 필요 |
| F-016 | D-2 | 해당 섹션 없음 | BE 액션 분할 기준 미존재 | 신규 §BE 액션 분할 기준 추가 |
| F-017 | D-2 | 해당 섹션 없음 | FE 3계층 분할 기준 미존재 | 신규 §FE 액션 분할 기준 추가 |
| F-017 | D-7 | `D-7:전체` | T0/T1/T2·컴포넌트 API 계약 역할 없음 | 역할 기재 추가 |
| F-018 | D-2 | 해당 섹션 없음 | BE/FE 분할 매트릭스 미존재 | 신규 §BE/FE 분할 매트릭스 추가 |
| F-020 | D-3 | `D-3:33-62` §실행 프로세스, `D-3:100-134` §5단계 VERIFY | 선형 6단계 — PLAN 재진입 없음, 실패 시 status:failed 즉시 반환 | 경계 재설계 루프로 전환 |
| F-021 | D-3 | `D-3:100-134` §5단계 VERIFY | triage 분류 없음 — L1~L3b 기계적 처리만 | triage(구현/설계/회귀) 3분류 추가 |
| F-021 | D-4 | `D-4:80-299` §3 실패 유형별 루핑 전략 | 구현/설계/회귀 3분류 없음 | 3분류 표 추가 |
| F-022 | D-3 | `D-3:100-134` §5단계 VERIFY | 1차 분류 + 자동승격 없음 | 1차분류 + fix 한도 초과 자동승격 흐름 추가 |
| F-023 | D-3 | `D-3:100-134` §5단계 VERIFY | 3계층 라우팅 없음 | 3계층 라우팅 표 추가 |
| F-023 | D-1 | `D-1:331-342` §Phase 3 §3-1 에이전트 결과 처리 | WBS/TRD 에스컬레이션 처리 없음 | scope별 PM 처리 분기 추가 |
| F-024 | D-1 | `D-1:331-342` §Phase 3 | WBS 변경 2단 기준·TRD/PRD 사용자 게이트 없음 | 기준 + 게이트 추가 |
| F-025 | D-3 | `D-3:154-200` §결과 반환 형식 | `failure_context`에 `scope` 필드 없음 | scope 필드 추가 |
| F-026 | D-6 | `D-6:44-57` §1 자동 루핑 제약 표 | PLAN 재진입 행 없음 (lint∞/build2/L3a3/L3b1/QA0만) | 행 신설 |
| F-027 | D-4 | `D-4:291-299` §3-5 | "0회 즉시 에스컬레이션" — B7 3계층 라우팅과 충돌 | scope 기반 분기로 재서술 |

### 1.3 의존성 맵

```
oppd SKILL.md (D-1)
  ├── Read → wbs-guide.md (D-2)                    [§2-1 사전 준비 지시]
  ├── Read → verification-loop-guide.md (D-4)       [§3-1a 자동 검증 루핑]
  ├── Read → parallel-execution-guide.md (D-5)      [§3-1b 병렬 액션 실행]
  └── dispatch → opal-task-action-agent (D-3)       [Phase 3 §3-1]

opal-task-action-agent (D-3)
  ├── references → verification-loop-guide.md (D-4) [§5단계 VERIFY 참조]
  └── references → opal-harness.md (D-6)            [Guards 재시도 한도]

verification-loop-guide.md (D-4)
  ├── 정합성 표(§7) ↔ opal-harness.md (D-6)        [한도 수치 일치 필수]
  └── 정합성 표(§7) ↔ opal-task-action-agent (D-3) [에이전트 내부 루프 일치]

opal-fe-agent (D-7)
  └── dispatched by → oppd SKILL.md (D-1)           [Phase 3 병렬 디스패치]
```

**동시 갱신 필요 쌍(짝)**:

1. **[D-6 ↔ D-4 ↔ D-3]** F-026 PLAN 재진입 상한 — D-6에 행 신설 후, D-4 §7 정합성 표와 D-3 행동 규칙의 한도 참조가 일치해야 함. 수치 복제 금지(D-6 SSOT, D-4/D-3은 포인터만).
2. **[D-1 ↔ D-2]** F-010 sizing 규칙 — `D-1:276`과 `D-2:24` 동시 교체 필수.
3. **[D-3 ↔ D-4]** F-021 triage 3분류 — D-3 §5단계와 D-4 §3에 동일 분류 표 일관 기재.
4. **[D-1 ↔ D-3]** F-023/F-025 — D-3에서 scope 반환, D-1 Phase 3에서 scope별 처리 분기. 짝 변경 필수.
5. **[D-2 ↔ D-5]** F-014 병렬=파생 재서술 — `D-2:22-23`과 `D-5:8-15` 동시 재서술.

### 1.4 테스트 현황

- 코드 파일(.py/.ts) 변경 없음 — 모든 변경 대상 Markdown 문서.
- 검증: grep/Bash 기반 문서 구조·정합성 검증(섹션 존재, 용어 일치, 교차 참조 수치 일치).
- TEST-SCENARIO는 "AC 충족 + 용어 일관성 + 하네스 SSOT 정합" 중심 문서 검증 시나리오.

---

## 2. 교차 참조 의존 맵 (상세)

### 2.1 3중 정합 관계: D-6 ↔ D-4 §7 ↔ D-3 §5

| 실패 유형 | D-6 §1 자동 루핑 제약 표 | D-4 §7 정합성 확인용 표 | D-3 §5단계 계층별 한도 |
|---------|------------------------|------------------------|----------------------|
| lint/format | 제한 없음 | 제한 없음 | 제한 없음 |
| build/type | 2회 | 2회 | 2회 |
| L3a unit/integration | 3회 | 3회 | 3회 |
| L3b E2E | 1회 | 1회 | 1회 |
| QA 설계/아키텍처 | 0회 | 0회 | (별도 QA 게이트 흐름 `D-3:80-82`) |
| **PLAN 재진입** | **미존재** | **미존재** | **미존재** |

현재 D-6·D-4 §7은 수치 정합 상태(`D-4:490-496`, `D-6:48-54`). F-026 신설 시 세 파일 동시 업데이트 필요 — D-6이 SSOT, D-4/D-3은 참조 포인터만.

### 2.2 SKILL Phase ↔ wbs-guide 참조 관계

| D-1 §섹션 | D-2 §섹션 | 현재 정합성 | F-ID 변경 시 주의 |
|----------|----------|-----------|----------------|
| §2-1 사전 준비 (`D-1:259-265`) | wbs-guide 전체 | 정합(D-1이 D-2 명시적 Read 지시) | 유지 |
| §2-2 분할 원칙 #4 (`D-1:276`) | §태스크 분할 원칙 #5 (`D-2:24`) | **1~3일 동시 존재** | F-010에서 동시 교체 필수 |
| §2-3 PM 검수 (`D-1:292-297`) | §PM 검수 체크리스트 (`D-2:214-230`) | 정합(D-1이 D-2 1:1 대조 지시) | F-015 변경 시 두 곳 동시 갱신 |
| §문서 등록 프로토콜 (`D-1:619-627`) | — | WBS.md 등록 행 존재 | F-003에서 D-1만 제거 |

---

## 3. F-027 의미 충돌 상세 분석

### 3.1 원문 인용

**D-4 §3-5 현재 서술** (`opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:291-299`):
> "재시도 한도: 0회 — 즉시 사용자 에스컬레이션"
> "QA 에이전트가 보고한 설계/아키텍처 수준의 이슈는 자동 수정이 불가능하다. ... 사람의 판단이 필요하므로 즉시 에스컬레이션한다."

**TASK.md B7 확정 방향** (`tasks/031-260621-opd-oppd-개선-세분화-완성도루프/TASK.md:49`):
> "설계 실패 3계층 라우팅: 액션-로컬(에이전트 자율 재PLAN) / WBS(PM) / TRD·PRD(사용자)"

### 3.2 충돌 구조

| 실패 scope | D-4 §3-5 현재 라우팅 | B7 확정 방향 | 충돌 여부 |
|-----------|--------------------|-----------|---------| 
| scope: action (로컬 설계 결함) | 즉시 사용자 에스컬레이션 | 에이전트 자율 재PLAN | **충돌** |
| scope: wbs (WBS 범위 변경) | 즉시 사용자 에스컬레이션 | PM 에스컬레이션 | **부분 충돌** (사용자 vs PM) |
| scope: trd (TRD/PRD 변경) | 즉시 사용자 에스컬레이션 | 사용자 에스컬레이션 | 정합 |

### 3.3 모순 없는 재서술 방향

D-4 §3-5를 다음과 같이 재서술한다:
- "설계/아키텍처 이슈"를 "설계 수준 실패"로 재명명
- scope에 따라 분기:
  - `scope: action` → 에이전트 자율 재PLAN 허용 (상한: F-026 PLAN 재진입 한도, SSOT는 D-6)
  - `scope: wbs` → PM 에스컬레이션(WBS 변경 2단 기준 적용)
  - `scope: trd` → 즉시 사용자 에스컬레이션(0회 규칙 유지)
- D-4 §7 정합성 표에서 "QA 설계/아키텍처" 행을 "설계 수준(scope별 분기)" 주석 추가
- "0회 즉시 에스컬레이션"은 `scope: trd`에만 적용됨을 명시

---

## 4. 배포본 vs 소스 드리프트 점검

| 파일 | 드리프트 | 내용 | 방향 |
|------|---------|------|------|
| D-1 SKILL.md | 있음 | 소스만 변경이력 섹션 존재 — install strip에 의한 정상 차이 | 기능 동일 |
| D-2 wbs-guide.md | **없음** | 소스=배포본 동일 | - |
| D-3 AGENT.md | **있음(역전)** | 배포본에만 "워커 디스패치 모델 규칙" 블록 + model: opus 교체 존재. 소스가 배포본보다 구버전 | EXECUTE 시 소스에 배포본 추가 내용 병합 필수 |
| D-4 verification-loop-guide.md | 있음 | 소스만 변경이력 섹션 존재 — 정상 차이 | 기능 동일 |
| D-5 parallel-execution-guide.md | 있음 | 소스만 변경이력 섹션 존재 — 정상 차이 | 기능 동일 |
| D-6 opal-harness.md | **있음(소스 최신)** | 소스 v5.5 "명확화 게이트" 절이 배포본에 없음 + 소스만 변경이력 존재 | 소스 수정 후 install 재배포 |
| D-7 opal-fe-agent/AGENT.md | 있음 | 소스만 변경이력 섹션 존재 — 정상 차이 | 기능 동일 |

**[MUST] 핵심 경고**: D-3 소스/배포본 역전 — `opal/agents/opal-task-action-agent/AGENT.md` 소스 수정 시 배포본(`~/.opal/agents/opal-task-action-agent/AGENT.md`)에만 존재하는 "워커 디스패치 모델 규칙" 블록(line 33~40)과 `model: opus` 교체 내용을 소스에도 반영해야 한다. EXECUTE 워커가 반드시 처리.

**변경이력 드리프트 정상 패턴**: D-1, D-4, D-5, D-7의 차이는 소스에만 `## 변경이력` 섹션이 있고 배포본에는 없는 것이며, `docs/CONVENTIONS.md §변경이력 작성 의무`: "배포 시 install-mac.sh가 변경이력 섹션을 자동 strip한다"에 의한 정상 동작.

---

## 5. 재사용 가능 패턴 식별

| 패턴 | 현재 위치 | 재활용 방식 |
|------|---------|-----------|
| L1~L3b 계층별 실패 전략 | `D-4:§3-1~§3-4` | F-021 triage "구현 수준" 라우팅을 이 패턴에 연결 — 기존 처리 그대로 활용 |
| 에스컬레이션 프로토콜 보고 형식 | `D-4:§5` | F-023 설계 실패 WBS/TRD 에스컬레이션 보고 형식으로 확장 |
| 회귀 방지 가드 | `D-4:§4`, `D-3:131-135` | B7 재설계 루프에서도 동일 패턴 유지(회귀 = 즉시 중단) |
| 자동 루핑 제약 표 패턴 | `D-6:§1 Guards` | F-026 PLAN 재진입 상한을 기존 표 행 패턴(상한N회 → 에스컬레이션)으로 등록 |
| 3-way 모드 체계 PM 자율/사용자 게이트 | `D-1:§Agentic/Semi-Agentic 모드` | B7 WBS 변경 2단 기준(PM 자율 / 사용자 게이트)을 이 체계와 통일 |
| AGENTIC-LOG 기록 패턴 | `D-1:§AGENTIC-LOG.md` | F-024 WBS 자율 조정 로그에 기존 AGENTIC-LOG 활용 가능 |

---

## 6. 영역 간 용어 일관성 점검

| 신규 용어 (TASK.md) | 기존 문서 출현 여부 | 충돌/중복 위험 |
|--------------------|------------------|--------------|
| `triage` (구현/설계/회귀) | D-3, D-4에 없음 | 충돌 없음 — 신규 도입 |
| `scope: action\|wbs\|trd` | D-3 failure_context에 없음 | 충돌 없음 — 신규 필드 |
| `FE T0/T1/T2` | D-2, D-7에 없음 | 충돌 없음 — 신규 계층명 |
| `통합 액션` | D-2에 없음 | "병렬 그룹"과 개념 구분 필요(통합=별도 액션, 병렬=실행 방식) |
| `수용 시나리오` | D-2 §PM 검수에 "완료 기준" 유사 개념 존재(`D-2:228`) | "완료 기준" vs "수용 시나리오" 용어 계층 정합 필요 — decision_required |
| `verification_log` | D-3 반환 형식에 이미 존재(`D-3:162-172`) | 기존 필드 확장 방식 활용 |
| `액션-로컬(재PLAN)` | D-3에 "PLAN 재지시" 맥락으로 부분 존재(`D-3:80-82`) | 용어 통일 결정 필요 — decision_required |
| `greenfield` / `반복 델타 병합` | 없음 | 충돌 없음. PLAN에서 판단 기준 기술 필요 |

**STATE.md 루프 상태 반영 필요**: 현재 STATE.md 템플릿(`D-1:527-574`)에 B7 PLAN 재진입 로그(triage 결과, 재PLAN 횟수, scope)를 기록하는 필드 없음. PLAN에서 "재설계 루프 로그" 행 추가 여부 설계 결정 필요 — decision_required.

---

## 7. 영향 범위

### 7.1 직접 영향

| 파일 | 변경 규모 |
|------|---------|
| `opal/skills/opal-pilot-project-dev/SKILL.md` | 중(Phase 1~3 여러 섹션) |
| `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 대(sizing 교체 + 4개 신규 섹션) |
| `opal/agents/opal-task-action-agent/AGENT.md` | 대(§실행 프로세스 + §5 VERIFY 전면 재설계 + 배포본 역전 내용 병합) |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 중(§3-5 재서술 + §7 정합성 표 갱신) |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 소(도입부 1~2줄 재서술) |
| `opal/core/references/opal-harness.md` | 소(§1 자동 루핑 제약 표 1행 추가) |
| `opal/agents/opal-fe-agent/AGENT.md` | 소(T0/T1/T2 역할 추가) |

### 7.2 간접 영향

- `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md`: F-010/F-014 변경 시 동일 "1~3일"/"병렬 식별" 구서술 잔존(→ §제약/리스크 R-2).
- 배포본 전체(`~/.opal/`): 소스 수정 후 install 재배포 필요 — 이번 태스크 범위 외.

### 7.3 영향 범위 요약

- [ ] DB 스키마 변경: 해당 없음
- [ ] API 인터페이스 변경: 해당 없음 (문서 전용)
- [ ] 설정/환경변수 변경: 해당 없음
- [ ] 빌드/배포 파이프라인 변경: install 재배포 (이번 태스크 범위 외)

---

## 8. 핵심 발견 사항

1. **D-3(액션 에이전트) 소스/배포본 역전 드리프트**: 배포본에만 "model: opus 통일" 블록이 존재하나 소스에 없다. EXECUTE 단계에서 D-3 소스 수정 시 배포본 추가 내용을 소스에도 병합해야 한다.

2. **F-027 충돌 핵심은 "계층 부재"**: D-4 §3-5의 "0회 즉시 에스컬레이션"은 TRD/PRD 수준에만 적용되어야 하나 현재 설계/아키텍처 이슈 전체에 적용된다. "액션-로컬 재PLAN" 중간 계층을 도입하면 기존 규칙과 B7이 모순 없이 공존 가능하다.

3. **F-026 PLAN 재진입 상한은 D-6 단독 등록, D-4/D-3은 포인터**: 세 파일이 동일 수치를 공유하는 SSOT 체계이므로 수치 복제 금지. D-6에 행 신설 후 D-4 §7과 D-3 행동 규칙에 참조 링크만 추가.

4. **병렬=세분화의 결과 재서술 대상이 3곳**: D-2, D-5 외 roadmap-guide.md(D-8)도 동일 구서술 보유. TASK 범위 밖이나 PLAN에서 처리 여부 결정 필요.

5. **"수용 시나리오" vs "완료 기준" 용어 계층 정합 필요**: D-2에 이미 "완료 기준"("검증 명령") 개념이 존재하며, "수용 시나리오"가 상위 개념(자연어 완료 기준 포함)임을 PLAN에서 명확히 정의해야 한다.

---

## 9. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-1 D-3 소스/배포본 역전 | 배포본에만 "opus 모델 통일" 블록 존재. 소스 수정 시 병합 누락 위험 | High | `~/.opal/agents/opal-task-action-agent/AGENT.md:33-40` (배포본에만 존재) |
| R-2 roadmap-guide.md 정합 | "1~3일", "병렬 식별" 구서술이 TASK 범위 밖 파일에 잔존 | Medium | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md:24`, `:173` |
| R-3 F-026 수치 삼중 기재 금지 | 하네스 수치 D-4/D-3에 복제 시 드리프트 재발 위험 | High | `TASK.md §제약 조건`: "발췌·복제 금지" / `D-9 §업무 수행 지침` |
| R-4 "수용 시나리오" vs "완료 기준" 혼용 | D-2에 "완료 기준" 개념 존재, F-012 "수용 시나리오" 도입 시 혼용 가능 | Medium | `D-2:228` §PM 검수 체크리스트 |
| R-5 D-3 §실행 프로세스 전면 재설계 규모 | B7 루프 도입은 6단계 선형 → 순환 구조 전환 — 테스트 시나리오 공수 과소 산정 위험 | Medium | `D-3:33-62` §실행 프로세스 |
| R-6 STATE.md 재설계 루프 로그 필드 부재 | B7 PLAN 재진입 로그 기록 필드 없음. PLAN에서 설계 결정 필요 | Low | `D-1:527-574` §STATE.md 템플릿 — 재설계 루프 로그 행 없음 |
| R-7 변경이력 의무 7개 파일 | 수정한 모든 파일에 변경이력 행 추가 필수 | Low | `D-11 docs/CONVENTIONS.md §변경이력 작성 의무` |

---

## 10. 기술 컨텍스트

### 10.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 문서 형식 | Markdown | - |
| 메타 | YAML frontmatter | - |
| 검증 도구 | grep/Bash | - |
| 버전 관리 | git | - |

### 10.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | PLAN.md 작성 — 7개 파일 변경 계획 + D-3 전면 재설계 설계 |
| op-dev-execute | 각 파일 수정 실행 |
| op-dev-test-scenario | 문서 정합성 검증 시나리오(grep/섹션 존재/수치 일치) |

### 10.3 추천 MCP

| MCP | 용도 |
|-----|------|
| — | 외부 라이브러리 조사 불필요 (문서 전용 작업) |

---

## decision_required

```json
{
  "decision_required": [
    {
      "type": "terminology_mismatch",
      "summary": "수용 시나리오 vs 완료 기준",
      "tokens": ["수용 시나리오", "완료 기준"],
      "areas": ["wbs-guide.md §PM 검수", "TASK.md F-012"],
      "source_refs": [
        "opal/skills/opal-pilot-project-dev/references/wbs-guide.md:228",
        "tasks/031-260621-opd-oppd-개선-세분화-완성도루프/TASK.md:92-94"
      ],
      "suggested_resolution": "수용 시나리오 = 상위 개념(자연어 완료 기준 포함), 완료 기준/검증 명령 = 기계적 명령. PLAN에서 계층 정의 후 wbs-guide 용어 통일"
    },
    {
      "type": "terminology_mismatch",
      "summary": "액션-로컬 재PLAN vs PLAN 재지시",
      "tokens": ["액션-로컬 재PLAN", "PLAN 재지시"],
      "areas": ["TASK.md B7 확정 방향", "opal-task-action-agent §2단계 QA"],
      "source_refs": [
        "tasks/031-260621-opd-oppd-개선-세분화-완성도루프/TASK.md:49",
        "opal/agents/opal-task-action-agent/AGENT.md:80-82"
      ],
      "suggested_resolution": "D-3에서 기존 'PLAN 재지시(QA 피드백 기반)'와 신규 'B7 재설계 루프 PLAN 재진입'을 구분 명명. PLAN에서 용어 확정 필요"
    },
    {
      "type": "scope_decision",
      "summary": "roadmap-guide.md F-010/F-014 수정 여부",
      "tokens": ["roadmap-guide.md"],
      "areas": ["opal/skills/opal-pilot-project-dev/references/"],
      "source_refs": [
        "opal/skills/opal-pilot-project-dev/references/roadmap-guide.md:24",
        "opal/skills/opal-pilot-project-dev/references/roadmap-guide.md:173"
      ],
      "suggested_resolution": "TASK.md §범위에 명시되지 않음. PLAN에서 포함 여부 결정 후 F-010/F-014 EXECUTE 시 함께 수정 또는 후속 태스크로 분리"
    },
    {
      "type": "design_decision",
      "summary": "STATE.md 재설계 루프 로그 필드 신설 여부",
      "tokens": ["재설계 루프 로그", "STATE.md 템플릿"],
      "areas": ["oppd SKILL.md §STATE.md 관리"],
      "source_refs": [
        "opal/skills/opal-pilot-project-dev/SKILL.md:527-574"
      ],
      "suggested_resolution": "B7 PLAN 재진입 횟수·scope·triage 결과를 STATE.md에 기록하려면 템플릿 변경 필요. PLAN에서 설계 후 F-020 EXECUTE 범위에 포함 여부 결정"
    }
  ]
}
```

---

## 변경이력

| 날짜 | 변경내용 |
|------|---------|
| 2026-06-21 | 초기 작성 — oppd 3축 개선(F-001~F-027) 코드베이스 분석 + 드리프트 점검 + F-027 충돌 분석 + 교차 참조 의존 맵 + decision_required 4건 (031) |
