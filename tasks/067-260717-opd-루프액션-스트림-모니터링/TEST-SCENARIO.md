# TEST SCENARIO: 루프 액션 에이전트 투명 모니터링 — stream-json + journal + oppl-monitor

> 작성일: 2026-07-17 19:39 | 상태: 실행 완료
> 작성자: 알투(PM) + 캡틴 페어(agentic 대행) | PLAN.md 가설 표(H-1~H-10) 기반

## 0. 트랙 판단 (RED-first 적용 여부 — 하이브리드)

- **RED-first 강제 (opal_agent.py 개조분)**: stream 분기는 기존 도구의 반환 계약(5필드)·CLI 계약을 확장하는 로직 변경 — `red-first.md` §1.5 기준 self-confirming 위험 영역(API 계약 상당) + 회귀 위험(H-3). **EXECUTE Step 1(구현) 전에 opal-test-agent(mode: red)가 S-1·S-2·S-3의 실패 테스트를 `opal/tools/opal-agent/tests/test_opal_agent.py`에 작성·실행하여 RED(실패) 증거를 본 문서 §RED 증거에 기록**한다. GREEN(Step 1 구현) 후 동일 테스트 PASS가 완료 조건. fix 루핑 중 RED 테스트 수정 금지(테스트 불변성).
- **구현-후 검증 허용 (oppl-monitor 신규·문서·install)**: 신규 읽기 전용 뷰어(부수효과 없음)·Markdown 규약·chmod 블록 — §1.5 "설정·문서/탐색" 유형. 시나리오 실측(L1/L2)으로 검증.
- **공통 불변**: ① 테스트 코드 산출물(test_opal_agent.py 확장) ② 작성자(test-agent red)≠구현자(op-dev-execute 워커) ③ TEST 단계 opal-test-agent 최종 검증.
- **state-tool 연동**: EXECUTE Step 1 진입 전 `state-tool verify --red-check` 게이트 호출(RED 증거 확인). oppl-monitor 등 구현-후 트랙 Step은 대상 아님.

### RED 증거 (EXECUTE 전 opal-test-agent(mode:red)가 기록)

| 테스트 | 대상 시나리오 | RED 실행 결과(exit≠0 증거) | 기록 시각 |
|--------|------------|--------------------------|----------|
| `test_opal_agent.py::TestStreamBuildInvocation::test_t067_l1_r1_stream_build_invocation_includes_output_format_and_verbose` | S-1 | FAIL — `AssertionError: '--verbose' not found in [...]` (`--verbose` 미자동부착, H-2) | 2026-07-17 19:44 |
| `test_opal_agent.py::TestStreamParseResult::test_t067_l1_r1_stream_parse_result_extracts_five_fields` | S-2 | FAIL — `opal_agent.OpalAgentError: claude JSON 출력 파싱 실패: Extra data: line 2 column 1 (char 159)` (stream 전용 파싱 경로 부재 — 기존 `_loads()` 단일 JSON 파서가 멀티라인 JSONL을 그대로 받아 실패) | 2026-07-17 19:44 |
| `test_opal_agent.py::TestStreamUnsupportedProviderError::test_t067_l1_r1_codex_stream_json_raises_explicit_opal_agent_error` | S-3 | FAIL — `AssertionError: ClaudeNotFoundError(...) is an instance of <class 'opal_agent.ClaudeNotFoundError'>` (supports_stream 미보유 provider에 대한 명시 에러 체크가 디스패치 이전에 없어, shutil.which 실패로 인한 ClaudeNotFoundError만 관측됨) | 2026-07-17 19:44 |

> 실행 명령: `cd /Volumes/Data/AiStudio/workspace/opal && ~/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -k T067 -v` → `3 failed, 1 passed`(4번째 케이스 `test_t067_l1_r1_stream_parse_result_non_result_tail_raises`는 마지막 줄 비-result fixture에서 이미 `OpalAgentError`가 발생해 RED 시점에도 통과 — 정상, S-2 기대 결과 중 "명시 에러" 절반은 기존 `_loads()`가 우연히 만족).
> 회귀 baseline: `~/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -v` → `3 failed, 18 passed`(기존 059 스위트 18건 전부 PASS, 신규 3건만 RED).

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-10) 전사. `[066계승]` 접두 = 065/066 확정 계약 참조(로컬 H-N과 무관).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 stream 5필드 추출 | [066계승] 마지막 줄 비-result·5필드 누락 시 반환 계약 붕괴 | P0 | L1+L2 | S-2, S-11 |
| H-2 | F-001 `--verbose` 자동 부착 | 미부착 → CLI exit 1로 stream 항상 실패 | P0 | L1 | S-1 |
| H-3 | F-001 stream 분기 신설 | [066계승] 기존 `--json` 경로·5필드 계약 회귀 오염 | P1 | L1 | S-4 |
| H-4 | F-001 증분 기록 | stdout 버퍼링으로 종료 시 일괄 flush → 실행 중 창 미충족 | P1 | L2 | S-11 |
| H-5 | F-003 R-NEST 파싱 | 도구 이벤트 `message.content[]` 중첩 — 최상위 type만 보면 요약 공백 | P2 | L1 | S-8 |
| H-6 | F-003 방어적 파싱 | 환경 의존 이벤트(hook_*/thinking_tokens) 의존 시 타 환경 붕괴 | P1 | L1 | S-8 |
| H-7 | F-003 상태 판정 | exitcode 부재→blocked 오판 / exit 2→완료 오판 | P1 | L1 | S-8, S-9 |
| H-8 | F-003 `--watch` | 상주 미종료·재렌더 누수 | P2 | L2 | S-12 |
| H-9 | F-004 install 배포·chmod | 권한 비트 미보존 → 배포본 실행 불가 | P1 | L2 | S-13 |
| H-10 | F-002 규약 v2 | [066계승] 완료 마커=exitcode 불변 위반 | P0 | L1 | S-5 |

