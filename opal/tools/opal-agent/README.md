# opal-agent

여러 LLM CLI(**claude / gemini / codex / grok**)를 비대화형(headless) 서브에이전트로
호출하는 **Python 라이브러리 + CLI**. OPAL 스킬·오케스트레이터가 다른 에이전트에게
작업을 위임할 때 사용한다.

- **무의존성** — Python 3.10+ 표준 라이브러리만 사용
- **provider 어댑터 계층** — 공통 API 뒤에서 provider별 CLI 차이를 흡수
- **단발 기본 + 다중 턴** — `session_id`로 resume 이어가기
- **JSON 출력 우선** — provider별 파싱 격리

## 설치/배포 경로

```
~/.opal/tools/opal-agent/run.sh  →  ~/.opal/.venv/bin/python opal_agent.py
```

`run.sh`가 OPAL 전용 가상환경(`~/.opal/.venv`)의 python으로 `opal_agent.py`를 실행한다
(state-tool·brain-tool 등 다른 OPAL 파이썬 툴과 동일 관례). 표준 라이브러리만 쓰므로 추가 의존성은 없다.

**bin symlink 없음** — opal-agent는 스킬이 호출하는 툴이라 다른 skill-called 툴처럼
`~/.opal/tools/opal-agent/run.sh` 전체 경로로 부른다. (`~/.opal/bin` symlink는 사용자가
터미널에서 직접 타이핑하는 `opal-cli` 전용.) `opal-cli update`가 `~/.opal/tools/` 전체를
재배포하므로 opal-agent도 자동 포함된다 — install 스크립트 변경 불필요.

## provider별 매핑 (공식 CLI 문서 + 실측, 2026-07)

| | claude | gemini | codex | grok (xAI Build) | cursor |
|---|---|---|---|---|---|
| 실행 | `claude -p` | `gemini -p` | `codex exec` | `grok -p` | `cursor-agent -p` |
| 시스템 프롬프트 | `--append-system-prompt` (**추가**) | `GEMINI_SYSTEM_MD` env (**교체**) | `-c model_instructions_file` (**교체**) | `--system-prompt-override` (**교체**) | 플래그 없음 → 프롬프트에 **접붙임**(best-effort) |
| JSON | `--output-format json` (단일) | `--output-format json` (단일) | `--json` (**JSONL 스트림**) | `--output-format json` (단일) | `--output-format json` (단일, claude와 유사 스키마) |
| resume | `--resume <id>` (신규 세션은 `--session-id <id>`로 caller-supplied cold 지정 가능) | `--resume <id>` | `exec resume <id>` (**별도 서브커맨드**) | `--resume <id>` | `--resume <id>` |
| 자동 실행 | `--allowedTools` | `--approval-mode yolo` | `--sandbox workspace-write` | `--tools` | `--force` |
| 모델 | `--model` | `-m` | `-m` | `-m grok-4.5` | `--model` (gpt-5, sonnet-4 …) |
| effort | `--effort` (low/medium/high/xhigh/max) | ❌ | `-c model_reasoning_effort=` | `--effort` | ❌ (모델명 내장 `sonnet-4-thinking`, `model[effort=high]`) |

> **antigravity**는 위 표에 없다(text-only 2급) — 아래 별도 절 참조. effort 미지원(모델 표시명에 `(High)`/`(Thinking)` 내장).

### 검증 상태

| provider | 상태 |
|----------|------|
| **claude** | ✅ 엔드투엔드 실측 (단발·resume·json/text) |
| **codex** | ✅ 엔드투엔드 실측 (단발·resume·session_id/usage 추출). 실측으로 `--ask-for-approval`·resume `--sandbox` 미지원을 확인해 반영 |
| **gemini** | ⚠️ 명령 조립 검증. CLI 실행은 인증 티어 필요(설치 환경 의존) |
| **grok** | ⚠️ 공식 문서 기반. CLI 미설치로 실행 미검증. JSON 세부 스키마는 문서 미명시 → 방어적 파싱 |
| **cursor** | ⚠️ 실제 `cursor-agent --help`로 플래그 검증(문서에 있던 `--trust`가 설치 버전엔 없어 제외). 실행은 `cursor-agent login` 인증 필요 → E2E 미검증 |
| **antigravity** | ✅ 엔드투엔드 실측(agy v1.1.1). 단, **text-only 2급** — 아래 caveat |

