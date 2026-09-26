---
template: sdlc-v2
---
# TEST-SCENARIO: OPAL Docs 스킬 문서 화면

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 저장소 루트(`/Volumes/Data/AIStudio/workspace/ai-framework`). backend는 `python -m pytest dashboard/backend/tests`, frontend는 `cd dashboard/frontend && npm test|typecheck|lint|build`, 프레임워크 도구는 `node --test opal/tools/skill-registry/tests/*.js`로 실행한다. 설치 검증은 `./scripts/install-mac.sh` `[1] OPAL 설치`와 `http://127.0.0.1:7823`의 OPAL Console을 사용한다.
- 공통 데이터: backend·verifier 시나리오는 임시 corpus fixture(축소 registry JSON + 형식이 서로 다른 `SKILL.md` 몇 건 + `pipeline.json` 1건)를 DI로 주입한다. 실 배포본(`~/.opal/`)을 읽지 않는다. 설치 후 시나리오만 실제 55개 corpus를 대상으로 한다.
- 대역 사용과 한계: 사용하지 않음. backend는 FastAPI TestClient로 실제 라우터와 실제 파일을 읽고, 프레임워크 도구는 실제 프로세스를 실행한다. 기존 `dashboard/backend/tests/test_adapters.py`의 "실 도구 호출, mock 대체 금지" 계약을 신규 테스트에도 적용한다. FE 컴포넌트 시나리오는 네트워크 계층만 테스트 더블로 두며, 이는 S-15·S-16의 실제 연동 증거를 대신하지 않는다.
- 실행 조건: S-1~S-14, S-17, S-18은 자동 실행. S-15·S-16은 캡틴이 직접 실행하는 사용자 협업 시나리오이며, install 실행 권한과 브라우저(데스크톱 뷰포트 + 약 390px 모바일 뷰포트)가 필요하다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-4, AC-8, C-3, H-4 | 임시 fixture root 4종 — ①registry canonical set = 폴더 set ②registry에만 있는 엔트리 ③폴더에만 있는 스킬 ④같은 alias가 두 canonical을 가리킴 | `node opal/tools/skill-registry/skill-registry.js verify-bundle --registry <fixture registry> --skills-root <fixture roots>`를 4종 각각에 실행 | ①`ok:true`·`missing_source:[]`·`unregistered:[]`·exit 0 ②`missing_source`에 해당 엔트리·exit≠0 ③`unregistered`에 해당 폴더·exit≠0 ④`ambiguous_alias`에 충돌 alias·exit≠0. 네 경우 모두 출력이 JSON으로 파싱된다 | unit — `node --test opal/tools/skill-registry/tests/test-verify-bundle.js` | 구현 전 RED |
| S-2 | AC-4, H-4 | `verify-bundle` 추가 후의 `skill-registry.js` | `node --test opal/tools/skill-registry/tests/test-validate.js opal/tools/skill-registry/tests/test-match.js` 실행 후 저장소 루트에서 `node opal/tools/skill-registry/skill-registry.js validate` 실행 | 기존 두 테스트가 전부 통과하고(배포 환경 reverse scan 생략 계약 불변), source validate가 `valid:true`·`unregistered:[]`·canonical 55건을 유지한다 | unit + 실제 CLI 실행 — 저장소 루트 | 구현 후 |
| S-3 | AC-2, C-2, C-3 | 임시 corpus fixture를 DI로 주입한 FastAPI TestClient | `GET /api/docs/skills`를 ①무필터 ②스킬명 일부 ③alias ④설명 단어 ⑤자연어 용도 ⑥`group` 필터 ⑦`domain` 필터로 호출 | ①canonical 행 수가 fixture 폴더 수와 같다 ②~⑤각 질의가 해당 스킬을 결과에 포함한다 ⑥파일럿·독립·오퍼레이터·내부 단계 그룹이 각각 조회되고 어느 그룹도 0건으로 사라지지 않는다 ⑦도메인 필터가 적용되며 facet count가 결과 수와 일치한다. 응답 어디에도 프론트엔드 하드코딩 값이 아닌 registry·SKILL.md 유래 필드만 존재한다 | integration — `python -m pytest dashboard/backend/tests/test_skill_docs.py` | 구현 전 RED |
| S-4 | AC-5 | fixture에 폴더명과 frontmatter `name`이 다른 스킬 2건(`opal-onboarding`/`onboarding`, `opal-skill-manager`/`skill-manager`) 포함 | 목록을 호출하고, canonical id와 frontmatter name 양쪽으로 상세를 호출 | 목록에 각 스킬이 정확히 1건만 나타난다(중복 카드 0). 두 id 모두 같은 canonical 상세로 해석되고 응답의 canonical id는 폴더 basename이며 `aliases`에 frontmatter name이 포함된다 | integration — pytest | 구현 전 RED |
| S-5 | AC-4 | fixture에 `opal-pilot-project-build`(alias `oppb`, `references/pipeline.json` 포함)와 `op-oppb-project-slice`·`op-oppb-knowledge-finalize` 포함 | `GET /api/docs/skills/oppb`와 두 내부 단계 스킬의 상세를 호출 | oppb 상세의 그룹이 파일럿 계열, alias에 `oppb` 포함, 단계 요약이 `pipeline.json`의 `meta.stages`(P0~P5)에서 오고 task row 22건이 단계 카드로 나오지 않는다. 두 내부 단계 스킬은 내부 단계 그룹으로 조회되고 관련 스킬로 oppb가 중복 없이 연결된다 | integration — pytest | 구현 전 RED |
| S-6 | AC-3, AC-6 | registry에는 있으나 `SKILL.md` 파일이 없는 엔트리를 fixture에 포함 | 해당 canonical id로 상세를 호출 | HTTP 200. `source.available=false`, `usage_markdown`·`when_to_use_markdown`·`quick_start`는 `null`, `arguments`·`options`·`examples`·`related_skills`는 `[]`, canonical_name·description·group·aliases·source_path는 유지된다. 거짓 기본값 문자열이 채워지지 않는다 | integration — pytest | 구현 전 RED |
| S-7 | AC-6 | ①canonical/alias 어디에도 없는 id ②registry 파일을 읽을 수 없는 상태 ③frontmatter YAML이 깨진 `SKILL.md` | 각 조건에서 목록 또는 상세를 호출 | ①404 + `code: skill_not_found` ②500 + `code: registry_unavailable` ③500 + `code: parse_error`. 세 응답 모두 `{error:{code,message,details}}` envelope 형식을 지키고 stack trace를 싣지 않는다 | integration — pytest | 구현 전 RED |
| S-8 | C-5, C-7 | 기동한 Docs 라우터 | ①`/api/docs/skills`와 `/api/docs/skills/{id}`에 POST·PUT·PATCH·DELETE ②`skill_id`에 `../`·절대경로·URL 인코딩된 traversal 문자열 ③정상 상세 응답 본문 검사 | ①전부 405 ②전부 404 또는 422이며 허용 root 밖 파일 내용이 응답에 나타나지 않는다 ③응답에 로컬 절대경로가 없고 `opal/skills/{canonical}/SKILL.md` 또는 `skills/{canonical}/SKILL.md` 상대 경로만 존재한다. 스킬 실행·파일 수정·설치를 수행하는 엔드포인트가 존재하지 않는다 | integration — pytest | 구현 전 RED |
| S-9 | C-4 | fixture 중 예시 코드 펜스를 가진 스킬과 registry `triggers`에 정규식(`^oppb$` 형태)을 가진 스킬 | 상세 응답의 모든 `examples[].command` 문자열을 수집해 검사 | 어떤 command에도 터미널 프롬프트 문자(`$`, `%`, `>`)가 선두에 없고 정규식 메타문자(캐럿·달러·대안 구분자·`(?i)` 등)가 포함되지 않는다. registry triggers 원문이 사용자 대면 예시로 노출되지 않는다. 추출 실패한 스킬은 `examples: []`이며 발명된 명령이 없다 | integration — pytest | 구현 전 RED |
| S-10 | AC-3, H-2 | fixture에 본문 구조가 서로 다른 `SKILL.md` 3건(표준 heading 보유 / heading 없음 / 일부 섹션만 보유) 포함 | 세 건의 상세를 호출 | 추출 가능한 섹션만 값이 있고 추출 실패한 필드는 `null` 또는 `[]`이다. 어느 필드에도 다른 스킬의 내용이나 생성된 문장이 들어가지 않는다 | integration — pytest | 구현 전 RED |
| S-11 | AC-6, C-7 | 기존 `apiClient` 호출자와 신규 Docs 호출자 | ①FastAPI `detail`만 있는 오류 응답 ②`{error:{code,message,details}}` envelope 응답 ③타임아웃 ④JSON이 아닌 오류 본문에서 각각 요청 실패를 유발 | ①기존 메시지 추출 동작과 기존 호출자 시그니처가 그대로 유지된다 ②`ApiError`가 `status`·`code`·`message`·`details`를 보존해 던져진다 ③기존 timeout 동작과 메시지가 유지된다 ④generic message 폴백이 유지된다. 기존 `api-timeout.test.ts`가 계속 통과한다 | unit — `cd dashboard/frontend && npm test` (vitest) | 구현 전 RED |
| S-12 | AC-2, AC-3, AC-6, C-1, C-4, C-7 | 네트워크 계층을 테스트 더블로 둔 Testing Library + memory router + QueryClient | 카탈로그와 상세를 ①로딩 중 ②전체 0건 ③검색 결과 0건 ④오류 code별 ⑤source 부재 partial ⑥alias URL 진입 ⑦검색·필터 입력 ⑧복사 버튼 성공 ⑨복사 API 실패 ⑩키보드 Tab 이동으로 조작 | ①로딩 상태 표시 ②~③빈 상태가 서로 구분되어 표시 ④code별 복구 UI가 분기 ⑤메타는 남고 본문 부재 Alert 표시 ⑥canonical URL로 `replace` 되어 히스토리가 중복되지 않음 ⑦URL 쿼리에 `q`/`group`/`domain`이 동기화되고 새로고침 시 복원 ⑧클립보드에 프롬프트 문자 없는 명령 원문이 전달되고 성공 피드백 표시 ⑨실패 폴백 경로 제공 ⑩모든 조작 요소가 접근 가능한 이름을 갖고 포커스가 순서대로 이동. 신규 npm 의존성이 추가되지 않는다 | component — vitest + Testing Library | 구현 전 RED |
| S-13 | AC-1, C-1 | 셸 메뉴·라우트 변경 후 | 좌측 내비게이션 렌더 결과와 라우터 정의를 검사하고, 기존 7개 경로와 `/docs/skills`·`/docs/skills/:skillId`로 이동 | 메뉴가 8개이고 `OPAL Docs` 항목이 `/docs/skills`를 가리킨다. 신규 2개 route가 기존 셸의 child로 동작하고, 기존 7개 메뉴·route·active 상태·SPA shell 동작이 변하지 않는다 | component — vitest + Testing Library | 구현 후 |
| S-14 | AC-7 | 모든 구현 Work item 완료 후 저장소 | `python -m pytest dashboard/backend/tests` 전체, `cd dashboard/frontend && npm test && npm run typecheck && npm run lint && npm run build`, `node --test opal/tools/skill-registry/tests/test-validate.js opal/tools/skill-registry/tests/test-match.js opal/tools/skill-registry/tests/test-verify-bundle.js` 실행 | 네 계열이 모두 exit 0이며 실패·에러 0건이다. 기존 backend 7개 API 테스트와 기존 FE 화면 테스트에 회귀가 없다. 실행 명령과 스코프를 결과에 기록한다 | integration — 저장소 루트 | 구현 후 |
| S-15 | AC-1, AC-4, AC-8, C-6, H-5 | 저장소에 모든 변경이 반영되고 캡틴이 install을 실행할 수 있는 상태 | `./scripts/install-mac.sh`에서 `[1] OPAL 설치` 실행 → 설치본 대상으로 `verify-bundle` 실행 → `curl -fsS http://127.0.0.1:7823/health` → 목록 API → `GET /api/docs/skills/oppb` → `GET /docs/skills/oppb` | install이 오류 없이 완료된다. 설치본 `~/.opal/references/opal-skills-registry.json`과 `~/.opal/skills/*/SKILL.md`의 canonical set이 55/55이고 `missing_source`·`unregistered` 모두 0이며 exit 0이다. health 200, 목록 API가 55행을 반환, oppb 상세가 그룹·alias·pipeline 단계를 담아 200, SPA deep-link가 셸을 반환한다 | E2E(api) + manual — 설치본 런타임 | 설치 후 |
| S-16 | AC-1, AC-2, AC-3, AC-5, AC-6, C-7, H-3 | S-15 완료 후 브라우저 | 데스크톱 뷰포트와 약 390px 모바일 뷰포트 각각에서 `OPAL Docs` 진입 → 검색·그룹/도메인 필터 → 카드에서 상세 진입 → alias URL 직접 입력 → source 부재 스킬 상세 → 존재하지 않는 alias URL → 예시 명령 복사 → 기존 7개 화면 순회 | 두 뷰포트 모두에서 탐색·상세 열람·명령 복사가 가능하고 가로 스크롤이 발생하지 않는다. 필터 상태가 URL에 남아 공유 가능하다. alias URL이 canonical URL로 정규화된다. source 부재는 메타 유지 + 부재 표시, 없는 alias는 404 상태와 목록 복귀 동선이 제공된다. 복사한 명령이 그대로 실행 가능한 형태다. 기존 7개 화면이 정상 동작한다. 목록 API 첫 응답 체감 지연을 관측 항목으로 기록한다 | E2E(browser) + manual — 설치본 Console | 설치 후 |
| S-17 | AC-8, H-1 | 문서 갱신 Work item 완료 후 | `tasks/140-260917-opdw-스킬-문서-화면/wireframe.md` §5.4와 `docs/PROJECT.md`·`docs/ARCHITECTURE.md`·`README.md`를 검사 | wireframe §5.4의 `source_missing` 행이 409/422가 아니라 200 partial의 `source.available=false`로 정정되어 PLAN DEC-1과 충돌하는 표기가 남아 있지 않다. PROJECT·ARCHITECTURE의 Console 화면 수가 8개로 갱신되고 새 Docs read-only API가 기재되며, README에 Console 스킬 문서 화면이 반영된다. OPPB 관련 기재가 중복 추가되지 않았다 | 결정론 검사(grep) + 문서 리뷰 | 구현 후 |
| S-18 | C-6 | 모든 구현 Work item 완료 후 | `git status --short`로 변경 파일 목록을 확인하고 `~/.opal/` 경로 수정 여부를 검사 | 변경 파일이 전부 저장소 소스 경로(`opal/`, `dashboard/`, `docs/`, `scripts/`, `tasks/`)에 있고 `~/.opal/` 배포본을 직접 편집한 흔적이 0건이다 | 결정론 검사 — 저장소 루트 | 구현 후 |

