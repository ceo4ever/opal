# AGENTIC-LOG: OPAL Docs 스킬 문서 화면

> 모드: semi-agentic — EXECUTE 이후 구간은 PM 자율 진행, CLOSE 진입만 캡틴 승인.
> 생성: 2026-09-18 15:02 (EXECUTE 첫 행 진입 시점)

## PM 판단 기록

| 시점 | 판단 | 근거 |
|---|---|---|
| 2026-09-18 15:02 | EXECUTE 진입 전 baseline 재확인 — 재기준화 불필요 | 세션 도중 HEAD가 `0ea0f54` → `4655c27`(태스크 127 E2E 하네스 병합)로 이동. PLAN 전제를 재실측한 결과 `skill-registry.js validate` `valid:true`·`unregistered:[]`, NAV 7개·route 7개, `api.ts` 117행·`main.py` 183행으로 인용이 모두 유효해 PLAN 재작성 없이 진행 |
| 2026-09-18 15:02 | Git 사전 점검 통과 | 워킹트리 미커밋 변경이 태스크 140 자체 산출물 4건과 미추적 4건뿐이며 PLAN 변경 대상과 겹치지 않음 |
| 2026-09-18 15:02 | RED 대상 11건 확정 | TEST-SCENARIO `시점` 열이 `구현 전 RED`인 S-1·S-3~S-12만 `red_required: true`. `scenario-status` red_required 11 확인 |
| 2026-09-18 15:02 | S-15·S-16 profile을 `collaborative`로 확정 | 최초 `hybrid`/`browser`로 기재했으나 `test-tool`의 `EXECUTOR_MATRIX`가 `hybrid`에 human executor를 불허하고 `browser`는 browser executor만 허용해 `executor contract mismatch`로 거부됨. 두 시나리오 모두 사람이 주체이고 handoff 8필드를 가지므로 `collaborative`가 실제 성격에 부합 |
| 2026-09-18 15:05 | P1 배치를 3개 워커 병렬로 디스패치 | PLAN `Work items`의 W-1·W-2·W-3이 같은 실행 그룹 P1이고 변경 대상(`opal/tools/skill-registry/tests/`, `dashboard/backend/tests/`, `dashboard/frontend/src/**/*.test.*`)이 겹치지 않아 `pm/dispatch-process.md` Step 1의 비중첩 변경 범위 계약을 충족 |
| 2026-09-18 15:05 | 세 워커 모두 RED mode로 구현 금지를 명시 주입 | `red-first.md` §1.5 — 구현자와 다른 주체가 실패 테스트를 작성해야 하며, GREEN은 W-4·W-5·W-6 배치가 수행 |

## 관측된 하네스 이슈

| 시점 | 이슈 | 영향 |
|---|---|---|
| 2026-09-18 15:05 | Stop hook이 서브에이전트 실행 중에도 `transition_action=continue`만 보고 세션 종료를 차단한다 | 워커가 소유한 행이 `in_progress`인 동안 PM은 대기가 정상 행동인데, hook은 이를 "PM이 멈췄다"로 판정한다. PM이 실질 작업 없는 응답을 반복 생성하게 되며 이번 태스크에서 3회 발생했다(PLAN 워커·evaluator·P1 배치). 판정에 "활성 서브에이전트 존재 여부" 축이 없다 |

## 배치 결과 실측 검증

| 시점 | W | PM 실측 재현 결과 |
|---|---|---|
| 2026-09-18 15:08 | W-1 | `node --test opal/tools/skill-registry/tests/test-verify-bundle.js` exit 1, tests 4 / pass 0 / fail 4. `skill-registry.js`·`test-validate.js`·`test-match.js` 변경 0건(git diff 빈 출력). S-1 red_confirmed |
| 2026-09-18 15:08 | W-3 | `npx vitest run` 4파일 exit 1, Test Files 3 failed / 1 passed, Tests 5 failed / 10 passed. 기존 `api-timeout.test.ts`는 전량 pass로 회귀 없음. `api.ts`·`router.tsx`·`AppShell.tsx` 변경 0건. S-11·S-12 red_confirmed |

### W-8 인계 사항 (W-3이 테스트로 고정한 계약)

W-3의 RED 테스트가 FE 컴포넌트 이름을 계약으로 고정했다. W-8 구현자는 이를 따라야 GREEN이 된다.

