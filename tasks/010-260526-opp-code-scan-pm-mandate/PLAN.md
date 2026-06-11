# PLAN: code-scan PM 우선 무조건화 — 코드 작업 한정 + scan.json 자동 생성 + brain 역할 분담

> 작성일: 2026-06-11
> 입력: `tasks/010-260526-opp-code-scan-pm-mandate/TASK.md` (**v2 재정의** — "v2 재정의" 표가 범위 SSOT)
> 출력: PLAN.md
> 모드: semi-agentic (PLAN까지 캡틴 검토)

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | §3 디스패치 전 프로세스(stub)·§9 code-scan.json PM 관리 의무 — F-1 정합 앵커 |
| D-2 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악(:103-109)·§Step 1.5 brain(:111-131, 016 v1.3) — F-1·F-2 |
| D-3 | 설계 | core/AGENT.md | `opal/core/AGENT.md` | §code-scan 활용 규칙(:176-189)·§opal-brain 활용 규칙(:191-221, 016 v3.2) — F-2 |
| D-4 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | §생성 시점(:10-27) — F-3 |
| D-5 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | §code-scan 활용 가이드(:52-74) — F-4 |
| D-6 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | 표준 검토 항목(현행 13항목, :44-88) — F-5 |
| D-7 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | .md frontmatter @header 파싱 능력 검증 `:274-312` |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 포맷(테이블+인라인+MUST) |
| D-9 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 Guards·§9 도구 우선 원칙(:205-209) — 오버라이드 근거 |
| D-10 | 외부 | MAMS scan.json 실증 | `/Volumes/Data/StoreLinkStudio/mams/.opal/code-scan.json` | scopes/extensions/.md 패턴 실증 |
| D-11 | 설계 | 016 결정 (brain 역할) | `tasks/016-260611-opp-wiki-intelligence/DONE.md` + `.opal/brain/pages/concept/wiki-intelligence-decisions-016.md` | brain/code-scan 역할 분담·analyze 의존 근거 |
| D-12 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | analyze/sync-header의 code-scan @header 의존 검증 `:6, :629-643` |
| D-13 | 설계 | PROJECT.md | `docs/PROJECT.md` | §프로젝트 구성(:85-90) — F-3 scopes 추론 소스 |
| D-14 | 설계 | install-mac.sh | `scripts/install-mac.sh` | §변경이력 strip(`:212-226`)·배포 절차 — 마지막 Step |
| D-15 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력·배포 경계·네이밍 [MUST] |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/pm/dispatch-process.md` | PM 디스패치 전 프로세스 SSOT | ✅ 수정 (F-1·F-2) | `:103-109`(code-scan 조건부 문구), `:111-131`(Step 1.5 brain) |
| `opal/core/AGENT.md` | 에이전트 정의·code-scan/brain 활용 규칙 | ✅ 수정 (F-2) | `:176-189`(code-scan 규칙), `:191-221`(brain 규칙) |
| `opal/core/references/pm/code-scan-management.md` | scan.json PM 관리 의무 | ✅ 수정 (F-3) | `:10-27`(생성 시점·최소 구조) |
| `opal/core/references/harness/header-rules.md` | @header 규칙·code-scan 활용 가이드 | ✅ 수정 (F-4) | `:52-74`(활용 가이드·적용 조건) |
| `opal/core/references/harness/pm-review-gate.md` | PM Gate 표준 검토 항목 | ✅ 수정 (F-5) | `:44-88`(현행 13항목) |
| `opal/core/references/opal-pm.md` | PM 행동 프로세스(상위 stub) | ⚠️ 조건부 (F-1 정합) | `:53-59`(§3 stub), `:112-118`(§9 code-scan PM 관리) |
| `.opal/MEMORY.md` | 프로젝트 메모리 인덱스 | ✅ 수정 (F-6) | `:23-25`(메모리 표), `:39`(010 히스토리 행) |
| `opal/tools/code-scan/code-scan.js` | code-scan 도구 | ❌ 무변경 (제약) | `:274-312`(.md @header 파싱 — 능력 확인용) |
| 워커 AGENT.md 6종 | 전문 워커 정의 | ❌ 무변경 (제약) | — |

### 현재 상태

**조사로 확인한 사실 (추측 아님):**

1. **dispatch-process.md (v1.3)** — `§code-scan 사전 범위 파악`(:103-109)이 `"`.opal/code-scan.json`이 존재하는 프로젝트에서"`로 시작하는 **조건부 진입**이며, `:109`에 `"code-scan.json 없으면 일반 파일 탐색(Glob/Grep) 사용"`이라는 회피 경로가 박혀 있다. brain `§Step 1.5`(:111-131)는 016 v1.3로 이미 정합 상태이며 `:131`에 `"순서는 brain → code-scan"`이 명시됨 (회귀 금지 대상).

2. **opal-pm.md** — TASK F-1의 "opal-pm.md §3 요약 정합"과 **불일치**: opal-pm.md `§3`(:53-59)은 dispatch-process.md로 위임하는 **stub일 뿐 code-scan 텍스트를 직접 포함하지 않는다**. code-scan 관련 요약은 `§9 code-scan.json PM 관리 의무`(:112-118)에 존재. → F-1의 opal-pm.md 정합 대상은 §3이 아니라 **§9**가 적절 (doc_code_mismatch C-1 참조).

3. **core/AGENT.md (v3.2)** — `§code-scan 활용 규칙`(:176-189)이 `"`.opal/code-scan.json`이 존재하는 프로젝트에서"`로 시작 + `:189`에 `"code-scan.json 없으면 code-scan 사용 생략 → Glob/Grep으로 탐색"` 회피 경로. `§opal-brain 활용 규칙`(:191-221)은 016 W4(ingest 트리거)·W5(search 후보→선택)로 이미 정합 (회귀 금지). 두 규칙 간 **역할 분담 표 부재** — brain과 code-scan의 코드 정보 경계가 명문화되지 않음.

4. **code-scan-management.md** — `§생성 시점`(:12)이 `"처음 사용하려 할 때 ... PM이 직접 생성한다"`로 게이트·자동화 부재. 최소 구조(:16-23)는 `.md` 미포함·`scopes: {}` 빈 값.

5. **header-rules.md** — `§code-scan 활용 가이드 §적용 조건`(:74)이 `"`.opal/code-scan.json`이 존재하는 프로젝트에서만 활용한다. 없으면 일반 파일 탐색(Glob/Grep)"`. **빈 결과/저커버리지 폴백 기준은 전무**.

6. **pm-review-gate.md** — 표준 검토 항목은 현행 **13개**(:44-88, 1~13). code-scan 관련은 §8(EXECUTE 사후 @header 검증)뿐 — **디스패치 전 code-scan 인용 검증 항목 부재**.

7. **code-scan.js 능력 검증** — `extractHeader`(:274-312)가 @header JSON을 brace-matching으로 추출하며 Python docstring·Vue HTML comment·주석 prefix(`*`/`#`/`//`) 정리 후 `JSON.parse`. `.md` 확장자는 code-scan.json `extensions`에 `.md`를 추가하면 frontmatter @header가 파싱됨 (MAMS 실증 D-10: extensions에 `.md` 포함).

