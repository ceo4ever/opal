# PLAN: @header 워커 기입 필드 작성 기준 신설 + 이력 분리

> 작성일: 2026-09-06 | 입력: TASK.md(캡틴 확정 반영본), ANALYSIS.md
> 모드: Multi-Feature (F-001 ~ F-004)

## 결론

- **축 정의를 먼저 세우고 정규식을 유도했다** — `description`/`note`가 담은 것이 **단발 출처 인용**(이 자산이 어느 태스크에서 왔는가, 1개)인가 **이력 누적**(서로 다른 시점의 변경이 겹겹이 쌓임, 2개 이상)인가가 축이며, 임계값 **2**는 이 정의에서 곧바로 나온다(1=출처 / 2+=이력). 길이·raw 3자리 카운트는 축이 아니다.
- **판정 절차는 "구조적 마스킹 → 태스크 토큰화 → distinct 카운트"** 3단이다. 마스킹 4종(경로:줄번호 / 소수·버전·절번호 / 접두 하이픈 식별자와 그 나열·범위 / 수량 표기)이 `F-00X`·`TS-0XX`를 **구조적으로** 배제하므로 오탐을 사후 필터로 걷어내지 않는다.
- **전수 실측(109파일, E1) 결과 진성 18건 전건 탐지 · ANALYSIS §7 Q2 오탐 9건 전건 배제**를 달성했다. 임계값 2는 선택이 아니라 강제다 — 3으로 올리면 진성 18건 중 6건(`code-map-hook.js`·`brain_session.py`·`main.py`·`models.py`·`test_stats.py`·`test_opal_agent.py`, 전부 distinct 2)이 탈락해 R-3 AC(c)가 즉시 깨진다.
- **경계 3건은 축이 자동으로 갈랐다** — `test-feature.js`·`test-validate.js`는 서로 다른 실태스크 2개(077·080)를 병기하므로 **진성으로 재분류(탐지)**, `DashboardPage.stats.test.tsx`는 `[T103]` 단발 + `TS-142/143`(마스킹)이므로 **미탐지**. 규칙을 사례에 맞춘 것이 아니라 축이 결론을 냈다.
- **탐지 총계 23건 = 정리 집합 23건이다** — 초안은 캡틴 확정 18건과의 차 5건을 잔여로 두려 했으나, **D-REQ-1이 (나)로 확정**되어 잔여 0건으로 닫는다. 5건은 F/TS 오탐이 아니라 ANALYSIS의 거친 정규식(raw 3자리 ≥3)이 놓친 **진성**이며 3건은 ANALYSIS 30건 목록에도 없었다. 정리 후 `header_history` 탐지 **0건**이 완료기준이다.
- **P-2 결정: 설정 미노출(상수 하드코딩)** — 임계값 2는 축 정의에서 유도된 상수이지 튜닝 파라미터가 아니고, 비차단 경고는 프로젝트별 협상 압력이 없으며, `.opal/code-scan.json` 스키마 확장은 검증 경로·`header-standard.md` §7.1 필드 표·`discover`/`init` 시드까지 파급된다.
- **P-3 결정: Step 6(전수 git log 증거 수집)으로 배정**하고 `HISTORY-EVIDENCE.md` 1건을 산출해 R-4 AC(c)를 문서로 닫는다.
- **`VERSION` 상향 없음** — 기존 필드 스키마·CLI 인터페이스 무변경 additive 확장이며, 핀 2건 갱신은 106 ADD-1에서 테스트 5건을 깬 전례가 있어 얻는 것 없이 위험만 진다.
- 분량 초과 사유: R-3 정규식 재설계가 이 태스크의 단일 최대 난제여서 §3.2에 실측 근거표(23건 탐지·9건 배제)를 함께 실었다.

---

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| **[결정]** 이력은 `@header`에 남기지 않는다 — git이 추적 가능하므로 자산 안에 중복해 두지 않는다. `note`로 옮기는 것도 아니다 | 유효 | - |
| **[결정]** `description` 글자수 상한은 두지 않는다 | 유효 | - |
| **[결정]** 도구 검증은 태스크번호 패턴 감지로 설계한다 | 유효 | - |
| **[결정]** `header-standard.md` §4 `exports` 가이드 형식을 준용해 4필드 가이드를 신설한다 | 유효(부분 준용) | §4는 3열(layer/담는 내용/예시)이라 「담지 않는 것」 열이 없다 — 표 형식은 유지하고 열만 4열로 확장한다(ANALYSIS Q6, `opal/core/references/header-standard.md:133-159`) |
| **[사실]** `note` 필드는 3스코프 전수 109파일 중 2건에만 존재하며 비어 있지 않다. `feature`는 0/109건 | 유효(재확인) | E1 재측정: `node opal/tools/code-scan/code-scan.js scan --json` 109파일 — `note` 보유 = `opal/tools/code-scan/code-map-hook.js`(625자)·`opal/tools/code-scan/code-scan.js`(1712자), `feature` 0건 |
| **[사실]** `opal-doc-standard.md:28`이 "변경 이력은 git이 갖는다"를 `.md` 실행 지시문에 대해 이미 확립했다 | 유효 | `opal/core/references/opal-doc-standard.md:28` |
| **[사실]** `description` 증가 동인은 코드량이 아니라 이력 누적이다 | 유효 | ANALYSIS §확정 입력 판정 승계(상류 확인 완료) |
| **[확정 107/캡틴]** 정리 대상 집합 = 진성 **23건** 전건 (P-5 → D-REQ-1로 갱신 확정) | 유효 | `TASK.md` §범위 ④ · R-4 · 본 문서 §D-REQ-1 |
| **[확정 107/캡틴]** `docs/CONVENTIONS.md` 편입 (P-1 닫힘) | 유효 | `TASK.md:103` R-2 AC(e) |
| **[확정 107/캡틴]** `note` 2건 포함 (P-4 닫힘) | 유효 | `TASK.md:105` R-4 AC(f) |

> **[MUST] 확정은 검증 면제가 아니라 재설계 면제다** — 위 항목은 재도출하지 않았고, 3값 판정만 수행했다.

### 소유자 보고 — 상류 문서와 실측이 어긋난 지점

| # | 지점 | 상류 기재 | 실측(E1) | 처리 |
|---|------|----------|---------|------|
| RPT-1 | R-5 AC(b) `state-tool` 회귀 기준 | `TASK.md:106` "400 passed / 3 skipped / 0 failed" | 일치 — ANALYSIS가 이미 383→400 정정 반영 | 그대로 사용 |
| RPT-2 | R-5 AC(a) `code-scan` 회귀 기준 | `TASK.md:106` "344 passed / 0 failed" | 344 passed / 0 failed 일치. 단 **F-002가 테스트를 신설**하므로 종료 시점 총계는 344 + 신설분이 된다 | AC 문구를 「기존 344건 전건 통과 + 신설분 전건 통과」로 읽는다(§5.2에 명시) |
| RPT-3 | 탐지 집합 규모 | ANALYSIS Q2 = 30건(raw 3자리 ≥3) 중 진성 6·오탐 9·경계 3 | 재설계 규칙(§3.2.2) 적용 시 **23건** 탐지 | **해소** — D-REQ-1 (나) 확정으로 정리 집합 = 탐지 집합 23건 |
| RPT-4 | ANALYSIS 30건 목록의 완전성 | 30건이 후보 전집합 | `AppShell.tsx`·`backlog_tool.py`·`test-shard.js` 3건은 raw 3자리 distinct가 2뿐이라 30건 목록에 **없었으나** 축 기준으로는 진성이다 | **해소** — 23건에 포함되어 Step 12b·13b·13c에서 정리 |

### 소유자 결정 필요 (decision_required)

| ID | 쟁점 | 선택지 | PLAN 권고 | 미결 시 기본 동작 |
|----|------|--------|----------|-----------------|
| D-REQ-1 | 탐지 23건 − 정리 18건 = **잔여 5건**(`dashboard/frontend/src/components/app-shell/AppShell.tsx` · `opal/tools/backlog-tool/backlog_tool.py` · `opal/tools/code-scan/tests/test-shard.js` · `opal/tools/code-scan/tests/test-feature.js` · `opal/tools/code-scan/tests/test-validate.js`)을 이번 태스크에서 함께 정리할 것인가 | (가) 18건 유지 + 잔여 5건을 DONE.md §이월에 기록 / (나) 23건으로 확대 | **(나) — 캡틴 확정(2026-09-06)**. 캡틴이 18건을 고른 선택지의 근거 문구가 「규정 신설 직후 위반 0건 상태를 만든다」였고, 임계값 재설계로 진성 집합이 23건이 된 이상 5건을 남기면 그 근거가 성립하지 않는다 | (나) 적용 — **Step 12b·13b·13c 신설**(+3 Step. PLAN 초안은 +2로 추산했으나 잔여 4파일을 한 Step에 묶으면 §산출량 상한 3파일을 넘어 분할이 강제된다). Step 14 기대 잔여를 **0건**으로 갱신 |

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`@header` 워커 기입 5필드 중 가이드가 없는 4필드(`description`·`depends`·`note`·`feature`)에 「담는 것 / 담지 않는 것 / 예시」 작성 기준을 신설하고, **「이력은 `@header`에 남기지 않는다 — git과 태스크 산출물이 갖는다」** 원칙을 ① 규정 3문서 ② `code-scan validate` 비차단 감지 ③ 기존 진성 23건 정리의 3층에 일관 적용한다. 규정 신설 직후 프레임워크 자산이 그 규정을 위반한 상태로 남지 않게 하는 것이 이 태스크의 완결 조건이다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 4필드 작성 기준 + 「이력은 git이 갖는다」 3문서 명문화 | R-1, R-2 | P0 | 없음 |
| F-002 | `code-scan validate` 이력 누적 패턴 비차단 감지 | R-3 | P0 | F-001(축 정의가 규정 원문에 실려야 도구가 그 문서를 근거로 인용) |
| F-003 | 기존 진성 23건 `description`·`note` 이력 정리 | R-4 | P0 | F-001(작성 기준), F-002(측정 도구) |
| F-004 | 회귀 보존 검증 | R-5 | P0 | F-002, F-003 |

### 1.3 기능 의존 그래프

