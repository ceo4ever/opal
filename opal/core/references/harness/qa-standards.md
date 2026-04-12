# QA 표준

> 출처: opal-harness.md §2
> 로드 시점: QA Gate 수행 시
> 역할: QA 체크리스트 검증 + QA/단계별 산출물 표준 파일명 + 스킬별 검증 방식 + 갱신 의무

---

### QA 체크리스트 검증

각 단계(PLAN, EXECUTE 등) 완료 후, 해당 시점의 체크리스트를 검증하고 갱신한다. 모든 오케스트레이터에 공통 적용.

**2단계 갱신 구조**:

| 단계 | 주체 | 역할 |
|------|------|------|
| 1차 갱신 | QA 에이전트 | QA 수행 시 체크리스트를 Read하고, 검증 통과 항목을 `[x]`로 갱신 |
| 2차 확인 | PM (오케스트레이터) | PM Gate에서 갱신 상태를 확인. 미갱신 시 QA 에이전트를 재소환하여 갱신 |

> **PM 직접 갱신 금지**: PM은 체크리스트를 직접 `[x]`로 갱신하지 않는다. 미갱신 발견 시 QA 에이전트를 재소환한다.

### QA 산출물 표준 파일명

PM Gate 자가 진단(interactive §3 / agentic §4)에서 확인하는 필수 산출물 파일명의 기본값.
오케스트레이터 SKILL.md에서 오버라이드 가능하며, 명시가 없으면 이 표준을 따른다.

| 단계 | 필수 산출물 파일 | 위치 |
|------|--------------|------|
| PLAN QA | `QA-PLAN.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| EXECUTE QA | `QA-EXECUTE.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| ANALYSIS QA | `QA-ANALYSIS.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (해당 단계가 있는 스킬만) |

### 단계별 주요 산출물 표준 파일명

파이프라인 현황판 산출물 행에서 추적하는 파일명의 기본값.
오케스트레이터 SKILL.md에서 오버라이드 가능하며, 명시가 없으면 이 표준을 따른다.

| 단계 | 주요 산출물 | 위치 |
|------|-----------|------|
| TASK | `TASK.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| ANALYSIS | `ANALYSIS.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (해당 단계가 있는 스킬만) |
| PLAN | `PLAN.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| TEST-SCENARIO | `TEST-SCENARIO.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (해당 단계가 있는 스킬만) |
| WIREFRAME | `wireframe.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (opdw 전용) |
| DONE | `DONE.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |

**스킬별 산출물 오버라이드**: 각 오케스트레이터 SKILL.md의 "STATE.md 도메인 치환값" 또는 별도 섹션에서 단계별 QA 산출물 파일명을 명시할 수 있다.

**스킬별 검증 방식**:

| 스킬 | 검증 수단 | 체크리스트 갱신 |
|------|----------|--------------|
| opd/opds | TEST-SCENARIO.md 결과 + QA Gate | QA 에이전트가 검증 시 갱신 → PM Gate에서 확인 |
| opp | QA Gate (QA 에이전트) | QA 에이전트가 검증 시 갱신 → PM Gate에서 확인 |

**갱신 의무**: DONE.md 생성 전에 QA 체크리스트의 모든 항목이 `[x]` 또는 "N/A + 사유"로 채워져야 한다. 미갱신 상태에서 DONE.md를 생성하지 않는다.
