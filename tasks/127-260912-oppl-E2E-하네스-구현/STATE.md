# STATE: OPAL 범용 E2E 하네스 구현 (제안서 태스크 3~9)

> 최종 갱신: 2026-09-14 17:47:53
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-14 16:05:06 | force flag used at init | 캡슐 교체 — oppl → opd 전환(캡틴 지시). oppl 수행분은 archive/에 보존(state.oppl.json 포함), 계약 4종(PRD·TRD·CONTRACT·surfaces.json)은 캡슐 루트 유지. 태스크 번호·브랜치 불변 |
| 2 | 2026-09-14 17:40 | 표면 커버리지 결손을 분모 축소가 아니라 시나리오 보강으로 해소 | `CONTRACT.md` §B.5:625가 40표면 전수를 분모로 확정하고 `surfaces.json`을 읽기 전용으로 둔다(C-8). 분모를 줄이면 "계약은 있는데 집행자가 없다"는 원 문제를 검증 축에서 재생산한다 |
| 3 | 2026-09-14 18:01 | S-14·S-16을 RED 대상에서 제외하고 구현 후 회귀 가드로 전환 | S-14는 비공개 헬퍼를 겨냥해 `red-first.md` §2 검증 경계 위반, S-16은 AC-16이 선행 커밋으로 기충족. §2의 자동 우회 금지에 따라 워커가 BLOCKED 반환, PM이 실측 후 재정의 |
| 4 | 2026-09-14 18:30 | `CONTRACT.md` §B.1.1을 개정하지 않고 구현을 계약에 맞춘다 | 계약이 SSOT이고 RED 테스트는 그 하위 산출물이다. 구현을 테스트에 맞추면 위계가 뒤집힌다. 재작업 범위는 호출 인자 추가 수준 |

## 블로커

| # | 시점 | 블로커 | 소유 | 상태 |
|---|------|--------|------|------|
| B-1 | 2026-09-15 12:45 | `tool-scan` 4건 실패(`test_agentmd_cmux_routing`·`test_agentmd_usage_discipline`·`test_drift_entries`·`test_registry_parity`)가 main 상속 결함 — 태스크 131 W-16의 레지스트리 표 축소가 이 테스트들이 단언하던 `opal/core/AGENT.md` 인지맵 구조를 제거했다. PM 재검증: `main:opal/core/AGENT.md`에 `cmux-tool`·`playwright` 0건, 테스트 파일은 main과 동일 | **태스크 127 범위 밖** — 별도 태스크 | 이월(W-13 완료 기준에서 제외) |

> B-1을 이 태스크에서 고치면 `opal/core/AGENT.md`(미소유)에 playwright fallback 산문을 되살려야 해 AC-14(경쟁 SSOT 0건)와 정면 충돌한다. 따라서 수정이 아니라 **이월**이 옳다.
