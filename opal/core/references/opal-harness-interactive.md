# opal-harness-interactive.md

> interactive 모드(기본) 전용 하네스. 공통 하네스(opal-harness.md)와 함께 로드한다.

---

## 1. 단계 게이트

각 단계 완료 시 사용자에게 보고하고 승인을 받는다.

| 응답 | 동작 |
|------|------|
| "확인", "다음", "승인" | 다음 단계 진행 |
| 피드백/수정 요청 | 현재 단계 수정 후 재보고 |
| "중단", "보류" | 산출물 저장 후 대기 |

---

## 2. QA Gate

단계 완료 후 QA 에이전트를 호출하여 산출물을 검증한다.

| 오케스트레이터 도메인 | QA 스킬 (qa_skill) | QA 에이전트 |
|---------------------|-------------------|------------|
| dev (opd/opds/opdw) | op-dev-qa | opal-task-qa-agent |
| 범용 (opp) | op-task-qa | opal-task-qa-agent |

각 오케스트레이터 SKILL.md에서 QA 스킬명을 명시한다.
탐색 경로: `{프로젝트}/.opal/skills/{qa-skill}/SKILL.md` -> `~/.opal/skills/{qa-skill}/SKILL.md`

---

## 3. PM Gate

`.opal/AGENT.md`가 존재하면 PM 검토 기준으로 산출물을 검토한다.
상세: 글로벌 AGENT.md "PM 컨텍스트 로드 > PM 검토 게이트".
AGENT.md 미존재 시 스킵.

---

## 4. 체크리스트 검증 게이트

EXECUTE 완료 후, PLAN.md 실행 체크리스트 갱신을 2단계로 보장한다.

**1차 책임 — 워커(서브에이전트)**:
- EXECUTE 중 각 Step 완료 시 PLAN.md 체크박스 즉시 갱신 (`- [ ]` → `- [x]`)
- QA 체크리스트도 검증 후 갱신

**2차 검증 — 오케스트레이터(PM)**:
- 워커 결과 수신 후 PLAN.md를 Read하여 체크리스트 갱신 상태 확인
- 미갱신 항목 발견 시: PM이 직접 갱신
- **체크리스트 완전 갱신 확인 후에만** DONE.md / 완료 보고로 진행

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-31 | 초기 작성 — opal-harness.md §2에서 분리 (058) |
