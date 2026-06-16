# PLAN: brain-tool search 공백 무시 매칭

> 작성일: 2026-06-16 | 입력: TASK.md (ANALYSIS.md 없음 — 직접 코드 분석)
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`brain-tool search`가 한국어 복합명사의 띄어쓰기 편차(`"자동 취소"` vs `"자동취소"`)로 검색이 갈리는 문제를, **검색 시점 공백 무시(whitespace-insensitive) 매칭**으로 해결한다. 정규화는 검색 시점의 **휘발성 사본**에만 적용하며 디스크 `.md`·메모리 원본·스니펫 표시용 원문은 불변이다. 단일 정규화 헬퍼(`_norm`)를 4개 비교 필드(title·rel·tags·body)와 스니펫 위치 탐색에 일괄 적용하여 비대칭을 방지한다.

### 1.2 참조 문서 테이블

> citation-rules.md §3.1 공통 스키마. 인라인 인용은 `(→ D-N §N)` 또는 `경로:줄번호` 단축 참조.

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | 수정 대상 — `_score_page`/`_make_snippet`/`cmd_search`/`scan_pages` |
| D-2 | 소스 | test_brain_tool.py | `opal/tools/brain-tool/tests/test_brain_tool.py` | 회귀·신규 테스트 추가 대상 |
| D-3 | 설계 | brain-tool README | `opal/tools/brain-tool/README.md` | §5 search 사용법 + 변경이력 갱신 |
| D-4 | 설계 | PROPOSAL | `~/.opal/tools/brain-tool/PROPOSAL-search-improvement.md` | 원 제안서 (공백 매칭으로 범위 축소 확정 — 토큰화/OR/정규식 비채택) |
| D-5 | 설계 | opal-brain SKILL | `~/.opal/skills/opal-brain/SKILL.md` | `//opbr ask` 후보→선택 흐름 (검색 소비처) |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header / 배포 경계 / 변경이력 / 도구 규칙 |
| D-7 | 환경 | install-mac.sh | `scripts/install-mac.sh:942-965` | tools/ 배포 경로 (R7 재배포 검증) |

### 1.3 핵심 설계 제약 ([MUST] — 재해석 금지)

> citation-rules.md §2.4 / §2.5. PM이 주입한 제약을 산출물에 그대로 옮긴다.

- [MUST] `TASK.md` §확정방향 1: "비교 직전 쿼리와 비교 대상 양쪽의 **휘발성 사본**에서 모든 공백을 제거한 뒤 substring 비교. 디스크 `.md`·메모리 원본·스니펫 표시용 원문은 불변." (→ D-1)
- [MUST] `TASK.md` §확정방향 2: "title·rel·tags·body 비교 모두 동일 정규화(비대칭 방지). 스니펫은 매칭 후에도 **원문(공백 포함) 그대로** 노출."
- [MUST] `TASK.md` §제약: "JSON 출력 계약 유지 — `{\"ok\":..., \"matches\":[{page,title,type,score,snippet}], \"total\":...}` 스키마 불변."
- [MUST] `TASK.md` §제약: "외부 의존성 추가 금지 — PyYAML + stdlib만 사용." (정규화는 stdlib `str.split()`/`"".join()` 또는 `re`로만)
- [MUST] `TASK.md` §제약: "결정론 유지 — 동일 입력 → 동일 결과." / "저장 문서 불변 — `.opal/brain/` 페이지 파일을 수정/마이그레이션하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §구현규칙 배포경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행한다. 변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다." (→ D-6)
- [MUST] `docs/CONVENTIONS.md` §구현규칙 @header: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성/갱신한다." (→ D-6) — 본 변경은 함수 동작만 바꾸므로 @header `description`/`exports` 의미 변화 없음 → 갱신 불요 (단, 검수 시 재확인).
- [MUST] `docs/CONVENTIONS.md` §변경이력: "참조 문서를 변경하면 변경이력 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm`(KST), 변경내용은 태스크 번호(025)를 포함." (→ D-6) — README 변경이력 행 추가 의무.

### 1.4 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 정규화 헬퍼 + 4필드 매칭 (`_norm` + `_score_page`) | R1, R2 | P0 | 없음 |
| F-002 | 스니펫 정규화 대응 + 원문 노출 (`_make_snippet`) | R3 | P0 | F-001 |
| F-003 | 동작 검증 (캡틴 실증 등가 케이스 + 하위호환 회귀) | R4, R5 | P0 | F-001, F-002 |
| F-004 | 문서화 + 재배포 (README §5 + 변경이력 + install) | R6, R7 | P1 | F-001, F-002, F-003 |

### 1.5 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ─┬─ F-003 ── F-004
       └─────────┘