- `dashboard/frontend/src/pages/docs/DocsCatalogPage.tsx` — export `DocsCatalogPage`
- `dashboard/frontend/src/pages/docs/DocsDetailPage.tsx` — export `DocsDetailPage`
- props 없는 형태로 import된다

PM 판단: 이 이름 고정은 RED-first에서 테스트가 공개 인터페이스를 먼저 선언한 정상 결과이며 PLAN 범위(`src/pages/docs/**` 신규)를 벗어나지 않는다. PLAN을 수정하지 않고 인계 사항으로만 기록한다.
| 2026-09-18 15:09 | W-2 | `pytest dashboard/backend/tests/test_skill_docs.py -q` exit 1, `2 failed, 32 errors`. 실패 원인이 `ModuleNotFoundError: dashboard.backend.routers.docs_skills` 34건 단일 — 구현 부재로 인한 정상 RED. 구현 파일·`test_main.py`·`test_routers.py` 변경 0건. S-3~S-10 red_confirmed |

### W-5·W-7 인계 사항 (W-2가 테스트로 고정한 계약)

- corpus root DI 지점: `dashboard.backend.routers.docs_skills.get_skill_docs_corpus_root` — 테스트가 FastAPI `dependency_overrides`로 이 심볼을 오버라이드한다. W-7 라우터가 이 이름으로 의존성을 노출해야 GREEN이 된다.
- fixture corpus 구조: `tests/fixtures/skill_docs_corpus/{registry.json, opal_skills/*, skills/*}` — adapter가 registry 1개 + 두 skills root를 받는 형태를 전제한다.
- 오류 fixture 2종: `skill_docs_corpus_broken_yaml`(parse_error), `skill_docs_corpus_missing_registry`(registry_unavailable).
| 2026-09-18 15:13 | W-6 | `npx vitest run api-error.test.ts api-timeout.test.ts` exit 0, Test Files 2 passed / Tests 15 passed. 기존 timeout 6건 포함 회귀 없음. `api.ts` 1건만 변경 |
| 2026-09-18 15:13 | W-4 | 테스트·회귀는 통과(verify-bundle 4/4, 기존 19/19, validate valid:true)했으나 **실제 registry에 대해 동작하지 않음 — Fail** |

## PM Gate Fail — W-1·W-4 계약 오류

| 항목 | 내용 |
|---|---|
| 증상 | `verify-bundle --registry opal/core/references/opal-skills-registry.json --skills-root opal/skills --skills-root skills` → `{"ok":false,"error":"registry_not_found","total":0}` |
| 원인 | W-1의 RED fixture가 registry를 평탄 `skills: [...]` 배열로 합성했다(`test-verify-bundle.js:64`). 실제 registry 스키마는 `groups`(그룹명 → 엔트리 배열)이며 `flattenGroups()`(`skill-registry.js:74-90`)가 이를 평탄화한다. W-4는 테스트에 충실하게 `Array.isArray(registry.skills)`를 요구하도록 구현(`skill-registry.js:988`)해 실제 registry를 malformed로 판정한다 |
| 영향 | AC-8("설치본 레지스트리에서도 누락 0건 검사 통과")을 증명할 수 없다. S-15의 설치본 대조 step도 실패한다 |
| 판정 | RED fixture가 실재하지 않는 스키마를 계약으로 고정한 오류다. 기대 계약의 **약화**가 아니라 **오류 정정**이므로 테스트 수정이 필요하다 |
| 조치 | ① opal-test-agent에 W-1 재지시 — fixture를 실제 `groups` 스키마로 교체하고 4개 단언은 유지, RED 재관찰 ② opal-task-agent에 W-4 재지시 — `flattenGroups()`를 사용하도록 수정하고 실제 registry 대상 실행까지 검증. 각 1회 한도(`guards.md` §자동 루핑 제약) |
| 2026-09-18 15:18 | W-5 | `pytest dashboard/backend/tests -q` → `2 failed, 389 passed, 32 errors`. 실패·에러가 전부 `test_skill_docs.py`에 국한(비-test_skill_docs 실패 0건)되며 원인은 W-7 라우터 부재. 신규 2건 @header 정상(layer=service, domain=console). 구현 파일·테스트 미수정 — Pass |
| 2026-09-18 15:18 | W-1 재지시 | 새 `groups` fixture로 `node --test test-verify-bundle.js` exit 1, tests 4 / pass 0 / fail 4. TC1이 `opal-pilot`·`op-dev` 2그룹으로 평탄화까지 고정. `skill-registry.js` 미접촉 — PM의 결함 분석이 실측 확인됨 |