> **cursor caveat**: 시스템 프롬프트 전용 플래그가 없어(`.cursor/rules`·`AGENTS.md`·`CLAUDE.md` 파일 기반) `system_prompt`는 사용자 프롬프트 앞에 접붙이는 best-effort 방식이다. 진짜 시스템 프롬프트가 필요하면 워크스페이스에 rules 파일을 두는 방식을 권장.

### antigravity (agy) — text-only 2급 어댑터

실행: `agy -p "<프롬프트>"` · 모델: `--model "Claude Sonnet 4.6 (Thinking)"` 등(표시명, `agy models`로 조회) · 자동승인: `--dangerously-skip-permissions` · resume: `--conversation <ID>`/`--continue`

실측(agy v1.1.1)으로 확인된 **제약** — 다른 provider보다 기능이 제한적이다:

- **JSON/구조화 출력 플래그가 없다** → 텍스트만. `session_id`·`cost_usd`·`duration_ms` 확보 불가(모두 `None`).
- **resume**: `--conversation <ID>`는 있으나 ID를 출력에서 얻을 수단이 없어(JSON 없음) 자동 캡처 불가. 외부에서 아는 ID를 넘기거나 `--continue`(최근 대화)만 실질적.
- **출력 오염**: agy 실행 시 환경에 따라 에이전트 chrome(부트스트랩 로그·`알투:` 같은 에이전트명 접두)이 stdout에 섞일 수 있다. `text`에 그대로 담기므로 호출측에서 후처리가 필요할 수 있다.
- 모델명이 표시 문자열(공백 포함)이라 정확한 지정은 `agy models` 출력 참조.

> 안정적 프로그래매틱 통합이 필요하면 CLI보다 공식 **Antigravity Python SDK**가 더 나은 경로다.

### 주의(caveat)

1. **시스템 프롬프트 의미가 다르다** — claude만 기본 프롬프트에 **추가(append)**, gemini/codex/grok는 **교체(replace)**.
2. **codex는 JSONL 스트림** — 단일 JSON이 아니라 이벤트 스트림을 파싱해 최종 agent 메시지·`thread_id`·`usage`를 추출한다. resume는 `codex exec resume` 별도 서브커맨드로 `--sandbox`를 받지 않는다(원 세션에서 상속).
3. **비용(cost) 필드** — claude만 `total_cost_usd`를 제공. gemini/codex는 토큰 usage만, grok은 미명시.
4. **gemini/grok JSON 스키마 세부 필드**는 공식 문서 미명시라 방어적으로 파싱(누락 필드는 `None`).

## 라이브러리로 사용

```python
from opal_agent import call_agent

# 단발 호출 (기본 provider=claude)
result = call_agent(
    "이 저장소의 테스트 커버리지를 요약해줘",
    provider="claude",
    system_prompt="너는 QA 전문가다.",
    allowed_tools=["Bash", "Read", "Grep"],
    model="claude-sonnet-5",
    effort="high",              # claude/codex/grok만 지원 (그 외 무시)
    cwd="/path/to/repo",
    timeout=300,
)
print(result.text, result.session_id, result.cost_usd, result.is_error)

# 다른 provider
r2 = call_agent("release notes 작성해줘", provider="codex")

# 다중 턴 — session_id로 이어가기
follow = call_agent("방금 결과에서 가장 취약한 모듈은?",
                    provider="claude", session_id=result.session_id)
```

