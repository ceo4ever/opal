# TEST SCENARIO: 코드 헤더 작성층 신설 — 인라인 + 외부 code-map 2소스

> 작성일: 2026-07-28 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표(H-1~H-18) 기반
> RED-first 트랙: **강제 적용** — 변경 영역이 도구 CLI 계약·판정 로직이므로 `~/.opal/references/harness/red-first.md` §1.5 "RED-first 강제(API 계약·비즈니스 로직)"에 해당. RED 테스트 작성 주체는 `opal-test-agent(mode: red)`, 구현 주체는 별도(§2 작성자≠구현자).
> M2 의무 트리거: **해당 없음** — 변경 영역에 FE 화면/컴포넌트·인증/인가·외부 API 연동이 없다(전량 Node.js CLI 도구 + 규칙 문서). `test-scenario-guide.md` §Step 3-b "DB 스키마·비즈니스 로직 단독 변경은 M2 면제".

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-012 픽스처 배치 | 저장소 전체 스캔이 픽스처 코드 파일을 흡수 → `missing`·brain `sync-header` 오염 | P1 | L2 | S-19 |
| H-2 | F-002 tier③ package 상속 | `depends` 역의존 탐색이 "파일 선언" → "패키지 선언"까지 매칭 → 정밀도 의미 변화 | P2 | L2 | S-20 |
| H-3 | F-008 `feature` × `--scope` | 기존 `--scope`의 탐색 축소 의미와 cross-scope 조회 요구 충돌 | P2 | L2 | S-16 |
| H-4 | F-011 문서 범위 | 2소스 의미 변화가 `brain-tool/README.md`·`opal-harness.md` §9에 미반영 | P2 | L1 | S-21 |
| H-5 | F-002 단일 파일 역매핑 | PM Gate 8번 `scan <file> --json`이 readonly 파일에서 결과 0건 → 기존 검증 절차 파손 | P0 | L2 | S-8 |
| H-6 | F-009 hook 전역 병합 | code-map 미사용 프로젝트의 매 `Edit`/`Write`에서 실행 → 성능·부작용 | P0 | L2 + L3 | S-18, S-25 |
| H-7 | F-012 테스트 자산 0 | 회귀 기준선 부재로 8커맨드 파손 미검출 | P1 | L2 | S-7 |
| H-8 | F-002 `scanAll:324` 교체 | code-map 부재 시 `resolveHeader`가 `extractHeader`와 다른 값 반환 → 기존 출력 변화 | P0 | L1 + L2 | S-5, S-7 |
| H-9 | F-009 hook matcher | matcher 정규식 alternation 미지원 시 hook 무발동 | P1 | L3 | S-25 |
| H-10 | F-004 scaffold 멱등 | 키 순서·개행 비결정성으로 재실행 diff 발생 → 확정 방향 10 위반 | P1 | L2 | S-10 |
| H-11 | F-001 `stripPrefix` | 두 소스 디렉토리가 동일 미러 경로로 접혀 매니페스트 덮어쓰기 → 데이터 손실 | P0 | L1 + L2 | S-1, S-11 |
| H-12 | F-001 `layerRules` | 동률 구체성에서 배열 순서 의존 시 조회 결과가 흔들림 | P1 | L1 | S-2 |
| H-13 | F-006 `draft` 차단 정책 | `draft`를 위반으로 취급하면 pass2 직후 `validate` 항상 실패 → 우회 유발 | P1 | L2 | S-14 |
| H-14 | F-006 `exports` 텍스트 대조 | 문법 파싱 없는 부분 문자열 대조가 주석·리터럴 우연 일치를 통과시킴 | P2 | L1 | S-3 |
| H-15 | F-005 판정 순서 | readonly 스코프 신규 파일에서 tier 순서 역전 시 `inline` 반환 → 규약 위반 | P0 | L2 | S-12 |
| H-16 | F-002 `_source` 의미론 | brain `sync-header`가 매니페스트 유래 헤더를 코드 실재 주석으로 오인 | P2 | L1 | S-6, S-21 |
| H-17 | F-013 배포 배선 | install 후 `run.sh` 실행 권한 누락 → `tool-scan usage` 실패 잔존 | P0 | L3 | S-22 |
| H-18 | F-012 `.gitignore` | `.opal/*` 무시로 수작업 자산 code-map이 추적되지 않음 | P1 | L2 | S-23 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 이 태스크는 DB를 사용하지 않는다. 사전 조건 데이터는 **저장소 내 합성 픽스처 파일 트리**이며 전량 커밋 자산이다(TASK 제약 ⑦).

| 테이블(=픽스처 트리) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| `tests/fixtures/codemap-repo/` | 6조건 정상 트리 | 자체 `.opal/code-scan.json` + `.opal/code-map/index.json` 보유, 5단 이상 깊은 패키지·소스 루트 상용구 포함 | fixture (Step 2 생성) |
| `tests/fixtures/codemap-repo/` (readonly 스코프) | `scopes.ro` | `readonly: true`, 인라인 헤더 0건, 매니페스트만 보유 | fixture |
| `tests/fixtures/codemap-repo/` (혼재 파일) | 인라인+매니페스트 동시 보유 파일 1건 | 인라인 실필드 + 매니페스트 실필드 동시 | fixture |
| `tests/fixtures/codemap-repo/` (컴파일 사본) | `bin/`·`build/` 중복 사본 디렉토리 | 동일 파일명이 원본과 중복 존재 | fixture |
| `tests/fixtures/codemap-repo/` (앵커 2종) | 빌드 매니페스트 기반 앵커 / 단순 디렉토리 앵커 | 각 1건 | fixture |
| `tests/fixtures/violations/` | 위반 9케이스 | orphan(file/dir)·uncovered(no_entry/incomplete)·conflict(inline_shadowed/mirror_collision)·draft·exports_not_found·권한침범 각 1건 격리 | fixture |
| `tests/fixtures/tiebreak/` | 동률 `layerRules` 2건 | 구체성 점수 동일, 배열 순서만 상이한 2 index | fixture |
| `tests/fixtures/legacy-repo/` | code-map 부재 트리 | `.opal/code-scan.json`만 보유, `.opal/code-map/` 없음 | fixture |
| `tests/fixtures/golden/` | 8커맨드 골든 출력 8파일 | **변경 전 코드**로 비TTY 캡처 | fixture (Step 3 생성) |
| 저장소 자체 | `.opal/code-scan.json` | 신규 생성 — scopes 3종, `exclude`에 `fixtures` 포함 | Step 1 산출 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | codemap-repo index(`stripPrefix` 다중·앵커 유무) | `mirrorPathForDir` 5케이스 직접 호출 | 반환 경로 5건이 기대 문자열과 일치 |
| S-2 | tiebreak index 2건(순서만 상이) | 각 index로 동일 파일 `scan --json` 2회 | 두 결과의 `layer` 동일 |
| S-3 | 존재·미존재·주석내존재 3파일 + 각 exports 엔트리 | exports 대조 함수 직접 호출 | 통과/`exports_not_found`/통과(계약된 한계) |
| S-4 | `version: 2` index / `scopes`·`root` 누락 index | code-map 서브명령 각 1회 | `unsupported_version`·`invalid_index` + exit 1 |
| S-5 | 5단 각 단독 성립 5파일 | `scan --json` 1회 | 필드값 기대 일치 + `_source` 5종 각각 표기 |
| S-6 | 혼재 파일 1건 | `scan <file> --json` | 인라인 값 단독, 매니페스트 필드 미병합, `_source: inline` |
| S-7 | legacy-repo + golden 8파일 | 8커맨드 각 1회(비TTY) | 출력이 골든과 바이트 동일, `_source` 키 0건 |
| S-8 | readonly 스코프 파일(인라인 없음, 매니페스트만) | `scan <해당 파일 경로> --json` | 헤더 반환 + `_source: file` (0건 아님) |
| S-9 | codemap-repo(앵커 2종·컴파일 사본), index 미존재 상태 | `discover` / `discover --dry-run` / index 존재 후 재실행 | 초안 4표시·scopes≥2·layerRules≥1·exclude에 사본 디렉토리 / 파일 미생성 / `index_exists` exit 1 |
| S-10 | codemap-repo, 매니페스트 미존재 → 생성 → description 채움 → 소스 1파일 삭제 | `scaffold` 4회(초기·2회차·채움후·삭제후) | 디렉토리 수=매니페스트 수 / 2회차 바이트 동일 / description 보존 + 신규만 `draft` / 삭제 엔트리 제거 + `pruned` 보고 / 소스 mtime·내용 무변화 |
| S-11 | 동일 미러 경로로 접히는 2 디렉토리 픽스처 | `scaffold` 1회 | `mirror_collision` exit 1 + 어떤 매니페스트도 쓰이지 않음 |
| S-12 | readonly/인라인보유/신규/레거시 4상태 파일 | `target <file>` 각 1회 + code-map 부재 트리 1회 | `reason` 4종 정확 + `write_to` 정확 + manifest 경로·key·scope 실제 미러와 일치 + 부재 트리는 항상 `inline` |
| S-13 | violations 트리(5종) + 위반 0 트리 | `validate` / `validate --changed "a,b"` / `validate --changed -` | 유형별 검출 + exit 2 / 지정 파일만 판정 + `skipped[]` / 위반 0에서 exit 0·`ok: true` / 커버리지 이중 계상 0 |
| S-14 | scaffold 직후(description 공백) 상태 | `validate` → description 채움 → `validate` | exit 2(`draft` N건) → exit 0 |
| S-15 | 허용 필드만 수정 / `dir` 조작 / `files` 키 가감 / `layer`·`domain`·`module` 기재 매니페스트 | `validate` 각 1회 + `scan --json` 1회 | 허용은 exit 0 / 침범은 `worker_scope_violation` + 전용 detail + exit 2 / 침범 `layer`가 조회 결과를 바꾸지 않음 |
| S-16 | 동일 `feature` 태그를 2스코프에 배치 | `feature <id>` / `feature <id> --scope <one>` | 스코프별 그룹 2건 반환 / 지정 스코프 1군만 반환 |
| S-17 | 혼재 픽스처 + `headerSource` 4값(auto/inline/manifest/bogus) | 각 값으로 `scan --json` | inline=지도 유래 0건 / manifest=인라인 유래 0건 / bogus=auto 폴백 + stderr 경고 + stdout JSON 무오염 |
| S-18 | hook 이벤트 JSON 5종(미갱신/갱신완료/code-map부재/깨진JSON/`tool_name: Bash`·`file_path` 부재) + `claude-hooks.json` | hook 스크립트에 stdin 주입 각 1회 + hooks 파일 파싱 | 미갱신만 경고 출력, 나머지 stdout 0바이트, 전 케이스 exit 0 / `PostToolUse` 배열에 기존 Bash 엔트리 + 신규 엔트리 공존 |
| S-19 | 저장소 루트 + 픽스처 루트 | 저장소 루트에서 `scan --json` / 픽스처 루트 `cwd`에서 `scan --json` | 결과 경로에 `fixtures/` 0건 / 결과에 저장소 파일 0건 |
| S-20 | package tier에 `depends` 부여한 매니페스트 | `depends <module>` 1회 | 패키지 상속 파일이 결과에 포함됨(의도된 동작 스냅샷 고정) |
| S-21 | 갱신 대상 문서 7종 | grep 기반 산출물 검사 | 변경이력 행 존재 / "별도 도구 없음" 0건 / 4단·3단·권한경계 3표 존재 / brain README 1문장 추가 + 단방향 문언 diff 0 / harness §9 정합 |
| S-22 | install 실행 전 상태 | `install-mac.sh` 실행 → `run.sh --help` → `tool-scan usage code-scan` → `OPAL_NODE_BIN=/nonexistent run.sh --help` | exit 0 + 사용법 / `ok: true` + 신규 서브명령 포함 / `node_missing` JSON + exit 1 |
| S-23 | `.gitignore` 수정 후 | `git check-ignore -v` 2회 | `.opal/code-map/index.json` 비무시 / `.opal/code-scan.json` 무시 유지 |
| S-24 | codemap-repo 초기 상태(매니페스트 0) + 저장소 자체 | discover→scaffold→(description 채움)→target→validate 4-pass + 자체 저장소 dogfooding 4항목 | 픽스처 소스 파일 0개 수정 상태로 전 파일이 조회 가능(`scan`/`domain`/`layer` 결과에 등장) + validate exit 0 + dogfooding 4항목 로그 |
| S-25 | 배포 완료 상태의 실 세션 | 실제 세션에서 `Write` 1회·`Edit` 1회 발생 | hook 발동 관측(미발동 시 3엔트리 분리 폴백 판정) |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 미러 경로 사상 정방향 5케이스

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `mirrorPathForDir` — `root`→`anchors`→`stripPrefix` 적용 순서, 최장 일치 승리 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | codemap-repo index. 5케이스 = 깊은 경로 / `stripPrefix` 최장 승리 / 앵커 없음 / 루트 직속 / 스코프 외 |
| 기대 결과 | 5케이스 반환 경로가 기대 문자열과 정확히 일치. 스코프 외는 `null`(또는 계약된 미해당 표기) |
| 도구 | `node:test` + `node:assert/strict` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` |
| 결과 | PASS |
| 상세 | `TS-008 (S-1): mirrorPathForDir이 module.exports로 노출되고 5케이스가 기대 문자열과 일치` — 1.5ms, exit 0. 5케이스(깊은 경로/stripPrefix 최장승리/앵커없음/루트직속/스코프외) 전부 기대 문자열과 일치 확인 |

#### S-2: `layerRules` 동률 tie-break 순서 무관

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | 구체성 4단 tie-break(리터럴 문자 수 → 와일드카드 토큰 수 → 원문 길이 → 사전순) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | tiebreak 픽스처 — 동일 점수 규칙 2개를 배열 순서만 바꾼 index 2종 |
| 기대 결과 | 두 index로 동일 파일 조회 시 `layer` 값이 동일 |
| 도구 | `node:test` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` |
| 결과 | PASS |
| 상세 | `TS-009 (S-2): 동률 layerRules — 배열 순서를 바꿔도 동일 layer 반환 (order-a vs order-b)` — 137.5ms, exit 0. tiebreak 픽스처 2종(규칙 순서만 상이)에서 동일 파일 조회 시 `layer` 값 동일 확인 |