(F-001 정규화 헬퍼가 F-002 스니펫·F-003 검증·F-004 문서의 전제)
```

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `_score_page` 정규화 매칭 (F-001) | 공백 없는 기존 쿼리(`자동취소`)가 정규화 후에도 동일 결과여야 함 — 회귀 위험 | P0 (검색 신뢰도) | L1 단위 (실 파일 기반) | S-3, S-4 |
| H-2 | `_score_page` 정규화 매칭 (F-001) | 비대칭 방향 — 짧은 쿼리가 긴 복합어를 포함해야(넓게), 반대는 안 잡아야(좁게). 양방향으로 매칭되면 정밀도 붕괴 | P1 (검색 정밀도) | L1 단위 | S-5 |
| H-3 | `_make_snippet` 정규화 (F-002) | 정규화 인덱스→원문 위치 역매핑 오류 시 스니펫이 깨진 위치에서 잘리거나 IndexError | P1 (가독성) | L1 단위 | S-6 |
| H-4 | `_score_page` body hit 카운트 (F-001) | body가 공백 제거 기준으로 변경되며 hit 카운트가 달라져 점수/랭킹이 흔들릴 수 있음 | P2 (랭킹) | L1 단위 | S-2 |
| H-5 | JSON 출력 계약 (F-001~F-002) | `matches[].{page,title,type,score,snippet}` + `total` 스키마가 불변이어야 함 | P0 (소비처 `//opbr ask` 파싱) | L1 단위 (스키마 키 검증) | S-7 |
| H-6 | tag/type 필터·query_empty 에러 (F-001) | 필터·에러 경로가 정규화 도입으로 깨질 위험 | P1 | L1 회귀 | S-8 |
| H-7 | 배포본 정합 (F-004) | 소스 수정 후 install 미재배포 시 `~/.opal/` 배포본이 stale → 실제 `//opbr` 동작 불일치 | P0 (배포 경계) | L2 통합 (재배포 후 배포본 실행) | S-9 |

**가설 도출 근거**: 본 태스크는 검색 동작을 바꾸는 로직 변경(self-confirming 위험 영역, 헌법 §4)이므로 H-1~H-7 모두 동작검증(TEST)이 필수다. mock 없는 실 파일 기반 단위 테스트로 L1을 구성하고, R7 배포는 배포본 실행(L2)으로 확인한다.

---

## 2. 기능별 분석

### F-001: 정규화 헬퍼 + 4필드 매칭

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/brain-tool/brain_tool.py` | `_score_page` (4필드 substring 매칭) + 정규화 헬퍼 신규 | 수정 |

#### 2.1.2 현재 구현

`_score_page(pg, query_lower, type_filter, tag_filter)` (`brain_tool.py:561-581`):
- `type_filter` / `tag_filter` 통과 검사 후 점수 산출.
- `title = str(fm.get("title","")).lower()` → `if query_lower in title: score += 5` (`:571-573`)
- `if query_lower in pg["rel"].lower(): score += 3` (`:574`)
- `tags = [str(t).lower() for t in (fm.get("tags") or [])]` → `if any(query_lower in t for t in tags): score += 2` (`:566, :576`)
- `body_lower = (pg["body"] or "").lower()` → `body_hits = body_lower.count(query_lower)` → `score += min(body_hits, 5)` (`:578-580`)
- 즉 **4필드 모두 `query_lower`를 통째로 substring 매칭**하며 비교 직전 `.lower()`만 적용 — 공백 정규화 없음.

`cmd_search` (`:597-626`):
- `query = (args.query or "").strip()` → 빈 문자열이면 `err(command,"query_empty")` (`:602-604`)
- `query_lower = query.lower()` (`:605`) → 이 값을 `_score_page`·`_make_snippet`에 전달.
- `matches` 빌드 시 JSON 키: `page`(`str(pg["path"])`), `title`, `type`, `score`, `snippet` (`:614-620`).
- `scored.sort(key=score, reverse=True)` → `limit` 적용 → `ok(command, query=query, matches=matches, total=len(scored))` (`:622-626`). **결정론·JSON 계약 SSOT.**

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: `cmd_search`가 `_score_page`/`_make_snippet`를 호출. `cmd_search`의 JSON 출력은 `//opbr ask` RAG 흐름의 입력 (→ D-5).
- **하위 의존(피호출자)**: `scan_pages` (`:299-314`)가 `{path, rel, fm, body}`를 메모리 적재 — 본 변경은 이 원본을 **읽기만** 하고 변형하지 않음 ([MUST] §1.3 휘발성 사본).
- **공유 상태**: 없음 (순수 함수). 결정론 보존.
- **관련 테스트**: `test_brain_tool.py` `TestSearch` (`:400-471`) — happy-path 7종. body 기반 검증은 템플릿 placeholder 본문 의존이라 등가 케이스 검증엔 **커스텀 본문 페이지가 필요**(F-003에서 신설).

