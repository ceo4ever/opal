# ANALYSIS: @header 워커 기입 필드 작성 기준 신설 + 이력 분리

> 작성일: 2026-09-06
> 입력: TASK.md
> 출력: ANALYSIS.md

## 확정 입력 판정
| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] 이력은 `@header`에 남기지 않는다 — git이 추적 가능하므로 자산 안에 중복해 두지 않는다. `note`로 옮기는 것도 아니다 | 해당없음(결정) | - |
| [결정] `description` 글자수 상한은 두지 않는다 | 해당없음(결정) | - |
| [결정] 도구 검증은 태스크번호 패턴 감지로 설계한다 | 해당없음(결정) | - |
| [결정] `header-standard.md` §4 `exports` 가이드 형식을 준용해 4필드 가이드를 신설한다 | 해당없음(결정) | - |
| [사실] `note` 필드는 71건 전건 0자다 — 규정상 자리가 있으나 미사용 | **수정필요** | 프로젝트 설정 스코프(`framework`/`console-fe`/`console-be`, `.opal/code-scan.json:3-7`) 전수(109파일) 재측정 결과 `note` 필드가 **존재하는 파일 2건뿐**(`opal/tools/code-scan/code-map-hook.js`, `opal/tools/code-scan/code-scan.js`)이며, 그 2건은 **전건 비어있지 않다**(각각 700자·1400자대 이력성 텍스트, E1 실행 관측: `code-scan scan --json` 전수 스캔). "71건 전건 0자"는 TASK가 참조한 표본(§배경 분석 (6) 12건과 다른 별도 코퍼스, 아마 Python 8파일 한정)의 수치로 추정되나 그 표본 정의가 산출물에 재확인 가능한 형태로 남아있지 않다 — 전 프로젝트 스코프로 일반화하면 성립하지 않는다. 아래 Q7 상세 참조 |
| [사실] `opal-doc-standard.md:28`이 "변경 이력은 git이 갖는다"를 `.md` 실행 지시문에 대해 이미 확립했다 | 유효(대조 확인) | `opal/core/references/opal-doc-standard.md:28`: "실행 지시문은 코드처럼 제자리에서 갱신되고 **변경 이력은 git이 갖는다**. 다만 **버전 번호**는 문서 안에 남는다" — 원문 일치 확인 |
| [사실] 상관 실측상 `description` 증가 동인은 코드량(+0.39)이 아니라 이력 누적(+0.76)이다 | 유효(대조 확인) | TASK.md §배경 분석 (4) 표 수치는 대화 세션 내 산출로 본 ANALYSIS 단계에서 재계산 대상 밖(상류 확인 완료로 간주) — 단, 12건 표본에 대한 3-digit 태스크번호 실측(§7 지정 분석 질문 Q2)이 방향성을 재확인함(전건 unique 4개 이상 검출) |

> TASK.md에 `[사실]` 3항목이 있고(`TASK.md:87-89`) 그중 1건(`note` 71건 0자)이 전체 스코프 재측정에서 어긋났다 — §7 Q7에서 소유자 보고 사항으로 병기.

## 0. 참조 문서
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | @header 표준 | `opal/core/references/header-standard.md` | §2 필드 정의·§4 exports 가이드·§7 2소스 표현 — R-1·R-2 개정 대상 원문 |
| D-2 | 설계 | EXECUTE @header 규칙 | `opal/core/references/harness/header-rules.md` | §8 워커 권한 경계·갱신 시점 — R-2 개정 대상 원문 |
| D-3 | 설계 | 문서 표준 | `opal/core/references/opal-doc-standard.md` | `:28` "변경 이력은 git이 갖는다" — R-2 근거 원문 |
| D-4 | 소스 | code-scan 도구 | `opal/tools/code-scan/code-scan.js` | R-3 신설 대상(`cmdValidate`, `:3155`), `VERSION` 상수(`:38`) |
| D-5 | 소스 | code-scan 테스트 | `opal/tools/code-scan/tests/` 9파일(`test-discover.js`/`test-feature.js`/`test-header-source.js`/`test-hook.js`/`test-regression.js`/`test-resolve-header.js`/`test-scaffold.js`/`test-scope-filter.js`/`test-shard-policy.js`, `test-shard.js` 별도) | R-3·R-5 회귀 기준 실측(344 passed) |
| D-6 | 산출물 | 태스크 106 | `tasks/106-260904-opd-코드맵-스킬신설-하네스개정/DONE.md` · `ADD_DONE-1.md` | §8 이월 1·2번이 이 태스크의 발원 |
| D-7 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | §@header 규칙(`:218`)이 R-2와 충돌 — Q1 판정 대상 |
| D-8 | 규칙 | Citation Rules | `opal/core/references/harness/citation-rules.md` | 인용 포맷·근거 등급(E1~E5) 준수 |
| D-9 | 규칙 | 분석 코어 SSOT | `opal/core/references/harness/analysis-core.md` | §1 선조회 3단·§5 관련 파일 맵 6영역(프레임워크 축)·§7 품질 체크리스트 |
| D-10 | 설정 | 프로젝트 code-scan 설정 | `.opal/code-scan.json` | 스캔 스코프(`framework`/`console-fe`/`console-be`) 정의 — Q7 전수 재측정의 스코프 근거 |

> 선조회 3단 수행 결과: 1단 brain — `~/.opal/tools/brain-tool/run.sh search "header description 이력"` 0건(과거 관련 브레인 페이지 부재, PM 선별 6페이지는 디스패치 프롬프트에 이미 인용되어 그대로 소비함). 2단 code-scan — `scan`/`search`로 대상 파일(`header-standard.md`·`header-rules.md`·`code-scan.js`) 및 전수 스캔(109파일) 수행, 아래 §1.1·Q2·Q7에 반영. 3단 docs 레지스트리 — `docs/PROJECT.md` 문서 표 조회 완료(D-7 CONVENTIONS.md 발견). 3단-B(과거 태스크 산출물)는 T3(TASK.md가 태스크 106을 인용) 트리거 충족으로 수행 — `tasks/106-*/DONE.md`·`ADD_DONE-1.md`는 디스패치 프롬프트가 이미 지정해 그대로 소비.