### 반환 구조 (`AgentResult`)

| 필드 | 의미 |
|------|------|
| `text` | 최종 응답 텍스트 |
| `provider` | 사용한 provider |
| `session_id` | resume용 세션 ID (지원/확보 가능 시) |
| `is_error` | 에이전트 오류 여부 |
| `cost_usd` | 총 비용(USD) — 제공 provider만 |
| `duration_ms` | 소요 시간(ms) |
| `raw` | 원본 출력 (dict, codex는 `{events, usage}`) |

### 예외

| 예외 | 발생 조건 |
|------|----------|
| `ClaudeNotFoundError` | provider CLI 미설치(PATH 부재) |
| `OpalAgentTimeout` | hard timeout, 또는 stream 모드의 heartbeat timeout |
| `OpalAgentError` | 비정상 종료 / 파싱 실패 / 알 수 없는 provider 등 |

`is_error=true`는 예외가 아니라 결과에 담겨 반환된다.

세 예외 모두 `code` 속성으로 안정적 실패 식별자를 노출한다(문자열 매칭 불필요) —
`timeout_limit_exceeded`, `output_format_invalid`, `timed_out`, `framing_error`.

## CLI로 사용

```bash
# 텍스트 출력 (기본), provider 지정
opal-agent "이 함수 리팩터링해줘" --provider claude --system-prompt "너는 시니어 엔지니어다"

# 전체 JSON 출력 (session_id·메타 포함, 스킬 파싱용)
opal-agent "..." --provider codex --model gpt-5.4 --json

# 세션 이어가기
opal-agent "후속 질문" --provider claude --resume <session_id> --json

# stdin으로 프롬프트 전달
echo "긴 프롬프트..." | opal-agent --provider gemini --json
```

| 옵션 | 설명 |
|------|------|
| `--provider P` | `claude`(기본) \| `gemini` \| `codex` \| `grok` |
| `--system-prompt S` | 에이전트 역할 부여 |
| `--model M` | 모델 지정 |
| `--effort L` | 추론 강도 (claude: `low`~`max`, codex/grok 지원). 미지원 provider엔 경고 후 무시 |
| `--allowed-tools A,B` | 허용 도구 화이트리스트 (콤마 구분) |
| `--cwd DIR` | 작업 디렉토리 |
| `--timeout SEC` | 타임아웃(초, 기본 300) |
| `--resume ID` | 이어갈 세션 ID (warm resume, `--session-id`와 상호배타) |
| `--session-id ID` | 신규(cold) 세션에 지정할 caller-supplied session id — **claude만** 지원(`--resume`과 상호배타) |
| `--bin PATH` | CLI 바이너리 경로 오버라이드 |
| `--run-dir DIR` | attempt 산출물 디렉토리. `--phase`와 **함께** 줘야 opal-agent가 산출물 writer가 된다(§attempt 산출물 소유) |
| `--phase NAME` | 산출물 파일명 접두 문자열. opal-agent는 phase 의미론을 모른다 |
| `--attempt aN` | 재시도 접미 — `<phase>.aN.*` |
| `--heartbeat-timeout-sec SEC` | 무출력 허용 상한. **stream mode 전용**(D10) — sync에는 적용하지 않으며 heartbeat 부재를 `timed_out` 사유로 쓰지 않는다. 기본 없음 |
| `--terminate-grace-sec SEC` | timeout 회수 시 SIGTERM 후 SIGKILL까지 유예(기본 `5`) |
| `--max-timeout-sec SEC` | 전역 hard timeout 상한. `--timeout`이 넘으면 프로세스를 만들지 않고 `timeout_limit_exceeded`로 거부. 기본 없음 |
| `--phase-timeout-limit-sec SEC` | **호출자가 계산해 넘기는** phase별 상한. 초과 시 동일하게 거부. opal-agent는 phase별 상한 표를 갖지 않는다. 기본 없음 |
| `--opal-bootstrap on\|assistant\|off` | 서브에이전트 첫 줄 마커 어댑터(기본 `on`). `assistant`는 `[ASSISTANT]`→`session.assistant`, `off`는 `[WORKER]`→`session.worker`로 해석된다. setting의 `bootstrap: off`→`session.disabled`와는 다른 계약이다. |
| `--json` / `--text` / `--stream` | 출력 형식 (기본 `--text`). `--json`/`--text`/`--stream`은 상호배타. `--stream`은 claude 전용(§stream 모드 참조) |

