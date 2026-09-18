# DONE: OPAL Docs 스킬 문서 사이드바

## 결과

좌측 그룹 사이드바에서 스킬을 고르면 우측에 그 스킬의 `README.md`가 원문 그대로 렌더되는 단일 화면으로 교체했다. 태스크 140의 "카탈로그 카드 + 상세 2화면" 구조와 슬롯 파싱을 폐기했다.

폐기 이유는 140의 상세 화면이 비어 있었기 때문이다. 파서가 `## Usage`·`## Arguments` 같은 영문 표준 제목을 기대했으나 실제 SKILL.md는 `## 입력 분기`·`## STEP 1: TASK` 체계를 쓴다. 55개 스킬 전부에서 quick_start·usage·arguments·options·examples가 0건이었다. 제목 체계를 맞추는 대신 스킬마다 사람이 쓴 `README.md`를 SSOT로 두고 그대로 보여주는 방식으로 바꿨다.

| 항목 | 값 |
|------|-----|
| 사이드바 노출 | 55건 중 **33건** (internal-stage 21건, 폴더명 불일치 `opal-pilot-dev-short` 1건 제외) |
| 그룹 | 파일럿 12 · 오퍼레이터 14 · 독립 8 |
| 본문 출처 | 배포본 전수 55건 `origin=readme`, null 0건, 공백 0건 |
| 제거한 공개 필드 | `usage_markdown`·`when_to_use_markdown`·`quick_start`·`arguments`·`options`·`examples`·`use_cases` |
| 추가한 공개 필드 | `body{markdown,origin,source_path}` · `listed: bool` |

`listed`는 서버가 두 조건 AND로 파생한다. ① `display_group != "internal-stage"` ② 레지스트리 엔트리 `paths[0]`의 폴더명이 canonical `name`과 일치. `listed=false`여도 URL 직접 접근 상세 조회는 200이다.

## 변경 파일

**백엔드**
- `dashboard/backend/parsers/skill_parser.py` — 슬롯 파싱 5함수와 정규식·상수 제거. frontmatter(`name`·`description`) + `content_hash` + frontmatter 제거 본문만 반환
- `dashboard/backend/adapters/skill_docs_adapter.py` — `_resolve_body`(README → SKILL.md 2단 폴백, `_safe_join` 경유, 상대 `source_path`), `_is_listed`(DEC-4 두 조건) 추가. `_matches_query` haystack에서 `use_cases` 제거
- `dashboard/backend/models.py` — `SkillBody` 추가, `listed` 추가, 슬롯 7종·`ArgumentItem`·`ExampleBlock` 삭제
- `dashboard/backend/routers/docs_skills.py` — 무변경(계약대로)

**프런트엔드**
- `dashboard/frontend/src/pages/docs/SkillDocsPage.tsx` (신규) — 단일 컴포넌트가 두 라우트를 렌더. 좌측 `nav` 사이드바(3그룹, canonical+alias 병기, `aria-current`, 모바일 Sheet 토글, ScrollArea), 우측 `MarkdownView` 본문
- `dashboard/frontend/src/pages/docs/types.ts` — 새 응답 계약으로 교체
- `dashboard/frontend/src/router.tsx` — route 2개 유지, element만 교체
- `dashboard/frontend/src/pages/docs/{DocsCatalogPage,DocsDetailPage}.tsx` 및 각 테스트 — 삭제
- `dashboard/frontend/vite.config.ts` — `base: './'` → `'/'` (**PLAN 이탈**, 아래 참조)

**테스트**
- `dashboard/backend/tests/test_skill_docs.py` — RED 6건 신설, 폐기 5건 삭제, 수정 2건 + S-8 보강
- `dashboard/backend/tests/test_skill_docs_layout.py` — 실자산 단언 3건 신설(33건 집계, 분포, 전수 origin)
- `dashboard/backend/tests/fixtures/skill_docs_corpus/**` — README 유무 3조합으로 재목적화
- `dashboard/frontend/src/pages/docs/SkillDocsPage.test.tsx` (신규) — 13건

**문서**
- `docs/ARCHITECTURE.md` — OPAL Docs 절 재작성, 본문 계약·목록 노출 2행 신설
- `README.md` 886행 — 제거된 기능 기술을 사이드바 탐색+README 열람으로 교체

## 검증

시나리오 **13/13 pass, 실패 0**. RED 대상 10건 전부 `red_confirmed` 후 `scenario-lock`.

