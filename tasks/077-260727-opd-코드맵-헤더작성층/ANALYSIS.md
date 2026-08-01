# ANALYSIS: 코드 헤더 작성층 신설 — 인라인 + 외부 code-map 2소스

> 작성일: 2026-07-28
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 헤더 해석 단일 지점·8커맨드·config 로더 — 전량 626줄 Read 완료 |
| D-2 | 설계 | header-standard.md | `opal/core/references/header-standard.md` | 필드 정의·layer 표준값·언어별 주석 포맷·삽입 위치 규칙 |
| D-3 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | 현행 작성 규칙·"별도 도구 없음"·빈 결과 폴백 3분기 |
| D-4 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | code-scan.json PM 관리 의무·추론 소스 3종 |
| D-5 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | PM Gate 8·14번 항목 @header 검증 절차 |
| D-6 | 소스 | brain-tool README | `opal/tools/brain-tool/README.md` | `sync-header` 단방향 계약(:15) |
| D-7 | 설계 | brain entity 템플릿 | `opal/tools/brain-tool/templates/page-entity.md` | 현행 자산의 구조축 한정(기능축 키 부재) |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §8.6 정책·IA 토큰 체계(조인 키 설계 근거) |
| D-9 | 기획 | 076 태스크 | `tasks/076-260723-opds-todo미러-hook자동화/` | 산문→hook 강제 전환 선례·멱등 upsert 패턴 |
| D-10 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py:766-854` | `sync-header`가 code-scan `--json`을 소비하는 실제 경로 |
| D-11 | 소스 | todo_mirror_hook.py | `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse hook 선례 구현(입력 계약·fail-safe 패턴) |
| D-12 | 소스 | claude-hooks.json | `opal/core/hooks/claude-hooks.json` | hook 등록 스키마(matcher·command) — 배포 소스 |
| D-13 | 소스 | install-mac.sh | `scripts/install-mac.sh:180-187,1212-1219` | hook 배선 지점 — `merge_hooks_config()` 호출 위치 |
| D-14 | 소스 | test_todo_mirror_hook.py | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | hook 테스트 컨벤션(Python unittest+subprocess) |
| D-15 | 소스 | skill-registry tests | `opal/tools/skill-registry/tests/test-validate.js` 외 2건 | 유일한 순수 Node.js 도구 테스트 컨벤션(RED-first) |
| D-16 | 소스 | tool-scan manifest | `opal/tools/tool-scan/manifest.json:51-65` | code-scan capability 등록 항목(`when` 키워드) |
| D-17 | 소스 | .gitignore | `.gitignore:2-4` | `.opal/*` 무시 + `!.opal/brain/**` 예외 선례 |
| D-18 | 소스 | tool-scan tests/fixtures | `opal/tools/tool-scan/tests/fixtures/` | 저장소 내 정적 픽스처 배치 선례 |
| D-19 | 문서 | PROJECT.md | `docs/PROJECT.md` §프로젝트 구성(:158) | Framework 스코프 = `opal/`, `skills/`, `agents/` (code-scan.json scopes 추론 소스) |
| D-20 | 설계 | opal-doc-standard 변경이력 규칙 | `docs/CONVENTIONS.md` §변경이력 작성 의무 | F-11 SSOT 5문서 갱신 형식 근거 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조. 이 태스크는 전량 저장소 내부 근거만 사용한다(외부 저장소 인용 금지 — 태스크 Guards).

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/code-scan/code-scan.js` | 헤더 스캐너 본체 — 626줄, 8커맨드 + config 로더 + 헤더 파서 | 예 — 5단 해석기 신설·4서브명령 추가·`headerSource` 스위치 | `opal/tools/code-scan/code-scan.js:1-627` |
| `opal/core/references/header-standard.md` | @header 필드·layer 표준값·언어별 포맷 SSOT | 예 — 2소스 표현 절(index.json/매니페스트 스키마) 신설 | `opal/core/references/header-standard.md:1-189` |
| `opal/core/references/harness/header-rules.md` | EXECUTE 단계 작성 규칙 SSOT | 예 — "별도 도구 없음" 문구 교체, 4단 판정·3단 시점 반영 | `opal/core/references/harness/header-rules.md:12,27,44,53` |
| `opal/core/references/pm/code-scan-management.md` | code-scan.json PM 관리 의무 | 예 — `headerSource` 필드 추론 규칙 추가 여지 | `opal/core/references/pm/code-scan-management.md:1-68` |
| `opal/core/references/harness/pm-review-gate.md` | PM Gate 8·14번 @header 검증 절차 | 예 — 커버리지 합산·워커 권한 경계 반영 | `opal/core/references/harness/pm-review-gate.md:52-56,89-94` |
| `opal/core/references/tools.md` | code-scan 도구 레지스트리 항목 | 예 — 신규 서브명령 커맨드 표 갱신 | `opal/core/references/tools.md:202-289` |
| `opal/tools/tool-scan/manifest.json` | code-scan capability 등록 | 예 — `when` 키워드에 discover/scaffold/target/validate/feature 추가 | `opal/tools/tool-scan/manifest.json:51-65` |
| `opal/tools/brain-tool/brain_tool.py` | `sync-header` 커맨드 — code-scan `--json` 소비 | 불필요 — `_source` 필드는 무해 통과(§4 근거) | `opal/tools/brain-tool/brain_tool.py:766-854` |
| `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse hook 구현 선례 | 참조만 — code-scan hook은 별도 파일(Node.js)로 신설 | `opal/tools/state-tool/todo_mirror_hook.py:1-131` |
| `opal/core/hooks/claude-hooks.json` | Claude Code hooks 배포 소스 | 예 — 신규 hook 엔트리 추가(배열 additive) | `opal/core/hooks/claude-hooks.json:1-11` |
| `scripts/install-mac.sh` | hook 배선(`merge_hooks_config`) | 불필요 — 기존 배선이 `claude-hooks.json` 전체를 그대로 merge하므로 신규 엔트리는 소스에만 추가하면 자동 배포됨 | `scripts/install-mac.sh:1212-1219` |
| `.gitignore` | `.opal/*` 무시 + brain 예외 | 예 — `.opal/code-map/` 추적 예외 추가 | `.gitignore:2-4` |
| `opal/tools/code-scan/tests/` (신설) | RED-first 단위 테스트 | 신규 — 현재 디렉토리 자체가 부재 | (부재 — §1.4 확인) |

