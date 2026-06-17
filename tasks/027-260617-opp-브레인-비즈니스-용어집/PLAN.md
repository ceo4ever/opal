# PLAN: OPAL Brain 프로젝트별 비즈니스 용어집(term) 관리 체계

> 작성일: 2026-06-17
> 입력: TASK.md
> 출력: PLAN.md
> 모드: semi-agentic (PLAN 완료 후 캡틴 검토 게이트)

---

## 0. 설계 명제 (PM↔캡틴 수렴 골격)

Brain을 "검색 위키"에서 "업무 언어 번역 계층"으로 격상한다. 진짜 레버는 새 스키마가 아니라 ① 용어가 자동 축적되는 경로(CLOSE ingest 부산물), ② 답변이 번역되는 행동 규칙(advisory), ③ 일관성을 결정론적으로 집행하는 단 한 지점(lint 신규 규칙 2종)이다.

- **수혜자 = 다운스트림 실서비스**: OPAL은 프레임워크 레포라 비즈니스 도메인 용어가 거의 없다. 실수혜자는 `//opbr init`으로 OPAL을 받아 쓰는 다운스트림 실서비스(pointail 등)다. 따라서 변경 대상 = SSOT 3종(schema-template / opal-brain·op-brain-ingest SKILL / citation-rules §8) + brain_tool.py. OPAL 자기 brain에는 **억지 용어집을 만들지 않는다** (TASK 요구사항 #5는 concept 페이지 1장으로 충족).
- **타입명 = `term`** (not glossary): brain은 "1페이지=1엔티티" 패러다임. `glossary`(묶음 뉘앙스)는 충돌하므로 `term`(1페이지=1용어) 채택.
- **척추 = 자동 축적**: 수동 작성에 의존하는 용어집은 죽은 자산이 된다. CLOSE ingest가 `status: draft`로 후보를 등록 → 캡틴/PM 확정 시 `active` 승격. draft는 답변에 쓰지 않는다.
- **정직한 검증**: query의 "업무 언어 번역"은 brain-tool이 강제 못 하는 LLM 행동(advisory)이다. OPAL 레포 내 결정론적 집행 가능 범위 = brain_tool.py 단위 테스트(RED-first): (1) SCHEMA term 타입 동적 로드, (2) draft 상태 필터링, (3) lint 신규 규칙 2종(`term_duplicate`/`alias_collision`).

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL PM 프로필 | `.opal/AGENT.md` | 프로젝트 금지사항, 변경이력 의무(KST+태스크번호), 확정 기준 #2 비즈니스 용어 우선 |
| D-2 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 구조, Brain 컴포넌트 위치 |
| D-3 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §8 비즈니스 용어 우선 원칙 SSOT (024 신설) |
| D-4 | 설계 | opal-brain SKILL | `opal/skills/opal-brain/SKILL.md` | init/ingest/query/lint 동작 규칙 |
| D-5 | 설계 | op-brain-ingest SKILL | `opal/skills/op-brain-ingest/SKILL.md` | CLOSE ingest 워커 규칙·STEP 3 백필 SSOT |
| D-6 | 설계 | Brain schema template | `opal/tools/brain-tool/templates/schema-template.md` | SCHEMA SSOT — §1.5 동적 타입, §2 frontmatter, §4 링크 규칙 |
| D-7 | 지식 | Business terminology principle | `.opal/brain/pages/concept/business-terminology-first-principle.md` | 024 기존 결정 페이지(027 후속의 선행) |
| D-8 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | cmd_lint / cmd_search·_score_page / cmd_add_page / load_page_types / cmd_validate 구현 |
| D-9 | 소스 | brain-tool 단위 테스트 | `opal/tools/brain-tool/tests/test_brain_tool.py` | RED-first 테스트 추가 위치·패턴(실제 import, tmpdir 격리, `_mock_kst`) |
| D-10 | 소스 | page-concept 템플릿 | `opal/tools/brain-tool/templates/page-concept.md` | concept 페이지 구조 참조 |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/harness/citation-rules.md` | 인용 규칙 헌법 — §8 비즈니스 용어 우선 SSOT | O | `citation-rules.md:324-367` (§8 본문·8.1~8.5·변경이력) |
| `opal/tools/brain-tool/templates/schema-template.md` | SCHEMA SSOT — 동적 타입·frontmatter·링크 규칙 | O | `schema-template.md:33-46`(§1.5), `:66-101`(§2), `:136-143`(§4) |
| `opal/skills/opal-brain/SKILL.md` | init/ingest/query/lint 동작 규칙 | O | `opal-brain/SKILL.md:49-92`(init STEP0), `:163-271`(ingest), `:273-329`(query), `:345-352`(lint kind 표) |
| `opal/skills/op-brain-ingest/SKILL.md` | CLOSE ingest 워커 | O | `op-brain-ingest/SKILL.md:48-75`(STEP3), `:76-154`(STEP4) |
| `opal/tools/brain-tool/brain_tool.py` | brain-tool 결정론 집행 CLI | O | `brain_tool.py:768-824`(cmd_lint), `:570-598`(_score_page), `:438-498`(cmd_add_page), `:89-124`(load_page_types) |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | brain-tool 단위 테스트 | O | `test_brain_tool.py:713-791`(TestLint), `:1065-1163`(TestDynamicPageTypes), `:400-619`(TestSearch) |
| `.opal/brain/pages/concept/<신규>.md` | 027 설계 설명 concept 페이지 | O (신규) | TASK #5 / D-7 후속 |

### 현재 상태

1. **SCHEMA §1.5 동적 타입 메커니즘은 이미 존재한다.** brain_tool은 `load_page_types`가 SCHEMA.md §1.5 마크다운 테이블에서 `type`·`category` 컬럼을 정규식으로 파싱해 타입 세트·`TYPE_TO_CATEGORY`·`CATEGORY_ORDER`·`BRAIN_DIRS`를 파생한다 (`brain_tool.py:81-139`). **타입 하드코딩이 없으므로 term 추가는 SCHEMA 테이블에 행을 더하는 것으로 충분**하다. `cmd_add_page`·`cmd_index`·`cmd_validate`가 모두 `load_page_types`를 호출해 동적 타입을 검증/배치한다.
2. **`status` enum은 이미 `active|stale|draft`를 지원한다** (`brain_tool.py:53`, `validate_frontmatter:289-291`). draft 등록 토대는 갖춰져 있다. 단 `cmd_add_page`는 생성 시 `status`를 항상 `"draft"`로 하드코딩한다 (`brain_tool.py:473`) — draft 등록 경로가 도구 차원에서 기본 보장됨.
3. **search는 status를 필터하지 않는다.** `_score_page`는 type/tag 필터만 적용하고 body 포함 4필드(title/rel/tags/body)를 매칭한다 (`brain_tool.py:570-598`). 따라서 "draft term을 답변에 쓰지 않는다"는 현재 도구가 자동 보장하지 못한다 → 027에서 draft 필터 옵션을 search에 추가하여 결정론적으로 집행한다.
4. **lint는 issue kind 확장 구조를 가진다.** `cmd_lint`는 `issues[]`에 `{kind, page, detail}`을 append하며 현재 6종(orphan/stale/broken_link/missing_link/unsourced/contradiction)을 검출한다 (`brain_tool.py:768-824`). frontmatter 임의 키(`aliases` 등) 접근이 자유롭다(`pg["fm"]` 직접 사용). 여기에 term 일관성 2종을 추가하는 것이 일관성 붕괴를 막는 유일한 결정론적 레버다.
5. **citation-rules §8은 024에서 신설**되어 비즈니스 용어 우선 원칙(8.1 적용대상~8.5 검증연결)을 담고 있다 (`citation-rules.md:324-367`). 027은 이 §8을 **재서술 없이 델타만 추가**해야 한다(헌법 거버넌스).
6. **인용 "형식"과 "원칙"의 위치 분리**: 다층 근거 토큰 문법(`POL-xxx`, `ia:{system}:{screen}`)은 brain SCHEMA §4 링크 규칙(현재 3종)에 정의하고, 다층 근거를 언제 쓰는지의 "원칙"·업무 표면 명명·개발자 부록 분리·5W1H 사고 프레임은 citation-rules §8에 추가한다.
7. **배포본 vs 소스 구분**: `.opal/brain/SCHEMA.md`(배포된 brain 인스턴스, v1.0-era, §1.5 미보유)는 수정 대상이 아니다. SSOT는 `opal/tools/brain-tool/templates/schema-template.md`(§1.5 보유)이며 `init` 시 복사된다. 027은 **template SSOT만** 수정한다.
8. **테스트 패턴**: `test_brain_tool.py`는 실제 `brain_tool.py`를 import(`BT`)하여 tmpdir 격리·`_mock_kst()`로 KST 고정·`_call`로 exit_code+result를 추출하는 진짜 테스트(mock 금지)다 (`test_brain_tool.py:36-148`). 신규 테스트는 이 패턴을 그대로 따른다.

### 영향 범위

| 영역 | 영향 | 비고 |
|------|------|------|
| SSOT 문서 3종 + SCHEMA template | term 타입·frontmatter 키·다층 근거 형식·business-first 흐름 추가 | 다운스트림 init 시 전파 |
| brain_tool.py | cmd_lint 2종 신설 + search draft 필터 + (term은 동적 로드라 타입 하드코딩 변경 불필요) | RED-first 트랙 |
| 단위 테스트 | term 동적로드·draft 필터·lint 2종 신규 케이스 | RED→GREEN |
| OPAL 자기 brain | concept 페이지 1장(메타지식)만 추가 — term dogfooding 강제 안 함 | TASK #5 |
| 기존 멱등 규칙(source_ref/code-scan/ingest-scan) | **불변** — 변경 금지(TASK §제약) | 회귀 0 보장 |
| 기존 lint 6종·search 4필드 매칭(025) | **불변** — 신규는 추가만, 기존 동작 보존 | 회귀 0 보장 |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `.opal/brain/pages/concept/brain-business-term-layer.md` | 027 설계(업무 언어 번역 계층·term 타입·draft 자동축적·lint 일관성) 설명 concept 페이지 | TASK #5 / D-7 후속 |

> N-1 파일명은 kebab-case. 본문은 비즈니스 용어·자연어로 서술하고 코드 식별자는 `경로:줄번호` 근거로만 병기한다 (→ D-3 §8). `add-page`로 등록 시 `status`가 `draft`로 생성되므로(`brain_tool.py:473`), 등록 후 캡틴 확정 의미로 `active` 의도를 본문/log에 명시한다(active 승격은 도구 add-page 범위 밖 — index/log는 brain-tool로만 갱신, 본문 status 전환은 후속 운영).

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/tools/brain-tool/templates/schema-template.md` | §1.5 테이블에 `term` 행 추가 + §2에 term frontmatter 선택 키 절 신설(aliases/actors/surfaces) + §4 링크 규칙에 다층 근거 토큰 2종 추가 + 변경이력 027 행 | D-6 `:33-46`,`:66-101`,`:136-143` |
| M-2 | `opal/core/references/harness/citation-rules.md` | §8에 **델타만** 추가(§8.6 다층 근거 원칙·§8.7 업무 표면 명명·§8.8 개발자 부록 분리·§8.9 5W1H 사고 프레임 + 인용 형식은 SCHEMA §4 포인터) + 변경이력 v2.2(027) 행 | D-3 `:324-367` |
| M-3 | `opal/skills/opal-brain/SKILL.md` | init term 채택 가이드(STEP 0) + ingest/ingest-all term 추출·draft 등록 흐름 + query business-first/term 우선 흐름 + lint kind 표에 신규 2종 행 + 변경이력 v1.3(027) 행 | D-4 `:49-92`,`:163-271`,`:273-329`,`:345-352`,`:391-398` |
| M-4 | `opal/skills/op-brain-ingest/SKILL.md` | STEP 3에 draft term 후보 추출(채택 게이트) + STEP 4 term 페이지 작성 규칙 + 변경이력 v1.3(027) 행 | D-5 `:48-75`,`:76-154`,`:237-243` |
| M-5 | `opal/tools/brain-tool/brain_tool.py` | cmd_lint에 `term_duplicate`·`alias_collision` 검출 추가 + cmd_search/_score_page에 draft 필터(`--include-draft` 기본 제외) + ERROR/argparse 정합 | D-8 `:768-824`,`:570-658`,`:1114-1121` |
| M-6 | `opal/tools/brain-tool/tests/test_brain_tool.py` | RED-first 신규 케이스: term 동적로드(TestDynamicPageTypes 확장), draft search 필터(TestSearch 확장), lint term_duplicate/alias_collision(TestLint 확장) | D-9 `:713-791`,`:1065-1163`,`:400-619` |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

의존 받는 쪽(SCHEMA·도구 계약) → 행동 규칙(SKILL) → 메타지식 페이지 순. RED-first 트랙(M-6→M-5)은 코드 한 묶음으로 묶는다.

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | SCHEMA template에 term 타입·frontmatter·다층 근거 형식 추가 | M-1 | 중 |
| 2 | citation-rules §8 델타 추가(원칙·표면·부록·5W1H) | M-2 | 중 |
| 3 | (RED) lint 2종 + draft 필터 실패 테스트 작성 | M-6 | 중 |
| 4 | (GREEN) brain_tool.py lint 2종 + search draft 필터 구현 | M-5 | 중상 |
| 5 | opal-brain SKILL init/ingest/query/lint 규칙 반영 | M-3 | 중 |
| 6 | op-brain-ingest SKILL draft term 추출 규칙 반영 | M-4 | 중 |
| 7 | OPAL brain에 027 설계 concept 페이지 등록 | N-1 | 하 |
| 8 | 변경이력 027 행 일괄 검수 + 검증 명령 실행 | M-1~M-5 | 하 |

### 핵심 설계

> 인라인 인용: `(→ D-N §N)` 또는 `경로:줄번호`. 필수 제약은 [MUST] 포맷.

#### M-1. schema-template.md — term 타입·frontmatter·다층 근거 형식

**(a) §1.5 테이블에 term 행 추가** (→ D-6 §1.5, `schema-template.md:38-44`)

```
| term | 도메인 | 프로젝트 비즈니스 표준 용어 (1페이지=1용어) |
```

- `category`를 `도메인`으로 지정하여, `_get_category_order`가 선두 고정하는 `도메인` 카테고리(`brain_tool.py:127-132`)를 term이 채운다. index.md의 비어있던 "도메인" 섹션이 실제 항목을 갖게 된다.
- [MUST] `schema-template.md` §1.5: "페이지 타입 세트 완전 동적 — init이 origin 분석으로 채택/제외/추가/전면 교체 가능. SCHEMA가 타입 SSOT, brain-tool은 하드코딩 없이 SCHEMA에서 타입 동적 로드." → term은 **채택 게이트가 있는 동적 타입**임을 §1.5 설명 불릿에 명시한다(비즈니스 도메인 프로젝트면 채택, 순수 기술 레포면 제외).
- brain_tool 정규식(`_SCHEMA_TABLE_RE`, `brain_tool.py:81-86`)은 §1.5 테이블 데이터 행을 모두 흡수하므로 term 행 추가만으로 동적 로드된다. **타입 하드코딩 변경 불필요**.

**(b) §2에 term frontmatter 선택 키 절 신설** (→ D-6 §2.2)

term 페이지의 "가벼운 노드" frontmatter 선택 키(필수 키는 기존 §2.1 type/title/created/updated/status 그대로 사용):

| 키 | 타입 | 설명 |
|----|------|------|
| `aliases` | string[] | 별칭·동의 표현 (검색·alias_collision lint 대상) |
| `actors` | string[] | 업무 행위자 (예: PM, 운영자, 구매자) |
| `surfaces` | string[] | 업무 표면 — 용어가 등장하는 화면·프로세스 (명명 규칙: §8.7) |

- `sources`·`related`·`status`는 기존 §2.2 공통 키 재사용(다층 근거는 `sources`에 토큰으로 기재). 본문 = 업무 의미 2~4문장. **그 이상 무겁게 만들지 않는다** (PM 골격 ★2).
- 별칭을 `aliases` frontmatter + 본문에 적으면 search `_score_page`의 body 포함 매칭이 검색 토대를 제공한다(025) — 자동 동의어 그래프·임베딩은 만들지 않는다(과설계 차단).

**(c) §4 링크 규칙에 다층 근거 토큰 추가** (→ D-6 §4, `schema-template.md:136-143`)

현재 3종(교차참조 `[[page]]` / 코드참조 `` `file_path:line` `` / 외부소스 `[[source:id]]`)에 다층 근거 토큰 2종 추가:

| 종류 | 형식 | 용도 |
|------|------|------|
| 정책참조 | `POL-{번호}` | 정책서 조항 근거 |
| IA참조 | `ia:{system}:{screen}` | 화면·정보구조 근거 |

- 이 토큰들은 term의 `sources`에 코드참조와 **병기**되어 "코드 단층"이 아닌 다층 근거를 형성한다. 형식(문법)은 SCHEMA §4에 SSOT로 두고, "언제 다층 근거를 쓰나"의 원칙은 citation-rules §8.6에 둔다(형식/원칙 분리, PM 골격 ★4).

#### M-2. citation-rules.md §8 — 델타만 추가 (헌법 거버넌스)

> [MUST] 기존 §8.1~§8.5를 **재서술하지 않는다**. 027 델타(§8.6~§8.9)만 추가한다. (→ D-3 §8, 산출물 요구)

- **§8.6 다층 근거 원칙**: 비즈니스 용어·결정의 근거는 코드 단층이 아니라 코드(SSOT)·정책서(`POL-xxx`)·IA(`ia:{system}:{screen}`)·설계 문서를 다층으로 병기한다. **언제** 다층 근거를 쓰는가의 원칙만 기술하고, 토큰 **형식**은 brain SCHEMA §4를 포인터로 가리킨다.
- **§8.7 업무 표면(business-surface) 명명**: 용어가 등장하는 화면·프로세스·접점을 가리키는 표면 명명 규칙. brain term의 `surfaces` 키와 정합.
- **§8.8 개발자 부록 분리**: 코드 식별자·enum·API path·레포명은 본문 주어 금지(§8.2 재확인 아님 — 분리 위치 규정 추가)이며 "소스 커버리지"·"개발자 부록" 섹션으로 강등 배치한다(TASK §제약 "개발자 부록 유지").
- **§8.9 5W1H 사고 프레임**: 5W1H는 ingest/query 품질 **점검 틀**로만 사용한다. [MUST] 페이지 섹션 템플릿으로 강제하지 않는다 (→ D-제약, TASK 배경분석 "5W1H는 사고의 틀이지 페이지 양식이 아니다").
- **변경이력**: `| v2.2 | 2026-06-17 | §8.6 다층 근거 원칙 / §8.7 업무 표면 명명 / §8.8 개발자 부록 분리 / §8.9 5W1H 사고 프레임 추가 — 인용 형식은 brain SCHEMA §4 포인터 (027) |`

#### M-3. opal-brain/SKILL.md — init/ingest/query/lint 흐름

- **init STEP 0 (term 채택 가이드)**: STEP 0-2 타입 제안 표(`opal-brain/SKILL.md:62-65`)에 term 행 추가 — "비즈니스 도메인 프로젝트(POL/IA/도메인 용어 존재)면 term 채택, 순수 기술 레포면 제외". 이 판단이 op-brain-ingest 채택 게이트와 연동된다(PM 골격 ★3 정합 조건).
- **ingest/ingest-all term 추출·draft 등록**: 소스별 처리 표(`:212-219`)에 "신규 업무 용어·상태·업무 표면 후보 → `status: draft` term 페이지 등록" 흐름 추가. [MUST] draft는 답변에 쓰지 않으며, 캡틴/PM 확정 시 `active` 승격.
- **query business-first/term 우선** (`:273-329`): 질의 절차에 "관련 term 검색(draft 제외) → 업무 언어로 답변 합성" 단계 추가. [MUST] 이 번역은 brain-tool이 강제 못 하는 **advisory LLM 행동**이며, draft 제외는 search 필터로 결정론 집행됨을 명시(정직한 검증 경계, PM 골격 ★5).
- **진입점 ③ — query 시 미등록 용어 발견→draft 제안 (캡틴 승인 2026-06-17)**: 질의어가 미등록 업무 용어로 판단되면(LLM 판단), `status: draft` term 등록을 **제안**한다. [MUST] 자동 등록 금지 — 노이즈 오등록 방지를 위해 사용자 확정 게이트를 거친다. 사용자 확정 시 해당 term 페이지의 `status`를 `active`로 전환(frontmatter)하고 `index` 재생성 → draft→active **승격 흐름의 빈틈도 메운다**. 질의가 곧 그 프로젝트의 살아있는 업무 어휘라는 점에서 query가 용어 발견의 자연스러운 진입점이 된다(번역 계층 비전 정합).
- **lint kind 표** (`:345-352`): `term_duplicate`(유사 표준명 중복)·`alias_collision`(별칭 충돌) 2행 추가 + 권고 조치 기재.
- **변경이력**: v1.3 (2026-06-17 / 027).

#### M-4. op-brain-ingest/SKILL.md — CLOSE draft term 추출 (채택 게이트)

- **STEP 3 채택 게이트** (`op-brain-ingest/SKILL.md:48-75`): [MUST] term 타입이 **채택된 프로젝트에서만** draft term 후보를 추출한다. 미채택(term이 SCHEMA §1.5에 없는) 프로젝트에서 term 추출 시 `invalid_page_type` SCHEMA 위반 — 추출하지 않는다(opal-brain init 채택 가이드와 연동).
- **STEP 3 포함 기준**에 행 추가: "신규 업무 용어·업무 표면 후보 → `term` (status: draft)".
- **STEP 4 term 작성 규칙** (`:76-154`): term frontmatter 키(aliases/actors/surfaces) + 본문 업무 의미 2~4문장 + 다층 근거 `sources` 병기. [MUST] draft로 등록하고 답변에 쓰지 않는다. 기존 §8 비즈니스 용어 우선 불릿(`:87`)과 정합.
- **변경이력**: v1.3 (2026-06-17 / 027).

#### M-5. brain_tool.py — lint 2종 + search draft 필터 (GREEN)

**(a) cmd_lint 신규 검출 2종** (→ D-8 `brain_tool.py:768-824`)

term 페이지(`fm.get("type") == "term"`)만 대상으로 한다(term 미채택 brain은 term 페이지가 0개 → 신규 검출 0건, 회귀 0):

- `term_duplicate`: 서로 다른 term 페이지의 표준명(`title`) 정규화 비교 — 동일/유사 표준명 중복 시 검출. 정규화는 기존 `_norm`(소문자+공백제거, `brain_tool.py:561-567`) 재사용(결정론). [MUST] 자동 동의어 해소·임베딩 금지 — 정확/공백무시 일치만(과설계 차단).
- `alias_collision`: 한 term의 `aliases` 항목이 다른 term의 `title` 또는 `aliases`와 충돌(동일 정규화) 시 검출.
- 출력 포맷은 기존 `{kind, page, detail}` 구조 유지(`issues[]` append). `issues_count`는 자동 일치(`:824`).

**(b) cmd_search draft 필터** (→ D-8 `brain_tool.py:629-658`, argparse `:1114-1121`)

- `_score_page`에 status 필터 추가: **[R-6 결정: term 한정]** 기본적으로 `type == "term" AND status == "draft"`인 페이지만 검색 결과에서 제외한다. `--include-draft` 플래그로만 포함. **비-term 타입(concept/entity 등)은 draft 여부와 무관하게 기존대로 노출**(add-page가 전 타입을 draft로 생성하므로, 전 타입 적용 시 일반 페이지가 검색서 사라지는 회귀 방지).
- [MUST] 기존 type/tag 필터·body 4필드 매칭·`_norm` 동작 **불변**(025 회귀 0). draft 필터는 신규 분기만 추가.
- argparse `p_srch`에 `--include-draft` (`action="store_true"`) 추가. `make_args` 기본값에 `include_draft=False` 반영 필요(테스트 헬퍼).

**(c) 정합**: ERROR_CODES 신규 키 불필요(lint는 issue 추가, 에러 아님). term은 동적 로드라 타입 상수 변경 불필요.

#### M-6. test_brain_tool.py — RED-first 신규 케이스 (→ D-9)

> [MUST] RED-first: 아래 테스트를 **먼저 작성하여 실패(RED)를 확인**한 후 M-5 구현으로 GREEN 전환한다.

- **TestDynamicPageTypes 확장**: SCHEMA §1.5에 term 행을 넣은 fixture로 `load_page_types`가 term을 반환하는지 + `cmd_add_page --type term`이 통과하는지 검증(기존 `test_load_page_types_from_schema_custom_type` 패턴 재사용, `test_brain_tool.py:1082-1156`). **유의**: 테스트 fixture SCHEMA는 M-1 적용 후의 template을 쓰거나 §1.5에 term 행을 주입한 임시 SCHEMA를 만든다.
- **TestSearch 확장**: **type=term**인 draft 페이지가 기본 검색에서 제외되고 `--include-draft`로 포함되는지 검증. + **type=concept/entity인 draft 페이지는 기본 검색에 노출됨**(R-6 term 한정 회귀 케이스, 필수). `_add_page`는 status=draft로 생성되므로(`brain_tool.py:473`) draft fixture 생성이 자연스럽다. 기존 검색 동작 보존 회귀 케이스 1건 포함.
- **TestLint 확장**: ① 동일 정규화 표준명 term 2개 → `term_duplicate` 검출, ② term A의 alias가 term B의 title과 충돌 → `alias_collision` 검출, ③ term 미존재 brain → 신규 kind 0건(회귀 0).
- 패턴: 실제 `BT` import·tmpdir 격리·`_mock_kst`·`_call` 사용(`test_brain_tool.py:36-148`). [MUST] mock 금지(@header 제약 `:17-18`).

---

## 3. 실행 체크리스트

> 총 8개 Step. Phase A(1-2: 문서 SSOT, 병렬 가능) → Phase B(3-4: RED-first 코드, 순차) → Phase C(5-6: SKILL, 병렬 가능) → Phase D(7-8: 페이지·검수, 순차).

### Step 1: SCHEMA template에 term 타입·frontmatter·다층 근거 형식 추가
- [ ] 완료
- **파일**: `opal/tools/brain-tool/templates/schema-template.md`
- **작업 내용**: §1.5 테이블에 `term | 도메인 | ...` 행 추가 + 동적 채택 게이트 설명 불릿 + §2에 term frontmatter 선택 키 절(aliases/actors/surfaces) 신설 + §4 링크 규칙에 정책참조(`POL-{번호}`)·IA참조(`ia:{system}:{screen}`) 2종 추가 + 변경이력 027 행
- **완료 기준**: §1.5에 term 행 존재, §2에 term 키 3종 정의, §4에 다층 근거 토큰 2종 정의, 변경이력에 KST 일시(`2026-06-17`)+027 행. `_SCHEMA_TABLE_RE`로 파싱 가능한 테이블 형식 유지(헤더+구분선+데이터 행)
- **테스트**: Step 4의 `load_page_types` 테스트가 term을 반환(Step 3 RED→Step 4 GREEN에서 검증)
- **의존**: 없음
- **agent**: opal-task-agent

### Step 2: citation-rules §8 델타 추가
- [ ] 완료
- **파일**: `opal/core/references/harness/citation-rules.md`
- **작업 내용**: §8.6 다층 근거 원칙(형식은 SCHEMA §4 포인터) + §8.7 업무 표면 명명 + §8.8 개발자 부록 분리 + §8.9 5W1H 사고 프레임([MUST] 페이지 템플릿 강제 금지) 추가 + 변경이력 v2.2(027) 행
- **완료 기준**: §8.1~§8.5 원문 불변(재서술 0), §8.6~§8.9 신규 절 존재, 5W1H 페이지 템플릿 강제 금지 명문화, 변경이력 v2.2 행
- **테스트**: 정적 검토 — §8.1~8.5 diff 0줄(추가만), 5W1H 강제 금지 문구 존재
- **의존**: 없음 (단 §8.6 토큰 형식 포인터는 Step 1 §4와 정합 — Step 1 선행 권장)
- **agent**: opal-task-agent

### Step 3: (RED) lint 2종 + draft 필터 실패 테스트 작성
- [x] 완료
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: TestDynamicPageTypes에 term 동적로드 케이스, TestSearch에 draft 제외/`--include-draft` 포함 케이스, TestLint에 `term_duplicate`·`alias_collision`·회귀(term 미존재 0건) 케이스 추가. `make_args` 기본값에 `include_draft=False` 추가
- **완료 기준**: 신규 테스트가 **실패(RED)**함을 확인 — 미구현 기능(draft 필터·lint 2종)이 없으므로 assert 실패. 실제 `BT` import·tmpdir·`_mock_kst` 패턴 준수, mock 금지
- **테스트**: `cd opal/tools/brain-tool && python -m pytest tests/test_brain_tool.py -k "term or draft or alias" -v` → 신규 케이스 FAIL, 기존 케이스 PASS
- **의존**: Step 1 (term fixture가 SCHEMA §1.5 term 행에 의존)
- **agent**: opal-be-agent

### Step 4: (GREEN) brain_tool.py lint 2종 + search draft 필터 구현
- [x] 완료
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: cmd_lint에 term 대상 `term_duplicate`(title 정규화 중복)·`alias_collision`(alias↔title/alias 충돌) 검출 추가(`_norm` 재사용). _score_page/cmd_search에 draft 제외 필터 + argparse `--include-draft` 추가
- **완료 기준**: Step 3 신규 테스트 전부 GREEN + 기존 전체 테스트 회귀 0. 기존 lint 6종·search 4필드 매칭·멱등 규칙 불변. term 미채택 brain에서 신규 kind 0건
- **테스트**: `cd opal/tools/brain-tool && python -m pytest tests/test_brain_tool.py -v` → 전체 PASS
- **의존**: Step 3 (RED 확인 후 GREEN)
- **agent**: opal-be-agent

### Step 5: opal-brain SKILL init/ingest/query/lint 규칙 반영
- [ ] 완료
- **파일**: `opal/skills/opal-brain/SKILL.md`
- **작업 내용**: init STEP 0 타입 제안 표에 term 채택 가이드 행, ingest/ingest-all에 draft term 추출 흐름, query에 business-first/term 우선(draft 제외, advisory 경계 명시) 흐름 **+ 진입점 ③(미등록 업무 용어 발견 시 draft term 등록 제안 → 사용자 확정 시 status active 전환 + index 재생성. 자동 등록 금지)**, lint kind 표에 `term_duplicate`·`alias_collision` 2행 + 변경이력 v1.3(027) 행
- **완료 기준**: 4개 모드 모두 term 흐름 반영, [MUST] draft 답변 제외·번역 advisory 경계 명시, **진입점 ③ query 용어 발견→draft 제안→확정 시 active 승격 흐름 명문화(자동 등록 금지 게이트)**, lint 표 8종(기존 6 + 신규 2), 변경이력 v1.3 행
- **테스트**: 정적 검토 — 4모드 term 규칙 존재, lint 표 행 수 8, citation-rules §8/schema §4 포인터 정합
- **의존**: Step 1, Step 4 (도구 계약 확정 후 SKILL이 그것을 가리켜야 정합)
- **agent**: opal-task-agent

### Step 6: op-brain-ingest SKILL draft term 추출 규칙 반영
- [ ] 완료
- **파일**: `opal/skills/op-brain-ingest/SKILL.md`
- **작업 내용**: STEP 3에 term 채택 게이트([MUST] 채택 프로젝트만 추출) + 포함 기준 행(신규 업무 용어→term draft), STEP 4에 term 작성 규칙(aliases/actors/surfaces + 업무 의미 2~4문장 + 다층 근거 sources) + 변경이력 v1.3(027) 행
- **완료 기준**: 채택 게이트 [MUST] 명문화, term 포함 기준·작성 규칙 존재, draft 등록 규칙, §8 비즈니스 용어 우선 정합, 변경이력 v1.3 행
- **테스트**: 정적 검토 — 채택 게이트·term 작성 규칙·draft 규칙 존재, opal-brain init 채택 가이드와 연동 정합
- **의존**: Step 1, Step 5 (SCHEMA term + opal-brain 채택 가이드와 연동)
- **agent**: opal-task-agent

### Step 7: OPAL brain에 027 설계 concept 페이지 등록
- [ ] 완료
- **파일**: `.opal/brain/pages/concept/brain-business-term-layer.md` (add-page로 생성)
- **작업 내용**: `~/.opal/tools/brain-tool/run.sh add-page pages/concept/brain-business-term-layer.md --type concept --title "Brain 업무 언어 번역 계층(term)" --tags "brain,citation-rules,term" --sources "task:027"` 호출 + 본문(비즈니스 용어 서술, 코드는 `경로:줄번호` 근거) 작성. 관련 링크 `[[business-terminology-first-principle]]`. 이후 `index` + `log --op ingest` 호출
- **완료 기준**: 페이지 생성 + index/log brain-tool로 갱신. [MUST] 본문 비즈니스 용어 우선(→ D-3 §8), term dogfooding 강제 안 함(concept 1장만). [MUST] index.md/log.md는 brain-tool로만 갱신(LLM 직접 편집 금지)
- **테스트**: `~/.opal/tools/brain-tool/run.sh lint` 실행 → 신규 치명 이슈 0(orphan 회피 위해 D-7 페이지와 상호 링크)
- **의존**: Step 1~6 (설계 확정 후 메타지식 기록)
- **agent**: opal-task-agent

### Step 8: 변경이력 027 행 일괄 검수 + 검증 명령 실행
- [ ] 완료
- **파일**: M-1~M-5 (schema-template / citation-rules / opal-brain / op-brain-ingest / brain_tool.py는 코드라 @header description 갱신 여부만 확인)
- **작업 내용**: 변경된 각 .md 문서(M-1~M-4) 변경이력 표에 KST 일시(`2026-06-17`)+027 행 존재 확인. `brain-tool validate` + `brain-tool lint` + 전체 단위 테스트 실행
- **완료 기준**: 4개 .md 문서 변경이력 027 행 존재(→ D-1 §변경이력 의무), `brain-tool validate` valid=true, `lint` 치명 이슈 0, 전체 pytest PASS
- **테스트**: `~/.opal/tools/brain-tool/run.sh validate && ~/.opal/tools/brain-tool/run.sh lint && cd opal/tools/brain-tool && python -m pytest tests/test_brain_tool.py -v`
- **의존**: Step 1~7
- **agent**: PM 직접 (검수 게이트)

---

## 4. QA 체크리스트

### 기능 테스트
- [x] `load_page_types`가 SCHEMA §1.5 term 행을 동적 로드하여 term을 반환한다 (타입 하드코딩 없음 확인)
- [x] `add-page --type term`이 통과하고 페이지가 `pages/term/`(또는 동적 디렉토리)에 생성된다
- [x] search가 기본적으로 draft 페이지를 제외하고, `--include-draft`로 포함한다
- [x] lint가 동일 정규화 표준명 term 중복을 `term_duplicate`로 검출한다
- [x] lint가 alias↔title/alias 충돌을 `alias_collision`으로 검출한다
- [x] term 미채택 brain에서 신규 lint kind 0건 (회귀 0)
- [x] 기존 lint 6종·search 4필드 매칭(025)·멱등 규칙(source_ref/ingest-scan) 동작 불변
- [x] 전체 단위 테스트 PASS, `brain-tool validate` valid=true

### 일관성 테스트
- [ ] term 타입 이름이 SCHEMA·opal-brain·op-brain-ingest·brain_tool 테스트 전반에서 `term` 단일 토큰으로 통일(`glossary` 미혼용)
- [ ] 인용 "형식"(POL/ia 토큰)은 SCHEMA §4에만, "원칙"은 citation-rules §8.6에만 — 위치 분리 정합
- [ ] opal-brain init term 채택 가이드 ↔ op-brain-ingest 채택 게이트 연동 정합(미채택 시 추출 안 함)
- [ ] frontmatter 키(aliases/actors/surfaces)가 SCHEMA §2와 op-brain-ingest STEP 4에서 동일 명칭 사용
- [ ] §7.1 영역 쌍(정책서↔코드 등) 신규 용어 불일치 발견 시 §리스크 기재(현재 발견 없음)

### 문서 품질
- [ ] citation-rules §8.1~§8.5 원문 불변(재서술 0, 추가만)
- [ ] 5W1H가 사고 프레임으로만 — 페이지 섹션 템플릿 강제 금지 명문화
- [ ] term 본문이 비즈니스 용어 우선(코드 식별자 본문 주어 금지, → D-3 §8)
- [ ] 변경된 4개 .md 문서에 KST 일시+027 변경이력 행 존재
- [ ] N-1 concept 페이지가 비즈니스 용어로 서술되고 D-7과 상호 링크(orphan 회피)
- [ ] 한국어 본문 + 영어 frontmatter 키/파일명, kebab-case 준수

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | query "업무 언어 번역"은 brain-tool이 집행 못 하는 advisory LLM 행동 → self-confirming 검증 위험 | 기능이 "그럴듯한 말"에 그칠 수 있음 | 결정론적 집행 가능 범위(term 동적로드·draft 필터·lint 2종)만 단위 테스트로 검증. 번역 품질은 PLAN/SKILL에 "advisory + 다운스트림 실증"으로 경계 명시 (PM 골격 ★5) |
| R-2 | 같은 개념을 다른 표현으로 등록하는 일관성 붕괴(@header 커버리지 2파일 전철) | 용어집이 신뢰 못 할 자산이 됨 | lint `term_duplicate`/`alias_collision`을 유일한 결정론적 레버로 추가. 자동 동의어 그래프·임베딩은 만들지 않음(과설계 차단) |
| R-3 | term 미채택(순수 기술 레포)에서 op-brain-ingest가 term 추출 시 `invalid_page_type` SCHEMA 위반 | CLOSE ingest 실패 가능 | 채택 게이트 [MUST] — term이 SCHEMA §1.5에 채택된 프로젝트에서만 추출. opal-brain init 채택 가이드와 연동 |
| R-4 | 배포본 `.opal/brain/SCHEMA.md`(v1.0, §1.5 미보유)와 SSOT template 혼동 | 잘못된 파일 수정 | [MUST] template SSOT(`opal/tools/brain-tool/templates/schema-template.md`)만 수정. `~/.opal/` 배포본·`.opal/brain/SCHEMA.md` 직접 수정 금지 (→ D-1 §제약) |
| R-5 | search `--include-draft` 추가 시 `make_args` 기본값 미반영으로 기존 테스트 AttributeError | 기존 테스트 회귀 | Step 3에서 `make_args` 기본값 `include_draft=False` 선반영 후 RED 확인 |
| R-6 | cmd_add_page가 status를 항상 draft로 하드코딩(`brain_tool.py:473`) → N-1 concept 페이지도 draft 생성 | concept 페이지가 답변 검색서 제외될 수 있음(draft 필터가 term 외 타입에도 적용 시) | **[결정 2026-06-17 캡틴 승인: term 한정]** draft 검색 필터는 `type==term`에만 적용. 비-term 타입은 draft여도 검색 노출 → 일반 ingest 페이지(N-1 concept 포함) 가시성 회귀 0. Step 3 회귀 테스트로 검증 |

---

> **검증 경계 명시 (정직한 검증)**: 이 PLAN의 결정론적 집행 대상은 (1) SCHEMA term 동적 로드, (2) draft 상태 search 필터, (3) lint term_duplicate/alias_collision 2종이다. query의 업무 언어 번역·다층 근거 사용·term draft 등록 판단은 SKILL prose가 규율하는 **반자동 LLM 행동(advisory)**이며 OPAL 레포 내 실증이 불가하다(OPAL은 시연할 업무 용어가 없음). 실증은 다운스트림 비즈니스 도메인 프로젝트에서 이뤄진다.