## 1. 기존 코드 분석

### 1.1 관련 파일 목록
| 영역 | 경로 | 역할 | 변경 유형 | 근거(줄번호) |
|------|------|------|------|-------------|
| 참조 문서 | `opal/core/references/header-standard.md` | @header 필드 정의·언어별 예시·exports 가이드·2소스 표현 SSOT | 수정 | `:11-23`(§2 필드 정의), `:133-159`(§4 exports 가이드) |
| 가이드 | `opal/core/references/harness/header-rules.md` | EXECUTE 단계 @header 작성 규칙 — 기록 위치 판정·갱신 시점·워커 권한 경계 | 수정 | `:66-76`(워커 권한 경계 표), `:112-123`(파일 수정 시 갱신 대상 필드 표) |
| 문서 | `docs/CONVENTIONS.md` | 프로젝트 컨벤션 — §@header 규칙에 R-2와 충돌하는 "헤더 내 변경이력 라인" 문구 존재(Q1 판정 대상) | 수정(Q1 결론에 따름) | `:218`: "변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다." |
| 도구 | `opal/tools/code-scan/code-scan.js` | `cmdValidate` — @header 검증 로직(violations/counts/blockingViolations 계산) | 수정 | `:3155`(함수 시작), `:3434-3451`(counts·비차단 필터 계산), `:38`(`VERSION` 상수) |
| 도구 테스트 | `opal/tools/code-scan/tests/test-shard.js` | `VERSION` 값 단언(`code-scan v1.6.0` 출력 고정) | 무변경(회귀 기준) | `:696-701` |
| 도구 테스트 | `opal/tools/code-scan/tests/test-shard-policy.js` | `VERSION` 값 단언(`'1.6.0'`) | 무변경(회귀 기준) | `:1519-1521` |
| 도구 테스트 | `opal/tools/code-scan/tests/` 9파일(합 344 테스트) | R-3 신설분의 회귀 기준 | 무변경(회귀 기준, 신설 테스트는 별도 파일 또는 기존 파일 확장 가능) | `-` |
| 이력 정리 대상 | `opal/tools/state-tool/state_tool.py` | state-tool CLI 본체 | 수정(`description` 정리) | `@header description` 11791자, 태스크번호 unique 26개 |
| 이력 정리 대상 | `opal/tools/state-tool/tests/test_state_tool.py` | state-tool 테스트 | 수정(`description` 정리) | `@header description` 7049자, unique 21개 |
| 이력 정리 대상 | `dashboard/backend/tests/test_routers.py` | 콘솔 BE 라우터 테스트 | 수정(`description` 정리) | `@header description` 2033자, unique 21개 |
| 이력 정리 대상 | `opal/tools/brain-tool/brain_tool.py` | brain-tool CLI 본체 | 수정(`description` 정리) | `@header description` 1213자, unique 4개 |
| 이력 정리 대상 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | todo_mirror_hook 테스트 | 수정(`description` 정리) | `@header description` 948자, unique 7개 |
| 이력 정리 대상 | `opal/tools/state-tool/todo_mirror_hook.py` | todo 미러 훅 | 수정(`description` 정리) | `@header description` 924자, unique 5개 |
| 이력 정리 대상 | `dashboard/backend/tests/test_stats.py` | 콘솔 BE 통계 테스트 | 수정(`description` 정리) | `@header description` 877자, unique 8개 |
| 이력 정리 대상 | `opal/tools/test-tool/lib/scenario.py` | test-tool 시나리오 모듈 | 수정(`description` 정리) | `@header description` 828자, unique 5개 |
| 이력 정리 대상 | `opal/tools/brain-tool/tests/test_brain_tool.py` | brain-tool 테스트 | 수정(`description` 정리) | `@header description` 553자, unique 5개 |
| 이력 정리 대상 | `opal/tools/memory-tool/tests/test_memory_tool.py` | memory-tool 테스트 | 수정(`description` 정리) | `@header description` 473자, unique 15개 |
| 이력 정리 대상 | `opal/tools/opal-agent/tests/test_opal_agent.py` | opal-agent 테스트 | 수정(`description` 정리) | `@header description` 430자, unique 6개 |
| 이력 정리 대상 | `opal/tools/improve-tool/tests/test_improve_tool.py` | improve-tool 테스트 | 수정(`description` 정리) | `@header description` 179자, unique 6개 |

> 영역 라벨: 이 태스크는 코드 실행이 아닌 프레임워크 문서·도구 개정이므로 `analysis-core.md` §5 "프레임워크 문서·스킬 태스크 축"(스킬/가이드/오케스트레이터/에이전트/문서/환경/배치)을 따르되, 이력 정리 대상 12건은 원 소속 도메인이 섞여 있어(state-tool/brain-tool/test-tool/console-BE 등) 개별 파일 단위로 "이력 정리 대상" 라벨을 부여했다(6축 밖 확장 — PLAN 단계에서 재조정 가능).

### 1.2 아키텍처 패턴

- `@header`는 JSDoc/docstring 내부에 JSON 객체로 인라인 기재되며(`header-standard.md` §3), `code-scan.js`의 `extractHeader()`/`resolveHeader()`가 정규식 기반으로 파싱한다.
- `cmdValidate`의 위반 판정은 **동일 `violations` 배열**에 `code` 필드로 종류를 구분해 push하고, 마지막에 `counts`(종류별 집계)와 `blockingViolations`(차단 여부 판정용 필터)를 파생시키는 단일 패턴을 쓴다(`code-scan.js:3434-3451`). 비차단 신호(`uncovered:pre_existing`, `manifest_oversize`)는 **새 채널을 만들지 않고** 이 필터에서 제외하는 방식으로 구현되어 있다(`code-scan.js:3447-3450`: "'uncovered:pre_existing'과 'manifest_oversize'는 비차단(U-2) — 나머지는 차단 불변.").
- 참조 문서(`header-standard.md`)와 실행 규칙(`header-rules.md`)은 역할이 분리되어 있다 — 전자는 필드/포맷 SSOT, 후자는 EXECUTE 단계 작성 절차·갱신 시점·권한 경계를 규정한다. 두 문서가 서로 다른 말을 하면 안 된다는 R-2 AC(d)는 이 기존 역할 분리 패턴과 정합한다.

