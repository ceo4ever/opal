---
template: sdlc-v2
---
# ANALYSIS: 세션 브리핑 출력 집행

> 입력: [TASK.md](TASK.md) | 조사 기준: 현재 워킹트리 · 2026-09-12 08:59 KST

## Findings

| 질문 | 확인한 사실 | 근거 | 설계에 미치는 영향 |
|---|---|---|---|
| 조회 성공 뒤 왜 출력이 누락될 수 있는가 | 기존 계약은 상태·메모리 도구의 JSON을 각각 조회한 뒤 모델이 블록을 조립하도록 맡겼고, 감사도 명령 문구와 JSON 필드만 검사했다. | `TASK.md` §Problem, `scripts/tests/task113_bootstrap_audit.py:397-487` | JSON→사용자 응답 사이를 결정론적 생산자로 대체해야 한다. |
| 어느 컴포넌트가 완성된 브리핑을 소유해야 하는가 | `event-loader`는 이미 세션 이벤트 진입점이며 소스·설치본 root를 공통 해석한다. 설치 스크립트도 `opal/tools/` 전체와 플랫폼 부트스트래퍼를 배포한다. | `opal/tools/event-loader/event_loader.py:62-92`, `scripts/install-mac.sh:1289-1308`, `scripts/install-mac.sh:1430-1451` | 새 도구를 늘리지 않고 `event-loader project-brief`로 조회 조율과 렌더링을 결합할 수 있다. |
| 기존 경계를 어떻게 보존하는가 | 상태 도구는 미완료 태스크 1건, 메모리 도구는 검토 후보 2건을 이미 bounded JSON으로 반환한다. | `opal/tools/state-tool/state_tool.py:2294-2322`, `opal/tools/memory-tool/README.md` §show | 두 SSOT의 선택 로직은 바꾸지 않고 성공 결과만 조합해야 한다. |

## Change boundary

| 경로·인터페이스 | 역할 | 변경 영향 |
|---|---|---|
| `opal/tools/event-loader/event_loader.py` `project-brief` | 상태·메모리 조회와 Markdown 조립 | 신규 공개 CLI, UTF-8 상한과 실패 시 블록 생략을 코드로 집행 |
| `opal/bootstrapper/*-bootstrap*`, `opal/core/AGENT.md` | 최초 세션 소비자 | 두 JSON 명령을 단일 명령과 stdout 전문 출력 의무로 교체 |
| `scripts/tests/task113_bootstrap_audit.py`, `opal/tools/event-loader/tests/` | 회귀 게이트 | 완성된 stdout, 빈 결과, 1,024바이트 상한을 실제 실행으로 검증 |
| `opal/core/references/opal-pm.md`, `docs/ARCHITECTURE.md`, `docs/PROJECT.md`, event-loader README | 문서 소비자 | 새 소유권과 source→installed 경계를 최신화 |

## Critical assumptions

| 가정 | 확인 방법·결과 | 남은 한계 |
|---|---|---|
| event-loader가 형제 상태·메모리 도구를 소스와 설치본에서 동일하게 찾는다 | 도구 디렉터리 상대 경로를 사용하고 source fixture 및 실제 프로젝트 실행이 통과했다. | 설치본은 install 후 별도 parity와 실호출 확인 필요 |
| 완성된 Markdown이면 모델의 재조립 누락 지점을 제거한다 | 실제 프로젝트 출력에서 부트스트랩·이어보기·우선 검토가 한 stdout으로 생성됐다. | 플랫폼이 stdout 전문 출력 MUST 자체를 위반하는 경우까지 외부 hook 없이 강제할 수는 없음 |

## Handoff

- PLAN에서 결정할 것: 단일 `project-brief` CLI 공개 계약, 실패 폴백, 플랫폼 문구와 실제 stdout 회귀 범위
- 착수 차단: 없음
