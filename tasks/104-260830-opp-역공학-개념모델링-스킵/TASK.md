# TASK: opdd 역공학 트랙 — 개념모델링 스킵

> 작성일: 2026-08-30 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opdd(opal-pilot-data-design) 파이프라인에 **신규/역공학 2트랙 판정**을 도입하고, 역공학 트랙에서는 MODEL 단계의 **개념모델링(concept) 모드를 스킵**한다.

## 배경

opdd는 MODEL 단계를 언제나 `concept → logical → physical` 3모드 순차로 고정 실행한다. 기존 DB·DDL·ORM이 이미 존재하는 역공학 상황에서는 비즈니스 관점 개념 ERD를 새로 그리는 것이 무의미한 재작업이며, 실제 출발점은 이미 확정된 물리 스키마다.

## 배경 분석 (대화에서 도출)

PM이 opdd 관련 산출물을 실측하여 확인한 현행 상태다.

| # | 확인 사항 | 근거 |
|---|----------|------|
| A-1 | 개념모델링은 파이프라인 **행이 아니라 MODEL 단계 내부의 모드**다. MODEL은 `model.modeling` 1개 행으로만 존재한다 | `opal/skills/opal-pilot-data-design/references/pipeline.json` `task_steps[]` id 6 |
| A-2 | 3모드 순차는 opdd STEP 3 디스패치 프롬프트의 `**실행 순서**` 줄이 지시한다 — 따라서 스킵은 행 삭제가 아니라 **실행 순서 분기**로 구현된다 | `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 3: MODEL |
| A-3 | opdd TASK 단계에 「기존 ORM → 현행 스키마 역추적」 인풋 감지 행이 있으나, 이 감지가 MODEL 실행 순서에 연결되지 않는다 | `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 1 인풋 컨텍스트 주입 |
| A-4 | opdd에 신규/역공학 트랙 개념 자체가 없다 — 모드 축은 `--interactive`/`--semi-agentic`/`--agentic` 3종뿐이다 | `opal/skills/opal-pilot-data-design/SKILL.md` §명시 모드 |
| A-5 | op-data-model 모드 선택 규칙 표에 「기존 개념 ERD 주입 → logical부터」·「기존 논리 ERD 주입 → physical부터」 분기는 있으나 **「기존 DB/DDL 주입」 분기가 없다** | `opal/skills/op-data-model/SKILL.md` §모드 선택 규칙 |
| A-6 | 역공학 자체는 이미 DDL 단계에 존재한다 — `sql2dbml`로 기존 DDL에서 물리 DBML을 역추출하며, 산출물은 op-data-model physical 모드 경로를 따른다 | `opal/skills/op-data-ddl/SKILL.md` §Step 4. 역공학 (선택 — DDL → DBML) |
| A-7 | MODEL PM Gate 체크리스트가 「3모드 순차 완료」·「개념·논리·물리 모델링」을 무조건 요구한다 — 스킵 시 게이트가 자기모순이 된다 | `opal/skills/opal-pilot-data-design/references/pipeline.json` `model.pm_gate.gate.checklist` |
| A-8 | QA 검증 항목도 「단계 간 정합: 개념 ERD ↔ 논리 ↔ 물리」를 무조건 요구한다 | `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 5: QA |
| A-9 | opdd SKILL.md의 3모드 순차·QA 항목은 **설계 SSOT의 [MUST] 인용**이다 — SSOT를 고치지 않고 스킬만 고치면 스킬이 자기 인용문과 모순된다. SSOT는 「pilot은 MODEL 단계에서 3모드를 순차 실행(개념→논리→물리)」·「단계 간 정합: 개념 ERD ↔ 논리 ↔ 물리」를 무조건으로 규정한다 | `docs/proposals/opal-data-design.md` §3.2 파이프라인, §3.2.1 MODEL 3모드, §3.4 QA 검증 항목 |

## 확정된 설계 방향 (대화에서 합의)

- `[결정]` 역공학 트랙 판정은 **자동 감지 + 명시 플래그 병행**으로 한다. 캡틴이 제시된 후보 중 1안(자동 감지 + 사용자 확인)과 2안(명시 플래그)을 함께 채택했다.
- `[결정]` 자동 감지는 TASK 단계에서 수행하고, 감지 결과를 **사용자 확인으로 확정**한다 — 감지만으로 자동 스킵하지 않는다.
- `[결정]` 명시 플래그가 있으면 자동 감지 결과보다 **플래그가 우선**한다(사용자 주권 — `~/.opal/PRINCIPLES.md` §Core Stance).
- `[결정]` 이번 범위에서 스킵 대상은 **개념모델링 1개 모드**다. 논리·물리 모드는 유지한다.
- `[사실]` 개념모델링 스킵은 pipeline.json 행 삭제가 아니라 MODEL 단계 내부 실행 순서 분기로 구현된다 (→ A-1, A-2).

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | opdd에 신규/역공학 2트랙 판정을 도입하고, 역공학 트랙에서 MODEL의 concept 모드를 스킵한다 | - | - |
| 범위 | **포함**: opdd SKILL.md(트랙 판정·실행 순서·QA 항목), opdd pipeline.json(`model.pm_gate` 체크리스트), op-data-model SKILL.md(모드 선택 규칙), 설계 SSOT `docs/proposals/opal-data-design.md`(§3.2·§3.2.1·§3.4 트랙 분기 반영). **제외**: 기존 DB 접속·덤프 확보 절차, op-data-ddl §Step 4 역공학 명령 자체, DICT·DDL·CLOSE 단계 로직 | 역공학 트랙에서 논리·물리 모드의 **실행 순서**(`logical → physical` 유지 vs `physical → logical` 역전) — PLAN에서 결정 | `opal/skills/opal-pilot-data-design/references/pipeline.json`, `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 3·§STEP 5, `opal/skills/op-data-model/SKILL.md` §모드 선택 규칙, `docs/proposals/opal-data-design.md` §3.2.1 |
| 제약 | ① `~/.opal/` 배포 파일 직접 편집 금지 — 프로젝트 소스만 수정 후 install 재배포. ② 트랙 플래그는 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교**하며 `mode_flag_conflict` 판정 대상이 아니다. ③ 플래그 미사용 시 현행 동작 100% 유지(회귀 0). ④ 스킬·참조 문서 수정 시 변경이력 표 행 추가 의무 | - | `{프로젝트}/.opal/AGENT.md` §금지사항, `~/.opal/references/opal-harness.md` §2.5 워크스페이스 축 |
| 완료기준 | ① 역공학 트랙 판정 규칙이 opdd SKILL.md에 명문화되고 자동 감지 대상·확인 절차·플래그명이 모두 기재된다. ② 역공학 트랙에서 MODEL 실행 순서에 `concept`이 나타나지 않는다. ③ `model.pm_gate` 체크리스트와 QA 검증 항목이 트랙별로 분기되어 역공학 트랙에서 개념 산출물을 요구하지 않는다. ④ op-data-model 모드 선택 규칙 표에 「기존 DB/DDL 주입」 행이 존재한다. ⑤ 트랙 플래그 없이 호출하면 기존 3모드 순차 문구가 그대로 유지된다. ⑥ 수정한 2개 SKILL.md에 변경이력 행이 추가된다. ⑦ 설계 SSOT(`docs/proposals/opal-data-design.md`) §3.2·§3.2.1·§3.4가 트랙 분기를 반영하고, opdd SKILL.md의 `[MUST]` 인용문과 축자 일치한다 | - | - |