### 1.2 아키텍처 패턴

- 단일 해석 지점 패턴: `extractHeader(filePath)`(`opal/tools/code-scan/code-scan.js:274-312`)가 파일 1개를 받아 헤더 JSON 또는 `null`을 반환하는 순수 함수이고, 상위 8커맨드는 전부 `scanAll`(`:318-333`)을 경유해 이 함수 하나만 호출한다. `scanAll`은 `discoverFiles`(`:242-258`)가 반환한 파일 목록을 순회하며 `extractHeader(f)`(`:324`)를 호출해 `{path, file, header}` 형태로 `withHeader`/`noHeader` 두 배열에 분류한다.
- 소비자 단일화: `scanHeaders`(`:335-342`)가 `scanAll`을 감싸 domain/layer 필터를 적용하고, `cmdScan`(`:390`)/`cmdDomain`(`:394`)/`cmdLayer`(`:421`)/`cmdSearch`(`:447`)/`cmdExports`(`:470`)/`cmdSummary`(`:496`)/`cmdDepends`(`:524`) 7개 커맨드가 모두 `scanHeaders`를 호출하고, `cmdMissing`(`:577`)만 `scanAll`을 직접 호출한다 — 즉 8커맨드 전부가 `scanAll`을 통과하며, `scanAll` 내부의 `extractHeader` 호출 지점(`:324`) 단 하나가 전체 도구의 유일한 헤더 해석 진입점이다.
- 출력 계층의 필드 불가지성: `fmtBrief`(`:348-361`)/`fmtFull`(`:363-370`)/`fmtJson`(`:372-376`)은 `header` 객체의 특정 필드(`layer`/`description`/`domain`)만 선택적으로 꺼내 쓰거나(`fmtBrief`), 객체 전체를 `JSON.stringify`로 그대로 출력한다(`fmtFull`/`fmtJson`). 어떤 출력 함수도 `header` 객체의 키 목록을 사전 검증하지 않는다.
- 바이패스 패턴: `cmdSummary`(`:496-522`)와 `cmdDepends`(`:524-575`)는 공용 `output()`/`fmtBrief`/`fmtFull`/`fmtJson`(`:378-384`)을 거치지 않고 자체 `console.log` 포맷팅을 한다 — 이는 신규 4서브명령(discover/scaffold/target/validate)이 공용 출력 계층을 우회하고 전용 포맷을 갖는 것이 기존 관례에 부합함을 보여주는 선례다.
- 설정 로더 단일화: `loadConfig(projectRoot)`(`:150-164`)가 `.opal/code-scan.json`을 읽어 `{extensions, exclude, excludePatterns, scopes}` 정확히 4개 키를 가진 객체를 반환한다(`:155-160`). 5번째 키를 추가하는 것은 기존 소비자 코드가 이 4개 키만 구조분해하지 않으므로(전체 `config` 객체를 그대로 넘겨 다님) 하위호환이다.
- 프로젝트 루트 탐지 패턴: `findProjectRoot()`(`:136-148`)는 `.git` 또는 `.opal` 또는 `CLAUDE.md`가 있는 디렉토리까지 상위로 걸어 올라간다. `.opal` 조건이 있으므로, 자체 `.opal/` 마커를 가진 하위 트리(예: 합성 픽스처 루트)는 실제 프로젝트 루트 판정에서 독립적으로 자기 자신을 프로젝트 루트로 인식한다(§4 핵심 발견 참조).

