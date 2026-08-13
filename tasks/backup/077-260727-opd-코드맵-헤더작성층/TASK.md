# TASK: 코드 헤더 작성층 신설 — 인라인 + 외부 code-map 2소스

> 작성일: 2026-07-27 | 작업 유형: 신규 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

코드 `@header` 메타를 **소스 인라인 주석**과 **프로젝트 외부 파일(`.opal/code-map/`)** 두 소스에서 동등하게 관리·조회할 수 있게 하고, 현재 프레임워크에 비어 있는 **헤더 작성층**(초안 생성·기록 위치 판정·정합 검증·hook 감시)을 신설한다.

## 배경

현재 프레임워크는 헤더 **작성**을 워커의 손에만 맡기고 있어(도구 없음), 이미 존재하는 코드에 헤더를 부여하는 경로가 없다. 또한 헤더를 소스 파일에만 기록할 수 있어, 소스를 수정할 수 없거나 수정 부담이 과도한 프로젝트에서는 code-scan 자산화가 원천적으로 불가능하다.

## 배경 분석 (대화에서 도출)

### (1) 현재 헤더 체인 — 작성 칸만 비어 있다

| 단 | 담당 | 상태 |
|----|------|------|
| 포맷 정의 | `opal/core/references/header-standard.md` | 문서 존재 (필수 5종 + 선택 2종, layer 표준값 27종) |
| 작성 지시 | PM이 디스패치 프롬프트에 주입 (`opal-harness.md` §8) | 산문 |
| **작성 실행** | **워커 손 (Edit/Write)** | **도구·스킬 없음** |
| 검증 | PM Gate + `code-scan scan <file> --json` (`harness/pm-review-gate.md:52-56`) | 도구화됨 |
| 소비 | code-scan 8커맨드, `brain-tool sync-header`(단방향) | 도구화됨 |

- [MUST] `opal/core/references/harness/header-rules.md` §8: "**작성 주체**: 워커(LLM)가 직접 작성. 별도 도구 없음."
- 코드 확인: `opal/tools/`·`scripts/` 전체에서 소스 파일에 헤더를 **기록**하는 자동화 0건 — 히트는 ① 도구 자신의 헤더 ② 읽기·파싱(`code-scan.js`) ③ `brain-tool sync-header`뿐이며, ③은 `opal/tools/brain-tool/README.md:15`에 "단방향 동기화: `sync-header`는 code-scan @header → brain entity frontmatter 방향만 (역방향 금지)"로 못박혀 있어 소스에 쓰지 않는다
- 결과: 현행 규칙은 "생성·수정하는 파일" 전제이므로 건드리지 않는 기존 파일은 영구히 헤더가 없다. `code-scan missing`(`code-scan.js:577`)은 나열만 하고 채우는 수단을 제공하지 않는다

### (2) 확장 지점 — 헤더 해석은 단일 함수를 통과한다

- `opal/tools/code-scan/code-scan.js:274` `extractHeader(filePath)`가 유일한 해석 지점이며, 상위 8커맨드(scan/domain/layer/search/exports/summary/depends/missing)가 모두 `scanAll`(`:318`)→이 함수를 경유한다
- 소비자는 `--json` 출력(`:372-376`)만 보므로 해석 소스가 확장돼도 하위호환이 유지된다
- 설정 로더는 `loadConfig`(`:150`) 단일 지점이며 `.opal/code-scan.json`의 `scopes`·`extensions`·`exclude`·`excludePatterns`를 읽는다

### (3) 프레임워크가 지원해야 하는 프로젝트 조건 3종

인라인 기록만으로는 아래 조건에서 자산화가 불가능하거나 규약 위반이 된다. 이번 작업은 이 3종을 지원 범위로 정의한다.

| 조건 | 왜 인라인이 불가한가 |
|------|--------------------|
| **레거시 대량** — 기존 소스가 수천~수만 파일 | 전량 파일 수정이 필요해 도입 비용이 도입 가치를 초과 |
| **읽기 전용 레포** — 프로젝트 규약상 수정 금지 대상 | 소스 수정 자체가 규약 위반 |
| **공유 레포** — 여러 서비스·팀이 공유, 우리 스코프만 자산화 | 인라인은 타 팀 소유 코드를 침범 |

- 세 조건 모두 "메타는 필요하지만 소스에 쓸 수 없다"는 동일 구조이므로, 기록 위치를 소스 밖으로 분리하면 한 번에 해소된다

