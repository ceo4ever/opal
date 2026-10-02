# worktree-launcher

허브에서 워크트리 실행 세션을 띄우는 launcher를 소유하는 도구다. **공통 lifecycle**(`launcher_core`),
**CLI 표면**(`cli`), **설정 2-레이어 로더**(`settings`), **터미널 adapter**(`adapters/`) 4축으로 이뤄진다.

## 패키지 레이아웃

```
opal/tools/worktree-launcher/
├── run.sh                      # OPAL .venv 래퍼 — 가드 2종 뒤 CLI에 위임
├── README.md
├── conftest.py                 # tool-dir을 sys.path에 삽입(패키지 배선만)
├── worktree_launcher/          # 파이썬 패키지
│   ├── __init__.py
│   ├── launcher_core.py        # preflight → adapter → receipt 2종 → 상태 전이
│   ├── settings.py             # launcher 설정 2-레이어 머지 + 명령 결정
│   ├── cli.py                  # launch/read/close/recover 4서브명령
│   └── adapters/
│       ├── __init__.py
│       ├── orca.py             # Orca terminal adapter (launch/read/close/status)
│       ├── cmux.py             # cmux workspace adapter (launch/read/close; status unsupported)
│       ├── generic.py          # 템플릿 실행 adapter (launch만)
│       └── opal_agent_fallback.py  # opal-agent one-shot 폴백 (launch만)
└── tests/
    ├── conftest.py             # fixture 플레이스홀더 치환·tmp 허브 조립
    ├── test_launcher_core.py
    ├── test_settings.py
    ├── test_cli.py
    ├── test_adapter_orca.py
    ├── test_adapter_conformance.py
    ├── test_adapter_generic.py
    └── test_integration.py
```

`worktree-launcher`는 하이픈 디렉터리라 패키지명이 될 수 없으므로 `worktree_launcher/` 하위 패키지를
둔다(ownership-tool과 같은 배치). 테스트는 `from worktree_launcher import launcher_core` 형태로
import하며 tool-dir `conftest.py`가 경로를 잇는다.

## CLI

`run.sh`는 OPAL `.venv` 존재와 패키지 import 두 가드를 통과한 뒤
`python -m worktree_launcher.cli "$@"`에 인자를 그대로 넘기고 종료 코드를 그대로 돌려준다.
출력은 언제나 stdout 단일 라인 JSON 객체 하나이며 성공 exit 0 / 실패 exit 1이다.

```bash
~/.opal/tools/worktree-launcher/run.sh launch --adapter orca \
  --project-root <hub> --task 145 --worktree-root <root> [--agent claude] [--command …] [--owner-session-id …]
~/.opal/tools/worktree-launcher/run.sh read  --adapter orca --terminal <handle> [--cursor N] [--limit N] [--screen]
~/.opal/tools/worktree-launcher/run.sh close --adapter orca --terminal <handle>
~/.opal/tools/worktree-launcher/run.sh close --adapter orca --worktree-root <root> --all [--json]
~/.opal/tools/worktree-launcher/run.sh recover --adapter orca \
  --project-root <hub> --task 145 --worktree-root <root> [--owner-session-id …]
~/.opal/tools/worktree-launcher/run.sh launch --adapter cmux \
  --project-root <hub> --task 152 --worktree-root <root> [--command …]
```

`--adapter`는 **전 서브명령 필수**이고 값은 폐쇄 목록 `cli.SUPPORTED_ADAPTERS`(현재 `orca`, `cmux` 2종)
안에서만 해석한다 — 목록 밖 이름은 import를 시도조차 하지 않는다. 다른 어댑터로 자동 폴백하거나
OS·터미널 종류를 자동 탐지하는 경로는 없다(설정도 adapter를 소유하지 않는다).