### F-002: 스니펫 정규화 대응 + 원문 노출

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/brain-tool/brain_tool.py` | `_make_snippet` (스니펫 위치 탐색) | 수정 |

#### 2.2.2 현재 구현

`_make_snippet(body, query_lower)` (`:584-594`):
- `body_lower = body.lower()` → `idx = body_lower.find(query_lower)` (`:586-587`)
- `idx == -1`이면 본문 첫 비어있지 않은 라인 앞 120자 반환 (fallback, `:588-591`)
- 매칭되면 `start = max(0, idx-40)`, `end = min(len(body), idx+80)` → `body[start:end].replace("\n"," ").strip()` (`:592-594`)
- 문제: `body_lower.find(query_lower)`는 **공백 정규화 없는 위치 탐색**이라, 공백 차이로 `idx == -1`이 되면 등가 검색에서 스니펫이 첫 라인 fallback으로 떨어짐(부정확).

#### 2.2.3 영향 범위

- **상위 의존**: `cmd_search:619`가 `_make_snippet(pg["body"] or "", query_lower)` 호출.
- **계약**: 반환은 문자열(스니펫). JSON `snippet` 필드 채움 — 타입/계약 불변.
- **핵심 요구**: 정규화 기준으로 매칭 위치를 찾되, 출력은 **원문(공백 포함)** ([MUST] §1.3). → 정규화 인덱스를 원문 인덱스로 역매핑하는 설계 필요 (§3.2.2).

### F-003: 동작 검증 (등가 케이스 + 회귀)

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/brain-tool/tests/test_brain_tool.py` | `TestSearch`에 등가/비대칭/회귀/스니펫 테스트 추가 | 수정 |

#### 2.3.2 현재 구현

`TestSearch` (`:400-471`):
- `setUp`이 `_init()` + `_add_page("state-tool", entity, ...)` + `_add_page("brain-design", concept, ...)`로 2개 페이지 구성 (`:403-408`).
- `_add_page` (`:127-137`)는 템플릿 본문(placeholder)으로 페이지 생성 — body에 임의 한국어 복합명사가 없음.
- mock 금지 원칙 ([MUST] `test_brain_tool.py:17`): 실제 `brain_tool.py`를 import 호출. KST만 `_mock_kst()` 격리.

#### 2.3.3 영향 범위

- 등가 케이스(`"자동 취소"`≡`"자동취소"`)는 **본문/제목에 해당 복합명사가 있는 페이지가 필요** → 테스트 내에서 커스텀 본문 페이지를 생성해야 함. 두 경로 중 택1:
  - (A) `_add_page`로 title에 `"선정 자동 취소"` 등을 넣어 생성 후, body 본문 정규화 검증이 필요하면 `page_path.write_text`로 본문을 직접 덮어쓰기(tmpdir 격리, 저장 문서 불변 제약은 **프로덕션 `.opal/brain/`** 대상이며 tmpdir 테스트 픽스처는 무관).
  - (B) 신규 헬퍼로 본문 포함 페이지를 작성.
- 권고: 기존 `_add_page` 패턴 재사용(A) — title·body에 등가 복합명사를 심은 픽스처 페이지를 `setUp` 또는 각 테스트에서 추가.

### F-004: 문서화 + 재배포

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/tools/brain-tool/README.md` | §5 search 설명 + 변경이력 표 행 | 수정 |
| 배치 | `scripts/install-mac.sh` (실행) | 소스 → `~/.opal/` 재배포 (코드 수정 아님, 실행만) | - |

#### 2.4.2 현재 구현

- README §5 (`README.md:79-88`): "frontmatter title·tags·본문을 검색해 점수순 관련 페이지를 반환한다 (PM 참조용)." — 공백 무시 매칭 설명 없음.
- 변경이력 (`README.md:127-131`): v1.0 (015) 행만 존재.
- install (`install-mac.sh:942-965`): `install_dir "$opal_dir/tools" "$opal_home/tools"` → tools/ 전체 복사 후 `strip_deploy_md_recursive`로 .md 변경이력 strip. **`.py`는 verbatim 복사** → 소스/배포본 `.py` `diff` 동일 보장 (R7 AC 달성 근거, → D-7).

#### 2.4.3 영향 범위

- README는 사용자/PM이 읽는 문서 — `.md` strip 대상이나 본문은 배포됨.
- install 실행은 파일 수정이 아니라 **검증 행위** — Short Task 파일 카운트에 미포함.

---

## 3. 기능별 설계

### F-001: 정규화 헬퍼 + 4필드 매칭

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/brain-tool/brain_tool.py` | 공통 | `_norm` 헬퍼 신설(`_score_page` 인근, `:560` 부근) + `_score_page` 4필드 비교를 `_norm` 사본 기준으로 전환 | (→ D-1:561-581) |

