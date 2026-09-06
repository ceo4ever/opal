# TASK: @header 워커 기입 필드 작성 기준 신설 + 이력 분리

> 작성일: 2026-09-06 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`@header`의 **워커 기입 5필드** 중 작성 가이드가 없는 4필드(`description`·`depends`·`note`·`feature`)에 기준을 신설하고, **이력은 `@header`에 남기지 않고 git이 갖는다**는 원칙을 규정·도구·기존 자산 3층에 일관 적용한다.

## 배경

태스크 106이 `code-scan`의 헤더 창문 결함(문자/바이트 비대칭)을 고치면서 **창문 재포화**가 시간 문제임이 드러났다. 원인을 추적하니 도구 결함이 아니라 **작성 기준의 공백**이었다.

## 배경 분석 (대화에서 도출)

### (1) 5필드 중 가이드는 `exports` 하나뿐

`opal/core/references/header-standard.md`는 7개 절인데 **필드 작성 기준은 §4 하나**다.

| 필드 | 안내 | 분량 |
|------|------|------|
| `exports` | **§4 layer별 작성 가이드** | 21 layer × 담는 내용 × 예시 = 21행 표 |
| `description` | §2 정의 1줄 | "파일의 역할 한 줄 요약" |
| `depends` | §2 정의 1줄 | 코드/문서 구분 + 예시 1개 |
| `note` | §2 정의 1줄 | "추가 메모 (작업 흔적, 특이사항)" |
| `feature` | §2 정의 1줄 + §7 조회 키 참조 | 형식만 |

- 다른 참조 문서에도 없다 — `opal/core/references/` 전수 grep 0건.

### (2) 그 공백이 `description` 누적의 직접 원인

- `description`은 "한 줄"만 말하고 **한 줄이 아닌 것이 갈 곳**을 지정하지 않는다.
- `note`는 "작업 흔적"이라 하는데 **무엇을 어떤 형식으로**인지 기준이 없다.
- 실측: **`note` 필드 71건 전건 0자.** 규정상 자리가 있는데 아무도 쓰지 않고 `description`에 쌓았다.
- 즉 **워커가 규정을 어긴 것이 아니라 규정이 갈 곳을 지정하지 않았다.**

### (3) `exports`만 지켜지는 이유 — 규정 + 도구 집행

- `exports`는 layer별 표로 명시되고 `code-scan validate`가 `exports_not_found`로 **텍스트 존재를 대조**한다.
- 규정과 도구 검증이 둘 다 있는 유일한 필드이며 실제로 정합이 유지된다(106 ADD-1 실측: `code-scan.js` `exports` 10건이 `module.exports` 10건과 문자열까지 일치).
- 나머지 4필드는 규정도 얕고 도구 검증도 없다 — `description`은 비어 있지만 않으면 통과한다.

### (4) 증가 동인은 코드량이 아니라 이력 — 상관 실측

표본 71건 상관계수:

| 축 | 상관 |
|----|------|
| 태스크번호 수 ↔ `description` 길이 | **+0.76** (이력 누적) |
| 파일 줄수 ↔ `description` 길이 | +0.66 (겉보기) |
| 파일 줄수 ↔ `exports` 개수 | +0.69 (코드량 축 대조군) |