## 요구사항

- [ ] **R-1 트랙 판정 규칙 신설** — 무엇을: 신규/역공학 2트랙 정의 + 판정 절차(명시 플래그 우선 → 없으면 자동 감지 → 사용자 확인) / 어디에: `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 1: TASK / 왜: 확정 방향 1·2 (자동 감지 + 명시 플래그 병행) / AC: SKILL.md에 트랙명 2종, 플래그명, 자동 감지 대상 인풋 목록, 확인 절차가 모두 기재되고, 플래그가 자동 감지보다 우선한다는 규칙이 명문화된다
- [ ] **R-2 트랙 플래그 축 정의** — 무엇을: 트랙 플래그가 모드 축과 직교하며 `mode_flag_conflict` 대상이 아님을 명시 / 어디에: `opal/skills/opal-pilot-data-design/SKILL.md` §명시 모드 / 왜: 모드 플래그 개수 검사에 트랙 플래그가 섞이면 정상 호출이 거부된다 (→ A-4) / AC: 「모드 플래그 개수 검사에 트랙 플래그를 세지 않는다」는 취지의 문장이 존재하고, 플래그 미사용 시 현행 동작 유지가 명시된다
- [ ] **R-3 MODEL 실행 순서 분기** — 무엇을: STEP 3 디스패치 프롬프트의 `**실행 순서**` 줄을 트랙별로 분기 / 어디에: `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 3: MODEL / 왜: 스킵의 실질 구현 지점 (→ A-2) / AC: 신규 트랙은 `concept → logical → physical`이 그대로 남고, 역공학 트랙 순서 문자열에 `concept`이 0건이다
- [ ] **R-4 MODEL PM Gate 체크리스트 분기** — 무엇을: `model.pm_gate.gate.checklist`의 「{설계}/개념·논리·물리 모델링」·「3모드 순차 완료」를 트랙 조건부로 전환 / 어디에: `opal/skills/opal-pilot-data-design/references/pipeline.json` / 왜: 스킵 시 게이트가 없는 산출물을 요구해 자기모순이 된다 (→ A-7) / AC: 역공학 트랙에서 개념 산출물을 요구하지 않음이 체크리스트 문언으로 읽히고, JSON이 파싱 가능하며 기존 15개 `task_steps` 행 수·key가 불변이다
- [ ] **R-5 QA 검증 항목 분기** — 무엇을: 「단계 간 정합: 개념 ERD ↔ 논리 ↔ 물리」를 트랙별로 분기 / 어디에: `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 5: QA / 왜: 존재하지 않는 개념 ERD와의 정합을 검증할 수 없다 (→ A-8) / AC: 역공학 트랙 QA 항목이 논리↔물리 정합만 요구한다
- [ ] **R-6 op-data-model 모드 선택 규칙 확장** — 무엇을: 모드 선택 규칙 표에 「기존 DB/DDL 스키마 주입(역공학)」 행 추가 / 어디에: `opal/skills/op-data-model/SKILL.md` §모드 선택 규칙 / 왜: 단독 호출(`//erm`) 경로에서도 동일 판정이 필요하다 (→ A-5) / AC: 표에 역공학 행이 1행 이상 존재하고 발동 모드에 `concept`이 포함되지 않는다
- [ ] **R-8 설계 SSOT 정합** — 무엇을: 3모드 순차·QA 정합 규정에 트랙 분기를 반영 / 어디에: `docs/proposals/opal-data-design.md` §3.2 파이프라인, §3.2.1 MODEL 3모드, §3.4 QA 검증 항목 / 왜: opdd SKILL.md가 이 문서를 `[MUST]` 원문 인용하므로, SSOT를 두고 스킬만 고치면 스킬이 자기 인용문과 모순된다 (→ A-9) / AC: 세 절 각각에 역공학 트랙에서 개념 모드가 제외된다는 취지가 명시되고, opdd SKILL.md의 `[MUST]` 인용문과 SSOT 원문이 축자 일치한다
- [ ] **R-7 변경이력 갱신** — 무엇을: 변경이력 표에 행 추가 (일시 KST + 태스크 번호 104) / 어디에: `opal/skills/opal-pilot-data-design/SKILL.md` §변경이력, `opal/skills/op-data-model/SKILL.md` §변경이력 / 왜: `{프로젝트}/.opal/AGENT.md` §금지사항 「변경이력 누락 금지」 / AC: 2개 파일 각각에 104 태스크 행이 1행씩 추가된다