| 검증 | 결과 |
|------|------|
| `pytest dashboard/backend/tests` | 439 passed |
| `node --test` (registry 3종) | 23 pass / 0 fail |
| `npm test` | 153 passed (13 files) |
| typecheck / lint / build | 전부 exit 0 |
| `skill-registry validate` | `valid:true`, `unregistered:[]` |
| fidelity-check | `all_met: true` (13/13) |
| coverage-check | `all_covered: true` (요구 17 · 가설 7) |
| state validate / code-map validate | violations 0 / OK |
| 신규 의존성 | 0건 |

AC-1~9 · C-1~8 · H-1~7 총 24종이 전부 pass 시나리오로 커버됐다.

설치본 실측(S-12·S-13): `listed=true` 33, 전수 `origin=readme`, 404 envelope 정상, 절대경로 노출 0, 데스크톱·모바일 두 뷰포트 렌더, 기존 7화면 회귀 없음.

## PLAN 이탈

**D-1. `dashboard/frontend/vite.config.ts` 수정** — PLAN W-4의 변경 대상에 없던 파일이다. AC-9와 S-13의 "새로고침·URL 직접 접근" 항목이 이 수정 없이는 구조적으로 통과할 수 없어(화면 자체가 뜨지 않음) 범위 안으로 판단했다. 사후 회귀 6단계 전량 재실행으로 영향 없음을 확인했다.

## 실측으로 발견한 결함

**F-1. 2단 경로에서 자산 로드 실패로 화면 백지**

`vite.config.ts`의 `base: './'` 때문에 산출 `index.html`이 자산을 `./assets/...`로 참조한다. `/docs/skills`는 Console에서 **유일한 2단 경로**라 브라우저가 `/docs/assets/...`로 해석하고, 그 경로는 SPA fallback이 HTML을 돌려주어 모듈 스크립트 MIME 검사에 걸린다. 나머지 7개 화면은 전부 1단 경로라 우연히 맞아떨어져 정상 동작했다.

`base: './'`는 태스크 115에서 들어왔고 2단 경로는 태스크 140이 처음 도입했다. 즉 **140 이후 이 화면은 URL 직접 접근·새로고침에서 한 번도 뜬 적이 없다.** 메뉴 클릭 진입은 클라이언트 라우팅이라 자산을 다시 받지 않아 정상으로 보였고, 140의 검증이 거기서 멈췄다.

## 회고적 학습 후보

1. **GREEN 612건과 백지 화면이 양립했다.** 단위·통합 테스트는 컴포넌트를 직접 마운트하므로 번들 자산 경로를 검증하지 않는다. 회귀 단계도 `npm run build`의 exit code만 보고 산출 `index.html`의 자산 경로를 보지 않았다. 잡아낸 것은 real-usage 실측 하나뿐이다.
2. **픽스처 대 실자산 괴리가 또 나왔다.** W-2 픽스처 레지스트리의 `name` 필드 부정확을 "영향 없음"으로 넘겼다가 `opds` 레코드 유실로 이어졌다. 같은 실패가 태스크 039·044·045에서도 기록돼 있다. 이번에 실자산 전수 단언(`records` 기준, `len(order)` 금지)을 테스트에 박아 재발을 막았다.
3. **파서가 기대하는 문서 구조를 실물로 확인하지 않았다.** 태스크 140은 슬롯 7종을 만들면서 실제 SKILL.md 제목 분포를 세지 않았다. 세어봤다면 `## 쓰는 법`이 106회 등장하고 그중 1개 파일에만 있다는 사실이 바로 드러났다.

## 인계 사항

- **불안정 테스트 1건 미해결** — W-4 직후 `npm test`에서 1건 실패 후 총 8회 실행에서 재현되지 않았고 이름을 확보하지 못했다. 원인 미확정.
- **`ownership-tool` 훅** — `~/.claude/settings.json`이 이 저장소에 없는 도구를 PreToolUse(`Edit|Write|NotebookEdit|Bash`)·SessionStart에서 참조한다. 파일 부재로 훅이 오류를 내면 해당 도구가 전부 차단되고, install이 `~/.opal`을 재구성할 때마다 재발한다. 이번에는 빈 스텁 파일로 넘겼으며 근본 해결이 아니다.
- **`opal-pilot-dev-short` 폴더 제거** — 레지스트리 multi-alias 지원 후로 이연(사용자 결정).

## 참고

- 상세 기록: `run/deviations.md`
- 실측 증적: `run/s13-desktop.png`, `run/s13-mobile.png`
- 태스크 140: `tasks/140-260917-opdw-스킬-문서-화면/`