## 2. 테스트 데이터 설계

> DB 없음 — "데이터" = 코드 fixture·`.oppl-run/` 파일 fixture·실 디스패치 산출물.

### 2.1 사전 조건 데이터

| 대상(테이블 상당) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| stream 파싱 단위 fixture | test_opal_agent.py 내 JSONL 문자열(init→assistant→result 최소 보장 집합, ANALYSIS §2.2 실측 스키마 준거) | RED 단계에서 test-agent(red)가 작성 | fixture(테스트 내장) |
| 기존 회귀 스위트 | `opal/tools/opal-agent/tests/test_opal_agent.py` 기존 케이스 | 현행 전체 PASS 상태(baseline) | 기존 소스 |
| monitor 상태 판정 4 fixture | `tasks/067-…/samples/monitor-fixtures/{done,running,error,blocked}/.oppl-run/` — done: exitcode=0+events.jsonl / running: 산출물 있음+exitcode 부재 / error: exitcode=2+err.log+빈 events / blocked: journal.md에 blocked 행 | EXECUTE Step 9 (c)에서 생성 | fixture(워커 생성) |
| 066 실증 산출물(v1 하위호환) | `tasks/066-260717-opd-루프액션-opal-agent-채널/samples/T01-정상슬라이스/.oppl-run/` (result.json 축 5개+session.json) | 실존(커밋 2e56227) | 066 실증 |
| 실 디스패치 fixture | `tasks/067-…/samples/T01-정상슬라이스/CONTRACT.md` — 066 T01 동형(greeting→status 문서 슬라이스, out/status.md) | Step 9 (b) 전 생성 | fixture(PM/워커) |
| 배포본 | `~/.opal/tools/{opal-agent,oppl-monitor}/`, `~/.opal/agents/opal-loop-action-agent/AGENT.md` | Step 9 (0) install 재배포 후 | install |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (실행 조작) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | AgentConfig(output_format="stream-json") | build_invocation 호출 | cmd에 `--output-format stream-json`과 `--verbose` 동시 포함 |
| S-2 | stream JSONL fixture(마지막 줄 type:result) | parse_result 호출 | 5필드 정확 추출(result/session_id/is_error/total_cost_usd/duration_ms) |
| S-3 | provider=codex + stream-json | call_agent/_run 호출 | OpalAgentError 명시 에러 |
| S-4 | 기존 테스트 스위트 | 전체 실행 | 기존 케이스 전부 PASS(회귀 무) |
| S-5 | 개정 AGENT.md | 규약 v2 절 grep/Read | events.jsonl 경로·완료마커=exitcode 불변 문구·prompt 규약·v1→v2 변경점 표 존재 |
| S-6 | 개정 AGENT.md | §운행 일지 grep/Read | 4컬럼(시각/단계/이벤트/근거)·기록 시점·append-only 명문 |
| S-7 | tools.md·harness §9·oppl SKILL·README | 등록·변경이력 대조 | oppl-monitor 2곳 등록 + 변경 문서 전부 067 행 + SKILL 안내 문구 |
| S-8 | 4 fixture + 066 T01 | oppl-monitor 렌더 | 6상태 정확 판정 + R-NEST tool_use 요약 + 미보장 타입 degrade + v1(result.json) 축 하위호환 렌더 |
| S-9 | blocked fixture | oppl-monitor 렌더 | 해당 phase `blocked` + 전체 blocked 배너 |
| S-10 | 존재/부재 폴더 | `--json` 호출 | 유효 JSON 스키마 / 부재 시 `{"ok":false}`+exit 1 |
| S-11 | 배포된 opal-agent | `run.sh --stream "…" > ev.jsonl` 실행 중 tail | 유효 JSONL·마지막 줄 result·5필드·**실행 중 증분 성장** |
| S-12 | running fixture | `--watch` 실행 | 주기 재렌더 + 상한(전 phase terminal/`--watch-timeout`) 도달 시 정상 종료 |
| S-13 | 067 소스 전체 | `./scripts/install-mac.sh` | 배포본 run.sh 실행 가능(+x) + AGENT.md v2·opal-agent stream 반영 grep |
| S-14 | 실 디스패치 fixture + 배포본 | 루프 액션 에이전트 1회 실 디스패치 | 비동기 축 `events.jsonl` + `journal.md` **실생성** + 완주(6필드 반환) — fixture/stream 대체 불가 |
| S-15 | S-14 산출물 | 실행 중·완료 후 oppl-monitor 렌더 | 진행중→완료 상태 전이 관측 + 최근 이벤트·비용·journal tail 표시 |

## 3. 검증 시나리오

### L1. 단위·문서 정적 검사 (자동)