### 1.3 의존성 맵

- `header-standard.md` ← `header-rules.md`(§파일 생성/수정 시 "포맷 표준: 참조" 인용), `docs/CONVENTIONS.md`(§@header 규칙 "근거" 열에 두 문서 인용).
- `code-scan.js`(`cmdValidate`) → `violations`/`counts`/`headerSource` 등 JSON 필드를 CLOSE 게이트(`state-tool`/PM)가 소비 — 스키마 변경 시 소비 측 영향 확인 필요(R-3는 필드 추가만 하고 기존 필드를 변경하지 않으므로 하위 호환).
- 12개 정리 대상 파일은 서로 독립(같은 프로젝트의 서로 다른 도구/테스트 파일) — 상호 의존 없음, 각 파일의 `exports`/`module`/`layer`/`domain`은 이번 태스크의 변경 범위 밖(TASK.md §제약 ②).

### 1.4 테스트 현황

- `opal/tools/code-scan/tests/` — 9개 파일 합계 **344 passed / 0 failed**(E1 실행 관측, 스코프: `node --test tests/*.js`, 실행 시각 본 ANALYSIS 작성 중). TASK.md가 예정한 344 수치와 **정확히 일치**.
- `opal/tools/state-tool/` — `python3 -m pytest tests/ -q` 결과 **400 passed, 3 skipped, 98 subtests passed**(E1 실행 관측, 스코프: `tests/` 디렉토리 전체). TASK.md가 예정한 383과 **불일치** — §7 Q8 상세 참조.
- 정리 대상 12파일 중 8개 자체가 테스트 파일이다 — `description` 정리가 테스트 내용(assert 로직)에는 영향을 주지 않고 `@header` JSON 블록만 건드리므로, 정리 전/후 파일 자체의 테스트 통과 여부는 영향받지 않아야 한다(AC(d) JSON 파싱 정상 여부만 R-4 책임).

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 순수 내부 문서·도구 개정 태스크, 외부 라이브러리/API 조사 대상 없음.

## 3. 영향 범위

### 3.1 직접 영향

- `header-standard.md`(§2·§4 신규 서술 추가, §4 exports 원문 무변경), `header-rules.md`(이력 비기재 원칙 명문화 추가).
- `code-scan.js`의 `cmdValidate` 내부 — 태스크번호 패턴 감지 로직 추가(신규 `code`/`sub` 값 + `counts` 필드 1개 추가, 기존 필드 무변경).
- 정리 대상 12파일의 `@header.description` 필드 값(파일 본문 로직 무변경).
- (Q1 결론에 따라) `docs/CONVENTIONS.md` §@header 규칙 5번째 불릿 문구.

### 3.2 간접 영향

- `code-scan validate` JSON 출력을 소비하는 PM Gate(`header-rules.md` §갱신 시점 (b)(d))는 `counts`에 필드가 추가되어도 기존 판정 로직(exit code, `ok` 불리언)에 영향받지 않는다 — 신규 필드는 additive.
- 12파일 정리로 `description` 총량이 27,298자 감소하면 `code-scan scan`/`search`의 출력 바이트가 줄어든다(창문 재포화 완화 효과, 태스크 106 동기와 직결).
- brain(`ingest-scan`)이 이 12파일의 `description`을 이미 시드했다면 다음 ingest 시 스냅샷이 갱신된다(비차단, brain은 파생물).

### 3.3 영향 범위 요약
- [ ] DB 스키마 변경
- [ ] API 인터페이스 변경
- [x] 설정/환경변수 변경 — 해당 없음(단, `code-scan.js` 로직 변경이 `.opal/code-scan.json` 신규 키를 요구하지 않는지 PLAN에서 확정 필요. 현재 조사로는 신규 설정 키 불필요, 임계값은 상수 하드코딩 또는 기존 `shardPolicy`류 3단 우선순위 재사용 후보)
- [ ] 빌드/배포 파이프라인 변경

## 4. 핵심 발견 사항

