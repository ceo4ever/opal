# opal Memory Index

> 최종 갱신: 2026-06-11 (feat/opal-brain-wiki ↔ main 병합 — 양 PC 작업 합류)
> last_task_number: 22
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
| 2026-06-15 | 021 OPAL Console 로컬 프로젝트 통합 관리 대시보드 1차 뷰어 (opd, semi-agentic) — dashboard/ 신규: FastAPI BE(스캐너+read-only어댑터5+파서4+라우터5, pytest76)+React/shadcn FE 5화면(대시보드/프로젝트/태스크칸반/메모리/환경) + opal-cli console + install_dashboard(+windows.ps1). 핵심: 데몬=도구오케스트레이터·SSOT=프로젝트파일, .opal/AGENT.md 마커스캔(scan_roots 3루트), 절대경로 식별자=query param, 5화면 contextProject 전역구독, 시그니처3색 :root토큰, 공통 MarkdownView(@header아코디언+TOC), 칸반 아카이브(tasks/backup)+산출물 단계추론, 문서/산출물/메모리 오른쪽Sheet 통일. 정식배포 실측(install_dashboard)·cmux 5화면 검증. brain 4(entity1+concept3). 캡틴 실테스트가 build-only 놓친 결함 다수 발견→cmux 실렌더 검증 도입(교훈). 후속=SSE·md→html프레임워크스킬·미적용토글. 커밋안함 | 완료 | tasks/021-260615-opd-opal-console/ | 2026-06-15 10:21 | 2026-06-15 18:13 |
| 2026-06-14 | 020 opi 아키텍처 문서 생성 깊이 강화 (WHERE→HOW, agentic) — 신규1 code-analysis-guide.md(공통 심층분석 4블록: 탐색패턴·BE/FE체크리스트·1:1재대조·멀티레포/서비스판별+자체docs흡수) + 수정2 docs-guide.md(ARCHITECTURE HOW 5종+"구현 주입 가능 수준" 기준)·SKILL.md v4.0→4.2(초기화 심층화·최신화 StepC/D 가이드추출로 비대칭해소·멀티레포/멀티서비스 docs/services분기·자체docs흡수·대형 워커디스패치 임계 영역≥2/모듈≥10). living ref=pointail/backend docs/architecture L3. 게이트3 Pass·brain 2 concept. 정적검증 완료 / 동작검증(install재배포+opi재실행)=후속. 커밋 안 함 | 완료 | tasks/020-260614-opp-opi-architecture-depth/ | 2026-06-14 00:01 | 2026-06-14 15:26 |
| 2026-06-12 | 019 opal-pilot-data-design DB 설계 OPAL 내재화 (opds→opd 전환, agentic) — 신규4: 오케스트레이터 opal-pilot-data-design(opdd, TASK→DICT→MODEL→DDL/MIGRATION→QA, STATE 15행)+단계스킬 op-data-dictionary(사전·코드 CRUD, md SSOT+xlsx 단방향, db-type-mapping 4 DBMS)/op-data-model(concept·logical·physical 3모드)/op-data-ddl(DBML→DDL+마이그레이션). 수정4: opal-db-agent 사전관리 확장·레지스트리 op-data 그룹·erd-modeler deprecate(//erm 하위호환)·PROJECT.md. DICT 선행(사전=속성SSOT)·DDL 물리후·경로 opwt패턴({설계}/200.설계/). TEST S-1~7 ALL PASS. brain 8페이지. 게이트 7 Pass. 후속=install 재배포 실연동검증 | 완료 | tasks/019-260612-opd-opal-pilot-data-design/ | 2026-06-12 15:53 | 2026-06-12 17:09 |
| 2026-06-12 | 018 README 최신화 (신규 베이스라인 반영, agentic) — A신규6(브레인 //opbr·GC //opgc·Codex·헌법·L2 경량트랙·RED-first)+독립스킬2(html-mockup·html-sa) / B정정4(부트스트랩 principles 선두·opsdd 정본 통일·Codex·에이전트 전문7+범용4+GC2=13). README 단일파일 +108/−7. ppt-builder 보류(미커밋). brain ingest concept 3. 후속=opsdd SSOT 3곳(레지스트리·PROJECT.md·SKILL.md) 정합. 커밋 안 함 | 완료 | tasks/018-260612-opp-readme-feature-sync/ | 2026-06-12 11:00 | 2026-06-12 12:28 |
| 2026-06-11 | 016-brain wiki 지능화 (opal-wiki-pilot 완성, agentic — ⚠️중복 채번) — brain-tool 타입 동적화+analyze/ingest-scan(83 tests)+SKILL 4모드 지능화(v1.2 source_ref MUST)+W4/W5 PM 규칙+7 pilot CLOSE 훅(rows 불변)+install 배포+brain 54페이지(dogfooding+백필+synthesis+CLOSE ingest 실증). M-4 opal-brain 유지·M-5 brain git 추적. 커밋 6b29bb2 | 완료 | tasks/016-260611-opp-wiki-intelligence/ | 2026-06-11 18:21 | 2026-06-11 21:50 |
| 2026-06-10 | 015-brain OPAL Project Brain 코어 (⚠️중복 채번) — llm-wiki 융합 지식 위키: brain-tool(Python 8커맨드 66test)+opal-brain 스킬(4모드)+PM융합+opp CLOSE 자동 ingest 파일럿+brain 시드. origin=SSOT/wiki=요약+참조 단방향 (agentic) | CLOSE | tasks/015-260610-opp-opal-brain/ | 2026-06-10 00:34 | 2026-06-11 18:19 |
| 2026-05-26 | 010 code-scan PM 우선 무조건화 (v2 다이어트, semi-agentic) — 코드 작업 한정 디스패치 전 무조건화+scan.json 즉석 자동 생성+빈 결과 폴백 3분기+사용자 오버라이드+brain↔code-scan 역할 분담 4축(선별·신선도·깊이, analyze 의존 명문화)+PM Gate 14번. 규약 .md 7파일, install 2회 배포. 후속=Phase2 워커 강제·@header 커버리지 확충(메모리 기록). 커밋 완료(feat/opal-brain-wiki) | 완료 | tasks/010-260526-opp-code-scan-pm-mandate/ | 2026-05-26 15:24 | 2026-06-11 22:56 |
| 2026-06-02 | 011 모델 매핑 최신화 + 최신 추종 전략 — Gemini standard/advanced 부동 별칭(`-latest`) + light 핀(`gemini-3.1-flash-lite`) + Codex gpt-5.4-mini/gpt-5.5/gpt-5.3-codex + OpenAI 참조전용 + windows.ps1 4번째 동기지점 신규발견 (agentic) | 완료 | tasks/011-260602-opp-model-mapping-latest-tracking/ | 2026-06-02 19:57 | 2026-06-02 20:18 |
| 2026-06-07 | 012 OPAL 헌법(PRINCIPLES.md) 신설 — 카파시 스킬 철학 SSOT + always-on 등록(AGENT.md Eager 2.5) + 테스트 하네스 §4 집행(목업 금지·동작 증거: test-agent adversarial화·qa-standards·test-scenario-guide) + coding-principles 다이어트 + install 배포 (agentic) | CLOSE | tasks/012-260607-opp-opal-principles-constitution/ | 2026-06-07 17:44 | 2026-06-07 17:44 |
| 2026-06-07 | 013 state-tool 동작 증거 강제 게이트 — 헌법 §4 deterministic 집행: verify 서브커맨드(mock 코드패턴 검출 + 증거 누락 검출) + cmd_mark TEST stage 자동 훅 + ERROR_CODES 2종 + TestVerify 13케이스(136 passed). 캡틴 사례(목업 API) 기계적 차단 (agentic) | CLOSE | tasks/013-260607-opds-state-tool-enforcement/ | 2026-06-07 | 2026-06-07 |