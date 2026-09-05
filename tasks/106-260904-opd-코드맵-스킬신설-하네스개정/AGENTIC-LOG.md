# AGENTIC-LOG: @header 자산 스킬 신설 + 하네스 갱신·소비 절차 편입

> 모드: agentic | 시작: 사용법: node date.js [format] | 스킬: //opd

## [DECISION] 스킬명·약어 확정
- 확정: `opal-code-map-builder` / alias `opcmb`
- 근거: 캡틴 지시("opcmb 로 갈게"). 접미사 `-builder`는 `wireframe-builder`(wfb) 선례(`docs/CONVENTIONS.md` §약어 (Alias))
- 동반 결정: 스킬 범위를 `manifest` 구축 중심으로 확정. `inline`은 설정 확정 후 종료 분기(`code-scan missing` 안내 반환)
- 반영: TASK.md §확정된 설계 방향 + §명확화 결과(범위) + R-1 어디에·AC (b)(d)

## [DECISION] 하네스 모드 전환
- 전환: semi-agentic → agentic
- 근거: 캡틴 지시(`//opd --agentic`)
- 집행: `state-tool init --mode agentic --force --note` (16행 재초기화). 재초기화 시점의 완료 행은 TASK 작업 행 1건뿐이어서 손실 없음
- 효과: PLAN까지의 사용자 검토를 PM 대행으로 대체. CLOSE 진입 게이트는 유지(`agentic_close_gate_requires_user`)

## [GATE] TASK 단계
- 판정: Pass
- 확인 항목: (1) TASK.md 존재·140행 (2) 명확화 4요소 잠김 — `state-tool verify --clarification-check` = `pass` (3) 요구사항 R-1~R-6 전건에 Pass/Fail 판정 가능 AC 기재 (4) 관련 문서 D-1~D-12 인용 형식이 `citation-rules.md` §2.1 준수
- 트랙 강등 판정(`track-routing.md` §1): A1 미충족(미확정 2건) · A3 미충족(신규 스킬 1종) · A4 미충족(R-4 AC가 실행 출력 관찰 요구) → 4축 전건 미충족으로 `opd` 유지

## [GATE] ANALYSIS 단계
- 판정: **Pass** (강화 검토 6항 전건 충족)
- 워커: `opal-task-agent` (op-dev-analysis, model standard) · 소요 6분 · 산출물 174행
- PM 독립 실측 4건 — 워커 주장과 전건 일치:
  1. `state-tool verify --evidence-check` 플래그 **실존** (`verify --help` 출력) → Q2 1순위 후보의 재사용 근거 성립
  2. `claude-hooks.json` matcher = PostToolUse(`Bash`, `Edit|Write|MultiEdit`) + SubagentStop + Stop → **PreToolUse 0건·Task matcher 0건** 확인
  3. `pipeline.json` task_steps = opd 16 / opds 11 / opp 9 확인
  4. `code-map-hook.js:115-132` 조기 이탈 ⑤(모드 게이트)→⑥(자산 존재 게이트) 순서 계약 확인 — 소스 주석에 "[MUST] 이 게이트는 ⑥ code-map 로딩보다 반드시 위에 있어야 한다" 명기
- PM 보완 2건 (결론 불변 — Gate Fail 사유 아님, PLAN 입력으로 이관):
  - **누락**: `SubagentStop` hook 슬롯이 실재한다(현재 용도는 osascript 알림 1줄). 워커의 Q2 후보 열거에서 빠졌다. 사전 차단은 불가하나 **사후 검증 경로**로는 성립하므로 PLAN이 4번째 후보로 검토해야 한다
  - **부정확**: 변경이력 마커 형태가 문서마다 다르다 — `## 변경이력`(5문서) vs `변경이력:`(`header-rules.md:149`). Q5 결론(행 추가)은 불변이나 PLAN은 문서별 기존 형태를 따라야 한다
- 미승인 폴백 판정: 워커가 Write 도구 오탐(report file 차단)으로 Bash heredoc으로 전환 — 산출물 동일, **PM 사후 승인**(경미, 방식 이탈이 결과에 영향 없음)

## [DECISION] 목표계열 선작성 미착수
- 결정: opd STEP 3 병렬 트랙(TEST-SCENARIO Block A 선작성)을 착수하지 않는다
- 근거: `opal-pilot-dev/SKILL.md` STEP 3 — 선작성은 opt-in이며 미착수 시 STEP 3.5에서 Block A·B를 연속 수행해 결과가 동등하다

