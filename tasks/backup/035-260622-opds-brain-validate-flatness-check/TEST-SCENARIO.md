# TEST-SCENARIO: brain validate 평탄성 검사 추가

> 작성일: 2026-06-22 | 입력: PLAN.md §리스크 가설 표, TASK.md R-1/R-2 AC
> 대상: `opal/tools/brain-tool/brain_tool.py` `validate_frontmatter`(`:274`)
> **트랙: RED-first 강제** — 검증 로직 변경은 self-confirming 위험 높음 ([MUST] `opal/core/references/harness/red-first.md` §1.5: "RED-first 강제(self-confirming 위험 높음): … 버그 수정(회귀 방지)")

---

## 0. RED-first 적용 명시 + 작성자≠구현자

- **RED-first 강제 근거**: 검증 함수에 검증 케이스를 추가하는 작업은 "테스트와 구현이 같은 가정을 공유"하는 self-confirming 위험이 높다. PLAN §1.4 [MUST] red-first.md §1.5에 따라 **RED 증거(수정 전 FAIL)를 먼저 확보**한 뒤 GREEN으로 전환한다.
- **작성자≠구현자 (red-first.md §2)**: 본 TEST-SCENARIO.md는 시나리오만 설계한다. RED 테스트 코드는 **EXECUTE 워커(opal-task-agent)가 PLAN §4.2 Step 1에서 작성**한다. PLAN 워커는 테스트 코드를 작성하지 않는다.
- **검증 계층**: L1(단위 — `validate_frontmatter` 반환값) + L2(통합 — `cmd_validate` 종단) + L3(배포 — install-mac.sh 후 배포본 발효, [SUPERVISOR]).

---

## 1. RED 증거 표

> "수정 전" = 현재 `validate_frontmatter`(`:274-293`)에 평탄성 검사 부재 상태. 각 RED 케이스가 수정 전 FAIL함을 EXECUTE Step 1에서 캡처해야 한다.

| RED-ID | 시나리오 후보 | 입력 fm | 수정 전 동작 (RED) | 수정 후 기대 (GREEN) | 리스크 가설 |
|--------|--------------|---------|-------------------|---------------------|------------|
| RED-1 | S-1 | `{...필수5..., "related": [['a','b']]}` | issues=`[]` (미검출) → 테스트 assertTrue(violation) **FAIL** | `"related must be a flat list of strings"` ∈ issues | H-2 |
| RED-2 | S-4 | `{...필수5..., "tags": [['x']]}` | issues=`[]` (미검출) **FAIL** | `"tags must be a flat list of strings"` ∈ issues | H-1 |
| RED-3 | S-5 | `{...필수5..., "sources": [1, 2]}` | issues=`[]` (미검출) **FAIL** | `"sources must be a flat list of strings"` ∈ issues | H-1 |
| RED-4 | S-6 | `{...필수5..., "related": [1]}` | issues=`[]` (미검출) **FAIL** | `"related must be a flat list of strings"` ∈ issues | H-2 |
| RED-5 | S-8 | 중첩 related 페이지 + `cmd_validate` | violations에 frontmatter 평탄성 항목 부재 **FAIL** | `rule:frontmatter` violation 표면화 + exit 1 | H-5 |

> RED 증거 캡처 방법: 수정 전 상태에서 `pytest tests/test_brain_tool.py::TestValidateFrontmatter -v` 실행 → RED-1~4 케이스가 FAIL하는 로그를 DONE/TEST.md에 기록. RED 미확인 시 self-confirming(거짓 GREEN) 위험.

---

## 2. 시나리오 매핑 (리스크 가설 → S-N → TS-ID)

| S-ID | 시나리오 | 리스크 가설 | TS-ID (PLAN §3.5) | 계층 |
|------|---------|------------|-------------------|------|
| S-1 | 중첩 related 검출 | H-2 | TS-001 | L1 |
| S-2 | None(필드 부재) 통과 | H-4 | TS-003 | L1 |
| S-3 | 빈 리스트 `[]` 통과 | H-4 | TS-003 | L1 |
| S-4 | 중첩 tags 검출 | H-1 | TS-004 | L1 |
| S-5 | 비문자열 sources 검출 | H-1 | TS-005 | L1 |
| S-6 | 비문자열 related 검출 | H-2 | TS-006 | L1 |
| S-7 | 기존 정탐 회귀 0 | H-3 | TS-007 | L1 (회귀) |
| S-8 | cmd_validate 종단 통합 | H-5 | TS-008 | L2 |
| S-9 | 배포본 발효 | H-6 | TS-009 | L3 [SUPERVISOR] |
| S-10 | @header 변경이력 | H-7 | TS-010 | L1 (산출물) |

