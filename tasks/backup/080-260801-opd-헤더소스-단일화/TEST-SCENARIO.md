# TEST SCENARIO: 헤더 소스 단일화 — headerSource 기준 통일 + 스코프 include/exclude

> 작성일: 2026-08-01 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표 기반
> self-confirming 방지: PLAN 작성자(opal-plan-agent) ≠ 본 문서 작성자(PM)
> RED-first 트랙: **적용** (PLAN §3.7.4) — RED 작성 `opal-test-agent(mode: red)` ≠ 구현 `opal-task-agent`

## 0. 테스트 스택 결정 (`test-tool resolve` 결과 + 코드 실측)

| 항목 | `test-tool resolve` 반환 | 이 태스크 실제값 | 채택 근거 |
|------|------------------------|----------------|----------|
| source | `global` | — | 프로젝트 `test-tools.yaml` 부재 |
| 감지 스택 | `typescript / nextjs / node` | **Node.js 무의존 CLI** | 저장소 루트의 `dashboard/frontend`를 보고 추론한 값이며 이번 변경 대상(`opal/tools/code-scan/`)과 무관 |
| unit 러너 | `vitest` | **`node --test` (node:test + node:assert/strict)** | 코드가 실질적 문서 — 기존 테스트 8파일이 전부 `node:test` (`opal/tools/code-scan/tests/test-regression.js` 등). 신규 의존 도입은 [MUST] TASK.md §제약 "외부 npm 의존 금지" 위반 |
| integration | `pytest + httpx` | **`node --test` + 실 CLI subprocess 실행** | 검증 대상이 CLI 프로세스이므로 실 subprocess 호출이 곧 통합 검증 |
| e2e | `cmux(1순위) / playwright(2순위)` | **해당 없음** | 브라우저·FE 화면·인증·외부 API 연동 변경 0건 → M2 의무 트리거 비해당 (아래 §3.0) |
| supervisor | `captain-manual` | **S-22 1건** | PostToolUse hook의 실세션 동작은 자동화 불가 |

> `resolve`가 반환한 전역 기본값과 실제 러너가 다르다. 문서/코드 불일치 규칙에 따라 **코드 기준**으로 `node --test`를 채택하고, 이 불일치를 여기 명시 기록한다. `no_runner`는 반환되지 않았으므로 에스컬레이션 대상이 아니다.

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-14)를 그대로 승계하고, 각 가설에 시나리오를 연결한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 `main()` 전 명령 게이트 | code-scan을 subprocess로 호출하는 전 소비자(brain-tool `sync-header`·PM Gate·hook)가 동시 정지 | P0 | L2/M1 | S-1, S-14 |
| H-2 | F-001 `loadConfig` 무종료 계약 | `loadConfig`가 종료하면 hook fail-safe(무출력 exit 0)가 붕괴 — hook은 `main()`을 거치지 않고 직접 호출(`code-map-hook.js:120`) | P0 | L1+L2/M1 | S-2, S-22 |
| H-3 | F-002 `getSearchPaths` 반환 타입 변경 | 호출자 `discoverFiles`(`code-scan.js:299`) 1곳 — 조회 8커맨드 전체가 이 경로를 탄다 | P0 | L2/M1 | S-3, S-17 |
| H-4 | F-002 `resolveScope` 우선순위 변경 | 기존 "최장 root → 이름 사전순"(`code-scan.js:564`)에 include 매칭 단계 삽입 → 귀속이 바뀌면 매니페스트 경로가 통째로 이동 | P1 | L1/M1 | S-4, S-5 |
| H-5 | F-002 `isInScope` 5개 지점 배선 누락 | 077 결함 D와 동형 오탐 재발 — `scaffold`가 제외한 파일을 `validate`가 `files_key_removed`로 잡음 | P0 | L2/M1 | S-6, S-7 |
| H-6 | F-003 `decideTarget` reason 도메인 축소 | `header-rules.md:25` "이 4값 외를 반환하지 않는다" 명문 계약 위반 + hook `buildWarning`이 reason 출력 | P1 | L1/M1 | S-8, S-10 |
| H-7 | F-003 `validate` 모드별 커버리지 | `pm-review-gate.md:57` "합산 커버리지" 게이트 기준 무효 → PM Gate 오판정 | P1 | L2/M1 | S-11 |
| H-8 | F-004 `readonly` **무시** 전환 | index.json 18종 중 17종이 `readonly` 키 보유(`true`는 1건 — `fixtures/codemap-repo/.opal/code-map/index.json:23`). **초판의 `manifest` 흡수 로직이 잔존하면** 그 스코프만 전역값을 벗어나 전역 단일 키 결정이 조용히 파괴된다 | P1 | L1/M1 | S-13 |
| H-9 | F-007 픽스처 20종 `code-scan.json` | 전량에 `headerSource` 부재 → 게이트 도입 즉시 기존 100 케이스 전량 exit 1 | P0 | L2/M1 | S-16 |
| H-10 | F-007 골든 재캡처 | `legacy-repo`는 code-map 부재이므로 `inline` 결과가 기존 `auto` 결과와 같아야 한다 — 바이트가 다르면 조회 경로 회귀 | P1 | L2/M1 | S-17 |
| H-11 | F-005 이 저장소 `.opal/code-scan.json` | gitignore 대상이라 설정이 커밋되지 않아 신규 clone·CI에서 게이트 재발 | P1 | L1/M1 | S-15 |
| H-12 | F-003 `manifest` 모드 + index.json 부재 | 조회 결과 전량 공백 = 조용한 실패 | P2 | L1/M1 | S-12 |
| H-13 | F-002 **`target`은 애초에 필터 대상이 아니었다** | `decideTarget`의 필터 유틸 호출 0건 — 계약 없이 배선하면 스코프 밖 파일에 경로 없는 `write_to: manifest`가 나간다 | P0 | L1+L2/M1 | S-9 |
| H-14 | F-005 `.gitignore` 예외 추가 | 077 TS-055(`test-regression.js:126-127`)가 "계속 무시되어야 함"을 단언 → 반전 누락 시 GREEN 실패 | P1 | L2/M1 | S-15 |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 이 태스크는 DB를 사용하지 않는다. 사전 조건 데이터 = **파일시스템 픽스처**이며, 전량이 저장소에 커밋된 실 자산이다(mock 0건).

| 픽스처(테이블 대응) | 식별자 | 상태 | 출처 |
|-------------------|--------|------|------|
| `tests/fixtures/legacy-repo/` | `.opal/code-scan.json` | code-map 부재 · 인라인 @header 보유 · `headerSource` **추가 필요**(→ `inline`) | fixture (기존, Step 1에서 키 추가) |
| `tests/fixtures/codemap-repo/` | `.opal/code-scan.json` + `.opal/code-map/index.json` | 5-tier 상속 트리 · 혼재 파일 `AdminHome.tsx` 보유 · `headerSource` **추가 필요**(→ `manifest`) | fixture (기존, 트리 자체는 무변경 — PLAN §3.7.2) |
| `tests/fixtures/header-proximity/` | `.opal/code-scan.json` | 인라인 근접성 판정용 · `headerSource` 추가 필요(→ `inline`) | fixture (기존) |
| `tests/fixtures/tiebreak/order-a/`, `order-b/` | `.opal/code-scan.json` ×2 | 스코프 사전순 tiebreak · include 미사용 · `headerSource` 추가 필요 | fixture (기존) |
| `tests/fixtures/schema/` 4종 | `manifest-parse-failed` · `missing-root` · `missing-scopes` · `version-mismatch` | index 스키마 위반 4종 · `headerSource` 추가 필요 | fixture (기존) |
| `tests/fixtures/violations/` 11종 | `clean` · `conflict-inline-shadowed` · `conflict-mirror-collision` · `draft` · `exports-missing` · `orphan` · `uncovered` · `worker-scope-dir` · `worker-scope-exclude-symmetry` · `worker-scope-files` · `worker-scope-layer` | 위반 검출 5종 + 워커 권한 경계 · `headerSource` 추가 필요 | fixture (기존) |
| `tests/fixtures/mixed-scope/` | `.opal/code-scan.json`(`headerSource: "inline"`) + `.opal/code-map/index.json` | **신규** — `svc/shared/` 한 디렉토리에 **생존 스코프 2개**(`order-svc`: `include:["Order*.java"]` → `OrderService.java`·`OrderRepo.java` / `ship-svc`: `include:["Ship*.java"]` → `ShipService.java`·`ShipRepo.java`)와 어느 include에도 미매칭인 `VendorLegacy.java` 1개. 두 스코프는 `path` 동일 + `include`만 다름 | fixture (Step 1 신설) |
| `tests/fixtures/mixed-scope-ambiguous/` | `.opal/code-scan.json` + `.opal/code-map/index.json` | **신규** — 양쪽 `include`가 **동시 매칭**되는 설정. `scope_ambiguous`는 exit 1이므로 정상 트리에 심으면 그 트리를 쓰는 TS 전부가 같은 에러에 막혀 별도 트리로 분리 | fixture (Step 1 신설) |
| `tests/fixtures/golden/` | `scan.json` · `domain.txt` · `layer.txt` · `search.json` · `exports.json` · `summary.txt` · `depends.txt` · `missing.txt` | 077 캡처본 8종 — `headerSource: inline` 명시 상태로 **재캡처 대상** | fixture (기존 → Step 13 교체) |
| 이 저장소 루트 | `.opal/code-scan.json` | `headerSource` 키 없음 · gitignore 대상 | 실 저장소 (Step 9에서 키 추가 + `.gitignore` 예외) |
| 임시 트리 | `mktemp -d` 하위 최소 프로젝트 | `.opal/code-scan.json` 미생성(미설정 상태 재현용) | 테스트 런타임 생성 |

> `codemap-repo`의 임시 복제 + `headerSource` 실기재는 기존 헬퍼 `makeHeaderSourceFixture(value)`(`tests/test-resolve-header.js:74-83`)를 재사용한다 — 077 TS-044/045/046이 이미 사용 중이므로 신규 픽스처 트리 생성 불필요.

### 2.2 시나리오별 데이터 흐름 (Given / When / Then)