`launch`에서 `--command`를 주지 않으면 `settings.load_launcher_settings()` +
`settings.resolve_command()`가 명령을 결정하며, 이때 쓰는 `task_path`는 registry meta가 발급한
canonical 값뿐이다 — 없으면 `--worktree-root`로 대체하지 않고 `task_path_unresolved`로 거부한다.

### builder 모델 기동 시점 주입

`--command` 없이 설정으로 명령을 정할 때, launcher는 워크트리 세션(PM·builder)이 쓸 모델을
`models.<provider>.standard`(전역 `~/.opal/setting.json` → 프로젝트 `setting.local.json` 셀 단위
머지)에서 읽어 실행 파일 바로 뒤에 넣는다. 검증기(evaluator·security 등)는 각 에이전트
frontmatter 레벨을 그대로 따르므로 이 주입과 무관하다.

| 에이전트 | provider | 주입 옵션 | 이미 지정된 것으로 보는 옵션 |
| --- | --- | --- | --- |
| `claude` | `claude` | `--model <값>` | `--model` |
| `codex` | `codex` | `-m <값>` | `-m`, `--model` |

- `argv_template`에 이미 모델 옵션이 있으면 주입하지 않는다 — 사용자 지정이 우선이다.
- 셀 값이 `inherit`이거나 표 밖 에이전트(gemini·cursor-agent 등)면 주입하지 않는다.
- 주입 대상인데 셀이 전역·로컬 둘 다 없으면 `builder_model_unresolved`(`missing` 동봉)로
  멈춘다. 모델을 추정하거나 폴백하지 않는다.
- `--command`로 명령을 직접 주면 주입하지 않는다. 호출자가 명령 전체를 책임진다.
- 설정 파일(`argv_template`)이 아니라 코드가 주입하므로, 기존 설치도 install로 도구만 갱신되면
  별도 설정 이관 없이 적용된다.

### builder 모델 레벨

기본 builder 레벨은 `standard`다. `launcher.builderModelLevel.<에이전트|provider>`에 `light`·`standard`·`advanced`를 쓰면 그 레벨의 `models.<provider>.<레벨>` 셀을 builder 모델로 주입한다. 에이전트 이름 키가 provider 키를 이기고, 미설정이거나 알 수 없는 값이면 `standard`다. 셀이 `inherit`면 주입하지 않고, 셀이 없으면 `builder_model_unresolved`로 멈춘다. 전역 `~/.opal/setting.json` 위에 프로젝트 `setting.local.json`이 에이전트 키 단위로 덮어쓴다.

```json
{ "launcher": { "builderModelLevel": { "claude": "advanced" }, "builderEffort": { "claude": "high" } } }
```

### 같은 CLI의 다른 계정 — 엔트리 `provider`·`env`

`agents.<name>` 엔트리는 `argv_template` 외에 선택 필드 2개를 받는다.

| 필드 | 뜻 |
| --- | --- |
| `provider` | 모델·effort 주입 규칙과 `models.<provider>` 셀을 고르는 키. 없으면 에이전트 이름(주입 표에 있을 때) → 실행 파일 basename 순으로 정한다 |
| `env` | 기동 명령 앞에 붙일 환경변수(이름→값). 값의 `~`는 홈으로 펼치고 셸 인용한다. 셸 변수 이름 규칙을 벗어나거나 값이 문자열이 아니면 그 항목만 건너뛴다 |

셸 alias는 launcher가 넘기는 비대화형 명령에서 풀리지 않으므로, alias 대신 이 두 필드로
같은 효과를 낸다.

```json
{ "launcher": { "agents": { "acct2": {
  "provider": "codex",
  "env": { "CODEX_HOME": "~/.codex_acct2" },
  "argv_template": "codex -c 'cli_auth_credentials_store=\"file\"' --no-daemon --add-dir \"{meta_dir}\" \"{utterance}\""
} } } }
```

