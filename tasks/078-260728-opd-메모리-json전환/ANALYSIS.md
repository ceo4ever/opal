# ANALYSIS: 프로젝트 메모리 SSOT를 MEMORY.md → MEMORY.json으로 전환

> 작성일: 2026-07-28
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 메모리 형식·라이프사이클 SSOT | `opal/core/references/harness/memory-learning.md` | R-6 슬림화 대상, 마커·라이프사이클·이관 워크플로우 규범 원천 |
| D-2 | 설계 | PM 행동 프로세스 | `opal/core/references/opal-pm.md` §15, §17 | R-4 브리핑 절차·§17 프로젝트 컨텍스트 변경 대상 |
| D-3 | 소스 | memory-tool 본체 | `opal/tools/memory-tool/memory_tool.py` | R-1~R-5 주 변경 대상, 전체 1273줄 정독 |
| D-4 | 소스 | memory-tool 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 88개 테스트 전수 분류(md종속/동작계약) |
| D-5 | 소스 | memory-tool 스키마 | `opal/tools/memory-tool/schema/memory.schema.json` | R-1 현행 스키마 실태(문서용, 런타임 미사용) |
| D-6 | 소스 | memory-tool README | `opal/tools/memory-tool/README.md` | 서브명령 계약 현황 |
| D-7 | 소스 | improve-tool 위임 로직 | `opal/tools/improve-tool/improve_tool.py` | R-7 존재 판정 3곳(L213/L291/L337) |
| D-8 | 소스 | improve-tool 테스트 | `opal/tools/improve-tool/tests/test_improve_tool.py` | R-7 회귀 대상 |
| D-9 | 소스 | dashboard 메모리 파서·라우터·doctor | `dashboard/backend/parsers/memory_parser.py`, `dashboard/backend/routers/memory.py`, `dashboard/backend/routers/doctor.py` | R-8 소비자 전환, 응답 스키마 확인 |
| D-10 | 소스 | dashboard 파서 테스트 | `dashboard/backend/tests/test_parsers.py` | R-8 회귀 대상 |
| D-11 | 설계 | 도구 인벤토리·사용법 | `opal/core/references/tools.md` §memory-tool (L542-639) | R-3 옵션 문서화 + 077 충돌 지점 실측 |
| D-12 | 설계 | 태스크 채번 규칙 | `opal/core/references/harness/task-process.md` | A-2 `last_task_number` 거처 판단 원천 |
| D-13 | 설계 | Observability(스킬 탐색·메모리 동기화) | `opal/core/references/harness/observability.md` | R-10 — pre-045 잔존 직접편집 서술 발견 |
| D-14 | 설계 | Lazy 트리거 테이블 | `opal/core/AGENT.md` L48-63 | R-4 Lazy 트리거 행(L60) 변경 대상 |
| D-15 | 설계 | 프로젝트 초기화 스킬 | `opal/skills/opal-project-init/SKILL.md` | R-9 인라인 템플릿(L427-448) + 최신화 조회 절차(L681-682, L950-956) |
| D-16 | 기획 | 프로젝트 정의·문서 레지스트리 | `docs/PROJECT.md` | R-10 문서 등록 정합 |
| D-17 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` | 2-Layer·배포 경계 확인 |
| D-18 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | @header/배포 경계/State 관리 규칙 |
| D-19 | 소스 | 태스크 077 산출물 | `tasks/077-260727-opd-코드맵-헤더작성층/PLAN.md`, `STATE.md` | A-5 파일 충돌 실측 |
| D-20 | 소스 | ai-framework 실 MEMORY.md | `.opal/MEMORY.md` | A-1 포맷 실측 1(신포맷+구주석 잔재) |
| D-21 | 소스 | invest-stock 실 MEMORY.md | `/Volumes/Data/AIStudio/workspace/invest-stock/.opal/MEMORY.md` | A-1 포맷 실측 2(완전 구포맷, 마커 없음) |
| D-22 | 소스 | aos 실 MEMORY.md | `/Volumes/Data/AIStudio/workspace/aos/.opal/MEMORY.md` | A-1 포맷 실측 3(신포맷, 빈 인덱스) |
| D-23 | 소스 | state-tool 본체 | `opal/tools/state-tool/state_tool.py` | ok/err/ERROR_CODES 패턴 원조, JSON SSOT+md 렌더 선례 대조 |
| D-24 | 인용규칙 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 본 산출물 인용 포맷·의무 수준 준수 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/memory-tool/memory_tool.py` | 9서브명령(init/append/update/promote/prune/migrate/show/review/delete) 결정론 CLI, md 마커·표 파싱 전담 | 필수 — R-1,R-2,R-3,R-5 | `memory_tool.py:1-1273` 전체 |
| `opal/tools/memory-tool/tests/test_memory_tool.py` | 88개 유닛테스트(23클래스) | 필수 — 다수 재작성 | `test_memory_tool.py:1-1952` |
| `opal/tools/memory-tool/README.md` | 서브명령 사용법 문서 | 필수 | `README.md:1-195` |
| `opal/tools/memory-tool/schema/memory.schema.json` | 행 단위 JSON Schema(문서용) | 필수 — 전면 재설계 | 스키마 전체(§1.1 하단 상세) |
| `opal/tools/memory-tool/tests/fixtures/fixture_legacy.md` | 구포맷 md 픽스처(6행) | 삭제 또는 lazy-migrate 픽스처로 대체 | `fixture_legacy.md:1-27` |
| `opal/tools/memory-tool/tests/fixtures/fixture_valid.md`, `fixture_populated.md`, `fixture_no_marker.md` | 신포맷/무마커 md 픽스처 | 전량 `.json` 픽스처로 교체 | 각 파일 전체 |
| `opal/tools/improve-tool/improve_tool.py` | `.opal/MEMORY.md` 존재 판정 3곳(record/list/show) → memory-tool 위임 | 필수 — R-7 | `improve_tool.py:213,291,337` |
| `opal/tools/improve-tool/tests/test_improve_tool.py` | proj-A(유효 마커 MEMORY.md)/proj-B(부재) fixture 기반 회귀 | 필수 | `test_improve_tool.py:117-122,162-163` |
| `dashboard/backend/parsers/memory_parser.py` | MEMORY.md md 표 파싱 — 구포맷(5컬럼, 등록일시/카테고리/상태/파일/설명) 전용, 제목 컬럼 없음 | 필수 — R-8, 현재도 이미 stale | `memory_parser.py:82-152` |
| `dashboard/backend/routers/memory.py` | `GET /api/memory` — md 파일 직접 read | 필수 — R-8 | `memory.py:40-78` |
| `dashboard/backend/routers/doctor.py` | doctor 점검 항목에 `.opal/MEMORY.md` 파일 존재 체크 | 필수 — R-8 | `doctor.py:63` |
| `dashboard/backend/tests/test_parsers.py` | `parse_memory_index` 회귀(구조/필드/mtime불변) | 필수 | `test_parsers.py:24-87` |
| `opal/core/references/harness/memory-learning.md` | 마커 규약·라이프사이클·이관 워크플로우 SSOT | 필수 — R-6 슬림화 | `memory-learning.md:40-49`(마커 규약, 삭제 대상) |
| `opal/core/references/opal-pm.md` | §15 브리핑 절차("MEMORY.md를 Read"), §17 프로젝트 컨텍스트 | 필수 — R-4 | `opal-pm.md:284,336` |
| `opal/core/AGENT.md` | Lazy 트리거 테이블 — `.opal/MEMORY.md` 행 | 필수 — R-4 | `AGENT.md:60` |
| `opal/core/references/tools.md` | memory-tool 서브명령·에러코드 표 | 필수 — R-3,R-5,R-10 | `tools.md:542-639,603-607` |
| `opal/core/references/harness/task-process.md` | 태스크 채번 — `last_task_number` 헤더 필드 직접 Read+Edit(도구 미경유) | 필수 — A-2 | `task-process.md:19-22` |
| `opal/core/references/harness/observability.md` | "프로젝트 메모리 동기화" 절 — pre-045 직접 표 편집 서술 잔존(FIFO=10 오기재) | 필수 — R-10 | `observability.md:23-29` |
| `opal/core/references/harness/pm-improvement-loop.md` | local scope 기록 = memory-tool 위임 서술 | 경미 수정 | `pm-improvement-loop.md:85` |
| `opal/core/references/pm/context-injection.md` | "이전 태스크 결과 참조" 표에 `.opal/MEMORY.md` 언급 | 경미 수정 | `context-injection.md:25` |
| `opal/skills/opal-project-init/SKILL.md` | MEMORY.md 인라인 템플릿(md 마커 그대로) + 최신화 모드 직접 Read 절차 | 필수 — R-9 | `SKILL.md:394,427-448,681-682,950-956` |
| `opal/skills/opal-project-init/templates/common/platform/GEMINI.md`, `opal/bootstrapper/gemini-hardening.md`, 루트 `GEMINI.md` | Gemini Lazy 트리거 표 — `.opal/MEMORY.md` 행(AGENT.md L60과 동형 3중 사본) | 필수 — R-4·R-10 | 각 파일 동일 라인(`... PM 컨텍스트 로드 이후 |`) |
| `opal/skills/op-task/SKILL.md`, `opal/skills/opal-pilot-gc/SKILL.md` | 채번 시 `last_task_number` 직접 참조 | A-2 결정에 종속 | `op-task/SKILL.md:174`, `opal-pilot-gc/SKILL.md:79` |
| `opal/skills/opal-improve/SKILL.md` | local scope 위임 서술 | 경미 수정 | `opal-improve/SKILL.md:99` |
| `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/skills/opal-pilot-project-loop/SKILL.md` | "프로젝트 메모리 동기화" 절 — observability.md와 동일 계열 pre-045 직접편집 서술 | 필수 — R-10 | `opal-pilot-project-dev/SKILL.md:716-721`, `opal-pilot-project-loop/SKILL.md:578-` |
| `opal/skills/opal-pilot-project-dev/references/{prd,roadmap,trd,wbs}-guide.md` | 체크리스트 항목 "MEMORY.md 작업 히스토리를 갱신했는가" | 경미 수정(문구 일반화) | 각 파일 1줄 |
| `opal/tools/brain-tool/templates/schema-template.md` | 메모리 계층 설명에 "FIFO 10항목" 오기재 | 경미 수정(기존 drift, 이번 기회 정정) | `schema-template.md:58` |
| `docs/proposals/opal-brain-design.md` | brain 설계안 — MEMORY.md 역할 서술 3곳, "FIFO 10" 오기재 포함 | 선택(설계 히스토리 문서, 갱신 여부 PM 판단) | `opal-brain-design.md:18,58,356` |
| `docs/PROJECT.md`, `docs/ARCHITECTURE.md` | 프로젝트 문서 테이블에 `.opal/MEMORY.md` 등재 | 필수 — R-10 | `PROJECT.md` 문서 표, `ARCHITECTURE.md` Project Layer 표 |
| `skills/html-mockup/SKILL.md`, `skills/system-architecture-html/SKILL.md` | 세션 컨텍스트 폴백 파일명으로 "MEMORY.md" 언급(TASK.md 목록에 없던 신규 발견) | 경미 수정 | 각 2줄 |

