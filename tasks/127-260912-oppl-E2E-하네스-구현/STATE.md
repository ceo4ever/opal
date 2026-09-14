# STATE: OPAL 범용 E2E 하네스 구현 (제안서 태스크 3~9)

> 최종 갱신: 2026-09-14 16:28:35
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-14 16:05:06 | force flag used at init | 캡슐 교체 — oppl → opd 전환(캡틴 지시). oppl 수행분은 archive/에 보존(state.oppl.json 포함), 계약 4종(PRD·TRD·CONTRACT·surfaces.json)은 캡슐 루트 유지. 태스크 번호·브랜치 불변 |

## 블로커
없음
