# TASK: 프로젝트 메모리 SSOT를 MEMORY.md → MEMORY.json으로 전환

> 작성일: 2026-07-28 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

프로젝트 메모리 인덱스·히스토리의 SSOT를 `.opal/MEMORY.md`(마커+마크다운 표)에서 `.opal/MEMORY.json`(스키마 검증 JSON)으로 전환하고, PM 부트스트랩 브리핑을 전체 Read에서 `memory-tool` 필터 조회로 교체한다.

## 배경

현재 메모리 인덱스는 HTML 주석 마커로 구획된 마크다운 표이며, `memory-tool`이 이 표를 정규식으로 파싱·재작성한다. 두 가지 문제가 있다.

1. **파싱 취약성** — 마커 유실 시 모든 변경 명령이 `marker_missing`으로 거부되고, 표 셀의 `|`·백틱·개행 처리가 도구 내부에 흩어져 있다. 구포맷 변환기(`migrate`)와 legacy fixture까지 유지 부담으로 남아 있다.
2. **전체 Read 로드** — PM 부트스트랩이 `MEMORY.md` 전체를 컨텍스트에 올린다. 로드 대상이 아닌 `dead`/`superseded`/`promoted` 행과 설명 스캐폴딩까지 매 세션 토큰을 잠식한다.

`state`(state.json) · `backlog`(backlog.json) · `code-scan`(code-scan.json)은 이미 JSON SSOT로 전환되었고, `brain`은 `search` 후보→선택 주입으로 전체 로드를 끊었다. 메모리만 "md가 SSOT이면서 전체가 컨텍스트에 로드되는" 마지막 예외로 남아 있다.

## 배경 분석 (대화에서 도출)

### (1) 실측 — 파일 크기 비교

현 `.opal/MEMORY.md`(메모리 3행 + 히스토리 5행) 기준 실측:

| 방식 | 크기 | 대비 |
|------|------|------|
| `MEMORY.md` 전체 Read (현행) | 3,518 B | 기준 |
| `MEMORY.json` 전체 Read (pretty) | 2,915 B | −17% |
| `MEMORY.json` 전체 Read (compact) | 2,561 B | −27% |
| 필터 조회 (`active`만 + 히스토리 3) | 1,889 B | **−46%** |

### (2) 절약 원천의 정직한 귀속 [MUST 기록]

| 원천 | 크기 | JSON 전환이 필요한가 |
|------|------|---------------------|
| 브리핑 필터 조회 | −1,629 B / 세션 | ❌ 불필요 — 현행 md에서도 가능 |
| 규범 문서 슬림화 (마커 규약 소멸) | ~35줄 × Lazy 로드마다 | ✅ JSON 귀속 |
| MEMORY 본체 설명 스캐폴딩 제거 | −603 B | ✅ 부분 귀속 |

- **행 단위로는 JSON이 md보다 무겁다** — 키 이름이 행마다 반복되어 행당 약 45 B 손해. 행이 30~40개로 늘면 *전체 Read* 기준으로는 JSON이 md보다 커진다.
- 따라서 토큰 절약은 **조회 경로 전환**이 주 지분이며, JSON 자체의 토큰 기여는 **규범 문서 쪽**에 있다. 이 태스크는 두 가지를 함께 수행하므로 절약이 성립한다.
- JSON 전환의 1순위 정당화 근거는 **도구 정확성**(파싱 취약 계층 소멸)이다.

### (3) 기존 `cmd_show`는 이미 존재한다

`opal/tools/memory-tool/memory_tool.py` `cmd_show`는 이미 md를 파싱해 `index_rows`/`history_rows` 구조화 JSON을 반환한다. 빠진 것은 **필터**뿐이며, 현재는 `dead`/`superseded`까지 전량 반환한다.

### (4) 다른 md 자산 실측 — 확산 대상이 아님

| 자산 | 실측 | 판정 |
|------|------|------|
| `state.json` 3,377 B / `STATE.md` 1,730 B | JSON이 md의 약 2배 | 이미 JSON SSOT, md는 렌더뷰 — 전환 무의미 |
| `.opal/brain/index.md` 27,243 B (201줄) | JSON 변환 시 증가 | 전체 로드하지 않는 구조 — 전환 시 손해 |