| 시나리오 | Given (read) | When (실행) | Then (re-read) |
|---------|------------|-----------|---------------|
| S-1 | `.opal/code-scan.json`에 `headerSource` 키가 없는 임시 트리 | 13개 서브명령을 각각 CLI 실행 | 13건 전부 exit 1 · stdout JSON `error === "header_source_unset"` · stderr 3줄(사유·해결·근거 문서) |
| S-2 | 동일 미설정 트리 + `headerSource: "auto"` 트리 + `inline` 트리 | `code-map-hook.js`에 PostToolUse 이벤트 JSON을 stdin 주입 | 3건 전부 stdout 0바이트 · exit 0 |
| S-3 | `legacy-repo` (`headerSource: "inline"` 명시) | 조회 8커맨드 실행 | 출력이 재캡처 골든과 **바이트 동일** · `scan --json` 결과에 `_source` 키 0건 |
| S-4 | 문자열 `scopes` 픽스처 20종 + 객체 형식 `mixed-scope` | 각 픽스처에서 `scan --json` 실행 | 문자열 20종 무수정 동작(exit 0) · 객체 형식 스키마 검증 통과(exit 0) |
| S-5 | `mixed-scope`(생존 2스코프) + **`mixed-scope-ambiguous`**(양쪽 매칭) + `tiebreak/order-a`,`order-b` | 정상 트리에서 `target` 귀속 조회 · ambiguous 트리에서 별도 실행 | 파일이 자기 `include` 스코프로 귀속 · **ambiguous 트리는 `scope_ambiguous` exit 1** · tiebreak 결과 불변 |
| S-6 | `mixed-scope` (include로 `VendorLegacy.java` 제외) | 열거·scaffold 열거·`validate` 구조 패스·`--changed`·`target` 5지점 각각 실행 | 5지점이 **동일 파일 집합**(생존 4파일)을 판정 · `grep`으로 확인한 필터 판정 로직이 `isInScope` 외 0곳 |
| S-7 | 동일 `mixed-scope` + 매니페스트 `files` 내용 (PLAN §3.7.2 명세) | `validate --json` 실행 | include 제외 `VendorLegacy.java`는 `files_key_removed` 미집계 · 필터에 안 걸리는 미등재 파일은 여전히 검출 |
| S-8 | `codemap-repo` 오버레이 2종(`inline` / `manifest`) | 신규 파일·인라인 보유 파일에 `target` 실행 | `manifest` → `write_to:manifest`/`reason:header_source_manifest` + `scope`·`manifest`·`key` 채워짐 / `inline` → 항상 `write_to:inline`/`reason:header_source_inline` |
| S-9 | `mixed-scope`의 include 탈락 파일 + `legacy-repo`의 스코프 밖 파일 | `target` 실행 · 동일 파일로 hook 이벤트 주입 | 탈락 파일 `{write_to:'none', reason:'out_of_scope'}` exit 0 · `scope`/`manifest`/`key` **부재** · hook stdout 0바이트 · 미사용 프로젝트 결과는 필터 도입 전과 동일 |
| S-10 | `headerSource: "inline"` 설정 픽스처 | `scaffold` 실행 | `.opal/code-map/` 하위 파일 생성 0건 · `skipped[0].reason === 'header_source_inline'` · exit 0 |
| S-11 | 동일 픽스처를 `inline` / `manifest` 두 모드로 오버레이 | 각 모드로 `validate --json` 실행 | 커버리지 분모·분자가 각 모드 소스만 반영 · 반대 소스 부재 비집계 · `uncovered:pre_existing` 비차단·exit 2 정책 불변 · 결과에 `headerSource` 필드 존재 |
| S-12 | `manifest` 모드 설정 + `.opal/code-map/index.json` 부재 트리 | `scan --json` 실행 | stderr 경고 1줄 · exit 0(비차단) · stdout JSON 무오염 |
| S-13 | `readonly: true` 스코프 보유 index 픽스처 | 전역 `inline` / 전역 `manifest` 두 조건으로 `target` 실행 · `discover` 실행 | **양방향 모두 전역값을 따른다**(`inline`→`inline`, `manifest`→`manifest`) · `readonly`가 결과를 바꾸지 않는다 · stderr deprecated 안내 1줄 · `discover` 산출물에 `readonly` 키 0건 · 소스에 `readonly` 판정 근거 0건 |
| S-14 | 이 저장소 루트(`headerSource: "inline"` 추가 후) + 미설정 임시 트리 | 저장소에서 8커맨드 실행 · 미설정 트리에서 `brain-tool sync-header` 실행 | 8커맨드 exit 0 · sync-header 실패 detail에 `header_source_unset` 문자열 포함 · `brain_tool.py` 변경 0줄 |
| S-15 | `.gitignore`에 `!.opal/code-scan.json` 예외 추가 후 | `git check-ignore` 2건 실행 | `.opal/code-scan.json` exit 1(비무시) · `.opal/code-map/index.json` exit 1 유지 |
| S-16 | 픽스처 20종 `headerSource` 추가 완료 상태 | `grep -L headerSource` 집계 · `node --test` 전량 실행 | 누락 0건 · 전량 pass · exit 0 |
| S-17 | `legacy-repo` `headerSource: "inline"` 명시 | 골든 8커맨드 재캡처 + `git diff --stat` | 재캡처 골든과 바이트 동일 · `README.md`에 캡처 조건과 077 대비 diff 근거 기록 |
| S-18 | 규칙 문서 5종 + `docs/` 3종 개정 후 + `code-scan.js` 소스 | 산출물 grep 검사 | 8문서 변경이력 행 존재 · `readonly` 판정 근거 서술 0건 · 개인 식별자 신규 0건 · **`reason` 3값 + `write_to` 3값 표기** · **`auto`를 유효값으로 서술하는 문장 0건** · **소스에 `auto` 리터럴 0건**(마이그레이션 힌트 문자열 제외) · `code-scan-management.md` 예시에 `headerSource` 포함 |
| S-19 | `mixed-scope` — **생존 4파일(2스코프)**, `VendorLegacy.java` 1건 탈락 | (Ⅰ) 픽스처 기준값 **`inline`**으로 5경로 연속 실행 → (Ⅱ) **전역값만 `manifest`로 뒤집어** 5경로 재실행 | 전 단계가 동일 include 집합 위에서 동작 · **두 스코프가 동일 모드 보고** · **4경로 모드 일치** · **전역 한 줄 변경으로 5경로 동시 반전** · 두 소스 혼재 0건 · `validate` `ok: true` |
| S-20 | `auto` 설정 트리 + 깨진 JSON 트리 + **`bogus` 등 임의 무효값 트리** + **`--header-source <무효값>` CLI 호출** | 각각 CLI 실행 | `auto` → `header_source_invalid` + `detail:"auto"` + 마이그레이션 힌트 exit 1 · 깨진 JSON → `code_scan_config_invalid`(미설정과 구분) exit 1 · **임의 무효값 → `header_source_invalid`(마이그레이션 힌트 없음, `where:"config"`)** · **CLI 무효값 → `header_source_invalid` + `where:"cli"`** |
| S-21 | 미설정 트리 · 전역 `manifest` 트리 · 스코프에 `headerSource`를 넣은 트리 | 3조합으로 `target`/`scan` 실행 | 미설정 + CLI → exit 0 · 전역 + CLI → **CLI 승리**(실행당 1값) · 스코프 키 → **무시**되고 전역값 적용 + 안내 |
| S-22 | 실제 편집 세션 + 미설정 프로젝트 | 캡틴이 해당 프로젝트 파일을 Edit/Write | 세션에 에러·경고 노출 0건 · 편집 정상 완료 |

---

## 3. 검증 시나리오

### 3.0 실행 방식(M) 판정 근거

| 판정 | 결과 | 근거 |
|------|------|------|
| M2 의무 트리거 (FE 화면/컴포넌트·인증/인가·외부 API 연동) | **비해당 → M2 면제** | 변경 대상은 Node.js CLI 도구 2개 + 규칙 문서 8종 + 테스트 자산. FE·인증·외부 API 연동 변경 0건 (`test-scenario-guide.md` §Step 3-b) |
| BE API M2 트리거 (API 엔드포인트) | **비해당** | HTTP 엔드포인트 변경 0건 — CLI 프로세스 계약만 변경 |
| M3 (사용자 협업) | **1건 필요** | PostToolUse hook의 실세션 동작은 자동 재현이 불가능 (S-22) |
| 나머지 | **M1** | `node --test` + 실 CLI subprocess 실행으로 전부 자가 점검 가능 |

---

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-2: `loadConfig` 무종료 계약 — hook fail-safe 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `code-scan.js` `loadConfig` 반환 계약 · `code-map-hook.js` 조기 이탈 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — `node --test` |
| 조건 | 미설정 트리 · `headerSource:"auto"` 트리 · `inline` 트리 3종에 PostToolUse 이벤트 JSON을 stdin 주입. `loadConfig` 소스에 `process.exit`·`throw` 0건 |
| 기대 결과 | 3케이스 전부 stdout 0바이트 · exit 0. `code-map-hook.js:151-158` fail-safe 경로 불변. `manifest` 모드 + 미갱신 매니페스트에서는 경고가 **정상 출력**되어 077 TS-038 계약 보존 |
| 도구 | `node --test` (node:test) — `tests/test-hook.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-hook.js`<br>직접 재현: `printf '{"tool_name":"Edit","tool_input":{"file_path":"<T>/src/a.js"}}' \| node code-map-hook.js` (미설정 / `auto` / `bogus` / `inline` / 깨진 JSON 5트리) |
| 결과 | **PASS** |
| 상세 | 5트리 전부 **stdout 0바이트 · stderr 0바이트 · exit 0** (미설정·`auto`·`bogus`·`inline`·설정 파싱 실패). 판별력: 양성 대조군 TS-042(`manifest` 모드 + 미갱신 매니페스트)가 **경고를 정상 출력**함을 먼저 확인해 "트리가 원래 조용한 것"과 구분됨 — 077 TS-038 계약 보존. 산출물 검사: `loadConfig` 본문에 `process.exit`·`throw` 0건. 관련 케이스 TS-040/041/042/043 + fail-safe 산출물 검사 = 7건 전량 pass |

#### S-4: `scopes` 문자열 하위호환 + 객체 형식 정규화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `loadConfig` · `loadCodeMap` 스키마 검증 · `normalizeConfigScope`/`normalizeIndexScope` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 기존 문자열 `scopes` 픽스처 20종 무수정 · 신규 객체 형식 `{path, include, exclude}` |
| 기대 결과 | 문자열 20종이 무수정으로 동작(exit 0) · 객체 형식이 스키마 검증을 통과 · 두 형식이 내부적으로 동일 형태로 정규화된다 |
| 도구 | `node --test` — `tests/test-scope-filter.js`(신규), `tests/test-resolve-header.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-scope-filter.js opal/tools/code-scan/tests/test-resolve-header.js`<br>직접 재현: 픽스처 전량 순회 — `for f in $(find tests/fixtures -name code-scan.json); do (cd $(dirname $(dirname $f)) && node code-scan.js scan --json); done` |
| 결과 | **PASS** |
| 상세 | 픽스처 **22종** = 문자열형 20 + 객체형 2. 문자열 20종 중 16종 `exit 0`, `schema/` 4종(`version-mismatch`·`missing-scopes`·`missing-root`·`manifest-parse-failed`)은 index.json을 **고의로 깨뜨린 자산**이라 `exit 1`이 계약(077 TS-002/TS-003) — **`code_scan_config_invalid`로 거부된 문자열 스코프는 0건**이므로 하위호환 성립. 객체형 `mixed-scope`·`mixed-scope-ambiguous` 스키마 검증 통과 `exit 0`. 두 형식 모두 `{root, include, exclude}` 단일 내부 형태로 정규화(`normalizeConfigScope`/`normalizeIndexScope`). TS-075 타입 위반 **12케이스**(스칼라·비문자열 원소·객체 × `include`/`exclude` × 두 레지스트리) 전부 `invalid_index`/`code_scan_config_invalid`로 거부 |

#### S-5: 스코프 중복 우선순위 — include 승리 / 양쪽 매칭 거부 / tiebreak 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `resolveScope` → `resolveScopeIn` 위임 · 우선순위 판정 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | (a) `mixed-scope` — `path` 동일 + `include`만 다른 생존 스코프 2개 (b) **`mixed-scope-ambiguous`** — 양쪽 `include`가 동시 매칭되는 별도 트리 (c) include 미사용 `tiebreak/order-a`·`order-b` |
| 기대 결과 | (a) `Order*.java`는 `order-svc`로, `Ship*.java`는 `ship-svc`로 귀속 (b) ambiguous 트리는 `scope_ambiguous` exit 1 — 정상 트리와 **분리 실행**한다(정상 트리에 심으면 그 트리를 쓰는 TS 전부가 같은 에러에 막힌다) (c) include 미사용 프로젝트의 사전순 판정 결과 **불변** |
| 도구 | `node --test` — `tests/test-scope-filter.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-scope-filter.js`<br>직접 재현: `(cd fixtures/mixed-scope && node code-scan.js target svc/shared/{Order,Ship}*.java --json)` · `(cd fixtures/mixed-scope-ambiguous && node code-scan.js target svc/shared/OrderService.java --header-source manifest --json)` · `(cd fixtures/tiebreak/order-{a,b} && node code-scan.js scan --json)` |
| 결과 | **PASS** |
| 상세 | (a) `mixed-scope`(`path` 동일 + `include`만 다름) `manifest` 모드 `target` — `OrderService.java`·`OrderRepo.java` → `scope:"order-svc"`, `ShipService.java`·`ShipRepo.java` → `scope:"ship-svc"`. 사전순 일괄 귀속(`order-svc`) 아님. (b) `mixed-scope-ambiguous`(양쪽 `include:["*.java"]`) → `{"ok":false,"error":"scope_ambiguous","detail":"svc/shared/OrderService.java가 동률 root 스코프 order-svc, ship-svc의 include에 동시 매칭됩니다 — 한쪽 include를 좁혀 소속을 1개로 확정하세요"}` **exit 1**, 정상 트리와 분리 실행. (c) `tiebreak/order-a`·`order-b`의 `scan --json` 결과 완전 동일, layer `layer-foo` 불변 — 사전순 판정 회귀 0<br>※ 부수 관측(§7 이슈①): ambiguous 트리에서 `scaffold --header-source manifest`는 exit 1이 아니라 **exit 0**으로 통과하며 5파일을 양쪽 매니페스트에 중복 등재한다. 시나리오 (b)의 단언 대상은 `target`이라 PASS 판정에 영향 없으나 계약 비대칭이므로 그대로 보고한다 |

