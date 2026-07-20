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
| `OpalAgentTimeout` | `timeout` 초과 |
| `OpalAgentError` | 비정상 종료 / 파싱 실패 / 알 수 없는 provider 등 |

`is_error=true`는 예외가 아니라 결과에 담겨 반환된다.

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
| `--opal-bootstrap on\|assistant\|off` | 서브에이전트 OPAL 부트스트랩 (기본 `on`). `assistant`면 프롬프트 첫 줄에 `[ASSISTANT]` 마커 주입 → 비서 tier(Phase A)만 로드(PM tier 승격 억제). `off`면 첫 줄에 `[WORKER]` 마커 주입 → 부트스트랩 전체 스킵(깨끗한 워커) |
| `--json` / `--text` / `--stream` | 출력 형식 (기본 `--text`). `--json`/`--text`/`--stream`은 상호배타. `--stream`은 claude 전용(§stream 모드 참조) |

종료 코드: 정상 `0`, 에이전트 오류(`is_error`) `1`, 실행 오류 `2`.

## stream 모드 (`--stream`, claude 전용, opt-in)

기본 `--json`/`--text` 경로는 프로세스 종료까지 블로킹(`subprocess.run`)한 뒤 결과를 일괄 반환한다 — 장시간 실행 중에는 진행 상황을 볼 수 없다. `--stream`은 claude CLI의 `--output-format stream-json`을 이용해 **실행 중에도** 이벤트를 흘려보내는 opt-in 경로다. 기존 `--json` 경로(단일 JSON 일괄 반환)는 **불변** — `--stream`을 지정하지 않으면 동작이 전혀 바뀌지 않는다.

### 사용법

```bash
# 표준출력을 파일로 리다이렉트 — 실행 중에도 파일이 증분 성장한다(JSONL)
~/.opal/tools/opal-agent/run.sh --provider claude --stream "긴 리팩터링 작업을 수행해줘" \
    > events.jsonl 2> events.err.log
echo $? > events.exitcode
```

- opal-agent 자신은 `events.jsonl` 같은 내부 파일을 열지 않는다 — claude stream-json 각 줄을 opal-agent의 **자기 stdout으로 그대로(line-buffered) passthrough**할 뿐이다. 파일 증분 기록은 호출측 셸의 `>` 리다이렉트가 담당한다(단일 writer).
- `--stream`을 지정하면 내부적으로 `--output-format stream-json --verbose`가 **항상 자동 부착**된다. claude CLI는 `--verbose` 없이 `--output-format stream-json`을 쓰면 exit 1(사용법 에러)로 항상 실패하므로, 호출자가 별도로 `--verbose`를 챙길 필요가 없다.
- `--stream`은 **claude 전용**이다(`ClaudeAdapter.supports_stream = True`, 타 어댑터는 미지원). `--provider`가 claude가 아닌 상태로 `--stream`을 쓰면 즉시 `OpalAgentError`("provider '...'는 stream-json 실행 경로를 지원하지 않습니다")로 명시 실패한다 — 조용한 폴백은 없다.
- 실행이 끝나면 리다이렉트된 파일의 **마지막 비어있지 않은 줄**이 claude stream-json의 `type: "result"` 이벤트다. 이 줄에서 기존 `--json` 경로와 동일한 5필드(`result`, `session_id`, `is_error`, `total_cost_usd`, `duration_ms`)를 그대로 추출할 수 있다 — 마지막 줄이 `result` 타입이 아니면 파싱 실패로 간주해 `OpalAgentError`를 던진다.
- CLI에서 `--stream`을 쓰면 실행 중 passthrough로 이미 전량 출력이 끝난 상태이므로, `main()`은 별도 dump 없이 `result.is_error` 기준 종료 코드(0/1)만 반환한다. 실행 오류는 기존과 동일하게 `2`.
- 라이브러리로 쓸 때는 `call_agent(..., output_format="stream-json")` — 호출측이 `sys.stdout`을 파일로 리다이렉트하거나 자체적으로 캡처해야 증분 기록이 이뤄진다.

### `--json`과의 관계

`--stream`은 `--json`을 대체하지 않는 **opt-in 별도 경로**다. 실행 중 진행 상황 관측이 필요한 장시간 비동기 작업에만 `--stream`을 쓰고, 그 외 일반 호출은 기존 `--json`/`--text`를 그대로 쓴다. 두 경로는 `_run()` 디스패치 단계에서 분기되며 서로의 동작에 영향을 주지 않는다.

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
  필요한 컨텍스트를 프롬프트에 직접 주입한다(`--opal-bootstrap off` = `[WORKER]` 규약과 동일 취지).
