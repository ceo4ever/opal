# TASK: brain-tool search 공백 무시 매칭

> 작성일: 2026-06-16 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`brain-tool search`가 한국어 복합명사의 띄어쓰기 편차(`"자동 취소"` vs `"자동취소"`)로 검색이 갈리는 문제를, **검색 시점 공백 무시(whitespace-insensitive) 매칭**으로 해결한다.

## 배경

현재 `search`는 쿼리 문자열을 통째로 substring 매칭하며, 비교 직전 `.lower()`만 적용한다(`opal/tools/brain-tool/brain_tool.py:578`). 한국어는 복합명사의 띄어쓰기가 작성자마다 달라, 쿼리와 본문의 공백 위치가 어긋나면 정작 답 페이지가 존재해도 매칭이 깨진다.

캡틴 실증 요구:
- `"자동 취소"` ≡ `"자동취소"` — 같은 검색 결과를 원함
- `"선정 자동 취소"` ≡ `"선정자동취소"` ≡ `"선정자동 취소"` — 같은 검색 결과를 원함

## 배경 분석 (대화에서 도출)

코드 SSOT 검증 결과 (`opal/tools/brain-tool/brain_tool.py`):

| 함수 | 위치 | 현재 동작 |
|------|------|----------|
| `_score_page` | `:561-581` | `query_lower`(쿼리 전체 소문자)를 title·rel(파일명)·tags·body 4개 필드에 **통째로 substring 매칭**. body는 `body_lower.count(query_lower)`로 연속 문자열 hit만 카운트 |
| `_make_snippet` | `:584-594` | `body_lower.find(query_lower)`로 전체 쿼리 위치를 찾아 스니펫 추출 |
| `cmd_search` | `:597-626` | `query_lower = query.strip().lower()` 한 덩어리를 `_score_page`에 전달 |
| `scan_pages` | `:299-314` | 호출마다 `pages/` 전체 `.md`를 디스크에서 read → `{path, rel, fm, body}` 메모리 적재 (캐시 없음) |

- 검색 대상 4필드 가중치: title +5 / rel(파일명) +3 / tags +2 / body hit ≤+5.
- `//opbr ask`는 `cmd_search` 결과(후보 목록: page·title·score·snippet)를 사용자에게 제시 → 선택 페이지만 Read 주입하는 RAG식 흐름(`~/.opal/skills/opal-brain/SKILL.md` §질의 절차).
- 라이브 재현: `search "brain-tool search 검색"` → 0건 (연속 문자열 부재).

## 확정된 설계 방향 (대화에서 합의)

1. **검색 시점 정규화** — 비교 직전 쿼리와 비교 대상 양쪽의 **휘발성 사본**에서 모든 공백을 제거한 뒤 substring 비교. 디스크 `.md`·메모리 원본·스니펫 표시용 원문은 불변.
2. **4개 비교 필드 + 스니펫 일괄 적용** — title·rel·tags·body 비교 모두 동일 정규화(비대칭 방지). 스니펫은 매칭 후에도 **원문(공백 포함) 그대로** 노출(가독성 유지) → 정규화 인덱스에서 원문 위치로 역매핑하거나 원문 라인 노출.
3. **하위호환 보존** — 공백 없는 쿼리·필드는 현재와 동일 동작(`자동취소` 16건 유지). 공백 포함 쿼리는 공백 제거판으로 매칭 범위가 넓어지는 방향(회귀 0).
4. **범위 제외 (별도 사안)**:
   - 정규식 `--regex` 옵션 — 이번 태스크 제외.
   - 토큰화·stopword·OR 매칭(기존 PROPOSAL §3-A/B) — 정밀도 위험, 캡틴 실요구 아님 → 제외.
   - 기존 brain 54페이지 **문서 마이그레이션 없음** — 검색 시점 정규화이므로 불필요.
   - 인덱싱·임베딩 — 현 규모(54페이지) 과설계, 별도 설계 스파이크로 분리.
5. **대상은 프로젝트 소스** — `opal/tools/brain-tool/brain_tool.py` 수정 후 install 재배포. `~/.opal/` 직접 편집 금지(배포 경계).

## 요구사항

