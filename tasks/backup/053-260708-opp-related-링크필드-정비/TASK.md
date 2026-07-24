# TASK: brain related 프론트매터 위키링크 정비 + validate 링크필드 집행 강화

> 작성일: 2026-07-08 | 작업 유형: 수정+개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청 (`//opp --agentic`) + 선행 리뷰 대화
> 출력: TASK.md

## 작업 목표

brain 페이지의 `related` 프론트매터에 잘못 기입된 마크다운 위키링크(`[[...]]`) 6항목을 평탄 슬러그 리스트로 정규화하고, 동일 오류가 재발하지 않도록 `validate`에 링크필드 값 검사를 추가하여 결정론적으로 집행한다. 부수적으로 `add-page`에 `--related` 플래그를 추가해 손편집 유인을 줄인다.

## 배경

brain wiki의 `related` 프론트매터 필드는 **평탄한 페이지 슬러그 리스트**(예: `[state-tool, brain-tool]`)여야 한다. 그러나 일부 페이지에서 LLM이 골격 생성 후 파일을 손편집하며 본문용 마크다운 위키링크 문법 `[[...]]`를 `related` YAML 값에 잘못 써넣었다. 이 값은 `add-page` 도구가 생성하는 것이 아니라 사후 손편집으로 유입된 것이며, 현행 `validate`의 035 평탄성 가드가 이 형태(quoted string)를 잡지 못하는 사각지대가 존재한다.

## 배경 분석 (대화에서 도출)

선행 리뷰(코드 실측 기반)에서 확인된 사실:

**1) `add-page`는 `related`를 생성하지 않는다**
- `cmd_add_page`의 인자는 `--type`·`--title`·`--tags`·`--sources`뿐 — `--related` 플래그 없음 (`opal/tools/brain-tool/brain_tool.py:1187-1194`).
- 도구는 템플릿 frontmatter를 복사하고 tags/sources만 `.split(",")`로 평탄화한다 (`opal/tools/brain-tool/brain_tool.py:501-504`). `related`는 건드리지 않으므로 잘못된 값은 **LLM 손편집으로 유입**된 것.

**2) 잔존 오류 범위 — 3페이지 6항목 (전부 quoted block form)**
- `.opal/brain/pages/entity/memory-tool.md` — `[[state-tool]]`, `[[three-layer-memory-architecture]]`
- `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md` — `[[memory-tool]]`, `[[agentic-output-direct-verification-lesson]]`
- `.opal/brain/pages/concept/memory-lifecycle-graduation-workflow.md` — `[[memory-tool]]`, `[[three-layer-memory-architecture]]`
- unquoted 인라인형(`related: [[a,b]]`)은 현재 0건.

**3) 탐지 도구 동작 — validate는 눈감고 lint만 잡는다**
- `validate` 실측 결과: `valid:true, violations:0`. 035 평탄성 가드(`opal/tools/brain-tool/brain_tool.py:294-299`)는 `related`가 "flat list of strings"인지만 검사하며, `"[[state-tool]]"`은 **정상 문자열**이라 통과시킨다.
- 035 가드가 겨냥한 것은 unquoted `related: [[a,b]]`가 PyYAML에 의해 중첩 리스트 `[['a','b']]`로 파싱되는 형태뿐이다 (`.opal/brain/pages/concept/brain-validate-flatness-enforcement.md` §034 사각지대 기록).
- 이 6항목을 실제로 잡는 것은 `lint`의 `missing_link`(값 `[[state-tool]]`이 본문 링크와 매칭 실패)다.
- ⇒ 근본 구멍: **quoted `[[...]]` 문자열이 validate를 그냥 통과**한다.

## 확정된 설계 방향 (대화에서 합의)

캡틴이 AskUserQuestion에서 **전체 범위(정비 + validate 강화 + add-page 플래그)**를 선택함.