- **이력성 12건을 제외하면 파일 줄수 ↔ `description` 상관이 +0.66 → +0.39로 반감**하고 중앙값 177자다.
- 같은 규모 대조: `state_tool.py` 3558줄/**11791자**(태스크 26개) vs `test_brain.py` 3219줄/**1151자**(태스크 0개) — **10배 차이**의 원인은 크기가 아니라 이력이다.
- ⇒ **역할 요약은 코드가 늘어도 늘지 않는다.** 코드량 축은 `exports`가 담당하도록 이미 설계돼 있다.

### (5) 프레임워크 SSOT가 이미 방향을 갖고 있다

`opal/core/references/opal-doc-standard.md:28`: "실행 지시문은 코드처럼 제자리에서 갱신되고 **변경 이력은 git이 갖는다**. 다만 **버전 번호**는 문서 안에 남는다"

- `.md` 실행 지시문에 대해 확립된 이 원칙을 코드 `@header`에도 적용하는 것이 이번 작업이다.

### (6) 정리 대상 실측 — 12건 / 27,298자

| `description` | 태스크# | 파일 |
|---|---|---|
| 11791자 | 26 | `opal/tools/state-tool/state_tool.py` |
| 7049자 | 19 | `opal/tools/state-tool/tests/test_state_tool.py` |
| 2033자 | 20 | `dashboard/backend/tests/test_routers.py` |
| 1213자 | 4 | `opal/tools/brain-tool/brain_tool.py` |
| 948자 | 7 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` |
| 924자 | 5 | `opal/tools/state-tool/todo_mirror_hook.py` |
| 877자 | 8 | `dashboard/backend/tests/test_stats.py` |
| 828자 | 5 | `opal/tools/test-tool/lib/scenario.py` |
| 553자 | 3 | `opal/tools/brain-tool/tests/test_brain_tool.py` |
| 473자 | 15 | `opal/tools/memory-tool/tests/test_memory_tool.py` |
| 430자 | 6 | `opal/tools/opal-agent/tests/test_opal_agent.py` |
| 179자 | 6 | `opal/tools/improve-tool/tests/test_improve_tool.py` |

## 확정된 설계 방향 (대화에서 합의)

- **[결정]** 이력은 `@header`에 남기지 않는다 — **git이 추적 가능하므로** 자산 안에 중복해 두지 않는다. `note`로 옮기는 것도 아니다(블록 총량이 그대로여서 창문 재포화를 늦출 뿐이다).
- **[결정]** `description` **글자수 상한은 두지 않는다.** 길이는 잘못된 축이다 — 역할 요약은 코드량과 무관하며, 잡아야 할 것은 **이력이 들어가는 성질** 자체다.
- **[결정]** 도구 검증은 **태스크번호 패턴 감지**로 설계한다 — 길이가 아니라 성질을 본다.
- **[결정]** `header-standard.md` **§4 `exports` 가이드 형식을 준용**해 4필드 가이드를 신설한다.
- **[사실]** `note` 필드는 프로젝트 3스코프 전수 109파일 중 **2건에만 존재**하며 그 2건은 비어 있지 않다(`code-map-hook.js` 625자·`code-scan.js` 1712자, 둘 다 이력성 서술). `feature` 필드는 **0/109건**(필드 선언 자체가 없다). **[정정 107/ANALYSIS]** 당초 기재한 「71건 전건 0자」는 전수 재측정과 불일치하여 철회한다 — 문제는 '자리가 있는데 안 쓴다'가 아니라 '자리가 거의 선언되지 않으며, 선언된 소수는 이미 이력으로 오염돼 있다'이다.
- **[사실]** `opal-doc-standard.md:28`이 "변경 이력은 git이 갖는다"를 `.md` 실행 지시문에 대해 이미 확립했다.
- **[사실]** 상관 실측상 `description` 증가 동인은 코드량(+0.39)이 아니라 이력 누적(+0.76)이다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `@header` 워커 기입 4필드(`description`·`depends`·`note`·`feature`)에 작성 기준을 신설하고, 「이력은 git이 갖는다」를 규정·도구 검증·기존 자산 3층에 일관 적용한다 | - | `opal/core/references/header-standard.md` §2·§4 · `opal/core/references/opal-doc-standard.md` §0 |
| 범위 | **포함** — ① `header-standard.md`에 4필드 작성 가이드 신설(§4 형식 준용) ② 「이력 비기재」 원칙 명문화 + 이력의 소재(git·태스크 산출물) 지정 ③ `code-scan validate`에 태스크번호 패턴 감지(**비차단 경고**) 신설 ④ 기존 이력성 **진성 23건** `description`·`note` 정리 + **⑤ `changelog` 필드 전건 제거(28파일·81엔트리)**. **[확정 107/캡틴 2차]** PLAN이 임계값을 축 정의에서 2로 재유도하면서 진성 집합이 18 → **23건**으로 바뀌었고, 캡틴이 23건 전건 정리를 확정했다(D-REQ-1). 내역 = TASK 12건 + ANALYSIS 진성 6건(`models.py`·`config.py`·`main.py`·`brain_session.py`·`test_config.py`·`code-map-hook.js`) + PLAN 확대분 5건(`AppShell.tsx`·`backlog_tool.py`·`test-shard.js`·`test-feature.js`·`test-validate.js`). **[확정 107/캡틴 3차]** `@header`에 문서화되지 않은 `changelog` 필드가 28파일에 81엔트리 실려 있음이 EXECUTE 중 발견됐다(`header-standard.md` §2 필드 정의에 **없는 필드**). 「이력은 @header에 남기지 않는다」의 가장 큰 잔존이므로 전건 편입한다 — 정리 대상 파일은 23 ∪ 28 = **43파일**. **제외** — `description` 글자수 상한, `note`로의 이력 이관, `.md` 문서의 `## 변경이력` 표 A안(별건), `HEADER_READ_BYTES` 재조정 | ④의 정리 방식(일괄 vs 단계) | `opal/core/references/harness/header-rules.md` §워커 권한 경계 |
| 제약 | ① `~/.opal/` 직접 편집 금지 — 소스 수정 후 install 재배포 ② `exports`·`module`·`layer`·`domain` 기존 규정 무변경 ③ 도구 검증은 **비차단**(`exports_not_found` 계열) — CLOSE를 새로 막지 않는다 ④ 정리로 소실되는 이력은 git·태스크 DONE.md에 이미 존재함을 확인한 뒤 제거한다 ⑤ `code-scan` 테스트 344건·`state-tool` **400 passed/3 skipped**(당초 383은 낡은 수치 — 107/ANALYSIS 실측 정정) 회귀 0건 ⑥ `VERSION` 상수는 083이 테스트 2건에 핀했으므로 상향 시 단언 갱신 동반(106 ADD-1 교훈) | ⑥ 상향 여부 | `docs/CONVENTIONS.md` §네이밍 규칙 · `opal/tools/code-scan/tests/test-shard-policy.js` |
| 완료기준 | R-1~R-5 AC 전건 충족 + `code-scan` 344 passed/0 failed · `state-tool` 400 passed/3 skipped 회귀 0건 + 정리 후 `header_history` 탐지 **0건**(진성 23건 `description`·`note` 전건 해제 **AND** `changelog` 필드 보유 파일 0건) + 신설 경고가 **정리 전 진성 23건을 탐지하고 `F-00X` 기능번호·`TS-0XX` 시나리오 id 오탐 0건** | - | 본 문서 §배경 분석 (6) · `ANALYSIS.md` §7 Q2(18건 분류: 진성 6/오탐 9/경계 3) |

## 요구사항

- [ ] **R-1 4필드 작성 가이드 신설** — 무엇을: `description`·`depends`·`note`·`feature` 각각의 「담는 것 / 담지 않는 것 / 예시」를 §4 `exports` 가이드 형식으로 신설. 어디에: `opal/core/references/header-standard.md`. 왜: 배경 분석 (1)(2) — 5필드 중 `exports`만 가이드가 있고 그 공백이 누적의 원인. **AC**: (a) 4필드 각각에 「담는 것」·「담지 않는 것」·예시 3요소가 존재한다 (b) `description`의 「담지 않는 것」에 **변경 이력·태스크 번호**가 명시된다 (c) `note`의 「담지 않는 것」에도 이력이 명시된다(대체 저장소가 아님) (d) §2 필드 정의 표와 모순되지 않는다 (e) 기존 §4 `exports` 가이드 원문 무변경
- [ ] **R-2 「이력은 git이 갖는다」 명문화** — 무엇을: `@header`에 이력을 남기지 않는 원칙과 이력의 실제 소재(git 로그·태스크 폴더 DONE.md)를 명시. 어디에: `header-standard.md` + `opal/core/references/harness/header-rules.md` §파일 수정 시. 왜: 확정 방향 1항. **AC**: (a) 원칙 문장이 `opal-doc-standard.md:28` 원문을 인용해 근거를 밝힌다 (b) 이력 소재 2곳(git·태스크 산출물)이 명시된다 (c) `header-rules.md` §파일 수정 시 갱신 대상 필드 표와 정합한다 (d) 두 문서가 서로 다른 말을 하지 않는다 (f) **[신설 107/캡틴 3차]** 원칙의 적용 범위가 **`@header` JSON 블록 전체**로 명시된다(당초 초안의 「워커 기입 5필드 한정」은 `changelog` 같은 **이력 전용 필드 신설**을 막지 못한다). `header-standard.md` §2 필드 정의에 「`@header`에 이력 전용 필드를 신설하지 않는다 — `changelog`·`history`·`revisions` 등 이름을 불문한다」가 명문화된다 (e) **[신설 107/ANALYSIS Q1]** `docs/CONVENTIONS.md` §@header 규칙의 「변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 **헤더 내 변경이력 라인**으로 갱신한다」 문구에서 헤더 내 이력 갱신 어구가 제거되고 R-2 원칙과 정합하는 문구로 교체된다 — 이 문서는 「개발 작업 시 항상」 참조되는 [MUST] 등재 문서이므로(`docs/PROJECT.md` §프로젝트 문서) 미개정 시 다음 태스크 워커가 이 문구를 근거로 이력을 다시 쌓는다
- [ ] **R-3 태스크번호 패턴 감지 신설** — 무엇을: `code-scan validate`가 `description`의 태스크번호 패턴을 감지해 **비차단 경고**를 낸다. 어디에: `opal/tools/code-scan/code-scan.js`. 왜: 확정 방향 3항 — 길이가 아니라 성질을 본다. **AC**: (a) 임계값 이상이면 경고가 나오고 **exit code는 불변**(차단 0건) (b) 경고 항목이 `violations`가 아닌 별도 채널 또는 비차단 `sub`로 분류된다 (c) 정리 전 **진성 23건을 전건 탐지**하고 `F-00X` 기능번호·`TS-0XX` 시나리오 id **오탐 0건** — 단순 3자리 카운트로는 성립하지 않는다(임계값 3에서 30건이 걸리고 그중 9건이 순수 오탐, `ANALYSIS.md` §7 Q2). 정규식은 F-code·TS-id를 구조적으로 배제하도록 재설계한다 (d) `code-scan` 테스트 344건 회귀 0건 (e) **[신설 107/캡틴 3차]** `changelog` 필드 **존재 자체**를 `sub:"changelog"`로 감지한다 — 임계값 판정 대상이 아니다. 필드 이름이 곧 이력 선언이므로 엔트리 1개라도 위반이다
- [ ] **R-4 기존 진성 23건 정리 + `changelog` 28건 제거** — 무엇을: 이력성 `description` **23건**에서 이력을 제거하고 역할 한 줄로 되돌린다. 어디에: §배경 분석 (6) 12파일 + `ANALYSIS.md` §7 Q2 진성 6파일(`dashboard/backend/models.py`·`dashboard/backend/config.py`·`dashboard/backend/main.py`·`dashboard/backend/adapters/brain_session.py`·`dashboard/backend/tests/test_config.py`·`opal/tools/code-scan/code-map-hook.js`) + `PLAN.md` D-REQ-1 확대분 5파일(`dashboard/frontend/src/components/app-shell/AppShell.tsx`·`opal/tools/backlog-tool/backlog_tool.py`·`opal/tools/code-scan/tests/test-shard.js`·`opal/tools/code-scan/tests/test-feature.js`·`opal/tools/code-scan/tests/test-validate.js`). 왜: 규정 신설 직후 위반 상태를 남기지 않는다 — 12건만 정리하면 프레임워크 자산이 신설 규정을 위반한 채 남는다. **AC**: (a) 23건 전건이 이력성 판정에서 해제된다(정리 후 `header_history` hits 0) (b) 각 파일의 **역할 한 줄**이 보존된다(내용 소실 아님) (c) 제거되는 이력이 git 로그 또는 태스크 DONE.md에 존재함을 확인한 근거가 산출물에 남는다 — 12건 중 3건은 `ANALYSIS.md` §7 Q5에서 확인 완료, 나머지 20건은 EXECUTE에서 수행 (d) `@header` JSON 파싱이 23건 전건 정상 (e) `exports`·`module`·`layer`·`domain` 무변경 (g) **[신설 107/캡틴 3차]** `changelog` 필드를 보유한 **28파일 전건에서 그 필드를 제거**한다(81엔트리). 제거 전 각 엔트리의 이력이 git 로그 또는 `tasks/{NNN}-*/DONE.md`에 실재함을 확인하고 근거를 `HISTORY-EVIDENCE.md`에 남긴다 — AC(c)와 동일 강도(해시 resolve·경로 실존) (f) `note` 필드 중 **이력 누적 판정에 걸리는 건**을 함께 제거한다(R-2 원칙은 `note`에도 동일 적용). **[정정 107/PLAN]** 대상은 실측 **1건**(`opal/tools/code-scan/code-scan.js`, distinct `077,080,082,083`)이다 — `code-map-hook.js`의 `note`는 태스크 080 단발 인용이라 이력 누적이 아니며, 당초 2건 지목은 「`note`가 존재하는 파일 수(2건)」와 「이력성인 파일 수(1건)」를 혼동한 것이다
- [ ] **R-5 회귀 보존** — 무엇을: 기존 테스트·게이트 무변경 확인. 어디에: `code-scan` 테스트 12파일 · `state-tool` 테스트. 왜: 도구·규정 변경이 기존 파이프라인을 깨지 않아야 한다. **AC**: (a) `code-scan` **344 passed / 0 failed** (b) `state-tool` **400 passed / 3 skipped / 0 failed**(107/ANALYSIS 실측 — 당초 383 정정) (c) 메타 테스트 3건(S-19·TS-062·TS-080) 통과 (d) `validate --changed` 차단 위반 증가 0건

## 제약 조건

- **배포 경계**: `~/.opal/` 배포본을 직접 수정하지 않는다. 소스 수정 후 install로 재배포한다.
- **비차단 원칙**: R-3 경고는 CLOSE를 새로 막지 않는다 — `exports_not_found`·`manifest_oversize` 계열의 비차단 신호로 둔다.
- **이력 소실 금지**: R-4 정리 전에 제거 대상 이력이 git·태스크 산출물에 존재함을 확인한다.
- **`VERSION` 핀 주의**: `code-scan.js`의 `VERSION`은 `test-shard-policy.js:1519`·`test-shard.js:696`이 `'1.6.0'`으로 핀한다. 상향 시 두 단언 갱신이 동반된다(106 ADD-1에서 이를 놓쳐 테스트 5건이 깨진 전례).
- **메타 테스트 예산**: `test-validate.js` 등 확장 시 메타 3건이 중첩 실행하므로 신설분 실행 시간을 최소화한다.

## 기술 스택

- Markdown (`header-standard.md`·`header-rules.md`)
- Node.js — `opal/tools/code-scan/code-scan.js` (v1.6.0), `tests/*.js` 12파일
- Python — 정리 대상 8파일 (`state_tool.py`·`brain_tool.py` 등)
- TypeScript/Python — `dashboard/backend/tests/*` 2파일

## 관련 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 설계 | @header 표준 | `opal/core/references/header-standard.md` | §2 필드 정의·§4 exports 가이드 — R-1·R-2 개정 대상 |
| D-2 | 설계 | EXECUTE @header 규칙 | `opal/core/references/harness/header-rules.md` | §파일 수정 시 갱신 대상 필드·§워커 권한 경계 — R-2 개정 대상 |
| D-3 | 설계 | 문서 표준 | `opal/core/references/opal-doc-standard.md` | `:28` "변경 이력은 git이 갖는다" — R-2 근거 원문 |
| D-4 | 소스 | code-scan 도구 | `opal/tools/code-scan/code-scan.js` | R-3 신설 대상 (`validate` 경로) |
| D-5 | 소스 | code-scan 테스트 | `opal/tools/code-scan/tests/` 12파일 | R-3·R-5 회귀 기준(344 passed) |
| D-6 | 산출물 | 태스크 106 | `tasks/106-260904-opd-코드맵-스킬신설-하네스개정/DONE.md` · `ADD_DONE-1.md` | §8 이월 1·2번이 이 태스크의 발원 |
| D-7 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | §변경이력·§네이밍 — 정합 확인 |