종료 코드: 정상 `0`, 에이전트 오류(`is_error`) `1`, 실행 오류 `2`.

## stream 모드 (`--stream`, claude 전용, opt-in)

기본 `--json`/`--text` 경로는 프로세스 종료까지 블로킹한 뒤 결과를 일괄 반환한다 — 장시간 실행 중에는 진행 상황을 볼 수 없다. `--stream`은 claude CLI의 `--output-format stream-json`을 이용해 **실행 중에도** 이벤트를 흘려보내는 opt-in 경로다. 기존 `--json` 경로(단일 JSON 일괄 반환)는 **불변** — `--stream`을 지정하지 않으면 동작이 전혀 바뀌지 않는다.

### 사용법

```bash
# 표준출력을 파일로 리다이렉트 — 실행 중에도 파일이 증분 성장한다(JSONL)
~/.opal/tools/opal-agent/run.sh --provider claude --stream "긴 리팩터링 작업을 수행해줘" \
    > events.jsonl 2> events.err.log
echo $? > events.exitcode
```

- `--run-dir`·`--phase`·`--attempt`를 **하나도 주지 않으면** opal-agent는 내부 파일을 열지 않는다 — claude stream-json 각 줄을 opal-agent의 **자기 stdout으로 그대로(line-buffered) passthrough**할 뿐이다. 파일 증분 기록은 호출측 셸의 `>` 리다이렉트가 담당한다(단일 writer). `--run-dir`+`--phase`를 주면 대신 opal-agent가 산출물을 소유한다(§attempt 산출물 소유).
- `--stream`을 지정하면 내부적으로 `--output-format stream-json --verbose`가 **항상 자동 부착**된다. claude CLI는 `--verbose` 없이 `--output-format stream-json`을 쓰면 exit 1(사용법 에러)로 항상 실패하므로, 호출자가 별도로 `--verbose`를 챙길 필요가 없다.
- `--stream`은 **claude 전용**이다(`ClaudeAdapter.supports_stream = True`, 타 어댑터는 미지원). `--provider`가 claude가 아닌 상태로 `--stream`을 쓰면 즉시 `OpalAgentError`("provider '...'는 stream-json 실행 경로를 지원하지 않습니다")로 명시 실패한다 — 조용한 폴백은 없다.
- 실행이 끝나면 **마지막 유효한 `type: "result"` 이벤트**(마지막 물리 줄이 아니다)가 terminal candidate다. 여기서 기존 `--json` 경로와 동일한 5필드(`result`, `session_id`, `is_error`, `total_cost_usd`, `duration_ms`)를 추출한다 — 소비할 result가 하나도 없으면 `OpalAgentError`를 던진다. 판정 규칙은 §stream terminal framing 참조.
- CLI에서 `--stream`을 쓰면 실행 중 passthrough로 이미 전량 출력이 끝난 상태이므로, `main()`은 별도 dump 없이 `result.is_error` 기준 종료 코드(0/1)만 반환한다. 실행 오류는 기존과 동일하게 `2`.
- 라이브러리로 쓸 때는 `call_agent(..., output_format="stream-json")` — 호출측이 `sys.stdout`을 파일로 리다이렉트하거나 자체적으로 캡처해야 증분 기록이 이뤄진다.

### `--json`과의 관계

