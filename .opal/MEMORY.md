# opal Memory Index

> 최종 갱신: 2026-06-11 21:50 (태스크 016 완료 — wiki 지능화, brain 54페이지)
> last_task_number: 16

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
| 2026-06-11 22:43 | task | 대기 | `memory/follow-up-code-scan-phase2.md` | 010 Phase 2 후속 — 워커 자체 탐색 강제(code-scan 우선) 격상. 운영 데이터 축적 후 판단 |
| 2026-06-11 22:43 | task | 대기 | `memory/follow-up-code-scan-phase2.md` | 010 후속 — OPAL 본 프로젝트 @header 커버리지 확충. brain analyze 품질의 원료 (현 2파일 수준, 016 세션 확인) |
| 2026-06-11 22:43 | task | 폐기 기록 | `memory/follow-up-code-scan-phase2.md` | 010 v2 폐기 — Phase 3 .md @header 표준화. 사유: 문서 요약·검색은 brain ingest가 흡수(016 W2) |


## 작업 히스토리 (최대 10개, FIFO)

> v0.5.0 베이스라인 시작 — 이전 작업 히스토리는 git log + tasks/ 폴더(삭제됨)에서 추적
> 새 태스크는 001부터 채번

| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|----------|------|------|------|---------|---------|
| 2026-06-11 | 016 wiki 지능화 (opal-wiki-pilot 완성, agentic) — brain-tool 타입 동적화+analyze/ingest-scan(83 tests)+SKILL 4모드 지능화(v1.2 source_ref MUST)+W4/W5 PM 규칙+7 pilot CLOSE 훅(rows 불변)+install 배포+brain 54페이지(dogfooding+백필+synthesis+CLOSE ingest 실증). M-4 opal-brain 유지·M-5 brain git 추적. 캡틴 테스트로 멱등 결함 발견·해소. 커밋 6b29bb2 (브랜치 feat/opal-brain-wiki) | 완료 | tasks/016-260611-opp-wiki-intelligence/ | 2026-06-11 18:21 | 2026-06-11 21:50 |
| 2026-06-10 | 015 OPAL Project Brain 코어 — llm-wiki 융합 지식 위키: brain-tool(Python 8커맨드 66test)+opal-brain 스킬(4모드)+PM융합+opp CLOSE 자동 ingest 파일럿+brain 시드(entity2/concept1). origin=SSOT/wiki=요약+참조 단방향. install·전체pilot확산·wiki지능화는 016 (agentic) | CLOSE | tasks/015-260610-opp-opal-brain/ | 2026-06-10 00:34 | 2026-06-11 18:19 |
| 2026-05-20 | 007 cmux-tool 범용 확장 + wtm-agent fallback 체인 재배선 (원래 006 채번 → 다른 PC 006 install-linux와 충돌하여 007 재채번) | CLOSE | tasks/007-260520-opp-cmux-tool-generic-expansion/ | 2026-05-20 20:02 | 2026-05-23 00:02 |
| 2026-05-24 | 008 opwt 산출물 체계 v4 — interview 통합 + PRD 8섹션 + 시나리오·화면 흐름도 + WBS 제거 (app-planning-presentation 자료 흡수) | CLOSE | tasks/008-260524-opp-opwt-v4-output-system/ | 2026-05-24 13:57 | 2026-05-24 15:35 |
| 2026-05-24 | 009 Codex CLI OPAL 프레임워크 통합 — 4번째 플랫폼 편입 (부트스트래퍼 + sub-agent TOML 어댑터 + codex mcp add + 모델 매핑 gpt-5-mini/gpt-5-codex/gpt-5.1-codex-max) | CLOSE | tasks/009-260524-opp-codex-bootstrapper-integration/ | 2026-05-24 18:11 | 2026-05-24 22:41 |
| 2026-05-26 | 010 code-scan PM 우선 무조건화 (v2 다이어트, semi-agentic) — 코드 작업 한정 디스패치 전 무조건화+scan.json 즉석 자동 생성+빈 결과 폴백 3분기+사용자 오버라이드+brain↔code-scan 역할 분담 4축(선별·신선도·깊이, analyze 의존 명문화)+PM Gate 14번. 규약 .md 7파일, install 2회 배포. 후속=Phase2 워커 강제·@header 커버리지 확충(메모리 기록). 커밋 완료(feat/opal-brain-wiki) | 완료 | tasks/010-260526-opp-code-scan-pm-mandate/ | 2026-05-26 15:24 | 2026-06-11 22:56 |
| 2026-06-02 | 011 모델 매핑 최신화 + 최신 추종 전략 — Gemini standard/advanced 부동 별칭(`-latest`) + light 핀(`gemini-3.1-flash-lite`) + Codex gpt-5.4-mini/gpt-5.5/gpt-5.3-codex + OpenAI 참조전용 + windows.ps1 4번째 동기지점 신규발견 (agentic) | 완료 | tasks/011-260602-opp-model-mapping-latest-tracking/ | 2026-06-02 19:57 | 2026-06-02 20:18 |
| 2026-06-07 | 012 OPAL 헌법(PRINCIPLES.md) 신설 — 카파시 스킬 철학 SSOT + always-on 등록(AGENT.md Eager 2.5) + 테스트 하네스 §4 집행(목업 금지·동작 증거: test-agent adversarial화·qa-standards·test-scenario-guide) + coding-principles 다이어트 + install 배포 (agentic) | CLOSE | tasks/012-260607-opp-opal-principles-constitution/ | 2026-06-07 17:44 | 2026-06-07 17:44 |
| 2026-06-07 | 013 state-tool 동작 증거 강제 게이트 — 헌법 §4 deterministic 집행: verify 서브커맨드(mock 코드패턴 검출 + 증거 누락 검출) + cmd_mark TEST stage 자동 훅 + ERROR_CODES 2종 + TestVerify 13케이스(136 passed). 캡틴 사례(목업 API) 기계적 차단 (agentic) | CLOSE | tasks/013-260607-opds-state-tool-enforcement/ | 2026-06-07 | 2026-06-07 |
| 2026-06-07 | 014 파이프라인 간소화 — 전 Phase 완료: stage-transition guard(P1)+opds 19→10(P2)+QA→PM Gate 통합(P3)+전 pilot STATE 재구성·gate-pass deprecate(P4, opd 28→15/opsdd 35→24)+L2 경량트랙 공식화(P5). 158 passed, 동작검증 불변. 후속=install 배포 (semi-agentic) | 완료 | tasks/014-260607-opp-pipeline-simplification/ | 2026-06-07 | 2026-06-08 07:31 |
