# ANALYSIS: 루프 액션 에이전트 내부 디스패치 채널 opal-agent 전환

> 작성일: 2026-07-17
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 루프 액션 에이전트 정의 | `opal/agents/opal-loop-action-agent/AGENT.md` | 개정 대상 — 내부 디스패치 절 전수 확인 |
| D-2 | 소스 | opal-agent README | `opal/tools/opal-agent/README.md` | 채널 능력 SSOT(문서) |
| D-3 | 소스 | opal-agent 구현 | `opal/tools/opal-agent/opal_agent.py` | 채널 능력 SSOT(코드 — 문서/코드 불일치 시 우선) |
| D-4 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 정합 대상 — 내부 디스패치 언급 전수 확인 |
| D-5 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` | §5 Observability·§6 Model Mapping 보강 지점 |
| D-6 | 설계 | Observability 모듈 | `opal/core/references/harness/observability.md` | Agent 도구 전제 서술 확인 |
| D-7 | 기록 | 065 AGENTIC-LOG | `tasks/065-260717-opd-oppl-태스크-실행자/AGENTIC-LOG.md` | #12d·#12e 릴레이 마찰 실측 근거 |
| D-8 | 설계 | OPAL 코어 부트스트랩 | `opal/core/AGENT.md` | `[WORKER]`/`[ASSISTANT]` 3단 마커 사다리 근거 |
| D-9 | 지식 | brain concept | `.opal/brain/pages/concept/oppl-executor-delegation-architecture.md` | 065 위임 구조 설계 결정(4축·3-SSOT·blocked 7종·결과계약 6필드) |
| D-10 | 지식 | brain entity | `.opal/brain/pages/entity/opal-loop-action-agent.md` | 루프 액션 에이전트 책임·관계 정의 |
| D-11 | 설계 | 모델 매핑 | `~/.opal/references/opal-model-mapping.md` | opal-agent `--model` 지정 시 레벨↔실모델 변환 근거 |

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/agents/opal-loop-action-agent/AGENT.md` | 루프 액션 에이전트 정의 — 내부 4축 디스패치 서술 본체 | O (R-1~R-6 본체) | `opal/agents/opal-loop-action-agent/AGENT.md:38-155` |
| `opal/tools/opal-agent/opal_agent.py` | opal-agent CLI/라이브러리 구현 — 채널 능력 SSOT | X (개조 범위 외 원칙, 기존 기능만 참조) | `opal/tools/opal-agent/opal_agent.py:76-728` |
| `opal/tools/opal-agent/README.md` | opal-agent 사용법 문서 | X (참조만) | `opal/tools/opal-agent/README.md:1-217` |
| `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl 오케스트레이터 — 태스크 내부 파이프라인·디스패치 절 | O (R-5 정합) | `opal/skills/opal-pilot-project-loop/SKILL.md:288-382` |
| `opal/core/references/opal-harness.md` | 공통 하네스 §5 Observability·§6 Model Mapping stub | O (R-5 보강, 채널 항목 추가 여부는 PLAN 결정) | `opal/core/references/opal-harness.md:167-189` |
| `opal/core/references/harness/observability.md` | Observability 본문 — Agent 도구 전제 서술 | O (R-5, 아이콘 룩업·디스패치 선언 형식이 Agent 도구 전제) | `opal/core/references/harness/observability.md:40-59` |
| `opal/skills/opal-pilot-project-loop/references/loop-control.md` | 재시도 상한 SSOT 포인터 규칙 | X (참조만, §2 포인터 유지 확인용) | `-` |
| `opal/skills/opal-pilot-project-loop/references/verification.md` | 검증 2원화 순서·결과계약 스키마 | X (065 확정 계약 불변 확인용) | `-` |
| `opal/core/AGENT.md` | `[WORKER]`/`[ASSISTANT]` 3단 마커 사다리 정의 | X (참조만) | `opal/core/AGENT.md:9-24` |
| `tasks/065-260717-opd-oppl-태스크-실행자/AGENTIC-LOG.md` | 릴레이 마찰 실측 기록 | X (근거 인용만) | `tasks/065-260717-opd-oppl-태스크-실행자/AGENTIC-LOG.md:35-36` |

### 1.2 아키텍처 패턴

- **내부 4축 디스패치 패턴** (D-1 §실행 프로세스): 루프 액션 에이전트가 T1~T5+G를 자신의 세션 내부에서 생성자(fe/be/db/task-agent)·Evaluator(opal-evaluator-agent)·test-agent(opal-test-agent)·conv/sec-checker 4개 별도 에이전트로 재디스패치한다. 현재는 예외 없이 플랫폼 Agent 도구를 전제로 서술되어 있다 — `opal-loop-action-agent/AGENT.md:42`: "Agent 도구로 내부 디스패치 (op-dev-plan, model: advanced)", `opal-loop-action-agent/AGENT.md:139`: "각각 별도 에이전트로 Agent 도구를 통해 내부 디스패치한다".
- **결과 반환 계약 패턴** (D-1 §결과 반환 형식, `opal-loop-action-agent/AGENT.md:117-126`): task_id/verdict/scenario_results/changed_files/done_md_path/blockers 6필드 JSON. 이 구조는 opal-agent 전환과 무관하게 065 확정 계약으로 불변 유지된다(TASK.md §제약 조건).
- **3-SSOT tool-gated 경계** (D-1 §3-SSOT 도구 호출 규칙, `:108-112`): 루프 액션 에이전트는 `test-tool scenario-*`만 직접 호출하고 backlog-tool·state-tool은 호출하지 않는다. 채널 전환과 독립적인 불변 규칙.
- **opal-agent provider 어댑터 패턴** (D-3): `ProviderAdapter` ABC(`opal_agent.py:137-168`) + provider별 구현(Claude/Gemini/Codex/Grok/Cursor/Antigravity, `:171-478`) — `build_invocation`(CLI 인자 조립) + `parse_result`(stdout 파싱) 2메서드로 provider 차이를 흡수. `call_agent()`(`:507-555`)가 공개 라이브러리 API, `_run()`(`:558-618`)이 실제 subprocess 실행부, `main()`(`:677-728`)이 CLI 진입점.
- **부트스트랩 3단 스킵 사다리** (D-8, `opal/core/AGENT.md:9,11,13`): `[WORKER]`(전부 스킵)/`[ASSISTANT]`(비서 tier만)/무마커(A+B). opal-agent의 `--opal-bootstrap off|assistant|on`이 이 마커를 프롬프트 첫 줄에 주입하는 방식으로 이미 연동되어 있다(D-2 README:187-199, D-3 `opal_agent.py:134,165-168`).

### 1.3 의존성 맵

- `opal-loop-action-agent/AGENT.md` → (Agent 도구, 전환 대상) → op-dev-plan/op-dev-execute(생성자), opal-evaluator-agent, opal-test-agent, opal-convention-checker/opal-security-checker.
- `opal-loop-action-agent/AGENT.md` → (도구 직접 호출, 전환 무관) → `~/.opal/tools/test-tool/run.sh scenario-*`.
- `opal-pilot-project-loop/SKILL.md` → PM이 `opal-loop-action-agent`를 Agent 도구로 1회 디스패치(이 경로는 TASK.md §범위에서 "불변 사항 7" — 전환 대상 아님) → 루프 액션 에이전트가 내부 4축을 재디스패치.
- opal-agent(`opal_agent.py`) → provider CLI(`claude`/`gemini`/`codex`/`grok`/`cursor`/`antigravity`) subprocess 호출 → stdout JSON/JSONL/텍스트 파싱 → `AgentResult` 반환. claude만 이번 태스크 1차 릴리스 대상(TASK.md §확정된 설계 방향 6).
- `opal-model-mapping.md`(D-11) → PM/에이전트가 model 레벨명(`light`/`standard`/`advanced`)을 실제 모델명으로 치환 → opal-agent `--model` 플래그에 주입. 현재 opal-agent는 레벨명을 실모델명으로 자동 변환하지 않으므로(코드에 매핑 로직 없음, `opal_agent.py:637` `--model M` 단순 pass-through), 호출측(루프 액션 에이전트 AGENT.md)이 레벨→실모델 치환을 직접 수행해야 한다.

### 1.4 테스트 현황

- opal-agent 자체의 자동화 테스트 파일은 탐색 범위(`opal/tools/opal-agent/`)에서 발견되지 않았다 — README에 "claude/codex E2E 실측 완료" 기술이 있으나(D-2 §검증 상태), 이는 수동 실측 기록이지 회귀 테스트 스위트가 아니다.
- 루프 액션 에이전트의 채널 전환 자체를 검증하는 테스트는 R-7(동작 실증)에서 신규 정의되며 TEST-SCENARIO 단계 산출물이다. 이번 ANALYSIS 시점에는 부재.

### 1.5 opal-agent 출력 계약 현황 (결과 파일 규약 설계 근거)

> PM Gate 보완 지시(1/3) 반영 — TASK.md 분석 산출 요구 3(결과 파일 규약 설계에 필요한 현황) 구체화.

#### 1.5.1 `AgentResult` 필드 전체 목록 (라이브러리 반환값)

`call_agent()`가 반환하는 dataclass 필드 전부 (`opal_agent.py:109-119`):

| 필드 | 타입 | 기본값 | 의미 | 근거 |
|------|------|--------|------|------|
| `text` | `str` | (필수) | 최종 응답 텍스트 | `opal_agent.py:113` |
| `provider` | `str` | `"claude"` | 사용된 provider명 | `opal_agent.py:114` |
| `session_id` | `str \| None` | `None` | resume용 세션 ID(지원/확보 가능 시) | `opal_agent.py:115` |
| `is_error` | `bool` | `False` | 에이전트 오류 여부(에이전트가 실행은 됐으나 실패로 자체 보고) | `opal_agent.py:116` |
| `cost_usd` | `float \| None` | `None` | 총 비용(USD) — 제공 provider만(claude만 실측 확인, D-2 caveat 3) | `opal_agent.py:117` |
| `duration_ms` | `int \| None` | `None` | 소요 시간(ms) | `opal_agent.py:118` |
| `raw` | `Any` (dict 기본) | `{}` | provider 원본 출력 전체(provider별 스키마 상이 — §1.5.2) | `opal_agent.py:119` |

이 7필드는 **라이브러리 반환값**(`call_agent()` 호출 시)이며, CLI 표면(`run.sh`)에서 얻는 stdout과는 노출 방식이 다르다(§1.5.2).

#### 1.5.2 CLI stdout 출력 스키마 (`main()` 표면 — 루프 액션 에이전트가 실제로 소비하는 표면)

`main()`(`opal_agent.py:677-728`)은 라이브러리 호출은 **항상 `output_format="json"`으로 고정 실행**한다(`:714`, 주석: "라이브러리는 항상 JSON으로 실행해 session_id·메타를 확보한다"). `--json`/`--text`는 그 결과를 **어떻게 표시할지**만 분기한다(`display` 변수, `:722-726`).

**① `--json` 지정 시 stdout** (스킬 파싱용, 이번 태스크의 결과 파일 규약이 사용할 표면):

```python
json.dump(result.raw, sys.stdout, ensure_ascii=False, indent=2, default=str)  # :723
```

즉 stdout에 찍히는 JSON은 `AgentResult` 전체가 아니라 **`result.raw`만**이다 — provider별로 내용이 다르다:

| provider | `raw` 구성 | 근거 |
|----------|-----------|------|
| claude | provider CLI(`claude --output-format json`)가 낸 JSON 객체 **원문 그대로**(`data`) — opal-agent가 읽는 서브필드는 `result`(텍스트)·`session_id`·`is_error`·`total_cost_usd`·`duration_ms`뿐이나, 원본 객체의 다른 필드(claude CLI 자체 스키마, 예: `type`/`subtype`/`num_turns`/`usage` 등)도 그대로 남아 stdout에 포함될 수 있음(코드가 서브셋만 소비할 뿐 필터링하지 않음) | `opal_agent.py:199-211`(ClaudeAdapter.parse_result, `raw=data`) |
| gemini | gemini CLI JSON 원문 그대로(`data`) | `opal_agent.py:241-256` |
| codex | opal-agent가 **재구성**한 `{"events": [...JSONL 이벤트 전체...], "usage": {...}}` — codex는 원본이 JSONL 스트림이라 원문 그대로가 아니라 이벤트 배열로 감싼 형태 | `opal_agent.py:299-341` |
| grok | grok CLI JSON 원문 그대로(`data`, 방어적 파싱) | `opal_agent.py:371-387` |
| cursor | cursor CLI JSON 원문 그대로(`data`) | `opal_agent.py:415-429` |
| antigravity | JSON 미지원 provider라 opal-agent가 **합성**한 `{"text": "...", "provider": "antigravity"}` (원본 stdout 텍스트 전체를 그대로 담음, 에이전트 chrome 포함 가능) | `opal_agent.py:466-478` |

> **1차 릴리스는 claude 한정**(TASK.md §확정된 설계 방향 6)이므로, 결과 파일 규약(R-2)이 실제로 다뤄야 하는 것은 **claude 원문 JSON 그대로**다. 이 JSON에서 결정론적으로 존재가 보장되는 키는 opal-agent가 명시적으로 읽는 4개(`result`/`session_id`/`is_error`/`total_cost_usd`/`duration_ms`)뿐이며, 그 외 claude CLI 자체 스키마 필드는 opal-agent 코드상 문서화되어 있지 않다 — PLAN에서 결과 파일 스키마를 이 4개 필드 중심으로 설계하거나, claude CLI 공식 문서로 원본 스키마를 추가 조사할지 결정 필요(§5 리스크 R-H 신규).

**② `--text`(기본) 지정 시 stdout**:

```python
print(result.text)   # :726 — 순수 텍스트, JSON 아님
```

**③ 성공/실패 각각의 stdout 형태 요약**:

| 케이스 | stdout(`--json`) | stdout(`--text`) | 종료 코드 |
|--------|------------------|-------------------|----------|
| 정상 성공(`is_error=False`) | provider raw JSON 객체 | 응답 텍스트 | `0` |
| 에이전트 자체 보고 실패(`is_error=True`, 프로세스는 정상 종료) | provider raw JSON 객체(단, 내부 `is_error`/`error` 필드가 true) | 응답 텍스트(에러 메시지일 수 있음) | `1` |
| opal-agent 레벨 하드 에러(예외) | **없음** — stdout 전혀 안 찍힘, `stderr`에만 `[opal-agent 오류] {메시지}` | 좌동 | `2` |

#### 1.5.3 종료 코드 체계

`main()` 반환값 = 프로세스 exit code (`opal_agent.py:677-728`):

| 코드 | 조건 | 근거 |
|------|------|------|
| `0` | 정상 실행 + `result.is_error == False` | `opal_agent.py:728`: `return 1 if result.is_error else 0` |
| `1` | 정상 실행(프로세스는 성공)이나 에이전트가 `is_error=True`로 자체 보고 | `opal_agent.py:728` (동일 라인의 else 분기) |
| `2` | `OpalAgentError`(및 하위 클래스 `ClaudeNotFoundError`/`OpalAgentTimeout`) 발생 — CLI 실행 자체가 실패 | `opal_agent.py:718-720`: `except OpalAgentError as exc: print(..., file=sys.stderr); return 2` |

#### 1.5.4 에러 계약 — 케이스별 stdout/stderr 형태

예외 클래스 계층(`opal_agent.py:76-86`): `OpalAgentError`(베이스) ← `ClaudeNotFoundError`, `OpalAgentTimeout`. **`main()`은 `OpalAgentError` 한 곳에서만 캐치**(`:718`)하므로 하위 클래스 전부 동일한 종료 코드(`2`)·동일한 stderr 포맷으로 수렴한다.

| 케이스 | 예외 | 발생 위치 | stdout | stderr | 종료 코드 |
|--------|------|----------|--------|--------|----------|
| 타임아웃 초과 | `OpalAgentTimeout` | `_run()` — `subprocess.run(..., timeout=...)`이 `TimeoutExpired` 발생 시 변환 | 없음 | `[opal-agent 오류] {provider} 실행이 {timeout}초를 초과했습니다.` | `2` | `opal_agent.py:592-604` |
| provider CLI 미설치(PATH 부재) | `ClaudeNotFoundError` | `_run()` — `shutil.which(bin_name)`이 `None` | 없음 | `` [opal-agent 오류] `{bin_name}` 실행 파일을 PATH에서 찾을 수 없습니다. ... `` | `2` | `opal_agent.py:580-585` |
| provider CLI 비정상 종료(subprocess exit ≠ 0) | `OpalAgentError` | `_run()` — `proc.returncode != 0` | 없음 | `[opal-agent 오류] {provider} 비정상 종료 (exit {returncode})\nstderr: {원본 stderr}` | `2` | `opal_agent.py:612-616` |
| JSON 파싱 실패(provider 출력이 유효 JSON 아님) | `OpalAgentError` | `_loads()` — `json.JSONDecodeError` | 없음 | `[opal-agent 오류] {provider} JSON 출력 파싱 실패: {exc}\n원본: {stdout 앞 500자}` | `2` | `opal_agent.py:490-497` |
| JSON이 객체가 아님(배열/스칼라 등) | `OpalAgentError` | `_loads()` | 없음 | `[opal-agent 오류] {provider} JSON 출력이 객체가 아닙니다: {타입명}` | `2` | `opal_agent.py:498-501` |
| codex JSONL에 유효 이벤트 0개 | `OpalAgentError` | `CodexAdapter.parse_result()` | 없음 | `[opal-agent 오류] codex --json 출력 파싱 실패(이벤트 없음). 원본: {stdout 앞 500자}` | `2` | `opal_agent.py:329-332` |
| 알 수 없는 provider 지정 | `OpalAgentError` | `call_agent()` — `provider not in _ADAPTERS` | 없음 | `[opal-agent 오류] 알 수 없는 provider: '{provider}'. 지원: {목록}` | `2` | `opal_agent.py:536-539` |
| cold(`new_session_id`)·warm(`session_id`) 동시 지정 | `OpalAgentError` | `_run()` — 상호배타 검증(단일 chokepoint) | 없음 | `[opal-agent 오류] new_session_id(cold)와 session_id(warm resume)는 동시 지정할 수 없습니다.` | `2` | `opal_agent.py:567-570` |
| cold `--session-id`를 미지원 provider(claude 외)에 지정 | (예외 아님 — **경고만**) | `_run()` | 정상 진행(무시하고 계속) | `[opal-agent 경고] provider '{provider}'는 caller-supplied session id(--session-id)를 지원하지 않아 무시됩니다.` | 해당 없음(정상 종료 코드) | `opal_agent.py:571-576` |
| `--effort`를 미지원 provider에 지정 | (예외 아님 — **경고만**) | `main()` | 정상 진행 | `[opal-agent 경고] provider '{provider}'는 --effort를 지원하지 않아 무시됩니다. ...` | 해당 없음 | `opal_agent.py:693-698` |

**결과 파일 규약(R-2) 설계 시사점**: 하드 에러(종료 코드 `2`)는 stdout에 아무 것도 남기지 않으므로, 비동기 축에서 `stdout > result.json` 리다이렉트만으로는 하드 에러 케이스를 결과 파일에서 구분할 수 없다(파일이 비어 있거나 존재하지 않음). 종료 코드와 stderr를 **함께** 캡처해야만 "완료(성공/에이전트 실패)" vs "미완료(하드 에러)"를 결정론적으로 구분할 수 있다 — 예: `run.sh ... > result.json 2> result.err.log; echo $? > result.exitcode`.

### 1.6 opal-agent 능력 매트릭스 (요약표)

> PM Gate 보완 지시(2/3) 반영 — §4 발견 사항의 근거를 표로 집약.

| 기능 | 지원 여부 | 근거 |
|------|----------|------|
| 동기 호출(블로킹, 반환까지 대기) | O | `_run()`이 `subprocess.run(...)`으로 블로킹 실행 (`opal_agent.py:592-600`) — 반환 시점에 이미 전체 출력 확보 |
| `--resume <session_id>` (warm) | O (claude 포함 대다수 provider) | `ClaudeAdapter.supports_resume = True`(`opal_agent.py:176`), `--resume` cmd 매핑(`:195-196`); CLI 옵션 문서화(`README.md:146`) |
| `--session-id <id>` (cold, caller-supplied) | O (**claude 전용**) | `ClaudeAdapter.supports_session_assign = True`(`opal_agent.py:178`), `--session-id` cmd 매핑(`:193-194`); 타 provider는 `_run()`에서 경고 후 무시(`:571-576`) |
| `--allowed-tools`(CLI) / `--allowedTools`(claude 실제 플래그) | O | `ClaudeAdapter.build_invocation()` — `--allowedTools` 매핑(`opal_agent.py:191-192`); CLI 인자 정의(`:643-646`) |
| `--output-format json` / `--json`(CLI 표시) | O | 라이브러리는 항상 `output_format="json"`으로 실행(`main():714`), claude 어댑터가 `--output-format json` cmd 추가(`:181-182`) + JSON 파싱(`:199-211`) |
| 백그라운드(비동기) 실행 | **X (opal-agent 내장 기능 없음)** | `_run()`은 `subprocess.run`(블로킹 전용, `opal_agent.py:592-600`)만 사용 — nohup/데몬화/폴링 API 부재. 비동기 축은 호출측(루프 액션 에이전트가 Bash `run_in_background` + stdout/stderr/exitcode 파일 리다이렉트, §1.5.4 참조)에서 감싸야 함 |

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 전환 대상은 OPAL 내부 도구(opal-agent)와 내부 문서이며 외부 라이브러리/API 조사가 필요한 새 의존성이 없다(TASK.md §기술 스택: Python/Bash 표준 라이브러리만).

### 2.1 라이브러리/API 조사

- N/A

### 2.2 버전 호환성

- N/A — opal-agent는 Python 3.10+ 표준 라이브러리만 사용(D-2 README:7), 외부 패키지 버전 제약 없음.

## 3. 영향 범위

### 3.1 직접 영향

- `opal/agents/opal-loop-action-agent/AGENT.md` — §실행 프로세스(T1~T5+G) 전체, §행동 규칙 항목 6, 신규 §결과 파일 규약(R-2)·§생성자 resume 절차(R-3)·§allowedTools 표준(R-4)·§플랫폼 가용성(R-6) 섹션 추가.
- `opal/skills/opal-pilot-project-loop/SKILL.md` — §태스크 내부 파이프라인, §디스패치(루프 액션 에이전트) 절의 "내부 디스패치" 서술이 Agent 도구 전제 문구와 공존하지 않도록 정합(R-5).
- `opal/core/references/opal-harness.md` §5(Observability stub)·§6(Model Mapping) — opal-agent 채널 항목 보강 여부 결정(R-5).
- `opal/core/references/harness/observability.md` — "아이콘 룩업"·"디스패치 선언 형식" 절(§40-59)이 "Agent 도구로 에이전트를 디스패치할 때"로 명시되어 있어(`:46`), opal-agent 채널 디스패치 시 동일 관측 규칙 적용 방식 정의 필요.

### 3.2 간접 영향

- `opal-evaluator-agent`, `opal-test-agent`, `opal-convention-checker`, `opal-security-checker`, `opal-fe-agent`/`opal-be-agent`/`opal-db-agent`/`opal-task-agent`(생성자) — 이들 AGENT.md 자체는 변경 대상이 아니지만(TASK.md §범위에 미포함), 이번 태스크로 이들이 opal-agent CLI를 통해 headless(`claude -p`)로 호출되는 방식이 신설된다. 각 AGENT.md의 "실행 프로세스"가 헤드리스 워커 컨텍스트(`[WORKER]` 마커, fresh 프로세스, 세션 컨텍스트 미공유 — D-2 README:169-170)에서도 그대로 동작하는지는 R-7 실증에서 확인해야 하며, 이번 ANALYSIS에서는 미확인 리스크로 §5에 기재한다.
- `opal-task-action-agent`(oppd), `opal-sdd-action-agent`(opsdd) — TASK.md §범위에서 명시적으로 전환 대상 제외("oppd/opsdd 액션 에이전트 전환"은 제외). 이번 개정이 이 두 액션 에이전트의 AGENT.md 서술과 구조적 유사성(동형 선례, D-10)을 가지므로, 067 이후 유사 전환 태스크가 후속될 가능성이 있으나 이번 범위 밖.
- 컨벤션/보안 체커의 T4b 인라인 경량화 경로(저위험 슬라이스)는 opal-agent 호출 자체가 발생하지 않는 경로이므로 이번 전환의 직접 영향 밖(내부 디스패치가 실제로 일어나는 고위험 케이스만 영향).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경
- [ ] API 인터페이스 변경
- [x] 설정/환경변수 변경 — 없음(구독 기반 로컬 `claude -p` 그대로 사용, `memory/console-brain-subscription-auth.md` 선례). 체크 표기는 "변경 없음 확인됨"의 의미.
- [ ] 빌드/배포 파이프라인 변경

## 4. 핵심 발견 사항

1. **4축 서술은 2곳(명시)+6곳(암묵) 전환 대상이다.** `opal-loop-action-agent/AGENT.md`에서 "Agent 도구"가 명시적으로 등장하는 곳은 T1(`:42`)과 행동 규칙 6번(`:139`) 단 2곳뿐이지만, T2~T4b(`:46-71`)의 "내부 디스패치" 서술 전부가 Agent 도구 방식을 암묵적으로 전제한다 — 개정 시 명시/암묵 구분 없이 §실행 프로세스 전체를 재작성해야 한다(TASK.md R-1 AC와 일치).
2. **opal-agent는 이번 태스크에 필요한 핵심 기능(동기 호출·resume·session-id·allowedTools·JSON 출력)을 모두 기존 기능 범위에서 지원한다**(§1.6 매트릭스) — 개조 없이 사용 가능하다는 TASK.md §범위의 전제가 코드 근거로 확인된다. 단, **백그라운드 실행(비동기 축)은 opal-agent 자체에 내장 기능이 없다** — `_run()`(`opal_agent.py:558-618`)은 `subprocess.run`(블로킹)만 사용하며 nohup/데몬화/폴링 API가 없다. 비동기화는 호출측(루프 액션 에이전트가 Bash 도구의 `run_in_background` + stdout 리다이렉트)에서 구현해야 한다 — 이는 "opal-agent 도구 자체의 기능 개조" 범위가 아니라 "opal-agent를 감싸는 호출 패턴"이므로 TASK.md §범위 제외 대상(도구 개조)에 해당하지 않는다고 판단되나, PLAN에서 이 경계를 명문화할 필요가 있다.
3. **T2(생성자 축 내 test-agent RED 작성)와 T4a(test-agent GREEN 검증)는 동일 에이전트(opal-test-agent)이지만 TASK.md의 동기/비동기 이원화 기준으로는 서로 다른 축에 속한다** — TASK.md §확정된 설계 방향 2는 "T1 설계+T2 시나리오·T3 구현"을 장시간(비동기)으로, "T4a 검증 실행"을 단시간(동기)으로 분류한다. 즉 test-agent라는 "축"이 호출 시점(T2 vs T4a)에 따라 다른 호출 모드를 가지며, AGENT.md D-1의 "4축(생성자·Evaluator·test-agent·checker)" 명명과 TASK.md의 "동기/비동기 이원화" 명명이 1:1 대응하지 않는다 — R-1 개정 시 이 불일치를 명확히 해소해야 한다(§5 리스크 R-A로 기재).
4. **T1→T3 생성자 resume 연속성은 opal-agent의 claude 어댑터가 이미 지원하는 기능(cold `--session-id` + warm `--resume`)으로 구현 가능하다** — `ClaudeAdapter`(`opal_agent.py:171-211`)가 `new_session_id`(cold prime, T1에서 지정) → `session_id`(warm resume, T3에서 재개)를 상호배타 필드로 처리한다(D-3 `opal_agent.py:193-196`). 단, T1을 cold prime(`--session-id`)으로 시작할지 자연 발급된 session_id를 그대로 재사용할지는 PLAN 설계 결정 사항이다.
5. **하네스 §5 Observability는 "Agent 도구로 에이전트를 디스패치할 때"를 아이콘 룩업·선언 형식의 트리거로 명시**(D-6 `observability.md:46`) — opal-agent 채널로 내부 디스패치가 전환되면 이 관측 규칙이 그대로 적용되는지(예: opal-agent 호출 시에도 아이콘 선언을 유지할지) 정의가 필요하다. 단, 이 절의 적용 주체는 "PM"(오케스트레이터)이고 루프 액션 에이전트 내부 디스패치는 PM 발화가 아니므로, 실제로는 루프 액션 에이전트 자신의 결과 요약 방식 문제로 축소될 수 있다 — PLAN에서 적용 범위를 좁혀 정의할 필요가 있다.
6. **결과 파일 규약(R-2)의 유일한 결정론적 매체는 하드 에러 시 비어 있다** — `--json` stdout 리다이렉트만으로는 opal-agent 레벨 하드 에러(종료 코드 `2`, §1.5.3~1.5.4)를 구분할 수 없다(stdout에 아무 것도 안 남음). 결과 파일 규약은 stdout뿐 아니라 종료 코드·stderr까지 함께 파일로 캡처하는 3-분리 규약(예: `result.json`/`result.err.log`/`result.exitcode`)으로 설계해야 완료 판정이 결정론적이다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-A | test-agent 축의 동기/비동기 이원화 모호성(T2=비동기 그룹 vs T4a=동기 그룹, 동일 에이전트) | 중 | `opal/agents/opal-loop-action-agent/AGENT.md:46-49,62-65` / TASK.md §확정된 설계 방향 2 |
| R-B | opal-agent에 백그라운드/폴링 내장 기능 없음 — 비동기 축은 호출측(Bash `run_in_background`)에서 구현 필요, 이번 태스크가 "opal-agent 개조 없이" 처리 가능한지 PLAN에서 재확인 필요 | 중 | `opal/tools/opal-agent/opal_agent.py:592-618`(subprocess.run 블로킹 전용) |
| R-C | 헤드리스 워커(claude -p, `[WORKER]` 마커)는 fresh 프로세스로 세션 컨텍스트를 공유하지 않는다 — 현재 Agent 도구 디스패치 방식(부모 세션의 대화 컨텍스트 상속)과 정보 전달량이 달라, 각 생성자/Evaluator/test-agent/checker AGENT.md가 요구하는 입력이 프롬프트에 전부 명시적으로 재주입되어야 한다 | 중 | `opal/tools/opal-agent/README.md:169-170` |
| R-D | Bash 도구 타임아웃(기본 2분·최대 10분) 상한 — 단시간 축(G·T4a·T4b)이 실제로 이 상한 내에 완료된다는 실측 근거는 아직 없음(065에서는 Agent 도구 기반이라 상한이 다름) | 중 | TASK.md §제약 조건: "Bash 타임아웃(기본 2분·최대 10분)이 동기 호출의 상한" |
| R-E | claude 1차 릴리스 한정이나, 타 provider(gemini/codex/grok/cursor)는 opal-agent README §검증 상태 기준 "명령 조립 검증" 수준에 그침(E2E 미검증) — R-6(플랫폼 가용성 표) 작성 시 이 구분을 명확히 반영해야 함 | 저 | `opal/tools/opal-agent/README.md:40-49`(검증 상태 표) |
| R-F | 결과 파일 규약(R-2) 신설 시 경로 충돌·동시성(같은 태스크 폴더 내 여러 비동기 축 동시 실행) 처리 방식 미정 | 중 | TASK.md §요구사항 R-2(AC: 재시도/blocked 처리 명문화 요구, 현재 무근거) |
| R-G | opal-agent `--model`은 실모델명을 그대로 전달할 뿐 레벨명(`light`/`standard`/`advanced`) 자동 치환 로직이 없다 — 루프 액션 에이전트가 opal-model-mapping.md 매핑을 스스로 적용해 실모델명을 조립해야 하며, 이 책임 소재가 AGENT.md에 명문화되지 않으면 모델 매핑 누락 위험 | 저 | `opal/tools/opal-agent/opal_agent.py:637`(`--model` help 텍스트에 레벨 변환 언급 없음), `~/.opal/references/opal-model-mapping.md` §4 |
| R-H | claude `--output-format json` 원본 스키마 중 opal-agent가 명시적으로 소비하는 필드(`result`/`session_id`/`is_error`/`total_cost_usd`/`duration_ms`) 외의 필드는 opal-agent 코드/문서 어디에도 전체 목록화되어 있지 않음 — 결과 파일 규약이 이 필드들 이상을 참조해야 한다면 claude CLI 공식 문서로 별도 조사 필요 | 저 | `opal/tools/opal-agent/opal_agent.py:199-211`(ClaudeAdapter.parse_result, raw 원문 그대로 전달) |
| R-I | 하드 에러(종료 코드 2) 시 stdout이 완전히 비므로, `stdout > file` 리다이렉트만으로는 비동기 축의 "미완료" 상태를 파일 존재/내용만으로 결정론적으로 판별할 수 없음 — 결과 파일 규약은 stdout·stderr·exit code 3종을 함께 캡처해야 함 | 중 | `opal/tools/opal-agent/opal_agent.py:718-720`(하드 에러는 stderr에만 출력, stdout 없음) |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Markdown (AGENT.md/SKILL.md/하네스 문서) | - |
| 언어 | Python | 3.10+ (표준 라이브러리만, `opal/tools/opal-agent/README.md:7`) |
| 셸 | Bash | `run.sh` 래퍼 |
| 헤드리스 CLI | Claude Code (`claude -p`) | `--resume`/`--session-id`/`--allowedTools`/`--output-format json` 지원 (D-2/D-3) |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan (본 파이프라인) | PLAN 단계에서 이 ANALYSIS를 입력으로 설계 결정(결과 파일 규약 스키마 등) 구체화 |

### 6.3 추천 MCP

해당 없음 — 외부 라이브러리 문서 조회가 필요한 신규 의존성이 없다(전부 OPAL 내부 소스 분석).

---

## 변경이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-07-17 | 최초 작성 — 4축 디스패치 현황 전수 식별, opal-agent 능력 매트릭스, 결과 파일 규약 설계 현황, 하네스·oppl SKILL 전제 서술 목록, 리스크 7건(R-A~R-G) 도출 (066) |
| 2026-07-17 | PM Gate 보완(1/3) — §1.5 opal-agent 출력 계약 현황 신설(AgentResult 7필드·CLI stdout JSON 스키마 provider별·종료 코드 3종·에러 계약 9케이스 표), §1.6 능력 매트릭스 표 신설(§4 근거 집약), §4에 발견사항 6 추가, §5에 리스크 R-H·R-I 추가 (066) |
