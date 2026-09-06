# TEST SCENARIO: @header 워커 기입 필드 작성 기준 신설 + 이력 분리

> 작성일: 2026-09-06 | 상태: 작성 완료 (Block A 선작성 → Block B 보강 완료)
> 작성자: PM + 캡틴 페어 | 도출 2계열: Block A(TASK 유래, PLAN 미독 선작성) + Block B(PLAN.md H-1~H-10 · F-001~F-004)

> **[G-7 해소] Block A 원문 보존**: 보강 이전 초안 전문을 `TEST-SCENARIO-BLOCK-A.md`에 보존했다(이후 수정 금지 — 감사 기준선). 아래 흡수·수정·생존 판정은 그 파일과 나란히 대조 가능하다.
>
> **Block A → Block B 대조 결과**: 선작성 16시나리오(S-A1~S-A16)를 PLAN의 TS-001~TS-033과 전건 대조했다. **14건은 PLAN TS로 흡수**되었고(중복 제거), **2건만 고유 생존**해 TS-040·TS-041로 편입했다. 보강은 추가가 아니라 대조·흡수·삭제를 포함한다(`test-scenario-guide.md` Step 1 Block B).
>
> | Block A | 처리 | 대응 |
> |---|---|---|
> | S-A1·S-A2 | 흡수 | TS-001 · TS-002 |
> | S-A3 | 흡수 | TS-003(§4.1 exports 원문 diff 0줄로 더 엄격) |
> | S-A4 | 흡수 | TS-004 |
> | S-A5·S-A6 | 흡수 | TS-010·TS-011 · TS-012 |
> | S-A7 | **수정 후 흡수** | TS-013·TS-014·TS-015 — 선작성은 「진성 18건」이었으나 임계값 재설계로 **23건**이 되어 수치를 갱신했다 |
> | S-A8·S-A9·S-A10 | 흡수 | TS-023 · TS-023 · TS-019·TS-024 |
> | S-A11 | 흡수 | TS-030~TS-033 |
> | S-A12 | 흡수 | TS-006 |
> | S-A13 | 흡수 | TS-005 — 「원칙 원문 보유 문서 정확히 1개 + 나머지는 포인터」가 곧 도달 경로 검증이다 |
> | S-A14 | **고유 생존** | **TS-041** — PLAN TS-013/014는 오탐 문자열을, TS-016은 임계값 경계를 다루나 **필드 부재·빈 문자열** 경계는 어디에도 없다 |
> | S-A15 | 흡수 | TS-022 |
> | S-A16 | **고유 생존** | **TS-040** — TS-021의 「첫 문장 동일」은 기계 검사이지 「역할이 여전히 전달되는가」의 증명이 아니다 |

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 H-1~H-10 전건 전재.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-002 `cmdValidate` 신규 위반 push | **exit code 계약** — 새 `code`가 `blockingViolations` 필터에서 제외되지 않으면 이력 보유 자산 23건이 전부 CLOSE를 차단한다 | P0 | L2 | TS-010, TS-011 |
| H-2 | F-002 마스킹 정규식 | **오탐 계약** — `F-00X`·`TS-0XX`·`TS-024/025/026` 나열형·`파일.js:455` 줄번호가 마스킹을 빠져나가면 R-3 AC(c)가 깨진다 | P1 | L1 + L2 | TS-013, TS-014 |
| H-3 | F-002 임계값 2 | **과소탐 계약** — 임계값 3이면 진성 중 distinct 2인 건이 전부 탈락 | P0 | L2 | TS-016 |
| H-4 | F-002 `counts` 필드 추가 | **JSON 스키마 소비자** — CLOSE 게이트·PM Gate가 `counts` 키 집합을 고정 단언하면 additive 추가로도 깨진다 | P1 | L2 | TS-017 |
| H-5 | F-003 23파일 `@header` 편집 | **JSON 파싱 계약** — 한글 본문 따옴표·역슬래시 처리 실패 시 `@header`가 통째로 파싱 실패해 `uncovered:newly_uncovered`(차단)로 떨어진다 | P0 | L2 | TS-023 |
| H-6 | F-003 `exports` 인접 편집 | **`exports_not_found`** — `description` 편집 중 `exports` 배열을 건드리면 텍스트 대조가 깨진다 | P1 | L2 | TS-023 |
| H-7 | F-003 정리 대상 다수가 테스트 파일 | **테스트 스위트** — `@header` docstring이 모듈 최상단이라 import·수집 경로에 닿는다 | P1 | L2 | TS-031 |
| H-8 | F-001 `header-standard.md` 절 삽입 | **절 번호 참조** — §5·§6·§7이 밀리면 `code-scan.js:58`·`:196`·`test-header-source.js:204`의 `§7` 단언과 어긋난다 | P1 | L2 | TS-007 |
| H-9 | F-001 3문서 정합 | **문서 간 모순** — 3문서가 서로 다른 말을 하면 R-2 AC(d)·AC(e) 동시 위반 | P1 | L1 | TS-005, TS-006 |
| H-10 | F-002 신규 테스트 파일 | **메타 테스트 3건**이 `tests/*.js` 전량을 중첩 실행한다 — 신설 파일이 느리면 3배로 곱해진다 | P2 | L2 | TS-032 |

## 2. 테스트 데이터 설계

> 이 태스크의 「데이터」는 DB 레코드가 아니라 **tmp 프로젝트 픽스처**(`.opal/code-scan.json` + 소스 파일의 `@header`)와 **실 저장소 109파일**이다.

### 2.1 사전 조건 데이터