8. **brain ↔ code-scan 의존 검증** — `brain_tool.py:6`(@header description)에 `"sync-header는 code-scan @header → brain entity frontmatter 단방향 동기화"`, `"analyze는 code-scan @header 정량 집계 → JSON"` 명시. `:632-643`에서 `analyze`/`sync-header`가 `.opal/code-scan.json` 부재 시 `code_scan_json_missing`로 실패. → **brain 품질은 code-scan @header 커버리지에 종속**(v2 진단 §5 실증). 역할 분담의 핵심 근거.

9. **MAMS 실증(D-10)** — `scopes`(be/fe/plan/design 4종), `extensions`에 `.md` 포함, `exclude`에 `backup`·`.pytest_cache`·`tests` 등 보강. F-3 추론 소스 3종(scopes/extensions/exclude)의 실제 패턴.

10. **PROJECT.md §프로젝트 구성**(:85-90) — F-3 `scopes` 추론의 1차 소스. "요소/경로/기술 스택/전문 에이전트" 표의 `경로` 컬럼이 scopes 후보.

### 영향 범위

- **수정 대상 .md 5종 확정** (F-1~F-5) + **MEMORY.md**(F-6) + **opal-pm.md §9 조건부**(F-1 정합) → 최대 7개 소스 파일.
- **무변경 보장**: `code-scan.js`(코드 무변경 제약), 워커 AGENT.md 6종(범위 한정 제약), brain 규칙 W4/W5(016 회귀 금지 제약).
- **배포 영향**: 소스(`opal/core/`) 수정 → `install-mac.sh` 재배포 필요 (`~/.opal/` 직접 편집 금지 — D-15 §배포 경계).
- **하위 호환**: 기존 태스크/문서 소급 변경 없음 (citation-rules §5). 신규 규약은 트리거 시점부터 발동.

---

## 2. 구현 계획

### 핵심 제약 ([MUST] 원문 인용)

- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" (→ D-15)
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, ...)에서 수행한다. 변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다." (→ D-15)
- [MUST] TASK.md §제약: "변경 범위 한정 — PM 행동 규약 + 생성 규약 + 폴백 기준 + PM Gate 항목만. 워커 AGENT.md 6종 미수정. 코드(code-scan.js) 무변경."
- [MUST] TASK.md §제약: "016 산출물 회귀 금지 — AGENT.md v3.2·dispatch-process v1.3의 brain 규칙(W4·W5)을 훼손하지 않는다. brain→code-scan 순서 유지."
- [MUST] TASK.md §제약: "state-tool 정합 — STATE.md 폴백 기록은 자유 텍스트 영역만 사용, 현황판 행 직접 편집 금지."
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "문서 본문 = 한국어(기술 용어 영어 병기), 파일/폴더 이름 = English, kebab-case" (→ D-15)

### v2 핵심 의미론 (캡틴 합의 — 설계 기준)

> brain = **선별 핵심 모듈**의 @header 스냅샷 + 설계 배경 WHY (원천은 code-scan @header, ingest/sync 시점 기준이라 **stale 가능**) / code-scan = **전수·실시간** WHAT 구조·exports·depends. **코드 정보의 차이는 "포함 여부"가 아니라 선별·신선도·깊이.** (→ D-11, 검증 D-12 `:6`)

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| — | (없음) | F-4는 신설 파일 없이 header-rules.md에 흡수 (TASK F-4 "신설 파일 없음") | TASK F-4 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M1 | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악 조건부 문구 제거 → "코드 작업 무조건 호출" + 코드/문서 판별 + 결과 3분기 연결. §Step 1.5에 "analyze는 code-scan @header 의존" 1줄. 변경이력 v1.4 | F-1·F-2 (→ D-2) |
| M2 | `opal/core/AGENT.md` | §code-scan 활용 규칙: brain↔code-scan 역할 분담 표 신설 + "scan.json 없으면 사용 생략"행 → F-3 자동 생성 교체 + 사용자 오버라이드 문구. 변경이력 v3.3 | F-2 (→ D-3) |
| M3 | `opal/core/references/pm/code-scan-management.md` | §생성 시점: "처음 사용하려 할 때" → "PM 첫 호출 시 부재면 인터럽트 없이 즉석 추론 생성" + 추론 소스 3종 + 생성 보고 1줄. 변경이력 신설 | F-3 (→ D-4) |
| M4 | `opal/core/references/harness/header-rules.md` | §code-scan 활용 가이드에 빈 결과 폴백 3분기 표 + STATE 자유 텍스트 기록 규약 흡수. §적용 조건 조건부 문구 정합. 변경이력 v1.1 | F-4 (→ D-5) |
| M5 | `opal/core/references/harness/pm-review-gate.md` | 표준 검토 항목 14번 신설 — 코드 변경 태스크 디스패치 컨텍스트의 code-scan 결과 인용 검증 (문서 N/A). 변경이력 v1.5 | F-5 (→ D-6) |
| M6 | `opal/core/references/opal-pm.md` | (조건부) §9 code-scan.json PM 관리 의무 요약에 "코드 작업 디스패치 전 무조건 호출" 1줄 정합. 변경이력 v1.2 | F-1 정합 (→ D-1) |
| M7 | `.opal/MEMORY.md` | 후속 후보 2건(Phase 2 워커 강제·OPAL @header 커버리지 확충) + 폐기 1건(.md @header 표준화=brain ingest 흡수) 기록 + 010 작업 히스토리 행 단계 갱신 | F-6 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| — | (없음) | — |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | F-3 scan.json 자동 생성 규약 (하위 규약 — F-1/F-2가 참조) | M3 | 중 |
| 2 | F-4 빈 결과 폴백 기준 (하위 규약 — F-1이 참조) | M4 | 중 |
| 3 | F-2 brain↔code-scan 역할 분담 + 오버라이드 (AGENT.md) | M2 | 중 |
| 4 | F-1 디스패치 전 무조건화 (dispatch-process — F-3·F-4 참조) | M1 | 상 |
| 5 | F-1 정합 (opal-pm.md §9) | M6 | 하 |
| 6 | F-2 analyze 의존 1줄 (dispatch-process §Step 1.5) | M1 (동일 파일, Step 4와 병합) | 하 |
| 7 | F-5 PM Gate 14번 항목 | M5 | 중 |
| 8 | F-6 메모리 후속 기록 | M7 | 하 |
| 9 | install 재배포 + 검증 | — | 하 |

> **의존 원리**: F-3(생성 규약)·F-4(폴백 기준)는 F-1(무조건화)이 "결과 3분기 연결" / "부재 시 자동 생성"으로 **참조하는 하위 규약**이므로 먼저 확정한다. M1(dispatch-process)은 F-1+F-2가 동일 파일을 수정하므로 **순차 병합**(Step 4+6).

### 핵심 설계

#### M1 — dispatch-process.md (F-1 + F-2 analyze 의존, 동일 파일 순차)

**(F-1) §code-scan 사전 범위 파악 전면 재작성** (현재 `:103-109` 조건부) (→ D-2:103-109):

