# PLAN: brain validate 평탄성 검사 추가 (tags/sources/related string[] 강제)

> 작성일: 2026-06-22 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석)
> 모드: Flat (단일 기능)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`brain_tool.py`의 `validate_frontmatter`(`:274`)에 **선택 필드(`tags`/`sources`/`related`)의 평탄성 검사**를 추가한다. 각 필드가 존재하면 "평평한 문자열 리스트(`string[]`)"인지 검증하고, 중첩 리스트(`[['a','b']]`)·비문자열 요소(`[1,2]`)는 `frontmatter_invalid` violation으로 검출한다. 기존 검증(파싱·필수 5필드·type·status enum)은 불변이며, 최소 변경(`validate_frontmatter` 1함수 + 테스트)만 수행한다. 검증 로직 변경은 self-confirming 위험이 높으므로 RED-first 강제 트랙으로 진행한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 선택 필드 평탄성 검사 (tags/sources/related = flat string[]) | R-1, R-2 | P0 | 없음 |

> 기능 1개 → **Flat 모드**. §2·§3는 F 하위 섹션 없이 평면으로 작성.

### 1.3 기능 의존 그래프 (ASCII)

생략 (단일 기능).

### 1.4 참조 제약 ([MUST] 원문 인용)

> citation-rules.md §2.4 · §4 (PLAN 단계 [MUST] 필수). TASK §제약 / PM 주입 [MUST]를 그대로 옮긴다.

