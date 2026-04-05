# TASK: 오케스트레이터 스킬 게이트 — 폴더명 + TASK.md 적용 스킬 강제화

> 작성일: 2026-04-01 | 작업 유형: 개선 | 적용 스킬: opp

## 작업 목표

태스크 폴더 생성 시점부터 오케스트레이터 스킬을 강제 결정하도록, 폴더 네이밍 규칙과 TASK.md 헤더에 스킬약어를 포함시키고, op-task 및 harness에 오케스트레이터 선택 프로세스를 추가한다.

## 배경

PM(알투)이 op-task로 TASK.md만 작성한 뒤, 오케스트레이터 스킬 없이 직접 EXECUTE하는 문제가 반복 발생했다 (064, 065 사례). 폴더명에 스킬약어가 없으면 어떤 오케스트레이터가 사용됐는지 추적도 불가하다.

폴더 생성 = 스킬 결정이 되어야 하고, TASK.md에도 기록되어야 한다.

## 요구사항

### A. op-task SKILL.md 업데이트

- [ ] A1. 저장 경로 규칙 변경: `tasks/{NNN}-{스킬약어}-{태스크명}/` (스킬약어 추가)
- [ ] A2. TASK.md 헤더 템플릿에 `적용 스킬` 필드 추가
- [ ] A3. STEP 5 추가 — 오케스트레이터 선택:
  - 작업 유형 기반 추천 로직 (추천 테이블)
  - 확실하지 않을 경우 선택지 제시 후 사용자 확인
  - 완료 보고에 `적용 스킬: {스킬약어}` 명시

### B. opal-harness.md §4 TASK 공통 프로세스 업데이트

- [ ] B1. op-task 호출 시 스킬약어 전달 의무 명시
- [ ] B2. 완료 보고 형식에 `적용 스킬` 포함

### C. docs/PROJECT.md 네이밍 규칙 업데이트

- [ ] C1. tasks/ 네이밍 규칙에 스킬약어 포함 반영
- [ ] C2. 예시 업데이트

### D. .opal/AGENT.md 확정 기준 추가

- [ ] D1. "태스크 폴더 생성 전 오케스트레이터 스킬 결정 필수" 원칙 추가

## 제약 조건

- 오케스트레이터 각각의 SKILL.md는 수정하지 않는다 (harness §4로 공통 적용)
- 기존 태스크 폴더명은 소급 변경하지 않는다 (신규부터 적용)
- op-task는 소스(`skills/`) 수정 후 배포본(`~/.opal/skills/`)에도 동기화

## 기술 스택

- Markdown 문서 (SKILL.md, opal-harness.md, PROJECT.md, AGENT.md)

## 관련 문서

- `~/.opal/skills/op-task/SKILL.md` — 수정 대상
- `~/.opal/references/opal-harness.md` — 수정 대상
- `docs/PROJECT.md` — 수정 대상
- `.opal/AGENT.md` — 수정 대상
- `opal/skills/` 하위 op-task 소스 — 배포본과 동기화
