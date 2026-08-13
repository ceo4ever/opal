# DONE: 프로젝트 메모리 SSOT를 MEMORY.md → MEMORY.json으로 전환

> 완료일시: 2026-07-29 17:32 (KST) | 시작일시: 2026-07-28 14:11 (KST)
> 적용 스킬: opd (Full Task) | 모드: agentic (TASK 단계에서 semi-agentic → agentic 전환)
> 태스크 번호: 078

## 1. 작업 결과 요약

프로젝트 메모리 인덱스·히스토리의 SSOT를 `.opal/MEMORY.md`(HTML 주석 마커 + 마크다운 표)에서 `.opal/MEMORY.json`(문서 스키마 검증 JSON)으로 전환하고, PM 부트스트랩 브리핑을 전체 Read에서 `memory-tool show --brief` 필터 조회로 교체했다.

**1순위 정당화는 도구 정확성**(마커·표 파싱 취약 계층 소멸)이며, 토큰 절약은 ① 조회 경로 전환 ② 규범 문서 슬림화 두 지분에서 나온다.

> **[MUST] 절약 귀속의 정직한 기록** (`TASK.md` §배경 분석 (2)): 행 단위로는 JSON이 md보다 무겁다(키 반복으로 행당 약 45 B 손해). 이 태스크의 절약은 JSON 포맷 자체의 효과가 아니다.

| 절약 원천 | 실측 |
|-----------|------|
| 브리핑 필터 조회 (`show --brief` vs `show`) | **1,422 B vs 2,781 B = −49%** |
| MEMORY 본체 스캐폴딩 제거 (`MEMORY.md` → `MEMORY.json`) | 3,518 B → 2,938 B = **−16.5%** |
| 규범 문서 슬림화 (`memory-learning.md`) | 105줄 → **81줄** |

> 태스크 착수 시 캡틴께 보고한 추정치(−46% / −17%)가 실측 −49% / −16.5%로 확인되었다.

## 2. 요구사항 달성 (R-1 ~ R-10)

| R-ID | 요구사항 | 결과 | 근거 |
|------|---------|------|------|
| R-1 | 문서 스키마 신설(런타임 검증) | ✅ | `$defs.memoryRow`/`historyRow` + `x-constants`/`x-advisory`, type 7종·status 5종이 코드 상수와 **집합 동일**. TS-001~005·037 |
| R-2 | 8서브명령 JSON I/O 전환 | ✅ | 마커·표 심볼 grep 0건, `marker_missing`·`import_failed` 카탈로그 제거, `show` 응답 키 보존. TS-006~009·038 |
| R-3 | `show --brief` 필터 | ✅ | dead/superseded/promoted/candidate 0건, 출력 −49% 실측. TS-010~012·039 |
| R-4 | PM 브리핑 경로 전환 | ✅ | "MEMORY.md를 Read" 0건 + `show --brief` 지시, Lazy 트리거 4개 사본 동일 문구. TS-022·042 |
| R-5 | lazy 마이그레이션 + `.bak` + 구 `migrate` 삭제 | ✅ | 행 회계 불변식으로 무성 유실 차단, `.bak` 선점 시 타임스탬프 suffix, `cmd_migrate` grep 0건. TS-013~018·040 |
| R-6 | `memory-learning.md` 슬림화 | ✅ | "마커"·`<!-- memory:` 0건, 라이프사이클 4행·라우팅 5행 보존, 105→81줄. TS-023 |
| R-7 | improve-tool 위임 전환 | ✅ | json/md(lazy)/부재 3케이스 검증. TS-024~026 |
| R-8 | dashboard 소비자 전환 | ✅ | 응답 모델 additive-only, 값 1:1 일치, mtime 불변, FE 변경 0건. TS-027~029·043 |
| R-9 | opi 템플릿 전환 | ✅ | 마커·인라인 md 템플릿·구 6컬럼 스니펫 0건. TS-030·031 |
| R-10 | 구형 잔존 0 + 신형 채택 | ✅ | grep 재정의 기준 0건 + 실세션 왕복·배포본 스모크. TS-032~036·044 |
| D-1 | 채번 tool-gated (PM 선결정) | ✅ | `task-number` 신설, 20프로세스 동시 bump 중복 0. TS-019~021·041 |

## 3. 변경 파일 (약 40개)

### 코드 (6)
| 파일 | 핵심 변경 |
|------|----------|
| `opal/tools/memory-tool/memory_tool.py` | JSON I/O 전환 · 스키마 런타임 검증 · `memory_lock`(O_EXCL+stale 60s) · `atomic_write_json`(tmp→`os.replace`) · `_migrate_md_to_json`(V-1~V-9 + 행 회계 불변식) · `task-number` 신설 · `show --brief`/`--history` · 마커·표·`cmd_migrate` 계층 전면 삭제 |
| `opal/tools/improve-tool/improve_tool.py` | `_resolve_memory_target`로 존재 판정 3곳 통합, md만 있어도 json 경로 위임(lazy 유도) |
| `dashboard/backend/parsers/memory_parser.py` | `json.load` 기반 교체 — **pre-045 5컬럼 가정으로 깨져 있던 오프바이원 해소** |
| `dashboard/backend/routers/memory.py` | 대상 경로 `MEMORY.json`, `@header.depends` 정합 |
| `dashboard/backend/routers/doctor.py` | 점검 대상 `MEMORY.json` + `MEMORY.md` 잔존 warn |
| `dashboard/backend/models.py` | `title`/`result` **additive만** 추가 (FE 무파손) |