### 1.3 의존성 맵

```
main() (:593-619)
 - parseArgs(argv) (:95-130)              CLI 파싱, command/commandArg/옵션 추출
 - findProjectRoot() (:136-148)           .git/.opal/CLAUDE.md 탐지
 - loadConfig(projectRoot) (:150-164)     .opal/code-scan.json 로드
 - commands[opts.command](...) (:602-611) 디스패치 테이블(8엔트리, flat map)
     cmdScan (:390)     -> scanHeaders -> scanAll -> discoverFiles -> extractHeader
     cmdDomain (:394)   -> scanHeaders -> scanAll -> discoverFiles -> extractHeader
     cmdLayer (:421)    -> scanHeaders -> scanAll -> discoverFiles -> extractHeader
     cmdSearch (:447)   -> scanHeaders -> scanAll -> discoverFiles -> extractHeader
     cmdExports (:470)  -> scanHeaders -> scanAll -> discoverFiles -> extractHeader
     cmdSummary (:496)  -> scanHeaders -> scanAll -> discoverFiles -> extractHeader
     cmdDepends (:524)  -> scanHeaders -> scanAll -> discoverFiles -> extractHeader
     cmdMissing (:577)  -> scanAll(직접) -> discoverFiles -> extractHeader

discoverFiles (:242-258)
 - getSearchPaths (:223-240) opts.scope > opts.targetPath > config.scopes 값들 > projectRoot 폴백
 - walkDir (:202-221)        재귀 디렉토리 순회, config.exclude(이름 매칭)·config.extensions(확장자) 필터
 - isExcluded / mergeExcludePatterns / patternToRegex (:170-196) excludePatterns 매칭

extractHeader (:274-312)
 - readFileHead (:264-272) 파일 첫 8192바이트만 읽음(HEADER_READ_BYTES:27)
 - (내부) @header 탐지 -> 중괄호 균형 매칭(문자열 인식) -> JSON.parse (직접 또는 주석 접두 제거 후)
```

