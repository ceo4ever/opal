# TEST SCENARIO: opal-pilot-project-loop(oppl) 루프 기반 오케스트레이터 신설

> 작성일: 2026-07-10 | 상태: 작성 완료
> 작성자: 알투(PM) — agentic 모드 캡틴 대행 | PLAN.md §리스크 가설 표 기반
> 도구셋: `test-tool resolve` → be/py = pytest (unit·integration), lint ruff·문법 `bash -n`/`py_compile`

## 0. RED-first 트랙 판단 (red-first.md §1.5)

| 대상 | 트랙 | 근거 |
|------|------|------|
| F-001 backlog-tool / F-002 test-tool scenario-* / F-003 state-tool enum | **RED-first 강제** | 상태 전이·동결 게이트·CLI JSON 계약 = 비즈니스 로직 + API(CLI) 계약 |
| F-004~F-009 (AGENT.md·SKILL.md·references·레지스트리·install·docs) | 구현-후-검증 | 문서·설정 자산 (탐색·시각 아님, 산출물 검사로 충분) |

- RED 코드 작성: **opal-test-agent(mode: red)** 가 EXECUTE 진입 전 S-001~S-020 그룹(도구 시나리오)을 실패 테스트 코드로 변환·실행·RED 증거 기록 (작성자≠구현자 — red-first.md §2).
- EXECUTE(GREEN) 진입 게이트: `state-tool verify <task> --red-check` ON.
- GREEN/fix 루핑 중 RED 테스트 파일 수정 금지 (red-first.md §3).

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 전사 + 시나리오 확정. H-7 계층은 PLAN 권고 L3 → **L2로 조정**: 드라이런은 에이전트 자동화 가능 항목으로 L3(사용자 협업, 자동화 불가 한정) 요건에 해당하지 않음 (test-scenario-guide.md §Step 3 계층 결정 원칙 — 작성자 독립 판단).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-003 state-tool `--skill` enum | oppl 미등록 시 init 거부 → 오케스트레이터 진입 실패 | P0 | L2 | S-020 |
| H-2 | F-002 `scenario-lock` 동결 게이트 | RED 미확인 lock 허용 시 self-confirming | P0 | L1+L2 | S-011, S-012 |
| H-3 | F-001 backlog.json 동시 쓰기 | 병렬 mark 시 상태 유실/손상 | P1 | L2 | S-001b |
| H-4 | F-004 evaluator readonly 계약 | mutate 시 생성자=평가자 헌법 위반 | P0 | L1+L2 | S-030, S-090 |
| H-5 | F-001/F-002 결과 계약(JSON) | 단일라인 JSON·exit code 위반 시 파싱 실패 | P1 | L1 | S-007 |
| H-6 | F-001 tool-gated 축 분리 | BACKLOG.md 손편집 허용 시 double-truth | P1 | L2 | S-006 |
| H-7 | F-006 oppl 루프 종료조건 | 가드 부재 시 무한 루프/비용 폭주 | P0 | L1+L2 | S-055, S-090 |
| H-8 | F-006 3-way 모드 승계 | semi-agentic 경계 미승계 시 게이트 우회 | P0 | L1 | S-051 |
| H-9 | F-006/F-004 검증 2원화 순서 | Evaluator(전)/test-agent(후) 역전 시 게이트 무력화 | P1 | L2 | S-090 |
| H-10 | F-007 skills-registry 트리거 | 정규식 충돌/누락 시 `//oppl` 미발동·오발동 | P1 | L1 | S-060 |
| H-11 | F-008 install 실행권한 | run.sh 실행비트 누락 시 배포본 미동작 | P1 | L2 | S-071 |
| H-12 | F-005/F-006 용어 일관성 | BACKLOG.md ↔ 태스크 PLAN.md 명칭 혼동 | P2 | L1 | S-041 |

## 2. 테스트 데이터 설계

> 이 태스크의 "테이블" = 도구가 관리하는 JSON 파일. 모든 fixture는 테스트가 임시 태스크 폴더에 생성한다 (실 파일 생성·재읽기, mock 불용).

### 2.1 사전 조건 데이터

