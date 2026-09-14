# STATE: 태스크 실행 로그 표준화

> 최종 갱신: 2026-09-13 04:55:05
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-12 17:36 | 파일럿을 opd → oppl로 전환 | 제안서 §10이 Phase 0~1C를 독립 태스크로 고정 — opd 1태스크 파이프라인은 순서·종료조건·커버리지를 집행할 수 없음 |
| 2 | 2026-09-12 17:36 | 제안서 §4.2.1 신설 — 계약/데이터 소유 분리 | 분리 없이는 Phase 0 실측 전에 CONTRACT 확정 불가 → D7 잠금과 구조적 충돌 (커밋 b44ef2f) |
| 3 | 2026-09-12 17:36 | Phase 2·3을 백로그 범위에서 제외 | 제안서가 "1C 표본으로 필요성 검증 후 별도 승인"으로 한정 — Loop 2 종료 판정이 1C까지 닫혀야 done-check 성립 |
| 4 | 2026-09-12 17:40 | D1.5 여정 매핑 스킵 | 대상이 CLI 도구·프레임워크 내부 계약이며 최종 사용자 화면 여정이 없음 — `references/journey-flow.md` §2의 비-user-facing 조건에 해당 |
| 5 | 2026-09-12 17:40 | 워킹 스켈레톤을 CLI 관통으로 재정의 | oppl D5 `[MUST]`의 BE+FE+브라우저 구성이 CLI 프로젝트에 적용 불가 — `state-tool init` → `run-log-tool append` → `validate-run` 관통 1건을 등가로 채택 (제안서 §10 Phase 1A) |
| 6 | 2026-09-12 19:22:51 | additional row inserted after row 13: stage=EXECUTE, item=T01: Phase 0 — 채널 관측 능력 실측 (T1~T5+G), key=execute.t01_1, new_row_id=14 | additional work entry |
| 7 | 2026-09-12 20:02:41 | additional row inserted after row 14: stage=EXECUTE, item=T01G: 게이트 — Phase 1A 승인 (사람), key=execute.t01g_1, new_row_id=15 | additional work entry |
| 8 | 2026-09-12 20:03:02 | additional row inserted after row 15: stage=EXECUTE, item=T02: 워킹 스켈레톤 — CLI 관통 1건 (T1~T5+G), key=execute.t02_1, new_row_id=16 | additional work entry |
| 9 | 2026-09-13 00:06:32 | additional row inserted after row 16: stage=EXECUTE, item=T03: 기록 코어 — 스키마·출처·멱등·순번 (T1~T5+G), key=execute.t03_1, new_row_id=17 | additional work entry |
| 10 | 2026-09-13 00:06:33 | additional row inserted after row 17: stage=EXECUTE, item=T05: 상태 1.2 — 보관함·중단 가능 초기화 (T1~T5+G), key=execute.t05_1, new_row_id=18 | additional work entry |

## 블로커
없음
