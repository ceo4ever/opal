# GC 컨벤션 재진단 보고서 (2차)

## §1 헤더

- 실행 일시: 2026-09-06 (KST), 2차 재진단
- 범위: 1차 지적 GC-C001/C002/C003 재판정 + Step 6e 신규 도입분(`DECLARED_HEADER_FIELDS`/`HEADER_FIELD_EXCEPTIONS`/판정 루프, `tests/test-header-history.js` TS-055·TS-056) 신규 진단. 전체 변경분 재검사는 하지 않음(1차가 49파일 전수 완료).
- 코드 루트: `.opal-worktrees/task_107` (브랜치 `feat/OP-TASK-107`). 1차 이후 `git diff --name-only HEAD` 재확인 — 1차 목록과 동일(49파일 + 미추적 `test-header-history.js` 1건), 신규 변경 없음.
- 기준 문서: `docs/CONVENTIONS.md`(단일 진입점) + `opal/core/references/header-standard.md`(§2, §2.1, §7.2 원문 소유) + `opal/core/references/harness/header-rules.md`(집행 절차).
- 1차 보고서(`GC-CONVENTION-260906.md`)는 감사 기준선으로 보존, 수정하지 않음.

## §2 요약 지표

**Critical 0 / High 1 / Medium 1 / Low 1 / Info 0**

| 심각도 | 건수 |
|--------|------|
| Critical | 0 |
| High | 1 |
| Medium | 1 |
| Low | 1 |
| Info | 0 |

(내역: GC-C001 해소 확인 0건 신규 위반 아님 / **GC-C004 신규 High 1건** / GC-C002 잔여 관측 Medium 1건 / GC-C003 미해소 Low 1건 이월)

## §3 1차 지적 재판정

### GC-C001 [1차 High] → **해소**

- **1차 지적**: `header_history` 감지기가 `resolved.changelog` 이름 하나만 리터럴 검사 — header-standard.md §2 "이름을 불문한다" 원칙과 자기 위반.
- **재현 확인**: `opal/tools/code-scan/code-scan.js:3339-3355`를 Read로 직접 확인. 현재 구현은 이름 리터럴 검사가 아니라, `DECLARED_HEADER_FIELDS`(§2 선언 8필드: module/layer/domain/description/exports/depends/note/feature, `code-scan.js:56-58`) + `HEADER_FIELD_EXCEPTIONS`(`task`/`scenarios`, `code-scan.js:64`) **밖의 모든 키**를 `Object.keys(resolved)` 전수 순회하여 비어있지 않으면 `sub:'undeclared_field'`로 위반 처리하는 방식으로 일반화되어 있다.
  ```js
  for (const key of Object.keys(resolved)) {
    if (key.startsWith('_')) continue; // _source/_sources 등 내부 메타 키
    if (DECLARED_HEADER_FIELDS.has(key)) continue;
    if (HEADER_FIELD_EXCEPTIONS.has(key)) continue;
    ...
    violations.push({ code: 'header_history', sub: 'undeclared_field', ... });
  }
  ```
- **실증 재현(테스트)**: `tests/test-header-history.js` TS-055(라인 491-509)가 `changelog`/`history`/`revisions`/`updates` 4개 임의 이름을 각각 별도 케이스로 돌려 전부 `sub:'undeclared_field'`로 탐지되는지 검증한다. 실제 실행:
  ```
  node --test tests/*.js  →  367 tests, 367 pass, 0 fail  (opal/tools/code-scan)
  ```
  전건 통과. PM이 보고한 "임시 픽스처로 임의 이름 `updates` 탐지 확인"과 동일한 결과를 TS-055에서 코드 형태로 재현 확인했다.
- **실 저장소 재현**: `node opal/tools/code-scan/code-scan.js validate --json` 직접 실행 결과 `header_history` 2건, 전부 `sub:'undeclared_field'`, `detail:'track'` — PM 실측치와 정확히 일치(`opal/tools/test-tool/tests/test_test_tool.py`, `opal/tools/tool-scan/tests/test_tool_scan.py`).
- **판정**: 이름 불문 원칙이 실제로 이름-불문 방식(화이트리스트 밖 전수)으로 구현되어 있고, 자체 테스트가 이를 명시적으로 증명한다. **해소로 판정한다.**

### GC-C002 [1차 Medium] → **해소(전제 소멸)** — 단, 설계 특성은 잔존(비위반)

