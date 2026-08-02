# TASK: 헤더 소스 단일화 — headerSource 기준 통일 + 스코프 include/exclude

> 작성일: 2026-08-01 | 작업 유형: 개선 | 적용 스킬: opd (opds에서 에스컬레이션 전환, 2026-08-01) | 모드: agentic
> 입력: 사용자 요청 (077 테스트 중 도출)
> 출력: TASK.md

## 작업 목표

`code-scan`의 헤더 **조회·작성·검증 전 경로**가 `headerSource` 한 키를 기준으로 동작하게 하여 인라인과 code-map의 혼재 관리를 없애고, 혼재 디렉토리를 다루기 위해 `scopes` 값에 객체 형식(`include`/`exclude`)을 추가한다.

## 배경

077에서 2소스(인라인 + `.opal/code-map/`) 지원을 완성했으나, 실제 프로젝트에 적용하는 과정에서 두 가지가 드러났다.

1. **`headerSource`가 조회 경로에서만 동작한다.** 작성 판정(`target`)·`scaffold`·`validate` 커버리지는 모드를 무시하고 파일별 4단 판정과 합산 커버리지로 동작한다. 그 결과 `manifest`로 설정한 프로젝트에서도 신규 파일에는 인라인이 권고되어 두 소스가 계속 섞인다.
2. **혼재 디렉토리를 표현할 수단이 없다.** 한 디렉토리에 여러 서비스의 파일이 섞여 있을 때, 형제 파일을 하나씩 부정(`excludePatterns`)하는 방식은 유지보수가 어렵다. 원하는 것을 긍정으로 지정하는 화이트리스트가 필요하다.

## 배경 분석 (대화에서 도출)

### (1) `headerSource` 소비 지점은 1곳뿐

- `code-scan.js:690-699` — `resolveHeader`(조회)에서만 분기한다
- `decideTarget`(`:755-792`)은 `headerSource`를 참조하지 않는다. 판정 순서는 `readonly` → `inline_exists` → `new_file` → `legacy_no_header`
- `cmdScaffold`는 모드와 무관하게 전 디렉토리 매니페스트를 생성한다
- `cmdValidate`의 커버리지는 인라인+매니페스트 합산이다

### (2) `readonly`와 `headerSource`는 같은 일을 한다

- `readonly` 전량 참조: `code-scan.js:761`(decideTarget 1순위 판정), `:1098`·`:1107`(discover 초안 기록) — **그 외 없음**
- hook(`code-map-hook.js`)에는 참조가 0건이다
- 즉 구현상 `readonly`의 효력은 "이 스코프의 헤더는 매니페스트에 기록한다" 하나이며, **소스 코드 편집을 막는 코드는 존재하지 않는다**
- `header-standard.md:206` 서술도 동일하다: "`true`면 `target`이 무조건 `manifest` 반환"
- 따라서 `readonly: true`는 **스코프 단위 `headerSource: manifest`의 다른 이름**이다

### (3) 혼재 디렉토리 실사례

- 한 디렉토리에 서비스 A 파일 1개와 서비스 B 파일 다수가 공존하는 구조가 실재한다
- 현행 수단(`excludePatterns`)은 "제외할 것"을 하나씩 나열해야 하므로, 형제 파일이 늘어날 때마다 설정이 따라 늘어난다

### (4) 077에서 확인된 필터 적용 지점

- 열거(`discoverFiles`)·scaffold 열거(`collectDirsWithCodeFiles`)·`validate` 구조 패스(`listCodeFilesInDir`)·`--changed` 경로·`target`이 각각 파일 집합을 판정한다
- 077 추가작업에서 이 중 한 곳(구조 패스)이 필터를 빠뜨려 오탐이 발생한 전례가 있다 — 적용 지점이 갈라지면 조용한 오작동이 생긴다

## 확정된 설계 방향 (대화에서 합의)