### 테스트·스키마·픽스처 (7)
- `opal/tools/memory-tool/schema/memory.schema.json` — 행 스키마 → **문서 스키마** 전면 재설계
- `opal/tools/memory-tool/tests/test_memory_tool.py` — RED 61건 신규 + 구 T045 24건 폐기/재작성 + 약 30건 어서션 치환 → **132건 GREEN**
- `tests/fixtures/` — json 2종·md 변형 3종 신규 / 구 md 3종 삭제 / `fixture_legacy.md` 용도 전환
- `opal/tools/improve-tool/tests/test_improve_tool.py`, `dashboard/backend/tests/test_parsers.py`

### 문서·스킬 (27)
`opal-pm.md`(§15·§17) · `core/AGENT.md` · `GEMINI.md`×2 · `gemini-hardening.md` · `memory-learning.md` · `tools.md`(memory-tool 절 + improve-tool 절) · `task-process.md` · `observability.md` · `pm-improvement-loop.md` · `pm/context-injection.md` · `op-task` · `opal-pilot-gc` · `opal-project-init` · `opal-pilot-project-dev`(+guide 4종) · `opal-pilot-project-loop` · `opal-improve` · `memory-tool/README.md` · `brain-tool/templates/schema-template.md` · `html-mockup` · `system-architecture-html` · `docs/PROJECT.md` · `docs/ARCHITECTURE.md`

## 4. 검증 결과

| 항목 | 결과 |
|------|------|
| TEST-SCENARIO | **46 Pass / 0 Fail** (TS-046은 캡틴 확인) |
| memory-tool 회귀 | **132 tests OK** |
| improve-tool 회귀 | 17 OK |
| dashboard 회귀 | **249 passed**, 1 skipped |
| 컨벤션 자동 진단 | **Critical 0 / High 0** (Medium 2 중 GC-C001 즉시 수정) |
| RED-first | 강제 트랙 — RED 증거 exit 1(149건 중 68 fail) 확보 후 GREEN 진입, `state-tool verify --red-check` pass |
| 목표-커버 게이트 | coverage-check exit 0(R10/F12/H13/S47) + 평가자 rubric pass(goal 2·adoption 2·boundary 2, gaps 0) — **1회차 수렴** |

### P0 리스크 실증

| 가설 | 결과 |
|------|------|
| **H-1 무성 유실** | `invest-stock` 복사본 변환에서 **히스토리 3행이 3행으로 보존**(구 로직은 조용히 0행). `unmapped_statuses` 3건(`확정`×2·`승인대기`×1) 표면화. 프로파일 강제 무력화 시 `migration_failed` + md mtime 불변 + json 미생성 |
| **H-2 경쟁조건** | 2프로세스 동시 append → json 1개·양쪽 행 보존·`.bak` 1개·락 잔여 0 |
| **H-3 enum 불일치** | 스키마에 누락됐던 `improvement`/`candidate` 반영 → 스키마 파생 상수로 **구조적 재발 차단** |
| **H-7 채번 원자성** | 20프로세스 동시 `--bump` 중복 0, 최종값 = 초기+20 |

### 마이그레이션 실증 (캡틴 (b)안)

| 대상 | 결과 |
|------|------|
| `ai-framework` | **실 변환** — memories 3/3 · history 5/5 · `last_task_number` 78 보존 · `.bak` md5 원본 동일 |
| `invest-stock` | 읽기 전용 복사본 검증. **원본 mtime·md5 불변** (`Jun 24 18:43:24`) |
| `aos` | 동일. **원본 불변** (`Jul 16 20:42:26`). 빈 인덱스가 `memories:[]`+`empty_source_regions`로 정상 처리 |

> 두 프로젝트 실 변환은 **다음 진입 시 lazy 자동 변환**에 위임한다(캡틴 결정 2026-07-28).

## 5. 태스크 중 발견·교정한 기존 결함

이 태스크가 만든 문제가 아니라, 전환 과정에서 드러난 **선행 결함**이다.