### S-15 구조화 계약

- `surface_kind`: `collaborative`
- `profile`: `collaborative`
- `actors`: `human`, `service`
- `steps[]`: `s15-1`(executor `human`, install 실행) · `s15-2`(executor `api`, 설치본 verify-bundle) · `s15-3`(executor `api`, health) · `s15-4`(executor `api`, 목록) · `s15-5`(executor `api`, oppb 상세) · `s15-6`(executor `api`, SPA deep-link)
- `assertions[]`: `s15-a1` expected `install exit 0` · `s15-a2` expected `canonical 55/55, missing_source 0, unregistered 0, exit 0` · `s15-a3` expected `HTTP 200 health` · `s15-a4` expected `목록 55행` · `s15-a5` expected `oppb 상세 200 + pipeline 단계 P0~P5` · `s15-a6` expected `SPA shell 200`
- `required_evidence[]`: `install-stdout`, `verify-bundle-json`, `health-response`, `catalog-response`, `oppb-detail-response`, `deeplink-response`
- `handoff`: `handoff_id` `s15-install` / `instruction` "저장소 루트에서 ./scripts/install-mac.sh 실행 후 [1] OPAL 설치를 선택하고 완료 출력을 제출한다" / `expected_observation` "install 완료 메시지와 exit 0" / `required_evidence` `install-stdout` / `timeout_seconds` 1800 / `resume_token` `s15-install-resume` / `server_policy` `await_submission` / `submission_path` `tasks/140-260917-opdw-스킬-문서-화면/run/s15-install.json`