#### S-8: `target` 모드 직결 + `reason` 도메인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `decideTarget` 모드 직결 · `reason`/`write_to` 도메인 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `codemap-repo` 오버레이 2종(`inline`/`manifest`) · 신규 파일과 인라인 보유 파일 각각 |
| 기대 결과 | `manifest` 모드는 두 파일 모두 `write_to:manifest` + `reason:header_source_manifest` + `scope`/`manifest`/`key` 정확 · `inline` 모드는 항상 `write_to:inline` + `reason:header_source_inline`. 파일 상태(신규/기존/인라인 유무)가 판정에 영향 0 |
| 도구 | `node --test` — `tests/test-target.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-target.js`<br>직접 재현: `codemap-repo` 복사본 2종에 `headerSource`만 `inline`/`manifest`로 오버레이 → `node code-scan.js target <file> --json` × 5파일(인라인 보유 / 인라인 부재 / 혼재 / readonly 스코프 / 존재하지 않는 신규 경로) |
| 결과 | **PASS** |
| 상세 | `manifest` 모드: 5파일 전부 `write_to:"manifest"` + `reason:"header_source_manifest"`. 부가 필드 정확 — `web/admin/pages/AdminHome.tsx` → `scope:"web"`, `manifest:".opal/code-map/web/admin/pages.json"`, `key:"AdminHome.tsx"` / `legacy/lib/legacy_util.py` → `scope:"legacy"`, `.opal/code-map/legacy/lib.json`, `legacy_util.py`. `inline` 모드: 같은 5파일 전부 `write_to:"inline"` + `reason:"header_source_inline"` + `scope`/`manifest`/`key` **부재**(부정 단언). **파일 상태(신규/기존/인라인 유무)가 판정에 영향 0** — 존재하지 않는 경로도 모드값 그대로 반환 |

#### S-9: `target` 스코프 필터 탈락 반환 계약 (신규 배선)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | `decideTarget` 선두 `isFilteredOutOfScope` 배선 · out-of-scope 반환 계약 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | (a) `mixed-scope`에서 include에 탈락한 형제 파일 (b) 동일 파일로 hook 이벤트 주입 (c) include/exclude 미사용 `legacy-repo`의 스코프 밖 파일 |
| 기대 결과 | (a) `{write_to:'none', reason:'out_of_scope'}` + exit 0 + `scope`/`manifest`/`key` 필드 **부재** (b) hook stdout 0바이트·exit 0 (`write_to !== 'manifest'` 이탈 경로) (c) 필터 도입 전과 결과 동일 — `out_of_scope` 오발동 0건 |
| 도구 | `node --test` — `tests/test-target.js`, `tests/test-hook.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-target.js opal/tools/code-scan/tests/test-hook.js`<br>직접 재현: `(cd fixtures/mixed-scope && node code-scan.js target svc/shared/VendorLegacy.java --json)` · 동일 파일로 hook stdin 주입 · `(cd fixtures/legacy-repo && node code-scan.js target <스코프 밖 파일> --json)` |
| 결과 | **PASS** |
| 상세 | (a) `target svc/shared/VendorLegacy.java` → `{"write_to":"none","reason":"out_of_scope"}` **exit 0**, `scope`/`manifest`/`key` 필드 **부재**. 전역값을 `manifest`로 뒤집어도 결과 불변 — **`out_of_scope`가 모드 판정보다 먼저** 평가됨을 관측으로 고정. (b) 같은 파일로 PostToolUse 이벤트 주입 → **stdout 0바이트 · exit 0**(`write_to !== 'manifest'` 이탈), 양성 대조군(같은 트리·같은 모드의 in-scope 미등재 파일)은 경고가 실제로 출력됨. (c) `legacy-repo`·`codemap-repo` 계열(include/exclude 미사용)에서 `out_of_scope` 오발동 **0건** · 같은 트리 include 통과 4파일도 오발동 0건 |

#### S-10: `inline` 모드 `scaffold` no-op

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `cmdScaffold` 모드 존중 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `headerSource: "inline"` 설정 프로젝트에서 `scaffold` 실행 |
| 기대 결과 | `.opal/code-map/` 하위 파일 생성 **0건** · `skipped[0].reason === 'header_source_inline'` · exit 0 (사유가 보고되고 조용히 넘어가지 않는다) |
| 도구 | `node --test` — `tests/test-scaffold.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-scaffold.js`<br>직접 재현: `mixed-scope`(`headerSource:"inline"`) 복사본에서 `find .opal/code-map -type f \| xargs shasum` → `node code-scan.js scaffold --json` → 해시 재측정 |
| 결과 | **PASS** |
| 상세 | 출력 `{"ok":true,"created":0,"updated":0,"unchanged":0,"added":[],"pruned":[],"stale":[],"skipped":[{"reason":"header_source_inline","detail":"전역 헤더 소스가 inline이므로 매니페스트를 생성하지 않습니다"}]}` **exit 0**. `.opal/code-map/` 하위 3파일의 실행 전후 shasum **동일**, 신규 생성 **0건**. `index.json` 부재 트리에서도 `index_missing`으로 실패하지 않음. **사유가 `skipped[0].reason`으로 보고되어 조용히 넘어가지 않는다.** 대조군: 같은 트리를 `manifest`로 뒤집으면 `updated:2`로 실제 갱신 |

#### S-12: `manifest` 모드 + index.json 부재 — fail-soft

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `resolveHeader` `manifest` 분기의 index 부재 처리 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `headerSource: "manifest"` 설정 + `.opal/code-map/index.json` 부재 트리에서 `scan --json` |
| 기대 결과 | stderr 경고 1줄 · exit 0(비차단) · stdout JSON 무오염(파이프 소비자 보호). 조용한 전량 공백이 아니라 **사유가 보이는** 빈 결과 |
| 도구 | `node --test` — `tests/test-resolve-header.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-resolve-header.js`<br>직접 재현: `headerSource:"manifest"` + `.opal/code-map/index.json` 부재 임시 트리에서 `node code-scan.js scan --json` (stdout/stderr 분리 캡처) |
| 결과 | **PASS** |
| 상세 | **exit 0**(비차단) · stderr **정확히 1줄** — `code-scan: manifest 모드이지만 .opal/code-map/index.json이 없습니다 — 조회 결과가 비어 있습니다 (비차단)` · stdout `{}` (순수 JSON, `JSON.parse` 성공 — 파이프 소비자 보호). 대조군: 같은 트리를 `inline`으로 두면 stderr **0줄** + 인라인 헤더 1건 정상 반환 → 경고가 모드 조건부임이 구분됨 |

#### S-13: `readonly` 무시 + 전역값 적용 (양방향) + 판정 근거 잔존 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `normalizeIndexScope`의 `readonly` **무시 + 안내** · `decideTarget` 분기 제거 · `inferScopes`/`cmdDiscover` 산출물 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | (a) `readonly: true` 스코프 + 전역 `headerSource: "inline"` (b) **같은 스코프 + 전역 `headerSource: "manifest"`** (c) `discover` 신규 실행 |
| 기대 결과 | (a) `write_to: inline` / `reason: header_source_inline` — **`manifest`가 아니다**(초판 흡수 계약에서 반전) + stderr deprecated 안내 1줄(실행당 1회, 전역 설정 방법 포함) (b) `write_to: manifest` — (a)와 짝을 이뤄 "**결과가 `readonly`가 아니라 전역값을 따른다**"를 두 방향으로 고정한다(한 방향만 보면 우연 일치와 구분되지 않는다) (c) 산출물 `scopes[]`에 `readonly` 키 0건. 소스에 `readonly`를 판정 근거로 쓰는 코드 0건(`note` 문자열 포함) |
| 도구 | `node --test` — `tests/test-target.js`, `tests/test-discover.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-target.js opal/tools/code-scan/tests/test-discover.js`<br>직접 재현: `codemap-repo` 복사본 2종(전역 `inline` / 전역 `manifest`)에서 `node code-scan.js target legacy/lib/legacy_util.py --json` (readonly 스코프 소속) · `node code-scan.js discover --dry-run --json` |
| 결과 | **PASS** |
| 상세 | 대상 스코프: `codemap-repo/.opal/code-map/index.json:23` `legacy` 스코프 `"readonly": true`.<br>(a) 전역 `inline` → `{"write_to":"inline","reason":"header_source_inline"}` — **`manifest`가 아니다**(초판 흡수 계약 반전 확인). (b) 전역 `manifest` → `{"write_to":"manifest","reason":"header_source_manifest","scope":"legacy","manifest":".opal/code-map/legacy/lib.json","key":"legacy_util.py"}`. **양방향 모두 전역값을 따르므로 우연 일치가 배제된다.** 두 실행 모두 stderr deprecated 안내 **정확히 1줄**(`.opal/code-map/index.json의 scopes[].readonly는 제거되었습니다 (Task 080) — 이 키는 무시됩니다. 기록 소스는 .opal/code-scan.json의 전역 headerSource (inline 또는 manifest)로 설정하세요.`), stdout JSON 무오염.<br>(c) `discover --dry-run --json` 산출물 `scopes[]`(svc·web·legacy 3종) `readonly` 키 **0건** · `headerSource` 키 **0건**. 소스 검사: `readonly` 잔존 3건 전부 `normalizeIndexScope`(`code-scan.js:454-456`)의 폐기 안내 내부이며 **판정 근거 0건**, `note` 문자열도 `OWNER REVIEW REQUIRED — headerSource/anchors/stripPrefix/include …`로 교체돼 `readonly` 언급 0건 |

#### S-15: `.gitignore` 예외 — 설정 파일 추적 전환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11, H-14 |
| 대상 | `.gitignore` `!.opal/code-scan.json` 예외 1줄 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — `git check-ignore` 실측 |
| 조건 | 예외 추가 후 이 저장소에서 `git check-ignore` 실행 |
| 기대 결과 | `.opal/code-scan.json` **exit 1**(비무시 — 077 TS-055 반전) · `.opal/code-map/index.json` exit 1 유지(기존 단언 불변). 반전 누락 시 GREEN 실패로 검출 |
| 도구 | `node --test` — `tests/test-regression.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-regression.js` (TS-046·TS-047)<br>직접 재현: `git check-ignore .opal/code-scan.json; echo $?` · `git check-ignore .opal/code-map/index.json; echo $?` |
| 결과 | **PASS** |
| 상세 | `.gitignore:7`에 `!.opal/code-scan.json` 예외 1줄 존재(`.opal/*` 무시 뒤 브레이스 예외 4줄 중 하나). `git check-ignore .opal/code-scan.json` → **exit 1**(비무시) — 077 TS-055 반전 성립. `git check-ignore .opal/code-map/index.json` → **exit 1** 유지. 주의: `-v` 플래그를 붙이면 git이 **부정 패턴 매칭도 보고**하느라 exit 0을 반환하므로, 판정 기준은 플래그 없는 호출이다(테스트도 플래그 없이 호출). 현 시점 파일은 비무시 상태이지만 아직 `git add` 전(`git ls-files --error-unmatch` 실패 = untracked) — 실제 추적 전환은 커밋 시점 PM 책임이며 이 시나리오의 단언 대상은 아니다 |