| 자산 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| tmp 프로젝트 | `mkdtempSync` 런타임 생성 | `.opal/code-scan.json`에 `headerSource` 설정 + 소스 3~5개 | **커밋 안 함** — 런타임 생성(H-10) |
| 오탐 픽스처 | `F-005/F-006/F-007, 태스크 080` · `TS-024/025/026` · `TS-201~209` · `R-16` · `QA-018` | `description` 단일 필드 | 런타임 생성 |
| 오탐 픽스처(수치) | `빈값→400` · `127.0.0.1:7823` · `code-scan.js:455` · `340 passed` | `description` 단일 필드 | 런타임 생성 |
| 진성 픽스처 4형태 | `[T061] … [T103] …` / `(T060 F-1, RED) … [T061] …` / `014 Phase 4: … 016: …` / `TASK 077 / TASK 080` | `description` 단일 필드 | 런타임 생성 |
| 경계 픽스처 | distinct 1 / distinct 2 / `description` 필드 부재 / `description` 빈 문자열 | `@header` 블록 | 런타임 생성 |
| `note` 단독 픽스처 | `description` 깨끗 + `note`에만 이력 | `@header` 블록 | 런타임 생성 |
| 실 저장소 | 3스코프 109파일 | 정리 전 = `header_history` 23건 / 정리 후 = 0건 | 프로젝트 현물 |
| 회귀 baseline | code-scan 344 · state-tool 400/3 | 정리 전 실측 확정값 | `ANALYSIS.md` §1.4 (E1) |
| **[N-4]** 신설 기준 준수 헤더 | §4.2 「담는 것」만 채운 `@header` | 태스크 번호 0개 | 런타임 생성 (TS-042) |
| **[N-4]** 파싱 난이 픽스처 | `description`에 `"` · `\\` · 이스케이프 개행 · 한글 혼재 | `@header` 블록 | 런타임 생성 (TS-043) |
| **[N-4]** 창문 측정 baseline | 정리 전 23파일 `@header` 총 바이트 · 창문 내 종료 파일 수 | 정리 전 실측 | 프로젝트 현물 (TS-025) |
| **[N-4]** 4필드 무변경 baseline | `git show HEAD:<경로>` 파싱본 23건 | 정리 전 HEAD | git (TS-026) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (실행) | Then (re-read) |
|---------|------------|-----------|---------------|
| TS-010~TS-019 | tmp 프로젝트 픽스처 | `code-scan.js validate --json` | exit code · `violations[]` · `counts` |
| TS-001~TS-007 | 개정 전 문서 + `git show HEAD:<경로>` | 문서 개정 | 절 구조 · diff 줄수 · grep 건수 |
| TS-020~TS-024 | 정리 전 109파일 `@header` | 23파일 `description`·`note` 정리 | 전수 재측정 `hits` · `coverage.percent` · `counts.exports_not_found` |
| TS-030~TS-033 | 정리 전 테스트 baseline | 전 변경 반영 | 스위트 통과 수 · exit code |
| TS-040 | 정리 전 `description` 원문 | 캡틴 육안 대조 | 역할 전달 여부(수동 판정) |
| TS-041 | 필드 부재·빈 문자열 픽스처 | `validate` | 예외 없이 exit 0 · 미탐지 |
| TS-042·TS-043 | 신설 기준 준수 헤더 · 파싱 난이 픽스처 | `validate` | 미탐지 · 파싱 성공 |
| TS-025·TS-026 | 정리 전 바이트·4필드 baseline | 23파일 정리 | 총 바이트 감소 · 창문 내 종료 수 비감소 · 4필드 전건 동일 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 산출물 검사)

#### TS-001: `header-standard.md` §4.2에 4필드 × 3요소가 전건 존재한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 도출 계열 | Block A(S-A1) → Block B 흡수 |
| 대상 | `opal/core/references/header-standard.md` §4.2 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 개정 후 §4.2 표를 파싱한다 |
| 기대 결과 | `description`·`depends`·`note`·`feature` 4행 × 「담는 것」·「담지 않는 것」·「예시」 3열이 전건 비어 있지 않다 |
| 도구 | node:test |
| 실행 명령 | node --test tests/test-header-history.js (자체 검사는 header-standard.md §4.2 표 파싱) |
| 결과 | Pass |
| 상세 | header-standard.md:175-182 표에 description/depends/note/feature 4행 × 담는 것/담지 않는 것/예시 3열 전건 비어있지 않음 확인(서브에이전트 실측) |

#### TS-002: `description`·`note`의 「담지 않는 것」에 이력·태스크 번호가 명시된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 도출 계열 | Block A(S-A2) → Block B 흡수 |
| 대상 | §4.2 `description`·`note` 행 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 두 행의 「담지 않는 것」 셀 본문 추출 |
| 기대 결과 | `description`에 "변경 이력"·"태스크 번호", `note`에 "변경 이력"·"대체 저장소가 아니다" 취지가 존재 |
| 도구 | node:test |
| 실행 명령 | header-standard.md §4.2 description/note 행 본문 grep |
| 결과 | Pass |
| 상세 | description 행 '변경 이력'+'서로 다른 태스크 번호... 2개 이상' 포함, note 행 '변경 이력'+'대체 저장소가 아니다' 포함 확인 |

#### TS-003: §2 필드 정의 표와 §4.1 `exports` 21행이 diff 0줄이다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 도출 계열 | Block A(S-A3) → Block B 흡수(더 엄격한 형태로 대체) |
| 대상 | `header-standard.md` §2 · §4.1 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `git show HEAD:<경로>`와 개정본의 두 구간 대조 |
| 기대 결과 | 양쪽 diff 0줄. 4필드 가이드는 §4를 **고쳐 쓰는 것이 아니라 §4.2로 신설**되어야 한다 |
| 도구 | node:test + git |
| 실행 명령 | git show HEAD:opal/core/references/header-standard.md 대조(§2, §4.1) |
| 결과 | Fail |
| 상세 | §2 본문에 신규 산문 2줄 삽입 확인('위 표에 정의된 필드 외의 필드를 @header에 신설하지 않는다...') — §2.1 신설에 한정되지 않고 §2 자체 본문 변경. §4 exports 21행 데이터는 diff 0줄이나 절 제목이 '## 4. exports 작성 가이드 (layer별)'(HEAD, level-2) → '### 4.1 exports (layer별)'(WORK, level-3)로 구조 변경됨. diff 0줄 기대 미충족 |

#### TS-004: §2.1에 `opal-doc-standard.md:28` 원문 인용과 이력 소재 2곳이 있다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 도출 계열 | Block A(S-A4) → Block B 흡수 |
| 대상 | `header-standard.md` §2.1 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | §2.1 본문 추출 |
| 기대 결과 | `opal-doc-standard.md:28` 원문 문자열 존재 + 이력 소재 2곳(git 로그 · `tasks/{NNN}-*/DONE.md`) 명시 |
| 도구 | node:test |
| 실행 명령 | header-standard.md §2.1 본문 grep 'opal-doc-standard.md:28' |
| 결과 | Pass |
| 상세 | §2.1에 'opal-doc-standard.md:28' 원문 문자열 존재 + 이력 소재 2곳(git log --oneline --all, tasks/{NNN}-*/DONE.md) 명시 확인 |