---

## 3. L1 — 단위 검증 (`validate_frontmatter` 반환값)

> 대상: `BT.validate_frontmatter(fm, page_types=None)` 직접 호출. mock 금지(stdlib만). 기준 fm = 필수 5필드 완비(type=entity, title, created, updated, status=active) + 선택 필드 1개 변형.

### 3.1 violation 검출 케이스 (RED 대상 — 수정 전 FAIL)

| TS-ID | S-ID | 입력 선택 필드 | 기대 issue | 검증 단언 |
|-------|------|---------------|-----------|----------|
| TS-001 | S-1 | `related: [['a','b']]` (중첩) | `"related must be a flat list of strings"` | `any("related must be a flat list" in i for i in issues)` |
| TS-004 | S-4 | `tags: [['x']]` (중첩) | `"tags must be a flat list of strings"` | `any("tags must be a flat list" in i for i in issues)` |
| TS-005 | S-5 | `sources: [1, 2]` (비문자열 int) | `"sources must be a flat list of strings"` | `any("sources must be a flat list" in i for i in issues)` |
| TS-006 | S-6 | `related: [1]` (비문자열) | `"related must be a flat list of strings"` | `any("related must be a flat list" in i for i in issues)` |
| TS-004b | S-4 | `tags: "notalist"` (list 아님) | `"tags must be a flat list of strings"` | list 미통과도 검출 (방어적 추가 케이스) |

### 3.2 통과 케이스 (수정 전·후 모두 PASS — 오탐 방지)

| TS-ID | S-ID | 입력 선택 필드 | 기대 | 검증 단언 |
|-------|------|---------------|------|----------|
| TS-002 | (정상) | `tags: ['a','b']`, `sources: ['code:x']`, `related: ['page-y']` | issue 0 (평탄성 관련) | 평탄성 detail 미포함 |
| TS-003a | S-2 | 선택 필드 전부 부재 (필수 5필드만) | issue 0 | `validate_frontmatter` == `[]` |
| TS-003b | S-3 | `tags: []`, `sources: []`, `related: []` (빈 리스트) | issue 0 | `[]` → `all()` True 통과 (H-4 경계) |

> H-4 핵심: 빈 리스트 `[]`는 `all(isinstance(x,str) for x in [])` == True이므로 별도 분기 없이 통과해야 한다. None은 `v is None: continue`로 통과. 이 경계가 깨지면 정상 페이지가 validate 실패(P0 오탐).

### 3.3 회귀 케이스 (S-7 / H-3)

| TS-ID | 대상 | 기대 |
|-------|------|------|
| TS-007 | 기존 `TestValidateFrontmatter` 6종(`test_valid_frontmatter_no_issues`, `test_missing_required_key`, `test_invalid_type_enum`, `test_invalid_status_enum`, `test_none_frontmatter`, `test_all_page_types_valid`) | 전부 PASS — 필수키/type/status/None/4타입 정탐 불변 |

### 3.4 @header 산출물 검사 (S-10 / TS-010)

| TS-ID | 대상 | 기대 |
|-------|------|------|
| TS-010 | `brain_tool.py` 파일 상단 @header `description` | `035` + 평탄성/flat 관련 변경이력 문자열 존재 (grep) |

---

## 4. L2 — 통합 검증 (`cmd_validate` 종단)

> 대상: `BT.cmd_validate(args)` — tmp_path brain에 중첩 related 페이지를 직접 작성 후 종단 실행. 기존 `TestValidate` 패턴(`test_brain_tool.py:869-887`) 준용.

| TS-ID | S-ID | 시나리오 | 기대 결과 |
|-------|------|---------|----------|
| TS-008 | S-8 | tmp brain pages/concept/에 `related: [[a, b]]`(중첩) frontmatter 페이지 작성 → `cmd_validate` 실행 | `result["valid"] == False` + `violations`에 `rule == "frontmatter"` 항목 존재 + exit 1. 단위(L1) 통과만으로는 검출 못하는 issue→violation 매핑(`:944-945`) 경로 검증 |