> **JSON은 본질적으로 토큰 절약 포맷이 아니다.** 이 사실을 비범위 근거로 고정한다.

### (5) 영향 범위 — 약 30개 파일

| 영역 | 대상 |
|------|------|
| 도구 본체 | `memory_tool.py`(1,273줄), `tests/test_memory_tool.py`(1,952줄), `README.md`, `schema/memory.schema.json`, `tests/fixtures/fixture_legacy.md` |
| 연계 도구 | `improve_tool.py`(`.opal/MEMORY.md` 존재 판정 3곳 — L213/L291/L337), `tests/test_improve_tool.py` |
| 대시보드 | `dashboard/backend/parsers/memory_parser.py`, `routers/memory.py`, `routers/doctor.py`(L63), `tests/test_parsers.py` |
| 참조 문서 | `harness/memory-learning.md`, `opal-pm.md`(§15/§17), `core/AGENT.md`(Lazy 테이블/Step 5), `tools.md`, `harness/task-process.md`, `harness/pm-improvement-loop.md`, `harness/observability.md`, `pm/context-injection.md` |
| 스킬 | `opal-project-init/SKILL.md`(템플릿·최신화), `op-task/SKILL.md`, `opal-improve/SKILL.md`, `opal-pilot-gc/SKILL.md`, `opal-pilot-project-dev/SKILL.md`(+refs 4종), `opal-pilot-project-loop/SKILL.md` |
| 부트스트래퍼·문서 | `opal/bootstrapper/gemini-hardening.md`, `GEMINI.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md` |

### (6) 마이그레이션 대상 프로젝트

워크스페이스 실측 3개: `ai-framework`, `invest-stock`, `aos`.

### (7) 077과의 파일 충돌 가능성

태스크 077(코드맵 헤더작성층)이 `tools.md`를 공통으로 건드릴 수 있다. EXECUTE 순서 조정이 필요하다.

> **[갱신 2026-07-28 14:40 — ANALYSIS 실측으로 정정]** 작성 시점의 "077은 PLAN 사용자 확인 대기" 가정은 stale이다. 077은 **별도 세션에서 EXECUTE 진행 중**(`tasks/077-.../STATE.md` 행 12 🔄, 14:31 기준)이며 `.gitignore`·`opal/tools/code-scan/tests/`에 이미 변경을 냈다. 또한 겹치는 파일은 `tools.md` **1개뿐**이고(077은 `tools.md:202-289` code-scan 절, 본 태스크는 `tools.md:542-639` memory-tool 절 — 줄 구간 분리), `opal-project-init/SKILL.md`는 077이 전혀 건드리지 않는다(grep 0건). 근거: `ANALYSIS.md` §A-5.

## 확정된 설계 방향 (대화에서 합의)