- **제거 대상**: `"`.opal/code-scan.json`이 존재하는 프로젝트에서"`(:105) 진입 조건 + `"code-scan.json 없으면 일반 파일 탐색(Glob/Grep) 사용"`(:109) 회피 경로.
- **신설 구조**:
  1. **코드/문서 작업 판별 기준 1줄**: "변경·탐색 대상에 code-scan 지원 확장자(코드 파일) 또는 코드 구조 이해가 포함되면 **코드 작업**, 순수 .md 문서·기획·정책만이면 **문서 작업**." (AC ③)
  2. **무조건화 문구**: "**코드 변경·코드 탐색이 필요한 작업이면 디스패치 전 code-scan을 무조건 호출한다.**" 순수 문서 작업은 명시적 스킵 허용. (AC ①②)
  3. **부재 시**: "scan.json 부재면 code-scan-management.md §생성 시점에 따라 즉석 자동 생성 후 진행 (Glob/Grep 회피 금지)." (→ M3 / F-3 연결)
  4. **결과 3분기**: "결과 해석·폴백은 `harness/header-rules.md §code-scan 활용 가이드 §빈 결과 폴백`을 따른다." (→ M4 / F-4 연결, AC ④)
- [MUST] 016 회귀 금지: §Step 1.5 brain 순서 문구(`:131` "brain → code-scan") 불변 유지. (→ D-11)

**(F-2) §Step 1.5 brain에 analyze 의존 1줄 추가** (현재 `:131` 원칙 박스 인근) (→ D-2:131):

- 추가 문구: "brain `analyze`(init 동적 제안 입력)는 code-scan @header 정량 집계에 의존하므로, code-scan 보급률이 brain 지식 품질의 상한이다 (brain → code-scan 순서 유지)." (→ D-12 `:6` 검증, AC ③)

#### M2 — core/AGENT.md §code-scan 활용 규칙 (F-2)

(현재 `:176-189`) (→ D-3:176-189):

- **(1) 역할 분담 표 신설** (§code-scan 활용 규칙과 §opal-brain 활용 규칙 사이 또는 §code-scan 말미):

  | 축 | code-scan | opal-brain |
  |----|-----------|------------|
  | 코드 정보 범위 | **전수**(전 파일 @header) | **선별** 핵심 모듈만 |
  | 신선도 | **실시간**(호출 시점 스캔) | **stale 가능**(ingest/sync 시점 스냅샷) |
  | 깊이/성격 | WHAT — 구조·exports·depends | WHY/HOW — 설계 배경 + @header 스냅샷 |
  | 원천 | 파일 @header(SSOT) | code-scan @header에서 파생 |

  > 코드 정보의 차이는 "포함 여부"가 아니라 **선별·신선도·깊이**다. (→ D-11, 검증 D-12 `:6`)

- **(2) "scan.json 없으면 사용 생략"행 교체**: `:189` `"code-scan.json 없으면 code-scan 사용 생략 → Glob/Grep으로 탐색한다"` → "**code-scan.json 부재 시 PM이 즉석 자동 생성**(`code-scan-management.md §생성 시점`) 후 활용. 자동 생성으로도 빈 결과면 `header-rules.md §빈 결과 폴백`을 따른다." (→ M3·M4)
- **(3) 사용자 오버라이드 명문화**: "사용자가 'grep으로 해'·'직접 찾아' 등 특정 도구를 명시하면, code-scan 우선 원칙을 보류하고 지정 도구로 즉시 전환한다 (소유자 주도성 원칙 — D-9 §1)." (AC ②)
- [MUST] 016 회귀 금지: §opal-brain 활용 규칙(:191-221) W4(ingest 트리거)·W5(search 후보→선택)는 불변. 역할 분담 표는 두 규칙의 경계를 명시할 뿐 기존 규칙을 수정하지 않는다. (→ D-11)

#### M3 — code-scan-management.md §생성 시점 (F-3)

(현재 `:10-27`) (→ D-4:10-27):

- **(1) 즉석 생성 문구**: `:12` `"처음 사용하려 할 때 ... PM이 직접 생성한다"` → "**PM이 code-scan을 첫 호출하는 시점에 `.opal/code-scan.json`이 부재하면, 사용자 인터럽트 없이 즉석 추론으로 생성한 뒤 호출을 진행한다.**" (AC ①)
- **(2) 추론 소스 3종 규약**:
  - `scopes`: `docs/PROJECT.md §프로젝트 구성`의 요소·경로 표에서 추론 (부재 시 디렉토리 구조 1-depth 스캔). (→ D-13:85-90)
  - `extensions`: 프로젝트에 실재하는 코드 확장자 자동 감지 + **`.md` 기본 포함**(brain·문서 @header 자산화). (→ D-10 실증: MAMS extensions에 `.md`)
  - `exclude`: 최소 구조 기본값 + `backup`·`.pytest_cache`·`.next`·`.nuxt` 등 보강. (→ D-10 실증)