## [GATE] PLAN 단계
- 판정: **Pass** (opd STEP 3 검증 4항 + agentic 강화 6항 전건 충족)
- 워커: `opal-plan-agent` (op-dev-plan, model advanced) · 소요 19분 · 산출물 1102행 (Multi-Feature 모드)
- PM 독립 실측 4건 — 워커 신규 주장과 전건 일치:
  1. `schema/state.schema.json` + `pipeline-spec.schema.json` 양쪽 `gate`가 `additionalProperties: false`, props = `artifacts`·`checklist` 2종 → DEC-2 근거(checklist 확장은 스키마 무변경) 성립
  2. `CONVENTIONS.md` 약어 표 27종 vs 레지스트리 29종 — 결손 = `opgr`·`opeli5` → H-9 정확
  3. `opal/skills/` 실측 44개 vs `docs/PROJECT.md` "42종" → H-12 드리프트 2건 정확
  4. `install-mac.sh:1236` 글롭 루프(`for skill_dir in "$opal_dir/skills"/*/`) + `:1235` `find|wc -l` 동적 계수 → 하드코딩 스킬명 0건, 스크립트 수정 불요 확인
- 게이트 순서 설계 검증: 게이트 ①이 `stage == "EXECUTE"` **AND 자기 stage 첫 행**으로 한정되므로, 이 태스크 자신은 EXECUTE 진입을 이미 지난 시점에 배포되어도 신설 훅이 재발동하지 않는다(자기 차단 없음). H-8이 다루지 않은 축을 PM이 확인했다.
- 미승인 폴백: 0건
- PM 판정 유보 사항 → 캡틴 에스컬레이션(agentic §3 에스컬레이션 책임): TASK.md 범위 밖 인접 수정 2건(Step 3 약어 표 결손 2건 보정 / Step 13 스킬 수 셀 드리프트 2건 보정). PRINCIPLES §3 Surgical Changes 관점에서 스코프 확장이나, H-9·H-12에 따르면 보정 없이 신규 항목만 더하면 총계가 더 틀어진다
- **PLAN 사용자 확인 행은 자동 승인하지 않는다** — agentic 자동 승인 자격은 있으나, 이 태스크가 모든 프로젝트 PM의 디스패치 전 절차와 EXECUTE 진입 게이트를 바꾸므로 설계 확정에 소유자 판단을 요청한다

## [GATE] TEST-SCENARIO 목표-커버 게이트 (2 라운드)
- 작성 주체: **PM 직접**(워커 미디스패치) — self-confirming 방지 규정상 PLAN 워커와 다른 작성자여야 한다
- RED-first 트랙 **적용** — `state_tool.py` 게이트 판정 로직은 판정 결과가 곧 통과 근거가 되는 self-confirming 위험 영역(`red-first.md` §1.5 「모호하면 RED-first 기본」). 대상 S-9·S-10
- **iteration 1**: 결정론 `all_covered:true`(R6/F6/H12/S22, exit 0) → Evaluator `{goal:1, adoption:2, boundary:1}` avg **1.33** → `verdict: fail`. 종료조건 판정: 수렴✗ / 반복상한(3) 미초과 / 직전 이력 없음 → **rewrite**
  - PM 자체 점검으로 사전 보강 1건: R-4가 교체형 목표인데 구형 잔존0(「PM이 판정한다」 문면 0건) 검증 시나리오가 없어 **S-22 신설**
  - 평가자 최대 지적: S-11이 게이트 ⑥에 닿지 않아 **`[MUST]` 순서 계약이 깨진 구현도 전건 Pass 가능**. goal 시나리오 2건이 모두 `R-1`에만 매핑(생성 국면 편중)
- **재작성**: S-23(갱신 국면 런타임 탐지)·S-24(순서 계약 판별 조합)·S-25(스킵 분기 3종 + 플래그 상호배타) 신설 → S 25건, goal 3 / adoption 1 / boundary 5
- **iteration 2**: 결정론 exit 0 → Evaluator `{goal:1, adoption:2, boundary:2}` avg **1.67** → **`verdict: pass`** (각 축 ≥1 AND 평균 ≥1.5 충족)
- 게이트 행 mark 근거 = tool-gated 두 증거(결정론 exit 0 + 평가자 pass). 산문 판단 미사용

## [DECISION] 요구사항 문면 교정 — R-2 AC(c) (PLAN 승인 후 변경)
- 계기: iteration 2 평가자가 잔여 gap을 **PM 판단 사항으로 명시 에스컬레이션** — "(d) 행이 `newly_uncovered`만 인용하는데 실제 차단 사유가 `no_entry`라면 F-002 문면 자체의 정확성 신호"
- PM 독립 실측(`code-scan.js` 5지점) — 지적 전건 확인:
  - `:3207` `const sub = managedByManifest ? 'no_entry' : classifyUncovered(...)` — manifest 관리 하위 누락은 **git 무관하게 `no_entry`**
  - `:3427` `counts.newly_uncovered`는 `sub === 'newly_uncovered'`만 계상 → `no_entry` 전용 카운터 **없음**(값 0)
  - `:3434-3436` 차단 필터는 `pre_existing`·`manifest_oversize`만 제외 → **`no_entry`는 차단**(exit 2)
  - `:1085` `!isGitUsable` → `pre_existing`(비차단) / `:1025-1035` `isGitUsable`은 work-tree **AND** `HEAD` 요구 → 커밋 없는 트리는 탐지 미발동