#### 3.1.2 API·데이터 모델·설계

**정규화 헬퍼 `_norm`** (신규, `_score_page` 직전 배치):

```python
def _norm(s: str) -> str:
    """검색 시점 정규화 — 소문자화 + 모든 공백 제거 (휘발성 사본 전용)."""
    return "".join(str(s).lower().split())
```

- 시그니처: `_norm(s: str) -> str`. 입력 `None` 방어를 위해 호출부에서 `str(...)` 또는 `_norm`이 `str(s)`로 캐스팅.
- `str.split()` (인자 없음)은 **모든 연속 공백류**(스페이스·탭`\t`·개행`\n`·전각 공백 등 `str.isspace()` 대상)를 구분자로 분리 → `"".join(...)`이 공백을 완전 제거. stdlib만 사용([MUST] §1.3 외부 의존성 금지).
- AC: `_norm("자동 취소") == _norm("자동\t취소") == _norm("자동취소") == "자동취소"`, `_norm("Auto Cancel") == "autocancel"` (R1).
- 결정론: 순수 문자열 변환 — 동일 입력 → 동일 출력 ([MUST] §1.3 결정론).

> 설계 선택: `re.sub(r"\s+","",...)` 대신 `"".join(s.split())` 채택 — 동일 결과이며 정규식 컴파일 비용 없고 stdlib 관용구(가독성). 단, 전각 공백(`　`)은 Python `str.split()`이 공백류로 처리하므로 한국어 입력에 안전. (→ D-1)

**`_score_page` 전환** (`:561-581`): `query_lower` 파라미터를 정규화 쿼리로 해석하고, 비교 대상 4필드를 `_norm`으로 정규화한다. 비대칭(substring 포함 방향) 보존을 위해 비교 연산자는 그대로 `in` 유지.

```python
def _score_page(pg, query_norm, type_filter, tag_filter):
    fm = pg["fm"] or {}
    if type_filter and fm.get("type") != type_filter:
        return None
    # tag_filter는 정확 일치(정규화 미적용) — 기존 동작 보존 (H-6)
    tags_raw = [str(t) for t in (fm.get("tags") or [])]
    tags_lower = [t.lower() for t in tags_raw]
    if tag_filter and tag_filter.lower() not in tags_lower:
        return None

    score = 0
    if query_norm in _norm(fm.get("title", "")):
        score += 5
    if query_norm in _norm(pg["rel"]):
        score += 3
    if any(query_norm in _norm(t) for t in tags_raw):   # 가중치 매칭은 정규화
        score += 2
    body_norm = _norm(pg["body"] or "")
    body_hits = body_norm.count(query_norm) if query_norm else 0
    score += min(body_hits, 5)
    return score
```

- **[MUST] 비대칭 보존** — `query_norm in _norm(field)` 방향 유지. 짧은 쿼리(`"자동취소"`)는 긴 복합어 페이지(`"선정자동취소"`)를 잡고(넓게), 긴 쿼리는 짧은 페이지를 못 잡음(좁게) ([MUST] §1.3 캡틴 수용). (→ D-1)
- **tag_filter vs tag 가중치 구분** — `--tag` **필터**는 기존처럼 소문자 정확 일치 유지(공백 정규화 미적용, 회귀 0). tag **가중치(+2)** 매칭만 `_norm` 적용(4필드 일괄 정규화 일관성). 이 분리는 H-6 회귀를 막는다. (→ D-1:566-576)
- body hit는 공백 제거판 `body_norm`에서 `count` — 공백 차이로 분절됐던 hit가 합쳐질 수 있음(H-4). 점수 캡(`min(...,5)`)은 불변.
- 빈 쿼리 가드: `cmd_search`가 이미 `query_empty`로 차단하나, `query_norm`이 빈 문자열일 때 `"" in x`는 항상 True → 방어적으로 `if query_norm else 0` 처리(스니펫·점수 폭주 방지). cmd_search 레벨 가드가 1차 방어선.

#### 3.1.3 환경 변경

해당 없음 (stdlib `str` 메서드만 사용).

#### 3.1.4 배치/마이그레이션