- **(3) 생성 보고 1줄 형식**: "`📂 code-scan.json 자동 생성: scopes={N}종 · extensions=[...] · exclude=[...]`" — 생성 직후 STATE 자유 텍스트 또는 응답에 1줄 보고. (AC ③)
- [MUST] 016 회귀 금지: brain `sync-header`/`analyze`가 `.opal/code-scan.json` 부재 시 `code_scan_json_missing`로 실패하므로(D-12 `:632-643`), 자동 생성은 brain 품질 회복에도 기여 (v2 진단 §5).

#### M4 — header-rules.md §code-scan 활용 가이드 (F-4)

(현재 `:52-74`) (→ D-5:52-74):

- **(1) 빈 결과 폴백 3분기 표 신설** (§적용 조건 앞 또는 활용 절차 뒤):

  | 분기 | 조건 | 대응 |
  |------|------|------|
  | ① 매칭 0건 | `search`/`exports` 결과 0건 | Glob/Grep **보강**(code-scan 결과 + 추가 탐색) |
  | ② 저커버리지 | `scan`/`domain`/`layer` @header 커버리지 30% 미만 | code-scan **+ Glob/Grep 동시** 활용 |
  | ③ 정상 | 그 외 | code-scan 결과만 |

- **(2) STATE 기록 규약**: "폴백(①②) 발동 시 STATE.md **자유 텍스트 영역**(블로커/다음 액션 — **현황판 표 행 아님, state-tool 비경유**)에 `code-scan 폴백: {사유}` 1줄을 기록한다." (AC ②)
  - [MUST] TASK §제약: "STATE.md 폴백 기록은 자유 텍스트 영역만 사용, 현황판 행 직접 편집 금지."
- **(3) §적용 조건 정합**(:74): 조건부 단정 문구를 "scan.json 부재 시 자동 생성(`code-scan-management.md`) 후 활용 — 미생성 직행 Glob/Grep 금지"로 정합. PM이 디스패치 전 Read 가능한 경로임을 명시. (AC ③)

#### M5 — pm-review-gate.md 표준 검토 항목 14번 (F-5)

(현행 13항목 — `:44-88`) (→ D-6):

- **신설 항목 14**: "**코드 변경 태스크의 디스패치 컨텍스트에 code-scan 결과(domain/layer/depends/exports)가 인용되었는가** — 코드 변경/탐색 태스크 한정. 순수 문서 작업은 **N/A**. 인용 부재 시 Fail → 재디스패치 1회." (AC ①②)
- 기존 13번(컨벤션 자동 진단)과 번호 충돌 없이 14번으로 추가. (AC ③)
- 트리거 조건: §8/§13과 동형으로 "changed_files / target에 code-scan 지원 확장자 포함" — 문서 전용이면 스킵.

#### M6 — opal-pm.md §9 정합 (F-1 정합)

(현재 `:112-118` §9 code-scan.json PM 관리 의무) (→ D-1:112-118):

- §9 요약에 1줄 추가: "**코드 변경·코드 탐색 작업의 디스패치 전 code-scan 호출은 무조건이며**(상세 `dispatch-process.md §code-scan 사전 범위 파악`), scan.json 부재 시 PM이 즉석 자동 생성한다(`code-scan-management.md §생성 시점`)."
- **doc_code_mismatch C-1**: TASK F-1은 "opal-pm.md **§3** 요약 정합"이라 했으나, 실제 §3(:53-59)은 dispatch-process로 위임하는 stub이라 code-scan 텍스트가 없다. code-scan 요약 앵커는 **§9**다. → §9에 정합한다 (코드 기준 우선 원칙).

#### M7 — .opal/MEMORY.md (F-6)

(현재 `:23-44`) (→ TASK F-6):

- **후속 후보 2건** (메모리 표 또는 작업 히스토리 비고에 task 카테고리로):
  - 후속 ①: "Phase 2 — 워커 자체 탐색 강제(code-scan 우선). **운영 데이터 축적 후 판단**."
  - 후속 ②: "OPAL 본 프로젝트 @header 커버리지 확충 — brain analyze 품질의 원료(현 2파일 수준, D-11 016 세션 확인)."
- **폐기 1건**: "Phase 3 .md @header 표준화 → **폐기**. 사유: 문서 요약·검색은 brain ingest가 흡수(016 W2). (010 v2 재정의)"
- 010 작업 히스토리 행(:39) 단계 `TASK` → 진행 단계로 갱신은 **PM/state-tool 영역** — 워커는 직접 편집하지 않음 (Step 8은 메모리 후속/폐기 기록만).