`--stream`은 `--json`을 대체하지 않는 **opt-in 별도 경로**다. 실행 중 진행 상황 관측이 필요한 장시간 비동기 작업에만 `--stream`을 쓰고, 그 외 일반 호출은 기존 `--json`/`--text`를 그대로 쓴다. 두 경로는 `_run()` 디스패치 단계에서 분기되며 서로의 동작에 영향을 주지 않는다.

## 실행 원시 기능 (attempt)

opal-agent는 호출자가 준 **timeout·출력 경로·mode**만 안다. round·수렴 판정·백로그·태스크
파이프라인 같은 상위 정책은 호출자 소유이며 이 도구에 들어오지 않는다. `phase`는 파일명
문자열일 뿐이라 opal-agent는 phase 목록도 phase별 정책도 갖지 않는다.

### process group과 watchdog

두 실행 경로 모두 루트 프로세스를 `start_new_session=True`로 **별도 process group**에 띄우고
PID·PGID를 attempt record에 남긴다. watchdog은 stdout read loop와 **독립된 monotonic timer
스레드**라, 출력이 전혀 없는 프로세스도 정확한 시점에 만료된다.

만료 시 `os.killpg(PGID, SIGTERM)` → `terminate_grace_sec` 대기 → `os.killpg(PGID, SIGKILL)`
순으로 그룹 전체(손자 포함)를 회수하고, **PGID 소멸을 확인한 뒤에만** `timed_out`을 확정한다.

| 인자 | 기본 | 의미 |
|------|------|------|
| `timeout` | 300 | hard timeout(초) — 두 mode 공통 |
| `heartbeat_timeout_sec` | `None` | 무출력 허용 상한. **stream 모드 전용** — sync에는 적용하지 않으며 heartbeat 부재를 `timed_out` 사유로 쓰지 않는다 |
| `terminate_grace_sec` | 5 | SIGTERM 후 SIGKILL까지 유예 |
| `max_timeout_sec` | `None` | 전역 hard timeout 상한 |
| `phase_timeout_limit_sec` | `None` | 호출자가 계산한 phase별 상한 |

`timeout` 요청값이 `phase_timeout_limit_sec`나 `max_timeout_sec`를 넘으면 **프로세스를 만들지
않고** `OpalAgentError(code="timeout_limit_exceeded")`로 거부한다. 상한값은 호출자가 인자로
넘긴다 — opal-agent는 그 값이 어느 정책에서 왔는지 모른다.

다섯 인자 모두 CLI에도 있다(`--timeout`, `--heartbeat-timeout-sec`, `--terminate-grace-sec`,
`--max-timeout-sec`, `--phase-timeout-limit-sec`). 실제 호출 경로가 `run.sh` 셸 호출이므로
라이브러리 전용 인자로 두면 상한 거부와 heartbeat 경계가 실제 경로에서 도달 불가해진다.
`--heartbeat-timeout-sec`는 CLI에서도 stream mode에서만 적용된다.

### attempt 산출물 소유

`run_dir`와 `phase`를 **함께** 주면 opal-agent가 파일명을 스스로 만들고 열고 닫는다. 파일 1개의
writer는 항상 opal-agent 프로세스 1개다. 셋 다 없으면 기존 stdout passthrough 동작이 그대로다.

| 파일 | mode | 기록 방식 |
|------|------|----------|
| `<phase>[.aN].events.jsonl` | stream | 줄 단위 **append + flush** — 실행 중 증분 관측이 목적이라 atomic rename을 쓰지 않는다 |
| `<phase>[.aN].result.json` | sync(`json`) | 단일 JSON 객체, temp write·fsync·atomic rename |
| `<phase>[.aN].err.log` | 공통 | atomic rename |
| `<phase>[.aN].exitcode` | 공통 | atomic rename — 프로세스 생존 중에는 **나타나지 않는다**. 관측자는 그 부재를 `running`의 근거로 쓴다 |
| `<phase>[.aN].attempt.json` | 공통 | atomic rename |

