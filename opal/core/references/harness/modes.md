---
module: modes
role: pilot 실행 모드 판정과 서브 하네스 라우팅의 단일 SSOT
load: pilot.start
---

# Modes

## 모드별 서브 하네스

| 모드 | 선택 조건 | 서브 하네스 |
|------|-----------|-------------|
| `semi-agentic` | 모드 플래그 없음(기본) 또는 `--semi-agentic` | `opal-harness-semi-agentic.md` |
| `interactive` | `--interactive` | `opal-harness-interactive.md` |
| `agentic` | `--agentic` | `opal-harness-agentic.md` |

소스 checkout에서는 `{source_root}/opal/core/references/{서브 하네스}`, 설치본에서는
`{deployed_root}/references/{서브 하네스}`를 읽는다(기본 설치 루트는 `~/.opal`).

## 라우팅 계약

1. pilot은 `pilot.start` 이벤트 load와 receipt 계약을 먼저 충족한다.
2. 위 표로 모드를 하나만 판정하고 해당 서브 하네스 전문을 읽는다.
3. 모드 플래그가 없으면 `semi-agentic`으로 판정한다.
4. 둘 이상의 모드 플래그가 동시에 있으면 `mode_flag_conflict`로 거부한다. state init도 같은 판정을 따라야 한다.
5. `--worktree`/`--wt`는 모드가 아니라 별도 워크스페이스 축이므로 모드 플래그 개수에 포함하지 않는다. 해당 축의 원문은 `harness/worktree.md`가 소유한다.
6. 선택된 서브 하네스가 현재 세션에 이미 로드되었으면 중복 Read를 생략할 수 있다. receipt가 필요한 이벤트 자체를 생략할 수 있다는 뜻은 아니다.
7. 새 모드는 이 문서의 폐쇄된 라우팅 표와 대응 서브 하네스를 함께 변경해야 한다.
8. `--pm`은 모드가 아니라 별도 실행 주체(actor) 축이므로 모드 플래그 개수에 포함하지 않는다. 해당 축의 원문은 `harness/actor.md`가 소유한다.

모드별 단계 게이트와 사용자 확인 동작은 각 서브 하네스가 소유한다. 모든 모드에
공통인 승인·CLOSE·자동 루핑 경계는 `harness/guards.md`가 소유한다.