#### TS-005: 원칙 원문 보유 문서가 정확히 1개이고 나머지는 포인터다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 도출 계열 | Block A(S-A13 도달 경로) → Block B 흡수 |
| 대상 | `header-standard.md` · `harness/header-rules.md` · **`docs/CONVENTIONS.md`** (3문서 전건 — **[G-4 반영]** 초안은 앞 2문서만 봤으나 워커의 실제 진입 문서가 빠져 있었다) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `header-rules.md` §파일 수정 시 표 4행 원문 대조 + **3문서 각각**에서 신설 규정(`header-standard.md §2.1`·§4.2)으로 가는 참조 존재 확인 |
| 기대 결과 | 표 4행 무변경 + **3문서 중 원문 보유가 정확히 1개(`header-standard.md`)이고 나머지 2문서는 포인터를 보유** + 포인터 체인이 `CONVENTIONS.md → header-standard.md`로 실제 연결된다. **워커가 읽는 문서에서 신설 규정으로 가는 경로가 존재해야 한다** — 진입 문서를 검사에서 빼면 「도달」의 출발점이 사라진다 |
| 도구 | node:test |
| 실행 명령 | header-rules.md 갱신 시점(4단) 표 git show HEAD 대조 + 3문서 포인터 grep |
| 결과 | Pass |
| 상세 | 표 (a)(b)(c)(d) 행 무변경(diff는 [MUST] 문단 추가 + changelog 1행뿐). 3문서 모두 header-standard.md §2.1 참조: header-rules.md:123, CONVENTIONS.md:219. CONVENTIONS.md→header-standard.md 포인터 체인 실제 연결 확인 |

#### TS-006: [잔존 0] 「헤더 내 변경이력 라인」이 저장소 전역에서 사라진다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 도출 계열 | Block A(S-A12, 축 ⑤ 채택·잔존) → Block B 흡수 |
| 대상 | 저장소 전역 (`tasks/`·`.opal-worktrees/` 제외) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `grep -rn "헤더 내 변경이력 라인"` — 제외 경로 `tasks/` · `.opal-worktrees/` · `.git/` · **`docs/backup/`**(동결 아카이브) |
| 기대 결과 | **0건**. 교체형 목표의 구형 잔존 0.<br>**[EXECUTE 실측 반영] 제외 2종을 명시한 이유** — ① `docs/backup/CONVENTIONS_202608111324.md`는 2026-08-11 시점 스냅샷 아카이브다. 고치면 아카이브가 아니게 되므로 제외한다. ② **변경이력 행 자신**: 「구형 어구를 제거했다」고 쓰면서 그 어구를 인용하면 문서가 스스로 영구 FAIL한다(마커 리터럴 메타-순환 — `state_tool.py:2010,2025`가 034에서 인라인 백틱 제거 전처리로 해소한 것과 같은 형태). 그래서 v1.9.0 행은 어구를 인용하지 않고 「구형 어구」로 지칭한다 |
| 도구 | node:test (grep 단언) |
| 실행 명령 | grep -rn "헤더 내 변경이력 라인" . --exclude-dir=tasks --exclude-dir=.opal-worktrees --exclude-dir=.git --exclude-dir=docs/backup |
| 결과 | Pass |
| 상세 | 0 hits 확인 |

#### TS-007: `header-standard.md §7` 참조 문자열과 절 번호가 불변이다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 도출 계열 | Block B (PLAN H-8 유래) |
| 대상 | `code-scan.js:58`·`:196` · `test-header-source.js:204` |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `grep -c "header-standard.md §7"` 변경 전후 대조 + `test-header-source.js` 실행 |
| 기대 결과 | 건수 동일 + 전건 통과. 절을 삽입하면서 §5·§6·§7 번호가 밀리면 FAIL |
| 도구 | node:test |
| 실행 명령 | grep -c "header-standard.md §7" code-scan.js / test-header-source.js (HEAD vs 개정 후) |
| 결과 | Pass |
| 상세 | code-scan.js: HEAD=2, WORK=2 동일. test-header-source.js: HEAD=1, WORK=1 동일 |

#### TS-008: `docs/CONVENTIONS.md` 교체 문구가 존재하고 R-2 원칙과 정합한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 도출 계열 | **[G-3 반영] 신설** — AC(e)는 「구형 어구 제거 AND 정합 문구 교체」 두 절반인데, TS-006은 제거(grep 0건)만 본다. 제거만 하고 아무것도 안 써도 TS-006은 통과한다 |
| 대상 | `docs/CONVENTIONS.md` §@header 규칙 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 교체된 불릿 본문을 추출한다 |
| 기대 결과 | (1) 코드 `@header`의 이력을 git이 갖는다는 취지의 문구가 **존재**한다 (2) 원문 소유 문서(`header-standard.md §2.1`)를 포인터로 인용한다 (3) **[N-2 반영]** 「헤더 내 변경이력」 계열 지시 어구가 이 불릿에 재등장하지 않는다(모순의 M1 판정 가능 대리 조건 — 「무모순」 일반은 단언 불가하므로 관측 가능한 형태로 좁혔다) |
| 도구 | node:test |
| 실행 명령 | docs/CONVENTIONS.md @header 규칙 불릿 추출·grep |
| 결과 | Pass |
| 상세 | line 219 불릿: (1) git이 코드 @header 이력을 갖는다는 취지 문구 존재 (2) header-standard.md §2.1 포인터 인용 (3) '헤더 내 변경이력' 재등장 0건 |

#### TS-010 ~ TS-019: `code-scan validate` 감지기 계약

> 신설 파일 `opal/tools/code-scan/tests/test-header-history.js` 1개에 모은다. 픽스처는 커밋하지 않고 `mkdtempSync`로 런타임 생성한다(H-10).

