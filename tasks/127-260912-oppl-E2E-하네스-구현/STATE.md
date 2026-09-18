# STATE: OPAL 범용 E2E 하네스 구현 (제안서 태스크 3~9)

> 최종 갱신: 2026-09-18 14:41:15
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-14 16:05:06 | force flag used at init | 캡슐 교체 — oppl → opd 전환(캡틴 지시). oppl 수행분은 archive/에 보존(state.oppl.json 포함), 계약 4종(PRD·TRD·CONTRACT·surfaces.json)은 캡슐 루트 유지. 태스크 번호·브랜치 불변 |
| 2 | 2026-09-14 17:40 | 표면 커버리지 결손을 분모 축소가 아니라 시나리오 보강으로 해소 | `CONTRACT.md` §B.5:625가 40표면 전수를 분모로 확정하고 `surfaces.json`을 읽기 전용으로 둔다(C-8). 분모를 줄이면 "계약은 있는데 집행자가 없다"는 원 문제를 검증 축에서 재생산한다 |
| 3 | 2026-09-14 18:01 | S-14·S-16을 RED 대상에서 제외하고 구현 후 회귀 가드로 전환 | S-14는 비공개 헬퍼를 겨냥해 `red-first.md` §2 검증 경계 위반, S-16은 AC-16이 선행 커밋으로 기충족. §2의 자동 우회 금지에 따라 워커가 BLOCKED 반환, PM이 실측 후 재정의 |
| 4 | 2026-09-14 18:30 | `CONTRACT.md` §B.1.1을 개정하지 않고 구현을 계약에 맞춘다 | 계약이 SSOT이고 RED 테스트는 그 하위 산출물이다. 구현을 테스트에 맞추면 위계가 뒤집힌다. 재작업 범위는 호출 인자 추가 수준 |
| 5 | 2026-09-18 13:41:05 | current_status changed: in_progress → completed_unmerged | CLOSE 완료 — main 병합 대기 |
| 6 | 2026-09-18 13:48:32 | additional row inserted after row 16: stage=CLOSE, item=ADD-1 Ego Lite driver 흡수, key=close.add_1, new_row_id=17 | additional work entry |
| 7 | 2026-09-18 14:41:15 | current_status changed: completed_unmerged → done | main 병합(ef7b31e)·worktree 회수·메모리 귀속 완료 |

## 블로커

| # | 시점 | 블로커 | 소유 | 상태 |
|---|------|--------|------|------|
| B-1 | 2026-09-15 12:45 | `tool-scan` 4건 실패(`test_agentmd_cmux_routing`·`test_agentmd_usage_discipline`·`test_drift_entries`·`test_registry_parity`)가 main 상속 결함 — 태스크 131 W-16의 레지스트리 표 축소가 이 테스트들이 단언하던 `opal/core/AGENT.md` 인지맵 구조를 제거했다. PM 재검증: `main:opal/core/AGENT.md`에 `cmux-tool`·`playwright` 0건, 테스트 파일은 main과 동일 | **태스크 127 범위 밖** — 별도 태스크 | 이월(W-13 완료 기준에서 제외) |
| B-2 | 2026-09-15 15:20 | `opal-cli mcp add playwright`가 설치본에서 실패 — `mcp.sh:59,113`이 install이 만들지 않는 `~/.opal/opal/core/mcps`를 참조. BEFORE 홈에서도 동일 실패하는 선행 결함 | 태스크 127 범위 밖 | 이월 |
| B-3 | 2026-09-16 01:00 | **F-4(Critical)** `orchestrator._open_executor()`가 human executor에 `prepare`를 dispatch — `HUMAN_OPERATIONS`에 없어 collaborative·manual profile이 `e2e run`으로 실행 불가. AC-9 미충족의 직접 원인 | 태스크 127 | 수정 대기 |
| B-4 | 2026-09-16 01:00 | **AC-12 blocked** — `console_autostart()` 7823 하드코딩 + `install_dashboard()` FE 빌드가 소스 트리 `dist/`에 씀. 격리 `OPAL_HOME` install이 성립하지 않아 S-21이 pass로 올라갈 수 없다 | 태스크 127 | 판정 필요 |
| B-5 | 2026-09-16 01:10 | **F-3** api profile 충실도 상한(`real-http`)과 동결 spec의 `required_fidelity: real-usage`가 모순 — 동결 spec·`e2e_contract.py`(C-1) 양쪽 다 수정 불가로 `all_surfaces_green` 도달 불가 | 태스크 127 | 판정 필요 |
| B-6 | 2026-09-16 01:05 | **F-5** cleanup이 `complete`/`leaked:[]`를 거짓 보고 — 실제 누출 6건을 PM이 수동 회수. 대장이 거짓이면 회수가 소유권 없이 PID만 보고 판단하게 된다 | 태스크 127 | 수정 대기 |

> B-1을 이 태스크에서 고치면 `opal/core/AGENT.md`(미소유)에 playwright fallback 산문을 되살려야 해 AC-14(경쟁 SSOT 0건)와 정면 충돌한다. 따라서 수정이 아니라 **이월**이 옳다.
