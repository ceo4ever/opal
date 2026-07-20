# TEST SCENARIO: 커뮤니티 스킬 관리 워크플로우 통일

> 작성일: 2026-07-17 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 (agentic — PM 대행) | PLAN.md 가설 표 기반
> RED-first 트랙: **적용** (F-001/F-002/F-006 도구 로직 = 비즈니스 로직·계약 → RED-first 강제 / F-003/F-005 문서 = 구현 후 산출물 검사 허용. SSOT: `opal/core/references/harness/red-first.md` §1.5)

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `getCommunitySkillPath` 이중 탐지 재구현 | 호출자(matchCommand/validate)의 "존재 경로 or null" 기대 — 미설치 오판 회귀 | P0 | L1 | S-1, S-4 |
| H-2 | `matchByAlias` basename 확장 | 반환 다형화(단일→ambiguous 센티넬) 시 matchCommand TypeError | P0 | L1 | S-5 |
| H-3 | `loadAllSkills` user-registry 병합 | user-registry 부재/파손 시 CLI 전체 다운 | P0 | L1+L2 | S-6 |
| H-4 | migrate 이동 로직 | 미등재/충돌 flat 삭제·오이동 = 사용자 데이터 소실(142 D-4 위반) | P0 | L2 | S-2, S-3 |
| H-5 | user-registry.json 기록 경로 | references에 기록하면 install 재실행 시 소실 | P0 | L2/L3 | S-9, S-10 |
| H-6 | clone-copy source_repo 파싱 | `owner/repo@subdir` 파싱 오류 → 잘못된 clone/빈 복사 | P1 | L1 | S-7 |
| H-7 | commit_sha 업데이트 감지 | ls-remote 실패/commit_sha null 시 판정 오류 | P2 | 산출물 검사+L3 | S-8, S-10 |
| H-8 | npx add 제거 | 잔존 설치 지시가 §6 clone-copy와 모순(D4 재발) | P1 | L1(grep) | S-8 |
| H-9 | skill-commands ↔ §6 라우팅 | §6이 clone-copy로 동작하지 않으면 `//` 미설치 흐름 단절 | P0 | L2+L3 | S-9, S-10 |

## 2. 테스트 데이터 설계

> 대상이 DB가 아닌 파일시스템·JSON registry이므로 "테이블"은 fixture 디렉토리/파일로 대응한다. 전 시나리오 실 파일시스템 사용(mock 금지). 도구 테스트는 `HOME` 오버라이드로 합성 fixture 격리(기존 `tests/test-validate.js:44-115` makeFixture 패턴 계승).

### 2.1 사전 조건 데이터