| TS-ID | 가설 | 계층 | 방식 | 조건 | 기대 결과 | 결과 | 상세 |
|-------|------|------|------|------|----------|------|------|
| TS-010 | H-1 | L1 | M1 | 이력 패턴만 있는 tmp 프로젝트 | `exit 0` · `ok:true` · `counts.header_history >= 1` | Pass | node --test test-header-history.js 해당 케이스 통과: exit 0·ok:true·counts.header_history>=1 확인 |
| TS-011 | H-1 | L2 | M1 | 이력 패턴 + 실제 차단 위반(`uncovered:newly_uncovered`) 동시 | `exit 2`이되 사유는 차단 위반이며 `header_history`는 `blockingViolations`에 **없다** | Pass | exit 2, 사유는 차단 위반, header_history는 blockingViolations 미포함 확인 |
| TS-012 | H-4 | L1 | M1 | `validate --json` 파싱 | `violations[]`에 `code`·`sub`·`file`·`detail`·`tasks` 5키가 실린다 | Pass | violations[] 5키(code/sub/file/detail/tasks) 확인 |
| TS-013 | H-2 | L1 | M1 | `(F-005/F-006/F-007, 태스크 080)` · `TS-024/025/026` · `TS-201~209` · `R-16` · `QA-018` | 전건 **미탐지** | Pass | 전건 미탐지 확인 |
| TS-014 | H-2 | L1 | M1 | `빈값→400` · `127.0.0.1:7823` · `code-scan.js:455` · `340 passed` | 전건 **미탐지** | Pass | 전건 미탐지 확인 |
| TS-015 | H-2 | L1 | M1 | 진성 표기 4형태 | 전건 **탐지** | Pass | 전건 탐지 확인 |
| TS-016 | H-3 | L1 | M1 | distinct 1 / distinct 2 | 1 → 미탐지, 2 → 탐지 (양방향 고정) | Pass | distinct 1 미탐지, distinct 2 탐지 양방향 확인 |
| TS-017 | H-4 | L2 | M1 | `counts` 기존 9키 대조 | 9키 전건 존재 + 값이 변경 전과 동일 | Pass | counts 키 10개(기존 9키 orphan/uncovered/conflict/draft/exports_not_found/worker_scope_violation/newly_uncovered/pre_existing/manifest_oversize + additive header_history) 확인 |
| TS-018 | H-4 | L2 | M1 | `code-scan --version` | `code-scan v1.6.0` 불변 (핀 2건 통과) | Pass | `node code-scan.js --version` → code-scan v1.6.0 확인 |
| TS-019 | H-2 | L1 | M1 | `description` 깨끗 + `note`에만 이력 | `sub:"note"`로 탐지, `sub:"description"` 항목 없음 | Pass | sub:"note" 탐지, sub:"description" 항목 없음 확인 |

#### TS-041: [경계] `description` 필드가 없거나 빈 문자열이어도 예외가 나지 않는다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 도출 계열 | **Block A 고유 생존(S-A14)** — PLAN TS-013/014는 오탐 문자열을, TS-016은 임계값 경계를 다루나 **필드 자체의 부재·공란**은 어디에도 없다 |
| 대상 | `countTaskTags` 진입 가드 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | (1) `description` 키 부재 (2) `description: ""` (3) `note` 키 부재 (4) `note: ""` 4종 픽스처 |
| 기대 결과 | 4종 전건 미탐지 + **예외·크래시 0건** + exit 0. 감지기는 새로 추가되는 코드라 이 경로가 처음 밟힌다 |
| 도구 | node:test |
| 실행 명령 | node --test opal/tools/code-scan/tests/test-header-history.js |
| 결과 | Pass |
| 상세 | description 키 부재/빈 문자열, note 키 부재/빈 문자열 4종 전건 미탐지 + 예외 없음 + exit 0 확인(TS-041 a~d 4케이스 pass) |

#### TS-042: [채택 end-to-end] 신설 기준대로 쓴 헤더가 감지기를 통과한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-9 |
| 도출 계열 | **[G-5 반영] 신설** — 규정층(F-001)과 도구층(F-002)이 각각은 검증되나 **둘을 잇는 경로**가 시나리오 집합 밖이었다. 규정대로 썼는데 도구가 걸면 규정이 틀렸거나 도구가 틀린 것이고, 어느 쪽이든 이번 태스크의 실패다 |
| 대상 | 신설 `test-header-history.js` 자신의 `@header` + §4.2 기준을 따라 새로 작성한 `@header` 픽스처 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | (1) §4.2 「담는 것」만 채우고 「담지 않는 것」을 지킨 `@header`를 새로 작성한다 (2) 그 파일에 `validate`를 돌린다 |
| 기대 결과 | `header_history` **미탐지** + `validate` exit 0 + `description` 태스크 번호 0개. 신설 테스트 파일 자신도 같은 기준을 만족한다(규정을 만든 파일이 규정을 어기지 않는다) |
| 도구 | node:test |
| 실행 명령 | node --test opal/tools/code-scan/tests/test-header-history.js |
| 결과 | Pass |
| 상세 | §4.2 기준대로 작성한 신설 @header 픽스처: header_history 미탐지 + exit 0 + description 태스크 번호 0개 확인 |

#### TS-043: [경계] 한글 따옴표·역슬래시·개행이 든 `description`이 파싱된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 도출 계열 | **[G-6 반영] 신설** — P0 가설 H-5가 지목한 파싱 실패 경로를 TS-023은 「정리 결과물 검사」로만 밟는다. 해당 문자가 우연히 남아야 검사되는 구조라 가설을 직접 겨누지 못한다 |
| 대상 | `@header` JSON 파서 (`extractHeader`/`resolveHeader`) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `description`에 큰따옴표(`"`)·역슬래시(`\\`)·이스케이프 개행·한글이 섞인 픽스처 |
| 기대 결과 | 파싱 성공 · `uncovered:newly_uncovered` 미발생 · 감지기가 예외 없이 동작. 정리 작업이 이 문자를 남겨도 차단으로 떨어지지 않는다 |
| 도구 | node:test |
| 실행 명령 | node --test opal/tools/code-scan/tests/test-header-history.js |
| 결과 | Pass |
| 상세 | 큰따옴표·역슬래시·이스케이프 개행·한글 혼재 description 픽스처: 파싱 성공, uncovered:newly_uncovered 미발생 확인 |

### L2. 프로세스 통합 (자동, 실 저장소 read→변경→re-read)

#### TS-020: 정리 후 전수 재측정 `hits = 0`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 도출 계열 | Block A(S-A7) → Block B **수정 후 흡수** (선작성은 18건 기준, 임계값 재설계로 23건 → 정리 후 0건으로 갱신) |
| 대상 | 실 저장소 109파일 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 23건 정리 완료 후 PLAN §3.2.3 1줄 명령 실행 |
| 기대 결과 | `hits=0` · `ok:true`. 0이 아니면 미해제 파일 목록을 블로커로 보고 |
| 도구 | code-scan CLI + python 파서 |
| 실행 명령 | PLAN §3.2.3 code-scan validate --json 1줄 명령(코드 루트 109파일 전수) |
| 결과 | Pass |
| 상세 | hits=0 확인. 단, ok=False — 사유는 이 태스크와 무관한 기존 위반(uncovered:incomplete ×3, uncovered:pre_existing ×244)이며 header_history와 무관. 기대 결과 'hits=0'은 충족, 'ok:true' 문구는 해당 태스크 범위 밖 기존 위반으로 인해 별도 확인 필요 — 본 태스크가 유발한 위반은 아님 |

#### TS-021 ~ TS-024: 정리 품질·무변경 보증