- 반환 JSON의 `result`로 결과, `session_id`로 다중 턴(`--resume`).
- 비-claude 플랫폼(codex/gemini/grok/cursor/antigravity) 워커도 `--provider`로 디스패치 가능
  — Agent/Task 툴(claude 전용)로는 불가능한 크로스-프로바이더 서브에이전트.
- 미배포 환경이면 `bash ~/.opal/tools/opal-agent/run.sh ...` 또는
  `~/.opal/.venv/bin/python ~/.opal/tools/opal-agent/opal_agent.py ...`로 대체.

## 변경이력

- v1.0 (2026-07-12) 초기 구현 — claude 전용 `call_agent` + CLI
- v2.0 (2026-07-12) 멀티 provider 어댑터 계층 — gemini/codex/grok 추가, codex 플래그 실측 반영
- v2.1 (2026-07-12) cursor provider 추가(플래그 실측), `ProviderAdapter` ABC화. Antigravity는 보류
- v2.2 (2026-07-12) antigravity(agy) provider 추가 — 실측 기반 text-only 2급 어댑터
- v2.3 (2026-07-12) `effort`(추론 강도) 지원 — claude/codex/grok, 미지원 provider 경고. `model`은 v1.0부터 지원
- v2.4 (2026-07-12) `--opal-bootstrap on\|off` — `off`면 `[WORKER]` 첫 줄 마커로 OPAL 부트스트랩 스킵(부트스트래퍼 진입점 게이트 배선과 연동). claude/codex/agy 실측 검증
- v2.5 (2026-07-13 15:25 KST, 059) `--opal-bootstrap`을 `on\|assistant\|off` 3-way로 확장(`assistant`=`[ASSISTANT]` 첫 줄, 비서 tier Phase A만) + claude 전용 caller-supplied cold `--session-id` 지원(`--resume`과 상호배타, 미지원 provider는 경고 후 무시)
- v2.6 (2026-07-17 19:49 KST, 067) `--stream` opt-in 실행 경로 추가(claude 전용) — `--output-format stream-json --verbose` 자동 조립, stdout line-buffered passthrough(호출측 리다이렉트로 증분 기록), 마지막 `type:result` 줄에서 기존과 동일한 5필드 추출. 기존 `--json`/`--text` 경로·5필드 계약·종료 코드 0/1/2는 불변

## OPAL 부트스트랩 스킵 (`--opal-bootstrap on|assistant|off`)

opal-agent가 띄우는 서브에이전트는 기본적으로 OPAL 부트스트랩(정체성 `알투`·PM tier 등)을 수행한다. `--opal-bootstrap`은 프롬프트 첫 줄에 마커를 주입해 이 부트스트랩을 3단으로 스킵할 수 있는 사다리다:

| 값 | 첫 줄 마커 | 로드 범위 |
|---|-----------|----------|
| `on` (기본) | 없음 | 비서 tier(Phase A) + PM tier(Phase B) 전부 |
| `assistant` | `[ASSISTANT]` | 비서 tier(Phase A)만 — `.opal/AGENT.md`가 있어도 PM tier 승격 억제 |
| `off` | `[WORKER]` | 전부 스킵 — 순수 워커(깨끗한 컨텍스트) |

- **메커니즘**: 첫 줄 마커 → OPAL 부트스트래퍼 진입점 게이트(`~/.claude/CLAUDE.md`·`~/.codex/AGENTS.md`·`~/.gemini/GEMINI.md`)가 `[MUST]`보다 먼저 이를 감지해 스킵 범위를 결정. env(`OPAL_BOOTSTRAP`) 방식이 아님 — 과거 env 게이트는 매 세션 권한 프롬프트 문제로 폐기됨(043).
- **검증**(off → on): claude `클로드`→`알투`, codex `Codex`→`알투`, antigravity `Antigravity`(chrome 없음)→`알투:`+부트스트랩 로그.
- **전제**: 부트스트래퍼 진입점에 "첫 줄 마커 게이트"가 배포돼 있어야 함(bootstrapper v1.1+/gemini v1.3+, 3-way는 v1.2+/059).

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