- 교정 내용: R-2 AC(c)를 "탐지 조건 명시"에서 **모드별 차단 사유 2종 명시**(`inline`=`newly_uncovered` ≥1 / `manifest` 관리 하위=`sub=="no_entry"`)로 좁혀 정확화. PLAN Step 7 완료 기준 (d)·TS-006·S-6 기대 결과·S-23 fixture(2갈래 + git 커밋 사전조건)를 함께 교정
- 판정: **AC를 넓힌 것이 아니라 사실관계에 맞게 정확화**한 것이며, `header-rules.md` §갱신 시점 (b) 원문("또는 다른 위반 존재")은 이미 두 사유를 포괄하므로 하네스 SSOT와 모순 없음. 교정 후 결정론 재검증 통과(`all_covered:true`, `verify` mock 0건)
- 게이트 재호출(iteration 3)은 하지 않았다 — 교정이 평가자가 지목한 gap 자체를 해소하며 판단 3축을 강화만 하고, 결정론 축은 재실행으로 통과 확인했다
- **캡틴 보고 대상**: 승인된 PLAN의 AC 1건 문면 변경

## [EXECUTE] 배치 1 — Step 1 · 4 · 7 병렬 디스패치
- 근거: `harness/parallel-execution.md` §7 "병렬 가능한 작업은 무조건 병렬로, 의존관계 있는 작업만 순차로". Step 1·4·7은 선행 의존 0건
- 워커별 범위 격리로 동일 파일 동시 편집 충돌 원천 배제 — Step 1=SKILL.md만 / Step 4=`state_tool.py`만 / Step 7=`header-rules.md`만. 전 워커에 `~/.opal/` 배포본 편집 금지 `[MUST]` 주입
- Step 4 워커에 **`_run_clarification_hook` 배치 답습 금지**를 `[MUST]`로 명시 — 그 함수가 `auto_pass` 거부를 graceful skip 앞에 두므로 복사 시 H-7(P0)이 재생산된다

## [GATE] Step 7 — `header-rules.md` §갱신 시점 (4단)
- 판정: **Pass** · 워커 `opal-task-agent`(advanced) · 소요 4분
- PM 독립 실측: `git diff --numstat` = **+25/-2**, 삭제 2줄은 표 제목·도입문뿐. `^-\| \((a|b|c)\)` 매칭 **0건** → (a)(b)(c) 원문 보존 증명
- (d) 행이 DEC-4대로 `git diff --name-only HEAD`(+untracked) → 기존 `validate --changed` 재사용 — **신규 도구 0건**
- PM 교정 문면 반영 확인: 모드별 차단 사유 2종 표(`inline`=`newly_uncovered` ≥1 / `manifest` 관리 하위=`sub=="no_entry"`) + **`[MUST] counts.newly_uncovered 단독 인용은 금지`** 1줄
- 폴백 3종에 `code-map-hook.js:121-124` 순서 계약 인용 + "판정보다 앞에 평가한다" `[MUST]`
- DEC-6 준수: `## 변경이력` 헤딩 **0건**, 기존 `변경이력:` 인라인형 유지(`:171`), v1.9 행 1건

## [GATE] Step 1 — `opcmb` SKILL.md 신설
- 판정: **Pass** · 워커 `opal-task-agent`(advanced) · 소요 5분 · 229행
- 완료 기준 (a)~(e) 전건 충족. PM 실측: frontmatter 5필드 + `domain: metadata`, 모드 판별 4분기가 "최초 일치 행" 평가로 명문화
- 설계 초과 없음 확인 — `## 경계 — 신설하지 않는 것` 절이 병합 경로·자동 폴백·스코프별 재선언 3종을 `header-standard.md` §7 원문 인용과 함께 **금지 표**로 명시(R-1 AC(d)를 예상보다 강하게 충족)
- 워커 보고 2건 PM 판정: ① 신규 `.md`에 `@header` 1블록 추가 = **정당**(§갱신 시점 (a) 의무. 추가 후 커버리지 100%·위반 0·exit 0. 기존 45 SKILL.md 미보유는 `pre_existing` 비차단이라 소급은 범위 밖) ② PLAN.md 체크박스 미갱신 = **정당한 판단**(동시 편집 충돌 회피 — PM 일괄 갱신)

## [GATE] Step 2 — 레지스트리 `opcmb` 등록
- 판정: **Pass** · 워커 `opal-task-agent`(standard) · 소요 1분
- PM 독립 실측: `version` 3.14.0 · `updated_at` 2026-09-04 · **alias 30종 · 중복 0건** · `opcmb` 등재 확인 · JSON 파싱 성공
- 삭제 라인 전수 = 2줄(`version`·`updated_at`)뿐 → 기존 29종 항목 무변경 증명

