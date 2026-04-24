---
name: opal-pilot-dev-wireframe
description: |
  **Wireframe UI 오케스트레이터**. 와이어프레임 설계부터 UI 구현까지 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev-wireframe", "opdw".
  "화면 구현", "UI 만들어줘", "화면 수정" 등 기존 프로젝트 기반 UI 작업은 opal-pilot-dev 또는 opal-pilot-dev-short에서 ui-designer plan-driven 모드로 수행한다.
---

# Wireframe UI 오케스트레이터

## Harness
모드: Wireframe UI (TASK → WIREFRAME → EXECUTE → CLOSE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

---

## 입력물에 따른 분기

| 입력물 상태 | 판별 방법 | 다음 단계 |
|------------|----------|----------|
| wireframe.md 존재 | 파일 존재 확인 | WIREFRAME 스킵 → EXECUTE |
| 정책서/요구사항 문서 | .md/.txt/.pdf/.docx 파일 | WIREFRAME |
| 이미지(스케치/스크린샷) | .png/.jpg 파일 | WIREFRAME |
| 구두 요청만 | 파일 없음 | interview → WIREFRAME |

---

## STEP 1: TASK (Wireframe 특화)

Harness "TASK 공통 프로세스"를 따르되, 아래를 추가:
- 기술 환경 (React/Next.js 버전, shadcn/ui 여부)
- 출력 모드: 프로토타입(bundle.html) vs 프로덕션(Next.js)
- 입력물 분류 + wireframe.md 경로 (기존/생성 필요)
- 보고 시 입력물 분기 판별 결과 포함

TASK 완료 → **State Gate** (하네스 §3 참조 — STATE.md 갱신 확인) → 사용자 보고.

---

## STEP 2: WIREFRAME

> wireframe.md가 이미 존재하면 **스킵** → EXECUTE.

워커 디스패치로 wireframe.md 생성. **model**: standard.
- 스킬: op-dev-wireframe, 입력: TASK.md + 정책서/이미지
- 완료
  → op-dev-qa 호출 (단계: WIREFRAME) → **State Gate**
  → **PM Gate** (TASK.md 요구사항 체크박스 갱신 포함 — 하네스 §3 참조) → **State Gate** → 사용자 보고

> **[PM 컨텍스트 주입]** 워커 디스패치 프롬프트의 첫 줄에 `[WORKER]`를 삽입한다. `[WORKER]` 마커가 있으면 워커는 부트스트랩을 생략한다. PM은 디스패치 시 다음을 프롬프트에 포함해야 한다:
> 1. 하네스 Guards 핵심 규칙 (구현 금지 원칙, 커밋 규칙)
> 2. 관련 참조 문서 경로 (docs/PROJECT.md 문서 테이블 기반)
> 3. 기술 스택 연동 지시 (기존 "참조 문서 전달 의무" 통합)

---

## STEP 3: EXECUTE (UI 구현)

### 3-1. 라우팅 결정 (v2.2 신설)

와이어프레임 파이프라인의 EXECUTE는 **FE 단일 라우팅**을 사용한다 (분배 디스패치 대상 아님).

- **기본 에이전트**: `opal-fe-agent` (FE 전문)
- **근거**: wireframe.md에는 PLAN.md §4.2와 같은 agent 필드가 없다(op-dev-wireframe 산출물). 와이어프레임 구현은 본질적으로 FE 작업이므로 UI 전문 에이전트를 직접 지정한다.
- **폴백**: `opal-fe-agent` 사용 불가 플랫폼이면 `opal-task-agent`로 디스패치 (op-dev-execute/SKILL.md 매핑에 따라 generalist-guide로 폴백).

### 3-2. 디스패치 프롬프트

워커 디스패치로 wireframe.md 기반 UI 구현. **model**: standard.

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**스킬 경로**: {op-dev-execute/SKILL.md 탐색 경로}
**태스크 폴더**: tasks/{NNN}-{태스크명}/
**checklist_source**: wireframe.md
**UI 구현 모드**: ui-designer scaffold(프로토타입) 또는 plan-driven(프로덕션)
**담당 Step**: wireframe.md 전체 (분배 없음)
**Scope 제한**: FE 영역. 영역 외 파일 수정 시 즉시 블로커 보고.
**하네스 Guards**: wireframe.md에 없는 화면 추가 금지. 설계 임의 변경 금지. 블로커 발생 시 즉시 중단 후 보고.
**참조 문서**: {docs/PROJECT.md 문서 테이블 기반 관련 문서 경로}
**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식 원문 인용}
```

> **에이전트별 자동 가이드 선택**: `opal-fe-agent`로 라우팅되면 워커는 op-dev-execute/SKILL.md 매핑에 따라 execute-specialist-guide.md를 자동 Read한다.

### 3-3. 완료 후

1. op-dev-qa 호출 (단계: EXECUTE-UI) → 빌드/린트 + wireframe↔코드 대조 → **State Gate**
2. **PM Gate** — QA 결과 + 실행 결과 검토 + 체크리스트 갱신 (하네스 §2, §3 참조) → **State Gate**
3. 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청

보고 형식:
```
📋 [EXECUTE] 완료 보고
📎 변경 파일: {changed_files}
📎 산출물: {QA-EXECUTE.md 등}
다음 단계(CLOSE)로 넘어갈까요?
```

---

## STEP 4: CLOSE

모든 체크리스트 갱신 완료 확인 후 태스크를 마감한다.

1. DONE.md 생성
2. State Gate (하네스 §3 참조)
3. 완료 보고

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.

---

## STATE.md 도메인 치환값

Harness STATE.md 템플릿에 적용:
- `{모드}`: Wireframe UI
- `{단계 목록}`: TASK / WIREFRAME / EXECUTE / CLOSE
- `{산출물 목록}`: TASK.md, wireframe.md(기존 존재 가능), QA-*.md, DONE.md

**진행 현황 행 예시** (STATE.md 초기 생성 시 이 구조로 작성):

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | TASK.md 생성 | ⬜ | - |
| 3 | TASK | 사용자 확인 | ⬜ | - |
| 4 | WIREFRAME | 작업 | ⬜ | - |
| 5 | WIREFRAME | wireframe.md 생성 | ⬜ | - |
| 6 | WIREFRAME | QA Gate | ⬜ | - |
| 7 | WIREFRAME | QA-WIREFRAME.md 생성 | ⬜ | - |
| 8 | WIREFRAME | State Gate | ⬜ | - |
| 9 | WIREFRAME | PM Gate | ⬜ | - |
| 10 | WIREFRAME | State Gate | ⬜ | - |
| 11 | WIREFRAME | 사용자 확인 | ⬜ | - |
| 12 | EXECUTE | 작업 | ⬜ | - |
| 13 | EXECUTE | QA Gate | ⬜ | - |
| 14 | EXECUTE | QA-EXECUTE.md 생성 | ⬜ | - |
| 15 | EXECUTE | State Gate | ⬜ | - |
| 16 | EXECUTE | PM Gate | ⬜ | - |
| 17 | EXECUTE | State Gate | ⬜ | - |
| 18 | EXECUTE | 사용자 확인 | ⬜ | - |
| 19 | CLOSE   | DONE.md 생성 | ⬜ | - |
| 20 | CLOSE   | State Gate | ⬜ | - |

> WIREFRAME 스킵 시 (wireframe.md 기존 존재): WIREFRAME 단계 행(#4-#11)을 `-`로 표기한다.

---

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| WIREFRAME | TASK.md, wireframe.md, QA-WIREFRAME.md | TASK.md 요구사항 |
| EXECUTE | QA-EXECUTE.md | - |

---

## Agentic Mode

opal-harness-agentic.md 참조. `--agentic` 플래그 활성화 시 이 스킬의 차이점만 기술한다.

### 활성화

`//opdw --agentic {작업 설명}` 형식으로 호출. STATE.md 모드 필드를 `agentic`으로 기록한다.