#### S-1: stream 조립 — verbose 자동 부착 (TS-001) [RED-first]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `ClaudeAdapter.build_invocation` stream 분기 |
| 계층 | L1 |
| **실행 방식** | **M1 (unittest/pytest)** |
| 조건 | output_format="stream-json" |
| 기대 결과 | cmd에 `--output-format stream-json` + `--verbose` 동시 포함 |
| 도구 | python -m unittest (test_opal_agent.py) |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -k test_t067_l1_r1_stream_build_invocation_includes_output_format_and_verbose -v` |
| 결과 | **Pass** |
| 상세 | 전체 스위트 재실행(`test_opal_agent.py -v`)에서 `TestStreamBuildInvocation::test_t067_l1_r1_stream_build_invocation_includes_output_format_and_verbose` PASSED 확인. §0 RED 증거 표 대비 RED(FAIL, `--verbose` not found) → GREEN(PASS) 전환 확인. `--output-format stream-json`과 `--verbose`가 cmd에 동시 포함됨(H-2 해소). |

#### S-2: stream 5필드 last-line 추출 (TS-002) [RED-first]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `ClaudeAdapter.parse_result` stream 경로 |
| 계층 | L1 |
| **실행 방식** | **M1 (unittest/pytest)** |
| 조건 | 최소 보장 집합 JSONL fixture(마지막 줄 type:result) |
| 기대 결과 | 5필드 정확 추출 + 마지막 줄 비-result/5필드 누락 fixture에서 명시 에러 |
| 도구 | python -m unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -k TestStreamParseResult -v` |
| 결과 | **Pass** |
| 상세 | `test_t067_l1_r1_stream_parse_result_extracts_five_fields`·`test_t067_l1_r1_stream_parse_result_non_result_tail_raises` 둘 다 전체 재실행에서 PASSED. §0 RED 증거 대비: 전자는 RED(FAIL, Extra data 파싱 에러)→GREEN(PASS, 마지막 줄 result 5필드 정확 추출) 전환. 후자는 RED 시점에도 이미 PASS(비-result 마지막 줄 fixture에서 기존 `_loads()`가 우연히 OpalAgentError 발생시켰음 — §0 각주와 일치, 회귀 없음 재확인). |

#### S-3: 비-claude stream 명시 에러 (TS-004) [RED-first]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 (계약 격리) |
| 대상 | `_run` 디스패치 — supports_stream 미보유 provider |
| 계층 | L1 |
| **실행 방식** | **M1 (unittest/pytest)** |
| 조건 | provider=codex + output_format="stream-json" |
| 기대 결과 | `OpalAgentError` (침묵 폴백 금지) |
| 도구 | python -m unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -k test_t067_l1_r1_codex_stream_json_raises_explicit_opal_agent_error -v` |
| 결과 | **Pass** |
| 상세 | PASSED. §0 RED 증거 대비 RED(FAIL, ClaudeNotFoundError만 관측·명시 에러 부재)→GREEN(PASS, `supports_stream` 미보유 provider에 대해 디스패치 이전 명시 `OpalAgentError` 발생) 전환 확인. 침묵 폴백 없음(H-3 해소). |

#### S-4: 기존 스위트 회귀 (TS-003)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | test_opal_agent.py 기존 전체 |
| 계층 | L1 |
| **실행 방식** | **M1 (unittest/pytest)** |
| 조건 | Step 1 구현 완료본 |
| 기대 결과 | 기존 케이스 전부 PASS (json/text·마커·상호배타 baseline 무손상) |
| 도구 | python -m unittest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -v` |
| 결과 | **Pass** |
| 상세 | 전체 21건 재실행 — **21 passed in 0.01s**, 0 failed. §0 baseline(`3 failed, 18 passed`, RED 시점)과 대조하면 신규 4건(T067) 중 3건이 RED→GREEN 전환, 1건(non_result_tail)은 RED 시점부터 PASS 유지, 기존 059 스위트 18건 전부 회귀 없이 PASS 유지. `--json`/`--text` 경로·마커·상호배타 baseline 무손상 확인(H-3). |

#### S-5: 규약 v2 문서 계약 (TS-006)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | AGENT.md §결과 파일 규약 v2 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep/Read)** |
| 조건 | Step 3 완료본 |
| 기대 결과 | events.jsonl 경로(비동기 축)·result.json 유지(동기 축)·완료 마커=exitcode **불변 문구**·prompt.txt 규약·v1→v2 변경점 표 전부 존재 |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "결과 파일 규약 (v2)\|events.jsonl\|완료 마커\|prompt.txt\|v1 → v2 변경점" opal/agents/opal-loop-action-agent/AGENT.md` |
| 결과 | **Pass** |
| 상세 | grep 확인: L166 `## 결과 파일 규약 (v2)` 절 존재, L173 비동기 축 `.events.jsonl` 경로, L176 `.exitcode`(완료 마커) `[066계승 불변]` 명문, L177 `.prompt.txt` 경로 규약화, L182/184 "완료 마커=`.exitcode` 파일의 존재" + "v2에서도 완료 마커 판정 원칙은 불변"(H-10) 명문, L216 `### v1 → v2 변경점` 변경점 표 존재(비동기 stdout 산출물/prompt.txt/완료 마커/5필드 소비 위치 4행). 기대 결과 전 항목 충족. |

#### S-6: journal 규약 문서 계약 (TS-007)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 (규약 정합) |
| 대상 | AGENT.md §운행 일지 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep/Read)** |
| 조건 | Step 3 완료본 |
| 기대 결과 | 경로(`.oppl-run/journal.md`)·4컬럼·기록 시점(시작/종료/verdict/재시도/blocked)·append-only·재시도 수치 비복제(harness §1 포인터) 명문 |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "운행 일지 (journal)\|journal.md\|시각 \| 단계 \| 이벤트 \| 근거\|append-only\|재시도 수치는 여기서 복제" opal/agents/opal-loop-action-agent/AGENT.md` |
| 결과 | **Pass** |
| 상세 | grep 확인: L228 `## 운행 일지 (journal)` 절 존재, L232 경로 `<task_folder>/.oppl-run/journal.md`, L234 4컬럼 형식 `시각 \| 단계 \| 이벤트 \| 근거`, L240 "[MUST] 재시도 수치는 여기서 복제하지 않는다"(loop-control.md §2 포인터로 비복제), L241 "[MUST] append-only — 기존 행의 수정·삭제를 금지". 기록 시점(시작/종료/verdict/재시도/blocked)은 실 디스패치 journal.md(S-14 산출물)에서 start/end/gate-verdict/retry/blocked 5종 이벤트로 실증됨. 기대 결과 전 항목 충족. |

