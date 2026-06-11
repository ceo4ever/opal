# opal Memory Index

> 최종 갱신: 2026-06-11 (feat/opal-brain-wiki ↔ main 병합 — 양 PC 작업 합류)
> last_task_number: 17
> ⚠️ 채번 충돌: 015·016이 양 PC에서 중복 사용됨 (main: 015 보고형식·016 TDD·017 가드 / brain 라인: 015 brain 코어·016 wiki 지능화). 다음 채번은 018부터.

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
| 2026-06-11 | 016-brain wiki 지능화 (opal-wiki-pilot 완성, agentic — ⚠️중복 채번) — brain-tool 타입 동적화+analyze/ingest-scan(83 tests)+SKILL 4모드 지능화(v1.2 source_ref MUST)+W4/W5 PM 규칙+7 pilot CLOSE 훅(rows 불변)+install 배포+brain 54페이지(dogfooding+백필+synthesis+CLOSE ingest 실증). M-4 opal-brain 유지·M-5 brain git 추적. 커밋 6b29bb2 | 완료 | tasks/016-260611-opp-wiki-intelligence/ | 2026-06-11 18:21 | 2026-06-11 21:50 |
| 2026-06-10 | 015-brain OPAL Project Brain 코어 (⚠️중복 채번) — llm-wiki 융합 지식 위키: brain-tool(Python 8커맨드 66test)+opal-brain 스킬(4모드)+PM융합+opp CLOSE 자동 ingest 파일럿+brain 시드. origin=SSOT/wiki=요약+참조 단방향 (agentic) | CLOSE | tasks/015-260610-opp-opal-brain/ | 2026-06-10 00:34 | 2026-06-11 18:19 |
| 2026-05-26 | 010 code-scan PM 우선 무조건화 (v2 다이어트, semi-agentic) — 코드 작업 한정 디스패치 전 무조건화+scan.json 즉석 자동 생성+빈 결과 폴백 3분기+사용자 오버라이드+brain↔code-scan 역할 분담 4축(선별·신선도·깊이, analyze 의존 명문화)+PM Gate 14번. 규약 .md 7파일, install 2회 배포. 후속=Phase2 워커 강제·@header 커버리지 확충(메모리 기록). 커밋 완료(feat/opal-brain-wiki) | 완료 | tasks/010-260526-opp-code-scan-pm-mandate/ | 2026-05-26 15:24 | 2026-06-11 22:56 |
| 2026-06-02 | 011 모델 매핑 최신화 + 최신 추종 전략 — Gemini standard/advanced 부동 별칭(`-latest`) + light 핀(`gemini-3.1-flash-lite`) + Codex gpt-5.4-mini/gpt-5.5/gpt-5.3-codex + OpenAI 참조전용 + windows.ps1 4번째 동기지점 신규발견 (agentic) | 완료 | tasks/011-260602-opp-model-mapping-latest-tracking/ | 2026-06-02 19:57 | 2026-06-02 20:18 |
| 2026-06-07 | 012 OPAL 헌법(PRINCIPLES.md) 신설 — 카파시 스킬 철학 SSOT + always-on 등록(AGENT.md Eager 2.5) + 테스트 하네스 §4 집행(목업 금지·동작 증거: test-agent adversarial화·qa-standards·test-scenario-guide) + coding-principles 다이어트 + install 배포 (agentic) | CLOSE | tasks/012-260607-opp-opal-principles-constitution/ | 2026-06-07 17:44 | 2026-06-07 17:44 |
| 2026-06-07 | 013 state-tool 동작 증거 강제 게이트 — 헌법 §4 deterministic 집행: verify 서브커맨드(mock 코드패턴 검출 + 증거 누락 검출) + cmd_mark TEST stage 자동 훅 + ERROR_CODES 2종 + TestVerify 13케이스(136 passed). 캡틴 사례(목업 API) 기계적 차단 (agentic) | CLOSE | tasks/013-260607-opds-state-tool-enforcement/ | 2026-06-07 | 2026-06-07 |
| 2026-06-07 | 014 파이프라인 간소화 — 전 Phase 완료: stage-transition guard(P1)+opds 19→10(P2)+QA→PM Gate 통합(P3)+전 pilot STATE 재구성·gate-pass deprecate(P4, opd 28→15/opsdd 35→24)+L2 경량트랙 공식화(P5). 158 passed, 동작검증 불변. 후속=install 배포 (semi-agentic) | 완료 | tasks/014-260607-opp-pipeline-simplification/ | 2026-06-07 | 2026-06-08 07:31 |
| 2026-06-08 | 015 보고형식 Eager 슬림화 — reporting-template.md(318줄/9KB) 제거: §보고형식 헌법문체 AGENT.md 인라인(🎯결론·근거 통합+AskUserQuestion 도구+승인대기) + §8 단계전환양식 semi-agentic §10 이전 + 참조 3곳 재지정 + 부트스트랩 ✅reporting 칼럼 제거. Eager 약 -285줄. 후속=install 배포 (agentic) | 완료 | tasks/015-260608-opp-reporting-eager-slim/ | 2026-06-08 16:26 | 2026-06-08 17:07 |
| 2026-06-10 | 016 TDD RED-first 트랙 도입 — 독립 RED 작성(opal-test-agent `mode:red`, 작성자≠구현자) + 영속 테스트코드 산출물 + state-tool `verify --red-check`(RED 증거 게이트)·`--fix-mode`(테스트 불변성) ERROR_CODES 2종 + 하이브리드 자동분기 정책(red-first.md SSOT) + 모듈 미러링·@header·탐지 4단계. 자기적용 RED 6 FAIL→GREEN 165 OK. 워커 끊김 2회로 Step3 PM직접. 후속=install 배포 + 017(다중Step done 가드) (agentic) | 완료 | tasks/016-260609-opds-tdd-red-first-track/ | 2026-06-09 18:15 | 2026-06-10 14:11 |
| 2026-06-10 | 017 state-tool 다중 Step 조기 done 가드 — `mark --step N/M`에서 N<M+`--done`이면 in_progress 유지(조기 done 차단)+진행률 영속화, N==M에서만 done. ②단계전환·③CLOSE는 기존 stage-transition guard가 in_progress 행 미완 판정으로 자동 차단(신규 코드 0, ERROR_CODE 30 보존). 016 RED-first 자기적용: RED 5 FAIL→GREEN 172 OK. 후속=install 016+017 일괄 (semi-agentic) | 완료 | tasks/017-260610-opds-state-tool-multistep-done-guard/ | 2026-06-10 14:15 | 2026-06-10 15:02 |