| # | 결정 | 비고 |
|---|------|------|
| **D-1** | 도구는 **비대화형 유지** + `--header-source <inline\|manifest>` 플래그. 최초 설정을 묻는 주체는 **PM(오케스트레이터)** | 규칙 문서에는 개인 식별자(에이전트 이름·소유자 호칭)를 쓰지 않고 **역할명**으로 기재한다 |
| **D-2** | `readonly` **제거** → `headerSource` **전역 단일 키**로 통합. **스코프별 오버라이드 없음** (2026-08-02 소유자 결정) | 혼재 케이스는 존재할 수 없다는 것이 소유자 판단이다. 기존 `readonly` 키는 무시하고 deprecated 안내 1회를 출력한다(즉시 파괴 금지) |
| **D-3** | `auto` **완전 제거** → `inline` / `manifest` **2택** | 혼재를 허용하는 값이 남으면 이번 결정이 무력화된다 |
| **D-4** | 미설정 = **에러 거부**(`header_source_unset`) | 암묵 기본값을 두지 않는다 |
| **D-5** | 차단 범위 = **code-scan 전 명령** | 조회 8커맨드 포함 |
| **개선 A** | `scopes` 값에 객체 형식 추가 — `{path, include: [], exclude: []}`. 문자열은 동일 형태로 정규화(하위호환) | `include`가 있으면 화이트리스트 우선, 그 다음 `exclude`. 패턴 문법은 기존 `excludePatterns`와 동일(`*` `**` `?`, `/` 포함 시 전체 경로) |

### 개선 A 보강 5건 (설계 시 반드시 반영)

| # | 보강 | 근거 |
|---|------|------|
| ① | **단일 필터 계약** — `isInScope(relPath, scopeDef)` 하나를 만들고 열거·scaffold·validate·target이 전부 그것만 호출한다 | 적용 지점을 "4곳 동기화"에서 "1곳 계약"으로 축소해야 동기화 실패가 구조적으로 불가능해진다 |
| ② | **위반 검출기까지 필터 적용** — `files_key_removed`(`code-scan.js:1582`)와 `uncovered` 검출기 | 생성만 필터하면 매니페스트에 없는 형제 파일이 위반으로 잡힌다 |
| ③ | **스코프 중복 우선순위** — `resolveScope`(`:557-569`)는 현재 최장 root 승리 + 동률 시 이름 사전순이다. `include` 도입 시 root가 같고 include만 다른 스코프가 가능해지므로, 동률에서는 **include 매칭 스코프 승리**, 둘 다 매칭되면 명시 에러 | 사전순 우연 판정을 남기지 않는다 |
| ④ | **`dir` 의미 변경 명시** — include로 걸러지면 매니페스트가 디렉토리 전체를 대표하지 않는다. `files{}`가 부분집합인 것이 정상임을 스키마·문서에 못박는다 | ②의 근본 원인 |
| ⑤ | **`discover`는 `include`를 추론하지 않는다** — 빈 배열로 두고 사람이 채우는 필드로 규정 | 어느 파일이 우리 것인지는 도메인 지식이며, 도구 추측은 오탐을 자산에 고정시킨다 |

### D-4·D-5 동반 필수 작업 (전 명령 차단의 파급 대응)