## 제약 조건

- [MUST] `{프로젝트}/.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `{프로젝트}/.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."
- 트랙 플래그 미사용 시 opdd 현행 동작이 100% 유지되어야 한다 (회귀 0). 축 정의 선례는 `~/.opal/references/opal-harness.md` §2.5 워크스페이스 축을 따른다.
- 변경이력은 **현행 규칙대로 행을 추가**한다. `.opal/MEMORY.json`에 「변경이력 표 제거 A안 확정」(2026-08-14) 메모리가 active로 남아 있으나, 대상 파일에 변경이력 표가 그대로 존재하고 `docs/CONVENTIONS.md` §변경이력 작성 의무도 유효하므로 미집행 상태로 판정한다 — 이번 태스크에서 제거를 선행하지 않는다.
- `pipeline.json`의 `task_steps[]` 행 수·`key`는 변경하지 않는다 — state-tool이 key로 주소지정하므로 기존 태스크 호환이 깨진다.

## 기술 스택

- Markdown (SKILL.md 스펙 문서), JSON (pipeline.json)
- 코드 변경 없음 — 프레임워크 스펙 문서 개정 태스크

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opdd SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md` | 개정 주 대상 — TASK 인풋 감지·MODEL 실행 순서·QA 항목·명시 모드 |
| D-2 | 설계 | opdd pipeline.json | `opal/skills/opal-pilot-data-design/references/pipeline.json` | MODEL PM Gate 체크리스트 SSOT |
| D-3 | 설계 | op-data-model SKILL.md | `opal/skills/op-data-model/SKILL.md` | 3모드 정의·모드 선택 규칙 |
| D-4 | 설계 | op-data-ddl SKILL.md | `opal/skills/op-data-ddl/SKILL.md` | 기존 역공학 절차(§Step 4) — 트랙 정의 시 정합 대상 |
| D-5 | 설계 | opal-harness.md | `~/.opal/references/opal-harness.md` | §2.5 직교 축(`--worktree`) 정의 선례 — 트랙 플래그 축 서술의 본 |
| D-6 | 설계 | 프로젝트 PM 프로필 | `.opal/AGENT.md` | 금지사항·검토 기준 |
| D-7 | 설계 | Data Design 설계 SSOT | `docs/proposals/opal-data-design.md` | opdd SKILL.md가 `[MUST]` 원문 인용하는 상위 SSOT — §3.2·§3.2.1·§3.4 동반 개정 대상 |
| D-8 | 설계 | brain — opdd 파이프라인 흐름 | `.opal/brain/pages/flow/opdd-pipeline-flow.md` | 「개념 → 논리 → 물리 (순차 3모드)」 흐름 기재 — CLOSE 단계 관련 문서 갱신 대상 |
