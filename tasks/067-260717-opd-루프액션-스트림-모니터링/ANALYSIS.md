# ANALYSIS: 루프 액션 에이전트 투명 모니터링 — opal-agent stream-json 개조 + journal 규약 + oppl-monitor 도구

> 작성일: 2026-07-17
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| R-1 | 소스 | opal-agent 구현 | `opal/tools/opal-agent/opal_agent.py` | 개조 본체 — `_run`/어댑터/CLI 구조 실측 |
| R-2 | 소스 | opal-agent README | `opal/tools/opal-agent/README.md` | CLI 옵션·검증 상태·배포 경로(bin symlink 없음) |
| R-3 | 기록 | 066 ANALYSIS §1.5~1.6 | `tasks/066-260717-opd-루프액션-opal-agent-채널/ANALYSIS.md:61-159` | opal-agent 출력 계약(5필드·종료코드·에러계약) 선행 정밀분석 — 067에서 재검증 |
| R-4 | 기록 | 066 DONE | `tasks/066-260717-opd-루프액션-opal-agent-채널/DONE.md` | 채널 전환 결과·후속(067) 정의 원문 |
| R-5 | 실증 | 066 샘플 산출물 | `tasks/066-260717-opd-루프액션-opal-agent-채널/samples/T01-정상슬라이스/.oppl-run/` | 뷰어 입력 실데이터 형태(3-분리 5축 + session.json) |
| R-6 | 설계 | brain concept | `.opal/brain/pages/concept/oppl-internal-channel-opal-agent.md` | 066 채널 설계 결정 근거 |
| R-7 | 기록 | 067 후속 메모리 | `memory/후속_067_stream_json_journal.md` | 캡틴 확정 범위·배제 사항 원문 |
| R-8 | 설계 | 루프 액션 에이전트 AGENT.md | `opal/agents/opal-loop-action-agent/AGENT.md` | 결과 파일 규약 v1(3-분리)·journal 신설 대상 |
| R-9 | 설계 | 도구 레지스트리 | `opal/core/references/tools.md`, `opal/core/references/opal-harness.md` §9 | oppl-monitor 등록 대상 — 현황 실측(opal-agent 미등록 확인) |
| R-10 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 모니터링 안내 정합 대상 |
| R-11 | 소스 | install 스크립트 | `scripts/install-mac.sh:1110-1180` | 도구 배포 방식(일괄 복사 + 개별 chmod) 실측 |
| R-12 | 실측 | claude CLI stream-json 실행 로그 | scratchpad `stream_test1.jsonl`/`stream_test2.jsonl`/`stream_test3.jsonl` (본 세션 생성) | 이벤트 스키마·`--verbose` 필요성 실측 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조. 유형: 기획/설계/소스/외부(+실증/실측 — 본 태스크 확장 표기, citation-rules 위반 아님).

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/opal-agent/opal_agent.py` | 멀티 provider 서브에이전트 호출 라이브러리+CLI — stream 모드 개조 본체 | O | `:558-618`(`_run` 블로킹), `:171-211`(ClaudeAdapter), `:637-728`(CLI 인자·`main`), `:299-341`(CodexAdapter JSONL 파싱, 재사용 후보) |
| `opal/tools/opal-agent/README.md` | opal-agent 사용 설명서 | O | stream 모드 절 부재 — 신설 필요 |
| `opal/agents/opal-loop-action-agent/AGENT.md` | 루프 액션 에이전트 정의 — 결과 파일 규약 v1 | O | `:151-224`(§결과 파일 규약), journal 절 부재 |
| `opal/tools/oppl-monitor/` (신규) | 진행 현황 렌더 CLI | O(신규) | 부재 확인(`ls opal/tools/` 결과 없음) |
| `opal/core/references/tools.md` | 도구 레지스트리 | O | opal-agent조차 미등록 확인(§1.5 발견) — oppl-monitor 신규 등록 필요 |
| `opal/core/references/opal-harness.md` §9 | 도구 표 | O | `:242-256` 등록 도구 표, opal-agent 미포함 확인 |
| `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl 오케스트레이터 스킬 | O | `:291-303`(단계별 `[opal-agent 채널]` 표기), 모니터링 안내 1~2줄 추가 대상 |
| `scripts/install-mac.sh` | 설치 스크립트 — 도구 배포 | 확인만(변경 불요 가능성) | `:1110-1180`(도구 일괄 복사 + 개별 tool `chmod +x` 블록, opal-agent는 개별 블록 없이도 배포됨) |
| `opal/tools/state-tool/`, `opal/tools/backlog-tool/` | 기존 OPAL 도구 관례(run.sh 래퍼·JSON 에러계약) 참조 | 참조만 | `opal/core/references/tools.md:69-190`(state-tool 출력 형식·에러 코드 패턴) |