### 잠금 이후 RED 재기록 시도 결과

W-1 재지시 워커의 `scenario-red --id S-1` 재호출이 `exit 12, scenario_already_locked`로 거부됐다. PM 판단: `scenario-lock` 이후 RED 증거 덮어쓰기를 막는 정상 동작이고, S-1의 기존 증거는 유효하며 이번 재지시는 fixture 코드 정정이 목적이었다. 정정 후 실패 로그(위 행)를 증거로 대체한다. 별도 조치 없음.

### 재지시하지 않은 기록 — W-2 fixture의 registry name 부정확성

fixture registry가 `name: onboarding`(폴더 `opal-onboarding`)·`name: skill-manager`(폴더 `opal-skill-manager`)처럼 **registry name 자리에 frontmatter name을 넣었다**. 실제 registry에서는 두 값이 같다(`opal-skills-registry.json`의 canonical은 `opal-onboarding`·`opal-skill-manager`).

PM 판단: 재지시하지 않는다.
- W-5가 canonical을 `paths[0]`의 폴더 basename에서 파생해 이 부정확성을 흡수했고, 실제 registry에서는 registry name = 폴더 basename이라 동작이 동일하다. DEC-5의 "= 폴더 basename" 규칙과도 정합한다.
- AC-5의 실제 메커니즘(frontmatter name → 파생 alias)은 fixture의 `SKILL.md`가 `name: onboarding`을 그대로 갖고 있어 여전히 검증된다.
- 재지시 1회 한도는 실제 동작을 바꾸는 결함(W-1·W-4 계열)에 쓰는 것이 우선순위상 맞다.
| 2026-09-18 15:18 | W-4 재지시 | 4개 조건 전부 PM 실측 재현 통과 — ①verify-bundle 4/4 exit 0 ②기존 19/19 exit 0 ③validate valid:true·unregistered:[] ④**실제 registry** exit 0, stdout 1줄 `{"ok":true,"total":55,"missing_source":[],"unregistered":[],"ambiguous_alias":[]}`, stderr 0바이트. PM 독립 계산값과 완전 일치 — Pass. P2 완료 |
| 2026-09-18 15:23 | W-7 | `pytest test_skill_docs.py -q` 34 passed exit 0, 전체 `423 passed` exit 0(기존 389+신규 34, 회귀 0), @header layer=router 조회 정상, 응답에 절대경로 미노출 확인 — 테스트 기준 Pass |

## PM Gate Fail — 운영 corpus 레이아웃 불일치 (W-7이 자진 신고)

| 항목 | 내용 |
|---|---|
| 증상 | adapter가 `corpus_root/registry.json` + `corpus_root/opal_skills/` + `corpus_root/skills/` 레이아웃을 전제한다(`skill_docs_adapter.py:37-38,184`). 실제 배포본은 `~/.opal/references/opal-skills-registry.json` + `~/.opal/skills/`이고 `~/.opal/opal_skills`는 존재하지 않는다. 소스 저장소는 `opal/core/references/opal-skills-registry.json` + `opal/skills/` + `skills/`다 |
| 원인 | W-2의 fixture가 실재하지 않는 물리 레이아웃을 합성했고 W-5가 그 레이아웃에 맞춰 구현했다. **fixture가 실재를 대표하지 않아 생긴 세 번째 결함**(① registry 평탄 `skills[]` ② registry name=frontmatter name ③ 이번 레이아웃) |
| 영향 | 테스트는 34/34 GREEN이지만 실제 Console은 목록을 만들 수 없다. AC-1·AC-8과 S-15·S-16이 실패한다 |
| 왜 테스트가 못 잡았나 | 모든 backend 테스트가 fixture root만 DI로 주입한다. **실제 배포본·소스 레이아웃을 입력으로 쓰는 테스트가 0건**이다 |
| 조치 | ① opal-test-agent — 배포본·소스 두 실레이아웃 해석을 고정하는 RED 테스트 추가 ② opal-be-agent — 레이아웃 해석기 구현 후 실제 두 루트로 실행 검증. 기존 34건 단언은 불변 |
| 2026-09-18 15:27 | 레이아웃 RED | `pytest test_skill_docs_layout.py -q` exit 1, `5 failed, 1 passed`. 실패 원인 전부 `RegistryUnavailableError: registry.json not found under <corpus_root>` — 실레이아웃 미지원 확인. 전체 `5 failed, 424 passed`로 기존 계약 약화 0 — PM 결함 분석 실측 확인 |

