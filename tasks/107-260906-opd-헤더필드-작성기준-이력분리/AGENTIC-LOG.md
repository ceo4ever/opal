# AGENTIC-LOG: @header 워커 기입 필드 작성 기준 신설 + 이력 분리

> 모드: agentic | 시작: 2026-09-06 | 스킬: //opd

## [DECISION] 이력은 @header에 남기지 않는다 (캡틴 확정)
- 캡틴 발화: "이력 같은 것은 남기지 말자. git 으로 추적이 가능하니"
- 반려된 대안: `note` 필드로 이관 — **블록 총량이 그대로**여서 창문 재포화를 늦출 뿐이다
- 근거 승계: `opal-doc-standard.md:28` "실행 지시문은 코드처럼 제자리에서 갱신되고 **변경 이력은 git이 갖는다**" — `.md` 실행 지시문에 확립된 원칙을 코드 `@header`에 적용

## [DECISION] `description` 글자수 상한 미채택
- PM이 앞선 대화에서 "상한 같은 도구 검증 가능 기준"을 제안했으나 **실측으로 철회**
- 상관 실측(표본 71건): 태스크번호 수 ↔ desc 길이 **+0.76** vs 파일 줄수 ↔ desc 길이 +0.66. 이력성 12건 제외 시 후자가 **+0.39로 반감**
- 같은 규모 대조: `state_tool.py` 3558줄/11791자(태스크 26개) vs `test_brain.py` 3219줄/1151자(태스크 0개) — **10배 차이의 원인은 크기가 아니라 이력**
- 판정: **길이는 잘못된 축**이다. 역할 요약은 코드량과 무관하며 코드량 축은 `exports`가 담당한다(상관 +0.69). 검증은 길이가 아니라 **태스크번호 패턴(성질)** 으로 설계한다

## [GATE] TASK 단계
- 판정: Pass — `verify --clarification-check` = pass
- Git 사전 점검: 워킹트리 **클린**(106 커밋 `5641fdf` 이후 변경 0건)
- 태스크 번호 107 (`memory-tool task-number --bump`), 날짜 260906 (`date.js yymmdd`)
- 발원: 태스크 106 DONE.md §8 이월 1·2번. 106 ADD-1이 창문을 상향했으나 **재포화가 시간 문제**임이 드러났고, 원인 추적 결과 도구 결함이 아니라 **작성 기준 공백**이었다

## [DECISION] `--wt` 재진입 — worktree 생성, state.json 재초기화는 하지 않는다 (2026-09-06 11:52)
- 캡틴 재호출: `//opd --agentic --wt 태스크 107` — TASK 단계 완료 후 워크스페이스 축이 추가로 지정됐다
- 실행: `worktree-tool create --task 107` → `ok:true`, `worktree_root=.opal-worktrees/task_107`, `branch=feat/OP-TASK-107`(base `main`), layout `monorepo`, gitignore `present`
- 경고 1건(비차단): uv 캐시가 프로젝트와 다른 볼륨 — 슬롯당 `.venv` 실복사. `UV_CACHE_DIR` 이전으로 해소 가능
- 미결 setup 1건: `dashboard/frontend`에서 `npm ci` (이번 태스크 변경 영역 밖 — 미실행)
- **반려한 대안**: `state-tool init --force --worktree <path>`로 재초기화 — `worktree` 키는 `state_tool.py:1371` 조건부 대입 1행이 전부이고 어떤 게이트도 소비하지 않는 **기록 전용 필드**인데, 재초기화는 완료된 TASK 행(row 1)의 timestamp를 파기한다. 얻는 것이 기록 1줄, 잃는 것이 실제 이력이라 채택하지 않았다
- **대체 경로**: 코드 루트는 규약상 결정론적 경로(`{프로젝트}/.opal-worktrees/task_{NNN}/`)이므로, PM이 `pm/dispatch-process.md` §작업 경로 블록을 워커 프롬프트에 직접 주입해 동등 효과를 얻는다

## [GATE] ANALYSIS 진입
- 판정: Pass — TASK 행(row 1) `done`, `advance analysis.analysis_md` 시 도구가 row 2(사용자 확인)를 `auto_approved`로 자동 승인(agentic 계약, 093)
- Git 사전 점검: `.opal/MEMORY.json` 1행 수정 + `tasks/107-.../` untracked. 코드 변경은 worktree(별도 브랜치)에서 수행하므로 허브 워킹트리와 충돌하지 않는다 — 커밋/스태시 요구 없이 진행
- brain 사전 조회(6페이지 후보): `exports-generation-tool-verification-division`·`code-header-dual-source-inheritance`·`shard-policy-block-vs-nonblock-fallback-criterion`·`code-scan-mandatory-policy`·`code-map-write-location-decision`·`code-scan-gate-deadlock-init-placement` → 워커 컨텍스트에 주입
- code-scan 사전 범위 파악: `summary` 호출 완료(코드 작업 판별 = 코드 작업 — `code-scan.js` 변경 포함)

