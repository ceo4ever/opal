---
template: sdlc-v2
---
# TEST-SCENARIO: OPAL Docs 스킬 문서 사이드바·README 렌더

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 저장소 루트(`/Volumes/Data/AIStudio/workspace/ai-framework`), 브랜치 `feat/143-opds-스킬-문서-사이드바`. backend는 `python -m pytest dashboard/backend/tests`, frontend는 `cd dashboard/frontend && npm test|typecheck|lint|build`, 프레임워크 도구는 `node --test opal/tools/skill-registry/tests/*.js`. 설치 검증은 `./scripts/install-mac.sh`와 `http://127.0.0.1:7823`.
- 공통 데이터: 합성 fixture(`dashboard/backend/tests/fixtures/skill_docs_corpus`)는 README 유무 3조합과 `paths` 공유 엔트리를 재현한다. **이와 별개로 실 corpus(저장소 루트, `~/.opal`)를 직접 읽는 시나리오를 둔다** — 태스크 140에서 fixture만 통과하고 실데이터에서 깨지는 결함이 5회 반복됐기 때문이다.
- 대역 사용과 한계: 백엔드는 FastAPI TestClient로 실제 라우터와 실제 파일을 읽는다. FE 컴포넌트 시나리오만 네트워크 계층을 테스트 더블로 두며, 이는 S-12·S-13의 실제 연동 증거를 대신하지 않는다.
- 실행 조건: S-1~S-11은 자동 실행. S-12·S-13은 캡틴이 직접 수행하는 협업 시나리오로 install 권한과 브라우저(데스크톱 + 약 390px 모바일 뷰포트)가 필요하다.
- 검증 순서: backend → framework → `npm test` → typecheck → lint → **build(마지막)**. build가 저장소 `dist/`를 남기면 `api-env-files.test.ts`가 실패한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-3, C-3, H-4 | README를 가진 스킬을 포함한 fixture corpus | 상세를 조회해 `body` 객체를 검사 | `body.markdown`이 README 파일 원문과 동일하고, `body.origin`이 `readme`, `body.source_path`가 `.../README.md` 상대경로다. 응답 어디에도 corpus root 절대경로가 없다 | integration — pytest | 구현 전 RED |
| S-2 | AC-4, C-3 | README가 없고 SKILL.md만 있는 스킬 | 상세 조회 | HTTP 200, `body.origin`이 `skill_md`, `body.markdown`에 YAML frontmatter 구분선과 `name:` 줄이 포함되지 않는다 | integration — pytest | 구현 전 RED |
| S-3 | AC-4, AC-7 | README·SKILL.md 둘 다 없는 엔트리 | 상세 조회 | HTTP 200, `body.markdown`이 `null`, `body.origin`이 `null`. 오류 envelope가 아니다 | integration — pytest | 구현 전 RED |
| S-4 | AC-5, C-2, C-4 | fixture에 `internal-stage` 스킬과 `paths` 공유 엔트리 포함 | 목록·상세에서 `listed` 필드 검사 | `internal-stage`는 `listed:false`. 레지스트리 `paths[0]`의 폴더명이 canonical과 다른 엔트리도 `listed:false`. 두 경우 모두 상세 조회는 200으로 성공한다 | integration — pytest | 구현 전 RED |
| S-5 | AC-3, C-3, H-3 | 슬롯 필드가 제거된 공개 계약 | 상세 응답의 키 집합 검사 | `usage_markdown`·`when_to_use_markdown`·`quick_start`·`arguments`·`options`·`examples`·`use_cases` 7종이 응답 키에 **존재하지 않는다**. `description`과 `pipeline`은 유지된다 | integration — pytest | 구현 전 RED |
| S-6 | AC-1, AC-5, C-2, C-4, H-1, H-2 | **실 corpus**(저장소 루트, 합성 fixture 아님) | `build_skill_docs_corpus`로 corpus를 만들고 `listed` 집계 | `listed:true`가 정확히 **33**건. `display_group` 분포가 pilot 12 · operator 14 · standalone 8 · internal-stage 21이며 합이 55다. `opal-pilot-dev-short`가 `listed:false`다 | integration — pytest, 실 corpus | 구현 전 RED |
| S-7 | AC-3, C-3, H-1 | **실 corpus**(저장소 루트) 전체 | corpus의 **모든 스킬**을 순회해 `body`를 집계 | `origin`이 `null`인 건수가 **0**이고, 모든 건의 `body.markdown`이 공백이 아니며, `origin`이 `readme` 또는 `skill_md` 중 하나다. 표본이 아니라 **전수 집계**로 단언한다. 추가로 임의 1건의 `body.markdown`이 그 스킬 폴더의 README 파일 내용과 일치한다. 태스크 140의 실패는 개별 조회가 아니라 전수 측정(`quick_start` 0/55 등)으로만 드러났으므로 같은 측정 방식을 재현한다 | integration — pytest, 실 corpus | 구현 전 RED |
| S-8 | AC-1, AC-2, AC-6, C-4, C-5, C-8, H-7 | 네트워크 계층을 더블로 둔 Testing Library | 사이드바를 렌더하고 ①그룹 구성 ②`listed:false` 항목 ③alias 표기 ④항목 클릭 ⑤검색·필터 존재 여부 ⑥키보드 포커스를 검사 | ①파일럿·오퍼레이터·독립 3그룹 헤더가 보이고 ②`listed:false` 항목은 렌더되지 않으며 ③각 항목에 canonical과 alias가 함께 표시되고 ④클릭 시 URL이 `/docs/skills/{id}`가 되며 사이드바가 유지되고 선택 항목에 `aria-current`가 적용되고 ⑤`role="searchbox"` 입력과 그룹·도메인 Select가 **없고** ⑥사이드바가 `nav` 랜드마크와 접근 가능한 이름을 가지며 항목 간 탭 이동이 된다. 추가로 화면 어디에도 스킬 실행·파일 수정·설치를 유발하는 조작 요소가 없고, 항목 전환 시 사이드바 목록이 재요청되지 않는다 | component — vitest + Testing Library | 구현 전 RED |
| S-9 | AC-3, AC-4, C-6 | 상세 응답 3종(`readme`·`skill_md`·`null`)을 더블로 주입 | 우측 본문 렌더 검사 | `readme`면 Markdown이 요소로 렌더되어 제목·목록·표·코드 블록이 나타나고, `skill_md`면 폴백 안내가 함께 보이며, `null`이면 부재 상태가 보인다. raw HTML이 실행되지 않는다 | component — vitest | 구현 전 RED |
| S-10 | AC-7 | 로딩 중·목록 0건·목록 조회 실패·상세 404 | 각 상태에서 화면 검사 | 네 상태가 각각 구분되어 표시되고, 오류 메시지에 절대경로나 스택이 노출되지 않는다 | component — vitest | 구현 전 RED |
| S-11 | AC-8, C-1, C-5, H-3, H-6 | 모든 구현 Work item 완료 후 | `pytest dashboard/backend/tests` → `node --test` 3파일 → `npm test` → `npm run typecheck` → `npm run lint` → **`npm run build`(마지막)** 순서로 실행하고, 이어 `skill-registry.js validate`와 `package.json`·requirements diff를 확인 | 여섯 계열이 모두 exit 0이고 기존 Console 7개 화면 테스트에 실패가 없다. `validate`가 `valid:true`·`unregistered:[]`를 유지한다. 신규 npm·Python 의존성이 0건이다. build 이후 저장소에 `dist/`가 남았는지 확인해 기록한다 | integration — 저장소 루트 | 구현 후 |
| S-12 | AC-1, AC-3, AC-9, C-7 | 소스 변경 반영 후 캡틴이 install을 실행할 수 있는 상태 | `./scripts/install-mac.sh` 전체 설치 → `~/.opal` corpus 대상 `curl`로 목록의 `listed:true` 개수와 특정 스킬 상세의 `body` 확인 | install이 오류 없이 완료되고, 설치본 목록에서 `listed:true`가 33건이며, `oppb` 등 실존 스킬 상세의 `body.origin`이 `readme`이고 본문이 비어 있지 않다 | E2E(collaborative) — 설치본 런타임 | 설치 후 |
| S-13 | AC-1, AC-2, AC-5, AC-6, AC-8, C-4, C-8, H-5 | S-12 완료 후 브라우저 | 데스크톱과 약 390px 모바일 뷰포트 각각에서 `/docs/skills` 진입 → 사이드바 3그룹 33개 확인 → 항목 클릭 → 새로고침·URL 직접 접근 → `listed:false` 스킬 URL 직접 접근 → 검색·필터 부재 확인 → 키보드 탭 이동 → 없는 skill id 접근 → 기존 7개 화면 순회 | 두 뷰포트 모두에서 사이드바 탐색과 본문 열람이 되고 가로 스크롤이 없다. 클릭 시 URL이 바뀌고 새로고침해도 같은 문서가 열린다. `listed:false` 스킬은 사이드바에 없지만 URL로는 읽힌다. 검색·필터가 보이지 않는다. 없는 id는 404 상태와 복귀 동선이 제공된다. 기존 7개 화면이 정상 동작한다. 항목 전환 체감 지연을 관측 항목으로 기록한다 | E2E(collaborative) — 설치본 Console | 설치 후 |

