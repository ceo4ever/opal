# terminal-context

현재 OPAL 프로세스가 실제로 연결된 터미널 계층을 판별한다.

```bash
~/.opal/tools/terminal-context/run.sh
```

stdout은 단일 라인 JSON이며 공개 필드는 정확히 네 개다.

```json
{"host":"cmux","multiplexers":["tmux"],"confidence":"high","evidence":["env:CMUX_SURFACE_ID","env:TMUX"]}
```

- `host`: 최종 화면과 터미널 lifecycle을 소유하는 앱. `cmux`, `orca`, 정규화된 일반 터미널명 또는 `unknown`.
- `multiplexers`: host와 shell 사이의 계층. 현재는 `tmux`만 보고한다.
- `confidence`: 직접 환경·조상 계보는 `high`, `TERM_PROGRAM` 폴백은 `medium`, 미판별은 `low`.
- `evidence`: 사용한 신호 이름만 담는다. 환경변수 값, socket 경로, token은 담지 않는다.

우선순위는 `OPAL_TERMINAL_HOST`/cmux 명시 신호 → 현재 프로세스 조상 → tmux client 조상 → `TERM_PROGRAM` → `unknown`이다. 설치된 앱 목록이나 시스템 전체 실행 프로세스는 조회하지 않는다. `OPAL_TERMINAL_HOST`는 wrapper/launcher가 불완전한 프로세스 계보를 보완할 때 `cmux` 또는 `orca`만 명시할 수 있다.
