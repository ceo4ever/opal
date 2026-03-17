# TASK: EXECUTE 후 검증 흐름 재설계 — task-flow-test 중심으로 전환

> 작성일: 2026-03-18 | 작업 유형: 기능 개선

## 작업 목표

EXECUTE 완료 후 코드 검증을 task-flow-test가 모든 모드에서 항상 수행하도록 재설계하고, 커뮤니티 테스트 스킬(Playwright, pytest 등)을 도구로 활용할 수 있게 한다.

## 배경

현재 EXECUTE 완료 후 검증을 task-flow-qa(문서 리뷰 에이전트, `readonly: true`)가 QA-EXECUTE.md로 담당하고 있다. 하지만 QA는 실제 코드를 실행할 수 없고, 문서만 읽고 "인라인 테스트 결과가 Pass인가?"를 판단하는 수준이다. task-flow-test는 복잡 모드에서만 호출되어 대부분의 작업에서 동적 검증이 빠져 있다.

## 요구사항

- [ ] task-flow-test: 복잡 모드 전용 → **모든 모드에서 항상 호출**
- [ ] task-flow-qa: 코드 검증 포함 → **문서 정합성 검증만** (TEST-REPORT.md 참조)
- [ ] TEST-REPORT.md: 복잡 모드만 → **모든 모드에서 생성**
- [ ] 새로운 EXECUTE 후 흐름 통일: `EXECUTE 완료 → test → qa → DONE.md → 보고`
- [ ] 테스트 시나리오 책임 분배 (미확정, 아래 설계 논점 참조)
- [ ] 문서만 변경한 태스크는 B-1/B-2 스킵 규칙 추가
- [ ] TEST-REPORT.md 템플릿에 "사용된 테스트 스킬" 섹션 추가
- [ ] 3개 플랫폼(Claude, Cursor, Antigravity) 에이전트 파일 동기화

## 설계 논점: 테스트 시나리오 책임 분배

테스트 시나리오 구성요소:
1. **대상** — 뭘 테스트할지 (어떤 기능/변경점)
2. **조건** — 어떤 입력, 어떤 상태에서
3. **기대 결과** — 성공 기준
4. **방법/도구** — 어떻게 검증할지 (jest, pytest, Playwright 등)

| 선택지 | PLAN | task-flow-test | 장점 | 단점 |
|--------|------|---------------|------|------|
| **A** PLAN 1~4 | 대상+조건+기대+도구 | 실행만 | 승인 전 전체 검토 가능 | PLAN이 무거움, 구현 전에 도구까지 정하는 건 과할 수 있음 |
| **B** PLAN 1~3 | 대상+조건+기대 | 도구 결정+실행 | 자연스러운 분업. "뭘 검증할지"와 "어떻게 돌릴지" 분리 | test가 도구 선택 책임 |
| **C** PLAN 1만 | 대상만 | 조건+기대+도구+실행 | PLAN 가벼움 | test가 테스트 설계자가 됨. 책임 과다 |
| **D** test 전부 | 없음 | 전부 | PLAN 부담 없음 | 사전 검토 불가. test가 코드 분석까지 해야 함 |

> 현재 유력: **B안** — PLAN이 1~3(대상+조건+기대), task-flow-test가 4(도구)+실행. 최종 결정 보류 중.

## 제약 조건

- 기존 QA 에이전트의 RESEARCH/PLAN 단계 검증 역할은 변경하지 않음
- Planner 에이전트 호출 규칙(Full Task 복잡 모드 전용)은 변경하지 않음
- 3개 플랫폼 에이전트 파일의 내용은 동일하게 유지 (포맷만 다름)

## 새로운 EXECUTE 후 흐름 (모든 모드 통일)

```
EXECUTE 워커 완료 → 결과 반환
  → 오케스트레이터: task-flow-test 호출 → TEST-REPORT.md 생성
  → 오케스트레이터: task-flow-qa 호출 → QA-EXECUTE.md 생성 (문서 정합성만)
  → 오케스트레이터: DONE.md 생성
  → 사용자에게 완료 보고
```

## 변경 파일 목록 (10개)

| # | 파일 | 변경 규모 | 변경 내용 |
|---|------|----------|----------|
| 1 | `agents/claude/task-flow-test/AGENT.md` | 대폭 | 모든 모드 호출, 입력 확장, PLAN 기반 테스트 전략 실행, 문서 전용 규칙, 템플릿 확장 |
| 2 | `skills/task-flow/SKILL.md` | 중간 | Test 호출 규칙 확장, 3가지 흐름에 test 호출 추가, 산출물 구조 갱신 |
| 3 | `skills/task-flow/references/execute-guide.md` | 중간 | 단순/Short 모드에 test 호출 추가, 최종 보고 갱신, 품질 체크리스트 갱신 |
| 4 | `agents/claude/task-flow-qa/AGENT.md` | 중간 | E-5/E-7 역할 축소, TEST-REPORT.md 필수, 호출 시점 명시 |
| 5 | `agents/cursor/task-flow-test.md` | 대폭 | #1과 동일 내용 (Cursor 포맷) |
| 6 | `agents/cursor/task-flow-qa.md` | 중간 | #4와 동일 내용 (Cursor 포맷) |
| 7 | `agents/antigravity/task-flow-test/SKILL.md` | 대폭 | #1과 동일 내용 (SKILL.md 포맷) |
| 8 | `agents/antigravity/task-flow-qa/SKILL.md` | 중간 | #4와 동일 내용 (SKILL.md 포맷) |
| 9 | `skills/task-flow/references/execute-plan-guide.md` | 경미 | Part C-4에 커뮤니티 테스트 스킬 매칭 항목 추가 |
| 10 | `CLAUDE.md` | 경미 | 산출물 구조에서 "(복잡 모드)" 제거, Short Task에 TEST-REPORT.md 추가 |

## 관련 문서

- `skills/task-flow/SKILL.md` — 오케스트레이터 스킬
- `agents/claude/task-flow-test/AGENT.md` — 테스트 에이전트
- `agents/claude/task-flow-qa/AGENT.md` — QA 에이전트
- `skills/task-flow/references/execute-guide.md` — EXECUTE 가이드
- `skills/task-flow/references/execute-plan-guide.md` — 실행 아키텍처 가이드