확장자와 실제 직렬화가 불일치하거나 JSONL 한 사건이 여러 물리 행에 걸치면
`OpalAgentError(code="output_format_invalid")`로 종료하고 `done`을 기록하지 않는다.

`attempt.json`은 PID·PGID·시작 fingerprint·heartbeat·terminal result·exit code 원문을 담는다.
외부 ledger는 이 파일을 **경로로만** 외래 참조한다(내용을 복제하지 않는다).

| 필드 | 의미 |
|------|------|
| `phase` / `attempt` / `mode` / `provider` | 호출 식별 (`mode`: `stream` \| `sync`) |
| `status` | `done` \| `running` \| `error` \| `timed_out` |
| `exit_class` | `ok` \| `impl_failure` \| `api_error` \| `timed_out` \| `output_format_invalid` \| `framing_error` |
| `pid` / `pgid` | 루트 프로세스와 그 process group |
| `pgid_reclaimed` | PGID 소멸 확인 여부 — `timed_out` 확정의 전제 |
| `exit_code` | 루트 exit code 원문 (시그널 종료는 음수) |
| `timeout_reason` | `null` \| `hard` \| `heartbeat` |
| `started_at` / `ended_at` / `duration_ms` | 실행 구간 |
| `fingerprint` | `provider`·`bin`·`cwd`·`output_format`·`argv_len`·`argv_sha256`·`timeout_sec`·`heartbeat_timeout_sec`·`terminate_grace_sec` (프롬프트 원문 대신 argv 해시) |
| `heartbeat` | `timeout_sec`·`count`·`last_at`·`expired` |
| `terminal` | terminal candidate result 이벤트 원본 (없으면 `null`) |
| `cost_used` | terminal candidate의 `total_cost_usd` — **합산이 아니다** |
| `unterminated_children` | stream 종료 시점 미종료 자식 task_id 목록 |
| `origin` | 진단 전용 |
| `outputs` | 실제로 기록한 산출물 경로 맵 |

### stream terminal framing

`analyze_stream(stdout) -> StreamVerdict`가 stream 전체를 단일 판정한다. "마지막 줄만 본다"와
"어디든 result가 있으면 성공" 두 규칙은 모두 폐기됐다.

1. 마지막 **유효 result**가 terminal candidate다.
2. 그 앞 result는 `session_id`가 같고 `result_index`가 **단조 증가**할 때만 선행 turn으로
   인정하며, 현재 결과로 소비하지 않는다. 둘 중 하나라도 깨지면 `error`다.
3. candidate 뒤에는 `EPILOGUE_ALLOWLIST`만 허용한다 — `type`이 아니라 **`subtype` 기준**으로
   `background_tasks_changed` / `task_updated` / `task_notification`이다.
4. epilogue를 순서대로 reduce한 **stream 종료 시점**에 등록된 모든 자식이 terminal이어야 한다.
   중간에 실행 중 task가 있다가 뒤에서 닫히면 허용한다.
5. 루트 exit 0 + PGID 소멸 + 최종 자식 terminal + result schema 성공이 모두 성립해야 `done`이다.

`StreamVerdict`는 `status`·`exit_class`·`terminal`·`cost_used`·`origin`·`unterminated_children`을
노출한다. `origin`은 **진단 정보로만 기록**하며 판정 분기 조건에 쓰지 않는다 — `origin`이 없는
stream도 정상이다.

## 스킬에서 호출

스킬이 **서브에이전트가 필요할 때** `SKILL.md` 안에서 Bash로 `run.sh`를 직접 호출한다
(state-tool 등과 동일):

```bash
~/.opal/tools/opal-agent/run.sh \
    --provider claude \
    --opal-bootstrap off \
    --system-prompt "너는 백엔드 전문 워커다." \
    --allowed-tools Bash,Read,Edit,Write \
    --json \
    "PLAN.md의 BE Step을 구현해줘. [필요 컨텍스트를 여기 전부 주입]"
```

