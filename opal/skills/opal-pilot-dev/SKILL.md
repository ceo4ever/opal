---
name: opal-pilot-dev
description: |
  **Full Task 오케스트레이터**. 대규모 개발 작업을 4단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev", "opd".
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 기획 문서(opal-pilot-write-tech), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---
# Full Task 오케스트레이터

## Harness
모드: Full Task (TASK → ANALYSIS → PLAN → EXECUTE → TEST)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

## STEP 1: TASK
opal-harness.md "TASK 공통 프로세스" 참조.

TASK 완료 → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인) → 사용자 보고.

## STEP 2: ANALYSIS
워커를 디스패치하여 코드베이스를 분석한다.

**디스패치 프롬프트**:
```
[WORKER]
op-dev-analysis 스킬을 수행하라.
**스킬 경로**: {op-dev-analysis/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {ANALYSIS.md 경로}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```
**model**: light

워커 완료
  → **State Gate**
  → **PM Gate** (분석 방향 종합 검토) → **State Gate**
  → 사용자 보고 (분석 방향 검토 후 PLAN 진입 승인).

## STEP 3: PLAN

### 3-1. PLAN 디스패치
```
[WORKER]
op-dev-plan 스킬을 수행하라.
**스킬 경로**: {op-dev-plan/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {ANALYSIS.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {PLAN.md 경로}, {TEST-SCENARIO.md 경로}, {execution-plan.json 경로 (FE/BE 시)}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```
**model**: advanced

> op-dev-plan 워커가 PLAN.md와 TEST-SCENARIO.md를 통합 작성한다. (문서 전용 작업 시 TEST-SCENARIO.md 스킵 — 워커가 자체 판별)

PLAN 완료
  → **State Gate**
  → **PM Gate** (PLAN.md + TEST-SCENARIO.md 직접 검증 — 점검 목록 참조):
    1. `{PLAN.md 경로}` Read — §4.2 실행 체크리스트, §5 QA 체크리스트 확인
    2. `{TEST-SCENARIO.md 경로}` Read — 시나리오 목록, 코드 품질, 보안 항목 확인 (스킵 시 해당 없음)
    3. 검증 체크리스트:
       - [ ] TASK.md 요구사항 전체 커버 여부 (PLAN.md §1.2 기능 목록 대조)
       - [ ] PLAN.md §4.2 실행 체크리스트 완성도 (소속 F-ID, 완료 기준 명시)
       - [ ] TEST-SCENARIO.md 시나리오가 TASK.md 요구사항 전체를 커버하는가
       - [ ] TEST-SCENARIO.md 보안 항목(시크릿 스캔, .gitignore) 포함 여부
       - [ ] 설계 피드백 섹션에 미해결 빈틈이 없는가
  → **State Gate**
  → 사용자에게 PLAN + TEST-SCENARIO 함께 보고. 승인 = EXECUTE 시작 허가.

## STEP 4: EXECUTE
워커를 디스패치하여 코드를 작성한다.

**디스패치 프롬프트**:
```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**checklist_source**: {PLAN.md 경로}, 섹션: 3. 실행 체크리스트
**execution-plan.json**: {경로 (있으면)}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 매칭 참조 문서. 미존재 시 CLAUDE.md 폴백}
**하네스 Guards**: PLAN.md에 없는 파일 생성/수정 금지. PLAN 설계를 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
```
**model**: standard

### FE/BE 병렬 (execution-plan.json 존재 시)
1. Phase 1: Common → 단일 워커 순차
2. Phase 2: FE + BE 워커 병렬
3. Phase 3: 양쪽 완료 후 통합

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
→ **State Gate** → **TEST 단계 진입**

---

## STEP 5: TEST

op-dev-test-agent 워커 디스패치. TEST-SCENARIO.md 실행 + 결과 기록 + PASS/FAIL 판정.

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + TEST-SCENARIO.md 경로 + changed_files 전달.