## [EXECUTE] Step 3 — `CONVENTIONS.md` 약어 표 사본 갱신 (PM 직접)
- 실행: PM 직접(PLAN §4.2 Step 3 `agent: PM 직접`)
- 변경: 「프레임워크 운영」 표에 `opcmb` 1행 + **실측 결손 2건 보정**(`opgr`/opal-grill · `opeli5`/opal-eli5) + 도입문 총계 27종→**30종**. 변경이력 v1.6.0 행 1건
- 결손 보정 근거: 본 표가 스스로 "레지스트리의 사본"임을 선언하므로 사본 정합 회복은 규정 집행이다(H-9). 캡틴이 PLAN 원안 승인 시 인접 수정 2건을 포함해 승인
- PM 검증: 표 30종 ↔ 레지스트리 30종 **양방향 차집합 공집합**. `git diff --numstat` = +5/-1, 삭제 1줄은 도입문 총계뿐 → 약어 표 외 절 무변경

## [EXECUTE] 배치 2 — Step 2 · 8+9 병렬 (의존 해소)
- Step 8+9는 **동일 파일**(`opal-pm.md`)이라 한 디스패치에 묶어 순차 편집 — `pm/dispatch-process.md` Step 6 산출량 상한(단일 디스패치 3파일 초과 금지) 준수
- Step 8 워커에 "Step 7이 실제로 쓴 (d) 행 문면을 먼저 Read해 확인한 뒤 인용하라"를 명시 — 추측 인용 차단

## [GATE] Step 8+9 — `opal-pm.md` §12 각주 + §13 2단 표
- 판정: **Pass** · 워커 `opal-task-agent`(advanced) · 소요 2분
- PM 독립 실측: `git diff --numstat` = **+15/-0**, 삭제 라인 전수 **0건** → 「미적용」 5행·`:237` 오버라이드 문단 원문 보존 증명
- DEC-3 충족: 각주가 "Gate ❌ 미적용"을 파이프라인 게이트 3종(QA/State/PM) 한정으로 못 박고, @header 갱신 검증은 `state.json` 미경유·변경 파일 목록이라는 객관 입력만으로 도구가 판정하는 **별개 축**임을 명문화 → 자기모순 소멸(H-1 대응)
- §13 2단 표의 2차 전환 조건이 실제 분기명·기준값까지 인용("1차 후보 확정 후" / 빈 결과 폴백 ① 매칭 0건 · ② `coverage.percent` 30% 미만)
- 축 분리 정확도: 오버라이드 = 1차 자체를 면제하는 **소유자 권한 행사**(인용 의무 판정 대상 아님, `citation-rules.md` §9 (f)) / 2차 전환 = 1차 수행 후 **PM 자율 절차**

## [GATE] Step 10 — `dispatch-process.md` 2차 전환 포인터
- 판정: **Pass** · 워커 `opal-task-agent`(standard) · 소요 1분
- PM 독립 실측: `git diff --numstat` = **+2/-0**, 삭제 0건 → `:130` 무조건 호출·`:134` 직행 금지 원문 보존
- SSOT 단일성 유지: 불릿이 "전환 규정의 원문은 `opal-pm.md` §13 「2단 소비 절차」가 소유한다"로 포인터만 두고 표·조건 복제 0건 — PRINCIPLES §2 "Remove a duplicated existing pattern before introducing a new one." 준수

## [EXECUTE] 배치 4 — Step 5 · 6 · 15 병렬
- Step 15는 PM이 PLAN 결손을 발견해 `add-row`로 추가한 Step이다 — Step 4의 `ERROR_CODES` 45→46이 종수 단언 6건을 깨뜨렸고(PM 실측 `374 passed, 6 failed`), 098이 동일 문제를 H-10 「테스트 선갱신」으로 흡수한 선례가 있으나 106 PLAN에는 대응 Step이 없었다. Step 4 Guards가 테스트·README를 금지 대상으로 뒀으므로 그 워커는 고칠 수 없었다 — **격리는 정상 작동했고 PLAN의 Step 분해가 부족했다**

## [GATE] Step 4 — `state_tool.py` 인용 검증 라우터 + EXECUTE 진입 훅
- 판정: **Pass** · 워커 `opal-be-agent`(advanced) · 소요 11분 · `+233/-5`
- PM 독립 실측 — 게이트 배치 소스 확인: ①`:2620` ②`:2626` ③`:2630` ④`:2647` ⑤`:2652` **⑥`:2659`(③④⑤ 뒤)** ⑦`:2664`. 주석에 `[MUST] ③④⑤ 뒤` 명기
- H-7(P0) 실행 방어 확인: 문서 전용 PLAN + `--auto-pass` → **정상 통과(exit 0)**. ⑥을 앞에 뒀다면 거부가 났을 조합
- `reason` 3값 도메인 닫힘 4경로 전건 재현. 훅 거부 전후 `state.json` md5 동일 → 영속 무변경. `schema/*.json` 무변경
- 워커 자율 발견 1건(PM 승인): `depends_on`(Step 의존 필드)이 `depends`로 오인되면 **전 PLAN이 무조건 통과해 게이트가 무력화**됨을 감지하고 `(?<![\w-])…(?![\w-])` 토큰 경계 적용. `depends_on`만 있는 PLAN이 `unmet`으로 떨어짐을 실측
- 선존 결함 보고(이 태스크 회귀 아님): `code-scan.js:39` `HEADER_READ_BYTES = 8192` < `state_tool.py` @header 블록 약 11.9KB → 탐지 불가·`coverage 0%`. HEAD 시점 동일 확인. `validate` exit 0(비차단)