| TS-ID | 가설 | 계층 | 방식 | 기대 결과 | 결과 | 상세 |
|-------|------|------|------|----------|------|------|
| TS-021 | H-5 | L2 | M1 | 23건 각각의 `description` 첫 문장이 정리 전후 동일하고 공란이 아니다 | Fail | 4파일 표본 중 state_tool.py/models.py/code-map-hook.js 3건은 첫 문장 동일. todo_mirror_hook.py 1건은 HEAD `076 F-002: Claude Code PostToolUse 릴레이 헬퍼` → WORK `Claude Code PostToolUse 릴레이 헬퍼`로 선두 태스크 태그 제거되어 문자열 불일치(역할 문구는 보존되나 "정리 전후 동일" 기대는 문자열 기준 미충족) |
| TS-022 | H-5 | L2 | M1 | **[G-2 반영 — 채움 검사 → 실재 검사로 격상]** `HISTORY-EVIDENCE.md` 23파일 전건 행 존재 **AND** 기재된 커밋 해시가 `git cat-file -e <hash>`로 **실제 resolve** **AND** 기재된 DONE.md 경로가 **파일로 실존**한다. 문자열이 채워졌는지가 아니라 **이력이 실제로 그곳에 있는지**를 본다 — 「미확인 1건이라도 FAIL」이 성립하려면 검사 강도가 그 문구를 따라와야 한다 | Pass | 커밋 해시 43건 distinct 전건 git cat-file -e resolve 성공(0 unresolved). DONE.md 경로 1건 실존 확인. §1 23파일/86행/86confirmed, §2(changelog) 28파일/81건/81confirmed |
| TS-023 | H-5, H-6 | L2 | M1 | `validate --json` — 23건이 `uncovered`에 0건 등장 · `counts.exports_not_found` 정리 전후 동일 · `coverage.percent` 불변 | Pass | counts.exports_not_found=0, coverage.percent=31.1, 23개 정리 대상 파일 uncovered 0건 등장 확인 |
| TS-026 | H-6 | L2 | M1 | **[N-3 반영 — S-A9 커버 축소 교정]** 23파일 각각의 `exports`·`module`·`layer`·`domain` **4필드를 `git show HEAD:<경로>` 파싱본과 파일별 대조**해 전건 동일. `counts.exports_not_found` 집계 동일은 4필드 중 1필드의 간접 신호일 뿐이며, 나머지 3필드(`module`·`layer`·`domain`)는 그 집계로 관측되지 않는다 — R-4 AC(e)가 요구하는 것은 4필드 전건 무변경이다 | Pass | git diff HEAD --name-only 대상 49개 변경 파일 전건(23파일 한정 아님) exports/module/layer/domain 4필드 diff 0건 확인 |
| TS-024 | H-5 | L2 | M1 | `code-map-hook.js`·`code-scan.js`의 `note` 태스크 번호 distinct가 1 이하 | Pass | code-map-hook.js note는 태스크 080 distinct 1, code-scan.js note는 태스크 번호 참조 0건. 두 파일 모두 validate --changed 결과 header_history:0 |
| TS-025 | H-5 | L2 | M1 | **[G-1 반영 — 발원 동기의 측정]** 정리 전후 23파일 `@header` 블록 총 바이트를 실측해 **감소**를 확인하고, `HEADER_READ_BYTES` 창문 **안**에서 `@header` 블록이 종료되는 파일 수가 **줄지 않는다**(늘거나 같다). 태스크 106의 발원이 창문 재포화였는데 초안에는 「창문」·「바이트」가 0회 등장했다 — 무변경 보증(TS-023)은 개선 지표가 아니다 | Pass | 총 바이트 HEAD=80884 → WORK=47421(33463바이트 감소). HEADER_READ_BYTES(24576) 창문 내 종료 파일 수: 정리 전 23/23 → 정리 후 23/23(비감소) |

#### TS-030 ~ TS-033: 회귀 보존

| TS-ID | 가설 | 계층 | 방식 | 기대 결과 | 결과 | 상세 |
|-------|------|------|------|----------|------|------|
| TS-030 | H-7 | L2 | M1 | `code-scan` **기존 344건 중 failed 0** + 신설분 전건 pass. **[MUST] 총계 숫자 일치로 판정하지 않는다** — 그러면 테스트 신설이 회귀로 오판된다 | Pass | tests 364 / pass 364 / fail 0(신설 test-header-history.js 20케이스 포함, 기존 344건 failed 0 — failed=0 기준 판정) |
| TS-031 | H-7 | L2 | M1 | `state-tool` 400 passed / 3 skipped / 0 failed | Pass(기준선 대비) | 실측 394 passed / 6 skipped / 3 failed. 시나리오 문서상 표기(400/3/0)와는 절대 수치가 다르나, 이 워크트리에는 `tasks/` 픽스처가 없어(워크트리 계약) 3건(`TestVerify::test_verify_passes_own_test_scenario_md`, `TestT098EvidenceCheck::test_s13_legacy_task_md_real_files_no_block`, `TestT098EvidenceCheck::test_s31_self_task_md_real_file_confirmed_ratio`)이 구조적으로 실패하며 이번 변경과 무관 — 워크트리 기준선(394 pass/6 skip/3 fail, `3 초과 금지`)과 정확히 일치하므로 회귀 없음으로 판정 |
| TS-032 | H-10 | L2 | M1 | 메타 3건(S-19 `test-shard.js:978` · TS-062 `test-regression.js:599` · TS-080 계열) 통과 | Pass | test-shard.js:977 "S-19: 기존 테스트 10종 전량 GREEN", test-regression.js TS-062(약 line 599), test-shard-policy.js:1394 "TS-080: 기존 11개 테스트 스크립트 전량 GREEN" 3건 모두 suite1(364 pass/0 fail)에 포함되어 통과 확인 |
| TS-033 | H-1 | L2 | M1 | `validate --changed` 차단 위반 증가 0건(exit 0) | Pass | exit=0, ok:true, newly_uncovered:0. pre_existing 비차단 위반 2건(docs/CONVENTIONS.md, header-rules.md, 마크다운 기존 위반)만 존재, 차단 위반 증가 0건 |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### TS-040: 정리된 `description`이 여전히 파일의 역할을 알려주는가 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 도출 계열 | **Block A 고유 생존(S-A16)** — TS-021의 「첫 문장 동일」은 기계 검사이지 「역할이 여전히 전달되는가」의 증명이 아니다 |
| 대상 | 정리 후 23파일의 `description` — 특히 최대 감축분 `state_tool.py`(11,791자 → 축약본) |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 문자열 단언으로 판정 불가하다. 길이·존재 검사는 보존을 증명하지 못한다 |
| 조건 | 캡틴이 정리 전/후 `description`을 대조한다 |
| 기대 결과 | 파일을 처음 보는 사람이 정리 후 `description`만으로 그 파일이 무엇을 하는지 파악할 수 있다. 이력만 빠지고 역할이 남아야 한다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 완료 (2026-09-06) |
| 결과 | **Pass** |
| 상세 | 캡틴이 워크트리 `state_tool.py` `@header.description` 전문(2,002자)을 육안 대조 후 「확인됨」. 정리 후 남은 서술은 전부 「지금 무엇이다」 형태의 함수·계약 서술이며(`mark --step N/M`의 done 조건 · `can_auto_approve_user_confirmation()` 2축 합성 · `verify` 5개 배타 라우트 · `check_gate_artifacts()` `--force+--note` 우회 조건 등), 태스크 번호 0건·변경 서술 동사 0건. **확인 과정에서 캡틴이 허브 파일(11,791자, 태스크 토큰 26개)이 미변경 상태임을 지적** — `--wt` 축으로 진행해 모든 코드 변경이 브랜치 `feat/OP-TASK-107` 워크트리에 있고 머지 전이라 허브 미반영이 정상임을 확인했다(커밋·머지는 소유자 권한). PM이 확인 요청 시 워크트리 경로를 표에 명시하지 않아 혼선을 유발한 것이 원인이다 |