| # | 확정 사항 | 근거 |
|---|----------|------|
| 1 | `MEMORY.json` **단독 SSOT** — md 렌더본을 만들지 않는다 | SSOT 이중화 금지. 045가 `promote`에서 해소한 이중화를 되살리지 않는다. 사람 열람은 `show`와 dashboard가 담당 |
| 2 | 개별 `memory/*.md` 본문 파일은 **유지** — 인덱스만 JSON | 긴 산문 본문은 md가 적합 |
| 3 | `show --brief` 필터 신설 + **브리핑 경로 전환** | 토큰 절약의 실제 지분(−46%) |
| 4 | 마이그레이션은 **첫 접촉 시 lazy 자동** + `.opal/MEMORY.md.bak` 보존 | 프로젝트별 진입 시점을 예측할 수 없어 수동 1회성은 누락 리스크. 실 발동점은 PM 부트스트랩 브리핑 |
| 5 | install 일괄 변환은 **배제** | install은 글로벌 자산(`~/.opal/`) 배포 담당. 프로젝트 파일 수정은 2-Layer 모델 위반 |
| 6 | 구 `migrate`(구md→신md)는 **삭제**, md→json 변환으로 대체 | 구포맷 md 잔존 없음 |
| 7 | `memory-learning.md` **슬림화** — 마커 규약·표 형식 서술을 스키마로 이관 | 문서는 라이프사이클·졸업 워크플로우만 보유 |
| 8 | `STATE.md`·`brain/index.md`·`backlog.json`·`code-scan.json`은 **비범위** | 배경 분석 (4) 실측 근거. 재점화 방지를 위해 명시 고정 |

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 메모리 인덱스·히스토리 SSOT를 `MEMORY.json`으로 전환하고, PM 브리핑을 `memory-tool` 필터 조회로 교체한다 | - | 배경 분석 (2) 절약 귀속 |
| 범위 | **포함**: memory-tool 전 서브명령 JSON I/O 전환, 스키마 신설, `show --brief`, lazy 마이그레이션+`.bak`, 구 `migrate` 삭제, `memory-learning.md` 슬림화, improve-tool·dashboard·참조문서·스킬 연쇄 전환. **제외**: `STATE.md`/`state.json`, `brain/index.md`, `backlog.json`, `code-scan.json` | - | 확정 방향 §1~§8 |
| 제약 | 무손실(`.bak` 보존 + `delete` dead/superseded 가드 유지) / 배포 경계(`~/.opal/` 직접 편집 금지, 프로젝트 소스만 수정 후 install) / 2-Layer(install이 프로젝트 파일 미수정) / 표준 라이브러리만(memory_tool.py 현 원칙) / `@header` 규칙 / 077과 공통 파일 충돌 회피 | - | `.opal/AGENT.md` 금지사항 |
| 완료기준 | 아래 요구사항 R-1~R-10의 AC를 전부 충족하고, 3개 프로젝트 마이그레이션이 무손실로 검증된다 | - | - |

## 요구사항

- [ ] **R-1. `memory.json` 스키마 신설 (런타임 검증용)**
  - 무엇을: `memories[]`(title/date/type/status/file/summary) + `history[]`(title/date/stage/path/result) + `version` + `last_task_number`를 담는 JSON 스키마를 정의하고 도구가 실제 검증에 사용한다
  - 어디에: `opal/tools/memory-tool/schema/memory.schema.json`
  - 왜: 확정 방향 §1 — 현 스키마는 "문서용 SSOT"로만 존재하고 런타임 검증에 쓰이지 않는다
  - AC: 스키마 위반 입력(잘못된 `type`/`status` enum, `summary` 81자, `date` 형식 오류)을 넣으면 도구가 각각 대응 에러 코드로 거부하고, 파일이 변경되지 않는다

- [ ] **R-2. memory-tool 전 서브명령 JSON I/O 전환**
  - 무엇을: `init`/`append`/`update`/`promote`/`prune`/`show`/`review`/`delete`를 `MEMORY.json` 읽기·쓰기로 전환하고, 마크다운 표 파서·마커 처리 코드를 제거한다
  - 어디에: `opal/tools/memory-tool/memory_tool.py`, `tests/test_memory_tool.py`, `README.md`
  - 왜: 확정 방향 §1 + 배경 (1) 파싱 취약성
  - AC: (a) `memory_tool.py`에 `marker`·표 파싱 관련 심볼이 0건 (b) 8개 서브명령이 `MEMORY.json`만으로 정상 동작하며 기존 테스트 항목이 JSON 기준으로 전량 통과 (c) `marker_missing` 에러 코드가 카탈로그에서 제거됨

- [ ] **R-3. `show --brief` 필터 신설**
  - 무엇을: `status=active` 메모리만 + 히스토리 최근 N건(기본 3)만 반환하는 `--brief` 옵션을 추가한다
  - 어디에: `opal/tools/memory-tool/memory_tool.py` `cmd_show`, `README.md`, `tools.md`
  - 왜: 확정 방향 §3 — 토큰 절약의 실제 지분
  - AC: `dead`/`superseded`/`promoted` 행이 각 1건 이상 존재하는 픽스처에서 `show --brief` 출력에 해당 행이 0건이고, 출력 바이트가 `show`(전체) 대비 감소한다