| 테이블(fixture) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| `{tmpHome}/.opal/community-skills/pdf/SKILL.md` | flat-registered | registry 등재 basename과 매칭되는 flat 스킬 | fixture (test-migrate.js 생성) |
| `{tmpHome}/.opal/community-skills/my-private/SKILL.md` | flat-unregistered | registry 미등재 flat 디렉토리 | fixture |
| `{tmpHome}/.opal/community-skills/obra/brainstorming/SKILL.md` | nested-ok | 이미 vendor 중첩 정합 | fixture |
| `{tmpHome}/.opal/references/community-skills-registry.json` | catalog | v2.1 스키마, `anthropics/pdf`·`obra/brainstorming` + 충돌 검증용 `vendorx/pdf` 합성 항목 | fixture |
| `{tmpHome}/.opal/community-skills/user-registry.json` | user-reg | ① 부재 ② 정상(신규 name 1 + 기존 name override 1) ③ 파손(`{invalid`) 3상태 | fixture |
| `{scratchpad}/e2e/` | e2e-home | 합성 HOME + 실 git clone 가능 네트워크 | 수동 준비(S-9) |
| 실 PC `~/.opal/` | live-env | install 재실행 + 실 `//` 흐름 | 캡틴 환경(S-10) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | fixture: nested-ok·flat-registered·양쪽 없음 3상태 | `resolveCommunitySkillPath()` 호출 | nested 경로 / flat 경로 / null 정확 반환 |
| S-2 | flat-registered + nested-ok 공존 fixture | `migrate` 실행 → 재실행 | flat→`anthropics/pdf/` 이동, nested skip, 2회차 moved 0(멱등) |
| S-3 | flat-unregistered + basename 충돌 fixture(`vendorx/pdf` 합성 등재) | `migrate` 실행 | 미등재·충돌 디렉토리 원위치 보존, preserved reason 기록, errors 0 |
| S-4 | S-2 완료 상태 fixture | `list --group=community` | catalog 등재 전수 `installed:true` |
| S-5 | catalog fixture (32항목 상당 + 충돌 합성) | `match` 4종 입력 | 단일/basename/정식명/ambiguous 각 계약대로 반환 |
| S-6 | user-reg 3상태 fixture | `match`/`list` 호출 | 부재=기존 동작, 정상=병합(override+추가), 파손=무시·정상 응답 |
| S-7 | catalog fixture | `match "//pdf ..."` 출력 + source_repo 파싱 함수 | npx 문구 0, `install_method:"clone-copy"`, 파싱 (owner,repo,subdir) 정확 |
| S-8 | 프로젝트 소스 전체 | grep `npx skills add` + 문서 절차 대조 | 설치 지시 0건(설명·변경이력 제외), 4절차 모순 0, 업데이트 절차에 commit_sha 비교 명시 |
| S-9 | e2e-home(미설치 상태) | match(installed:false 확인) → §6 clone-copy 절차 실행 → match 재호출 | vendor 중첩 설치 + `installed:true` + user-registry에 commit_sha 항목 |
| S-10 | live-env (배포 후) | install 재실행 + 실 `//` 미설치 스킬 호출 | user-registry 잔존 + 자동 설치·즉시 실행 흐름 완주 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 경로 탐지 3분기 (vendor 우선 → flat 폴백 → null)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `resolveCommunitySkillPath()` + `getCommunitySkillPath()` 시그니처 불변 |
| 계층 | L1 |
| **실행 방식** | M1 (node:test — `tests/test-migrate.js`) |
| 조건 | §2.1 fixture 3상태 (nested/flat/absent), HOME 오버라이드 |
| 기대 결과 | nested→nested 경로, flat만→flat 경로, 없음→null. `getCommunitySkillPath`는 canonical vendor 경로 반환 유지 |
| 도구 | node:test |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-migrate.js` |
| 결과 | **Pass** |
| 상세 | T101/L1-F1 3서브케이스 전부 ok (flat만→flat경로, nested→nested경로, 둘다없음→installed:false+path:null). exit 0. 파일 전체 결과: tests 9, pass 9, fail 0 (S-2/S-3/S-4 공유 실행). |

#### S-5: matchByAlias 4분기 (basename·하위호환·ambiguous)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `matchByAlias()` + `matchCommand` ambiguous 분기 |
| 계층 | L1 |
| **실행 방식** | M1 (node:test — `tests/test-match.js`) |
| 조건 | catalog fixture. 입력 4종: `//pdf 문서 만들어줘` / `//brainstorming` / `//anthropics/pdf` / 충돌 basename(`vendorx/pdf` 합성 추가 후 `//pdf`) |
| 기대 결과 | ① `anthropics/pdf`+`cleanInput:"문서 만들어줘"` ② `obra/brainstorming` ③ 정식명 단일 반환(하위호환) ④ `ambiguous:true`+candidates 2건(자동 선택 없음) |
| 도구 | node:test |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-match.js` |
| 결과 | **Pass** |
| 상세 | T201~T204/L1-F2 4서브케이스 전부 ok — ①`anthropics/pdf`+cleanInput:"문서 만들어줘" ②`obra/brainstorming` ③정식명 단일 반환 ④ambiguous:true+candidates 2건. exit 0. |

#### S-6: user-registry 병합 로드 방어성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `loadUserRegistry()` + `loadAllSkills()` 병합 |
| 계층 | L1 (부재/파손) + L2 (정상 병합 실 파일) |
| **실행 방식** | M1 (node:test — `tests/test-match.js`) |
| 조건 | user-registry 3상태 fixture (§2.1) |
| 기대 결과 | 부재=기존 응답과 동일, 정상=동일 name override·신규 name 추가, 파손 JSON=무시하고 CLI 정상 exit 0 |
| 도구 | node:test |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-match.js` |
| 결과 | **Pass** |
| 상세 | T601~T602/L1-F6 3서브케이스 전부 ok — 부재=기존 응답과 동일, 정상=override+신규 병합, 파손 JSON=무시하고 exit 0 정상 응답. |