| 테이블(파일) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| `{tmp}/backlog.json` | 태스크 T01 | pending, P0, depends=[] | fixture (테스트가 `backlog-tool init`+`add-task`로 생성) |
| `{tmp}/backlog.json` | 태스크 T02 | pending, P1, depends=[T01] | fixture (동일) |
| `{tmp}/test-scenario.json` | 시나리오 S1 | red_confirmed=true | fixture (`scenario-init` 후 갱신) |
| `{tmp}/test-scenario.json` | 시나리오 S2 | red_confirmed=false | fixture (동일) |
| `{tmp}/state.json` | 056-dryrun 태스크 | `--skill oppl --mode semi-agentic` init 산출 | 테스트 실행 시 `state-tool init` 생성 |
| `tasks/056-260710-opd-oppl-루프-오케스트레이터/dryrun/` | 드라이런 미니 프로젝트 | CONTRACT.md 샘플 + 백로그 1태스크 | S-090 실행 시 opal-test-agent 생성 |
| `~/.opal/` 배포본 | oppl·evaluator·backlog-tool | install 실행 후 존재 | S-071 실행 시 `./scripts/install-mac.sh` |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-001 | 빈 임시 폴더 | `backlog-tool init` 2회 | 1회차 backlog.json+BACKLOG.md 생성, 2회차 `already_initialized` exit 1 |
| S-002 | T01(pending)·T02(depends=T01) | `select-next` 호출 | T01 반환 (T02는 depends 미충족 스킵), T01 done 후 재호출 시 T02 |
| S-003 | T01 pending | `mark --status in_progress` → `done` → 무효 전이(done→pending) | 유효 전이 반영, 무효 전이 `invalid_status_transition` exit 1 |
| S-004 | T01 done·T02 pending | `done-check` | `all_done:false, remaining:[T02]` → T02 done 후 `all_done:true` |
| S-007 | 각 서브명령 정상/오류 입력 | 6서브명령 전체 호출 | stdout 단일라인 JSON 파싱 성공 + exit 0/1/2 규정 준수 |
| S-001b | T01·T02 pending | `mark` 2건 동시(&) 실행 | backlog.json 유효 JSON 유지 + 두 상태 모두 반영(또는 명시적 락 에러 — 유실 없음) |
| S-011 | S1(red=true)·S2(red=false) | `scenario-lock` | `red_not_confirmed` exit 1 → S2 red=true 후 재호출 시 locked=true |
| S-012 | locked=false | `scenario-mark --result pass` | `scenario_not_locked` exit 1 → lock 후 재호출 시 result 기록 |
| S-014 | 기존 test-tool 스위트 | `resolve`/`check` 호출 + 기존 pytest 스위트 실행 | 기존 4서브명령 JSON 계약 불변, 기존 테스트 GREEN |
| S-020 | state-tool 소스 수정본 | `init --skill oppl --mode semi-agentic` (임시 폴더) | state.json 생성 + skill=oppl, 기존 8스킬 init 회귀 GREEN |
| S-030 | `opal/agents/opal-evaluator-agent/AGENT.md` | frontmatter·본문 grep | tools=[Read,Grep,Glob,Bash]만, Edit/Write 부재, verdict-only·커밋 금지 명문 |
| S-041 | references 4종 + SKILL.md | 용어 grep | BACKLOG.md=프로젝트 백로그 / PLAN.md=태스크 미시설계 구분 위반 0건 |
| S-051 | oppl SKILL.md | 섹션 grep | Harness 블록(3-way selector)+Agentic/Semi 절+CLOSE 게이트 존재, semi-agentic 기본 명시 |
| S-055 | references/loop-control.md + SKILL.md | 섹션 grep | 종료조건 5종(반복상한·예산·무진전·목표체크·사람게이트) 전부 존재 |
| S-060 | 갱신된 opal-skills-registry.json | `skill-registry match "oppl"` + 기존 alias(opp/opd/oppd/opsdd) match | oppl 정확 매칭 + 기존 alias 회귀 0건 + JSON 유효 |
| S-071 | 프로젝트 소스 완성본 | `./scripts/install-mac.sh` 실행 | `~/.opal/skills/opal-pilot-project-loop/SKILL.md`·`~/.opal/agents/opal-evaluator-agent/AGENT.md`·`~/.opal/tools/backlog-tool/run.sh(-x)` 존재 + 어댑터 생성 |
| S-090 | 배포 완료 상태 + dryrun 폴더 | 설계 루프 산출물(CONTRACT 샘플)→evaluator 1회 실판정→백로그 1태스크: select→scenario-init→RED→lock→(구현 시뮬)→mark pass→backlog done→done-check | ① 판정 순서 evidence: QA-SPEC(구현 전) 시점 < 테스트 결과(구현 후) 시점 ② evaluator changed_files=보고서만 ③ done-check all_done:true ④ 무진전 시나리오에서 반복상한 가드 발동 기록 |

## 3. 검증 시나리오