- [ ] **R-4. PM 브리핑 경로 전환**
  - 무엇을: 브리핑 절차를 "`MEMORY.md`를 Read" → "`memory-tool show --brief` 호출"로 교체한다
  - 어디에: `opal/core/references/opal-pm.md` §15, `opal/core/AGENT.md` Lazy 트리거 테이블
  - 왜: 확정 방향 §3
  - AC: 두 문서에서 "MEMORY.md를 Read"류 지시가 0건이고, `show --brief` 호출 지시가 명시되어 있다

- [ ] **R-5. lazy 자동 마이그레이션 + `.bak` 보존, 구 `migrate` 삭제**
  - 무엇을: 모든 서브명령이 "`MEMORY.json` 부재 + `MEMORY.md` 존재"를 감지하면 변환 후 원 명령을 수행한다. 원본은 `.opal/MEMORY.md.bak`으로 보존한다. 구포맷 md→신포맷 md 변환기 `cmd_migrate`는 삭제한다
  - 어디에: `opal/tools/memory-tool/memory_tool.py`, `tests/`, `tests/fixtures/fixture_legacy.md`
  - 왜: 확정 방향 §4·§6
  - AC: (a) md만 있는 상태에서 `show` 호출 시 `MEMORY.json` 생성 + `.bak` 존재 + 원 명령 결과 정상 반환 (b) 변환 전후 메모리·히스토리 행 수와 각 필드 값이 100% 일치 (c) 스키마 검증 실패 시 원본 무변경 + `migration_failed` 반환 (d) `cmd_migrate` 심볼 0건

- [ ] **R-6. `memory-learning.md` 슬림화**
  - 무엇을: "마커 규약" 절과 인덱스·히스토리 표 형식 서술을 제거하고 스키마 참조로 대체한다. 라이프사이클·졸업 워크플로우는 존치한다
  - 어디에: `opal/core/references/harness/memory-learning.md`
  - 왜: 확정 방향 §7 — 규범 문서가 JSON 전환의 실제 토큰 수혜처
  - AC: 문서에서 "마커"·"`<!-- memory:` " 문자열이 0건이고, 라이프사이클 표 4행과 졸업 라우팅 표가 보존되며, 총 줄 수가 전환 전 대비 감소한다

- [ ] **R-7. improve-tool 위임 경로 전환**
  - 무엇을: `.opal/MEMORY.md` 존재 판정 3곳을 `.opal/MEMORY.json` 기준으로 바꾸고, no-op 사유 문자열을 갱신한다
  - 어디에: `opal/tools/improve-tool/improve_tool.py`, `tests/test_improve_tool.py`
  - 왜: 배경 분석 (5) — 존재 판정이 md에 묶여 있어 전환 후 상시 no-op이 된다
  - AC: `MEMORY.json`만 있는 프로젝트에서 `record --scope local`이 no-op이 아니라 memory-tool append 위임에 성공하고, 메모리가 하나도 없는 프로젝트에서는 graceful no-op을 유지한다

- [ ] **R-8. dashboard 소비자 전환**
  - 무엇을: 파서를 JSON 로드로 교체하고 라우터·doctor 점검 대상 경로를 갱신한다
  - 어디에: `dashboard/backend/parsers/memory_parser.py`, `routers/memory.py`, `routers/doctor.py`, `tests/test_parsers.py`
  - 왜: 배경 분석 (5)
  - AC: `GET /api/memory`가 `MEMORY.json` 기반으로 기존과 동일한 응답 스키마를 반환하고, 읽기 전용(mtime 불변) 원칙이 유지되며, doctor 점검 항목이 `MEMORY.json`을 가리킨다

- [ ] **R-9. `opal-project-init` 템플릿 전환**
  - 무엇을: 신규 프로젝트 초기화 시 `MEMORY.md` 인라인 템플릿 대신 `memory-tool init`으로 `MEMORY.json`을 생성하도록 바꾸고, 최신화 모드의 메모리 조회 절차도 도구 조회로 교체한다
  - 어디에: `opal/skills/opal-project-init/SKILL.md`
  - 왜: 확정 방향 §1 — 신규 프로젝트가 구포맷으로 생성되면 전환이 무의미해진다
  - AC: `opi` 초기화 산출물 목록에 `MEMORY.json`이 있고 `MEMORY.md`가 없으며, SKILL.md에 md 인라인 템플릿이 0건이다

