# opal Memory Index

> 최종 갱신: 2026-06-11 (feat/opal-brain-wiki ↔ main 병합 — 양 PC 작업 합류)
> last_task_number: 29
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
| 2026-06-18 | 029 스킬레지스트리 정합+분류정리+opal-brain 오기재교정+validate (opd, semi-agentic) — 수정4(레지스트리 JSON·PROJECT.md·ARCHITECTURE.md·skill-registry.js)+신규1(test-validate.js). F-001 드리프트해소(dangling op-sdd-tasks·opal-orchestrator 제거[git a940318·45d2118]+op-sdd-action-plan 등록)·F-002 그룹재배치(op-spec-validator→op-sdd, op-brain-ingest→신규op-brain, opal-pilot-project-dev→opal-pilot)·F-003 opal-brain 오기재교정·F-004 validate확장(warning→error격상+validateUnregistered 소스환경전용 opal/skills+skills 양쪽스캔). **핵심교훈: opal-brain≠pilot** — PLAN게이트서 캡틴 "pilot은 단계파이프라인+워커지휘인데 brain도?" 지적→실SKILL검증(독립4모드라우터+brain-tool직접호출,워커디스패치·STATE없음)→리네임(opal-pilot-brain+opbr→opb)+9파일cascade 전면철회→PROJECT.md "Pilot"오기재교정 1곳으로 축소(9Step/4Phase→6Step/2Phase). 스킬분류=opal-pilot(오케스트레이터)/op-*(단계스킬)/opal-*(operator직접실행:onboarding/start/init/creator류/opal-brain). validate가 작동중 잠복드리프트 system-architecture-html(paths ~/.opal경로 누락) 추가검출→도구효용실증. RED-first(TC2·TC3 RED→GREEN, TC1~5 PASS). validate exit0·불변회귀(opal-brain폴더·brain_tool.py 0건). brain ingest concept3. 후속=install재배포·validate를 opgc/CI훅연결. 커밋 안 함 | 완료 | tasks/029-260618-opd-스킬레지스트리-정합-분류정리/ | 2026-06-18 10:54 | 2026-06-18 14:43 |
| 2026-06-17 | 028 Codex 워커 디스패치 어댑터 정합 (opp, agentic) — Codex tool-backed 세션(=OPAL 스킬의 모델 자율 워커 호출 경로)은 커스텀 에이전트 이름호출 불가(#15250 OPEN, generic spawn_agent만 노출)→공식 우회=인라인 주입(PM이 ~/.opal/agents/<name>/AGENT.md 본문을 spawn_agent message에 주입+model 매핑, **배포 아닌 디스패치 런타임 PM 행위**) 규칙화. 수정5: agents.md(메커니즘표 Codex행+변환표 Codex컬럼+§Codex tool-backed 인라인주입 신설, v1.7)·dispatch-process.md(Step0 포인터, v1.5)·opal-model-mapping.md(install 정합기록+인라인주입 매핑참조, v1.5)·install-mac.sh(install_codex_config=config [agents] 멱등작성+stale 모델매핑 2개소 정정, v3.2)·windows.ps1(Install-CodexConfig 미러+ModelMap정정, v1.13.0). 핵심: 헌법 플랫폼독립→core/AGENT.md 불변(분기는 어댑터에만)·.toml 유지(스펙정합·TUI 호명용)·config [agents]=글로벌 한계치(개별등록 아님, max_threads6/max_depth1/runtime1800). 부수성과=install 3개소 일몰예정 gpt-5.3-codex(6/30) stale→SSOT v1.4 정정. PM 강화검토 직접검증(멱등성 3회 실테스트→[agents]1·mcp보존, core/AGENT.md diff빈결과, 4지점 매핑동일). /agent=실행스레드 watch피커(정의목록 아님)→캡틴 미표시 정상. brain concept2([[codex-platform-integration]] 후속). 후속=인라인주입 런타임 실증·model핀 검증·max_depth·v2플래그. 커밋함 | 완료 | tasks/028-260617-opp-코덱스-디스패치-어댑터/ | 2026-06-17 15:37 | 2026-06-17 16:34 |
| 2026-06-16 | 025 brain-tool search 공백 무시 매칭 (opds, agentic) — 한국어 복합명사 띄어쓰기 편차로 검색 갈리는 문제 해결. brain_tool.py: `_norm`(="".join(str(s).lower().split())) 헬퍼 신설 + `_score_page` 4필드(title·rel·tags가중치·body) 정규화 매칭(`--tag` 필터는 정확일치 유지=H-6 회귀차단) + `_make_snippet` orig_index 역매핑(원문 노출) + `cmd_search` query_norm 전환(query=query 원문 출력 유지=계약 불변). 핵심: 검색 시점 휘발성 사본 정규화 → 저장 문서 불변·마이그레이션 없음, 부분문자열 포함 방향(비대칭: 짧은쿼리 넓게/긴쿼리 좁게) 보존. RED-first(S-3/S-4 2 FAILED→GREEN, 89 passed 회귀0). 배포본 실데이터 시연 "파이프라인"="파이프 라인"="파 이 프 라 인" 29건 동일. 비채택=정규식옵션·토큰화·stopword·OR·인덱싱·임베딩(과설계/정밀도위험, 별도 스파이크). install 재배포 diff무차이. brain concept1(80p). 커밋 안 함 | 완료 | tasks/025-260616-opds-brain-search-space-insensitive/ | 2026-06-16 17:58 | 2026-06-16 18:18 |
| 2026-06-16 | 005 명확화 게이트 — TASK 4요소 잠금 기계 집행 (opds, semi-agentic, 005 재스코핑·재개) — 수정4: state_tool.py(`verify --clarification-check`+헬퍼3종+`_run_clarification_hook` cmd_advance/mark 자동훅+ERROR_CODES `clarification_gate_unmet`)+test(`TestClarificationGate` 12)+op-task SKILL("명확화 결과" 4요소 템플릿)+opal-harness §1("명확화 게이트" 절, PRINCIPLES §1 참조·재서술X). 핵심: PRINCIPLES §1을 prose→tool 집행 전환. TASK 4요소 미잠금 시 다음단계 진입 도구 거부. 옵션1=TASK 한점 게이트(캡틴), 정책A=graceful skip(섹션 있는 TASK만 발동→기존 회귀0·신규 템플릿이 섹션 생성→100% 집행). 원안 흡수분 제거(소크라테스→AskUserQuestion·reporting-template 삭제됨), opp→opds 재라우팅(코드+테스트). RED-first(10 RED→184 passed). 배포본 실호출3종 PASS/FAIL/skip 검증. brain concept2+entity1. 후속=ANALYSIS/PLAN 델타게이트(보류). 커밋 안 함 | 완료 | tasks/005-260616-opds-clarification-gate/ | 2026-06-16 17:38 | 2026-06-16 18:11 |
| 2026-06-16 | 023 OPAL Console 칸반 현재 단계 표시 + 파이프라인 스테퍼 모호성 개선 (opd, semi-agentic) — 수정4: routers/tasks.py(`_derive_current_stage` 도달단계 기준·`_aggregate_status` na/skipped 제외·`_group_pipeline_stages` 신규)+models.py(`PipelineStageGroup` 신규, pipeline 타입 전환, PipelineRow 보존)+TasksPage.tsx(카드 단계 뱃지 승격·스테퍼 stage 그룹 렌더 단계당1+n/m·타입동기)+test_routers.py(신규16). 핵심: 단계파생 BE 단일소스·미시작(pending) 단계는 current_stage 미표시(진행중↔CLOSE 모순 해소)·na/skipped="해당없음" 집계제외. RED-first(12+4 RED→GREEN, 49 passed). fix루프1회=TEST 실데이터(152) 검증서 미시작CLOSE표기+na미고려 결함 발견·교정(021 교훈 재현: 실렌더가 build-only 보완). 정식배포(install[5]) 재기동·L3 캡틴확인 PASS. brain concept3. 커밋 안 함 | 완료 | tasks/023-260616-opd-kanban-stage-pipeline-ux/ | 2026-06-16 13:21 | 2026-06-16 17:14 |
| 2026-06-15 | 021 OPAL Console 로컬 프로젝트 통합 관리 대시보드 1차 뷰어 (opd, semi-agentic) — dashboard/ 신규: FastAPI BE(스캐너+read-only어댑터5+파서4+라우터5, pytest76)+React/shadcn FE 5화면(대시보드/프로젝트/태스크칸반/메모리/환경) + opal-cli console + install_dashboard(+windows.ps1). 핵심: 데몬=도구오케스트레이터·SSOT=프로젝트파일, .opal/AGENT.md 마커스캔(scan_roots 3루트), 절대경로 식별자=query param, 5화면 contextProject 전역구독, 시그니처3색 :root토큰, 공통 MarkdownView(@header아코디언+TOC), 칸반 아카이브(tasks/backup)+산출물 단계추론, 문서/산출물/메모리 오른쪽Sheet 통일. 정식배포 실측(install_dashboard)·cmux 5화면 검증. brain 4(entity1+concept3). 캡틴 실테스트가 build-only 놓친 결함 다수 발견→cmux 실렌더 검증 도입(교훈). 후속=SSE·md→html프레임워크스킬·미적용토글. 커밋안함 | 완료 | tasks/021-260615-opd-opal-console/ | 2026-06-15 10:21 | 2026-06-15 18:13 |
| 2026-06-14 | 020 opi 아키텍처 문서 생성 깊이 강화 (WHERE→HOW, agentic) — 신규1 code-analysis-guide.md(공통 심층분석 4블록: 탐색패턴·BE/FE체크리스트·1:1재대조·멀티레포/서비스판별+자체docs흡수) + 수정2 docs-guide.md(ARCHITECTURE HOW 5종+"구현 주입 가능 수준" 기준)·SKILL.md v4.0→4.2(초기화 심층화·최신화 StepC/D 가이드추출로 비대칭해소·멀티레포/멀티서비스 docs/services분기·자체docs흡수·대형 워커디스패치 임계 영역≥2/모듈≥10). living ref=pointail/backend docs/architecture L3. 게이트3 Pass·brain 2 concept. 정적검증 완료 / 동작검증(install재배포+opi재실행)=후속. 커밋 안 함 | 완료 | tasks/020-260614-opp-opi-architecture-depth/ | 2026-06-14 00:01 | 2026-06-14 15:26 |
| 2026-06-12 | 019 opal-pilot-data-design DB 설계 OPAL 내재화 (opds→opd 전환, agentic) — 신규4: 오케스트레이터 opal-pilot-data-design(opdd, TASK→DICT→MODEL→DDL/MIGRATION→QA, STATE 15행)+단계스킬 op-data-dictionary(사전·코드 CRUD, md SSOT+xlsx 단방향, db-type-mapping 4 DBMS)/op-data-model(concept·logical·physical 3모드)/op-data-ddl(DBML→DDL+마이그레이션). 수정4: opal-db-agent 사전관리 확장·레지스트리 op-data 그룹·erd-modeler deprecate(//erm 하위호환)·PROJECT.md. DICT 선행(사전=속성SSOT)·DDL 물리후·경로 opwt패턴({설계}/200.설계/). TEST S-1~7 ALL PASS. brain 8페이지. 게이트 7 Pass. 후속=install 재배포 실연동검증 | 완료 | tasks/019-260612-opd-opal-pilot-data-design/ | 2026-06-12 15:53 | 2026-06-12 17:09 |
| 2026-06-12 | 018 README 최신화 (신규 베이스라인 반영, agentic) — A신규6(브레인 //opbr·GC //opgc·Codex·헌법·L2 경량트랙·RED-first)+독립스킬2(html-mockup·html-sa) / B정정4(부트스트랩 principles 선두·opsdd 정본 통일·Codex·에이전트 전문7+범용4+GC2=13). README 단일파일 +108/−7. ppt-builder 보류(미커밋). brain ingest concept 3. 후속=opsdd SSOT 3곳(레지스트리·PROJECT.md·SKILL.md) 정합. 커밋 안 함 | 완료 | tasks/018-260612-opp-readme-feature-sync/ | 2026-06-12 11:00 | 2026-06-12 12:28 |
| 2026-06-11 | 016-brain wiki 지능화 (opal-wiki-pilot 완성, agentic — ⚠️중복 채번) — brain-tool 타입 동적화+analyze/ingest-scan(83 tests)+SKILL 4모드 지능화(v1.2 source_ref MUST)+W4/W5 PM 규칙+7 pilot CLOSE 훅(rows 불변)+install 배포+brain 54페이지(dogfooding+백필+synthesis+CLOSE ingest 실증). M-4 opal-brain 유지·M-5 brain git 추적. 커밋 6b29bb2 | 완료 | tasks/016-260611-opp-wiki-intelligence/ | 2026-06-11 18:21 | 2026-06-11 21:50 |