#### S-3: `exports` 텍스트 대조 3케이스 계약

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-14 |
| 대상 | exports 존재 대조 — 문법 파싱 없이 텍스트 포함 여부만(PM-4) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 식별자가 ① 실제 선언으로 존재 ② 파일에 부재 ③ 주석 안에만 존재 — 3파일 |
| 기대 결과 | ① 통과 ② `exports_not_found` 보고(파일·키·식별자 단위) ③ **통과**(계약된 한계 — 문법 파서 미도입) |
| 도구 | `node:test` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | `TS-027 (S-3): exports 대조 — 존재(통과)/미존재(exports_not_found)/주석내존재(통과, H-14 계약된 한계)` — 69.9ms, exit 0. 3케이스(실선언/부재/주석내부재) 판정이 계약(H-14)대로 동작함을 확인 |

#### S-21: 규칙 SSOT 7문서 산출물 검사

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-16 |
| 대상 | `header-standard.md`·`header-rules.md`·`code-scan-management.md`·`pm-review-gate.md`·`tools.md`·`opal-harness.md`·`brain-tool/README.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 15~18 문서 갱신 완료 상태 |
| 기대 결과 | ① 변경이력 행이 대상 문서별로 추가 ② `header-rules.md`에서 "별도 도구 없음" grep 0건 ③ 4단 기록 위치 판정·3단 갱신 시점·워커 권한 경계가 각각 표로 존재 ④ `brain-tool/README.md`에 2소스 의미 1문장 추가 + 단방향 계약 문언 diff 0 ⑤ `opal-harness.md` §9 code-scan 행에 신규 서브명령 표기 ⑥ **`pm-review-gate.md` 고유 검사** — 8번 항목에 2소스 판정·합산 커버리지·`validate --changed` CLOSE 게이트 절차 문구가 존재하고, 14번 항목에 신규 서브명령 결과도 인용 대상임이 명시(변경이력 행 존재만으로 통과 처리하지 않는다) |
| 도구 | grep + 산출물 검사 |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-regression.js` |
| 결과 | PASS |
| 상세 | `TS-048/TS-049/TS-047/TS-051/S-21고유` 5건 전부 PASS(0.1~0.9ms). ① 6문서 변경이력에 "077" 표기 존재 ② `header-rules.md` "별도 도구 없음" grep 0건(직접 재확인: `grep -c "별도 도구 없음" opal/core/references/harness/header-rules.md` → 0) ③ 4단 판정·3단 시점·권한경계 3표 존재 ④ `brain-tool/README.md` 1문장 추가 + 단방향 문언 diff 0 ⑤ `opal-harness.md` §9 정합 ⑥ `pm-review-gate.md` 8/14번 항목에 2소스 판정·합산 커버리지·`validate --changed` 게이트 절차 반영(직접 확인: `pm-review-gate.md:52,58,92` 문구 존재). **[재검증(post-fix), 2026-07-28]** 재작업 4건(uncovered 2분류 도입·`--changed` exclude 적용·근접성 판정·`code-scan.js` @header/VERSION 1.3.2/규칙문서 3종 게이트 문구 정합) 반영 후 직접 재확인: `grep -n "077" header-rules.md/pm-review-gate.md/header-standard.md/opal-harness.md/tools.md/code-scan-management.md/brain-tool/README.md` → 7문서 전부 신규 변경이력 행 존재(`header-rules.md` v1.3+v1.4, `pm-review-gate.md` v1.6+v1.7, `header-standard.md` v1.3, `opal-harness.md` v6.7, `tools.md` v2.5+v2.6, `code-scan-management.md` 2026-07-28 v1.2, `brain-tool/README.md` v1.3). `grep -n "newly_uncovered\|pre_existing" pm-review-gate.md` → §8 게이트 기준이 "violations 0건"에서 "`counts.newly_uncovered` 0건"으로 갱신되고 `pre_existing` 비차단 문구가 본문(59~60행)과 변경이력(v1.7)에 모두 존재함을 확인 — "별도 도구 없음" grep 재확인 0건 유지, 문서 정합 회귀 없음 |

### L2. 프로세스 통합 (자동, 실 파일시스템 픽스처 read→CUD→re-read)