- **1차 지적**: 비차단(exit 0) 설계가 GC-C001의 커버리지 공백(changelog 이름 외 누락)과 겹쳐 "이름 불문 금지" 원칙의 실효 강도를 이중으로 약화시킨다.
- **재판정**: GC-C001이 해소되어 "커버리지 공백"이라는 전제 자체가 사라졌다. 즉 이제는 "이름을 불문하고 전부 탐지"되며, 다만 그 탐지가 여전히 비차단 경고(exit code 불변, `code-scan.js:3529,3533,3537`의 `EXIT_BLOCKING_CODES`에서 `header_history` 제외 확인)라는 설계만 남는다.
- **근거**: `harness/header-rules.md:107` 원문("`code-scan validate`가 ... `header_history` 비차단 경고를 낸다(exit code 불변)")이 이 설계를 명문으로 승인하고 있으며, 1차 스스로도 "비차단 자체는 의도된 설계이므로 위반은 아니다"라고 명시했다. 결합 문제(이중 약화)의 원인이던 좁은 커버리지가 사라졌으므로, 남는 것은 "의도된 설계"뿐이다.
- **판정**: GC-C002가 지적한 결합 효과는 **해소**됐다. 설계 자체(비차단)는 위반이 아니므로 잔여 지적 없음.

### GC-C003 [1차 Low] → **미해소** (변동 없음)

- **재확인**: `docs/CONVENTIONS.md` 변경이력 표 재열람 — `v1.6.0`이 여전히 두 행(283행: 태스크 094, 287행: 태스크 106)에 중복 기재되어 있고, v1.7.0(285행)·v1.8.0(286행)이 그 사이에 끼어 순서가 역전된 상태 그대로다. 107이 추가한 v1.9.0(288행)은 각주로 "직전 행이 v1.8.0 뒤에 v1.6.0으로 기재된 것은 106의 버전 표기 오류이며 본 행은 실제 최신인 v1.8.0을 기준으로 채번했다"고 인지만 하고 106의 오기 자체는 그대로 두었다 — 1차 지적 시점과 바이트 단위로 동일.
- **판정**: **미해소**. 조치 없음이 확인된다(107의 규율 §"코드를 수정하지 마라" 및 1차 보고서의 "재작성 대상은 오너 승인 후"라는 성격상 자연스러운 결과이며, 2차 재진단도 이를 정정하지 않는다 — 진단자는 관찰만 한다).
- **이월 판단에 대한 의견**: 타당하다. semver.org의 단조성 관례는 있으나 `docs/CONVENTIONS.md` 자체가 단조성을 명문화하지 않아 Low 등급이 적절하고, 소유자 승인 없이 버전 재채번을 하는 것은 진단자·워커 권한 밖의 이력 재작성(107 STATE 소유가 아닌 106 소유 행 수정)에 해당하므로 이번 Step 범위 밖으로 이월하는 것이 맞다. 다만 다음 컨벤션 문서 개정 태스크에서 "106 v1.6.0 중복" 항목을 명시적으로 백로그화해 두는 것을 권한다(그렇지 않으면 계속 각주로만 인지되고 실제 정정은 무기한 유예될 위험이 있다).

## §4 Step 6e 신규 도입분에 대한 신규 진단

### [High] GC-C004 (신규) — `header_history`/`undeclared_field` 판정 루프가 §7.2 매니페스트 전용 필드 `draft`를 미정의 필드로 오탐

- **파일:라인**: `opal/tools/code-scan/code-scan.js:1561`(`if (hasOwn(fe, 'draft')) result.draft = fe.draft;` — manifest 모드 `resolveHeader()`가 `draft` boolean을 `resolved`에 주입) + `code-scan.js:3339-3355`(undeclared_field 판정 루프가 `DECLARED_HEADER_FIELDS`/`HEADER_FIELD_EXCEPTIONS`/`_`-prefix 3종만 예외 처리하고 `draft`는 어디에도 없음)
- **위반 절**: `opal/core/references/header-standard.md` §7.2 "패키지 매니페스트 ... 필드" 표 — `files[].draft`를 "선택, boolean, 도구가 기입하는 골격 미기입 마커"로 **명문 정의**한 필드다(`header-standard.md:259`). §2가 규정하는 것은 인라인 `@header`의 8필드이고, §7.2의 `draft`는 그와 다른 층위(매니페스트 파일 엔트리 스키마)에 속하는 별개의 정당한 필드다. 그런데 GC-C001을 고친 undeclared_field 루프는 §2 화이트리스트 하나만 기준으로 `resolved` 전체를 훑기 때문에, manifest 모드에서 `draft:true`가 있으면 이 필드까지 "미정의 필드"로 오탐한다.
- **실측 재현**: 저장소에 이미 존재하는 회귀 픽스처 `opal/tools/code-scan/tests/fixtures/violations/draft`(manifest 모드, `Draft.java`에 `draft:true`)를 대상으로 직접 실행:
  ```
  $ cd opal/tools/code-scan/tests/fixtures/violations/draft && node <code-scan.js> validate --json
  {"...,"counts":{...,"draft":1,...,"header_history":1},
   "violations":[
     {"code":"draft","file":"svc/mod/Draft.java",...},
     {"code":"header_history","sub":"undeclared_field","file":"svc/mod/Draft.java",...,"detail":"draft","tasks":1}
   ]}
  ```
  `draft` 위반(의도된 기존 위반)과 별개로, **같은 필드 때문에** `header_history`/`undeclared_field`(`detail:"draft"`)가 추가로 발생한다. 이는 §7.2가 정의한 정당한 필드를 §2 화이트리스트 잣대로 재판정한 결과로, 명백한 오탐(false positive)이다.