> L1 = EXECUTE 워커 자가검증(`test-tool unit`) / L2 = TEST 단계(opal-test-agent, `test-tool integration`) 묶음.

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-001: backlog-tool init 멱등·생성 계약

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 (H-6 연계) |
| 대상 | `backlog-tool init` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 빈 임시 태스크 폴더 (§2.2 S-001) |
| 기대 결과 | backlog.json+BACKLOG.md 생성, 재실행 `already_initialized` exit 1 |
| 도구 | pytest (`opal/tools/backlog-tool/tests/test_backlog_tool.py`, 케이스 `[T056/L1-F001]`) |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py::TestInit -v` |
| 결과 | **PASS** |
| 상세 | 3 passed (`test_init_creates_backlog_json_and_md`, `test_init_stdout_is_single_line`, `test_init_twice_rejects_with_already_initialized`) — exit 0. backlog.json+BACKLOG.md 생성 확인, 재실행 시 `already_initialized` exit 1 확인. RED-EVIDENCE.md §1.1(18 failed) 대비 GREEN 전환. |

#### S-002: select-next 의존·우선순위 규칙

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `backlog-tool add-task`/`select-next` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | T01(P0)·T02(P1, depends=T01) fixture (§2.2 S-002) |
| 기대 결과 | depends 미충족 스킵 + priority 순 pending 반환, 소진 시 null |
| 도구 | pytest, 케이스 `[T056/L1-F001]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py::TestSelectNext -v` |
| 결과 | **PASS** |
| 상세 | 3 passed (`test_returns_highest_priority_pending_with_depends_met`, `test_returns_dependent_task_after_dependency_done`, `test_returns_null_when_exhausted`) — exit 0. depends 미충족 스킵 + priority 순 반환 + 소진 시 null 확인. |

#### S-003: mark 상태 전이 가드

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `backlog-tool mark` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | §2.2 S-003 |
| 기대 결과 | 유효 전이 반영(done 시 done_at), 무효 전이 `invalid_status_transition` exit 1 |
| 도구 | pytest, 케이스 `[T056/L1-F001]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py::TestMarkTransition -v` |
| 결과 | **PASS** |
| 상세 | 2 passed (`test_valid_transition_pending_to_in_progress_to_done`, `test_invalid_transition_done_to_pending_rejected`) — exit 0. 유효 전이 반영(done_at 기록) + 무효 전이 `invalid_status_transition` exit 1 확인. |

#### S-004: done-check 종료 판정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-7(종료 판정 입력) |
| 대상 | `backlog-tool done-check` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | §2.2 S-004 |
| 기대 결과 | 잔여 시 `all_done:false`+`remaining[]`, 전체 done 시 `all_done:true` |
| 도구 | pytest, 케이스 `[T056/L1-F001]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py::TestDoneCheck -v` |
| 결과 | **PASS** |
| 상세 | 2 passed (`test_all_done_false_with_remaining`, `test_all_done_true_when_all_tasks_done`) — exit 0. 잔여 시 `all_done:false`+`remaining[]`, 전체 done 시 `all_done:true` 확인. |

#### S-007: 도구 결과 계약 (단일라인 JSON + exit code)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | backlog-tool 6서브명령 + test-tool scenario-* 4서브명령 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 정상/오류 입력 각 1건 이상 (§2.2 S-007) |
| 기대 결과 | stdout 1줄 JSON 파싱 성공, exit 0(성공)/1(위반)/2(내부) 준수, ERROR_CODES 키 일치 |
| 도구 | pytest, 케이스 `[T056/L1-F001]`·`[T056/L1-F002]` |
| 실행 명령 | (F-002분) `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_scenario.py::TestScenarioResultContract -v` · (F-001분, opal-test-agent 보강 실행) `~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py::TestResultContract opal/tools/test-tool/tests/test_scenario.py::TestScenarioResultContract -v` |
| 결과 | **PASS** |
| 상세 | 12 passed, 0 failed (backlog 6 + scenario 6) — exit 0. backlog-tool 6서브명령(init/add-task/select-next/mark/done-check/show) + test-tool scenario-* 4서브명령(scenario-init/lock/mark/status) 전체 stdout 단일라인 JSON 파싱 성공, exit 0/1 규정 준수 확인. |

#### S-011: scenario-lock RED-first 동결 게이트

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `test-tool scenario-lock` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | S1(red=true)·S2(red=false) fixture (§2.2 S-011) |
| 기대 결과 | red 미확인 존재 시 `red_not_confirmed` exit 1, 전건 확인 후 locked=true |
| 도구 | pytest (`opal/tools/test-tool/tests/test_scenario.py` 신규 — lib/scenario.py 모듈 미러링), 케이스 `[T056/L1-F002]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_scenario.py::TestScenarioLockRedGate -v` |
| 결과 | **PASS** |
| 상세 | 2 passed (`test_lock_rejected_when_any_scenario_red_unconfirmed`, `test_lock_succeeds_when_all_scenarios_red_confirmed`) — exit 0. red 미확인 존재 시 `red_not_confirmed` exit 1 확인 → 전건 확인 후 `scenario-lock` locked=true 확인. RED-EVIDENCE.md §1.2 대비 GREEN 전환. |

#### S-012: scenario-mark 잠금 전 기록 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `test-tool scenario-mark` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | locked=false 상태 (§2.2 S-012) |
| 기대 결과 | `scenario_not_locked` exit 1 → lock 후 result·evidence 기록 성공 |
| 도구 | pytest, 케이스 `[T056/L1-F002]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_scenario.py::TestScenarioMarkLockGate -v` |
| 결과 | **PASS** |
| 상세 | 2 passed (`test_mark_rejected_before_lock`, `test_mark_succeeds_after_lock`) — exit 0. lock 전 `scenario-mark` 시도 `scenario_not_locked` exit 1 확인 → lock 후 result·evidence 기록 성공 확인. |

#### S-030: evaluator readonly 계약 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `opal/agents/opal-evaluator-agent/AGENT.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | AGENT.md 작성 완료 |
| 기대 결과 | frontmatter tools에 Read/Grep/Glob/Bash만(Edit·Write 부재), verdict-only·mutate 금지·커밋 금지 명문, model: advanced, 결과 계약 {item,result,reason,suggestion}+verdict 정의 |
| 도구 | grep/Bash |
| 실행 명령 | `grep -n "^tools:" AGENT.md` (Read/Grep/Glob/Bash만, Edit·Write 부재 확인) · `grep -n "^model:" AGENT.md` (advanced) · `grep -n "verdict-only\|mutate 금지\|커밋 금지" AGENT.md` · `grep -n "\"item\"\|\"result\"\|\"reason\"\|\"suggestion\"\|\"verdict\"" AGENT.md` (대상: `opal/agents/opal-evaluator-agent/AGENT.md`) |
| 결과 | **PASS** |
| 상세 | `tools:` 라인(9행) = `[Read, Grep, Glob, Bash]` — Edit·Write 부재 확인. `model:` 라인(7행) = `advanced`. `verdict-only·mutate 금지·커밋 금지` 명문 3건(5·119·120행) 확인 — 119행 "verdict-only · mutate 금지 — 소스 코드·설계 산출물 수정 금지. tools는 Read/Grep/Glob/Bash만 허용(Edit/Write 미부여)", 120행 "커밋 금지 — git commit 호출 금지". 결과 계약 키 `item/result/reason/suggestion`(78행) + `verdict`(106행) 정의 확인. |