## PM Gate Fail — canonical 파생 규칙 위반으로 opds 소실

| 항목 | 내용 |
|---|---|
| 증상 | 소스·배포본 두 루트 모두 `len(corpus.records)` = **54**인데 registry canonical은 55다. 누락은 `opal-pilot-dev-short`(alias `opds`) 1건 |
| 원인 | adapter가 canonical을 registry `name`이 아니라 `Path(paths[0]).parent.name`에서 파생한다. `opal-pilot-dev-short`의 `paths`는 `opal-pilot-dev/SKILL.md`를 가리키므로(같은 SKILL 파일을 공유하는 프로필 엔트리) canonical이 `opal-pilot-dev`로 접혀 기존 레코드와 충돌한다. 폴더 `opal/skills/opal-pilot-dev-short/SKILL.md`는 실제로 존재한다 |
| 계약 위반 | PLAN DEC-5 "canonical identity는 registry `name` = 폴더 basename 하나뿐". AC-4(미등재 0)·AC-5(중복 카드 0)·C-3(그룹 누락 금지)도 함께 깨진다 |
| 왜 테스트가 못 잡았나 | ① 레이아웃 테스트가 `len(corpus.order)`(55, 중복 포함)를 세어 `records`(54)의 소실을 못 본다 ② W-2 fixture가 registry `name` 자리에 frontmatter name(`onboarding`)을 넣어, canonical을 registry name에서 파생하면 fixture가 깨지도록 만들어 뒀다 |
| 워커 보고 오류 | 구현 워커가 "canonical 55건"이라 보고했으나 실측은 54다. `order`를 센 것으로 보인다 |
| PM 자기 정정 | 앞서 W-2 fixture의 registry name 부정확성을 "실동작에 영향 없음"으로 판단해 재지시하지 않았다. **그 판단이 틀렸다** — 그 fixture가 구현을 잘못된 canonical 규칙으로 유도해 opds 소실을 낳았다 |
| 조치 | ① opal-test-agent — fixture registry name을 폴더 basename과 일치시키고(frontmatter name 차이는 유지), `order` 중복 0 + opds 계열(같은 paths를 공유하는 별도 엔트리) 분리 보존을 RED로 추가 ② opal-be-agent — canonical을 registry `name`에서 파생하도록 정정 |
| 2026-09-18 15:38 | fixture 정정 RED | `pytest dashboard/backend/tests -q` → `7 failed, 427 passed`. 신규 7건이 전부 RED이고 기존 단언 약화 0. 실패 내용이 PM 실측 결함과 정확히 일치(라우트 404·order 중복·records 54 vs 55·배포본 동일 소실) |
| 2026-09-18 15:38 | 영향 범위 확정 | registry 전체에서 `paths` 공유 그룹은 1개(`opal-pilot-dev`+`opal-pilot-dev-short`)뿐이고 name≠paths폴더명도 1건뿐 — 54→55 정확히 1건 복원이면 충분하며 숨은 소실 없음 |
| 2026-09-18 15:40 | canonical 정정 | PM 실측 재현 — 전체 `434 passed` exit 0(RED 7건 전부 전환, 회귀 0). 소스·배포본 두 루트 모두 `records=55 order=55 uniq=55`, `opal-pilot-dev`·`opal-pilot-dev-short` 각각 존재, opds source_path가 각각 `opal/skills/...`·`skills/...` 상대경로이고 `available=true` — Pass. P3 backend 완료 |
| 2026-09-18 15:49 | 실API 점검 | 소스 corpus로 TestClient 엔드투엔드 — 목록 200/items 55, opd·opds 둘 다 포함, 그룹 분포 pilot 12·internal-stage 21·standalone 8·operator 14(0건 그룹 없음 → C-3 실데이터 충족), alias `opds` 상세 200→canonical opal-pilot-dev-short, `oppb` pipeline steps 6(P0~P5), POST 405, traversal 404, 절대경로 누출 없음 |
| 2026-09-18 15:49 | W-8 | `npx vitest run src/pages/docs` exit 0, Test Files 2 passed / Tests 15 passed. typecheck는 exit 2이고 오류가 정확히 1건 — `DocsDetailPage.test.tsx(18,21) TS6133 'ApiError' 미사용 import`. 구현 파일 타입 오류 0 |