### (4) 기능·화면 축은 구조축으로 좁혀지지 않는다

- 현행 자산은 모두 **구조축**(module·layer·domain)만 보유한다 — `opal/tools/brain-tool/templates/page-entity.md` frontmatter도 `module`·`layer`·`domain`·`exports`·`source_ref`까지이고 기능·화면 축 키가 없다
- 화면·정책 축 토큰 체계는 별도로 정의돼 있다 — `citation-rules.md` §8.6: "`POL-{번호}`(정책참조), `ia:{system}:{screen}`(IA참조)" (형식 SSOT: `opal/tools/brain-tool/templates/schema-template.md` §4)
- 즉 "특정 화면이 쓰는 소스 전체" 류 질의는 도메인·레이어 필터만으로는 후보를 좁힐 수 없고, 구조축과 기능축을 잇는 **조인 키가 없다**
- 이번 작업은 조인 키가 들어갈 자리(`files[].feature` 옵셔널 필드 + 조회)만 만들고, 태그 실채우기는 범위에서 제외한다

## 확정된 설계 방향 (대화에서 합의)

1. **디렉토리**: `{프로젝트}/.opal/code-map/` — 문서 정식명 "소스 코드 지도(source code map)". `source-map`은 웹 생태계에서 "빌드 산출물 ↔ 원본 매핑"으로 확정된 용어라 금지. `codes`는 표준코드·코드사전 어휘와 충돌하여 기각
2. **구조**: 디렉토리(패키지) 단위 미러 1파일 — 소스 디렉토리 `A/B/C/` ↔ 매니페스트 `.opal/code-map/{scope}/{module}/B/C.json`. 파일 단위는 그 안의 `files` 객체(키=basename). 파일별 사이드카는 파일 수를 2배로 만들어 기각
3. **3계층 표현**: `index.json`(scope·domains·layerRules) → 매니페스트 `package`(패키지 공통) → `files[basename]`(파일 고유)
4. **앵커·접두 절단**: scope별 `anchors`(빌드 매니페스트 기반 모듈 목록 등) + `stripPrefix`(언어별 소스 루트·패키지 상용구 제거)로 미러 경로 비대를 방지
5. **5단 상속**(필드별 최근접 승리): ① 인라인 `@header`(파일 단독 승리, 병합 없음) → ② `files[basename]` → ③ `package` → ④ `index.layerRules` → ⑤ `index.domains.paths`. 모든 조회 결과에 `_source: inline|file|package|rule|domain` 표기
6. **4단 기록 위치 판정**(사람·워커 판단 배제): ① `readonly` 스코프 → code-map 강제 ② 인라인 존재 → 인라인 갱신 ③ 신규 파일 → 인라인 작성 ④ 기존 파일 + 인라인 없음 → code-map. 도구(`target`)가 `write_to`·`reason`을 반환하고 워커는 그대로 따른다
7. **3단 갱신 시점**: (a) 워커가 파일 변경과 같은 자리에서 지도 갱신 (b) CLOSE 진입 전 `validate --changed` 게이트 (c) PostToolUse hook 감시. "작업 완료 후 일괄 갱신"은 금지
8. **4-pass 작성 파이프라인**: pass1 `discover`(PM 직접, 초안) → 소유자 리뷰 → pass2 `scaffold`(PM 직접, 골격 전량·LLM 개입 0) → pass3 워커 배치(의미 채움) → pass4 `validate` + 샘플 대조 검증(생성자≠평가자)
9. **워커 권한 경계**: 워커 가능 필드 = `description`·`exports`·`depends`·`note` / 금지 = `dir`·`files` 키 목록·`layer`·`domain`·`scope`·`module`(도구 관할). 침범 시 `validate`가 거부
10. **멱등성**: `scaffold` 재실행 시 도구 관할 필드만 갱신하고 사람·워커 작성 필드는 보존 merge (state-tool todo 미러 upsert 선례)
11. **양쪽 공용**: `discover`/`scaffold`/`target`/`validate`는 code-map 전용이 아니라 **인라인에도 적용**되며, 커버리지는 인라인+지도 합산으로 계산한다
12. **범위 분리**: 077은 도구·규칙·스키마·픽스처 검증까지. 실제 대형 레포 자산화 파일럿과 `feature` 태그 실채우기는 후속 태스크

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | code-scan을 인라인·code-map 2소스로 확장하고, 비어 있는 헤더 작성층(discover/scaffold/target/validate + hook)을 신설한다 | - | 배경분석 (1)(2) |
| 범위 | **포함**: code-map 스키마(index+매니페스트), 5단 상속·`_source`, 4 서브명령(discover/scaffold/target/validate), **exports 존재 대조 검증**, `feature` 옵셔널 필드 + `feature` 조회, PostToolUse hook, `headerSource` 스위치, **`run.sh` 래퍼 신설(F-13)**, **`.opal/code-scan.json` 생성(F-12 선결)**, 규칙 SSOT 5문서 갱신, 합성 픽스처 검증, 자체 dogfooding<br>**제외**: exports **자동 추출** 파서(생성=워커·검증=도구 분업 확정), **`scaffold --inline`(소스 파일 주석 삽입)**, 지도→인라인 역주입 마이그레이션, 해시·mtime stale 감지, 파일별 사이드카, 외부 레포 자산화 파일럿, `feature` 태그 실채우기 | - | 확정 방향 12 + ANALYSIS PM Gate |
| 제약 | ① 기존 프로젝트 동작 변화 0(`headerSource: auto` 기본) ② `code-scan.js` 8커맨드 하위호환 유지 ③ `~/.opal/` 직접 편집 금지(프로젝트 소스 수정 후 install) ④ 도구 언어는 code-scan과 동일(Node.js) ⑤ 산문 규칙 대신 도구·hook 집행(076 교훈) ⑥ `.opal/*` gitignore 예외 필요(code-map은 수작업 자산) ⑦ 검증은 저장소 내 합성 픽스처로만 수행 — 외부 레포 의존 금지 | - | `.opal/AGENT.md` §금지사항 / 076 |
| 완료기준 | RED-first 시나리오 전량 PASS + 기존 code-scan 회귀 0 + 규칙 5문서 갱신 완료 + 합성 픽스처 6조건 전량 검증 + 자체 저장소 dogfooding 1회 성공 + `tool-scan usage code-scan`이 `ok: true` 반환 | - | 요구사항 F-1~F-13 AC |