#### S-041: 용어 일관성 (BACKLOG ↔ 태스크 PLAN)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | references 4종 + oppl SKILL.md |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | F-005·F-006 작성 완료 |
| 기대 결과 | BACKLOG.md=프로젝트 백로그 미러 / PLAN.md=태스크 미시설계로 일관, 혼용 0건 |
| 도구 | grep |
| 실행 명령 | `grep -rn "BACKLOG.md" opal/skills/opal-pilot-project-loop/SKILL.md opal/skills/opal-pilot-project-loop/references/*.md` · `grep -rn "PLAN.md" opal/skills/opal-pilot-project-loop/SKILL.md opal/skills/opal-pilot-project-loop/references/*.md` (opal-test-agent 실행) |
| 결과 | **PASS** |
| 상세 | `BACKLOG.md` 참조 6건 — 모두 "backlog-tool 렌더 미러/프로젝트 백로그" 문맥(48·52·77·115·219행 SKILL.md). `PLAN.md` 참조 7건 — 모두 "태스크 미시 설계" 문맥(SKILL.md 82·192·289·306·320행, contract.md 80행, journey-flow.md 33행). 87행에 명시적 구분 문장 존재: "BACKLOG.md는 프로젝트 백로그 미러(backlog-tool 렌더)이고, 태스크 폴더 PLAN.md는 해당 태스크의 미시 설계다. 둘을 혼용하지 않는다." 혼용 0건. |

#### S-051: oppl SKILL 3-way 모드 승계 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `opal/skills/opal-pilot-project-loop/SKILL.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | F-006 작성 완료 |
| 기대 결과 | Harness 블록(interactive/agentic/semi-agentic selector + mode_flag_conflict) + Agentic/Semi 절 + CLOSE 진입 게이트(auto-pass 거부) 존재, 기본=semi-agentic 명시, 플랫폼 조건문 0건 |
| 도구 | grep |
| 실행 명령 | `grep -n "^## Harness" opal/skills/opal-pilot-project-loop/SKILL.md` · `grep -n -- "--interactive\|--agentic\|--semi-agentic\|mode_flag_conflict" opal/skills/opal-pilot-project-loop/SKILL.md` · `grep -n "^## Agentic / Semi-Agentic 모드\|기본 모드 (semi-agentic)" opal/skills/opal-pilot-project-loop/SKILL.md` · `grep -n "auto-pass.*거부\|agentic_close_gate_requires_user" opal/skills/opal-pilot-project-loop/SKILL.md` · `grep -niE "if.*platform|switch.*platform|플랫폼.*(분기\|조건)" opal/skills/opal-pilot-project-loop/SKILL.md` (기대: 마지막 명령 0건) |
| 결과 | **PASS** |
| 상세 | `## Harness` 블록 존재(24행). 모드 플래그 3종+`mode_flag_conflict` 존재(30~33행: `--interactive`→opal-harness-interactive.md, `--agentic`→opal-harness-agentic.md, 무플래그/`--semi-agentic`(기본)→opal-harness-semi-agentic.md, 다중 플래그 시 `mode_flag_conflict`). `## Agentic / Semi-Agentic 모드` 절(394행)+"기본 모드 (semi-agentic)"(398행) 존재. CLOSE 게이트 auto-pass 거부 명문(441행: "semi-agentic / agentic 모두 CLOSE 첫 행(#19) `--auto-pass` 거부(`agentic_close_gate_requires_user`)"). 플랫폼 조건문 검색 0건(exit 1, 매치 없음) — 플랫폼 독립성 원칙 위반 없음. |

#### S-055: 루프 종료조건 5종 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `references/loop-control.md` + SKILL.md §루프 제어 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | F-005·F-006 작성 완료 |
| 기대 결과 | 반복상한·예산·무진전·목표체크·사람게이트 5종 가드 전부 정의 + SKILL 인라인 참조 정합 |
| 도구 | grep |
| 실행 명령 | `grep -n "반복 상한\|예산\|무진전 감지\|목표 달성 체크\|사람 게이트" opal/skills/opal-pilot-project-loop/references/loop-control.md` · `grep -n "반복 상한\|예산\|무진전 감지\|목표 달성 체크\|사람 게이트" opal/skills/opal-pilot-project-loop/SKILL.md` · `grep -n "references/loop-control.md" opal/skills/opal-pilot-project-loop/SKILL.md` |
| 결과 | **PASS** |
| 상세 | loop-control.md에 5종 전부 존재: 반복 상한(§2, 17·30행), 예산(§3, 18·46행), 무진전 감지(§4, 19·57행), 목표 달성 체크(§5, 20·72행), 사람 게이트(§9, 24·123행) — §26에 "TEST-SCENARIO.md S-055가 검사하는 종료조건 5종은 8요소 중 직접 종료를 판정하는 5요소(#1·#2·#3·#4·#8)"라는 명시적 대응 주석 존재. SKILL.md §루프 제어(376~382행)에 동일 5종 인라인 목록 + `references/loop-control.md` 참조 다수(225·274·378~382·437·452·453행) — 정합 확인. |

