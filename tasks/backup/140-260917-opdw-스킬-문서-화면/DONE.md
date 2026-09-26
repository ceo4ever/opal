# DONE: OPAL Docs 스킬 문서 화면

## 결과

OPAL Console에 `OPAL Docs` 메뉴와 읽기 전용 스킬 문서 API를 추가했다. 목록·상세 두 엔드포인트가 레지스트리와 번들 `SKILL.md`, 선택적 `pipeline.json`을 canonical 병합해 55개 스킬을 반환하며, 소스 저장소와 설치본 두 레이아웃 모두에서 동작한다.

**달성한 것**

- 읽기 전용 공개 표면 2개(`GET /api/docs/skills`, `GET /api/docs/skills/{skill_id}`). 쓰기 메서드는 405, traversal은 404, 응답에 로컬 절대경로를 싣지 않는다.
- corpus 레이아웃 해석기. 소스 저장소(`opal/core/references/opal-skills-registry.json` + `opal/skills` + `skills`), 설치본(`~/.opal/references/...` + `~/.opal/skills`), 테스트 fixture 세 형태를 모두 해석한다.
- canonical identity를 레지스트리 `name`에서 파생한다. `paths`가 다른 스킬과 겹치는 프로필 엔트리(`opal-pilot-dev-short`)도 독립 레코드로 보존된다.
- `skill-registry.js verify-bundle` 신설. 레지스트리 canonical set과 skills root 폴더 집합을 양방향 대조하고 불일치 시 non-zero exit. 기존 `validate`의 배포 환경 reverse scan 생략 계약은 무변경이다.
- 프런트엔드 `ApiError` additive 확장. `status`·`code`·`details`를 보존하되 기존 `detail` 추출·timeout·generic 폴백 동작을 유지한다.
- 셸 메뉴 1개와 라우트 2개 추가. 기존 7개 메뉴·라우트·active 상태는 그대로다.

**달성하지 못한 것**

- 상세 화면 본문이 비어 있다. 파서가 `## Usage`·`## Arguments` 같은 영어 표준 heading을 전제하는데 실제 `SKILL.md` 55개는 `## 입력 분기`·`## STEP 1: TASK` 같은 다른 구조를 쓴다. 전수 측정 결과 `quick_start` 0/55, `usage_markdown` 0/55, `arguments` 0/55, `options` 0/55, `examples` 0/55다.
- 그 결과 AC-3(상세 섹션 표시)과 S-16(브라우저 확인)이 충족되지 않았다. 후속 태스크가 사이드바 + README 렌더 구조로 교체한다.

**유지한 경계**

- 기존 Console 7개 화면·API·`skill_adapter.py`(Doctor용)·`markdown-view.tsx`·installer 복사 로직은 변경하지 않았다.
- 백엔드 캐시를 도입하지 않았다. 프런트엔드 30초 query stale time에 의존한다.
- 레지스트리 데이터를 변경하지 않았다. OPPB 3건은 태스크 132에서 이미 등재된 상태였다.
- 신규 npm·Python 의존성 0건.

## 변경 파일

- `dashboard/backend/parsers/skill_parser.py`
- `dashboard/backend/adapters/skill_docs_adapter.py`
- `dashboard/backend/routers/docs_skills.py`
- `dashboard/backend/models.py`
- `dashboard/backend/main.py`
- `dashboard/backend/tests/test_skill_docs.py`
- `dashboard/backend/tests/test_skill_docs_layout.py`
- `dashboard/backend/tests/fixtures/skill_docs_corpus/**`
- `dashboard/backend/tests/fixtures/skill_docs_corpus_broken_yaml/**`
- `dashboard/frontend/src/pages/docs/DocsCatalogPage.tsx`
- `dashboard/frontend/src/pages/docs/DocsDetailPage.tsx`
- `dashboard/frontend/src/pages/docs/types.ts`
- `dashboard/frontend/src/pages/docs/DocsCatalogPage.test.tsx`
- `dashboard/frontend/src/pages/docs/DocsDetailPage.test.tsx`
- `dashboard/frontend/src/lib/api.ts`
- `dashboard/frontend/src/lib/api-error.test.ts`
- `dashboard/frontend/src/components/app-shell/AppShell.tsx`
- `dashboard/frontend/src/router.tsx`
- `dashboard/frontend/src/test/setup.ts`
- `opal/tools/skill-registry/skill-registry.js`
- `opal/tools/skill-registry/README.md`
- `opal/tools/skill-registry/tests/test-verify-bundle.js`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `README.md`

## 검증

- `python -m pytest dashboard/backend/tests -q` → exit 0, 434 passed
- `cd dashboard/frontend && npm test` → exit 0, 14 files / 155 tests
- `npm run typecheck` / `npm run lint` / `npm run build` → 전부 exit 0
- `node --test opal/tools/skill-registry/tests/{test-validate,test-match,test-verify-bundle}.js` → exit 0, 23/23
- `node opal/tools/skill-registry/skill-registry.js validate` → `valid:true`, `unregistered:[]`
- `verify-bundle` 소스 저장소 대상 → `{"ok":true,"total":55,"missing_source":[],"unregistered":[],"ambiguous_alias":[]}`, exit 0
- `verify-bundle` 설치본(`~/.opal`) 대상 → 동일 결과, exit 0
- 설치본 런타임 실측 → `/health` 200, 목록 API items 55(`opd`·`opds` 모두 포함), `/api/docs/skills/oppb` 200 + pipeline 6단계, alias `opds` → canonical `opal-pilot-dev-short`, POST 405, traversal 404, SPA deep-link 200
- `code-scan validate --changed` → `ok:true`, `newly_uncovered 0`
- 컨벤션 자동 진단 3영역 → Critical 0 / High 0 (Console BE는 1차 High 1건을 재지시로 해소 후 재검사)
- `state-tool validate` → violations 0건
- 시나리오 18건 → 16 pass / 0 fail / 2 blocked. `test-scenario.json`이 원본을 소유한다.

## 회고적 학습 후보

없음

## 참고

- 이 태스크의 산출물은 `feat/140-opdw-스킬-문서-화면` 브랜치에만 존재한다. 상세 화면이 비어 있는 상태를 main에 배포하지 않기 위한 소유자 결정이다. 후속 태스크가 화면을 완성한 뒤 함께 머지한다.
- S-15는 pass, S-16은 fail이다. 두 시나리오 모두 설치 후 소유자 수행 단계였고, S-15(설치본 API·deep-link)는 통과했으나 S-16(브라우저 상세 확인)에서 본문 미표시가 드러났다.
- 후속 태스크 범위: 좌측 그룹 사이드바(검색·필터 제거, `op-*` 21개 제외) + 우측 `README.md` 렌더, README 없으면 `SKILL.md` 폴백. 55개 스킬의 README는 별도 커밋 `4724340`으로 main에 이미 반영됐다.
- `opal-pilot-dev-short`는 `opds`가 `opal-pilot-dev`로 통합돼 폴더의 `SKILL.md`가 실행에 쓰이지 않는다. DEPRECATED 배너를 달았고 폴더·레지스트리 엔트리 제거는 레지스트리 다중 alias 지원을 선행한 뒤 별도 태스크로 다룬다.