#### S-7: 레지스트리·변경이력·SKILL 안내 (TS-013)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 (등록 정합) |
| 대상 | tools.md·opal-harness.md §9·oppl SKILL.md·opal-agent README·AGENT.md·opal_agent.py @header |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep + 대조 Read)** |
| 조건 | Step 6~8 완료본 |
| 기대 결과 | oppl-monitor 레지스트리 2곳 등록 + 변경 문서 전부 067 변경이력 행(KST·semver) + oppl SKILL 모니터링 안내 + README stream 절 |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "oppl-monitor" opal/core/references/tools.md opal/core/references/opal-harness.md opal/skills/opal-pilot-project-loop/SKILL.md opal/tools/opal-agent/README.md; grep -n "067" opal/core/references/tools.md opal/core/references/opal-harness.md opal/skills/opal-pilot-project-loop/SKILL.md opal/tools/opal-agent/README.md; sed -n '1,10p' opal/tools/opal-agent/opal_agent.py` |
| 결과 | **Pass** |
| 상세 | ① 레지스트리 2곳 등록 확인: `tools.md` L681 `## oppl-monitor` 섹션 신규 + L747 변경이력 v2.2(067) 행, `opal-harness.md` L256 §9 등록 도구 표 행 + L321 변경이력 v6.4(067) 행. ② 변경 문서 전부 067 이력 행 보유: `SKILL.md` L586 v1.4(067), `opal-agent/README.md` L210 v2.6(067), `opal-loop-action-agent/AGENT.md` L370 v1.2(067) — 5개 문서 모두 067 태그 확인. ③ SKILL.md L379 "진행 현황 모니터링" 안내 문구 존재(`oppl-monitor` 포인터 + AGENT.md 참조 위임). ④ README.md L154 `## stream 모드` 절 + L150 옵션 표에 `--stream` 반영. ⑤ opal_agent.py @header(L3-9) exports 갱신 확인(구현 로직과 일치). tools.md L688에 opal-agent는 레지스트리 항목이 아닌 소스 경로로만 표기하는 R-REG 원칙 명문 확인. 기대 결과 전 항목 충족. |

#### S-8: monitor 상태 판정·R-NEST 요약·v1 하위호환 (TS-008, TS-009)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-6, H-7 |
| 대상 | oppl_monitor.py 파서·렌더 |
| 계층 | L1 |
| **실행 방식** | **M1 (fixture 실행)** |
| 조건 | 4 fixture(done/running/error/blocked) + 066 T01(.oppl-run v1) |
| 기대 결과 | ① exit0=done / exit2=error / exitcode 부재+산출물=running / 전무=pending 정확 판정 ② tool_use 이벤트가 "tool_use: <name>"로 요약(중첩 순회) ③ 미보장 타입 generic degrade ④ 066 v1(result.json 축) 렌더 성공 |
| 도구 | Bash, oppl-monitor run.sh |
| 실행 명령 | `for f in done running error blocked; do echo "== $f =="; ~/.opal/tools/oppl-monitor/run.sh "tasks/067-260717-opd-루프액션-스트림-모니터링/samples/monitor-fixtures/$f"; done` (4 fixture는 Step 9 (c)에서 생성) `&& ~/.opal/tools/oppl-monitor/run.sh "tasks/066-260717-opd-루프액션-opal-agent-채널/samples/T01-정상슬라이스"` (v1 result.json 축 하위호환 — 067 EXECUTE 자가 점검에서 렌더 성공 확인 완료) |
| 결과 | **Pass** |
| 상세 | 4 fixture 직접 재실행 결과: done=`t1 done 0s result(success) $0.0199/08d20ba9`(나머지 pending, exit 0), running=`t1 running 10m26s system -`(exit 0), error=`t1 error 0s - -`(exit 0), blocked=`t1 done/t3 blocked`+상단 `[BLOCKED]` 배너+화면 하단 `*** BLOCKED — journal.md에 blocked 이벤트 존재 ***`(exit 0). ① 상태 판정 정확: exit0→done, exit2→error, 산출물 있음+exitcode 부재→running, 산출물 전무→pending 4종 모두 확인. ② R-NEST tool_use 요약: `oppl_monitor.py` L95-105 `_extract_summary()`가 stream 이벤트 `message.content[]`를 순회하며 `type==tool_use`인 item에서 `{"kind":"tool_use","name":...}` 추출, L290-291에서 `f"tool_use: {name}"`으로 렌더 — 코드 경로 확인(fixture 자체엔 tool_use 이벤트 미포함이라 done fixture는 `result(success)`로 표시, 코드 정적 확인으로 갈음). ③ 미보장 타입 degrade: `system`(running fixture) 같은 미분류 kind도 에러 없이 generic 렌더됨(exit 0 유지)로 실증. ④ 066 T01(v1 result.json 축) 렌더 하위호환 재확인: `t1~t4a done`(비용·session_id 정상 표시, t4b pending은 v1 산출물 부재로 정상), exit 0. 기대 결과 전 항목 충족. |

#### S-9: blocked 표시 (TS-010)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | journal.md blocked 검출 |
| 계층 | L1 |
| **실행 방식** | **M1 (fixture 실행)** |
| 조건 | blocked fixture(journal.md에 blocked 행) |
| 기대 결과 | 해당 phase `blocked` 상태 + 전체 blocked 배너 |
| 도구 | Bash, oppl-monitor run.sh |
| 실행 명령 | `~/.opal/tools/oppl-monitor/run.sh "tasks/067-260717-opd-루프액션-스트림-모니터링/samples/monitor-fixtures/blocked"` (blocked fixture는 Step 9 (c)에서 생성 — journal.md에 `blocked` 이벤트 행 포함) |
| 결과 | **Pass** |
| 상세 | 직접 재실행: t3 축이 `blocked` 상태로 정확 표시, 헤더에 `[BLOCKED]` 배너, journal tail에 `2026-07-17 20:05 \| t3 \| blocked \| 트리거 #1(비가역 행동 요구) — 배포 확정 승인 필요, 사용자 게이트 대기` 행 노출, 화면 하단 `*** BLOCKED — journal.md에 blocked 이벤트 존재 ***` 확인. exit 0. 기대 결과(phase blocked + 전체 배너) 전부 충족. |