#### S-4: index 스키마 거부 2종

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | index 스키마 검증 — `unsupported_version` / `invalid_index` |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `version: 2` index 픽스처 / `scopes` 누락·`root` 누락 index 픽스처 |
| 기대 결과 | ① 모든 code-map 서브명령이 해당 에러 코드로 exit 1 (스키마 오류는 exit 1, 위반은 exit 2 — 계약 분리 확인) ② **패키지 매니페스트 자체가 파싱 불가 JSON일 때 조회 경로(`scan`)가 `manifest_parse_failed` exit 1로 명시 실패하고, 깨진 매니페스트를 조용히 무시한 부분 결과를 반환하지 않는다** (게이트 관찰 보강 — 조회 경로 fail-safe 계약) |
| 도구 | `node:test` + `spawnSync` CLI 블랙박스 |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` |
| 결과 | PASS |
| 상세 | `TS-002 (S-4)` ×2(discover·scan 양쪽 unsupported_version exit 1), `TS-003 (S-4)` ×2(scopes/root 누락 invalid_index exit 1), `S-4 pt.2`(매니페스트 파싱 실패 → manifest_parse_failed exit 1, 부분결과 반환 없음) — 5건 전부 PASS |

#### S-5: 5단 상속 단독 성립 5케이스 + `_source` 표기

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `resolveHeader` — 인라인/`files`/`package`/`layerRules`/`domains` 5단 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 각 단이 단독으로 성립하는 파일 5건 |
| 기대 결과 | 필드값이 기대치와 일치하고 `_source`가 `inline`·`file`·`package`·`rule`·`domain`으로 각각 표기 |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` |
| 결과 | PASS |
| 상세 | `TS-004 (S-5)` 5건 전부 PASS — inline(AdminHome.tsx)/file(OrderService.java)/package(ShipRepo.java)/rule(AdminGuard.tsx)/domain(OrderMisc.java) 각 `_source` 값 기대치 일치. 추가로 headerSource 4값(auto/inline/manifest/bogus)을 별도 임시 픽스처 복사본(`headersource-demo`, 사용 후 삭제)에서 직접 재현 검증(TEST-SCENARIO 작성자 재검증) — auto: 9파일(OrderService.java `_source:file` 포함) / inline: 1파일(AdminHome.tsx만, `_source` 키 미부여) / manifest: 9파일(AdminHome.tsx가 매니페스트 필드로 대체, `_source:file`) / bogus: stderr `Warning: invalid headerSource "bogus", falling back to "auto"` + stdout 9파일(auto와 동일) — S-17 자동 테스트(TS-044/046)가 실제로는 headerSource 값을 오버레이하지 않는 계약 검증 공백을 발견해 수동 재현으로 보강함(§S-17 상세 참조). **[재검증(post-fix), 2026-07-28]** 재작업 3건(uncovered 2분류·`--changed` exclude 적용·근접성 판정) 중 5단 상속 해석(`resolveHeader`) 자체에 대한 변경은 없음 — `node --test opal/tools/code-scan/tests/*.js` 97/97 재실행에 `TS-004`가 포함되어 재확인 PASS(회귀 없음) |

#### S-6: 인라인 단독 승리 (혼재 케이스)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-16 |
| 대상 | 확정 방향 5 — 인라인은 파일 단위 단독 승리, 필드 병합 없음 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 인라인 헤더와 매니페스트 엔트리를 동시에 가진 파일 1건 (매니페스트에만 있는 필드 포함) |
| 기대 결과 | 인라인 값만 반환되고 매니페스트 전용 필드가 병합되지 않으며 `_source: inline` |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` |
| 결과 | PASS |
| 상세 | `TS-005 (S-6): 혼재 파일(AdminHome.tsx) — 매니페스트 전용 필드가 병합되지 않음` — 73.8ms, exit 0. 인라인 값만 반환·매니페스트 전용 필드 미병합·`_source: inline` 확인. **[재검증(post-fix), 2026-07-28]** 인라인 단독 승리 판정 로직은 이번 재작업 범위 밖 — 97/97 재실행에 `TS-005` 포함되어 재확인 PASS(회귀 없음) |

#### S-7: 8커맨드 골든 회귀 (제약② 하위호환)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-8 |
| 대상 | `scan`/`domain`/`layer`/`search`/`exports`/`summary`/`depends`/`missing` — code-map 부재 시 동작 불변 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | legacy-repo 픽스처(code-map 부재) + **변경 전 코드**로 캡처한 골든 8파일. 비TTY 실행(색상 코드 배제) |
| 기대 결과 | 8커맨드 출력이 골든과 **바이트 동일** + 결과에 `_source` 키 0건 + `node code-scan.js` 직접 호출 경로도 동일 |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-regression.js` |
| 결과 | PASS |
| 상세 | `TS-006/043` 골든 회귀 8건(scan/domain/layer/search/exports/summary/depends/missing) 전부 바이트 동일 PASS + `scan --json`에 `_source` 키 0건 확인 — legacy-repo(code-map 부재) 픽스처 대상, 골든은 변경 전 코드로 캡처(mtime 14:40, GREEN 작업 15:24 이전). **[재검증(post-fix), 2026-07-28]** 근접성 판정(`findProximateHeaderIndex`) 도입이 legacy-repo 픽스처의 골든 출력에 영향을 주는지 재확인 — `node --test opal/tools/code-scan/tests/test-regression.js` 단독 재실행 결과 `TS-006/043` 8건 전부 여전히 PASS(바이트 동일 유지, 회귀 없음). 근접성 판정은 저장소 실파일(프로즈에 `@header`를 언급하는 문서)에만 영향을 주고 legacy-repo 골든 픽스처의 JSON 블록 헤더에는 영향 없음을 확인 |

#### S-8: 단일 파일 역매핑 — PM Gate 8번 보호

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `scan <file>` 단일 경로 인자에서 스코프·매니페스트 역매핑 (PM-2 필수 구현) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | readonly 스코프의 파일 1건 — 인라인 헤더 없음, 매니페스트에만 헤더 존재 |
| 기대 결과 | 헤더가 반환되고 `_source: file`. 결과 0건이 아님(0건이면 기존 PM Gate 절차 파손) |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` |
| 결과 | PASS |
| 상세 | `TS-007 (S-8): scan <단일파일> --json — readonly 스코프 파일의 매니페스트 헤더 반환 (PM Gate 8 보호)` — 70.7ms, exit 0. readonly 스코프 단일 파일에서 헤더 반환(0건 아님) + `_source: file` 확인 |

#### S-9: `discover` 초안 생성 + 앵커 2종 + `--dry-run` + 재실행 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `cmdDiscover` — 추론 5종 + 초안 표시 + 멱등 가드 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | index 미존재 codemap-repo(앵커 2종·컴파일 사본 디렉토리 포함) |
| 기대 결과 | ① scopes ≥2 · layerRules ≥1 · exclude에 컴파일 산출물 디렉토리 포함 ② 초안 표시 4필드(`origin`/`status: draft`/`generatedAt`/`note`) 존재 ③ 앵커 2종 각각 검출 ④ `--dry-run`은 파일 미생성 ⑤ index 존재 시 `index_exists` exit 1 ⑥ `domains`·`readonly`는 추론하지 않음 |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-discover.js` |
| 결과 | PASS |
| 상세 | `TS-011` scopes≥2·layerRules≥1·exclude에 target 포함, `TS-012` 초안 4필드(origin/status:draft/generatedAt/note) 존재, `TS-013` 앵커 2종(pom.xml 기반 svc / 1-depth 디렉토리 web) 각각 검출, `TS-014` 기존 index 존재 시 index_exists exit 1 + `--dry-run` 파일 미생성 — 5건 전부 PASS |

#### S-10: `scaffold` 골격·멱등·보존·정리 + 소스 무접촉

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `cmdScaffold`·`mergeManifest`·`writeIfChanged` (PM-5 — `--inline` 미구현) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | codemap-repo. 4회 실행 — 초기 / 즉시 재실행 / description 채운 뒤 / 소스 1파일 삭제 뒤 |
| 기대 결과 | ① 코드 보유 소스 디렉토리 수 = 매니페스트 수 ② `dir`·`files` 키가 실제 파일 목록과 일치 ③ 재실행 산출물 **바이트 동일** ④ description 값 보존 + 신규 파일만 `draft: true` 빈 엔트리 추가 ⑤ 삭제 파일 엔트리 제거 + `pruned` 보고, `dir` 소멸 매니페스트는 자동삭제 없이 `stale` 보고 ⑥ **소스 파일 내용·mtime 변화 0건** |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-scaffold.js` |
| 결과 | PASS |
| 상세 | `TS-015`(디렉토리 수=매니페스트 수), `TS-016`(2회 연속 실행 바이트 동일 — 멱등), `TS-017`(description 보존 + 신규만 draft:true), `TS-018`(소스 삭제 → 엔트리 제거 + pruned 보고), `TS-019`(scaffold 후 소스 mtime·내용 무변화) — 5건 전부 PASS |

#### S-11: 미러 경로 충돌 거부 (`mirror_collision`)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `stripPrefix` 적용 후 두 소스 디렉토리가 동일 미러 경로로 접히는 상황 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 충돌이 성립하는 index + 2 디렉토리 픽스처 |
| 기대 결과 | `mirror_collision` exit 1로 거부되고 **어떤 매니페스트도 쓰이지 않음**(부분 쓰기 없음 — 2-pass 구조 확인) |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-scaffold.js` |
| 결과 | PASS |
| 상세 | `S-11: mirror_collision — scaffold가 exit 1로 거부하고 어떤 매니페스트도 쓰지 않음` — 74.3ms, exit 0(테스트 자체는 통과). 충돌 픽스처에서 `scaffold` 실행 시 exit 1 + 부분 쓰기 0건(2-pass 계산-후-쓰기 구조) 확인 |