#### S-20: 채택/잔존 — 구형 값 거부 (`auto` 소멸 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (파생 — 채택/잔존 축) |
| 대상 | `headerSource` 값 도메인 2택 · 에러 코드 분기 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | (a) `"headerSource": "auto"` 설정 트리 (b) 깨진 JSON `.opal/code-scan.json` 트리 (c) `"headerSource": "bogus"` 등 **임의 무효값** 트리 — 077 TS-046 반전 대상 (d) 정상 설정 프로젝트에 `--header-source <무효값>` CLI 호출 |
| 기대 결과 | (a) `header_source_invalid` + `detail: "auto"` + **마이그레이션 힌트** + exit 1 — 구형 값이 조용히 폴백되지 않는다 (b) `code_scan_config_invalid`로 **미설정과 구분**되어 반환 (c) `header_source_invalid` + `where: "config"` + **마이그레이션 힌트 없음** — `auto`는 특례 경로이고 일반 무효값은 별도 경로임이 구분된다 (d) `header_source_invalid` + `where: "cli"` — 무효값의 **출처가 에러에 실린다** |
| 도구 | `node --test` — `tests/test-header-source.js`(신규) |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-header-source.js` (TS-003·TS-008·TS-009·TS-065)<br>직접 재현: 임시 트리 4종에서 `node code-scan.js scan` / `node code-scan.js scan --header-source zzz` |
| 결과 | **PASS** |
| 상세 | (a) `"headerSource":"auto"` → **exit 1** `{"ok":false,"error":"header_source_invalid","detail":"auto","where":"config","fix":"…inline 또는 manifest 중 하나여야 합니다","doc":"~/.opal/references/header-standard.md §7","migration":"구형 값 \"auto\"는 제거되었습니다 — 프로젝트 전체를 inline 또는 manifest 중 하나로 통일해 다시 지정하세요 (자동 변환하지 않습니다)"}` — **조용한 폴백 0**. (b) 깨진 JSON → `{"error":"code_scan_config_invalid","detail":".opal/code-scan.json을 JSON으로 파싱할 수 없습니다"}` exit 1 — **미설정(`header_source_unset`)과 코드가 구분**된다. (c) `"headerSource":"bogus"` → `header_source_invalid` + `where:"config"` + **`migration` 키 부재** — 특례(`auto`)와 일반 무효값 경로가 구분된다. (d) `--header-source zzz` → `header_source_invalid` + `detail:"zzz"` + **`where:"cli"`** + `fix:"--header-source 값은 …"` — 출처가 에러에 실린다. 4케이스 전부 stdout 순수 JSON, stderr에 사유·해결·근거 병기 |

#### S-21: 경계/부정 — 우선순위 2층 (CLI > 전역) + 스코프 오버라이드 부재 단언

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 (파생 — 경계 축) |
| 대상 | `resolveHeaderSource` 단일 판정 지점 · **모드가 실행당 1값으로 확정됨** |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | (a) 미설정 프로젝트 + `--header-source inline` (b) 전역 `manifest` + `--header-source inline` (c) 전역 `inline` + **`index.json`** `scopes.{name}`에 `headerSource: "manifest"`를 넣은 트리 (d) 전역 `inline` + **`code-scan.json`** 스코프 객체에 `headerSource: "manifest"`를 넣은 트리 |
| 기대 결과 | (a) `scan` exit 0 (b) **CLI 승리** — 실행 전체가 `inline`이며 서로 다른 파일·스코프가 모두 동일 모드를 보고한다(실행당 1값 확정) (c)(d) **양쪽 파일 모두 스코프 키는 무시**되고 전역 `inline`이 적용된다(`write_to: inline`) + stderr 안내 1줄 · stdout JSON 무오염 — 특히 (d)는 **사용자가 실제로 편집하는 파일**이므로 조용히 버려지면 오버라이드가 되살아난 것을 아무도 모른다. "스코프 오버라이드가 없다"는 것 자체가 지켜야 할 계약이므로 두 파일 대칭으로 부정 단언을 고정한다 |
| 도구 | `node --test` — `tests/test-header-source.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-header-source.js` (TS-004·TS-005·TS-006·TS-069)<br>직접 재현: (a) 미설정 트리 `node code-scan.js scan --header-source inline --json` (b) `mixed-scope`(전역 manifest) 4파일 `target … --header-source inline --json` (c)(d) `mixed-scope` 복사본 2종에 `index.json` / `code-scan.json` 스코프 객체로 `headerSource:"manifest"` 주입 후 `target … --json` |
| 결과 | **PASS** |
| 상세 | (a) 미설정 + `--header-source inline` → `scan` **exit 0** + 정상 결과 — CLI 층만으로 게이트 해제. (b) 전역 `manifest` + `--header-source inline` → `order-svc`/`ship-svc` 소속 4파일이 **전부 `{"write_to":"inline","reason":"header_source_inline"}`** — **CLI 승리 + 실행당 1값 확정**. (c) `index.json` `scopes["order-svc"].headerSource="manifest"` 주입 → 결과 `inline` 유지 + stderr 1줄 `code-scan: [deprecated] .opal/code-map/index.json의 스코프 단위 headerSource는 지원하지 않습니다 — 이 키는 무시됩니다. headerSource는 .opal/code-scan.json의 **최상위** 키 1개로만 설정합니다 (전역 단일 키, Task 080).` (d) `code-scan.json` `scopes["order-svc"].headerSource="manifest"` 주입 → 결과 `inline` 유지 + stderr 1줄 `code-scan: [deprecated] scopes."order-svc".headerSource는 지원하지 않습니다 — …`. **(c)(d) 대칭으로 "스코프 오버라이드 부재"가 부정 단언으로 고정**되고, 둘 다 조용히 버려지지 않고 안내가 나가며 stdout JSON은 무오염 |

---

### L2. 프로세스 통합 (자동, 실 CLI subprocess → 파일시스템 read→write→re-read)

#### S-1: 전 명령 차단 게이트 — 13커맨드 일관 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `main()` 디스패치 진입부 게이트 · 에러 메시지 품질 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — 실 CLI subprocess 13회 호출 |
| 조건 | `.opal/code-scan.json`에 `headerSource` 키가 없는 임시 트리에서 조회 8커맨드 + 작성층 5커맨드 전량 실행 |
| 기대 결과 | 13건 전부 **동일 에러·동일 exit code**(exit 1) · stdout JSON `{"ok":false,"error":"header_source_unset",...}` · stderr에 해결 방법 1줄 + 근거 문서 경로 포함. `--help`/`--version`은 미설정 상태에서도 exit 0(게이트 이전 처리) |
| 도구 | `node --test` — `tests/test-header-source.js`(신규) |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-header-source.js` (TS-001·TS-002·TS-007)<br>직접 재현: `headerSource` 키 없는 임시 트리에서 13커맨드 순차 실 subprocess 호출 — `scan` / `domain` / `layer` / `search auth` / `exports token` / `summary` / `depends mod` / `missing` / `discover --dry-run` / `scaffold --dry-run` / `target src/a.js` / `validate` / `feature f1` |
| 결과 | **PASS** |
| 상세 | **13/13 전부 exit 1 · 동일 에러**. stdout(13건 동일): `{"ok":false,"error":"header_source_unset","detail":".opal/code-scan.json에 headerSource가 없습니다","where":"config","fix":"\"headerSource\": \"inline\" 또는 \"manifest\"를 .opal/code-scan.json에 추가하거나 --header-source <inline\|manifest>로 실행하세요","doc":"~/.opal/references/header-standard.md §7"}`. stderr **정확히 3줄**(사유 / 해결 / 근거 `~/.opal/references/header-standard.md §7`). 게이트 이전 처리: `--help` **exit 0**, `--version` **exit 0**(`code-scan v1.4.0`). `USAGE`에 `--header-source <inline\|manifest>` 옵션과 2택 도메인 안내 존재. `feature` 경로도 미설정 오버레이에서 차단되고, `--header-source manifest <tag>` 형태에서 플래그가 값을 소비해 태그 인자를 덮어쓰지 않음 |

#### S-3: 조회 경로 회귀 — `getSearchPaths` 반환 타입 변경

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `getSearchPaths` → `discoverFiles` 경로 (조회 8커맨드 전체가 경유) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `legacy-repo`에 `headerSource: "inline"` 명시 후 조회 8커맨드 실행 |
| 기대 결과 | 출력이 재캡처 골든과 **바이트 동일** · `scan --json` 결과에 `_source` 키 0건(`inline` 모드) · `module.exports` 10개 심볼 시그니처 불변 |
| 도구 | `node --test` — `tests/test-regression.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-regression.js` (TS-060·TS-064)<br>직접 재현: `(cd fixtures/legacy-repo && node code-scan.js <cmd> > /tmp/out && cmp /tmp/out ../golden/<file>)` × 8커맨드 |
| 결과 | **PASS** |
| 상세 | `legacy-repo`(`headerSource:"inline"` 명시) 8커맨드 재실행 → 골든 8종과 **전부 `cmp` 바이트 동일**: `scan --json`→`scan.json`(844B) · `domain`→`domain.txt`(292B) · `layer`→`layer.txt`(289B) · `search auth --json`→`search.json`(844B) · `exports token --json`→`exports.json`(305B) · `summary`→`summary.txt`(451B) · `depends auth_service`→`depends.txt`(113B) · `missing`→`missing.txt`(59B). `inline` 모드 `scan --json`에 `_source` 문자열 **0건**(`grep -c` = 0). `getSearchPaths` 반환 타입 변경이 `discoverFiles` 경유 조회 8커맨드에 회귀 0 |

#### S-6: 단일 필터 계약 — 5개 지점 동일 집합 판정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `isInScope` 단일 계약 · 열거·scaffold 열거·`validate` 구조 패스·`--changed`·`target` 5지점 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `mixed-scope` — `svc/shared/`의 5파일 중 `include`로 4파일(`Order*.java` 2 + `Ship*.java` 2)이 생존하고 `VendorLegacy.java` 1개가 탈락. 5지점을 각각 실행해 판정 집합을 수집 |
| 기대 결과 | 5지점이 **동일 파일 집합**을 판정(교차 비교 일치) · `grep`으로 확인한 스코프 필터 판정 로직이 `isInScope` 외 **0곳** · `scan <file>` 명시 경로는 include 밖이어도 결과 반환(PM Gate 보호 경로) |
| 도구 | `node --test` — `tests/test-scope-filter.js`(신규) |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-scope-filter.js` (TS-012·TS-013·TS-019)<br>직접 재현: `mixed-scope`(manifest 오버레이) 복사본에서 ①`scan --json` ②`scaffold` 후 매니페스트 `files` 키 ③`validate --json`의 `coverage.total` ④`validate --changed "<5파일 CSV>" --json` ⑤`target` ×5 · 소스 grep `\.include\b` |
| 결과 | **PASS** |
| 상세 | 5지점 전부 **생존 4파일 동일 집합**(`OrderRepo.java`·`OrderService.java`·`ShipRepo.java`·`ShipService.java`) — ①열거 4건 ②`order-svc:[OrderRepo,OrderService]` + `ship-svc:[ShipRepo,ShipService]` ③`coverage.total=4`(`manifest=4`, `ok:true`) ④5파일 전량 투입해도 `total=4` + `skipped:[{"file":"svc/shared/VendorLegacy.java","reason":"out_of_scope"}]` ⑤4×`manifest` / `VendorLegacy.java`=`none`. 교차 비교 불일치 0.<br>산출물 검사: 스코프 필터 판정 로직이 **`isInScope`(`code-scan.js:479`) 1곳** — 나머지 등장은 전부 호출부(`:515` `isFilteredOutOfScope` / `:534` `resolveScopeIn` / `:617` `discoverFiles` / `:1567` / `:1792`)이고 주석·문자열 제외 `.include` 판정 줄 **0건**.<br>TS-019: `VendorLegacy.java`에 인라인 헤더를 실제 부여했을 때 전체 열거는 `[]`(필터 적용), **명시 경로 `scan svc/shared/VendorLegacy.java --json`은 해당 파일을 반환** exit 0 — PM Gate 단일 파일 조회 보호 성립 |

#### S-7: 위반 검출기 필터 존중 — 오탐/미탐 양방향

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `cmdValidate`의 `files_key_removed`·`uncovered` 검출기 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `mixed-scope`에서 (a) include로 걸러진 `VendorLegacy.java`가 매니페스트에 미등재 (b) 필터에 걸리지 않는 생존 파일이 매니페스트에 미등재. 매니페스트 `files` 내용과 `scaffold` 선행 순서는 PLAN §3.7.2 명세를 따른다 |
| 기대 결과 | (a) `files_key_removed` **미집계**(오탐 0) (b) 여전히 검출됨(미탐 0). 필터가 검출기를 무력화하지 않는다 |
| 도구 | `node --test` — `tests/test-validate.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-validate.js` (TS-014·TS-015)<br>직접 재현: `mixed-scope` manifest 오버레이 복사본에서 `scaffold` 선행 → `validate --json` → 매니페스트에서 생존 파일 1건(`OrderRepo.java`) 삭제 → `validate --json` 재실행 |
| 결과 | **PASS** |
| 상세 | (a) include로 걸러진 `VendorLegacy.java`가 매니페스트에 미등재된 상태 → `{"ok":true,"violations":[],"counts":{"orphan":0,"uncovered":0,"conflict":0,"draft":0,"exports_not_found":0,"worker_scope_violation":0,"newly_uncovered":0,"pre_existing":0}}` — **`files_key_removed` 오탐 0**. (b) 필터에 걸리지 않는 in-scope 파일 `OrderRepo.java`를 매니페스트에서 제거 → `ok:false` + `[{"code":"uncovered","sub":"no_entry","file":"svc/shared/OrderRepo.java"},{"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/order-svc/_root.json","key":"OrderRepo.java"}]` — **미탐 0**. 필터가 검출기를 무력화하지 않는다 |

#### S-11: 모드별 커버리지 — 합산 폐기

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `cmdValidate` 모드별 커버리지 산출 · 검출기 분기 · `result.headerSource` 필드 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 동일 픽스처를 `inline`/`manifest` 두 모드로 오버레이 후 `validate --json` 실행하여 대조 |
| 기대 결과 | 커버리지 분모·분자가 각 모드의 소스만 반영 · `manifest` 모드의 인라인 부재와 `inline` 모드의 매니페스트 부재가 각각 위반 미집계 · `uncovered:pre_existing` 비차단 + 나머지 5종 차단 + exit 2 정책 불변 · `--json` 결과에 `headerSource` 필드 존재(소비자가 모드 식별 가능) |
| 도구 | `node --test` — `tests/test-validate.js` |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-validate.js` (TS-024~TS-027·TS-029)<br>직접 재현: `codemap-repo` 복사본 2종에 `headerSource`만 오버레이 → 각각 `node code-scan.js validate --json` |
| 결과 | **PASS** |
| 상세 | 동일 픽스처 2모드 대조 — `inline`: `coverage {total:9, inline:1, manifest:0, covered:1, percent:11.1}` / `manifest`: `coverage {total:9, inline:0, manifest:7, covered:7, percent:77.8}`. **분자가 각 모드 소스만 반영하며 합산이 사라졌다**(`inline+manifest` 합계가 `covered`와 별개로 계산되지 않음). `manifest` 모드에서 인라인 부재는 위반 미집계, `inline` 모드는 구조 패스 자체를 스킵(stderr 안내 1줄)해 매니페스트 무결성 위반 미집계. `--json` 결과에 **`headerSource` 필드 존재**(소비자 모드 식별 가능). 정책 불변: 두 모드 모두 위반 보유 시 **exit 2**, `uncovered:pre_existing`은 비차단(비git `mixed-scope` 트리에서 `uncovered:4`여도 `ok:true` 확인) |