해당 없음 (저장 문서 불변 — `.opal/brain/` 페이지 미수정).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R1 AC | 기능 테스트 | `_norm`이 `"자동 취소"`·`"자동\t취소"`·`"자동취소"`를 모두 `"자동취소"`로, `"Auto Cancel"`을 `"autocancel"`로 변환 |
| TS-002 | R2 AC | 기능 테스트 | body가 공백 제거 기준 hit를 카운트 (분절 hit 합산, H-4) |

### F-002: 스니펫 정규화 대응 + 원문 노출

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 2 | `opal/tools/brain-tool/brain_tool.py` | 공통 | `_make_snippet`을 정규화 위치 탐색 + 원문 위치 역매핑으로 전환 | (→ D-1:584-594) |

#### 3.2.2 API·설계

**`_make_snippet` 전환** — 정규화 인덱스 → 원문 인덱스 역매핑 방식:

```python
def _make_snippet(body, query_norm):
    """정규화 기준으로 매칭 위치를 찾되, 스니펫은 원문(공백 포함)으로 출력."""
    # 원문 각 문자의 "공백 제거 후 정규화 인덱스" 매핑 테이블 구성
    norm_chars = []          # 정규화된 문자열
    orig_index = []          # norm_chars[i] 가 원문에서 위치한 인덱스
    for i, ch in enumerate(body):
        if ch.isspace():
            continue
        norm_chars.append(ch.lower())
        orig_index.append(i)
    body_norm = "".join(norm_chars)

    pos = body_norm.find(query_norm) if query_norm else -1
    if pos == -1:
        # fallback — 첫 비어있지 않은 라인 앞 120자 (기존 동작 보존)
        first = next((ln.strip() for ln in body.split("\n") if ln.strip()), "")
        return first[:120]
    orig_start = orig_index[pos]                      # 원문 매칭 시작 위치
    start = max(0, orig_start - 40)
    end = min(len(body), orig_start + 80)
    return body[start:end].replace("\n", " ").strip()
```

- **[MUST] 원문 노출** — `orig_index`로 정규화 위치를 원문 위치로 역매핑하여 `body[start:end]`(원문, 공백 포함)를 반환. `"자동 취소"`로 검색해도 스니펫에 원문 `"...자동 취소..."`가 공백 포함으로 노출 (R3 AC). (→ D-1)
- fallback 경로(`pos == -1`)는 기존 첫 라인 120자 동작 보존 — 비매칭 페이지도 cmd_search가 `score<=0`으로 이미 제외하므로 실사용 영향 적음.
- 결정론: `body` 순회는 결정적, `find`도 결정적. 비결정 요소 없음.
- 시그니처 변경: 파라미터명 `query_lower`→`query_norm`(의미 명확화). 호출부 `cmd_search:619`도 동일 변수로 갱신.

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-003 | R3 AC | 기능 테스트 | `search "자동 취소"`의 결과 `snippet`에 원문 `"자동 취소"`(공백 포함)가 포함됨 |

**cmd_search 연결 변경** (F-001·F-002 공통): `cmd_search:605` `query_lower = query.lower()` → `query_norm = _norm(query)`로 교체하고, `_score_page(pg, query_norm, ...)`·`_make_snippet(..., query_norm)` 호출로 갱신. `query=query`(원문)은 JSON 출력에 그대로 유지 (계약 불변, H-5).

### F-003: 동작 검증

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 3 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 공통 | `TestSearch`에 등가/비대칭/스니펫/회귀 테스트 + `_norm` 단위 테스트 추가 | (→ D-2:400-471) |

#### 3.3.2 설계

**테스트 추가 전략** (mock 금지, 실 `brain_tool.py` 호출 — `[MUST] D-2:17`):

1. `_norm` 단위 테스트 — `BT._norm` 직접 호출로 R1 AC 검증 (TS-001).
2. 등가 케이스 픽스처 — title/body에 등가 복합명사를 심은 페이지를 `_add_page`로 생성. 본문 정규화 검증이 필요한 케이스는 `result["page"]` 경로에 `write_text`로 본문 덮어쓰기(tmpdir 격리 — 프로덕션 `.opal/brain/` 불변 제약과 무관).
3. **RED-first 트랙** — 등가/비대칭/스니펫 테스트(TS-004~006, S-5,S-6)는 구현 전 RED 상태(FAIL)임을 먼저 확인하고, 구현(F-001·F-002) 후 GREEN 전환을 검증한다 (TEST-SCENARIO.md §RED-first 트랙 참조).
4. 회귀 — 기존 `TestSearch` 7종 + tag/type/limit/query_empty 전부 PASS 유지(TS-007~008).