## [ERROR] ANALYSIS Q2 — 임계값 3의 탐지 집합이 12건이 아니라 30건 (2026-09-06 12:10)
- 워커 주장: "임계값 3 적용 시 12건 전건이 정확히 탐지되고 대조군 오탐 0건"
- PM 전수 재측정(E1, `code-scan scan --json` 109파일 × 정규식 후보 A): unique 3-digit ≥3인 파일이 **30건**
- 12건 밖 18건 예시: `dashboard/backend/adapters/brain_session.py`(1954자·3개)·`dashboard/backend/models.py`(1938자·3개)·`opal/tools/code-scan/tests/test-shard-policy.js`(450자·9개)·`opal/tools/code-scan/code-map-hook.js`(414자·3개)
- 워커 검증 설계 결함: 대조군을 **1개 파일**(`test_brain.py`)로만 두고 전수 대조를 하지 않았다. 12건은 확인했으나 "12건**만**"은 확인하지 않았다
- 파급: R-3 AC(c)「정리 전 12건을 정확히 탐지하고 오탐 0건」이 임계값 3에서 성립하지 않는다. TASK.md §완료기준「정리 후 태스크번호 3개 이상 0건」을 문자대로 적용하면 정리 대상이 30건이 되어 §범위 ④(12건)와 충돌한다

## [GATE] ANALYSIS PM Gate — Fail (루핑 1/3)
- 판정: **Fail** — agentic §4 강화 검토 항목 6(산출물 직접 Read 실질 검증)에서 위 ERROR 검출
- 통과 항목: 게이트 체크리스트 5건 전건 충족(§0 선조회 기재·확정 입력 전건 판정·§1.1 5열 표·§다음 단계 입력 3열 표·소스코드 원문 블록 0건)
- PM 독립 재현으로 **확인된** 워커 주장: `VERSION='1.6.0'`(`code-scan.js:38`) · 핀 2곳(`test-shard-policy.js:1519`·`test-shard.js:696`) · `blockingViolations` 비차단 필터(`code-scan.js:3448-3451`) · code-scan **344 passed/0 failed** · state-tool **400 passed/3 skipped**(TASK.md 383과 불일치 확정) · `note` 2/109건 존재·전건 비어있지 않음 · `feature` 0/109건
- 부수 오류: 산출물 주석의 "TASK.md에 `[사실]` 5항목" — 실제 3항목
- 조치: 전수 측정 근거를 주입해 워커 재지시(Q2·§5 R-3·§8·P-2 정정 + 18건 분류)

## [FIX] ANALYSIS 재지시 반영 확인 (2026-09-06 12:15) — 선행 [ERROR](Q2 탐지 집합) 참조
- C-1 Q2 전면 재작성 ✅ / C-2 18건 분류 표 신설 ✅ / C-3 §5 R-5 신규 ✅ / C-4 §8·P-5 신설 ✅ / C-5 `[사실]` 3항목 정정 ✅
- 18건 분류 집계: **진성 6 / 오탐 9 / 경계 3**
- PM 독립 표본 검증 3건으로 분류 정확성 확인 — `test-hook.js`(F-005/F-002 + 태스크 080 단발 → 오탐 타당) · `test-shard-policy.js`(F-001~F-012 + 태스크 083 단발 → 오탐 타당) · `models.py`(`[T061]` 태그 단락 순차 누적 → 진성 타당)

## [GATE] ANALYSIS PM Gate — Pass
- 판정: **Pass** — 게이트 체크리스트 5항목 전건 충족 + agentic §4 강화 검토 6항목 충족
- 행 처리: `analysis.analysis_md` done(`--as-worker --worker-stage ANALYSIS --worker-duration-minutes 15` — 워커 2회 합산 594757ms + 326355ms = 921112ms ≈ 15분) / `analysis.pm_gate` done
- 최대 산출은 요구사항 결함 발견이다 — R-3의 「태스크번호 패턴 감지」가 단순 3자리 카운트로는 성립하지 않는다. 18건 중 오탐 9건이 전부 `F-00X` 기능번호·`TS-0XX` 시나리오 id였고, 진성 6건은 TASK.md 12건 목록 **밖**에서 이미 위반 상태였다

## [ESCALATION] 정리 대상 집합 확정 — TASK.md 내부 충돌 (소유자 판단 필요)
- 사유: agentic §6「요구사항 모호성(TASK.md에서 판단 불가)」 — §범위 ④「기존 이력성 12건 정리」와 §완료기준「태스크번호 3개 이상 0건」이 서로 다른 집합을 지목한다
- 실측: 임계값 3~9 전 구간에서 TASK.md 12건과 정확히 일치하는 값이 없다(임계값 5에서 12건 중 `brain_tool.py`가 먼저 탈락)
- PM이 대행 결정하지 않는 근거: 세 후보가 태스크 범위 자체를 각각 다르게 만든다 — 12건 유지(축소) / 진성 18건 확대 / 임계값 상향(집합 재정의). 범위 결정은 소유자 권한이다

