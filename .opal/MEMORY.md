# opal Memory Index

> 최종 갱신: 2026-05-20 23:15 (태스크 006 채번 — 재정렬)
> last_task_number: 6

## 메모리 카테고리

| 카테고리 | 설명 | 완료 시 |
|----------|------|---------|
| task | 일회성 작업 계획/예정 | 삭제 |
| project | 프로젝트 비전, 방향성 등 지속 지식 | 유지 (폐기 시 삭제) |
| architecture | 아키텍처 설계 결정과 근거 | 유지 (변경 시 갱신) |
| feedback | 캡틴의 작업 방식 피드백 | 유지 (철회 시 삭제) |
| preferences | 이 프로젝트에서 캡틴이 선호하는 방식 | 유지 |
| issues | 반복되는 이슈와 해결법 | 유지 |

> 메모리 파일은 `memory/` 디렉토리에 저장한다.
> 새 메모리가 생기면 이 인덱스에 파일 경로와 설명을 추가한다.
> **task 타입은 완료 시 메모리 파일 + 인덱스 항목을 삭제한다.**

## 메모리

| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|----------|----------|------|------|------|
| 2026-05-09 | preferences | 유지 | [memory/preferences_default_semi_agentic.md](memory/preferences_default_semi_agentic.md) | 캡틴 기본 작업 패턴: PLAN 검토 + EXECUTE 자율 (semi-agentic 모드 기본 채택) |


## 작업 히스토리 (최대 10개, FIFO)

> v0.5.0 베이스라인 시작 — 이전 작업 히스토리는 git log + tasks/ 폴더(삭제됨)에서 추적
> 새 태스크는 001부터 채번

| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|----------|------|------|------|---------|---------|
| 2026-05-12 | 001 카르파시 행동 원칙 흡수 — Coding Principles SSOT 신설 + TASK AC 보강 | CLOSE | tasks/001-260512-opp-coding-principles-ssot/ | 2026-05-12 10:48 | 2026-05-12 14:54 |
| 2026-05-12 | 002 wtm-agent OPAL 표준화 + cmux 통합 + 사용자 surface 재사용 | CLOSE | tasks/002-260512-opp-wtm-opal-standardization/ | 2026-05-12 18:10 | 2026-05-12 22:15 |
| 2026-05-13 | 003 보고 형식 양식 보강 — 결론/근거 번호화 + 이모티 prefix + 다음 블록 2갈래 | CLOSE | tasks/003-260513-opp-reporting-format-enhancement/ | 2026-05-13 17:21 | 2026-05-13 17:48 |
| 2026-05-15 | 004 테스트 시나리오 양식·파이프라인 재설계 — 7섹션 양식(가설→데이터→L×M 매트릭스) + STEP 3.5 신설 + EXECUTE scenario_source + 5단계 직렬 + self-confirming 4분리 | CLOSE | tasks/004-260515-opp-test-scenario-pipeline-redesign/ | 2026-05-15 13:25 | 2026-05-19 17:59 |
| 2026-05-15 | 005 명확화 게이트 SSOT — 추정 진행 차단 + 소크라테스식 인터뷰 | TASK | tasks/005-260515-opp-clarification-gate-ssot/ | 2026-05-15 13:59 | - |
| 2026-05-20 | 006 Linux 설치 스크립트 신설 — scripts/install/linux.sh (원래 001 채번 → divergent reconcile 후 006 재채번) | CLOSE | tasks/006-260520-opp-install-linux/ | 2026-05-20 08:35 | 2026-05-20 22:51 |