- **설계 의도와의 배치**: `code-scan.js:3306-3312`(draft 처리 블록) 주석 자체가 "draft는 매니페스트 전용 개념"이라고 명시하는데도, 바로 아래 3339행 undeclared_field 루프는 이 사실을 반영하지 않는다 — 같은 함수 스코프 안에서 두 정책이 충돌한다.
- **테스트 커버리지 공백**: `tests/test-header-history.js`(TS-010~TS-056)는 전부 inline 모드 픽스처만 사용하며, manifest 모드에서 `draft`와 `header_history`가 동시에 관측되는 조합을 검증하는 케이스가 **하나도 없다** — Step 6e가 새 판정축을 추가하면서 기존에 존재하던 manifest 전용 필드(`draft`)와의 상호작용을 시나리오에 넣지 않은 것으로 보인다.
- **영향 범위**: 현재 이 저장소의 `.opal/code-scan.json`은 `headerSource:"inline"`이므로(실제 `validate --json` 결과 `"headerSource":"inline"` 확인) 지금 이 순간 실 저장소에는 영향이 없다. 그러나 manifest 모드를 쓰는 프로젝트, 또는 이 저장소가 향후 manifest 모드로 전환하거나 scaffold 직후(=항상 `draft:true`로 시작, `code-scan.js:269` 근방 `S-10` 테스트가 이를 보증) 상태를 거치는 모든 워크플로에서, 매 파일마다 정당한 `draft:true` 골격이 자동으로 `header_history` 경고를 유발한다 — 골격 미기입이라는 정상 임시 상태를 "이력 위반"으로 오분류하는 것이므로 신호 대 잡음비를 해친다.
- **자기 위반 성격**: GC-C001이 지적한 결함의 성격("이름을 불문한다"는 원칙을 지키려다 다른 층위 필드를 못 가르는 문제)과 구조적으로 같은 종류의 결함이다 — 이번엔 반대 방향으로, §2 밖 필드를 무조건 위반 취급하다가 §7.2가 별도로 정의한 필드를 오분류했다.
- **auto_fixable**: false (판정 루프에 최소 1개 예외 추가 또는 모드별 화이트리스트 분리 필요 — 재설계 성격)
- **수정 방안 제안**: `HEADER_FIELD_EXCEPTIONS`에 `draft`를 추가하거나(다만 `draft`는 `task`/`scenarios`와 성격이 다르므로 별도 상수 `MANIFEST_ONLY_FIELDS` 신설 후 `mode === 'manifest'`일 때만 예외 처리하는 것이 §7.2/§2 층위 분리를 더 정확히 반영함), undeclared_field 루프 앞단에서 `mode`를 참조해 manifest 전용 필드를 먼저 제외.
- **참조 URL**: 참조: TBD — 프로젝트 내부 규칙(header-standard.md §7.2), 외부 표준 없음

### `DECLARED_HEADER_FIELDS`/`HEADER_FIELD_EXCEPTIONS` 자체의 정당성 — 개별 확인 결과