`--agent acct2`로 기동하면 `CODEX_HOME=<홈>/.codex_acct2 codex -m <models.codex.standard> …`가 된다.
기동 전 점검은 `env`를 붙이기 전 원본 템플릿을 보므로 실행 파일이 첫 토큰으로 남는다.
`builderEffort`는 에이전트 이름 키(`acct2`)가 provider 키(`codex`)를 이긴다.

### builder effort 기동 시점 주입

`launcher.builderEffort.<에이전트>`에 값이 있으면 모델 옵션 뒤에 effort 옵션을 넣는다. 모델과
달리 **선택값**이다 — 미설정이면 주입하지 않고 각 CLI의 기본 effort로 폴백한다(오류 아님).
전역 `~/.opal/setting.json` 위에 프로젝트 `setting.local.json`이 에이전트 키 단위로 덮어쓴다.

```json
{ "launcher": { "builderEffort": { "claude": "high", "codex": "medium" } } }
```

| 에이전트 | 주입 인자 | 이미 지정된 것으로 보는 조각 |
| --- | --- | --- |
| `claude` | `--effort <값>` | `--effort` |
| `codex` | `-c model_reasoning_effort="<값>"` | `model_reasoning_effort` |

- 템플릿에 이미 effort 지정이 있거나 값이 `inherit`이거나 표 밖 에이전트면 주입하지 않는다.
- 값의 유효성은 각 CLI가 판정한다(claude: `low|medium|high|xhigh|max`). launcher는 목록을 복제하지 않는다.
- `--command`로 명령을 직접 주면 주입하지 않는다.

`launcher.leasePollTimeoutSec`은 child lease claim을 기다리는 bounded polling 상한(초)이다.
코드 기본값은 **30초**이며, 양의 숫자만 전역 설정과 프로젝트 `setting.local.json`에서 이를
덮어쓸 수 있다. 이 대기는 child가 bootstrap을 처리해 lease를 claim할 시간을 주는 것이며,
작업 준비 완료를 뜻하지 않는다.

`close`의 스코프는 `--terminal` 또는 `--worktree-root --all` **정확히 하나**이며, 위반은 어댑터를
호출하기 전에 거부한다(`--json`은 회수 스윕 호출 형태와의 호환용 no-op — 출력은 항상 JSON이다).

### 기동 전 점검

`launch`는 lease 이관·터미널 기동(`launcher_core.run`) **이전**에 아래 점검을 수행한다.
실패하면 어댑터·lease를 한 번도 건드리지 않고 `launch_preflight_failed` + `cause`로 종료한다.

1. **메타 폴더 존재·쓰기 가능** — `launcher_core.task_meta_dir_path(project_root, task)`가
   계산한 태스크 전용 메타 폴더와 그 안의 `meta.json`이 존재해야 하고(부재는
   `meta_dir_missing`), 허브 프로세스가 그 폴더에 쓸 수 있어야 한다
   (`meta_dir_not_writable`). registry 조회(`--command`로 명령을 직접 줄 때도 포함)보다
   **먼저** 독립적으로 판정하며, registry 조회 실패(`registry_unreadable` 등)와 섞이지
   않는다.
2. **grant 옵션 지원 확인** — 명령 확정 뒤, 확정된 `argv_template`
   (`settings.resolve_argv_template`)에 `{meta_dir}`가 있을 때만 적용된다. 그 직전 옵션
   토큰(예: `--add-dir`)을 뽑아 실행 파일의 `<실행 파일> --help`(10초 제한) 출력에 있는지
   확인한다 — 실행 파일을 PATH에서 찾지 못했거나 `--help` 실행 자체가 실패·타임아웃하면
   `agent_help_unavailable`, 실행은 됐지만 출력에 그 옵션이 없으면
   `grant_option_unsupported`다.