| # | 결함 | 조치 |
|---|------|------|
| 1 | `dashboard/backend/parsers/memory_parser.py`가 태스크 045(2026-06-26) 이후 줄곧 pre-045 5컬럼을 가정 — 헤더 행 유입·오프바이원(`date="제목"`, `file="active"`)으로 **몇 주간 잘못된 값을 화면에 표시** | JSON 기준 정답 기대값으로 재작성 |
| 2 | `last_task_number`가 **어떤 도구로도 게이트되지 않는 유일한 비게이트 쓰기 경로** — LLM이 헤더를 직접 Read+Edit | `task-number` 서브명령 tool-gated 전환 + 채번 문서 3곳 개정 |
| 3 | 스키마 enum이 코드 상수보다 좁음(`improvement`/`candidate` 누락) | 스키마 파생 상수로 단일 출처화 |
| 4 | "프로젝트 메모리 동기화" 절 3곳 + brain 템플릿에 **pre-045 관행 잔존** — "단계 컬럼 직접 갱신", "FIFO **10개**"(실제 5) | 도구 호출·FIFO 5로 정정, "기존 결함 교정"으로 변경이력 명시 |
| 5 | `opal-pm.md` §15 타입 우선순위에 **실존하지 않는 enum** `user`/`reference` | 실 enum 기준 정정 |
| 6 | CLI `--help`가 실제 동작과 반대(`init`이 "마커·표 삽입", `--file`이 "MEMORY.md 경로") | 9곳 정정 + 재배포 |
| 7 | `routers/memory.py` `@header.depends`에 미사용 `parsers.memory_file_parser` | 제거 (GC-C001) |

## 6. 비범위 (명시 고정)

| 대상 | 제외 근거 |
|------|----------|
| `STATE.md` / `state.json` | 이미 JSON SSOT. 실측 `state.json` 3,377 B > `STATE.md` 1,730 B — **JSON은 토큰 절약 포맷이 아니다** |
| `.opal/brain/index.md` | 27,243 B, JSON 변환 시 증가. 애초 전체 로드하지 않는 구조(search 후보→선택 주입) |
| `backlog.json` / `code-scan.json` | 이미 JSON |

## 7. 잔여 미해결 · 후속 후보

| # | 항목 | 성격 |
|---|------|------|
| 1 | `~/.claude_platform_mkt/settings.json`에 `todo_mirror` PostToolUse hook 미등록 — 이 세션에서 파이프라인 todo가 표시되지 않은 원인. 훅 동작은 파이프 테스트로 검증됨(exit 0, 비대상 무출력) | **캡틴 수동 조치** (설정 파일 편집이 권한 차단됨) |
| 2 | 076이 설계한 "hook 강제"가 `CLAUDE_CONFIG_DIR` 비표준 시 배포 누락 — install이 `~/.claude`만 대상 | **FW 개선 후보** |
| 3 | GC-C002 — 테스트 `@header`의 `changelog` 키가 `header-standard.md` 미정의(2파일, 빈도 임계 N=3 미달) | 비차단 후속 |
| 4 | `invest-stock`·`aos` 실 변환 | 다음 진입 시 lazy 자동 |
| 5 | 서브에이전트 Write 가드가 파이프라인 계약 산출물(`ANALYSIS.md` 등) 생성을 거부 | **FW 개선 후보** |

## 8. 특이사항 (agentic 운영)

- **워커 인프라 실패 3연속**(API 연결 종료 ×2, 600초 스톨 ×1). 산출물 유실 없음을 매회 `git diff`로 확인. 대응: **모델 하향(opus→sonnet) + 전체 파일 통독 금지 + 함수 단위 저장 + 배치 4분할** → 이후 전량 성공
- **동시 태스크 077**이 같은 워킹트리에서 EXECUTE 진행 — `tools.md` 공유. `Write` 금지·`Edit` 전용 규율로 상호 변경 보존(충돌 0건), code-scan 절 무변경 확인(TS-047)
- **검증 2원화 유지**: RED 작성(`opal-test-agent`) ≠ 구현(`opal-be-agent`), 시나리오 작성(PM) ≠ 채점(`opal-evaluator-agent`), 테스트 이관도 구현자와 분리(PLAN 배정에서 의도적 이탈, 근거 기록)
- **PM Gate에서 워커 보고 오류 2건 적발**: Step 14 "에러코드 표 일치" 보고가 실제 13/23이었던 건, TS-034 검사 패턴 오탐. 둘 다 실측 대조로 발견·교정
- 판단 이력 33건: `AGENTIC-LOG.md`

## 9. 산출물

| 파일 | 내용 |
|------|------|
| `TASK.md` | 요구사항 R-1~R-10 · 확정 방향 8 · 비범위 4 · 명확화 4요소 |
| `ANALYSIS.md` | 현행 실태 · A-1~A-6 판단 · R-T1~R-T8 리스크 (316줄) |
| `PLAN.md` | F-001~F-012 · 22 Step / 6 Phase · H-1~H-13 (1,665줄) |
| `TEST-SCENARIO.md` | 47 시나리오 (L1 26 / L2 12+ / L3 1) · 결과 기재 완료 |
| `SCENARIO-GATE-1.md` | 목표-커버 루브릭 채점 (1회차 수렴) |
| `GC-CONVENTION-20260728.md` | 컨벤션 진단 (Critical 0 / High 0) |
| `AGENTIC-LOG.md` | PM 대행 일지 33건 |
| `STATE.md` / `state.json` | 파이프라인 현황판 |