- opal-agent 서브에이전트는 **fresh 프로세스**라 세션 컨텍스트를 공유하지 않는다 →
  필요한 컨텍스트를 프롬프트에 직접 주입한다. OPAL 워커 디스패치라면 `[WORKER]` 다음에
  `worker.dispatch` event id와 검증 가능한 receipt를 함께 주입해야 하며, 누락·stale·wrong-event
  receipt는 워커가 blocked로 반환한다.
- 반환 JSON의 `result`로 결과, `session_id`로 다중 턴(`--resume`).
- 비-claude 플랫폼(codex/gemini/grok/cursor/antigravity) 워커도 `--provider`로 디스패치 가능
  — Agent/Task 툴(claude 전용)로는 불가능한 크로스-프로바이더 서브에이전트.
- 미배포 환경이면 `bash ~/.opal/tools/opal-agent/run.sh ...` 또는
  `~/.opal/.venv/bin/python ~/.opal/tools/opal-agent/opal_agent.py ...`로 대체.

## OPAL 세션 마커 (`--opal-bootstrap on|assistant|off`)

`--opal-bootstrap`은 이름을 하위호환으로 유지하는 첫 줄 마커 어댑터다. 최종 상태는
`opal_agent.resolve_session_event()`와 `opal/core/AGENT.md`의 우선순위 계약으로 판정한다.

| 값 | 첫 줄 마커 | 로드 범위 |
|---|-----------|----------|
| `on` (기본) | 없음 | 비프로젝트면 `session.assistant`, 프로젝트면 `session.project`. 프로젝트 존재만으로 PM을 활성화하지 않음 |
| `assistant` | `[ASSISTANT]` | `session.assistant` — 프로젝트 brief와 PM 활성화를 모두 억제 |
| `off` | `[WORKER]` | `session.worker` — 전역 문서 0건, OPAL 워커는 별도 `worker.dispatch` receipt 필요 |

- **최우선 설정 게이트**: effective setting의 `bootstrap`이 정확히 `off`면 marker보다 먼저
  `session.disabled`가 선택되며 identity·PRINCIPLES·memory·PM·harness를 포함한 OPAL 문서를
  0건 로드한다. 이는 `--opal-bootstrap off`가 만드는 `session.worker`와 다르다.
- **PM JIT**: `session.project`에서 프로젝트 작업 또는 프로젝트 내 `//` 커맨드가 들어온 때
  `pm.activate`를 load·verify한 뒤에만 PM으로 전환한다.
- **이벤트 SSOT**: 필수 문서 목록은 `opal/core/references/events.json`, 전문·hash·receipt
  계약은 `opal/tools/event-loader`가 소유한다.

## cold session id 지정 (`--session-id`, claude 전용)

claude 서브에이전트를 처음(신규) 실행할 때, 호출자가 미리 만든 session id를 그 신규 세션에 지정하고 싶을 때 쓴다(브레인 등 상위 시스템이 세션 registry를 caller 쪽에서 관리하는 경우). `--resume`(warm, 기존 세션 이어가기)과는 반대 방향이며 둘은 상호배타다.

```bash
# 신규 세션을 caller-supplied UUID로 prime (cold)
~/.opal/tools/opal-agent/run.sh \
    --provider claude --session-id "3fa1c2e4-...-uuid" \
    --json "새 작업을 시작해줘"

# 이후 같은 세션을 이어가려면 warm resume(--resume)로 전환
~/.opal/tools/opal-agent/run.sh \
    --provider claude --resume "3fa1c2e4-...-uuid" \
    --json "이어서 진행해줘"
```

claude 외 provider(gemini/codex/grok/cursor/antigravity)에 `--session-id`를 지정하면 무시되고 stderr에 경고가 출력된다(`--effort` 미지원 경고와 동일 패턴).