### 1.2 아키텍처 패턴

- **결정론 CLI 3종 공유 패턴** — `ok()`/`err()`/`ERROR_CODES` 딕셔너리는 state-tool이 원조이고 memory-tool이 그대로 재사용한다(`memory_tool.py:96-114` vs `state_tool.py:144-151,80-`). 단일라인 JSON, `code`→메시지 템플릿 치환 방식이 동일 — JSON 전환 후에도 그대로 유지 가능(이 패턴은 md/JSON 여부와 무관한 CLI 계약층이다).
- **마커-표 파싱 계층** — `replace_marker_section`(`memory_tool.py:145-155`) → `_parse_index_rows`/`_parse_history_rows`(`208-243`) → `_render_index_table`/`_render_history_table`(`246-270`) 호출 그래프가 `cmd_init`/`cmd_append`/`cmd_update`/`cmd_promote`/`cmd_prune`/`cmd_migrate`/`cmd_show`/`cmd_delete` 8개 커맨드 전부에서 재사용된다. `build_review_block`(`328-414`)도 동일 파서에 의존한다. JSON 전환 시 이 계층 전체(약 250줄)가 `json.load`/`json.dump` + 스키마 검증으로 대체되며, 커맨드 함수 본문의 "행 리스트 조작" 로직(딕셔너리 append/필터/제거) 자체는 자료구조가 이미 dict 리스트이므로 재사용 가능하다.
- **state-tool과의 정합/이탈 지점** — state-tool은 JSON SSOT(`state.json`) + md 렌더뷰(`STATE.md`, 마커 있음, 사람은 md만 읽고 도구가 단방향 렌더)** 모델이다(`state_tool.py:197-222,263-` render_pipeline_table 등). TASK.md 확정 방향 §1은 memory-tool에 대해 md 렌더본을 만들지 않는 단독 SSOT를 명시적으로 선택했다 — state-tool 선례와 의도적으로 다른 모델이며, 사람 열람은 `show`/dashboard가 대신한다. 이 이탈은 이미 TASK.md에서 결정되었으므로 재점화 대상이 아니나, PLAN 단계에서 "왜 state-tool과 다른가"를 1줄 근거로 남겨두는 편이 향후 재질문을 막는다.
- **서브프로세스 위임 패턴** — improve-tool은 memory-tool을 `run.sh` 서브프로세스로 호출한다(`improve_tool.py:59,135-141`). 이 패턴은 파일 포맷과 무관하게 유지되며, JSON 전환의 영향은 위임 인자(`--file <path>`)가 가리키는 파일 확장자만 바뀌는 수준이다.
- **읽기전용 어댑터 패턴** — dashboard는 OPAL 도구를 호출하지 않고 직접 md 파일을 파싱한다(`memory_parser.py`, `memory.py:47-48`). 이는 다른 dashboard 어댑터(state-tool/code-scan/skill-registry는 CLI 위임)와 다른 예외 경로이며, 이미 오래전에 memory-tool 신포맷과 어긋나 있었다(§1.4·§4 참조).