### 자율 게이트 흐름

```
TASK (PM 직접) → WIREFRAME Gate → EXECUTE Gate → CLOSE
                  PM 자율 검토     PM 자율 검토    (사용자 승인 후 자동 진행)
```

- TASK 이후 2개 게이트를 PM이 자율 통과 (CLOSE 진입은 사용자 승인 필수)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md에 모든 판단/오류/수정/의사결정 기록

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | Harness 참조 전환으로 슬림화 |
| v1.2 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.3 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
| v1.4 | 2026-04-01 | WIREFRAME/EXECUTE 워커 디스패치에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 (063) |
| v1.5 | 2026-04-02 | 서브 하네스 [MUST] 추가 + WIREFRAME/EXECUTE PM Gate 추가 (072) |
| v1.6 | 2026-04-07 | TASK/WIREFRAME/EXECUTE 각 단계 Gate 순서에 State Gate 추가 + Agentic Mode 섹션 신설 (094) |
| v1.7 | 2026-04-07 | State Gate를 PM Gate 전 1개 → 각 Gate 직후로 재배치 (097) |
| v1.8 | 2026-04-09 | STATE.md 도메인 치환값 — 진행 현황 행 예시 신규 추가 (산출물 생성 행 포함) (101) |
| v1.9 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.0 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v2.1 | 2026-04-15 | STEP 4 CLOSE 단계 신설 + EXECUTE PM Gate 후 State Gate/사용자 확인 추가 + 진행 현황 행 CLOSE 2행 구조 반영 + 보고 형식 C안 적용 (121) |
| v2.2 | 2026-04-23 11:39 | STEP 3 EXECUTE를 FE 단일 라우팅(opal-fe-agent)으로 지정 — 와이어프레임 전용 흐름상 PLAN.md §4.2 분배 디스패치 미적용 근거 명시, 디스패치 프롬프트에 담당 Step/Scope 제한 필드 추가 (129) |
| v2.3 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
