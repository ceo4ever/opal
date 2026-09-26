---
template: sdlc-v2
task: 143-260918-opds-스킬-문서-사이드바
created: 2026-09-18 20:22
branch: feat/143-opds-스킬-문서-사이드바
base: feat/140-opdw-스킬-문서-화면
---

# PLAN: OPAL Docs 스킬 문서 사이드바·README 렌더

## 참조 문서

| # | 유형 | 문서/소스 | 경로 | 참조 이유 |
|---|------|-----------|------|-----------|
| D-1 | 기획 | TASK.md | `tasks/143-260918-opds-스킬-문서-사이드바/TASK.md` | AC-1~AC-9, C-1~C-8 요구 SSOT |
| D-2 | 회고 | 140 DONE.md | `tasks/140-260917-opdw-스킬-문서-화면/DONE.md` | 승계 자산 목록·미달성 사유(상세 본문 공백)·유지한 경계 |
| D-3 | 지식 | brain concept | `.opal/brain/pages/concept/skill-md-body-is-freeform-not-structured-slots.md` | 본문 heading 슬롯 추출이 성립하지 않는다는 전수 실측 근거 |
| D-4 | 지식 | brain concept | `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md` | fixture가 실재를 대표하지 못해 140에서 결함 5회 반복 — 실자산 대조 의무 근거 |
| D-5 | 설계 | PROJECT.md | `docs/PROJECT.md` §프로젝트 구성(236-244행), 191행 | 영역↔경로↔전문 에이전트 매핑, Console 8개 화면 기재 |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` §배포 경계(256행~), §커밋 규칙(175행~), §Citation Rules(229행~) | 배포 경계·커밋 형식·인용 의무 |
| D-7 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` 351-359행 | 현재 OPAL Docs 화면·엔드포인트·BE/FE 구성 기재 — 이번 변경의 갱신 대상 |
| D-8 | 소스 | skill_docs_adapter.py | `dashboard/backend/adapters/skill_docs_adapter.py` | 레이아웃 해석(51행)·물리 경로 해석(82행)·corpus index(131행)·`_display_group`(380행) |
| D-9 | 소스 | skill_parser.py | `dashboard/backend/parsers/skill_parser.py` | frontmatter 파싱(46행~)과 heading 슬롯 추출(118-196행) — 후자가 폐기 대상 |
| D-10 | 소스 | docs_skills.py | `dashboard/backend/routers/docs_skills.py` | `get_skill_docs_corpus_root`(32행), GET 2개(55·74행), 오류 매핑(41행) |
| D-11 | 소스 | models.py | `dashboard/backend/models.py` 498-600행 | 공개 응답 모델 — `SkillDetailResponse`(568행)가 슬롯 필드 7종을 노출 |
| D-12 | 소스 | markdown-view.tsx | `dashboard/frontend/src/components/markdown-view.tsx` 298-332행 | remark-gfm + rehype-slug만 사용, raw HTML 플러그인 없음 |
| D-13 | 소스 | docs 화면·라우팅 | `dashboard/frontend/src/pages/docs/`, `src/router.tsx` 38-39행, `src/components/app-shell/AppShell.tsx` 97행 | 교체 대상 화면과 유지 대상 메뉴·라우트 |
| D-14 | 소스 | 레지스트리 | `opal/core/references/opal-skills-registry.json` | 그룹 10종 55 엔트리, `paths`·`stage`·`dispatched_by`·`pipeline` 필드 |
| D-15 | 소스 | 백엔드 테스트 | `dashboard/backend/tests/test_skill_docs.py`, `test_skill_docs_layout.py`, `tests/fixtures/skill_docs_corpus/**` | 유지·수정·폐기 판정 대상 |
| D-16 | 소스 | FE 빌드 가드 | `dashboard/frontend/src/lib/api-env-files.test.ts:49-57` | `npm run build`가 저장소 `dist/`를 남기면 실패 — 검증 순서 고정 근거 |
| D-17 | 계약 | guards.md | `~/.opal/references/harness/guards.md` §구현 금지 원칙 | 승인 전 구현 금지 |
| D-18 | 계약 | citation-rules.md | `~/.opal/references/harness/citation-rules.md` §4 | PLAN 인용 의무 |
| D-19 | 계약 | .opal/AGENT.md | `.opal/AGENT.md` §금지사항 | `~/.opal/` 직접 편집 금지 |
| E-1 | 실측 | corpus 전수 측정 | 본 태스크 20:22 실행, `build_skill_docs_corpus` 직접 호출 | 아래 §Approach 실측표의 근거(E1 실행 관측) |

**[MUST]** `~/.opal/references/harness/guards.md` §구현 금지 원칙: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." — 본 PLAN은 설계 산출물이며 본 문서 외 어떤 파일도 생성·수정하지 않았다.