## 요구사항

- [ ] **F-1 code-map 스키마 정의** — 무엇을: `index.json`(version·origin·scopes[root/anchors/stripPrefix/readonly]·domains·layerRules·exclude) + 패키지 매니페스트(version·dir·package·files) 스키마 확정 / 어디에: `opal/core/references/header-standard.md` 신설 절 + `opal/tools/code-scan/` 스키마 상수 / 왜: 확정 방향 2·3 / **AC**: header-standard.md에 2소스 표현 절이 존재하고 두 파일 형식의 필수·선택 필드가 각각 표로 열거되며, 스키마 위반 입력 시 `validate`가 에러 코드로 거부한다
- [ ] **F-2 5단 상속 해석** — 무엇을: `extractHeader`를 2소스 해석으로 확장, 필드별 최근접 승리, 인라인은 파일 단독 승리 / 어디에: `opal/tools/code-scan/code-scan.js` / 왜: 확정 방향 5 / **AC**: 5단이 각각 단독 적용되는 5개 케이스와 혼재 케이스에서 조회 결과 필드값이 시나리오 기대치와 일치하고, 모든 결과에 `_source`가 `inline|file|package|rule|domain` 중 하나로 표기된다
- [ ] **F-3 `discover` 서브명령** — 무엇을: 빌드 매니페스트·확장자·디렉토리 규약에서 `index.json` 초안 생성 / 어디에: `code-scan.js` + `opal/core/references/tools.md` / 왜: 확정 방향 8 pass1 / **AC**: 픽스처 실행 시 scopes(2종 이상)·layerRules(디렉토리 규약 기반)·exclude(컴파일 산출물 디렉토리 포함)가 담긴 초안이 생성되고, 초안 상태 표시가 파일에 포함된다
- [ ] **F-4 `scaffold` 서브명령 + 멱등 보존** — 무엇을: 미러 트리·골격 매니페스트 전량 생성(description 빈칸·draft), 재실행 시 사람 작성 필드 보존 merge / 어디에: `code-scan.js` / 왜: 확정 방향 8 pass2 + 10 / **AC**: ① 대상 스코프의 소스 디렉토리 수와 생성된 매니페스트 수가 일치 ② `dir`·`files` 키가 실제 파일 목록과 일치 ③ description을 채운 뒤 재실행해도 그 값이 유지되고 신규 파일만 빈 엔트리로 추가된다
- [ ] **F-5 `target` 서브명령 (4단 판정)** — 무엇을: 파일별 기록 위치 판정 + `reason` 반환 / 어디에: `code-scan.js` / 왜: 확정 방향 6 / **AC**: `readonly_repo`·`inline_exists`·`new_file`·`legacy_no_header` 4종 조건에서 각각 해당 `reason`과 올바른 `write_to`(code-map일 때 `manifest`·`key` 포함)를 반환한다
- [ ] **F-6 `validate` 서브명령** — 무엇을: orphan·uncovered·conflict·draft 잔량 + **exports 존재 대조** 판정 + 인라인·지도 합산 커버리지 + `--changed` 모드 + exit code / 어디에: `code-scan.js` / 왜: 확정 방향 7(b) + 생성=워커·검증=도구 분업 / **AC**: 5종 위반(orphan·uncovered·conflict·draft·exports_not_found)을 각각 심어둔 픽스처에서 유형별로 검출되고, 위반 존재 시 non-zero exit, 커버리지 %가 인라인+지도 합산으로 산출되며, `--changed`가 변경 파일만 판정한다. **exports 존재 대조**는 언어 문법 파싱 없이 대상 파일 텍스트에 해당 식별자가 나타나는지만 확인하며(무의존 유지), 미존재 항목을 파일·키·식별자 단위로 보고한다
- [ ] **F-7 워커 권한 경계 집행** — 무엇을: 도구 관할 필드(`dir`·`files` 키·`layer`·`domain`·`scope`·`module`) 침범 거부 / 어디에: `code-scan.js` validate 경로 / 왜: 확정 방향 9 / **AC**: 워커 허용 필드만 수정된 매니페스트는 통과하고, 도구 관할 필드가 변경된 매니페스트는 전용 에러 코드로 거부된다
- [ ] **F-8 `feature` 옵셔널 필드 + 조회** — 무엇을: `files[].feature` 필드 정의(옵셔널) + `code-scan feature <id>` cross-scope 조회 / 어디에: `code-scan.js` + header-standard.md / 왜: 배경분석 (4) / **AC**: 동일 `feature` 태그가 2개 이상 스코프에 존재할 때 `feature <id>` 1회 호출로 스코프별로 묶여 반환되고, 태그 미부여 프로젝트에서도 기존 8커맨드가 정상 동작한다
- [ ] **F-9 PostToolUse hook** — 무엇을: 대상 파일 수정 후 기록 위치(target 판정) 미갱신 감지 / 어디에: `opal/tools/code-scan/` hook + 설치 배선 / 왜: 확정 방향 7(c) / **AC**: code-map 대상 파일을 수정하고 매니페스트를 갱신하지 않은 시나리오에서 hook이 경고를 출력하고, 갱신한 시나리오에서는 침묵하며, hook 미설치 환경에서 파이프라인이 깨지지 않는다
- [ ] **F-10 `headerSource` 스위치** — 무엇을: `.opal/code-scan.json`에 `headerSource: auto|inline|manifest` 추가(기본 auto) / 어디에: `code-scan.js` + `pm/code-scan-management.md` / 왜: 제약 ① / **AC**: code-map이 없는 프로젝트에서 8커맨드 출력이 변경 전과 동일하고(회귀 0), `inline`/`manifest` 명시 시 해당 소스만 해석된다
- [ ] **F-11 규칙 SSOT 갱신 (교체 포함)** — 무엇을: 작성층 신설·4단 선택·3단 시점·커버리지 합산 반영 / 어디에: `harness/header-rules.md`, `pm/code-scan-management.md`, `harness/pm-review-gate.md`, `opal/core/references/tools.md`, tool-scan 매니페스트 / 왜: 확정 방향 11 + 프레임워크-우선 개선 원칙 / **AC**: ① 5문서 모두 변경이력 행 추가 ② `header-rules.md`에서 "별도 도구 없음" 문구 잔존 0건 ③ 4단 선택 규칙·3단 갱신 시점·워커 권한 경계가 각각 문서에 표로 존재 ④ `tool-scan usage code-scan`이 신규 4서브명령을 반환
- [ ] **F-12 합성 픽스처 + 자체 dogfooding 검증** — 무엇을: 저장소 내 픽스처로 6조건 재현 후 4-pass 실행 + 자체 저장소 실행 1회 / **선결**: 이 저장소 `.opal/code-scan.json`을 생성한다(현재 부재 — scopes는 `docs/PROJECT.md` §프로젝트 구성 3요소 Framework/Console FE/Console BE에서 추론, exclude에 `tasks`·`node_modules`·`dashboard/frontend/node_modules` 등 반영). 부재 상태에서는 스코프 미지정 스캔이 저장소 전체를 순회하여 픽스처가 실제 스캔에 오염된다 / 어디에: 도구 내 테스트 경로 + `.opal/code-scan.json` / 왜: 완료기준 + 제약 ⑦ + ANALYSIS R-1 / **AC**: 픽스처가 ① 5단 이상 깊은 패키지 경로 ② 언어별 소스 루트 상용구(`stripPrefix` 대상) ③ 앵커 2종(빌드 매니페스트 기반·단순 디렉토리) ④ `readonly` 스코프 1종 ⑤ 컴파일 산출물 중복 사본 디렉토리 ⑥ 인라인·지도 혼재 파일을 모두 포함하고, discover→scaffold→target→validate가 전 조건에서 기대 결과를 반환하며, 자체 저장소 실행에서 위반 0건이 로그로 증명된다
- [ ] **F-13 `run.sh` 래퍼 신설** — 무엇을: `opal/tools/code-scan/run.sh` 신설(다른 도구 12종과 동일 규약) / 어디에: `opal/tools/code-scan/run.sh` + 배포 배선 확인 / 왜: 현재 code-scan에만 래퍼가 없어 `tool-scan usage code-scan`이 `help_exec_failed`(exit 127)로 실패하며, `opal-harness.md` §9 "OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다" 규약을 위반 중이다. F-11 AC④·F-9 hook 커맨드 경로의 공통 선결 조건 / **AC**: ① `~/.opal/tools/code-scan/run.sh --help`가 정상 종료(exit 0)하고 사용법을 출력 ② `tool-scan usage code-scan`이 `ok: true`로 신규 서브명령을 포함한 사용법을 반환 ③ 기존 `node code-scan.js <cmd>` 직접 호출 경로도 계속 동작(하위호환)

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다."
- 기존 `code-scan.js` 8커맨드 하위호환 유지 — code-map 부재 프로젝트 동작 변화 0
- 신규 도구 코드는 code-scan과 동일 언어(Node.js) — 도구 내 언어 이원화 금지
- `.opal/*` gitignore 예외 등록 필요 — code-map은 파생 캐시(`code-scan.json`)와 달리 수작업 자산이므로 추적 대상
- 검증은 저장소 내 합성 픽스처와 자체 소스로만 수행 — 외부 저장소를 완료기준에 넣지 않는다(재현성·독립성)