### S-12 구조화 계약

- `surface_kind`: `collaborative` · `profile`: `collaborative` · `actors`: `human`, `service`
- `steps[]`: `s12-1`(executor `human`, install 실행) · `s12-2`(executor `api`, 목록 `listed` 집계) · `s12-3`(executor `api`, 실존 스킬 상세 `body` 확인)
- `assertions[]`: `s12-a1` expected `install exit 0` · `s12-a2` expected `listed:true 33건` · `s12-a3` expected `body.origin=readme, markdown 비공백`
- `required_evidence[]`: `install-stdout`, `listed-count-response`, `detail-body-response`
- `handoff`: `handoff_id` `s12-install` / `instruction` "저장소 루트에서 ./scripts/install-mac.sh로 전체 설치를 수행하고 완료 출력을 제출한다" / `expected_observation` "install 완료 메시지와 exit 0" / `required_evidence` `install-stdout` / `timeout_seconds` 1800 / `resume_token` `s12-install-resume` / `server_policy` `await_submission` / `submission_path` `tasks/143-260918-opds-스킬-문서-사이드바/run/s12-install.json`

### S-13 구조화 계약

- `surface_kind`: `collaborative` · `profile`: `collaborative` · `actors`: `human`, `user`
- `steps[]`: `s13-1`~`s13-9`(전부 executor `human`) — 데스크톱 진입, 사이드바 33개 확인, 항목 클릭, 새로고침·URL 직접 접근, `listed:false` URL 접근, 검색·필터 부재 확인, 키보드 탭 이동, 없는 id 접근, 기존 7개 화면 순회
- `assertions[]`: `s13-a1` expected `3그룹 33개 표시` · `s13-a2` expected `클릭 시 URL 변경과 본문 렌더` · `s13-a3` expected `새로고침 후 동일 문서` · `s13-a4` expected `listed:false 스킬이 사이드바에 없고 URL로는 읽힘` · `s13-a5` expected `검색·필터 미표시` · `s13-a6` expected `탭 이동 가능` · `s13-a7` expected `없는 id 404 상태와 복귀 동선` · `s13-a8` expected `두 뷰포트 모두 가로 스크롤 없음` · `s13-a9` expected `기존 7개 화면 정상`
- `required_evidence[]`: `desktop-screenshots`, `mobile-screenshots`, `url-state-record`, `regression-walkthrough-note`
- `handoff`: `handoff_id` `s13-browser` / `instruction` "설치본 Console에서 데스크톱·모바일 뷰포트로 9개 step을 수행하고 스크린샷과 관측값을 제출한다" / `expected_observation` "9개 assertion의 실제 관찰값" / `required_evidence` `desktop-screenshots`, `mobile-screenshots`, `url-state-record`, `regression-walkthrough-note` / `timeout_seconds` 3600 / `resume_token` `s13-browser-resume` / `server_policy` `await_submission` / `submission_path` `tasks/143-260918-opds-스킬-문서-사이드바/run/s13-browser.json`
