# TASK: 루프 액션 에이전트 투명 모니터링 — opal-agent stream-json 개조 + journal 규약 + oppl-monitor 도구

> 작성일: 2026-07-17 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 (066 후속 — 캡틴 확정 "066 CLOSE → 067 stream+journal" + "oppl --monitor 등 명령어로 진행상황 일목요연" 요구)
> 출력: TASK.md

## 작업 목표

루프 액션 에이전트의 내부 opal-agent 채널 실행을 **투명하게 관측 가능**하게 만든다: ① opal-agent에 stream-json 모드를 추가해 워커의 도구 이벤트를 기계 방출(events.jsonl)로 기록하고, ② 루프 액션 에이전트 자신의 판단을 journal 규약으로 남기며, ③ 신규 OPAL 도구 `oppl-monitor`로 캡틴/PM이 진행 상황을 한 명령으로 일목요연하게 본다.

## 배경

066에서 내부 4축이 opal-agent 채널로 전환되어 3-분리 캡처(result.json/err.log/exitcode)가 생겼으나, "완료 후 증거"이지 "실행 중 창"이 아니다 — 루프 액션 에이전트는 서브에이전트라 이중 블랙박스(PM↔루프 액션 중간 침묵 + 루프 액션↔워커 진행 비가시)다. 캡틴 요구: 중간 진행·발생 사건·주고받은 메시지가 투명하게 보이고, 명령어 하나로 현황판을 볼 것. 근거: `memory/후속_067_stream_json_journal.md`, `tasks/066-260717-opd-루프액션-opal-agent-채널/DONE.md` §후속.

## 배경 분석 (대화에서 도출)