1. **비차단 경고의 기존 구현 패턴이 이미 코드베이스에 존재한다** — `manifest_oversize`가 `violations` 배열에 동일하게 push되면서도 `blockingViolations` 필터(`code-scan.js:3447-3450`)에서 제외되어 `ok`에 영향을 주지 않는 방식으로 이미 구현돼 있다. R-3는 이 패턴을 그대로 재사용(새 `code` 값 + 동일 필터 제외 + `counts` 필드 추가)하면 되고, AC(b)가 요구하는 "violations가 아닌 별도 채널"은 이미 코드에 있는 "같은 배열, 다른 code, 필터에서 제외"라는 **기존 관용구**로 충족 가능하다(신규 채널 발명 불필요).
2. **CONVENTIONS.md가 R-2와 직접 충돌한다** — `docs/CONVENTIONS.md:218` "변경이력은 ... 헤더 내 변경이력 라인으로 갱신한다"는 TASK.md R-2("이력은 @header에 남기지 않는다")와 정면으로 반대되는 문장이며, 이 태스크의 개정 대상 목록(D-1·D-2)에는 없다. 이 문서는 "개발 작업 시 항상" 참조되는 [MUST] 등재 문서(`docs/PROJECT.md:226`)이므로, 미개정 상태로 이번 태스크가 닫히면 다음 태스크의 워커가 CONVENTIONS.md를 읽고 다시 헤더에 이력을 쌓기 시작할 구조적 위험이 있다.
3. **`note`·`feature` 필드는 "미사용"이 아니라 "존재 자체가 희소"하다** — TASK.md가 인용한 "71건 전건 0자"는 전 프로젝트 스코프(109파일, `.opal/code-scan.json` 3스코프) 재측정과 불일치한다. `note`는 109파일 중 **2건에만 존재**하고 그 2건은 이력성 텍스트로 채워져 있다(오히려 이번 R-2가 막으려는 패턴이 `note`에서 선제적으로 발생 중). `feature`는 109파일 중 **0건**(필드 자체가 아예 없음) — "채움률 0%"가 아니라 "필드 선언 자체가 0%"라는 더 강한 사실이다.
4. **`VERSION` 상수는 이미 083에서 상향된 이력이 있고 현재 `1.6.0`이며, 이번 태스크가 `cmdValidate` 로직만 확장(신규 기능 추가)하고 기존 필드 스키마를 변경하지 않는다면 상향 불필요**로 잠정 판단된다 — `header-rules.md` v1.9(106) 사례가 선례다: 106은 갱신 시점 표를 3단→4단으로 확장했지만 `VERSION` 상수(`code-scan.js:38`) 자체는 그 태스크에서 건드리지 않았다(083→106 사이 버전 변경 이력 없음, `test-shard.js:81` 주석: "S-22 `shardPolicy` 정규식 1건 추가 + 기대 버전 v1.5.0 → v1.6.0 이전" — 이는 082→083 전환 시점 얘기이며 106은 미해당).
5. **12건 정리 대상은 표본적으로 이력 소실 위험이 낮다** — 3파일 표본(`state_tool.py`, `brain_tool.py`, `test_improve_tool.py`) 각각의 `description`에 등장하는 태스크번호가 `git log --oneline --all -- <파일>`에서 전건 실재 확인됨(034/070/027/053/071/078). git 로그가 이미 이력의 실제 소재이므로 "제거해도 이력이 남는다"는 R-4 전제가 최소 표본에서는 성립한다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-1 | `docs/CONVENTIONS.md`가 개정 대상에서 빠지면 R-2 원칙이 프로젝트 전역에 관철되지 않고, 다음 태스크에서 재발할 구조적 위험이 있다 | 높음 | `docs/CONVENTIONS.md:218` |
| R-2 | `state-tool` 테스트 회귀 기준(383)이 실측(400 passed/3 skipped)과 불일치 — R-5 AC(b) "383 passed / 0 failed"를 문자 그대로 적용하면 PLAN/EXECUTE 단계에서 오판(회귀로 오인) 위험 | 중간 | 본 ANALYSIS §1.4 E1 실행 관측(`opal/tools/state-tool` `pytest tests/ -q`) |
| R-3 | 태스크번호 패턴(정규식 후보 A, unique 3-digit ≥3)을 109파일 전수 재측정한 결과 30건이 걸리며, TASK.md 12건 밖 18건 중 9건은 `F-00X`/`TS-0XX`/HTTP상태코드/IP옥텟발 오탐, 6건은 R-2가 막으려는 패턴이 이미 실재하는 진성 위반, 3건은 판정이 갈리는 경계다 — 정규식은 F-code/TS-code/HTTP/IP 배제 없이는 오탐·과소탐 양쪽에서 신뢰할 수 없다 | 중간 | 본 ANALYSIS §7 Q2 전수 실측(30건 표·18건 분류표) |
| R-4 | 신규 설정 키(임계값 등)를 `.opal/code-scan.json`에 추가할지 상수로 고정할지 미정 — PLAN 결정 필요 | 낮음 | 본 ANALYSIS §3.3 |
| R-5 | TASK.md §범위 ④(12건 정리)와 §완료기준(태스크번호 3개 이상 0건)이 서로 다른 집합을 가리킨다 — 완료기준을 문자대로 적용하면 정리 대상이 (정규식 후보 A 기준) 30건이 되어 §범위 ④의 12건과 충돌한다. 어떤 임계값(3~9)을 적용해도 12건과 정확히 일치하는 값이 없어(본 ANALYSIS §7 Q2 임계값 표) 이 불일치는 정규식 미세조정만으로 해소되지 않고 소유자의 범위 확정이 필요하다 | 높음 | TASK.md §범위 ④, TASK.md §완료기준, 본 ANALYSIS §7 Q2 |

## 6. 기술 컨텍스트

### 6.1 프로젝트 SSOT
전체 기술 스택은 `docs/PROJECT.md`를 참조한다. 이 섹션은 재기재하지 않는다.

### 6.2 이번 태스크 델타
변경 없음(SSOT 그대로) — 신규 라이브러리·버전 변경 없음. Markdown 문서 2건 + Node.js 도구 1건(`code-scan.js` v1.6.0 기존 확장) + Python 파일 8건 + TS/Python 콘솔 파일 2건의 `description` 필드만 수정.

### 6.3 추천 스킬
| 스킬 | 용도 |
|------|------|
| 해당 없음 | 프레임워크 내부 문서·도구 개정으로 외부 스킬 불필요 |

### 6.4 추천 MCP
| MCP | 용도 |
|-----|------|
| 해당 없음 | 외부 라이브러리 조사 불필요 |

## 7. 지정 분석 질문 Q1~Q8 답변

