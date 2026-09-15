---
module: modes
role: pilot 실행 모드 판정과 서브 하네스 라우팅의 단일 SSOT
load: pilot.start
---

# Modes

## 모드별 서브 하네스

| 모드 | 선택 조건 | 서브 하네스 |
|------|-----------|-------------|
| `semi-agentic` | 신규 태스크의 모드 플래그 없음(기본) 또는 `--semi-agentic` | `opal-harness-semi-agentic.md` |
| `interactive` | `--interactive` | `opal-harness-interactive.md` |
| `agentic` | `--agentic` | `opal-harness-agentic.md` |

소스 checkout에서는 `{source_root}/opal/core/references/{서브 하네스}`, 설치본에서는
`{deployed_root}/references/{서브 하네스}`를 읽는다(기본 설치 루트는 `~/.opal`).

## 라우팅 계약

1. pilot은 `pilot.start` 이벤트 load와 receipt 계약을 먼저 충족한다.
2. 태스크 경로를 확정한 뒤 `state-tool resolve-mode <task-path> [--mode <mode>] [--new-task]`를 호출한다. 신규 태스크만 `--new-task`를 사용한다.
3. effective mode 우선순위는 **명시 플래그 > 유효한 `state.json.mode` > 신규 태스크의 `semi-agentic` 기본값**이다. 기존 태스크의 무플래그 재개는 저장 mode를 상속한다.
4. 기존 state의 mode가 누락·비문자·허용값 밖이면 `interactive` / `fail_closed`로 판정해 자동 승인을 막고 파일은 고치지 않는다. 명시 플래그만 mode를 복구할 수 있으며, JSON 자체가 손상되면 `state_json_malformed`로 중단한다.
5. resolver의 구조화 결과로 모드를 하나만 확정한 뒤 해당 서브 하네스 전문 하나를 읽는다. 프로젝트 브리프의 mode 표시는 안내이며 판정 입력으로 파싱하지 않는다.
6. 둘 이상의 모드 플래그가 동시에 있으면 `mode_flag_conflict`로 거부한다. state init도 같은 판정을 따라야 한다.
7. `--worktree`/`--wt`는 모드가 아니라 별도 워크스페이스 축이므로 모드 플래그 개수에 포함하지 않는다. 해당 축의 원문은 `harness/worktree.md`가 소유한다.
8. 선택된 서브 하네스가 현재 세션에 이미 로드되었으면 중복 Read를 생략할 수 있다. receipt가 필요한 이벤트 자체를 생략할 수 있다는 뜻은 아니다.
9. 새 모드는 이 문서의 폐쇄된 라우팅 표와 대응 서브 하네스를 함께 변경해야 한다.
10. `--pm`은 모드가 아니라 별도 실행 주체(actor) 축이므로 모드 플래그 개수에 포함하지 않는다. 해당 축의 원문은 `harness/actor.md`가 소유한다.

모드별 단계 게이트와 사용자 확인 동작은 각 서브 하네스가 소유한다. 모든 모드에
공통인 승인·CLOSE·자동 루핑 경계는 `harness/guards.md`가 소유한다.