## 기술 스택

- Node.js — `opal/tools/code-scan/code-scan.js` (v1.2.0, 626줄, 무의존)
- Bash — 도구 래퍼(`run.sh`) 및 설치 배선(`install-mac.sh`)
- Markdown — 규칙 SSOT 5문서

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 헤더 해석 단일 지점(`:274`)·8커맨드·config 로더(`:150`) |
| D-2 | 설계 | header-standard.md | `opal/core/references/header-standard.md` | 필드 정의·layer 표준값·언어별 주석 포맷 |
| D-3 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | 현행 작성 규칙·"별도 도구 없음"·빈 결과 폴백 3분기 |
| D-4 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | code-scan.json PM 관리 의무·추론 소스 3종 |
| D-5 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | PM Gate 8항목 @header 검증 절차(`:52-56`) |
| D-6 | 설계 | brain-tool README | `opal/tools/brain-tool/README.md` | `sync-header` 단방향 계약(소스 역기록 금지, `:15`) |
| D-7 | 설계 | brain entity 템플릿 | `opal/tools/brain-tool/templates/page-entity.md` | 현행 자산의 구조축 한정 근거(기능축 키 부재) |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §8.6 정책·IA 토큰 체계(조인 키 설계 근거) |
| D-9 | 설계 | 076 태스크 | `tasks/076-260723-opds-todo미러-hook자동화/` | 산문→hook 강제 전환 선례·멱등 upsert 패턴 |