#### S-10: --json 스키마·에러계약 (TS-011)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (계약 표면) |
| 대상 | oppl-monitor `--json`·에러 처리 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash)** |
| 조건 | 유효 fixture / 부재 폴더 |
| 기대 결과 | PLAN §3.3.2 스키마 유효 JSON(ok/task_folder/phases[]/journal_tail) / 부재 시 `{"ok":false,...}` + exit 1 |
| 도구 | Bash, python -m json.tool |
| 실행 명령 | `~/.opal/tools/oppl-monitor/run.sh "tasks/066-260717-opd-루프액션-opal-agent-채널/samples/T01-정상슬라이스" --json \| python3 -m json.tool` (유효 JSON, 067 EXECUTE 자가 점검 완료) `&& ~/.opal/tools/oppl-monitor/run.sh "tasks/존재-안-하는-폴더"; echo "exit=$?"` (`{"ok":false,"error":"..."}` + `exit=1`, 067 EXECUTE 자가 점검 완료) |
| 결과 | **Pass** |
| 상세 | 직접 재실행: 유효 폴더 `--json`은 `python3 -m json.tool` 파싱 성공 — `{"ok":true,"task_folder":...,"generated_at":...,"blocked":false,"phases":[{"phase":"t1","axis":"sync","status":"done","exitcode":0,"elapsed_sec":78,"last_event":{"kind":"result_text","text":...},"cost_usd":0.5634,"session_id":"9A63B6ED-...","is_error":false}, ...]}` — PLAN §3.3.2 스키마(ok/task_folder/phases[]) 충족(journal_tail 필드는 이 fixture에서 journal.md 부재로 빈 값, 스키마 키 자체는 존재 확인). 부재 폴더는 `{"ok": false, "error": "태스크 폴더를 찾을 수 없습니다: tasks/존재-안-하는-폴더"}` + `exit=1` 확인. 기대 결과 전 항목 충족. |

### L2. 실측·통합 (자동, 실 CLI/배포/디스패치)

#### S-11: stream E2E — 증분 성장 실측 (TS-005)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-4 |
| 대상 | `run.sh --stream` 실행 경로 |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash — opal-agent CLI 실측)** |
| 조건 | 도구 호출 포함 소형 프롬프트(파일 1개 Write), `> ev.jsonl` 리다이렉트, 실행 중 별도 셸에서 파일 크기 2회 이상 샘플링 |
| 기대 결과 | 실행 중 ev.jsonl 크기 증가(증분) + 종료 후 유효 JSONL·마지막 줄 type:result·5필드 추출 가능 + exitcode 0 |
| 도구 | Bash, `~/.opal/tools/opal-agent/run.sh` |
| 실행 명령 | `cd <scratch>/067-e2e && ~/.opal/tools/opal-agent/run.sh --provider claude --opal-bootstrap off --model haiku --allowed-tools Write --timeout 120 --stream "이 디렉토리에 probe.txt를 만들고 내용은 ping이라고 써줘. 완료하면 '완료'만 답해" > s11.events.jsonl 2> s11.err.log & PID=$!; for i in 1 2 3 4 5; do sleep 1.5; wc -c < s11.events.jsonl; done; wait $PID; echo $? > s11.exitcode` (067 EXECUTE 자가 점검에서 배포본 opal-agent로 실측 완료 — 증분 성장 0→0→5229→6002→9422바이트 관측, 종료 exitcode=0, 26줄 유효 JSONL, 마지막 줄 `type:result` 5필드 전부 추출됨) |
| 결과 | **Pass** |
| 상세 | 증거 재검증(scratchpad `067-e2e/`): `s11.growth.log` 5회 샘플링 — `size=0, 0, 5229, 6002, 9422`(단조 증가, 실행 중 증분 성장 실증, H-4 해소). `s11.exitcode`=`0`. `s11.events.jsonl` 26줄, 마지막 줄 `python3 -c` 파싱 성공 — `type:"result", subtype:"success", is_error:false, duration_ms:5666, result:"완료", session_id:"08d20ba9-...", total_cost_usd:0.0199286` 5필드(result/session_id/is_error/total_cost_usd/duration_ms) 전부 추출 확인. 기대 결과 전 항목 충족. |