| # | 항목 | 이유 |
|---|------|------|
| ① | 이 저장소 `.opal/code-scan.json`에 `"headerSource": "inline"` 추가 | 이 저장소 자신도 차단 대상이다(인라인 헤더 보유) |
| ② | 에러 메시지 품질 — 에러 코드 + 해결 방법 1줄 + 근거 문서 경로 | 미설정 사용자의 유일한 접점이다 |
| ③ | `brain-tool sync-header` 대응 | `code-scan scan --json`을 subprocess로 호출한다(`brain_tool.py:786-793`) → 미설정 프로젝트에서 즉시 실패하므로 실패 사유가 그대로 전달되어야 한다 |
| ④ | `pm-review-gate.md` 8번 절차 보강 | PM Gate가 `code-scan scan <file> --json`을 사용한다 |
| ⑤ | **hook은 예외 — 미설정에서도 무출력 exit 0** | PostToolUse hook의 fail-safe 계약(077 PM-7). 매 편집마다 에러가 뜨면 세션이 망가진다 |

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | **전역 `headerSource` 한 키**가 code-scan의 조회·작성 판정·검증 전 경로를 지배하게 하고(스코프 예외 없음), `scopes` 객체 형식의 include/exclude로 혼재 **디렉토리**를 지원한다 | - | 배경분석 (1)(3) |
| 범위 | **포함**: D-1~D-5 전량 · 개선 A + 보강 5건 · 동반 필수 작업 5건 · 규칙 문서 갱신 · 골든 재캡처 · 테스트<br>**제외**: `inline ↔ manifest` 자동 이관(주석 삽입·역주입) · `discover`의 include 추론 · 스코프별 정책 추천 로직 · 외부 저장소 자산화 | - | 확정 방향 |
| 제약 | ① `readonly: true`를 만나도 실행이 실패하지 않는다 — 무시 + 안내 1회(즉시 파괴 금지). 단 `manifest`로 해석하지 않는다(전역 단일 키 결정, 2026-08-02) ② 신규 도구 코드는 Node.js 무의존 ③ `~/.opal/` 직접 편집 금지 ④ 변경이력 누락 금지 ⑤ 필터는 단일 함수 계약으로만 적용 ⑥ hook은 미설정에서도 fail-safe 유지 ⑦ **제약②(기존 프로젝트 동작 변화 0)는 이번 태스크에서 의도적으로 파기된다** — 대신 "명시 설정 후 동작 변화 0"으로 재정의하고 골든을 재캡처한다 | - | D-3·D-4·D-5 |
| 완료기준 | 신규·기존 테스트 전량 GREEN + 명시 설정(`headerSource: inline`) 상태에서 8커맨드 골든 바이트 동일 + 미설정 시 전 명령이 `header_source_unset`으로 exit 1 + `readonly` 하위호환 동작 확인 + 혼재 디렉토리 픽스처에서 include/exclude가 5개 적용 지점 전부에서 일관 동작 + 규칙 문서 갱신 완료 | - | 아래 요구사항 AC |

## 요구사항