- **stream-json이 경량 3종 중 2종을 상위 호환 대체**: 워커 자가 보고(heartbeat)는 누락 가능하나, claude CLI `--output-format stream-json`은 실행·파일 읽기/쓰기 등 모든 도구 이벤트를 기계적으로 방출 — 완전판. prompt 보존은 스트림 메시지 이벤트에 포함되거나 덤프 1줄로 흡수. **journal만은 대체 불가** — 루프 액션 에이전트의 게이트 판단·재시도 사유·단계 전환은 CLI(워커) 밖의 행동이라 스트림에 없다.
- **opal-agent 현 구조**: `_run()`이 `subprocess.run`(블로킹) 전용, stdout 종료 시점 일괄 파싱(`opal_agent.py:558-618`, 066 ANALYSIS §1.5~1.6). 스트리밍 실행(증분 기록)은 개조 필요. claude 어댑터의 5필드 보장 계약(result/session_id/is_error/total_cost_usd/duration_ms)은 stream의 최종 result 이벤트에서 추출해 유지해야 한다. stream-json 이벤트 스키마는 실측 검증 필요(066 리스크 R-H 유형).
- **관측 데이터는 파일 SSOT**: 066 규약이 `.oppl-run/` 파일 기반이므로, 뷰어(모니터)는 실행 프로세스와 독립적으로 파일만 읽어 렌더 가능 — "실행 중 에이전트 직접 질의" 채널은 릴레이 마찰(065 #12d·#12e) 재발 소지로 배제(캡틴 합의: 파일 경유, 질의 응답은 알투가 파일 읽고 답변).
- **066 실증 관측치**: 축 5개(t1/t2/g/t3/t4a) 3-분리 + session.json + prompt.txt(비규약 자발)가 실제 생성됨 — 뷰어 입력 데이터 형태가 이미 실존.

## 확정된 설계 방향 (대화에서 합의)

1. **stream-json 개조 + journal 규약 2건 구성** — 경량 3종(heartbeat·prompt 규약·journal) 중 heartbeat/prompt는 stream이 상위 호환이라 건너뜀 (캡틴 확정, 066 CLOSE 시).
2. **monitor는 신규 OPAL 도구 `oppl-monitor`** — `~/.opal/tools/oppl-monitor/run.sh <task_folder> [--watch] [--json]` 형태, 기존 도구 패턴(run.sh 래퍼·JSON 출력) 준수 (캡틴 확정, AskUserQuestion).
3. **stream은 opt-in 모드** — 기존 `--json`(일괄) 경로·5필드 계약 하위호환 유지, 루프 액션 에이전트 채널이 stream 모드를 채택하는 형태로 규약 v2 개정.
4. **질의 채널은 파일 경유** — 실행 중 서브에이전트 직접 질의 배제, 알투(PM)가 journal/events를 읽고 답변.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | opal-agent stream-json 모드 신설(events.jsonl 기계 방출) + 루프 액션 에이전트 journal 규약 + oppl-monitor 도구로 진행 현황 단일 명령 관측 | - | claude CLI stream-json 지원(실측 검증은 ANALYSIS/EXECUTE) |
| 범위 | 포함: opal-agent 개조(claude 어댑터 stream 모드)·AGENT.md 결과 파일 규약 v2·journal 규약 신설·oppl-monitor 신규 도구·tools.md/하네스 등록·oppl SKILL 정합·동작 실증. 제외: claude 외 provider stream(점진)·Console 대시보드 뷰(후속)·실행 중 에이전트 직접 질의 채널(배제)·PM→루프 액션 에이전트 채널 변경(Agent 도구 불변) | stream 플래그 명칭·events.jsonl 스키마·monitor 화면 구성은 PLAN에서 설계 | `opal/tools/opal-agent/opal_agent.py`, 066 규약 |
| 제약 | 구독 로컬 claude -p 유지(API키·SDK 금지) / `--dangerously-skip-permissions` 금지 / Python 3.10+ 표준 라이브러리만 / 5필드 결과 계약·기존 `--json` 경로 하위호환 / 065·066 확정 계약 불변(H-9 2원화·blocked 7종·3-SSOT·결과 6필드·완료 마커=exitcode) / `~/.opal/` 직접 편집 금지 / 재시도 수치 비복제 | - | `.opal/AGENT.md` §금지사항, 066 DONE.md |
| 완료기준 | ① stream 모드 E2E 실측 — events.jsonl 증분 기록 + 최종 5필드 추출 정상 + 기존 `--json` 회귀 무 ② 루프 액션 에이전트 재실증(066 S-8급)에서 events.jsonl·journal.md 실생성 관측 ③ `oppl-monitor <task_folder>`가 단계×축 현황(상태·경과·최근 이벤트·journal)을 렌더 + `--json` 기계 출력 + `--watch` 갱신 ④ 하드에러·blocked 케이스가 모니터에서 구분 표시 ⑤ 문서 정합(규약 v2·tools.md·하네스 도구 표·oppl SKILL·변경이력) | - | TEST-SCENARIO에서 시나리오 확정 |

## 요구사항

- [ ] R-1 **opal-agent stream 모드**: claude 어댑터에 stream-json 실행 경로 신설 — 서브프로세스 증분 소비로 `events.jsonl`(1행 1이벤트) 기록 + 종료 시 최종 result 이벤트에서 5필드(result/session_id/is_error/total_cost_usd/duration_ms) 추출해 기존 반환 계약 유지. 어디에: `opal/tools/opal-agent/opal_agent.py`(+README). 왜: 확정 방향 §1·§3. AC: stream 모드 E2E 실측 통과(events.jsonl 존재·유효 JSONL·5필드 추출) + 기존 `--json` 일괄 경로 회귀 테스트 무손상 + 미지원 provider에 stream 지정 시 명시 에러 또는 경고 폴백(에러계약 준수).
- [ ] R-2 **결과 파일 규약 v2**: `opal/agents/opal-loop-action-agent/AGENT.md` §결과 파일 규약 개정 — 비동기 축을 stream 모드로 전환(`<phase>.events.jsonl` 편입), 완료 마커=exitcode 파일 불변, prompt 보존(`<phase>.prompt.txt`) 규약화. 왜: 확정 방향 §3, 066 규약 계승. AC: v2 절에 events.jsonl 경로·완료 마커 불변·prompt 규약이 명문화되고 v1(3-분리) 대비 변경점이 표기된다.
- [ ] R-3 **journal 규약**: AGENT.md에 §운행 일지 신설 — 루프 액션 에이전트가 `.oppl-run/journal.md`에 단계 시작/종료·게이트 판단(verdict+근거)·재시도(회차+사유)·blocked 사유를 시계열 append. 왜: stream 대체 불가 영역(배경 분석). AC: 기록 시점·형식(시각+단계+이벤트+근거 컬럼)·append-only 원칙이 명문화되고 재실증에서 journal.md가 실생성된다.
- [ ] R-4 **oppl-monitor 도구**: `opal/tools/oppl-monitor/`(run.sh + Python 표준 라이브러리) 신규 — `<task_folder>` 인자로 `.oppl-run/`(exitcode·events.jsonl·journal.md·session.json·err.log)을 파싱해 단계×축 현황판(축·상태 진행중/완료/실패/blocked·경과시간·최근 이벤트 요약·journal tail) 텍스트 렌더. `--json`(기계 출력)·`--watch`(주기 갱신) 지원. 왜: 캡틴 요구("명령어로 일목요연") + 확정 방향 §2. AC: 066 실증 산출물(samples/T01)과 067 재실증 폴더 양쪽에서 렌더 성공 + 하드에러(exit 2)·미완료(마커 부재)·blocked가 구분 표시 + `"ok": false` 에러계약(폴더 부재 등) 반환.
- [ ] R-5 **문서 정합·등록**: tools.md(도구 레지스트리)와 `opal/core/references/opal-harness.md` §9 도구 표에 oppl-monitor 행 추가, opal-agent README stream 모드 절 추가, oppl SKILL.md에 모니터링 안내 1~2줄, 변경 문서 전부 변경이력 행(067). install 스크립트가 신규 도구를 배포하는지 확인(도구 디렉토리 일괄 복사면 무변경). 왜: 도구 우선 원칙·레지스트리 정합. AC: 레지스트리 2곳 등록 + 변경이력 전부 존재 + install 후 `~/.opal/tools/oppl-monitor/run.sh` 실행 가능.
- [ ] R-6 **동작 실증**: 066 S-8급 샘플 태스크 재실증 — 루프 액션 에이전트 1회 디스패치로 events.jsonl(비동기 축)·journal.md 실생성 + 실행 중/완료 후 oppl-monitor 렌더 실측 + blocked fixture에서 모니터 blocked 표시. 왜: PRINCIPLES §4. AC: TEST-SCENARIO 해당 시나리오 전부 PASS + 증거 기록.

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `memory/console-brain-subscription-auth.md`: 구독(로컬 claude -p) 사용 — API키·SDK 금지.
- [MUST] TASK 066 계승: `--dangerously-skip-permissions` 금지 / 완료 마커=exitcode 파일 불변 / 065·066 확정 계약 불변.
- [MUST] `opal/skills/opal-pilot-project-loop/references/loop-control.md` §2: 재시도 수치 비복제.
- opal-agent는 Python 3.10+ 표준 라이브러리만(README §전제) — oppl-monitor도 동일 원칙.
- 기존 `--json` 일괄 경로·5필드 반환 계약 하위호환 — stream은 opt-in.
- claude CLI stream-json 이벤트 스키마는 문서화 불충분 — 실측 우선, 미보장 필드 의존 금지(066 R-H 원칙).

## 기술 스택

- Python 3.10+ (opal-agent 개조, oppl-monitor — 표준 라이브러리만)
- Bash (run.sh 래퍼, Bash `run_in_background` 호출 패턴)
- Markdown (AGENT.md 규약 v2·journal 규약·tools.md·SKILL 정합)
- Claude Code headless (`claude -p --output-format stream-json`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-agent 구현 | `opal/tools/opal-agent/opal_agent.py` | 개조 본체 — 어댑터·_run·파싱 구조 |
| D-2 | 소스 | opal-agent README | `opal/tools/opal-agent/README.md` | CLI 옵션·검증 상태·stream 절 추가 대상 |
| D-3 | 설계 | 루프 액션 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 규약 v2·journal 신설 대상 (066 v1.1) |
| D-4 | 기록 | 066 DONE | `tasks/066-260717-opd-루프액션-opal-agent-채널/DONE.md` | 채널 전환 결과·후속 정의 |
| D-5 | 기록 | 066 실증 산출물 | `tasks/066-260717-opd-루프액션-opal-agent-채널/samples/T01-정상슬라이스/.oppl-run/` | 뷰어 입력 실데이터 형태 |
| D-6 | 지식 | brain concept | `.opal/brain/pages/concept/oppl-internal-channel-opal-agent.md` | 066 채널 설계 결정 |
| D-7 | 기록 | 067 후속 메모리 | `memory/후속_067_stream_json_journal.md` | 캡틴 확정 범위·배제 사항 |
| D-8 | 설계 | 도구 레지스트리 | `opal/core/references/tools.md`, `opal/core/references/opal-harness.md` §9 | oppl-monitor 등록 대상 |
| D-9 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 모니터링 안내 정합 대상 |