---

## 3. 실행 체크리스트

> 총 8개 Step | Phase 4개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2 | 병렬 | M3·M4 독립 파일 (하위 규약, 선행) |
> | 2 | 3, 5 | 병렬 | M2(AGENT.md)·M5(pm-review-gate.md) 독립 파일 |
> | 3 | 4 | 순차 | M1 — F-1+F-2 동일 파일, Phase1 규약(F-3·F-4) 참조 |
> | 4 | 6, 7 | 병렬 | M6(opal-pm.md)·M7(MEMORY.md) 독립 파일 |
> | 5 | 8 | 순차 | install 재배포 — 전 Step 의존 |

> agent 배정: 전부 .md 규약 문서 수정이므로 **opal-task-agent**(EXECUTE 공통/범용, standard). 코드·테스트 Step 없음(code-scan.js 무변경 제약).

### Step 1: F-3 scan.json 자동 생성 규약 신설
- [x] 완료
- **파일**: `opal/core/references/pm/code-scan-management.md`
- **작업 내용**: §생성 시점 재작성 — ① "처음 사용하려 할 때"→"PM 첫 호출 시 부재면 인터럽트 없이 즉석 추론 생성" ② 추론 소스 3종(scopes=PROJECT.md §프로젝트 구성 / extensions=실재 확장자+`.md` 기본 / exclude=기본값+보강) ③ 생성 보고 1줄 형식. M3 핵심 설계 참조. 변경이력 행 추가(KST + 010).
- **완료 기준**: AC ①②③ 충족 — 즉석 생성 문구·추론 소스 3종 규약·생성 보고 1줄 모두 존재. 변경이력 행 존재.
- **테스트**: 문서 Read하여 3개 AC 문구 grep 확인. brain `code_scan_json_missing`(D-12) 회복 근거 1줄 포함 확인.
- **의존**: 없음
- **agent**: opal-task-agent

### Step 2: F-4 빈 결과 폴백 기준 흡수
- [x] 완료
- **파일**: `opal/core/references/harness/header-rules.md`
- **작업 내용**: §code-scan 활용 가이드에 빈 결과 폴백 3분기 표(①매칭0건→보강 ②커버리지30%미만→동시 ③정상→결과만) + STATE **자유 텍스트** 기록 규약(현황판 행 아님 명시) + §적용 조건 조건부 문구 정합. M4 핵심 설계 참조. 변경이력 v1.1(KST + 010).
- **완료 기준**: AC ①②③ 충족 — 3분기 표·STATE 자유 텍스트 규약(행 편집 아님 명시)·PM Read 가능 경로 명시. 변경이력 행 존재.
- **테스트**: 3분기 표 존재 확인. "현황판 행 직접 편집 금지" 취지 문구 grep. state-tool 비경유 명시 확인.
- **의존**: 없음
- **agent**: opal-task-agent

### Step 3: F-2 brain↔code-scan 역할 분담 + 오버라이드 (AGENT.md)
- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: §code-scan 활용 규칙에 ① 역할 분담 표(전수/실시간/WHAT vs 선별/stale/WHY — "차이는 선별·신선도·깊이") ② "scan.json 없으면 생략"행→F-3 자동 생성 교체 ③ 사용자 오버라이드 문구. M2 핵심 설계 참조. §opal-brain 활용 규칙(W4/W5) **불변**. 변경이력 v3.3(KST + 010).
- **완료 기준**: AC ①②③ 충족 — 역할 분담 표·오버라이드 문구·자동 생성 교체 존재. W4/W5 원문 보존(diff로 brain 규칙 무변경 확인). 변경이력 행 존재.
- **테스트**: 역할 분담 표 4축 확인. 오버라이드("grep으로 해" 류) 문구 grep. §opal-brain 활용 규칙 :191-221 무변경 확인.
- **의존**: Step 1 (자동 생성 교체 문구가 M3 규약 참조)
- **agent**: opal-task-agent

### Step 4: F-1 디스패치 전 무조건화 + F-2 analyze 의존 (dispatch-process)
- [x] 완료
- **파일**: `opal/core/references/pm/dispatch-process.md`
- **작업 내용**: (F-1) §code-scan 사전 범위 파악 전면 재작성 — 조건부 문구 제거 + 코드/문서 판별 1줄 + 무조건 호출 + 부재 시 자동 생성(F-3 연결) + 결과 3분기(F-4 연결). (F-2) §Step 1.5에 "analyze는 code-scan @header 의존" 1줄. M1 핵심 설계 참조. §Step 1.5 brain 순서(:131) **불변**. 변경이력 v1.4(KST + 010).
- **완료 기준**: F-1 AC ①②③④ + F-2 AC ③ 충족 — 무조건 문구·조건부 제거·판별 기준·3분기 연결·analyze 의존 1줄 존재. "brain → code-scan" 순서 보존. 변경이력 행 존재.
- **테스트**: 조건부 문구(":105 .opal/code-scan.json이 존재하는 프로젝트에서") 제거 확인. 무조건/판별/3분기 grep. brain 순서 문구 무변경 확인. Step 1·2 규약 참조 경로 정합.
- **의존**: Step 1, Step 2
- **agent**: opal-task-agent