- **Q1** (CONVENTIONS.md 편입 여부): **편입 권고**. `docs/CONVENTIONS.md:218` "변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다"는 R-2("이력은 @header에 남기지 않는다")와 문자 그대로 충돌한다(§4 핵심발견 2). 이 문서는 `docs/PROJECT.md:226`이 "개발 작업 시 항상" 참조로 등재한 [MUST] 문서이므로, 미수정 상태로 두면 다음 태스크 워커가 이 문구를 근거로 다시 헤더에 이력을 쌓기 시작할 수 있다(재발 경로가 이미 문서에 열려 있음). 편입 규모는 **1개 불릿 문구 정정**(별건 태스크로 분리할 만큼 크지 않음) 수준으로 국한된다 — "헤더 내 변경이력 라인으로 갱신한다" 어구만 제거하고 "코드 `@header`의 이력은 git이 갖는다(R-2 원칙 인용)"로 교체하는 정도. 별건 분리보다 **본 태스크 R-2에 AC 추가**를 권고한다: R-2 AC(e) 신설 — "`docs/CONVENTIONS.md` §@header 규칙의 「헤더 내 변경이력 라인으로 갱신한다」 문구가 제거되고 R-2 원칙(git이 이력을 갖는다)과 정합하는 문구로 교체된다." 근거: `docs/CONVENTIONS.md:218`, `opal/core/references/opal-doc-standard.md:28`, `opal/core/references/opal-doc-standard.md:53`("§7 변경이력 테이블은 산출물 문서 계열에 적용한다. 실행 지시문 계열의 변경이력 일괄 정리는 별건 태스크로 예정되어 있다" — 이 문장은 **스킬/에이전트/참조 문서 자신의 "## 변경이력" 표** 정리를 가리키는 것으로, 코드 `@header` 내부 이력 문제와는 별개 사안이다. 따라서 이 문장이 CONVENTIONS.md 편입을 막는 근거가 되지 않는다).
- **Q2** (태스크번호 패턴 임계값 3) — **[정정, PM Fail 반영]** 최초 실측은 대조군 1개(`test_brain.py`)만으로 "오탐 0건"을 선언했으나, PM이 프로젝트 3스코프 전수(109파일, `.opal/code-scan.json:3-7`)를 정규식 후보 A `(?<![\d.])(\d{3})(?![\d])`(주의: 최초 실측이 썼던 `\b(\d{3})\b` 버전과 달리 **단어 경계 `\b`가 없다** — `T060`·`TS-070`처럼 문자 바로 뒤 3자리도 매칭 대상이 되어 unique count가 최초 실측보다 커진다)로 재측정한 결과, `description` 내 unique 3-digit 토큰 수 **≥3인 파일이 30건**이다(E1, `code-scan scan --json` 전수 + 파일별 재확인). TASK.md §배경 분석 (6)의 12건은 이 30건의 **부분집합**이며, 12건 밖에 **18건이 추가로 임계값 3에 함께 걸린다**. "12건이 걸린다"는 맞지만 "임계값 3에서 12건**만** 걸린다"는 틀렸다 — 이 차이를 이전 실측에서 확인하지 않았다.

  30건 unique count 분포(내림차순, TASK 12건은 ✔ 표시):
  | unique | 파일 | TASK 12건 |
  |---|---|---|
  | 26 | `opal/tools/state-tool/state_tool.py` | ✔ |
  | 23 | `dashboard/backend/tests/test_routers.py` | ✔ |
  | 21 | `opal/tools/state-tool/tests/test_state_tool.py` | ✔ |
  | 15 | `opal/tools/memory-tool/tests/test_memory_tool.py` | ✔ |
  | 9 | `dashboard/backend/tests/test_stats.py` | ✔ |
  | 9 | `opal/tools/code-scan/tests/test-shard-policy.js` | — |
  | 7 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | ✔ |
  | 6 | `opal/tools/opal-agent/tests/test_opal_agent.py` | ✔ |
  | 6 | `opal/tools/improve-tool/tests/test_improve_tool.py` | ✔ |
  | 5 | `opal/tools/state-tool/todo_mirror_hook.py` | ✔ |
  | 5 | `opal/tools/test-tool/lib/scenario.py` | ✔ |
  | 5 | `opal/tools/brain-tool/tests/test_brain_tool.py` | ✔ |
  | 5 | `opal/tools/code-scan/tests/test-regression.js` | — |
  | 4 | `opal/tools/brain-tool/brain_tool.py` | ✔ |
  | 4 | `opal/tools/code-scan/tests/test-feature.js` | — |
  | 4 | `opal/tools/code-scan/tests/test-validate.js` | — |
  | 4 | `opal/tools/code-scan/tests/test-target.js` | — |
  | 3 | `dashboard/backend/adapters/brain_session.py` | — |
  | 3 | `dashboard/backend/models.py` | — |
  | 3 | `dashboard/backend/config.py` | — |
  | 3 | `dashboard/backend/tests/test_config.py` | — |
  | 3 | `dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` | — |
  | 3 | `dashboard/backend/main.py` | — |
  | 3 | `opal/tools/code-scan/code-map-hook.js` | — |
  | 3 | `opal/tools/code-scan/tests/test-hook.js` | — |
  | 3 | `opal/tools/code-scan/tests/test-scope-filter.js` | — |
  | 3 | `opal/tools/code-scan/tests/test-resolve-header.js` | — |
  | 3 | `opal/tools/code-scan/tests/test-discover.js` | — |
  | 3 | `opal/tools/code-scan/tests/test-scaffold.js` | — |
  | 3 | `opal/tools/improve-tool/fw-inbox-README.md` | — |

  **임계값을 올렸을 때 탐지 집합이 어떻게 줄어드는지**(위 표에서 직접 도출, 30건 기준 누적 카운트):
  | 임계값(unique ≥) | 탐지 파일 수 | TASK 12건과 일치? |
  |---|---|---|
  | 3 | 30 | 아니오(18건 초과 포함) |
  | 4 | 17 | 아니오(TASK 12건 전부 포함 + `test-shard-policy.js`·`test-regression.js`·`test-feature.js`·`test-validate.js`·`test-target.js` 5건 초과 포함) |
  | 5 | 13 | 아니오(TASK 12건 중 `brain_tool.py`(4) 탈락 + `test-shard-policy.js`·`test-regression.js` 2건 초과 포함) |
  | 6 | 9 | 아니오(TASK 12건 중 4건 탈락, 초과 포함 1건(`test-shard-policy.js`) 잔존) |
  | 7 | 7 | 아니오 |
  | 9 | 6 | 아니오 |

  **어떤 임계값에서도(3~9 전 구간) TASK.md의 12건과 정확히 일치하는 값은 없다** — 임계값을 올려도 TASK 12건 자체가 먼저 탈락하기 시작하고(예: 5에서 `brain_tool.py` 탈락), 반대로 낮추면 12건 밖 파일이 계속 섞여 들어온다. 두 집합은 애초에 다른 기준(TASK.md 12건은 PM이 수동 선별한 "이력 정리 대상" 목록, 30건은 정규식 임계값 3-digit unique count)으로 만들어졌으므로 억지로 일치시킬 수 없다 — 이 사실을 그대로 기록한다.

  **12건 밖 18건 분류**(각 파일 `description` 원문 직접 확인, E1):
  | 파일 | unique(토큰) | 분류 | 근거 |
  |---|---|---|---|
  | `opal/tools/code-scan/tests/test-shard-policy.js` | 9 (`001,002,003,004,005,006,011,012,083`) | 오탐 | `001~012`는 전부 `F-00X` 기능번호(예: "F-001", "F-011")이며 태스크번호는 `083` 1건뿐(단발 출처 인용, 이력 누적 아님) |
  | `opal/tools/code-scan/tests/test-regression.js` | 5 (`005,006,007,070,080`) | 오탐 | `005~007`은 `F-00X`, `070`은 `TS-070`(시나리오 id) — 태스크번호는 `080` 1건뿐 |
  | `opal/tools/code-scan/tests/test-feature.js` | 4 (`001,008,077,080`) | 경계 | `001,008`은 `F-00X`이나 `077`·`080` **둘 다 실제 태스크번호**("077 자산 유지 + 080 신 계약 정합") — 이전 태스크 077에서 만든 동작을 080이 이어받는다는 서술로, 단일 인용인지 이력 서술인지 판정이 갈림 |
  | `opal/tools/code-scan/tests/test-validate.js` | 4 (`005,009,077,080`) | 경계 | 위와 동일 패턴("077 위반 검출 ... 회귀" + "태스크 080") — 077/080 두 태스크 병기 |
  | `opal/tools/code-scan/tests/test-target.js` | 4 (`003,004,008,080`) | 오탐 | `003,004,008`은 `F-00X`, 태스크번호는 `080` 1건뿐 |
  | `dashboard/backend/adapters/brain_session.py` | 3 (`003,060,063`) | 진성 | `003`은 `F-003`이나 `[T060 F-2/F-4, T063 F-003 need-기반 충전]`처럼 `T060`·`T063` 두 개의 서로 다른 태스크가 붙은 기능 서술 단락이 본문에 누적돼 있다 — R-2가 겨냥하는 패턴 |
  | `dashboard/backend/models.py` | 3 (`061,103,400`) | 진성 | `400`은 HTTP 상태코드(`session_id 필수·빈값→400`)이나, `[T061] ...`·`[T103] ...`·`[T103/R-16] ...`·`[T103/R-20] ...` 4개 단락이 태스크 태그를 달고 순차 누적돼 있다 |
  | `dashboard/backend/config.py` | 3 (`060,061,103`) | 진성 | `[T061 F-1] save_config ...`·`[T103 R-21] load_quiet_hours ...` 등 태스크 태그 단락이 순차 누적 |
  | `dashboard/backend/tests/test_config.py` | 3 (`060,061,103`) | 진성 | `(T060 F-1, RED)`·`[T061] ...`·`[T103 R-21] ...` 순차 누적 |
  | `dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` | 3 (`103,142,143`) | 경계 | `103`은 `[T103] ...` 진성 태스크 태그이나 `142,143`은 `TS-142`·`TS-143`(시나리오 id) — 진성 1 + 오탐 2 혼재 |
  | `dashboard/backend/main.py` | 3 (`060,061,127`) | 진성 | `127`은 IP 주소(`127.0.0.1:7823`)이나 `[T060 F-3] lifespan ...`·`[T061 Step4] config 라우터 등록 ...` 두 태스크 태그 단락이 순차 누적 |
  | `opal/tools/code-scan/code-map-hook.js` | 3 (`005,077,080`) | 진성 | `005`는 `F-005`이나 본문이 명시적으로 "TASK 077 / TASK 080 F-005"로 **두 태스크번호를 병기** — 077에서 만든 게이트를 080이 확장했다는 이력 서술 |
  | `opal/tools/code-scan/tests/test-hook.js` | 3 (`002,005,080`) | 오탐 | `002,005`는 `F-00X`, 태스크번호는 `080` 1건뿐 |
  | `opal/tools/code-scan/tests/test-scope-filter.js` | 3 (`002,003,080`) | 오탐 | `002,003`은 `F-00X`, 태스크번호는 `080` 1건뿐 |
  | `opal/tools/code-scan/tests/test-resolve-header.js` | 3 (`003,028,080`) | 오탐 | `003`은 `F-003`, `028`은 `TS-028`(시나리오 id), 태스크번호는 `080` 1건뿐 |
  | `opal/tools/code-scan/tests/test-discover.js` | 3 (`002,004,080`) | 오탐 | `002,004`는 `F-00X`, 태스크번호는 `080` 1건뿐 |
  | `opal/tools/code-scan/tests/test-scaffold.js` | 3 (`004,023,080`) | 오탐 | `004`는 `F-004`, `023`은 `TS-023`(시나리오 id), 태스크번호는 `080` 1건뿐 |
  | `opal/tools/improve-tool/fw-inbox-README.md` | 3 (`002,005,058`) | 오탐 | `002,005`는 `F-00X`, 태스크번호는 `058` 1건뿐 |

  **집계: 진성 6 / 오탐 9 / 경계 3** (18건 전건 분류 완료).

  최초 실측의 대조군 1개("오탐 0건")는 **틀리지 않았지만 불충분했다** — 대조군을 전수로 넓히자 오탐 9건(단발 F-code/시나리오-id 매칭)과 경계 3건(다중 태스크 인용이나 단발 인용과 구분 애매)이 추가로 드러났고, 그중 6건은 오히려 **진성**(R-2가 막으려는 패턴이 TASK 12건 밖에서도 이미 발생 중)이다. 정규식 후보는 아래와 같이 재조정한다.
  - 정규식 후보 A(PM 실측 사용, `\b` 없음): `(?<![\d.])(\d{3})(?![\d])` — unique count ≥3, 30건 탐지.
  - 정규식 후보 B(HTTP 상태코드·IP 옥텟 배제): 후보 A에서 매칭된 값이 `{200,201,204,400,401,403,404,409,422,500,502,503}`(HTTP) 또는 IP 옥텟 패턴(`\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` 내부)에 속하면 카운트 제외 — `models.py`의 400, `main.py`의 127 배제 가능하나 F-code·TS-code·T0XX 다중 인용 문제는 해결하지 못함.
  - 정규식 후보 C(F-code/TS-code/T-prefix 선행 배제): `F-`, `TS-`, `T`(대문자, 바로 앞) 뒤에 붙는 3자리는 애초에 "기능/시나리오/태스크 접두 표기"로 별도 분류해 카운트에서 제외하고, `(태스크 NNN)`/`TASK NNN` 형태만 카운트하는 형식 제약형 — 오탐(F/TS-code)은 구조적으로 배제되지만 `T060`처럼 접두 없이 대괄호에 실리는 진성 인용은 여전히 잡아야 하므로 후보 C 단독으로는 미완성이며 PLAN에서 정규식 재설계가 필요하다.