3. **비차단 경고** — `{meta_dir}`를 쓰는 에이전트(현재 Codex 기본값)는 검사 ①②를 통과하면
   응답 `warnings` 배열에 `git_write_requires_escalation`을 싣는다 — 공유 워크트리 `.git`에
   대한 쓰기는 별도 에스컬레이션이 필요하다는 뜻이며 기동을 막지 않는다. `{meta_dir}`를
   쓰지 않는 에이전트(Claude 기본값)는 이 경고가 붙지 않는다.

**`--command`로 직접 명령을 주면 검사 ①은 항상 적용되고, 검사 ②③은 그 명령 문자열에
`{meta_dir}` 리터럴이 없으므로 적용되지 않는다** — `{meta_dir}` 치환은 `resolve_command`를
거치는 registry 기반 경로에서만 일어난다.

### 오류 코드

argparse usage 오류도 exit 2 + 사람용 usage로 새지 않고 구조화 JSON + exit 1로 바뀐다.

| 코드 | 언제 |
| --- | --- |
| `adapter_required` | `--adapter` 누락 |
| `adapter_unsupported` | 폐쇄 목록 밖 어댑터 이름(`fallback_attempted: false` 동봉) |
| `invalid_arguments` | 서브명령 누락·argparse usage 오류·`launch` 필수 인자 누락 |
| `registry_unreadable` | registry meta를 읽지 못함 |
| `task_path_unresolved` | meta에 canonical `task_path`가 없음 |
| `builder_model_unresolved` | 주입 대상 에이전트의 `models.<provider>.standard` 셀이 전역·로컬 둘 다 없음 |
| `launch_preflight_failed` | 기동 전 점검 실패. `cause` ∈ `meta_dir_missing`\|`meta_dir_not_writable`\|`grant_option_unsupported`\|`agent_help_unavailable` |
| `launcher_error` | `launcher_core.LauncherError` |
| `terminal_required` | `read`에 `--terminal` 누락 |
| `close_scope_invalid` | `close` 스코프 배타성 위반 |
| `adapter_report_invalid` | 어댑터가 dict가 아닌 것을 보고 |

어댑터 실패는 예외가 아니라 `exit_code != 0` 보고이므로, 그 `failure_reason`이 그대로 `error`로 실린다.

## lifecycle 계약

`launcher_core.run(adapter, hub_root=…, task=…, worktree_root=…, command=…)` 1회 호출이 아래 순서를 밟는다.

1. **preflight** — registry meta(태스크 전용 폴더
   `<hub_root>/.opal-worktrees/.meta/task_{NNN}/meta.json`, `launcher_core.registry_meta_path`)를 읽고
   등록된 `worktree_root`가 인자와 realpath 동치인지 확인한다. 상태가 `hub_owned`이면
   `session_launching`으로 전이하고, 이미 `session_launching`이면 그 소유를 이어받아
   generation을 낭비하지 않는다(멱등 재진입). 둘 다 아니면 상태를 건드리지 않고 거부한다.
2. **adapter 호출** — `adapter.launch(worktree_root, command)` **한 번**. adapter는 호출자가
   명시 선택해 주입하며 launcher는 OS·터미널 종류를 추측하지 않는다.
3. **launch receipt 수집** — `{adapter, adapter_handle, reported_cwd, launched_at}`.
4. **cwd 가드** — `reported_cwd`가 registry `worktree_root`와 realpath 동치가 아니면 전이하지 않는다.
5. **prompt receipt 수집** — `{prompt_id, submitted_at}`.
6. **child claim 대기** — 유계 polling과 마감 직전 재조회로 hub가 아닌 live lease owner를 찾는다.
7. **상태 전이** — 관측 owner를 `--expected-owner`로 지정한 `worktree_session_owned` 전이(receipt 2종 동봉).