### PM 승인 — 범위 밖 변경 1건 수락 (`src/test/setup.ts`)

W-8 워커가 `dashboard/frontend/src/test/setup.ts`에 happy-dom `navigator.clipboard` 폴리필을 추가하고 자진 신고했다. PM 판단: **수락**.
- happy-dom이 `navigator.clipboard`를 getter-only 상속 프로퍼티로 노출해 테스트의 `Object.assign` 대역이 TypeError를 내고 **clipboard 테스트 4건이 실행 자체가 불가**했다. 기능 우회가 아니라 환경 갭 해소다.
- 같은 파일에 이미 있는 `window.localStorage` 폴리필(zustand persist 대응)과 동일 패턴·동일 성격이며, `Object.defineProperty`로 좁게 재정의하고 @header description도 갱신했다.
- 테스트 어서션·계약 변경 0건. PLAN W-8의 변경 대상에는 없지만 W-8 완료 기준(S-12 복사 시나리오)을 만족시키기 위한 필수 인프라라 별도 Work item으로 승격하지 않고 W-8에 귀속한다.
| 2026-09-18 15:53 | 배포본 API 점검 | `~/.opal` corpus root로 TestClient — 목록 200/items 55, opd·opds 둘 다, 그룹 분포 소스와 동일, alias opds 상세 200, 없는 id 404 skill_not_found, 절대경로 누출 없음 |
| 2026-09-18 15:53 | import 정리 | typecheck exit 0(오류 0), docs 15 passed 유지, lint·build exit 0. 워커가 "쓸 단언이 없어 dead import만 제거"로 판단 — 억지 단언 추가를 피한 올바른 선택 |
| 2026-09-18 15:53 | W-9 | NAV 8개·route 9개 실측 확인, 기존 7개 `to` 값·순서 보존(`/`·projects·tasks·memory·doctor·brain·**docs/skills**·settings). 기존 화면 회귀 없음 |
| 2026-09-18 15:53 | FE 전체 | `npm test` exit 0 — **Test Files 14 passed / Tests 155 passed**. typecheck exit 0, lint exit 0 |

### 검증 순서 함정 1건 (W-11 인계)

`npm test`의 `api-env-files.test.ts` S-2가 "`npm run build`가 저장소 `dist/`를 남기지 않는다"를 단언한다. 앞선 배치가 검증차 `npm run build`를 실행해 `dashboard/frontend/dist/`(gitignore 대상, mtime 15:50)가 남았고 그 때문에 이 1건이 실패했다. PM이 `dist/`를 scratchpad로 이동하자 4/4 통과했다.

**W-11 인계**: 전체 회귀는 `npm test` → typecheck → lint → **build를 마지막에** 수행한다. build 이후 `npm test`를 다시 돌리려면 `dist/`를 먼저 정리해야 한다. 이동한 사본은 `/private/tmp/claude-501/-Volumes-Data-AIStudio-workspace-ai-framework/af9c8527-01aa-4122-b58f-d891921b3c71/scratchpad/dist-backup/dist-1550`에 있고 재생성 가능한 산출물이다.
| 2026-09-18 15:55 | W-10 | 조건 1·2 실측 0건 통과 — `grep "7개 화면" docs/` 0건, `grep source_missing wireframe.md` 0건. 변경 파일이 `docs/ARCHITECTURE.md`·`docs/PROJECT.md`·`wireframe.md` 3건으로 범위 준수 |
| 2026-09-18 15:55 | W-11 사전 | PM이 문서 외 검증을 선실행 — backend 434 passed, `node --test` 3파일 23/23, source validate valid:true·unregistered:[] |

### PM 판단 — README.md 미갱신 수락

W-10 워커가 README를 고치지 않고 "Console 화면 목록·개수를 언급하는 사용자 기능 서술이 없어 정정할 앵커가 없다"고 보고했다. PM 실측: README에서 Console 관련 언급은 `:372`·`:456` 두 줄뿐이고 둘 다 `//opdw`·`//oppd` 사용 예시 문장이라 Console 화면 구성과 무관하다. PLAN W-10은 "Console에 스킬 문서 화면이 생긴 사용자 기능 변경만 반영"이었으므로 갱신 대상 없음이 맞다 — 수락한다.
| 2026-09-18 15:59 | W-11 | 전 항목 PM 기대치와 일치, 회귀 0, changed_files 빈 배열. backend 서브셋 155·전체 **434 passed**, `node --test` **23/23**, validate `valid:true`, verify-bundle `{"ok":true,"total":55,...}` 단일 라인, FE `npm test` **14 files/155 tests**, typecheck·lint exit 0, build exit 0(맨 마지막). 실자산: 두 corpus root 각각 canonical 55·opd·opds 존재·목록 200/items 55·절대경로 미노출·POST 405·traversal 404 |