#### S-14: 소비자 파급 — 이 저장소 + `brain-tool sync-header`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 이 저장소 `.opal/code-scan.json` 설정 · `brain_tool.py:766-798` subprocess 소비 계약 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — 실 CLI + 실 `brain-tool` subprocess |
| 조건 | (a) 이 저장소 루트에 `headerSource: "inline"` 추가 후 8커맨드 실행 (b) 미설정 임시 트리에서 `brain-tool sync-header` 실제 실행 |
| 기대 결과 | (a) 8커맨드 exit 0 (b) 실패 detail에 `header_source_unset` 문자열이 그대로 전달됨 — 사유가 소비자까지 도달한다. **`brain_tool.py` 변경 0줄**(stderr 병기 설계로 무수정 성립) |
| 도구 | `node --test` — `tests/test-regression.js` + `brain-tool` 실행 |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-regression.js` (TS-044·TS-045)<br>직접 재현: (a) 저장소 루트에서 조회 8커맨드 실행 (b) 미설정 트리 + HOME 격리 → `~/.opal/.venv/bin/python opal/tools/brain-tool/brain_tool.py sync-header` |
| 결과 | **PASS** |
| 상세 | (a) 이 저장소 `.opal/code-scan.json`에 `"headerSource": "inline"` 명시됨. 루트에서 `scan`·`domain`·`layer`·`search auth`·`exports token`·`summary`·`depends code-scan`·`missing` **8/8 exit 0** — 게이트가 자기 저장소를 막지 않는다.<br>(b) 실 `brain_tool.py` 실 subprocess(HOME을 임시 디렉토리로 돌려 **배포본이 아니라 이 저장소 소스 `code-scan.js`**가 실행되게 함) → stdout `{"ok": false, "command": "sync-header", "error": "header_parse_failed", "message": "code-scan @header 파싱 실패: code-scan exit=1, stderr=code-scan: header_source_unset — .opal/code-scan.json에 headerSource가 없습니다\n  해결: … \n  근거: ~/.opal/references/header-standard.md §7", "detail": "code-scan exit=1, stderr=code-scan: header_source_unset — …"}` **exit 1** — **`header_source_unset`이 소비자 detail까지 그대로 도달**. `git diff HEAD -- opal/tools/brain-tool/brain_tool.py` 빈 출력 = **변경 0줄**(stderr 병기 설계로 무수정 성립).<br>참고: 시스템 기본 `python3`에는 `yaml`이 없어 `brain-tool`이 뜨지 않는다 — 실행은 OPAL `.venv` 인터프리터 기준이며 테스트도 동일 경로를 강제한다 |

#### S-16: 픽스처 계약 + 전량 GREEN

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | 픽스처 20종 `headerSource` 보유 · 전체 테스트 스위트 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | Step 1 완료 후 `find ... -name code-scan.json \| xargs grep -L headerSource` 집계 · 전체 테스트 실행 |
| 기대 결과 | 누락 **0건** · `node --test "opal/tools/code-scan/tests/*.js"` 전량 pass · exit 0. 게이트 도입으로 기존 케이스가 붕괴하지 않는다 |
| 도구 | `node --test` — `tests/test-regression.js` + 전체 스위트 |
| 실행 명령 | `find opal/tools/code-scan/tests/fixtures -name code-scan.json \| xargs grep -L headerSource`<br>`env -u NODE_TEST_CONTEXT node --test --test-reporter=tap "opal/tools/code-scan/tests/*.js"` |
| 결과 | **PASS** |
| 상세 | 픽스처 `code-scan.json` **22건** 발견, `grep -L headerSource` **누락 0건**(값 분포 `manifest` 18 / `inline` 4 — 전량 2택 유효값). 전체 스위트: **`tests 191 / suites 0 / pass 191 / fail 0 / cancelled 0 / skipped 0 / todo 0` · duration 9,405ms · exit 0**. 게이트 도입으로 붕괴한 기존 케이스 0건.<br>주의(RED-EVIDENCE §5-③ 계승): `node --test`가 심는 `NODE_TEST_CONTEXT`가 손자 러너로 전파되면 위양성 exit 0이 나므로, 위 실행은 `env -u NODE_TEST_CONTEXT`로 변수를 제거한 상태에서 수행했다 |

#### S-17: 골든 재캡처 — 명시 설정 하 바이트 동일

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10, H-3 |
| 대상 | `tests/fixtures/golden/` 8종 + `README.md` |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `legacy-repo`(code-map 부재)에 `headerSource: "inline"` 명시 후 8커맨드 재캡처 → `git diff --stat`으로 077 골든과 대조 |
| 기대 결과 | 재캡처본과 실행 출력이 **바이트 동일** · **diff 0이 예측이자 검증 조건** — 차이가 나오면 GREEN 처리 금지하고 원인 규명 후 PM 보고 · `README.md`에 캡처 명령·설정 전문·diff 결과·근거 기록 |
| 도구 | `node --test` — `tests/test-regression.js` |
| 실행 명령 | `git diff --stat HEAD -- opal/tools/code-scan/tests/fixtures/golden/`<br>`env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-regression.js` (TS-060·TS-061·TS-064) |
| 결과 | **PASS** |
| 상세 | `git diff --stat HEAD -- tests/fixtures/golden/` **빈 출력 = 077 골든 대비 차이 0**. "캡처 미실행 위양성" 배제: 골든 8종의 mtime이 `2026-08-02 14:59`(재캡처 실행 시각)로 갱신돼 있음에도 내용 diff가 0이다 — 즉 **재캡처가 실행됐고 결과가 바이트 동일**이다. 추가로 `legacy-repo`에서 8커맨드를 다시 돌려 `cmp`로 전량 바이트 동일 재확인(S-3 상세와 동일 수치). `fixtures/golden/README.md`(4,022B)에 캡처 조건(`headerSource:"inline"` 설정 전문)·캡처 명령·077 대비 diff 근거 기록됨 |

#### S-18: 규칙 문서 5종 + `docs/` 3종 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, H-7 (문서 계약 동반 갱신) |
| 대상 | `header-standard.md` · `header-rules.md` · `code-scan-management.md` · `pm-review-gate.md` · `tools.md` + `docs/` 3종 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — 산출물 grep 검사 |
| 조건 | Step 10~12 완료 후 8문서 + `code-scan.js` 소스 대상 산출물 검사 |
| 기대 결과 | (a) 8문서 변경이력 표에 신규 행(버전 · `YYYY-MM-DD HH:mm` KST · `(080)`) (b) `readonly`를 판정 근거로 서술하는 문장 **0건**(deprecated 표기는 허용) (c) 개인 식별자 신규 기재 **0건**(역할명 PM/소유자만) (d) `header-rules.md`·`tools.md` 판정표의 `reason`이 **3값**(`header_source_inline`/`header_source_manifest`/`out_of_scope`) + `write_to`가 **3값**(`inline`/`manifest`/`none`) — 문서가 실제보다 좁은 폐쇄 도메인을 선언하지 않는다 (e) **`auto`를 유효값으로 서술하는 문장 0건**(`tools.md`·`header-standard.md` §7·`code-scan-management.md`) (f) **`code-scan.js`에 `auto` 리터럴 0건** — `USAGE` 설정 예시·`DEFAULT_CONFIG` 포함, 단 마이그레이션 힌트 문자열은 예외 (g) `code-scan-management.md` 최소 구조 예시에 `headerSource` 포함 (h) **`headerSource`를 판정·재계산하는 지점이 `resolveHeaderSource` 외 0곳** — `ctx.headerSource` 참조는 허용이며 grep이 판정과 참조를 구분한다. F-8의 TS-013(필터 판정이 `isInScope` 외 0곳)과 대칭인 **모드 축 집행**이다 (i) `discover` 산출물 `scopes[]`에 `headerSource` 키 0건 — TS-032(`readonly` 0건)의 대응물 |
| 도구 | `node --test` — `tests/test-regression.js` 산출물 검사 |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-regression.js` (TS-050~TS-055·TS-066~TS-068·TS-070·TS-071)<br>직접 재현: 8문서 `grep -c '(080)'` / `grep 'Task 080'` · `grep -n "'auto'" code-scan.js` · `grep -n "resolveHeaderSource\|headerSource" code-scan.js` |
| 결과 | **PASS** |
| 상세 | (a) 규칙 문서 5종 각 `(080)` 변경이력 행 1건 — `references/header-standard.md` · `references/harness/header-rules.md` · `references/pm/code-scan-management.md` · `references/harness/pm-review-gate.md` · `references/tools.md`(v2.9, `2026-08-02 14:50`). `docs/` 3종은 `(Task 080)` 표기로 각 1건(`ARCHITECTURE.md:402` · `CONVENTIONS.md:175` · `PROJECT.md:179`). (b) `readonly`를 판정 근거로 서술하는 문장 **0건**(폐기 표기만). (c) 개인 식별자 신규 기재 **0건**. (d) `header-rules.md:18-25` 판정표가 `write_to` **3값**(`none`/`inline`/`manifest`) × `reason` **3값**(`out_of_scope`/`header_source_inline`/`header_source_manifest`) 폐쇄 도메인으로 명시되고 두 축이 분리 서술됨. (e) `auto`를 **유효값으로** 서술한 문장 **0건** — 잔존 언급(`tools.md:287`, `:332`)은 전부 "제거되었다 / 거부된다" 폐기 표기. (f) 소스 `auto` 리터럴 **1개소** = `code-scan.js:52 const HEADER_SOURCE_LEGACY = 'auto';` — 마이그레이션 힌트 전용이며 `DEFAULT_CONFIG`·`USAGE`·`loadConfig`에는 0건(계약된 예외). (g) `code-scan-management.md` 최소 구조 예시에 `headerSource` 포함. (h) **모드 판정 지점 = `resolveHeaderSource`(`code-scan.js:258`, 호출 `:2078`) 1곳** — 그 밖의 `headerSource` 등장은 `parseArgs` 원문 적재(`:156` `:172`)·`loadConfig` 통과(`:243`)·스키마 안내 문자열·`ctx.headerSource` **읽기 전용 소비**(`:1019` `:1096` `:1650` `:1803` `:2022`)뿐이고 중간 전달 변수명은 `mode`. (i) `discover` 산출물 `scopes[]`에 `headerSource` 키 **0건**(`note` 문자열 언급뿐) |

