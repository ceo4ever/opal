# opal Memory Index

> 최종 갱신: 2026-06-26 (044 도구·MCP·스킬 통합 검색·사용법·활용 체계 — TASK)
> last_task_number: 63


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





> v0.5.0 베이스라인 시작 — 이전 작업 히스토리는 git log + tasks/ 폴더(삭제됨)에서 추적
> 새 태스크는 001부터 채번

## 메모리
<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
| Console 브레인 구독 인증 | 2026-06-22 | project | active | `memory/console-brain-subscription-auth.md` | Console 브레인 질의는 종량제 API 아닌 사용자 Claude 구독(로컬 claude -p). API키·SDK 금지 |
| 브레인 질의 콜드 경량화(037후속) | 2026-06-23 | task | active | `memory/follow-up-brain-query-lite.md` | 브레인 질의 콜드 latency 경량화 — 검색을 LLM 밖 brain-tool로. opbr --lite 권고 |
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
| 063 콘솔 브레인 휘발성 단일 세션 | 2026-07-15 | 완료·커밋 | tasks/063-260715-opd-콘솔-브레인-세션-단순화/ | 멀티대화·이력 제거→휘발 단일세션, 풀2+need충전, 이탈가드4경로. FE85·BE249 Pass |
| 061 콘솔 설정 화면 — 프라임 풀 토글 | 2026-07-14 | 완료 | tasks/061-260714-opd-콘솔-설정-화면/ | 설정 라우터 격리+토글 단일 반영(캡틴 축소 확정). 245 GREEN·E2E Pass. 커밋 9443606·배포 완료 |
| 062 브레인답변 content-driven 6단계 워크플로우 | 2026-07-14 | 완료·커밋대기 | tasks/062-260714-opds-브레인답변-레이아웃-워크플로우/ | opbr query 답변을 content-driven 6단계 워크플로우로 재구조화. 6축→5후보·가드3종·가독성규율. All Pass. 후속=커밋 |
| 060 브레인 프라임 연결 풀 | 2026-07-14 | 완료 | tasks/060-260713-opd-브레인-프라임-연결풀/ | prewarm 선프라임+웜풀 신설, 웜9.6s vs 콜드26.7s. 13/13 Pass. 후속=커밋·배포·설정화면 |
| 059 opal-agent 마커 3-way + cold session id | 2026-07-13 | 완료 | tasks/059-260713-opds-에이전트마커-3단-세션주입/ | assistant 캡+--session-id 신설, 17/17 GREEN·실측 캡 관측. 브레인 이관 선행조건 완비. 후속=커밋·opbr 이관 |
<!-- memory:history:end -->