## W-12 인계 — 캡틴이 직접 수행할 설치·확인 절차

배포와 브라우저 확인은 소유자 단계다(PLAN W-12, S-15·S-16 profile `collaborative`). 아래 순서로 수행한다.

| # | 명령·행동 | 기대 |
|---|---|---|
| 1 | 저장소 루트에서 `./scripts/install-mac.sh` 실행 → `[1] OPAL 설치` 선택 | 오류 없이 완료. 메뉴 5(dashboard만)로는 registry+skills+FE+BE 동시 반영이 되지 않는다 |
| 2 | `node opal/tools/skill-registry/skill-registry.js verify-bundle --registry=~/.opal/references/opal-skills-registry.json --skills-root=~/.opal/skills` | exit 0, `{"ok":true,"total":55,"missing_source":[],"unregistered":[],"ambiguous_alias":[]}` |
| 3 | `curl -fsS http://127.0.0.1:7823/health` | 200 |
| 4 | `curl -fsS http://127.0.0.1:7823/api/docs/skills` | 200, items 55 |
| 5 | `curl -fsS http://127.0.0.1:7823/api/docs/skills/oppb` | 200, pipeline 단계 P0~P5 |
| 6 | 브라우저로 `http://127.0.0.1:7823/docs/skills/oppb` 직접 진입 | SPA shell 200 (deep-link) |
| 7 | 데스크톱·모바일(약 390px)에서 카탈로그→검색·필터→상세→예시 복사, alias URL(`/docs/skills/opds`) 정규화, 없는 alias 404, 기존 7개 화면 순회 | S-16 assertions 8종 |

PM이 설치 전 예행으로 2번을 이미 실행해 `{"ok":true,"total":55,...}`를 확인했다(배포본 skills 55폴더·registry canonical 55건). 3~7은 install로 FE/BE 산출물이 배포된 뒤에만 유효하다.

## TEST 1차 결과 — 13 pass / 3 fail / 2 blocked, PM 원인 분석

| S | 워커 판정 | PM 분석 | 조치 |
|---|---|---|---|
| S-14 | fail | **환경 아티팩트**. `dashboard/frontend/dist`(mtime 16:03)는 W-11이 마지막에 실행한 `npm run build` 산출물이다. `api-env-files.test.ts`가 "저장소 dist/를 남기지 않는다"를 단언해 실패했다. 제품 결함 아님 | PM이 `dist`를 scratchpad로 이동 후 재실행·재판정 |
| S-17 | fail | **정당한 실패**. README에 Console 스킬 문서 화면 언급이 0건이다. PM이 앞서 W-10의 README 미갱신을 "고칠 앵커 없음"으로 수락했으나 README에는 `## 아키텍처 개요`(862행)·`## 독립 스킬 사용법`(715행) 등 반영할 자리가 실제로 있다 — **PM 판단 오류** | README 갱신 재지시 후 재판정 |
| S-18 | fail | **오탐**. 지목된 `?? .claude/skills/`는 `html-diagram` 스킬이고 mtime 2026-09-13으로 이 태스크(09-17 시작)보다 **5일 앞선다**. 이 태스크가 만든 변경이 아니며 `~/.opal/` 편집 흔적은 0건이다 | 사전 존재 미추적 항목임을 증거에 명시하고 재판정 |
| S-15·S-16 | blocked | 설계대로. 설치 후 사람 협업 시나리오이며 W-12에서 캡틴이 수행 | 유지 |

## TEST 재판정 결과 — 16 pass / 0 fail / 2 blocked