#### S-12: `target` 4단 판정 + readonly 우선

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15 |
| 대상 | `decideTarget` — `readonly_repo`·`inline_exists`·`new_file`·`legacy_no_header` |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 4조건 각 1파일 + readonly 스코프 × (신규/인라인보유/레거시) 3케이스 + code-map 부재 트리 |
| 기대 결과 | ① 4조건에서 각 `reason`·`write_to` 정확 ② `write_to: manifest`일 때 `scope`·`manifest`·`key`가 실제 미러 경로와 일치 ③ readonly 3케이스 **전부** `manifest`+`readonly_repo` ④ code-map 부재 트리는 항상 `inline` |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-target.js` |
| 결과 | PASS |
| 상세 | `TS-020/022` readonly(legacy) 기존+신규 파일 전부 `manifest+readonly_repo`, `TS-020` 인라인보유(inline/inline_exists)·신규(inline/new_file), `TS-020/021` 존재+인라인없음(manifest/legacy_no_header + 경로정합), `TS-023` code-map 부재 트리는 항상 `inline` — 7건 전부 PASS. S-24 ⑨에서 실사용 재현(신규 파일 target=inline/new_file, 관련 상세는 §S-24 참조) |

#### S-13: `validate` 5종 위반 + 합산 커버리지 + `--changed`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | `cmdValidate` 검출기 5종 + `computeCoverage` + exit code 0/1/2 계약 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | violations 트리(orphan·uncovered·conflict·draft·exports_not_found) + 위반 0 트리 |
| 기대 결과 | ① 유형별 검출 + exit 2 ② 커버리지 %가 인라인+지도 합산, 동일 파일 이중 계상 0 ③ `--changed "a,b"`·`--changed -`(stdin) 두 형식에서 지정 파일만 판정 + 대상 외 경로는 `skipped[]` 기록 ④ 위반 0에서 exit 0·`ok: true` ⑤ **[재검증(post-fix)]** `uncovered`가 git 기준 2분류(`newly_uncovered` 차단/`pre_existing` 비차단)로 분리되고, `--changed`가 전체 스캔과 동일한 `exclude`/`excludePatterns`를 적용해 제외 경로는 `skipped[{file,reason}]`로 기록 |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | `TS-024` 위반 7종(orphan:file_missing/dir_missing, uncovered:no_entry/incomplete, conflict:inline_shadowed, draft, exports_not_found) 전부 검출+exit 2, `TS-025`(커버리지 인라인+지도 합산·이중계상 0), `TS-026` ×2(`--changed` csv·stdin 두 형식, 범위 외 skipped[]), `TS-028`(위반 0건 → exit 0·ok:true) — 11건 전부 PASS. **[재검증(post-fix), 2026-07-28]** 재작업 반영 후 `node --test opal/tools/code-scan/tests/*.js` 재실행 → **97/97 PASS, exit 0**(기존 81건 + 신규 `TS-077-A-1~5`(newly_uncovered/pre_existing 5분기) + `TS-077-B-1~3`(exclude 적용 3케이스) 16건 추가). 신규 케이스 전부 PASS: `TS-077-A-1`(신규 미커버 파일→newly_uncovered+exit2), `TS-077-A-2`(HEAD엔 있었으나 회귀 제거→newly_uncovered+exit2), `TS-077-A-3`(HEAD에도 미커버 기존 파일→pre_existing+exit0), `TS-077-A-4`(혼재→newly_uncovered exit2 + counts 양쪽 노출), `TS-077-A-5`(비git 트리→전량 pre_existing+exit0+stderr 경고), `TS-077-B-1`(exclude 디렉토리 대상 --changed 파일→skipped[excluded_dir]), `TS-077-B-2`(excludePatterns 매치→skipped[excluded_pattern]), `TS-077-B-3`(대조군, exclude 미해당 신규 미커버 파일→기존대로 newly_uncovered+exit2 — 회귀 없음 확인). 직접 재실행 증거: `node opal/tools/code-scan/code-scan.js validate --changed "<22개 077 변경파일 csv>" --json` → `exit 0`, `{"ok":true,...,"counts":{"uncovered":6,"newly_uncovered":0,"pre_existing":6},"skipped":[5건 unsupported_extension]}` — 참조문서 6종은 `pre_existing`(비차단)으로 정확히 분류됨 |

#### S-14: `draft` 차단 정책과 해소 경로

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | `draft`를 차단 위반으로 취급하는 정책의 정상 해소 흐름 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `scaffold` 직후 상태(description 공백 다수) → pass3 채움 후 상태 |
| 기대 결과 | scaffold 직후 `validate` = exit 2(`draft` N건 보고) → 채움 후 = exit 0. `--changed`로 판정 범위가 변경 파일에 한정됨 |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | `TS-029 (S-14): draft 상태 exit 2 → description 채운 뒤 exit 0` — 142.1ms. scaffold 직후(description 공백) `validate`=exit 2(draft N건) → 채움 후 exit 0 확인. `--changed` 범위 한정은 TS-026과 공유 검증. **[재검증(post-fix), 2026-07-28]** `draft` 정책 로직 자체는 이번 재작업 대상이 아니므로(재작업 3건은 uncovered 2분류·`--changed` exclude 적용·근접성 판정) 변경 없음 — `node --test opal/tools/code-scan/tests/test-validate.js`가 전체 97/97 재실행에 포함되어 `TS-029` 재확인 PASS(회귀 없음) |

#### S-15: 워커 권한 경계 집행

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15 |
| 대상 | `checkWorkerScope` — 도구 관할 필드 재계산·대조 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | ① 허용 필드(`description`/`exports`/`depends`/`note`)만 수정 ② `dir` 조작 ③ `files` 키 임의 추가·삭제 ④ `layer`·`domain`·`module` 기재 — 4종 매니페스트 |
| 기대 결과 | ① exit 0 통과 ② `worker_scope_violation`/`dir_mismatch` ③ `files_key_added`/`files_key_removed` ④ 각 전용 detail로 거부 + exit 2 ⑤ 침범 기재된 `layer`가 `scan` 결과 layer를 바꾸지 않음(해석 단계 무시 확인) |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | `TS-030`(허용 필드만 수정 → exit 0), `TS-031`(`dir` 조작 → worker_scope_violation:dir_mismatch exit 2), `TS-032`(`files` 키 추가/삭제 → files_key_added/files_key_removed), `TS-033/034`(layer/domain/module 침범 → 전용 detail 거부 + `scan` 결과 layer 불변으로 해석 무시 확인) — 4건 전부 PASS. S-24 ⑨ 재현에서 `files_key_removed`(스테일 매니페스트) 실사례 추가 관측(상세는 §S-24) |

#### S-16: `feature` cross-scope 조회와 `--scope` 상호작용

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `cmdFeature` (PM-1 — 기본 전체 순회, `--scope` 시 제한) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 동일 `feature` 태그를 서로 다른 2스코프 파일에 부여 |
| 기대 결과 | `feature <id>`는 스코프별 그룹 2건 반환 / `feature <id> --scope <one>`은 해당 스코프 1군만 반환 |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-feature.js` |
| 결과 | PASS |
| 상세 | `TS-035`(기본 전체 순회, svc 스코프 order-create 검출), `TS-036` ×2(`--scope web`/`--scope svc` 각 단일 그룹만 반환), `TS-037` ×2(태그 미부여 시 빈 결과, 인자 누락 시 Usage+exit 1) — 5건 전부 PASS |

#### S-17: `headerSource` 스위치 4값

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `headerSource: auto|inline|manifest` + 잘못된 값 폴백 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 혼재 픽스처에 `headerSource` 4값(auto/inline/manifest/`"bogus"`) 각각 설정 |
| 기대 결과 | `inline`=지도 유래 헤더 0건 / `manifest`=인라인 보유 파일도 `_source`가 `inline`이 아님 / `bogus`=`auto` 폴백 + stderr 경고 + **stdout JSON 무오염** |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` (자동) + 수동 재현(임시 픽스처 복사본) |
| 결과 | PASS (자동 테스트는 통과하나 커버리지 공백 발견 — 수동 재현으로 보강 확인) |
| 상세 | 자동: `TS-044`(inline, 71ms)·`TS-046`(bogus→auto 폴백+stdout 무오염, 71ms) PASS. **발견**: `test-resolve-header.js:319-342`의 테스트 코드 주석에 "환경변수 오버라이드는 지원되지 않으므로... 별도 설정 오버레이 없이 계약만 검증"이라 명시되어 있어, TS-044/046은 실제로 `headerSource` 값을 fixture config에 설정하지 않고 auto 모드 결과만 확인한다 — 즉 `headerSource:"inline"`/`"manifest"`/`"bogus"`를 실제로 오버레이해 분기 동작을 검증하는 자동 테스트는 없음(TS-045 "manifest" 케이스 자체가 아예 부재). 이는 F-010 AC에 대한 자동 회귀 커버리지 공백이다. **수동 재현**(codemap-repo 픽스처를 임시 복사본 `headersource-demo`에 복제 후 `.opal/code-scan.json`에 각 값 주입, 검증 후 삭제)으로 실제 구현 동작은 정확함을 직접 확인: auto=9파일(OrderService.java `_source:file`), inline=1파일(AdminHome.tsx만, `_source` 키 없음), manifest=9파일(AdminHome.tsx가 매니페스트 필드로 대체됨, 인라인 무시), bogus=stderr 경고 `Warning: invalid headerSource "bogus", falling back to "auto"` + stdout 9파일(auto와 동일, JSON 무오염). **판정**: 기능 구현은 PASS, 자동 테스트 커버리지는 미흡(권고: TS-045 신설 + TS-044/046에 실제 config 오버레이 추가) |

#### S-18: hook 무해 이탈 + 경고 발생 + 배선 공존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, H-9 |
| 대상 | `code-map-hook.js` 조기 이탈 9단 + `claude-hooks.json` additive 엔트리 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | stdin 이벤트 JSON 5종 — ① 대상 파일 수정 + 매니페스트 미갱신 ② 갱신 완료 ③ code-map 부재 트리 ④ 깨진 JSON ⑤ `tool_name: Bash`·`file_path` 부재 |
| 기대 결과 | ①만 경고 출력, ②~⑤ stdout **0바이트**, 전 케이스 **exit 0**(fail-safe). `claude-hooks.json` 파싱 시 `PostToolUse`에 기존 Bash 엔트리와 신규 엔트리가 공존 |
| 도구 | `node:test` + `spawnSync`(stdin 주입) |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-hook.js` |
| 결과 | PASS |
| 상세 | `TS-038`(미갱신 대상 → additionalContext 경고 + exit 0), `TS-039`(갱신 완료 → 0바이트 + exit 0), `TS-040`(code-map 부재 트리 → 0바이트 + exit 0), `TS-041` ×3(깨진 JSON/`tool_name:Bash`/`file_path` 부재 → 전부 0바이트+exit 0 fail-safe), `TS-042`(`claude-hooks.json` PostToolUse 배열에 기존 Bash 엔트리 + 신규 엔트리 공존) — 7건 전부 PASS. hook 소스에 `exec/execSync/spawn/child_process` 부재 확인(§6 보안 항목3과 연동) |

#### S-19: 픽스처 이중 격리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 저장소 `.opal/code-scan.json`의 `exclude` + 픽스처 자기완결 `.opal/`(PM-6) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 1·2 완료 상태 |
| 기대 결과 | 저장소 루트 `scan --json` 결과 경로에 `fixtures/` **0건** / 픽스처 루트 `cwd` 실행 결과에 저장소 파일 **0건** |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-regression.js` |
| 결과 | PASS |
| 상세 | `TS-052 (S-19): 저장소 루트 scan --json — fixtures/ 경로 0건` (111ms) + `TS-053 (S-19): 픽스처 루트 cwd 실행 — 저장소 파일 0건` (76ms) — 이중 격리 확인. Step 19 시점 실측 재확인(수동): 저장소 루트 `run.sh scan --json` 결과 `fixtures/` 경로 0건, `tasks/` 경로 0건(§S-24 ⑦과 동일 근거 데이터). **[재검증(post-fix), 2026-07-28]** 근접성 판정(`findProximateHeaderIndex`) 도입으로 오탐 4건이 제거되어 저장소 전체 헤더 보유 수가 101→**97**로 변경됨 — 직접 재실행: `node opal/tools/code-scan/code-scan.js scan --json`(저장소 루트) → 결과 파일 수 **97**, `tasks/` 경로 **0건**, `fixtures/` 경로 **0건**(파이썬으로 키 필터링 재계산 확인) — 격리 계약 자체는 회귀 없음, 총량만 오탐 제거로 감소 |

#### S-20: `depends` 패키지 상속 정밀도 스냅샷

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `cmdDepends` 역의존 탐색이 tier③ 상속 `depends`까지 매칭하는 동작 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `package` 계층에 `depends`를 부여한 매니페스트 + 그 디렉토리의 파일 2건 |
| 기대 결과 | 패키지 상속 파일이 `depends <module>` 결과에 포함됨 — 의도된 동작임을 스냅샷으로 고정(향후 변경 시 회귀 검출) |
| 도구 | `node:test` + `spawnSync` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` |
| 결과 | PASS |
| 상세 | `S-20 (H-2): depends "ship-common" — package tier 상속이 2개 파일 모두에서 dependedBy로 검출` — 69.9ms, exit 0. package tier `depends` 상속분이 `depends <module>` 결과에 2파일(ShipRepo.java, ShipValidator.java) 모두 포함됨을 스냅샷 고정 |

#### S-23: `.gitignore` code-map 추적 예외

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-18 |
| 대상 | `.opal/*` 무시 규칙과 code-map 예외의 공존 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `.gitignore`에 `!.opal/code-map/` + `!.opal/code-map/**` 추가 후 |
| 기대 결과 | `git check-ignore -v .opal/code-map/index.json`이 **비무시** / `.opal/code-scan.json`은 **무시 유지**(파생 캐시와 수작업 자산 구분) |
| 도구 | `git check-ignore` + `node:test` |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-regression.js` (자동) + `git check-ignore -v` (수동 재확인) |
| 결과 | PASS |
| 상세 | `TS-055 (S-23)` 자동 PASS(39.2ms). 수동 재확인: `git check-ignore -v .opal/code-map/index.json` → `.gitignore:6:!.opal/code-map/**` 매칭(비무시), `git check-ignore -v .opal/code-scan.json` → `.gitignore:2:.opal/*` 매칭(무시 유지) |

### L3. 실환경 / 사용자 협업

#### S-22: `run.sh` 래퍼 배포·권한·tool-scan 연동

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-17 |
| 대상 | `opal/tools/code-scan/run.sh` + `install-mac.sh` chmod 블록 + tool-scan 매니페스트 |
| 계층 | L3 |
| **실행 방식** | **M1** (실환경 CLI — install 실행 필요) |
| 조건 | Step 13 완료 후 `./scripts/install-mac.sh` 재실행 |
| 기대 결과 | ① `~/.opal/tools/code-scan/run.sh --help` exit 0 + 사용법 출력 ② `tool-scan usage code-scan`이 `ok: true` + 신규 서브명령 포함(현재는 `help_exec_failed`) ③ `OPAL_NODE_BIN=/nonexistent run.sh --help` → `node_missing` JSON + exit 1 |
| 도구 | Bash + `tool-scan` |
| 실행 명령 | `./scripts/install-mac.sh` → `~/.opal/tools/code-scan/run.sh --help` → `~/.opal/tools/tool-scan/run.sh usage code-scan` → `OPAL_NODE_BIN=/nonexistent ~/.opal/tools/code-scan/run.sh --help` |
| 결과 | PASS |
| 상세 | install 재실행 exit 0(OPAL v0.6.10-13-g7632527, Console 재기동 포함 정상 완료). ① `run.sh --help` exit 0 + USAGE 전문 출력(신규 서브명령 discover/scaffold/target/validate/feature 포함) ② `tool-scan usage code-scan` → `{"ok": true, ..., "exit_code": 0, "usage_text": "...discover...scaffold...target...validate...feature..."}` — H-17이 지적한 기존 `help_exec_failed` 잔존이 해소됨을 실측 확인 ③ `OPAL_NODE_BIN=/nonexistent run.sh --help` → `{"ok":false,"error":"node_missing","detail":"Node.js not found. Install Node 18+."}` + exit 1. **[재검증(post-fix), 2026-07-28]** install 재실행은 하네스 Guards(install 재실행 금지)에 따라 생략하고, 이미 배포된 바이너리 상태만 재조회 — `~/.opal/tools/code-scan/run.sh --help` → exit 0 + `code-scan v1.3.2` 배너 + USAGE 전문(신규 서브명령 5종 포함) 확인(버전 표기가 1.3.2로 재작업 항목 4 반영 확인), `~/.opal/tools/tool-scan/run.sh usage code-scan` → `{"ok":true,...,"exit_code":0}` + usage_text에 discover/scaffold/target/validate/feature 5종 포함 재확인, `OPAL_NODE_BIN=/nonexistent ~/.opal/tools/code-scan/run.sh --help` → `{"ok":false,"error":"node_missing",...}` + exit 1 재확인, `~/.claude/settings.json`의 `PostToolUse` 배열에 `matcher: "Edit\|Write\|MultiEdit"` 엔트리(`code-map-hook.js` 호출)가 기존 `Bash`(state-tool) 엔트리와 공존함을 재확인 — 배포 배선 회귀 없음 |

#### S-24: 목표달성 — 소스 0수정 자산화 4-pass + 자체 dogfooding

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-5, H-13 (태스크 목표 종합) |
| 대상 | **태스크 목표 자체** — 소스 파일을 수정하지 않고 기존 코드 전량을 code-scan 조회 자산으로 만든다 |
| 계층 | L3 |
| **실행 방식** | **M1** (실환경 CLI 연속 실행) |
| 조건 | 매니페스트 0 상태의 codemap-repo(readonly 스코프 포함) + 자체 저장소 |
| 기대 결과 | ① discover→scaffold→(description 채움)→target→validate 4-pass 완주 ② 픽스처 **소스 파일 0개 수정**(`git status` 기준 소스 diff 0) ③ 4-pass 후 `scan`/`domain`/`layer` 결과에 readonly 스코프 파일이 전부 등장 ④ `validate` exit 0 ⑤ 자체 저장소 dogfooding 4항목(8커맨드 골든 회귀 / `discover --dry-run` / `validate --changed` / `tool-scan usage`) 로그 증명 ⑥ 신규 테스트 파일 8종이 `@header` JSON 블록을 보유하고 `scan`에 잡힘 ⑦ **저장소 스캔 범위 교체 전후 대조** — Step 1 전(스코프 미정의 → 저장소 전체 순회)과 후(3스코프 한정)의 `scan --json` 결과 경로 수를 비교하고, 후 상태에서 `tasks/`·`fixtures/` 경로가 0건임을 증명 ⑧ **`missing` 결과 축소 전후 대조** — 동일 대조로 `missing` 목록이 실제 대상 스코프로 축소됨을 증명(신설 도구의 자기 보고가 아니라 기존 커맨드의 관측 변화로) ⑨ **인라인 트랙 4-pass 1케이스** — 비 readonly 스코프의 신규 파일에서 `target`이 `inline`을 반환하고, 인라인 헤더 작성 후 `validate` 커버리지에 인라인분으로 합산됨을 확인 |
| 도구 | Bash + `node --test` + `git status` |
| 실행 명령 | (아래 상세에 개별 명령 나열 — 4-pass는 픽스처 `codemap-repo` 격리 실행, dogfooding 4항목 + 보강 3항목은 저장소 자체 실행) |
| 결과 | **PASS** (재검증 후 갱신 — 이전 PARTIAL FAIL의 원인이었던 ④가 재작업으로 해소됨. 이력: 최초 검증 시 ①②③⑤⑥⑦⑧⑨ PASS / ④ FAIL → 재작업 후 ④ PASS로 전환, 전 항목 PASS) |
| 상세 | **① 4-pass**: `node --test opal/tools/code-scan/tests/test-scaffold.js`(TS-015~019)·`test-target.js`(TS-020~023)·`test-validate.js`(TS-024~034) 전량 PASS로 discover→scaffold→(description 채움)→target→validate 흐름이 픽스처 `codemap-repo`에서 완주됨을 자동 테스트로 확인. **② 소스 0수정**: `git status --porcelain opal/tools/code-scan/tests/` → 전 항목 `??`(신규 미추적)만 존재, `M`(수정) 0건 — 픽스처 소스 파일에 대한 수정 이력 없음. **③**: `TS-020/022`(readonly 파일 전부 조회 가능, manifest+readonly_repo)로 확인. **④ FAIL**: 자체 저장소 changed_files(`.gitignore`, `claude-hooks.json`, `header-rules.md`, `pm-review-gate.md`, `header-standard.md`, `opal-harness.md`, `code-scan-management.md`, `tools.md`, `brain-tool/README.md`, `code-scan.js`, `tool-scan/manifest.json`, `install-mac.sh`, `code-map-hook.js`, `run.sh`, 신규 테스트 8파일)를 `~/.opal/tools/code-scan/run.sh validate --changed "<21개 경로>" --json`로 실행한 결과 **`exit=2`, `ok:false`, 8건 `uncovered` 위반**(`header-rules.md`/`pm-review-gate.md`/`header-standard.md`/`opal-harness.md`/`tools.md`/`brain-tool/README.md`/`code-scan.js`가 `no_entry`, `code-scan-management.md`가 `incomplete`) — PLAN §3.12.2(G)③·pm-review-gate.md §8이 요구하는 "CLOSE 진입 전 게이트 = exit 0"을 이 태스크 자신의 변경분이 통과하지 못함. 원인: 이 저장소 `.opal/code-scan.json`이 `extensions`에 `.md`를 포함하고 `header-rules.md` 자신도 "`.md`가 config에 추가된 경우 md 파일도 적용 대상"이라 규정하므로, 이번에 수정한 참조문서 6종과 `code-scan.js` 자신이 실제로 @header 작성 대상인데 미기재 상태다. **고치지 않고 실패로 보고**(Guards: 이 Step은 검증 전용). **⑤**: `discover --dry-run --json`은 stdout에만 초안 생성, `.opal/code-map/` 미생성(`ls` 실패로 확인) — 위 S-22 실행과 별개로 재확인. **⑥ dogfooding 4항목**: (1) 8커맨드(`scan --scope framework --json`/`summary`/`missing`/`domain`/`layer`/`search`/`exports`/`depends`, 전부 `--scope framework`) 전부 exit 0 — 골든 대조는 S-7(legacy-repo 픽스처)로 이미 확보, 저장소 실행은 정상종료만 확인(회귀는 픽스처 골든이 권위 소스이므로 이중 대조 불필요) (2) `discover --dry-run --json` → scopes 3종(framework/console-fe/console-be)·layerRules 6개·exclude 10건 포함 초안 생성, `.opal/code-map/` 미생성 (3) `validate --changed` → **위 ④ FAIL 참조** (4) `tool-scan usage code-scan` → `ok:true` + 신규 서브명령 포함(S-22와 동일 근거). **⑦ 스캔 범위 전후 대조** (임시 격리 복사본 `before-sim-077`에서 수행, 실제 `.opal/code-scan.json` 무변경): AFTER(현재 3스코프 설정) `scan --json` = 101개 헤더 파일, `tasks/`·`fixtures/` 경로 **0건**. BEFORE(복사본의 config만 `scopes:{}`로 교체해 전체 워크 시뮬레이션) `scan --json` = 114개, 그중 `tasks/` **5건**(우연히 @header JSON 블록을 예시로 포함한 기존 태스크 문서 4건 + 유사 1건), `fixtures/` **5건**(픽스처가 의도적으로 보유한 실헤더 파일) — 스코프 한정으로 실오염 5+5건이 정확히 0으로 차단됨을 수치로 증명. **⑧ missing 축소 전후 대조** (동일 복사본): AFTER(스코프 한정) `missing` = **231건**, `tasks/` 0건·`fixtures/` 0건. BEFORE(전체 워크) `missing` = **1036건**, `tasks/` **526건**·`fixtures/` **37건** — 스코프 한정이 `missing` 노이즈를 1036→231건(-78%)으로, tasks/fixtures 오염을 526+37→0으로 축소함을 기존 커맨드의 관측 변화로 증명(AGENTIC-LOG Step1 기록 230건과 현재 231건의 근소한 차이는 ④에서 발견된 문서 7종의 최근 uncovered 전이가 원인). **⑨ 인라인 트랙 1케이스** (임시 복사본에서만 수행, `tests/fixtures/codemap-repo` 원본은 무수정): svc(비readonly) 스코프에 존재하지 않는 신규 파일 경로에서 `target` → `{"write_to":"inline","reason":"new_file"}` 확인 → 인라인 `@header` JSON 블록 작성 → `target` 재조회 시 `{"write_to":"inline","reason":"inline_exists"}` → `validate` 커버리지 `covered` 7→8(inline 1→2, total 9→10)로 신규 인라인분이 합산됨을 확인. 부수 관찰: 해당 디렉토리가 이미 scaffold된 매니페스트를 보유해 신규 파일이 매니페스트 `files` 목록에 없다는 `worker_scope_violation:files_key_removed`가 추가로 발생 — 이는 버그가 아니라 "매니페스트 존재 디렉토리는 재scaffold 필요"라는 설계상 정합 신호(재scaffold로 해소됨, 별도 결함 아님). **RED 파일 불변**: `tests/test-*.js` 8종 mtime 14:49~14:58(RED phase), `fixtures/golden/*` mtime 14:40(RED phase, 코드 변경 15:24 이전 캡처) — GREEN 이후(15:24~) 무수정 확인. 예외 1건: `fixtures/violations/exports-missing/svc/mod/Missing.java` mtime 15:33(GREEN 이후) — 내용은 결함 설명 주석 1줄 추가(`// fixture: the manifest declares an identifier that is absent from this file's text.`)이며 PM 승인된 결함 수정으로 처리(디스패치 프롬프트 명시 예외). ***[재검증(post-fix), 2026-07-28] ④ 재확인 — 핵심 항목***: 재작업 3건(`uncovered` 2분류 도입, `--changed` exclude 적용, `code-scan.js` @header/VERSION 1.3.2/규칙문서 3종 게이트 문구 정합) 반영 후, 이 태스크의 실제 변경 파일(22개 — `.gitignore`, `claude-hooks.json`, 참조문서 6종(`header-rules.md`/`pm-review-gate.md`/`header-standard.md`/`opal-harness.md`/`code-scan-management.md`/`tools.md`), `brain-tool/README.md`, `code-scan.js`, `tool-scan/manifest.json`, `install-mac.sh`, `code-map-hook.js`, `run.sh`, 신규 테스트 8종)를 대상으로 재실행: `node opal/tools/code-scan/code-scan.js validate --changed "<22개 경로 csv>" --json` → **결과: `exit 0`**, `{"ok":true,"coverage":{"total":17,"inline":11,"manifest":0,"covered":11,"percent":64.7},"counts":{"orphan":0,"uncovered":6,"conflict":0,"draft":0,"exports_not_found":0,"worker_scope_violation":0,"newly_uncovered":0,"pre_existing":6},"violations":[6건 전부 code:"uncovered",sub:"pre_existing"(header-rules.md/pm-review-gate.md/opal-harness.md/code-scan-management.md/tools.md/brain-tool/README.md)],"skipped":[5건 unsupported_extension(.gitignore/.json×2/.sh×2)]}` — **`newly_uncovered: 0`**로 CLOSE 게이트 통과 조건(`counts.newly_uncovered` 0건, pm-review-gate.md §8 v1.7 기준) 충족. 남은 6건 `uncovered`는 전부 `pre_existing`(HEAD 시점에도 미커버였던 기존 문서 — 레거시 소급 부여는 discover/scaffold 몫)으로 비차단 분류되어 `ok:true`에 포함됨. 참고로 `header-standard.md`와 `code-scan.js`는 이번 violations 목록에서 완전히 사라짐(이전 FAIL 시점의 `no_entry`에서 해소 — 현재 인라인 헤더/커버리지 보유 상태로 전환 확인). 추가로 저장소 전체 변경분(tasks/ 제외 55개 `.js`/`.md`) 대상 광역 재확인도 수행: `exit 0`, `counts:{"uncovered":33,"newly_uncovered":0,"pre_existing":33}`, `skipped`에 `tests/fixtures/**` 경로들이 `reason:"excluded_dir"`로 정확히 제외됨을 확인(재작업 항목 2 — `--changed`의 exclude/excludePatterns 적용 회귀 없음). **결론: 이전 검증(Step 19)의 FAIL이 재작업으로 완전히 해소됨 — CLOSE 게이트 통과.** |

#### S-25: hook 실 세션 발동 관측 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9, H-6 |
| 대상 | 배포된 `claude-hooks.json` matcher가 실제 세션의 `Edit`/`Write`에서 발동하는지 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — matcher 발동은 세션 런타임 이벤트라 자동화 불가. M2 자동화 시도 대상 아님(브라우저·외부 시스템 무관) |
| 조건 | install 재실행 완료 + code-map 보유 프로젝트에서 실제 세션 진행 |
| 기대 결과 | code-map 대상 파일을 `Write`·`Edit`로 수정했을 때 hook 경고가 관측된다. 미발동이면 폴백 판정 = matcher를 `Edit`/`Write`/`MultiEdit` 3엔트리로 분리 등록 |
| 실행자 | **[SUPERVISOR]** — 캡틴 수동 확인 필요 |
| 결과 | 캡틴 확인 대기 |
| 상세 | opal-test-agent는 L3 [SUPERVISOR] 시나리오를 실행하지 않고 PM에 위임한다(행동 규칙). install 재배포는 S-22/S-24에서 완료되어 실 세션 관측을 위한 전제 조건은 충족된 상태 |

**PM 표준 요청 양식 (TEST 단계에서 사용)**:
```
캡틴, [시나리오 S-25]는 사용자 협업 검증이 필요합니다.
요청 내용: install 재배포 후 code-map을 보유한 프로젝트에서 파일 1개를 Write/Edit로 수정해 주십시오.
기대 결과: 매니페스트 미갱신 상태라면 code-map hook 경고가 1회 표시됩니다(무관 파일·code-map 부재 시에는 아무 출력도 없어야 정상).
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 AC (스키마 표 존재) | H-4 | L1 | S-21 | 산출물 검사 [T077/L1-F1] | `header-standard.md` 2소스 절 |
| F-1 AC (스키마 위반 거부) | H-8 | L2 | S-4 | `test-resolve-header.js`:[T077/L2-F1] | `unsupported_version`·`invalid_index` |
| F-2 AC (5단 + `_source`) | H-8 | L2 | S-5 | `test-resolve-header.js`:[T077/L2-F2a] | 5단 단독 5케이스 |
| F-2 AC (인라인 단독 승리) | H-16 | L2 | S-6 | `test-resolve-header.js`:[T077/L2-F2b] | 병합 금지 |
| F-2 AC (경로 사상) | H-11 | L1 | S-1 | `test-resolve-header.js`:[T077/L1-F2] | 정방향 5케이스 |
| F-1 AC (`layerRules` 결정론) | H-12 | L1 | S-2 | `test-resolve-header.js`:[T077/L1-F1b] | 동률 tie-break 순서 무관 |
| F-2 AC (단일 파일 역매핑) | H-5 | L2 | S-8 | `test-resolve-header.js`:[T077/L2-F2c] | PM Gate 8번 보호 |
| F-3 AC | H-10 | L2 | S-9 | `test-discover.js`:[T077/L2-F3] | 초안 4표시·앵커 2종·dry-run |
| F-4 AC①②③ | H-10 | L2 | S-10 | `test-scaffold.js`:[T077/L2-F4] | 멱등·보존·pruned·소스 무접촉 |
| F-4 AC (충돌 거부) | H-11 | L2 | S-11 | `test-scaffold.js`:[T077/L2-F4b] | `mirror_collision` |
| F-5 AC | H-15 | L2 | S-12 | `test-target.js`:[T077/L2-F5] | `reason` 4종 + readonly 우선 |
| F-6 AC (5종·커버리지·changed) | H-13 | L2 | S-13 | `test-validate.js`:[T077/L2-F6] | exit 0/1/2 계약 |
| F-6 AC (exports 대조) | H-14 | L1 | S-3 | `test-validate.js`:[T077/L1-F6] | 계약된 한계 고정 |
| F-6 AC (draft 정책) | H-13 | L2 | S-14 | `test-validate.js`:[T077/L2-F6b] | scaffold 직후 exit 2 → 채움 후 0 |
| F-7 AC | H-15 | L2 | S-15 | `test-validate.js`:[T077/L2-F7] | 권한 경계 + 해석 무시 |
| F-8 AC | H-3 | L2 | S-16 | `test-feature.js`:[T077/L2-F8] | cross-scope + `--scope` |
| F-9 AC | H-6 | L2 | S-18 | `test-hook.js`:[T077/L2-F9] | 무해 이탈 + 경고 + 배선 |
| F-9 AC (실 발동) | H-9 | L3 | S-25 | 수동 [SUPERVISOR] | matcher 런타임 검증 |
| F-10 AC | H-8 | L2 | S-17 | `test-resolve-header.js`:[T077/L2-F10] | 4값 + 폴백 |
| F-10 AC (회귀 0) | H-7, H-8 | L2 | S-7 | `test-regression.js`:[T077/L2-F10b] | 골든 바이트 동일 |
| F-11 AC①②③④ | H-4, H-16 | L1 | S-21 | 산출물 검사 [T077/L1-F11] | 7문서 + 변경이력 |
| F-11 AC④ (tool-scan) | H-17 | L3 | S-22 | Bash [T077/L3-F11] | `ok: true` |
| F-12 AC (격리) | H-1 | L2 | S-19 | `test-regression.js`:[T077/L2-F12a] | 이중 격리 |
| F-12 AC (gitignore) | H-18 | L2 | S-23 | `test-regression.js`:[T077/L2-F12b] | 예외 + 무시 유지 |
| F-12 AC (4-pass·dogfooding) | H-1, H-5, H-13 | L3 | S-24 | Bash + `node --test` [T077/L3-F12] | **목표달성 시나리오** |
| F-13 AC①②③ | H-17 | L3 | S-22 | Bash [T077/L3-F13] | 래퍼·권한·하위호환 |
| 제약② (하위호환) | H-7, H-8 | L2 | S-7 | `test-regression.js`:[T077/L2-C2] | 8커맨드 골든 |
| 확정 방향 5 (정밀도 의미) | H-2 | L2 | S-20 | `test-resolve-header.js`:[T077/L2-H2] | 상속 스냅샷 고정 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | 해당 없음(구성 부재) | N/A | 저장소 루트에 ESLint 설정(`.eslintrc*`) 및 루트 `package.json`이 없음 — JS 린터 미구성. 대신 `node --check`로 구문 검사 수행(#4 참조) |
| 2 | 타입 체크 | 해당 없음(구성 부재) | N/A | 순수 Node.js CommonJS(`code-scan.js`/`code-map-hook.js`), TypeScript 미사용 — 타입체커 대상 아님 |
| 3 | 포맷터 | 해당 없음(구성 부재) | N/A | `.prettierrc*`/포맷터 설정 없음 |
| 4 | `node --check` 구문 검사 (린트 대체) | `node --check` | PASS | `code-scan.js`, `code-map-hook.js`, `tests/test-*.js` 8종 — 10개 파일 전부 구문 오류 0건. **[재검증(post-fix), 2026-07-28]** 재작업 후 동일 10개 파일(신규 `TS-077-A/B` 케이스가 추가된 `test-validate.js` 포함) `node --check` 전부 재실행 → 10개 파일 전부 구문 오류 0건(회귀 없음) |
| 5 | 신규/수정 파일 `@header` 보유 | `code-scan scan`/`validate` | **PASS** (재검증 후 갱신) | 신규 테스트 파일 8종은 `layer:test`+`task:"077"` JSON 블록 `@header` 보유(`TS-057`), 신규 `code-map-hook.js`도 완전한 `@header`(module/layer/domain/description/exports/depends/note) 보유 확인(`scan` 실측). `run.sh`는 header-rules.md §적용 대상 확장자에서 `.sh` 명시 제외(대상 아님). **이전 검증 시점(Step 19)에는 이번 태스크가 수정한 기존 파일 `code-scan.js` 자신과 참조문서 6종이 @header 미기재 상태(`no_entry` 7건 + `incomplete` 1건)로 FAIL이었으나, 재작업 후 재확인 결과 PASS로 전환**: `node opal/tools/code-scan/code-scan.js validate --changed "<22개 변경파일 csv>" --json` → `exit 0`, `newly_uncovered:0`. 남은 `uncovered` 6건(header-rules.md/pm-review-gate.md/opal-harness.md/code-scan-management.md/tools.md/brain-tool/README.md)은 전부 `sub:pre_existing`(HEAD 기준 기존 미커버 문서 — 회귀 아님, 비차단)로 분류됨. `header-standard.md`·`code-scan.js`는 violations에서 완전히 사라짐(헤더/커버리지 보유로 전환 확인) |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | PASS | 신규 파일(`code-scan.js`, `code-map-hook.js`, `run.sh`, `tests/test-*.js` 8종) 대상 `grep -nEi "api[_-]?key|secret|password|token\s*=|Bearer ...|AKIA...|-----BEGIN"` → 매치 0건. **[재검증(post-fix), 2026-07-28]** 동일 명령 재실행 → 매치 0건(exit 1, grep no-match), 회귀 없음 |
| 2 | .gitignore 확인 | PASS | `git check-ignore -v .opal/code-map/index.json` → `!.opal/code-map/**`(비무시), `git check-ignore -v .opal/code-scan.json` → `.opal/*`(무시 유지) — 파생 캐시와 수작업 자산 구분 의도대로 동작. **[재검증(post-fix), 2026-07-28]** 두 명령 재실행 → 결과 동일(비무시/무시 유지), 회귀 없음 |
| 3 | hook 임의 명령 실행 경로 부재 | PASS | `grep -nE "exec\(|execSync|spawn\(|child_process" opal/tools/code-scan/code-map-hook.js` → 매치 0건. hook은 stdin JSON 파싱 + `decideTarget`/`loadCodeMap` 순수 함수 호출만 수행, 외부 프로세스 실행 경로 없음. **[재검증(post-fix), 2026-07-28]** 재실행 → 매치 0건, 회귀 없음(`code-map-hook.js`는 이번 재작업 대상 파일이 아님) |

## 7. 판정

### [재검증(post-fix), 2026-07-28] 최종 판정 — All Pass

**이전 판정(Step 19)**: Partial Fail — 핵심 기능(도구 로직) 전량 Pass, 태스크 자신의 EXECUTE 산출물이 자신이 신설한 @header 갱신 규칙(CLOSE 게이트)을 위반(아래 "이전 판정 근거(보존)" 참조).

**재작업 3건 반영 후 재검증 결과**: 이전 FAIL의 유일한 원인이던 S-24 ④(자체 저장소 `validate --changed`)가 이제 **exit 0, `newly_uncovered:0`**으로 해소됨을 실제 재실행으로 확인. 이번 재검증에서 다룬 24개 시나리오(S-25 [SUPERVISOR] 제외) 중 FAIL로 남는 항목 없음.

**판정: All Pass** (S-25는 [SUPERVISOR] 수동 항목으로 본 판정에서 제외 — 아래 "S-25 미확인 사실" 참조)

### 재검증 판정 근거

- **핵심 기능 — All Pass(유지)**: 재작업 반영 후 `node --test opal/tools/code-scan/tests/*.js` **97/97 PASS**(exit 0, 이전 81/81에서 재작업 검증용 신규 케이스 `TS-077-A-1~5`/`TS-077-B-1~3` 16건 추가). 8커맨드 골든 회귀 바이트 동일(제약②, 회귀 없음). `discover`/`scaffold`/`target`/`validate`/`feature` 5신규 서브명령 전부 기대 계약대로 동작. install 재배포 상태 재조회 결과 `run.sh --help`/`OPAL_NODE_BIN=/nonexistent`/`tool-scan usage` 계약 전부 유지(H-17 해소 유지).
- **해소 확인 — S-24 ④ (자체 저장소 `validate --changed` — 이전 FAIL → PASS)**: 이 태스크의 실제 변경 파일(22개: `.gitignore`, `claude-hooks.json`, 참조문서 6종, `brain-tool/README.md`, `code-scan.js`, `tool-scan/manifest.json`, `install-mac.sh`, `code-map-hook.js`, `run.sh`, 신규 테스트 8종)를 대상으로 `node opal/tools/code-scan/code-scan.js validate --changed "<22개 경로>" --json`을 재실행한 결과 **`exit 0`, `ok:true`, `newly_uncovered:0`**. 남은 `uncovered` 6건은 전부 `sub:pre_existing`(HEAD 시점에도 미커버였던 기존 문서)으로 비차단 분류되어 `ok:true`에 포함됨 — `pm-review-gate.md` §8 v1.7이 명시한 새 게이트 기준("`counts.newly_uncovered` 0건")을 충족한다. 저장소 전체 변경분(tasks/ 제외 55개 `.js`/`.md`) 대상 광역 재확인에서도 `exit 0`, `newly_uncovered:0`, 위반 33건 전부 `pre_existing`, `incomplete` 0건으로 동일하게 확인.
- **근접성 판정 부작용 확인**: `extractHeaderFromContent`의 `@header`↔`{` 근접성 판정(`findProximateHeaderIndex`) 도입으로 저장소 헤더 보유 수가 101→**97**(오탐 4건 제거)로 변경 — S-19(격리)·S-24 ⑦⑧(범위 대조) 재실행 결과 이 수치 변화만 반영되고 격리·축소 계약 자체는 회귀 없음(재검증 완료).
- **부차 발견(비차단, 권고, 유지)**: S-17 `headerSource` 스위치의 자동 회귀 테스트(TS-044/046)가 실제로는 config 오버레이 없이 auto 모드만 검증하는 취약한(vacuous) 테스트임을 발견 — 수동 재현으로 실제 구현은 정확함을 확인했으나, 자동 커버리지 보강(TS-045 신설 등)을 권고한다(비차단, CLOSE를 막지 않음).
- 보안 3항목 재확인 전부 PASS(회귀 없음). RED 테스트 파일 불변성 확인(PM 승인 예외 1건 제외, 재작업으로 인한 추가 변경 없음). 커밋 없음, 소스/규칙 문서 무수정(검증 전용 준수) — 본 재검증 작업 자체도 산출물은 `TEST-SCENARIO.md`/`TEST.md` 갱신뿐, 소스·규칙 문서 무수정.

### S-25 미확인 사실 (명시)

S-25(hook 실 세션 발동 관측)는 [SUPERVISOR] 마커 시나리오로 opal-test-agent가 자동 실행하지 않는다. 위 "All Pass" 판정은 **S-25를 제외한 24개 시나리오** 기준이며, S-25는 여전히 "캡틴 확인 대기" 상태로 미확인이다. install 재배포는 완료되어 실 세션 관측을 위한 전제 조건은 충족되어 있다.

### 남은 조치 (PM 판단 필요)

1. (비차단 권고, 유지) `test-resolve-header.js`의 S-17 관련 테스트에 실제 `headerSource` config 오버레이 fixture 추가(TS-045 신설 등).
2. S-25는 캡틴의 수동 확인 필요 — 위 "PM 표준 요청 양식"으로 세션 내 `Write`/`Edit` 1회 발생 후 hook 발동 여부 보고 필요.

### 이전 판정 근거(보존 — Step 19 시점, 추적성 유지)

- **핵심 기능 — All Pass**: `node --test opal/tools/code-scan/tests/*.js` **81/81 PASS**(exit 0). 8커맨드 골든 회귀 바이트 동일(제약②). `discover`/`scaffold`/`target`/`validate`/`feature` 5신규 서브명령 전부 기대 계약대로 동작(S-1~S-21, S-23 전량 PASS). install 재배포 성공, `run.sh --help`/`OPAL_NODE_BIN=/nonexistent` 계약 충족, `tool-scan usage code-scan` `ok:true`로 H-17 완전 해소(S-22 PASS).
- **FAIL — S-24 ④ (자체 저장소 `validate --changed` exit 0 미충족)**: 이 태스크의 실제 changed_files(참조문서 6종 + `code-scan.js` 자신)를 `~/.opal/tools/code-scan/run.sh validate --changed "<changed_files>" --json`으로 실행하면 **`exit 2`, 8건 uncovered 위반**이 발생한다. `pm-review-gate.md` §8(이번 태스크가 직접 작성한 CLOSE 게이트 절차) 기준으로는 이 태스크 자체가 지금 CLOSE에 진입할 수 없는 상태다. 원인은 버그가 아니라 **EXECUTE 단계에서 이 태스크가 수정한 문서·코드 파일들에 @header 미기재**(작업 완료 후 일괄 갱신 금지 원칙을 놓친 것으로 추정). 코드를 고치는 대신 실패로 보고한다(Guards: Step 19는 검증 전용).
- **부차 발견(비차단, 권고)**: S-17 `headerSource` 스위치의 자동 회귀 테스트(TS-044/046)가 실제로는 config 오버레이 없이 auto 모드만 검증하는 취약한(vacuous) 테스트임을 발견 — 수동 재현으로 실제 구현은 정확함을 확인했으나, 자동 커버리지 보강(TS-045 신설 등)을 권고한다.
- 보안 3항목 전부 PASS. RED 테스트 파일 불변성 확인(PM 승인 예외 1건 제외). 커밋 없음, 소스/규칙 문서 무수정(검증 전용 준수).
- **이전 남은 조치(블로커, 해소됨)**: `code-scan.js`, `header-rules.md`, `pm-review-gate.md`, `header-standard.md`, `opal-harness.md`, `tools.md`, `brain-tool/README.md`에 @header 작성 후 `validate --changed` 재확인 exit 0 필요 — **재작업 완료로 해소**(위 재검증 판정 근거 참조).

### PM Gate 체크 (7대 강제 룰)

- [x] 시나리오 본문에 대역 객체·패치 기법 부재 (전량 실 파일시스템 픽스처 + CLI 블랙박스)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (10행 × 4컬럼)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (S-1~S-25 전량)
- [x] 가설↔시나리오 매핑(§4) 완전 — 미매핑 시나리오 없음
- [x] L1/L2/L3 계층 명시 (25 시나리오 전량)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-25)
- [x] 리스크 가설 표(§1) H-1~H-18 전량이 시나리오와 1:N 매핑
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] **FE 변경 시 M2 시나리오 포함** — 해당 없음(FE 화면·인증/인가·외부 API 연동 무변경, `test-scenario-guide.md` §Step 3-b M2 면제 조건)
- [x] **목표 커버** — TASK.md F-1~F-13 전량이 §4에 커버되고, 태스크 목표(소스 0수정 자산화)를 검증하는 목표달성 시나리오 S-24가 §3 L3에 존재