워커 완료 → **State Gate**

### PASS 시

→ **PM Gate** (TEST-SCENARIO.md 직접 검증):
  1. `{TEST-SCENARIO.md 경로}` Read — 시나리오 PASS/FAIL 전체 확인
  2. 검증 체크리스트:
     - [ ] TEST-SCENARIO.md 모든 시나리오 PASS
     - [ ] 코드 품질 항목(린트/타입/포맷) 모두 Pass
     - [ ] 보안 항목(시크릿 스캔/.gitignore) Pass
     - [ ] 회귀 테스트 항목 Pass
     - [ ] 설계 피드백 미해결 빈틈 없음
→ **State Gate**
→ DONE.md 생성 (checkpoint-guide.md 참조)
→ 사용자에게 완료 보고

### FAIL 시 (루핑 — 최대 3회, 하네스 §1 L3a)

1. PM이 TEST-SCENARIO.md에서 FAIL 항목을 추출한다
2. op-dev-execute 워커 디스패치 (fix 모드):
   ```
   [WORKER]
   op-dev-execute 스킬을 수행하라 (fix 모드).
   **모드**: fix
   **fix 컨텍스트**:
     - 실패한 TEST-SCENARIO 항목: {FAIL 항목 목록}
     - 현재 시도 회차: {N}/3
     - 실패 요약: {op-dev-test-agent 결과 요약}
   **checklist_source**: PLAN.md 실행 체크리스트 (실패 항목 집중)
   **하네스 Guards**: fix 범위를 실패 항목으로 한정. 회귀 방지: 이전 PASS 항목 재실행.
   ```
3. fix 완료 → **State Gate** → op-dev-test-agent 재호출 (루프)
4. 3회 초과 시 사용자 에스컬레이션:
   "TEST {N}회 FAIL — 수동 개입 필요. 실패 항목: {목록}"

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 추가작업 프로세스를 따른다.

## STATE.md 도메인 설정
- 모드: Full Task
- 단계: TASK / ANALYSIS / PLAN / EXECUTE / TEST
- 산출물: TASK.md, ANALYSIS.md, PLAN.md, TEST-SCENARIO.md, DONE.md

**진행 현황 행 예시** (STATE.md 초기 생성 시 이 구조로 작성):

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | TASK.md 생성 | ⬜ | - |
| 3 | TASK | 사용자 확인 | ⬜ | - |
| 4 | ANALYSIS | 작업 | ⬜ | - |
| 5 | ANALYSIS | ANALYSIS.md 생성 | ⬜ | - |
| 6 | ANALYSIS | State Gate | ⬜ | - |
| 7 | ANALYSIS | PM Gate | ⬜ | - |
| 8 | ANALYSIS | State Gate | ⬜ | - |
| 9 | ANALYSIS | 사용자 확인 | ⬜ | - |
| 10 | PLAN | 작업 | ⬜ | - |
| 11 | PLAN | PLAN.md 생성 | ⬜ | - |
| 12 | PLAN | TEST-SCENARIO.md 생성 | ⬜ | - |
| 13 | PLAN | State Gate | ⬜ | - |
| 14 | PLAN | PM Gate | ⬜ | - |
| 15 | PLAN | State Gate | ⬜ | - |
| 16 | PLAN | 사용자 확인 | ⬜ | - |
| 17 | EXECUTE | 작업 | ⬜ | - |
| 18 | EXECUTE | State Gate | ⬜ | - |
| 19 | TEST | 작업 | ⬜ | - |
| 20 | TEST | State Gate | ⬜ | - |
| 21 | TEST | PM Gate | ⬜ | - |
| 22 | TEST | DONE.md 생성 | ⬜ | - |
| 23 | TEST | State Gate | ⬜ | - |
| 24 | TEST | 사용자 확인 | ⬜ | - |
```

> TEST 루핑 발생 시: "TEST | fix 작업 (N/3)", "TEST | State Gate (N/3)" 행을 동적 추가한다.

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| ANALYSIS | ANALYSIS.md | - |
| PLAN | TASK.md, PLAN.md, TEST-SCENARIO.md | TASK.md 요구사항, PLAN.md §4.2, §5; TEST-SCENARIO.md 시나리오 목록/보안/설계 피드백 |
| TEST | TEST-SCENARIO.md | TEST-SCENARIO.md 시나리오 결과/코드품질/보안/회귀 |

---

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opd --agentic {작업 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름

```
TASK (PM 직접) → ANALYSIS Gate → PLAN Gate → EXECUTE Gate → TEST Gate
                   PM 자율 검토      PM 자율 검토   PM 자율 검토    PM 자율 검토