- brain-tool 소비 경로: `opal/tools/brain-tool/brain_tool.py:786-793`가 `node code-scan.js scan --json`을 subprocess로 실행해 `{relpath: header}` 맵을 얻고(`_load_code_scan_json`, `:766-798`), `cmd_sync_header`(`:801-854`)가 entity 페이지 frontmatter의 `module/layer/domain/exports` 4개 필드만(`:839`) 비교·갱신한다. `--scope` 인자 없이 호출하므로 `.opal/code-scan.json`에 정의된 전체 scope를 순회한다(`getSearchPaths:236-239`).
- 외부 패키지 의존성: 없음. `code-scan.js:19-20`이 `fs`/`path` 표준 모듈만 require — TASK.md 기술 스택 표(:107 "무의존")와 일치.
- 순환 의존성: 없음 — 단방향 파이프라인(parseArgs→config→discover→extract→format).

### 1.4 테스트 현황

- `opal/tools/code-scan/` 디렉토리 실태: `code-scan.js` 단일 파일만 존재하며 `tests/` 하위 디렉토리 자체가 없다(디렉토리 리스팅으로 확인). code-scan 테스트는 0건이다.
- `scripts/tests/` 3종: `test_version_stamp.sh`(Bash), `test_merge_hooks.py`(Python, 076 hook merge 로직), `test_console_scan.sh`(Bash) — 모두 install 스크립트 조각(버전 스탬프·hook merge·콘솔 스캔) 테스트이며 code-scan 도구와 무관.
- `opal/tools/*/tests/` 구성 — 10개 도구에 `tests/` 존재: `test-tool`, `memory-tool`, `state-tool`, `brain-tool`, `git-sync-tool`, `improve-tool`, `tool-scan`, `skill-registry`, `backlog-tool`, `opal-agent`. code-scan은 이 목록에 없다.
- Python 도구 테스트 컨벤션(state-tool 예): `unittest.TestCase` + `subprocess`(스크립트 end-to-end 실행) + 순수 함수 직접 import 병행, 표준 라이브러리만(`opal/tools/state-tool/tests/test_todo_mirror_hook.py:9-20`).
- Node.js 도구 테스트 컨벤션 — 유일한 순수 Node.js CLI 도구인 `skill-registry`가 유일한 선례:
  - 러너: `node:test` + `node:assert/strict`(`opal/tools/skill-registry/tests/test-validate.js:24-25`). 리포지토리 어디에도 `package.json`이 없고(확인: repo root·opal/tools 전역 검색 0건), 중앙 러너 스크립트도 없다 — `node --test <path>` 개별 호출이 실질 컨벤션이다.
  - 방식: CLI 블랙박스 — `child_process`로 `node skill-registry.js <subcommand>`를 실제 실행해 exit code + stdout JSON을 검증. 목·몽키패치 0건, 실 파일시스템 위 합성 fixture(HOME 오버라이드) 사용(`test-match.js` 파일 헤더 주석).
  - RED-first 표기: `// [RED 기대] 현행 코드는 ... FAIL한다` 인라인 주석 + 파일 상단에 TC번호↔TEST-SCENARIO.md S-ID 매핑 표(`test-migrate.js` 주석부).
  - 파일명 규칙: `test-<verb>.js`(예: `test-match.js`, `test-migrate.js`, `test-validate.js`) — `test_<verb>.py`(Python)와 대응하는 kebab 변형.
  - 관찰(참고, 비수정 대상): 이 파일들 자신의 상단 주석은 `// @module ...` 평문 라인 스타일이며, code-scan이 실제로 파싱하는 `@header { ... }` JSON 블록 포맷(`header-standard.md §3`)과 다르다 — 즉 skill-registry의 기존 테스트 파일 자체는 code-scan으로 discoverable하지 않다. 이번 태스크의 수정 대상은 아니나, 신규 code-scan 테스트 파일 작성 시 `header-standard.md §3` JSON 블록 포맷을 실제로 따라야 code-scan 자체 dogfooding(F-12 AC)에 잡힌다.
  - 정적 픽스처 선례: `opal/tools/tool-scan/tests/fixtures/manifest.stub.json`, `help_*.sh` 3종 — 이 도구는(skill-registry와 달리) 커밋된 정적 픽스처 파일을 사용한다. 도구별로 두 방식(동적 합성 vs 정적 커밋)이 혼재하는 것이 현재 실태다.
