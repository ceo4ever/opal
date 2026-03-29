---
name: opal-pilot-dev-wireframe
description: |
  **Wireframe UI 오케스트레이터**. 와이어프레임 설계부터 UI 구현까지 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-dev-wireframe", "opdw".
  "화면 구현", "UI 만들어줘", "화면 수정" 등 기존 프로젝트 기반 UI 작업은 opal-pilot-dev 또는 opal-pilot-dev-short에서 ui-designer plan-driven 모드로 수행한다.
---

# Wireframe UI 오케스트레이터

## Harness
모드: Wireframe UI (TASK → WIREFRAME → EXECUTE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

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

---

## STEP 2: WIREFRAME

> wireframe.md가 이미 존재하면 **스킵** → EXECUTE.

워커 디스패치로 wireframe.md 생성. **model**: standard.
- 스킬: op-dev-wireframe, 입력: TASK.md + 정책서/이미지
- 완료 → op-dev-qa 호출 (단계: WIREFRAME) → 사용자 보고

---

## STEP 3: EXECUTE (UI 구현)

워커 디스패치로 wireframe.md 기반 UI 구현. **model**: standard.
- 스킬: op-dev-execute, checklist_source: wireframe.md
- **UI 구현 모드**: ui-designer scaffold(프로토) 또는 plan-driven(프로덕션) 호출

### 완료 후
1. op-dev-qa 호출 (단계: EXECUTE-UI) → 빌드/린트 + wireframe↔코드 대조
2. DONE.md 생성 → 사용자 완료 보고

---

## STATE.md 도메인 치환값

Harness STATE.md 템플릿에 적용:
- `{모드}`: Wireframe UI
- `{단계 목록}`: TASK / WIREFRAME / EXECUTE
- `{산출물 목록}`: TASK.md, wireframe.md(기존 존재 가능), QA-*.md, DONE.md

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-26 | 초기 작성 — dev-task-pilot 컴포지션 전환 |
| v1.1 | 2026-03-28 | Harness 참조 전환으로 슬림화 |
| v1.2 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.3 | 2026-03-29 | model override를 레벨 기반으로 전환 (044) |
