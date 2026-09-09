# QA 표준

> 출처: opal-harness.md §2
> 로드 시점: PM Gate 문서검증 수행 시
> 역할: QA 체크리스트 검증 + QA/단계별 산출물 표준 파일명 + 스킬별 검증 방식 + 갱신 의무
>
> 문서 QA(요구사항→설계 검토)는 별도 QA Gate 단계를 두지 않고 PM Gate가 직접 흡수한다. 본 문서의 검증·갱신은 PM이 PM Gate에서 단독으로 수행한다 (`harness/pm-review-gate.md` 검토 절차 §문서 QA 검증 참조). 동작 검증(TEST / TEST-SCENARIO / state-tool verify)은 본 문서와 독립이며 그 영역은 건드리지 않는다.

---

### QA 체크리스트 검증

각 단계(PLAN, EXECUTE 등) 완료 후, PM Gate가 해당 단계 산출물을 검증한다. 신규 `template: sdlc-v2` 태스크에서는 체크리스트를 갱신하지 않고, 단계 상태는 `state.json`, 시나리오 결과·증거는 `test-scenario.json`이 소유한다.

**PM 단독 검토·갱신**:

PM Gate 문서검증 시 PM이 직접 산출물을 읽고 단계별 기준으로 Pass/Needs Revision을 판단한다. 별도 QA 에이전트 1차 갱신 단계나 재소환은 없다.

legacy 태스크 또는 pipeline artifact가 체크리스트 갱신을 명시 요구하는 경우에만 PM이 체크리스트를 `[x]` 또는 "N/A + 사유"로 갱신한다. 검증을 통과하지 못한 항목은 `[ ]` 유지 + 미흡 사유를 남긴다.

### QA 산출물 표준 파일명

PM Gate 자가 진단(interactive §3 / agentic §4)에서 확인하는 QA 산출물 파일명의 legacy 기본값.
오케스트레이터 SKILL.md에서 오버라이드 가능하며, 명시가 없으면 이 표준을 따른다.

신규 sdlc-v2 태스크는 pipeline artifact가 QA 파일을 요구할 때만 이 표를 적용한다.

| 단계 | 필수 산출물 파일 | 위치 |
|------|--------------|------|
| PLAN QA | `QA-PLAN.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| EXECUTE QA | `QA-EXECUTE.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| ANALYSIS QA | `QA-ANALYSIS.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (해당 단계가 있는 스킬만) |

### 단계별 주요 산출물 표준 파일명

파이프라인 산출물 행(`state.json` `rows[]`, 조회: `state-tool show`)에서 추적하는 파일명의 기본값.
오케스트레이터 SKILL.md에서 오버라이드 가능하며, 명시가 없으면 이 표준을 따른다.

| 단계 | 주요 산출물 | 위치 |
|------|-----------|------|
| TASK | `TASK.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| ANALYSIS | `ANALYSIS.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (해당 단계가 있는 스킬만) |
| PLAN | `PLAN.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |
| TEST-SCENARIO | `TEST-SCENARIO.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (해당 단계가 있는 스킬만) |
| WIREFRAME | `wireframe.md` | `tasks/{NNN}-{YYMMDD}-{name}/` (opdw 전용) |
| DONE | `DONE.md` | `tasks/{NNN}-{YYMMDD}-{name}/` |

**스킬별 산출물 오버라이드**: 각 pilot `references/pipeline.json`의 `task_steps[].gate.artifacts`가 단계별 게이트 산출물의 SSOT다 — `state-tool mark`가 이를 존재 검증하고 `gate.checklist`를 stdout으로 반환한다 (091).

**스킬별 검증 방식**:

| 스킬 | 검증 수단 | 체크리스트 갱신 |
|------|----------|--------------|
| opd/opds | TEST-SCENARIO.md 명세 + `test-scenario.json` 결과(동작 검증, 독립 영역) + PM Gate 문서검증 | sdlc-v2는 상태 JSON 갱신, legacy는 필요 시 체크리스트 갱신 |
| opp | PM Gate 문서검증 | sdlc-v2는 상태 JSON 갱신, legacy는 필요 시 체크리스트 갱신 |

**갱신 의무**: 신규 sdlc-v2는 `state.json` 행 상태와 필요한 검증 JSON을 기준으로 DONE 진입을 판단한다. legacy 또는 pipeline artifact가 QA 체크리스트를 요구하면 DONE.md 생성 전에 모든 항목이 `[x]` 또는 "N/A + 사유"여야 한다.

### EXECUTE QA — 동작 증거 의무 (헌법 §4 집행)

EXECUTE QA는 "글자 존재 여부(grep)"가 아니라 **실제 동작**으로 검증한다. 원칙 자체는 `PRINCIPLES.md` §4를 따른다.

> 이 동작 검증의 실수행 주체는 TEST / TEST-SCENARIO / state-tool verify(독립·불변 영역)이며, PM Gate는 그 산출 증거(실행 출력·실응답)를 **확인**한다. 아래 체크리스트는 그 증거 확인용 항목으로 보존한다.

- [ ] 각 AC 충족이 실행 출력(stdout/exit code) 또는 실응답으로 입증되었는가 — 문자열 grep만으로 Pass 금지
- [ ] 지시된 실연동(API/DB 등)을 목업으로 대체하지 않았는가 — 대체 시 Fail
- [ ] 목업·스텁이 프로덕션 경로에 잔존하지 않는가
- [ ] 증거가 없는 항목은 Pass가 아니라 미완으로 처리했는가 (헌법: "No evidence → not done")

> 순수 문서 태스크(코드 변경 없음)는 본 의무에서 제외한다.

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-06-07 | QA Gate 별도 단계 전제 → PM Gate 문서검증 전제로 전환 — 로드 시점/2단계 갱신 구조(QA 에이전트 1차→PM 2차)/스킬별 검증 방식을 PM 단독 검토·갱신으로 재정의, EXECUTE QA 동작 증거의 실수행 주체(TEST/verify, 불변)·PM 확인 역할 1줄 명시. 동작 검증 영역은 불변 (014) |
| v1.1 | 2026-08-14 08:38 | 스킬별 산출물 오버라이드 근거를 오케스트레이터 SKILL.md에서 각 pilot `references/pipeline.json`의 `task_steps[].gate.artifacts`로 이전 — `state-tool mark`의 존재 검증·`gate.checklist` stdout 반환 연계 명시 (091) |
| v1.2 | 2026-08-16 13:26 | STATE.md 저널화 — "파이프라인 현황판 산출물 행"(표 전제)을 "파이프라인 산출물 행(`state.json` rows[])"으로 치환, `state-tool show` 조회 경로 명시 (094) |
| v1.3 | 2026-09-09 | sdlc-v2에서 QA 체크리스트·QA 파일을 기본 생성/갱신하지 않고 `state.json`·`test-scenario.json` 소유권을 명시. legacy와 pipeline artifact 요구 시에만 기존 QA 파일·체크리스트 표준을 적용 (111) |