### 1.2 아키텍처 패턴

- **provider 어댑터 계층**: `ProviderAdapter` ABC — `build_invocation()`/`parse_result()` 2메서드 구현 계약(`opal_agent.py:137-168`). stream 모드는 이 계약을 깨지 않고 `ClaudeAdapter`에 신규 경로를 추가하는 방식이 정합적이다(§3.1 참조).
- **동기 서브프로세스 단일 실행 경로**: `_run()`(`:558-618`)이 유일한 실행 진입점이며 `subprocess.run(capture_output=True, ...)`(블로킹, 전체 출력 확보 후 반환)만 사용한다. 스트리밍(증분 소비)을 위해서는 `subprocess.Popen` + `stdout` 파이프 라인 단위 readline 루프가 필요 — 현재 코드에 이 경로가 전혀 없다.
- **JSON 우선 + provider별 파싱 격리**: `main()`(`:677-728`)은 라이브러리 레벨에서 항상 `output_format="json"`으로 고정 실행하고(`:714`), CLI `--json`/`--text`는 표시 방식만 분기한다(`display`, `:722-726`). stream 모드는 이 구조에 세 번째 축(`--stream` 또는 `output_format="stream-json"`)을 추가하는 형태가 기존 패턴과 정합적이다.
- **JSONL 이벤트 파싱 선례**: `CodexAdapter.parse_result()`(`:299-341`)가 이미 `stdout.splitlines()` → `json.loads(line)` 방어적 파싱(빈 줄 skip, `JSONDecodeError` skip) 패턴을 구현하고 있다 — codex는 **일괄 실행 후 전체 stdout을 라인 단위로 사후 파싱**하는 구조이며, **실행 중 증분 소비는 하지 않는다**(`subprocess.run`으로 전체 캡처 후 `stdout.splitlines()`). 따라서 이 선례는 "JSONL 라인 파싱 로직"은 재사용 가능하나 "실행 중 증분 기록(events.jsonl append)"의 선례는 아니다 — stream 모드가 요구하는 것은 프로세스 실행 도중 파일에 append하는 것이므로 `Popen` 기반 신규 실행 경로가 필요하다(§3.1 확정).
- **부트스트랩 마커 계약**: `_mark()`(`:165-168`)이 프롬프트 최외곽 첫 줄에 `[WORKER]`/`[ASSISTANT]` 마커를 붙인다 — stream 모드에서도 이 마커 삽입 지점은 변경 없이 재사용 가능(프롬프트 조립 로직은 실행 방식과 독립적).
- **결과 파일 3-분리 규약(066)**: 루프 액션 에이전트가 `stdout > result.json`, `stderr > err.log`, `echo $? > exitcode`로 캡처(`AGENT.md:159-167`). stream 모드에서 `events.jsonl`은 이 3-분리 위에 **추가되는 4번째 파일**로 편입되는 구조가 자연스럽다(완료 마커=exitcode 불변 유지, TASK 제약).

### 1.3 의존성 맵

```
opal/tools/opal-agent/opal_agent.py (호출 대상)
  ← opal/tools/opal-agent/run.sh (실행 래퍼, ~/.opal/.venv 파이썬 경유)
    ← opal/agents/opal-loop-action-agent/AGENT.md §호출 모드별 명령 형태 (Bash 직접 호출, "opal-agent 채널")
      ← opal/skills/opal-pilot-project-loop/SKILL.md (오케스트레이터가 루프 액션 에이전트를 Agent 도구로 디스패치)
        ← PM(사용자 대면, //oppl 진입)

opal/tools/oppl-monitor/ (신규, 독립 도구)
  → 입력: <task_folder>/.oppl-run/{exitcode,result.json,err.log,events.jsonl(신규),journal.md(신규),session.json}
  → 호출자: PM(캡틴이 명령 실행) — 루프 액션 에이전트 실행과 프로세스 독립(파일 SSOT 경유, 실행 중 직접 질의 없음)
```