- RED-first 시나리오가 붙을 자리: `opal/tools/code-scan/tests/`(신설) — skill-registry 패턴을 따라 `test-resolve-header.js`(5단 상속), `test-discover.js`, `test-scaffold.js`, `test-target.js`, `test-validate.js`, `test-feature.js` 6개 파일 분할을 제안한다. 실행은 `node --test opal/tools/code-scan/tests/`(개별 호출, 중앙 러너 없음 — 기존 컨벤션과 동일).

---

## 2. 외부 조사 결과

해당 없음 — 이 태스크는 라이브러리·API 신규 도입이 없고(TASK 기술 스택: Node.js 무의존, 기존 코드 확장), 태스크 Guards가 외부 저장소 참조·인용을 명시적으로 금지한다. 근거 매트릭스상 개발 트랙이며 소스 코드 근거가 필수·웹 근거는 선택이므로(`opal/core/references/harness/citation-rules.md` §1.5) 본 절은 공란으로 둔다.

---

## 3. 영향 범위

### 3.1 직접 영향

| 파일/모듈 | 변경 내용 |
|----------|----------|
| `opal/tools/code-scan/code-scan.js` | 신규 해석기 함수(가칭 `resolveHeader`) 추가 + `scanAll`(:324)의 `extractHeader` 호출을 이 함수로 교체. `loadConfig`(:150-164)에 `headerSource` 키 추가. 신규 `.opal/code-map/index.json` 로더 함수 신설. `parseArgs`(:95-130)에 `--changed` 등 신규 플래그 분기 추가. `main()`의 `commands` 디스패치 테이블(:602-611)에 discover/scaffold/target/validate/feature 5엔트리 추가 + 대응 `cmdXxx` 함수 5개 신설 |
| `opal/core/references/header-standard.md` | 2소스 표현 절(index.json 스키마 + 매니페스트 스키마) 신설(F-1) |
| `opal/core/references/harness/header-rules.md` | §8 "작성 주체" 문구 교체(:12) + 4단 기록 위치 판정·3단 갱신 시점 표 신설(F-11) |
| `opal/core/references/pm/code-scan-management.md` | `headerSource` 필드 추론 규칙 추가(선택) |
| `opal/core/references/harness/pm-review-gate.md` | 8·14번 항목에 커버리지 합산·워커 권한 경계 확인 절차 반영 |
| `opal/core/references/tools.md` | code-scan 섹션 커맨드 표에 4서브명령 + feature 추가 |
| `opal/tools/tool-scan/manifest.json` | code-scan 엔트리 `when` 배열(:55)에 키워드 추가 |
| `opal/core/hooks/claude-hooks.json` | `PostToolUse` 배열에 신규 matcher 엔트리 추가(Node.js hook 스크립트 포인터) |
| `.gitignore` | `.opal/code-map/` 추적 예외 패턴 추가 |
| `opal/tools/code-scan/tests/` | 신규 디렉토리 — RED-first 테스트 6파일 + 픽스처 |

### 3.2 간접 영향