### Step 5: F-5 PM Gate 14번 검토 항목
- [x] 완료
- **파일**: `opal/core/references/harness/pm-review-gate.md`
- **작업 내용**: 표준 검토 항목 14번 신설 — "코드 변경 태스크 디스패치 컨텍스트에 code-scan 결과(domain/layer/depends/exports) 인용 검증, 문서 N/A". 현행 13번과 번호 충돌 없이 추가. M5 핵심 설계 참조. 변경이력 v1.5(KST + 010).
- **완료 기준**: AC ①②③ 충족 — 14번 항목 추가·코드/문서 트리거 조건 명시·기존 13번 번호 정합. 변경이력 행 존재.
- **테스트**: 14번 항목 존재 확인. "문서 작업 N/A" 명시 grep. 13번(컨벤션 자동 진단) 무변경·번호 정합 확인.
- **의존**: 없음 (단 Phase 배치상 Step 3과 병렬)
- **agent**: opal-task-agent

### Step 6: F-1 정합 (opal-pm.md §9)
- [x] 완료
- **파일**: `opal/core/references/opal-pm.md`
- **작업 내용**: §9 code-scan.json PM 관리 의무 요약에 "코드 작업 디스패치 전 무조건 호출 + 부재 시 즉석 자동 생성" 1줄 정합. **doc_code_mismatch C-1**: TASK가 지정한 §3은 stub이라 §9로 라우팅(보고 필수). M6 핵심 설계 참조. 변경이력 v1.2(KST + 010).
- **완료 기준**: §9에 무조건화 정합 1줄 + dispatch-process/code-scan-management 참조 경로 존재. 변경이력 행 존재. doc_code_mismatch C-1이 결과 반환에 기재됨.
- **테스트**: §9 정합 문구 grep. §3이 stub임을 재확인(코드 기준 우선).
- **의존**: Step 4 (dispatch-process 본문 확정 후 요약 정합)
- **agent**: opal-task-agent

### Step 7: F-6 메모리 후속 기록
- [x] 완료
- **파일**: `.opal/MEMORY.md`
- **작업 내용**: 후속 후보 2건(Phase 2 워커 강제=운영 데이터 후 / OPAL @header 커버리지 확충=brain analyze 원료) + 폐기 1건(.md @header 표준화=brain ingest 흡수, 사유 명시) 기록. 010 히스토리 행 단계 갱신은 PM/state-tool 영역이므로 **미수행**. M7 핵심 설계 참조.
- **완료 기준**: AC 충족 — 후속 2건 + 폐기 1건이 **사유와 함께** 기재. 현황판 행/state-tool 영역 미침범.
- **테스트**: 후속 2건·폐기 1건 문구 grep. 각 항목에 사유 동반 확인.
- **의존**: 없음 (Phase 배치상 Step 6과 병렬)
- **agent**: opal-task-agent

### Step 8: install 재배포 + 검증
- [x] 완료
- **파일**: — (배포 스크립트 실행)
- **작업 내용**: `./scripts/install-mac.sh` 실행하여 수정 소스(`opal/core/`)를 `~/.opal/`로 재배포. 배포본에서 변경이력 strip 확인. [MUST] `~/.opal/` 직접 편집 금지 — 소스→배포 경로만 사용.
- **완료 기준**: install 정상 종료. 배포본 5개 .md에 수정 내용 반영 + 변경이력 섹션 strip 확인. (`~/.opal/references/...`와 소스 본문 일치, 변경이력만 제거)
- **테스트**: 배포본 grep으로 신규 규약 문구 존재 + "## 변경이력" 부재 확인. `git status`로 `~/.opal/` 외부 직접 편집 0건 확인.
- **의존**: Step 1~7 전부
- **agent**: opal-task-agent

---

## 4. QA 체크리스트

