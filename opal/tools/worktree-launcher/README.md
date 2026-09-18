# worktree-launcher

허브에서 워크트리 실행 세션을 띄우는 launcher의 **공통 lifecycle**을 소유하는 도구다.
현재 구현 범위는 코어(lifecycle)까지이며 터미널 adapter 2종과 CLI 표면은 후속 Work item이 채운다.

## 패키지 레이아웃

```
opal/tools/worktree-launcher/
├── run.sh                      # OPAL .venv 래퍼 (CLI 미구현 — not_implemented 반환)
├── README.md
├── conftest.py                 # tool-dir을 sys.path에 삽입(패키지 배선만)
├── worktree_launcher/          # 파이썬 패키지
│   ├── __init__.py
│   └── launcher_core.py        # preflight → adapter → receipt 2종 → 상태 전이
└── tests/
    ├── conftest.py             # fixture 플레이스홀더 치환·tmp 허브 조립
    ├── test_launcher_core.py
    ├── test_adapter_orca.py    # 후속 Work item(미구현)
    └── test_adapter_generic.py # 후속 Work item(미구현)
```

`worktree-launcher`는 하이픈 디렉터리라 패키지명이 될 수 없으므로 `worktree_launcher/` 하위 패키지를
둔다(ownership-tool과 같은 배치). 테스트는 `from worktree_launcher import launcher_core` 형태로
import하며 tool-dir `conftest.py`가 경로를 잇는다.

## lifecycle 계약

`launcher_core.run(adapter, hub_root=…, task=…, worktree_root=…, command=…)` 1회 호출이 아래 순서를 밟는다.

1. **preflight** — registry meta(`<hub_root>/.opal-worktrees/.meta/task_{NNN}.json`)를 읽고
   등록된 `worktree_root`가 인자와 realpath 동치인지 확인한다. 상태가 `hub_owned`이면
   `session_launching`으로 전이하고, 이미 `session_launching`이면 그 소유를 이어받아
   generation을 낭비하지 않는다(멱등 재진입). 둘 다 아니면 상태를 건드리지 않고 거부한다.
2. **adapter 호출** — `adapter.launch(worktree_root, command)` **한 번**. adapter는 호출자가
   명시 선택해 주입하며(`orca` · `generic` · `opal-agent`) launcher는 OS·터미널 종류를 추측하지 않는다.
3. **launch receipt 수집** — `{adapter, adapter_handle, reported_cwd, launched_at}`.
4. **cwd 가드** — `reported_cwd`가 registry `worktree_root`와 일치하지 않으면 전이하지 않고
   `launch_failed`로 복귀한다.
5. **prompt receipt 수집** — `{prompt_id, submitted_at}`.
6. **상태 전이** — `worktree_session_owned`(receipt 2종 동봉).

launch 실패 · prompt 실패 · cwd 불일치 어느 경로든 **원자 복귀**를 호출한다 —
`failure_reason=launch_failed` + `hub_owned` + `attribution_state` 키 부재 + `generation` 증가가
**한 번의 교체**에 담기므로 dual owner도, owner 없는 `session_launching` 잔존도 남지 않는다.

## 상태 쓰기는 전부 `ownership-set` 경유

launcher는 **사설 ownership writer를 두지 않는다.** registry 상태 전이는 전부
`worktree-tool`의 `ownership-set` CLI(`worktree_tool.cmd_ownership_set`)를 subprocess로 경유하며,
registry lock(`<meta>.lock`)·temp→`os.replace` 원자 교체·허용 조합 6개·`generation` 단조성·
`worktree_session_owned` 진입의 receipt 2종 요구는 전부 그쪽 계약이 판정한다. 이 도구는 registry를
**읽기만** 하고 쓰기 로직을 복제하지 않는다.

registry 조회는 인자로 발급받은 `hub_root`·`task`로 만든 1경로에서만 한다 — 경로 문자열 접두·
basename·mtime으로 신원을 추론하지 않는다(`harness/worktree.md` §canonical path 발급 계약).

## adapter seam

adapter는 아래 한 메서드만 요구하는 덕타이핑 경계다.

```python
class Adapter:
    name: str  # 선택 — registry meta의 adapter 값이 우선한다

    def launch(self, worktree_root, command) -> dict:
        """터미널 기동 + handoff prompt 제출을 수행하고 receipt 원천 필드를 보고한다.

        반환 dict: {adapter, adapter_handle, reported_cwd, launched_at,
                    prompt_id, submitted_at, exit_code, stderr?}
        """
```

필드가 비었거나 `exit_code`가 0이 아니면 launcher가 해당 단계 실패로 판정한다.
구체 adapter(`adapters/orca.py`·`adapters/generic.py`)는 후속 Work item이 추가한다.

## 테스트

```bash
~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests/ -q
```

`test_launcher_core.py`는 GREEN이고, `test_adapter_orca.py`·`test_adapter_generic.py`는
adapter 미구현으로 RED(`ModuleNotFoundError: worktree_launcher.adapters`)다.
