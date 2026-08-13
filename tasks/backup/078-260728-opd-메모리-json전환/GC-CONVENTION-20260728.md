<!--
  module: gc-convention-report-078
  layer: report
  domain: opal-pilot-gc
  description: 태스크 078(메모리 JSON 전환) changed_files 컨벤션 체크 보고서 — docs/CONVENTIONS.md 단독 기준
-->

# GC CONVENTION REPORT — 2026-07-28

## 1. 헤더

- 실행 일시: 시작 2026-07-28 23:30:00 / 완료 2026-07-28 23:44:35 / 소요 약 15분
- 범위: `all` (허브+링크 미적용 — OPAL 단일 `docs/CONVENTIONS.md` 진입점) / 대상 파일 39개 (077 소관 12건 제외)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 해당 문서 전체(§언어 규칙·§네이밍 규칙·§파일 구조·§구현 규칙[@header/변경이력/배포 경계/플랫폼 분기 격리/도구 우선 원칙])를 기준으로 적용. 상세 링크(허브+링크) 없음 — 허브 전체가 곧 기준.
- APPLY 수행 여부: N (진단 전담, 읽기 전용)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 2 / Low 0 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 2 |
| 파일별 상위 Top 5 | dashboard/backend/routers/memory.py (1건) / dashboard/backend/tests/test_parsers.py (1건) |
| 카테고리별 빈도 | 문서화(@header 정확성) (2 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 트리거 미달 — 아래 §4 참고 메모만 기재) |

**점검 결과 요약**: 코드 6종(`memory_tool.py`/`improve_tool.py`/`memory_parser.py`/`memory.py`/`doctor.py`/`models.py`) 모두 표준 라이브러리 전용 import 확인(외부 패키지 없음), 파일명 snake_case 준수, EOF 개행·trailing whitespace·탭 혼용 없음. `@header` `description`/`exports`는 6종 전부 실제 코드와 정확히 일치. 변경이력 작성 의무는 대상 27종 문서·스킬 중 “## 변경이력” 섹션을 보유한 모든 문서에서 078 행 확인됨(섹션 자체가 없는 문서는 “대상 아님”으로 정상 분류). 배포 경계(`~/.opal/` 직접 편집) 흔적 없음. GEMINI.md 3중 사본(루트·`gemini-hardening.md`·템플릿)이 동일한 1줄 변경(`MEMORY.md`→`MEMORY.json`)으로 정합 유지, 신규 플랫폼 조건문 없음(플랫폼 분기 격리 준수).

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (2건)

- [ ] GC-C001 [dashboard/backend/routers/memory.py:8] `@header.depends`에 실제 미사용 모듈이 남아있음
  - 카테고리: 문서화 (@header 정확성)
  - 위반 기준: 프로젝트(CONVENTIONS.md §구현 규칙 > @header 규칙 — "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다", 근거 문서 `opal/core/references/harness/header-rules.md` §워커 권한 경계 — description/exports/depends는 실제 코드와 일치해야 워커 기입 신뢰성이 유지됨)
  - 설명: `"depends": ["models", "scanner", "config", "cache", "parsers.memory_parser", "parsers.memory_file_parser"]` 중 `parsers.memory_file_parser`는 파일 내 실제 import 목록(`models`, `parsers.memory_parser`, `scanner`, `dashboard.backend.cache`, `dashboard.backend.config`)에 없음. 078이 같은 헤더 블록의 `description`을 `MEMORY.md`→`MEMORY.json`으로 갱신하면서(git diff 확인) `depends` 필드는 손대지 않아, 실제 코드와 어긋난 상태가 그대로 남았다.
  - 해결 방안: `depends` 배열에서 `parsers.memory_file_parser`를 제거하거나(실제로 쓰지 않으면), 실제로 필요하다면 해당 import 구문을 추가한다. 파일 수정 시 관련 필드만 갱신한다는 header-rules.md §파일 수정 시 표를 따른다.
  - 자동 수정: N (헤더 필드는 워커 판단 필요 — 코드 자체 변경 아님)
  - 참조: `opal/core/references/header-standard.md` §2(필드 정의: depends), `opal/core/references/harness/header-rules.md` §워커 권한 경계

- [ ] GC-C002 [dashboard/backend/tests/test_parsers.py:9-12] `@header`에 표준 미정의 필드 `changelog` 신설
  - 카테고리: 문서화 (@header 정확성 / 필드 표준)
  - 위반 기준: 프로젝트(CONVENTIONS.md §구현 규칙 > @header 규칙 및 §변경이력) — header-standard.md §2가 정의하는 필드는 `module`/`layer`/`domain`/`description`/`exports`/`depends`(선택)/`note`(선택)/`feature`(선택)이며, `layer: test` 파일은 추가로 `task`(string)·`scenarios`(list)만 허용한다(header-rules.md §테스트 파일 전용 선택 필드). `changelog`(array)는 이 목록에 없다.
  - 설명: 078 diff에서 이 파일에 `"task": "078"`(허용됨)와 함께 `"changelog": ["2026-07-28 T078 F-009: ..."]`(비표준 필드)를 신규 추가했다. CONVENTIONS.md가 정한 변경이력 표기 방식은 "## 변경이력" 마크다운 표(문서용) 또는 헤더 내 변경이력 라인(코드 파일, 예: `memory_tool.py`의 docstring 하단 평문 "변경이력:" 블록)이며, `@header` JSON 객체 내부에 `changelog` 배열 키를 두는 제3의 방식은 정의돼 있지 않다. 동일 패턴이 `dashboard/backend/models.py`(078 이전, task 061에서 최초 도입)에도 존재해 2개 파일로 확산 중 — 아직 §4 빈도 트리거 임계값(N=3 파일)에는 못 미치지만, 표준화 여부를 결정하지 않으면 계속 늘어날 소지가 있다.
  - 해결 방안: (a) `changelog` 내용을 `@header` JSON 밖으로 옮겨 파일 하단에 header-rules.md가 인정하는 "헤더 내 변경이력 라인"(memory_tool.py 방식) 평문 블록으로 옮기거나, (b) `changelog`를 header-standard.md §2에 선택 필드로 정식 추가하는 문서화 변경을 검토한다. 둘 중 하나로 `models.py`·`test_parsers.py` 2개 파일을 통일한다.
  - 자동 수정: N (문서 표준 결정이 선행되어야 함)
  - 참조: `opal/core/references/header-standard.md` §2, `opal/core/references/harness/header-rules.md` §테스트 파일 전용 선택 필드

### Low (0건)

### Info (0건)

---

## 4. 문서 업데이트 제안 (트리거 발동 시만)

트리거 임계값(빈도 N≥3 파일) 미달로 정식 트리거 항목은 없음. 참고 메모만 기록한다.

- (참고, 비트리거) `@header` JSON 내부 `changelog` 배열 키가 `models.py`(061)·`test_parsers.py`(078) 2개 파일에서 관찰됨. 3번째 파일에서 재발하면 header-standard.md §2에 정식 필드로 추가하거나 금지 규정을 명문화하는 것을 제안.

---

## 5. 문서 작성 유도

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