| 2026-09-18 16:12 | S-14 | pass(real-http) — dist 부재 확인 후 재실행. backend 434 / node 23·23 / FE 14 files·155 tests / typecheck·lint·build 전부 exit 0. build가 마지막이라 `dist/`는 다시 생성됨(후속 `npm test` 전 정리 필요) |
| 2026-09-18 16:12 | S-17 | pass(real-http) — grep 3종(7개 화면 0건·source_missing 0건·OPAL Docs 1건)에 더해 네 문서 `git diff` 육안 확인으로 사실관계(Console 8개 화면·Docs API 2종·source 부재=200 partial) 일치 |
| 2026-09-18 16:12 | S-18 | pass(real-http) — 변경이 전부 `opal/`·`dashboard/`·`docs/`·`tasks/`·`README.md` 내. `.claude/skills/` mtime 2026-09-13으로 사전 존재 확인, `~/.opal/` 직접 편집 흔적 0건 |

`scenario-status` 최종: `passed 16 / failed 0 / blocked 2 / total 18`, `red_confirmed 11/11`, `locked true`.

### TEST PM Gate 진행 상황

| 항목 | 결과 |
|---|---|
| test-scenario.json 필수 시나리오 PASS·FAIL 0 | ✅ 16 pass / 0 fail (blocked 2는 설치 후 소유자 단계) |
| 실제 실행 증거 존재 | ✅ 각 S의 evidence에 명령·exit·출력 기록 |
| @header 커버리지(`code-scan validate --changed`) | ✅ `ok:true`, `newly_uncovered 0`, pre_existing 1(README.md, 비차단) |
| 컨벤션 자동 진단 | 진행 중 — Framework·Console BE·Console FE 3영역 병렬 |
| TEST-SCENARIO.md에 결과·증거 미기록 | ✅ 워커가 `scenario-mark`로만 기록, 문서 무수정 |

## 컨벤션 자동 진단 (PM Gate §13)

영역 분할 근거: `docs/PROJECT.md` §프로젝트 구성 prefix 매칭 — Framework(`opal/`) / Console BE(`dashboard/backend/`) / Console FE(`dashboard/frontend/`).

| 영역 | 대상 | 결과 | Critical | High |
|---|---|---|---|---|
| Framework | 3파일 | pass | 0 | 0 |
| Console BE | 7파일 | **fail** | 0 | **1** |
| Console FE | 10파일 | 진행 중 | - | - |

### Console BE High 1건 — PM 실측 확인

`dashboard/backend/main.py:6`의 `@header.description`이 "7개 라우터 등록"이라 서술하나 실제 `app.include_router` 호출은 **8개**다(`main.py:136-143`, 마지막이 `docs_skills`). `@header.depends`에도 `routers.docs_skills`가 누락됐다.

- 위반 기준: `docs/CONVENTIONS.md` §@header 규칙(T0) "현재 사실만 기재", `.opal/AGENT.md` §도메인 검토 "@header 현재 사실 규칙"
- 판정: PM Gate §13 "Critical 또는 High ≥1건 → Fail" → `opal-be-agent` 재지시 1회
- 나머지 6개 BE 파일(models.py·routers/docs_skills.py·adapters·parsers·테스트 2건)은 위반 0건

### 이월 — Console BE 컨벤션 검사의 구조적 결측

검사기가 `missing_capabilities`를 보고했다: `dashboard/backend/`에 Python 전용 컨벤션 문서가 없고 formatter·linter 실행 설정(pyproject.toml 등)도 없다. Console BE 영역 검사가 @header·네이밍 수준에서만 성립한다는 뜻이다. 이번 태스크 범위 밖이므로 CLOSE 회고 개선 후보로 올린다.

### 빌드 산출물 확인 (S-15·S-16 전제 점검)

`dashboard/frontend/dist/assets/index-fxzkGRZ1.js`에 `OPAL Docs` 라벨과 카탈로그 빈 상태 문구가 포함됨을 확인했다. install이 이 dist를 배포하면 SPA deep-link·브라우저 확인이 가능하다. "빌드는 됐는데 화면이 번들에 없다"는 실패 경로는 배제됐다.
| 2026-09-18 16:19 | 컨벤션 재검사 | Console BE — Critical 0 / High 0 / Medium 0 / Low 0. 1차 High(main.py @header) **해소 확인**, 정정 과정의 신규 위반 0건. 1차 산출물 보존하고 `-1625-console-be-recheck`로 별도 기록 |
| 2026-09-18 16:19 | 정정 후 회귀 | FE `npm test` exit 0 **14 files / 155 tests**, backend `pytest` **434 passed** — @header 정정이 코드 동작에 영향 없음 확인 |