claim timeout, receipt 오류, 원자 owner 비교 거부를 포함한 실패는 복구 판정으로 간다. close 전 마지막
lease 조회에서 child claim이 확인되면 성공 전이로 합류하지만, close 뒤 발견한 claim은 성공으로 확정하지
않는다. `not_created`는 close를 생략하고, `created`는 close 뒤 `status == absent`를 요구하며, `unknown`은
자동 복귀하지 않는다. 시작된 handoff 취소와 lease 재조회까지 확인되면 `hub_owned`로 원자 복귀한다.
하나라도 불명·실패이거나 외부 live lease가 남으면 `recovery_required`와
`launch_recovery_required`를 반환하고 새 launch를 거부한다.

### 원자 복귀 시 터미널 정리

복귀는 `ownership-set` 전에 `adapter.close(handle=…)`를 1회 시도한다. handle은 launch 보고에서만
취하고 스코프는 정밀 close 하나다. close 결과 뒤 `status(handle, worktree_root=…) == absent`를
확인해야 `hub_owned`로 복귀할 수 있다. Orca는 stale show와 worktree list 부재가 함께 있을 때, 또는
show가 `orphaned:true`·`connected:false`·`exitCause.kind:operator_close`를 함께 보고하고 성공한 목록에
같은 handle과 `ptyId`가 모두 없을 때만 absent다.
상태 동사가 없는 adapter와 조회 오류는 `unknown`이며 `recovery_required`로 보존한다.

`recover --adapter … --project-root … --task … --worktree-root …`는 보존된 상태에서만 동작한다.
created terminal은 handle absence, unknown/not-created terminal은 worktree 단위 absence를 새로 확인하고,
handoff cancel과 안전한 lease 재조회까지 통과해야 `hub_owned`가 된다.

## 상태 쓰기는 전부 `ownership-set` 경유

launcher는 **사설 ownership writer를 두지 않는다.** registry 상태 전이는 전부
`worktree-tool`의 `ownership-set` CLI(`worktree_tool.cmd_ownership_set`)를 subprocess로 경유하며,
registry lock(`<meta>.lock`)·temp→`os.replace` 원자 교체·허용 조합 6개·`generation` 단조성·
`worktree_session_owned` 진입의 receipt 2종 요구는 전부 그쪽 계약이 판정한다. 이 도구는 registry를
**읽기만** 하고 쓰기 로직을 복제하지 않는다.

registry 조회는 인자로 발급받은 `hub_root`·`task`로 만든 1경로에서만 한다 — 경로 문자열 접두·
basename·mtime으로 신원을 추론하지 않는다(`harness/worktree.md` §canonical path 발급 계약).

## adapter seam

adapter는 상속 계층 없는 덕타이핑 경계이며 `launch`·`read`·`close` 3동사를 노출한다.
세 동사 모두 성공·실패가 **같은 모양의 dict**이며 실패는 예외가 아니라 `exit_code != 0`이다.

공통 키는 `adapter`(str) · `exit_code`(int) · `fallback_attempted`(항상 `False` — 다른 어댑터를
자동으로 되부르지 않는다는 사실을 응답이 스스로 밝힌다)이고, 동사별로 다음이 더해진다.

| 동사 | 추가 키 |
| --- | --- |
| `launch(worktree_root, command)` | `adapter_handle` · `reported_cwd` · `launched_at` · `prompt_id` · `submitted_at` · `prompt_receipt_source` · `launch_mode` |
| `read(handle, *, cursor, limit, screen)` | `handle` · `content` · `next_cursor` · `source` |
| `close(*, handle=…)` 또는 `close(*, worktree_root=…, all=True)` | `scope`(`terminal` \| `worktree_all`) · `closed`(list) |

실패 보고는 같은 dict에 `failure_reason`과 `detail`을 싣는다. 필드가 비었거나 `exit_code`가 0이
아니면 launcher_core가 해당 단계 실패로 판정한다.

### prompt receipt의 원천은 기동 argv다

handoff prompt는 별도 seam 없이 `--command`로 띄운 TUI에 함께 제출되므로 receipt의 원천은
기동 argv 하나뿐이다 — `prompt_receipt_source`는 항상 `launch_argv`, `prompt_id`는 실제로 실어
보낸 명령 문자열의 sha256 앞 16자, `submitted_at`은 exit 0을 관측한 시각이다.

