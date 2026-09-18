# STATE: OPAL 범용 E2E 하네스 구현 (제안서 태스크 2~9)

> 최종 갱신: 2026-09-13 12:17:49
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-12 21:00 | `docs/proposals` 미커밋 7파일을 워크트리 생성 전에 커밋 | 워크트리가 main HEAD에서 분기하므로 미커밋 제안서 최신본이 작업본에 누락된다. 캡틴 승인 후 `35c62d0` 커밋 |
| 2 | 2026-09-12 21:00 | 프로젝트 범위 = 제안서 §14 태스크 2~9 전부 | 태스크 1(E2E profile·verdict 계약)은 태스크 125로 완료. 캡틴 승인 |
| 3 | 2026-09-12 21:05 | D1.5 여정 매핑 스킵 | 본 프로젝트는 E2E 하네스·CLI 내부 자산이며 사용자 대면 화면을 신설하지 않는다. Console FE 변경은 API base URL 주입 등 런타임 설정이고 UI 기능이 아니다 (`references/journey-flow.md` §2 「CLI 내부 로직」 행) |
| 4 | 2026-09-12 21:55 | D6 fail 대응 — 실행 스켈레톤(T01)이 FE 주소 주입·CORS를 흡수하고 T03·T04 제거 | oppl SKILL D5 [MUST]가 실행 스켈레톤을 의존 루트 P0로 규정하므로, 의존 역전(T03·T04를 루트로) 대안은 규약 위반이다. 흡수가 유일한 정합 해 |
| 5 | 2026-09-12 21:55 | backlog.json·BACKLOG.md 삭제 후 `backlog-tool init` 재생성 | backlog-tool에 태스크 삭제 서브명령이 없고 `init --force`가 기존 태스크를 보존한다. 실행 0건 상태의 재생성이며 JSON 손편집이 아니다 |
| 6 | 2026-09-12 21:57 | 격리 `OPAL_HOME` 생성을 범위 밖으로 선언 | 배포본 생성은 설치 파이프라인 소관이다. 하네스가 install을 호출하면 저장소 무오염(AC-13)·사용자 자원 보호(C-2)를 깬다(TD-9) |
| 7 | 2026-09-12 22:18:56 | additional row inserted after row 13: stage=EXECUTE, item=T01: 실행 스켈레톤 — 주소 주입·CORS 포함 FE→BE 관통 (T1~T5+G), key=execute.t01_1, new_row_id=14 | additional work entry |
| 8 | 2026-09-12 23:45:19 | additional row inserted after row 14: stage=EXECUTE, item=T02: Console 프로세스 소유권 — PID 레코드·pkill 2지점 제거 (T1~T5+G), key=execute.t02_1, new_row_id=15 | additional work entry |

## 블로커
없음