```
F-001 ──┬──> F-002 ──┬──> F-003 ──> F-004
        └────────────┘        │
                              └──────────^
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 `cmdValidate` 신규 위반 push | **exit code 계약** — 새 `code`가 `blockingViolations` 필터에서 제외되지 않으면 이력 보유 자산 23건이 전부 CLOSE를 차단한다(비차단 원칙 정면 위반) | P0 | L2(CLI 블랙박스, exit code 직접 단언) | S-후보: 이력 패턴만 있는 픽스처 → `exit 0` · `ok:true` |
| H-2 | F-002 마스킹 정규식 | **오탐 계약** — `F-00X`·`TS-0XX`·`TS-024/025/026` 나열형·`파일.js:455` 줄번호가 마스킹을 빠져나가면 R-3 AC(c)가 깨진다 | P1 | L1(순수 텍스트 단위) + L3(실 저장소 전수 재측정) | S-후보: 표기 6종 픽스처 · 실 저장소 23건 재현 |
| H-3 | F-002 임계값 2 | **과소탐 계약** — 임계값을 3으로 올리면 진성 18건 중 distinct 2인 6건이 탈락 | P0 | L2(임계값 경계 픽스처: distinct 1 → 미탐, 2 → 탐지) | S-후보: 경계값 양방향 |
| H-4 | F-002 `counts` 필드 추가 | **JSON 스키마 소비자** — CLOSE 게이트·PM Gate가 `counts` 키 집합을 고정 단언하면 additive 추가로도 깨질 수 있다 | P1 | L2(`validate --json` 기존 키 9종 전건 존재 + 값 불변 단언) | S-후보: 기존 counts 키 회귀 |
| H-5 | F-003 23파일 `@header` 편집 | **JSON 파싱 계약** — 한글 본문에서 따옴표·역슬래시·줄바꿈 처리를 그르치면 `@header`가 통째로 파싱 실패해 `uncovered:newly_uncovered`(차단)로 떨어진다 | P0 | L2(`validate` 전수 exit 0 + `scan --json` 23건 파싱 성공) | S-후보: 정리 후 커버리지 불변 |
| H-6 | F-003 `exports` 인접 편집 | **`exports_not_found`** — `description` 편집 중 `exports` 배열을 건드리면 텍스트 대조가 깨진다(R-4 AC(e) 위반) | P1 | L2(`counts.exports_not_found` 정리 전후 동일) | S-후보: exports 불변 |
| H-7 | F-003 정리 대상 8건이 테스트 파일 | **테스트 스위트** — `@header` docstring 편집이 모듈 최상단 docstring이라 import·수집 경로에 닿는다 | P1 | L2(`state-tool` pytest 400 passed/3 skipped 유지) | S-후보: pytest 회귀 |
| H-8 | F-001 `header-standard.md` 절 삽입 | **절 번호 참조** — §5·§6·§7 번호가 밀리면 `code-scan.js:58`·`:196`·`test-header-source.js:204`의 `§7` 문자열 단언과 어긋난다 | P1 | L2(문자열 `header-standard.md §7` grep 불변 + `test-header-source.js` 통과) | S-후보: 절 번호 불변 |
| H-9 | F-001 3문서 정합 | **문서 간 모순** — `header-standard.md`·`header-rules.md`·`docs/CONVENTIONS.md`가 서로 다른 말을 하면 R-2 AC(d)·AC(e) 동시 위반 | P1 | L1(산출물 검사: 3문서 교차 grep) | S-후보: "헤더 내 변경이력 라인" 어구 잔존 0건 |
| H-10 | F-002 신규 테스트 파일 | **메타 테스트 3건**(S-19·TS-062·TS-080)이 `tests/*.js` 전량을 중첩 실행한다 — 신설 파일이 느리면 3배로 곱해진다 | P2 | L2(신설 파일 자체 실행 시간 관측) | S-후보: 신설분 tmp 픽스처만 사용(커밋 픽스처 미증설) |

---

## 2. 기능별 분석

> **[MUST] 승계 원천 2원 규정** — §2의 파일 맵은 `ANALYSIS.md` §1.1 앞 4열을, 확정값은 `ANALYSIS.md` §8을 재조사 없이 승계했다. 미결(P-2·P-3)만 아래에서 소비한다.

### F-001: 4필드 작성 기준 + 「이력은 git이 갖는다」 3문서 명문화

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/header-standard.md` | @header 필드 정의·언어별 예시·exports 가이드·2소스 표현 SSOT | 수정 |
| 가이드 | `opal/core/references/harness/header-rules.md` | EXECUTE 단계 @header 작성 규칙 — 기록 위치 판정·갱신 시점·워커 권한 경계 | 수정 |
| 문서 | `docs/CONVENTIONS.md` | 프로젝트 컨벤션 §@header 규칙 — R-2와 충돌하는 문구 보유 | 수정 |
| 가이드 | `opal/core/references/opal-doc-standard.md` | `:28` 「변경 이력은 git이 갖는다」 — 인용 원문 | 무변경(근거) |

#### 2.1.2 현재 구현

- `header-standard.md` §2 필드 정의 표(`:11-23`)는 `description`을 "파일의 역할 한 줄 요약", `note`를 "추가 메모 (작업 흔적, 특이사항)", `feature`를 조회 키로만 1줄씩 정의한다. 작성 기준은 §4(`:133-159`) `exports` 하나뿐이며 3열 표(layer / exports에 담는 내용 / 예시), layer당 1행 21행이다.
- `header-rules.md` §파일 수정 시(`:112-123`)는 4행 표(변경 내용 → 갱신 대상 필드)로 "파일 역할 변경 → `description`"까지만 말하고, **무엇을 담지 않는가**를 말하지 않는다. §워커 권한 경계(`:66-76`)가 워커 기입 5필드를 확정한다.
- `docs/CONVENTIONS.md:218`이 "변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 **헤더 내 변경이력 라인**으로 갱신한다"로 R-2와 정면 충돌한다. 이 문서는 `docs/PROJECT.md`가 「개발 작업 시 항상」 참조로 등재한 [MUST] 문서다.
- 절 번호 외부 참조 실측: `header-standard.md §3`(`code-scan.js:1061`), `§7`(`code-scan.js:58`·`:196`, `test-header-source.js:204`, `code-map-hook.js:10` note). **§4·§5·§6에 대한 외부 참조는 0건**이다(E1 grep).

#### 2.1.3 영향 범위

- `header-standard.md` → `header-rules.md`(포맷 표준 인용) → `docs/CONVENTIONS.md`(근거 열 인용)의 3단 종속. 세 문서가 같은 말을 해야 R-2 AC(d)·AC(e)가 성립한다.
- 절 번호를 밀면 `test-header-source.js:204`가 stderr에 `header-standard.md §7`이 실리는지 문자열 단언한다 — **[MUST] 기존 절 번호(§3·§5·§6·§7) 불변**. 신설은 하위 절(`### 2.1`, `### 4.1`/`### 4.2`)로만 한다.
- `install-mac.sh`가 배포 시 변경이력 섹션을 strip한다(`docs/CONVENTIONS.md:249`) — 소스에는 유지, 배포본에서는 제거되므로 변경이력 행 추가는 배포본 바이트에 영향을 주지 않는다.

### F-002: `code-scan validate` 이력 누적 패턴 비차단 감지

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/code-scan/code-scan.js` | `cmdValidate` — @header 검증(violations/counts/blockingViolations) | 수정 |
| 도구 테스트 | `opal/tools/code-scan/tests/test-header-history.js` | 신설 감지기 CLI 블랙박스 테스트 | 신규 |
| 도구 테스트 | `opal/tools/code-scan/tests/test-shard-policy.js` | `VERSION` 값 단언 | 무변경(회귀 기준) |
| 도구 테스트 | `opal/tools/code-scan/tests/test-shard.js` | `VERSION` 값 단언 | 무변경(회귀 기준) |
| 도구 테스트 | `opal/tools/code-scan/tests/` 12파일(344 테스트) | 회귀 기준 | 무변경 |

#### 2.2.2 현재 구현

- `cmdValidate`(`code-scan.js:3155`)는 파일 루프(`:3200-3257`)에서 `extractHeader`/`resolveHeader`로 헤더를 얻고, 필수 5필드 결손(`uncovered:incomplete`)·`conflict`·`draft`·`exports_not_found`를 같은 `violations` 배열에 push한다. 루프 종료 후 `counts`(`:3434-3444`) 9종 집계 → `blockingViolations` 필터(`:3447-3450`) → `ok` → `process.exit(ok ? 0 : 2)`(`:3469`).
- 비차단 관용구가 이미 있다: `manifest_oversize`는 `violations.push`(`:3295-3308`) + `counts.manifest_oversize`(`:3443`) + 필터에서 `v.code !== 'manifest_oversize'` 제외(`:3450`)로 구현된다. 주석 `:3447` "「uncovered:pre_existing」과 「manifest_oversize」는 비차단(U-2) — 나머지는 차단 불변."
- 상수는 `Constants` 블록(`:34-46`)에 근거 주석과 함께 둔다 — `VERSION = '1.6.0'`(`:38`), `HEADER_READ_BYTES = 24576`(`:46`, 전수 실측 근거 주석 5줄 동반). **신규 상수의 선례가 이 형식이다.**
- 테스트는 CLI 블랙박스(`spawnSync` + `OPAL_HOME` 가짜 홈 주입)가 표준이며, `test-validate.js:22`에 `[MUST] red-first.md §3 — GREEN/fix 루핑 중 이 파일 수정 금지` 동결 주석이 살아 있다.

#### 2.2.3 영향 범위

- `validate --json` 소비자(CLOSE 게이트·PM Gate)는 `ok`/exit code/`counts`를 읽는다 — 신규 필드는 additive라 기존 판정에 영향 없음(H-4로 회귀 단언).
- `code-scan.js` 자신의 `note`(1712자, 태스크 077·080·082·083 4개 누적)가 R-4 AC(f) 정리 대상이다 — **같은 파일이므로 반드시 같은 Step에서 처리**한다(동시 편집 시 후행 저장이 선행 편집을 덮어쓴다).
- 신규 테스트 파일 1개는 메타 테스트 3건의 중첩 실행 대상에 들어간다(H-10) — 커밋 픽스처를 늘리지 않고 `mkdtempSync` 런타임 생성으로 한정한다.

### F-003: 기존 진성 23건 이력 정리

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 이력 정리 | `opal/tools/state-tool/state_tool.py` | state-tool CLI 본체 (11791자 / 태스크 20개) | 수정 |
| 이력 정리 | `opal/tools/state-tool/tests/test_state_tool.py` | state-tool 테스트 (7049자 / 15개) | 수정 |
| 이력 정리 | `opal/tools/state-tool/todo_mirror_hook.py` | todo 미러 훅 (924자 / 3개) | 수정 |
| 이력 정리 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | todo 미러 훅 테스트 (948자 / 3개) | 수정 |
| 이력 정리 | `opal/tools/test-tool/lib/scenario.py` | test-tool 시나리오 모듈 (828자 / 4개) | 수정 |
| 이력 정리 | `opal/tools/brain-tool/brain_tool.py` | brain-tool CLI 본체 (1213자 / 4개) | 수정 |
| 이력 정리 | `opal/tools/brain-tool/tests/test_brain_tool.py` | brain-tool 테스트 (553자 / 3개) | 수정 |
| 이력 정리 | `opal/tools/memory-tool/tests/test_memory_tool.py` | memory-tool 테스트 (473자 / 4개) | 수정 |
| 이력 정리 | `opal/tools/opal-agent/tests/test_opal_agent.py` | opal-agent 테스트 (430자 / 2개) | 수정 |
| 이력 정리 | `opal/tools/improve-tool/tests/test_improve_tool.py` | improve-tool 테스트 (179자 / 2개) | 수정 |
| 이력 정리 | `opal/tools/code-scan/code-map-hook.js` | PostToolUse 훅 (414자 / 2개, `note` 625자 동반) | 수정 |
| 이력 정리 | `dashboard/backend/models.py` | Pydantic 응답 스키마 (1938자 / 2개) | 수정 |
| 이력 정리 | `dashboard/backend/config.py` | console.config 로더 (1163자 / 3개) | 수정 |
| 이력 정리 | `dashboard/backend/main.py` | FastAPI 진입점 (458자 / 2개) | 수정 |
| 이력 정리 | `dashboard/backend/adapters/brain_session.py` | 대화별 BrainSession 상태기계 (1954자 / 2개) | 수정 |
| 이력 정리 | `dashboard/backend/tests/test_config.py` | config 테스트 (996자 / 3개) | 수정 |
| 이력 정리 | `dashboard/backend/tests/test_routers.py` | 라우터 테스트 (2033자 / 5개) | 수정 |
| 이력 정리 | `dashboard/backend/tests/test_stats.py` | 통계 테스트 (877자 / 2개) | 수정 |
| 문서 | `tasks/107-260906-opd-헤더필드-작성기준-이력분리/HISTORY-EVIDENCE.md` | **23건** 이력 소실 확인 근거(R-4 AC(c)) | 신규 |

> 괄호 안 「N자 / 태스크 M개」는 E1 재측정값이다 — `description` 문자수는 `scan --json` 원문 기준, 태스크 개수는 §3.2.2 규칙 적용 후 distinct 카운트다. `code-scan.js`의 `note`(1712자 / 4개)는 F-002 Step에서 함께 처리한다.

#### 2.3.2 현재 구현

관측된 이력 누적 표기는 4형태다 — ① 대괄호 태스크 태그 `[T061] …` / `[T103/R-16] …`(`dashboard/backend/models.py`) ② 괄호 태그 `(T060 F-1, RED)`(`dashboard/backend/tests/test_config.py`) ③ 콜론 선행 번호 `014 Phase 4: …` / `016: …` / `088: …`(`opal/tools/state-tool/state_tool.py`) ④ 병기형 `TASK 077 / TASK 080 F-005`(`opal/tools/code-scan/code-map-hook.js`). 네 형태 모두 **역할 요약 뒤에 시점별 변경 단락이 순차 append된 구조**이며, 첫 문장(역할 한 줄)은 어느 파일에서도 훼손되지 않은 채 앞에 남아 있다 — R-4 AC(b)(역할 한 줄 보존)가 기계적으로 달성 가능한 이유다.

#### 2.3.3 영향 범위

- 23파일 상호 의존 없음 — 서로 다른 도구/테스트 파일이며 `@header` 블록만 건드린다(파일 본문 로직 무변경).
- 8건이 테스트 파일이라 모듈 docstring을 편집한다(H-7) — `state-tool` pytest 400 passed/3 skipped, `code-scan` 344 passed가 회귀 기준이다.
- `description` 총량이 약 34,000자 감소하면 `scan`/`search` 출력 바이트가 줄어 헤더 창문 재포화가 늦춰진다(태스크 106 동기와 직결).
- brain(`ingest-scan`)이 이 자산의 `description`을 시드했다면 다음 ingest에서 스냅샷이 갱신된다 — brain은 파생물이므로 비차단.

### F-004: 회귀 보존 검증

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 테스트 | `opal/tools/code-scan/tests/` | 344 passed / 0 failed 기준 | 무변경(검증) |
| 도구 테스트 | `opal/tools/state-tool/tests/` | 400 passed / 3 skipped 기준 | 무변경(검증) |

#### 2.4.2 현재 구현

E1 실행 관측 — `code-scan`: `node --test tests/*.js` → 344 passed / 0 failed. `state-tool`: `python3 -m pytest tests/ -q` → 400 passed / 3 skipped / 98 subtests passed. 메타 테스트 3건(S-19 `test-shard.js:978`, TS-062 `test-regression.js:599`, TS-080 계열 `test-shard-policy.js`)이 `CODE_SCAN_META_CHILD` 재귀 가드로 스위트를 중첩 실행한다.

#### 2.4.3 영향 범위

F-002가 테스트를 신설하므로 종료 시점 `code-scan` 총계는 344 + 신설분이다. **[MUST] 회귀 판정은 "기존 344건 중 failed 0"으로 하고 총계 숫자 일치로 하지 않는다** — 총계 단언은 신설 자체를 회귀로 오판한다(RPT-2).

---

## 3. 기능별 설계

### F-001: 4필드 작성 기준 + 「이력은 git이 갖는다」 3문서 명문화

#### 3.1.1 파일 변경 계획

**신규 생성** — 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/header-standard.md` | 가이드 | `### 2.1 이력 비기재 원칙` 신설 + `## 4` 헤딩을 「필드 작성 가이드」로 확장하고 하위에 `### 4.1 exports (layer별)`(기존 표 원문 그대로 이동) · `### 4.2 description·depends·note·feature` 4열 표 신설 + 변경이력 행 v1.5 | (→ D-1 §2·§4), `opal/core/references/header-standard.md:133-159` |
| 2 | `opal/core/references/harness/header-rules.md` | 가이드 | §파일 수정 시 갱신 대상 필드 표 아래에 `[MUST] 이력 비기재` 1블록 + 「이력의 소재 2곳」 명시 + 변경이력 행 v1.10 | (→ D-2 §파일 수정 시), `opal/core/references/harness/header-rules.md:112-123` |
| 3 | `docs/CONVENTIONS.md` | 문서 | §@header 규칙 5번째 불릿 교체 + 변경이력 행 v1.9.0 | `docs/CONVENTIONS.md:218` |

#### 3.1.2 설계

**(A) 이력 비기재 원칙 — 정본 문장** (`header-standard.md` `### 2.1`에 두고 나머지 2문서는 이를 인용한다. R-2 AC(d) 「두 문서가 서로 다른 말을 하지 않는다」를 SSOT 1곳 + 포인터 2곳 구조로 보장한다 — `docs/CONVENTIONS.md:281` v1.7.0 행이 확립한 "원문 복제 대신 포인터" 패턴 준용)

> `@header`의 어느 필드에도 **변경 이력을 기재하지 않는다**. 근거는 `opal-doc-standard.md:28` — "실행 지시문은 코드처럼 제자리에서 갱신되고 **변경 이력은 git이 갖는다**. 다만 **버전 번호**는 문서 안에 남는다". `@header`는 코드 파일의 실행 지시문이므로 같은 원칙이 적용된다.
> **이력의 소재는 2곳이다** — ① `git log --oneline --all -- <파일>`(커밋 메시지에 태스크 번호가 실린다) ② `tasks/{NNN}-*/DONE.md`(태스크별 변경 서술).
> `@header`는 **현재 시점의 사실만** 담는다. 필드를 갱신할 때는 이전 값 옆에 덧붙이지 않고 **제자리에서 교체**한다.
> 적용 범위: `@header` JSON 블록 내부 5필드(`description`·`exports`·`depends`·`note`·`feature`). `@header` 블록 **밖**의 평문 주석 `변경이력:` 블록(예: `opal/tools/code-scan/tests/test-validate.js:39-48`)과 `.md` 문서의 `## 변경이력` 표는 이 원칙의 적용 대상이 **아니다**(별건). — (→ D-3 `:28`), `TASK.md:96` §범위 제외