#### S-19: **[목표달성]** 혼재 디렉토리 운영 워크플로 end-to-end

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-13 (목표 달성 축 — `scenario-gate.md` §2 ①) |
| 대상 | **태스크 목표 그 자체**(TASK.md §명확화 결과 갱신본) — "**전역 `headerSource` 한 키**가 code-scan의 조회·작성 판정·검증 전 경로를 지배하게 하고(**스코프 예외 없음 — 모드는 실행당 1값으로 확정**), `scopes` 객체 형식의 include/exclude로 혼재 **디렉토리**를 지원한다" |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** — 실 CLI 연속 호출 |
| 조건 | `mixed-scope` 픽스처 — `svc/shared/` 한 디렉토리에 **서로 다른 두 스코프의 파일이 include로 살아남는다**: `order-svc`(`include: ["Order*.java"]` → `OrderService.java`·`OrderRepo.java`)와 `ship-svc`(`include: ["Ship*.java"]` → `ShipService.java`·`ShipRepo.java`). 두 스코프는 `path`가 동일하고 `include`만 다르다. `VendorLegacy.java`는 어느 include에도 매칭되지 않아 `out_of_scope`로 상주한다. 이 트리에서 (Ⅰ) 픽스처 기준값 `headerSource: "inline"`으로 `discover` → `scaffold` → `target` → `validate` → `scan` 5경로를 연속 실행하고, (Ⅱ) **전역값만 `"manifest"`로 뒤집어** 동일 5경로를 재실행한다 (PLAN TS-072~074의 기준 방향과 일치) |
| 기대 결과 | **[혼재 디렉토리 지원]** (a) `discover` 산출물에 `include`가 추론되지 않고 빈 배열로 남는다(사람이 채우는 필드) (b) `scaffold` 매니페스트가 include 집합(생존 4파일)과 정확히 일치하고 `VendorLegacy.java`가 들어가지 않는다 (c) `target`이 생존 4파일은 모드값을, `VendorLegacy.java`는 `out_of_scope`를 반환한다 (d) `validate`가 `ok: true` — 탈락 파일 미등재를 위반으로 잡지 않는다<br>**[전역 단일 키 — 이번 축소의 목표]** (e) **서로 다른 두 스코프의 파일이 같은 실행에서 동일 모드를 보고한다** — 스코프 예외가 존재하지 않는다 (f) **`target`·`scaffold`·`validate`·`scan` 4경로가 보고하는 모드가 서로 일치한다** — 경로마다 모드가 갈리지 않는다 (g) **(Ⅱ)에서 전역값 한 줄만 뒤집으면 5경로 결과가 함께 뒤집힌다** — 모드 결정권이 전역 키 1곳에만 있다 (h) 어느 실행에서도 반대 소스 유래 필드가 0건 — **두 소스 혼재 0건** |
| 도구 | `node --test` — `tests/test-scope-filter.js` 통합 케이스 |
| 실행 명령 | `env -u NODE_TEST_CONTEXT node --test opal/tools/code-scan/tests/test-scope-filter.js` (TS-072·TS-073·TS-074)<br>직접 재현: `mixed-scope`를 스크래치패드에 2벌 복사 → 한쪽만 `headerSource`를 `manifest`로 치환(`diff -r`로 **차이가 그 1줄뿐**임을 먼저 확인) → 두 트리에서 `discover --dry-run --json` → `scaffold --json` → `target` ×5 → `validate --json` → `scan --json` (+ hook stdin 주입) 연속 실행 |
| 결과 | **PASS** |
| 상세 | 두 트리의 `diff -r` 결과: `.opal/code-scan.json` 2행 `"headerSource": "inline"` ↔ `"manifest"` **한 줄뿐**.<br>**[혼재 디렉토리 지원]** (a) `discover` 산출물의 `include`는 **추론되지 않는다** — config에 include가 없는 트리에서 `{"svc":{"root":"svc/","anchors":["shared"],"include":[],"exclude":[]}}`로 빈 배열, 사람이 명시한 include는 그대로 보존(추론 아닌 승계). (b) `scaffold` 매니페스트 = `order-svc:["OrderRepo.java","OrderService.java"]` + `ship-svc:["ShipRepo.java","ShipService.java"]`, `.opal/code-map/` 전체 `grep -rl VendorLegacy` **0건**. (c) `target` 생존 4파일은 모드값, `VendorLegacy.java`는 `out_of_scope`. (d) `validate` **`ok:true`** — 탈락 파일 미등재를 위반으로 잡지 않음.<br>**[전역 단일 키]** (e) **서로 다른 두 스코프(`order-svc`/`ship-svc`)의 4파일이 같은 실행에서 동일 모드 보고** — 스코프 예외 0. (f) `target`·`scaffold`·`validate`·`scan` **4경로 모드 일치**(`inline`: target `write_to:inline` / scaffold `skipped:header_source_inline` / validate `manifest:0` / scan `{}` ↔ `manifest`: target `write_to:manifest` / scaffold `updated:2` / validate `headerSource:"manifest"` / scan 4엔트리). (g) **전역 한 줄 반전으로 5경로 동시 반전** — scaffold `created:0,updated:0,skipped:[header_source_inline]` → `updated:2,skipped:[]` · target `{"write_to":"inline","reason":"header_source_inline"}` → `{"write_to":"manifest","reason":"header_source_manifest","scope":…,"manifest":…,"key":…}` · validate `coverage{inline:0,manifest:0,covered:0,percent:0}` → `{inline:0,manifest:4,covered:4,percent:100}` + `headerSource` 필드 · scan `{}` → 4엔트리(`_source:"file"`) · hook 무출력 → in-scope 미등재 파일 경고. (h) 어느 실행에서도 반대 소스 유래 필드 0건 — `inline` 실행 `_source` 키 0, `manifest` 실행 인라인 유래 값 0 |

