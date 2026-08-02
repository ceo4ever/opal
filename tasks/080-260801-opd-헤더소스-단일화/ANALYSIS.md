# ANALYSIS: 헤더 소스 단일화 — headerSource 기준 통일 + 스코프 include/exclude

> 작성일: 2026-08-01
> 입력: TASK.md
> 출력: ANALYSIS.md
> 특수 조건: 이 태스크는 opds→opd 에스컬레이션으로 PLAN.md가 선행 작성됨. 본 문서는 (1) 표준 ANALYSIS.md 산출물이자 (2) PLAN.md의 코드 주장에 대한 독립 교차 검증이다. 모든 판정은 코드를 먼저 읽고 도출했으며, PLAN.md는 §7 대조 절에서만 열람했다.

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 주 분석 대상, v1.3.3, 1774줄 |
| D-2 | 소스 | code-map-hook.js | `opal/tools/code-scan/code-map-hook.js` | PostToolUse hook, loadConfig 직접 호출 |
| D-3 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py:766-798` | `sync-header`의 code-scan subprocess 소비 |
| D-4 | 소스 | tests/*.js + fixtures/ | `opal/tools/code-scan/tests/` | 8테스트파일 + 20 code-scan.json + 18 index.json 픽스처 |
| D-5 | 설계 | header-standard.md | `opal/core/references/header-standard.md` | §7 2소스 스키마 |
| D-6 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | 4단 판정표 §8 |
| D-7 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | headerSource 필드 관리 절 |
| D-8 | 설계 | tools.md | `opal/core/references/tools.md` | code-scan CLI 사용법 |
| D-9 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md:171-174` | @header 규칙 — readonly 강제 서술 |
| D-10 | 기획 | 077 DONE.md / PLAN.md | `tasks/077-260727-opd-코드맵-헤더작성층/` | 선행 설계 결정 원본 |
| D-11 | 기획 | PLAN.md (본 태스크) | `tasks/080-260801-opd-헤더소스-단일화/PLAN.md` | 교차 검증 대상 (대조 절에서만 열람) |
| D-12 | brain | 3페이지 | `.opal/brain/pages/concept/*.md`, `.opal/brain/pages/entity/code-scan-tool.md` | 구계약 서술 여부 확인 |

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/code-scan/code-scan.js` | 조회 8커맨드 + 작성층 5서브명령(discover/scaffold/target/validate/feature) 전체 구현 | 예 — F-1~F-10 전량 | `code-scan.js:1-1774` |
| `opal/tools/code-scan/code-map-hook.js` | PostToolUse hook — `loadConfig`+`decideTarget`을 `main()` 우회하여 직접 호출 | 예 — F-2 게이트가 hook을 우회하지 않는지 확인 필요 | `code-map-hook.js:120,130` |
| `opal/tools/brain-tool/brain_tool.py` | `sync-header`가 `code-scan scan --json`을 subprocess로 호출, 실패 시 stderr만 detail로 전달 | 예 — F-12③ | `brain_tool.py:783-793` |
| `opal/tools/code-scan/tests/*.js` (8파일) | 기존 회귀 자산 | 예 — F-13 골든 재캡처 + headerSource 오버레이 확대 | `tests/test-resolve-header.js:74-83` |
| `opal/tools/code-scan/tests/fixtures/*/.opal/code-scan.json` (20개) | 테스트 픽스처 설정 | 예 — 전량 `headerSource` 부재 | 아래 §1.4 |
| `opal/core/references/header-standard.md` | 스키마 SSOT | 예 — F-11, `:219` 집합일치 서술 정정 | `header-standard.md:206,219` |
| `opal/core/references/harness/header-rules.md` | 4단 판정표 SSOT | 예 — F-11, `:26` readonly 행 제거 | `header-rules.md:20-26` |
| `opal/core/references/pm/code-scan-management.md` | headerSource 필드 관리·PM 절차 | 예 — F-11, `:73` 줄번호 정정 | `code-scan-management.md:63-75` |
| `opal/core/references/tools.md` | CLI 사용법 요약 | 예 — F-11, `:240` reason 4값 오기 정정 | `tools.md:240` |
| `opal/core/references/harness/pm-review-gate.md` | PM Gate 8번 절차 | 예 — F-11·F-12④ | (미열람, 절차 8번 텍스트 확인 필요) |
| `docs/CONVENTIONS.md` | @header 규칙 | 검토 필요 — readonly 강제 서술 | `docs/CONVENTIONS.md:174` (TASK/PLAN F-11 목록에 없음, 신규 발견) |

### 1.2 아키텍처 패턴

- **단일 CLI 파일 + `module.exports`** — `code-scan.js`는 Node 무의존 단일 파일이며, `require.main === module` 가드(`:1735`)로 CLI 실행과 라이브러리 임포트를 분리한다. 노출 심볼 10개(`:1739-1750`): `mirrorPathForDir, decideTarget, loadCodeMap, loadConfig, findProjectRoot, resolveScope, matchLayerRule, matchDomain, resolveHeader, extractHeader`.
- **커맨드 디스패치 테이블** — `main()`(`:1696-1733`)이 `--help`/`--version`을 `findProjectRoot`/`loadConfig` **이전**에 처리(`:1699-1700`)하고, 이후 13개 서브커맨드를 객체 리터럴 테이블(`:1705-1719`)로 디스패치한다. 게이트·전처리 로직을 넣을 유일한 공통 지점이다.
- **필터 판정 3유틸 + 4개소 분산 호출** — `patternToRegex`/`isExcluded`/`hasExcludedSegment`(`:219-252`)가 존재하지만, 이를 호출하는 지점은 열거(`discoverFiles`)·scaffold열거(`collectDirsWithCodeFiles`)·validate구조패스(`listCodeFilesInDir`)·`--changed`(`cmdValidate` changedMode) 4곳에 각각 분산되어 있고, **`decideTarget`(`target` 커맨드)은 이 유틸을 전혀 호출하지 않는다** — 배경분석 (4)가 지목한 "5개 판정 지점" 중 `target`은 현재 필터 자체가 없는 공백 지점이다.
- **fail-safe 계층 분리** — `code-scan.js` 자신은 에러 시 exit code + stderr(query 계열)를 쓰지만, `discover/scaffold/target/validate`는 `CodeMapFatalError` throw → `main()`의 try/catch(`:1727-1732`) → `codeMapErrorExit`(`:474`)로 JSON 에러 객체를 stdout에 출력하는 별도 계약을 쓴다. hook(`code-map-hook.js`)은 이와 무관하게 9단계 조기이탈(`:88-139`) + 최외곽 try/catch(`:152-157`)로 완전히 다른 fail-safe 계층을 갖는다.

### 1.3 의존성 맵

```
code-map-hook.js ──require──> code-scan.js (decideTarget, loadCodeMap, loadConfig, findProjectRoot)
                                  └─ main()을 거치지 않고 4개 함수를 직접 import (H-2 확인, 아래 §7)