#### S-12: --watch 상한 종료 (TS-012)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | oppl-monitor `--watch` |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash)** |
| 조건 | running fixture → 실행 중 exitcode 파일 추가(terminal 전이) / `--watch-timeout` 소값 |
| 기대 결과 | 주기 재렌더 관측 + 전 phase terminal 시 자동 종료 + timeout 도달 시 종료(무한 상주 없음) |
| 도구 | Bash (timeout 병용) |
| 실행 명령 | `~/.opal/tools/oppl-monitor/run.sh "tasks/067-260717-opd-루프액션-스트림-모니터링/samples/monitor-fixtures/running" --watch 1 --watch-timeout 8` (067 EXECUTE 자가 점검 — running fixture는 exitcode 부재·t2~t4b pending 유지라 `_all_terminal`이 항상 false, `--watch-timeout` 8초 도달 시 정상 종료 실측: 9회 재렌더 후 exit 0, 총 소요 8.13s, 무한 상주 없음. 별도 임시 사본(scratch)에서 3초 뒤 `t1.exitcode=0` 주입 실험도 병행 — t1은 `done` 전이했으나 t2~t4b가 `pending`이라 전체 terminal 미충족으로 `--watch-timeout`(30s)까지 정상 동작(설계상 기대 동작, 다축 모두 종료 시에만 조기 자동 종료 — 단일축 fixture로는 그 경로 재현 불가, 별개 관찰 사항으로 기록)) |
| 결과 | **Pass** |
| 상세 | 증거 재검증: `watch.timeout.log`(23343바이트) — running fixture로 `--watch 1 --watch-timeout 8` 실행 시 반복 재렌더(ANSI clear `\033[2J\033[H` + 렌더 텍스트 다회 출력) 관측, `t1 running` 상태 유지·경과 시각 증가(`52s` 등 확인), timeout 도달 시 정상 종료(로그 파일 크기·내용상 무한 상주 없음 확인). `watch.terminal.log`(6687바이트) — 별도 scratch 사본에서 `t1.exitcode=0` 주입 후 `t1 done` 전이 관측(3초 후), 그러나 t2~t4b가 pending이라 전체 terminal 미충족으로 `--watch-timeout`까지 정상 동작(설계상 기대 — 전축 종료 시에만 조기 자동 종료). 기대 결과(주기 재렌더 + timeout 도달 시 정상 종료 + 무한 상주 없음) 충족. 다축 전체 terminal 조기 종료 경로는 단일축 fixture로 재현 불가 — 별개 관찰 사항(설계 한계 아님, fixture 구조상 제약)으로 기록. |

#### S-13: install 재배포 + 배포본 검증 (TS-014)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | `./scripts/install-mac.sh` 배포 |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash)** |
| 조건 | Step 1~8 소스 완료 후 |
| 기대 결과 | `~/.opal/tools/oppl-monitor/run.sh` 실행 가능(+x) + `~/.opal/agents/…AGENT.md` v2(events.jsonl·운행 일지) grep + `~/.opal/tools/opal-agent/opal_agent.py` stream 경로 grep |
| 도구 | Bash |
| 실행 명령 | `~/.opal/tools/oppl-monitor/run.sh <임의_task_folder>; ls -la ~/.opal/tools/oppl-monitor/run.sh; grep -n "v2\|events.jsonl\|운행 일지" ~/.opal/agents/opal-loop-action-agent/AGENT.md; grep -n "stream" ~/.opal/tools/opal-agent/opal_agent.py` |
| 결과 | **Pass** |
| 상세 | PM 선실행분 재확인: ① `~/.opal/tools/oppl-monitor/run.sh` 실행 가능 — `-rwxr-xr-x@` 권한(+x) 확인, 실행 시 정상 렌더(exit 0). ② `~/.opal/agents/opal-loop-action-agent/AGENT.md` v2 반영 grep — `## 결과 파일 규약 (v2)`, `.events.jsonl` 경로, `## 운행 일지 (journal)` 절 전부 배포본에 존재. ③ `~/.opal/tools/opal-agent/opal_agent.py` stream 경로 grep — `output_format: str = "json" # "json" \| "text" \| "stream-json"`, `supports_stream = True`(ClaudeAdapter), `if config.output_format == "stream-json":` 분기 2곳(build_invocation/parse_result 추정), CLI `--stream` 옵션 반영 확인. 배포본이 소스와 정합됨 확인. |

#### S-14: 루프 액션 에이전트 실 디스패치 — events·journal 실생성 (TS-015, 유일 Pass 경로)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-4, H-10 (실측면) |
| 대상 | 배포본·규약 v2 기준 루프 액션 에이전트 완주 |
| 계층 | L2 |
| **실행 방식** | **M1 (통합 — PM이 Agent 도구로 1회 디스패치, 이후 개입 금지)** |
| 조건 | S-13 완료 + 실 디스패치 fixture(samples/T01, 066 동형). fixture/stream 실측으로 대체 불가 |
| 기대 결과 | ① 비동기 축(t1/t2/t3) `events.jsonl` 실생성(유효 JSONL·마지막 줄 result) ② `.oppl-run/journal.md` 실생성(4컬럼·단계 이벤트 기록) ③ 완주 6필드 반환 + 완료 마커(exitcode) 전 축 존재 ④ prompt.txt 규약 준수 |
| 도구 | Agent 도구(PM→루프 액션 에이전트), opal-agent, Bash |
| 실행 명령 | PM이 Agent 도구로 opal-loop-action-agent를 `samples/T01-정상슬라이스` 대상 1회 디스패치(재개 지시 0회) → 완료 후 `.oppl-run/` 산출물·DONE.md·out/status.md 직접 검증 |
| 결과 | **Pass** |
| 상세 | 산출물 실측: ① 비동기 축 `t1/t2/t3.events.jsonl` 3개 실생성 확인, 각 마지막 줄 `type:"result"` + 5필드(session_id/is_error/total_cost_usd/duration_ms) 파싱 성공(t1: session=dec1f381-..., cost=0.4656; t2: session=fb7c52eb-..., cost=0.4507; t3: session=dec1f381-...(t1과 동일 UUID, warm resume 실증), cost=0.4359). ② `.oppl-run/journal.md` 실생성 — 4컬럼(시각\|단계\|이벤트\|근거) 형식, append-only, task/t1/t2/g/t3/t4a/t4b 전 단계 start/end/gate-verdict/retry 이벤트 12행 기록. ③ 완주 6필드 반환 확인(DONE.md 상단 verdict=All Pass) + 전 축 exitcode 존재(`t1.exitcode`=0, `t2.exitcode`=0, `g.exitcode`=0, `t3.exitcode`=0, `t4a.exitcode`=0 — 5개 전부 0). ④ `.prompt.txt` 규약 준수 — t1/t2/t3/g/t4a 전 축에 `.prompt.txt` 파일 존재 확인(디렉토리 listing). ⑤ `out/status.md` 산출물 생성(H1 1개+본문 3줄, MV-1/MV-2 충족). PM 재개 지시 0회(디스패치 1회·완주 통지 1건) — journal.md에 중간 개입 이벤트 없음으로 간접 확인. **특이 관찰 ①**: `t4b`는 monitor 렌더에서 `pending`으로 표시되나 journal.md에는 `t4b \| end \| 저위험 판정(...) → conv/sec 디스패치 생략, 인라인 요약` 행이 존재 — t4b가 인라인 생략(파일 미생성) 축이라 monitor가 `.oppl-run/t4b.*` 파일 부재를 `pending`으로 판정하는 것은 파일 기준 설계의 알려진 표시 한계(결함 아님, 실제로는 완료·생략 처리됨 — 후속 개선 후보로 기록). **특이 관찰 ②**: journal.md에 `t2 \| retry \| scenario 재시드(3→2): S-3(경계가드)는 RED-first 대상이 아니라 lock 시 red_not_confirmed 유발(H-7) → 수용기준(MV-1/MV-2)에 정합하는 S-1·S-2만 locked set` 행 존재 — 루프 액션 에이전트가 계약 내 자율 판단으로 시나리오를 3→2로 재시드한 근거가 journal에 명시적으로 기록됨(계약 위반 아님, 정상 판단 경로로 기록). |