> H-5: 단위 함수가 issue를 반환해도 `cmd_validate`가 `{"rule":"frontmatter", "detail": iss}`로 매핑(`:944-945`)하지 못하면 종단 violation 누락. 종단 경로를 독립 검증한다.

---

## 5. L3 — 배포 검증 [SUPERVISOR] (S-9 / H-6)

> [MUST] `docs/CONVENTIONS.md` §배포 경계: 소스 수정 후 `./scripts/install-mac.sh` 재배포해야 배포본 발효. 배포본 직접 수정 금지.

| TS-ID | S-ID | 절차 | Pass 조건 |
|-------|------|------|----------|
| TS-009 | S-9 | (1) `./scripts/install-mac.sh` 실행 (2) `grep "must be a flat list of strings" ~/.opal/tools/brain-tool/brain_tool.py` (3) 배포본 기준 `pytest` 재실행 | (1) 재배포 성공 (2) 배포본에 평탄성 로직 문자열 존재 — 발효 확인 (3) 전체 pytest GREEN. 배포본 직접 수정 0건 |

---

## 6. 실행 명령 요약

| 단계 | 명령 | 기대 |
|------|------|------|
| RED 증거 | `cd opal/tools/brain-tool && python3 -m pytest tests/test_brain_tool.py::TestValidateFrontmatter -v` (수정 전) | TS-001/004/005/006 **FAIL** 로그 |
| GREEN 단위 | `python3 -m pytest tests/test_brain_tool.py::TestValidateFrontmatter -v` (수정 후) | 전체 PASS |
| 회귀/통합 | `python3 -m pytest tests/test_brain_tool.py -v` | TS-001~008 전체 PASS, 회귀 0 |
| 배포 [SUPERVISOR] | `./scripts/install-mac.sh && grep -c "flat list of strings" ~/.opal/tools/brain-tool/brain_tool.py` | 재배포 성공 + grep ≥ 1 |

---

## 7. 통과 게이트 (DONE 조건)

- [x] RED 증거 캡처: TS-001/004/005/006이 수정 전 FAIL함을 로그로 확인 (self-confirming 방지) — RED 워커 확보 완료(EXECUTE Step 1)
- [x] L1 GREEN: violation 검출 5종(3.1) + 통과 4종(3.2) 전부 PASS — `TestValidateFrontmatter` 14 passed (2026-06-22, pytest 0.01s)
- [x] L1 회귀: 기존 `TestValidateFrontmatter` 6종 PASS (S-7) — test_valid_frontmatter_no_issues/test_missing_required_key/test_invalid_type_enum/test_invalid_status_enum/test_none_frontmatter/test_all_page_types_valid 전부 PASS
- [x] L2 통합: TS-008 `cmd_validate` 종단 violation 표면화 PASS — `TestValidateFlatness035::test_validate_detects_nested_related_violation` PASSED
- [ ] L3 배포: install-mac.sh 후 배포본 발효 + 배포본 pytest GREEN (TS-009) — **캡틴 확인 대기 [SUPERVISOR]**
- [x] @header 035 변경이력 반영 (TS-010) — brain_tool.py L6에 `[035] validate_frontmatter에 선택 필드(tags/sources/related) 평탄성 검사(flat string[]) 추가` 존재 확인 (grep)

### TEST 실행 증거 (2026-06-22)

```
platform darwin -- Python 3.14.3, pytest-9.0.2
109 passed in 0.26s
TestValidateFrontmatter: 14 passed
TestValidateFlatness035: 1 passed
```

시나리오별 판정:

| TS-ID | 테스트 함수 | 판정 |
|-------|------------|------|
| TS-001 | test_flatness_nested_related_detected | PASS |
| TS-002 | test_flatness_valid_flat_lists_pass | PASS |
| TS-003a | test_flatness_optional_fields_absent_pass | PASS |
| TS-003b | test_flatness_empty_lists_pass | PASS |
| TS-004 | test_flatness_nested_tags_detected | PASS |
| TS-004b | test_flatness_tags_not_a_list_detected | PASS |
| TS-005 | test_flatness_nonstring_sources_detected | PASS |
| TS-006 | test_flatness_nonstring_related_detected | PASS |
| TS-007 | 기존 6종 (test_valid_frontmatter_no_issues 외) | PASS |
| TS-008 | test_validate_detects_nested_related_violation | PASS |
| TS-009 | (배포 검증) | 캡틴 확인 대기 |
| TS-010 | grep "[035]" brain_tool.py L6 | PASS |