- brain-tool `sync-header`: `_load_code_scan_json`(`opal/tools/brain-tool/brain_tool.py:766-798`)이 code-scan `--json` 출력을 그대로 소비하며 `module/layer/domain/exports` 4필드만 비교한다(`:839`). `_source` 필드가 header 객체에 추가돼도 이 4필드 비교 로직은 무관한 키를 무시하므로 코드 변경 불필요. 다만 §4에 기술한 의미론적 리스크(코드맵 유래 헤더가 "코드에 실재하는 헤더"인 것처럼 brain frontmatter에 동기화될 수 있음)가 간접 영향으로 남는다.
- PM Gate 8번 항목(`pm-review-gate.md:52-56`): `code-scan scan <file> --json` 실행으로 @header 검증 — 파일 1개 경로를 직접 스캔하는 방식이 2소스 해석기에서도 유지되려면, 단일 파일 경로 인자가 주어졌을 때도 코드맵 조회가 동작해야 한다(파일→스코프→매니페스트 역매핑 필요). PLAN 단계 확인 필요.
- PM Gate 14번 항목(`pm-review-gate.md:89-94`): 디스패치 컨텍스트의 code-scan 결과 인용 검증 — 신규 서브명령 결과도 인용 대상에 포함되는지는 F-11 갱신 시 명시 필요.
- `.opal/code-scan.json` 자동 생성 로직(`opal/core/references/pm/code-scan-management.md:12-31`): scopes 추론 소스가 `docs/PROJECT.md §프로젝트 구성`이며(:18), 이 저장소는 현재 `.opal/code-scan.json` 자체가 존재하지 않는다(확인: 조회 결과 파일 없음) — 이는 5절 리스크에서 상세히 다룬다.
- `opal-harness.md §9 OPAL Tools` / `tools.md` drift 정합 관례: `tools.md` 변경이력(:802 "harness §9 drift 정합")에 보이듯 도구 커맨드 추가 시 `opal-harness.md §9` 도구 집합 표와의 동일화가 관례이므로, code-scan 신규 서브명령 추가 시 `opal-harness.md §9`도 함께 확인 필요(F-11 범위에 명시적으로 나열되지 않은 잠재 6번째 문서).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — code-scan CLI에 5개 신규 서브명령 + `_source` 필드 + `headerSource` 설정 키 추가(하위호환 유지 설계)
- [x] 설정/환경변수 변경 — `.opal/code-scan.json`에 `headerSource` 키, `.opal/code-map/index.json` 신규 파일 포맷
- [ ] 빌드/배포 파이프라인 변경 — `install-mac.sh` 자체 수정 불필요(§1.1 근거), `.gitignore` 예외만 추가

---

## 4. 핵심 발견 사항

1. 8커맨드 전부가 단일 호출점(`scanAll`:324의 `extractHeader` 호출)을 경유하므로, 5단 상속 해석기는 이 지점 하나만 교체하면 8커맨드에 자동 전파된다. `discoverFiles`/`walkDir`/`getSearchPaths`(파일 탐색 계층)와 `fmtBrief`/`fmtFull`/`fmtJson`(출력 계층)은 코드 변경이 전혀 필요 없다 — 출력 계층은 `header` 객체를 필드명으로 선별 접근하거나(`fmtBrief`) 통째로 직렬화하므로(`fmtFull`/`fmtJson`) `_source` 필드가 자동으로 통과한다(`code-scan.js:348-376`). 이는 TASK.md 확정 방향 2/5의 "단일 해석 지점"·"모든 조회 결과에 `_source` 표기" 주장을 코드 레벨에서 실증한다.

2. 이 저장소 자체가 `.opal/code-scan.json`을 아직 보유하지 않는다. 확인 결과 파일이 부재하므로, 현재 이 프로젝트에서 `code-scan scan`/`missing`을 스코프 없이 실행하면 `getSearchPaths`(:236-239)가 `config.scopes`가 빈 객체(`DEFAULT_CONFIG.scopes:{}`)인 것을 보고 `[projectRoot]` 전체를 순회한다(:238-239) — 즉 현재 이 순간 `tasks/` 하위까지 포함한 저장소 전체가 스캔 대상이다. 이는 F-12의 합성 픽스처 격리 설계에 직접적인 선결 조건이 된다(§5 R-1 참조).

3. `findProjectRoot()`(:136-148)의 `.opal` 마커 조건 덕분에, 자체 `.opal/` 디렉토리를 가진 픽스처 하위 트리는 그 안에서 실행 시 자기 자신을 프로젝트 루트로 인식한다. 합성 픽스처를 `<fixture-root>/.opal/code-scan.json` + `<fixture-root>/.opal/code-map/`로 자기완결시키고, 테스트가 `cwd: <fixture-root>`로 subprocess를 실행하면(skill-registry CLI 블랙박스 패턴과 동일), 실제 저장소 설정과 완전히 격리된 환경에서 4서브명령을 검증할 수 있다.