## [GATE] Step 5 — 3 `pipeline.json` checklist 확장
- 판정: **Pass** · 워커 `opal-task-agent`(standard) · 소요 1분
- PM 독립 실측(`git show HEAD:` 스냅샷 대조): `task_steps` **16/11/9 불변** · key 집합 **동일** · `checklist` 4→5/4→5/3→4 · `gate` 필드 `artifacts`·`checklist` **2종 불변** · **기존 checklist 접두 보존 True** · `spec-validate` × 3 **violations 0건**
- DEC-2 판단 검증됨 — `gate` 필드 불변이라 `additionalProperties: false` 스키마 2파일 무접촉. **R-6 AC(a) 원문을 재정의 없이 충족**

## [GATE] Step 6 — `pm-review-gate.md` 항목 14 집행 승격
- 판정: **Pass** · 워커 `opal-task-agent`(advanced) · 소요 3분 · `+13/-3`
- PM 독립 실측: 항목 14 범위(`:112~128`) 자기판정 패턴 grep **0건** → S-22 「구형 잔존 0」 사전 충족. `git diff -U0` 헌크 **2개뿐**(항목 14 내부 + 변경이력) → 항목 1~13·자가 진단 절 무변경 구조 증명
- 처치 계약 소실 없음 — 구형 "재디스патch 1회"가 `unmet`(exit 1) 결과 처치로 이관. 기능을 지우지 않고 판정 주체만 교체
- 자기판정 금지를 **부정문으로 명문화**(`:118` "인용 여부를 눈으로 읽어 스스로 판단하지 않는다" + 헌법 §Core Stance 원문) + "도구는 Pass 조건 토큰 집합을 그대로 집행한다(별도 판정 기준 신설 금지)"
- 스킵 조건 3값이 `state_tool.py` `reason` 도메인과 **3/3 일치**. `header-rules.md` (d) 3번째 항목만 갈리는 것은 판정 대상 차이(헤더 커버리지 vs PLAN 인용)에 따른 **도메인 분화**이며 모순 아님
- PM 정정 1건: 워커 보고 "산출물이 `.md`라 code-scan 적용 확장자 0건"은 **부정확**(이 레포 `extensions`에 `.md` 포함, 실측 True). 다만 `@header` 미보유 레거시라 `pre_existing` 비차단 exit 0 — 결론 무영향

## [GATE] Step 15 — `ERROR_CODES` 종수 단언 6건 + README 카탈로그
- 판정: **Pass** · 워커 `opal-be-agent`(advanced) · 소요 10분
- PM 독립 실측: `pytest` → **379 passed, 3 skipped, 98 subtests passed, 0 failed** / `state_tool.py` numstat `233 5` **불변**(Step 4 산출물 보존) / README 표 46행 ↔ `ERROR_CODES` 46종 **양방향 차집합 공집합**
- 워커가 프롬프트 예상값(380)과 실측(379)의 차이를 정확히 규명 — 실패 6건 중 1건이 테스트가 아니라 **subtest**(`test_r11_invariants_S40`의 `error_codes_key_set_untouched`)여서 회복이 `passed` 374→379(5건) + `subtests passed` 97→98(1건)로 나뉜다
- 단언 무력화 0건 확인 — 테스트 메서드 수 HEAD 382 = 현재 382(삭제·신설 0건), `skip`·`assertTrue(True)` 0건
- #4 subcheck는 리터럴 갱신이 불가한 **이동 기준점**(`git show HEAD:`)이라 판정식을 「삭제 0건 고정 + 추가는 태스크 선언 종목 한정」으로 분해 — 미선언 추가·임의 삭제를 여전히 FAIL로 잡는다(무력화 아님)

## [EXECUTE] Step 13 — docs 스킬 수 셀 정합 (PM 직접)
- 실측 `find opal/skills -mindepth 1 -maxdepth 1 -type d | wc -l` = **45**
- 갱신 4셀: `docs/PROJECT.md:37` 42종→45종 / `docs/ARCHITECTURE.md:77`·`:217`·`:425` 42개→45개. 변경이력 2문서 각 1행
- H-12 확인: 신설 반영 전에도 이미 **문서 42 vs 실측 44** 드리프트 2건이었다 — `+1`만 하면 43이 되어 오차가 커진다