### S-16 구조화 계약

- `surface_kind`: `collaborative`
- `profile`: `collaborative`
- `actors`: `human`, `user`
- `steps[]`: `s16-1`(executor `human`, 데스크톱 카탈로그 진입·검색·필터) · `s16-2`(executor `human`, 카드→상세 진입) · `s16-3`(executor `human`, alias URL 직접 입력) · `s16-4`(executor `human`, source 부재 상세) · `s16-5`(executor `human`, 없는 alias URL) · `s16-6`(executor `human`, 예시 명령 복사) · `s16-7`(executor `human`, 약 390px 뷰포트 반복) · `s16-8`(executor `human`, 기존 7개 화면 순회)
- `assertions[]`: `s16-a1` expected `필터 상태가 URL 쿼리에 반영되고 새로고침 후 복원` · `s16-a2` expected `상세에 제목·설명·분류·Quick Start·Usage·Arguments/Options·사용 시점·예시·파이프라인·관련 스킬·원본 경로 표시` · `s16-a3` expected `alias URL이 canonical URL로 정규화` · `s16-a4` expected `메타 유지 + 본문 부재 안내` · `s16-a5` expected `404 상태와 목록 복귀 동선` · `s16-a6` expected `복사 결과가 프롬프트 문자 없는 실행 가능한 명령` · `s16-a7` expected `두 뷰포트 모두 가로 스크롤 없음` · `s16-a8` expected `기존 7개 화면 정상`
- `required_evidence[]`: `desktop-screenshots`, `mobile-screenshots`, `url-state-record`, `copy-result-record`, `catalog-latency-note`
- `handoff`: `handoff_id` `s16-browser` / `instruction` "설치본 Console에서 데스크톱·모바일 뷰포트로 위 8개 step을 수행하고 스크린샷과 관측값을 제출한다" / `expected_observation` "8개 assertion의 실제 관찰값" / `required_evidence` `desktop-screenshots`, `mobile-screenshots`, `url-state-record`, `copy-result-record`, `catalog-latency-note` / `timeout_seconds` 3600 / `resume_token` `s16-browser-resume` / `server_policy` `await_submission` / `submission_path` `tasks/140-260917-opdw-스킬-문서-화면/run/s16-browser.json`
