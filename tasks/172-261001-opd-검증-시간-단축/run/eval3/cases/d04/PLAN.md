<!--
원본: 태스크 162(opd-TEST-단계-소요시간-단축), 설계 게이트 i1 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "W-1 CLI 입력·출력과 저장 구조, 중복·누락 종료 처리, 상한 초과 상태 전이·재개 방법 미정"
이 Work item은 원본 i1 PLAN의 미결정을 의도적으로 재현한다 — "~일 수도 있고, 또는 ~일 수도 있다" 식으로
CLI 입출력 형식, 중복/누락 종료 처리, 상한 초과 전이가 모호하게 남아 있다.
-->
---
template: sdlc-v2
---
# PLAN: TEST 단계 소요시간 측정 CLI 추가(합성 축소판)

## Approach

기존 state-tool에 측정 서브커맨드를 추가하는 방향으로 간다.

## Findings

### 직접 변경

- `opal/tools/test-tool/duration_cli.py`(신규) — 소비자 없음(신규). 측정 CLI 본체.

### 회귀 확인

- 기존 state-tool 서브커맨드는 영향 없음(신규 파일이라 기존 경로를 건드리지 않음).

### 문서 갱신

- `opal/tools/test-tool/README.md` — 신규 서브커맨드 설명 추가.

### 미확인 가정

- 저장 위치를 state.json에 둘지 별도 파일에 둘지는 구현 중 정할 수도 있다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 측정 데이터 저장 위치 | state.json에 새 블록을 추가하거나, 혹은 별도 `run/duration.json` 파일에 둘 수도 있다 — 구현 시점에 더 쉬운 쪽으로 정한다. | 아직 어느 쪽이 기존 계약과 더 잘 맞는지 결정하지 않았다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 측정 CLI 구현 | opal-task-agent | `opal/tools/test-tool/duration_cli.py` | `start`/`stop` 서브커맨드를 추가한다. CLI 입력·출력 형식(인자, JSON 응답 스키마)과 저장 구조(파일 또는 state.json 블록)는 구현하면서 정한다. `stop` 없이 다시 `start`하는 경우나 `start` 없이 `stop`하는 경우는 적절히 처리한다. 측정 상한을 넘긴 세션은 적절한 상태로 전이하고, 필요하면 재개할 수 있게 한다 | 없음 | P1 | AC-1, AC-2, AC-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 저장 구조 미정으로 구현 중 재작업 가능성 | 측정 CLI 구현 일정 | 구현 중 저장 위치를 바꾸면 재작업이 생길 수 있다 | 없음(아직 미해결) |

## Release and recovery

별도 배포 절차 없음(신규 CLI, 내부 전용).
