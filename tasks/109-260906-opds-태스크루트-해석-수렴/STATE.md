# STATE: 태스크 루트 해석 수렴 + OPAL_TASKS_ROOT 계약 신설

> 최종 갱신: 2026-09-07 23:37:10
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-06 23:39:00 | force flag used at init | opds → opd 승격(캡틴 //opd --agentic --wt). 사유: 경로 조립 8곳 수렴 + 테스트 하드코딩 4곳 + 하네스 문서 3건 + worktree-tool 응답 확장이 Short Task 규모를 넘어 ANALYSIS·TEST-SCENARIO 단계가 필요하다. 태스크 폴더명의 opds 접미사는 유지한다(폴더 rename은 인용 경로를 깨뜨린다). |

## 블로커
없음