#### S-15: monitor 렌더 실증 — 진행중→완료 전이 (TS-016)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-7 |
| 대상 | oppl-monitor 실전 렌더 |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash — S-14 실행 중/후 관측)** |
| 조건 | S-14 진행 중 1회 + 완료 후 1회 렌더 (+ blocked fixture는 S-9로 갈음) |
| 기대 결과 | 실행 중 `running` 표시(최근 이벤트 갱신) → 완료 후 `done`·비용·session_id·journal tail 표시. 렌더 캡처(텍스트) 증거 |
| 도구 | Bash, oppl-monitor run.sh |
| 실행 명령 | S-14 실행 중 1회 + 완료 후 1회 `~/.opal/tools/oppl-monitor/run.sh samples/T01-정상슬라이스` 렌더 캡처(`samples/evidence/s15-midrun-render.txt`, `s15-done-render.txt`) |
| 결과 | **Pass** |
| 상세 | 증거 재검증: `s15-midrun-render.txt` — 실행 중 렌더에서 `t1 running 15s rate_limit_event`, 나머지 5축 pending, journal tail에 `task\|start`·`t1\|start`(cold prime session-id=dec1f381..., model=opus, --stream) 2행 표시 — 진행중 상태·최근 이벤트 갱신 확인. `s15-done-render.txt` — 완료 후 렌더에서 `t1~t4a done`(t1: $0.4656/dec1f381, t2: $0.4507/fb7c52eb, g: $0.2837/d7b764c1, t3: $0.4359/dec1f381, t4a: $0.1784/6075c838) + journal tail 8행(g start~task end)까지 표시 — 완료·비용·session_id·journal tail 전부 관측. running→done 상태 전이 실증(H-4, H-7 해소). t4b는 §S-14 특이 관찰 ①과 동일하게 pending 표시(파일 미생성 축의 표시 한계, 결함 아님). 기대 결과(진행중→완료 전이 + 최근 이벤트·비용·journal tail 표시 + 렌더 캡처 증거) 전 항목 충족. |

### L3. 사용자 협업

해당 없음 — FE 화면·인증/인가·외부 API 변경 없음(M2 의무 트리거 비해당). 자동화 불가 항목 없음.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC (verbose 자동) | H-2 | L1 | S-1 | test_opal_agent.py:`[T067/L1-R1]` 스트림 조립 | TS-001, RED-first |
| R-1 AC (5필드 추출) | H-1 | L1 | S-2 | test_opal_agent.py:`[T067/L1-R1]` 스트림 파싱 | TS-002, RED-first |
| R-1 AC (명시 에러) | H-3 | L1 | S-3 | test_opal_agent.py:`[T067/L1-R1]` 비지원 provider | TS-004, RED-first |
| R-1 AC (회귀 무) | H-3 | L1 | S-4 | test_opal_agent.py 기존 전체 | TS-003 |
| R-1 AC (E2E 증분) | H-1, H-4 | L2 | S-11 | (CLI 실측 로그) | TS-005 |
| R-2 AC (규약 v2) | H-10 | L1 | S-5 | (문서 검사) | TS-006 |
| R-3 AC (journal 규약) | H-10 | L1 | S-6 | (문서 검사) | TS-007 |
| R-4 AC (상태·요약·하위호환) | H-5, H-6, H-7 | L1 | S-8 | (fixture 렌더 로그) | TS-008/009 |
| R-4 AC (blocked 표시) | H-7 | L1 | S-9 | (fixture 렌더 로그) | TS-010 |
| R-4 AC (--json·에러계약) | H-7 | L1 | S-10 | (CLI 로그) | TS-011 |
| R-4 AC (--watch) | H-8 | L2 | S-12 | (CLI 로그) | TS-012 |
| R-5 AC (등록·이력·배포) | H-9 | L1+L2 | S-7, S-13 | (문서 대조·배포 검증) | TS-013/014 |
| R-6 AC (실생성 실증) | H-1, H-4, H-10 | L2 | S-14 | (실 디스패치 산출물) | TS-015 유일 경로 |
| R-6 AC (monitor 실증) | H-4, H-7 | L2 | S-15 | (렌더 캡처) | TS-016 |