4. brain-tool `sync-header`는 코드 변경 없이 `_source` 필드를 무해하게 통과시키지만, 의미론적으로는 새로운 상황이 발생한다. `cmd_sync_header`(`brain_tool.py:801-854`)는 `source_ref`(entity frontmatter)가 가리키는 파일의 헤더를 code-scan 출력에서 조회해 `module/layer/domain/exports` 4필드를 그대로 신뢰·갱신한다(:839-845). 2소스 해석이 도입되면 이 4필드가 (a) 실제 파일 내부 인라인 주석에서 온 것인지 (b) 소유자가 소스를 건드릴 수 없어 외부 매니페스트에 채워 넣은 값인지 구분 없이 동일하게 동기화된다 — `sync-header`의 "단방향(code-scan @header → brain)" 계약(`brain-tool/README.md:15`) 문언 자체는 위반하지 않지만, "code-scan @header"라는 표현이 이제 "코드에 실재하는 주석"만을 의미하지 않게 된다는 점은 F-11 갱신 시 `brain-tool/README.md`에도 언급 여부를 검토할 근거가 된다(단, TASK.md 범위 표는 이 문서를 F-11 대상 5문서에 포함하지 않았음 — §5 R-4 참조).

5. PostToolUse hook 선례(`todo_mirror_hook.py`)는 `matcher: "Bash"` 한정이며, 코드 파일 수정은 대개 `Edit`/`Write` 도구로 발생하므로 F-9 hook은 선례와 다른 matcher·입력 계약이 필요하다. `claude-hooks.json:2-11`의 유일한 `PostToolUse` 엔트리는 `"matcher": "Bash"`이고, `todo_mirror_hook.py`는 `tool_input.command`(Bash 명령 문자열)만 파싱한다(`:25-31`). 코드 파일이 수정됐는지 감지하려면 `Edit`/`Write`/`MultiEdit` 도구의 `tool_input.file_path`를 읽는 별도 matcher·별도 파싱 로직이 필요하다 — 이는 `claude-hooks.json`의 `PostToolUse` 배열에 새 엔트리를 추가하는 additive 변경이며(기존 Bash 엔트리와 충돌 없음), 언어는 TASK 제약 ④에 따라 Python(`~/.opal/.venv/bin/python`) 대신 Node.js(`node ~/.opal/tools/code-scan/<hook>.js`)로 작성해야 하는 점이 선례와의 두 번째 차이다.

---

## 5. 제약/리스크