**[MUST]** `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." (동일 규정: `docs/CONVENTIONS.md` §배포 경계 "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다.") — 모든 Work item의 변경 대상은 프로젝트 경로이며 배포는 W-7 사용자 확인 단계가 소유한다.

**[MUST]** `tasks/143-260918-opds-스킬-문서-사이드바/TASK.md` §Constraints C-3: "본문은 파싱해 슬롯으로 쪼개지 않고 Markdown 원문 그대로 렌더한다. `README.md`가 없으면 `SKILL.md` 본문으로 폴백해 어떤 스킬도 빈 화면이 되지 않는다." — DEC-1·DEC-2·DEC-3이 이 제약의 구현 계약이다.

**[MUST]** `tasks/143-260918-opds-스킬-문서-사이드바/TASK.md` §Constraints C-5: "기존 Console의 읽기 전용 원칙을 유지하고 이 화면에서 스킬 실행·파일 수정·설치를 수행하지 않는다." — 공개 표면은 기존 GET 2개를 유지하고 메서드를 추가하지 않는다(DEC-9).

**[MUST]** `docs/CONVENTIONS.md` §Citation Rules: "`[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리."

**[MUST]** `docs/CONVENTIONS.md` §커밋 규칙: "하나의 태스크 = 하나의 커밋 (원칙)", 형식 `{type}({scope}): {한국어 설명}`, scope는 태스크 번호 — 이번 커밋은 `feat(143): ...` 형식이다.

## Approach

태스크 140은 백엔드 corpus 해석기까지는 올바르게 만들었고 표시 계층만 틀렸다(→ D-2 "달성한 것"/"달성하지 못한 것"). 따라서 이번 태스크는 **corpus 해석기 재사용 + 표시 계층 교체**이며 재작성이 아니다. 교체 대상은 세 곳뿐이다.

1. **본문 산출 방식** — `skill_parser.py`의 heading 슬롯 추출(D-9:118-196행)을 제거하고, 스킬 폴더의 `README.md` 원문(없으면 `SKILL.md` 본문)을 그대로 실어 보내는 본문 로더로 대체한다.
2. **노출 집합 판정** — 사이드바에 보일 스킬인지를 서버가 레지스트리로부터 파생해 응답 필드로 내려보낸다. 프런트엔드는 상수를 갖지 않는다(C-2).
3. **화면 구조** — 카드 그리드 + 검색 + 필터를 좌측 그룹 사이드바 + 우측 Markdown 본문으로 교체한다.

### 실측 근거 (E-1, 2026-09-18 20:22 실행)

`build_skill_docs_corpus`를 소스 저장소 루트와 `~/.opal` 두 corpus root에 직접 호출해 얻은 값이다. 두 root의 결과는 모든 항목에서 동일했다.

| 관측 | 값 |
|------|-----|
| canonical 총계 | 55 |
| `display_group` 분포 | `pilot` 12 · `operator` 14 · `standalone` 8 · `internal-stage` 21 |
| 비-internal 소계 | 34 |
| `opal-pilot-dev-short` 제외 후 | **33** (AC-1 요구치와 일치) |
| `README.md` 보유 | **55/55** (두 root 모두, 누락 0) |
| `usage_markdown` 채워짐 | 0/55 |
| `when_to_use_markdown` | 1/55 |
| `quick_start` / `arguments` / `options` / `examples` / `use_cases` | 각 0/55 |
| `pipeline` | 10/55 |
| `description` | 55/55 |
| 레지스트리 `paths[0]` 폴더명 ≠ `name` | **1건** — `opal-pilot-dev-short` 단독 |

마지막 행이 이번 설계의 핵심 발견이다. `opal-pilot-dev-short`는 레지스트리에서 자기 `paths`가 다른 스킬 폴더(`opal-pilot-dev/SKILL.md`)를 가리키는 유일한 엔트리다(→ D-14). 즉 "실행 본체가 다른 스킬에 있는 라우팅 프로필 엔트리"라는 사실이 레지스트리 데이터만으로 판정 가능하며, 이름을 하드코딩하지 않고 C-2를 지킬 수 있다.

### 검증 전략

**[MUST]** `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md` §대응 원칙: "단위 테스트 통과만으로는 충분하지 않다. 도구가 실데이터에서 end-to-end로 동작하는지 직접 실행해서 확인한다." 140에서 같은 맹점이 한 태스크 안에 5회 반복됐다(→ D-4). 따라서 fixture 테스트와 별도로 **실제 55개 자산 대상 단언**을 테스트 코드에 고정한다(W-1의 실자산 항목, W-6·W-7의 실측). 합성 fixture 단독 GREEN을 완료 근거로 쓰지 않는다.

RED-first 경계: 공개 계약이 바뀌는 지점(상세 응답 본문 필드, 폴백 표시, 노출 집합 필드)과 새 화면 동작을 각각 실패 테스트로 먼저 고정한 뒤 구현한다(W-1·W-2가 W-3·W-4에 선행).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|------|--------------|----------------|
| **DEC-1. 상세 응답에 본문 원문 필드를 추가한다** | `SkillDetailResponse`에 `body` 객체를 추가한다: `{ markdown: string \| null, origin: "readme" \| "skill_md" \| null, source_path: string \| null }`. `markdown`은 파일 원문 그대로이며 서버는 heading을 해석하지 않는다. `origin`은 어느 파일에서 왔는지, `source_path`는 `opal/skills/{canonical}/README.md` 같은 **상대 경로**다(절대경로 금지 — 기존 계약 유지, D-10 @header). 목록 응답(`SkillCatalogItem`)에는 본문을 싣지 않는다. | **[MUST]** D-1 §Constraints C-3 "본문은 파싱해 슬롯으로 쪼개지 않고 Markdown 원문 그대로 렌더한다". 슬롯 추출은 전수 0/55로 사용자 가치가 없음이 확정됐다(→ E-1 실측, D-3). 목록에서 본문을 제외하는 이유는 55개 파일 전문을 한 응답에 싣지 않기 위함이며, 사이드바는 이름·alias·그룹만 필요하다(AC-1). |
| **DEC-2. 폴백은 README → SKILL.md 본문 2단이며 사용자에게 고지한다** | `README.md`가 존재하면 `origin="readme"`. 없으면 `SKILL.md`에서 YAML frontmatter를 제거한 본문을 싣고 `origin="skill_md"`. 둘 다 없거나 본문이 공백이면 `markdown=null`, `origin=null`이고 HTTP는 여전히 200이다(기존 DEC-1 200-partial 계약 유지, → D-15 `test_s6_source_missing_returns_200_partial`). 프런트엔드는 `origin="skill_md"`일 때 본문 위에 폴백 안내를 표시하고, `origin=null`일 때만 부재 상태를 표시한다. | **[MUST]** D-1 §Constraints C-3 후단 "`README.md`가 없으면 `SKILL.md` 본문으로 폴백해 어떤 스킬도 빈 화면이 되지 않는다"와 AC-4 "폴백 사실을 사용자에게 알린다". 현재 README는 55/55로 폴백 경로가 실데이터에 없으므로(→ E-1), 폴백은 신규 스킬 추가 시를 위한 안전장치이며 fixture로만 검증 가능하다 — 이 사실을 W-1 fixture 설계에 명시한다. frontmatter 제거는 이미 `_split_frontmatter`가 수행한다(D-9:111행). |
| **DEC-3. 슬롯 필드 7종을 공개 계약과 파서에서 제거한다** | `SkillDetailResponse`에서 `usage_markdown`·`when_to_use_markdown`·`quick_start`·`arguments`·`options`·`examples`·`use_cases`를 삭제한다. `models.py`의 `ArgumentItem`·`ExampleBlock`은 다른 사용처가 없으면 함께 삭제한다. `skill_parser.py`의 `_split_sections`·`_parse_items`·`_parse_examples`·`_parse_use_cases`·`_parse_quick_start`와 관련 정규식·상수를 제거하고, 파서는 frontmatter(`name`·`description`)·`content_hash`·본문 원문만 반환한다. `description`(55/55)·`pipeline`(10/55)·`related_skills`·`source`·`resolved_from`은 **유지**한다. | 필드를 남기면 C-3이 금지한 슬롯 파싱 코드가 계속 살아 있어야 하고, 전수 0/55인 죽은 필드가 계약에 남아 다음 소비자를 오도한다(→ D-3 "heading 매칭 기반 자동 추출은 사실상 작동하지 않는다"). 폐기한 대안(필드를 남기고 항상 null 반환)은 C-3 위반 코드를 존치시키면서 계약만 거짓으로 만든다. `description`은 레지스트리 유래라 슬롯 파싱과 무관하고, `pipeline`은 `references/pipeline.json`이라는 기계가독 SSOT에서 온다(D-8:406행) — 둘 다 C-3의 대상이 아니다. |
| **DEC-4. 사이드바 노출 여부는 서버가 레지스트리에서 파생해 `listed` 필드로 내려보낸다** | 목록·상세 응답에 `listed: boolean`을 추가한다. 판정 규칙은 두 조건의 AND다. ① `display_group != "internal-stage"` ② 레지스트리 엔트리의 `paths[0]` 마지막 스킬 폴더명이 canonical `name`과 같다. ②를 만족하지 못하는 엔트리는 실행 본체가 다른 스킬에 있는 라우팅 프로필이므로 독립 문서로 노출하지 않는다. 프런트엔드는 `listed===true`만 사이드바에 렌더하고 그룹·스킬 이름 상수를 두지 않는다. `listed=false`인 스킬도 `/docs/skills/{id}` 직접 접근 시 정상 200으로 문서를 반환한다. | **[MUST]** D-1 §Constraints C-2 "스킬 메타데이터를 프론트엔드에 하드코딩하지 않고 레지스트리와 각 스킬 폴더의 파일에서 읽기 전용으로 파생한다". ①은 기존 `_display_group`(D-8:380행)이 `stage`/`dispatched_by`로 이미 파생하는 값이라 새 데이터가 필요 없다. ②는 실측상 `opal-pilot-dev-short` 단 1건에만 해당하며(→ E-1 마지막 행), 이름 하드코딩 없이 AC-5의 "`opal-pilot-dev-short` 제외"를 만족한다. 33 = 55 − 21 − 1로 AC-1과 일치한다. 폐기한 대안(FE 상수 배열 `["pilot","operator","standalone"]` + 이름 제외 목록)은 C-2 정면 위반이고, 새 파일럿 스킬 추가 시 FE 수정을 강제한다. AC-5 후단 "URL로 직접 접근하면 문서를 읽을 수 있다"는 `listed`가 조회를 차단하지 않기 때문에 자동 성립한다. |
| **DEC-5. 검색·필터는 화면에서만 제거하고 백엔드 파라미터는 유지한다** | `GET /api/docs/skills`의 `q`·`group`·`domain` 쿼리 파라미터와 `facets`·`meta`는 그대로 둔다(D-10:55행). 프런트엔드는 어떤 파라미터도 보내지 않고 검색 입력·Select 2개를 화면에서 제거한다. 단 DEC-3으로 `use_cases`가 사라지므로 `_matches_query`의 haystack은 `canonical_name` + `aliases` + `description`으로 축소된다(D-8:211행). | AC-6은 "검색 입력과 그룹·도메인 필터가 **화면에서** 제거된다"만 요구한다. 백엔드 제거는 AC를 진전시키지 않으면서 layout 테스트를 포함한 기존 단언을 깨뜨린다(→ D-15). `use_cases` 축소는 DEC-3의 불가피한 귀결이며, 실측상 `use_cases`는 0/55라 실데이터 검색 품질에 영향이 없다(→ E-1). 이 축소로 무효가 되는 시험 1건은 DEC-7 표에서 처리한다. |
| **DEC-6. 사이드바+본문은 단일 컴포넌트가 두 라우트를 모두 렌더한다** | `src/pages/docs/`에 `SkillDocsPage.tsx`(가칭)를 신설해 `docs/skills`와 `docs/skills/:skillId` **두 route의 element로 동일 컴포넌트**를 지정한다. `useParams().skillId` 부재 시 우측은 안내 빈 상태, 존재 시 상세를 렌더한다. `DocsCatalogPage.tsx`·`DocsDetailPage.tsx`와 그 테스트 2건은 삭제한다. `AppShell.tsx`의 `OPAL Docs` 메뉴 1개(D-13:97행)와 `router.tsx`의 route 경로 2개(D-13:38-39행)는 유지하고 element만 교체한다. 사이드바는 목록 API 1회 호출 결과를 `display_group`으로 파일럿·오퍼레이터·독립 3그룹으로 묶고, 각 항목에 canonical 이름과 alias를 함께 표시한다. | AC-2는 사이드바가 유지된 채 우측만 바뀌고 URL이 `/docs/skills/{skill}`로 변하기를 요구한다. 두 컴포넌트를 각각 두면 사이드바가 중복 구현되고 목록 쿼리가 라우트 전환마다 재마운트된다. 단일 컴포넌트는 React Router가 같은 element를 유지해 사이드바 스크롤·선택 상태가 보존된다. 그룹 라벨 3종은 `display_group` 값 → 한국어 표시명 매핑이며 이는 표현 계층의 i18n이지 C-2가 금지하는 "스킬 메타데이터 하드코딩"이 아니다. |
| **DEC-7. 무효가 되는 시험은 시험 단위로 판정한다** | 아래 §무효 시험 처리표가 정본이다. 요약: `test_skill_docs.py`에서 **폐기 5건**, **수정 2건**, **유지 나머지**. `test_skill_docs_layout.py` 8건은 전부 유지하고 실자산 단언을 **추가**한다. FE 테스트 `DocsCatalogPage.test.tsx`·`DocsDetailPage.test.tsx`는 폐기하고 신규 테스트로 교체한다. fixture 스킬 3개(`opal-standard-heading`·`opal-no-heading`·`opal-partial-heading`)는 삭제하지 않고 **README 유무 조합 fixture로 재목적화**한다. | 무효 판정 기준은 "DEC-3으로 단언 대상 필드가 사라지는가"다. 필드가 사라지면 그 시험은 수정이 아니라 폐기다 — 삭제된 키를 `is None`으로 단언하면 계약 제거를 검증하지 못하고 통과만 한다. fixture 폴더 재목적화는 폴더를 지웠다가 다시 만드는 것보다 diff가 작고, 폴더명이 이미 "본문 형태가 제각각인 스킬"이라는 시험 의도를 담고 있다. |
| **DEC-8. 전체 회귀는 build를 마지막에 두는 고정 순서로 실행한다** | ① `python -m pytest dashboard/backend/tests` → ② `node --test opal/tools/skill-registry/tests/*.js` → ③ `cd dashboard/frontend && npm test` → ④ `npm run typecheck` → ⑤ `npm run lint` → ⑥ `npm run build`. 이 순서를 W-6의 완료 기준으로 고정한다. | `api-env-files.test.ts`는 저장소 `dist/`가 존재하면 실패한다(D-16:49-57행 — "`npm run build`가 TMPDIR outDir로 exit 0 통과하고 저장소 dist/를 남기지 않는다"). `npm test`보다 `npm run build`를 먼저 실행하면 이 시험이 실패한다. build를 마지막에 두면 잔여 `dist/`가 후속 검증을 오염시키지 않는다. |
| **DEC-9. 읽기 전용 표면과 Markdown 안전 정책을 무변경으로 유지한다** | 공개 표면은 `GET` 2개뿐이며 메서드·엔드포인트를 추가하지 않는다. 본문 렌더는 기존 `MarkdownView`(D-12)를 그대로 쓰고 `rehype-raw` 등 raw HTML 플러그인을 추가하지 않는다. 본문 파일 읽기는 `_safe_join`(D-8:372행)을 경유해 corpus root 하위로만 허용한다. 신규 npm·Python 의존성 0건. | **[MUST]** D-1 §Constraints C-5 "이 화면에서 스킬 실행·파일 수정·설치를 수행하지 않는다". C-6은 raw HTML 플러그인 미사용, C-1은 신규 런타임 의존성 금지를 요구한다. `MarkdownView`는 remark-gfm + rehype-slug만 쓰고 raw HTML을 허용하지 않으며 heading 2개 이상이면 목차를 렌더한다(D-12) — README 렌더에 그대로 부합한다. |

### 무효 시험 처리표 (DEC-7 정본)

| 시험 | 파일:위치 | 판정 | 근거 |
|------|-----------|------|------|
| `test_s3_list_search_by_use_case_phrase` | `test_skill_docs.py:118` | **폐기** | DEC-3으로 `use_cases`가 제거되어 검색 haystack에서 사라진다(DEC-5). 단언 대상 자체가 없다 |
| `test_s6_source_missing_returns_200_partial` | `test_skill_docs.py:250` | **수정** | 200 partial 계약과 header metadata 보존 단언은 유지. 삭제된 슬롯 필드 단언 6줄을 제거하고 `body.markdown is None`·`body.origin is None`으로 교체 |
| `test_s9_examples_have_no_prompt_chars_or_regex_metachars` | `test_skill_docs.py:342` | **폐기** | `examples`·`quick_start` 필드 제거로 순회 대상이 사라지고 말미의 `assert checked_any`가 항상 실패한다. 수정 여지가 없다 |
| `test_s9_registry_triggers_not_exposed` | `test_skill_docs.py:365` | **수정** | 유지하되 강화 — 응답 원문 검사 범위에 새 `body.markdown`을 포함해 본문 경유 trigger 정규식 노출이 없음을 확인 |
| `test_s10_standard_heading_extracts_all_sections` | `test_skill_docs.py:375` | **폐기** | 슬롯 추출 계약 자체가 제거됨 |
| `test_s10_no_heading_returns_null_or_empty` | `test_skill_docs.py:386` | **폐기** | 동일 |
| `test_s10_partial_heading_extracts_only_available_section` | `test_skill_docs.py:398` | **폐기** | 동일 |
| S-3 나머지 6건 / S-4 5건 / S-5 2건 / S-7 3건 / S-8 전건 | `test_skill_docs.py` | **유지** | 목록·canonical identity·pipeline·오류 계약·읽기 전용 계약은 이번 변경의 영향을 받지 않는다. 단 S-8의 절대경로 미노출 시험은 `body.markdown`까지 검사 범위에 포함하도록 W-1에서 보강한다 |
| `test_skill_docs_layout.py` 8건 | 전건 | **유지 + 추가** | 레이아웃 해석 계약 무변경. 실자산 단언(listed 33건·README origin)을 이 파일에 추가한다 |
| `DocsCatalogPage.test.tsx` · `DocsDetailPage.test.tsx` | `src/pages/docs/` | **폐기** | 검증 대상 컴포넌트 2개가 DEC-6으로 삭제된다 |
| fixture 스킬 `opal-standard-heading`·`opal-no-heading`·`opal-partial-heading` | `tests/fixtures/skill_docs_corpus/opal_skills/` | **재목적화** | 각각 ①README 보유 ②README 없음+SKILL 본문 있음 ③README·SKILL 본문 모두 없음(공백) 케이스로 전환 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|------|------|-----------|-------------|-----------|-----------|----------------|
| **W-1. 백엔드 공개 계약 RED 테스트와 무효 시험 정리** | opal-test-agent | `dashboard/backend/tests/test_skill_docs.py`, `dashboard/backend/tests/test_skill_docs_layout.py`, `dashboard/backend/tests/fixtures/skill_docs_corpus/**` | DEC-1·2·4 계약의 실패 테스트를 먼저 작성한다. ①`body.markdown`이 README 원문과 바이트 동일하고 `origin="readme"`, `source_path`가 `.../README.md` 상대경로일 것 ②README 부재 스킬은 `origin="skill_md"`이고 `body.markdown`에 YAML frontmatter가 포함되지 않을 것 ③둘 다 없으면 `markdown=null`·`origin=null`·HTTP 200 ④목록·상세 응답에 `listed` 필드가 있고 `internal-stage`는 `listed=false` ⑤`paths` 폴더명이 canonical과 다른 엔트리는 `listed=false`지만 상세 조회는 200 ⑥삭제 대상 슬롯 필드 7종이 응답 키에 **존재하지 않을 것**. 같은 커밋에서 DEC-7 처리표대로 폐기 5건을 삭제하고 수정 2건을 갱신하며 fixture 3개를 README 유무 조합으로 재목적화한다. **실자산 단언을 `test_skill_docs_layout.py`에 추가한다**: 소스 저장소 루트 corpus에서 `listed=true` 개수가 정확히 33이고, `display_group` 분포가 pilot 12·operator 14·standalone 8·internal-stage 21이며, 실존 스킬 1건 이상의 `body.origin`이 `"readme"`이고 `body.markdown`이 비어 있지 않을 것 — 합성 fixture가 아닌 실 corpus를 읽는다. 완료 시 신규 단언이 전부 실패(RED)해야 한다 | 없음 | P1 | AC-3, AC-4, AC-5, AC-7, C-2, C-3, C-4 |
| **W-2. 프런트엔드 화면 RED 테스트** | opal-test-agent | `dashboard/frontend/src/pages/docs/SkillDocsPage.test.tsx` (신규), 기존 `DocsCatalogPage.test.tsx`·`DocsDetailPage.test.tsx` 삭제 | DEC-6 계약의 실패 테스트를 먼저 작성한다. ①사이드바에 3그룹 헤더와 `listed=true` 항목만 렌더되고 `listed=false` 항목은 렌더되지 않을 것 ②각 항목에 canonical 이름과 alias가 함께 표시될 것 ③항목 클릭 시 URL이 `/docs/skills/{id}`가 되고 사이드바가 유지되며 선택 항목에 `aria-current` 등 시각적 구분이 적용될 것 ④`body.markdown`이 Markdown으로 렌더되어 제목·목록·표·코드 블록이 요소로 나타날 것 ⑤`origin="skill_md"`면 폴백 안내가 보이고 `origin=null`이면 부재 상태가 보일 것 ⑥검색 입력(`role="searchbox"`)과 그룹·도메인 Select가 화면에 **없을 것** ⑦로딩·목록 빈 상태·목록 조회 실패·상세 404 각각의 상태가 표시될 것 ⑧사이드바가 `nav` 랜드마크와 접근 가능한 이름을 갖고 키보드로 항목 간 포커스 이동이 가능할 것. 기존 Testing Library + memory router + QueryClient 패턴을 따르고 스크린샷 golden을 만들지 않는다. 완료 시 전부 실패(RED)해야 한다 | 없음 | P1 | AC-1, AC-2, AC-5, AC-6, AC-7, C-4, C-8 |
| **W-3. 백엔드 본문 로더·`listed` 파생·공개 모델 교체** | opal-be-agent | `dashboard/backend/parsers/skill_parser.py`, `dashboard/backend/adapters/skill_docs_adapter.py`, `dashboard/backend/models.py`, `dashboard/backend/routers/docs_skills.py` | DEC-1·2·3·4·5·9대로 구현해 W-1을 GREEN으로 만든다. parser: `_split_sections`·`_parse_items`·`_parse_examples`·`_parse_use_cases`·`_parse_quick_start`와 관련 정규식·상수를 제거하고, frontmatter(`name`·`description`)·`content_hash`·frontmatter 제거 본문만 반환한다. adapter: 스킬 폴더의 `README.md`를 `_safe_join` 경유로 읽어 없으면 SKILL.md 본문으로 폴백하는 본문 해석을 추가하고, `listed`를 DEC-4 두 조건으로 파생한다(레지스트리 엔트리 `paths[0]`의 스킬 폴더명 대조). `_matches_query` haystack에서 `use_cases`를 제거한다. `_resolve_corpus_layout`·`_resolve_physical_skill_path`·`_display_group`·`_derive_aliases`·`_load_pipeline`·alias index·related_skills 2차 패스는 **변경하지 않는다**. models: `SkillDetailResponse`에서 슬롯 필드 7종을 삭제하고 `SkillBody`(`markdown`·`origin`·`source_path`)를 추가하며, 목록·상세 모델에 `listed: bool`을 추가한다. 사용처가 사라진 `ArgumentItem`·`ExampleBlock`은 삭제한다. router: GET 2개·오류 매핑·DI 지점을 변경하지 않는다. 응답에 절대경로를 싣지 않는다. 수정한 파일의 `@header`를 현재 사실로 갱신한다 | W-1 | P2 | AC-3, AC-4, AC-5, C-2, C-3, C-4, C-5, C-7 |
| **W-4. 사이드바+본문 화면 구현과 기존 화면 교체** | opal-fe-agent | `dashboard/frontend/src/pages/docs/SkillDocsPage.tsx` (신규), `dashboard/frontend/src/pages/docs/types.ts`, `dashboard/frontend/src/router.tsx`, 기존 `DocsCatalogPage.tsx`·`DocsDetailPage.tsx` 삭제 | DEC-6·9대로 구현해 W-2를 GREEN으로 만든다. 단일 컴포넌트가 좌측 사이드바(목록 API 무파라미터 1회 호출 → `listed=true`만 `display_group`으로 파일럿·오퍼레이터·독립 3그룹 묶음, 항목에 canonical과 alias 병기, 현재 선택 항목 시각 구분과 `aria-current`)와 우측 본문(`MarkdownView`로 `body.markdown` 렌더, `origin="skill_md"`면 폴백 안내, `origin=null`이면 부재 상태)을 렌더한다. `skillId` 미지정 시 우측은 안내 빈 상태다. 검색 입력과 Select 2개를 제거하고 목록 요청에 `q`·`group`·`domain`을 보내지 않는다. `types.ts`를 새 응답 계약(슬롯 필드 제거, `body`·`listed` 추가)에 맞춰 교체한다. `router.tsx`는 route 경로 2개를 유지한 채 element만 새 컴포넌트로 교체한다. `AppShell.tsx`의 메뉴 1개와 기존 7개 화면·라우트는 **변경하지 않는다**. 데스크톱은 상시 사이드바, 모바일은 기존 `sheet.tsx` 또는 `drawer.tsx` 프리미티브로 토글하고 `scroll-area.tsx`로 긴 목록을 처리한다 — 기존 shadcn/ui 프리미티브와 전역 색상 토큰만 쓰고 신규 npm 의존성을 추가하지 않는다. raw HTML 플러그인을 추가하지 않는다. 신규·수정 파일의 `@header`를 작성·갱신한다 | W-2, W-3 | P3 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, C-1, C-2, C-4, C-5, C-6, C-8 |
| **W-5. 프로젝트 문서 갱신** | PM 직접 | `docs/ARCHITECTURE.md` 351-359행, `README.md` 886행 | ARCHITECTURE의 OPAL Docs 절을 현재 사실로 갱신한다 — 화면 구조를 "카탈로그 카드 + 상세"에서 "그룹 사이드바 + README 원문 렌더"로, FE 구성 `pages/docs/{DocsCatalogPage,DocsDetailPage,types}`를 새 컴포넌트 구성으로, 상세 응답 설명에 `body`·`listed` 추가와 슬롯 필드 제거를 반영한다. README 886행의 "목적·호출 형식·옵션·예시·파이프라인·관련 스킬을 확인하며 명령을 복사할 수 있다"는 제거된 기능을 기술하므로 사이드바 탐색과 README 열람으로 고쳐 쓴다. `docs/PROJECT.md` 191행은 Console 8개 화면 목록이며 화면 수·이름이 바뀌지 않으므로 갱신하지 않는다. `docs/CONVENTIONS.md`는 규약 변경이 없어 갱신하지 않는다. 태스크 140의 PLAN·wireframe은 종료된 태스크 산출물이므로 소급 수정하지 않는다 | W-4 | P4 | AC-8 |
| **W-6. 전체 회귀 검증** | opal-test-agent | 변경 없음 (검증 실행) | DEC-8 고정 순서대로 실행하고 각 단계의 명령·exit code·건수를 결과에 기록한다. ①`python -m pytest dashboard/backend/tests` ②`node --test opal/tools/skill-registry/tests/test-validate.js opal/tools/skill-registry/tests/test-match.js opal/tools/skill-registry/tests/test-verify-bundle.js` ③`cd dashboard/frontend && npm test` ④`npm run typecheck` ⑤`npm run lint` ⑥`npm run build`. build를 마지막에 두는 이유는 저장소 `dist/` 잔존 시 `api-env-files.test.ts`가 실패하기 때문이며, ⑥ 실행 후 저장소 `dist/`가 남지 않았는지 확인한다. 추가로 `node opal/tools/skill-registry/skill-registry.js validate`가 `valid:true`·`unregistered:[]`를 유지하는지, 백엔드 테스트 총계가 140 기준(434 passed)에서 DEC-7 폐기·신설분만큼만 변동했는지 확인한다. 기존 Console 7개 화면 관련 테스트에 실패가 없어야 한다. 신규 npm·Python 의존성이 0건인지 `package.json`·`requirements` diff로 확인한다 | W-5 | P5 | AC-8, C-1 |
| **W-7. 설치 배포와 실자산 브라우저 실측** | 사용자 확인 단계 (캡틴 직접 실행) | 변경 없음 (배포·실측 실행) | 소스 루트에서 `./scripts/install-mac.sh`를 실행해 전체 설치를 선택한다(**[MUST]** `docs/CONVENTIONS.md` §배포 경계 "변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다" — `~/.opal/`을 직접 편집하지 않는다). 이어 `~/.opal` corpus에서 목록 API의 `listed=true`가 33건인지, 특정 스킬(예: `oppb`) 상세의 `body.origin`이 `"readme"`이고 본문이 비어 있지 않은지 curl로 확인한다. 브라우저에서 데스크톱·모바일 두 뷰포트로 `/docs/skills` 진입 → 3그룹 사이드바 33개 확인 → 항목 클릭 시 URL 변경과 본문 렌더 확인 → 새로고침·URL 직접 접근 확인 → `listed=false` 스킬(`op-*` 1건, `opal-pilot-dev-short`)이 사이드바에 없지만 URL 직접 접근으로는 읽히는지 확인 → 검색·필터 부재 확인 → 키보드 탭 이동 확인 → 존재하지 않는 skill id 404 상태 확인. 마지막으로 기존 Console 7개 화면을 순회해 회귀가 없음을 확인한다 | W-6 | P6 | AC-1, AC-2, AC-3, AC-5, AC-6, AC-8, AC-9, C-4, C-7, C-8 |

### 완료 기준 커버리지

| 기준 | 연결된 Work item |
|------|------------------|
| AC-1 | W-2, W-4, W-7 |
| AC-2 | W-2, W-4, W-7 |
| AC-3 | W-1, W-3, W-4, W-7 |
| AC-4 | W-1, W-3, W-4 |
| AC-5 | W-1, W-2, W-3, W-4, W-7 |
| AC-6 | W-2, W-4, W-7 |
| AC-7 | W-1, W-2, W-4 |
| AC-8 | W-5, W-6, W-7 |
| AC-9 | W-7 |
| C-1 | W-4, W-6 |
| C-2 | W-1, W-3, W-4 |
| C-3 | W-1, W-3 |
| C-4 | W-1, W-2, W-3, W-4, W-7 |
| C-5 | W-3, W-4 |
| C-6 | W-4 |
| C-7 | W-3, W-7 |
| C-8 | W-2, W-4, W-7 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|------|------------------------|------|-----------|
| **H-1. 합성 fixture만으로 GREEN을 선언하고 실 corpus에서 다시 비는 화면이 나온다** | AC-1의 33건·AC-3의 본문 표시 | 140의 실패(본문 공백 배포 직전 발견)가 그대로 재발한다 | **[MUST]** `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md` §대응 원칙 "PM 직접 실행 검증". W-1이 `test_skill_docs_layout.py`에 실 corpus 단언(listed 33·분포·실제 README origin)을 **테스트 코드로** 고정하고, W-7이 `~/.opal` 설치본에서 브라우저 실측한다. fixture 통과만으로는 W-6이 완료되지 않는다 |
| **H-2. `listed` 파생 규칙 ②가 미래의 정상 엔트리를 잘못 숨긴다** | AC-1의 노출 집합 | 새 스킬이 사이드바에서 소실되고 원인이 서버 파생 규칙에 숨어 발견이 늦어진다 | 현재 실측상 해당 엔트리는 1건뿐이다(→ E-1). W-1의 실자산 단언이 `listed=true` 개수를 33으로 못 박아 규칙이 과잉 적용되면 즉시 RED가 된다. 스킬 추가로 33이 바뀔 때는 기대값 갱신이 강제되어 변화가 가시화된다 |
| **H-3. 공개 계약에서 필드 7종을 제거해 다른 소비자가 깨진다** | `SkillDetailResponse`를 읽는 코드 | 런타임 오류 또는 조용한 undefined | 현재 소비자는 이번에 삭제되는 `DocsDetailPage.tsx` 단 하나다(→ D-13). `ArgumentItem`·`ExampleBlock` 삭제 전 W-3이 `models.py` 참조를 확인하고, 다른 사용처가 있으면 삭제하지 않고 남긴 뒤 근거를 DONE에 기록한다. W-6의 typecheck가 FE 잔여 참조를 잡는다 |
| **H-4. README 원문을 그대로 실어 보내면서 로컬 절대경로나 레지스트리 정규식이 응답에 노출된다** | 기존 S-8 절대경로 미노출 계약, S-9 trigger 미노출 계약 | 사용자 대면 화면에 내부 경로·정규식 노출 | W-1이 절대경로 미노출 시험과 trigger 미노출 시험의 검사 범위를 `body.markdown`까지 확장한다(DEC-7 처리표). 실 README에 `~/.opal/...` 같은 문서용 경로 표기는 정상이며 금지 대상은 corpus root 절대경로 유출이다 — 이 구분을 W-1 단언에 명시한다 |
| **H-5. 목록 응답에 본문을 싣지 않기로 했으므로 상세 진입마다 파일 I/O가 발생한다** | 체감 응답 속도 | 사이드바 항목 전환이 느려질 수 있다 | 기존 계약대로 요청마다 corpus를 재구성하되 캐시를 도입하지 않는다(140 DEC-4 승계, → D-2 "백엔드 캐시를 도입하지 않았다"). FE의 30초 query stale time으로 같은 스킬 재방문은 재요청하지 않는다. W-7 실측에서 체감 지연이 관측될 때만 별도 태스크로 승격한다 |
| **H-6. `npm run build`를 검증 중간에 실행해 `api-env-files.test.ts`가 실패한다** | AC-8 판정 | 회귀 검증이 거짓 실패로 막힌다 | DEC-8이 순서를 고정하고 W-6의 완료 기준에 순서 준수를 포함한다(→ D-16:49-57행) |
| **H-7. 두 route가 같은 컴포넌트를 쓰면서 상세 전환 시 사이드바 쿼리가 재요청된다** | AC-2의 사이드바 유지 | 항목 클릭마다 사이드바가 깜빡인다 | DEC-6이 단일 컴포넌트를 채택한 이유가 이것이다. 목록 쿼리 key를 `skillId`와 무관하게 고정해 상세 전환이 목록 쿼리를 무효화하지 않게 한다. W-2 ③단언이 전환 후 사이드바 항목 유지를 검증한다 |

## Release and recovery

- **브랜치·머지**: `feat/143-opds-스킬-문서-사이드바`(base `feat/140-opdw-스킬-문서-화면`)에서 작업한다. 140 산출물은 상세 화면이 빈 상태라 단독 머지하지 않기로 결정됐으므로(→ D-2 §참고), 이번 태스크 완료 후 두 브랜치를 함께 main으로 올린다.
- **커밋**: **[MUST]** `docs/CONVENTIONS.md` §커밋 규칙 "하나의 태스크 = 하나의 커밋 (원칙)", 형식은 `feat(143): {한국어 설명}`. 커밋 실행은 사용자 요청 시점에만 수행한다.
- **배포**: W-7에서 `./scripts/install-mac.sh` 전체 설치로만 반영한다. dashboard-only 메뉴로는 FE·BE 동시 반영이 되지 않는다(→ D-2 W-12 기재). `~/.opal/`을 직접 편집해 우회하지 않는다.
- **롤백**: 변경이 모두 `dashboard/` 하위와 문서 2건에 한정되므로 브랜치 되돌리기 + 재설치로 복구한다. 레지스트리(`opal/core/references/opal-skills-registry.json`)와 스킬 `README.md` 55건은 이번 태스크가 건드리지 않으므로 롤백 대상이 아니다.
- **데이터 마이그레이션 없음**: 읽기 전용 표면이며 영속 상태를 만들지 않는다.
- **부분 실패 시 경계**: W-3까지 GREEN이고 W-4가 막히면 백엔드 계약만 먼저 확정된 상태로 남으며, 기존 화면이 삭제되기 전이므로 사용자 노출 동작은 140 상태(빈 상세)로 유지된다 — 배포하지 않은 브랜치 상태이므로 사용자 영향은 없다.
