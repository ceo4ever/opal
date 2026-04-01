# TASK: EXECUTE 후 검증 흐름 재설계 — task-flow-test 중심으로 전환

> 작성일: 2026-03-18 | 작업 유형: 기능 개선

## 작업 목표

EXECUTE 전후 검증 흐름을 재설계한다:
1. PLAN/TODO 완료 후 task-flow-agent가 TEST-SCENARIO.md를 작성 (설계 검증 + 테스트 계획)
2. EXECUTE 완료 후 task-flow-test가 TEST-SCENARIO.md에 실행 결과를 채워넣고 판정
3. task-flow-test 결과를 오케스트레이터가 사용자에게 보고
4. task-flow-qa의 EXECUTE 검증(QA-EXECUTE.md) 폐지 — task-flow-test가 대체

## 배경

현재 EXECUTE 완료 후 검증을 task-flow-qa(문서 리뷰 에이전트, `readonly: true`)가 QA-EXECUTE.md로 담당하고 있다. 하지만 QA는 실제 코드를 실행할 수 없고, 문서만 읽고 "인라인 테스트 결과가 Pass인가?"를 판단하는 수준이다. task-flow-test는 복잡 모드에서만 호출되어 대부분의 작업에서 동적 검증이 빠져 있다.

또한 현재 테스트 시나리오는 PLAN/TODO의 QA 체크리스트에 항목 수준(`- [ ] 로그인 성공 시 토큰 반환`)으로만 존재한다. 구체적인 시나리오(조건, 기대 결과)를 작성하는 과정 자체가 설계의 빈틈을 발견하는 중요한 활동인데, 이 과정이 빠져 있다.

## 요구사항

- [ ] TEST-SCENARIO.md 산출물 신규 추가 — PLAN/TODO 완료 후, EXECUTE 전에 작성
- [ ] task-flow-agent가 TEST-SCENARIO.md 작성 (PLAN/TODO 컨텍스트를 이어서, 설계 검증 겸 수행)
- [ ] TEST-SCENARIO.md를 사용자 검토 게이트로 설정 (승인 후 EXECUTE 진행)
- [ ] task-flow-test: 복잡 모드 전용 → **모든 모드에서 항상 호출**
- [ ] task-flow-test: TEST-SCENARIO.md를 입력으로 받아 실행하고 **같은 파일에 결과를 채워넣음**
- [ ] task-flow-test: 결과를 오케스트레이터에게 반환 → 사용자에게 보고
- [ ] QA-EXECUTE.md 폐지 — task-flow-test가 EXECUTE 검증을 대체
- [ ] task-flow-qa: EXECUTE 단계 검증 제거 (RESEARCH, PLAN 검증만 유지)
- [ ] TEST-REPORT.md 삭제 — TEST-SCENARIO.md가 계획과 결과를 단일 파일로 관리
- [ ] 문서만 변경한 태스크는 코드 테스트 스킵 규칙 추가
- [ ] 3개 플랫폼(Claude, Cursor, Antigravity) 에이전트 파일 동기화

## 설계 결정

### 1. 테스트 시나리오 책임 분배

테스트 시나리오 구성요소:
1. **대상** — 뭘 테스트할지 (어떤 기능/변경점)
2. **조건** — 어떤 입력, 어떤 상태에서
3. **기대 결과** — 성공 기준
4. **방법/도구** — 어떻게 검증할지 (jest, pytest, Playwright 등)

**결정: B안** — task-flow-agent(1~3) + task-flow-test(4+실행)

| 역할 | 담당 | 이유 |
|------|------|------|
| 시나리오 작성 (1~3) | task-flow-agent | PLAN/TODO 컨텍스트를 이어서 작성. 작성 과정에서 설계 빈틈 발견 시 즉시 피드백 가능 |
| 도구 결정 + 실행 (4) | task-flow-test | 독립 컨텍스트에서 프로젝트 환경에 맞는 도구로 실행. 구현자와 검증자 분리 |

기각된 안:
- **A안** (PLAN 1~4): 구현 전에 도구까지 정하는 건 과함
- **C안** (PLAN 1만): task-flow-test 부담 과다
- **D안** (test 전부): 사전 검토 불가, 코드 분석 맥락 없음
- **전담 에이전트 신설**: 컨텍스트가 이어지지 않으므로 task-flow-agent 대비 이점 없음

### 2. EXECUTE 검증 역할 변경

| 변경 전 | 변경 후 |
|---------|---------|
| task-flow-qa가 QA-EXECUTE.md 생성 (문서 리뷰 기반) | task-flow-test가 TEST-SCENARIO.md에 결과 기록 (실제 실행 기반) |
| task-flow-test는 복잡 모드에서만 TEST-REPORT.md 생성 | task-flow-test가 모든 모드에서 TEST-SCENARIO.md에 결과 채움 |
| QA-EXECUTE.md + TEST-REPORT.md 2개 산출물 | TEST-SCENARIO.md 1개로 통합 |

이유: task-flow-test가 실제로 코드를 실행해서 검증하는데, task-flow-qa가 또 문서를 보고 "검증됐나?" 확인하는 건 중복.