### 기능 테스트
- [x] F-1: dispatch-process §code-scan 사전 범위 파악에 무조건 호출 문구 존재 + 조건부 문구 제거 + 코드/문서 판별 기준 + 결과 3분기 연결 (AC ①②③④ — 배포본 :107 grep 증거)
- [x] F-2: AGENT.md 역할 분담 표(전수/실시간/WHAT vs 선별/stale/WHY) + 오버라이드 문구 + dispatch-process analyze 의존 1줄 (AC ①②③ + §도입부 잔존 조건부는 PM Gate에서 발견·보정 후 재배포)
- [x] F-3: code-scan-management 즉석 생성 문구 + 추론 소스 3종 + 생성 보고 1줄 (AC ①②③ — :12 grep 증거)
- [x] F-4: header-rules 폴백 3분기 표 + STATE 자유 텍스트 기록(행 편집 아님) + PM Read 경로 (AC ①②③)
- [x] F-5: pm-review-gate 14번 항목 + 코드/문서 트리거 + 기존 번호 정합 (AC ①②③ — 배포본 :89-94 grep 증거)
- [x] F-6: MEMORY.md 후속 2건 + 폐기 1건 사유 동반 기재 (AC — memory/follow-up-code-scan-phase2.md)

### 일관성 테스트
- [x] 016 회귀 금지: AGENT.md §opal-brain 활용 규칙(W4/W5) 무변경(워커 diff + PM grep 재검증) + dispatch-process "brain → code-scan" 순서 보존(:134-135)
- [x] state-tool 정합: STATE 폴백 기록이 자유 텍스트 영역 한정, 현황판 행 직접 편집 0건 (3중 한정 명문화)
- [x] 변경 범위 한정: code-scan.js 무변경 + 워커 AGENT.md 6종 무변경 (git status 확인)
- [x] 5개 .md + opal-pm.md 변경이력 행 전부 추가 (KST + 010)
- [x] F-1/F-3/F-4 상호 참조 경로 정합 (무조건화→자동생성→폴백 체인 — Step 4가 실파일 섹션명 확인 후 인용)
- [x] 배포 경계: `~/.opal/` 직접 편집 0건, 소스→install 경로만 사용 (install 2회 — Step 8 + PM 보정 재배포)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명(scopes/extensions/exclude/domain/layer/depends/exports) 규칙 준수
- [x] kebab-case 파일/폴더 네이밍 준수 (신규 파일 memory/follow-up-code-scan-phase2.md — kebab-case)
- [x] 표·인용 포맷이 citation-rules.md 준수 (`[MUST]` 토큰·경로 백틱)

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | **doc_code_mismatch (C-1)** — TASK F-1이 지정한 "opal-pm.md §3"이 실제로는 dispatch-process 위임 stub이라 code-scan 텍스트 없음 | F-1 정합 대상 오인 시 잘못된 위치 수정 | §9(code-scan PM 관리)로 라우팅. 결과 반환·DONE에 mismatch 명시 (코드 기준 우선 — doc-code-mismatch 원칙) |
| R-2 | dispatch-process가 F-3·F-4 규약을 참조하므로, 선행 규약 문구가 흔들리면 참조 경로 깨짐 | 무조건화→자동생성→폴백 체인 단절 | Phase 1(Step 1·2)에서 규약 확정 후 Phase 3(Step 4) 진행. 참조 경로(섹션명)를 명시적으로 고정 |
| R-3 | AGENT.md 수정 시 §opal-brain 활용 규칙(W4/W5) 인접 편집으로 016 산출물 회귀 위험 | brain 규칙 훼손 → 016 회귀 | 역할 분담 표는 §code-scan 활용 규칙에만 신설, brain 규칙 본문 무편집. diff로 :191-221 보존 검증 |
| R-4 | STATE 폴백 기록 규약이 모호하면 워커가 현황판 행을 직접 편집할 위험 | state-tool 정합 위반 | M4에서 "자유 텍스트 영역(블로커/다음 액션), state-tool 비경유, 현황판 행 아님"을 명시적 3중 한정 |
| R-5 | 용어 불일치 — code-scan은 "scan/domain/layer/exports/depends", brain은 "search/analyze/ingest" | 폴백 3분기·역할 표에서 커맨드 혼동 | 각 도구 고유 커맨드를 표에서 분리 표기. F-4 폴백은 code-scan 커맨드만 대상 |
| R-6 | install 재배포 누락 시 `~/.opal/` 배포본과 소스 불일치 | 실사용 환경에 규약 미반영 | Step 8 필수 — 배포본 grep 검증 + git status로 직접 편집 0건 확인 |
| R-7 | F-3 extensions에 `.md` 기본 포함 시 대형 프로젝트에서 스캔 범위 과다 | 성능·노이즈 | 폐기된 ".md @header 표준화"와 구분 — `.md` 포함은 brain @header 자산화 목적의 **옵션 기본값**일 뿐, 전 .md @header 강제 아님 (F-6 폐기 기록과 정합) |

---

> **decision_required**: 없음. F-1 정합 위치(§3→§9)는 doc_code_mismatch로 코드 기준 우선 처리하므로 양자택일 아님. 다만 캡틴 검토 시 R-1(§9 라우팅)을 확인 권장.