### 1.3 의존성 맵

```
[LLM/PM 직접 접촉 — 도구 미경유]
  opal-pm.md §15,§17 --Read--> .opal/MEMORY.md (브리핑, 전체)
  core/AGENT.md L60 Lazy트리거 --Read--> .opal/MEMORY.md
  task-process.md §채번 --Read+Edit(직접)--> .opal/MEMORY.md의 last_task_number 헤더 필드
  op-task/SKILL.md:174, opal-pilot-gc/SKILL.md:79 --참조--> 위 채번 절차

[도구 경유]
  improve-tool (record/list/show --scope local)
    -> subprocess run.sh (improve_tool.py:135-141)
        -> memory-tool (append --type improvement --status candidate | show)
            -> .opal/MEMORY.md (마커 파싱·재작성)

  opal-project-init(opi) Phase 2-4
    -> .opal/MEMORY.md 인라인 템플릿 직접 생성(SKILL.md:427-448) — memory-tool init 미사용
    -> 최신화 모드에서 .opal/MEMORY.md Read(직접, SKILL.md:681-682)
    -> 4-2 히스토리 기록 시 구 6컬럼(#/작업/단계/경로/시작일시/완료일시) 표 스니펫 직접 삽입(SKILL.md:579-586) — memory-tool append 미사용, 6컬럼 자체가 현행 5컬럼 히스토리 스키마와도 불일치(기존 drift)

[dashboard — 독립 파서, 도구 미경유]
  routers/memory.py:get_memory()
    -> _parse_memory_for_project() (memory.py:40-78)
        -> open(.opal/MEMORY.md) 직접 read
            -> parsers/memory_parser.py:parse_memory_index()
                -> _extract_section_lines("메모리")/_extract_section_lines("히스토리")
                -> 구포맷 5컬럼(등록일시/카테고리/상태/파일/설명) 가정 — 현행 memory-tool 6컬럼과 불일치
  routers/doctor.py:_build_project_section()
    -> Path(".opal/MEMORY.md").exists() 파일존재 체크만(파싱 없음)
```

**순환 의존 없음** — improve-tool → memory-tool 단방향, dashboard → (memory-tool 미경유) 독립 파서 단방향. 다만 improve-tool이 memory-tool을 서브프로세스로 호출하는 구조에서 memory-tool 내부에 lazy 마이그레이션 훅을 심으면, improve-tool의 `record`/`list`/`show` 호출 각각이 memory-tool 프로세스를 매번 새로 띄우므로 호출마다 독립적으로 마이그레이션 감지 로직이 실행된다(§5 A-4 참조. "중첩 재귀 호출"은 발생하지 않으나 "반복 감지 오버헤드"는 발생).

### 1.4 테스트 현황

**memory-tool (`test_memory_tool.py`, 1952줄, 23클래스, 88개 `test_` 메서드)** — `TestSkeleton`(7)·`TestMarkerGuard`(3)·`TestSummaryLengthCap`(2)·`TestCountUnlimited`(1)·`TestHistoryFIFO`(2)·`TestPruneIdempotent`(2)·`TestPromoteToDocs`(3)·`TestPromoteLossless`(4)·`TestPromoteToBrain`(2)·`TestUpdateStatusTransition`(4)·`TestInit`(3)·`TestInitAlreadyInitialized`(2)·`TestMigrate`(6)·`TestMigrateLossless`(2)·`TestReviewAmbient`(6)·`TestReviewRoleBoundary`(5)·`TestSecurity`(4)·`TestIntegrationTemplate`(4)·`TestErrorCodes`(3)·`TestDelete`(10)·`TestUpdateNewTitle`(5)·`TestSkeletonV2`(4)·`TestBacktickFileFieldDeletion`(4) (`test_memory_tool.py:90-1949`).

