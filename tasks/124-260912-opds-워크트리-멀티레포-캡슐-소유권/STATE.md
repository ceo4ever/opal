# STATE: 워크트리 multi-repo 캡슐 소유권 — 계약 이관과 worktree-tool 구현

> 최종 갱신: 2026-09-12 20:09:05
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-12 18:00:34 | force flag used at init | 행 구성 정정 — opds는 pipeline-short.json 소유. 최초 init이 opd용 pipeline.json을 참조해 ANALYSIS·TEST-SCENARIO 행이 잘못 생성됨 |

## 블로커
없음