- [ ] **R-10. 구형 참조 잔존 0 + 신형 실채택 검증 (교체형 AC)**
  - 무엇을: 참조 문서·스킬·부트스트래퍼·프로젝트 문서의 `MEMORY.md` 언급을 전수 정리한다
  - 어디에: 배경 분석 (5)의 "참조 문서 / 스킬 / 부트스트래퍼·문서" 전 항목
  - 왜: 확정 방향 §1 — 문서가 구형을 가리키면 에이전트가 구형 경로로 되돌아간다
  - AC: (a) **구형 잔존 0** — `tasks/` 이력 폴더와 `.opal/brain/` 과거 지식 페이지를 제외한 전 경로에서 `MEMORY.md` grep 0건 (b) **신형 채택** — 실제 세션에서 PM 부트스트랩이 `show --brief`로 브리핑을 생성하고, `append`→`show --brief`→`update --status dead`→`show --brief` 왕복이 `MEMORY.json`에 반영된다

## 제약 조건

- **무손실** — 마이그레이션 시 `.opal/MEMORY.md.bak` 보존. `delete`의 `dead`/`superseded` 전용 가드는 그대로 유지한다.
- **배포 경계** — `~/.opal/` 배포본을 직접 편집하지 않는다. 프로젝트 소스만 수정 후 install로 재배포한다.
- **2-Layer 모델** — install이 프로젝트 파일(`{프로젝트}/.opal/`)을 수정하지 않는다. 마이그레이션은 도구의 lazy 경로로만 수행한다.
- **표준 라이브러리만** — `memory_tool.py`의 현행 원칙을 유지한다(외부 의존 추가 금지).
- **JSON 계약** — 모든 응답은 `{"ok": true|false, ...}` 단일라인 JSON. 크래시·traceback 금지.
- **`@header` 규칙** — 변경하는 `.py` 파일의 `@header` 메타블록을 갱신한다.
- **변경이력** — 수정한 스킬·참조 문서의 변경이력 표에 행을 추가한다.
- **077 충돌 회피** — `tools.md`·`opal-project-init/SKILL.md`는 077과 겹칠 수 있으므로 PLAN에서 순서를 명시한다.

## 기술 스택

- Python 3 (표준 라이브러리) — `memory_tool.py`, `improve_tool.py`
- FastAPI (Python) — `dashboard/backend`
- 마크다운 문서 — OPAL 참조 문서·스킬 SSOT
- Bash 래퍼 (`run.sh`) — 도구 호출 표준

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 메모리 형식·라이프사이클 SSOT | `opal/core/references/harness/memory-learning.md` | R-6 슬림화 대상이자 형식 규범 원천 |
| D-2 | 설계 | PM 행동 프로세스 | `opal/core/references/opal-pm.md` §15 | R-4 브리핑 절차 변경 대상 |
| D-3 | 소스 | memory-tool 본체·README·스키마 | `opal/tools/memory-tool/` | R-1~R-5 주 변경 대상 |
| D-4 | 소스 | improve-tool 위임 로직 | `opal/tools/improve-tool/improve_tool.py` | R-7 존재 판정 3곳 |
| D-5 | 소스 | dashboard 메모리 파서·라우터 | `dashboard/backend/` | R-8 소비자 전환 |
| D-6 | 설계 | 도구 인벤토리·사용법 | `opal/core/references/tools.md` | R-3 옵션 문서화 + 077 충돌 지점 |
| D-7 | 기획 | 프로젝트 정의·문서 레지스트리 | `docs/PROJECT.md` | R-10 잔존 정리 대상 |
| D-8 | 설계 | PM 프로필·금지사항 | `.opal/AGENT.md` | 배포 경계·2-Layer 제약 원천 |