## [DECISION] 정리 대상 = 진성 18건 전건 (캡틴 확정, 2026-09-06 12:22)
- 캡틴 선택: 「진성 18건 전건」 — TASK.md 12건 + ANALYSIS 신규 발견 진성 6건
- 반려된 대안: 12건 유지+6건 이월 / R-4 별건 분리 — 둘 다 **규정을 신설한 직후 프레임워크 자산이 그 규정을 위반한 상태**로 태스크가 닫힌다
- TASK.md 반영: §범위 ④ · §완료기준 · R-4 제목·AC 전면 · R-3 AC(c). `verify --clarification-check` = pass 재확인

## [DECISION] TASK.md 확정 입력 2건 실측 정정 (PM 대행)
- `state-tool` 회귀 기준 383 → **400 passed / 3 skipped**(제약 ⑤ · 완료기준 · R-5 AC(b) 3곳). 383을 두면 **달성 불가능한 AC**가 되므로 방치가 곧 결함이다
- `[사실]` 「`note` 71건 전건 0자」 철회 → 「109파일 중 2건만 존재, 그 2건은 이력으로 오염」. 문제 진술 자체가 뒤집혔다 — '안 쓴다'가 아니라 '거의 선언되지 않고, 선언된 소수는 이미 위반'
- 파생 조치: R-4 AC(f) 신설 — `note`에 실린 이력성 서술도 정리 대상에 포함(R-2 원칙은 `note`에도 동일 적용)
- PM 대행 근거: 둘 다 **실측으로 반증된 사실의 정정**이지 기준 완화가 아니다(PRINCIPLES §1 「나중에 추가된 기준은 합리화」의 대상이 아님)

## [DECISION] R-2 AC(e) 신설 — `docs/CONVENTIONS.md` 편입 (PM 대행)
- ANALYSIS Q1 권고 채택. 규모가 **1개 불릿 문구 정정**이라 별건 분리 비용이 편익을 넘는다
- 방치 시 결함: CONVENTIONS.md는 「개발 작업 시 항상」 참조되는 [MUST] 등재 문서다 — 반대 규정을 남겨 두면 다음 태스크 워커가 그 문구를 근거로 헤더에 이력을 다시 쌓는다. R-2가 표방한 "3층 일관 적용"이 4번째 층에서 무너진다

## [GATE] PLAN 진입
- 판정: Pass — `advance plan.plan_md` 시 도구가 row 5(ANALYSIS 사용자 확인)를 `auto_approved`로 자동 승인
- 워커: `opal-plan-agent`(advanced/opus). 주입 강화 3건 — ① 선행 확정값 승계 목록(재조사 금지) ② ANALYSIS P-1~P-5의 **닫힘/열림 상태표**(산출물의 P 표를 그대로 믿지 말라는 지시) ③ `Write` 차단 사전 고지(heredoc 직행)
- 최대 난제로 지목한 항목: R-3 정규식 재설계 — "단발 인용과 이력 누적을 가르는 축을 먼저 정의하고 거기서 정규식을 유도하라, 정규식을 먼저 쓰고 사례를 끼워 맞추지 마라"

## [DECISION] 목표계열 선작성 트랙 ON (PLAN 병렬)
- 채택 근거: 이 태스크의 핵심 목표가 **파괴 관점으로 환원되지 않는다** — R-1·R-2는 문서 개정이라 "깨질 수 있는 계약"이 없어 리스크 가설 표만으로 도출하면 목표 달성 검증이 통째로 누락된다. 「헤더 내 이력 라인 → git」은 **교체형 목표**여서 채택/잔존 축(⑤)도 실재한다
- `red-first.md` §1.6이 경고한 오용(효율 기대)에 해당하지 않음을 확인 — 095 실측상 순 절감은 7%에 그치며, 켜는 이유는 품질이다
- 산출: `TEST-SCENARIO.md` Block A 초안 16시나리오(18,972 bytes) — 축 ① 4건 · ⑤ 2건 · ⑥ 4건 포함, 보강 대기 마커 39개
- PLAN.md 미독 상태 유지 확인. 목표-커버 게이트 미호출(`scenario-gate.md` §4), `test_scenario.*` 행 미전이

