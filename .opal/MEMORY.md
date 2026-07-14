# opal Memory Index

> 최종 갱신: 2026-06-26 (044 도구·MCP·스킬 통합 검색·사용법·활용 체계 — TASK)
> last_task_number: 62


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
| 061 콘솔 설정 화면 예약 | 2026-07-14 | task | active | memory/061_콘솔_설정_화면_예약.md | 프로젝트별 설정 화면 — 풀 토글+console.config+로컬 설정. //opd --agentic 착수 대기 |
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
| 062 브레인답변 content-driven 6단계 워크플로우 | 2026-07-14 | 완료·커밋대기 | tasks/062-260714-opds-브레인답변-레이아웃-워크플로우/ | opbr query 답변을 content-driven 6단계 워크플로우로 재구조화. 6축→5후보·가드3종·가독성규율. All Pass. 후속=커밋 |
| 060 브레인 프라임 연결 풀 | 2026-07-14 | 완료 | tasks/060-260713-opd-브레인-프라임-연결풀/ | prewarm 선프라임+웜풀 신설, 웜9.6s vs 콜드26.7s. 13/13 Pass. 후속=커밋·배포·설정화면 |
| 059 opal-agent 마커 3-way + cold session id | 2026-07-13 | 완료 | tasks/059-260713-opds-에이전트마커-3단-세션주입/ | assistant 캡+--session-id 신설, 17/17 GREEN·실측 캡 관측. 브레인 이관 선행조건 완비. 후속=커밋·opbr 이관 |
| 057 opal-cli console scan 설정 자동생성 | 2026-07-13 | TEST 완료·CLOSE 대기 | tasks/057-260710-opds-콘솔스캔-설정자동생성/ | console scan 신설+install 자동호출(mac v3.9/win v1.17). 커밋 d9c9902·bed80ad. 후속=DONE.md |
| 056 oppl 루프 오케스트레이터 신설 | 2026-07-10 | 완료 | tasks/056-260710-opd-oppl-루프-오케스트레이터/ | oppl 2-루프+evaluator+backlog-tool+scenario-* 신설. All Pass·드라이런 evidence. 후속=커밋·scenario-red |
<!-- memory:history:end -->
