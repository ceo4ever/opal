---
name: dtp-dev-short
description: |
  **Short Task 오케스트레이터**. 소규모 개발 작업을 4단계 파이프라인으로 수행한다. ANALYSIS와 TODO를 생략하고, PLAN에서 분석+설계를 통합한다.
  반드시 이 스킬을 사용해야 하는 상황: "수정해줘", "Short", "/dtp-dev-short", 코드 변경이 수반되는 소규모 작업 (버그 수정, 단순 기능 수정/추가, 리팩토링).
  코드를 읽기만 하는 설명 요청, API 명세서(api-analyzer), 문서(doc-writer), PR 리뷰, git 작업, 단순 설정 변경은 이 스킬이 아니다.
---

# Short Task 오케스트레이터

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
dtp-task → dtp-plan (ANALYSIS.md 없이) → [QA] → 검토
  → dtp-test-scenario → 검토/승인
  → dtp-execute → [Test] → 완료
```

> **Short Task는 단계를 줄이는 것이지, 분석을 줄이는 것이 아니다.** dtp-plan이 ANALYSIS.md 없이 호출되면 코드 분석을 직접 수행한다. 분석 품질은 Full Task와 동일해야 한다.

---

## STEP 1: TASK

오케스트레이터가 **직접 수행**한다.

1. `dtp-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/dtp-task/SKILL.md` → `~/.opal/skills/dtp-task/SKILL.md`
2. 스킬 프로세스를 따라 TASK.md를 작성한다.
3. STATE.md를 생성한다.
4. 사용자에게 보고:

```
📋 [TASK] 완료 보고
📎 산출물: tasks/{NNN}-{태스크명}/TASK.md
다음 단계(PLAN)로 넘어갈까요?
```

---

## STEP 2: PLAN (분석 + 설계 통합)

워커를 디스패치하여 코드 분석과 구현 계획을 통합 수립한다. **ANALYSIS.md를 전달하지 않는다** → dtp-plan이 자동으로 코드 분석을 포함한다.

**디스패치 프롬프트**:

```
dtp-plan 스킬을 수행하라.

**스킬 경로**: {dtp-plan/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**프로젝트 컨벤션**: {CLAUDE.md 경로}
**산출물 저장 경로**: {PLAN.md 경로}, {execution-plan.json 경로 (FE/BE 시)}
```

**model**: opus

워커 완료 → **dtp-qa 워커 호출** (단계: PLAN) → QA 결과 포함하여 사용자 보고.

---

## STEP 3: TEST-SCENARIO

워커를 디스패치하여 테스트 시나리오를 작성한다.

**디스패치 프롬프트**:

```
dtp-test-scenario 스킬을 수행하라.

**스킬 경로**: {dtp-test-scenario/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}, {PLAN.md 경로}
**프로젝트 컨벤션**: {CLAUDE.md 경로}
**산출물 저장 경로**: {TEST-SCENARIO.md 경로}
```

**model**: haiku

워커 완료 → 사용자에게 보고. **승인 = EXECUTE 시작 허가**.

---

## STEP 4: EXECUTE

워커를 디스패치하여 코드를 작성한다.

**디스패치 프롬프트**:

```
dtp-execute 스킬을 수행하라.

**스킬 경로**: {dtp-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**checklist_source**: {PLAN.md 경로}, 섹션: 3. 실행 체크리스트
**execution-plan.json**: {경로 (있으면)}
**프로젝트 컨벤션**: {CLAUDE.md 경로}
```

**model**: sonnet

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
1. **dtp-test 워커 호출** → TEST-SCENARIO.md에 결과 채움 + 판정
2. **DONE.md 생성**
3. 사용자에게 완료 보고

---

## 에스컬레이션 규칙

dtp-plan 결과에서 아래 조건이 감지되면 **Full Task(dtp-dev) 전환을 제안**한다:

| 조건 | 판별 방법 |
|------|----------|
| 예상 변경 파일 ≥10개 | PLAN.md 파일 변경 계획에서 카운트 |
| 다단계 기술 의사결정 | 아키텍처 선택, 기술 스택 비교가 필요한 수준 |
| 다중 모듈 연쇄 영향 | 변경이 3개 이상 독립 모듈에 연쇄 영향 |

```
⚠️ [에스컬레이션 제안]

이 작업은 Short Task 범위를 초과할 수 있습니다:
- {해당 조건}

Full Task(dtp-dev)로 전환할까요?
- "Full로 해줘" → Full Task 전환
- "Short로 진행해" → Short Task 유지
```

---

## STATE.md 관리

dtp-dev와 동일. 오케스트레이터 전용.

### STATE.md 템플릿

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: Short Task
- 단계: {TASK / PLAN / TEST-SCENARIO / EXECUTE}
- 진행: {Step N/M 완료 (EXECUTE 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | {완료 / 미생성} |
| PLAN.md | {완료 / 미생성} |
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

---

## 프로젝트 메모리 동기화

dtp-dev와 동일. `{프로젝트}/.opal/MEMORY.md` 존재 시 작업 히스토리 갱신.

---

## 스킬 탐색 경로

dtp-dev와 동일.
1. `{프로젝트}/.opal/skills/dtp-{stage}/SKILL.md`
2. `~/.opal/skills/dtp-{stage}/SKILL.md`

---

## 게이트 체크포인트

dtp-dev와 동일. 각 단계 완료 시 사용자 보고 + 승인 대기.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