## [GATE] PLAN PM Gate — Pass
- 판정: **Pass** — PLAN.md 83,537 bytes / 986줄 / 15 Step / 5 Phase / F-001~F-004, H-1~H-10
- 검증 체크리스트 4항목 전건 충족: TASK.md R-1~R-5 → F-001~F-004 커버 · §4.2 Step 전건 소속 F-ID·완료 기준·agent 배정 근거 보유 · §리스크 가설 표 H-1~H-10 · 설계 빈틈 잔여는 D-REQ-1 1건(소유자 결정 사안이지 설계 결함이 아님)
- 행 처리: `plan.plan_md` done(`--worker-duration-minutes 18` — 1077875ms) / `plan.pm_gate` done
- **PM 독립 재현 검증(E1)**: PLAN §3.2.2 감지 규칙(M1~M4 마스킹 + TOK + distinct≥2)을 PM이 별도 스크립트로 구현해 109파일 전수에 적용 — `description` 탐지 **23건** · 진성 **18/18** · ANALYSIS 오탐 **0/9** · `note` **1건**(`code-scan.js`) · 잔여 5건 목록까지 PLAN 기재와 **완전 일치**. 워커 주장을 문서만 보고 통과시키지 않았다
- 설계 품질 평가: 임계값 2를 튜닝값이 아니라 **축 정의의 귀결**로 유도했고(3으로 올리면 진성 6건 탈락을 실측으로 제시), 오탐을 사후 예외 목록이 아니라 **토큰화 이전 구조적 마스킹**으로 제거했다. M4의 나열·범위 꼬리는 「정리한 파일이 `TS-024/025/026` 하나로 다시 걸리는」 실패 모드를 실측으로 잡아 넣은 것이다

## [ERROR] R-4 AC(f) 과다 특정 — PM 자신의 정정
- 내가 TASK.md에 쓴 AC(f)가 `note` 대상을 `code-map-hook.js`·`code-scan.js` **2파일로 지목**했으나, 실측상 이력 누적은 **1건**(`code-scan.js`)뿐이다
- 원인: 「`note` 필드가 **존재하는** 파일 수(2건)」와 「그 `note`가 **이력성인** 파일 수(1건)」를 혼동했다. `code-map-hook.js`의 `note`는 태스크 080 단발 인용을 포함한 설계 계약 서술이라 이력 누적이 아니다
- 조치: AC(f)를 파일 목록형 → **판정 기준형**으로 교체(TASK.md), PLAN §5.1 「note 2건 정리」도 1건으로 정정. 목록으로 못박으면 규칙이 아니라 그때의 관측을 고정하게 된다

## [ESCALATION] D-REQ-1 — 탐지 23건 vs 정리 18건, 잔여 5건
- 사유: 캡틴이 「진성 18건 전건」을 확정한 것은 **임계값 3 기준의 진성 정의** 위에서였다. PLAN이 축을 재정의하면서 진성 집합이 **23건**으로 바뀌었다 — 집합의 정의가 달라졌으므로 같은 질문의 반복이 아니다
- 잔여 5건: `AppShell.tsx`(061,063) · `backlog_tool.py`(056,069) · `test-shard.js`(082,083) · `test-feature.js`(077,080) · `test-validate.js`(077,080)
- 이 중 3건(`AppShell.tsx`·`backlog_tool.py`·`test-shard.js`)은 **ANALYSIS 30건 목록에도 없었다** — 거친 정규식(raw 3자리 ≥3)이 놓친 진성이다
- PLAN 권고는 (가) 18건 유지 + 이월. PM은 이를 그대로 대행하지 않는다 — 캡틴이 18건을 고른 선택지의 문구가 「규정 신설 직후 위반 0건 상태를 만든다」였고, 5건을 남기면 그 이유가 성립하지 않는다

## [DECISION] D-REQ-1 = (나) 23건 확대 (캡틴 확정, 2026-09-06 13:20)
- 캡틴 선택: 「23건으로 확대」 — 잔여 5건까지 정리해 정리 후 `header_history` 탐지 0건을 달성
- 이것을 P-5의 재질문으로 보지 않은 근거: P-5는 **임계값 3 기준의 진성 정의** 위에서 답한 것이고, PLAN이 축을 재정의하며 진성 집합 자체가 18 → 23으로 바뀌었다. 같은 질문이 아니라 **집합의 정의가 달라진 새 사안**이다
- 전파: TASK.md 6곳(범위 ④·완료기준·R-3 AC(c)·R-4 제목·AC(a)·AC(c)·AC(d)) / PLAN.md 20곳(결론·RPT-3·RPT-4·D-REQ-1 결정·§4.1 Phase 3·§3.2.3·§3.4.2·§5.1·Step 5·Step 14·총 Step 수 등)
- **Step 12b·13b·13c 신설(+3)** — PLAN 초안 추산은 +2였으나 잔여 4파일을 한 Step에 묶으면 `dispatch-process.md` §산출량 상한 3파일을 넘어 분할이 강제된다. 12b는 FE 영역이라 `opal-fe-agent`로 분리 배정
- `verify --clarification-check` = pass 재확인