- [MUST] `opal/core/references/harness/red-first.md` §1.5: "RED-first 강제(self-confirming 위험 높음): … 버그 수정(회귀 방지)" — 검증 로직 변경은 self-confirming 위험 → RED-first 강제 트랙. (PM 주입, TASK §제약 ②)
- [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical: "Touch only what the plan names." → `validate_frontmatter` 1함수 + 테스트만. lint/search/index/parse_frontmatter 불변. (PM 주입)
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, …)에서 수행한다. 변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다." (→ D-6 §배포 경계)
- [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다 … 변경이력은 … 헤더 내 변경이력 라인으로 갱신한다." → brain_tool.py @header description에 035 변경 요약 추가. (→ D-6 §@header 규칙)
- [MUST] `opal/tools/brain-tool/templates/schema-template.md` §2.2: "`tags` string[] / `sources` string[] / `related` string[]" — 평탄성 검사의 타입 계약 SSOT. (→ D-4 §2.2)

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `validate_frontmatter` 평탄성 루프 (`:291` 이후) | tags 중첩(`[['a','b']]`) 미검출 → `_score_page` tag 정확일치(`:610`) 실패로 `--tag` 검색 누락이 잠복 | P1 | L1 (validate 반환값 단위) | S-1, S-4 |
| H-2 | `validate_frontmatter` 평탄성 루프 | related 중첩 미검출 → `cmd_lint` missing_link 순회(`:840`)가 비-str 요소에서 `f"[[{r}]]"` 오매칭 → 링크 그래프 누락 | P1 | L1 (validate 반환값 단위) | S-1, S-6 |
| H-3 | `validate_frontmatter` 반환 계약 (issues: list[str]) | 신규 issue 추가가 기존 정탐(필수키/type/status) 케이스에 오탐/누락 회귀 유발 | P1 | L1 (회귀: 기존 TestValidateFrontmatter 6종) | S-7 |
| H-4 | None·빈 리스트(`[]`) 경계 처리 | 선택 필드 부재/빈 값을 violation으로 오탐 → 정상 페이지가 validate 실패(False positive) | P0 | L1 (None·`[]` 통과 단위) | S-2, S-3 |
| H-5 | `cmd_validate`(`:943`) 경유 통합 경로 | 단위 함수는 통과해도 `cmd_validate`가 issue를 violations로 매핑(`:944-945`)하지 못해 종단 violation 누락 | P1 | L2 (cmd_validate 종단 통합) | S-8 |
| H-6 | 소스→배포본 발효 (`./scripts/install-mac.sh`) | 소스만 수정하고 재배포 누락 시 `~/.opal/tools/brain-tool/brain_tool.py` 배포본 미발효 → 런타임 변경 없음 | P1 | L3 [SUPERVISOR] (배포 후 배포본 검증) | S-9 |
| H-7 | @header description 변경이력 | install-mac.sh strip 대상 외 — @header는 소스·배포본 모두 유지. 변경이력 미반영 시 컨벤션 위반 | P2 | L1 (@header 텍스트 검사) | S-10 |

---

## 2. 기능별 분석

> Flat 모드 — F 하위 섹션 없이 평면 작성.

### 2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬/도구 | `opal/tools/brain-tool/brain_tool.py` | `validate_frontmatter`(`:274-293`) 평탄성 검사 추가 + @header 변경이력 | 수정 |
| 환경(테스트) | `opal/tools/brain-tool/tests/test_brain_tool.py` | RED-first 단위 케이스 추가 (`TestValidateFrontmatter` 확장) | 수정 |
| 환경(배치) | `scripts/install-mac.sh` | 소스→배포본 재배포 (코드 변경 없음, 실행만) | 실행 |

### 2.2 현재 구현

**`validate_frontmatter(fm, page_types=None)` — `brain_tool.py:274-293`** (직접 분석):

```python
def validate_frontmatter(fm, page_types=None):
    allowed_types = page_types if page_types is not None else PAGE_TYPES
    issues = []
    if fm is None:
        return ["frontmatter block missing or unparseable"]          # ① 파싱 (:282)
    for key in REQUIRED_FRONTMATTER:                                  # ② 필수 5필드 (:283-285)
        if key not in fm or fm.get(key) in (None, ""):
            issues.append(f"missing required key: {key}")
    ptype = fm.get("type")
    if ptype is not None and ptype not in allowed_types:             # ③ type enum (:286-288)
        issues.append(f"invalid type: {ptype}")
    status = fm.get("status")
    if status is not None and status not in STATUS_ENUM:            # ④ status enum (:289-291)
        issues.append(f"invalid status: {status} (allowed: ...)")
    return issues                                                    # ← 평탄성 검사 부재
```

- 검사 항목 4종: ①파싱(`:282`) ②필수 5필드(`REQUIRED_FRONTMATTER` `:50`) ③type enum(`:287`) ④status enum(`STATUS_ENUM` `:53`, `:290`). **선택 필드 값 형식은 미검사** ← 추가 지점은 `return issues`(`:293`) 직전.
- 상수 `OPTIONAL_FRONTMATTER = ["tags", "sources", "related"]`(`:51`) 기존재 — 재사용.
- 반환 계약: 위반 detail 문자열의 list (빈 list = 정상). (`:275` docstring)
- violation 표면: `cmd_validate`(`:943`)가 issue를 `{"page": rel, "rule": "frontmatter", "detail": iss}`로 매핑(`:944-945`), `add-page`(`:499-501`)는 `err(... "frontmatter_invalid", detail="; ".join(issues))`. `frontmatter_invalid` 에러코드는 `:148`.

**영향 입증 (PM 실증 — 미검출 시 잠복 결함):**
- tags 중첩 → `_score_page`(`:589`)의 tag 정확일치(`tag_filter`, `:610`)가 `[['a','b']]`에서 None → `--tag` 검색 누락(`:608-619`).
- related 중첩 → `cmd_lint` missing_link(`:838-844`)가 `for r in related`(`:840`)에서 `str(r)`가 `"['a', 'b']"` 형태가 되어 `f"[[{r}]]"`(`:842`) 매칭 깨짐 → 링크 그래프 순회 누락.

### 2.3 영향 범위

- **호출자(상위 의존)**: `cmd_add_page`(`:499`) — 페이지 생성 시 검증. `cmd_validate`(`:943`) — 전체 brain 검증. 둘 다 issue 비어 있을 때 통과, 비어 있지 않으면 violation 표면화.
- **피호출자(하위 의존)**: 없음 (stdlib `isinstance`만 사용, 외부 의존 0).
- **공유 상태**: `OPTIONAL_FRONTMATTER`(`:51`) 상수 읽기 전용 참조. 변형 없음.
- **불변 보장(Surgical)**: `parse_frontmatter`(`:258`) / `_score_page`(`:589`) / `cmd_lint`(`:795`) / `cmd_search`(`:655`) / `cmd_index`(`:523`) 로직은 건드리지 않는다 — 이들은 평탄성을 **소비**하던 부작용을 가진 코드이며, validate가 평탄성을 **집행**하면 구조적으로 보호된다.
- **관련 테스트**: `tests/test_brain_tool.py` `TestValidateFrontmatter`(`:1410-1461`) 단위 6종, `TestValidate`(`:825`) 통합. 기존 6종은 회귀 0 대상(H-3).

---

## 3. 기능별 설계

> Flat 모드 — 평면 작성.

### 3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | 없음 | - | - | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/brain-tool/brain_tool.py` | 스킬/도구 | `validate_frontmatter`의 status 검사(`:291`) 다음, `return issues`(`:293`) 직전에 `OPTIONAL_FRONTMATTER` 순회 평탄성 검사 추가 + @header description 035 변경이력 | `brain_tool.py:274-293`, (→ D-1) |
| 2 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 환경(테스트) | `TestValidateFrontmatter`(`:1410`)에 평탄성 RED-first 케이스 추가 (중첩/비문자열 violation, 정상/None/`[]` 통과, tags/sources/related 각각) | (→ D-2), TEST-SCENARIO.md |

### 3.2 API·데이터 모델·설계

**함수 시그니처 (불변)**: `validate_frontmatter(fm, page_types=None) -> list[str]` (`brain_tool.py:274`). 시그니처·반환 계약(위반 detail 문자열 list, 빈 list=정상)은 변경하지 않는다. (→ D-1 `:275`)

**추가 로직 (status 검사 다음, `return issues` 직전 삽입)**:

```python
# 선택 필드 평탄성 검사 (035) — tags/sources/related = flat list[str]
# None(부재)·빈 리스트는 통과. 존재 시 list이고 모든 요소가 str이어야 통과.
for key in OPTIONAL_FRONTMATTER:
    v = fm.get(key)
    if v is None:
        continue                       # 선택 필드 부재 → 통과 (H-4)
    if not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
        issues.append(f"{key} must be a flat list of strings")
```

설계 결정:
- **삽입 위치**: status enum 검사(`:289-291`) 다음, `return issues`(`:293`) 직전. TASK §명확화 확정값 + PM 설계 방향 일치. (→ D-1 `:289-293`)
- **순회 대상**: 기존 상수 `OPTIONAL_FRONTMATTER`(`:51`) 재사용 — 신규 상수 도입 없음(Surgical). [MUST] `opal/tools/brain-tool/templates/schema-template.md` §2.2: "tags/sources/related = string[]" (→ D-4 §2.2).
- **통과 조건**: `v is None`(필드 부재) → `continue`로 즉시 통과. 빈 리스트 `[]`는 `isinstance([], list) and all(... for x in [])` → `all()`이 빈 시퀀스에 `True` 반환하므로 **자동 통과**(H-4). 별도 분기 불필요.
- **위반 조건**: ①list가 아님 ②요소 중 하나라도 str이 아님(중첩 리스트 `[['a','b']]`의 요소는 list, 비문자열 `[1,2]`의 요소는 int) → `f"{key} must be a flat list of strings"` detail 추가. TASK R-1 AC 포맷 그대로. (→ D-1)
- **결정론**: `isinstance`/`all`만 사용 — stdlib, 외부 의존 0, 동일 입력 → 동일 출력. PyYAML 파싱 결과(`parse_frontmatter` `:258`)를 입력으로 받으므로 YAML이 `[[a,b]]`를 중첩 list로 파싱한 것을 그대로 검사.
- **bool 주의 (설계 메모)**: Python에서 `isinstance(True, int)`는 True지만, 검사 대상은 `str` 타입이므로 `isinstance(True, str)`는 False → bool 요소도 정확히 violation으로 검출된다. 별도 처리 불필요.
- **@header 변경이력**: description 끝에 `[035] validate_frontmatter에 선택 필드(tags/sources/related) 평탄성 검사(flat string[]) 추가 — 중첩 리스트·비문자열 요소를 frontmatter_invalid violation으로 집행.` 추가. [MUST] `docs/CONVENTIONS.md` §@header 규칙 (→ D-6).

### 3.3 환경 변경

해당 없음 (stdlib `isinstance`/`all`만 사용, 신규 패키지 0).

### 3.4 배치/마이그레이션

- **재배포 (배치)**: 소스 수정 후 `./scripts/install-mac.sh` 실행하여 `~/.opal/tools/brain-tool/brain_tool.py` 배포본 발효. [MUST] `docs/CONVENTIONS.md` §배포 경계 (→ D-6). DB 마이그레이션 없음.

### 3.5 테스트 시나리오 (AC ↔ TS 매핑)

> RED-first 강제 트랙. RED 증거 표 + 단위/회귀/배포 계층은 TEST-SCENARIO.md 참조. 아래는 PLAN 측 TS-ID 매핑 요약.

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (중첩 검출) | 기능 테스트 (RED→GREEN) | `related: [['a','b']]` → `validate_frontmatter`가 `"related must be a flat list of strings"` issue 반환. 수정 전 RED(빈 list), 수정 후 GREEN |
| TS-002 | R-1 AC (정상 통과) | 기능 테스트 | `tags: ['a','b']` 등 정상 string[] → issue 0 |
| TS-003 | R-1 AC (None/빈 통과) | 기능 테스트 | 필드 부재(None)·빈 리스트(`[]`) → issue 0 (선택 필드) |
| TS-004 | R-1 AC (tags 중첩) | 기능 테스트 (RED→GREEN) | `tags: [['x']]` → `"tags must be a flat list of strings"` 반환 |
| TS-005 | R-1 AC (sources 비문자열) | 기능 테스트 (RED→GREEN) | `sources: [1,2]` → `"sources must be a flat list of strings"` 반환 |
| TS-006 | R-1 AC (related 비문자열) | 기능 테스트 (RED→GREEN) | `related: [1]` → `"related must be a flat list of strings"` 반환 |
| TS-007 | R-1 제약 (기존 검증 불변) | 회귀 테스트 | 기존 `TestValidateFrontmatter` 6종(`:1422-1461`) 전부 PASS |
| TS-008 | R-1 AC (종단 통합) | 통합 테스트 | 중첩 related 페이지 → `cmd_validate`가 `rule:frontmatter` violation으로 표면화 + exit 1 |
| TS-009 | 완료기준(5) 배포 | 배포 검증 [SUPERVISOR] | `install-mac.sh` 후 전체 pytest GREEN + 배포본 `~/.opal/.../brain_tool.py`에 평탄성 로직 발효 |
| TS-010 | R-1 (@header) | 산출물 검사 | brain_tool.py @header description에 035 변경이력 문자열 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 (RED) | F-001 | 1 | opal-task-agent | 순차 | RED 테스트 먼저 작성 — 수정 전 FAIL 증거 확보 |
| 2 (GREEN) | F-001 | 2 | opal-task-agent | 순차 | 평탄성 검사 + @header 구현 → Step 1 테스트 GREEN |
| 3 (배포) | F-001 | 3 | opal-task-agent | 순차 | install-mac.sh 재배포 + 배포본 검증 |

> RED→GREEN 순서 강제: Step 1(RED) → Step 2(GREEN) → Step 3(배포). 동일 파일(test → 소스) 순차 의존.

### 4.2 실행 체크리스트

> 총 3개 Step | Phase 3개 | 실행 모드: 단순

#### Step 1: RED 테스트 작성 (평탄성 검사 케이스)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 환경(테스트)
- **agent**: opal-task-agent
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: `TestValidateFrontmatter` 클래스(`:1410`)에 평탄성 단위 케이스 추가 — TS-001(중첩 related violation), TS-002(정상 string[] 통과), TS-003(None·`[]` 통과), TS-004(tags 중첩), TS-005(sources 비문자열), TS-006(related 비문자열). TEST-SCENARIO.md §3 L1 케이스 표를 그대로 구현. mock 금지 — `BT.validate_frontmatter` 직접 호출.
- **완료 기준**: 신규 테스트 실행 시 TS-001/004/005/006 (violation 검출 케이스)가 **수정 전 FAIL(RED)** 함을 확인 — RED 증거 확보. TS-002/003(통과 케이스)은 수정 전에도 PASS(현 동작 = 미검사라 통과).
- **테스트**: `python3 -m pytest tests/test_brain_tool.py::TestValidateFrontmatter -v` → 중첩/비문자열 케이스 FAIL 로그 캡처
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: 평탄성 검사 로직 구현 + @header 변경이력 (GREEN)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 스킬/도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: `validate_frontmatter`(`:274`)의 status 검사(`:289-291`) 다음, `return issues`(`:293`) 직전에 §3.2 코드 블록(`OPTIONAL_FRONTMATTER` 순회 + `isinstance(v, list) and all(isinstance(x, str) for x in v)` 평탄성 검사) 삽입. 위반 시 `f"{key} must be a flat list of strings"` issue 추가. @header description 끝에 035 변경이력 문자열 추가(§3.2). 기존 ①~④ 검사 로직·시그니처 불변(Surgical).
- **완료 기준**: Step 1의 RED 케이스(TS-001/004/005/006) GREEN 전환 + 기존 `TestValidateFrontmatter` 6종 회귀 0 + 전체 `pytest tests/test_brain_tool.py` PASS. cmd_validate 종단(TS-008) violation 표면화 확인.
- **테스트**: `python3 -m pytest tests/test_brain_tool.py -v` (TS-001~008 전체 GREEN)
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: 재배포 + 배포본 발효 검증 [SUPERVISOR]
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 환경(배치)
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh` (실행), `~/.opal/tools/brain-tool/brain_tool.py` (발효 대상)
- **작업 내용**: `./scripts/install-mac.sh` 실행하여 소스→배포본 재배포. 배포본 `~/.opal/tools/brain-tool/brain_tool.py`에 평탄성 검사 로직이 반영됐는지 grep 확인. [MUST] `docs/CONVENTIONS.md` §배포 경계.
- **완료 기준**: 재배포 성공 + 배포본에 `must be a flat list of strings` 문자열 존재 + 배포본 기준 전체 pytest GREEN (TS-009). 배포본 직접 수정 0.
- **테스트**: TS-009 — 배포 후 배포본 grep + pytest 재실행
- **실행 방법**: direct
- **의존**: Step 2

> docs/ 갱신 Step: 불필요 — 내부 검증 로직 강화이며 docs/(BACKEND/FRONTEND/ARCHITECTURE/CONVENTIONS) 내용 변경 없음. SCHEMA §2.2가 이미 `string[]`을 명시(SSOT)하므로 신규 패턴 도입 아님. brain_tool.py @header 변경이력으로 추적 충족.

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED-first 강제 — 테스트 RED 증거 확보 후 소스 구현 (red-first.md §1.5) |
| Step 2 → Step 3 | 소스 수정 완료 후 배포 가능 (배포 경계) |
| 병렬 없음 | 단일 모듈·단일 함수 변경 — 직렬 의존 체인 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 중첩 리스트(`[['a','b']]`) → violation 검출 | TS-001, TS-004 | `validate_frontmatter`가 `"{key} must be a flat list of strings"` issue 반환 |
| F-001 | 비문자열 요소(`[1,2]`) → violation 검출 | TS-005, TS-006 | 해당 key violation 반환 |
| F-001 | 정상 string[] → 통과 | TS-002 | issue 0 |
| F-001 | None(부재)·빈 리스트(`[]`) → 통과 | TS-003 | issue 0 (선택 필드) |
| F-001 | tags/sources/related 3필드 각각 검사 | TS-004/005/006 | 각 필드 독립 검출 |
| F-001 | 종단 통합 (cmd_validate violation 표면화) | TS-008 | `rule:frontmatter` violation + exit 1 |
| F-001 | 배포본 발효 | TS-009 | 배포본 pytest GREEN + 로직 grep 확인 |

### 5.2 회귀 테스트

- [ ] 기존 `TestValidateFrontmatter` 6종(필수키/type/status/None/4타입) 전부 PASS (TS-007)
- [ ] 기존 `TestValidate` 통합 4종 PASS (정상 brain valid, 구조/frontmatter violation 검출)
- [ ] `cmd_add_page`/`cmd_lint`/`cmd_search` 관련 기존 테스트 전부 PASS (Surgical — 미변경)
- [ ] 전체 `pytest tests/test_brain_tool.py` 회귀 0

### 5.3 코드/문서 품질

- [ ] 프로젝트 컨벤션 준수 (Python snake_case, stdlib only)
- [ ] brain_tool.py @header description에 035 변경이력 반영 (TS-010)
- [ ] Surgical — `validate_frontmatter` 1함수 + 테스트만 변경, lint/search/index/parse 불변

### 5.4 보안

- [ ] 코드에 하드코딩된 토큰/시크릿 없음 (검증 로직만 추가)
- [ ] 외부 입력(frontmatter YAML)을 `isinstance` 타입 검사로만 처리 — eval/exec 없음, 인젝션 표면 0

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 3개 | 단순 (≤5) |
| 변경 파일 수 | 2개 (brain_tool.py, test_brain_tool.py) | 단순 (≤3) |
| 모듈 범위 | 단일 모듈 (brain_tool) | 단순 |
| 작업 유형 | 검증 로직 강화 (단순 기능 추가) | 단순 |
| 외부 의존성 | 없음 (stdlib isinstance/all) | 단순 |
| **실행 모드** | **단순** | |

> 모든 기준이 단순 모드 → **단순 모드 확정**. 모든 Step `direct`. 실행 아키텍처(§7) 생략.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Python (stdlib `isinstance`/`all`, PyYAML 파싱은 기존), argparse CLI | trailofbits/modern-python (해당 없음 — stdlib 변경만, 신규 패턴 미도입) |
| 테스트 | pytest/unittest (`tests/test_brain_tool.py`, tmp_path 격리, mock 금지) | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | stdlib 타입 검사 — 외부 라이브러리 API 조회 불필요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | 수정 대상 — `validate_frontmatter`(`:274-293`), `OPTIONAL_FRONTMATTER`(`:51`), `frontmatter_invalid`(`:148`), `_score_page`(`:589`·`:610` 영향), `cmd_lint`(`:838-844` 영향), `cmd_validate`(`:943-945` 종단) |
| D-2 | 소스 | brain-tool 테스트 | `opal/tools/brain-tool/tests/test_brain_tool.py` | RED-first 추가 대상 — `TestValidateFrontmatter`(`:1410-1461`) 확장, `TestValidate`(`:825`) 통합 |
| D-3 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | 검증 로직 변경 = RED-first 강제 트랙(§1.5) |
| D-4 | 설계 | schema-template.md | `opal/tools/brain-tool/templates/schema-template.md` | frontmatter 스키마 SSOT — tags/sources/related = `string[]`(§2.2 선택 키) |
| D-5 | 설계 | PRINCIPLES.md (헌법) | `~/.opal/PRINCIPLES.md` | Core Stance "Enforce, don't just advise" + §3 Surgical 근거 |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §배포 경계(`:200-203`) / §@header 규칙(`:170-174`) / §변경이력(`:194-198`) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | tags 중첩 잠복 → `--tag` 검색 누락 (H-1) | F-001 | P1 | validate가 평탄성 집행 — 페이지 생성/검증 시점 차단 (S-1/S-4) |
| R-2 | related 중첩 → lint missing_link 순회 깨짐 (H-2) | F-001 | P1 | validate 평탄성 집행 — related 비-str 차단 (S-1/S-6) |
| R-3 | 신규 issue가 기존 정탐에 회귀 유발 (H-3) | F-001 | P1 | RED-first + 기존 6종 회귀 테스트 보존 (S-7), Surgical 삽입 (return 직전 append only) |
| R-4 | None·`[]` 오탐 (정상 페이지 실패) (H-4) | F-001 | P0 | `v is None` continue + 빈 list `all()` True 통과 단위 검증 (S-2/S-3) |
| R-5 | 단위 통과·종단 누락 (H-5) | F-001 | P1 | cmd_validate 통합 테스트로 issue→violation 매핑 검증 (S-8) |
| R-6 | 배포 누락 → 배포본 미발효 (H-6) | F-001 | P1 | install-mac.sh 재배포 + 배포본 grep 검증 (S-9) [SUPERVISOR] |
| R-7 | 용어 일관성 (citation-rules §7) | F-001 | - | 해당 없음 — FE/BE/정책/ERD 영역 쌍 없음 (단일 검증 함수). decision_required 없음 |
