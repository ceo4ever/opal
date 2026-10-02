---
template: sdlc-v2
---
# TASK: @header 이력 누적 코드 차단 + state-tool 동작 보존 분할

## Problem

@header `description`에 태스크별 변경 내용을 덧붙이는 이력 누적은 태스크 107에서 금지했다(`opal/core/references/harness/header-rules.md:123`). 하지만 이 규칙은 막는 장치 없이 경고로만 집행되고 있어 같은 위반이 다시 쌓였다.

- 경고만 하고 막지 않는다. `code-scan validate`는 서로 다른 태스크 번호 2개 이상을 감지하면 `header_history`를 내지만 종료 코드를 바꾸지 않는다(`header-rules.md:124`). 그래서 PM Gate·TEST Gate를 그대로 통과했다. 2026-10-01 저장소 전체 validate에서 `header_history` 10건이 나왔다(9개 파일, 예: `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`).
- 위반이 커지면 검사에서 사라진다. code-scan은 파일 앞 24,576바이트만 읽어 머리말을 찾는다(`opal/tools/code-scan/code-scan.js:45`). 머리말이 그보다 길면 "머리말 없음(uncovered, pre_existing)"으로 분류되어 이력 검사도 하지 않고 비차단 처리된다. 실측상(PLAN 단계 재측정) 읽기 범위를 넘는 머리말은 `opal/tools/state-tool/state_tool.py`(머리말 끝 26,154바이트) 1건이다. `opal/tools/ownership-tool/tests/test_integration.py`·`test_session_start.py`는 머리말이 각각 2,538·462바이트에서 끝나고 JSON이 아닌 `# key: value` 형식이라 파싱되지 않아 uncovered가 된 것으로, 읽기 범위 초과가 아니며 이 태스크 범위 밖이다.
- `state_tool.py`는 107에서 설명을 10,644자에서 2,002자로 줄였는데, 이후 태스크 123~170을 거치며 16,336자로 다시 늘었다(git 이력 `5a8ad2bf`→`8ca5cf18`).
- 같은 파일은 8,256줄, 최상위 함수 199개로 커졌다. 여러 책임(상태 입출력·가드·실행 로그·검증 8종·설계 게이트·모드 판정·부트 브리핑 등)이 한 파일에 섞였고, 7월 이후 62개 커밋이 이 파일을 건드려 동시 진행 태스크 간 충돌 위험이 크다.

## Proposed outcome

- @header `description`·`note`에 이력을 덧붙이면 그 변경은 프레임워크 검사를 통과하지 못하고 막힌다. 막는 판정은 경고가 아니라 실패다.
- 머리말이 읽기 범위를 넘어 판정할 수 없는 파일도 조용히 "머리말 없음"으로 빠지지 않고 실패로 드러난다.
- 현재 저장소에 남아 있는 이력 누적 머리말과 읽기 범위를 넘은 머리말이 모두 정리되어, 차단을 켠 상태에서 저장소 전체 검사가 통과한다.
- `state_tool.py`는 책임 영역별로 나뉜 구조가 되고, 기존 CLI 호출 경로·명령·출력은 그대로 유지된다.

## Affected users and systems

- 사용자: OPAL로 태스크를 수행하는 캡틴·PM·워커, 머리말을 갱신하는 모든 워커.
- 포함: `opal/tools/code-scan/`의 머리말 이력·읽기 범위 판정과 차단 경로, 그 판정을 소비하는 게이트 문서(`header-rules.md` 등 해당 owner 문서), 이력 누적·읽기 범위 초과 머리말이 있는 저장소 파일 정리, `opal/tools/state-tool/state_tool.py` 구조 분할과 그 테스트·README, install 배포 확인.
- 제외: state-tool의 동작·명령·출력·오류 코드 변경, 큰 명령 함수의 로직 재설계와 파일럿 전용 가드의 플러그인 분리(후속 태스크), 머리말 커버리지(uncovered) 자체를 높이는 작업.

## Constraints

- C-1: state-tool 외부 계약은 바뀌지 않는다. `run.sh`·`state_tool.py` 실행 경로, 서브커맨드·인자, stdout JSON·종료 코드, 오류 코드, `state.json`·STATE.md 산출물이 분할 전과 같다.
- C-2: 머리말 정리는 이력을 지우고 현재 역할만 남기며, 파일 동작은 바꾸지 않는다.
- C-3: 프로젝트 공통 계약을 따른다 — 배포 경계와 플랫폼 분기 금지(`.opal/AGENT.md` §금지사항), 머리말 원칙 원문은 `header-standard.md` §2.1이 소유(`header-rules.md:123`).

## Acceptance criteria

- AC-1: @header `description`·`note`에 서로 다른 태스크 번호 2개 이상이 있는 파일을 변경하면 그 변경 검사가 실패로 끝나고, PM Gate가 이 실패를 통과시키지 않는다.
- AC-2: 머리말이 code-scan 읽기 범위를 넘어 판정할 수 없는 파일은 "머리말 없음"으로 조용히 처리되지 않고, 검사 결과에서 실패로 드러난다.
- AC-3: 정리 후 저장소 전체 code-scan 검사에서 이력 누적과 읽기 범위 초과가 0건이다.
- AC-4: `state_tool.py`가 책임 영역별 모듈로 나뉘고, 분할 전후에 기존 테스트 전체와 대표 명령의 출력이 같다.