## [EXECUTE] Step 16 — README `verify --code-scan-citation-check` 절 신설 (PM 직접, PLAN 결손 보강 2)
- 계기: Step 15 워커 보고 — 신규 플래그를 산문으로 설명하는 절이 어느 Step에도 배정되지 않았다
- PM 판정: **정당한 결손 지적**. README `:275`에 `### verify` 절이 실재하며 다른 플래그 4종을 열거하는 구조인데 신규 플래그만 빠졌다. 선례 098 v1.8이 카탈로그 정정과 함께 신규 절을 추가했다 — 인접 개선이 아니라 **기존 절의 결손 보완**
- 산출: `#### --code-scan-citation-check` 절 `:369` 신설(판정 대상·반환 3값·`reason` 3값·순서 계약·집행 지점 2곳·상호배타·영속 무변경·SSOT 포인터), 도입문 분기 열거 정정, 변경이력 v1.14. numstat `+33/-5`
- 회귀: `pytest -k "ErrorCodes or R11Invariants"` → **27 passed** (README 종수 대조 테스트 포함)

## [BLOCKED→에스컬레이션] Step 14 — install 재배포
- 사유: `scripts/install-mac.sh`는 대화형 메뉴(`:159` `read -rp "선택 (0-5)"`)이고, 비대화형 경로(`OPAL_AUTO_INSTALL=1` 또는 stdin 비-tty)는 **메뉴 [3] 전체 설치를 자동 실행**한다(`:2192-2199`) — OPAL 자산 배포에 더해 **MCP 5종 config_merge · dashboard npm 빌드 · Console 서버 자동 기동**이 동반된다
- MCP 스킵 플래그 부재 실측: `OPAL_*` 환경변수 19종 전수에 해당 항목 없음
- PM 판정: Step 14가 필요한 것은 **OPAL 자산 배포(메뉴 [1])** 뿐이다. 태스크 범위 밖 부수효과(타 플랫폼 MCP 설정 변경·서버 기동)를 PM 자율로 실행하지 않고 소유자에게 올린다 — agentic §3 에스컬레이션 책임
- 영향: Step 11·12가 H-11(배포본 실측 필수)로 Step 14에 묶여 있어 함께 대기한다

## [EXECUTE] Step 14 — install 재배포 (캡틴 실행)
- 캡틴이 직접 배포. PM 실측으로 완료 기준 전건 확인:
  1. `~/.opal/skills/opal-code-map-builder/SKILL.md` **존재**
  2. 배포본 레지스트리 `version 3.14.0` · alias **30종** · `opcmb` 등재
  3. 배포본 `state-tool run.sh verify --help`가 **`--code-scan-citation-check` 인식**
  4. 배포본 SKILL.md `## 변경이력` **0건** → install strip 정상 동작
  5. 배포본 `header-rules.md` §갱신 시점 **(4단)** 반영
  6. 배포본 3 `pipeline.json` rows **16/11/9** · checklist **5/5/4**
- `scripts/install-mac.sh`·`scripts/install/windows.ps1` git diff **0건** — PLAN 실측대로 스크립트 수정 불요

## [EXECUTE] Step 11 — 훅 발동 반경 8 파이프라인 회귀 (PM 직접)
- 관측 스코프: EXECUTE 단계 보유 파이프라인 **전수 8종**(opd·opds·opdw·opp·oppd·oppl·opsdd·opwt). `opdd`·`opgc`는 EXECUTE 행 0개로 대상 아님 — H-6 실측값과 일치
- 방법: `git show HEAD:opal/tools/state-tool/state_tool.py`로 **개정 전 베이스라인**을 복원해 동일 조건 A/B 대조. 각 파이프라인의 `pipeline.json`으로 임시 폴더를 `init`하고 EXECUTE 첫 행 앞 구간을 done 처리한 뒤 `advance --task-step <첫키>` 실행
- 실행 명령: `python3 <state_tool[HEAD|NEW]> init <dir> --skill <s> --mode agentic --rows-from <pipeline.json>` → `python3 <state_tool> advance <dir> --task-step <firstkey>`
- 결과: **8종 전건 (exit, ok, stdout 키집합) 개정 전후 동일** · 예기치 않은 거부(`ok=False`) **0건**
- 키집합 실측: `auto_approved,command,item,ok,row_id,stage,status,timestamp` — 16 실행(8종 × 2버전) 전건 동일
- 임시 자원 `tasks/.tmp-s11/` **회수 완료**(실측 부재)

## [EXECUTE] Step 12 — 회귀·폴백 실측 (PM 직접)
- (a) `task_steps` **16/11/9** + key 집합 동일 (`git show HEAD:` 대조) ✅
- (b) `spec-validate` × 3 → **violations 0건**(배포본 실행) ✅
- (c) 기존 태스크 3폴더(`103`·`104`·`105`) `show --format json` → **전건 exit 0** ✅
- (d) 폴백 오탐 0건 — `.md` 3파일 `validate --changed` → exit 0·`newly_uncovered` 0·`pre_existing` 3(비차단) / `state_tool.py` → exit 0·`newly_uncovered` 0·`pre_existing` 1 ✅
- 전 실행은 **배포본**(`~/.opal/tools/`) 경유 — H-11(구 배포본 판정 무의미) 회피

