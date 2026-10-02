# GC CONVENTION REPORT — 2026-09-23T22-12

## 1. 헤더

- 실행 일시: 시작 2026-09-23 22:12:00 (완료 시각은 반환 시점 기준, 소요 시간 미계측)
- 범위: `all` / 대상 파일 20개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` (존재) + `opal/core/references/opal-doc-standard.md` §5 + `opal/core/references/header-standard.md`(@header 규칙)
- APPLY 수행 여부: N (read-only 진단 전담)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 4 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 2 / Info 1 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 4 |
| 파일별 상위 | `docs/ARCHITECTURE.md` (1) / `opal/core/references/tools.md` (1) / 신규 테스트 파일 3건 공통(1) / cmux fixture 3건 공통(1) |
| 카테고리별 빈도 | 문서화 2건 / 이력 절 1건 / @header 형식 1건 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 임계값 N=3 미충족) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-101 [docs/ARCHITECTURE.md:92, docs/ARCHITECTURE.md:450] 같은 문서 내 도구 개수 수치 불일치
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md — 문서 정확성/일관성 원칙, docs/ARCHITECTURE.md 자기 정합성)
  - 설명: 이번 diff가 `:92`의 `tools/` 요약 행만 "25종"→"26종"으로 갱신했다. 그러나 같은 파일 `:450`(디렉토리 트리 주석)은 여전히 "CLI 도구 25종"으로 남아 있어 한 문서 안에서 두 값(25 vs 26)이 공존한다. 실제 `opal/tools/*/` 디렉토리 수는 28개(`terminal-context` 포함)로 두 수치 모두 실물과 다르다.
  - 해결 방안: `:450`의 "25종"도 "26종"(또는 실제 집계 기준을 재정의)으로 함께 갱신하거나, 두 표기가 서로 다른 집계 범위(예: 문서화된 공개 도구 vs 전체 디렉토리)라면 그 기준 차이를 본문에 명시한다.
  - 자동 수정: N
  - 참조: TBD — docs/ARCHITECTURE.md 자체 정합성 규칙 (별도 URL 없음)

### Low (2건)

- [ ] GC-102 [opal/core/references/tools.md:63] 수기 누적 이력 절에 신규 행 추가
  - 카테고리: 문서화 (이력 비기재 원칙)
  - 위반 기준: 프로젝트(`opal/core/references/opal-doc-standard.md` §5 — "SKILL, AGENT, harness, reference … 수기 누적 이력 절을 만들지 않는다")
  - 설명: `opal/core/references/tools.md`는 reference 계열 문서다. §5는 reference 문서에 `변경이력` 표(수기 누적 이력 절)를 만들지 말라고 명시한다. 이 파일은 이미 v1.0부터 그런 절을 보유한 기존 패턴이며(이번 태스크 이전부터 존재), 이번 diff는 그 절에 `v2.22` 행 1건을 추가해 위반 패턴을 그대로 이어갔다. 유사 사례가 `opal/core/references/header-standard.md`(§변경이력) 등 다른 reference 문서에도 존재해 저장소 전반의 기존 관행으로 보이므로, 단일 파일 교정보다 소유자 판단(§5 예외 인정 또는 전체 이관 계획)이 필요하다.
  - 해결 방안: (a) §5 원칙대로 `변경이력` 절을 제거하고 이력을 git log로 이관하거나, (b) 이 문서 유형(도구 레지스트리)에 한해 §5의 명시적 예외를 CONVENTIONS.md/opal-doc-standard.md에 등재해 규칙과 실제 관행을 일치시킨다. 둘 중 하나를 소유자가 결정해야 하며, 이번 태스크의 단일 행 추가만 되돌리는 것은 근본 불일치를 해소하지 않는다.
  - 자동 수정: N
  - 참조: `opal/core/references/opal-doc-standard.md` §5
  - **확인 요청**: reference 문서군 전반(§5 vs 실제 관행)의 정책 충돌이므로 판정하지 않고 그대로 보고한다.

- [ ] GC-103 [opal/tools/terminal-context/tests/test_terminal_context.py:1-7, opal/tools/worktree-launcher/tests/test_adapter_cmux.py:1-7] 신규 Python 테스트 파일의 `@header`가 JSON 블록이 아닌 평문 주석 형식
  - 카테고리: 문서화 (@header 형식)
  - 위반 기준: 프로젝트(`opal/core/references/header-standard.md` §3 — Python 예시는 docstring 내부 `@header { ... }` JSON 블록만 규정)
  - 설명: header-standard.md §3은 Python 파일의 `@header`를 `"""` docstring 안의 JSON 객체로만 예시한다. 두 신규 테스트 파일은 `# @header` 다음 `# module: ...` 형태의 평문 키:값 주석을 쓴다. 이 형식은 code-scan.js의 표준 JSON 파서 계약과 다를 수 있다. 다만 인접 코드 관측 결과 `opal/tools/worktree-launcher/tests/test_adapter_conformance.py`(기존 파일, 이번 태스크 대상 목록에도 포함)가 이미 동일한 평문 형식을 쓰고 있어, 이번 두 파일은 기존 저장소 관행을 그대로 따른 것으로 보인다.
  - 해결 방안: 이 평문 형식이 code-scan 파서가 실제로 지원하는 의도된 2번째 표기(§3 갱신 누락)인지, 아니면 미교정 기존 위반의 확산인지 소유자가 확인한다. 의도된 표기라면 header-standard.md §3에 "pytest 모듈 예외" 규정을 추가하고, 아니라면 세 파일(기존 1 + 신규 2) 모두 JSON 블록으로 통일한다.
  - 자동 수정: N
  - 참조: `opal/core/references/header-standard.md` §3

### Info (1건)

- [ ] GC-104 [opal/tools/ownership-tool/tests/fixtures/launcher/cmux-workspace-create-response.json, cmux-workspace-read-response.json, cmux-workspace-close-response.json] cmux fixture에 출처 메타데이터 없음
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md 근접 관측 — 동일 디렉토리 `orca-terminal-*.json` 관행)
  - 설명: 같은 디렉토리의 `orca-terminal-read-response.json` 등은 `_fixture_note`(실측 캡처 근거·버전·일시)를 포함한다. 신규 `cmux-workspace-*.json` 3건은 원시 문자열(JSON 인코딩된 stdout 한 줄)만 담고 캡처 근거나 합성(synthetic) 여부를 밝히지 않는다. cmux CLI 응답이 JSON이 아닌 plain text이므로 객체 형태로 메타데이터를 얹기 어려운 구조적 이유가 있어 보이나, 실측 캡처인지 추정 값인지 구분할 수 없다.
  - 해결 방안: 파일명 옆에 동반 `.meta.json` 또는 테스트 코드 주석에 "실측 캡처 / 합성" 여부와 근거를 한 줄 남긴다.
  - 자동 수정: N
  - 참조: TBD — 프로젝트 내부 관행(공식 규칙 문서 없음)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 — 빈도 임계값(N≥3 파일) 충족 카테고리 없음, 신규 카테고리 없음.

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 확인 — 작성 유도 생략.