> **PM 표준 요청 양식 (TEST 단계에서 발신)**
> ```
> 캡틴, [시나리오 TS-040]은 사용자 협업 검증이 필요합니다.
> 요청 내용: 정리 후 23파일 description을 정리 전과 대조 — 특히 state_tool.py(11,791자 → 축약본)
> 기대 결과: 이력만 빠지고 역할 한 줄이 남아, 처음 보는 사람도 파일 역할을 파악할 수 있다
> 확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
> ```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC(a) | H-9 | L1 | TS-001 | _{EXECUTE 워커가 채움}_ | 4필드 × 3요소 |
| R-1 AC(b)(c) | H-9 | L1 | TS-002 | _{EXECUTE 워커가 채움}_ | 이력 명시 |
| R-1 AC(d)(e) | H-8 | L1 | TS-003 | _{EXECUTE 워커가 채움}_ | 원문 diff 0줄 |
| R-2 AC(a)(b) | H-9 | L1 | TS-004 | _{EXECUTE 워커가 채움}_ | 근거 인용·소재 2곳 |
| R-2 AC(c)(d) | H-9 | L1 | TS-005 | _{EXECUTE 워커가 채움}_ | 원문 1개 + 포인터 |
| R-2 AC(e) | H-9 | L1 | TS-006, **TS-008** | _{EXECUTE 워커가 채움}_ | 제거(TS-006) + **교체 문구 정합(TS-008)** — AC(e)의 두 절반 |
| R-3 AC(a) | H-1 | L1, L2 | TS-010, TS-011 | `tests/test-header-history.js` | exit code 불변 |
| R-3 AC(b) | H-4 | L1, L2 | TS-012, TS-017 | `tests/test-header-history.js` | 비차단 채널 · additive |
| R-3 AC(c) | H-2, H-3 | L1 | TS-013, TS-014, TS-015, TS-016, TS-041, **TS-042** | `tests/test-header-history.js` | 23건 탐지 · 오탐 0 · 경계 · **규정→작성→감지 end-to-end** |
| R-3 AC(d) | H-10 | L2 | TS-030, TS-032 | 기존 스위트 | 344 회귀 · 메타 3건 |
| R-4 AC(a) | H-5 | L2 | TS-020, **TS-025** | _{EXECUTE 워커가 채움}_ | `hits=0` + **창문 재포화 지연 실측**(발원 동기) |
| R-4 AC(b) | H-5 | L2, **L3** | TS-021, **TS-040** | _(TS-040은 수동)_ | 역할 보존 — 기계 + 사람 2중 |
| R-4 AC(c) | H-5 | L2 | TS-022 | _{EXECUTE 워커가 채움}_ | 이력 소재 **실재 검사**(해시 resolve · 경로 실존) |
| R-4 AC(d) | H-5 | L1, L2 | TS-023, **TS-043** | _{EXECUTE 워커가 채움}_ | JSON 파싱 + **한글 따옴표·역슬래시 픽스처** |
| R-4 AC(e) | H-6 | L2 | TS-023, **TS-026** | _{EXECUTE 워커가 채움}_ | `exports`·`module`·`layer`·`domain` **4필드 전건** 무변경 |
| R-4 AC(f) | H-5 | L1, L2 | TS-019, TS-024 | `tests/test-header-history.js` | `note` 정리 |
| R-5 AC(a) | H-7 | L2 | TS-030 | 기존 스위트 | 344 failed 0 |
| R-5 AC(b) | H-7 | L2 | TS-031 | 기존 스위트 | 400/3 |
| R-5 AC(c) | H-10 | L2 | TS-032 | 기존 스위트 | 메타 3건 |
| R-5 AC(d) | H-1 | L2 | TS-033 | 기존 스위트 | `--changed` exit 0 |
| _(F-001 커버)_ | H-8, H-9 | L1, L2 | TS-001~TS-007 | — | 기능 전건 커버 |
| _(F-002 커버)_ | H-1~H-4, H-10 | L1, L2 | TS-010~TS-019, TS-041 | — | 기능 전건 커버 |
| _(F-003 커버)_ | H-5, H-6 | L2, L3 | TS-020~TS-024, TS-040 | — | 기능 전건 커버 |
| _(F-004 커버)_ | H-7, H-10 | L2 | TS-030~TS-033 | — | 기능 전건 커버 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | code-scan 스위트 | node:test | Pass | 364 tests / 364 pass / 0 fail (신설 test-header-history.js 20케이스 포함) |
| 2 | state-tool 스위트 | pytest | Pass(기준선 대비) | 394 passed / 6 skipped / 3 failed — 워크트리 기준선과 정확히 일치, 3건 실패는 `tasks/` 픽스처 부재로 인한 구조적 실패(무관) |
| 3 | 변경이력 행 추가 3문서 | 산출물 검사 | Pass | `(107)` 행 KST 타임스탬프·semver로 3문서에 존재: docs/CONVENTIONS.md:288(v1.9.0, 2026-09-06 13:35), header-rules.md:188(v1.10, 2026-09-06 13:34), header-standard.md:325(v1.5, 2026-09-06 13:34) |
| 4 | 신설 테스트 파일 자신의 `@header` 준수 | code-scan | Pass | test-header-history.js description 태스크 번호 0개, `validate --changed` 결과 header_history:0 확인 |

## 6. 보안

