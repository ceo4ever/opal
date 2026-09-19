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
│   ├── cli.py                  # launch/read/close 3서브명령
│   └── adapters/
│       ├── __init__.py
│       ├── orca.py             # Orca 터미널 adapter (3동사)
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
```

`--adapter`는 **전 서브명령 필수**이고 값은 폐쇄 목록 `cli.SUPPORTED_ADAPTERS`(현재 `orca` 1종)
안에서만 해석한다 — 목록 밖 이름은 import를 시도조차 하지 않는다. 다른 어댑터로 자동 폴백하거나
OS·터미널 종류를 자동 탐지하는 경로는 없다(설정도 adapter를 소유하지 않는다).

`launch`에서 `--command`를 주지 않으면 `settings.load_launcher_settings()` +
`settings.resolve_command()`가 명령을 결정하며, 이때 쓰는 `task_path`는 registry meta가 발급한
canonical 값뿐이다 — 없으면 `--worktree-root`로 대체하지 않고 `task_path_unresolved`로 거부한다.

`close`의 스코프는 `--terminal` 또는 `--worktree-root --all` **정확히 하나**이며, 위반은 어댑터를
호출하기 전에 거부한다(`--json`은 회수 스윕 호출 형태와의 호환용 no-op — 출력은 항상 JSON이다).

### 오류 코드

argparse usage 오류도 exit 2 + 사람용 usage로 새지 않고 구조화 JSON + exit 1로 바뀐다.

| 코드 | 언제 |
| --- | --- |
| `adapter_required` | `--adapter` 누락 |
| `adapter_unsupported` | 폐쇄 목록 밖 어댑터 이름(`fallback_attempted: false` 동봉) |
| `invalid_arguments` | 서브명령 누락·argparse usage 오류·`launch` 필수 인자 누락 |
| `registry_unreadable` | registry meta를 읽지 못함 |
| `task_path_unresolved` | meta에 canonical `task_path`가 없음 |
| `launcher_error` | `launcher_core.LauncherError` |
| `terminal_required` | `read`에 `--terminal` 누락 |
| `close_scope_invalid` | `close` 스코프 배타성 위반 |
| `adapter_report_invalid` | 어댑터가 dict가 아닌 것을 보고 |

어댑터 실패는 예외가 아니라 `exit_code != 0` 보고이므로, 그 `failure_reason`이 그대로 `error`로 실린다.

## lifecycle 계약

`launcher_core.run(adapter, hub_root=…, task=…, worktree_root=…, command=…)` 1회 호출이 아래 순서를 밟는다.

1. **preflight** — registry meta(`<hub_root>/.opal-worktrees/.meta/task_{NNN}.json`)를 읽고
   등록된 `worktree_root`가 인자와 realpath 동치인지 확인한다. 상태가 `hub_owned`이면
   `session_launching`으로 전이하고, 이미 `session_launching`이면 그 소유를 이어받아
   generation을 낭비하지 않는다(멱등 재진입). 둘 다 아니면 상태를 건드리지 않고 거부한다.
2. **adapter 호출** — `adapter.launch(worktree_root, command)` **한 번**. adapter는 호출자가
   명시 선택해 주입하며 launcher는 OS·터미널 종류를 추측하지 않는다.
3. **launch receipt 수집** — `{adapter, adapter_handle, reported_cwd, launched_at}`.
4. **cwd 가드** — `reported_cwd`가 registry `worktree_root`와 realpath 동치가 아니면 전이하지 않는다.
5. **prompt receipt 수집** — `{prompt_id, submitted_at}`.
6. **상태 전이** — `worktree_session_owned`(receipt 2종 동봉).

복귀 5경로 — `adapter_report_invalid` · `launch_receipt_missing` · `reported_cwd_mismatch` ·
`prompt_receipt_missing` · `ownership_set_rejected` — 전건이 **원자 복귀**를 호출한다.
`failure_reason=launch_failed` + `hub_owned` + `attribution_state` 키 부재 + `generation` 증가가
**한 번의 교체**에 담기므로 dual owner도, owner 없는 `session_launching` 잔존도 남지 않는다.

### 원자 복귀 시 터미널 정리

복귀는 `ownership-set` **직전에** `adapter.close(handle=…)`를 1회 시도하고 결과를 반환 dict의
`terminal_close` 필드로만 남긴다. handle은 launch 보고의 `adapter_handle`에서만 취하고 없으면
시도하지 않으며(대상 추측 금지), 스코프는 정밀 close 하나다(워크스페이스 스윕은 회수 경로 소유라
사용자의 다른 탭을 건드리지 않는다). close의 예외·미구현(`AttributeError`)·비-0 exit는 전부
삼키고 `ownership-set` 복귀는 반드시 수행한다 — 복귀가 정리 성공에 종속되면 dual owner가 남는다.

## 상태 쓰기는 전부 `ownership-set` 경유

launcher는 **사설 ownership writer를 두지 않는다.** registry 상태 전이는 전부
`worktree-tool`의 `ownership-set` CLI(`worktree_tool.cmd_ownership_set`)를 subprocess로 경유하며,
registry lock(`<meta>.lock`)·temp→`os.replace` 원자 교체·허용 조합 6개·`generation` 단조성·
`worktree_session_owned` 진입의 receipt 2종 요구는 전부 그쪽 계약이 판정한다. 이 도구는 registry를
**읽기만** 하고 쓰기 로직을 복제하지 않는다.

registry 조회는 인자로 발급받은 `hub_root`·`task`로 만든 1경로에서만 한다 — 경로 문자열 접두·
basename·mtime으로 신원을 추론하지 않는다(`harness/worktree.md` §canonical path 발급 계약).

## adapter seam

adapter는 상속 계층 없는 덕타이핑 경계이며 `launch`·`read`·`close` **3동사**를 노출한다.
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

### 이번 범위의 adapter

3동사를 갖춘 adapter는 `orca` 하나다. `generic`·`opal_agent_fallback`은 `launch`만 있어
적합성 스위트 대상이 아니며, cmux adapter는 존재하지 않는다.

## 설정 (`launcher` 블록)

`~/.opal/setting.json`(전역) + `{프로젝트}/.opal/setting.local.json`(로컬 우선) 2-레이어이며,
코드 상수가 그 아래 base다.

```jsonc
{
  "launcher": {
    "default": "claude",                                  // 쓸 에이전트 이름
    "agents": {
      "claude": { "argv_template": "claude \"{utterance}\"" }  // 셸 명령 문자열
    },
    "utterance_template": "{task_path} 이어서 수행"          // 첫 발화
  }
}
```

- `argv_template`은 argv 리스트가 아니라 **셸 명령 문자열**이다 — orca `--command <text>`가
  셸이 실행할 문자열 하나를 받기 때문이다.
- 치환 토큰은 `{utterance}`·`{task_path}` **2종뿐**이며 리터럴 치환이라 다른 중괄호는 그대로 남는다.
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

기본 스위트는 실제 orca CLI를 한 번도 호출하지 않는다 — 어댑터의 subprocess seam만 대체하고
응답은 실측 캡처 fixture를 쓴다.

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
