# PLAN: 테스트 시나리오 양식·작성 흐름·파이프라인 재설계

> 작성일: 2026-05-15
> 입력: TASK.md
> 출력: PLAN.md
> 모드: opp (Flat)

---

## §0. 핵심 제약 (원문 인용)

> [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."

> [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."

> [MUST] `.opal/AGENT.md` §금지사항: "**하네스 우회 금지** — Guards/Gates를 PM 임의 판단으로 건너뛰지 않는다."

> [MUST] `.opal/AGENT.md` §업무 수행 지침: "**하네스 변경 시**: `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다."

> [MUST] `.opal/AGENT.md` §업무 수행 지침: "**문서 변경이력**: 스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)."

> [MUST] `docs/PROJECT.md` §프로젝트 원칙: "**1. 표준화 > 커스터마이징** — 컴포넌트 구조와 인터페이스를 일관되게 유지한다"

> [MUST] `docs/PROJECT.md` §프로젝트 원칙: "**3. 플랫폼 독립성** — Claude Code, Cursor, Gemini 등 어디서든 동작해야 한다"

> [MUST] `docs/PROJECT.md` §프로젝트 원칙: "**5. 하네스가 품질을 보장한다** — 오케스트레이터 공통 인프라(Guards, Gates, State)로 누가 실행해도 일정한 산출물 품질이 나와야 한다"

> [MUST] `opal/core/references/opal-harness.md` §1 Guards — 구현 금지 원칙: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다."

---

## 1. 현황 조사

### §1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-dev-test-scenario SKILL.md | `opal/skills/op-dev-test-scenario/SKILL.md` | F-001 변경 대상 — 통일 형식 7섹션 재편 |
| D-2 | 설계 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | F-002 변경 대상 — 작성 프로세스 재구성 + mock 금지 룰 |
| D-3 | 설계 | opal-pilot-dev SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md` | F-003·F-005·F-007·F-009 변경 대상 |
| D-4 | 설계 | op-dev-execute SKILL.md | `opal/skills/op-dev-execute/SKILL.md` | F-004 변경 대상 — scenario_source input 추가 |
| D-5 | 설계 | opal-plan-agent AGENT.md | `opal/agents/opal-plan-agent/AGENT.md` | F-006 변경 대상 — 리스크 가설 표 의무 |
| D-6 | 설계 | opal-test-agent AGENT.md | `opal/agents/opal-test-agent/AGENT.md` | F-009 변경 대상 — L3 즉시 PM 반환 |
| D-7 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` | F-008 변경 대상 — §3 모드 경계 + §8 차이 표 |
| D-8 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards 참조 (변경 없음) |
| D-9 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 규칙 |
| D-10 | 설계 | op-dev-plan SKILL.md | `opal/skills/op-dev-plan/SKILL.md` | F-006 SSOT 위치 결정용 — PLAN.md 양식 소재 확인 |
| D-11 | 설계 | op-task-plan SKILL.md | `opal/skills/op-task-plan/SKILL.md` | 현재 스킬 (본 PLAN 수행 스킬) |
| D-12 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | 프로젝트 원칙 |
| D-13 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력 형식·인용 규칙 |
| D-14 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | PM 금지사항·배포 경계·변경이력 의무 |

### §1.2 관련 파일 (변경 대상)

| 파일 | 역할 | 변경 필요 | 근거 (줄번호) |
|------|------|----------|-------------|
| `opal/skills/op-dev-test-scenario/SKILL.md` | TEST-SCENARIO.md 작성 스킬 | 예 (F-001) | `D-1:61-116` — 통일 형식 섹션 전면 재편 |
| `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 작성 프로세스 가이드 | 예 (F-002) | `D-2:19-104` — 작성 프로세스 전면 재작성 |
| `opal/skills/opal-pilot-dev/SKILL.md` | Full Task 오케스트레이터 | 예 (F-003·F-005·F-007·F-009) | `D-3:58-94, 95-144, 147-200, 268-276` |
| `opal/skills/op-dev-execute/SKILL.md` | 코드 실행 단계 스킬 | 예 (F-004) | `D-4:1-8, 36-50` — 입력 파라미터·완료 기준 |
| `opal/agents/opal-plan-agent/AGENT.md` | PLAN 전문 워커 에이전트 | 예 (F-006) | `D-5:14-28, 83-90` |
| `opal/agents/opal-test-agent/AGENT.md` | 테스트 전문 워커 에이전트 | 예 (F-009) | `D-6:136-142` — 행동 규칙 섹션 |
| `opal/core/references/opal-harness-semi-agentic.md` | semi-agentic 모드 하네스 | 예 (F-008) | `D-7:22-33, 91-101` |

### §1.3 현재 상태 (분석 결과)

#### D-1: op-dev-test-scenario/SKILL.md

- **현행 통일 형식**: 단일 "시나리오 목록"(S-N 표 구조) + 코드 품질 + 보안 + 회귀 테스트 + 판정 + 설계 피드백 + AC 매핑 표 (총 7개 섹션이지만 비구조적)
- `D-1:14`: "op-dev-plan 워커가 PLAN 통합 작성 시 함께 수행 (115에서 PLAN에 통합)" — self-confirming 구조의 명시적 기록
- `D-1:61-116`: "TEST-SCENARIO.md 통일 형식" 코드 블록 위치. **F-001 변경 위치: 이 전체 블록 교체**
- `D-1:126-136`: "시나리오 작성 체크리스트" — F-001 변경 시 함께 갱신 필요

#### D-2: test-scenario-guide.md

- **현행 프로세스**: 5단계 (컨텍스트 확인→도구 결정→시나리오 도출→문서 전용 확인→설계 검증)
- `D-2:86-93`: "시나리오 수 가이드" 표 — TASK.md F-002 AC에서 "폐기됨" 명시 → **전체 삭제**
- `D-2:40-50`: "시나리오 유형→도구 매핑 테이블" — 유지하되 통합 테스트 카테고리 추가 필요
- **F-002 변경 위치**: 전체 파일 재작성 (신규 5단계 프로세스 + 계층 결정 규칙 표 신설 + mock 금지 룰)

#### D-3: opal-pilot-dev/SKILL.md

- `D-3:58-94`: STEP 3 PLAN 섹션 — `D-3:75`: "op-dev-plan 워커가 PLAN.md와 TEST-SCENARIO.md를 통합 작성한다" 제거 대상 (F-003)
- `D-3:63-75`: PLAN 디스패치 프롬프트 `**산출물 저장 경로**`에 `TEST-SCENARIO.md` 포함 → 제거하고 "PLAN.md만" 으로 변경 (F-003)
- `D-3:77-93`: PLAN PM Gate 검증 체크리스트에 TEST-SCENARIO.md 항목 → 제거 (F-003)
- `D-3:95-144`: STEP 4 EXECUTE — 4-2 디스패치 프롬프트에 `scenario_source` 필드 추가 (F-005)
- `D-3:224-265`: STATE.md 도메인 치환값 — 현재 25행 → TEST-SCENARIO 4행 추가 후 **총 29행** (F-003)
- `D-3:268-276`: PM Gate 점검 목록 — TEST-SCENARIO Phase 행 추가 (F-007)
- `D-3:282-317`: Agentic/Semi-Agentic 모드 섹션 — 모드 경계 설명 갱신 (F-003)
  - `D-3:287`: "PLAN 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율" → "TEST-SCENARIO 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율"
- `D-3:307-311`: 자율 게이트 흐름 다이어그램 — TEST-SCENARIO 단계 추가 (F-003)
- STEP 5 TEST 섹션(`D-3:147-200`): L3 협업 게이트 추가 (F-009)
  - STEP 5에 "L3 시나리오 협업 게이트" 서브섹션 신설
  - 표준 요청 양식 코드 블록 삽입

#### D-4: op-dev-execute/SKILL.md

- `D-4:1-8`: YAML frontmatter `version: 2.0`
- `D-4:15-21`: 실행 컨텍스트 "입력" 항목 — `checklist_source`만 명시 → `scenario_source` 추가 (F-004)
- **완료 기준 섹션 신설**: "자가 점검 절차" 섹션 — 코드 작성 → 시나리오 실행 명령 추출 → Bash 실행 → PASS 확인. L3 TEST 단계 위임 명시 (F-004)
- `D-4:156-166`: EXECUTE 품질 체크리스트 — L1/L2 시나리오 PASS 항목 추가 (F-004)

#### D-5: opal-plan-agent/AGENT.md

- `D-5:14-28`: 실행 프로세스 (8단계) — Step 6(산출물 생성)에서 "리스크 가설 표 작성" 의무 추가 필요
- 현재 PLAN.md 양식 SSOT는 `op-dev-plan/SKILL.md`에 있음 (`D-10:169-351`)
- `D-5:83-90`: 행동 규칙 — 추가 지시가 없음
- **F-006 SSOT 결정**: 아래 §1.4 참조

#### D-6: opal-test-agent/AGENT.md

- `D-6:136-142`: 행동 규칙 섹션 (현재 5개 항목) — L3 시나리오 처리 절차 추가 (F-009)
- 현재 행동 규칙에 TEST-SCENARIO.md 내 [SUPERVISOR] 마커 처리 없음

#### D-7: opal-harness-semi-agentic.md

- `D-7:22-33`: §3 모드 경계 표 — `opd` 행의 "PLAN-equivalent 종료 시점"을 "TEST-SCENARIO 사용자 확인 행"으로 갱신 (F-008)
- `D-7:91-101`: §8 차이 표 — "TEST-SCENARIO 완료" 행 추가 (F-008)
  - 단, TASK.md에서 `§8 차이 표`에는 "TEST-SCENARIO 완료" 행을 "interactive=사용자 승인 / semi-agentic=사용자 승인 / agentic=PM 자율"로 추가

### §1.4 F-006 PLAN.md 양식 SSOT 결정 (ANALYSIS)

**질문**: 리스크 가설 표 섹션을 (a) `opal-plan-agent/AGENT.md` (b) `op-dev-plan/SKILL.md` (c) 양쪽 모두에 추가할 것인가?

**분석**:
- 현행 PLAN.md 통일 형식(§1~§9 골격)의 SSOT는 `op-dev-plan/SKILL.md:169-351` (→ D-10)
- `opal-plan-agent/AGENT.md`는 **워커 실행 프로세스**를 정의하며, 구체적 PLAN.md 양식을 포함하지 않음 (→ D-5)
- SSOT 단일 위치 원칙(`docs/PROJECT.md` §프로젝트 원칙 1: "표준화 > 커스터마이징")에 따라 **발췌·복제 금지**

**결정**: `op-dev-plan/SKILL.md`에 신설. `opal-plan-agent/AGENT.md`에는 "리스크 가설 표 작성 의무" 행동 규칙 1줄만 추가.

- **PLAN.md 양식 변경 위치**: `opal/skills/op-dev-plan/SKILL.md` §9(또는 §1~§9 골격 내 새 섹션 "## 리스크 가설 표" 삽입)
  - 단, `op-dev-plan/SKILL.md`는 TASK.md D-10이 "F-006 변경 위치 확정"용으로만 읽힌다. F-006 **주 변경 파일**은 `opal-plan-agent/AGENT.md` 행동 규칙 + `op-dev-plan/SKILL.md` PLAN.md 양식.

### §1.5 F-009 L3 협업 게이트 위치 결정 (ANALYSIS)

**질문**: L3 시나리오 처리 책임을 `opal-pilot-dev/SKILL.md` STEP 5 vs `opal-test-agent/AGENT.md` 중 어디에 명시하는가?

**결정**: **양쪽 모두** (역할 분담):
- `opal-pilot-dev/SKILL.md` STEP 5: **PM 책임** — L3 게이트 존재, opal-test-agent가 L3 시나리오 만나면 PM에 반환, PM이 표준 양식으로 캡틴 요청
- `opal-test-agent/AGENT.md` 행동 규칙: **워커 책임** — TEST-SCENARIO.md에서 [SUPERVISOR] 마커를 만나면 즉시 PM에 반환(실행 중단). 반환 사유 명시.
- 이렇게 해야 PM 오케스트레이터(SKILL.md)와 워커(AGENT.md) 양쪽이 게이트를 인식하고 협력 가능.

### §1.6 F-003 STATE.md 행 구성 변화 측정

**현재 행 구성** (총 25행, `D-3:236-264`):

```
행 1-3:   TASK 3행 (작업/TASK.md 생성/사용자 확인)
행 4-9:   ANALYSIS 6행 (작업/ANALYSIS.md 생성/State Gate/PM Gate/State Gate/사용자 확인)
행 10-16: PLAN 7행 (작업/PLAN.md 생성/TEST-SCENARIO.md 생성/State Gate/PM Gate/State Gate/사용자 확인)
행 17-18: EXECUTE 2행 (작업/State Gate)
행 19-23: TEST 5행 (작업/State Gate/PM Gate/State Gate/사용자 확인)
행 24-25: CLOSE 2행 (DONE.md 생성/State Gate)
```

**변경 후 행 구성** (총 29행 예상):

F-003 변경으로 PLAN 단계에서 TEST-SCENARIO.md 생성 행 제거 후, 신설 TEST-SCENARIO 단계 4행 추가:

```
행 1-3:   TASK 3행 (유지)
행 4-9:   ANALYSIS 6행 (유지)
행 10-15: PLAN 6행 (작업/PLAN.md 생성/State Gate/PM Gate/State Gate/사용자 확인)
           ← TEST-SCENARIO.md 생성 행 제거 (1행 감소)
행 16-19: TEST-SCENARIO 4행 (작업/TEST-SCENARIO.md 생성/State Gate/사용자 확인)
           ← 신설 (4행 추가)
행 20-21: EXECUTE 2행 (유지)
행 22-26: TEST 5행 (유지)
행 27-28: CLOSE 2행 (유지)
합계: 3+6+6+4+2+5+2 = 28행
```

**정확한 행 수**: 28행 (TASK.md §AC에서 "약 29행" 언급이나, 정밀 계산 결과 28행)

**행 순서 도표**:

| # | 단계 | 항목 | 비고 |
|---|------|------|------|
| 1 | TASK | 작업 | 유지 |
| 2 | TASK | TASK.md 생성 | 유지 |
| 3 | TASK | 사용자 확인 | 유지 |
| 4 | ANALYSIS | 작업 | 유지 |
| 5 | ANALYSIS | ANALYSIS.md 생성 | 유지 |
| 6 | ANALYSIS | State Gate | 유지 |
| 7 | ANALYSIS | PM Gate | 유지 |
| 8 | ANALYSIS | State Gate | 유지 |
| 9 | ANALYSIS | 사용자 확인 | 유지 |
| 10 | PLAN | 작업 | 유지 |
| 11 | PLAN | PLAN.md 생성 | 유지 |
| 12 | PLAN | State Gate | 변경 (현 12행 TEST-SCENARIO.md 생성 → 제거) |
| 13 | PLAN | PM Gate | 변경 (행 번호 이동) |
| 14 | PLAN | State Gate | 변경 (행 번호 이동) |
| 15 | PLAN | 사용자 확인 | 변경 (행 번호 이동) |
| 16 | TEST-SCENARIO | 작업 | **신설** |
| 17 | TEST-SCENARIO | TEST-SCENARIO.md 생성 | **신설** |
| 18 | TEST-SCENARIO | State Gate | **신설** |
| 19 | TEST-SCENARIO | 사용자 확인 | **신설** |
| 20 | EXECUTE | 작업 | 유지 (행 번호 이동) |
| 21 | EXECUTE | State Gate | 유지 (행 번호 이동) |
| 22 | TEST | 작업 | 유지 (행 번호 이동) |
| 23 | TEST | State Gate | 유지 (행 번호 이동) |
| 24 | TEST | PM Gate | 유지 (행 번호 이동) |
| 25 | TEST | State Gate | 유지 (행 번호 이동) |
| 26 | TEST | 사용자 확인 | 유지 (행 번호 이동) |
| 27 | CLOSE | DONE.md 생성 | 유지 (행 번호 이동) |
| 28 | CLOSE | State Gate | 유지 (행 번호 이동) |

> 근거: `D-3:236-264` 현재 25행 구조 기반 + F-003 변경 사항 적용

### §1.7 F-008 모드 경계 적용 범위

TASK.md §제약 조건: "적용 범위 제한: `opal-pilot-dev`(opd) 전용. opds/opp/opdw/opsdd 등 다른 pilot은 본 태스크 범위 외"

F-008 변경:
- `D-7:27` `opd` 행만 갱신 (PLAN-equivalent 종료 시점 → TEST-SCENARIO 사용자 확인 행)
- `opds` 행은 **본 태스크 범위 외** — 향후 별도 태스크에서 갱신 필요 (현재 opds도 "PLAN 사용자 확인 행" 사용 중, mams에서 opds 활용 중이므로 retroactive 갱신 없음 원칙 준수)

---

## 2. 구현 계획

### §2.1 파일 변경 계획

#### 신규 생성

없음 (모든 변경은 기존 파일 수정)

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `opal/skills/op-dev-test-scenario/SKILL.md` | 통일 형식 7섹션 재편 + 체크리스트 갱신 | F-001 (→ D-1) |
| 2 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 전체 재작성 — 5단계 프로세스 + 계층 결정 규칙 표 + mock 금지 | F-002 (→ D-2) |
| 3 | `opal/skills/opal-pilot-dev/SKILL.md` | 5단계 재편 + STATE.md 행 + PM Gate + STEP 5 L3 게이트 + 모드 경계 이동 | F-003·F-005·F-007·F-009 (→ D-3) |
| 4 | `opal/skills/op-dev-execute/SKILL.md` | scenario_source input + 자가 점검 절차 + 완료 기준 갱신 | F-004 (→ D-4) |
| 5 | `opal/skills/op-dev-plan/SKILL.md` | PLAN.md 양식에 리스크 가설 표 섹션 신설 | F-006 SSOT (→ D-10) |
| 6 | `opal/agents/opal-plan-agent/AGENT.md` | 행동 규칙에 리스크 가설 표 작성 의무 1줄 추가 | F-006 (→ D-5) |
| 7 | `opal/agents/opal-test-agent/AGENT.md` | 행동 규칙에 L3 [SUPERVISOR] 마커 즉시 PM 반환 추가 | F-009 (→ D-6) |
| 8 | `opal/core/references/opal-harness-semi-agentic.md` | §3 opd 행 모드 경계 갱신 + §8 TEST-SCENARIO 행 추가 | F-008 (→ D-7) |
| (모든 파일) | 변경이력 표 행 추가 | EXECUTE 시작 시점 단일 KST 일시 사용 | F-010 (→ D-14) |

#### 삭제

없음

### §2.2 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 양식 SSOT 신설 — F-001 통일 형식 | `op-dev-test-scenario/SKILL.md` | 중 |
| 2 | 가이드 재작성 — F-002 | `test-scenario-guide.md` | 중 |
| 3 | PLAN.md 양식 리스크 가설 표 신설 — F-006 | `op-dev-plan/SKILL.md` | 중 |
| 4 | 파이프라인 재편 — F-003 | `opal-pilot-dev/SKILL.md` | 상 |
| 5 | EXECUTE 디스패치 갱신 — F-005 | `opal-pilot-dev/SKILL.md` | 하 |
| 6 | PM Gate 검증 룰 보강 — F-007 | `opal-pilot-dev/SKILL.md` | 하 |
| 7 | L3 게이트 신설 — F-009 (SKILL.md 파트) | `opal-pilot-dev/SKILL.md` | 중 |
| 8 | execute 스킬 input 추가 — F-004 | `op-dev-execute/SKILL.md` | 하 |
| 9 | plan-agent 행동 규칙 — F-006 | `opal-plan-agent/AGENT.md` | 하 |
| 10 | test-agent 행동 규칙 — F-009 | `opal-test-agent/AGENT.md` | 하 |
| 11 | 하네스 모드 경계 갱신 — F-008 | `opal-harness-semi-agentic.md` | 하 |
| 12 | 변경이력 일괄 추가 — F-010 | 모든 변경 파일 | 하 |

### §2.3 핵심 설계

#### F-001: TEST-SCENARIO.md 통일 형식 7섹션 재편

`opal/skills/op-dev-test-scenario/SKILL.md` "TEST-SCENARIO.md 통일 형식" 코드 블록 (`D-1:62-116`) 전체 교체. 새 양식:

```markdown
# TEST SCENARIO: {태스크 제목}

> 작성일: YYYY-MM-DD | 상태: {작성 완료 / 실행 완료}
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | {변경 단위} | {계약} | {영향} | L1/L2/L3 | S-N |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| {테이블} | {ID} | {상태} | {fixture/seed/수동} |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-N | {사전 데이터} | {실행 조작} | {검증 데이터} |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: {시나리오 제목}

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-N |
| 대상 | {테스트 대상 기능/변경점} |
| 계층 | L1 |
| 조건 | {입력, 사전 상태, 환경} |
| 기대 결과 | {성공 기준} |
| 도구 | {vitest / pytest 등} |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움: Pass / Fail / Skip}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

### L2. 프로세스 통합 (자동, 실 DB read→CUD→re-read)

{L2 시나리오 — S-N 형식 동일}

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-N: {시나리오 제목} [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-N |
| 대상 | {FE 화면 / 사용자 플로우} |
| 계층 | L3 |
| 조건 | {사전 조건} |
| 기대 결과 | {기대 결과} |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 비고 |
|-------|---------|---------|---------|------|
| {F-N AC (a)} | H-N | L1/L2/L3 | S-N | {설명} |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | _{채움}_ | _{채움}_ | _{채움}_ |
| 2 | 타입 체크 | _{채움}_ | _{채움}_ | _{채움}_ |
| 3 | 포맷터 | _{채움}_ | _{채움}_ | _{채움}_ |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | _{채움}_ | _{채움}_ |
| 2 | .gitignore 확인 | _{채움}_ | _{채움}_ |

## 7. 판정

**_{op-dev-test-agent가 채움: All Pass / Partial Fail / Critical Fail}_ -- _{판정 근거}_**

### PM Gate 체크 (7대 강제 룰)

- [ ] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인)
- [ ] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [ ] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [ ] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [ ] L1/L2/L3 계층 명시 (모든 시나리오)
- [ ] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부
- [ ] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
```

시나리오 작성 체크리스트도 새 7섹션 양식에 맞게 갱신. (→ D-1:126-136)

#### F-002: test-scenario-guide.md 전체 재작성

신규 5단계 프로세스:
1. PLAN.md 가설 표 Read — PLAN 워커가 PLAN.md에 삽입한 리스크 가설 표를 읽어 H-N 목록 파악
2. 데이터 설계 — §2 사전 조건 데이터(테이블/식별자/상태/출처) 표 작성 + §2.2 시나리오별 데이터 흐름(Given/When/Then)
3. 계층 결정 — 계층 결정 규칙 표(변경 영역 7종 × 의무 계층) 적용
4. 시나리오 본문 작성 — Given/When/Then 3필드 + [SUPERVISOR] 마커 부여
5. AC ↔ 가설 ↔ 계층 ↔ 시나리오 4열 매핑 표 완성

**계층 결정 규칙 표 (신설):**

| 변경 영역 | L1 의무 | L2 의무 | L3 의무 |
|----------|---------|---------|---------|
| DB 스키마/마이그레이션 | 단위 CRUD | FK/NOT NULL 제약 re-read | 해당 없음 |
| API 엔드포인트 | 요청/응답 계약 | 인증·권한 흐름 | 해당 없음 |
| 비즈니스 로직 | 함수 단위 정상/경계 | 서비스 계층 흐름 | 해당 없음 |
| 병렬/동시성 | 해당 없음 | 동시 요청 시나리오 | 수동 부하 테스트 |
| FE 화면/컴포넌트 | 렌더링 단위 | API 연동 흐름 | 사용자 시각 확인 [SUPERVISOR] |
| 인증/인가 | 토큰 발급 단위 | 세션 흐름 | 수동 로그인 [SUPERVISOR] |
| 외부 API 연동 | mock 없이 stub 사용 | 실 API 호출 흐름 | 해당 없음 |

**mock 금지 룰 (신설):**
- 시나리오 본문에 `mock`/`patch`/`MagicMock`/`unittest.mock` 등 사용 금지
- 위반 시 PM Gate FAIL (grep 자동 감지)
- 대안: 실 fixture / factory / seed 데이터 사용

시나리오 수 가이드 표 (`D-2:86-93`) **삭제** — 가설 N건 → 시나리오 N건 이상 원칙으로 대체.

#### F-003: opal-pilot-dev SKILL.md 5단계 재편

**STEP 3 PLAN 변경 (`D-3:58-94`)**:
- 디스패치 프롬프트 `산출물 저장 경로`에서 `{TEST-SCENARIO.md 경로}` 제거
- 75행 "op-dev-plan 워커가 PLAN.md와 TEST-SCENARIO.md를 통합 작성한다" 삭제
- PM Gate 검증 항목에서 TEST-SCENARIO.md 관련 2개 항목 제거
- 사용자 보고문에서 "PLAN + TEST-SCENARIO 함께 보고" → "PLAN 보고" 로 변경

**STEP 3.5 TEST-SCENARIO 신설** (STEP 3과 STEP 4 사이):
```
## STEP 3.5: TEST-SCENARIO

작성자: **알투(PM) + 캡틴 페어** — 오케스트레이터가 직접 작성 (워커 디스패치 없음).
이 단계는 self-confirming 방지를 위해 PLAN 워커(opal-plan-agent)와 다른 작성자가 수행한다.

1. PLAN.md §리스크 가설 표 Read
2. op-dev-test-scenario/SKILL.md의 "TEST-SCENARIO.md 통일 형식"을 따라 TEST-SCENARIO.md 작성
3. test-scenario-guide.md의 5단계 프로세스 적용
4. State Gate
5. 사용자에게 TEST-SCENARIO 보고 — 승인 = EXECUTE 시작 허가
```

**STATE.md 도메인 치환값 변경 (`D-3:224-265`)**: §1.6 도표의 28행 구조로 전면 교체

**자율 게이트 흐름 다이어그램 갱신 (`D-3:307-311`)**:
```
TASK → ANALYSIS Gate → PLAN Gate → TEST-SCENARIO Gate → EXECUTE Gate → TEST Gate → CLOSE
사용자   사용자 승인     사용자 승인    사용자 승인             PM 자율        PM 자율     사용자 승인 필수
                                     (모드 경계)
```

**"기본 모드 (semi-agentic)" 모드 경계 설명 갱신 (`D-3:284-288`)**:
> 현행: "PLAN 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율"
> 개정: "TEST-SCENARIO 사용자 확인 행 통과 후 → EXECUTE 작업 행부터 PM 자율"

#### F-004: op-dev-execute/SKILL.md 갱신

실행 컨텍스트 **입력** 항목에 `scenario_source` 추가:
- `scenario_source`: `TEST-SCENARIO.md` (오케스트레이터가 경로 지정)

**"자가 점검 절차" 섹션 신설** (Step 3 이후):
```markdown
### Step 3-S. 자가 점검 절차 (TDD red-green)

각 Step 구현 완료 후:
1. TEST-SCENARIO.md `scenario_source`에서 담당 Step 매핑 L1/L2 시나리오 식별
2. 각 시나리오의 "실행 명령" 추출 (없으면 도구·기대결과 기반으로 명령 구성)
3. Bash 실행 → 결과 확인
4. PASS: 다음 Step 진행. FAIL: 즉시 수정 후 재실행 (최대 3회)
5. L3 시나리오: TEST 단계로 위임 (이 단계에서 실행하지 않음)

**완료 기준**: checklist 100% + 담당 Step 매핑 L1/L2 시나리오 PASS
```

EXECUTE 품질 체크리스트에 항목 추가:
- `[ ] 담당 Step 매핑 L1/L2 시나리오 PASS 확인`
- `[ ] L3 시나리오는 TEST 단계로 위임함`

#### F-005: opal-pilot-dev SKILL.md EXECUTE 디스패치 프롬프트 갱신 (`D-3:109-123`)

4-2 디스패치 프롬프트 예시에 3 필드 추가:
```
**scenario_source**: {TEST-SCENARIO.md 경로}
**완료 기준**: checklist 100% + 담당 Step 매핑 L1/L2 시나리오 PASS (L3는 TEST 단계 위임)
**자가 점검 절차**: 코드 작성 → 시나리오 "실행 명령" 추출 → Bash 실행 → PASS 확인 → 완료 보고
```

#### F-006: PLAN.md 리스크 가설 표 신설

**`opal/skills/op-dev-plan/SKILL.md` 변경** (`D-10:169-351`):
PLAN.md 출력 형식 §1 섹션(태스크 개요 + 기능 리스트업) 바로 뒤 또는 §9(리스크) 앞에 신규 섹션 삽입:

```markdown
## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | {F-NNN 또는 파일} | {함수 반환 계약/DB 제약/API 계약} | {P0/P1/P2} | L1/L2/L3 | S-N 후보 |
```

**가설 도출 예시 3종**:
- H-예1: Repository.bulk_upsert 반환 계약 변경 → 호출자가 반환값 처리 오류 → 운영 영향 P1 → L1(단위) + L2(실 DB) 의무
- H-예2: 병렬 동시성 → 동시 요청 시 레이스 컨디션/커넥션 풀 고갈 → 운영 영향 P0 → L2(동시성 통합) 의무
- H-예3: NOT NULL/FK 제약 → mock 통과 후 실 DB에서 IntegrityError → 운영 영향 P1 → L2(실 DB 통합) 의무

**`opal/agents/opal-plan-agent/AGENT.md` 행동 규칙 추가** (`D-5:83-90`):
행동 규칙 섹션에 1줄 추가:
> - PLAN.md 산출물에 "리스크 가설 표" 섹션을 작성한다 — 변경 단위별 H-N 가설(깨질 수 있는 계약/운영 영향/검증 계층 권고/시나리오 후보)을 도출하여 TEST-SCENARIO.md §1의 입력으로 제공한다.

#### F-007: PM Gate 검증 룰 보강 (`D-3:268-276`)

PM Gate 점검 목록 표에 TEST-SCENARIO Phase 행 추가:

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| TEST-SCENARIO | TEST-SCENARIO.md | 6항목: ① mock 부재(grep) ② 사전 조건 데이터 채워짐 ③ Given/When/Then 3필드 ④ 가설↔시나리오 매핑 완전 ⑤ L1/L2/L3 계층 명시 ⑥ L3 [SUPERVISOR] 마커 존재 |

#### F-008: opal-harness-semi-agentic.md 모드 경계 갱신 (`D-7:22-33, 91-101`)

**§3 모드 경계 표** `opd` 행 갱신:

| pilot | PLAN-equivalent 종료 시점 | EXECUTE-equivalent 시작 시점 |
|-------|--------------------------|----------------------------|
| opd | ~~PLAN 사용자 확인 행~~ **TEST-SCENARIO 사용자 확인 행** | EXECUTE 작업 행 |

**§8 차이 표** TEST-SCENARIO 행 추가:

| 단계 | interactive | semi-agentic | agentic |
|------|-------------|-------------|---------|
| TEST-SCENARIO 완료 | 사용자 승인 | 사용자 승인 (모드 경계) | PM 자율 |

#### F-009: L3 협업 게이트 신설

**`opal/skills/opal-pilot-dev/SKILL.md` STEP 5 추가 (`D-3:147-200`)**:

STEP 5 TEST 시작 부분에 서브섹션 추가:
```markdown
### 5-0. L3 시나리오 협업 게이트

TEST 단계 진입 시 opal-test-agent 디스패치 전에:
1. TEST-SCENARIO.md에서 [SUPERVISOR] 마커 시나리오 식별
2. [SUPERVISOR] 시나리오 존재 시:
   - opal-test-agent를 L3 제외 모드로 디스패치 (L1/L2만 실행)
   - PM이 사용자에게 아래 표준 양식으로 요청
3. 사용자 응답 수신 후 결과 TEST-SCENARIO.md에 기록
4. L3 시나리오 없으면 정상 디스패치 진행

**PM 표준 요청 양식**:
\```
캡틴, [시나리오 S-N]은 사용자 협업 검증이 필요합니다.
요청 내용: {시나리오 조건 요약}
기대 결과: {기대 결과 요약}
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
\```
```

**`opal/agents/opal-test-agent/AGENT.md` 행동 규칙 추가 (`D-6:136-142`)**:
> - TEST-SCENARIO.md에서 `[SUPERVISOR]` 마커가 있는 시나리오를 만나면 해당 시나리오를 실행하지 않고 즉시 오케스트레이터(PM)에 반환한다. 반환 사유: "L3 [SUPERVISOR] 시나리오 감지 — PM에 위임". L1/L2 시나리오만 실행하고 L3 결과 칸은 비워둔다.

#### F-010: 변경이력 행 추가

모든 변경 파일의 `## 변경이력` 표에 행 추가. **일시는 EXECUTE 단계 시작 시점의 단일 KST 일시**를 사용 (`node ~/.opal/tools/date/date.js datetime` 결과). 태스크 번호 `(004)` 명시.

---

## 3. 실행 체크리스트

> 총 12개 Step | Phase 4개 | 실행 모드: 단순 (모든 .md 파일 변경)

### §4.1 Phase 구성 및 의존 관계

| Phase | 포함 Step | 실행 방식 | 비고 |
|-------|----------|---------|------|
| Phase 1 (양식·SSOT 신설) | Step 1, Step 2, Step 3 | 순차 | F-001→F-002→F-006 순서 (SSOT 먼저, 가이드 후) |
| Phase 2 (파이프라인 재편) | Step 4, Step 5, Step 6, Step 7 | 순차 | F-003→F-005→F-007→F-009 (모두 동일 파일 opal-pilot-dev/SKILL.md) |
| Phase 3 (워커 인터페이스) | Step 8, Step 9, Step 10, Step 11 | 병렬 가능 | F-004·F-006·F-009·F-008 (서로 다른 파일, 독립) |
| Phase 4 (변경이력 일괄) | Step 12 | 순차 (마지막) | F-010 — 모든 변경 완료 후 일시 확정 |

Phase 1과 Phase 2는 순차 의존 없음 → 이론상 병렬 가능하나, 동일 Step 목적 명확성을 위해 순차 권고.
Phase 3는 모두 다른 파일이므로 병렬 가능. 단, 단일 워커(opal-task-agent) 실행 전제.

### §4.2 실행 체크리스트 (agent: opal-task-agent)

#### Step 1: F-001 — op-dev-test-scenario/SKILL.md 통일 형식 7섹션 재편
- [x] 완료
- **파일**: `opal/skills/op-dev-test-scenario/SKILL.md`
- **작업 내용**: §2.3 F-001 설계 내용에 따라 "TEST-SCENARIO.md 통일 형식" 코드 블록(현행 `D-1:62-116`) 전체를 7섹션 새 양식으로 교체. 시나리오 작성 체크리스트(`D-1:126-136`)도 갱신.
- **완료 기준**: grep으로 §1 리스크 가설 표 컬럼 6종(ID/변경 단위/계약/영향/계층/시나리오) 존재, §2.1 사전 조건 데이터 표 컬럼 4종(테이블/식별자/상태/출처) 존재, §2.2 데이터 흐름 표 컬럼 4종(시나리오/Given/When/Then) 존재, §3 L1/L2/L3 서브헤딩 존재
- **테스트**: grep "L1\. 기능 단위" / grep "사전 조건 데이터" / grep "리스크 가설 표"
- **의존**: 없음

#### Step 2: F-002 — test-scenario-guide.md 재작성
- [x] 완료
- **파일**: `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- **작업 내용**: §2.3 F-002 설계에 따라 전체 재작성. 5단계 프로세스 + 계층 결정 규칙 표 7종 + mock 금지 룰 신설. 시나리오 수 가이드 표 삭제.
- **완료 기준**: grep "시나리오 수 가이드" 결과 없음(0건), grep "mock 금지" 결과 존재, grep "계층 결정 규칙" 결과 존재, 5단계 프로세스 헤딩 존재
- **테스트**: grep "시나리오 수 가이드" 파일 — 0건 확인
- **의존**: Step 1 완료 권장 (양식과 가이드 일관성 확인 목적)

#### Step 3: F-006 — op-dev-plan/SKILL.md 리스크 가설 표 신설
- [x] 완료
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**: PLAN.md 출력 형식 골격(`D-10:169-351`)에 "## 리스크 가설 표" 섹션 삽입. 컬럼 6종(ID/변경 단위/계약/영향/계층 권고/시나리오 후보). 가설 도출 예시 3종(Repository 반환/병렬 동시성/NOT NULL FK) 포함.
- **완료 기준**: grep "리스크 가설 표" 결과 존재, grep "H-예1" 존재, 컬럼 6종 명시
- **테스트**: grep "리스크 가설 표" 파일
- **의존**: 없음

#### Step 4: F-003 — opal-pilot-dev/SKILL.md 5단계 재편 + STATE.md 행 구성 갱신
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**:
  1. STEP 3 PLAN 디스패치 프롬프트에서 `{TEST-SCENARIO.md 경로}` 제거, "통합 작성" 문구 제거
  2. STEP 3.5 TEST-SCENARIO 단계 신설 (§2.3 F-003 설계 내용)
  3. STATE.md 도메인 치환값 28행 구조로 전면 교체 (§1.6 도표)
  4. "기본 모드 (semi-agentic)" 모드 경계 설명 갱신
  5. 자율 게이트 흐름 다이어그램 갱신 (TEST-SCENARIO 단계 추가)
- **완료 기준**: grep "STEP 3.5" 존재, STATE.md 행 예시에 "TEST-SCENARIO" 단계 존재(4행), grep "TEST-SCENARIO 사용자 확인 행 통과" 존재
- **테스트**: grep "STEP 3.5" 파일 / grep "TEST-SCENARIO | 작업" 파일
- **의존**: Step 3 완료 권장 (PLAN.md 양식 확인 후 통합 작성 제거 일관성)

#### Step 5: F-005 — opal-pilot-dev/SKILL.md EXECUTE 디스패치 프롬프트 갱신
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md` (Step 4와 동일 파일, 순차 실행)
- **작업 내용**: §4-2 디스패치 프롬프트에 3 필드 추가 (scenario_source, 완료 기준, 자가 점검 절차)
- **완료 기준**: grep "scenario_source" 결과 존재
- **테스트**: grep "scenario_source" 파일
- **의존**: Step 4 완료

#### Step 6: F-007 — opal-pilot-dev/SKILL.md PM Gate 검증 룰 보강
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md` (Step 4, 5와 동일 파일, 순차 실행)
- **작업 내용**: "PM Gate 점검 목록" 표에 TEST-SCENARIO Phase 행 추가 (6 검증 항목)
- **완료 기준**: grep "TEST-SCENARIO" PM Gate 점검 목록 행 존재
- **테스트**: grep "mock 부재" 또는 grep "grep으로" 파일
- **의존**: Step 5 완료

#### Step 7: F-009 (SKILL.md 파트) — opal-pilot-dev/SKILL.md STEP 5 L3 게이트 신설
- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md` (Step 4~6과 동일 파일, 순차)
- **작업 내용**: STEP 5 TEST 앞에 "5-0. L3 시나리오 협업 게이트" 서브섹션 신설 + PM 표준 요청 양식 코드 블록
- **완료 기준**: grep "5-0. L3 시나리오 협업 게이트" 존재, grep "캡틴, \[시나리오" 존재
- **테스트**: grep "L3 시나리오 협업 게이트" 파일
- **의존**: Step 6 완료

#### Step 8: F-004 — op-dev-execute/SKILL.md 입력 파라미터 + 자가 점검 절차 추가
- [x] 완료
- **파일**: `opal/skills/op-dev-execute/SKILL.md`
- **작업 내용**: 실행 컨텍스트 입력에 scenario_source 추가. Step 3-S 자가 점검 절차 신설. 품질 체크리스트에 L1/L2 PASS 항목 추가. L3 위임 룰 명시.
- **완료 기준**: grep "scenario_source" 존재, grep "자가 점검 절차" 존재, grep "L3 시나리오" 존재
- **테스트**: grep "scenario_source" 파일
- **의존**: 없음 (Phase 3 — Phase 1·2와 독립)

#### Step 9: F-006 (AGENT 파트) — opal-plan-agent/AGENT.md 행동 규칙 추가
- [x] 완료
- **파일**: `opal/agents/opal-plan-agent/AGENT.md`
- **작업 내용**: 행동 규칙 섹션에 "리스크 가설 표 작성 의무" 1줄 추가
- **완료 기준**: grep "리스크 가설 표" 행동 규칙 섹션 존재
- **테스트**: grep "리스크 가설 표" 파일
- **의존**: Step 3 완료 권장 (SKILL.md 양식 확인 후 행동 규칙 일치성)

#### Step 10: F-009 (AGENT 파트) — opal-test-agent/AGENT.md 행동 규칙 추가
- [x] 완료
- **파일**: `opal/agents/opal-test-agent/AGENT.md`
- **작업 내용**: 행동 규칙 섹션에 L3 [SUPERVISOR] 마커 발견 시 즉시 PM 반환 절차 추가
- **완료 기준**: grep "\[SUPERVISOR\]" 행동 규칙 섹션 존재
- **테스트**: grep "SUPERVISOR" 파일
- **의존**: 없음 (Phase 3 — Step 7과 독립, 다른 파일)

#### Step 11: F-008 — opal-harness-semi-agentic.md 모드 경계 갱신
- [x] 완료
- **파일**: `opal/core/references/opal-harness-semi-agentic.md`
- **작업 내용**: §3 opd 행 모드 경계 갱신 (PLAN → TEST-SCENARIO). §8 차이 표에 TEST-SCENARIO 완료 행 추가 (interactive=사용자 승인 / semi-agentic=사용자 승인 / agentic=PM 자율)
- **완료 기준**: §3 opd 행에 "TEST-SCENARIO" 텍스트 존재, §8 표에 TEST-SCENARIO 행 존재
- **테스트**: grep "TEST-SCENARIO 사용자 확인" 파일
- **의존**: 없음 (Phase 3 — 다른 파일)

#### Step 12: F-010 — 변경이력 일괄 추가
- [x] 완료
- **파일**: 위 Step 1~11에서 수정된 모든 파일 (8개 파일)
- **작업 내용**: 각 파일 `## 변경이력` 표에 행 추가. 일시 = `node ~/.opal/tools/date/date.js datetime` 결과 (EXECUTE 시작 시점 1회 실행). 버전은 각 파일 현행 버전 +0.1. 변경 내용 요약에 `(004)` 태스크 번호 포함.
- **완료 기준**: 8개 파일 모두 변경이력 표에 `(004)` 태스크 번호 포함 행 존재
- **테스트**: grep "(004)" 각 파일
- **의존**: Step 1~11 모두 완료

---

## 4. QA 체크리스트

### §5.1 기능 테스트 (자체 grep 기반 양식 검증)

> 본 태스크는 opp 파이프라인 (TEST-SCENARIO.md 생성 없음). 단, 산출물 자체가 "검증 가능 양식"이므로 EXECUTE 완료 후 아래 grep 기반 검증을 QA-EXECUTE.md에 포함한다.
> **QA-PLAN 검증 완료 항목**: 모든 검증 방법이 객관적 grep 기준으로 작성되어 있음을 확인. 실제 EXECUTE 단계에서 결과 확인.

| F-ID | 검증 항목 | 검증 방법 | QA-PLAN |
|------|---------|---------|---------|
| F-001 | §1 리스크 가설 표 컬럼 6종 존재 | `grep "ID \| 변경 단위 \| 깨질 수 있는 계약"` → 존재 확인 | [x] |
| F-001 | §2.1 사전 조건 데이터 표 컬럼 4종 존재 | `grep "테이블 \| 식별자 \| 상태 \| 출처"` | [x] |
| F-001 | §3 L1/L2/L3 서브헤딩 존재 | `grep "L1\. 기능 단위"` + `grep "L2\. 프로세스 통합"` + `grep "L3\. 사용자 협업"` | [x] |
| F-002 | "시나리오 수 가이드" 섹션 삭제 | `grep "시나리오 수 가이드"` → 0건 확인 | [x] |
| F-002 | mock 금지 룰 존재 | `grep "mock 금지"` → 존재 확인 | [x] |
| F-002 | 계층 결정 규칙 표 존재 | `grep "계층 결정 규칙"` → 존재 확인 | [x] |
| F-003 | STEP 3.5 TEST-SCENARIO 단계 존재 | `grep "STEP 3.5"` → 존재 확인 | [x] |
| F-003 | STATE.md 행 예시에 TEST-SCENARIO 4행 존재 | `grep "TEST-SCENARIO \| 작업"` → 존재 확인 | [x] |
| F-003 | 모드 경계 갱신 | `grep "TEST-SCENARIO 사용자 확인"` → 존재 확인 | [x] |
| F-004 | scenario_source 파라미터 존재 | `grep "scenario_source"` op-dev-execute/SKILL.md | [x] |
| F-004 | 자가 점검 절차 섹션 존재 | `grep "자가 점검 절차"` | [x] |
| F-005 | EXECUTE 디스패치에 scenario_source 필드 | `grep "scenario_source"` opal-pilot-dev/SKILL.md | [x] |
| F-006 | PLAN.md 양식에 리스크 가설 표 존재 | `grep "리스크 가설 표"` op-dev-plan/SKILL.md | [x] |
| F-006 | 가설 도출 예시 3종 존재 | `grep "H-예1"` + `grep "H-예2"` + `grep "H-예3"` | [x] |
| F-006 | plan-agent 행동 규칙 추가 | `grep "리스크 가설 표"` opal-plan-agent/AGENT.md | [x] |
| F-007 | PM Gate TEST-SCENARIO 행 존재 | `grep "TEST-SCENARIO" PM Gate` | [x] |
| F-008 | §3 opd 행 갱신 | `grep "TEST-SCENARIO 사용자 확인"` opal-harness-semi-agentic.md | [x] |
| F-009 | L3 협업 게이트 SKILL.md 존재 | `grep "5-0. L3 시나리오"` opal-pilot-dev/SKILL.md | [x] |
| F-009 | PM 표준 요청 양식 존재 | `grep "캡틴, \[시나리오"` | [x] |
| F-009 | test-agent 행동 규칙 추가 | `grep "SUPERVISOR"` opal-test-agent/AGENT.md | [x] |
| F-010 | 변경이력 행 (004) 태스크 번호 | 8개 파일 `grep "(004)"` 모두 존재 확인 | [x] |

### §5.2 일관성 테스트

- [x] `op-dev-test-scenario/SKILL.md` 통일 형식과 `test-scenario-guide.md` 5단계 프로세스가 일치하는가 (섹션 번호·컬럼명 대조) — SKILL.md 7섹션, guide 5단계 프로세스 모두 존재 확인
- [x] `opal-pilot-dev/SKILL.md` STEP 3.5와 STEP 4 사이에 TEST-SCENARIO 흐름이 자연스럽게 연결되는가 — STEP 3.5 신설, STEP 4 EXECUTE로 자연스럽게 연결 확인
- [x] STATE.md 28행 구조에서 semi-agentic 모드 경계 행 번호(행 19, TEST-SCENARIO 사용자 확인)가 `opal-harness-semi-agentic.md` §3 설명과 일치하는가 — 행 19: TEST-SCENARIO 사용자 확인 확인, 모드 경계 명시 확인
- [x] `opal-plan-agent/AGENT.md` 행동 규칙이 `op-dev-plan/SKILL.md` 리스크 가설 표 양식과 일치하는가 — plan-agent: "의무" 표현, op-dev-plan: 6컬럼 양식(ID/변경단위/계약/영향/계층권고/시나리오후보) 정의 확인
- [x] 변경이력 버전이 각 파일 현행 버전 대비 +0.1 이상인가 — op-dev-test-scenario v1.3→v1.4(+0.1), test-scenario-guide v1.0→v2.0(+1.0), opal-pilot-dev v3.7→v3.8(+0.1) 확인

### §5.3 문서 품질

- [x] 모든 변경 파일에 변경이력 행 추가 (F-010) — 누락 파일 없음 — 8개 파일 모두 (004) 태스크 번호 포함 확인
- [x] `~/.opal/` 경로 파일 직접 수정 없음 (배포 경계 준수) — ~/.opal 경로 최근 수정 0개 확인
- [x] 한국어 본문 + 영어 코드/필드명 규칙 준수 (→ D-13 §언어 규칙) — 모든 변경 파일에서 한국어 설명 + 영어 코드/파라미터명 일관성 확인
- [x] SSOT 분산 없음 — PLAN.md 리스크 가설 표 양식이 `op-dev-plan/SKILL.md` 단일 위치 — op-dev-plan에만 양식 정의(4회), opal-plan-agent는 "의무" 1줄만 명시 확인
- [x] opds 변경 없음 (본 태스크 범위 외 확인) — opal-pilot-dev-short/SKILL.md 수정 없음 확인
- [x] mams 107 태스크에 retroactive 갱신 없음 — 107 태스크의 최근 수정은 state.json 등 working 파일만 (프로젝트 소스 변경 없음) 확인

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| R-1: PLAN.md 양식 SSOT 분산 — `op-dev-plan/SKILL.md`와 `opal-plan-agent/AGENT.md` 양쪽에 양식 내용이 생기면 이후 갱신 시 불일치 발생 | 중 | 결정: op-dev-plan/SKILL.md만 양식 SSOT, opal-plan-agent/AGENT.md는 "의무" 1줄만 추가 (§1.4) |
| R-2: mams 진행 중 태스크 107 호환 — 기존 opds 워크플로우에 본 변경 영향 | 중 | TASK.md §제약: retroactive 갱신 없음. 본 변경 이후 신규 태스크부터 적용 |
| R-3: opds 변경 미반영 — opds도 동일 self-confirming 구조이나 본 태스크 범위 외 | 중 | TASK.md §제약 준수. 향후 별도 태스크에서 opds 갱신 필요 항목 식별: `opal-pilot-dev-short/SKILL.md` STATE.md 행 + 모드 경계 |
| R-4: `opal-harness-semi-agentic.md` §8 차이 표에 TEST-SCENARIO 행이 opd 전용인지 표기 불명확 | 하 | 행 추가 시 "opd 전용" 비고 컬럼 추가로 명시 |
| R-5: STEP 3.5 작성자 "알투(PM)+캡틴 페어"가 이후 opal-pilot-dev-short에서 워커 디스패치로 전환 시 일관성 깨질 위험 | 하 | 현재 범위 외. 향후 opds 갱신 태스크에서 검토 |

---

## 6. 기술 스택 및 도구

- **변경 파일 유형**: SKILL.md, AGENT.md, references/*.md (코드 변경 없음)
- **변경 도구**: Edit (대부분) / Write (test-scenario-guide.md 전체 재작성 시)
- **검증 도구**: grep (양식 구조 검증), Bash (markdown 구조 확인)
- **배포**: 본 태스크 범위 외 — 캡틴이 별도로 install-mac.sh 실행

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-15 | 초기 작성 — 테스트 시나리오 양식·파이프라인 재설계 PLAN.md (004) |
