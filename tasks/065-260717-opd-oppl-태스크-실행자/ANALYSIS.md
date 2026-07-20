# ANALYSIS: oppl 태스크 실행자 도입 설계 — 파이프라인 위임 경로 분석

> 작성일: 2026-07-17
> 입력: TASK.md
> 출력: ANALYSIS.md
> 작성 경위: 분석 수행 = ANALYSIS 워커(opal-task-agent, light). 워커가 산출물 파일 저장에 2회 실패(보고문 반환)하여 PM이 워커 보고 전문을 파일로 고정(폴백 — AGENTIC-LOG #2~#5). PM 스팟 체크 3건(install 배포·SKILL.md 줄번호·loop-control 줄 50) 일치 확인.

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | oppl 오케스트레이터 본문 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 태스크 내부 파이프라인(T1~T5+G)·디스패치(하이브리드 C) 절 개편 대상 |
| D-2 | 설계 | oppd 액션 에이전트 | `opal/agents/opal-task-action-agent/AGENT.md` | 입력 명세·내부 파이프라인·결과 계약·재시도 상한의 준거 구조 |
| D-3 | 설계 | opsdd 액션 에이전트 | `opal/agents/opal-sdd-action-agent/AGENT.md` | oppd와의 동형 선례, 입력/출력 계약 비교 |
| D-4 | 설계 | 루프 제어 가이드 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` | §2 상한 참조 원칙·하네스 비복제 원칙 |
| D-5 | 설계 | 검증 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | H-9 검증 2원화 순서 불변·결과 계약 스키마 |
| D-6 | 설계 | CONTRACT 거버넌스 | `opal/skills/opal-pilot-project-loop/references/contract.md` | 오너십 계층 4단계·drift 재콜백 예외 |
| D-7 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` | §1 자동 루핑 제약 SSOT |
| D-8 | 소스 | 설치 스크립트 | `scripts/install-mac.sh` | agents 배포 경로(~/.opal/agents/) + 자동 포함 방식 |
| D-9 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 근거 제시 원칙 및 포맷 |

---

## 1. oppl 태스크 내부 파이프라인·디스패치 구조 분석 (R-1)

### 1.1 파이프라인 현황

`opal/skills/opal-pilot-project-loop/SKILL.md` §태스크 내부 파이프라인 (줄 284~304):

| 단계 | 역할 | 현재 담당자 | PM 개입 |
|------|------|-----------|---------|
| T1 | 명세·설계 (PLAN.md) | 생성자 (도메인별) | 디스패치 1회 |
| T2 | 테스트시나리오 (RED-first) | 생성자 (연속) | 동일 디스패치 |
| G | 명세 리뷰 게이트 (Evaluator) | opal-evaluator-agent | 디스패치 1회 |
| T3 | 구현 (verdict pass 후) | 생성자 (①과 동일) | 재개 지시 1회 |
| T4a | 테스트 (구현 후) | opal-test-agent | 디스패치 1회 |
| T4b | 규칙검사 (conv/sec-checker) | PM 인라인 또는 디스패치 | 0~1회 |
| T5 | 마무리 (DONE.md) | 생성자 | 지시 포함 T3 |

**현재 디스패치 (하이브리드 C)** — `opal/skills/opal-pilot-project-loop/SKILL.md` §디스패치 줄 343~365:
- ① T1+T2: 생성자 1회 / ② G: Evaluator 1회 / ③ T3: 생성자 재개 / T4a/T4b: 추가 1~2회

**PM 총 개입**: 노미널 4~5회 → 실행자 위임 후 **1회로 압축**

### 1.2 개편 지점 전수 (줄번호 포함) — 11개 지점

| # | 절 | 줄 | 현재 서술 | 변경 필요 |
|----|-----|-----|---------|----------|
| 1 | §T1 명세·설계 | 288~290 | "생성자를 resolve하여 디스패치한다" | "실행자가 생성자를 resolve하여 내부 디스패치" |
| 2 | §T1 명세·설계 | 306 | "[생성자 디스패치]" | "[생성자 내부 디스패치]" |
| 3 | §T2 테스트시나리오 | 308~314 | "동일 생성자 디스패치 내에서(또는 연속 호출로)" | "실행자 내부 생성자 디스패치에서" |
| 4 | §G 명세 리뷰 게이트 | 317~327 | "[워커 디스패치] opal-evaluator-agent를 디스패치" | "실행자가 opal-evaluator-agent를 내부 디스패치" |
| 5 | §T3 구현 | 329 | "[생성자 디스패치 재개]" | "[생성자 재개 지시]" |
| 6 | §T4a 테스트 | 331~335 | "[워커 디스패치] opal-test-agent를 디스패치" | "실행자가 opal-test-agent를 내부 디스패치" |
| 7 | §T4b 규칙검사 | 337 | "저위험 인라인 경량화 / 고위험 디스패치" | "실행자가 규모 판정 후 인라인 또는 내부 디스패치" |
| 8 | §디스패치 (표) | 343~351 | 표: "# 시점 대상 역할" (①②③) | 표 갱신 — "실행자 내부" 명시 |
| 9 | §디스패치 (하이브리드 C 설명) | 345 | "~3회 디스패치" | "1회 디스패치 (내부 생성자/Evaluator/test-agent 별도)" |
| 10 | §디스패치 (생성자 resolve) | 355~364 | "생성자 도메인 resolve 설명" + "T1~T3 범위로 한정" | "실행자가 도메인 resolve 후 생성자 내부 디스패치" + "T1~T3는 실행자 위임 범위" |
| 11 | §검증 2원화 | 368~371 | "순서가 뒤바뀌면 G 게이트가 무력화" | 내용 동일 유지, 주체 PM→실행자로 변경 |

---

## 2. 액션 에이전트 구조 비교 (R-2)

### 2.1 입력 명세 비교

- **oppd** (`opal/agents/opal-task-action-agent/AGENT.md` 줄 19~30): action_id, action_goal, action_scope, verify_commands, task_folder, project_root, project_context (7개)
- **opsdd** (`opal/agents/opal-sdd-action-agent/AGENT.md` 줄 18~29): act_id, act_goal, act_scope, ac_mapping, ts_mapping, verify_commands, task_folder, sdd_context (8개)
- **oppl 설계(제안)**: task_id, task_goal, task_scope, task_area, task_folder, verify_commands, **contract_path(oppl 특화)**, project_root, project_context

### 2.2 내부 디스패치 비교

| 구조 | oppd | opsdd | oppl |
|------|------|-------|------|
| PLAN | ✅ opal-task-agent | ✅ opal-task-agent | ✅ 생성자(도메인 resolve) |
| QA | ✅ opal-task-qa-agent | ❌ 없음 | ❌ (G 게이트로 대체) |
| EXECUTE | ✅ 자체 VERIFY 루프 | ✅ 자체 VERIFY 루프 | ✅ T3 구현 후 자체 검증 |
| TEST | ✅ opal-test-agent | ✅ TEST.md 기록 | ✅ opal-test-agent (T4a) |

**특징**: 모두 내부 워커 재디스패치 구조, 재시도 상한(L1~L3) 관리 포함.

### 2.3 결과 계약 비교

- **oppd** (줄 183~202): 8필드 {action_id, status, verdict, artifact_path, summary, changed_files, verification_log, failure_context}
- **oppl 설계(제안)**: 6필드 (압축형) {task_id, verdict, scenario_results, changed_files, done_md_path, blockers}

---

## 3. references 3종 갱신 전략 (R-3)

### 3.1 갱신 필요: loop-control.md

**줄 50** — 현재 "디스패치 하이브리드 C(생성자 1회 + Evaluator 1회, 태스크당 ~2~3 디스패치)" → **갱신안**: "태스크당 실행자 1회 디스패치 (실행자 내부: 생성자·Evaluator·test-agent 별도 위임)"

### 3.2 갱신 불필요: verification.md

**줄 88~96** — 순서 논리는 주체 중립적(PM/실행자 모두 동일 적용 가능). 갱신 불필요.

### 3.3 갱신 필요: contract.md

**줄 54~75 (오너십 계층)** — 추가 명시 필요: "실행자는 drift #1·#2만 수행, #3·#4는 blocked 반환 후 PM 에스컬레이션"

---

## 4. install-mac.sh 배포 경로 (R-5)

✅ 자동 포함: `opal/agents/*` → `~/.opal/agents/` + 플랫폼 sub-agent 어댑터(`install_claude_agents`·`emit_platform_agent_adapter`, `scripts/install-mac.sh:462-464, 641`)가 `~/.claude/agents/` 등에 자동 변환 배포.

**신규 에이전트 추가 절차**: ① `opal/agents/opal-loop-action-agent/AGENT.md` 생성 → ② `./scripts/install-mac.sh` 실행 → ③ 자동 배포. **추가 스크립트 작업 없음.**

---

## 5. 워커 중첩 제약 (R-5)

- **깊이**: PM(L0) → 실행자(L1) → 워커(L2) = 2단계 (oppd Phase 3 동형 — `opal/agents/opal-task-action-agent/AGENT.md`: "기존 워커를 Agent 도구로 디스패치")
- **PM 제어점 불변**: L0(태스크 선택), L∞(관찰), L✓(종료 판정)은 PM 직접 수행 (TASK.md 확정 방향 §1)

---

## 6. 리스크 식별 (R-6)

| # | 리스크 | 심각도 | 완화 방법 |
|----|--------|--------|---------|
| 1 | 검증 2원화 순서 역전(H-9) | 극심 | AGENT.md 순서 강행 가드 + 테스트 시나리오로 순서 evidence 검증 |
| 2 | 비가역 행동 무단 진행 | 극심 | blocked 반환 계약 + PM 사람 게이트 유지 |
| 3 | 재시도 상한 SSOT 깨짐 | 중간 | "harness §1 참조" 원칙 유지 (수치 복제 금지) |
| 4 | PM 컨텍스트 손실 (G verdict 직접 관찰 상실) | 중간 | tool-gated 증거(test-scenario.json·QA-SPEC.md·verification_log) 사후 검증 + STATE.md 추적 |

**블로커**: 없음