- **순환 의존 없음**: opal-agent는 루프 액션 에이전트에 의해서만 소비되며, oppl-monitor는 `.oppl-run/` 파일만 읽는 독립 리더 — 두 도구 간 직접 import/호출 관계 없음(파일 계약으로만 연결).
- **외부 패키지 의존성 없음**: opal-agent·oppl-monitor 모두 Python 3.10+ 표준 라이브러리만(README §전제, TASK 제약과 일치) — `requirements.txt`(`scripts/install-mac.sh:1292`)에 신규 의존성 추가 불필요.

### 1.4 테스트 현황

- `opal/tools/opal-agent/tests/` 디렉토리 존재 확인(`ls` 결과) — 내용 미상세 분석(TASK 067 범위는 stream 모드 신설이므로 기존 테스트는 회귀 대상으로만 취급, PLAN에서 구체 확인 필요).
- `oppl-monitor`는 신규 도구라 기존 테스트 없음 — TASK R-6(동작 실증)이 유일한 검증 경로(TEST-SCENARIO에서 시나리오화).
- 066 실증 산출물(`samples/T01-정상슬라이스/`)이 067 재실증의 회귀 기준선 역할 — 3-분리 파일 5축(t1/t2/g/t3/t4a) + session.json이 실존하며 stream 모드 도입 후에도 이 구조가 하위호환되어야 함(TASK 제약).

## 2. 외부 조사 결과 (claude CLI stream-json 실측)

### 2.1 실측 환경

```
$ which claude && claude --version
/var/folders/.../cmux-cli-shims/.../claude
2.1.212 (Claude Code)
```

### 2.2 실측 1 — 기본 stream-json 이벤트 스키마 (도구 없음)

```bash
claude -p --output-format stream-json --verbose "1+1 결과만 답해" --model haiku --allowedTools "" \
  > stream_test1.jsonl 2> stream_test1.err.log
# exit=0, 33줄, err.log 공백
```

**이벤트 타입 분포(33행 전수 파싱, 파싱 실패 0건)**:

| 순번 | `type` | `subtype` | 비고 |
|------|--------|-----------|------|
| 0-1 | `system` | `hook_started` | 훅 실행 시작(환경 의존 — 본 실측 환경의 훅 설정에 따른 이벤트, claude CLI 공통 필수 이벤트는 아닐 수 있음) |
| 2-3 | `system` | `hook_response` | 훅 응답(`stdout`/`stderr`/`exit_code`/`outcome` 포함) |
| 4 | `system` | `init` | 세션 초기화 — `session_id`/`tools`/`mcp_servers`/`model`/`permissionMode`/`slash_commands`/`agents`/`skills` 등 세션 메타 전체 |
| 5-28 | `system` | `thinking_tokens` | 사고 토큰 증분(`estimated_tokens`/`estimated_tokens_delta`) — 24회 반복 발행(고빈도 이벤트) |
| 29-30 | `assistant` | (없음) | 메시지 이벤트 — `message.content`에 `thinking`/`text` 블록 |
| 31 | `rate_limit_event` | (없음) | `rate_limit_info` |
| 32 | `result` | `success` | **최종 이벤트** — 5필드 전부 포함(아래 §2.4) |

### 2.3 실측 2 — 도구 호출 포함(`Write` 허용)

```bash
claude -p --output-format stream-json --verbose \
  "이 디렉토리에 test.txt 파일을 만들고 내용은 hello라고 써줘. 완료하면 '완료'라고만 답해" \
  --model haiku --allowedTools "Write" \
  > stream_test2.jsonl 2> stream_test2.err.log
# exit=0, 24줄, 파일 실제 생성 확인(test.txt 내용 "hello")
```

**도구 호출 이벤트 형태(라인 15, `assistant` 이벤트 내부)**:

```json
{"type": "tool_use", "id": "toolu_01PZkpEj6UvhcnEF8YTEBf5y", "name": "Write",
 "caller": {"type": "direct"},
 "input": {"file_path": "/.../test.txt", "content": "hello"}}
```

**도구 결과 이벤트 형태(라인 16, `type: "user"` 최상위 이벤트)**:

```json
{"type": "user", "message": {"role": "user", "content": [
  {"tool_use_id": "toolu_01PZkpEj6UvhcnEF8YTEBf5y", "type": "tool_result",
   "content": "File created successfully at: /.../test.txt (...)"}]},
 "tool_use_result": {"type": "create", "filePath": "/.../test.txt", ...}}
```

→ **도구 이벤트는 최상위 `type`이 별도로 있는 게 아니라, `assistant` 이벤트의 `message.content[].type == "tool_use"` / `user` 이벤트의 `message.content[].type == "tool_result"` 서브필드로 표현된다.** events.jsonl을 소비하는 oppl-monitor는 최상위 `type`(`system`/`assistant`/`user`/`result`/`rate_limit_event`)만으로는 "도구 호출이 있었는가"를 판별할 수 없고, `assistant`/`user` 이벤트 내부의 `message.content[].type`까지 검사해야 한다.

### 2.4 실측 3 — 최종 `result` 이벤트 5필드 확인

```python
{k: last.get(k) for k in ['result','session_id','is_error','total_cost_usd','duration_ms']}
# {'result': '2', 'session_id': '2005e50d-...', 'is_error': False,
#  'total_cost_usd': 0.0252952, 'duration_ms': 7947}
```

→ **결정론적 확인**: stream-json 모드에서도 스트림 마지막 줄(`type: "result"`)에 opal-agent가 5필드 추출 시 참조하는 4개 서브필드(`result`/`session_id`/`is_error`/`total_cost_usd`/`duration_ms`)가 그대로 존재한다. 기존 `--output-format json`(단일 객체)의 최종 result 객체와 **동일 스키마**로 관찰됨(066 ANALYSIS §1.5.1 5필드와 정합) — stream 모드에서도 `ClaudeAdapter.parse_result()`와 동일한 필드 추출 로직을 마지막 줄에만 적용하면 기존 5필드 계약을 그대로 유지할 수 있다.

### 2.5 실측 4 — `--verbose` 필요성

```bash
claude -p --output-format stream-json "1+1" --model haiku --allowedTools ""
# exit=1
# stderr: "Error: When using --print, --output-format=stream-json requires --verbose"
```

→ **`--verbose`는 필수 플래그다.** stream 모드 개조 시 `ClaudeAdapter`가 `output_format="stream-json"`일 때 `--verbose`를 무조건 함께 추가해야 하며, 누락 시 exit 1(하드 에러는 아니고 CLI 자체 사용법 에러 — 066 §1.5.3 종료코드 체계의 `2`(OpalAgentError) 범주와는 다른 코드이므로 opal-agent가 이 실패를 어떻게 분류할지 PLAN에서 결정 필요, §5 리스크).

### 2.6 버전 호환성