**(B) `header-standard.md` §4.2 — 4필드 작성 가이드 표** (§4 `exports` 3열 표 형식 부분 준용, 「담지 않는 것」 열 신규 — ANALYSIS Q6)

| 필드 | 담는 것 | 담지 않는 것 | 예시 |
|------|--------|------------|------|
| `description` | 이 파일이 **지금 무엇인가** — 역할 한 줄. 코드량이 늘어도 길이가 늘지 않는 축이다(코드량 축은 `exports`가 담당한다) | 변경 이력, 태스크 번호(`[T061]`·`014:`·`TASK 077` 등 시점 표기 전반), 시점별 변경 단락의 append, 함수 목록(=`exports` 관할) | `"세션별 BrainSession 상태기계 — 대화 단위 인메모리 핸들 + 프라임 연결 풀"` |
| `depends` | 이 파일이 의존하는 **모듈 ID**(코드: kebab-case) 또는 **참조 문서명**(기획/설계) | 표준 라이브러리 나열, 버전 번호, 도입 시점·태스크 번호 | `["auth-service", "결제_정책서"]` |
| `note` | 코드를 읽어서는 알 수 없는 **현재 유효한 제약·계약**(순서 계약, fail-safe 이유, 의도적 예외) | **변경 이력**(`description`의 이력을 옮겨 담는 대체 저장소가 아니다 — 블록 총량이 그대로면 창문 재포화를 늦출 뿐이다), 태스크 번호, TODO·미래 계획 | `"모드 게이트는 code-map 로딩보다 위에 놓인다 — 아래에 있으면 무출력 계약이 stderr 축에서 깨진다"` |
| `feature` | 기능축 조인 키 1개 — `code-scan feature <id>` 조회 키(§7) | 복수 값 나열, 태스크 번호, 화면/정책 축 값(`ia:{system}:{screen}`·`POL-{번호}`는 별개 축) | `"F-003"` |

> **[MUST] 기존 §4 `exports` 가이드 표는 원문 무변경**으로 `### 4.1` 하위에 그대로 둔다(R-1 AC(e)). `## 4` 헤딩 문구만 「exports 작성 가이드 (layer별)」 → 「필드 작성 가이드」로 확장하며, **절 번호 4는 유지**한다. §5·§6·§7 번호를 밀지 않는다(H-8).

**(C) `header-rules.md` §파일 수정 시 — 추가 블록**

기존 4행 표(`:112-123`)는 원문 유지하고 바로 아래에 추가한다:

> **[MUST] 갱신은 교체지 누적이 아니다** — 위 표의 「갱신」은 해당 필드 값을 **제자리에서 바꾸는 것**이다. 이전 값 뒤에 태스크 번호를 붙여 새 단락을 append하지 않는다. 이력은 git과 `tasks/{NNN}-*/DONE.md`가 갖는다 — 원칙 원문은 `~/.opal/references/header-standard.md` §2.1이 소유하며 본 문서는 포인터만 둔다.
> `code-scan validate`가 `description`·`note`에서 서로 다른 태스크 번호 2개 이상을 감지하면 `header_history` **비차단 경고**를 낸다(exit code 불변). 경고를 받으면 이력 단락을 제거하고 역할 한 줄로 되돌린다.

**(D) `docs/CONVENTIONS.md:218` 교체 문구** (R-2 AC(e))

- AS-IS: `- 변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다.`
- TO-BE:
  - `- 변경이력은 스킬·에이전트·참조 문서의 "## 변경이력" 표로 갱신한다.`
  - `- **코드 @header에는 이력을 기재하지 않는다** — @header는 현재 시점의 사실만 담고, 이력은 git 로그와 `tasks/{NNN}-*/DONE.md`가 갖는다. 원칙 원문은 `opal/core/references/header-standard.md` §2.1이 소유한다. `code-scan validate`의 `header_history` 비차단 경고가 이를 관측한다 (Task 107).`
- **[MUST]** 「헤더 내 변경이력 라인」 어구는 프로젝트 전역에서 0건이 되어야 한다(R-2 AC(e)). 단 교체 문구는 `@header` JSON 필드에 한정되며, 코드 주석의 평문 `변경이력:` 블록 존폐는 이번 범위 밖임을 (A) 적용 범위 문단이 이미 못박는다.

**(E) 변경이력 행** — `[MUST] 'docs/CONVENTIONS.md' §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 「## 변경이력」 표에 행을 추가한다. 일시는 YYYY-MM-DD HH:mm (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: (138)."`

| 문서 | 현재 최신 | 신규 버전 |
|------|----------|----------|
| `opal/core/references/header-standard.md` | v1.4 | **v1.5** |
| `opal/core/references/harness/header-rules.md` | v1.9 | **v1.10** |
| `docs/CONVENTIONS.md` | v1.8.0 | **v1.9.0** |

#### 3.1.3 환경 변경

해당 없음. 단 참조 문서 2건은 `~/.opal/references/`로 배포되므로 실효화에는 `scripts/install-mac.sh` 재실행이 필요하다 — **[MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."** 재배포는 Step 15(조건부, 소유자 실행)로 분리한다.

#### 3.1.4 배치/마이그레이션

해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(a) | 산출물 검사 | `header-standard.md` §4.2 표에 `description`·`depends`·`note`·`feature` 4행이 있고 각 행에 「담는 것」·「담지 않는 것」·「예시」 3열이 모두 비어 있지 않다 |
| TS-002 | R-1 AC(b)(c) | 산출물 검사 | `description` 행의 「담지 않는 것」에 "변경 이력"과 "태스크 번호"가, `note` 행의 「담지 않는 것」에 "변경 이력"과 "대체 저장소가 아니다" 취지가 모두 존재 |
| TS-003 | R-1 AC(d)(e) | 산출물 검사 | §2 필드 정의 표 5필드 원문 무변경(diff 0줄) + §4.1 `exports` 21행 표 원문 무변경(diff 0줄) |
| TS-004 | R-2 AC(a)(b) | 산출물 검사 | §2.1에 `opal-doc-standard.md:28` 원문 인용 문자열이 존재하고 이력 소재 2곳(git·`tasks/{NNN}-*/DONE.md`)이 명시 |
| TS-005 | R-2 AC(c)(d) | 산출물 검사 | `header-rules.md` §파일 수정 시 표 4행 원문 무변경 + 추가 블록이 `header-standard.md §2.1`을 포인터로 인용 + 3문서 중 원칙 **원문**을 보유한 문서가 정확히 1개(`header-standard.md`) |
| TS-006 | R-2 AC(e) | 산출물 검사 | 저장소 전역 `grep -rn "헤더 내 변경이력 라인"` 결과 `tasks/`·`.opal-worktrees/` 제외 시 **0건** |
| TS-007 | H-8 | 회귀 테스트 | `grep -c "header-standard.md §7"`가 변경 전후 동일하고 `node --test tests/test-header-source.js` 전건 통과 |

### F-002: `code-scan validate` 이력 누적 패턴 비차단 감지

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/code-scan/tests/test-header-history.js` | 도구 테스트 | 감지기 CLI 블랙박스 테스트 — 표기 6종 · 임계값 경계 · exit code 불변 · counts additive | `TASK.md:114` 메타 테스트 예산 / H-10 |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `Constants` 블록에 감지 상수 3종 추가 · 순수 함수 `countTaskTags(text)` 신설 · `cmdValidate` 파일 루프에 감지 호출 2회(description/note) · `counts.header_history` 1행 · `blockingViolations` 필터 제외 1행 · **자기 `@header.note` 이력 제거(R-4 AC(f))** | `code-scan.js:34-46`, `:3245-3256`, `:3443`, `:3450` |

#### 3.2.2 설계 — R-3 감지 규칙

##### (A) 축 정의 — 정규식보다 먼저

`description`/`note`에 실린 태스크 번호는 두 가지 성격 중 하나다.

| 성격 | 뜻 | 예 | 판정 |
|------|----|----|------|
| **단발 출처 인용** | "이 자산은 어느 태스크에서 왔는가" — 자산의 **출신** 1개. 시간이 지나도 늘지 않는다 | `(F-005/F-006/F-007, 태스크 080)` · `[T103] …`(단독) · `(058 F-002/F-005)` | 허용 |
| **이력 누적** | "이 자산이 어떻게 변해 왔는가" — 서로 다른 **시점**의 변경이 겹겹이 쌓인다. 태스크가 지날 때마다 단조 증가한다 | `[T061] … [T103] … [T103/R-16] …` · `014 Phase 4: … 016: … 017: …` · `TASK 077 / TASK 080` | 경고 |

두 성격을 가르는 것은 **서로 다른 태스크 번호가 몇 개인가**다 — 출처는 본질적으로 1개고, 2개 이상은 "언제 무엇이 바뀌었는지"를 필드가 기록하기 시작했다는 뜻이다. 따라서:

> **판정식**: `distinct(태스크번호(description)) >= 2` → 경고. `note`도 같은 식을 독립 적용한다.
> **[MUST] 임계값 2는 선택이 아니라 축 정의의 귀결이다** — 3으로 올리면 진성 18건 중 distinct 2인 6건(`code-map-hook.js`·`brain_session.py`·`main.py`·`models.py`·`test_stats.py`·`test_opal_agent.py`)이 탈락해 R-3 AC(c)가 즉시 깨진다(§3.2.3 실측표).

그러면 남는 문제는 **"무엇이 태스크 번호인가"** 하나뿐이고, 오탐 9건은 전부 이 정의 실패에서 나왔다(`F-005`는 기능번호, `TS-070`은 시나리오 id, `400`은 HTTP 상태, `127`은 IP 옥텟, `340 passed`는 테스트 수량). 이들은 사후 필터가 아니라 **토큰화 이전 구조적 마스킹**으로 제거한다 — 사례별 예외 목록은 다음 사례에서 또 뚫리기 때문이다.

##### (B) 3단 절차

```
countTaskTags(text) -> Set<string>
  1) mask(text)      — 태스크 번호가 아닌 것을 '#'로 치환 (아래 M1~M4)
  2) tokenize(masked) — 태스크 번호 후보만 추출 (아래 TOK)
  3) distinct         — 3자리 문자열 집합 반환