```

- TASK 이후 4개 게이트를 PM이 자율 통과
- EXECUTE 진입 = PM이 대행 승인 (구현 금지 원칙의 "실행 허가"를 PM이 판단)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

## 변경이력
| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | TEST-SCENARIO를 TODO STEP에 통합, EXECUTE 후 커밋 규칙 추가 |
| v1.2 | 2026-03-28 | TODO를 PLAN에 흡수하여 5→4 STEP, TEST-SCENARIO를 PLAN STEP에 통합, TEST-SCENARIO 스킵 조건 추가 |
| v1.3 | 2026-03-28 | Harness 참조 전환으로 슬림화 (265→105줄) |
| v1.4 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.5 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.6 | 2026-03-31 | Agentic Mode 섹션 추가 (057) |
| v1.7 | 2026-03-31 | §7 참조 → opal-harness-agentic.md 참조 전환. EXECUTE 후 PM Gate + QA 체크리스트 갱신 추가 (058) |
| v1.8 | 2026-04-01 | 전체 워커 디스패치 프롬프트에 `[WORKER]` 마커 + 하네스 Guards + 참조 문서 주입 지침 추가 (063) |
| v1.9 | 2026-04-02 | PLAN PM Gate에 TASK.md 체크박스 갱신 명시 (072) |
| v2.0 | 2026-04-05 | QA Gate에 체크리스트 갱신 포함 + PM Gate에 갱신 상태 확인 + QA 재소환 절차 추가 (085) |
| v2.1 | 2026-04-05 | EXECUTE 후 추가작업 참조 가이드 추가 — 하네스 §3 추가작업 프로세스 (087) |
| v2.2 | 2026-04-07 | TASK/ANALYSIS/PLAN/EXECUTE 각 단계 Gate 순서에 State Gate 추가 (094) |
| v2.3 | 2026-04-07 | State Gate를 PM Gate 전 1개 → 각 Gate 직후로 재배치 (097) |
| v2.4 | 2026-04-08 | TEST-SCENARIO를 Gates 앞으로 이동 + TEST 단계 공식화 + TEST 루핑 구현 (100) |
| v2.5 | 2026-04-09 | STATE.md 도메인 설정 — 진행 현황 행 예시에 산출물 생성 행 추가 (101) |
| v2.6 | 2026-04-10 | ANALYSIS Gate 슬림화 — QA·PM Gate 제거, State Gate + Artifact Gate만 유지. PLAN QA 범위 확대 — ANALYSIS.md 포함 통합 검토 (107) |
| v2.7 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.8 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v2.9 | 2026-04-13 | STEP 3에서 TEST-SCENARIO 별도 디스패치 + QA Gate 제거. PLAN 워커가 TEST-SCENARIO.md 통합 작성. PM Gate에 PLAN.md+TEST-SCENARIO.md Read + 검증 체크리스트 추가. STEP 5 TEST QA Gate 제거, PM Gate에 TEST-SCENARIO.md Read + 검증 체크리스트 추가. Agentic Mode 흐름도 갱신. STATE.md 행 예시 31→24행 갱신 (115) |
