---
template: sdlc-v2
stage: PLAN
task: 140-260917-opdw-스킬-문서-화면
status: completed
planned_at: 2026-09-18 14:37
baseline_revision: 0ea0f54
---
# PLAN: OPAL Docs 스킬 문서 화면

> 입력: [TASK.md](TASK.md), [ANALYSIS.md](ANALYSIS.md), [wireframe.md](wireframe.md)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|---|---|---|---|
| D-1 | 기획 | TASK.md | `tasks/140-260917-opdw-스킬-문서-화면/TASK.md` | AC-1~AC-8, C-1~C-7 요구 SSOT |
| D-2 | 설계 | ANALYSIS.md | `tasks/140-260917-opdw-스킬-문서-화면/ANALYSIS.md` | Findings·Change boundary·검증 명령 6단계·Handoff |
| D-3 | 설계 | wireframe.md | `tasks/140-260917-opdw-스킬-문서-화면/wireframe.md` | 승인된 화면 설계, §5.2/§5.3 응답 계약, §5.4 오류 계약 |
| D-4 | 설계 | PROJECT.md | `docs/PROJECT.md` | §프로젝트 구성(236-244행) 영역↔경로↔에이전트 매핑, §문서 레지스트리(246-268행) |
| D-5 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | §컴포넌트 유형 스킬 표(112-171행), §OPAL Console(274-344행) — 현재 7개 화면 기술 |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §약어(Alias) 44-60행 — alias SSOT가 레지스트리임을 규정 |
| D-7 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | canonical 병합·validate·배포 환경 reverse scan 생략 |
| D-8 | 소스 | AppShell.tsx / router.tsx | `dashboard/frontend/src/components/app-shell/AppShell.tsx`, `dashboard/frontend/src/router.tsx` | 셸 메뉴·라우트 추가 지점 |
| D-9 | 소스 | api.ts | `dashboard/frontend/src/lib/api.ts` | 현재 오류 처리가 status/code/details를 소실 |
| D-10 | 소스 | main.py / models.py | `dashboard/backend/main.py`, `dashboard/backend/models.py` | router 등록 순서와 공개 응답 모델 위치 |
| D-11 | 설계 | citation-rules.md | `~/.opal/references/harness/citation-rules.md` | 산출물 인용 의무 SSOT |
| D-12 | 설계 | guards.md | `~/.opal/references/harness/guards.md` | 구현 금지 원칙 |
| D-13 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | 배포 경계·플랫폼 분기 금지 |

강제 규칙 원문:

- [MUST] `~/.opal/references/harness/guards.md` §구현 금지 원칙: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다."
- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다."
- [MUST] `tasks/140-260917-opdw-스킬-문서-화면/TASK.md` §Constraints C-2: "스킬 메타데이터를 프론트엔드에 하드코딩하지 않고 레지스트리·각 `SKILL.md`·`pipeline.json` 등 기존 소스 자산에서 읽기 전용으로 파생한다."
- [MUST] `tasks/140-260917-opdw-스킬-문서-화면/TASK.md` §Constraints C-4: "명령 예시는 그대로 복사해 사용할 수 있어야 하며 터미널 프롬프트 문자나 정규식 메타문자를 사용자 대면 예시에 포함하지 않는다."
- [MUST] `tasks/140-260917-opdw-스킬-문서-화면/TASK.md` §Constraints C-5: "기존 Console의 읽기 전용 원칙을 유지하고 스킬 문서 화면에서 스킬 실행·파일 수정·설치를 수행하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §약어(Alias): "SSOT: `opal/core/references/opal-skills-registry.json` — 약어의 등록·변경은 레지스트리에서만 수행한다."

## Approach

읽기 전용 Docs 표면을 4개 층으로 나눠 추가한다. 프레임워크 층은 설치본 완전성을 증명할 검증 진입점만 추가하고 레지스트리 데이터는 건드리지 않는다. 백엔드는 registry + bundled `SKILL.md` + 선택적 `pipeline.json`을 canonical 병합하는 parser/adapter와 GET 전용 라우터 2개를 추가한다. 프론트엔드는 오류 계약을 보존하는 additive `ApiError`를 먼저 세우고 `src/pages/docs/**`에 카탈로그·상세 화면을 응집시킨 뒤 셸 메뉴와 2개 라우트만 추가한다. 마지막으로 문서와 설치 검증을 닫는다.