- **Q3** (비차단 경고의 출력 채널 — 기존 구현 패턴): `cmdValidate`(`code-scan.js:3155`)의 `manifest_oversize`가 지목 대상이다. 구현은 (1) `violations.push({ code: 'manifest_oversize', ... })`(`:3301-3302`), (2) `counts.manifest_oversize`로 별도 집계(`:3443`), (3) `blockingViolations` 필터에서 `v.code !== 'manifest_oversize'` 조건으로 제외(`:3450`), (4) 주석 "`:3447` 'uncovered:pre_existing'과 'manifest_oversize'는 비차단(U-2) — 나머지는 차단 불변." R-3의 태스크번호 경고는 이 패턴을 그대로 재사용해 신규 `code`(예: `task_history_pattern`) + `counts.task_history_pattern` 필드 + `blockingViolations` 필터 조건 1행 추가로 구현 가능하다. AC(b)는 이 기존 관용구(같은 배열·다른 code·필터 제외)로 충족된다 — 신규 채널 발명 불필요(PRINCIPLES §2 재사용 우선과 정합).
- **Q4** (`VERSION` 상수·핀 위치): 현재값 **`'1.6.0'`**(`opal/tools/code-scan/code-scan.js:38`). 핀 단언 실제 위치: `opal/tools/code-scan/tests/test-shard-policy.js:1519-1521`, `opal/tools/code-scan/tests/test-shard.js:696-701`. TASK.md가 지목한 두 줄번호는 **정확**하다. 상향 필요 여부: 106(header-rules.md v1.9)이 직전 선례인데 그 태스크는 `VERSION` 상수를 건드리지 않았다(083 이후 무변경). 본 태스크(107)도 `cmdValidate`에 **추가적** 비차단 검증 로직을 더하는 것뿐 기존 필드 스키마·CLI 인터페이스를 변경하지 않으므로, 106 선례를 따라 **상향 불필요**로 잠정 판단한다(PLAN에서 소유자 확정 필요 — TASK.md §제약 ⑥이 미확정 항목으로 명시).
- **Q5** (12건 이력 소실 방지 근거): 3파일 표본 검증 — `state_tool.py`의 034·070, `brain_tool.py`의 027·053·071, `test_improve_tool.py`의 078 — `git log --oneline --all -- <경로>`에서 전건 커밋 존재 확인(`295ed45 fix(034)`, `c68cdb9 feat(070)`, `05ec41b feat(027)`, `2ce3c2e feat(053)`, `dafac7e feat(071)`, `d7a8ce0 feat(078)`). **3파일 표본 전건에서 "제거해도 이력이 남는다" 명제가 성립**한다. 나머지 9건은 EXECUTE 단계 진입 전 동일 방법으로 전건 재확인 필요(R-4 AC(c) 요구사항).
- **Q6** (`exports` 가이드 정확한 형식): `header-standard.md` §4(`:133-159`)는 **표 1개**로 구성된다 — 열 구성 `| layer | exports에 담는 내용 | 예시 |` 3열, 행 단위는 **layer 1개당 1행**(21종 layer), 예시 배치는 **같은 행 3번째 열에 배열 리터럴**(예: `["POST /auth/login", "DELETE /auth/logout"]`). R-1이 이 형식을 준용한다면 §4는 "담는 내용"만 있고 "담지 않는 내용" 열이 없으므로, R-1 AC(a)는 §4를 **부분 준용**(열 구성 확장, 표 형식 유지)하는 것으로 해석해야 한다.
- **Q7** (`note`·`feature` 실사용 현황): 3스코프 전수 스캔(109파일) 결과 — **`note` 필드 존재 2/109건(1.8%), 그 2건 전건 비어있지 않음**(`code-map-hook.js`·`code-scan.js` 자기 자신, 이력성 서술 포함). **`feature` 필드 존재 0/109건(0%)**. TASK.md의 "note 71건 전건 0자"는 본 재측정과 **불일치**(§확정 입력 판정에서 `수정필요`) — 표본 정의 차이로 추정되나 재현 불가, 소유자 보고 필요.
- **Q8** (회귀 기준 실측): `opal/tools/code-scan` — **344 passed / 0 failed**(TASK.md와 **일치**). `opal/tools/state-tool` — **400 passed, 3 skipped, 98 subtests passed**(TASK.md의 383과 **불일치**, 383 출처 재확인 불가). PLAN·EXECUTE 단계는 R-5 AC(b)를 "400 passed, 3 skipped 유지(회귀 0건)" 기준으로 재설정할 것을 권고한다.

## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| R-3 비차단 채널 구현 패턴 | `manifest_oversize` 패턴 재사용 — 동일 `violations` 배열에 신규 `code` push + `counts` 필드 추가 + `blockingViolations` 필터에 제외 조건 1행 추가 | `opal/tools/code-scan/code-scan.js:3301-3302,3443,3447-3450` |
| `VERSION` 현재값 | `'1.6.0'`(`code-scan.js:38`), 핀 단언 `test-shard-policy.js:1519-1521`·`test-shard.js:696-701` | 본 ANALYSIS Q4 |
| `VERSION` 상향 여부 | 상향 불필요로 잠정(106 선례 재사용, 최종 확정은 PLAN/소유자) | 본 ANALYSIS Q4·§4-4 |
| code-scan 회귀 기준 | 344 passed / 0 failed(`node --test tests/*.js`) | 본 ANALYSIS §1.4·Q8 E1 실행 관측 |
| state-tool 회귀 기준 | **400 passed, 3 skipped**(TASK.md 383과 불일치 — 이 값으로 R-5 AC(b) 재설정 권고) | 본 ANALYSIS §1.4·Q8 E1 실행 관측 |
| 태스크번호 패턴 임계값 | unique 3-digit 토큰 수 **≥3**은 109파일 전수에서 **30건**을 탐지한다(TASK 12건 + 추가 18건). 임계값을 4/5/6/7/9로 올려도 각각 17/13/9/7/6건이 걸릴 뿐 TASK 12건과 정확히 일치하는 값은 **없다**(본 ANALYSIS Q2 임계값 표) — "3 이상 = 12건 정확 탐지"는 최초 실측(대조군 1개)의 착오이며 철회한다 | 본 ANALYSIS Q2 전수 실측 |
| 태스크번호 패턴 정규식 | 후보 A `(?<![\d.])(\d{3})(?![\d])`(PM 실측 사용, `\b` 없음 — `T060`류도 매칭)는 30건을 탐지하되 `F-00X`/`TS-0XX`/HTTP상태코드/IP옥텟 오탐을 포함한다. 후보 B(HTTP·IP 배제)로도 F-code/TS-code/T-prefix 다중 인용 문제는 해소되지 않아 PLAN에서 정규식 재설계 필요(본 ANALYSIS Q2 18건 분류표: 오탐 9·경계 3·진성 6) | 본 ANALYSIS Q2 |
| `note`/`feature` 현행 baseline | `note` 2/109건 존재(전건 비어있지 않음), `feature` 0/109건 존재 | 본 ANALYSIS Q7 |
| R-4 이력 소실 확인(표본) | 3파일 전건 git log 확인 완료, 나머지 9파일 EXECUTE 단계에서 재확인 필요 | 본 ANALYSIS Q5 |
| exports 가이드 형식(§4 준용 대상) | 3열 표(layer/담는 내용/예시), layer당 1행, 예시는 배열 리터럴 — "담지 않는 것" 열은 §4에 없어 R-1이 신규 추가 | 본 ANALYSIS Q6 |