> 픽스처 예: `_add_page("auto-cancel", "concept", "선정 자동 취소 정책")` 후, 비교 대상으로 `_add_page("auto-cancel-2", "concept", "선정자동취소 정책")` 추가 → `search "선정자동취소"`와 `search "선정 자동 취소"`가 동일 페이지 집합(두 페이지 모두) 반환 검증.

#### 3.3.3 환경 변경

해당 없음 (pytest 기존 스택).

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R4 AC | 기능 테스트 | `"자동 취소"`≡`"자동취소"`가 **동일 페이지 집합** 반환 |
| TS-005 | R4 AC | 기능 테스트 | `"선정 자동 취소"`≡`"선정자동취소"`≡`"선정자동 취소"`가 동일 페이지 집합 반환 |
| TS-006 | R4 (비대칭) | 기능 테스트 | 짧은 쿼리 `"자동취소"`가 긴 복합어 페이지 `"선정자동취소"`를 잡고, 긴 쿼리 `"선정자동취소"`는 `"자동취소"`만 있는 페이지를 못 잡음 |
| TS-007 | R5 AC | 회귀 테스트 | 공백 없는 기존 쿼리(`자동취소`) 결과 불변 + 기존 `TestSearch` 7종 PASS |
| TS-008 | R5 AC | 회귀 테스트 | `--tag`/`--type` 필터, `query_empty` 에러 동작 불변 |
| TS-009 | R2/R3 (계약) | 회귀 테스트 | `matches[]` 키 `{page,title,type,score,snippet}` + `total` 스키마 불변, `ok=true` |

### F-004: 문서화 + 재배포

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 4 | `opal/tools/brain-tool/README.md` | 문서 | §5에 "공백 무시 매칭" 설명 1줄 + 변경이력 표에 025 행 추가 | (→ D-3:79-88, :127-131) |

#### 3.4.2 설계

- README §5 search 절(`:79-88`)에 1줄 추가 — 예: "한국어 복합명사 띄어쓰기 편차를 흡수하기 위해 **검색 시점 공백 무시 매칭**을 적용한다 (쿼리·대상 양쪽의 공백을 제거한 사본으로 비교, 스니펫은 원문 노출)." (R6 AC)
- 변경이력 표(`:127-131`)에 행 추가: `| v1.1 | 2026-06-16 HH:mm | search 공백 무시 매칭 — 한국어 복합명사 띄어쓰기 편차 흡수 (025) |` ([MUST] §1.3 변경이력, → D-6).
- **install 재배포**(R7): `./scripts/install-mac.sh` 실행 → `~/.opal/tools/brain-tool/brain_tool.py`가 소스와 `diff` 동일 확인 + 배포본 `run.sh search "자동 취소"`가 R4 케이스 통과 확인 (실행/검증 행위, 파일 수정 아님). (→ D-7:942-965)

#### 3.4.3 환경 변경

해당 없음.

#### 3.4.4 배치/마이그레이션

install-mac.sh 재배포 실행 (배치 영역, 검증 단계에서 수행).

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R6 AC | 산출물 검사 | README §5에 공백 무시 매칭 설명 1줄 이상 + 변경이력에 025 행 존재 |
| TS-011 | R7 AC | 통합 테스트 | 재배포 후 `diff` 소스/배포본 `.py` 동일 + 배포본 `search "자동 취소"`가 R4 통과 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-003 (RED) | 1 | opal-task-agent | 순차 | RED-first — 테스트 먼저 작성·실패 확인 |
| 2 | F-001, F-002 | 2 | opal-task-agent | 순차 | 동일 파일(brain_tool.py) — 충돌 방지 위해 단일 Step 권장 |
| 3 | F-003 (GREEN) | 3 | opal-task-agent | 순차 | 구현 후 테스트 GREEN 전환 + 회귀 |
| 4 | F-004 | 4, 5 | opal-task-agent / PM 직접 | 순차 | 문서 갱신 + 재배포 검증 |

### 4.2 실행 체크리스트

> 총 5개 Step | Phase 4개 | 실행 모드: 단순

#### Step 1: RED 테스트 작성 (등가·비대칭·스니펫·계약)

