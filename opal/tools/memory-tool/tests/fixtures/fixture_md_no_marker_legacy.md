# invest-stock 프로젝트 Memory Index

## 메모리 인덱스

| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|----------|----------|------|------|------|
| 2026-06-20 12:34 | 아키텍처/결정 | 확정 | memory/mvp-design-decisions.md | MVP 핵심 결정(시장·토스API·HITL·스택·연계기준·OAuth접속) + 추가확정(2026-06-21): Python3.14·uv·APScheduler·FE shadcn·공격적 병렬 WBS |
| 2026-06-24 09:28 | 프로젝트/구현현황 | 확정 | memory/stock-analysis-status.md | 종목 분석 BE·FE·테스트 엔드투엔드 완료(pytest 208·vitest 136). 정정(06-24): 분석 LLM 연결은 **이미 완료**(LLMBasedPersonaInvoker 배선). 남은 갭: 프롬프트 정합화·종목검색·추천연동 |
| 2026-06-24 18:42 | 프로젝트/진행계획 | 승인대기 | memory/stock-analysis-search-plan.md | 다음 세션 이어가기: ① 분석 프롬프트를 .claude/agents 4종에 정합화 ② 로컬 종목마스터+토스 조회 검색 구현. 결정·파일·제약(토스키 부재) 정리. 구현 착수 직전 |

## 작업 히스토리

| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|---|------|------|------|---------|---------|
| 1 | opi 프로젝트 초기화 | 완료 | docs/, .opal/ | 2026-06-20 09:55 | 2026-06-20 11:40 |
| 2 | opdw 와이어프레임 | 완료 | tasks/002.../, prototype/ | 2026-06-20 12:49 | 2026-06-20 23:21 |
| 3 | oppd 개발 파일럿 | Phase 3 실행 — **1단계 A01~A30 30/30 완료** (Wave4 완료, vitest 136·build green, main d0cc984). CLOSE(DONE.md) 캡틴 승인 대기 / 2·3단계 로드맵 | tasks/003-oppd-invest-stock/ | 2026-06-21 09:08 | - |