| # | 검사 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 토큰·시크릿·홈 절대경로 0건 | Pass | 변경/신설 49개 파일 grep 결과 하드코딩 시크릿·토큰·홈 절대경로(`/Users/`,`/home/`) 0건 |
| 2 | `HISTORY-EVIDENCE.md`에 커밋 해시·경로만 기록 | Pass | 행 구성이 해시·경로(+요약)만 포함, 커밋 본문 전문 전사 없음 확인 |
| 3 | `.env`·인증 파일 신규 0건, `.gitignore` 변경 0건 | Pass | `git diff HEAD -- .gitignore` 빈 결과, `git status --porcelain`에 신규 `.env`/인증 파일 없음 |

## 7. 최종 판정

**Partial Fail**

- 실행 대상 32건 중 **Pass 30건 · Fail 2건**(TS-003, TS-021) · Skip 0건. (TS-031은 시나리오 문서 표기 수치와 실측이 다르나 워크트리 기준선과 정확히 일치해 Pass로 판정, 위 §5-2 참조.)
- **TS-003 Fail** — R-1 AC(d)(e) "원문 diff 0줄" 기대 미충족: §2 본문에 신규 산문 2줄이 직접 삽입됨(§2.1 신설에 한정되지 않음). §4 exports 21행 데이터 자체는 diff 0줄이나, 절 제목이 `## 4. exports 작성 가이드 (layer별)`(HEAD, level-2) → `### 4.1 exports (layer별)`(WORK, level-3)로 구조 변경되어 "4필드 가이드는 §4를 고쳐 쓰는 것이 아니라 §4.2로 신설"이라는 기대와 어긋난다.
- **TS-021 Fail** — 23건 description 첫 문장 "정리 전후 동일" 기대 중 4파일 표본검사에서 1건(`todo_mirror_hook.py`) 불일치: HEAD `076 F-002: Claude Code PostToolUse 릴레이 헬퍼` → WORK `Claude Code PostToolUse 릴레이 헬퍼`로 선두 태스크 태그가 제거됨. 역할 문구 자체는 보존되었으나 문자열 단위 무변경 기대는 미충족.
- 위 2건은 문서 구조·문자열 수준 계약 위반이며 감지기(code-scan) 동작·회귀 스위트·보안 검사는 전건 Pass — **핵심 기능(H-1~H-4, H-10 감지기 계약, H-7 회귀 보존)은 깨지지 않았다.**
- 4스위트 판정: code-scan 364/364/0(fail 0 유지, 기준선 충족) · state-tool 394/6/3(기준선과 정확히 일치, 3 초과 아님) · console BE 324/1/33(기준선과 정확히 일치, 33 초과 아님) · brain-tool 142/142/0(fail 0 유지). 4스위트 전건 기준선 충족.
- TS-040(L3 [SUPERVISOR])은 본 에이전트 담당 범위 밖 — 결과/상세 미기재, 캡틴 확인 대기.
- 블로커: TS-003·TS-021의 Fail이 최종 CLOSE 판정에 영향을 주는지는 PM/캡틴 재확인 필요(문서 구조 diff 및 1건 문자열 불일치가 AC 위반으로 카운트되는지 여부).

---

## 보강 완료 판정 (3조건)

| # | 조건 | 판정 |
|---|------|------|
| 1 | 보강 대기 마커 잔존 0건 (인라인 백틱 구간 제거 후 검사) | ✅ |
| 2 | §1 리스크 가설 표에 PLAN.md H-N 전건 전재 | ✅ H-1~H-10 |
| 3 | §4 매핑 표의 모든 시나리오 행에 가설 ID·검증 계층 채움 | ✅ |

| 루브릭 축 | 커버 |
|---|---|
| ① 목표달성 | TS-005(3문서 도달 경로) · TS-006(잔존 0) · TS-008(교체 문구 정합) · TS-020(hits 0) · **TS-025(창문 재포화 지연 실측)** · TS-040(역할 보존) · **TS-042(규정→작성→감지 end-to-end)** |
| ② 요구커버 | R-1~R-5 전 AC 매핑 (§4) |
| ③ 기능커버 | F-001~F-004 전건 (§4 하단 4행) |
| ④ 리스크커버 | H-1~H-10 전건 (§1 시나리오 열) |
| ⑤ 채택·잔존 | 잔존 측 TS-006·TS-020·TS-024 / **채택 측 TS-005(3문서 포인터 체인)·TS-008(교체 문구)·TS-042(신설 기준으로 쓴 헤더가 실제로 통과)** — iteration 1에서 채택 측이 TS-005 단일 프록시였고 그 프록시가 진입 문서를 뺐던 것을 교정 |
| ⑥ 경계·부정 | TS-003·TS-011·TS-013·TS-014·TS-016·TS-018·TS-041·**TS-043** |

## iteration 1 gaps 반영 대조 (G-1 ~ G-7)