### 지원 adapter

Orca는 `status(handle)`와 `status_worktree(root)`도 구현한다. cmux CLI의 상태 조회와 worktree 단위 부재
판정을 이 환경에서 확인하지 못했으므로 cmux·generic·opal-agent fallback은 status를
`unknown(status_unsupported)`로 취급한다. 이 adapter로 실패한 launch는 `recovery_required`에서 명시
복구를 기다린다. cmux는 `new-workspace --cwd --command`의 stdout 한 줄 `OK workspace:<n>`에서
workspace ref를 handle로 사용하고 `read-screen --workspace`, `close-workspace --workspace`로 같은 workspace만
읽고 닫는다. worktree 경로만으로 cmux workspace를 추측하는 광역 close는 지원하지 않는다.

adapter 선택은 이 도구가 자동으로 하지 않는다. bootstrap과 `--wt` orchestration이
`terminal-context`의 `host`를 읽어 폐쇄 목록과 정확히 일치할 때만 명시 `--adapter`로 전달한다.
`tmux`는 multiplexer이므로 adapter가 아니며, `unknown`에는 폴백하지 않는다.

## 설정 (`launcher` 블록)

`~/.opal/setting.json`(전역) + `{프로젝트}/.opal/setting.local.json`(로컬 우선) 2-레이어이며,
코드 상수가 그 아래 base다.

```jsonc
{
  "launcher": {
    "default": "claude",                                  // 쓸 에이전트 이름
    "agents": {
      "claude": { "argv_template": "claude \"{utterance}\"" },              // 셸 명령 문자열
      "codex":  { "argv_template": "codex --dangerously-bypass-approvals-and-sandbox --no-daemon --add-dir \"{meta_dir}\" \"{utterance}\"" }
    },
    "utterance_template": "{task_path} 이어서 수행"          // 첫 발화
  }
}
```

- `argv_template`은 argv 리스트가 아니라 **셸 명령 문자열**이다 — orca `--command <text>`가
  셸이 실행할 문자열 하나를 받기 때문이다.
- 치환 토큰은 `{utterance}`·`{task_path}`·`{meta_dir}` **3종뿐**이며 리터럴 치환이라 다른
  중괄호는 그대로 남는다.
  - `{meta_dir}`은 태스크 전용 메타 폴더
    (`<hub_root>/.opal-worktrees/.meta/task_{NNN}/`, `launcher_core.task_meta_dir_path`가
    허브 루트·태스크 번호 발급값으로 계산) 절대경로다. Codex 기본값은 이 토큰을
    `--add-dir` 뒤에 실어 Codex가 자기 태스크 메타 폴더에만 쓰기 권한을 갖게 한다 —
    워크트리 전체나 허브 루트를 열어주지 않는다. **Claude 기본값은 이 토큰을 쓰지 않으며
    바이트 그대로 불변이다.**
  - `settings.resolve_argv_template(settings, agent=None)`은 치환 전 원본 `argv_template`을
    돌려준다 — CLI의 기동 전 점검이 `{meta_dir}` 사용 여부·직전 옵션 토큰을 판정하는 데 쓴다.
- 머지 입도: `agents.<name>`은 **이름 단위 통째 교체**(엔트리 내부를 깊게 합치지 않는다),
  그 위 키는 키 단위 덮어쓰기.
- **`launcher`는 `adapter`를 소유하지 않는다** — 어댑터 선택은 CLI `--adapter`가 단독으로 정한다.
- 파일 부재·JSON 파싱 실패·타입 불일치는 그 레이어만 무시하고 아래 레이어 값을 유지한다.
  즉 **미설정은 코드 기본값 폴백**이며, `models` 미설정이 디스패치를 중단하는 것과 비대칭이다.
  그 근거 문장은 `opal/core/setting.default.json`의 `launcher._help`가 소유한다.