## [DECISION] S-11 ① 기대 문면 정정 (PM 실측 기반)
- 초안 기대: 태스크 106 폴더 → `skipped` · `doc_only_task`
- 실측: **`pass` · exit 0** · `matched_tokens` 9종(`domain`·`layer`·`depends`·`exports`·`write_to`·`reason`·`coverage`·`counts`·`code-scan`) · `target_files` 20건
- 판정: **초안이 틀렸다.** 이 태스크 PLAN.md §4.2 대상에 `state_tool.py`(`.py`)가 포함되어 게이트 ⑤가 발동하지 않고 ⑦ 판정으로 진행하며, 인용 토큰이 실재하므로 `pass`가 정답이다. 초안은 이 태스크를 문서 전용으로 오판했다
- R-5 AC(a)의 판정 축은 「거부 0건」이며 `pass`도 이를 충족한다. `doc_only_task` 경로는 S-24·S-25가 전담 관측한다
- TEST-SCENARIO.md S-11 기대 결과를 실측 근거와 함께 정정했다(사후 합리화가 아니라 오판 교정 — 근거는 게이트 ⑤ 조건과 §4.2 대상 파일 목록)

## [GATE] TEST 단계 — Partial Fail
- 워커 `opal-test-agent`(mode: be, advanced) · 소요 26분 · Pass 22 / Fail 2 / SUPERVISOR 대기 1
- 산출물: `TEST-SCENARIO.md`(결과 기입) + `RED-EVIDENCE.md`(신규). 워커가 산출물 경계 2파일을 mtime으로 자증

### RED 증거 (S-9·S-10) — PM 확인
- 베이스라인 `69f5ce1` 복원 후 `grep -c 'code_scan_citation'` = **0**(게이트 부재 확인)
- **RED-2(핵심)**: 인용 0건 PLAN + EXECUTE 첫 행 `mark` → 개정 전은 `ok:true`·exit 0·`state.json` md5 **변경**(거부되지 않는다)
- **GREEN**: `unmet` exit 1 · `mark`/`advance` 양쪽 `code_scan_citation_unmet` · md5 **호출 전후 동일**
- 축퇴 배제 대조군 7케이스 병기 — `.py`+인용0+`--auto-pass`가 게이트 ⑥으로 exit 1이므로 S-24 통과가 "게이트 사망"이 아님을 증명
- 워커가 **시점 한계를 정직히 기록**: 구현·배포 완료 후 TEST였으므로 시간순 RED가 아니라 개정 전 코드 복원 A/B 대조임을 `RED-EVIDENCE.md` §0에 명시

### [정정] CLOSE 게이트 차단 원인 — PM 초기 판단 오류
- PM 초기 판단: "Step 15의 @header 증가분(+739자)이 8192 창문을 넘겨 `newly_uncovered`를 유발했다" → **틀렸다**
- 결정 실측: `git checkout --`로 이 태스크 변경을 배제한 **HEAD 원본 상태에서도 `newly_uncovered` 1건**이 재현된다 → 이 태스크의 회귀가 **아니다**
- 실제 원인 = `code-scan.js`의 **문자/바이트 비대칭**:
  - 라이브 경로 `:956-957` `Buffer.alloc(HEADER_READ_BYTES)` + `readSync` → **8192 바이트** 제한
  - HEAD 비교 경로 `classifyUncovered` → `head.content.slice(0, HEADER_READ_BYTES)` → **8192 문자** 제한
  - 한글 밀도가 높은 @header는 두 창문 사이에 놓인다 — `test_state_tool.py` 실측 json_end = **10887 바이트 / 8134 문자**. 라이브는 헤더를 못 찾고(미보유) HEAD는 찾으므로(보유) "회귀"로 분류된다
- 즉 **한글 @header가 8192자~8192바이트 구간에 있는 모든 파일이 변경될 때마다 거짓 회귀로 CLOSE를 차단**한다. Step 4 워커가 `state_tool.py`에서 보고한 것과 같은 계열이나, 그쪽은 비차단 `pre_existing`으로 축퇴해 드러나지 않았다
- Step 15 추가분 압축(739자→132자, 절감 632자)은 **게이트 해소에 기여하지 않았다** — 유지하되(헤더 간결화 + 상세는 PLAN §4.2 Step 15가 소유) 해결책으로 계상하지 않는다. 압축 후 `pytest 379 passed / 0 failed` 회귀 0건, @header JSON 파싱 정상