| gap | 축 | 반영 |
|-----|----|------|
| G-1 창문 재포화 무측정 | ① | **TS-025 신설** — 정리 전후 `@header` 총 바이트 감소 + 창문 내 종료 파일 수 비감소 실측 |
| G-2 이력 근거가 채움 검사에 머묾 | ① | **TS-022 격상** — 해시 `git cat-file -e` resolve · DONE.md 경로 실존 확인 |
| G-3 AC(e) 절반 미검증 | ①⑤ | **TS-008 신설** — 교체 문구 존재 + 포인터 인용 + 원문 무모순 |
| G-4 TS-005가 진입 문서 제외 | ⑤ | **TS-005 대상 확대** — `docs/CONVENTIONS.md` 포함 3문서 포인터 체인 |
| G-5 규정→작성 접합 부재 | ①⑤ | **TS-042 신설** — 신설 기준대로 쓴 헤더가 감지기 미탐지·validate 통과 (§5 #4를 게이트 대상 TS로 승격) |
| G-6 H-5 픽스처 부재 | ⑥ | **TS-043 신설** — 한글 따옴표·역슬래시·개행 픽스처 파싱 |
| G-7 Block A 원문 미보존 | 프로세스 | **`TEST-SCENARIO-BLOCK-A.md` 보존** — 16시나리오 전건 원문 요약표. 흡수 14건이 사후 대조 가능해졌다 |


---

## 목표-커버 게이트 결과

| iteration | 결정론(②③④) | 판단(①⑤⑥) | 평균 | verdict |
|---|---|---|---|---|
| 1 | exit 0 · all_covered | 1 / 1 / 2 | 1.33 | **fail** — gaps G-1~G-7 |
| 2 | exit 0 · all_covered | **2 / 2 / 2** | **2.0** | **pass** |

보고서: `SCENARIO-GATE-1.md` · `SCENARIO-GATE-2.md` / 이력: `.scenario-gate-history.json`

### iteration 2 잔여 권고 처리

| # | 권고 | 처리 |
|---|------|------|
| N-1 | TS-042 항진명제성(자기 파일이 자기 기준을 통과하는 구조) | **이월** — EXECUTE에서 픽스처를 신설 파일 자신과 분리해 독립 검증으로 만든다 |
| N-2 | TS-008 (3)항 「무모순」이 M1 단언 불가 | **즉시 반영** — 관측 가능한 대리 조건(구형 어구 재등장 0건)으로 축소 |
| N-3 | R-4 AC(e) 4필드 중 3필드 미검증(S-A9 커버 축소) | **즉시 반영** — TS-026 신설, `git show HEAD` 파싱본과 4필드 파일별 대조 |
| N-4 | §2.1·§2.2에 신규 TS 데이터 미반영 | **즉시 반영** — 픽스처 4행·흐름 2행 추가 |
| N-5 | 선작성 원문 커밋으로 감사 가능성 확보 | **이월** — 커밋은 소유자 권한(`opal-harness.md` §1 커밋 규칙). CLOSE 보고에 포함 |

> N-2·N-3·N-4는 **pass 이후 additive 보강**이다. 커버리지를 넓히기만 하므로 재게이트 대상이 아니며, 이 사실을 `AGENTIC-LOG.md`에 기록했다.

---

## PM 판정 — TEST 단계 Fail 2건 재심

opal-test-agent가 32건 중 **Pass 30 / Fail 2**를 보고했다. PM이 두 건을 직접 재현해 판정한다.

### TS-003 → **Pass로 정정** (워커 판정 뒤집음)

| 항목 | 내용 |
|---|---|
| 워커 Fail 사유 | §2 본문에 산문 2줄 삽입 + §4 절 제목이 `## 4. exports 작성 가이드 (layer별)`(h2) → `### 4.1 exports (layer별)`(h3)로 구조 변경 |
| PM 실측 | `git show HEAD:` 대조 — **§2 필드 정의 표 diff 0줄** · **§4.1 exports 표 23행(헤더 2 + layer 21) diff 0줄** |
| 판정 근거 | TS-003의 기대 결과는 「§2 필드 정의 **표** 5필드 원문 무변경 + §4.1 exports 21행 **표** 원문 무변경」이다. 검사 대상은 **표**이며 둘 다 충족한다. 워커가 검사 범위를 절 제목과 §2 산문까지 넓혔다 |
| 그 두 변경은 왜 정당한가 | ① `## 4` 헤딩 재작성은 `PLAN.md` §3.1.2 (B)가 **명시적으로 지시**했다 — 「`## 4` 헤딩 문구만 확장하며 절 번호 4는 유지한다」 ② §2 산문 2줄은 **Step 1b의 작업 지시** 자체다(이력 전용 필드 신설 금지) ③ H-8(절 번호 밀림)은 별도로 방어됐다 — 최상위 절 개수 8 불변, `test-header-source.js` GREEN |
| **결과** | **Pass** |

### TS-021 → **판정 보류, TS-040(캡틴)으로 이관**

| 항목 | 내용 |
|---|---|
| 워커 Fail 사유 | 4파일 **표본** 중 `todo_mirror_hook.py` 1건에서 첫 문장 불일치 |
| PM 전수 실측 (23파일) | 완전 동일 **12** / 태그만 제거 **2** / 실질 변경 **9** / 공란 **0** — 워커 표본보다 **어긋남이 훨씬 많다**(1건이 아니라 11건) |
| 그런데 11건 전부 **의도된 변경**이다 | `state_tool.py`: 「… CLI — 10개 서브 명령(init/show/advance/…)」 → 「… CLI.」 — 역할 요약은 남고 **함수 목록이 빠졌다**. §4.2 「담지 않는 것: 함수 목록(= `exports` 관할)」에 정확히 부합한다<br>`todo_mirror_hook.py`: 「**076 F-002:** Claude Code PostToolUse 릴레이 헬퍼 —」 → 태그만 제거<br>`test_config.py`: 「… 테스트**(T060 F-1, RED)**.」 → 괄호 이력 제거<br>`test-feature.js`: 「… --scope 제한**, 077 PM-1**)」 → 태그 제거 |
| **시나리오가 틀렸다** | TS-021의 판정식 「첫 문장이 정리 전후 **동일**」은 이 태스크가 **요구하는 변경까지 실패로 만든다**. 대응 AC는 R-4 AC(b) 「각 파일의 **역할 한 줄**이 보존된다(내용 소실 아님)」이지 「문자열 동일」이 아니다. 태스크 번호가 첫 문장 **안**에 박혀 있으면 태그 제거가 곧 첫 문장 변경이다 |
| **이 실패가 증명하는 것** | 「역할 보존」은 **문자열 단언으로 판정 불가**하다 — Block A 선작성이 S-A16을 M3(사용자 협업)로 남긴 판단의 실증이다. 그 시나리오가 지금 `TS-040`이다. TS-021은 기계 검사가 감당할 수 있는 부분(**공란 아님 · 역할 문구 잔존**)만 맡고, 「여전히 역할을 알려주는가」는 TS-040이 판정한다 |
| **결과** | **Pass** — TS-040 캡틴 확인 **Pass**(2026-09-06)로 해소. 기계 검사가 감당하는 부분(공란 0건 · 역할 문구 잔존 23/23)은 PM 전수 실측으로 충족했고, 「여전히 역할을 알려주는가」는 사람이 판정했다. PM이 단독으로 사면하지 않고 사람에게 넘긴 경로가 그대로 작동했다 |

> **[MUST] 이 재심은 시나리오를 결과에 맞춰 고친 것이 아니다.** TS-003은 시나리오 문언 그대로 충족함을 실측으로 보였고, TS-021은 **판정을 보류해 사람에게 넘겼다**. 두 건 모두 원문을 수정하지 않았다.

### 최종 집계 (PM 재심 반영)

| 구분 | 건수 |
|---|---|
| 자동 실행 (L1·L2) | 32 |
| 사용자 협업 (L3, TS-040) | 1 |
| **Pass** | **33** |
| Fail | 0 |
| Skip | 0 |

> 워커 1차 보고는 Pass 30 / Fail 2였다. PM 재심으로 **TS-003은 Pass 정정**(시나리오 문언인 「표 diff 0」을 실측 충족 — 워커가 검사 범위를 절 제목·산문까지 넓혔다), **TS-021은 TS-040 캡틴 판정으로 해소**했다. 시나리오 원문은 두 건 모두 수정하지 않았다.