- 실측 버전: Claude Code CLI 2.1.212. 이벤트 스키마(특히 `hook_started`/`hook_response`/`thinking_tokens`)는 로컬 환경 설정(훅 등록 여부)에 따라 달라질 수 있어 **범용 최소 보장 집합**은 `system/init`(1회) → 0회 이상의 `assistant`/`user`(도구 호출 왕복) → `result`(정확히 1회, 마지막 줄)로 좁혀 방어적으로 설계해야 한다(066 R-H 원칙 — 미보장 필드 의존 금지).
- 공식 문서 미조회(TASK 지시상 `--verbose` 실측 우선 원칙 — context7/WebSearch에 claude CLI stream-json 전용 문서 없음, 실측만이 유일한 근거).

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/opal-agent/opal_agent.py`: `ClaudeAdapter.build_invocation()`에 `output_format == "stream-json"` 분기(`--verbose` 강제 추가) 신설, `ClaudeAdapter.parse_result()`에 stream 전용 파싱 경로(마지막 줄만 5필드 추출) 신설, `_run()`에 `Popen` 기반 증분 실행 경로 신설(파일 append 콜백 또는 반환값에 이벤트 리스트 포함 방식은 PLAN 결정 필요 — decision_required 후보), CLI 인자(`_build_parser`, `main()`)에 stream 모드 진입 플래그·`events.jsonl` 출력 경로 인자 신설.
- `opal/tools/opal-agent/README.md`: stream 모드 사용법 절 신설.
- `opal/agents/opal-loop-action-agent/AGENT.md`: §결과 파일 규약 v1→v2(비동기 축의 `events.jsonl` 편입, 완료 마커=exitcode 불변, prompt 보존 규약), §운행 일지(journal) 신설.
- `opal/tools/oppl-monitor/`(신규): `run.sh` + `oppl_monitor.py`(가칭) 전체 신규 생성.
- `opal/core/references/tools.md`, `opal/core/references/opal-harness.md` §9: oppl-monitor 행 추가.
- `opal/skills/opal-pilot-project-loop/SKILL.md`: 모니터링 안내 1~2줄 추가.

### 3.2 간접 영향

- **066 확정 계약 소비자**: `opal/skills/opal-pilot-project-loop/SKILL.md`(`:291-303`)의 "[opal-agent 채널 — 동기/비동기]" 표기 문구 자체는 유지되나, 축별 결과 파일 산출물 구조가 v1(3-분리)→v2(+events.jsonl)로 바뀌므로 SKILL.md가 참조하는 결과 파일 경로 서술이 있다면 정합 확인 필요(현재 SKILL.md 본문은 AGENT.md를 참조 포인터로만 가리키고 구조를 복제하지 않음 — 직접 영향 적음, 근거: `SKILL.md:375`).
- **opal-harness.md §5/§6 관측 포인터**: `:175`(Observability), `:191`(Model Mapping)에 opal-agent 채널을 가리키는 1줄 SSOT 포인터가 이미 있음(066에서 추가) — 067에서 stream 모드가 추가돼도 포인터 대상 문서(AGENT.md) 갱신만으로 충분, harness 본문 추가 수정 불필요.
- **install-mac.sh**: opal-agent가 개별 `chmod +x` 블록 없이도 배포되는 이유는 소스 저장소의 `opal/tools/opal-agent/run.sh`가 이미 `rwxr-xr-x`이고 `install_dir()`(`:208-222`)이 `cp -r`/`cp -Rf`로 권한 비트를 보존하기 때문(실측: `ls -la` 결과 `-rwxr-xr-x`). 신규 `oppl-monitor/run.sh`도 저장소에 `chmod +x` 상태로 커밋하면 일괄 복사(`install_dir("$opal_dir/tools", ...)`, `:1112`)만으로 배포되어 **install-mac.sh 수정이 필수는 아니다** — 단, 기존 관례(state-tool·backlog-tool·git-sync-tool 등 신규 도구 도입 시마다 방어적 개별 `chmod +x` 블록을 추가해 온 패턴, `:1122-1178`)와의 일관성 여부는 PLAN 결정 필요(§5 리스크).
- **`.gitignore`**: 066 DONE.md 후속②가 `.oppl-run/`을 `.gitignore`에 반영 권고 — `events.jsonl`/`journal.md` 신설 파일도 동일 디렉토리 하위이므로 자동 커버되나, 067 범위에 포함되는지는 TASK.md에 명시 없음(067 후속 백로그 목록에는 미포함, 066 DONE.md 후속 그대로 남아있는 별개 항목 — 067 완료기준에는 해당 없음, 착각 방지 차 명기).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — `AgentConfig.output_format`에 `"stream-json"` 신규 값 추가(하위호환: 기존 `"json"`/`"text"` 유지, opt-in), `call_agent()`/`main()` 반환·CLI 인자 확장
- [ ] 설정/환경변수 변경 — 없음(옵션 플래그로만 제어)
- [ ] 빌드/배포 파이프라인 변경 — install-mac.sh는 수정 불요 가능성 높음(§3.2 참조, 관례 정합 여부만 PLAN 결정)

## 4. 핵심 발견 사항

1. **opal-agent는 현재 도구 레지스트리(tools.md·opal-harness.md §9) 어디에도 등록되어 있지 않다** — 066에서도 등록되지 않은 채로 남아있다(README에 "다른 skill-called 툴처럼 직접 경로로 호출" 서술만 존재). oppl-monitor는 TASK R-5가 명시적으로 레지스트리 등록을 요구하므로, 이번에 oppl-monitor만 등록하고 opal-agent는 미등록 상태로 둘지(범위 외) 명확화가 필요하다 — TASK.md 범위에는 opal-agent 등록이 없으므로 **oppl-monitor만 신규 등록**하는 것이 TASK 문면과 일치한다(범위 확대 금지).
2. **stream-json 실측 결과 5필드 계약이 그대로 보존된다** — 최종 `result` 이벤트가 기존 `--output-format json`의 단일 객체와 동일한 필드 구조를 가지므로, `ClaudeAdapter.parse_result()`의 필드 추출 로직(`result`/`session_id`/`is_error`/`total_cost_usd`/`duration_ms`)은 "stream의 마지막 줄에 적용"으로 그대로 재사용 가능하다 — 신규 파싱 로직이 아니라 **입력 표면(마지막 줄 vs 전체 stdout)만 다르다**.
3. **`--verbose`는 stream-json 사용의 필수 전제이며, 미지정 시 exit 1로 즉시 실패한다.** opal-agent의 stream 진입 분기는 `--verbose`를 항상 자동 부착해야 하며, 이 실패 케이스(exit 1)는 066 §1.5.3 종료코드 체계(0/1/2)의 어느 범주에도 정확히 대응하지 않는 CLI 자체 사용법 에러이므로 별도 취급이 필요하다(방어적으로 opal-agent가 항상 부착하면 이 케이스 자체가 발생하지 않음 — 코드 내부에서 흡수 가능).
4. **도구 호출 이벤트는 최상위 이벤트 타입이 아니라 `assistant`/`user` 이벤트의 `message.content[].type` 서브필드로 중첩되어 있다.** oppl-monitor가 "최근 이벤트 요약"을 렌더하려면 최상위 `type` 분기만으로는 부족하고 `assistant.message.content[]`/`user.message.content[]` 내부까지 순회해야 한다 — events.jsonl 스키마 정규화(정제된 요약 레이어를 opal-agent가 만들지, oppl-monitor가 원본 이벤트를 그대로 순회할지)는 PLAN 결정 필요.
5. **`_run()`은 현재 `subprocess.run` 블로킹 전용이며 증분 실행 경로가 코드에 전혀 없다** — CodexAdapter의 JSONL 파싱은 "일괄 실행 후 라인 분리 파싱" 선례이지 "실행 중 증분 append" 선례가 아니므로, stream 모드는 `_run()`과 별개의 신규 실행 경로(`Popen` + readline 루프)가 필요하다. 이는 066 ANALYSIS가 이미 지적한 "비동기 실행은 opal-agent 내장 기능 없음(호출측 `run_in_background`로 감쌈)"과는 다른 층위의 변경이다 — 비동기는 프로세스 백그라운드화(변경 없음, 호출측 책임 유지)이고, stream은 동일 프로세스 내에서 출력을 증분 소비하는 것(opal-agent 내부 개조 필요)이라는 점을 구분해야 한다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-H(계승) | claude CLI stream-json 이벤트 스키마는 공식 문서 미비 — 훅 이벤트(`hook_started`/`hook_response`) 등은 로컬 환경 의존적일 수 있어 범용성 낮음 | 높음 | 본 ANALYSIS §2.6, 066 ANALYSIS §1.5.2 동일 원칙 계승 |
| R-VERBOSE | `--verbose` 누락 시 exit 1(사용법 에러)로 즉시 실패 — opal-agent가 자동 부착하지 않으면 스트림 모드가 항상 실패 | 높음 | 본 ANALYSIS §2.5 실측(`stream_test3.jsonl` exit=1) |
| R-NEST | 도구 이벤트가 최상위 타입이 아니라 `message.content[]` 중첩 구조 — oppl-monitor의 "최근 이벤트 요약" 파싱이 단순 `type` 필터만으로 불가능 | 중간 | 본 ANALYSIS §2.3 |
| R-ASYNC | opal-agent에 내장 비동기(백그라운드) 기능이 전혀 없음 — stream 모드의 events.jsonl 증분 기록과 호출측 `run_in_background` 래핑을 동시에 설계해야 파일 락/경합 없이 append 가능한지 검증 필요(동일 프로세스 내부에서 opal-agent 자신이 파일에 쓰는지, 호출측 리다이렉트로만 쓰는지에 따라 설계가 갈림) | 높음 | `opal_agent.py:558-618`(증분 실행 경로 부재), 066 ANALYSIS §1.6 "백그라운드 실행 X" |
| R-REG | opal-agent 자체가 도구 레지스트리(tools.md·opal-harness.md §9)에 미등록 상태 — oppl-monitor 등록 시 "관련 도구" 포인터를 어떻게 서술할지(opal-agent를 함께 등록할지는 TASK 범위 밖) | 낮음 | 본 ANALYSIS §4 발견1, `opal/core/references/tools.md` 전체 grep(opal-agent 0건) |
| R-CHMOD | install-mac.sh가 개별 도구마다 방어적 `chmod +x` 블록을 추가해온 관례(state/brain/cmux/tool-scan/memory/git-sync/backlog 7종)와 달리 opal-agent는 이 블록이 없어도 배포됨(소스 권한 비트가 이미 +x, `cp -Rf`가 보존) — oppl-monitor에 개별 블록을 추가할지(관례 일관성) 생략할지(불필요한 추가) PLAN 결정 필요 | 낮음 | `scripts/install-mac.sh:1110-1180`, `ls -la opal/tools/opal-agent/run.sh`(-rwxr-xr-x 확인) |
| R-EVSCHEMA | events.jsonl을 opal-agent가 claude 원본 이벤트 그대로 기록할지, 정규화된 요약 스키마로 변환해 기록할지 미정 — 원본 그대로면 oppl-monitor가 파싱 부담을 지고, 정규화하면 opal-agent가 claude 스키마 변경에 더 취약해짐(양쪽 트레이드오프) | 높음 | TASK.md §확정된 설계 방향 3, §명확화 결과(미확정 항목: "events.jsonl 스키마는 PLAN에서 설계") — decision_required 후보 |
| R-WATCH | `--watch`(주기 갱신) 구현 방식 미정 — 폴링 간격, 터미널 재렌더 방식(clear+redraw vs append), 프로세스 상주 시간 상한 | 중간 | TASK.md R-4 AC, 참조할 기존 OPAL 도구 선례 없음(모든 기존 도구는 1회성 실행) |
| R-COMPAT | 기존 `--json` 일괄 경로 회귀 테스트가 opal-agent에 존재하는지 미확인(`tests/` 디렉토리 내용 미분석) — stream 분기 추가가 기존 경로에 부작용을 주지 않는지 확인할 회귀 스위트 유무가 불확실 | 중간 | `opal/tools/opal-agent/tests/`(존재만 확인, 내용 미상세 — §1.4) |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python | 3.10+ (표준 라이브러리만 — README §전제) |
| 실행기 | Claude Code CLI | 2.1.212 (본 세션 실측) |
| 셸 | Bash | run.sh 래퍼, `run_in_background` 호출 패턴 |
| 문서 | Markdown | AGENT.md 규약 v2·journal 규약·tools.md·SKILL 정합 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | 다음 PLAN 단계에서 stream 모드 인자 설계·events.jsonl 스키마 확정·oppl-monitor 화면 설계 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (해당 없음) | claude CLI stream-json은 공식 문서 미비로 context7/WebSearch 조사 대상이 아님(실측이 유일 근거, TASK 지시 원칙) |

## 변경이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-07-17 | v1.0 | 최초 작성 — opal_agent.py 개조 지점 정밀 식별(066 재검증), claude stream-json 3종 실측(기본/도구호출/verbose), oppl-monitor 입력 데이터 현황, 문서 개정 지점 5곳, 리스크 8건(decision_required 후보 3건: R-ASYNC/R-EVSCHEMA/R-WATCH) |