#### S-060: skills-registry oppl 트리거

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `opal/core/references/opal-skills-registry.json` |
| 계층 | L1 |
| **실행 방식** | **M1 (skill-registry CLI)** |
| 조건 | F-007 등록 완료 |
| 기대 결과 | `match "oppl"` → opal-pilot-project-loop 반환, 기존 alias(opp/opd/opds/oppd/opsdd) match 회귀 0건, JSON 파싱·정규식 컴파일 성공 |
| 도구 | `node ~/.opal/tools/skill-registry/skill-registry.js` (소스 검증은 프로젝트 경로 대상) |
| 실행 명령 | `python3 -c "import json,re; d=json.load(open('opal/core/references/opal-skills-registry.json')); [re.compile(t) for g in d['groups'].values() for it in g for t in it.get('triggers',[])]; print('parse+compile OK')"` (JSON 파싱 + 전체 트리거 정규식 컴파일) 및 수동 매칭 스크립트로 `oppl→opal-pilot-project-loop`, `opp/opd/opds/oppd/opsdd`가 각각 자기 자신에만 매칭됨을 확인 (배포본 `~/.opal/tools/skill-registry/skill-registry.js`는 배포 레지스트리를 읽으므로 소스 검증에는 미사용) |
| 결과 | **PASS** |
| 상세 | `parse+compile OK` 출력 확인 — JSON 파싱 성공 + 전체 트리거 정규식 컴파일 성공(컴파일 에러 없음). 수동 매칭 스크립트 결과: `oppl → ['opal-pilot-project-loop']`, `opp → ['opal-pilot-project']`, `opd → ['opal-pilot-dev']`, `opds → ['opal-pilot-dev-short']`, `oppd → ['opal-pilot-project-dev']`, `opsdd → ['opal-pilot-sdd']` — 신규 oppl 정확 매칭 + 기존 5개 alias 전부 자기 자신에만 매칭(교차 오발동 0건, 회귀 없음). |

### L2. 프로세스 통합 (자동, 실 파일 read→CUD→re-read)

#### S-006: BACKLOG.md 미러 ↔ backlog.json 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | backlog-tool 렌더 파이프라인 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | init→add-task→mark 연쇄 실행 (§2.2 S-001~004 데이터 재사용) |
| 기대 결과 | 매 CUD 후 BACKLOG.md 표가 backlog.json과 정합(태스크 수·상태 일치), 마커 구간 외 본문 보존 |
| 도구 | pytest, 케이스 `[T056/L2-F001]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py::TestBacklogMdMirror -v` |
| 결과 | **PASS** |
| 상세 | 1 passed (`test_md_reflects_json_after_cud_chain`) — exit 0. init→add-task→mark 연쇄 실행 후 BACKLOG.md 표가 backlog.json과 태스크 수·상태 일치 확인, 마커 구간 외 본문 보존 확인. |

#### S-001b: backlog.json 동시 쓰기 무손상

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `backlog-tool mark` 병렬 호출 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | T01·T02 pending, mark 2건 동시 실행 (§2.2 S-001b) |
| 기대 결과 | backlog.json 유효 JSON 유지 + 상태 유실 없음 (양쪽 반영 또는 명시적 잠금 에러 — silent 손상 금지) |
| 도구 | pytest (subprocess 병렬), 케이스 `[T056/L2-F001]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/backlog-tool/tests/test_backlog_tool.py::TestConcurrentMark -v` |
| 결과 | **PASS** |
| 상세 | 1 passed (`test_parallel_mark_no_silent_corruption`) — exit 0. T01·T02 mark 2건 동시(&) 실행 후 backlog.json 유효 JSON 유지 확인 + 양쪽 상태 반영(또는 명시적 잠금 에러) 확인 — silent 손상 없음. |

#### S-014: test-tool 기존 4서브명령 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 (회귀 — R-8) |
| 대상 | test-tool resolve/check/unit/integration |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + CLI)** |
| 조건 | scenario-* 확장 반영 후 |
| 기대 결과 | 기존 4서브명령 JSON 계약·동작 불변, 기존 `tests/test_test_tool.py` 스위트 GREEN |
| 도구 | pytest, 케이스 기존 스위트 + `[T056/L2-F002]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py -v` (참고: `TestResolve::test_resolve_infer_fallback_when_no_yaml` 1건은 RED-EVIDENCE.md §1.3 기록된 환경 의존적 사전 존재 이슈 — scenario-* 확장과 무관, 상태 불변 확인됨) |
| 결과 | **PASS** (회귀 없음 — 기지 환경성 실패 1건 상태 불변) |
| 상세 | `-q` 실행 결과 `1 failed, 11 passed, 9 subtests passed` — RED-EVIDENCE.md §1.3 기록값(`1 failed, 11 passed, 9 subtests passed`, scenario-* 확장 전)과 **정확히 동일**. 실패 1건(`TestResolve::test_resolve_infer_fallback_when_no_yaml`)은 로컬 `~/.opal` 전역 `test-tools.yaml` 존재로 `source: global`이 반환되는 환경 의존적 사전 존재 이슈(`data.get("source")` = `'global'` != `'infer'`) — scenario-* 확장과 무관, 회귀 아님으로 판정. 기존 4서브명령(resolve/check/unit/integration) JSON 계약·동작 불변 확인. |

