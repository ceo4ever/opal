# TASK: EXECUTE 완료 시 QA 체크리스트 갱신 + 완료 리포트 생성 규칙 추가

> 작성일: 2026-03-15 | 작업 유형: 기능 개선

## 작업 목표

task-flow EXECUTE 완료 후 (1) QA 체크리스트 항목을 검증하고 체크박스를 갱신하고, (2) DONE.md 완료 리포트를 생성하는 규칙을 task-flow 스킬에 정식 반영한다.

## 배경

현재 EXECUTE 단계에서 실행 체크리스트(PLAN.md 섹션 3 / TODO.md Part A)는 갱신하지만, QA 체크리스트(PLAN.md 섹션 4 / TODO.md Part B)는 갱신하지 않고 있다. 또한 태스크 완료 시 기록을 남기는 완료 리포트가 없어 추적이 어렵다.

## 요구사항

- [ ] R1. EXECUTE 완료 시 QA 체크리스트(기능/회귀/품질) 항목을 검증하고 체크박스 갱신하는 규칙 추가
- [ ] R2. 태스크 완료 시 DONE.md 생성 규칙 추가 (완료 요약, 변경 파일, QA 결과, 산출물 목록)
- [ ] R3. DONE.md 템플릿 정의
- [ ] R4. 산출물 저장 구조에 DONE.md 추가

## 제약 조건

- 기존 워크플로우 흐름(게이트 체크포인트, QA 에이전트 호출)은 변경하지 않는다
- QA 체크리스트 갱신은 워커가 수행 (QA 에이전트와는 별도)

## 관련 문서

- `skills/task-flow/SKILL.md` — EXECUTE 단계, 산출물 저장 구조
- `skills/task-flow/references/execute-guide.md` — EXECUTE 상세 가이드
- `CLAUDE.md` — 산출물 저장 구조
