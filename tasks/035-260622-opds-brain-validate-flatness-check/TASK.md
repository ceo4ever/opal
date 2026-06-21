# TASK: brain validate 평탄성 검사 추가 (tags/sources/related string[] 강제)

> 작성일: 2026-06-22 | 작업 유형: 기능 추가(검증 강화) | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청 (034 후속 — brain related 정비 중 발견한 validate 사각지대)
> 출력: TASK.md

## 작업 목표

`brain_tool.py`의 `validate_frontmatter`에 **선택 필드(`tags`/`sources`/`related`)의 평탄성 검사**를 추가한다. 각 필드가 존재하면 "평평한 문자열 리스트(`string[]`)"인지 검증하고, 중첩 리스트(`[['a','b']]`)나 비문자열 요소가 들어가면 `frontmatter_invalid` violation으로 검출한다. 기존 검증(필수 5필드·type·status enum)은 불변.

## 배경

034 후속으로 brain `related` frontmatter 7건을 정비하던 중, **validate의 사각지대**가 드러났다. `validate_frontmatter`(`brain_tool.py:274`)는 ①파싱 가능 ②필수 5필드 존재 ③`type`/`status` enum만 검사하고, `tags`/`sources`/`related` **값의 형식은 검사하지 않는다**. 그 결과 `related: [[a, b]]`가 `[['a','b']]` 중첩 리스트로 파싱돼도 validate를 통과했다(7건 중 5건이 이 케이스로 잠복).

PM 실증(034 세션):
- **tags가 중첩 리스트면 `--tag` 정확일치 검색에서 누락**된다(`_score_page` `:610` `tag_filter` 매칭 실패 — 정상 `[a,b]`→통과 / 중첩 `[[a,b]]`→None).
- **related가 중첩이면 링크 그래프 순회(`cmd_lint` missing_link `:839`)가 깨진다** — 교차참조 누락.
- validate가 이를 못 막으므로, 다음에 tags에서 같은 실수가 나면 **검색이 조용히 누락**된다.

→ 도구가 평탄성을 집행하면(`enforce, don't just advise` — 헌법 Core Stance) 이 클래스의 결함을 구조적으로 차단한다.

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | `validate_frontmatter`에 `OPTIONAL_FRONTMATTER`(tags/sources/related) 각 필드의 `string[]` 평탄성 검사 추가 — 존재 시 list이고 모든 요소가 str이어야 통과, 아니면 `frontmatter_invalid` violation | - | `brain_tool.py:51` OPTIONAL_FRONTMATTER 상수 기존재, `:274` validate_frontmatter |
| 범위 | **포함**: ①`validate_frontmatter` 평탄성 검사 로직 + `frontmatter_invalid` violation 생성 ②`tests/` RED-first 케이스 ③install 재배포. **제외**: 기존 required/type/status 검증 변경, `lint`/`search` 로직 변경, tags/sources/related 외 필드 검사 확대 | - | - |
| 제약 | ①기존 테스트 회귀 0 ②RED-first 강제(기능 추가지만 검증 로직 self-confirming 위험 — red-first §1.5) ③배포 경계(소스 수정→install 재배포, `~/.opal/` 직접 수정 금지) ④Surgical(validate_frontmatter 1함수 + 테스트만) ⑤@header/변경이력 | - | `red-first.md §1.5` |
| 완료기준 | (1)중첩 리스트(`[['a','b']]`)·비문자열 요소 → violation 검출 (2)정상 `string[]`(`['a','b']`) → 통과 (3)None(필드 부재)·빈 리스트(`[]`) → 통과(선택 필드) (4)기존 전체 테스트 회귀 0 + 신규 RED→GREEN (5)install 재배포 후 배포본 발효 | - | pytest 실측 |

## 요구사항

- [ ] **R-1 (평탄성 검사 추가)**: `validate_frontmatter`(`brain_tool.py:274`)에서 `OPTIONAL_FRONTMATTER`(`tags`/`sources`/`related`) 각 필드가 frontmatter에 존재하면 (a)`list` 타입이고 (b)모든 요소가 `str`인지 검사한다. 위반 시 `f"{key} must be a flat list of strings"` 형태의 violation detail을 issues에 추가. **무엇을**: 평탄성 검사 루프. **어디에**: `validate_frontmatter` 내부(기존 status 검사 다음). **왜**: 중첩 리스트/비문자열이 검색·링크를 누락시키나 validate가 미검출(배경). **AC**: 중첩 `[['a','b']]`·비문자열 `[1,2]` → violation; 정상 `['a','b']`·None·`[]` → 통과. 변경이력(@header) 반영.
- [ ] **R-2 (RED-first 테스트)**: `tests/`에 평탄성 검사 케이스를 추가한다. **무엇을**: (a)중첩 리스트 related → violation(현재 RED — 미검출) (b)정상 string[] → 통과 (c)None/빈 리스트 → 통과 (d)tags/sources도 동일 (e)기존 정상 페이지 회귀. **어디에**: `tests/test_brain_tool.py`(존재 시) 또는 해당 테스트 파일. **왜**: 버그 재현·고정. **AC**: 수정 전 (a) FAIL(RED 증거), 수정 후 전체 PASS.

## 제약 조건

- **기존 검증 불변**: 필수 5필드·type·status enum 검사 로직은 건드리지 않는다. 평탄성 검사만 추가.
- **RED-first 강제**: 검증 로직 변경은 self-confirming 위험(`red-first.md §1.5`) — RED 증거(현 validate가 중첩 리스트 미검출) 확보 후 GREEN.
- **배포 경계**: 소스 `opal/tools/brain-tool/brain_tool.py` 수정 후 install 재배포해야 배포본 발효. 배포본 직접 수정 금지.
- **최소 변경(Surgical)**: `validate_frontmatter` 1함수 + 테스트만. lint/search/index 등 다른 로직 불변.
- **변경이력**: brain_tool.py @header description에 035 변경 요약 추가.

## 기술 스택

- Python (brain_tool.py — argparse CLI, PyYAML frontmatter 파싱), pytest/unittest (`tests/`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | 수정 대상 — `validate_frontmatter`(`:274`), `OPTIONAL_FRONTMATTER`(`:51`), `_score_page`(`:589`, 영향 입증), `cmd_lint`(`:838`) |
| D-2 | 소스 | brain-tool 테스트 | `opal/tools/brain-tool/tests/` | RED-first 테스트 추가 대상 |
| D-3 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | 검증 로직 변경=RED-first 강제 트랙(§1.5) |
| D-4 | 설계 | schema-template.md | `opal/tools/brain-tool/templates/schema-template.md` | frontmatter 스키마 SSOT — tags/sources/related = `string[]`(§선택 필드) |
| D-5 | 설계 | PRINCIPLES.md (헌법) | `~/.opal/PRINCIPLES.md` | Core Stance "Enforce, don't just advise" — 도구 집행 근거 |