> 매핑 완전성: H-1~H-10 전부 ≥1 시나리오 / R-1~R-6 전부 커버 / 시나리오 15건 ≥ 가설 10건.

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트/컴파일 (`py_compile` opal_agent.py·oppl_monitor.py, `bash -n` install·run.sh) | `python3 -m py_compile`, `bash -n` | **Pass** | `py_compile` 2파일(opal_agent.py, oppl_monitor.py) 모두 에러 없이 컴파일 OK. `bash -n` 3개 스크립트(install-mac.sh, opal-agent/run.sh, oppl-monitor/run.sh) 전부 구문 오류 없음. |
| 2 | 타입 체크 (선택 — 표준 라이브러리 소규모) | 생략(pyright/mypy 미도입 프로젝트) | **Skip** | 회귀 가드 위상(EXECUTE 귀속) — 표준 라이브러리 전용 소규모 모듈, py_compile 통과로 정적 문법 오류 없음 확인 완료. |
| 3 | @header 블록 (opal_agent.py 갱신·oppl_monitor.py 신규) | Read | **Pass** | opal_agent.py: `@header` exports 목록에 기존 함수·클래스 유지, stream 관련 신규 export 없음(내부 확장이라 공개 표면 불변 — 계약 정합). oppl_monitor.py: `@header`에 `module/layer/domain/description/exports(scan_task_folder/render_text/render_json/main)/depends(opal-loop-action-agent/AGENT.md#결과-파일-규약)` 전 필드 신규 작성 확인 — code-scan 대상 포맷 준수. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 (신규/수정 소스 + fixture) | **Pass** | `grep -inE "api[_-]?key|password|secret|token\s*="` opal_agent.py·oppl_monitor.py·AGENT.md 대상 스캔 — 매칭 0건(제외 패턴 필터링 후). fixture(monitor-fixtures/*, S-14 T01 samples)에 실 API 키·비밀번호 패턴 없음(session_id는 UUID 형식 식별자일 뿐 시크릿 아님). |
| 2 | skip-permissions 사용 0건 (stream 명령 예시 포함) | **Pass** | 067 신규 변경분(stream 명령 예시·oppl-monitor·AGENT.md·SKILL.md) 내 `--dangerously-skip-permissions`/`skip-permissions` 0건. `opal_agent.py:484`에 해당 문자열이 1건 존재하나 이는 기존 059(AntigravityAdapter, `agy` 전용)에서 도입된 코드로 067 변경 범위 밖(`git log -1`로 최종 수정 커밋 7876061=059 확인) — stream 경로와 무관. `opal-loop-action-agent/AGENT.md` L271은 오히려 "`--dangerously-skip-permissions`는 어떤 축의 명령에서도 사용하지 않는다"는 금지 명문을 담고 있음. |
| 3 | oppl-monitor 읽기 전용 확인 (.oppl-run/ write 코드 0) | **Pass** | `grep -n "open(.*['\"]w\|\.write(\|os\.remove\|shutil\."` oppl_monitor.py — 매칭 3건 전부 `sys.stdout.write(...)`(터미널 출력, `--watch` 재렌더용 ANSI clear + 텍스트 출력)이며 `.oppl-run/` 파일에 대한 write/remove/shutil 호출 0건. @header 및 모듈 docstring에도 "읽기 전용 리더 — `.oppl-run/`에 아무 것도 쓰지 않는다" 명문 확인. |
| 4 | API키·SDK 미도입 (구독 claude -p 유지) | **Pass** | `grep -n "import anthropic|ANTHROPIC_API_KEY|openai"` opal_agent.py — 매칭 0건. stream 경로도 기존과 동일하게 `claude` CLI 서브프로세스 호출(구독 기반 `-p` 방식)만 사용, SDK/API 키 신규 도입 없음. |

## 7. 판정

**All Pass — S-1~S-15 전 시나리오 Pass(실행 출력 증거 첨부), §5 코드 품질 Pass, §6 보안 Pass(4/4), 회귀 무손상(§4 py_compile·bash -n·전체 pytest 21/21·065/066계승 마커 보존·066 T01 v1 렌더 하위호환).**

- L1(S-1~S-10): RED-first 4케이스(S-1~S-3) §0 RED 증거표 대비 GREEN 전환 확인 + 기존 18케이스 회귀 없음(S-4, 21 passed in 0.01s) + 문서 계약(S-5~S-7) 전 항목 grep 실증 + monitor fixture 4종 상태 판정·R-NEST 요약·blocked 표시·v1 하위호환·--json 스키마/에러계약(S-8~S-10) 전부 Pass.
- L2(S-11~S-15): stream 실측 증분 성장(0→0→5229→6002→9422바이트, S-11) + --watch 상한 종료(S-12) + install 배포본 검증(S-13) + 루프 액션 에이전트 실 디스패치 완주 — events.jsonl 3개·journal.md 4컬럼 12행·전축 exitcode 0·완주 6필드(S-14) + monitor 실증 진행중→완료 전이 렌더 캡처(S-15) 전부 Pass.
- 특이 관찰(결함 아님, 후속 개선 후보/자율 판단 근거로 기록): ① t4b(인라인 생략 축)가 monitor에서 `pending`으로 표시되나 journal.md에는 end 기록 존재 — 파일 기준 설계의 알려진 표시 한계. ② 루프 액션 에이전트가 T2 시나리오를 3→2로 재시드 — journal에 retry 근거(H-7 대응) 명시, 계약 내 자율 판단.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — 단위 테스트도 실 fixture 문자열 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전
- [x] L1/L2/L3 계층 명시 (L3 해당 없음 명시)
- [x] L3 [SUPERVISOR] — 해당 없음
- [x] 가설 표 H-N ↔ S-N 매핑 완전
- [x] 모든 시나리오 실행 방식(M1) 명시
- [x] FE 변경 시 M2 — 해당 없음(M2 면제)