범위 확정 사항:

- 레지스트리 등재는 이번 범위가 아니다. source 55개 = registry 55개, `validate`가 `valid:true`·`unregistered:[]`이며 OPPB 3건은 태스크 132 병합으로 이미 등재됐다 (→ D-2 §Findings Q4). AC-4의 잔여 검증은 OPPB 3건의 그룹·alias·pipeline 조회 정확성과 설치본 대조 두 가지다.
- 백엔드 캐시·installer 복사 로직·Doctor용 `skill_adapter.py`·`markdown-view.tsx`는 직접 변경하지 않고 회귀 확인 대상으로만 둔다 (→ D-2 §Change boundary).
- 신규 npm/Python 의존성을 추가하지 않는다 (→ D-2 §Critical assumptions).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| DEC-1. source-missing은 HTTP 200 partial detail | `GET /api/docs/skills/{skill_id}`는 registry에 canonical/alias가 존재하면 항상 200을 반환하고, 원본 `SKILL.md`를 읽지 못하면 header metadata(canonical_name·description·display_group·aliases·source_path)를 유지한 채 `source.available=false`, `source.content_hash=null`, `usage_markdown`·`when_to_use_markdown`·`quick_start`는 `null`, `arguments`·`options`·`examples`·`related_skills`는 `[]`로 반환한다. `skill_not_found`(404)는 canonical/alias 어디에도 없는 id에만 쓴다. registry 자체를 읽지 못하면 500 `registry_unavailable`, corpus parse 실패는 500 `parse_error`로 error envelope를 반환한다. 오류 envelope 형식은 wireframe §5.4를 그대로 유지한다. | wireframe 성공 모델은 이미 `source.available: boolean`을 요구하는데(→ D-3 §5.3 상세 응답 계약) 같은 문서 오류표는 `source_missing`을 409/422로 보내 부분 메타데이터를 보존할 수 없다(→ D-3 §5.4). 두 계약이 모순이므로 성공 모델 쪽을 정본으로 채택한다. 200 partial은 AC-3의 "적용할 수 없는 섹션은 거짓 기본값 대신 명시적으로 생략하거나 없음으로 표현한다"와 AC-6의 "상세 원본 부재" 상태를 동시에 만족하며(→ D-1 §Acceptance criteria), ANALYSIS 권고와 일치한다(→ D-2 §Handoff). 폐기한 대안(409/422 유지)은 error payload에 header metadata를 추가하는 오류 모델 확장을 요구해 공개 model과 오류 UI를 이중으로 만든다. 이 결정에 따라 wireframe §5.4의 `source_missing` 행은 "HTTP 상태 아님 — 200 partial의 `source.available=false`로 표현"으로 정정한다(W-10). |
| DEC-2. 다중 alias는 registry schema에 저장하지 않고 Docs service에서 파생한다 | `opal-skills-registry.json`의 엔트리 스키마는 변경하지 않고 기존 scalar `alias`를 그대로 유지한다. Docs adapter가 응답의 `aliases: string[]`를 ①registry `alias`, ②canonical과 다른 frontmatter `name`(= `source_name`) 순으로 순서 보존·중복 제거해 파생한다. alias 조회 인덱스에 같은 alias가 두 canonical을 가리키면 `ambiguous_alias`로 검증 실패시키고 자동 선택하지 않는다. | alias 등록·변경의 SSOT는 레지스트리 하나뿐인데([MUST] `docs/CONVENTIONS.md` §약어(Alias)), Docs 표시용 파생 별칭까지 레지스트리에 적재하면 표시 목적 데이터가 SSOT를 오염시킨다. 프로젝트 지식에 "레지스트리 메타데이터를 두 위치에 중복 저장하면 drift한다"는 기존 결정이 있다(`.opal/brain/pages/concept/tool-scan-thin-manifest-federation.md`). 파생만으로도 `opal-onboarding`/`onboarding`, `opal-skill-manager`/`skill-manager`의 AC-5 정규화가 성립한다(→ D-2 §Findings Q4). schema 무변경이므로 `docs/CONVENTIONS.md`의 alias 표(현재 32종)도 갱신 대상이 아니다. |
| DEC-3. 설치 bundle 검증은 `validate`와 분리된 `verify-bundle` 진입점을 신설한다 | `skill-registry.js`에 `verify-bundle --registry <path> --skills-root <path...>` 서브커맨드를 추가한다. 주어진 registry의 canonical set과 주어진 skills root의 폴더 basename set을 양방향 대조해 `{ ok, total, missing_source: [], unregistered: [], ambiguous_alias: [] }`를 JSON으로 출력하고 불일치 시 exit code를 0이 아닌 값으로 둔다. 기존 `validate`의 동작·출력·배포 환경 reverse scan 생략 계약은 변경하지 않는다. | 배포 환경 validate는 false positive 방지를 위해 reverse unregistered scan을 의도적으로 생략하며(`opal/tools/skill-registry/skill-registry.js:624-633`) 기존 test가 그 동작을 보호한다(→ D-2 §Findings Q5). 따라서 설치본에서 `validate` 성공만으로는 AC-8의 "누락 0"을 증명할 수 없다. 명시적 인자로 대상 경로를 받는 별도 진입점은 환경 추론을 제거해 source·설치본 양쪽에 같은 규칙을 적용할 수 있고, 기존 계약을 깨지 않는다. |
| DEC-4. Docs corpus는 backend 캐시 없이 요청마다 재구성한다 | `dashboard/backend/cache.py`를 변경하지 않고 Docs adapter는 매 요청 registry·55개 `SKILL.md`·선택적 `pipeline.json`을 읽어 canonical index를 만든다. 캐싱은 FE의 기존 30초 query stale time에 의존한다. | 공통 캐시는 단일 `source_path` mtime만 추적하므로 다중 파일 corpus에 그대로 쓰면 부분 갱신이 stale해진다(→ D-2 §Findings Q2). 캐시 유무는 AC/C 기능 계약을 바꾸지 않으므로 최초 구현에서 가장 작은 올바른 경계다. 성능 측정이 필요성을 입증할 때만 별도 태스크로 승격한다. |
| DEC-5. canonical identity는 registry `name` = 폴더 basename 하나뿐이다 | Docs row key는 `canonical_name`이고, frontmatter `name`은 `source_name` provenance 필드로만 보존한다. 같은 스킬이 두 카드로 분리되지 않으며 corpus 총계는 canonical 55행이다. | registry tool이 exact `name`으로 source를 병합하고(`opal/tools/skill-registry/skill-registry.js:196-227`) `opal-onboarding`·`opal-skill-manager`의 frontmatter name만 다르다(→ D-2 §Findings Q4). AC-5의 "중복 카드 없이 하나의 스킬로 정규화"를 이 규칙 하나로 충족한다. |
| DEC-6. 공개 API는 GET 2개만 노출하고 경로 조작을 차단한다 | `GET /api/docs/skills`(검색·필터 목록), `GET /api/docs/skills/{skill_id}`(canonical 또는 alias) 두 개만 등록하고 SPA fallback보다 앞에 둔다. 같은 경로의 POST/PUT/PATCH/DELETE는 405로 남는다. 요청 `skill_id`는 인덱스 조회 키로만 쓰고 파일 읽기는 기동 시 열거한 실제 경로에만 허용하며, `resolve()` 결과가 허용 root 하위인지 재검증한다. 응답에는 절대경로를 싣지 않고 `opal/skills/{canonical}/SKILL.md` 또는 `skills/{canonical}/SKILL.md` 형태의 상대 경로만 합성한다. trigger 정규식 실행·pipeline 실행·Markdown raw HTML 렌더를 금지한다. | [MUST] `tasks/.../TASK.md` §Constraints C-5의 읽기 전용 원칙과 registry tool 자체의 경로 제한(`opal/tools/skill-registry/skill-registry.js:309-333`)을 API 경계에도 그대로 적용한다. FastAPI는 router 7개 뒤 SPA fallback 순서를 유지한다(`dashboard/backend/main.py:91-134`). |
| DEC-7. FE 오류 계약은 additive `ApiError`로 확장한다 | `apiClient`가 실패 시 `status`, `code`, `message`, `details`(또는 `skill_id`·`retryable`)를 보존하는 `ApiError`를 던진다. 기존 FastAPI `detail` 메시지 추출, timeout 동작, generic message 폴백은 그대로 유지한다. | 현재 구현은 `detail`만 읽고 일반 `Error`를 던져 status와 wireframe error envelope를 잃는다(`dashboard/frontend/src/lib/api.ts:57-100`). AC-6의 code별 복구 UI 분기가 불가능하다. 기존 호출자 회귀를 막기 위해 교체가 아닌 additive 확장으로 둔다. |
| DEC-8. Docs 화면은 기존 Console 자산만 재사용한다 | `src/pages/docs/**`에 카탈로그·상세·query hooks·표현 타입을 응집시키고 기존 shadcn/ui primitives와 전역 색상 토큰을 쓴다. 새 문서 프레임워크·디자인 시스템·외부 런타임 의존성을 추가하지 않는다. 본문 Markdown은 기존 안전 정책(raw HTML 플러그인 없음)을 재사용하되 wireframe 전용 목차와 겹치지 않도록 본문 렌더러를 별도 컴포넌트로 분리한다. alias로 진입한 상세는 응답의 canonical id로 `replace` 탐색해 URL을 정규화한다. | [MUST] `tasks/.../TASK.md` §Constraints C-2 그리고 C-1의 스택 재사용 요구. 기존 `MarkdownView`는 GFM+heading slug만 쓰고 raw HTML을 허용하지 않는다(`dashboard/frontend/src/components/markdown-view.tsx:298-332`). |
| DEC-9. 예시 명령은 복사 원문으로만 저장한다 | `ExampleBlock.command`는 터미널 프롬프트 문자(`$`, `%`, `>`)와 정규식 메타문자를 포함하지 않는 순수 명령 문자열로 추출하고, 추출에 실패하면 내용을 발명하지 않고 해당 블록을 만들지 않는다. registry `triggers`의 정규식은 사용자 대면 예시로 노출하지 않는다. | [MUST] `tasks/.../TASK.md` §Constraints C-4. registry triggers는 `^oppb$` 같은 정규식이므로(`opal/core/references/opal-skills-registry.json:170-174`) 그대로 노출하면 C-4 위반이다. |
| DEC-10. 파싱 실패는 발명하지 않고 부재로 표시한다 | frontmatter는 `yaml.safe_load`로 읽고 섹션·예제·호출 조건은 보수적인 heading/fence 규칙으로만 추출한다. 추출 실패 필드는 `null` 또는 `[]`로 반환하고 UI는 거짓 기본값 대신 명시적 생략 또는 "없음"으로 표현한다. | 기존 project frontmatter 파서는 단순 정규식이라 YAML block/list를 온전히 다루지 못하고(`dashboard/backend/parsers/project_parser.py:60-84`), source body 형식이 균일하지 않다(→ D-2 §Critical assumptions). AC-3의 거짓 기본값 금지 요구와 직결된다. |
| DEC-11. OPPB 단계 요약은 pipeline 우선·본문 fallback | OPPB 상세의 step summary는 `references/pipeline.json`의 `meta.stages`를 우선 사용하고 없을 때만 본문 stage map을 쓴다. 관련 스킬은 registry의 `dispatched_by`/pipeline 참조를 canonical로 정규화해 중복 제거한다. | OPPB는 pipeline `meta.stages`와 본문 P0~P5를 모두 갖고 있고 내부 P2/P5 스킬은 독립 frontmatter를 가진다(→ D-2 §Findings Q4 OPPB 표시 데이터). 기계가독 SSOT를 우선하는 것이 22개 task row를 단계 카드로 오인하는 실패를 막는다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 설치 bundle verifier RED 테스트 | opal-test-agent | `opal/tools/skill-registry/tests/test-verify-bundle.js` (신규) | DEC-3 계약의 실패 테스트를 먼저 작성한다. ①canonical set이 일치하는 fixture는 `ok:true`·`missing_source:[]`·`unregistered:[]`, ②registry에만 있는 엔트리는 `missing_source`, ③폴더에만 있는 스킬은 `unregistered`, ④같은 alias가 두 canonical을 가리키면 `ambiguous_alias`와 non-zero exit. 임시 fixture root를 인자로 넘기며 실 배포본을 읽지 않는다. 기존 `test-validate.js`·`test-match.js`의 `validate` 계약은 건드리지 않는다. 완료 시 전부 실패(RED)해야 한다. | 없음 | P1 | AC-4, AC-8 |
| W-2. Backend Docs 공개 계약 RED 테스트 | opal-test-agent | `dashboard/backend/tests/test_skill_docs.py` (신규) | DEC-1·5·6·9·10·11 계약의 실패 테스트를 먼저 작성한다. 임시 corpus fixture(registry + `SKILL.md` + `pipeline.json`)를 DI로 주입하고, 실 도구 호출과 mock 대체 없이 실제 파일을 읽는다. 항목: 목록 검색(이름·alias·설명·용도)·그룹/도메인 필터·facet count, canonical 정규화로 중복 카드 0, OPPB 3건의 그룹·alias·pipeline 단계, source 부재 시 200 partial + `source.available=false`, unknown id 404 `skill_not_found`, registry 소실 500 `registry_unavailable`, 깨진 YAML 500 `parse_error`, `../` traversal 거부, 절대경로 미노출, POST/PUT/PATCH/DELETE 405, 예시 문자열에 프롬프트 문자·정규식 메타문자 부재. 완료 시 전부 실패(RED)해야 한다. | 없음 | P1 | AC-2, AC-3, AC-4, AC-5, AC-6, C-2, C-3, C-4, C-5 |
| W-3. FE 오류 계약·Docs 화면 RED 테스트 | opal-test-agent | `dashboard/frontend/src/lib/api-error.test.ts` (신규), `dashboard/frontend/src/pages/docs/**/*.test.tsx` (신규) | DEC-7·8 계약의 실패 테스트를 먼저 작성한다. `ApiError`가 status·code·message·details를 보존하고 기존 `detail` 메시지·timeout 동작이 유지되는지, 카탈로그의 loading/empty(전체 0건 vs 검색 0건 구분)/error 상태, 필터·검색의 URL 동기화, alias 진입 시 canonical URL `replace`, 상세의 source 부재 Alert, 404 상태와 목록 복귀 동선, 복사 성공·실패 폴백, 접근 가능한 이름과 키보드 포커스 이동을 검증한다. 기존 Testing Library + memory router + QueryClient 패턴을 따르고 screenshot golden은 만들지 않는다. 완료 시 전부 실패(RED)해야 한다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-6, C-4, C-7 |
| W-4. `verify-bundle` 서브커맨드 구현 | opal-task-agent | `opal/tools/skill-registry/skill-registry.js`, `opal/tools/skill-registry/README.md` | DEC-3대로 `verify-bundle --registry <path> --skills-root <path...>`를 추가해 W-1을 GREEN으로 만든다. 기존 `validate` 분기와 배포 환경 reverse scan 생략 로직(`skill-registry.js:624-633`)을 수정하지 않고 새 분기로만 추가한다. canonical/alias 규칙은 DEC-2·5와 동일하게 적용한다. README에 새 서브커맨드의 인자·출력·exit code를 기술한다. 기존 `test-validate.js`·`test-match.js`가 계속 통과해야 한다. | W-1 | P2 | AC-4, AC-8, C-2, C-3 |
| W-5. Docs corpus parser·adapter 구현 | opal-be-agent | `dashboard/backend/parsers/skill_parser.py` (신규), `dashboard/backend/adapters/skill_docs_adapter.py` (신규) | DEC-2·5·9·10·11대로 구현한다. parser는 `yaml.safe_load` frontmatter + 보수적 heading/fence 추출로 description·use_cases·quick_start·usage·arguments/options·when_to_use·examples를 만들고 실패 시 `null`/`[]`을 돌린다. adapter는 registry와 두 bundled root(`opal/skills/*`, `skills/*`)를 canonical 병합해 55행 index와 별도 alias index를 만들고, 검색(이름·alias·설명·용도)·그룹/도메인 필터·facet count·related skills 정규화·pipeline 단계 요약을 제공한다. corpus root는 DI로 주입받아 호출자가 경로를 지정할 수 없게 한다. Doctor용 기존 `adapters/skill_adapter.py`는 변경하지 않는다. 두 신규 파일에 @header를 작성한다. | W-2 | P2 | AC-2, AC-3, AC-4, AC-5, C-2, C-3, C-4 |
| W-6. FE `ApiError` additive 확장 | opal-fe-agent | `dashboard/frontend/src/lib/api.ts` | DEC-7대로 `ApiError`(status·code·message·details 보존)를 추가하고 `apiClient` 실패 경로가 이를 던지게 한다. 기존 FastAPI `detail` 추출·timeout·generic message 폴백 동작과 기존 호출자 시그니처를 유지한다. `api-timeout.test.ts` 등 기존 테스트가 계속 통과해야 한다. | W-3 | P2 | AC-6, C-7 |
| W-7. 공개 응답 모델·GET 라우터 등록 | opal-be-agent | `dashboard/backend/models.py`, `dashboard/backend/routers/docs_skills.py` (신규), `dashboard/backend/main.py` | DEC-1·6대로 wireframe §5.2/§5.3의 `SkillCatalogItem`·`SkillDetailResponse`·`ExampleBlock`과 §5.4 error envelope를 Pydantic 모델로 `models.py`에 추가하고, `routers/docs_skills.py`에 `GET /api/docs/skills`·`GET /api/docs/skills/{skill_id}`만 정의한다. `main.py`에서 SPA fallback보다 앞에 router를 등록한다. source 부재는 200 partial, unknown id는 404, registry/parse 장애는 500으로 매핑하고 절대경로·stack을 응답에 싣지 않는다. 신규 라우터 파일에 @header를 작성한다. W-2가 GREEN이 되어야 한다. | W-5 | P3 | AC-1, AC-3, AC-6, C-2, C-5 |
| W-8. Docs 카탈로그·상세 화면 구현 | opal-fe-agent | `dashboard/frontend/src/pages/docs/**` (신규) | DEC-8대로 카탈로그(검색·그룹/도메인 필터·facet·카드 목록)와 상세(제목·설명·분류, Quick Start, Usage, Arguments/Options, 사용 시점, 복사 가능한 예시, 파이프라인, 관련 스킬, 원본 상대 경로)를 구현한다. query key는 목록 `q/group/domain`, 상세 canonical id를 포함한다. loading/empty(전체 0 vs 검색 0)/error(code별 복구)/source 부재 partial 상태, 복사 성공·실패 폴백, 데스크톱·모바일 레이아웃, 접근 가능한 이름과 키보드 포커스를 제공한다. 적용 불가 섹션은 거짓 기본값 대신 생략하거나 "없음"으로 표시한다. 기존 UI primitives만 사용하고 신규 의존성을 추가하지 않는다. 신규 파일에 @header를 작성한다. W-3이 GREEN이 되어야 한다. | W-6, W-7 | P4 | AC-2, AC-3, AC-5, AC-6, C-1, C-3, C-4, C-7 |
| W-9. 셸 메뉴·라우트 추가 | opal-fe-agent | `dashboard/frontend/src/components/app-shell/AppShell.tsx`, `dashboard/frontend/src/router.tsx` | `NAV_ITEMS`에 `OPAL Docs`(`/docs/skills`) 1개를 추가하고, router에 기존 셸의 child로 `/docs/skills`와 `/docs/skills/:skillId` 2개 route만 추가한다. 기존 7개 메뉴·route·active 상태·SPA shell 동작을 바꾸지 않는다. | W-8 | P5 | AC-1, C-1 |
| W-10. 프로젝트 문서·wireframe 계약 갱신 | opal-task-agent | `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `README.md`, `tasks/140-260917-opdw-스킬-문서-화면/wireframe.md` | PROJECT는 Console 메뉴 7→8과 새 Docs read-only API·설치 산출물을 반영한다. ARCHITECTURE는 §OPAL Console(274-344행)의 7개 화면 기술을 8개로 갱신하고 Docs router/adapter/parser와 source→install 데이터 흐름을 추가한다. README는 Console에 스킬 문서 화면이 생긴 사용자 기능 변경만 반영한다. wireframe §5.4 오류표의 `source_missing` 행을 DEC-1에 맞춰 "HTTP 상태 아님 — 200 partial의 `source.available=false`" 로 정정한다. `docs/CONVENTIONS.md`는 DEC-2로 alias 스키마가 바뀌지 않으므로 갱신하지 않는다. OPPB 관련 기재는 이미 반영돼 있으므로 다시 쓰지 않는다. | W-9 | P6 | AC-1, AC-8 |
| W-11. 전체 회귀 검증 | opal-test-agent | 변경 없음 (검증 실행) | ANALYSIS 검증 순서 2~4를 실행한다. `python -m pytest dashboard/backend/tests/test_skill_docs.py dashboard/backend/tests/test_main.py dashboard/backend/tests/test_routers.py` 후 `python -m pytest dashboard/backend/tests` 전체. `cd dashboard/frontend && npm test && npm run typecheck && npm run lint && npm run build`. `node --test opal/tools/skill-registry/tests/test-validate.js opal/tools/skill-registry/tests/test-match.js opal/tools/skill-registry/tests/test-verify-bundle.js`. source `validate`가 `valid:true`·canonical 55개·`unregistered:[]`를 **유지**하는지 확인한다. 실행 스코프와 명령을 결과에 함께 기록한다. | W-9, W-10 | P7 | AC-4, AC-7 |
| W-12. 설치 배포와 설치본 smoke | 사용자 확인 단계 (캡틴 직접 실행) | 변경 없음 (배포 실행) | source root에서 `./scripts/install-mac.sh`를 실행해 `[1] OPAL 설치`를 선택한다(dashboard-only 메뉴 5로는 registry+skills+FE+BE 동시 반영이 되지 않는다). 이어 `verify-bundle`로 `~/.opal/references/opal-skills-registry.json`과 `~/.opal/skills/*/SKILL.md`의 canonical set이 55/55·missing 0인지 확인한다. `curl -fsS http://127.0.0.1:7823/health`, 목록 API, `/api/docs/skills/oppb`, `/docs/skills/oppb` SPA deep-link를 확인하고, 브라우저에서 데스크톱·모바일 카탈로그→상세, 필터, alias URL 정규화, source 부재, 404, 복사 성공·실패를 확인한 뒤 기존 7개 화면을 순회한다. | W-11 | P8 | AC-1, AC-4, AC-7, AC-8, C-6 |

완료 기준 커버리지: AC-1(W-7·W-8·W-9·W-10·W-12), AC-2(W-2·W-3·W-5·W-8), AC-3(W-2·W-3·W-5·W-7·W-8), AC-4(W-1·W-2·W-4·W-5·W-11·W-12), AC-5(W-2·W-5·W-8), AC-6(W-2·W-3·W-6·W-7·W-8), AC-7(W-11·W-12), AC-8(W-1·W-4·W-10·W-12), C-1(W-8·W-9), C-2(W-2·W-4·W-5·W-7), C-3(W-2·W-4·W-5·W-8), C-4(W-2·W-3·W-5·W-8), C-5(W-2·W-7), C-6(W-12), C-7(W-3·W-6·W-8).

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. wireframe §5.4의 `source_missing` 409/422 표기가 정본으로 남아 있으면 구현자가 DEC-1과 충돌하는 오류 분기를 만든다 | 상세 API 응답 계약과 FE 오류 UI | 공개 model·오류 UI 재작업, AC-3/AC-6 불일치 | DEC-1을 PLAN 정본으로 고정하고 W-10에서 wireframe 해당 행을 정정한다. W-2가 200 partial을 테스트로 먼저 고정한다 |
| H-2. `SKILL.md` 본문 형식이 균일하지 않아 Arguments/Options·예시 추출이 스킬마다 실패할 수 있다 | AC-3의 상세 섹션 표시 | 상세 화면 다수가 빈 섹션이 되어 사용자 가치가 떨어진다 | DEC-10대로 실패는 `null`/`[]`로 두고 발명하지 않는다. W-2 fixture에 형식이 다른 스킬을 포함해 부재 표현을 검증하고, 추출률이 낮으면 별도 태스크로 본문 규약을 승격한다 |
| H-3. 요청마다 registry + 55개 `SKILL.md` + pipeline을 파싱하면 목록 응답이 느릴 수 있다 | AC-7의 회귀 없음 판정과 사용자 체감 | 카탈로그 진입 지연 | DEC-4로 캐시를 쓰지 않는 최소 경계를 택하되, W-12 smoke에서 목록 API 응답 시간을 관측하고 문제가 실측될 때만 다중 파일 fingerprint 캐시를 별도 태스크로 승격한다 |
| H-4. `verify-bundle` 추가가 기존 `validate` 분기와 인자 파싱을 건드려 배포 환경 reverse scan 생략 계약을 깰 수 있다 | `skill-registry.js:624-633`과 이를 보호하는 기존 test | 배포 환경에서 false positive 오류가 재발해 install 검증이 막힌다 | W-4를 새 분기 추가로만 한정하고, W-11에서 `test-validate.js`·`test-match.js` 통과를 GREEN 조건으로 고정한다 |
| H-5. 구현 시점에 registry 또는 source 스킬이 동시 변경되어 55/55·누락 0 전제가 깨질 수 있다 | AC-4·AC-8의 완전성 판정 | 설치본 대조 실패로 CLOSE 차단 | 구현 착수 직전 W-11에서 source `validate`를 재실행해 55/`unregistered:[]`를 재확인한다. 불일치 시 등재는 이번 범위가 아니므로 blocked로 에스컬레이션한다 |

## Release and recovery

- 적용 순서: P1(RED 테스트 3건 병렬) → P2(verifier·BE 데이터 평면·FE 오류 계약 병렬) → P3(BE 공개 라우터) → P4(FE 화면) → P5(셸 라우팅) → P6(문서·wireframe 갱신) → P7(전체 회귀) → P8(install 실행과 설치본 smoke). 선행 작업은 항상 앞선 실행 그룹에 있고, 같은 실행 그룹 안의 W는 변경 대상 파일이 겹치지 않는다.
- 검증 범위: 결정론 검증은 W-11의 pytest·vitest·`node --test`와 typecheck/lint/build다. 회귀 경계는 백엔드 기존 7개 API와 health·405, 프론트엔드 기존 7개 화면·라우트·timeout 동작, `skill-registry.js`의 기존 `validate` 계약이다. 실제 연동 검증은 W-12의 설치본 `verify-bundle`·health·목록/상세 API·SPA deep-link와 브라우저 반응형 smoke이며 이것이 유일한 수동·환경 의존 단계다.
- 실측 경계: 목록 API 응답 시간만 W-12에서 관측 항목으로 기록한다. 별도 성능 목표치는 두지 않으며, 체감 지연이 관측될 때만 H-3의 캐시 승격 판단 근거로 쓴다.
- 실패 시: P1~P5는 코드 변경만이므로 해당 W 단위 revert로 복구한다. W-12에서 설치본 검증이 실패하면 `./scripts/install-mac.sh`의 `[1] OPAL 설치`를 직전 커밋 상태에서 재실행해 배포본을 되돌린다. `~/.opal/`을 직접 편집해 복구하지 않는다([MUST] `.opal/AGENT.md` §금지사항).
