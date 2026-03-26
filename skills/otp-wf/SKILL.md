---
name: otp-wf
description: |
  **Wireframe UI 오케스트레이터**. 와이어프레임 설계부터 UI 구현까지 4단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "와이어프레임", "wireframe", "otp-wf", 와이어프레임부터 설계가 필요한 UI 작업.
  "화면 구현", "UI 만들어줘", "화면 수정" 등 기존 프로젝트 기반 UI 작업은 otp-dev 또는 otp-dev-short에서 ui-designer plan-driven 모드로 수행한다.
---

# Wireframe UI 오케스트레이터

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
dtp-task (Wireframe 특화) → dtp-wireframe → [QA: wireframe] → 검토
  → dtp-execute (UI 구현) → [QA: execute-ui] → 완료
```

### 입력물에 따른 분기

| 입력물 상태 | 판별 방법 | 다음 단계 |
|------------|----------|----------|
| wireframe.md 존재 | 파일 존재 확인 | WIREFRAME 스킵 → EXECUTE |
| 정책서/요구사항 문서 | .md/.txt/.pdf/.docx 파일 | WIREFRAME |
| 이미지(스케치/스크린샷) | .png/.jpg 파일 | WIREFRAME |
| 구두 요청만 | 파일 없음 | interview → WIREFRAME |

---

## STEP 1: TASK (Wireframe 특화)

오케스트레이터가 **직접 수행**한다.

1. `dtp-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/dtp-task/SKILL.md` → `~/.opal/skills/dtp-task/SKILL.md`
2. Wireframe 특화 TASK.md를 작성한다:
   - 구현 목표, 기술 환경 (React/Next.js 버전, shadcn/ui 여부)
   - 출력 모드: 프로토타입(bundle.html) vs 프로덕션(Next.js)
   - 입력물 분류, wireframe.md 경로 (기존/생성 필요)
3. STATE.md를 생성한다.
4. 입력물 분기 판별 후 사용자에게 보고:

```
📋 [TASK] Wireframe UI 완료 보고
📎 산출물: tasks/{NNN}-{태스크명}/TASK.md
입력물 분류: {wireframe.md 존재 / 생성 필요}
다음 단계: {WIREFRAME / EXECUTE (wireframe.md 있을 시)}
진행할까요?
```

---

## STEP 2: WIREFRAME

> wireframe.md가 이미 존재하면 이 단계를 **스킵**하고 EXECUTE로 이동한다.

워커를 디스패치하여 wireframe.md를 생성한다.

**디스패치 프롬프트**:

```
dtp-wireframe 스킬을 수행하라.

**스킬 경로**: {dtp-wireframe/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**이전 산출물**: {TASK.md 경로}
**입력물**: {정책서/이미지 경로}
**프로젝트 컨벤션**: {CLAUDE.md 경로}
**산출물 저장 경로**: {wireframe.md 경로}
```

**model**: sonnet

워커 완료 → **dtp-qa 워커 호출** (단계: WIREFRAME) → QA 결과 포함하여 사용자 보고.

---

## STEP 3: EXECUTE (UI 구현)

워커를 디스패치하여 wireframe.md 기반으로 UI를 구현한다.

**디스패치 프롬프트**:

```
dtp-execute 스킬을 수행하라.

**스킬 경로**: {dtp-execute/SKILL.md 탐색 경로}
**태스크 폴더**: {tasks/{NNN}-{name}/}
**checklist_source**: {wireframe.md 경로} (화면 목록을 체크리스트로 사용)
**이전 산출물**: {TASK.md 경로}, {wireframe.md 경로}
**프로젝트 컨벤션**: {CLAUDE.md 경로}

**UI 구현 모드**:
- wireframe.md + TASK.md의 기술 환경을 입력으로 전달
- ui-designer 스킬의 scaffold 모드(프로토타입) 또는 plan-driven 모드(프로덕션) 호출
- ui-designer 탐색: {프로젝트}/.opal/skills/ui-designer/SKILL.md → ~/.opal/skills/ui-designer/SKILL.md
```

**model**: sonnet

### EXECUTE 완료 후

워커가 changed_files를 반환하면:
1. **dtp-qa 워커 호출** (단계: EXECUTE-UI) → 빌드/린트 + wireframe↔코드 대조
2. **DONE.md 생성**
3. 사용자에게 완료 보고

---

## STATE.md 관리

otp-dev와 동일. 오케스트레이터 전용.

### STATE.md 템플릿

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: Wireframe UI
- 단계: {TASK / WIREFRAME / EXECUTE}
- 진행: {Step N/M 완료 (EXECUTE 시)}
- 상태: {진행 중 / 대기 중 / 블로커 / 완료}

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | {완료 / 미생성} |
| wireframe.md | {완료 / 미생성 / 기존 존재} |
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

otp-dev와 동일. `{프로젝트}/.opal/MEMORY.md` 존재 시 작업 히스토리 갱신.

---

## 스킬 탐색 경로

otp-dev와 동일.
1. `{프로젝트}/.opal/skills/dtp-{stage}/SKILL.md`
2. `~/.opal/skills/dtp-{stage}/SKILL.md`

---

## 게이트 체크포인트

otp-dev와 동일. 각 단계 완료 시 사용자 보고 + 승인 대기.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