## [GATE] Step 17 — `opcmb` SKILL.md STEP 3·4·6 보강 (S-20 해소)
- 판정: **Pass** · 워커 `opal-task-agent`(advanced) · 소요 6분 · 229→**268행**
- 결정적 증거: 워커가 **음성 경로(빈 값 미확정 강행)를 재완주해 1차 S-20 Fail 관측값을 그대로 재현**(`uncovered:incomplete` detail `layer,domain` + `draft`) → 원인이 **문면 결손**임이 A/B로 확정. 정상 경로는 골격 완료·`draft` 3건·커버리지 100%, 기입 후 exit 0
- STEP 6이 exit 코드로 스킬 성패를 판정하지 않게 됨 — "이 스킬은 exit 0을 완료 조건으로 삼지 않는다" 명문화 + `header-rules.md` 도입부 "도구는 구조를 만들고 워커는 내용을 채운다" 원문 인용
- 워커 자율 정밀화 1건(PM 승인): STEP 3의 `detail: layer,domain` 고정 표기를 "`detail`에 미해소 필드가 실린다"로 — 실측에서 core 2건은 `layer,domain`, util 1건은 `domain`만 실렸다
- PM 실측 무변경 확인: 모드 판별 4분기 1건 · `## 경계 — 신설하지 않는 것` 1건 · 변경이력 v1.1 1행. untracked 파일이라 `git diff` 불가 → 워커가 배포본 스냅샷을 baseline으로 삼은 것은 정당한 대체(배포본 mtime 23:09 유지 확인)

## [GATE] Step 18 — `force` 우회 의사결정 로그 정합 (S-25 ① 해소)
- 판정: **Pass** · 워커 `opal-be-agent`(advanced) · 소요 12분 · `+26/-8`
- PM 독립 실측: `ERROR_CODES` **46 불변**(`code_scan_citation_force`는 `decision` 문자열, 에러 코드 아님) · force 관련 테스트 **31 passed** · `advance`에 `--force` 인자 **부재**(`hasattr` False) · `@header` 순증 **+2바이트** · `schema/*.json` 무변경
- 오탐 0건 대조군 2건(문서 전용·인용 존재 + force → 무기재) — 091 `gate_artifact_force` 동형 계약 유지
- 워커 설계 판단 1건(PM 승인): 게이트 ②를 조기 `return`에서 「거부만 무력화」로 전환. 조기 반환 유지 시 문서 전용·미보급의 force까지 전부 기재되어 오탐 + 091과 비대칭. 순서 계약과 보호 대상은 보존(⑥⑦의 `err`가 force에서 발생하지 않으므로 exit·stdout 종전 동일)
- `cmd_advance` 미변경도 정당 — `--force` 인자가 파서에 없어 우회 경로가 **존재하지 않는다**. 방어 코드 추가는 PRINCIPLES §3 "No error handling for impossible scenarios" 위반
- PM 정정 1건: 워커의 "기존 2 force 경로가 diff에 1바이트도 없다"는 **코드 기준으로 정확**(grep 3건은 전부 `@header` description 내 이력 문구)

## [GATE] Step 19 — 인용 게이트 동작 회귀 고정 (검증 2원화)
- 판정: **Pass** · 워커 `opal-test-agent`(advanced) · 소요 9분 · 구현자(`opal-be-agent`)와 **분리**(H-9)
- PM 독립 실측: `pytest` **383 passed, 3 skipped, 98 subtests passed, 0 failed**(1차 379 + 4) · 신설 4케이스 단독 실행 통과 · 테스트 메서드 **382→386(+4)** 소실 0건 · `ERROR_CODES` 46 불변 · `schema/` 변경 0건 · mock 0건
- 4케이스: C1 인용0+force → `code_scan_citation_force` 기재 / C2 문서전용+force → 무기재 / C3 인용존재+force → 무기재 / C4 인용0+`--auto-pass` → 거부 불변 exit 1
- **워커가 PM 지시 전제를 반증했다(정당)**: "문서 전용 + force → 의사결정 로그 **전체 공백**"은 `--auto-pass` 경로에서 성립하지 않는다 — 093-era 계약이 `agentic auto-pass at row N` 행을 별도로 쓴다. 워커는 테스트를 기대에 맞추지 않고 판정 축을 `code_scan_citation` 포함 행으로 **좁혀 격리**했다. 「전체 공백」 단언은 force 경로에서만 성립한다
- **워커가 PLAN 문면 drift를 발견했다**: PLAN §3.4.2 게이트 ② 표가 구판(`force → return`)으로 남아 Step 18 구현(거부만 무력화)과 불일치. 워커는 Guards상 PLAN 무접촉 → **PM이 §3.4.2 ②를 개정 근거와 함께 교정**(Step 18 개정 주석 병기)

## [EXECUTE] TEST-SCENARIO 마감 (PM 직접)
- §8 재검증 절 신설 — S-20·S-25 ① 재판정 **Pass**, 회귀 고정 Pass, 재검증에서 드러난 사실 2건 기재
- §4 매핑 표 「테스트 파일:케이스」 27칸을 `(CLI 블랙박스 — 테스트 파일 없음)`으로 마감. 예외는 F-004 인용 게이트 4케이스(`test_c1_`~`test_c4_`)
- 상태를 `작성 완료` → **`실행 완료`**로 전환