- [ ] **R1. 공백 정규화 헬퍼 신설** — 무엇을: "소문자화 + 모든 공백 제거" 정규화 함수(예: `_norm`)를 추가. 어디에: `opal/tools/brain-tool/brain_tool.py` `_score_page` 인근. 왜: 4필드·스니펫이 공유할 단일 정규화 지점(확정 방향 §1·§2). AC: 함수가 `"자동 취소"`·`"자동\t취소"`·`"자동취소"`를 모두 `"자동취소"`로 변환하고, 영문은 소문자화한다(유닛 테스트로 검증).
- [ ] **R2. `_score_page` 4필드 정규화 매칭** — 무엇을: title·rel·tags·body 비교를 정규화 사본 기준으로 전환. 어디에: `brain_tool.py:561-581`. 왜: 비대칭 방지(확정 방향 §2). AC: `search "자동 취소"`와 `search "자동취소"`가 **동일한 페이지 집합**을 반환하고, body는 공백 제거 기준 hit를 카운트한다.
- [ ] **R3. `_make_snippet` 정규화 대응 + 원문 노출** — 무엇을: 공백 제거 기준으로 매칭 위치를 찾되 스니펫은 원문(공백 포함)으로 출력. 어디에: `brain_tool.py:584-594`. 왜: 가독성 유지(확정 방향 §2). AC: `"자동 취소"`로 검색해도 스니펫에 원문 `"...자동 취소..."`가 공백 포함 형태로 나타난다.
- [ ] **R4. 캡틴 실증 케이스 통과** — 무엇을: 합의된 등가 쌍이 같은 결과를 내도록 보장. 어디에: 동작 검증(TEST). 왜: 캡틴 실요구. AC: `"자동 취소"`≡`"자동취소"`, `"선정 자동 취소"`≡`"선정자동취소"`≡`"선정자동 취소"`가 각각 동일 페이지 집합(또는 동일 상위 랭킹)을 반환.
- [ ] **R5. 하위호환 회귀 테스트** — 무엇을: 공백 없는 기존 쿼리 동작 불변 확인. 어디에: `opal/tools/brain-tool/tests/test_brain_tool.py`. 왜: 회귀 0(확정 방향 §3). AC: `tag`/`type` 필터, `query_empty` 에러, 기존 search 테스트가 모두 PASS.
- [ ] **R6. README search 섹션 갱신** — 무엇을: 공백 무시 매칭 동작을 문서화. 어디에: `opal/tools/brain-tool/README.md` §5 + 변경이력. 왜: 사용법 정합(PROPOSAL §8). AC: §5에 "공백 무시 매칭" 설명 1줄 이상 + 변경이력 표에 태스크 025 행 추가.
- [ ] **R7. install 재배포** — 무엇을: 수정된 소스를 `~/.opal/`에 재배포. 어디에: install 스크립트 경유. 왜: 배포 경계(확정 방향 §5). AC: 재배포 후 `~/.opal/tools/brain-tool/brain_tool.py`와 프로젝트 소스 `diff` 동일, 배포본 `search "자동 취소"`가 R4 케이스를 통과.

## 제약 조건

- 외부 의존성 추가 금지 — PyYAML + stdlib만 사용(형태소 분석기·임베딩 라이브러리 도입 금지).
- JSON 출력 계약 유지 — `{"ok":..., "matches":[{page,title,type,score,snippet}], "total":...}` 스키마 불변.
- 결정론 유지 — 동일 입력 → 동일 결과(비결정 요소 도입 금지).
- 저장 문서 불변 — `.opal/brain/` 페이지 파일을 수정/마이그레이션하지 않는다.
- 배포 경계 — `~/.opal/` 직접 편집 금지, 프로젝트 소스 수정 후 install 재배포.

## 기술 스택

- Python 3 (stdlib `re`, PyYAML) — `opal/tools/brain-tool/` (`.venv` 경유 `run.sh`)
- pytest — `opal/tools/brain-tool/tests/test_brain_tool.py`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | 수정 대상 — `_score_page`/`_make_snippet`/`cmd_search`/`scan_pages` |
| D-2 | 소스 | test_brain_tool.py | `opal/tools/brain-tool/tests/test_brain_tool.py` | 회귀·신규 테스트 추가 대상 |
| D-3 | 설계 | brain-tool README | `opal/tools/brain-tool/README.md` | §5 search 사용법 갱신 |
| D-4 | 설계 | PROPOSAL | `~/.opal/tools/brain-tool/PROPOSAL-search-improvement.md` | 원 제안서(공백 매칭으로 범위 축소 확정) |
| D-5 | 설계 | opal-brain SKILL | `~/.opal/skills/opal-brain/SKILL.md` | `//opbr ask` 후보→선택 흐름(검색 소비처) |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 구현 규칙(@header/배포 경계/도구) |