| # | 항목 | 설명 | 심각도 | 근거 |
|---|------|------|--------|------|
| R-1 | 합성 픽스처 오염 경로 실재 | 이 저장소에 `.opal/code-scan.json`이 없어 스코프 미지정 스캔이 프로젝트 전체를 순회한다(`getSearchPaths:236-239`). `opal/tools/code-scan/tests/fixtures/`에 `.js`/`.ts` 확장자 픽스처를 두면 저장소 전체 스캔(`missing`, brain `sync-header`)에 실제로 포함된다 — `.json` 확장자인 매니페스트 자체는 `DEFAULT_CONFIG.extensions`(:31)에 없어 안전하지만, 픽스처의 인라인 헤더 테스트 파일(조건⑥)은 그렇지 않다 | 높음 | `opal/tools/code-scan/code-scan.js:236-239,31` + 실측(`.opal/code-scan.json` 부재) |
| R-2 | `depends` 커맨드의 정밀도 저하 가능성 | 패키지 계층(tier 3)에서 `depends` 배열을 상속받는 파일이 생기면, `cmdDepends`(:524-575)의 역의존 탐색(:538-543)이 "이 파일이 실제로 선언한 의존"이 아니라 "이 파일이 속한 패키지가 선언한 의존"까지 매칭한다 — 확정 설계(5단 상속) 의도된 동작이지만 `depends` 결과의 정밀도 의미가 미묘하게 변한다는 점은 PLAN 단계에 명시 필요 | 중간 | `opal/tools/code-scan/code-scan.js:538-543` (확정 방향 5) |
| R-3 | `feature`와 `--scope`의 상호작용 미정 | F-8 AC는 "1회 호출로 스코프별 그룹 반환"을 요구하나, 기존 `--scope` 플래그는 `getSearchPaths`(:224-231)에서 단일 스코프로 탐색 경로를 좁힌다. `feature <id> --scope X`가 X로 좁혀야 하는지, 무시하고 전체 스코프를 순회해야 하는지 인터페이스 충돌 여지가 있다 | 중간 | `opal/tools/code-scan/code-scan.js:223-240` |
| R-4 | `brain-tool/README.md`가 F-11 대상 문서 목록에서 제외됨 | §4 발견 4에서 확인한 대로 "code-scan @header"의 의미가 2소스로 확장되지만, TASK.md 범위(F-11)는 5문서(`header-rules.md`/`code-scan-management.md`/`pm-review-gate.md`/`tools.md`/tool-scan 매니페스트)만 지정하고 `brain-tool/README.md`는 포함하지 않는다 — 문서 갱신 누락 리스크 | 낮음 | TASK.md F-11 "어디에" 필드 / `opal/tools/brain-tool/README.md:15` |
| R-5 | 단일 파일 경로 스캔과 코드맵 역매핑 | PM Gate 8번(`pm-review-gate.md:53`)은 `code-scan scan <file> --json`으로 파일 1개를 직접 스캔한다. `readonly` 스코프 파일처럼 인라인 헤더가 없고 코드맵에만 헤더가 있는 파일을 이 방식으로 검증하려면, 단일 파일 경로 인자에서도 소속 스코프·매니페스트를 역으로 찾는 로직이 필요 — 현재 `discoverFiles`(:242-258)는 `opts.targetPath`가 파일이면 그대로 단일 파일 배열을 반환하므로(:246) 스코프 컨텍스트가 소실된다 | 중간 | `opal/tools/code-scan/code-scan.js:242-248,53` |
| R-6 | hook 등록이 전역(글로벌) 단위 | `claude-hooks.json`은 `install-mac.sh`가 `~/.claude/settings.json`(사용자 전역)에 병합하므로(`:1213-1218`), F-9 hook은 코드맵을 사용하지 않는 프로젝트에서도 매 `Edit`/`Write` 호출마다 실행된다 — hook 스크립트 자체가 빠르게 무관 판정(코드맵 부재/미대상 파일)하고 무출력 반환해야 성능·부작용이 없다(`todo_mirror_hook.py` DEC-9 fail-safe 패턴 재사용 필요) | 중간 | `scripts/install-mac.sh:1212-1219` / `opal/tools/state-tool/todo_mirror_hook.py:124-130` |
| R-7 | 테스트 자산 0에서 시작 | `opal/tools/code-scan/`에 `tests/`가 없어(§1.4) F-12 RED-first 검증이 전량 신규 작성이며, 참조할 code-scan 자체 회귀 스위트가 없다 — 기존 8커맨드 회귀 검증(제약②)도 이번 태스크에서 처음 테스트 코드로 고정된다 | 낮음 | (부재 확인, §1.4) |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Node.js (외부 패키지 없음) | code-scan.js v1.2.0 |
| 언어(비교 대상) | Python (표준 라이브러리만) | state-tool/brain-tool/기타 도구 (venv) |
| 테스트 러너(신규 도구 언어 기준) | Node.js 내장 `node:test` | Node 18+ (skill-registry 선례) |
| hook 등록 스키마 | Claude Code `settings.json` hooks (JSON) | `opal/core/hooks/claude-hooks.json` |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| 해당 없음 | 이 태스크는 프레임워크 내부 도구 확장이며 외부 프레임워크 스킬 도입이 없다 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| 해당 없음 | 외부 라이브러리 조사가 없어 context7/WebSearch 불필요 |

---

## 변경이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-07-28 | 최초 작성 — code-scan.js 626줄 전량 분석, 5단 상속 삽입 지점, CLI 인터페이스 충돌 검토, 테스트 자산 0건 확인, 합성 픽스처 오염 경로 실측, hook 선례 차이 정리 (077) |
