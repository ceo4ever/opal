---
template: sdlc-v2
---
# TASK: 세션 브리핑 출력 집행

## Problem
`session.project` 부트에서 상태·메모리 JSON 조회가 성공해도 첫 응답에 `이어보기`와 `우선 검토`가 누락될 수 있다. 현재 코어 세션 계약은 메모리 조회와 부트스트랩 한 줄만 명시하고(`opal/core/AGENT.md:35-44`, `opal/core/AGENT.md:69-70`), 구체적인 조립 절차는 PM 활성화 뒤에야 로드되는 문서에 있다(`opal/core/references/opal-pm.md:331-384`). 플랫폼 부트스트래퍼 소스에는 렌더링 지시가 있지만(`opal/bootstrapper/codex-bootstrap.md:28-46`), 조회 결과를 실제 사용자 응답으로 내보냈는지는 기존 정적 감사가 검증하지 않는다(`scripts/tests/task113_bootstrap_audit.py:397-487`).

## Proposed outcome
프로젝트 세션 부트가 미완료 태스크나 우선 검토 후보를 조회하면, 해당 내용을 정해진 형식의 첫 사용자 응답으로 빠짐없이 출력한다. 결과가 없거나 조회가 실패한 경우에는 기존의 짧은 부트 응답을 유지한다.

## Affected users and systems
OPAL을 Claude Code, Codex, Cursor, Gemini에서 사용하는 사용자와 `session.project` 이벤트, 플랫폼 부트스트래퍼, 상태·메모리 조회 도구 및 부트 회귀 감사가 영향 범위다. `[ASSISTANT]`, `[WORKER]`, `session.disabled`의 동작과 기존 115 태스크 산출물은 범위에서 제외한다.

## Constraints
- C-1: 최초 브리핑은 `session.project`에서만 출력하고 PM 활성화 시 재생성하지 않는다 (`opal/core/references/opal-pm.md:375-384`).
- C-2: 상태 최대 1건과 검토 후보 최대 2건, UTF-8 1,024바이트 제한 및 빈 결과의 기존 응답 유지 계약을 보존한다 (`opal/core/references/opal-pm.md:347-359`).
- C-3: 플랫폼별 차이는 부트스트래퍼·설치 어댑터에 격리하고 네 플랫폼의 공통 계약을 동일하게 유지한다.
- C-4: 배포 파일 `~/.opal/`을 직접 수정하지 않고 프로젝트 소스 변경 후 공식 install 경로로 배포한다.
- C-5: 기존 115 태스크의 수정 파일과 상태를 변경하거나 되돌리지 않는다.

## Acceptance criteria
- AC-1: 미완료 태스크가 있는 fixture에서 첫 부트 응답에 `이어보기` 제목·단계·다음 행동이 모두 나타난다.
- AC-2: 검토 후보가 있는 fixture에서 첫 부트 응답에 우선순위에 따른 `우선 검토` 항목이 최대 2건 나타난다.
- AC-3: 조회 성공 후 출력 블록을 누락하는 구현 또는 계약 변경이 자동 검증에서 실패한다.
- AC-4: 상태와 검토 후보가 모두 없거나 각 조회가 실패한 fixture에서 기존 짧은 부트 응답이 유지된다.
- AC-5: `[ASSISTANT]`, `[WORKER]`, `session.disabled` fixture에서는 프로젝트 브리핑 조회·출력이 발생하지 않는다.
- AC-6: 네 플랫폼 부트스트래퍼의 공통 본문이 동등하고 source→installed 배포 결과가 검증된다.