- [x] 완료
- **소속 기능**: F-003
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: `TestSearch`에 `_norm` 단위 테스트(TS-001) + 등가 케이스(TS-004,005) + 비대칭(TS-006) + 스니펫 원문 노출(TS-003) + 계약 스키마(TS-009) 테스트를 추가한다. 픽스처는 `_add_page`로 등가 복합명사를 심어 생성(필요 시 `write_text`로 본문 덮어쓰기, tmpdir 격리). 구현 전이므로 등가/스니펫 테스트는 **FAIL(RED)** 이어야 한다.
- **완료 기준**: 신규 테스트가 추가되고, 등가/비대칭/스니펫 테스트가 RED(FAIL)로 확인됨. `_norm` 미존재로 인한 ImportError 발생 시 헬퍼 stub 없이 RED 의미가 성립하도록 테스트는 `getattr(BT,"_norm",None)` 가드 또는 구현 후 활성화 방식으로 작성(권고: 헬퍼 의존 테스트는 구현 직전 작성, 동작 등가 테스트는 즉시 RED).
- **테스트**: TS-001, TS-003, TS-004, TS-005, TS-006, TS-009 (RED 확인)
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: `_norm` 헬퍼 + `_score_page` + `_make_snippet` + `cmd_search` 연결 구현

- [x] 완료
- **소속 기능**: F-001, F-002
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: (1) `_score_page` 직전에 `_norm(s)` 헬퍼 신설(§3.1.2). (2) `_score_page`의 4필드 비교를 `_norm` 사본 기준으로 전환, `--tag` 필터는 정확 일치 유지(§3.1.2, H-6). (3) `_make_snippet`을 정규화 위치 탐색 + 원문 역매핑으로 전환(§3.2.2). (4) `cmd_search:605`의 `query_lower = query.lower()`를 `query_norm = _norm(query)`로 교체하고 두 호출부 인자 갱신. JSON 출력 `query=query`(원문) 유지.
- **완료 기준**: 외부 의존성 추가 없음(stdlib만). JSON 계약 키 불변. @header `description`/`exports` 의미 변화 없음 확인(갱신 불요).
- **테스트**: TS-001, TS-002, TS-003 (구현 동작)
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: GREEN 전환 + 전체 회귀 실행

- [x] 완료
- **소속 기능**: F-003
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: Step 1의 RED 테스트가 GREEN으로 전환됨을 확인하고, 회귀 테스트(TS-007,008)를 추가/확인한다. brain-tool 전체 테스트 스위트(`pytest`)를 실행해 기존 `TestSearch` 7종 + 신규 테스트 전부 PASS 확인.
- **완료 기준**: `pytest opal/tools/brain-tool/tests/test_brain_tool.py` 전체 PASS. 등가/비대칭/스니펫/계약/회귀 모두 GREEN.
- **테스트**: TS-004~009 (GREEN), 전체 회귀
- **실행 방법**: direct
- **의존**: Step 2

#### Step 4: README §5 + 변경이력 갱신

- [ ] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `opal/tools/brain-tool/README.md`
- **작업 내용**: §5 search 절에 공백 무시 매칭 설명 1줄 추가(§3.4.2), 변경이력 표에 `v1.1 | 2026-06-16 HH:mm | ... (025)` 행 추가.
- **완료 기준**: §5에 설명 1줄 이상 + 변경이력 025 행 존재.
- **테스트**: TS-010
- **실행 방법**: direct
- **의존**: Step 3

#### Step 5: install 재배포 + 배포본 검증

- [ ] 완료
- **소속 기능**: F-004
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: (실행) `scripts/install-mac.sh` — 파일 수정 아님
- **작업 내용**: `./scripts/install-mac.sh` 실행 → `~/.opal/tools/brain-tool/brain_tool.py`와 프로젝트 소스 `diff` 동일 확인 → 배포본 `~/.opal/tools/brain-tool/run.sh search "자동 취소"`가 R4 등가 케이스를 통과하는지 확인.
- **완료 기준**: 소스/배포본 `.py` `diff` 무차이, 배포본 search가 R4 통과.
- **테스트**: TS-011
- **실행 방법**: direct
- **의존**: Step 4

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED-first — 테스트가 구현보다 먼저(self-confirming 방지, 헌법 §4) |
| Step 2 → Step 3 | 구현 완료 후 GREEN 전환·회귀 검증 가능 |
| Step 2 (F-001+F-002 단일 Step) | 동일 파일 `brain_tool.py` 수정 — 충돌 방지 위해 묶음 |
| Step 3 → Step 4 → Step 5 | 테스트 GREEN 확인 후 문서화, 그 후 재배포 검증 (배포본은 최종 소스 반영) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | `_norm` 정규화 정확성 | TS-001 | 공백류 전부 제거 + 소문자화, 결정론 |
| F-001 | 4필드 정규화 매칭 (body hit 포함) | TS-002 | 공백 제거 기준 hit 카운트, 비대칭 방향 유지 |
| F-002 | 스니펫 원문 노출 | TS-003 | 정규화 매칭 + 원문(공백 포함) 스니펫 |
| F-003 | 캡틴 등가 케이스 | TS-004, TS-005 | 등가 쌍이 동일 페이지 집합 반환 |
| F-003 | 비대칭 확인 | TS-006 | 짧은 쿼리 넓게 / 긴 쿼리 좁게 |
| F-003 | 하위호환 회귀 | TS-007, TS-008, TS-009 | 기존 동작·필터·에러·JSON 계약 불변 |
| F-004 | README 문서화 | TS-010 | §5 설명 + 변경이력 025 행 |
| F-004 | 재배포 정합 | TS-011 | 소스/배포본 diff 동일 + 배포본 R4 통과 |