- [ ] **F-1 `headerSource` 스키마 재정의** — 무엇을: 값 2택(`inline`/`manifest`), `auto` 제거, 미설정 시 `header_source_unset` 에러, **전역 단일 키(스코프별 오버라이드 없음)** / 어디에: `code-scan.js` `loadConfig`(`:193-213`) + `header-standard.md` / 왜: D-3·D-4 / **AC**: `auto` 지정 시 명시 거부(에러 코드 반환), 미설정 시 전 명령 exit 1, **한 실행의 모드는 실행당 1값으로 확정되며 파일·스코프에 따라 달라지지 않는다**(우선순위 2층 — CLI 플래그 > 전역 config)
- [ ] **F-2 전 명령 차단 게이트** — 무엇을: 미설정 프로젝트에서 code-scan 전 서브명령이 `header_source_unset`으로 exit 1 / 어디에: `main()` 디스패치 진입부 / 왜: D-5 / **AC**: 조회 8커맨드 포함 전 명령이 동일 에러·동일 exit code로 거부되고, 에러 메시지에 해결 방법 1줄과 근거 문서 경로가 포함된다
- [ ] **F-3 `decideTarget`의 `headerSource` 존중** — 무엇을: `manifest`면 항상 매니페스트, `inline`이면 항상 인라인 / 어디에: `code-scan.js:755-792` / 왜: 배경분석 (1) / **AC**: `manifest` 설정 하에서 신규 파일·인라인 보유 파일 모두 `write_to: manifest`를 반환하고, `inline` 설정 하에서는 항상 `inline`을 반환한다
- [ ] **F-4 `scaffold`의 모드 존중** — 무엇을: `inline` 모드에서 매니페스트를 생성하지 않는다(no-op + 안내) / 어디에: `cmdScaffold` / 왜: 혼재 방지 / **AC**: `inline` 설정 프로젝트에서 `scaffold` 실행 시 `.opal/code-map/` 하위에 파일이 생성되지 않고 사유가 보고된다
- [ ] **F-5 `validate`의 모드별 판정** — 무엇을: 커버리지를 해당 소스로만 산출, `manifest` 모드에서 인라인 부재는 정상, `inline` 모드에서 매니페스트 부재는 정상 / 어디에: `cmdValidate` / 왜: 합산 커버리지의 의미 소실 해소 / **AC**: 동일 픽스처를 두 모드로 검증했을 때 커버리지 분모·분자가 각 모드의 소스만 반영하고, 반대 소스 부재가 위반으로 집계되지 않는다
- [ ] **F-6 `readonly` 제거** — 무엇을: 스키마에서 `readonly` 제거, 기존 값은 **무시**하고 deprecated 안내 1회 출력(전역 `headerSource` 설정을 안내) / 어디에: `code-scan.js`(`:761`·`:1098`·`:1107`·`:1199`) + `header-standard.md:206` + `header-rules.md` 4단 판정표 / 왜: D-2 / **AC**: `readonly: true`만 있는 기존 index로 실행해도 **전역 `headerSource`가 그대로 적용되고**(스코프 예외 없음) 안내 1줄이 출력되며, 신규 `discover` 산출물에는 `readonly`가 포함되지 않는다. 안내는 실행당 1회이며 stdout JSON을 오염시키지 않는다
- [ ] **F-7 `scopes` 객체 형식 + 정규화** — 무엇을: 문자열·객체 모두 `{path, include, exclude}`로 정규화 / 어디에: `loadConfig` + `inferScopes`(`:1093`) + index 스키마 검증(`:524` 부근) / 왜: 개선 A / **AC**: 기존 문자열 설정이 무수정으로 동작하고, 객체 형식에서 `include`·`exclude`가 스키마 검증을 통과하며, `discover` 산출물이 두 형식을 모두 기록할 수 있다
- [ ] **F-8 단일 필터 계약 `isInScope`** — 무엇을: 스코프 필터 판정 함수 1개 신설, 기존 `patternToRegex`·`isExcluded`·`hasExcludedSegment` 재사용 / 어디에: `code-scan.js` / 왜: 보강 ① / **AC**: 열거·scaffold 열거·`validate` 구조 패스·`--changed`·`target` **5개 지점이 모두 이 함수만 호출**하고, 중복 판정 로직이 존재하지 않는다
- [ ] **F-9 검출기 필터 적용** — 무엇을: `files_key_removed`·`uncovered` 검출기가 스코프 필터를 존중 / 어디에: `cmdValidate`(`:1582` 부근) / 왜: 보강 ② / **AC**: include로 걸러진 형제 파일이 매니페스트에 없어도 위반으로 집계되지 않고, 필터에 걸리지 않는 미등재 파일은 여전히 검출된다
- [ ] **F-10 스코프 중복 우선순위** — 무엇을: root 동률 시 include 매칭 스코프 승리, 양쪽 매칭 시 명시 에러 / 어디에: `resolveScope`(`:557-569`) / 왜: 보강 ③ / **AC**: root가 동일하고 include만 다른 두 스코프에서 파일이 올바른 스코프로 귀속되고, 양쪽 모두 매칭되는 설정은 전용 에러 코드로 거부된다
- [ ] **F-11 규칙 문서 갱신** — 무엇을: `header-standard.md`(스키마·`readonly` deprecated·`dir` 부분집합 의미) · `header-rules.md`(4단 판정표에서 `readonly` 제거) · `code-scan-management.md`(`headerSource` 관리·PM이 묻는 절차) · `pm-review-gate.md`(8번 절차) · `tools.md`(에러·exit code) / 왜: D-1~D-5 + 보강 ④ / **AC**: 5문서 변경이력 행 추가 + `readonly`를 판정 근거로 서술하는 문장 잔존 0건 + 규칙 문서에 개인 식별자(에이전트 이름·소유자 호칭) 신규 기재 0건
- [ ] **F-12 동반 필수 작업 5건** — 무엇을: ① 이 저장소 `headerSource: inline` 설정 ② 에러 메시지 품질 ③ `brain-tool sync-header` 실패 전달 확인 ④ `pm-review-gate.md` 절차 ⑤ hook 미설정 fail-safe / 왜: D-4·D-5 파급 / **AC**: 이 저장소에서 8커맨드가 정상 동작하고, hook에 미설정 트리 이벤트를 주입해도 stdout 0바이트·exit 0이며, `brain-tool sync-header`가 미설정 시 사유를 그대로 노출한다
- [ ] **F-13 골든 재캡처 + 회귀 방어** — 무엇을: `headerSource: inline` 명시 상태로 8커맨드 골든 재캡처, 기존 골든은 의미가 바뀌었으므로 교체 / 어디에: `tests/fixtures/golden/` / 왜: 제약⑦ / **AC**: 명시 설정 상태에서 8커맨드 출력이 재캡처 골든과 바이트 동일하고, 재캡처 전후 차이가 무엇이었는지 근거가 기록된다

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `opal/core/PRINCIPLES.md` §2: "Remove a duplicated existing pattern before introducing a new one." — 필터 판정은 단일 함수로만 존재한다
- [MUST] `~/.opal/references/harness/red-first.md` §3: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지."
- 신규 도구 코드는 Node.js 표준 모듈만 사용한다 (외부 npm 의존 금지)
- **제약②(기존 프로젝트 동작 변화 0)는 이번 태스크에서 파기된다** — D-3·D-4·D-5의 직접 결과이며, 완료기준을 "명시 설정 후 동작 변화 0"으로 대체한다
- 규칙·문서에 개인 식별자(에이전트 이름·소유자 호칭)를 기재하지 않고 역할명(PM/소유자)을 사용한다
- 커밋은 소유자가 명시 요청할 때만 수행한다