## 회수 연동

`worktree-tool remove`가 dirty→unpushed→unmerged 3중 가드를 통과한 뒤 `git worktree remove` 루프
**직전에** 워크트리 터미널을 1회 스윕한다. registry에 `execution_ownership.adapter`가 기록돼
있을 때만 `run.sh close --adapter <adapter> --worktree-root <root> --all --json`을 호출하며,
adapter 미기록 경로는 분기에 진입조차 하지 않는다. close 실패는 회수를 차단하지 않고
`warnings`로만 보고한다(orca 부재 환경에서 슬롯이 영구 잠기지 않도록).

## 테스트

```bash
~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests/ -q
```

기본 스위트는 실제 Orca/cmux CLI를 한 번도 호출하지 않는다 — 어댑터의 subprocess seam만
대체하고 응답 fixture를 쓴다.

### 적합성 스위트 — 새 어댑터의 유일한 계약

`tests/test_adapter_conformance.py`가 D-J 3동사 보고 스키마를 어댑터 모듈 파라미터화로 집행한다.
새 어댑터를 붙이는 비용은 상단 두 상수뿐이다 — `CONFORMANCE_ADAPTERS`에 이름 1줄,
`ADAPTER_FIXTURES`에 자기 fixture 등록. 그 스위트를 전건 통과시키는 것이 계약의 전부다.

이 스위트는 목킹 기반이므로 **실물 orca의 현재 응답 모양과 여전히 맞는지(버전 드리프트)는 잡지
않는다.** 드리프트를 관측하는 유일한 관문은 아래 live 테스트다.

### live 테스트

`tests/test_adapter_orca.py`의 live 대조 1건은 `OPAL_LIVE_ORCA=1`이고 `orca`가 PATH에 있을 때만
돈다(그 외 skip). 대상 워크트리는 `OPAL_LIVE_ORCA_WORKTREE`, 없으면
`orca worktree list --json`에서 레포 루트와 일치하는 항목으로만 정하며 워크트리를 새로 만들지 않는다.

`tests/test_adapter_cmux.py`의 live 대조 1건(S-4)은 `OPAL_LIVE_CMUX=1`이고 `cmux`가 PATH에 있을 때만
돈다. 실행마다 고유 이름의 임시 디렉터리로 workspace 1개를 만들어 cwd·command 전달과 유계 read를
확인하고, 같은 handle로 닫은 뒤 그 이름의 workspace가 0개인지 목록 반영을 기다려 확인한다.
사용자의 기존 workspace는 건드리지 않는다.

## 신원 preflight와 Codex 시작 (task 155)

launcher는 명시 owner 또는 ownership-tool resolver의 신원을 시작 시 한 번 확정한다.
미해석이면 registry/lease/terminal 변경 전에 `session_id_unresolved`로 종료한다.
실패에는 `cause`, adapter, 사용 가능한 identity **source 이름**을 남긴다.
같은 확정 ID를 handoff와 handoff-cancel의 `--session-id`로 전달한다.
기동 명령은 공개 `ownership-tool session-launch`로 감싸 부모 플랫폼 신원을 지운다.

최종 registry owner는 허브 입력 ID를 재사용하지 않고 공개
`worktree-tool ownership-set --owner-from-lease --expected-owner --exclude-owner`로 연결한다.
hub가 child live lease를 관측한 뒤에만 실제 lease owner를 기록하며, pending·unresolved이면 성공을
기록하지 않는다. receipt 수신은 명령 제출 증거이며 실제 Codex 실행/claim 완료 증거는 아니다.

Codex 기본 argv의 `--no-daemon`은 `codex --help`에 해당 옵션이 표시되는 설치본에서만 지원된다.
지원하지 않는 binary의 즉시 종료는 child claim timeout으로 처리하며, terminal absence를 확인할 수 있을
때만 hub로 복귀한다.