1. **정비**: 6항목을 `[[ ]]`·`.md` 접미사를 제거한 평탄 슬러그로 정규화.
2. **validate 강화 (최우선·enforce)**: `validate_frontmatter`의 링크성 선택 필드(`related`) 요소가 `[[`/`]]`/`.md` 접미사를 포함하면 `frontmatter_invalid` violation으로 거부. PRINCIPLES "advise 말고 enforce" 적용 — quoted 사각지대를 닫는다.
3. **add-page `--related` 플래그**: `tags`/`sources`처럼 CSV → 평탄 리스트 생성. 손편집 유인 감소(보조).
4. 리뷰에서 캡틴 원안 "lint에 validate 포함"은 이 케이스에 무효(validate가 quoted형을 못 잡음)로 판명 → 2번 validate 강화가 대체하며 채택하지 않는다.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 6항목 위키링크 정규화 + validate 링크필드 집행 강화 + add-page `--related` 플래그 추가 | - | 배경분석 1~3 |
| 범위 | **포함**: 3페이지 6항목 정규화 / `validate_frontmatter` 링크필드 검사 로직 + 테스트 / `add-page --related` 플래그 + 테스트. **제외**: lint↔validate 통합안, unquoted 케이스(현재 0건), `.md` 접미사 위키링크 본문 링크 정비(별건 broken_link) | - | 확정 설계 방향 1~4 |
| 제약 | `~/.opal/` 직접 편집 금지(프로젝트 소스 수정 후 install 재배포) / 변경이력 표 행 추가 / STATE.md는 state-tool로만 / 커밋은 캡틴 명시 요청 시에만 | - | `.opal/AGENT.md` §금지사항 |
| 완료기준 | (a) `grep -rn "\[\[" related 프론트매터` = 0건 (b) 정규화 후 `validate`·`lint` 해당 6 missing_link 소거 (c) 강화된 `validate`가 `[[x]]`/`x.md` 값을 `frontmatter_invalid`로 거부 — 신규 테스트 GREEN (d) `add-page --related a,b` → 평탄 리스트 생성 — 신규 테스트 GREEN (e) 기존 brain-tool 테스트 스위트 전체 GREEN(회귀 0) | - | - |

## 요구사항

- [ ] **R-1** 3페이지 6항목의 `related` 값을 `[[ ]]`·`.md` 제거한 평탄 슬러그로 정규화 — `.opal/brain/pages/entity/memory-tool.md`, `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md`, `.opal/brain/pages/concept/memory-lifecycle-graduation-workflow.md` — AC: 세 파일 `related`에 `[[`/`]]`/`.md` 미포함, 정규화된 슬러그가 실제 페이지 파일명과 일치
- [ ] **R-2** `validate_frontmatter`에 링크필드(`related`) 값 검사 추가 — `opal/tools/brain-tool/brain_tool.py` — AC: `related` 요소에 `[[`/`]]`/`.md`가 있으면 `frontmatter_invalid` violation 반환, None·빈 리스트·정상 슬러그는 통과(기존 동작 불변)
- [ ] **R-3** R-2에 대한 단위 테스트 추가 — `opal/tools/brain-tool/tests/` — AC: `[[x]]`·`x.md` 값 거부 케이스 + 정상 슬러그 통과 케이스가 테스트로 존재하고 GREEN
- [ ] **R-4** `add-page`에 `--related` 플래그 추가 (CSV → 평탄 리스트) — `opal/tools/brain-tool/brain_tool.py` — AC: `add-page ... --related a,b` 실행 시 생성 페이지 frontmatter `related: [a, b]`, 미지정 시 기존 동작(템플릿 기본값) 불변
- [ ] **R-5** R-4에 대한 단위 테스트 추가 — AC: `--related` 지정/미지정 케이스 GREEN
- [ ] **R-6** 변경된 도구/페이지 관련 문서(brain-tool @header·brain-validate-flatness-enforcement 페이지 등)에 변경이력·설명 반영 — AC: brain-tool.md entity 페이지 또는 tools.md 설명에 링크필드 검사 추가 기술

## 제약 조건

- **배포 경계**: `~/.opal/`(배포본) 직접 수정 금지. 프로젝트 소스 `opal/tools/brain-tool/`를 수정한 뒤 install로 재배포한다 (`.opal/AGENT.md` §금지사항).
- **정규화 슬러그 무결성**: `[[ ]]` 제거 후 슬러그가 실제 페이지 파일명과 일치해야 하며, 불일치 시 broken_link 유발 — 정비 시 대상 페이지 존재 확인.
- **회귀 방지**: `validate_frontmatter` 변경이 기존 검증(필수 5필드·type·status enum·035 평탄성)을 훼손하지 않아야 한다.
- **커밋 규칙**: agentic 모드라도 커밋은 캡틴 명시 요청 시에만.

## 기술 스택

- Python (brain-tool CLI, PyYAML) — `opal/tools/brain-tool/`
- 테스트: pytest (`opal/tools/brain-tool/tests/`)
- 셸 래퍼: `run.sh` + `.venv`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | validate_frontmatter·cmd_add_page 변경 대상 |
| D-2 | 설계 | brain-validate-flatness-enforcement | `.opal/brain/pages/concept/brain-validate-flatness-enforcement.md` | 035 평탄성 가드 설계 배경 + 034 사각지대 기록 |
| D-3 | 소스 | brain-tool 테스트 | `opal/tools/brain-tool/tests/` | R-3·R-5 테스트 추가 위치 |
| D-4 | 설계 | opal-doc-standard / tools.md | `opal/core/references/tools.md` | brain-tool 도구 설명 갱신(R-6) |