```

**마스킹 M1~M4** (순서 고정 — M1이 M2보다 먼저여야 `code-scan.js:455`의 `455`가 소수 규칙에 잡히지 않고 통째로 제거된다)

| # | 대상 | 정규식 | 실제 사례 |
|---|------|--------|----------|
| M1 | 경로:줄번호 인용 | `/[\w./-]+\.(?:py\|js\|jsx\|ts\|tsx\|md\|json\|sh\|ya?ml\|txt\|css)\s*:\s*\d+(?:\s*[-–~]\s*\d+)?/g` | `code-scan.js:455` · `todo_mirror_hook.py:124-130` |
| M2 | 소수·버전·절번호 | `/\d+(?:\.\d+)+/g` | `v1.6.0` · `§3.4.2` · `127.0.0.1` |
| M3 | 수량 표기 | `/\d{3}(?=\s*(?:passed\|failed\|skipped\|건\|개\|자\|줄\|바이트\|ms))/g` | `340 passed` · `347 passed` |
| M4 | 접두 하이픈 식별자 **및 그 나열·범위** | `/(?<![A-Za-z0-9])(?!TASK-)[A-Za-z]{1,4}-\d{1,4}(?:\s*[~\-/·,]\s*(?:[A-Za-z]{1,4}-)?\d{1,4})*/g` | `F-001` · `TS-070` · `R-16` · `QA-018` · **`TS-024/025/026`** · **`TS-201~209`** · `S-1~S-14` |

> M4의 꼬리 `(?:\s*[~\-/·,]\s*(?:[A-Za-z]{1,4}-)?\d{1,4})*`가 오탐 제거의 핵심이다 — 접두 없이 이어지는 나열(`TS-024/025/026`의 `025`·`026`)과 범위(`TS-201~209`의 `209`)까지 같은 식별자의 일부로 흡수한다. 이 꼬리가 없으면 정리 완료 후 `TS-024/025/026` 하나만으로 distinct 2가 되어 **정리한 파일이 다시 경고에 걸린다**(실측 확인: 꼬리 도입 전 `test_improve_tool.py`에서 `025`·`026`이 잘못 계상됐다).
> `(?!TASK-)`는 `TASK-077` 표기를 마스킹에서 보호한다.

**토큰화 TOK**

```
/(?<![0-9])(?:(TASK|task|태스크)[ \-#:]?|(T))?(\d{3})(?![0-9])/g
```

- 마커(`T` / `TASK` / `task` / `태스크`)가 붙은 3자리는 **무조건** 태스크 번호다 — `[T061]` · `TASK 077` · `태스크 080`.
- 마커 없는 3자리(bare)는 두 조건으로 걸러 통과시킨다:
  - **HTTP 상태코드 집합**(`200 201 202 204 301 302 304 400 401 403 404 405 409 410 422 429 500 501 502 503 504`)이면 제외.
  - 바로 앞 문자가 영문·한글·`#`(마스킹 잔재)이면 제외 — `abc123`류와 마스킹 경계 오검출 차단.
- 통과한 bare 3자리는 태스크 번호로 계상한다 — `014 Phase 4:` · `088:` · `077 자산 유지` 형태가 실제 이력 표기의 다수이므로 마커 필수화는 과소탐을 낳는다(실측: 마커 필수화 시 `state_tool.py` distinct 0).

##### (C) `cmdValidate` 배선

```js
// Constants 블록(code-scan.js:34-46 근처)
// 서로 다른 태스크 번호 N개 이상이면 이력 누적으로 본다. 1 = 단발 출처 인용(허용),
// 2 = 서로 다른 시점의 변경이 한 필드에 쌓이기 시작한 지점. 값 근거(3스코프 109파일 전수 실측,
// 태스크 107): 임계값 2에서 진성 18/18 탐지·F-code/TS-id 오탐 0건, 임계값 3이면 진성 6건 탈락.
const TASK_TAG_THRESHOLD = 2;
const HTTP_STATUS_CODES = new Set([...]);
const HISTORY_MASK_PATTERNS = [ /* M1~M4 */ ];

// 순수 함수 — module.exports에 노출하지 않는다(@header.exports 무변경 유지, R-4 AC(e) 정합).
function countTaskTags(text) -> Set<string>
```

파일 루프(`code-scan.js:3245-3256`의 `exports_not_found` 블록 **직후**)에 추가:

```js
for (const [field, sub] of [['description','description'], ['note','note']]) {
  const val = resolved && typeof resolved[field] === 'string' ? resolved[field] : '';
  if (!val) continue;
  const tags = countTaskTags(val);
  if (tags.size >= TASK_TAG_THRESHOLD) {
    violations.push({
      code: 'header_history', sub, file: relPath, manifest: ownerRel, key: basename,
      detail: [...tags].sort().join(','),
      tasks: tags.size,
    });
  }
}
```

집계·필터 2행:

```js
// counts (code-scan.js:3434-3444 블록 말미)
header_history: violations.filter(v => v.code === 'header_history').length,

// blockingViolations (code-scan.js:3447-3450) — 주석도 함께 갱신
// 'uncovered:pre_existing'·'manifest_oversize'·'header_history'는 비차단 — 나머지는 차단 불변.
&& v.code !== 'header_history'
```

- **[MUST] `manifest_oversize` 관용구를 그대로 재사용한다** — 같은 `violations` 배열 + 다른 `code` + `blockingViolations` 필터 제외. R-3 AC(b)의 "별도 채널"은 이 기존 관용구로 충족되며 신규 채널을 발명하지 않는다 (→ ANALYSIS §8 확정값, `code-scan.js:3301-3302,3443,3448-3451`).
- **[MUST] `VERSION` 상수는 상향하지 않는다** — 기존 필드 스키마·CLI 인터페이스 무변경 additive 확장이며, `test-shard-policy.js:1519-1521`·`test-shard.js:696-701`의 핀 2건을 건드리면 106 ADD-1의 테스트 5건 파손 전례를 반복할 위험만 진다(→ ANALYSIS Q4).
- **P-2 결정: `.opal/code-scan.json` 신규 설정 키를 만들지 않는다.** ① 임계값 2는 축 정의에서 유도된 상수이지 튜닝 파라미터가 아니다 ② 비차단 경고는 차단 게이트와 달리 프로젝트별 완화 압력이 없다 ③ 설정 키 1개 추가는 `code_scan_config_invalid` 검증 경로 · `header-standard.md` §7.1 필드 표 · `discover`/`init` 시드까지 파급되어 비용이 값 1개를 훨씬 넘는다 ④ 선례가 상수다 — `HEADER_READ_BYTES`(`code-scan.js:46`)도 전수 실측 근거를 주석으로 남긴 하드코딩이며, 설정으로 노출된 `shardPolicy`는 사람이 분할 결정을 내려야 하는 정책값이라 성격이 다르다.

#### 3.2.3 실측 검증 결과 (E1, 3스코프 109파일 전수)

**전수 재측정 명령 (1줄)** — 구현 완료 후 이 한 줄로 재현·검증한다:

```bash
node opal/tools/code-scan/code-scan.js validate --json | python3 -c "import json,sys; v=json.load(sys.stdin); h=[x for x in v['violations'] if x['code']=='header_history']; print('hits=%d ok=%s counts=%s'%(len(h), v['ok'], v['counts'].get('header_history'))); [print(' ', x['sub'], x['file'], x['detail']) for x in sorted(h, key=lambda y:(y['sub'], y['file']))]"; echo "exit=$?"
```

> 구현 전 설계 검증은 동일 규칙을 `scan --json` 출력에 적용한 프로토타입으로 수행했다(E1). 아래 표가 그 결과이며, 위 명령의 기대 출력과 집합이 일치해야 한다.

**결과 요약**

| 지표 | 값 | R-3 AC 대응 |
|------|---|------------|
| `description` 탐지 | **23건** | — |
| 진성 18건 탐지 | **18/18** | AC(c) 전건 탐지 ✅ |
| ANALYSIS §7 Q2 오탐 9건 탐지 | **0/9** | AC(c) 오탐 0건 ✅ |
| `note` 탐지 | **1건** (`opal/tools/code-scan/code-scan.js`, `077,080,082,083`) | R-4 AC(f) 대상과 정확히 일치 ✅ |
| 정리 후 잔여 탐지 예상 | **0건** — D-REQ-1 (나) 확정으로 23건 전건 정리 | R-3 AC(c)·완료기준 |

**탐지 23건 전량** (distinct 내림차순, ✔=캡틴 확정 정리 대상 18건)

| distinct | 파일 | 태스크 번호 | 18건 |
|---|---|---|---|
| 20 | `opal/tools/state-tool/state_tool.py` | 001,005,014,016,017,034,054,070,072,074,076,088,091,092,093,094,098,100,103,106 | ✔ |
| 15 | `opal/tools/state-tool/tests/test_state_tool.py` | 005,054,056,070,072,074,076,088,091,093,094,098,100,103,106 | ✔ |
| 5 | `dashboard/backend/tests/test_routers.py` | 021,023,061,101,103 | ✔ |
| 4 | `opal/tools/brain-tool/brain_tool.py` | 027,035,053,071 | ✔ |
| 4 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 045,078,079,096 | ✔ |
| 4 | `opal/tools/test-tool/lib/scenario.py` | 056,069,070,073 | ✔ |
| 3 | `dashboard/backend/config.py` | 060,061,103 | ✔ |
| 3 | `dashboard/backend/tests/test_config.py` | 060,061,103 | ✔ |
| 3 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 027,053,071 | ✔ |
| 3 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | 076,088,091 | ✔ |
| 3 | `opal/tools/state-tool/todo_mirror_hook.py` | 076,088,091 | ✔ |
| 2 | `dashboard/backend/adapters/brain_session.py` | 060,063 | ✔ |
| 2 | `dashboard/backend/main.py` | 060,061 | ✔ |
| 2 | `dashboard/backend/models.py` | 061,103 | ✔ |
| 2 | `dashboard/backend/tests/test_stats.py` | 101,103 | ✔ |
| 2 | `opal/tools/code-scan/code-map-hook.js` | 077,080 | ✔ |
| 2 | `opal/tools/improve-tool/tests/test_improve_tool.py` | 058,078 | ✔ |
| 2 | `opal/tools/opal-agent/tests/test_opal_agent.py` | 059,067 | ✔ |
| 2 | `dashboard/frontend/src/components/app-shell/AppShell.tsx` | 061,063 | — (D-REQ-1) |
| 2 | `opal/tools/backlog-tool/backlog_tool.py` | 056,069 | — (D-REQ-1) |
| 2 | `opal/tools/code-scan/tests/test-shard.js` | 082,083 | — (D-REQ-1) |
| 2 | `opal/tools/code-scan/tests/test-feature.js` | 077,080 | — (D-REQ-1, 경계) |
| 2 | `opal/tools/code-scan/tests/test-validate.js` | 077,080 | — (D-REQ-1, 경계) |

**배제된 오탐 9건** (ANALYSIS §7 Q2 분류) — 전부 `distinct == 1`로 임계값 미달

| 파일 | 마스킹으로 제거된 것 | 남은 태스크 번호 |
|---|---|---|
| `opal/tools/code-scan/tests/test-shard-policy.js` | `F-001`~`F-012` 8종(M4) | `083` 1개 |
| `opal/tools/code-scan/tests/test-regression.js` | `F-005/F-006/F-007`·`TS-070`(M4) | `080` 1개 |
| `opal/tools/code-scan/tests/test-target.js` | `F-003/F-004/F-008`(M4) | `080` 1개 |
| `opal/tools/code-scan/tests/test-hook.js` | `F-005/F-002`(M4) | `080` 1개 |
| `opal/tools/code-scan/tests/test-scope-filter.js` | `F-002/F-003`(M4) | `080` 1개 |
| `opal/tools/code-scan/tests/test-resolve-header.js` | `F-003`·`TS-028`(M4) | `080` 1개 |
| `opal/tools/code-scan/tests/test-discover.js` | `F-004/F-002`(M4) | `080` 1개 |
| `opal/tools/code-scan/tests/test-scaffold.js` | `F-004`·`TS-023`(M4) | `080` 1개 |
| `opal/tools/improve-tool/fw-inbox-README.md` | `F-002/F-005`(M4) | `058` 1개 |

**경계 3건 처리 방침** — 축이 자동으로 갈랐다. 별도 예외 규칙을 두지 않는다.

| 파일 | 축 적용 결과 | 판정 | 근거 |
|---|---|---|---|
| `opal/tools/code-scan/tests/test-feature.js` | `077`·`080` 2개 — 본문이 "**077 자산 유지 + 080 신 계약 정합**"으로 두 태스크의 변경 관계를 서술 | **탐지(진성으로 재분류)** | 이는 "어디서 왔는가"가 아니라 "무엇이 어떻게 이어졌는가" — 정의상 이력이다 |
| `opal/tools/code-scan/tests/test-validate.js` | `077`·`080` 2개 — "**+ 077 위반 검출/git 2분류/--changed 필터 회귀**"로 077 계약 승계를 서술 | **탐지(진성으로 재분류)** | 위와 동일 |
| `dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` | `[T103]` 1개 (`TS-142`·`TS-143`은 M4로 마스킹) | **미탐지** | 단발 출처 인용 — 축 정의상 허용 |

> 경고 수준 분리(별도 `sub` 등급)는 **두지 않는다** — 경고 자체가 이미 비차단이므로 등급을 나눠도 소비자 행동이 갈리지 않고, 등급 판정 축을 하나 더 만들면 그 축이 다시 사례 맞춤 대상이 된다. 대신 `detail`에 탐지된 태스크 번호 전량과 `tasks`(개수)를 실어 소비자가 스스로 판단할 재료를 준다.

#### 3.2.4 환경 변경

해당 없음 — 신규 패키지·설정 키 0건(P-2 결정).

#### 3.2.5 배치/마이그레이션

해당 없음.

#### 3.2.6 테스트 시나리오 (AC ↔ TS 매핑)

> 신설 테스트는 `opal/tools/code-scan/tests/test-header-history.js` 1파일에 모으고, 픽스처는 **커밋하지 않고** `mkdtempSync`로 런타임 생성한다(H-10 — 메타 3건이 스위트를 중첩 실행하므로 커밋 픽스처 증설은 `test-regression.js` 골든·픽스처 계약에도 파급된다).

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-3 AC(a) | 기능 테스트 | 이력 패턴만 있는 tmp 프로젝트 → `exit 0` · `ok:true` · `counts.header_history >= 1` |
| TS-011 | R-3 AC(a) | 기능 테스트 | 이력 패턴 + 실제 차단 위반(`uncovered:newly_uncovered`) 동시 → `exit 2`이되 사유는 차단 위반이며 `header_history`는 `blockingViolations`에 없다 |
| TS-012 | R-3 AC(b) | 기능 테스트 | `violations[]`에 `code:"header_history"` · `sub:"description"\|"note"` · `file` · `detail`(콤마 조인) · `tasks`(정수) 5키가 실린다 |
| TS-013 | R-3 AC(c) 오탐 | 기능 테스트 | `description: "… (F-005/F-006/F-007, 태스크 080)"` → 미탐지. `TS-024/025/026` 나열형·`TS-201~209` 범위형·`R-16`·`QA-018` 각각 미탐지 |
| TS-014 | R-3 AC(c) 오탐 | 기능 테스트 | HTTP 상태코드(`빈값→400`)·IP 옥텟(`127.0.0.1:7823`)·경로 줄번호(`code-scan.js:455`)·수량(`340 passed`)만 있는 `description` → 미탐지 |
| TS-015 | R-3 AC(c) 진성 | 기능 테스트 | 표기 4형태 각각 탐지 — `[T061] … [T103] …` / `(T060 F-1, RED) … [T061] …` / `014 Phase 4: … 016: …` / `TASK 077 / TASK 080` |
| TS-016 | H-3 임계값 경계 | 기능 테스트 | distinct 1(`[T103] …` 단독) → 미탐지, distinct 2(`[T103] … [T061] …`) → 탐지. 양방향 고정 |
| TS-017 | R-3 AC(b), H-4 | 회귀 테스트 | `counts`에 기존 9키(`orphan`/`uncovered`/`conflict`/`draft`/`exports_not_found`/`worker_scope_violation`/`newly_uncovered`/`pre_existing`/`manifest_oversize`)가 전건 존재하고 값이 변경 전과 동일 |
| TS-018 | R-3 AC(d), 제약 ⑥ | 회귀 테스트 | `code-scan --version` 출력이 `code-scan v1.6.0`으로 불변 (`test-shard.js:696-701`·`test-shard-policy.js:1519-1521` 통과) |
| TS-019 | R-4 AC(f) | 기능 테스트 | `note` 필드 단독 이력(`description`은 깨끗) → `sub:"note"`로 탐지되고 `sub:"description"` 항목은 없다 |

### F-003: 기존 진성 23건 이력 정리

#### 3.3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tasks/107-260906-opd-헤더필드-작성기준-이력분리/HISTORY-EVIDENCE.md` | 문서 | 23파일 × 제거 대상 태스크 번호 × `git log` 커밋 해시 대조표 — R-4 AC(c) 근거 | `TASK.md:105` R-4 AC(c) |

**수정** — §2.3.1 파일 맵 18건 + D-REQ-1 (나) 확대분 5건(`AppShell.tsx`·`backlog_tool.py`·`test-shard.js`·`test-feature.js`·`test-validate.js`) = **23건** (경로 재기재 생략, 전건 `@header` 필드만 편집)

#### 3.3.2 설계 — 정리 규칙

**(A) 보존/제거 판정 3단**

1. **보존** — 첫 문장(역할 한 줄). 관측된 18건 전건이 역할 요약으로 시작한다(§2.3.2). 확대분 5건도 같은 규칙을 적용하되, 첫 문장이 역할 요약이 아니면 역할 한 줄을 새로 세운다.
2. **보존** — 태스크 태그가 붙어 있어도 **현재 유효한 계약·제약**을 서술하는 문장. 태그만 떼고 문장은 남긴다. 예: `dashboard/backend/config.py`의 `[T103 R-21] load_quiet_hours — 진행 통계 야간 제외 구간을 OPAL setting 2층 머지로 로드한다` → 태그 제거 후 `load_quiet_hours`는 `exports`가 가리키는 현재 기능이므로 서술 유지.
3. **제거** — "언제 무엇이 바뀌었는지"만 말하는 문장. 예: `T061 범위 축소로 save_project_local 제거` · `S-13(구 위치 이전)은 …` · `077 자산 유지 + 080 신 계약 정합` · `구 index.json manifestMaxBytes는 폐기`.

> **[MUST] 판정 기준은 "지금도 참인가"이지 "짧은가"가 아니다** — `description` 글자수 상한은 두지 않는다(확정 방향 2항). `dashboard/backend/adapters/brain_session.py`처럼 1954자 중 대부분이 현재 유효한 동시성·락 순서 계약이면 태그만 떼고 대부분을 남기는 것이 정답이다.

**(B) 필드 경계**

- `description`이 담을 수 없게 된 **현재 유효한 계약**은 `note`로 옮길 수 있다. **[MUST] 단, 이력은 `note`로 옮기지 않는다** — `note`는 이력의 대체 저장소가 아니다(§3.1.2 (B) 표 `note` 행).
- **[MUST] `exports`·`module`·`layer`·`domain`은 무변경**(R-4 AC(e)). `depends`·`feature`도 이번 정리에서 건드리지 않는다.

**(C) 검증 (파일별, 편집 직후)**

```bash
node opal/tools/code-scan/code-scan.js validate --json | python3 -c "import json,sys;v=json.load(sys.stdin);print(v['ok'], v['counts'])"
```

- `@header` JSON 파싱 성공(H-5) — 해당 파일이 `uncovered`에 나타나지 않는다.
- `counts.exports_not_found` 불변(H-6).
- 해당 파일이 `header_history` 탐지 목록에서 사라진다(R-4 AC(a)).

**(D) 이력 소실 확인 절차** (Step 6, P-3 배정)

```bash
for f in <18 경로>; do echo "## $f"; git log --oneline --all -- "$f" | head -40; done
```

각 파일의 제거 대상 태스크 번호가 커밋 메시지(`feat(NNN)` / `fix(NNN)` 등) 또는 `tasks/NNN-*/DONE.md` 존재로 확인되면 `HISTORY-EVIDENCE.md`에 `파일 | 태스크번호 | 커밋 해시 또는 DONE.md 경로` 3열로 기록한다. ANALYSIS Q5가 3파일(`state_tool.py` 034·070, `brain_tool.py` 027·053·071, `test_improve_tool.py` 078)을 이미 확인했으므로 **나머지 15파일 + 3파일의 미확인 번호**가 이 Step의 범위다. 확인되지 않는 번호가 나오면 **그 문장은 제거하지 않고 보존**하고 `HISTORY-EVIDENCE.md`에 사유를 남긴다.

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-4 AC(a) | 기능 테스트 | 정리 후 `header_history` 탐지 **0건**(§3.2.3 재측정 명령 결과 `hits=0`) |
| TS-021 | R-4 AC(b) | 산출물 검사 | 23건 각각의 `description` 첫 문장이 정리 전후 동일하고 공란이 아니다 |
| TS-022 | R-4 AC(c) | 산출물 검사 | `HISTORY-EVIDENCE.md`에 23파일 전건 행이 있고, 제거된 태스크 번호마다 커밋 해시 또는 DONE.md 경로가 채워져 있다 |
| TS-023 | R-4 AC(d)(e) | 회귀 테스트 | `validate --json` — 23건이 `uncovered`에 0건 등장 · `counts.exports_not_found` 정리 전후 동일 · `coverage.percent` 불변 |
| TS-024 | R-4 AC(f) | 산출물 검사 | `code-map-hook.js`·`code-scan.js`의 `note`에서 태스크 번호 distinct가 1 이하로 내려간다 |

### F-004: 회귀 보존 검증

#### 3.4.1 파일 변경 계획

신규·수정 없음(검증 전용).

#### 3.4.2 설계

| 대상 | 명령 | 기준 |
|------|------|------|
| code-scan | `cd opal/tools/code-scan && node --test tests/*.js` | **기존 344건 중 failed 0** + 신설 `test-header-history.js` 전건 pass. 총계는 344 + 신설분 |
| state-tool | `cd opal/tools/state-tool && python3 -m pytest tests/ -q` | **400 passed / 3 skipped / 0 failed** |
| 메타 3건 | 위 code-scan 실행에 포함(`CODE_SCAN_META_CHILD` 재귀 가드) | S-19(`test-shard.js:978`) · TS-062(`test-regression.js:599`) · TS-080 계열(`test-shard-policy.js`) 통과 |
| 차단 위반 증가 0 | `node opal/tools/code-scan/code-scan.js validate --changed "$(git diff --name-only HEAD | tr '\n' ',')" --json` | `ok:true` · exit 0 |
| 전수 재측정 | §3.2.3 1줄 명령 | `hits` = **0**(D-REQ-1 (나) 확정 — 23건 전건 정리) · `ok:true` |

#### 3.4.3 환경 변경 / 3.4.4 배치

해당 없음.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-5 AC(a) | 회귀 테스트 | `code-scan` 기존 344건 failed 0 |
| TS-031 | R-5 AC(b) | 회귀 테스트 | `state-tool` 400 passed / 3 skipped / 0 failed |
| TS-032 | R-5 AC(c) | 회귀 테스트 | 메타 3건 통과 |
| TS-033 | R-5 AC(d) | 회귀 테스트 | `validate --changed` 차단 위반 증가 0건(exit 0) |

---

## 4. 통합 실행 계획

> **[MUST] 코드 변경은 코드 루트 `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_107/`(브랜치 `feat/OP-TASK-107`) 안에서만 수행한다.** 아래 각 Step의 `**파일**` 경로는 **허브 기준 상대경로**이며, EXECUTE 워커는 이를 코드 루트 절대경로로 치환해 작업한다. 산출물(`.md`)·state 기록은 문서 루트 `/Volumes/Data/AIStudio/workspace/ai-framework/tasks/107-260906-opd-헤더필드-작성기준-이력분리/`에 둔다.
> **[MUST] git 이력 변경 금지** — `git commit`·`push`·`reset`·`rebase` 미실행. 변경은 워킹트리에 남긴다 (`opal/core/references/opal-harness.md` §1 커밋 규칙).

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| 1 | F-001, F-002, F-003 | 1, 2, 3, 4, 5 | **병렬 5** | 전부 서로 다른 파일. Step 5(git log 증거)는 읽기 전용 |
| 2 | F-002 | 6, 6b | 순차 | Step 4(RED) 완료 후 구현(작성자≠구현자). 6b는 Step 6 후 PM Gate에서 발견·편입 |
| 3 | F-003 | 7, 8, 9, 10, 11, 12, 12b, 13, 13b, 13c | **병렬 10** | 파일 집합 비중첩. Step 1·5 완료 후 |
| 3b | F-001·F-002·F-003 | 1b, 5b, 6c, 16~22, 23 | **배치 분할** | 캡틴 3차 `changelog` 편입분. 6c는 5b·6b 후, 16~23은 6c 후 |
| 4 | F-004 | 14 | 순차 | Phase 3 전건 완료 후 |
| 5 | — | 15 | 순차(조건부) | 소유자 승인 시에만 |

### 4.2 실행 체크리스트

> 총 **33개** Step(초안 15 + D-REQ-1 (나) 확대분 3 + PM Gate 발견 편입 **4**[6b·6d·1c·6e] + 캡틴 3차 `changelog` 편입 11[1b·5b·6c·16~22·23]) | Phase 5개 | 실행 모드: **복잡**

#### Step 1: `header-standard.md` §2.1 이력 비기재 원칙 + §4.2 4필드 작성 가이드 신설
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent — FE/BE/DB 어느 영역도 아닌 프레임워크 참조 문서(.md) 개정이므로 공통 폴백을 쓴다
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: §3.1.2 (A) 원칙 정본 문장을 `### 2.1 이력 비기재 원칙`으로 신설. `## 4. exports 작성 가이드 (layer별)` 헤딩을 `## 4. 필드 작성 가이드`로 바꾸고 하위에 `### 4.1 exports (layer별)`(기존 21행 표 **원문 그대로**)와 `### 4.2 description·depends·note·feature`(§3.1.2 (B) 4열 표) 배치. §변경이력에 `v1.5 | {KST} | @header 4필드 작성 가이드(§4.2) 신설 + 이력 비기재 원칙(§2.1) 명문화 (107)` 행 추가
- **완료 기준**: TS-001·TS-002·TS-003·TS-004 통과. `grep -c "^## " `로 최상위 절 개수 불변(7개), `## 5`·`## 6`·`## 7` 번호 불변
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-007
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `header-rules.md` §파일 수정 시 이력 비기재 [MUST] 블록 추가
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent — 하네스 참조 문서(.md) 개정
- **파일**: `opal/core/references/harness/header-rules.md`
- **작업 내용**: §파일 수정 시 갱신 대상 필드 표(`:112-123`) **원문 유지** + 바로 아래에 §3.1.2 (C) 2문단 추가. §변경이력에 `v1.10 | {KST} | §파일 수정 시 — 갱신은 교체지 누적이 아님 [MUST] 블록 + header_history 비차단 경고 안내 추가, 원칙 원문은 header-standard.md §2.1 포인터 (107)` 행 추가
- **완료 기준**: TS-005 통과. 원칙 **원문**을 보유한 문서가 `header-standard.md` 1개뿐이고 본 문서는 포인터만 둔다
- **테스트**: TS-005
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: `docs/CONVENTIONS.md` §@header 규칙 문구 교체 (docs/ 갱신)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: PM 직접 — `docs/` 갱신 Step은 PM 관할(스킬 §docs/ 갱신 Step 자동 생성 규칙)
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: `:218` 불릿을 §3.1.2 (D) TO-BE 2불릿으로 교체. §변경이력에 `v1.9.0 | {KST} | §@header 규칙 — 「헤더 내 변경이력 라인으로 갱신한다」 어구 제거, 코드 @header 이력 비기재 원칙으로 교체(원문 소유권은 header-standard.md §2.1) (107)` 행 추가
- **완료 기준**: TS-006 통과 — 저장소 전역(`tasks/`·`.opal-worktrees/` 제외) "헤더 내 변경이력 라인" 0건
- **테스트**: TS-006
- **실행 방법**: direct
- **의존**: 없음

#### Step 4: `test-header-history.js` RED-first 신설
- [x] 완료
- **소속 기능**: F-002
- **영역**: 도구 테스트
- **agent**: opal-test-agent — 테스트 전문 워커. 작성자≠구현자(red-first.md §2)를 지키려면 Step 6과 다른 에이전트여야 한다
- **파일**: `opal/tools/code-scan/tests/test-header-history.js`
- **작업 내용**: TS-010~TS-019 10건을 CLI 블랙박스(`spawnSync` + `OPAL_HOME` 가짜 홈 주입, `test-validate.js:60-75` 하네스 패턴 준용)로 작성. 픽스처는 **커밋하지 않고** `mkdtempSync`로 런타임 생성(`.opal/code-scan.json` + 소스 3~5개). 파일 자신의 `@header`는 신설 기준(§3.1.2 (B))을 준수 — `description`에 태스크 번호 0개
- **완료 기준**: 구현 전 실행 시 신 계약 케이스 전량 FAIL(RED), 회귀 baseline 케이스(TS-017·TS-018)는 PASS
- **테스트**: 자기 자신
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 5: 23파일 이력 소실 확인 전수 (`HISTORY-EVIDENCE.md`)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: opal-task-agent — 읽기 전용 git 조사 + 문서 산출, 도메인 전문성 불필요
- **파일**: `tasks/107-260906-opd-헤더필드-작성기준-이력분리/HISTORY-EVIDENCE.md` (문서 루트 절대경로)
- **작업 내용**: §3.3.2 (D) 절차로 **23파일**(18건 + D-REQ-1 확대분 5건) 전건 `git log --oneline --all -- <경로>` 수행. `파일 | 태스크번호 | 커밋 해시 또는 DONE.md 경로 | 확인여부` 4열 표 산출. 미확인 번호는 「보존 대상」으로 표시
- **완료 기준**: TS-022 통과 — **23행** 전건 존재, 각 행의 태스크 번호마다 근거 채움 또는 「보존」 사유 기재
- **테스트**: TS-022
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 6: `code-scan.js` 감지기 구현 + 자기 `note` 이력 제거
- [x] 완료
- **소속 기능**: F-002 (+ F-003 AC(f) 일부)
- **영역**: 도구
- **agent**: opal-task-agent — Node.js CLI 도구 구현. BE 애플리케이션 코드가 아니라 프레임워크 도구이므로 공통 폴백
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.2.2 (C) 배선 — Constants 3종(근거 주석 동반, `HEADER_READ_BYTES` 형식 준용) · 순수 함수 `countTaskTags(text)` · 파일 루프 `:3256` 직후 감지 2회 · `counts.header_history` 1행 · `blockingViolations` 필터 제외 1행 + 주석 갱신. **같은 편집에서** 자기 `@header.note`(1712자, 태스크 077·080·082·083)의 이력 서술을 제거하고 현재 유효한 계약만 남긴다(R-4 AC(f)). `module.exports`·`@header.exports`·`VERSION` **무변경**
- **완료 기준**: Step 4 테스트 전건 GREEN + TS-024(자기 note) 통과 + §3.2.3 재측정 명령 결과 `description` 23건 / `note` 0건
- **테스트**: TS-010~TS-019, TS-024
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6b: 메타 테스트 단언 갱신 (신설 테스트 파일 편입) — **[PM Gate 발견, PLAN 사후 편입]**
- [x] 완료
- **소속 기능**: F-002 (+ F-004 회귀)
- **영역**: 도구 테스트
- **agent**: opal-task-agent — 메타 테스트 단언 갱신. 도메인 전문성 불필요
- **파일**: `opal/tools/code-scan/tests/test-header-history.js`, `opal/tools/code-scan/tests/test-regression.js`, `opal/tools/code-scan/tests/test-shard-policy.js` (3파일 — 산출량 상한 이내)
- **발견 경위**: Step 6 완료 후 PM이 전체 스위트를 재현하니 **4건 FAIL**. 워커는 「sparse-checkout worktree 환경 artifact, 태스크 107과 무관」으로 보고했으나 **오진**이다 — 허브에서는 344/0 passed이고, 4건 전부 신설 테스트 파일 추가가 직접 원인이다. 인과는 단일 뿌리에서 나온다: `test-regression.js` **TS-057**이 실패 → 스위트를 중첩 실행하는 **S-19·TS-080·TS-062**가 연쇄 실패.
- **작업 내용** (3건 — 단언을 **약화하지 말고 갱신**한다):
  1. `test-header-history.js` `@header`에 `"task": "107"` + `"scenarios": [...]`(담당 TS-ID) 추가. TS-057이 테스트 자산에 요구하는 2필드다. **`description`은 건드리지 않는다**(태스크 번호 0개 유지 — `task`는 별개 필드이며 감지기는 `description`·`note`만 본다).
  2. `test-regression.js:937` 허용 태스크 번호 배열 `['077','080','082','083']`에 **`'107'` 추가**. 그 줄의 주석이 「허용 태스크 번호는 테스트 자산을 신설한 태스크만 누적한다」로 **누적을 규약화**하고 있으므로 이는 규약 집행이지 완화가 아니다.
  3. `test-shard-policy.js:1398` `assert.strictEqual(OTHER_TEST_FILES.length, 11, ...)` → **12**로 갱신하고 메시지에 107 신설분을 반영. **[MUST] `>= 11` 같은 부등호로 바꾸지 마라** — 정확한 개수 핀이 이 단언의 검증력이며, 부등호로 완화하면 다음 신설이 무성 통과한다.
- **완료 기준**: `node --test tests/*.js` → **fail 0** · 메타 3건(S-19·TS-062·TS-080) + TS-057 전건 GREEN · `--version` 불변
- **테스트**: TS-030, TS-032
- **실행 방법**: sub-agent
- **의존**: Step 4, Step 6

#### Step 6d: TS-045 파일 diff 핀 재정의 — **[PM Gate 발견, PLAN 사후 편입]**
- [x] 완료
- **소속 기능**: F-002 (+ F-004 회귀)
- **영역**: 도구 테스트
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/tests/test-regression.js` (1파일)
- **발견 경위**: Step 9가 `brain_tool.py`의 `@header`를 정리하자 **TS-045**(`test-regression.js:511-517`)가 실패했다. 이 테스트는 `git diff --numstat HEAD -- opal/tools/brain-tool/brain_tool.py`가 **빈 문자열**일 것을 단언한다 — 즉 **그 파일에 워킹트리 변경이 한 줄이라도 있으면 영구 실패**한다. 연쇄로 TS-062·S-19·TS-080이 함께 무너져 스위트가 4 fail이 됐다.
- **왜 고쳐야 하는가**: TS-045가 실제로 보호하려는 명제는 자기 실패 메시지에 적혀 있다 — 「무수정 성립이 F-12③의 **설계 결론**이다」. 즉 **080의 stderr 병기 설계가 brain-tool 기능 코드 수정을 요구하지 않았다**는 주장이다. 그런데 판정 수단이 「파일 전체 diff 0줄」이라 **`@header` 메타데이터 편집까지 설계 위반으로 오판**한다. 태스크 080 시점의 사실을 영구 단언으로 굳힌 mis-scoped 가드다.
- **작업 내용**: 판정 대상을 **「파일 전체 diff」 → 「`@header` 블록을 제외한 기능 코드」**로 좁힌다.
  - 구현: `git show HEAD:opal/tools/brain-tool/brain_tool.py`와 워킹 사본에서 **각각 `@header` 블록(파일 최상단 docstring)을 제거**한 뒤 **나머지가 바이트 동일**임을 단언한다.
  - **[MUST] 이것은 완화가 아니라 강화다** — `numstat === ''`는 "차이가 없다"만 보지만, 잔여 바이트 동일은 "기능 코드가 정확히 같다"를 본다. 단언 문구와 실패 메시지에 이 근거를 남긴다.
  - **[MUST] `@header` 제외 범위를 넓히지 마라** — 제외하는 것은 `@header` JSON 블록 하나뿐이다. 주석 전체·docstring 전체를 제외하면 실제 완화가 된다.
- **완료 기준**: TS-045 GREEN + 연쇄 3건(TS-062·S-19·TS-080) GREEN + 전체 스위트 **fail 0** + 다른 단언 무변경
- **테스트**: TS-030, TS-032
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 6e: 감지기를 「미정의 필드」 축으로 일반화 — **[컨벤션 진단 GC-C001, High]**
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 도구 + 도구 테스트
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`, `opal/tools/code-scan/tests/test-header-history.js`
- **발견 경위**: TEST PM Gate의 컨벤션 자동 진단(`GC-CONVENTION-260906.md`)이 **High 1건**을 냈다 — Step 6c가 배선한 감지기는 `resolved.changelog` **이름 하나만 리터럴 검사**하는데, 같은 태스크가 `header-standard.md` §2에 쓴 규정은 「표에 정의된 필드 외의 필드를 신설하지 않는다. 특히 이력 전용 필드 — **이름을 불문한다**(예: `changelog`·`history`·`revisions`)」다. **구현이 자기가 세운 규정을 위반한다.**
- **왜 이름 목록 확장으로 때우지 않는가**: `changelog`·`history`·`revisions` 3개를 상수 집합으로 넣어도 「이름 불문」이 아니라 「이름 3개」다. 다음에 `updates`로 이름만 바꾸면 다시 뚫린다 — Step 1b에서 **규정을 이름이 아니라 성질로 걸었던 이유**와 같은 논리를 구현에도 적용한다.
- **작업 내용**: §2 필드 정의 표의 **선언 필드 집합**을 상수로 두고, `@header`에 **그 밖의 필드가 존재하면** 위반으로 본다.
  - 선언 집합: `module`·`layer`·`domain`·`description`·`exports`·`depends`·`note`·`feature` (§2 표 8필드) **+ 예외 `task`·`scenarios`** — 이 둘은 §2가 「이력 필드가 아니라 다른 도구(테스트 자산)가 참조하는 필드」로 명시 제외했고 `test-regression.js` TS-057이 요구한다.
  - push: `{code:'header_history', sub:'undeclared_field', ..., detail:'<필드명>'}` — **같은 `code`를 재사용**해 `counts` 집계·비차단 제외를 승계한다. 기존 `sub:'changelog'` 경로는 **제거**하고 이 일반 규칙이 흡수한다(`changelog`는 미정의 필드의 한 사례일 뿐이다).
  - **[MUST] 임계값 판정 미적용** — 필드 존재 자체가 위반이다(`description`·`note`의 2개 이상 임계와 다른 축이다).
  - **[MUST] 상수에 근거 주석 동반** — `HEADER_READ_BYTES` 형식 준용, `header-standard.md` §2를 인용.
- **예상 부수 효과(정상)**: 현재 `track` 필드 보유 2파일이 새로 경고에 잡힌다. `track`은 §2 표에 없는 필드이며 **규정대로 드러나는 것이 맞다**. 비차단이라 CLOSE를 막지 않는다 — 정리는 이월한다.
- **테스트 갱신**: TS-052·TS-053·TS-054의 `sub` 기대값을 `changelog` → `undeclared_field`로 맞추고, **`history`·`revisions`·임의 이름(`updates`) 각각이 탐지되는 케이스를 추가**하라(「이름 불문」의 실증). `task`·`scenarios`는 **미탐지**여야 한다.
- **완료 기준**: 전체 스위트 fail 0 · `changelog`/`history`/`revisions`/임의 이름 전건 탐지 · `task`·`scenarios` 미탐지 · `--version` 불변 · 컨벤션 재진단 **Critical/High 0건**
- **테스트**: TS-052, TS-053, TS-054, TS-030, TS-032
- **실행 방법**: sub-agent
- **의존**: Step 6c

#### Step 7: state-tool 코어 2건 정리
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-task-agent — Python 파일이나 애플리케이션 BE가 아닌 프레임워크 도구 자산의 `@header` 텍스트 편집
- **파일**: `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리(각 11791자/20태스크, 7049자/15태스크 — 최대 분량 2건이라 단독 Step). `HISTORY-EVIDENCE.md` 미확인 번호는 보존
- **완료 기준**: 2건이 `header_history` 탐지에서 해제 + `@header` 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 8: state-tool 훅 + test-tool 3건 정리
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-task-agent — 위와 동일 사유
- **파일**: `opal/tools/state-tool/todo_mirror_hook.py`, `opal/tools/state-tool/tests/test_todo_mirror_hook.py`, `opal/tools/test-tool/lib/scenario.py`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리
- **완료 기준**: 3건 탐지 해제 + 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 9: brain-tool + memory-tool 3건 정리
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-task-agent — 위와 동일 사유
- **파일**: `opal/tools/brain-tool/brain_tool.py`, `opal/tools/brain-tool/tests/test_brain_tool.py`, `opal/tools/memory-tool/tests/test_memory_tool.py`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리
- **완료 기준**: 3건 탐지 해제 + 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 10: opal-agent + improve-tool + code-scan 훅 3건 정리
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-task-agent — 위와 동일 사유
- **파일**: `opal/tools/opal-agent/tests/test_opal_agent.py`, `opal/tools/improve-tool/tests/test_improve_tool.py`, `opal/tools/code-scan/code-map-hook.js`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리. `code-map-hook.js`는 `note`(625자, 이력성 서술 포함)도 함께 정리(R-4 AC(f)). **`code-scan.js`는 이 Step이 아니라 Step 6에서 처리한다**(동일 파일 동시 편집 금지)
- **완료 기준**: 3건 탐지 해제(`code-map-hook.js`는 description·note 양축) + 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023, TS-024
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 11: console BE 소스 3건 정리
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-be-agent — `dashboard/backend/` FastAPI 애플리케이션 코드이므로 BE 전문 워커가 「현재 유효한 계약 vs 이력」 판정(§3.3.2 (A) 2·3단)을 정확히 내린다
- **파일**: `dashboard/backend/models.py`, `dashboard/backend/config.py`, `dashboard/backend/main.py`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리. `models.py`의 `[T103/R-16]`·`[T103/R-20]` 단락은 현재 유효한 스키마 계약이므로 **태그만 제거하고 서술 보존**
- **완료 기준**: 3건 탐지 해제 + 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 12: console BE 어댑터·설정 테스트 2건 정리
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-be-agent — 위와 동일 사유(`brain_session.py`는 1954자 중 대부분이 동시성·락 순서 계약이라 판정 난도가 가장 높다)
- **파일**: `dashboard/backend/adapters/brain_session.py`, `dashboard/backend/tests/test_config.py`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리. `brain_session.py`의 락 순서 계약·`[KEY]`·`[MUST]` 문단은 **보존**하고 `[T060 F-2/F-4, T063 …]`·`(T063, …)` 태그만 제거
- **완료 기준**: 2건 탐지 해제 + 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 13: console BE 테스트 2건 정리
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-be-agent — 위와 동일 사유
- **파일**: `dashboard/backend/tests/test_routers.py`, `dashboard/backend/tests/test_stats.py`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리. `test_routers.py`의 `[T021/L2-R4api]`·`[T021-fix]`·`[T021-fix2]`·`[T023/RED]`·`[T023/RED-fix]` 5단락은 전형적 이력 append이므로 제거, 현재 검증 대상 서술만 남긴다
- **완료 기준**: 2건 탐지 해제 + 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 12b: console FE 1건 정리 (D-REQ-1 확대분)
- [x] 완료
- **소속 기능**: F-003
- **영역**: FE
- **agent**: opal-fe-agent — `dashboard/frontend/` React 컴포넌트이며, 「현재 유효한 UI 계약 vs 지나간 변경 이력」 판정에 FE 문맥이 필요하다
- **파일**: `dashboard/frontend/src/components/app-shell/AppShell.tsx`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리. distinct `061,063` 태그 제거, 현재 셸 레이아웃·라우팅 역할 서술은 보존
- **완료 기준**: 1건 탐지 해제 + 파싱 정상 + `exports` 무변경
- **테스트**: TS-020, TS-021, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 13b: backlog-tool + code-scan `test-shard.js` 2건 정리 (D-REQ-1 확대분)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-task-agent — 프레임워크 도구·테스트의 `@header` 정리로 도메인 전문성 불필요
- **파일**: `opal/tools/backlog-tool/backlog_tool.py`, `opal/tools/code-scan/tests/test-shard.js`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리. `backlog_tool.py` distinct `056,069` · `test-shard.js` distinct `082,083` 태그 제거. **[MUST] `test-shard.js:696-701`의 `VERSION` 핀 단언 본문은 건드리지 않는다** — `@header` 블록만 편집한다
- **완료 기준**: 2건 탐지 해제 + 파싱 정상 + `exports` 무변경 + `test-shard.js` 자체 테스트 통과
- **테스트**: TS-020, TS-021, TS-023, TS-030
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 13c: code-scan `test-feature.js`·`test-validate.js` 2건 정리 (D-REQ-1 확대분, 경계 재분류)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리
- **agent**: opal-task-agent — 위와 동일 사유
- **파일**: `opal/tools/code-scan/tests/test-feature.js`, `opal/tools/code-scan/tests/test-validate.js`
- **작업 내용**: §3.3.2 (A)(B) 규칙으로 `description` 정리. 두 파일 모두 distinct `077,080` — ANALYSIS가 「경계」로 분류했으나 축 기준(서로 다른 두 태스크 병기 = 이력 누적)으로 **진성 재분류**된 건이다. 077에서 만든 계약을 080이 이어받았다는 서술을 현재 검증 대상 서술로 교체한다
- **완료 기준**: 2건 탐지 해제 + 파싱 정상 + `exports` 무변경 + 두 파일 자체 테스트 통과
- **테스트**: TS-020, TS-021, TS-023, TS-030
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 1b: `header-standard.md` §2 — 이력 전용 필드 신설 금지 명문화 **[캡틴 3차 확정 편입]**
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent — 프레임워크 참조 문서 개정
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: §2 필드 정의 표 아래에 1문단 추가 — 「표에 없는 필드를 `@header`에 신설하지 않는다. 특히 **이력 전용 필드**(`changelog`·`history`·`revisions` 등 이름 불문)를 두지 않는다 — 이력은 git과 `tasks/{NNN}-*/DONE.md`가 갖는다(§2.1).」 + §2.1 적용 범위 문단을 「5필드」에서 **「`@header` JSON 블록 전체」**로 확장. §변경이력 v1.5 행에 이 편입분을 반영(행을 새로 만들지 말고 기존 v1.5 행 본문에 추가)
- **완료 기준**: TS-050 통과 — §2에 이력 전용 필드 금지 문장 존재 + §2.1 적용 범위가 「5필드 한정」이 아님
- **테스트**: TS-050
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 1c: §4.2 `description`·`note` 「담지 않는 것」을 감지 축과 정합화 — **[PM Gate 발견, PLAN 사후 편입]**
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/header-standard.md` (§4.2 표 2행)
- **발견 경위**: Step 17 검토 중 `dashboard/backend/routers/dashboard.py`가 `description`에 `[T103]` **1개**를 남긴 채 감지기를 통과하는 것을 확인했다. 감지기는 정상 동작이다(§3.2.2 (A) 축 정의상 **단발 출처 인용 1개는 허용**, 2개 이상이 이력 누적). 그런데 Step 1이 신설한 §4.2 표는 `description` 「담지 않는 것」에 **「태스크 번호(`[T061]`·`014:`·`TASK 077` 등 시점 표기 전반)」**이라고 써서 **1개도 금지**로 읽힌다.
- **왜 고쳐야 하는가**: 이번 태스크의 목표가 「규정·도구·자산 3층 일관」이다. 규정이 도구보다 엄격하면 **워커는 규정을 지켜도 도구가 안 잡고, 도구를 통과해도 규정 위반**이 된다 — 이 태스크가 제거하려던 바로 그 구조(원칙은 「어느 필드에도」인데 적용 범위는 5필드였던 `changelog` 구멍)의 재발이다.
- **작업 내용**: §4.2 표 `description`·`note` 행의 「담지 않는 것」에서 「태스크 번호」 항목을 **축 정의와 같은 문언으로 정밀화**한다.
  - 취지: **변경 이력 — 서로 다른 태스크 번호가 2개 이상 쌓이는 형태**를 금지한다. **출신 태스크 1개의 단발 인용은 허용**한다(자산이 어디서 왔는지는 시간이 지나도 늘지 않는다).
  - **[MUST] 감지기 임계값(2)과 같은 근거를 인용**해 규정·도구가 같은 축을 말하고 있음을 본문에서 드러낸다.
  - **[MUST] `note` 행도 같은 기준으로 맞춘다** — 감지기가 `note`에 동일 판정식을 적용한다.
  - **[MUST] `changelog` 같은 이력 전용 필드 금지(§2)는 그대로 유지** — 그건 임계값 축이 아니라 필드 존재 축이다. 두 규칙을 섞지 마라.
- **완료 기준**: §4.2 `description`·`note` 「담지 않는 것」이 「2개 이상」 기준으로 서술되고, §3.2.2 임계값 2와 모순되지 않는다. 최상위 절 개수 불변. `code-scan` 스위트 fail 0
- **테스트**: TS-002, TS-050
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 1b

#### Step 5b: `changelog` 81엔트리 이력 소실 확인 **[캡틴 3차 확정 편입]**
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: opal-task-agent — 읽기 전용 git 조사
- **파일**: `tasks/107-260906-opd-헤더필드-작성기준-이력분리/HISTORY-EVIDENCE.md` (기존 파일에 §2 섹션 추가)
- **작업 내용**: `changelog` 보유 28파일 × 81엔트리 각각에 대해 그 이력이 git 로그 또는 DONE.md에 실재하는지 확인. Step 5와 **동일 강도** — 해시는 `git cat-file -e` resolve, 경로는 파일 실존. `파일 | 엔트리 요약 | 근거 유형 | 근거 | 확인여부` 5열 표
- **완료 기준**: TS-051 통과 — 81행 전건 근거 채움 또는 「보존 대상」 사유 기재
- **테스트**: TS-051
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 6c: 감지기 `changelog` 축 추가 **[캡틴 3차 확정 편입]**
- [x] 완료
- **소속 기능**: F-002
- **영역**: 도구 + 도구 테스트
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`, `opal/tools/code-scan/tests/test-header-history.js`
- **작업 내용**: `changelog` 필드 **존재 자체**를 `violations.push({code:'header_history', sub:'changelog', ...})`로 감지한다. **[MUST] 임계값 판정을 적용하지 마라** — `description`·`note`는 「단발 인용 vs 누적」을 가려야 하지만 `changelog`는 **필드 이름이 곧 이력 선언**이므로 비어 있지 않으면 엔트리 1개라도 위반이다. `detail`에 엔트리 수를 싣는다. 비차단 유지(`blockingViolations` 제외는 `code` 단위라 이미 적용됨). 테스트 3건 신설(존재→탐지 / 빈 배열·필드 부재→미탐지 / `sub` 값 검증)
- **완료 기준**: 신설 3건 GREEN + 전체 스위트 fail 0 + 재측정에서 `sub:"changelog"` **28건** 탐지(정리 전)
- **테스트**: TS-052, TS-053, TS-054
- **실행 방법**: sub-agent
- **의존**: Step 6, Step 6b

#### Step 16~22: `changelog` 제거 20파일 (신규분) **[캡틴 3차 확정 편입]**
- [x] 완료
- **소속 기능**: F-003
- **영역**: 이력 정리 (console BE 3 Step / console FE 4 Step)
- **agent**: `dashboard/backend/*` → opal-be-agent · `dashboard/frontend/*` → opal-fe-agent
- **파일**: 23건 정리목록 **밖**의 `changelog` 보유 20파일 — 3파일 이하씩 7 Step으로 분할(§산출량 상한)
  - Step 16(BE): `cache.py`, `stats.py`, `tests/test_cache.py`
  - Step 17(BE): `routers/brain.py`, `routers/config.py`, `routers/dashboard.py`
  - Step 18(BE): `routers/tasks.py`, `tests/test_brain.py`, `tests/test_parsers.py`
  - Step 19(FE): `lib/api.ts`, `router.tsx`, `store/ui-store.ts`
  - Step 20(FE): `pages/brain/BrainPage.tsx`, `pages/brain/brain-job-polling.test.ts`, `pages/brain/brain-new-conversation-prime.test.ts`
  - Step 21(FE): `pages/brain/brain-storage.test.ts`, `pages/dashboard/DashboardPage.tsx`, `pages/dashboard/DashboardPage.stats.test.tsx`
  - Step 22(FE): `pages/settings/SettingsPage.tsx`, `test/setup.ts`
- **작업 내용**: `@header`에서 **`changelog` 필드를 통째로 제거**한다. `description`에 이력이 섞여 있으면 §3.3.2 (A) 3단 판정으로 함께 정리한다. 그 밖 필드 무변경
- **완료 기준**: 파일별 `changelog` 부재 + `@header` JSON 파싱 정상 + `exports`·`module`·`layer`·`domain` 무변경
- **테스트**: TS-020, TS-023, TS-026, TS-055
- **실행 방법**: sub-agent
- **의존**: Step 5b, Step 6c

#### Step 23: `AppShell.tsx` `changelog` 제거 (Step 12b 후속) **[캡틴 3차 확정 편입]**
- [x] 완료
- **소속 기능**: F-003
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/components/app-shell/AppShell.tsx`
- **작업 내용**: Step 12b가 `description`을 정리했으나 `changelog`(2엔트리)는 캡틴 3차 확정 **이전**이라 남아 있다. 필드를 제거한다
- **완료 기준**: `changelog` 부재 + 파싱 정상
- **테스트**: TS-055
- **실행 방법**: sub-agent
- **의존**: Step 12b, Step 5b

#### Step 14: 회귀 검증 + 전수 재측정
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 검증
- **agent**: opal-test-agent — 테스트 전문 워커(mode: regression)
- **파일**: (검증 전용, 변경 없음)
- **작업 내용**: §3.4.2 5행 전건 실행. §3.2.3 1줄 명령으로 전수 재측정하여 `hits`가 **0건**인지 확인한다 — `sub:"description"`·`sub:"note"`·**`sub:"changelog"` 3축 전부 0건**(D-REQ-1 (나) 23건 + 캡틴 3차 `changelog` 28건 전건 정리). 0건이 아니면 미해제 파일 목록을 블로커로 보고한다
- **완료 기준**: TS-030~TS-033 전건 통과 + **23건 전건 탐지 해제** 확인(`header_history` hits 0)
- **테스트**: TS-020, TS-023, TS-030, TS-031, TS-032, TS-033
- **실행 방법**: sub-agent
- **의존**: Step 6, Step 7~13c 전건

#### Step 15: 배포 반영 (조건부 — 소유자 실행)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 환경
- **agent**: PM 직접 — `~/.opal/` 전역 배포본을 갱신하는 비가역 행동이므로 워커에 위임하지 않는다
- **파일**: (실행: `scripts/install-mac.sh`)
- **작업 내용**: `header-standard.md`·`header-rules.md` 개정본을 `~/.opal/references/`에 반영. **[MUST]** 소유자 명시 승인 없이 실행하지 않는다 — 워크트리 밖 전역 상태를 바꾼다
- **완료 기준**: 승인 시 `~/.opal/references/header-standard.md`에 §2.1·§4.2 존재. 미승인 시 DONE.md §이월에 「배포 미반영」 1행 기록 후 종료
- **테스트**: 수동 확인
- **실행 방법**: direct
- **의존**: Step 14

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ 2 ∥ 3 ∥ 4 ∥ 5 | 5개 Step의 대상 파일 집합이 완전 비중첩(참조 문서 2 · docs 1 · 신규 테스트 1 · 신규 문서 1) |
| Step 4 → Step 6 | RED-first — 테스트가 먼저 존재해야 구현이 GREEN을 향한다. 작성자(opal-test-agent) ≠ 구현자(opal-task-agent) |
| Step 6 ⊃ `code-scan.js` note 정리 | **동일 파일을 2개 Step이 변경하면 분할하지 않고 같은 Step에 묶어 순차 편집한다** — R-3 구현과 R-4 AC(f) note 정리가 같은 `code-scan.js`이므로 Step을 나누면 후행 저장이 선행 편집을 덮어쓴다 |
| Step 1, 5 → Step 7~13 | Step 1이 정리 기준(§3.1.2 (B))을 확정하고 Step 5가 이력 소실 방지 근거(R-4 AC(c))를 제공한 뒤에만 제거가 허용된다 |
| Step 7 ∥ 8 ∥ 9 ∥ 10 ∥ 11 ∥ 12 ∥ 12b ∥ 13 ∥ 13b ∥ 13c | 23파일을 3개 이하씩 비중첩 분할 — **산출 파일 3개 초과 시 분할** 규칙 준수. 파일 간 의존 없음 |
| Step 7~13 분할 기준 | 모듈 응집도 우선(state-tool / brain·memory / opal-agent·improve·code-scan훅 / console BE 소스 / console BE 어댑터·테스트). Step 7만 2건인 이유는 두 파일이 전체 분량의 55%(18,840자)를 차지해 단독 처리가 안전하기 때문 |
| Step 6, 7~13 → Step 14 | 회귀 검증은 모든 변경 반영 후 1회 |
| Step 14 → Step 15 | 배포는 검증 통과 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 4필드 가이드 3요소 완비 | TS-001, TS-002 | §4.2 표 4행 × 3열 전건 채움, `description`·`note` 「담지 않는 것」에 이력·태스크 번호 명시 |
| F-001 | 기존 원문 무변경 | TS-003, TS-007 | §2 필드 표·§4.1 exports 21행 diff 0줄, `header-standard.md §7` 참조 문자열 불변 |
| F-001 | 원칙 명문화 + 3문서 정합 | TS-004, TS-005, TS-006 | `opal-doc-standard.md:28` 인용 존재, 원문 보유 문서 정확히 1개, 「헤더 내 변경이력 라인」 0건 |
| F-002 | 비차단 보장 | TS-010, TS-011 | 이력 패턴만 있으면 exit 0 · `ok:true`, 차단 위반 동반 시에도 사유가 `header_history`가 아님 |
| F-002 | 오탐 0건 | TS-013, TS-014 | F-code·TS-id(나열·범위 포함)·HTTP·IP·경로줄번호·수량 전건 미탐지 |
| F-002 | 진성 전건 탐지 | TS-015, TS-016 | 표기 4형태 전건 탐지, 임계값 경계 양방향 고정 |
| F-002 | 스키마 additive | TS-012, TS-017, TS-018 | 신규 5키 존재 · 기존 counts 9키 값 불변 · `VERSION` 불변 |
| F-003 | 23건 해제 | TS-020 | 재측정 결과 `header_history` hits **0건** |
| F-003 | 역할 보존 + 이력 근거 | TS-021, TS-022 | 첫 문장 동일·비공란, `HISTORY-EVIDENCE.md` **23행** 근거 완비 |
| F-003 | 파싱·exports 무변경 | TS-023, TS-024 | `uncovered` 0건 · `exports_not_found` 불변 · `note` **1건**(`code-scan.js`) 정리 — 이력 누적 판정 대상 기준(TASK.md R-4 AC(f) 정정 반영) |
| F-004 | 회귀 0건 | TS-030~TS-033 | code-scan 기존 344 failed 0 · state-tool 400/3 · 메타 3건 · `--changed` exit 0 |

### 5.2 회귀 테스트

- [ ] `code-scan` **기존 344건 중 failed 0** (총계는 344 + `test-header-history.js` 신설분 — **[MUST] 총계 숫자 일치로 판정하지 않는다**, RPT-2)
- [ ] `state-tool` 400 passed / 3 skipped / 0 failed
- [ ] 메타 테스트 3건(S-19 · TS-062 · TS-080 계열) 통과
- [ ] `code-scan --version` = `code-scan v1.6.0` 불변
- [ ] `validate --json`의 `coverage.percent`·기존 `counts` 9키 값 불변
- [ ] `validate --changed` 차단 위반 증가 0건(exit 0)
- [ ] `header-standard.md` §3·§5·§6·§7 절 번호 불변 (`test-header-source.js` 통과)

### 5.3 코드/문서 품질

- [ ] **[MUST] `docs/CONVENTIONS.md` §배포 경계**: `~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다 — Step 1·2는 `opal/core/references/` 소스만 수정
- [ ] **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무**: 3문서 전건 변경이력 행 추가(KST `YYYY-MM-DD HH:mm`, semver, `(107)` 포함)
- [ ] **[MUST] `docs/CONVENTIONS.md` §Citation Rules**: PLAN·DONE 등 산출물의 모든 주장에 `{경로}:{라인}` 또는 `docs/문서명 §섹션` 인용
- [ ] **[MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리**: 이번 변경은 플랫폼 분기를 만들지 않는다 — `code-scan.js`는 어댑터 계층 밖 공통 도구이며 Claude/Cursor/Gemini 분기 코드를 추가하지 않는다
- [ ] 신설 테스트 파일 자신의 `@header`가 신설 기준(§3.1.2 (B))을 준수 — `description` 태스크 번호 0개
- [ ] `code-scan.js` 신규 상수에 실측 근거 주석 동반(`HEADER_READ_BYTES` 형식 준용)
- [ ] git 이력 미변경 — `commit`·`push`·`reset`·`rebase` 0회

### 5.4 보안

- [ ] 신규 코드에 하드코딩된 토큰·시크릿·절대 홈 경로 0건 (테스트는 `OPAL_HOME` 가짜 홈 주입으로 실제 홈 격리 — `test-validate.js:63-64` 패턴)
- [ ] 정리 대상 23파일의 `description`·`note`에 자격증명·개인 식별자가 남아 있지 않은지 확인(제거 방향이므로 노출 증가 없음)
- [ ] `HISTORY-EVIDENCE.md`에 커밋 해시·경로만 기록하고 커밋 본문 전문을 전사하지 않는다
- [ ] `.env`·인증 파일 신규 생성 0건, `.gitignore` 변경 0건

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 15개 | 복잡 |
| 변경 파일 수 | 22개 (문서 3 · 도구 1 · 테스트 신규 1 · 정리 18 중 `code-map-hook.js` 중복 제외 · 산출물 1) | 복잡 |
| 모듈 범위 | 다중 (참조 문서 / code-scan / state-tool / brain-tool / memory-tool / improve-tool / opal-agent / test-tool / console BE) | 복잡 |
| 작업 유형 | 규정 신설 + 도구 기능 신설 + 대규모 자산 정리 | 복잡 |
| 외부 의존성 | 없음 (신규 패키지·API 0건) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬 5)
  A1 opal-task-agent   : Step 1  (header-standard.md)
  A2 opal-task-agent   : Step 2  (header-rules.md)
  A3 PM 직접           : Step 3  (docs/CONVENTIONS.md)
  A4 opal-test-agent   : Step 4  (test-header-history.js, RED)
  A5 opal-task-agent   : Step 5  (HISTORY-EVIDENCE.md, 읽기 전용 git 조사)

Batch 2 (순차 1)
  A6 opal-task-agent   : Step 6  (code-scan.js — 구현 + 자기 note 정리)   [A4 완료 후]

Batch 3 (병렬 7)
  A7  opal-task-agent  : Step 7   (state-tool 코어 2)
  A8  opal-task-agent  : Step 8   (state-tool 훅 + test-tool 3)
  A9  opal-task-agent  : Step 9   (brain-tool + memory-tool 3)
  A10 opal-task-agent  : Step 10  (opal-agent + improve-tool + code-map-hook 3)
  A11 opal-be-agent    : Step 11  (console BE 소스 3)
  A12 opal-be-agent    : Step 12  (console BE 어댑터·설정 테스트 2)
  A13 opal-be-agent    : Step 13  (console BE 테스트 2)

Batch 4 (순차 1)
  A14 opal-test-agent  : Step 14  (회귀 + 전수 재측정)

Batch 5 (조건부)
  A15 PM 직접          : Step 15  (배포, 소유자 승인 시)
```

**파일 충돌 방지 검증**: 22개 대상 파일이 Step 간 **중복 0건**. 유일한 잠재 충돌인 `code-scan.js`(R-3 구현 + R-4 note 정리)는 Step 6 단일 에이전트로 묶었다. `code-map-hook.js`는 `code-scan.js`와 다른 파일이므로 Step 10 배치가 안전하다.

### C-2. 스킬 요구사항

| 필요 | 매칭 | 갭 |
|------|------|----|
| PLAN → EXECUTE 단계 진행 | `op-dev-execute` | 없음 |
| RED-first 테스트 작성 | `~/.opal/references/harness/red-first.md` §2·§3 | 없음 |
| `@header` 작성 규칙 | `opal/core/references/harness/header-rules.md`(본 태스크가 개정) | **Step 7~13 워커는 Step 1·2 개정본을 읽어야 한다** — 배포 전이므로 `~/.opal/` 사본이 아닌 **소스 경로**를 디스패치 프롬프트에 명시 주입 |
| 회귀 검증 | `op-dev-test-agent` (mode: regression) | 없음 |
| 동일 패턴 3회 이상 반복 | Step 7~13이 §3.3.2 (A)(B) 동일 규칙 7회 반복 → **인라인 지침으로 충분**(스킬 신설 불필요, 규칙 원문이 이미 `header-standard.md` §2.1·§4.2에 SSOT로 존재) | 없음 |

### C-3. 도구 요구사항

| 도구 | 용도 | 신규 설치 |
|------|------|----------|
| `node` (내장 `node:test`) | code-scan 테스트 실행 | 불필요 |
| `python3` + `pytest` | state-tool 회귀 | 불필요 |
| `git` | 이력 소실 확인(Step 5) — 읽기 전용 명령만 | 불필요 |
| `code-scan validate --json` | 전수 재측정 | 본 태스크가 확장 |
| MCP | 해당 없음 — 외부 라이브러리 조사 불필요 | - |

### C-4. 테스트 전략

| 계층 | 대상 | 명령 | 실행 시점 |
|------|------|------|----------|
| L1 산출물 검사 | 문서 3건(TS-001~007) | grep/diff 기반 | Step 1~3 직후 |
| L2 기능 (CLI 블랙박스) | 감지기(TS-010~019) | `node --test tests/test-header-history.js` | Step 4(RED) → Step 6(GREEN) |
| L2 회귀 | code-scan 전량 | `node --test tests/*.js` | Step 6, Step 14 |
| L2 회귀 | state-tool 전량 | `python3 -m pytest tests/ -q` | Step 14 |
| L3 실자산 전수 | 109파일 재측정(TS-020·TS-023) | §3.2.3 1줄 명령 | Step 6(23건 확인) → Step 14(5건 확인) |

**작성자≠구현자**: Step 4(opal-test-agent) ≠ Step 6(opal-task-agent), Step 14 검증자(opal-test-agent) ≠ Step 7~13 구현자. self-confirming을 구조로 차단한다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 참조 문서 | Markdown | 해당 없음 |
| 도구 | Node.js (CommonJS, `node:test`) — `code-scan.js` v1.6.0 | 해당 없음 |
| 정리 대상 | Python 3 (docstring `@header`) 13건 · JavaScript 2건 · TypeScript 1건(`.tsx`, D-REQ-1 대상) | 해당 없음 |
| 콘솔 BE | FastAPI · Pydantic (`dashboard/backend/`) | 해당 없음 |

> 프레임워크 내부 문서·도구 개정이라 community-skills(React/Next/Python 등) 적용 대상이 없다 — ANALYSIS §6.3·§6.4와 동일 결론.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 해당 없음 | 외부 라이브러리 API 조사 불필요 — 전부 프로젝트 내부 자산 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | @header 표준 | `opal/core/references/header-standard.md` | §2 필드 정의(`:11-23`)·§4 exports 가이드(`:133-159`) — R-1·R-2 개정 대상 원문, §4.2 형식 준용 근거 |
| D-2 | 설계 | EXECUTE @header 규칙 | `opal/core/references/harness/header-rules.md` | §워커 권한 경계(`:66-76`)·§파일 수정 시(`:112-123`) — R-2 개정 대상 |
| D-3 | 설계 | 문서 표준 | `opal/core/references/opal-doc-standard.md` | `:28` "변경 이력은 git이 갖는다" — R-2 원칙 인용 원문 |
| D-4 | 소스 | code-scan 도구 | `opal/tools/code-scan/code-scan.js` | `:34-46` Constants 형식 · `:3155` cmdValidate · `:3200-3257` 파일 루프 · `:3295-3308` manifest_oversize push · `:3434-3444` counts · `:3447-3450` blockingViolations |
| D-5 | 소스 | code-scan 테스트 | `opal/tools/code-scan/tests/test-validate.js` | `:22` red-first 동결 주석(신규 파일 분리 근거) · `:60-75` run() 하네스·`OPAL_HOME` 격리 패턴 |
| D-6 | 소스 | VERSION 핀 | `opal/tools/code-scan/tests/test-shard-policy.js:1519-1521` · `tests/test-shard.js:696-701` | VERSION 상향 시 갱신 필요 지점 — 상향 안 함 결정 근거 |
| D-7 | 설계 | 프로젝트 컨벤션 | `docs/CONVENTIONS.md` | `:218` @header 규칙(R-2 AC(e) 개정 대상) · §변경이력 작성 의무 · §배포 경계 · §Citation Rules · §플랫폼 분기 격리 |
| D-8 | 산출물 | 태스크 107 ANALYSIS | `tasks/107-260906-opd-헤더필드-작성기준-이력분리/ANALYSIS.md` | §7 Q2 18건 분류표(진성 6/오탐 9/경계 3) · §8 확정값 승계 |
| D-9 | 산출물 | 태스크 107 TASK | `tasks/107-260906-opd-헤더필드-작성기준-이력분리/TASK.md` | R-1~R-5 AC · §범위 ④ 캡틴 확정 18건 |
| D-10 | 설정 | code-scan 스코프 | `.opal/code-scan.json:3-7` | 전수 재측정 스코프(framework / console-fe / console-be = 109파일) |
| D-11 | 규칙 | Citation Rules | `opal/core/references/harness/citation-rules.md` | 인용 포맷·[MUST] 토큰·근거 등급 E1 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 신규 위반 코드가 `blockingViolations`에서 누락되면 이력 보유 자산 23건이 전부 CLOSE를 차단한다 | F-002 | P0 | TS-010·TS-011이 exit code를 직접 단언. Step 6 완료 기준에 재측정 `ok:true` 포함 (H-1) |
| 2 | 임계값을 3으로 "안전하게" 올리고 싶은 유혹 — 진성 6건이 조용히 탈락한다 | F-002 | P0 | §3.2.2 (A)에 **[MUST] 임계값 2는 축 정의의 귀결**로 못박고 TS-016이 경계를 양방향 고정 (H-3) |
| 3 | 마스킹 M4의 나열·범위 꼬리가 빠지면 정리 완료한 파일이 `TS-024/025/026` 하나로 다시 경고에 걸린다 | F-002 | P1 | TS-013에 나열형·범위형 케이스 명시. 실측으로 이미 확인된 실패 모드 (H-2) |
| 4 | 정리 중 `@header` JSON 파싱이 깨지면 `uncovered:newly_uncovered`(차단)로 떨어져 CLOSE가 막힌다 | F-003 | P0 | 각 Step 완료 기준에 `validate` 파싱 정상 포함. 한글 본문의 따옴표·역슬래시 주의 (H-5) |
| 5 | `description` 편집 중 `exports` 배열을 함께 건드리면 `exports_not_found`가 발생한다 | F-003 | P1 | **[MUST] `exports`·`module`·`layer`·`domain` 무변경**(R-4 AC(e)) + TS-023이 `counts.exports_not_found` 불변 단언 (H-6) |
| 6 | 8건이 테스트 파일이라 모듈 docstring 편집이 수집 경로에 닿는다 | F-003 | P1 | Step 14에서 state-tool 400/3 · code-scan 344 회귀 (H-7) |
| 7 | 절 삽입으로 `header-standard.md` §5·§6·§7 번호가 밀리면 `code-scan.js:58`·`:196`·`test-header-source.js:204`의 `§7` 문자열 단언이 깨진다 | F-001 | P1 | **[MUST] 신설은 하위 절(`### 2.1`·`### 4.1`/`### 4.2`)로만** + TS-007 (H-8) |
| 8 | 3문서에 원칙 원문을 각각 복제하면 다음 개정에서 갈라진다(R-2 AC(d) 위반) | F-001 | P1 | SSOT 1곳(`header-standard.md` §2.1) + 포인터 2곳 구조. `docs/CONVENTIONS.md:281` v1.7.0이 확립한 패턴 준용. TS-005가 원문 보유 문서 1개를 단언 (H-9) |
| 9 | 잔여 5건(D-REQ-1)이 방치되면 프레임워크 자산이 신설 규정을 위반한 채 남는다 — ANALYSIS §5 R-1이 지적한 재발 경로와 같은 구조 | F-003 | P1 | Step 14에서 잔여 목록을 명시 기록하고 DONE.md §이월에 올린다. 소유자가 (나)를 택하면 Step 12b·13b 2개 추가로 흡수 |
| 10 | Step 7~13 워커가 **배포 전** `~/.opal/references/header-rules.md` 사본을 읽고 구 규칙대로 작업한다 | F-003 | P1 | 디스패치 프롬프트에 **소스 경로**(`opal/core/references/...`)를 명시 주입 (C-2 갭 항목) |
| 11 | 신설 테스트 파일이 메타 3건에 곱해져 스위트 시간이 늘어난다 | F-002 | P2 | 커밋 픽스처 증설 없이 `mkdtempSync` 런타임 생성으로 한정, 테스트 10건 이내 (H-10) |
| 12 | Step 15 배포가 워크트리 밖 전역 `~/.opal/`을 바꾼다 | F-001 | P1 | **[MUST] 소유자 명시 승인 전 미실행**. 미승인 시 이월 기록 후 종료 |