---

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-22: 실 편집 세션에서 hook fail-safe 실증 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | PostToolUse hook (`code-map-hook.js`)의 실제 AI 세션 동작 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 자동 재현 불가. stdin 주입 테스트(S-2)는 hook 로직을 검증하지만 실세션 통합은 검증하지 못한다 |
| 조건 | 캡틴이 `headerSource` 미설정 프로젝트에서 코드 파일을 Edit 또는 Write |
| 기대 결과 | 세션에 에러·경고 노출 **0건** · 편집이 정상 완료 · 세션이 중단되지 않는다. (077 PM-7 fail-safe 계약: "매 편집마다 에러가 뜨면 세션이 망가진다") |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **PASS** (2026-08-02 16:12 · 소유자 지시로 PM이 실세션 수행 · revup) |
| 상세 (실측) | **환경**: 소유자가 `install-mac.sh`로 080을 배포한 뒤 수행(`~/.opal` code-scan **v1.4.0**, hook에 `headerSource` 인지 6곳, 프로젝트 소스와 `diff` 동일 확인). 대상 프로젝트 `/Volumes/Data/StoreLinkStudio/revup` — `headerSource: "auto"`(080이 폐기한 값 = **무효값 분기**), `.opal/code-map/` 27스코프, `index.json`에 폐기 키 28회. **수행**: 실제 `Edit` 도구로 `workspace/backend/domain/revup/src/main/kotlin/io/storelink/revup/aggregate/mapper/RevupCodeMapper.kt`(인라인 헤더 없음·매니페스트 등재분)에 임시 주석 1줄 추가 → 원복까지 **총 2회 편집 = hook 2회 발화**. **관측**: 두 번 모두 세션에 에러·경고·`additionalContext` **노출 0건**, 편집 정상 완료, 세션 중단 없음. 파일은 원본과 바이트 동일로 복원 확인(`TEMP` 잔존 0건). **대조**: 같은 시점 revup CLI는 `header_source_invalid`(+migration 힌트)로 exit 1 차단 — **CLI는 막고 hook만 조용한** 계약 비대칭이 실세션에서 의도대로 성립함을 확인. **범위 단서**: revup은 "미설정"이 아니라 "무효값" 상태이므로 이 실측이 덮은 것은 ⑤ 게이트의 **무효값 분기**다. 미설정·`inline` 분기는 동일 게이트를 공유하며 TS-076·S-2에서 stdout·stderr 양축 0바이트로 별도 실증됨. **선행 결함**: 이 검증의 사전 점검에서 hook 조기이탈 경로의 stderr 누출(295바이트/편집)이 발견되어 추가수정으로 교정한 뒤 재측정한 결과다(AGENTIC-LOG #70·#72) |
| 상세 (판정 경위) | M3 [SUPERVISOR] 시나리오이므로 `opal-test-agent`가 **판정하지 않았다**. 자동 재현으로 갈음하지 않았으며 임의 PASS 처리도 하지 않았다 — 자동 재현 불가가 이 시나리오의 존재 이유다. 인접 근거로 hook **로직** 자체는 S-2에서 5트리(미설정/`auto`/`bogus`/`inline`/깨진 JSON) 전부 stdout 0바이트·exit 0으로 실증돼 있으나, **실제 편집 세션 통합**은 여기서 다루지 않는다. 아래 PM 표준 요청 양식으로 소유자 확인을 발송한 뒤 회신 결과를 이 칸에 기록한다 |

**PM 표준 요청 양식** (TEST 단계에서 발송):

```
캡틴, [시나리오 S-22]는 사용자 협업 검증이 필요합니다.
요청 내용: headerSource가 설정되지 않은 아무 프로젝트에서 코드 파일 1개를 편집(Edit/Write)해 주세요.
기대 결과: 편집이 정상 완료되고, 세션에 code-scan 관련 에러·경고가 전혀 뜨지 않습니다.
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

> `테스트 파일:케이스` 열의 케이스명은 `[T080/L{계층}-{AC}]` 프리픽스 규약(`test-scenario-guide.md` §Step 4-b)을 따른다. 파일 경로는 전부 `opal/tools/code-scan/tests/` 하위.

| AC ID (TASK) | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 (TS-ID) | 비고 |
|-------------|---------|---------|---------|--------------------------|------|
| F-1 AC (2택·미설정·**실행당 1값**) | H-4 | L1 | S-21 | `test-header-source.js:[T080/L1-F1]` (TS-004, TS-005, TS-006) | 우선순위 **2층** + 스코프 오버라이드 부재 부정 단언 |
| F-1 AC (`auto` 명시 거부) | H-1 | L1 | S-20 | `test-header-source.js:[T080/L1-F1b]` (TS-003) | 구형 값 소멸 — 마이그레이션 힌트 특례 |
| F-1 AC (임의 무효값·CLI 무효값 거부) | H-1 | L1 | S-20 | `test-header-source.js:[T080/L1-F1c]` (TS-009, TS-065) | 일반 무효값 경로 · `where` 출처 표기 · 077 TS-046 반전 승계처 |
| F-2 AC (전 명령 exit 1) | H-1 | L2 | S-1 | `test-header-source.js:[T080/L2-F2]` (TS-001, TS-002) | 13커맨드 |
| F-2 AC (`--help`/`--version` 예외) | H-1 | L2 | S-1 | `test-header-source.js:[T080/L2-F2b]` (TS-007) | 게이트 이전 처리 |
| F-3 AC (`decideTarget` 모드 존중) | H-6 | L1 | S-8 | `test-target.js:[T080/L1-F3]` (TS-020, TS-021, TS-022) | reason 2값 |
| F-4 AC (`scaffold` no-op) | H-6 | L1 | S-10 | `test-scaffold.js:[T080/L1-F4]` (TS-023) | 사유 보고 |
| F-5 AC (모드별 커버리지) | H-7 | L2 | S-11 | `test-validate.js:[T080/L2-F5]` (TS-024~TS-027, TS-029) | 합산 폐기 |
| F-5 AC (fail-soft 파생 — 직접 대응 AC 없음) | **H-12** | L1 | **S-12** | `test-resolve-header.js:[T080/L1-H12]` (TS-028) | `manifest` + index 부재 → stderr 경고 1줄·exit 0. AC가 아닌 **가설 기원** 시나리오라 프리픽스를 가설 ID로 둔다 |
| F-6 AC (`readonly` 무시 + 전역값 적용) | H-8 | L1 | S-13 | `test-target.js:[T080/L1-F6]` · `test-discover.js:[T080/L1-F6b]` (TS-030~TS-034) | **양방향 고정**(TS-030 반전 · TS-033 재정의) + 안내 1회 |
| F-7 AC (`scopes` 객체 형식) | H-4 | L1 | S-4 | `test-scope-filter.js:[T080/L1-F7]` (TS-010, TS-011) | 문자열 무수정 |
| F-8 AC (5지점 단일 계약) | H-5 | L2 | S-6 | `test-scope-filter.js:[T080/L2-F8]` (TS-012, TS-013, TS-019) | grep 산출물 검사 포함 |
| F-8 AC (`target` 배선·반환 계약) | H-13 | L1 | S-9 | `test-target.js:[T080/L1-F8b]` · `test-hook.js:[T080/L1-F8c]` (TS-035~TS-037) | 신규 공백 지점 |
| F-9 AC (검출기 필터 존중) | H-5 | L2 | S-7 | `test-validate.js:[T080/L2-F9]` (TS-014, TS-015) | 오탐·미탐 양방향 |
| F-10 AC (스코프 중복 우선순위) | H-4 | L1 | S-5 | `test-scope-filter.js:[T080/L1-F10]` (TS-016~TS-018) | `scope_ambiguous` |
| F-11 AC (규칙 문서 5종) | H-6, H-7 | L2 | S-18 | `test-regression.js:[T080/L2-F11]` (TS-050~TS-055) | 산출물 검사 · `reason`/`write_to` **3값** 표기 |
| F-11 AC (`auto` 자산 잔존 0) | H-1 | L2 | S-18 | `test-regression.js:[T080/L2-F11b]` (TS-066, TS-067) | 소스 리터럴 0건 + 문서 서술 0건 |
| F-11 AC (`write_to` 3값 문서 반영) | H-6 | L2 | S-18 | `test-regression.js:[T080/L2-F11c]` (TS-068) | `write_to`·`reason` 축 분리 — M-2 재발 방지 |
| F-12① AC (이 저장소 설정) | H-1, H-11 | L2 | S-14, S-15 | `test-regression.js:[T080/L2-F12a]` (TS-044, TS-046, TS-047) | gitignore 예외 동반 |
| F-12② AC (에러 메시지 품질) | H-1 | L2 | S-1, S-20 | `test-header-source.js:[T080/L2-F12b]` (TS-002, TS-008) | 미설정/무효 구분 |
| F-12③ AC (`brain-tool` 실패 전달) | H-1 | L2 | S-14 | `test-regression.js:[T080/L2-F12c]` (TS-045) | `brain_tool.py` 무변경 |
| F-12④ (PM Gate 절차) | H-7 | L2 | S-18 | `test-regression.js:[T080/L2-F12d]` (TS-050, TS-051) | 문서 산출물 |
| F-12⑤ AC (hook fail-safe) | H-2 | L1 | S-2 | `test-hook.js:[T080/L1-F12e]` (TS-040~TS-043) | 3케이스 무출력 |
| F-12⑤ AC (실세션 실증) | H-2 | L3 | S-22 | (수동 — [SUPERVISOR]) | 자동화 불가 |
| F-13 AC (골든 재캡처) | H-10, H-3 | L2 | S-17, S-3 | `test-regression.js:[T080/L2-F13]` (TS-060, TS-061, TS-064) | 바이트 동일 |
| 완료기준 (전량 GREEN) | H-9 | L2 | S-16 | 전체 스위트 (TS-062, TS-063) | 픽스처 20종 |
| **TASK 목표 문장** (전역 단일 키 · 스코프 예외 없음 · 실행당 1값) | H-5, H-13 | L2 | **S-19** | `test-scope-filter.js:[T080/L2-GOAL]` (TS-072, TS-073, TS-074) | **목표달성 시나리오** — 두 스코프 동일 모드 · 4경로 일치 · 전역 1값 반전으로 5경로 동시 반전 |
| **스코프 오버라이드 잔존 0** (2026-08-02 신규 구형) | H-4 | L1·L2 | S-21, S-18 | `test-header-source.js:[T080/L1-F1d]` (TS-005, TS-069) · `test-regression.js:[T080/L2-F11d]` (TS-070, TS-071) | `index.json`·`code-scan.json` **대칭 쌍** 부정 단언 + 판정 지점 1곳 grep 집행 + `discover` 산출물 0건 |
| F-7 AC (타입 위반 거부) | H-4 | L1 | S-4 | `test-scope-filter.js:[T080/L1-F7b]` (TS-075) | `include`/`exclude` 스칼라·비문자열·객체 3케이스 |
| **제약② 파기 (채택/잔존)** | H-1 | L1 | **S-20** | `test-header-source.js:[T080/L1-F1b]` (TS-003) | **구형 잔존 0** |

**매핑 완전성**

- TASK 요구사항 F-1~F-13 **13건 전량**이 위 표에 커버됨 (미매핑 0건).
- 가설 H-1~H-14 **14건 전량**에 시나리오 연결됨 (미연결 0건).
- 시나리오 S-1~S-22 **22건 전량**에 계층(L)과 실행 방식(M)이 명시됨.
- TS-ID **67종**(v1.2에서 5종 + v2.1에서 TS-069~TS-075 7종 신설) 전량이 시나리오에 귀속됨.
- 가설 14건 → 시나리오 22건 (정량 요건 "가설 N건 → 시나리오 N건 이상" 충족).

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | (미도입) | **N/A** | 저장소 루트·`opal/tools/code-scan/` 모두 `package.json`·eslint 설정 **0건**. TASK.md §제약 "외부 npm 의존 금지"에 따라 린터를 도입하지 않는 것이 이 도구의 정책이며, 정적 검사는 아래 #2로 대체한다 |
| 2 | 타입 체크 | `node --check` | **Pass** | 순수 CommonJS JS — TypeScript 미사용(`tsconfig.json` 없음). `code-scan.js` · `code-map-hook.js` · `tests/*.js` **전 파일 `node --check` 통과**, 구문 오류 0 |
| 3 | 포맷터 | (미도입) | **N/A** | prettier 설정 0건 — #1과 같은 무의존 정책 |
| 4 | Node 표준 모듈만 사용 (`fs`/`path`/`child_process`) | `grep require(` | **Pass** | 런타임: `fs` · `path` · `child_process` + 내부 `./code-scan.js`뿐. 테스트: `node:test` · `node:assert/strict` · `node:fs` · `node:path` · `node:os` · `node:child_process`. **외부 npm 의존 0건** |
| 5 | `code-scan.js` `VERSION` = `1.4.0` + 변경이력 행 | `grep` + `--version` | **Pass** | `code-scan.js:37 const VERSION = '1.4.0'` · CLI 출력 `code-scan v1.4.0` · `:2168`에 `v1.4.0 — 2026-08-02 — 전역 단일 headerSource 2택…` 변경이력 행 존재 |
| 6 | 신규 테스트 2파일 @header (`layer: test` · `task: "080"` · `scenarios`) | `head`/`grep` | **Pass** | `test-header-source.js` → `{"layer":"test","task":"080","scenarios":["S-1","S-20","S-21"]}` · `test-scope-filter.js` → `{"layer":"test","task":"080","scenarios":["S-4","S-5","S-6","S-19"]}` |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | `code-scan.js` · `code-map-hook.js` · `tests/*.js` · 저장소 `.opal/code-scan.json` 대상 정규식 스캔(`api[_-]?key` / `secret` / `passwd` / `BEGIN … PRIVATE KEY` / `AKIA[0-9A-Z]{16}` / `ghp_…`) **매치 0건**. `token`은 `exports token` 검색 인자 예시로만 등장 |
| 2 | `.gitignore` 확인 — `!.opal/code-scan.json` 예외가 시크릿을 노출하지 않는가 | **Pass** | 추적 대상이 된 `.opal/code-scan.json`의 키는 `headerSource`·`scopes`·`extensions`·`exclude`·`excludePatterns` **5개뿐 — 전부 스캔 설정이며 크리덴셜 필드 0건**. 예외는 이 파일 1개로 한정(`.gitignore:7`)되어 `.opal/*` 나머지는 계속 무시된다 |
| 3 | 에러 메시지에 절대 경로·사용자명 과다 노출 0건 (프로젝트 상대 경로만) | **Pass** | 게이트 에러 payload의 경로 표기는 프로젝트 상대(`.opal/code-scan.json`) — 실측 `"detail":".opal/code-scan.json에 headerSource가 없습니다"`. 소스에 `/Users`·`/Volumes`·`$HOME` 절대경로 리터럴 0건 |
| 4 | `--header-source` 인자가 셸·파일 경로로 전달되지 않는가 (2택 화이트리스트 검증) | **Pass** | `HEADER_SOURCE_VALUES = ['inline','manifest']` + `.includes()` 화이트리스트 통과 값만 사용되고 무효값은 exit 1 차단. `spawnSync` 호출은 `git rev-parse` / `git rev-parse --verify` / `git show HEAD:<rel>` **3개소뿐이며 전부 배열 인자(셸 미경유)**, 인자에 `headerSource` 값이 실리는 경로 0건 |
| 5 | stdout JSON 오염 0건 — 안내·경고는 전부 stderr | **Pass** | 경고·안내를 동반하는 4실행(`manifest`+index 부재 / `readonly` deprecated / 스코프 `headerSource` deprecated / `inline` 구조패스 스킵) 전부 **stdout이 `JSON.parse` 성공**. 게이트 에러도 stdout은 JSON 1줄, 사람이 읽는 3줄 안내는 stderr |
| 6 | 신규 파일 생성 경로가 `.opal/code-map/` 하위로 한정 (경로 이스케이프 방지) | **Pass (단서 1)** | `writeFileSync` 2개소 — `scaffold`는 `.opal/code-map/` 하위 매니페스트(`:1713-1714`), `discover`는 `outPath`(`:1541-1542`, 기본 `.opal/code-map/index.json`). 단서: `discover --out <path>`는 **문서화된 CLI 옵션**이므로 사용자가 임의 경로를 지정할 수 있다 — 외부 입력이 아닌 사용자 자기 입력 경로이며 이 태스크가 도입한 표면이 아니다 |

## 7. 판정

**All Pass — L1/L2/L3 22건 전량 PASS.** S-22는 2026-08-02 16:12 소유자 지시로 PM이 배포 후 revup 실세션에서 수행하여 PASS 확정(상세는 §3 L3 S-22 결과 칸). 이로써 조건부 판정이 해제되고 3계층 전체 무조건 All Pass가 성립한다.

**판정 근거**

- **실행 결과**: L1 11건 + L2 10건 = **21건 전량 PASS, FAIL 0 · Skip 0**. 전체 스위트 `env -u NODE_TEST_CONTEXT node --test "opal/tools/code-scan/tests/*.js"` → **tests 191 / pass 191 / fail 0 / exit 0**. 각 시나리오는 테스트 케이스 통과에 더해 **실 CLI subprocess·실 픽스처 복사본으로 직접 재현**해 관측값을 상세 칸에 실었다(증거 없는 PASS 0건).
- **핵심 기능 · 보안**: 코드 품질 6항목 중 4 Pass / 2 N/A(린터·포맷터 미도입 — 무의존 정책), 보안 6항목 전부 Pass(단서 1건은 기존 문서화 옵션). Critical Fail 사유 0건.
- **mock 미사용**: 전 시나리오가 저장소 커밋 픽스처 또는 그 스크래치패드 복사본 + 실 subprocess로 수행됐다. 저장소 픽스처 원본·`tests/*.js`·소스 파일 변경 0건(RED 봉인 유지).
- **`All Pass`를 단서 없이 쓰지 않는 이유**: S-22(L3 [SUPERVISOR])는 **실행하지 않았고 판정하지도 않았다**. 자동 재현이 불가능한 것이 이 시나리오의 존재 이유이므로 S-2(stdin 주입)로 갈음하지 않았다. 시나리오 22건 중 1건이 미판정 상태이므로 "22/22 All Pass"라고 적으면 사실이 아니다. 반면 **실패는 0건**이므로 `Partial Fail`·`Critical Fail`도 사실이 아니다 — 따라서 범위를 명시한 조건부 All Pass로 기록한다.
- **후속**: S-22 소유자 회신이 PASS면 이 절을 무조건 `All Pass`로 갱신한다. FAIL이면 H-2(hook fail-safe, P0)가 깨진 것이므로 `Critical Fail`로 재판정해야 한다.

**PM 확인 필요 사항 2건 (고치지 않고 보고)**

| # | 내용 | 영향 |
|---|------|------|
| ① | `mixed-scope-ambiguous` 트리에서 `target`은 `scope_ambiguous` exit 1로 거부하지만 **`scaffold --header-source manifest`는 exit 0**으로 통과하며 5파일을 양쪽 매니페스트에 중복 등재한다(`order-svc/_root.json`·`ship-svc/_root.json`에 `VendorLegacy.java` 동시 추가 등). S-5 (b)의 단언 대상은 `target`이라 판정에는 영향 없다 | 계약 비대칭 — 후속 태스크 판단 대상 |
| ② | 각 시나리오의 `실행 명령` 칸이 EXECUTE 단계에서 채워지지 않은 채(`_{EXECUTE 워커가 채움}_`) TEST 단계로 넘어왔다. TEST 워커가 **실제로 실행한 명령**으로 대신 채웠다 | 문서 공백 해소 — 절차상 담당 단계 어긋남 |

### PM Gate 체크 (7대 강제 룰 + 확장)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — 실 픽스처·실 subprocess만 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (10행 전량)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (S-1~S-22)
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 0건)
- [x] L1/L2/L3 계층 명시 (22건 전량)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 표준 요청 양식 첨부 (S-22)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (H-1~H-14 전량)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **비해당(면제)**. 근거는 §3.0 판정표 (FE 화면·인증·외부 API 연동 변경 0건)
- [x] 목표 커버 — TASK 요구사항 F-1~F-13 전량이 §4에 커버되고, 목표달성 시나리오 **S-19**가 §3 L2에 존재

### RED-first 집행 확인

- [x] RED 작성 주체 `opal-test-agent(mode: red)` ≠ 구현 주체 `opal-task-agent` ([MUST] `red-first.md` §2)
- [x] RED 증거 기록 위치 명시 — `RED-EVIDENCE.md` (`node --test` exit≠0 로그)
- [x] [MUST] `red-first.md` §3 — Step 3~14 동안 `tests/*.js` 편집 금지를 PLAN §3.7.4 집행 규칙에 명문화
- [x] 픽스처(Step 1)는 RED(Step 2) 이전에 확정 — H-9 붕괴 방지

---

## 8. 목표-커버 게이트 결과 (iteration 1)

| 축 | 판정 주체 | 결과 |
|----|----------|------|
| ② 요구 커버 / ③ 기능 커버 / ④ 리스크 커버 | `test-tool scenario-coverage-check` (결정론) | **exit 0** — `all_covered: true`, 요구 13 / 기능 7 / 가설 14 / 시나리오 22 누락 0건 |
| ① 목표 달성 | `opal-evaluator-agent` (판단) | **2 / 2** — S-19가 목표 문장을 대상으로 `discover→scaffold→target→validate→scan`을 실 CLI로 관통, 070형 결함(시나리오 부재) 미재발 |
| ⑤ 채택/잔존 | `opal-evaluator-agent` (판단) | **1 / 2** — `readonly` 잔존은 4중 검증되나 `auto`가 런타임 거부 1종뿐이었음 |
| ⑥ 경계/부정 | `opal-evaluator-agent` (판단) | **2 / 2** — 부정 경로 7종 존재, "없어야 할 필드"까지 부정 단언 |
| **종합** | — | 평균 **1.67** (임계 각≥1 AND 평균≥1.5) → **verdict: pass** |

보고서: `SCENARIO-GATE-1.md`

**pass 이후 PM 자율 보정 3건** (평가자 `gaps` 반영 — 통과 여부와 무관하게 결함이므로 EXECUTE 진입 전 정정):

| gap | 내용 | 반영 |
|-----|------|------|
| gap-2 | S-18이 `reason`을 **2값**으로 검사 → 확정 도메인(3값, `out_of_scope` 포함)과 정면 모순. 문서가 거짓 폐쇄 도메인을 선언하는 것을 시나리오가 승인하는 형태 — 077 H-6과 동형 결함 재생산 | §2.2·§3 S-18을 `reason` 3값 + `write_to` 3값 검사로 정정. PLAN §3.6.2·TS-053도 정정 재지시 |
| gap-1 | `auto` 잔존이 자산 계층에서 미검증(런타임 거부 1종뿐) | S-18에 문서 서술 0건 + 소스 리터럴 0건 검사 추가 |
| gap-3 | 무효 입력값 거부의 **일반 경로** 부재 — `auto`는 마이그레이션 힌트가 붙는 특례 | S-20에 임의 무효값(`where:"config"`)·CLI 무효값(`where:"cli"`) 2케이스 추가 |

> 보정은 평가자가 지목한 gaps를 좁혀 반영한 것이며 시나리오 집합(S-1~S-22)·매핑 구조는 불변이다. 보정 후 `scenario-coverage-check`를 재실행해 exit 0을 재확인했다.

**PLAN 측 대응 결과** (PM 재지시 → PLAN v1.2, 1,761줄):

- `reason` **3값** / `write_to` **3값**으로 문서 갱신 명세 6곳 정렬. `header-rules.md`에 그대로 옮길 확정 3행 판정표를 PLAN §3.6.2 (2)에 직접 명시.
- 판정 순서 확정: **① `out_of_scope`(스코프 필터 탈락) → ② `inline` → ③ `manifest`** — 필터 판정이 모드 판정보다 먼저다.
- "모드 축 2값 병합 ≠ 전체 도메인 3값" 조정 문단을 §3.3.2 (B)에 추가 — 후속 워커가 "2값 축소" 문장을 보고 도메인을 다시 좁히지 않게 고정.
- 신설 TS 5종: **TS-009**(CLI 무효값 `where:'cli'`) · **TS-065**(config 임의 무효값 `where:'config'`, 077 TS-046 반전 승계처) · **TS-066**(소스 `auto` 리터럴 0건) · **TS-067**(문서 `auto` 유효값 서술 0건) · **TS-068**(`write_to` 3값 + `reason`과 축 분리).
- 이로써 `auto`도 `readonly`와 동일한 **4중 잔존 검사**를 받는다 — 런타임 거부(TS-003) · 소스 grep(TS-066) · 문서 grep(TS-067) · 픽스처 값 명시(TS-063).

---

## 9. 설계 축소 반영 (v1.2 — 2026-08-02)

소유자 결정으로 `headerSource`가 **전역 단일 키**가 되고 스코프별 오버라이드가 제거됐다(TASK.md D-2 갱신, PLAN v2.0 §12). 시나리오 집합(S-1~S-22)·가설(H-1~H-14)·매핑 구조는 불변이며, **전제가 바뀐 2개 시나리오만 재정의**했다.

| 시나리오 | 초판(v1.1) | 축소 후(v1.2) | 근거 |
|---------|-----------|--------------|------|
| S-21 | 우선순위 **3층**(스코프 > CLI > 전역) 승리 검증 | 우선순위 **2층**(CLI > 전역) + **스코프 키 무시 부정 단언** | 스코프 오버라이드 소멸. "오버라이드가 없다"는 것 자체가 지켜야 할 계약이므로 삭제 대신 부정 단언으로 남긴다 — 검증이 없으면 나중에 조용히 되살아난다 |
| S-13 | `readonly: true` → `manifest` 흡수 동작 | `readonly` **무시** + **전역값 양방향 고정**(`inline`→`inline`, `manifest`→`manifest`) | 흡수할 자리가 사라짐. 한 방향만 보면 우연 일치와 구분되지 않으므로 양방향으로 고정 |

가설 H-8 서술도 "하위호환 해석 누락" → "**흡수 로직 잔존 시 전역 단일 키 결정이 조용히 파괴됨**"으로 방향을 뒤집었다.

> 축소로 없어진 설계 표면적: 판정 함수 −1개(`effectiveHeaderSource`) · 판정 층 −1층 · index 스키마 신설 키 −1개 · 하위호환 분기 −2개. 판정 단위가 **파일 단위 → 실행 단위**로 바뀌어 소비자의 재계산 의무가 소멸했다(PLAN §12).

---

## 10. 목표-커버 게이트 결과 (iteration 2) + 보정

| 축 | iteration 1 | iteration 2 | 변화 |
|----|------------|------------|------|
| ② ③ ④ (결정론) | exit 0 | **exit 0** | 불변 (요구 13 / 기능 7 / 가설 14 / 시나리오 22) |
| ① 목표 달성 | 2 | **1** | ▼ — 품질 후퇴가 아니라 **목표가 이동했는데 목표 시나리오가 따라가지 않음** |
| ⑤ 채택/잔존 | 1 | **2** | ▲ — `auto` 4중 검사 확보 + `reason` 도메인 재발 경로 차단 |
| ⑥ 경계/부정 | 2 | **2** | 불변 |
| **종합** | 1.67 pass | **1.67 pass** | — |

보고서: `SCENARIO-GATE-2.md`

**pass 이후 PM 자율 보정 3건** (iteration 2 `gaps` 반영):

| gap | 내용 | 반영 |
|-----|------|------|
| ①-1 | S-19가 **구 목표 문장을 인용**한 채였고, 픽스처 구조상 형제 파일이 모드 판정 **이전에** `out_of_scope`로 탈락해 "전역성"을 보일 무대 자체가 없었다 | S-19 대상을 갱신 목표로 교체 + 단언 (e)(f)(g) 신설(두 스코프 동일 모드 · 4경로 일치 · 전역 반전 대조). 픽스처를 "**두 스코프 생존**" 구조로 바꾸도록 PLAN 재지시 |
| ⑤-1 | 스코프 오버라이드 차단이 `index.json` 쪽만이고, **사용자가 실제로 편집하는 `code-scan.json`** 스코프 객체는 무방비 — 넣어도 안내 없이 조용히 버려진다 | S-21에 조건 (d) 신설(config 측 대칭 부정 단언). PLAN에 `normalizeConfigScope` 안내 + TS 신설 재지시 |
| ⑤-2 | PLAN §12가 "모드 판정이 `main()` 1곳으로 수렴"을 구조적 이득으로 **선언만** 하고 집행이 없다 — 필터 축의 TS-013에 대응하는 모드 축 산출물 검사 부재 | S-18에 단언 (h)(i) 신설(판정 지점 `resolveHeaderSource` 외 0건 · `discover` 산출물 `headerSource` 0건) |

> 비차단 이월 1건: `include`/`exclude` 타입 위반(`string[]` 아님)의 `invalid_index` 거부가 미검증 — PLAN에 TS 1건 추가 지시.

**평가자가 확인한 것**: TS-005/TS-006을 삭제하지 않고 방향 반전으로 남긴 판단이 옳았고(축소가 시나리오를 증발시키지 않음), `readonly` 반전도 판별력 있는 방향을 포함한 양방향으로 고정돼 우연 일치를 배제한다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.4 | 2026-08-02 15:40 | TEST 단계 실행 결과 기입 — S-1~S-21 `실행 명령`·`결과`·`상세` 21건 실측 채움(전량 PASS), S-22는 [SUPERVISOR] 대기로 표기, §5 코드 품질 6항목·§6 보안 6항목 채움, §7 판정 확정(조건부 All Pass + PM 확인 2건) (080) |
| v1.3 | 2026-08-02 01:05 | 게이트 iteration 2 결과 반영(§10 신설) + gaps 3건 보정 — S-19 목표 재정합(전역성 단언 3건 신설·픽스처 2스코프 생존 구조), S-21 config 측 대칭 부정 단언, S-18 모드 판정 지점 집행 2건 (080) |
| v1.2 | 2026-08-02 00:30 | 설계 축소 반영(§9 신설) — 스코프별 오버라이드 제거에 따라 S-21(우선순위 2층 + 부정 단언)·S-13(`readonly` 무시 + 양방향 고정) 재정의, H-8 가설 방향 반전, §4 매핑 2행 갱신 (080) |
| v1.1 | 2026-08-01 23:05 | 목표-커버 게이트 iteration 1 결과 반영(§8 신설) + 평가자 gaps 3건 보정 — S-18 `reason`/`write_to` 3값 정정(gap-2), `auto` 자산 잔존 검사 추가(gap-1), 무효값 일반 경로 2케이스 추가(gap-3) (080) |
| v1.0 | 2026-08-01 21:30 | 초기 작성 — 가설 H-1~H-14 → 시나리오 S-1~S-22, TS-ID 55종 매핑, 목표달성(S-19)·채택/잔존(S-20)·경계/부정(S-21)·[SUPERVISOR](S-22) 축 포함 (080) |