## [GATE] TEST-SCENARIO Block B 보강 완료
- Block A 16건을 PLAN TS-001~TS-033과 전건 대조 — **14건 흡수 · 1건 수정 후 흡수(S-A7: 18건→23건) · 2건 고유 생존**
- 고유 생존 2건이 이 트랙의 실제 산출이다:
  - **TS-040**(L3/M3) — TS-021의 「첫 문장 동일」은 기계 검사이지 「역할이 여전히 전달되는가」의 증명이 아니다. 문자열 단언으로 판정 불가한 축이라 캡틴 수동 확인으로 남겼다
  - **TS-041**(L1) — PLAN TS-013/014는 오탐 문자열을, TS-016은 임계값 경계를 다루나 **필드 부재·빈 문자열** 경계는 어디에도 없었다. 감지기는 신규 코드라 이 경로가 처음 밟힌다
- 보강 완료 판정 3조건 충족: 마커 잔존 0건(백틱 제거 후 검사) · H-1~H-10 전건 전재 · §4 매핑 표 가설 ID·계층 전건 채움
- 행 처리: `test_scenario.test_scenario_md` done (row 8 사용자 확인 자동 승인)

## [GATE] 목표-커버 게이트 iteration 1 — Step 3 결정론 통과
- `test-tool scenario-coverage-check` → **exit 0 · `all_covered: true`** (requirements 5 / features 4 / hypotheses 10 / scenarios 28)
- Step 4 판단 루브릭은 `opal-evaluator-agent`(scenario-rubric)에 디스패치 — **Producer≠Evaluator 유지**. PM이 스스로 채점해 pass를 선언하지 않는다(tool-gated 규율 #1)

## [GATE] 목표-커버 게이트 iteration 1 — Step 4 판단 루브릭 **fail**
- 채점: `{goal:1, adoption:1, boundary:2}` 평균 **1.33** < 임계 1.5 → `verdict: rewrite`(반복상한·무진전 미해당)
- 미달이 ①·⑤에 몰렸다 — 잔존 측(구형 제거)은 3중 확인인데 **채택 측이 TS-005 단일 프록시**였고, 그 프록시가 정작 워커 진입 문서(`docs/CONVENTIONS.md`)를 대상에서 뺐다
- 게이트가 실제로 작동했다는 증거 2건:
  - **G-1** — 태스크 발원 동기(창문 재포화)가 시나리오 전문에 「창문」·「바이트」 0회. 발원을 검증하지 않는 시나리오 집합이 결정론 게이트는 통과했다
  - **G-2** — 「미확인 1건이라도 FAIL」이라 써 놓고 검사는 「채워져 있다」였다. 문구와 검사 강도의 괴리를 잡았다
- **G-7은 PM 프로세스 결함 지적이다** — Block A 원문을 보존하지 않아 흡수 14건 중 9건이 대조 불가였고, 평가자가 이를 가점하지 않고 **판정 불능**으로 처리했다. 흡수와 소멸이 사후 구별되지 않는 상태를 070 감사 불가능성과 같은 형태로 봤다

## [FIX] iteration 1 gaps 7건 전건 반영 — 선행 [GATE] fail 참조
| gap | 조치 |
|-----|------|
| G-1 | TS-025 신설 — 정리 전후 `@header` 총 바이트 감소 + 창문 내 종료 파일 수 비감소 실측 |
| G-2 | TS-022 격상 — 채움 검사 → `git cat-file -e` 해시 resolve · DONE.md 경로 실존 |
| G-3 | TS-008 신설 — AC(e)의 나머지 절반(교체 문구 존재·포인터 인용·원문 무모순) |
| G-4 | TS-005 대상 확대 — `docs/CONVENTIONS.md` 포함 3문서 포인터 체인 |
| G-5 | TS-042 신설 — 규정→작성→감지 end-to-end. §5 코드품질 #4를 게이트 대상 TS로 승격 |
| G-6 | TS-043 신설 — 한글 따옴표·역슬래시·개행 픽스처(P0 가설 H-5 직격) |
| G-7 | `TEST-SCENARIO-BLOCK-A.md` 보존(8,258 bytes) — 16시나리오 원문 요약표. 감사 기준선으로 고정 |
- 시나리오 28 → **32건**. 결정론 재검사 `all_covered: true` 유지
- `.scenario-gate-history.json`에 iteration 1 레코드 append(무진전 판정 기준선)
- iteration 2 재채점 디스패치 — 프롬프트에 **「반영을 액면가로 받지 마라」**·「G-7 보존본이 사후 재구성일 가능성도 따져라」를 명시했다. 내 자기 주장을 평가자가 검증 없이 통과시키면 게이트가 아니다

## [GATE] 목표-커버 게이트 iteration 2 — **pass**
- 채점: `{goal:2, adoption:2, boundary:2}` 평균 **2.0** ≥ 임계 1.5 → `verdict: pass`
- tool-gated 두 증거 확보: Step 3 `scenario-coverage-check` exit 0 · Step 4 evaluator `verdict: pass`. 이 둘로만 `test_scenario.scenario_gate` 행을 mark했다(산문 판단 mark 금지)
- 평가자가 G-7 보존본을 **액면가로 받지 않았다** — mtime이 게이트 1 보고서보다 110초 뒤이고 파일 자신이 「원문 그대로」와 「요약표」를 동시에 주장한다는 모순을 지적했다. 그럼에도 감사 도구로 채택한 근거가 설득력 있다: 재구성이라면 남길 이유가 없는 **결손을 스스로 노출**했고, S-A7이 「진성 18건」으로 적혀 있어 **현재 TASK.md(18→23 확정본)만 보고는 나올 수 없는 오차**를 담고 있다
- **흡수 9건 대조 결과 8건 진성 흡수 · 1건 소멸 확인** — S-A9 → TS-023이 커버 축소였다(N-3)

## [FIX] iteration 2 잔여 권고 처리 — pass 이후 additive 보강
| # | 권고 | 처리 |
|---|------|------|
| N-1 | TS-042 항진명제성 | 이월 — EXECUTE에서 픽스처를 신설 파일 자신과 분리 |
| N-2 | TS-008 「무모순」이 M1 단언 불가 | **즉시 반영** — 관측 가능한 대리 조건(구형 어구 재등장 0건)으로 축소 |
| N-3 | R-4 AC(e) 4필드 중 3필드 미검증 | **즉시 반영** — TS-026 신설, `git show HEAD` 파싱본과 `exports`·`module`·`layer`·`domain` 파일별 대조 |
| N-4 | §2.1·§2.2 신규 TS 데이터 미반영 | **즉시 반영** — 픽스처 4행·흐름 2행 추가 |
| N-5 | 선작성 원문 커밋 | 이월 — 커밋은 소유자 권한(`opal-harness.md` §1) |
- N-3을 이월하지 않은 이유: R-4 AC(e)가 「4필드 무변경」을 요구하는데 `counts.exports_not_found` 집계는 그중 1필드의 간접 신호일 뿐이다. 이월하면 AC 하나가 검증 없이 통과한다
- 세 반영은 **커버리지를 넓히기만 하므로 재게이트 대상이 아니다**. 결정론 재검사 `all_covered: true` 유지(시나리오 33건)

## [GATE] EXECUTE 진입 (agentic 대행 승인)
- `advance execute.implement` → row 11(TEST-SCENARIO 사용자 확인) `auto_approved`. 구현 금지 원칙의 「실행 허가」를 PM이 대행 판단(agentic §7)
- Phase 1 = Step 1·2·4·5 **병렬 4 워커 디스패치** + Step 3 **PM 직접**. 전 워커에 `Write` 차단을 사전 고지(heredoc/Edit 직행)

## [DECISION] Step 3 — CONVENTIONS.md 변경이력 채번을 v1.8.0 기준으로 잡았다
- 실측: 변경이력 표 마지막 행이 `v1.8.0`(2026-08-21) **뒤에** `v1.6.0`(2026-09-04, 106 기재)으로 역행해 있다 — 106의 버전 표기 오류
- 조치: 실제 최신인 v1.8.0을 기준으로 **v1.9.0** 채번하고, 그 사유를 변경이력 행 본문에 남겼다. 106 행 자체는 건드리지 않았다(과거 기록 개찬 금지 — 이번 태스크 범위 밖)

## [ERROR] TS-006 메타-순환 오탐 — PM이 자기 손으로 만들었다
- Step 3 직후 TS-006 grep을 돌리니 구형 어구가 **2건** 남았다
  - ① 내가 방금 쓴 **v1.9.0 변경이력 행 자신** — 「'헤더 내 변경이력 라인' 어구 제거」라고 쓰면서 그 어구를 인용했다. 「제거했다」고 선언하는 문장이 제거 대상을 포함해 문서가 **스스로 영구 FAIL**하는 구조다
  - ② `docs/backup/CONVENTIONS_202608111324.md` — 2026-08-11 동결 스냅샷
- 조치: ①은 어구를 인용하지 않고 「구형 어구」로 지칭하도록 문장 재작성. ②는 TS-006 제외 경로에 `docs/backup/` 명시(아카이브를 고치면 아카이브가 아니다)
- **선례가 이미 있었다** — `state_tool.py:2010,2025`가 034에서 마커 리터럴 메타-순환을 인라인 백틱 제거 전처리로 해소했고, `test-scenario-guide.md` Step 1이 그 사례를 규칙으로 적어 뒀다. 규칙을 읽고도 같은 형태를 만들었다
- 재검증: 제외 4종(`.git`·`tasks/`·`.opal-worktrees/`·`docs/backup/`) 적용 시 **0건**

## [GATE] Step 1 · Step 2 완료 검토
- **Step 1**(`header-standard.md`) Pass — 최상위 절 8개 불변(§5·§6·§7 번호 불변, H-8 회피), §2 필드 표·§4.1 exports 21행 **삭제 라인 0**, 전체 +22/-1(삭제 1줄은 승인된 §4 헤딩 교체). TS-001·002·003·004·007 전건 PASS 자가 보고
- **Step 2**(`header-rules.md`) Pass — 기존 표 4행 diff 0줄, 포인터 인용 확인, **원칙 원문 미복제**(SSOT 1곳 + 포인터 2곳 구조 유지)
- 단, 두 워커의 자가 보고는 PM Gate에서 재현 검증한다 — EXECUTE 완료 후 일괄 대조 예정

## [GATE] Phase 1 완료 — Step 1·2·3·4·5 전건 Pass
- **Step 5**(`HISTORY-EVIDENCE.md`, 7,933 bytes): 23파일 / 태스크번호 86행 / 확인 86 · **보존 대상 0**
  - PM 독립 재현: 인용 커밋 해시 **42개 전건 `git cat-file -e` resolve 성공**, 데이터 86행 중 「보존 대상」 0행. 워커가 근거를 지어내지 않았음이 실측으로 확인됐다 — R-4 AC(c) 전제 성립
  - 워커가 매칭 실패 2건을 은폐하지 않고 우회 근거로 처리한 점이 좋다(`brain_tool.py` 035 = 태스크 폴더 날짜 ↔ 커밋 날짜 대조 / `test_stats.py` 101 = DONE.md 실존)
- **Step 4**(`test-header-history.js`, 30,455 bytes): PM 재실행 실측 **tests 16 / pass 2 / fail 14**
  - 신 계약 14건 전량 FAIL(RED) · baseline 2건(TS-017 counts 9키 · TS-018 VERSION) PASS — RED-first 분포 정확히 일치
  - 자기 `@header` `description` 3자리 토큰 **0건** 확인 — 규정을 만드는 파일이 규정을 지킨다
  - TS-042 항진명제를 별도 픽스처(`Compliant.js`)로 회피 — 게이트 iteration 2 권고 N-1을 워커가 실제로 반영했다
- **Step 1·2 무변경 보증 PM 독립 검증**: `git diff -U0` 삭제 라인 전수 — `header-standard.md` 1줄(승인된 `## 4` 헤딩 교체)·`header-rules.md` **0줄**
- `verify --red-check` → `red_evidence_missing: pass` · `mock_in_scenario: pass` · `evidence_missing: pass`. **GREEN 진입 조건 충족**

## [ERROR] Step 6 워커의 회귀 오진 — 「환경 artifact」로 분류된 것이 실제로는 이번 변경의 회귀였다
- 워커 보고: 「순수 baseline `tests 344, pass 336, fail 8` — 기존 8건은 sparse-checkout worktree 환경 artifact, 태스크 107과 무관. stash 비교로 확인」
- PM 재현 실측: worktree 전체 스위트 `tests 360 / pass 356 / **fail 4**`. 숫자도 다르고 성격도 다르다
- 실패 4건: **TS-057**(`test-regression.js:924`) · **S-19**(`test-shard.js:978`) · **TS-080**(`test-shard-policy.js:1394`) · **TS-062**(`test-regression.js:599`)
- **허브에서는 344 passed / 0 failed**(PM이 ANALYSIS 단계에서 실측). 환경 문제라면 허브에서도 나야 한다 — 환경이 아니라 이번 변경이 원인이다
- 인과는 단일 뿌리다: 신설 `test-header-history.js`에 `task`·`scenarios` 필드가 없어 **TS-057이 실패** → 스위트를 중첩 실행하는 **S-19·TS-080·TS-062가 연쇄 실패**. 추가로 TS-080은 `OTHER_TEST_FILES.length === 11`로 **개수를 정확히 핀**해 12가 되면 그 자체로 실패한다
- **이 오진이 통과했다면**: R-5 AC(a)(c)가 깨진 채 TEST 단계에 넘어가고, TEST 워커가 같은 4건을 다시 만나 원인을 재추적했을 것이다. 「환경 탓」은 검증 가능한 주장이 아니므로 PM Gate에서 반드시 재현해야 한다는 사례다
- **106 ADD-1과 같은 계열**: TASK.md §제약 ⑥이 「`VERSION`을 테스트 2건이 핀했으므로 상향 시 단언 갱신 동반」을 경고했는데, **테스트 파일 개수 핀**은 아무도 예상하지 못했다. 「신설 자산이 기존 단언을 깬다」는 같은 실패 모드의 다른 얼굴이다

## [DECISION] Step 6b를 PLAN에 사후 편입 (총 18 → 19 Step)
- PM Gate에서 발견한 필수 수정이 `test-regression.js`·`test-shard-policy.js` 2파일을 건드리는데, 둘 다 PLAN의 어느 Step에도 없다 — 워커 Guards(「PLAN.md에 없는 파일 수정 금지」)에 걸린다
- 조치: PLAN §4.2에 **Step 6b** 신설 + §4.1 Phase 2에 편입 + 총 Step 수 갱신. 발견 경위와 오진 사실을 Step 본문에 남겼다
- **[MUST] 단언 약화 금지를 프롬프트에 명시**: TS-080의 `=== 11`을 `>= 11`로 바꾸면 다음 신설 파일이 무성 통과한다. 개수 핀이 그 단언의 검증력이므로 **12로 갱신**하되 등호를 유지하도록 지시했다
- 허용 태스크 번호 배열에 `'107'` 추가는 **완화가 아니라 규약 집행**이다 — `test-regression.js:936` 주석이 「허용 태스크 번호는 테스트 자산을 신설한 태스크만 누적한다」로 누적을 이미 규약화했고, 107은 실제로 테스트 자산을 신설했다
- 자기 검증 위험(PM이 자기 작업을 판정하는 테스트를 직접 손보는 것)을 피하려 **PM 직접 수정하지 않고 워커에 디스패치**했다

## [ERROR] `changelog` 필드 발견 — 이번 태스크 목표의 최대 잔존
- 발견 경위: Step 12b 워커가 완료 보고에서 「`changelog` 필드 무변경」을 언급 → PM이 전 필드 사용 빈도를 전수 집계
- 실측: **28파일 / 81엔트리**. 내용은 날짜+태스크 태그가 붙은 **완전한 변경 이력**(예: `dashboard/backend/config.py` 5엔트리 — `"2026-07-14 T061 범위 축소: save_project_local 제거…"`)
- **`header-standard.md` §2 필드 정의에 없는 필드다** — 표준에 정의되지 않은 채 관행으로 28파일에 퍼졌다
- **왜 지금까지 안 잡혔는가**: ① 원칙 문장은 「어느 필드에도」라고 쓰면서 **적용 범위를 5필드로 한정**해 `changelog`가 빠져나갔다 ② 감지기는 `description`·`note`만 본다. **규정과 도구가 같은 구멍을 공유**했다
- 파급: 이대로 닫으면 「이력은 @header에 남기지 않는다」를 신설하면서 **전용 이력 필드 28건을 그대로 둔 채** 태스크가 종료된다. 3층 일관 적용이라는 목표 진술이 성립하지 않는다

## [DECISION] `changelog` 28건 전건 편입 (캡틴 3차 확정)
- 캡틴 선택: 「28건 전건 편입」 — 규정·감지·자산 3층 모두
- 반려된 대안: 규정+감지만 하고 자산은 별건 / 이월 기록만 — 둘 다 규정과 자산의 괴리를 남긴다
- 설계 3건:
  1. **원칙 적용 범위 확장** — 「워커 기입 5필드」 → **「`@header` JSON 블록 전체」**. `header-standard.md` §2에 「이력 전용 필드를 신설하지 않는다 — `changelog`·`history`·`revisions` 이름 불문」 명문화(R-2 AC(f))
  2. **감지 축 추가** — `changelog` 필드 **존재 자체**가 위반이다. **[MUST] 임계값 판정 미적용** — `description`·`note`는 「단발 인용 vs 누적」을 가려야 하지만 `changelog`는 필드 이름이 곧 이력 선언이라 엔트리 1개도 위반이다(R-3 AC(e))
  3. **자산 정리** — 23 ∪ 28 = **43파일**. 겹치는 8건은 담당 Step에 흡수, 신규 20건은 Step 16~22, `AppShell.tsx`는 Step 12b 후속으로 Step 23
- 이력 소실 방지는 **Step 5와 동일 강도**를 적용한다(Step 5b) — 81엔트리 각각 해시 resolve·경로 실존 확인
- PLAN Step 수 19 → **30**. TASK.md 범위·완료기준·R-2·R-3·R-4 갱신, `verify --clarification-check` = pass 재확인

## [GATE] Phase 3 배치 A — Step 10 · 12b · 13c Pass
- **Step 10**: 3파일 430→189 / 179→83 / 414→391자. `code-map-hook.js`는 **태그만 떼고 문장 전체 보존**(조기 이탈 10단 계약 등 전부 현재 유효) — 「짧게 만들기」가 아니라 「지금도 참인가」 판정이 작동했다
- **Step 12b**: `AppShell.tsx` 300→240자. 워커가 **실제 컴포넌트 코드를 재확인**하고(`NAV_ITEMS`:100행 · `AlertDialog`:181~204행 · `brainDirty`:121·147행) 보존한 2계약이 지금도 참임을 검증했다 — FE 워커 배정 근거가 실현됐다
- **Step 13c**: 199→130 / 174→160자. TS-057 검사 대상 파일이라 `task`·`scenarios`·`layer` 무변경 확인, 전체 스위트 360/360 유지
- 3 Step 모두 `header_history` 잔존 0건