md 포맷 자체(마커/표/legacy 변환)에 구조적으로 종속되어 폐기 또는 전면 재작성이 불가피한 클래스:

| 클래스 | 건수 | 사유 | 근거 |
|--------|------|------|------|
| `TestMarkerGuard` | 3 | `marker_missing` 자체가 R-2(c)에서 제거 대상 에러코드 | `test_memory_tool.py:168-226` |
| `TestInit` | 3 | 마커 4개 삽입·표 헤더 삽입을 직접 검증 | `test_memory_tool.py:712-765` |
| `TestInitAlreadyInitialized` | 2 | 마커 존재 여부로 "이미 초기화" 판정(JSON은 파일 존재 자체로 대체 가능하나 검증 메커니즘 전면 교체) | `test_memory_tool.py:771-795` |
| `TestMigrate` | 6 | `cmd_migrate`(구md→신md) 자체가 R-5(d)로 삭제 | `test_memory_tool.py:801-907` |
| `TestMigrateLossless` | 2 | 위와 동일 | `test_memory_tool.py:913-941` |
| `TestIntegrationTemplate` | 4 | `TEMPLATE_CONTENT`가 마커 포함 md 리터럴 | `test_memory_tool.py:1192-1263` |
| `TestBacktickFileFieldDeletion` | 4 | migrate가 생성한 백틱 file 필드 버그 재현 — migrate 삭제 시 전제 자체 소멸 | `test_memory_tool.py:1684-1949` |
| **소계** | **24건** | | |

나머지 64건은 "동작 계약"(마커 가드 이외의 비즈니스 규칙 — 요약길이캡·FIFO=5·promote 무손실·update 상태전이·review ambient·보안·delete 무손실가드 등)을 검증하므로 의도는 재사용 가능하다. 단, 이 중 다수(`TestPromoteToDocs`/`TestPromoteLossless`/`TestUpdateStatusTransition`/`TestDelete`/`TestUpdateNewTitle` 등 약 30건)가 `content = md.read_text(...)` 후 `self.assertIn("제목문자열", content)` 형태로 원문 텍스트 포함 여부를 직접 검사한다(예: `test_memory_tool.py:448-449,652-656,1337-1338`). JSON 전환 후에는 이 어서션들을 `json.load(...)`로 읽은 뒤 필드 단위로 비교하는 방식으로 기계적 치환이 필요하다 — "로직 재사용"과 "어서션 전면 재작성 불요"는 다른 명제이며, R-2 AC(b) "기존 테스트 항목이 JSON 기준으로 전량 통과"는 이 치환 작업량을 포함해야 함을 뜻한다.

`tests/fixtures/fixture_legacy.md`(27줄, `_parse_legacy_index`/`_parse_legacy_history` 대응 6행 픽스처)는 `cmd_migrate` 삭제 시 직접 소비자가 사라진다. 다만 R-5(lazy 자동 마이그레이션)가 유사한 변환 로직을 필요로 하므로, 이 픽스처의 데이터(6행, 상태값 다양성)는 lazy 마이그레이션 테스트용으로 재활용 가능하다(파일 자체보다 데이터 구성이 재사용 가치가 있음).

**improve-tool (`test_improve_tool.py`, 392줄, 14개 `test_` 메서드)** — `_VALID_MEMORY_MD`(md 마커 포함 리터럴, `test_improve_tool.py:117-122`) 픽스처와 `_memory_md_text()` 헬퍼(`162-163`)가 md 파일을 직접 read한다. R-7 전환 시 이 헬퍼와 픽스처를 JSON 대응물로 교체해야 하며, 검증 대상 필드(`type=improvement, status=candidate`)는 그대로 유지된다.

**dashboard (`test_parsers.py`, 213줄, 12개 `test_` 메서드)** — `test_memory_parser_returns_structure`/`test_memory_parser_rows_have_fields`/`test_memory_parser_history_have_fields`/`test_memory_parser_mtime_invariant`(`test_parsers.py:25-87`) 4건이 `parse_memory_index`를 직접 검증한다. 주의: 이 테스트들은 실제 프로젝트 루트의 `.opal/MEMORY.md`(`MEMORY_MD = AI_FRAMEWORK_ROOT / ".opal" / "MEMORY.md"`, `test_parsers.py:19`)를 읽어 도는데, 현재 이 파일은 신포맷(6컬럼)이고 파서는 구포맷(5컬럼)을 가정하므로 오늘 시점에도 이미 빈 배열 또는 필드 오정렬 결과를 반환할 가능성이 높다(§4 핵심발견 참조 — 실행 검증은 QA 단계 권고).

---

## 2. 외부 조사 결과

해당 없음 — memory_tool.py는 "표준 라이브러리만" 사용하는 제약(`memory_tool.py:6` @header, `docs/CONVENTIONS.md` 도구 우선 원칙)이 있고, `json`/`argparse`/`pathlib`/`re` 등 Python 표준 모듈만으로 JSON 스키마 검증(직접 구현, `jsonschema` 등 외부 패키지 없이)까지 수행해야 한다. context7/WebSearch 조사 불필요.

### 2.1 라이브러리/API 조사

- 표준 라이브러리 `json.JSONDecodeError`로 파싱 실패를 감지할 수 있으나, JSON Schema의 `enum`/`maxLength`/`pattern` 검증은 표준 라이브러리에 없다 — memory_tool.py가 이미 `VALID_TYPES`/`VALID_STATUSES`/summary 길이 등을 자체 파이썬 코드로 검증하고 있으므로(`memory_tool.py:507-519` 등), R-1의 "스키마를 실제 검증에 사용"은 `jsonschema` 패키지 도입이 아니라 기존 자체 검증 로직을 스키마 정의와 동기화하는 방식(스키마를 SSOT 상수로 참조하거나, 스키마 파일을 파이썬이 직접 로드해 `enum`/`maxLength`/`pattern`을 자체 루프로 대조)으로 처리해야 제약 위반이 없다.