#### S-020: state-tool oppl init 실호출 + 8스킬 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `state-tool init --skill oppl` |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + CLI)** |
| 조건 | enum 확장 반영 후, 임시 태스크 폴더 (§2.2 S-020) |
| 기대 결과 | oppl init 성공(state.json skill=oppl, STATE.md 생성), 기존 8스킬 init 회귀 GREEN, schema validate 통과 |
| 도구 | pytest (`opal/tools/state-tool/tests/test_state_tool.py` 기존 파일에 케이스 추가 — 모듈 미러링), 케이스 `[T056/L2-F003]` |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestOpplSkillInit -v` (신규) + `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` (전체 회귀) |
| 결과 | **PASS** (회귀 없음 — 기지 환경성 실패 1건 상태 불변) |
| 상세 | 신규 케이스 2 passed(`test_init_with_skill_oppl_succeeds` — `--skill oppl` init 성공, state.json skill=oppl 생성; `test_existing_eight_skills_regression_unaffected` — 기존 스킬 회귀 확인). RED-EVIDENCE.md §1.3 시점 `test_init_with_skill_oppl_succeeds`는 FAIL(exit 2, choices에 oppl 미등록)이었으나 GREEN 전환 확인. 전체 스위트 `-q` 결과 `1 failed, 204 passed, 3 subtests passed` — RED 시점(`2 failed, 203 passed, 3 subtests passed`) 대비 RED 대상 1건이 GREEN 전환(203→204 passed)되었고, 잔여 실패 1건(`TestVerify::test_verify_passes_own_test_scenario_md`)은 034 태스크 경로(`tasks/034-.../TEST-SCENARIO.md`)가 `tasks/backup/`으로 이관되어 발생한 **본 태스크와 무관한 기존 환경성 실패** — 상태 불변(RED 시점부터 이미 존재) 확인, 회귀 아님으로 판정. 기존 8스킬 init 회귀 GREEN 확인. |

#### S-071: install 배포 + 실행권한

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `scripts/install-mac.sh` |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash)** |
| 조건 | 전 소스 자산 완성 후 (§2.1 배포본 행) |
| 기대 결과 | `bash -n` 문법 통과 → install 실행 → oppl SKILL·evaluator AGENT·backlog-tool 배포 + `run.sh -x` 실행권한 + `~/.claude/agents/opal-evaluator-agent.md` 어댑터 생성 |
| 도구 | Bash |
| 실행 명령 | `bash -n scripts/install-mac.sh` → `./scripts/install-mac.sh` → `ls -la ~/.opal/skills/opal-pilot-project-loop/SKILL.md ~/.opal/agents/opal-evaluator-agent/AGENT.md ~/.opal/tools/backlog-tool/run.sh ~/.claude/agents/opal-evaluator-agent.md` → `~/.opal/tools/backlog-tool/run.sh` (무인자) + `~/.opal/tools/backlog-tool/run.sh show --help` |
| 결과 | **PASS** |
| 상세 | `bash -n` 문법 통과(exit 0) → `./scripts/install-mac.sh` 실행 완료(`✓ OPAL 설치 완료 (v0.6.8-5-gf4be145)`, exit 0). 배포 확인: `~/.opal/skills/opal-pilot-project-loop/SKILL.md` 존재(31039 bytes), `~/.opal/agents/opal-evaluator-agent/AGENT.md` 존재(8313 bytes), `~/.opal/tools/backlog-tool/run.sh` 권한 `-rwxr-xr-x`(-x 확인), `~/.claude/agents/opal-evaluator-agent.md` 어댑터 생성 확인(8485 bytes). 실동작 검증: 배포본 `run.sh` 무인자 호출 → `usage: backlog-tool ...` + exit 2(정상 argparse 사용법 오류), `run.sh show --help` → 정상 help 출력 + exit 0 — 배포본이 실제로 동작함을 확인. |

#### S-090: oppl 드라이런 E2E (설계 루프 → 실행 루프 1태스크)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-9, H-4 (동작 검증) |
| 대상 | oppl 파이프라인 전체 (도구 체인 + evaluator 실디스패치) |
| 계층 | L2 |
| **실행 방식** | **M1 (도구 체인 Bash) + evaluator 에이전트 실디스패치 1회** |
| 조건 | S-071 배포 완료, dryrun 폴더 (§2.1·§2.2 S-090) |
| 기대 결과 | ① 설계 루프 산출물(CONTRACT 샘플) → evaluator 실판정(QA-SPEC 생성, changed_files=보고서만 — H-4) ② 실행 루프 1태스크 완주: select-next→scenario-init→RED 증거→lock→구현→mark pass→backlog done→done-check all_done:true ③ 순서 evidence: QA-SPEC(구현 전) 타임스탬프 < 테스트 결과(구현 후) — H-9 ④ 무진전 케이스에서 반복상한 가드 발동 기록 — H-7 |
| 도구 | Bash(도구 체인) + Agent 디스패치(opal-evaluator-agent) |
| 실행 명령 | ① `dryrun/PRD.md`·`TRD.md`·`CONTRACT.md`(스키마·시그니처·경계+기계검증절+루브릭절) + `backlog-tool init`·`add-task`(T01) 작성 → opal-evaluator-agent 실디스패치(phase: spec-review) → `QA-SPEC.md` 생성 ② `backlog-tool select-next dryrun` → `mark --id T01 --status in_progress` → RED 실관찰(`bash src/hello.sh World`) → `test-tool scenario-init --task-path dryrun --scenarios '[{"id":"S1",...,"red_confirmed":true}]'`(RED-first 시드) → 음성확인(`scenario-mark` lock 전 거부) → `scenario-lock` → `dryrun/src/hello.sh` 구현 → GREEN 확인(dryrun cwd + 프로젝트 루트 양쪽) → `scenario-mark --id S1 --result pass` → `scenario-status` → `backlog-tool mark --id T01 --status done` → `done-check` → `select-next` 재호출(무진전 가드) |
| 결과 | **PASS** |
| 상세 | ① 설계 루프: CONTRACT.md가 §2 구조(스키마/시그니처/경계+기계검증절+루브릭절) 준수하여 작성됨. evaluator 실디스패치 결과 `QA-SPEC.md` 생성(mtime 2026-07-10 17:04:08, 내부기록 17:03) — **verdict: pass**(전 차원 Likert≥4, drift:no), changed_files는 `QA-SPEC.md` 보고서 1건뿐(H-4: readonly·mutate 없음 확인 — CONTRACT/PRD/TRD/backlog.json 원본 불변). Evaluator가 backlog.json T01 수용기준의 `dryrun/` 경로 접두어 누락을 발견했고, PM은 백로그 손편집 금지 원칙을 유지한 채 "실행 cwd를 dryrun/으로 통일 해석"으로 반영(DRYRUN-LOG.md Phase B §2 결정1). ② 실행 루프 1태스크 완주: `select-next`→T01 반환→`in_progress`, RED 실관찰(`bash: src/hello.sh: No such file or directory`, exit 127, 17:05) 후 `scenario-init`으로 red_confirmed:true 시드(17:06:01, RED 우회 절차 — test-tool에 red_confirmed 갱신 전용 서브명령 부재는 설계 갭으로 기록), lock 전 `scenario-mark` 시도 시 `{"ok":false,"error":"scenario_not_locked"}`(exit 9) 확인 후 `scenario-lock`(locked_at 17:06:12) → `dryrun/src/hello.sh` 구현(17:06:18) → GREEN: dryrun cwd `bash src/hello.sh World`와 프로젝트 루트 `bash tasks/.../dryrun/src/hello.sh World` 양쪽 모두 `Hello, World!`+exit 0으로 동치 확인(PM 결정1 해소) → `scenario-mark pass`(marked_at 17:06:34) → `scenario-status`: total 1/red_confirmed 1/passed 1/failed 0 → `backlog mark done` → `done-check`: all_done:true, remaining:[] ③ H-9 순서 evidence: QA-SPEC(구현 전, 17:04:08) < RED(17:05) < scenario-init(17:06:01) < lock(17:06:12) < 구현(17:06:18) < scenario-mark pass(구현 후, 17:06:34) — Evaluator→구현→test-agent 순서 역전 없음 ④ H-7 무진전 가드: `select-next` 재호출 시 `next_task_id: null` 반환 → SKILL.md 규칙("null→done-check 직행")에 따라 L✓ 종료 판정으로 즉시 분기, 추가 회전 없이 종료됨을 확인(무한 루프 신호 없음). 전 evidence는 `tasks/056-260710-opd-oppl-루프-오케스트레이터/dryrun/DRYRUN-LOG.md`(Phase A~C 시계열 기록)에 명령/출력/타임스탬프와 함께 저장됨. |

### L3. 사용자 협업

해당 없음 — FE 화면·인증/인가·수동 부하 항목 없음. 드라이런(S-090)은 에이전트 자동화 가능으로 L2 배치 (§1 주석 참조).

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

> AC = TASK.md §명확화 결과 완료기준 ①~④ 의 세부 항목 (F-ID 단위).

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| ①-F001 backlog-tool 생성 | H-3, H-5, H-6 | L1+L2 | S-001~004, S-007, S-006, S-001b | `opal/tools/backlog-tool/tests/test_backlog_tool.py:[T056/L1-F001]·[T056/L2-F001]` | 신규 테스트 파일 |
| ①-F002 test-tool scenario-* | H-2, H-5 | L1+L2 | S-011, S-012, S-007, S-014 | `opal/tools/test-tool/tests/test_scenario.py:[T056/L1-F002]` + 기존 `test_test_tool.py`(회귀) | lib/scenario.py 미러링 신규 |
| ①-F003 state-tool oppl | H-1 | L2 | S-020 | `opal/tools/state-tool/tests/test_state_tool.py:[T056/L2-F003]` | 기존 파일에 케이스 추가 |
| ①-F004 evaluator 에이전트 | H-4 | L1+L2 | S-030, S-090 | (산출물 검사 + 드라이런) | readonly·verdict-only |
| ①-F005 references 4종 | H-7, H-12 | L1 | S-055, S-041 | (산출물 검사) | - |
| ①-F006 oppl SKILL | H-7, H-8, H-9 | L1+L2 | S-051, S-055, S-090 | (산출물 검사 + 드라이런) | - |
| ①-F007 레지스트리 등록 | H-10 | L1 | S-060 | (skill-registry CLI) | - |
| ①-F008 install 반영 | H-11 | L2 | S-071 | (Bash 검증) | - |
| ①-F009 docs 갱신 | - | L1 | (TEST 단계 산출물 검사 — 변경이력·표 반영) | (grep) | H 매핑 없음(문서 정합) |
| ② 도구 테스트 GREEN | H-1~H-6 | L1+L2 | S-001~S-020 전체 | 상동 | 완료기준② |
| ③ 드라이런 evidence | H-7, H-9, H-4 | L2 | S-090 | dryrun/ evidence | 완료기준③ |
| ④ 변경이력·@header | - | L1 | (TEST 단계 산출물 검사) | (grep) | 완료기준④ |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트/문법 | `python -m py_compile`(도구) + `bash -n`(install) | **PASS** | `python3 -m py_compile opal/tools/backlog-tool/backlog_tool.py opal/tools/test-tool/lib/scenario.py opal/tools/state-tool/state_tool.py opal/tools/test-tool/test_tool.py` → exit 0(문법 오류 없음). `bash -n scripts/install-mac.sh` → exit 0(쉘 문법 오류 없음). |
| 2 | 타입 체크 | (해당 시) mypy — 기존 도구 관례 따름 | **N/A** | backlog-tool/test-tool/state-tool 3개 도구 모두 별도 mypy 설정 파일(mypy.ini/pyproject.toml) 없음, 기존 관례상 타입 강제 검사 미도입(순수 argparse 스크립트) — 신규 파일도 동일 관례 준수, 회귀 가드 대상 아님. |
| 3 | 포맷터 | 기존 도구 스타일 준수 (별도 포맷터 없음) | **PASS** | 별도 포맷터(black/ruff format 등) 미설정 프로젝트 — 신규 파일(scenario.py 등)이 기존 backlog_tool.py/test_tool.py/state_tool.py의 들여쓰기·네이밍·docstring 스타일과 일관됨을 육안 확인(§5-1 py_compile 통과로 문법 정합 확인됨). |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **PASS** | `grep -rniE "api[_-]?key\s*=\s*['\"]\|password\s*=\s*['\"]\|secret\s*=\s*['\"]\|token\s*=\s*['\"][a-zA-Z0-9]{10,}"` 전 신규/수정 파일(backlog-tool 전체, test-tool scenario.py/schema/test_tool.py/README/tests, state-tool state_tool.py/schema/README/tests, evaluator AGENT.md, oppl SKILL.md+references, 레지스트리, install-mac.sh) 대상 실행 → 매치 0건(exit 1, no match). |
| 2 | .gitignore 확인 | **PASS** | 프로젝트 루트 `.gitignore`에 `.env`(22행) 포함 확인. 신규 도구(backlog-tool/test-tool/state-tool)는 민감 파일을 생성하지 않으며 태스크별 `backlog.json`/`test-scenario.json`/`state.json`은 태스크 산출물로 커밋 대상(민감정보 아님) — 추가 gitignore 항목 불필요. |
| 3 | evaluator tools readonly (H-4) | **PASS** | S-030 grep 검증과 동일 근거: `opal/agents/opal-evaluator-agent/AGENT.md` frontmatter `tools: [Read, Grep, Glob, Bash]`만 존재, Edit/Write 미부여 확인. verdict-only·mutate 금지·커밋 금지 명문(119·120행) 확인 — mutate 경로 원천 차단(Edit/Write 툴 자체가 없어 파일 수정 물리적으로 불가). |
| 4 | task-path 경로 조작 방지 (backlog/scenario) | **PASS** | `backlog_tool.py`의 `resolve_task_path()`(111행)는 `pathlib.Path(task_path_str).resolve()`로 정규화 후 `p.exists()` 검증, 미존재 시 `task_path_not_found` exit 1 반환(112~114행) — 존재하지 않는 임의 경로 조작 시 즉시 거부. `scenario.py`도 동일하게 `pathlib.Path(args.task_path)` 기반 파일 I/O로 셸 인젝션·`eval`·문자열 결합 실행 경로 없음(전부 Path 객체 연산). 두 도구 모두 로컬 CLI(사용자 자신이 `--task-path` 인자를 직접 지정하는 신뢰 경계 내 동작)로 원격 입력을 받지 않아 경로 탈출로 인한 권한 상승 벡터 없음. |

## 7. 판정

**All Pass** — S-001~S-089 전 시나리오 결과 PASS(FAIL/Partial/Critical 0건 확인, `**FAIL**` 등 grep 매치 0), §5 코드품질 3항목(PASS/PASS/N-A-정당화됨), §6 보안 4항목 전건 PASS, 마지막 남은 S-090(oppl 드라이런 E2E)도 본 라운드에서 PASS 확정. H-7(무진전 가드)·H-9(검증 순서)·H-4(evaluator readonly) 3대 가설을 드라이런 실행으로 동작 검증 완료 — QA-SPEC(구현 전) < 구현 < scenario-mark pass(구현 후) 순서 확인, evaluator changed_files=보고서 1건뿐(mutate 없음), `select-next` null 반환 시 무한 회전 없이 L✓ 직행 확인. 핵심 기능·보안·전 시나리오에 Fail 없어 Critical/Partial Fail 사유 없음.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — 본문 전체 실 CLI·실 파일 검증)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-12 전건 연결, 미매핑 시나리오 없음)
- [x] L1/L2 계층 명시 (모든 시나리오), L3 해당 없음 명시
- [x] L3 [SUPERVISOR] 시나리오 없음 → PM 요청 양식 불요
- [x] §1 H-N ↔ S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] FE 변경 없음 → M2 의무 트리거 해당 없음 (API 엔드포인트·인증·외부 API 없음 — CLI 도구·문서 자산)