### PLAN 결정 필요

| 항목 | 쟁점 | 근거 |
|------|------|------|
| P-1 | R-2 AC(e) 신설 여부 — `docs/CONVENTIONS.md:218` 정정을 R-2 범위에 편입할지 최종 확정(본 ANALYSIS는 편입 권고) | 본 ANALYSIS Q1 |
| P-2 | 태스크번호 패턴 임계값(3) 및 정규식(후보 A/B/C 중 택1)을 `.opal/code-scan.json` 신규 설정 키로 노출할지, 상수 하드코딩으로 둘지 | 본 ANALYSIS §3.3, TASK.md §제약 |
| P-3 | R-4 나머지 9파일(표에 미표본) 이력 소실 확인 — EXECUTE 단계 진입 전 `git log --oneline --all -- <경로>` 전건 수행 배정 | 본 ANALYSIS Q5 |
| P-4 | `note` 필드의 기존 2건(이력성 텍스트 포함, `code-map-hook.js`·`code-scan.js` 자기 자신)을 R-4 정리 대상에 추가 포함할지 — TASK.md 12건 목록에는 없으나 R-2 원칙과 동일하게 위반 상태 | 본 ANALYSIS §4-3, Q7 |
| P-5 | **정리 대상 집합 확정(R-5 직결, 소유자 결정 필요 — 본 ANALYSIS는 3안 중 결정하지 않음)**: (가) TASK.md 12건 유지 + §완료기준을 "정규식 임계값 기준 30건 중 0건"이 아니라 "TASK.md §범위 ④ 12건 목록 기준 0건"으로 문구 수정 — 소요 최소(완료기준 문구 정정 1줄), 영향: 12건 밖 18건(오탐 9·경계 3·진성 6, 특히 `brain_session.py`·`models.py`·`config.py`·`test_config.py`·`main.py`·`code-map-hook.js` 6건 진성)은 이번 태스크에서 방치되어 R-2 위반이 프로젝트에 남는다. / (나) 30건 중 진성 판정 전건(12건 + 진성 6건 = 18건)으로 정리 범위 확대 — 소요: 6개 신규 파일 `description` 재작성 + git log 이력 소실 확인(P-3과 동일 절차 6건 추가), 영향: TASK.md §범위 ④·§완료기준 모두 개정 필요, EXECUTE 단계 규모 50%(12→18) 증가. / (다) 정규식 임계값을 상향(예: 6~9)해 자연 탈락으로 집합을 축소 — 소요: 최소(정규식 상수 1곳 변경), 영향: 임계값 6에서도 TASK 12건 중 4건(unique 4~5인 `brain_tool.py`·`todo_mirror_hook.py`·`scenario.py`·`test_brain_tool.py`)이 함께 탈락해 §범위 ④ 12건과 어긋나므로 §범위 자체를 다시 정의해야 하는 순환 문제가 생긴다 | 본 ANALYSIS Q2, §5 R-5 |