### 2.2 버전 호환성

해당 없음.

---

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/memory-tool/memory_tool.py` — 9서브명령 I/O 계층 전면 교체(R-1,R-2,R-3,R-5)
- `opal/tools/memory-tool/tests/test_memory_tool.py` — 88건 중 24건 폐기/재작성, 64건 어서션 치환
- `opal/tools/memory-tool/tests/fixtures/*` — 4개 md 픽스처 → json 픽스처 전환 + legacy 픽스처 거취 결정
- `opal/tools/memory-tool/README.md`, `schema/memory.schema.json` — 문서·스키마 재작성
- `opal/tools/improve-tool/improve_tool.py:213,291,337` — 존재판정 대상 파일 경로 교체
- `dashboard/backend/parsers/memory_parser.py`, `routers/memory.py`, `routers/doctor.py:63` — 파서 전면 교체(현재도 구포맷 가정이라 "전환"이 아니라 "동시 수정"에 가까움)
- `opal/skills/opal-project-init/SKILL.md:394,427-448` — 인라인 템플릿 제거, `memory-tool init` 호출로 대체

### 3.2 간접 영향

- **PM 부트스트랩 경로 3중 사본**(`opal/core/AGENT.md:60`, 루트 `GEMINI.md:67`, `opal/skills/opal-project-init/templates/common/platform/GEMINI.md:67`, `opal/bootstrapper/gemini-hardening.md:71`) — 동일 Lazy 트리거 행이 플랫폼별로 중복 기재되어 있어 R-4 적용 시 4곳 동시 수정 필요
- **improve-tool 테스트**(`test_improve_tool.py`) — 위임 대상 파일 확장자 변경에 따른 픽스처·헬퍼 교체
- **dashboard 테스트**(`test_parsers.py`) — 4건 직접 영향, project brain/설정 라우터 등 타 라우터는 무관(격리 확인)
- **3개 실 프로젝트**(ai-framework/invest-stock/aos) `.opal/MEMORY.md` — lazy 마이그레이션 최초 발동 대상, §A-1 참조
- **참조 문서 38개 파일**(§1.1 표 + 아래 §4) — `MEMORY.md` 문자열 전수 검색 결과 TASK.md 추정치(약 30개)보다 많은 38개 파일(tasks/ 이력·`.opal/brain/` 지식페이지·`docs/backup/` 백업 제외)이 실제로 `MEMORY.md`를 언급
- **077 산출물과 동일 파일**(`tools.md`) — 줄 구간은 분리되어 있으나 동일 파일 동시 편집이므로 병합 시점 조율 필요(§A-5)

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음(파일 기반 SSOT)
- [x] API 인터페이스 변경 — `GET /api/memory` 응답 스키마 유지 여부가 R-8 AC의 핵심(§A-6에서 상세)
- [ ] 설정/환경변수 변경 — 없음
- [ ] 빌드/배포 파이프라인 변경 — 없음(install이 프로젝트 파일을 건드리지 않는 2-Layer 원칙 유지)

---

## 4. 핵심 발견 사항

1. **dashboard 파서가 이미 오래전부터 memory-tool 신포맷과 어긋나 있다.** `memory_parser.py:106-129`는 `등록일시/카테고리/상태/파일/설명`(5컬럼, 제목 없음) 구포맷을 가정하지만, memory-tool은 태스크 045(2026-06-26)부터 `제목/등록일/유형/상태/파일/요약`(6컬럼) 신포맷을 써왔다. 즉 R-8은 "md→json 전환"이 아니라 "이미 깨져 있던 파서를 JSON 기준으로 처음 제대로 맞추는 작업"에 가깝다 — PLAN에서 "회귀"가 아니라 "현행 동작 자체가 무엇을 반환하는지"부터 실측해야 한다.
2. **`last_task_number`는 현재 어떤 도구로도 게이트되지 않는다.** memory_tool.py의 9개 서브명령 전체를 뒤져도 `last_task_number`를 다루는 코드가 없다 — `task-process.md:19-22`가 지시하는 "헤더 필드 Read 후 즉시 갱신"은 오케스트레이터(LLM)가 `.opal/MEMORY.md`를 직접 Read+Edit하는 것이며, 마커 가드의 보호 범위 밖에 있다. JSON 전환 후 파일 전체가 스키마 검증 대상이 되면 이 직접 편집 관행이 "LLM 직접 편집 금지" 원칙과 더 뚜렷하게 충돌한다(§5 A-2에서 옵션 제시).
3. **schema/memory.schema.json은 "행 스키마"이지 "문서 스키마"가 아니다.** 현재 스키마는 인덱스 행 1개(`title/date/type/status/file/summary`)와 히스토리 행 1개만 정의하고, `version`/`last_task_number`/배열 컨테이너 자체는 스키마에 없다. 게다가 `type`/`status` enum이 `VALID_TYPES`/`VALID_STATUSES`(코드, `memory_tool.py:46-47` — `improvement`/`candidate` 포함)보다 좁다(스키마는 `improvement`/`candidate` 미포함) — 코드와 스키마가 이미 어긋나 있다. R-1은 스키마 확장과 문서-코드 동기화를 함께 요구한다.
4. **실 프로젝트 포맷 편차가 예상보다 크다.** invest-stock은 마커가 전혀 없고, 상태값이 자유 텍스트(`확정`/`승인대기` — 현 `LEGACY_STATUS_MAP`에 없는 키라 `cmd_migrate`가 무조건 `active`로 매핑), 히스토리 표 헤더가 `# | 작업 | 단계 | 경로 | 시작일시 | 완료일시`로 "등록일자"도 "등록일시"도 없어 현재 `_parse_legacy_history`(`등록일자`/`등록일시` 문자열 검색, `memory_tool.py:960-963`)가 이 표를 인식조차 못 한다 — 즉 오늘 이 프로젝트에서 `migrate`를 돌리면 히스토리 3행이 조용히 0행으로 유실된다. lazy 자동 마이그레이션은 이 실패 모드를 반드시 처리해야 한다(§A-1).
5. **"프로젝트 메모리 동기화" 절이 문서 3곳에 pre-045 서술로 잔존한다.** `observability.md:23-29`, `opal-pilot-project-dev/SKILL.md:716-721`, `opal-pilot-project-loop/SKILL.md:578-` 모두 "단계 완료 시 `단계` 컬럼을 직접 갱신", "FIFO 10개"(현 SSOT는 5, `memory_tool.py:32`)를 서술한다 — memory-tool(045) 도입 이전 관행이 그대로 남아 있으며, memory-tool의 "직접 편집 금지" 원칙과 충돌한다. R-10 정리 범위에 반드시 포함되어야 하며, 이 3곳은 이번 태스크 이전부터 이미 틀려 있던 것이므로 "전환으로 새로 생긴 문제"가 아니라 "전환 김에 바로잡을 기존 결함"으로 분류해야 한다.
6. **077과의 파일 충돌은 TASK.md 우려보다 좁지만, 타이밍 조율은 여전히 필요하다.** 077 PLAN.md는 `tools.md:202-289`(code-scan 절)만 건드리고 `opal-project-init/SKILL.md`는 전혀 건드리지 않는다(grep 0건) — 이 태스크의 대상은 `tools.md:542-639`(memory-tool 절)로 줄 구간이 완전히 분리되어 있어 의미적 충돌은 없다. 다만 077은 현재 STATE.md 기준 EXECUTE 진행 중(TASK.md 작성 시점의 "PLAN 대기" 가정은 이미 stale)이므로, 동일 파일에 대한 동시 편집 시점만 조율하면 된다(예: 077 EXECUTE 완료·커밋 후 착수, 또는 diff 병합 시 라인 오프셋 확인).

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-T1 | dashboard `memory_parser.py`가 구포맷 가정 — JSON 전환 전에도 이미 신포맷에 대해 오작동 가능성 | P1 | `memory_parser.py:119`(헤더 스킵 조건이 "등록일시" 등 구컬럼명 기준) |
| R-T2 | `last_task_number`가 도구 게이트 밖에서 LLM이 직접 편집 — JSON 스키마 전체 검증 도입 시 이 직접편집이 검증을 우회하는 유일한 쓰기 경로로 남을 위험 | P1 | `task-process.md:19-22` |
| R-T3 | invest-stock류 완전 구포맷(마커 없음, 상태 자유텍스트, 히스토리 헤더 변형)에서 lazy 자동 마이그레이션이 조용히 데이터 유실(히스토리 0행) | P0 | `/Volumes/Data/AIStudio/workspace/invest-stock/.opal/MEMORY.md:11-14` vs `memory_tool.py:960-963` |
| R-T4 | 스키마와 코드 enum 불일치(스키마에 `improvement`/`candidate` 없음)가 R-1 런타임 검증 도입 시 즉시 표면화 — improve-tool 위임이 스키마 위반으로 거부될 수 있음 | P1 | `memory.schema.json` enum 목록 vs `memory_tool.py:46-47` |
| R-T5 | 테스트 88건 중 24건 폐기/재작성 + 약 30건 어서션 치환 — PLAN 산정 시 "동작 재사용 가능"과 "테스트 코드 무변경"을 혼동하면 공수 과소추정 | P1 | §1.4 분류표 |
| R-T6 | 077과 `tools.md` 동일 파일 동시 편집(줄 구간은 분리) — 077이 EXECUTE 진행 중이라 병합 시점 조율 필요 | P2 | §4 발견 6, `tasks/077.../STATE.md` 행12 |
| R-T7 | 참조 문서 38개 중 다수가 "MEMORY.md" 단어를 일반 명사처럼 사용(`skills/html-mockup`, `system-architecture-html` 등 TASK.md 미기재분) — R-10 AC(a) "전 경로 grep 0건" 달성 시 이 신규 발견분 누락 위험 | P2 | §1.1 표 최하단 2행 |
| R-T8 | docs/backup, docs/proposals 등 "역사적 스냅샷" 성격 문서도 grep에 걸림 — R-10 범위 포함 여부가 불명확(TASK.md가 tasks/·brain/만 명시적 제외) | P2 | `docs/proposals/opal-brain-design.md:18,58,356` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python 3(표준 라이브러리 전용) | `memory_tool.py`, `improve_tool.py` — venv `~/.opal/.venv` |
| 백엔드 | FastAPI + uvicorn | `dashboard/backend` |
| 테스트 | `unittest`(Python 표준), `pytest`(dashboard) | `test_memory_tool.py`, `test_improve_tool.py`는 subprocess 기반 unittest, `test_parsers.py`는 pytest 스타일 함수 |
| 문서 | Markdown(OPAL 스킬/참조 SSOT) | — |
| 셸 래퍼 | Bash(`run.sh`) | `memory-tool/run.sh`, `improve-tool` 동일 패턴 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| opal-doc-standard(참조 문서 표준) | R-6 슬림화, R-10 다수 문서 변경 시 버전관리·변경이력 규칙 적용 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| 해당 없음 | 표준 라이브러리·내부 문서 작업만 — 외부 라이브러리 조사 불필요 |

---

## 7. TASK.md 필수 판단 대상 (A-1~A-6)

> 옵션·트레이드오프까지만 제시한다(확정은 PLAN 단계).

### A-1. 마이그레이션 변형 케이스 목록 (실측 기반)

3개 프로젝트 실물 대조 결과:

| 항목 | ai-framework | invest-stock | aos |
|------|:---:|:---:|:---:|
| 마커 존재 | O(`.opal/MEMORY.md:28,34,37,45`) | X(전혀 없음) | O(`MEMORY.md:7,10,13,17`, 빈 인덱스) |
| 인덱스 컬럼 수 | 6(신포맷) | 5(구포맷, 제목 없음) | 6(신포맷, 0행) |
| 상태값 | enum 정합(active 등) | 자유텍스트("확정"/"승인대기" — `LEGACY_STATUS_MAP` 부존재 키) | 해당 행 없음 |
| 히스토리 헤더 | `제목|등록일|단계|경로|핵심결과`(5컬럼) | `#|작업|단계|경로|시작일시|완료일시`(6컬럼, "등록일자/등록일시" 문자열 자체가 없음) | `제목|등록일|단계|경로|핵심결과`(5컬럼, 1행) |
| `last_task_number` 헤더 | O(`> last_task_number: 78`) | X(필드 자체 없음) | O(`> last_task_number: 1`) |
| 구 잔존 섹션 | O(L7-18에 구버전 3컬럼 카테고리 안내표가 죽은 텍스트로 남아있음) | 해당 없음(전체가 구포맷) | 없음 |
| 백틱 감싼 file 경로 | X(맨 경로 또는 백틱 혼재 — L31 백틱, L33 비백틱) | X | 해당 없음 |

lazy 변환기가 반드시 처리해야 할 변형(우선순위순):
1. **마커 완전 부재**(invest-stock류) — 현 `has_index_markers`가 False → lazy 훅이 "마커 없음"과 "JSON 없음"을 함께 보고 구포맷 변환 경로로 분기해야 함
2. **히스토리 헤더에 "등록일자"/"등록일시"가 없는 변형**(`#` 컬럼 등) — 현재 정규식 매칭 기준(`memory_tool.py:962`)으로는 탐지 실패 → 헤더 감지 로직을 컬럼 개수·상대 위치 기반으로 보강하거나, 감지 실패 시 "0행 변환"이 아니라 명시적 경고를 반환해야 함(무손실 원칙)
3. **자유텍스트 상태값**(LEGACY_STATUS_MAP 미포함 키) — 현재는 무조건 `active`로 폴백(`memory_tool.py:833-835`) → 최소한 `[REVIEW]` 플래그를 상태에도 남기거나 변환 로그에 "미매핑 상태값" 목록을 포함해야 검증 가능
4. **`last_task_number` 필드 부재**(invest-stock) — 변환기가 0 또는 기존 tasks/ 폴더 스캔 기반 추정값 중 무엇을 채울지 결정 필요(§A-2와 연동)
5. **빈 인덱스/히스토리**(aos) — 0행 변환은 정상 케이스이나 "변환 실패로 인한 0행"과 구분이 안 되면 §2 오판 위험 — 회귀 판정 로직에 "원본에 표 자체가 없었는가"를 별도 기록해야 함
6. **구버전 잔존 텍스트**(ai-framework L7-18 죽은 카테고리 안내표) — 마커 밖 자유 텍스트이므로 파싱 대상은 아니나, JSON 전환 후 이 설명 텍스트를 어디에 보존할지(삭제/README 이관) 결정 필요

### A-2. `last_task_number`의 거처

현재 상태: 마커 보호 밖 헤더 주석, 오케스트레이터가 직접 Read+Edit(`task-process.md:19-22`). memory-tool 어떤 서브명령도 이 필드를 다루지 않는다. 참조처 3곳(`task-process.md`, `op-task/SKILL.md:174`, `opal-pilot-gc/SKILL.md:79`).

옵션:

| 옵션 | 설명 | 트레이드오프 |
|------|------|-------------|
| (a) JSON 최상위 필드 유지 + 직접 편집 존속 | `{"version":..,"last_task_number":N,"memories":[...],"history":[...]}` 구조에서 `last_task_number`만 오케스트레이터가 여전히 직접 R/W | 구현 최소— 기존 절차 무변경. 단 "JSON SSOT는 도구로만 변경"이라는 이번 태스크의 정신(R-2 마커 가드 철학의 JSON 버전)과 불일치, state.json/backlog.json/test-scenario.json의 "3-SSOT tool-gated" 선례와도 어긋남 |
| (b) memory-tool 신규 서브명령(예: `bump-task-number`) 신설 | 채번 시 도구 호출로 원자적 증가 + 동시성 가드 | tool-gated 원칙과 정합, 동시 실행 인스턴스 간 경쟁조건도 도구가 책임질 수 있음. 단 서브명령 10번째 추가로 R-2 범위가 늘어나고 `task-process.md`/`op-task/SKILL.md`/`opal-pilot-gc/SKILL.md` 3곳의 채번 절차 문서도 함께 개정해야 함 |
| (c) state-tool류 별도 카운터 파일로 분리 | 메모리 SSOT와 분리된 `.opal/task-counter.json` 신설 | 메모리 스키마가 순수해짐. 단 "왜 카운터가 메모리 옆에 있었는데 갑자기 분리되는가"에 대한 마이그레이션 설명 부담 + 신규 파일 추가로 배포 경계 재검토 필요 |

세 옵션 모두 "채번 절차 문서(§task-process.md 등)가 함께 바뀌어야 하는가"의 답은 예이며, 차이는 얼마나 바뀌는가(옵션 a는 파일 확장자만, b/c는 절차 자체)이다.

### A-3. 마이그레이션 발동 지점

옵션:

| 옵션 | 설명 | 트레이드오프 |
|------|------|-------------|
| (a) 공통 진입 훅(모든 `cmd_*` 시작부에 삽입) | 각 커맨드 함수 진입 시 "json 없음+md 있음" 체크 후 변환 | R-5 AC "모든 서브명령이 감지" 요구를 직접 충족. 단 9개 커맨드 각각에 동일 가드 코드 반복(또는 데코레이터화 필요) |
| (b) 파일 로드 함수 1곳(`load_memory_json` 등 신설) 집중 | 모든 커맨드가 공통 로더를 거치도록 리팩터링 후 로더 안에서만 감지 | 코드 중복 없음, 단일 지점 테스트로 충분 — R-1,R-2 리팩터링과 자연스럽게 결합됨. 단 현재 각 `cmd_*`가 `pathlib.Path(args.file)`+`md_path.read_text()`를 직접 호출하는 구조(`memory_tool.py:425,481,588,661,763,1078,1112,1176`)를 먼저 공통 로더로 통합하는 선행 리팩터링이 필요 |

옵션 (b)가 R-2(전 서브명령 JSON I/O 전환)와 동시에 수행해야 하는 리팩터링과 자연스럽게 겹치므로 구현 비용이 더 낮다 — 다만 이는 PLAN에서 확정할 사항이며 본 단계는 옵션 제시까지만 한다.

### A-4. 순환 의존 리스크

improve-tool은 `record`/`list`/`show` 호출마다 매번 새 memory-tool 서브프로세스를 띄운다(`improve_tool.py:135-141` subprocess.run, 프로세스 상태 없음). 따라서:
- 진짜 재귀/중첩 호출은 발생하지 않는다 — improve-tool이 memory-tool을 부르고, memory-tool이 다시 improve-tool이나 자기 자신을 부르는 구조가 아님(단방향 서브프로세스 1홉).
- 리스크는 "중첩 재귀"가 아니라 "반복 감지 오버헤드 + 경쟁조건"이다: improve-tool이 짧은 시간에 `record`를 여러 번 호출하면(예: CLOSE 회고 하드스텝에서 여러 개선후보를 연속 기록), 매 호출이 lazy 마이그레이션 감지를 반복 수행한다. 감지 로직이 "json 파일 존재 여부"만 확인하는 가벼운 체크라면 문제가 없으나, 최초 1회의 실제 변환(md→json 쓰기) 도중에 두 번째 호출이 동시에 들어오면 쓰기 경쟁조건이 발생할 수 있다(현재 promote의 원자적 삭제 패턴처럼 "쓰기 확인 후 진행"이 필요).

### A-5. 077 충돌 지점 (실측)

077 PLAN.md(`tasks/077-260727-opd-코드맵-헤더작성층/PLAN.md:1007`)의 `tools.md` 변경 대상은 `tools.md:202-289`(code-scan 절)이며, 이번 태스크의 변경 대상은 `tools.md:542-639`(memory-tool 절)이다. `opal-project-init/SKILL.md`는 077 PLAN.md 전체에서 0건 언급된다(grep 확인). 즉 실제 겹치는 파일은 `tools.md` 1개이며, 줄 구간은 완전히 분리되어 있어 내용 충돌은 없다. 다만 077은 STATE.md(`tasks/077.../STATE.md:12`) 기준 EXECUTE 진행 중이므로, 두 태스크가 동시에 `tools.md`를 편집하면 diff 병합 시 줄번호 오프셋이 어긋날 수 있다 — PLAN에서 "077 EXECUTE 완료 후 착수" 또는 "편집 전 최신 `tools.md` 재확인" 중 하나를 순서로 명시할 필요가 있다.

### A-6. 회귀 위험

| 기존 동작 | 위험 | 검증 방법 |
|-----------|------|----------|
| PM 부트스트랩 브리핑(`opal-pm.md §15`) | Read 기반 브리핑 → `show --brief` 호출로 교체 시, 브리핑 문구 생성 로직(타입별 우선순위·날짜순 정렬)을 PM이 JSON 필드에서 동일하게 재현해야 함 | 브리핑 3~5개 예시를 신·구 양쪽에서 수동 대조(§15 "브리핑 형식" 예시 문구 기준) |
| opi 초기화(`opal-project-init/SKILL.md`) | 인라인 템플릿 제거 후 `memory-tool init` 호출 실패 시 신규 프로젝트가 `.opal/MEMORY.json` 없이 생성될 위험 | opi 신규 초기화 1회 실행 후 산출물 목록에 `.opal/MEMORY.json` 존재 + `.opal/MEMORY.md` 부재 확인(R-9 AC와 동일) |
| CLOSE 회고 하드스텝의 improve-tool record | `.opal/MEMORY.md` 존재 판정(`improve_tool.py:213,291,337`)이 `.json`으로 바뀌면서, 과도기(md만 있고 json 아직 없는 프로젝트)에서 lazy 마이그레이션이 먼저 발동해야 no-op이 아니라 정상 위임이 되는지 | `.opal/MEMORY.md`만 있는 임시 프로젝트에서 `improve-tool record --scope local` 실행 → lazy 마이그레이션 발동 + append 성공 여부 확인(R-7 AC와 동일 시나리오) |
| dashboard `GET /api/memory` | 파서 교체 후 응답 스키마(`MemoryIndexResponse`) 유지 여부 — 현재 필드(`date/category/status/file/description`)가 JSON 신필드(`title/date/type/status/file/summary`)와 다름 → 필드명 매핑 결정이 R-8 AC "기존과 동일한 응답 스키마"의 전제 조건 | FE(`dashboard/frontend`)가 실제로 `category`/`description` 필드를 참조하는지 grep으로 먼저 확인 후, 응답 모델을 유지할지 신필드로 교체할지 PLAN에서 결정 필요(본 ANALYSIS은 이 결정을 확정하지 않음 — 신규 발견 사항으로 표면화만 함) |
| 읽기전용(mtime 불변) 원칙 | `memory_parser.py`/`memory_file_parser.py`는 `open(read)`만 사용해 이미 보장됨(`memory_parser.py:6` @header) — JSON 전환 후에도 `json.load`만 사용하면 동일 원칙 유지 가능 | `test_memory_parser_mtime_invariant`(`test_parsers.py:74-87`) 패턴을 JSON 버전으로 재작성하여 대조 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-28 | 최초 작성 — memory-tool 9서브명령·88테스트 전수 분석, improve-tool 3곳 위임 확인, dashboard 파서 구포맷 drift 발견, 3개 실 프로젝트 포맷 편차 실측(A-1), last_task_number 비게이트 실태(A-2), 077 파일 충돌 실측(A-5) |
