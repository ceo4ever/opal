# TASK: QA 체크리스트 갱신 강제 — QA 에이전트 책임 + PM Gate 확인

> 작성일: 2026-04-05 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요구사항
> 출력: TASK.md

## 작업 목표

PM이 DONE.md 생성 전 PLAN.md QA 체크리스트 갱신을 반복 누락하는 구조적 문제를 해결한다. QA 에이전트가 QA 수행 시 체크리스트를 직접 갱신하고, PM Gate에서 갱신 상태를 확인하는 2단계 구조를 구축한다.

## 배경

- 057~058, 071, 084에서 동일 문제 반복 — PM이 QA 체크리스트를 갱신하지 않고 DONE.md 생성
- 하네스에 규칙은 있지만 강제 장치가 없어 PM 기억에 의존
- QA 에이전트가 항상 발동하지는 않으므로, 에이전트에만 의존할 수 없음 → PM Gate 확인 단계도 필수

## 요구사항

모든 QA Gate(PLAN QA, EXECUTE QA)와 모든 PM Gate에 공통 적용한다.

- [x] R1. QA 에이전트(op-task-qa, op-dev-qa)가 QA 수행 시 해당 시점의 체크리스트를 Read하고, 검증 통과 항목을 `[x]`로 갱신한다
  - PLAN QA 시: TASK.md 요구사항 체크박스 커버리지 확인 + 갱신
  - EXECUTE QA 시: PLAN.md 실행 체크리스트(§3) + QA 체크리스트(§4) 확인 + 갱신
- [x] R2. 모든 PM Gate에 "체크리스트 확인" 필수 단계를 추가한다 — PM이 체크리스트 갱신 상태를 확인하고, 누락이 있으면 QA 에이전트를 재소환하여 갱신하게 한다 (PM이 직접 갱신하지 않음)
  - PLAN PM Gate: TASK.md 요구사항 체크박스 갱신 상태 확인
  - EXECUTE PM Gate: PLAN.md 실행 체크리스트 + QA 체크리스트 갱신 상태 확인
- [x] R3. QA 에이전트가 발동하지 않는 경우에도 PM Gate 확인 단계에서 미갱신을 감지하고, 이 경우 QA 에이전트를 소환하여 갱신한다

## 제약 조건

- 플랫폼 독립 (Claude Code, Cursor, Gemini 모두 동작)
- 기존 QA 에이전트의 역할 확장이지 별도 에이전트 신설이 아님
- 하네스 공통 + 오케스트레이터 SKILL.md 수정으로 해결

## 기술 스택

- Markdown (하네스/스킬 문서 수정)
- OPAL 프레임워크 스킬 명세 형식

## 관련 문서

- `opal/core/references/opal-harness.md` — §2 QA 체크리스트 검증
- `opal/core/references/opal-harness-interactive.md` — §4 체크리스트 검증 게이트
- `opal/skills/op-task-qa/SKILL.md` — 범용 QA 스킬
- `opal/skills/op-dev-qa/SKILL.md` — dev QA 스킬
- `opal/skills/opal-pilot-project/SKILL.md` — opp EXECUTE 완료 후 흐름
- `opal/skills/opal-pilot-dev-short/SKILL.md` — opds EXECUTE 완료 후 흐름
- `opal/skills/opal-pilot-dev/SKILL.md` — opd EXECUTE 완료 후 흐름
- `.opal/memory/feedback_qa_checklist.md` — 기존 피드백
