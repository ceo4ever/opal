# PLAN 014 — 파이프라인 간소화

> 모드: semi-agentic | 근거: 캡틴 #2(속도) + 진단(QA 실효성·19행 실측) + 헌법 §2(단순성)

## 실측 현황 (전 pilot)

| pilot | STATE행 | QA Gate | State Gate 언급 | PM Gate 언급 | QA 워커 실사용 |
|-------|:---:|:---:|:---:|:---:|:---:|
| opds | 19 | 4 | 18 | 14 | ❌ |
| opdw | 20 | 4 | 17 | 15 | ✅ |
| opd | 28 | 5 | 26 | 20 | ❌ |
| opp(project) | 20 | 9 | 16 | 14 | ❌ |
| opwt | (별형식) | 3 | 13 | 10 | ✅ |
| opsdd | **35** | 3 | **32** | 17 | ❌ |

**두 가지 발견**
1) **State Gate가 왕복의 주범** — 트랙당 13~32회. 이게 다 state-tool 호출 = 멈춤.
2) **QA 워커 실사용처는 opdw·opwt 2개뿐** — 나머지는 PM Gate가 검토. → a(QA통합)의 행 감소 효과는 이 2개 트랙에 집중, 나머지는 PM Gate "내용" 강화.

## 의사결정

| # | 결정 | 권고 |
|---|------|------|
| M-1 | **a — QA 문서검토를 PM Gate로 통합.** QA Gate 단계 제거(opdw/opwt) + PM Gate를 "요구사항→설계 누락·오해 검토 + self-check"로 강화 | 채택 |
| M-2 | **L1 — 산출물 생성 행을 작업 행에 흡수** (PLAN.md/TEST-SCENARIO.md 등 별도행 제거, 문서는 그대로 작성) | 채택 |
| M-3 | **L1 — State Gate 중복 제거** (PM Gate 앞뒤 2개 → 1개) | 채택 |
| **M-A** | **State Gate 별도행 전면 제거 + 단계 건너뛰기 차단을 도구로 이전** — State Gate 행 제거(13~32회→0)하되, state-tool에 **stage-transition guard** 신설: "단계 N의 필수 작업/PM Gate 행이 done이 아니면 단계 N+1 진입(mark) 거부". 행(advisory)으로 막던 무단 진행을 도구(deterministic)로 차단 → 행↓ + 강제↑ | **채택 (캡틴 a)** |
| M-4 | **L2 — 경량 트랙** 진입 기준 정의 (파일 1~2개·단순수정 → 풀파이프라인 우회) | 채택 |
| M-5 | **불변** — TEST-SCENARIO 작성·TEST·state-tool verify는 독립 유지 (동작 검증, self-confirming 위험) | 고정 |

## 변경 규칙 (전 pilot 일괄)

1. **산출물 행 흡수**: `PLAN.md 생성`·`TEST-SCENARIO.md 생성` → `PLAN 작업` 행에 포함
2. **State Gate**: 별도행 전면 제거(M-A). 대신 state-tool에 **stage-transition guard** 신설 — 단계 N 필수 행 미완 시 N+1 진입 거부. **행 제거보다 guard 신설이 먼저**(강제 공백 방지)
3. **QA Gate → PM Gate**: QA 워커(opdw/opwt) 디스패치 제거. PM Gate 체크리스트에 QA 항목(요구사항 누락·오해·정합성) 흡수 + self-check 질문 추가
4. **L2 경량 트랙**: 진입 기준 + 축약 파이프라인 정의

## 영향 범위

| 대상 | 변경 |
|------|------|
| pilot 8종 SKILL.md | STATE 행 재구성 (규칙 일괄 적용) |
| `qa-standards.md` | QA→PM Gate 통합, EXECUTE QA 고아규칙을 PM Gate/TEST에 연결 |
| `pm-review-gate.md` | PM Gate에 QA 항목 + self-check 흡수 |
| `op-dev-qa` 스킬 | opdw/opwt 문서검토 전용으로 역할 한정 (또는 PM Gate 흡수) |
| `opal-harness-interactive.md` | QA Gate 절 ↔ opds 모순 해소 |
| `state_tool.py` | (M-A 채택 시) gate-pattern 검증 로직 수정 + 테스트 |

## before/after 추정 (행 수)

| pilot | 지금 | M-2·M-3만 | +M-A |
|-------|:---:|:---:|:---:|
| opds | 19 | ~11 | **~8** |
| opd | 28 | ~17 | **~12** |
| opsdd | 35 | ~22 | **~15** |

## Phase 구성

```
Phase 1: state_tool.py stage-transition guard 신설 + 테스트 (강제 기반 먼저 — 캡틴 우려 직결)
Phase 2: opds STATE 행 재구성 시범 적용 (guard 위에서 안전하게) → 검증 (파일럿)
Phase 3: PM Gate 강화 (QA 항목 흡수 + self-check) + QA 통합 (qa-standards/pm-review-gate/op-dev-qa/interactive 하네스)
Phase 4: 나머지 pilot 7종 STATE 행 일괄 재구성
Phase 5: L2 경량 트랙 정의
```

> **Phase 순서 핵심**: 단계 건너뛰기를 막던 State Gate 행을 제거하기 **전에**, 그 강제를 state-tool guard로 먼저 이전한다(Phase 1). 그래야 행 제거(Phase 2~) 시점에 강제 공백이 생기지 않는다 (캡틴 우려 반영).

## 리스크

| 리스크 | 대응 |
|------|------|
| State Gate 축소 → 추적 세밀도↓ | 기록 자체는 행 mark로 유지, 메타 추적행만 제거 |
| state_tool gate-pattern 변경 회귀 (M-A) | 헌법 §4 — 실제 테스트로 검증, 136 테스트 회귀 확인 |
| 전 pilot 일괄 변경 영향 큼 | Phase 1 opds 파일럿 후 확산 (단계적) |
| 동작 검증 약화 우려 | TEST·verify는 불변(M-5) — 손대지 않음 |