### 5.2 회귀 테스트

- [x] 기존 `TestSearch` 7종(title/relevant/no-match/tag/type/limit) 전부 PASS
- [x] `query_empty` 에러, `--tag`/`--type` 필터 동작 불변
- [x] JSON 출력 스키마 `{ok, matches:[{page,title,type,score,snippet}], total}` 불변
- [x] 다른 서브 명령(init/add-page/index/log/sync-header/lint/validate) 테스트 회귀 0

### 5.3 코드/문서 품질

- [x] 프로젝트 컨벤션 준수 (snake_case 함수, @header 블록 유지 — 의미 변화 없으면 갱신 불요)
- [ ] README 변경이력 행 추가 (v1.1, KST 일시, 025) — Step 4 (PM 담당)
- [x] 외부 의존성 미추가 (stdlib `str` 메서드만)
- [x] 결정론 보존 (비결정 요소 미도입)

### 5.4 보안

- [x] 하드코딩 토큰/시크릿 없음 (해당 없음 — 순수 문자열 로직)
- [x] 저장 문서 불변 — `.opal/brain/` 페이지 미수정 (테스트는 tmpdir 격리)
- [ ] 배포 경계 준수 — `~/.opal/` 직접 편집 없이 소스 수정 후 install 재배포 — Step 5 (PM 담당)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 (≤5) |
| 변경 파일 수 | 3개 (brain_tool.py, test_brain_tool.py, README.md) | 단순 (≤3) |
| 모듈 범위 | 단일 모듈 (brain-tool) | 단순 |
| 작업 유형 | 단순 기능 개선 (검색 매칭 로직) | 단순 |
| 외부 의존성 | 없음 (stdlib만) | 단순 |
| **실행 모드** | **단순** | |

> Short Task 범위 내 — 파일 3개, Step 5개. Full Task 에스컬레이션 불요. install 재배포는 실행 행위로 파일 카운트 미포함.

---

## 7. 실행 아키텍처

단순 모드 — 실행 아키텍처(C-1~C-4) 생략. 모든 Step `direct` 실행.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 로직 | Python 3 (stdlib `str`, PyYAML) | trailofbits/modern-python (참조 — 신규 의존성 없어 적용 최소) |
| 테스트 | pytest / unittest (mock 금지, 실 호출) | - |
| 배포 | bash `install-mac.sh` | - |

> 본 변경은 신규 패키지·async·외부 API가 없어 modern-python 스킬의 핵심(uv/ruff/async)은 적용 대상 외. stdlib 관용구(`"".join(s.split())`) + 순수 함수 결정론 원칙만 반영.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | stdlib 문자열 처리 — 외부 문서 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)

§1.2 참조 문서 테이블 참조 (D-1~D-7).

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 공백 정규화로 기존 공백 없는 쿼리 결과가 흔들림 | F-001 | P0 | TS-007 회귀 + 기존 7종 PASS 게이트 (H-1) |
| R-2 | 비대칭이 양방향으로 무너져 정밀도 저하 | F-001 | P1 | TS-006 비대칭 테스트 (`in` 방향 보존, H-2) |
| R-3 | 스니펫 역매핑 인덱스 오류 (IndexError/깨진 위치) | F-002 | P1 | TS-003 + `orig_index` 경계 가드 (H-3) |
| R-4 | body hit 카운트 변화로 랭킹 흔들림 | F-001 | P2 | TS-002 + 점수 캡 불변 확인 (H-4) |
| R-5 | JSON 계약 깨짐 → `//opbr ask` 파싱 실패 | F-001, F-002 | P0 | TS-009 스키마 키 검증, `query=query` 원문 유지 (H-5) |
| R-6 | 재배포 누락 → 배포본 stale | F-004 | P0 | TS-011 diff + 배포본 실행 검증 (H-7) |
| R-7 | 전각 공백(`　`) 미처리 가능성 | F-001 | P2 | Python `str.split()`이 `　` 포함 공백류 처리 — TS-001에 전각 공백 케이스 포함 권장 |

> 용어 일관성(citation-rules §7): FE↔BE/정책↔코드 영역 쌍 해당 없음(단일 Python 도구). decision_required 에스컬레이션 항목 없음.