brain_tool.py ──subprocess──> code-scan.js (scan --json, exit code + stdout만 소비)

tests/*.js (8파일) ──spawnSync──> code-scan.js (CLI 블랙박스, require는 test-resolve-header.js TS-008에서 1건)
```

- 순환 의존 없음. `code-map-hook.js`는 code-scan.js의 `main()`을 절대 거치지 않으므로, F-2(전 명령 차단 게이트)를 `main()` 안에만 넣으면 hook은 자동으로 그 게이트 밖에 남는다(TASK D-5 동반 필수 작업 ⑤와 정합).

### 1.4 테스트 현황

- 테스트 프레임워크: `node:test` + `node:assert/strict`, 8파일 2212줄, 정적 `test(` 호출 85건(TASK.md는 "100 케이스"로 서술 — 루프 생성 테스트(`GOLDEN_COMMANDS.forEach` 등) 포함 시 실행 시점 케이스 수가 더 많을 수 있어 완전히 배치되는 수치는 아님, 참고용 불일치).
- `headerSource` 키를 실제로 사용하는 테스트는 **`test-resolve-header.js` 1파일뿐**이다 (`grep -n headerSource tests/*.js` 결과 전량 이 파일). `test-target.js`/`test-scaffold.js`/`test-validate.js`/`test-hook.js`/`test-discover.js`/`test-feature.js` 6파일은 `headerSource` 언급 0건 — F-3(target)·F-4(scaffold)·F-5(validate)·F-9(검출기)가 요구하는 모드별 동작은 현재 전혀 테스트되지 않는다.
- 픽스처: `.opal/code-scan.json` 20개 전량 `headerSource` 키 부재(0/20). `index.json` 18개 중 17개가 `readonly` 키 보유.
- 골든 자산 8개(`tests/fixtures/golden/*`)는 `legacy-repo` 픽스처(코드맵 없음, `.opal/code-scan.json`에도 `headerSource` 키 없음) 대상 8커맨드(`scan --json`/`domain`/`layer`/`search auth --json`/`exports token --json`/`summary`/`depends auth_service`/`missing`) 바이트 동일성 검증(`test-regression.js:64-83`).
- `test-resolve-header.js:74-83`에 이미 "픽스처를 임시 디렉토리에 복제 후 `.opal/code-scan.json`에 `headerSource` 값을 실기재"하는 오버레이 헬퍼(`makeHeaderSourceFixture`)가 존재 — F-13 재캡처·F-7 정규화 테스트가 재사용 가능한 기존 자산.

## 2. 외부 조사 결과

해당 없음 — 순수 내부 도구(Node.js 표준 모듈만 사용, 외부 라이브러리 없음). context7/WebSearch 조사 불필요.

## 3. 영향 범위

### 3.1 직접 영향

- `code-scan.js`: `loadConfig`(스키마+게이트), `main()`(게이트 삽입), `decideTarget`(F-3), `cmdScaffold`(F-4), `cmdValidate`(F-5+F-9), `resolveScope`(F-10), `inferScopes`(F-7), `loadCodeMap`의 스키마 검증부(F-7), 신설 `isInScope`(F-8) — 함수 8~9개 변경/신설.
- 5문서(`header-standard.md`/`header-rules.md`/`code-scan-management.md`/`pm-review-gate.md`/`tools.md`) 갱신.
- `tests/fixtures/**/.opal/code-scan.json` 20개 전량에 `headerSource` 추가 필요(F-13, D-4 부재 확인 완료).
- 이 저장소 자신의 `.opal/code-scan.json`(F-12①) — 확인 결과 `headerSource` 키가 아직 없고, `git check-ignore`로 이 파일이 `.gitignore:2`(`.opal/*`) 규칙에 의해 추적 제외 대상임을 확인(§5 리스크 참조).

### 3.2 간접 영향

- `code-map-hook.js` — F-2 게이트가 `main()` 내부에만 존재하면 hook은 영향받지 않는다(§1.3 확인). 단, hook이 `decideTarget`을 직접 호출하므로 F-3(decideTarget의 headerSource 우선순위 변경)의 결과 스키마가 바뀌면 hook의 `buildWarning`/`isManifestEntryClean` 로직도 회귀 확인이 필요하다.
- `brain_tool.py` `_load_code_scan_json`(`:766-793`) — `result.returncode != 0`이면 `stderr`만 `detail`에 담아 `header_parse_failed`를 반환한다(`:788-790`). 신규 `header_source_unset` 에러가 stdout JSON으로만 실려 오고 stderr가 비어 있으면, brain-tool은 실제 실패 사유를 드러내지 못하고 `detail: "code-scan exit=1, stderr="`(빈 문자열)를 반환할 위험이 있다 — F-12③이 명시적으로 다뤄야 할 지점.
- `docs/CONVENTIONS.md:174` — "읽기 전용 스코프는 code-map 강제"라는 서술이 `readonly` 존재를 전제한다. TASK/PLAN의 F-11 문서 목록(5문서)에는 이 파일이 없다 — 누락 가능성(§5).
- brain 3페이지(`.opal/brain/pages/concept/*.md`, `entity/code-scan-tool.md`) — 구계약(5단 상속·`readonly` 4단 판정) 서술. 소유자 승인에 따라 CLOSE 후 갱신 대상(§8).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — `.opal/code-scan.json` 스키마(`headerSource` 2값 강제, `scopes` 객체 형식), `decideTarget`/`cmdValidate` 반환 스키마 변경
- [x] 설정/환경변수 변경 — `.opal/code-scan.json`(`headerSource` 필수화), `.opal/code-map/index.json`(`readonly` deprecated)
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음

## 4. 핵심 발견 사항

1. **`headerSource`는 정말로 조회 경로(`resolveHeader`) 1곳에서만 소비된다.** `decideTarget`·`cmdScaffold`·`cmdValidate`는 모드 문자열을 아예 참조하지 않으므로, F-3/F-4/F-5는 "기존 로직 수정"이 아니라 "신규 분기 추가"에 가깝다(`code-scan.js:690-699` vs `:755-791`).
2. **`readonly`는 실질적으로 코드 편집을 막지 않는다.** 유일한 효력은 `decideTarget`이 `write_to: manifest`를 반환하는 것(`:761-762`)뿐이며, 이는 스코프 단위 `headerSource: manifest`와 동치다 — D-2(제거+하위호환) 방향이 코드 근거로 뒷받침된다.
3. **필터 적용 지점은 현재 4곳이지 5곳이 아니다.** `isExcluded` 호출은 `discoverFiles`(`:312`)·`collectDirsWithCodeFiles`(`:1236`)·`listCodeFilesInDir`(`:1441`)·`cmdValidate --changed`(`:1475`) 4곳뿐이고, `decideTarget`(target 커맨드)은 어떤 exclude 필터도 거치지 않는다. F-8이 "5개 지점 통합"을 목표로 한다면, target은 신규로 필터를 추가하는 작업이지 기존 호출을 대체하는 작업이 아니다.
4. **`codemap-repo` 픽스처 기반 5단 상속 테스트 6건은 `auto` 제거와 구조적으로 충돌한다.** `resolveHeader`(`:693,699`)의 분기 구조상 `headerSource:"manifest"`에서는 인라인이 아예 추출되지 않고(`:693`), `headerSource:"inline"`에서는 매니페스트가 아예 조회되지 않는다(`:699`) — 즉 "한 파일은 인라인 단독 승리, 다른 파일은 매니페스트 4단 각각 단독 승리"를 **하나의 scan 실행**으로 동시에 보여주는 현재 TS-004(5케이스)·TS-005(S-6 혼재 승리) 구조는 2값 체계에서 재현 불가능하다(§7 R-10/N-4 상세).
5. **hook은 게이트 설계상 자동으로 안전하다.** `code-map-hook.js:120`이 `main()`을 거치지 않고 `loadConfig`를 직접 호출하므로(H-2 확인), F-2 게이트를 `main()` 내부에 두면 추가 조치 없이 hook의 fail-safe 계약(TASK D-5 동반 필수 작업 ⑤)이 유지된다.
6. **brain_tool.py의 실패 사유 전달 경로가 stderr 우선이다.** 신규 `header_source_unset` 에러가 (기존 `codeMapErrorExit` 관례대로) stdout JSON으로만 나가면, `brain_tool.py:788-790`은 빈 stderr를 detail로 넘겨 실제 원인을 감춘다 — F-12③은 단순 "확인"이 아니라 코드 수정(stdout도 detail에 포함)이 필요할 수 있다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-1 | `codemap-repo` 기반 6개 테스트(TS-004 5케이스+TS-005)가 `auto` 제거 후 동일한 "단일 scan에서 5-tier 전부 관찰" 구조를 유지할 수 없다 | 높음 | `code-scan.js:690-699`, `test-resolve-header.js:176-262` |
| R-2 | `brain_tool.py`가 stdout이 아닌 stderr를 detail 소스로 사용해 `header_source_unset` 실패 사유를 놓칠 수 있다 | 중간 | `brain_tool.py:788-790` |
| R-3 | 이 저장소의 `.opal/code-scan.json`이 `.gitignore:2`(`.opal/*`)에 의해 추적 제외 상태 — F-12①에서 `headerSource: inline`을 추가해도 git에 커밋되지 않아, 클론 직후 신규 환경에서는 이 파일이 아예 없다(→ 즉시 `header_source_unset`으로 전 명령 차단) | 높음 | `git check-ignore -v .opal/code-scan.json` → `.gitignore:2` 매치, exit 0 |
| R-4 | `docs/CONVENTIONS.md:174`가 "읽기 전용 스코프는 code-map 강제"로 `readonly` 존재를 전제 서술하나 F-11 문서 갱신 목록(5문서)에 포함되어 있지 않다 | 중간 | `docs/CONVENTIONS.md:174`, TASK.md F-11 |
| R-5 | `tools.md:240`의 target 커맨드 주석이 `reason` 4값을 `inline_exists/readonly_repo/legacy_no_header/manifest`로 잘못 나열(`manifest`는 `write_to` 값이지 `reason` 값이 아니며, 실제 4값 중 `new_file`이 누락) | 낮음(문서만) | `tools.md:240` vs `header-rules.md:20-26`, `code-scan.js:762,773,776,790` |
| R-6 | `code-scan-management.md:73`의 코드 인용(`code-scan.js:187-190`)이 실제 위치(`:198-201`)와 11줄 어긋남 | 낮음(문서만) | `code-scan-management.md:73` vs `code-scan.js:198-201` |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어/런타임 | Node.js (표준 모듈만, 외부 npm 의존 없음) | — |
| 대상 도구 | code-scan.js | v1.3.3 |
| 테스트 | `node:test` + `node:assert/strict` | Node 내장 |
| 문서 | Markdown (규칙 SSOT 5문서 + CONVENTIONS 1건) | — |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan (이미 PLAN.md 존재) | 본 태스크는 PLAN이 선행 완료 상태 — 신규 추천 불필요 |

### 6.3 추천 MCP

해당 없음 — 순수 내부 Node.js CLI 분석으로 외부 라이브러리 문서 조회 불필요.

## 7. 교차 검증 — V-1 ~ V-12

| # | 검증할 사실 | 판정 | 근거 |
|---|-----------|------|------|
| V-1 | `headerSource` 소비 지점이 `resolveHeader` 1곳뿐인가 | **확인** | `code-scan.js:690,693,699` 3줄만 실사용. `:45,108`은 기본값 상수, `:198-208`은 스키마 로딩(값 검증만, 소비 아님), `:1757`은 변경이력 주석 |
| V-2 | `readonly` 참조 지점이 `:761`·`:1098`·`:1107` 3곳 + "그 외 없음"인가 | **부분 반증** | 3곳은 정확하나, `:1199`에 `discover` 산출물의 `note` 문자열("readonly/anchors/stripPrefix 확인...")이 추가로 존재 — 필드 소비는 아니지만 `readonly`를 언급하는 4번째 코드 지점 |
| V-3 | 파일 집합 판정 지점 개수·위치 | **확인 (5곳 중 4곳만 필터 적용, target은 무필터)** | `discoverFiles`(`:312`)·`collectDirsWithCodeFiles`(`:1236`)·`listCodeFilesInDir`(`:1441`)·`cmdValidate --changed`(`:1475`) 4곳이 `isExcluded` 호출, `decideTarget`(target)은 호출 0건 |
| V-4 | 3개 패턴 유틸 시그니처·호출 지점 전량 | **확인** | `patternToRegex(pattern)`(`:219`, 호출 `:236,660,675`) / `isExcluded(relPath,fileName,patterns)`(`:234`, 호출 `:312,1236,1441,1475`) / `hasExcludedSegment(relPath,excludeDirs)`(`:250`, 호출 `:1434,1474`) |
| V-5 | `loadConfig` 종료 경로 + hook의 호출 방식 | **확인** | `loadConfig`(`:193-213`)는 `process.exit`/`throw` 없음(파싱 실패 시 `DEFAULT_CONFIG` 반환). `code-map-hook.js:120`이 `main()`을 거치지 않고 직접 호출 |
| V-6 | `main()` 디스패치 구조 + `--help`/`--version` 위치 | **확인** | `--help`/`--version`이 `findProjectRoot`/`loadConfig` **이전**(`:1699-1700`)에 처리, 이후 13커맨드 테이블 디스패치(`:1705-1725`), try/catch로 `CodeMapFatalError`만 별도 처리(`:1727-1732`) |
| V-7 | 픽스처 `.opal/code-scan.json` 개수·`headerSource`/`readonly` 보유 현황 | **확인** | 20개 전량 `headerSource` 부재(0/20). `readonly`는 `code-scan.json`에는 0건(스키마상 별개 파일 소관), `index.json` 18개 중 17개 보유 |
| V-8 | 골든 자산 파일 목록·캡처 커맨드·조건 | **확인** | `tests/fixtures/golden/*` 8파일, `legacy-repo`(코드맵 없음+`headerSource` 키도 없음) 대상 8커맨드(`test-regression.js:64-72`) |
| V-9 | `brain_tool.py`가 실패를 어떻게 전달하는가 | **확인 (위험 동반)** | `result.returncode`(exit code) 우선 검사 후 `stderr`를 `detail`에 담음(`:788-790`), stdout은 성공 시에만 JSON 파싱 — stdout 전용 에러 포맷과 상충 위험(§5 R-2) |
| V-10 | `module.exports` 노출 심볼 목록 | **확인** | `mirrorPathForDir, decideTarget, loadCodeMap, loadConfig, findProjectRoot, resolveScope, matchLayerRule, matchDomain, resolveHeader, extractHeader` 10개(`:1739-1750`), 인라인 `@header.exports`(`:8`)와 완전 일치 |
| V-11 | TASK.md 줄번호 스냅샷 9건 현재 코드 일치 여부 | **부분 반증** | `decideTarget`은 `:755-791`(TASK 서술 `:755-792`는 함수 종료 후 공백줄까지 포함해 1줄 초과), `files_key_removed`는 `:1597`(TASK §보강②의 `:1582`는 그 앞 필터 병합 줄이지 실제 위반 push 줄이 아님). 나머지(`:690-699`,`:557-569`,`:761`,`:1098`,`:1107`) 일치 |
| V-12 | `.opal/code-scan.json`이 gitignore 대상인가 | **확인** | `git check-ignore -v .opal/code-scan.json` → `.gitignore:2:.opal/*  .opal/code-scan.json`, exit 0(무시됨) |

## 8. PLAN.md 대조 결과

> 아래는 §7의 코드 확인 결과를 PLAN.md 서술과 대조한 것이다. **반증(코드와 다름) 항목을 먼저 제시한다.**

### 8.1 반증된 항목

- **§11.1 줄번호 교정** — PLAN의 교정 방향(`decideTarget :755-791`, `files_key_removed :1597`, `readonly` 참조에 `cmdDiscover` note `:1199` 추가)은 **코드로 확인된다**(V-11, V-2). 즉 이 항목은 "PLAN이 TASK.md의 원 서술을 코드 근거로 올바르게 교정했다"는 뜻이며, PLAN 자체가 반증되는 것이 아니라 TASK.md 원문이 반증된다.
- 그 외 PLAN의 핵심 구조적 주장(§11.2 M-1~M-4, H-2, F-8의 5지점 중 target 공백)은 모두 코드로 **확인**되었다(아래 8.2). 코드와 명백히 어긋나는 PLAN 주장은 발견되지 않았다.

### 8.2 확인된 항목

| PLAN 주장 | 판정 | 근거 |
|-----------|------|------|
| M-1 `code-scan-management.md:73`의 `code-scan.js:187-190` 인용이 stale | **확인** | 실제 위치는 `:198-201` (11줄 어긋남) |
| M-2 `tools.md:240` reason 4값 오기 | **확인** | 실제 나열이 `inline_exists/readonly_repo/legacy_no_header/manifest` — `manifest`는 `write_to` 값이지 `reason`이 아니고, 진짜 4번째 `reason`인 `new_file`이 빠짐 |
| M-3 `header-standard.md:219` "집합 일치" 서술이 include/exclude 도입 시 깨짐 | **확인** | `:219` "키는 `dir` 실제 파일 목록과 집합 일치" — include 필터링 도입 시 부분집합이 정상이 되어 이 문장이 거짓이 됨 |
| M-4 `header-rules.md:26` readonly 행 제거 필요 | **확인** | `:26`이 "① 소속 스코프의 `readonly === true` → manifest/readonly_repo" 행 그 자체 |
| N-3 픽스처 20종 전량 `headerSource` 부재 | **확인** | §7 V-7 |
| N-5 `buildCtx` 호출 6곳 | **정밀 반증 (5곳)** | `buildCtx(` 문자열 출현은 정의 1곳(`:535`) + 호출 5곳(`:799,1161,1314,1400,1449`) = 총 6줄이지만, **실제 호출(call site)은 5곳**이다. `cmdFeature`는 `scanHeaders`→`scanAll`을 경유하므로 `buildCtx`를 직접 호출하지 않는다(간접 경유, `:799`에 이미 포함됨). "6곳"이 grep 총 라인수 기준이면 정확하고 "호출 지점" 기준이면 1개 과다 — 인용 정밀도 이슈로만 기재 |
| N-1 (추정) gitignore | **확인 + 위험 확대** | `.opal/code-scan.json`이 gitignore 대상(V-12) — 단순 "사실 확인"을 넘어, F-12①(이 저장소에 `headerSource` 추가) 자체가 커밋되지 않는 파일에 대한 조치이므로 신규 clone 환경에서는 즉시 `header_source_unset`이 재발한다는 점을 R-3으로 별도 상향 기재함(§5) |
| H-2 hook이 `main()` 우회, `loadConfig` 직접 호출(`code-map-hook.js:120`) | **확인** | §7 V-5, 정확히 `:120`에서 `loadConfig(projectRoot)` 직접 호출 |
| F-8 5개 적용 지점 중 target이 현재 무필터 | **확인** | §7 V-3, V-4 — `decideTarget`은 `isExcluded`/`hasExcludedSegment` 호출 0건 |

### 8.3 판단보류

- §1.5 제약② 파기표의 "077 계약" 열이 v1.3.3 동작과 일치하는지는 PLAN.md 본문의 표 형태(파기표)를 직접 대조해야 하나, 본 산출물에서는 077 계약 자체(5단 상속·`readonly` 4단 판정·필터 4지점)가 코드와 일치함을 §7에서 개별 확인했다 — 표 전체 셀 단위 대조는 지면상 생략, 개별 셀은 위 항목들로 커버됨.

## 9. R-10 / N-4 — `codemap-repo` 픽스처 재배치 실현 가능성 판정

**판정: 부분 실현 가능 — 완전한 "이동"은 불가능하고, 테스트 그룹별로 다른 조치가 필요하다.**

### 근거

`resolveHeader`(`code-scan.js:688-751`)의 분기 구조가 결정적이다:

```
:693  if (headerSource !== 'manifest') { inline = extractHeader(filePath); }   // manifest 모드 → inline 절대 미추출
:699  if (!ctx.codeMap.present || headerSource === 'inline') { return inline; } // inline 모드 → 매니페스트 절대 미조회
```

2값 체계에서는 "인라인과 매니페스트 4-tier(file/package/rule/domain)가 같은 scan 실행 안에서 파일별로 다르게 관찰되는" 현재 `codemap-repo` 기반 테스트 구조가 원천적으로 재현 불가능하다. `test-resolve-header.js`의 직접 사용 지점(오버레이 미경유, `:177,188,202,214,228,245,270,408,425`)을 유형별로 나누면:

| 그룹 | 테스트 | 재배치 가능성 | 이유 |
|------|--------|-------------|------|
| A. tier②~⑤ 단독 (file/package/rule/domain) | TS-004 중 OrderService.java(file)/ShipRepo.java(package)/AdminGuard.tsx(rule)/OrderMisc.java(domain) 4케이스(`:187-238`), TS-007(readonly 스코프 file tier, `:269-285`), S-20 depends(`:424-434`) | **가능** | `headerSource:"manifest"` 오버레이(기존 `makeHeaderSourceFixture` 헬퍼 재사용, `:74-83`) 하에서 이 4개 파일은 애초에 인라인이 없으므로 결과가 동일하게 재현된다 |
| B. tier① inline 단독 (인라인만 있고 매니페스트 엔트리는 없는 경우) | TS-004 중 AdminHome.tsx `_source:inline` 케이스(`:176-185`)의 **순수 inline 단독 성립 의미** | **가능(형태 변경 필요)** | `headerSource:"inline"` 오버레이로 재현 가능하나, 이 모드에서는 매니페스트를 애초에 조회하지 않으므로 "5-tier 중 inline이 이겼다"가 아니라 "inline 모드이므로 매니페스트를 보지 않았다"는 다른 명제가 된다 |
| C. 혼재 파일 인라인 승리(양쪽 소스 모두 존재, 병합 없이 인라인 승리) | TS-004의 AdminHome.tsx(같은 파일이 매니페스트에도 `ManifestOnlyExport` 엔트리 보유), TS-005 전체(`:244-262`) | **불가능 (동일 의미로는)** | 이 테스트가 검증하는 불변식은 "두 소스가 공존할 때 우선순위 규칙이 적용되고 조용히 병합되지 않는다"이다. 2값 체계에서는 `headerSource:"inline"` 모드가 매니페스트를 아예 읽지 않으므로 "병합 안 됨"이 "비교 자체를 안 함"으로 격하된다 — 더 약한 명제이며 같은 리스크(과거 결함처럼 두 소스가 조용히 섞이는 사고)를 더 이상 이 테스트가 방어하지 못한다 |

### 결론

- 재배치는 **"오버레이 헬퍼를 그룹 A/B에 적용"**하는 선에서 실행 가능하다(N-3/N-5와 동일한 이미 존재하는 인프라 재사용, PLAN.md가 이미 지목한 방향과 일치).
- 그러나 **그룹 C(TS-005, TS-004의 AdminHome.tsx tier① 케이스)는 "재배치"가 아니라 "폐기 또는 재정의"가 필요하다.** 이는 PLAN.md가 아직 결정하지 않은 것으로 보이는 지점이며(디스패치 프롬프트가 "유일하게 열려 있는 P1 설계 빈틈"이라 명시한 것과 일치), 두 가지 옵션이 있다:
  1. **폐기**: 혼재 공존 시나리오 자체가 D-3(2택)에서 발생 불가능해지므로, 이 불변식을 지키는 테스트를 삭제하고 변경이력에 "auto 제거로 무의미해진 테스트 삭제"를 기록한다.
  2. **재정의**: "다른 모드로 설정된 파일이 실수로 반대 소스 필드를 노출하지 않는다"는 더 약한 명제로 다시 작성한다(이미 TS-044/TS-045가 사실상 이 약한 명제를 담당하고 있어 중복 가능성 있음 — PLAN이 TS-044/045/005의 관계를 재정리해야 함).
- 어느 쪽이든 **픽스처 자체(`codemap-repo/index.json`, 5개 파일의 tier 배치)는 손대지 않고 테스트 코드만 재배치/재정의하면 되므로, 픽스처 재작성은 불필요하다** — 이는 PLAN이 지목한 우려보다 작업 범위가 좁을 수 있음을 시사한다.

## 10. PLAN이 놓친 위험·누락

- **R-3(§5)**: `.opal/code-scan.json`이 gitignore 대상이라는 사실(N-1)을 PLAN이 이미 지목했으나, 이로 인해 F-12①(이 저장소 설정 추가)이 "커밋되지 않는 로컬 전용 조치"가 된다는 파급까지는 다뤄지지 않은 것으로 보인다 — 신규 clone·CI 환경에서 이 저장소 자체가 즉시 `header_source_unset`으로 막히는 시나리오에 대한 대응(예: `.gitignore`에 `!.opal/code-scan.json` 예외 추가 여부 결정)이 F-12 범위에 명시적으로 필요하다.
- **R-2(§5)**: `brain_tool.py`의 stderr 우선 에러 전달 구조(V-9)는 F-12③이 "확인"만으로 끝나지 않고 코드 수정(stdout도 detail 후보로 포함)이 필요할 가능성을 시사한다.
- **R-4(§5)**: `docs/CONVENTIONS.md:174`의 readonly 전제 서술이 F-11 문서 갱신 목록(5문서)에 없다 — 6번째 갱신 대상 후보로 고려 필요.
- **N-5 인용 정밀도**: "buildCtx 호출 6곳"은 grep 총 라인 수(정의+호출)이지 실제 호출 지점 수(5)가 아니다 — F-8 설계에서 "호출 지점 개수"를 근거로 쓸 경우 5로 정정 필요.

## 11. brain 3페이지와 현행 코드의 어긋남

| 페이지 | 서술 | 현행 코드와의 어긋남 |
|--------|------|-------------------|
| `concept/code-header-dual-source-inheritance.md` | "인라인이 하나라도 존재하는 파일은 인라인 값만 채택"(5단 상속, `auto` 암묵 전제) | D-3(`auto` 완전 제거)이 적용되면 이 페이지가 서술하는 "5단 상속 자동 병합 회피" 메커니즘 자체가 `headerSource:"manifest"` 모드에서는 무의미해진다(인라인을 아예 안 읽으므로 "인라인이 이긴다"는 명제 자체가 성립할 상황이 없음) — CLOSE 후 전면 재서술 필요 |
| `concept/code-map-write-location-decision.md` | "① 소속 영역이 읽기전용으로 지정됨 → 외부 지도"(4단 판정, `readonly` 1순위 조건) | F-6(`readonly` 제거 → `headerSource`로 통합)이 반영되면 이 표의 조건①이 사라지고 `headerSource: manifest` 스코프 오버레이로 대체됨 — 표 전체 재작성 필요 |
| `entity/code-scan-tool.md` | 소스 커버리지 표의 줄번호 인용(`:506,573,688,755,1448`) | **어긋남 없음** — 전량 현재 코드와 정확히 일치(별도 검증). 단 "5단 상속 해석기"(`:67`)·"기록 위치 4단 판정"(`:68`) 설명 문구는 위 두 concept 페이지와 동일하게 구계약 반영 — 갱신 필요 |

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-08-01 | 초판 — op-dev-analysis 표준 산출물 + PLAN.md 독립 교차 검증(V-1~V-12, R-10/N-4 판정) |