### 3. task-flow-qa 역할 축소

| 단계 | 변경 전 | 변경 후 |
|------|---------|---------|
| RESEARCH | QA 호출 | QA 호출 (유지) |
| PLAN | QA 호출 | QA 호출 (유지) |
| EXECUTE | QA 호출 → QA-EXECUTE.md | **제거** — task-flow-test가 대체 |

## 새로운 전체 흐름

### Full Task

```
TASK → RESEARCH → [QA] → PLAN → [QA] → TODO
  → task-flow-agent: TEST-SCENARIO.md 작성 (설계 검증)
  → 사용자 검토/승인
  → EXECUTE
  → task-flow-test: TEST-SCENARIO.md 실행 + 결과 채움 + 판정
  → 오케스트레이터: 테스트 결과 포함 완료 보고
  → DONE.md
```

### Short Task

```
TASK → PLAN → [QA]
  → task-flow-agent: TEST-SCENARIO.md 작성 (설계 검증)
  → 사용자 검토/승인
  → EXECUTE
  → task-flow-test: TEST-SCENARIO.md 실행 + 결과 채움 + 판정
  → 오케스트레이터: 테스트 결과 포함 완료 보고
  → DONE.md
```

## 산출물 구조 변경

### Full Task

```
tasks/{NNN}-{태스크명}/
├── STATE.md
├── TASK.md, RESEARCH.md, QA-RESEARCH.md
├── PLAN.md, QA-PLAN.md
├── TODO.md
├── TEST-SCENARIO.md      ← 신규: 테스트 시나리오 + 실행 결과 (단일 파일)
├── DONE.md
└── skills/                (복잡 모드, 필요 시)
```

### Short Task

```
tasks/{NNN}-{태스크명}/
├── STATE.md
├── TASK.md
├── PLAN.md, QA-PLAN.md
├── TEST-SCENARIO.md      ← 신규: 테스트 시나리오 + 실행 결과
└── DONE.md
```

**삭제되는 산출물:**
- ~~QA-EXECUTE.md~~ — task-flow-test가 대체
- ~~TEST-REPORT.md~~ — TEST-SCENARIO.md에 통합

## 제약 조건

- 기존 QA 에이전트의 RESEARCH/PLAN 단계 검증 역할은 변경하지 않음
- Planner 에이전트 호출 규칙(Full Task 복잡 모드 전용)은 변경하지 않음
- 3개 플랫폼 에이전트 파일의 내용은 동일하게 유지 (포맷만 다름)
- task-flow-agent 컨텍스트 연속성(resume 기본화)은 별도 태스크로 분리

## 변경 파일 목록

| # | 파일 | 변경 규모 | 변경 내용 |
|---|------|----------|----------|
| 1 | `agents/claude/task-flow-test/AGENT.md` | 대폭 | 모든 모드 호출, TEST-SCENARIO.md 입력, 도구 결정+실행+판정, 결과를 같은 파일에 기록 |
| 2 | `skills/task-flow/SKILL.md` | 중간 | TEST-SCENARIO.md 단계 추가, Test 호출 규칙 확장, QA EXECUTE 제거, 산출물 구조 갱신 |
| 3 | `skills/task-flow/references/execute-guide.md` | 중간 | 모든 모드에서 test 호출, QA-EXECUTE 제거, 최종 보고 갱신 |
| 4 | `agents/claude/task-flow-qa/AGENT.md` | 중간 | EXECUTE 검증 제거, RESEARCH/PLAN만 유지 |
| 5 | `agents/cursor/task-flow-test.md` | 대폭 | #1과 동일 내용 (Cursor 포맷) |
| 6 | `agents/cursor/task-flow-qa.md` | 중간 | #4와 동일 내용 (Cursor 포맷) |
| 7 | `agents/antigravity/task-flow-test/SKILL.md` | 대폭 | #1과 동일 내용 (SKILL.md 포맷) |
| 8 | `agents/antigravity/task-flow-qa/SKILL.md` | 중간 | #4와 동일 내용 (SKILL.md 포맷) |
| 9 | `skills/task-flow/references/execute-plan-guide.md` | 경미 | 테스트 전략에서 TEST-SCENARIO.md 참조 추가 |
| 10 | `CLAUDE.md` | 경미 | 산출물 구조 갱신 (TEST-SCENARIO.md 추가, QA-EXECUTE/TEST-REPORT 삭제) |
| 11 | 테스트 시나리오 가이드 (신규) | 신규 | TEST-SCENARIO.md 작성 가이드 + 템플릿 |

## 관련 문서

- `skills/task-flow/SKILL.md` — 오케스트레이터 스킬
- `agents/claude/task-flow-test/AGENT.md` — 테스트 에이전트
- `agents/claude/task-flow-qa/AGENT.md` — QA 에이전트
- `skills/task-flow/references/execute-guide.md` — EXECUTE 가이드
- `skills/task-flow/references/execute-plan-guide.md` — 실행 아키텍처 가이드