#### S-7: match 출력 clone-copy 전환 + source_repo 파싱

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, H-8 |
| 대상 | match community 출력 필드(`install_method`/`install_command`) + `owner/repo@subdir` 파싱 |
| 계층 | L1 |
| **실행 방식** | M1 (node:test — `tests/test-match.js`) |
| 조건 | catalog fixture. 파싱 입력: `anthropics/skills@pdf`, `obra/superpowers@brainstorming`, `@` 미포함 케이스 |
| 기대 결과 | 출력에 `npx` 문구 0 + `install_method:"clone-copy"`. 파싱 결과 (anthropics,skills,pdf) / (obra,superpowers,brainstorming) / subdir=repo 폴백 |
| 도구 | node:test |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-match.js` |
| 결과 | **Pass** |
| 상세 | T401/L1-F4 ok(install_method:"clone-copy", install_command에 npx 없음) + T402/L1-F4 3파싱케이스 전부 ok — (anthropics,skills,pdf) / (obra,superpowers,brainstorming) / `@`미포함→subdir=repo 폴백(myorg,myrepo). |

#### S-8: 산출물 정합 검사 (npx add 0건 + 4절차 모순 0)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-8 |
| 대상 | 프로젝트 소스 전체 문서 + skill-manager 4절차 + skill-commands 라우팅 |
| 계층 | L1 (정적 검사) |
| **실행 방식** | M1 (grep + 문서 대조) |
| 조건 | Step 5~7 완료 후 소스 트리 |
| 기대 결과 | ① `npx skills add`가 설치 지시로 등장 0건(설명·변경이력 제외 — `find`/`check`는 허용) ② 검색·설치·제거·업데이트 4절차 단계 목록 존재+상호 모순 0 ③ 업데이트 절차에 ls-remote commit_sha 비교 명시(null=재설치 제안 포함) ④ skill-commands v1.2 정책 원문 ↔ §6 모순 0 + §6에 "설치 후 SKILL.md 즉시 Read·실행" 단계 존재 |
| 도구 | grep / Read 대조 |
| 실행 명령 | `grep -rn "npx skills add" --include="*.js" --include="*.md" .`(tasks/·.opal/brain 제외) + Read `opal/skills/opal-skill-manager/SKILL.md` + `opal/core/references/harness/skill-commands.md` + `docs/ARCHITECTURE.md` 대조 |
| 결과 | **Pass** |
| 상세 | ① grep 잔존 4건 모두 허용 예외 — test-match.js:280(RED 이전 상태 설명 주석), skill-commands.md:24·SKILL.md:12,166,210(전부 "~는 사용하지 않는다" 부정 서술/changelog, 설치 지시 아님). docs/ARCHITECTURE.md:410도 changelog 서술. 설치 지시로서 등장 0건 확인. ② SKILL.md §1~§4(검색/설치/제거/업데이트) 단계 목록 존재, 상호 모순 없음(§2 clone-copy를 §1 검색 결과·§3 목록·§4 삭제가 참조 일관). ③ §5 업데이트 절차에 `git ls-remote` → commit_sha 비교 → 불일치 또는 `commit_sha==null`(레거시) 시 재설치 제안 명시(SKILL.md:126-136). ④ skill-commands.md 원문(installed:false→SKILL.md §6 라우팅, ambiguous:true→candidates 표시)과 SKILL.md §6 내용 모순 0. §6에 "설치 완료 후 SKILL.md를 Read하여 즉시 절차 실행" 단계 명시(SKILL.md:185) 확인. |

### L2. 프로세스 통합 (자동, 실 fs read→CUD→re-read)

#### S-2: migrate 이동·멱등

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `migrate` 서브커맨드 (등재 flat 이동 + 중첩 skip + 멱등) |
| 계층 | L2 |
| **실행 방식** | M1 (node:test 실 fs fixture — `tests/test-migrate.js`) |
| 조건 | flat-registered + nested-ok 공존 fixture. `--dry-run` 선행 → 본실행 → 재실행 |
| 기대 결과 | dry-run 무부작용(계획만 반환). 본실행: `pdf/`→`anthropics/pdf/` 이동·nested skip. 재실행: moved 0(멱등). 이동 경로는 `community-skills/` 하위 검증(path traversal 차단) |
| 도구 | node:test |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-migrate.js` |
| 결과 | **Pass** |
| 상세 | T102/L2-F1 3서브케이스 전부 ok — dry-run 무부작용(계획만 반환), 본실행 `pdf/`→`anthropics/pdf/` 이동+nested skip, 재실행 moved 0(멱등). |