## 기술 스택

- Node.js — `opal/tools/code-scan/code-scan.js` (v1.3.3, 1,774줄, 무의존)
- `node:test` + `node:assert/strict` — 테스트 8파일 100 케이스 기존 자산
- Markdown — 규칙 SSOT 5문서

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | `headerSource` 소비 지점(`:690-699`)·`decideTarget`(`:755-792`)·`resolveScope`(`:557-569`)·검출기(`:1582`) |
| D-2 | 설계 | header-standard.md | `opal/core/references/header-standard.md` | §7 2소스 스키마·`readonly` 서술(`:206`) |
| D-3 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | 4단 기록 위치 판정표 |
| D-4 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | `headerSource` 관리 규칙·PM 관리 의무 |
| D-5 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | 8번 항목이 code-scan을 호출 |
| D-6 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py:766-798` | `sync-header`가 code-scan을 subprocess로 소비 |
| D-7 | 기획 | 077 DONE.md | `tasks/077-260727-opd-코드맵-헤더작성층/DONE.md` | 이관 결정 D-1~D-5 원문·설계 결정 6건 |
| D-8 | 기획 | 077 PLAN.md | `tasks/077-260727-opd-코드맵-헤더작성층/PLAN.md` | 스키마·경로 사상·판정 계약 원본 |
| D-9 | 소스 | code-map-hook.js | `opal/tools/code-scan/code-map-hook.js` | fail-safe 계약(미설정에서도 무출력 exit 0) |
