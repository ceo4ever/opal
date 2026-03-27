---
name: otp-dev
description: |
  **Full Task 오케스트레이터**. 대규모 개발 작업을 7단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "otp-dev", "otpd".
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 문서(doc-writer), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---

# Full Task 오케스트레이터

## 구현 금지 원칙 (최우선 규칙)

**사용자가 명시적으로 "승인", "진행해", "구현해" 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다.**

허용: 산출물 문서(.md) 작성, QA 에이전트 호출, 코드베이스 읽기/분석, 웹 검색.
금지 (승인 전): 소스 코드 파일 생성/수정, 패키지 설치, DB 스키마 변경, 설정 파일 수정.

---

## Git 사전 점검

태스크 시작 전 `git status`를 확인한다:
- **클린 상태**: 진행
- **커밋되지 않은 변경**: 사용자에게 커밋/스태시를 제안한 후 진행

---

## 파이프라인

```
dtp-task → dtp-analysis → [QA] → 검토
  → dtp-plan → [QA] → 검토
  → dtp-todo → 검토
  → dtp-test-scenario → 검토/승인
  → dtp-execute → [Test] → 완료
```

---

## STEP 1: TASK

오케스트레이터가 **직접 수행**한다 (워커 디스패치 없음).

1. `dtp-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/dtp-task/SKILL.md` → `~/.opal/skills/dtp-task/SKILL.md`
2. 스킬 프로세스를 따라 TASK.md를 작성한다.
3. STATE.md를 생성한다 (아래 STATE.md 관리 참조).
4. 사용자에게 보고:

```
📋 [TASK] 완료 보고
📎 산출물: tasks/{NNN}-{태스크명}/TASK.md
다음 단계(ANALYSIS)로 넘어갈까요?
```

---

## STEP 2: ANALYSIS

워커를 디스패치하여 코드베이스를 분석한다.

**디스패치 프롬프트**:

```
dtp-analysis 스킬을 수행하라.

**스킬 경로**: {dtp-analysis/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 문서 테이블에서 매칭되는 참조 문서. docs/ 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {ANALYSIS.md 경로}
```

**model**: haiku

워커 완료 → **dtp-qa 워커 호출** (단계: ANALYSIS) → **PM 검토 게이트** → QA 결과 + PM 검토 포함하여 사용자 보고. (PM 검토: 글로벌 AGENT.md "PM 컨텍스트 로드" 참조. AGENT.md 미존재 시 스킵)

---

## STEP 3: PLAN

워커를 디스패치하여 구현 계획을 수립한다.

**디스패치 프롬프트**:

```
dtp-plan 스킬을 수행하라.

**스킬 경로**: {dtp-plan/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {ANALYSIS.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 문서 테이블에서 매칭되는 참조 문서. docs/ 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {PLAN.md 경로}, {execution-plan.json 경로 (FE/BE 시)}
```

**model**: opus

워커 완료 → **dtp-qa 워커 호출** (단계: PLAN) → **PM 검토 게이트** → QA 결과 + PM 검토 포함하여 사용자 보고. (PM 검토: 글로벌 AGENT.md "PM 컨텍스트 로드" 참조. AGENT.md 미존재 시 스킵)

---

## STEP 4: TODO

워커를 디스패치하여 실행 체크리스트를 상세 분해한다.

**디스패치 프롬프트**:

```
dtp-todo 스킬을 수행하라.

**스킬 경로**: {dtp-todo/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {ANALYSIS.md 경로}, {PLAN.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 문서 테이블에서 매칭되는 참조 문서. docs/ 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {TODO.md 경로}
```

**model**: haiku

워커 완료 → 사용자에게 보고 (QA 없음). 승인 대기.

---

## STEP 5: TEST-SCENARIO

워커를 디스패치하여 테스트 시나리오를 작성한다.

**디스패치 프롬프트**:

```
dtp-test-scenario 스킬을 수행하라.

**스킬 경로**: {dtp-test-scenario/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {PLAN.md 경로}, {TODO.md 경로}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 문서 테이블에서 매칭되는 참조 문서. docs/ 미존재 시 CLAUDE.md 폴백}
**산출물 저장 경로**: {TEST-SCENARIO.md 경로}
```

**model**: haiku

워커 완료 → 사용자에게 보고. **승인 = EXECUTE 시작 허가**.

---

## STEP 6: EXECUTE

워커를 디스패치하여 코드를 작성한다.

**디스패치 프롬프트**:

```
dtp-execute 스킬을 수행하라.

**스킬 경로**: {dtp-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**checklist_source**: {TODO.md 경로}, 섹션: Part A
**execution-plan.json**: {경로 (있으면)}
**프로젝트 컨텍스트**: {docs/PROJECT.md + 문서 테이블에서 매칭되는 참조 문서. docs/ 미존재 시 CLAUDE.md 폴백}
```

**model**: sonnet

### execution-plan.json 기반 FE/BE 병렬

execution-plan.json이 존재하고 FE+BE 모두 포함 시:
1. Phase 1: Common 항목 → 단일 워커 순차 실행
2. Phase 2: FE 워커 + BE 워커 병렬 디스패치
3. Phase 3: 양쪽 완료 후 통합

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
1. **dtp-test 워커 호출** → TEST-SCENARIO.md에 결과 채움 + 판정
2. **DONE.md 생성** (checkpoint-guide.md 참조)
3. 사용자에게 완료 보고

---

## STATE.md 관리

오케스트레이터 전용. 단계 스킬은 STATE.md를 갱신하지 않는다 (EXECUTE Step 진행 제외).

| 이벤트 | 갱신 주체 | 내용 |
|--------|----------|------|
| TASK 완료 | 오케스트레이터 | STATE.md 초기 생성 |
| 단계 시작 | 오케스트레이터 | `단계`, `상태: 진행 중` |
| 단계 완료 | 오케스트레이터 | `완료 산출물` 갱신, `상태: 대기 중` |
| EXECUTE Step 완료 | 워커 | `진행: Step N/M 완료` |
| 블로커 | 워커 | `상태: 블로커` + `블로커` 섹션 |
| 완료 | 오케스트레이터 | `상태: 완료` |

### STATE.md 템플릿

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: Full Task
- 단계: {TASK / ANALYSIS / PLAN / TODO / TEST-SCENARIO / EXECUTE}
- 진행: {Step N/M 완료 (EXECUTE 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | {완료 / 미생성} |
| ANALYSIS.md | {완료 / 미생성} |
| PLAN.md | {완료 / 미생성} |
| TODO.md | {완료 / 미생성} |
| TEST-SCENARIO.md | {완료 / 미생성} |
| QA-*.md | {완료 / 미생성} |
| DONE.md | {완료 / 미생성} |

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{다음으로 수행할 작업}
```

### 세션 복원

새 세션에서 `tasks/{NNN}-{name}/STATE.md`가 존재하면 Read하여 정확한 지점에서 재개한다.

---

## 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.md`가 존재하면, 단계 완료 시 작업 히스토리도 갱신한다:
- 단계 완료: `단계` 컬럼 → `{단계} ✅ → {다음} 대기`
- DONE.md 생성: `단계` 컬럼 → `완료 (커밋해시)`

---

## 스킬 탐색 경로

모든 단계 스킬 탐색:
1. `{프로젝트}/.opal/skills/dtp-{stage}/SKILL.md`
2. `~/.opal/skills/dtp-{stage}/SKILL.md`

에이전트 탐색:
1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md`
2. `~/.opal/agents/{agent-name}/AGENT.md`

---

## 게이트 체크포인트

각 단계 완료 시 사용자에게 보고하고 승인을 받는다. 응답 패턴:

| 응답 | 동작 |
|------|------|
| "확인", "다음", "승인" | 다음 단계 진행 |
| 피드백/수정 요청 | 현재 단계 수정 후 재보고 |
| "중단", "보류" | 산출물 저장 후 대기 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