#### S-3: migrate 보존 (142 D-4)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `migrate` 미등재·basename 충돌 보존 로직 |
| 계층 | L2 |
| **실행 방식** | M1 (node:test 실 fs fixture) |
| 조건 | flat-unregistered(`my-private/`) + 충돌 fixture(catalog에 `vendorx/pdf` 합성 등재 + flat `pdf/`) |
| 기대 결과 | 두 디렉토리 모두 원위치 무이동, `preserved`에 `reason:"unregistered"`/`"basename_collision"` 기록, errors 0, 파일 손실 0 |
| 도구 | node:test |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-migrate.js` |
| 결과 | **Pass** |
| 상세 | T103/L2-F1 2서브케이스 전부 ok — 미등재 flat(`my-private/`) 무이동 보존(reason:"unregistered"), basename 충돌 flat(`pdf/` vs `vendorx/pdf` 등재) 무이동 보존(reason:"basename_collision"), errors 0, 파일 손실 없음. |

#### S-4: migrate 후 전수 installed:true (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | migrate → `list --group=community` 판정 정합 + 기존 `test-validate.js` 5TC 회귀 |
| 계층 | L2 |
| **실행 방식** | M1 (node:test + CLI 실행) |
| 조건 | S-2 완료 fixture |
| 기대 결과 | catalog 등재 전수 `installed:true`. 기존 5TC(TC1~TC5) GREEN 유지 |
| 도구 | node:test |
| 실행 명령 | `node opal/tools/skill-registry/tests/test-migrate.js` (T104) + `node opal/tools/skill-registry/tests/test-validate.js` (회귀 5TC) |
| 결과 | **Pass** |
| 상세 | T104/L2-F1 ok — migrate 후 `list --group=community` catalog 등재 전수 installed:true. test-validate.js 기존 5TC(TC1~TC5) 전부 ok, exit 0 — 회귀 없음. |

#### S-9: 합성 E2E — 미설치 match → clone-copy → installed:true + commit_sha

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-9 |
| 대상 | §6 절차의 결정론 구간 전체 (match 판정 → clone-copy 설치 → user-registry 기록 → 재판정) |
| 계층 | L2 |
| **실행 방식** | M2 (스크래치패드 합성 HOME + 실 git clone — 네트워크 필요) |
| 조건 | e2e-home fixture: catalog만 있고 스킬 미설치. 대상: `anthropics/skills@pdf` (실 공개 repo) |
| 기대 결과 | ① match `installed:false`+`install_method:"clone-copy"` ② §6 절차대로 clone→`anthropics/pdf/` 복사→tmp 정리 ③ user-registry.json에 commit_sha(40자 hex) 포함 항목 기록 ④ match 재호출 `installed:true`+`path`=vendor 중첩 경로 |
| 도구 | bash + git + node CLI |
| 실행 명령 | **1차(Fail)**: 합성 HOME `{scratchpad}/e2e-064/` — 구 카탈로그(`anthropics/skills@pdf`)로 §2 절차 실행. **재검증(Pass, fix 반영 후)**: 신규 합성 HOME `{scratchpad}/e2e-064-retry/` — 정정 카탈로그(`anthropics/skills@skills/pdf`, v1.4.1) 재복사 후 ① `HOME=$E2E node skill-registry.js match "//pdf 문서 만들어줘"` ② `HOME=$E2E node skill-registry.js parse-source-repo "anthropics/skills@skills/pdf"` ③ `git clone --depth 1 https://github.com/anthropics/skills.git {tmp}` → `{tmp}/{subdir}/SKILL.md`(=`{tmp}/skills/pdf/SKILL.md`) 1단계 탐지 적중 확인 ④ `cp -r {tmp}/skills/pdf $E2E/.opal/community-skills/anthropics/pdf` ⑤ `git -C {tmp} rev-parse HEAD` ⑥ user-registry.json 기록 ⑦ match 재호출 |
| 결과 | **1차 Fail → fix 반영 후 재검증 Pass** |
| 상세 | **[1차 실행, Fail 이력]** ① match(HOME=합성) → `installed:false`+`source_repo:"anthropics/skills@pdf"` 확인. ② `parse-source-repo` 파싱 자체는 정확(`{owner:anthropics, repo:skills, subdir:pdf}`). ③ **[결함 발견]** §2 step3 `{tmp}/{subdir}/`=`{tmp}/pdf/`가 실 clone에서 디렉토리 부재 — 실제 anthropics/skills repo는 스킬이 `{tmp}/skills/pdf/`(2중 `skills/` 중첩) 아래 위치, catalog `anthropics/skills@{name}` 17건 전부 동일 결함(H-6 현실화). ④ 수동 경로 보정 후 하위 절차(commit_sha 40자 hex, user-registry 기록, match 재호출 installed:true)는 정상 확인. → PM에 결함 보고. **[재검증, fix 1/3 반영 후]** 코디네이터가 ① 카탈로그 anthropics 그룹 `source_repo`를 전수 `@skills/{name}`로 정정, ② SKILL.md §2에 복사 원본 4단계 탐지 폴백 추가(v1.4.1) 확인 후 신규 스크래치패드(`e2e-064-retry/`)에서 정정 카탈로그로 재실행: ① `match` → `installed:false`+`source_repo:"anthropics/skills@skills/pdf"`+`install_method:"clone-copy"` 정확(Pass). ② `parse-source-repo "anthropics/skills@skills/pdf"` → `{owner:anthropics, repo:skills, subdir:"skills/pdf"}` 정확(Pass). ③ 실 `git clone --depth 1 anthropics/skills` 후 `{tmp}/skills/pdf/SKILL.md` 1단계 탐지에서 즉시 적중 확인(`ls` 성공, 폴백 미발동) — 카탈로그 정정으로 결함 해소 실측 확인(Pass). ④ `cp -r {tmp}/skills/pdf → {vendor}/anthropics/pdf` 복사 완료, `git rev-parse HEAD` = 40자 hex `9d2f1ae187231d8199c64b5b762e1bdf2244733d` 확보, tmp 정리, user-registry.json에 `commit_sha` 포함 기록(Pass). ⑤ match 재호출 → `installed:true`+`path`=`{E2E}/.opal/community-skills/anthropics/pdf/SKILL.md`(vendor 중첩 경로) 정확 반환(Pass). **최종 결론**: fix 반영 후 §2 절차 전 구간(판정→clone→탐지→copy→commit_sha→registry 기록→재판정) 실 공개 repo 대상으로 완주 확인 — S-9 **Pass**로 재판정. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-10: 실환경 배포 후 `//` 미설치 흐름 + install 재실행 보존 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-7, H-9 |
| 대상 | 실 PC: install 배포 → 실제 `//` 미설치 커뮤니티 스킬 호출 → 자동 설치·즉시 실행 / install 재실행 후 user-registry 잔존 |
| 계층 | L3 |
| **실행 방식** | M3 (사용자 협업 — install 재실행은 실환경 변경이라 캡틴 판단 필요) |
| 조건 | 태스크 커밋 + `install-mac.sh` 배포 완료 상태 |
| 기대 결과 | ① 미설치 스킬 `//호출` 시 (확인된 라이선스) 자동 clone-copy 설치 후 즉시 실행 ② `~/.opal/community-skills/user-registry.json` 생성·commit_sha 기록 ③ install 재실행 후 user-registry.json 잔존 + references 카탈로그 갱신 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Pass** (캡틴 확인, 2026-07-17) |
| 상세 | 캡틴 실환경 확인 — ① install 배포 후 `anthropics/pdf` 제거 → 새 세션 `//pdf` 호출 시 자동 clone-copy 설치 + 즉시 실행 정상 ("자동 설치 잘 됨") ② install 재실행 후 user-registry.json 잔존 확인 ("4단계도 통과"). 사전 검증으로 PM이 migrate 실측 수행: 30건 이동·멱등·32/32 installed (modern-python 레거시 번들은 수동 정규화 — AGENTIC-LOG #23) |

**PM 표준 요청 양식** (TEST 단계에서 사용):
```
캡틴, [시나리오 S-10]은 사용자 협업 검증이 필요합니다.
요청 내용: install 배포 후 ① 미설치 커뮤니티 스킬을 //로 호출 ② install 1회 재실행
기대 결과: ① 자동 clone-copy 설치 + 즉시 실행 ② user-registry.json 잔존(등록분 보존)
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 AC(판정·이동·멱등) | H-1, H-4 | L1+L2 | S-1, S-2, S-4 | `tests/test-migrate.js`:[T101/L1-F1]·[T102/L2-F1]·[T104/L2-F1] | dry-run 포함 |
| F-1 AC(미등재 보존) | H-4 | L2 | S-3 | `tests/test-migrate.js`:[T103/L2-F1] | 142 D-4 |
| F-2 AC | H-2 | L1 | S-5 | `tests/test-match.js`:[T201~204/L1-F2] | 4분기 |
| F-3 AC①②③ | H-9 | L1+L2+L3 | S-8, S-9, S-10 | 산출물 검사 + E2E | 라우팅↔§6 정합 |
| F-4 AC | H-6, H-8 | L1+L2 | S-7, S-8, S-9 | `tests/test-match.js`:[T401~402/L1-F4] + grep | commit_sha 기록은 S-9③ |
| F-5 AC | H-7, H-8 | L1 | S-8 | 산출물 검사 | 4절차·업데이트 비교 |
| F-6 AC | H-3, H-5 | L1+L2+L3 | S-6, S-9, S-10 | `tests/test-match.js`:[T601~602/L1-F6] + E2E | install 잔존은 S-10③ |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | 도구 부재·구문 검사 대체 | Pass | ESLint/설정파일 프로젝트에 없음(`which eslint` 실패, `.eslintrc*` 없음). `node --check opal/tools/skill-registry/skill-registry.js` 구문 검사로 대체 — 통과. |
| 2 | 타입 체크 | 도구 부재·해당 없음 | Skip | 프로젝트가 순수 JS(node:test 기반), TypeScript/mypy 등 타입 체크 도구·설정 없음 — 스킵. |
| 3 | 포맷터 | 도구 부재·구문 검사 대체 | Pass | Prettier 등 포맷터 미설치(`which prettier` 실패, `.prettierrc*` 없음). 별도 포맷 규칙 없으므로 구문 검사(위 1번)로 대체. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | changed_files 전체(skill-registry.js, test-match.js, test-migrate.js, community-skills-registry.json, SKILL.md, skill-commands.md, ARCHITECTURE.md, CONVENTIONS.md, opal_framework_architecture.html) 대상 API key/secret/password/token/private_key 패턴 grep — 0건. |
| 2 | .gitignore 확인 | Pass | `.gitignore`에 `.env`/`env/`/`.venv/` 등 민감 파일 패턴 존재. 신규 파일(user-registry.json 등)은 `~/.opal/` 하위(레포 외부) 생성 대상이라 레포 .gitignore와 무관 — 이상 없음. |
| 3 | path traversal (migrate·제거 경로 검증) | Pass | skill-registry.js:233-235 `resolveFirstPath()`에서 `path.resolve` 정규화 후 `homeDir`/`cwd` 하위 검증(CWE-22 방어) 확인. migrate 로직(:556, :602-604)에서도 `communityDirResolved` 기준 `toPath.startsWith(communityDirResolved)` 가드 존재 — 이동 대상이 `community-skills/` 하위를 벗어나면 차단. |

## 7. 판정

**All Pass (S-1~S-10, 전 시나리오)** — S-10은 캡틴 실환경 확인으로 2026-07-17 Pass 확정 (자동 설치·즉시 실행 + install 재실행 후 user-registry 잔존).

판정 근거: L1/L2 전 시나리오(S-1~S-9) 전부 Pass. node:test 3파일(test-match.js 11건 + test-migrate.js 9건 + test-validate.js 5건, 총 25서브케이스) exit 0 전량 통과(회귀 포함). S-8 산출물 검사(grep + 문서 대조) 정합 확인. 코드 품질(구문 검사 대체) 및 보안(시크릿 스캔·gitignore·path traversal) 전 항목 Pass.

**S-9 이력**: 1차 실행에서 실 공개 anthropics/skills repo 대상 E2E 중 §2 clone-copy 절차의 `{tmp}/{subdir}/` copy 단계가 카탈로그 `source_repo` 값(`anthropics/skills@{name}`)과 실제 업스트림 레이아웃(`{repo}/skills/{name}/` 2중 중첩) 불일치로 실패함을 실측 발견 → PM에 결함 보고(H-6 현실화, anthropics 그룹 17건 전체 영향). 코디네이터가 fix(1/3) 반영: ① 카탈로그 `source_repo` 전수 `@skills/{name}`로 정정 ② SKILL.md §2에 4단계 탐지 폴백 추가(v1.4.1). 신규 스크래치패드(`e2e-064-retry/`)에서 정정 카탈로그로 재실행한 결과, match 판정(installed:false→true)·parse-source-repo·실 git clone→1단계 탐지 즉시 적중(폴백 미발동)→copy→commit_sha(40자 hex)→user-registry 기록→재판정 전 구간 정상 동작 확인. S-9 최종 **Pass**로 재판정.

실 `~/.opal`은 전 과정에서 불가침 유지(스크래치패드 합성 HOME만 사용).

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — 전 시나리오 실 fs/실 clone)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-9 전수, 미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-10)
- [x] 리스크 가설 표(§1) H-N ↔ S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 없음 → M2 의무 트리거 해당 없음 (S-9가 M2로 존재)