- **`DECLARED_HEADER_FIELDS`(8필드: module/layer/domain/description/exports/depends/note/feature)**: `header-standard.md` §2 필드 정의 표(라인 15-23)와 1:1 대조 — 정확히 일치한다. 위반 없음.
- **`HEADER_FIELD_EXCEPTIONS`(`task`/`scenarios`)**: §2 원문 "다만 `task`·`scenarios`처럼 이력 필드가 아니라 다른 도구(예: 테스트 자산)가 참조하는 필드는 이 금지의 대상이 아니다"(`header-standard.md:33`)와 정확히 일치 — 문서가 명시적으로 이 두 필드를 예외로 든다. 근거 있는 예외로 판정한다(위반 아님). GC-C004(위)에서 지적한 것과 달리, 이 예외 자체는 정당하다 — 문제는 `draft`가 이 예외 집합에 **없다**는 쪽이다.
- **`key.startsWith('_')` 스킵**: `resolveHeader()`(`code-scan.js:1579-1580`)가 `result._source`/`result._sources`를 직접 대입하는 코드를 확인했다 — 이 두 키는 `@header`에 사용자가 기입하는 필드가 아니라 `resolveHeader` 자신이 4단 상속 판정 결과를 부기하는 **내부 메타데이터**다(§7.3 `_source` 계약 문서화 확인, `header-standard.md:264`). inline 모드에서는 애초에 `_source`가 붙지 않는다(§7 표 "붙지 않음" 명시). 사용자가 실제로 `_`로 시작하는 필드를 `@header`에 authored할 가능성과 무관하게, 이 스킵은 도구 자신이 추가한 부기 값을 도구 자신이 되짚어 오탐하지 않기 위한 것으로 근거가 있다. 다만 이 스킵이 "사용자가 실제로 `_xyz`라는 이름의 필드를 넣는 경우"까지 관대하게 통과시키는 부작용은 있다 — 그러나 §2가 정의한 8필드 어디에도 `_`로 시작하는 이름이 없고, `_`로 시작하는 필드명을 authored하는 것 자체가 이례적이므로 실질 위험은 낮다고 판단해 **Low 신호로도 별도 등재하지 않는다**(근거는 있으나 미세한 잔여 관용 지점으로만 기록).

## §5 문서 업데이트 제안

- **[빈도 트리거]**: 미해당(N=3 기준 반복 fingerprint 없음).
- **[새 카테고리 트리거]**: 미해당(GC-C004도 기존 §@header/§7.2 절 하에서 다룰 수 있는 사안).
- **[심각도 트리거]**: High 1건(GC-C004, 신규) 발생 — §5에 분리 표기. 1차가 제안한 "문서 개정과 도구 구현의 동시성 담보 장치 부재" 보완이 이번에도 반복되는 패턴으로 관측된다: §2 문구를 일반화(이름 불문)하면서 §7.2(매니페스트 전용 필드)와의 경계를 검증하는 테스트가 따라가지 못했다. `header-rules.md` 또는 PLAN 게이트에 "판정 루프 변경 시 §2/§7 두 층위 모두에 대한 회귀 케이스 동반"을 명문 조건으로 추가하는 것을 제안한다.

## §6 track 2건 이월 판단에 대한 의견

- **재현**: `node opal/tools/code-scan/code-scan.js validate --json`(실 저장소, `headerSource:"inline"`) 실행 결과 `header_history` 2건, 전부 `sub:'undeclared_field'`, `detail:'track'` — `opal/tools/test-tool/tests/test_test_tool.py`, `opal/tools/tool-scan/tests/test_tool_scan.py`. PM 실측과 정확히 일치.
- **의견**: 이월이 타당하다. `header_history`는 설계상 비차단(exit 0)이며, 이번 재진단(§3 GC-C002)에서 확인했듯 이 설계 자체는 문서(`header-rules.md:107`)가 승인한 것이다. 또한 대상 2파일은 이번 태스크(107)의 정리 대상 43파일 목록 밖에 있는 기존(pre-existing) 위반으로, 107의 책임 범위가 아니다. 다만 §5에서 지적했듯 이 `track`이라는 이름 역시 "이력 전용 필드"의 실사례이므로, `track` 이월 자체와 별개로 **후속 정리 태스크의 백로그 항목으로 명시 등재**할 것을 권한다(비차단 경고로 계속 존재는 하지만, 아무도 후속 조치를 명시적으로 추적하지 않으면 GC-C003과 같은 방식으로 무기한 방치될 위험이 있다).

---

지적 총 2건(GC-C004 신규 High 1 / GC-C003 이월 Low 1), Critical 0, Medium 0(GC-C002는 전제 소멸로 해소), Info 0.
1차 지적 3건 중 해소 2건(GC-C001, GC-C002) · 미해소 1건(GC-C003, 이월) · 신규 발견 1건(GC-C004, High).
