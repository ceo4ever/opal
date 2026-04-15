# QA: PLAN 검증 결과 — 121 파이프라인 현황판 CLOSE 단계 분리

> 검증일: 2026-04-15 | 단계: PLAN | 대상: PLAN.md v2 (C안 + R-7 반영)
> TASK.md 기준 R-1 ~ R-7 / C안 설계 원칙 / 일관성

---

## 1. 요약

PLAN.md v2는 TASK.md의 모든 요구사항(R-1 ~ R-7)을 체계적으로 커버한다. C안 설계 원칙(CLOSE 2행, 직전 단계 사용자 확인이 CLOSE 진입 게이트)이 일관되게 반영되어 있으며, 10개 파일에 대한 구체적인 변경 명세(라인 번호, Before/After 비교)가 포함되어 있다. Phase 3개로 구분된 순차/병렬 실행 계획이 명확하고, 11개 Step 각각에 완료 기준과 테스트 방법이 명시되어 있다. 리스크 테이블에 7개 리스크와 대응 방안이 구체적으로 기술되어 있다. 현황 조사에 실제 파일을 Read한 결과(L47, L58, L117, L181 등 구체적 라인 번호)가 포함되어 있어 즉시 EXECUTE 진입 가능하다.

---

## 2. 검증 결과

### 2-1. TASK.md 요구사항별 검증 (R-1 ~ R-7)

| # | 요구사항 | AC 충족 | 근거 (PLAN.md) | 판정 |
|---|---------|--------|----------------|------|
| R-1 | state-template.md CLOSE 단계 공통 블록 규칙 (2행 구성 + CLOSE 진입 게이트 원칙) | Yes | Step 1 (L559-578): L47 "최종 단계 예외 규칙" 제거 + "CLOSE 단계: 2행(DONE.md 생성 / State Gate)" 교체 명시. L58 DONE.md 행 규칙 교체. CLOSE 진입 게이트 blockquote 추가 내용 명세. 완료 기준에 "최종 단계(EXECUTE/TEST)" 문구 제거 + "CLOSE 진입 게이트" 존재 확인 포함. | Pass |
| R-2 | opal-harness.md §3 이벤트 테이블 + 상태 전이 흐름 갱신 | Yes | Step 2 (L581-602): §3 이벤트 테이블에서 `태스크 완료`(L137), `추가작업 진입`(L138), `추가작업 완료`(L139) CLOSE 귀속 명시. 상태 전이 흐름에 "CLOSE 단계 완료 → 완료" 패턴 추가. 완료 기준에 이벤트-CLOSE 연관 기술 + CLOSE 종료 단계 명시 포함. | Pass |
| R-3 | 6개 오케스트레이터 SKILL.md 도메인 치환값 갱신 (C안) | Yes | Step 5~10 (L630-728): opp/opd/opds/opdw/opwt/opsdd 각각 Before/After 행 예시 포함. (a) 마감 3행 제거, (b) 최종 단계 끝 State Gate/사용자 확인 2행 추가, (c) CLOSE 2행 추가 명세. opwt(행 예시 없음)는 단계 목록+본문 변경으로 처리. opsdd(DONE→CLOSE 리네이밍 + 4행→2행)는 Step 10에서 별도 명세. 단계 목록에 CLOSE 추가 6개 모두 명시. | Pass |
| R-4 | additional-work.md CLOSE 재진입 원칙 | Yes | Step 4 (L618-628): "CLOSE 재진입 원칙" blockquote 추가 + 진입 절차 Before/After(5단계→7단계, 3단계에 "CLOSE 단계 재진입" 명시, 5/6단계 State Gate+사용자 확인 추가). AC의 "ADD_DONE.md 생성이 CLOSE 단계 소속으로 기술"에 해당. | Pass |
| R-5 | 레거시 호환 원칙 명시 | Yes | Step 2 작업 내용 5번 (L595-598): opal-harness.md §3 레거시 호환 노트 뒤에 "레거시 호환 (CLOSE 단계)" blockquote 추가 명세. "기존 STATE.md는 소급 변경하지 않는다. 신규 태스크부터 CLOSE 단계를 반영한다"는 문장 포함. AC 위치(opal-harness.md §3) 명확. | Pass |
| R-6 | 변경이력 갱신 (10개 파일) | Yes | Step 11 (L730-742): 10개 파일 전체 변경이력 일괄 확인 Step 신설. 태스크 번호 121 참조. state-template.md(변경이력 없는 경우 확인 필요), additional-work.md(신규 섹션 추가) 등 특수 케이스 명시. 완료 기준이 "변경된 모든 파일(10개)에 태스크 121 참조 변경이력 행 존재"로 명확. | Pass |
| R-7 | CLOSE 진입 게이트 Guard (3개 문서) | Yes | Step 1 (L572-575): state-template.md CLOSE 진입 게이트 원칙 blockquote 추가. Step 2 작업 내용 1번 (L586-591): opal-harness.md §1 Guards "CLOSE 진입 게이트" 서브섹션 신설. Step 3 (L604-616): opal-harness-agentic.md §7 유지되는 규칙 테이블 행 추가 — "agentic 모드에서도 CLOSE 진입은 사용자 승인 필수" 명시. AC (1)(2)(3) 모두 커버. | Pass |

### 2-2. C안 설계 정합성 검증

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| C-1 | CLOSE 단계가 반드시 2행(`DONE.md 생성` / `State Gate`)이며 사용자 확인 행이 없다 | Pass | L157-163: "CLOSE 단계는 2행이다" 명시. "CLOSE 단계에 사용자 확인 행 없음" 명시. opp/opd/opds/opdw/opsdd 행 예시 Before/After 모두 CLOSE 2행으로만 구성. |
| C-2 | 직전 단계(EXECUTE/TEST/QA/VERIFY) 끝에 `State Gate + 사용자 확인` 2행이 신규 추가되었다 | Pass | L166-174: "각 SKILL.md의 최종 단계에 `State Gate + 사용자 확인` 2행을 신규 추가" 명시. opp/opd/opds/opdw/opsdd 각각 Before/After에서 PM Gate 후 State Gate + 사용자 확인 2행 추가 확인. |
| C-3 | "사용자 확인"이 CLOSE 진입 게이트 역할임이 명시되었다 | Pass | L163: "직전 단계(EXECUTE/TEST/QA/VERIFY)의 사용자 확인이 CLOSE 진입 게이트 역할". L174: "이 `사용자 확인`이 곧 태스크 마감 승인이며, CLOSE 단계 진입을 허가하는 게이트" 명시. |
| C-4 | opsdd는 기존 Phase 6 DONE 4행을 2행으로 통일 + VERIFY의 State Gate+사용자 확인을 CLOSE 진입 게이트로 재활용 | Pass | L83-84: VERIFY Phase 끝에 이미 State Gate/사용자 확인 존재. 기존 #34 첫 State Gate와 #37 사용자 확인이 중복 → 제거 설명. Step 10 (L722): 4행→2행 Before/After 명시. 37→35 행수 확인. |
| C-5 | 보고 형식: EXECUTE/TEST/QA/VERIFY → "다음 단계(CLOSE)로 넘어갈까요?" / CLOSE → "태스크가 완료되었습니다" | Pass | L176-191: C안 보고 형식 명세 명확히 구분. opp Step 5 (L637): EXECUTE 보고 형식 + CLOSE 보고 형식. |

### 2-3. Step별 검증 (Step 1~11)

| Step | 파일 경로 명확 | 작업 구체적 | 완료 기준 검증 가능 | 테스트 방법 명시 | 의존 관계 명확 |
|------|-------------|-----------|------------------|----------------|-------------|
| 1 | Pass (opal/core/…/state-template.md) | Pass (L47/L58 교체 내용 + blockquote 신규 추가) | Pass (문구 제거/존재 Grep 검증) | Pass (Grep 검증) | Pass (의존 없음) |
| 2 | Pass (opal/core/…/opal-harness.md) | Pass (§1 신설 + §3 L137-139 + L147-151 + L153 후 추가) | Pass (Guard 존재 + 이벤트 CLOSE 연관) | Pass (Read §1 §3) | Pass (Step 1) |
| 3 | Pass (opal/core/…/opal-harness-agentic.md) | Pass (§7 테이블 행 추가 내용 명세) | Pass (§7 테이블 "CLOSE 진입 게이트" 행 존재) | Pass (Read §7) | Pass (Step 1) |
| 4 | Pass (opal/core/…/additional-work.md) | Pass (blockquote 추가 + 진입 절차 Before/After) | Pass (원칙 명시 + State Gate 포함) | Pass (Read 진입 절차) | Pass (Step 1) |
| 5 | Pass (opal/skills/opal-pilot-project/SKILL.md) | Pass (L13, L99, L73-88 변경 + STEP 4 신설 + 행 예시 Before/After) | Pass (CLOSE 포함 + DONE.md 부재 + 사용자 확인 부재 확인) | Pass (Grep) | Pass (Step 1) |
| 6 | Pass (opal/skills/opal-pilot-dev/SKILL.md) | Pass (L12, L154, L128-129 변경 + STEP 6 신설 + 행 예시) | Pass (CLOSE 포함 + TEST에 DONE.md 부재) | Pass (Grep) | Pass (Step 1) |
| 7 | Pass (opal/skills/opal-pilot-dev-short/SKILL.md) | Pass (L13, L158, L93-95 변경 + STEP 5 신설) | Pass (CLOSE 포함 + TEST에 DONE.md 부재) | Pass (Grep) | Pass (Step 1) |
| 8 | Pass (opal/skills/opal-pilot-dev-wireframe/SKILL.md) | Pass (L12, L80, L70-72 변경 + STEP 4 신설 + 행 예시) | Pass (CLOSE 포함 + EXECUTE에 DONE.md 부재) | Pass (Grep) | Pass (Step 1) |
| 9 | Pass (opal/skills/opal-pilot-write-tech/SKILL.md) | Pass (L213, L196, L201 변경 + CLOSE 단계 섹션 신설) | Pass (단계 목록 CLOSE 포함 + QA에 DONE.md 생성 제거) | Pass (Read) | Pass (Step 1) |
| 10 | Pass (opal/skills/opal-pilot-sdd/SKILL.md) | Pass (L273, L257, L259-264, L33-53, L329-332 변경 명세) | Pass (단계명 CLOSE 통일 + 행 2행 통일) | Pass (Grep) | Pass (Step 1) |
| 11 | Pass (10개 전체 파일) | Pass (태스크 121 참조, 특수 케이스 명시) | Pass (변경된 모든 파일에 121 참조 행 존재) | Pass (각 파일 하단 Read) | Pass (Step 1~10) |

### 2-4. 일관성 검증

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| I-1 | 5개 SKILL.md(opp/opd/opds/opdw/opsdd) CLOSE 2행 동일 구성 | Pass | L769: QA 체크리스트에 명시. 각 Step 완료 기준에 일관 반영. |
| I-2 | 6개 SKILL.md 단계 목록에 CLOSE 모두 포함 | Pass | Step 5~10 각각 단계 목록 갱신 작업 포함. |
| I-3 | 3개 문서(opal-harness.md §1, state-template.md, opal-harness-agentic.md §7) CLOSE 진입 게이트 규칙 동일 서술 | Pass | L778: QA 일관성 테스트에 "R-7 CLOSE 진입 게이트 규칙이 3개 문서에서 일관되게 서술되어 있는가" 포함. 리스크 테이블에도 "3개 문서 간 불일치" 리스크 대응 명시. |
| I-4 | 행수 계산 일관성 (opp 19→20, opd 24→25, opds 18→19, opdw 19→20, opsdd 37→35) | Pass | opp L370: 19→20 명시. opd L422: 24→25 명시. opds L455: 18→19 명시. opdw L485: 19→20 명시. opsdd L541: 37→35 명시. opwt는 행 예시 없음으로 행수 변화 없음(정상). |
| I-5 | opsdd VERIFY 끝 State Gate+사용자 확인이 CLOSE 진입 게이트 역할임이 명시 | Pass | L83-84, L541: VERIFY Phase 끝 기존 행이 CLOSE 진입 게이트임을 설명. 기존 #34/#37 중복 제거 근거로 명시. |

### 2-5. 제약 조건 준수

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| C-1 | `~/.opal/` 경로 수정 계획 없음 | Pass | 모든 파일 경로가 `opal/core/`, `opal/skills/`로 명시. `~/.opal/` 경로 없음. |
| C-2 | 120번 태스크 폴더 불가침 | Pass | L103: "120번 태스크 — 절대 건드리지 않음" 명시. 리스크 테이블 L796에도 충돌 리스크 대응 명시. |
| C-3 | 레거시 호환 원칙 (기존 STATE.md 소급 변경 없음) | Pass | L102: "기존 tasks/ 폴더의 STATE.md 파일 — 레거시 호환 원칙에 의해 소급 변경 없음". R-5 Step 2 작업 내용에 레거시 호환 원칙 추가 명세. |

### 2-6. PLAN.md 품질 기준 체크리스트

| # | 기준 | 결과 | 근거 |
|---|------|------|------|
| Q-1 | 이 PLAN만 보고 바로 EXECUTE에 들어갈 수 있는가 | Pass | 각 Step에 파일 경로, 라인 번호, Before/After 내용이 명시되어 있어 즉시 실행 가능. |
| Q-2 | 구현 순서의 의존성이 올바른가 | Pass | Phase 1(Step 1 순차) → Phase 2(Step 2,3,4 병렬) → Phase 3(Step 5-11 병렬). SSOT(state-template.md) 확정 후 하네스·스킬 수정이 의존성 상 올바름. |
| Q-3 | 현황 조사가 실제 파일을 Read한 결과로 보이는가 | Pass | L26-84: L47, L58, L117, L118, L119, L183, L184, L185, L103, L257-264 등 구체적 라인 번호 포함. 파일 내용 인용("현재 행 구성 규칙은 3가지 카테고리" 등). |
| Q-4 | 각 Step의 완료 기준이 명확하고 검증 가능한가 | Pass | 각 Step에 Grep/Read 기반 검증 방법 포함. |
| Q-5 | Phase 그룹핑(병렬/순차)이 수행되었는가 | Pass | L551-557: Phase 1 순차 / Phase 2,3 병렬 명시. |
| Q-6 | TASK.md 요구사항을 모두 커버하는가 (R-1~R-7) | Pass | §2-1 검증 결과 R-1~R-7 모두 Pass. |
| Q-7 | QA 항목이 기능/일관성/품질을 포함하는가 | Pass | §4 QA 체크리스트: 기능 테스트(R-1~R-7) + 일관성 테스트 + 문서 품질 3개 섹션 포함. |
| Q-8 | 리스크 대응이 구체적인가 | Pass | §5 리스크 테이블: 7개 리스크, 각 영향과 대응 방안 구체적. |

---

## 3. 지적 사항

### Warning 항목

**W-1 (Info): state-template.md 변경이력 테이블 부재 확인 필요**

PLAN.md Step 11 (L735)에 "state-template.md: 변경이력 없음 → 신규 추가 불필요 (현재 변경이력 테이블 없음 — 확인 필요)"로 기술되어 있다. 실제 파일에 변경이력 테이블이 없으면 R-6 AC("변경된 모든 파일(10개)의 변경이력 테이블에 태스크 121 참조 행이 추가되어 있다")를 충족하지 못할 수 있다. EXECUTE 단계에서 파일 확인 후 신규 변경이력 섹션 추가 여부를 결정해야 한다.

- 심각도: Info
- 권고: EXECUTE Step 11에서 state-template.md 파일 확인 후, 변경이력 테이블이 없으면 신규 생성. PLAN.md 자체는 이 케이스를 인지하고 있으므로 진행에 영향 없음.

**W-2 (Info): additional-work.md 변경이력 신규 생성 — v1.0 초기 버전 명세 필요**

PLAN.md L625에 "변경이력 테이블이 없으면 하단에 추가 (현재 없음 — 신규 생성)"이 명시되고, L738에 "v1.0(초기 작성) + v1.1(CLOSE 재진입, 121) 행 추가"로 기술되어 있다. v1.0의 작성 일시 및 작성자 특정이 EXECUTE 단계에서 추가 판단이 필요하다.

- 심각도: Info
- 권고: EXECUTE 단계에서 기존 OPAL 변경이력 컨벤션(docs/CONVENTIONS.md)을 참조하여 v1.0 작성.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 AC | state-template.md CLOSE 2행 + 최종 단계 예외 규칙 제거 + CLOSE 진입 게이트 | Pass — Step 1에 AC 전항목 반영 |
| TASK.md R-2 AC | 이벤트 테이블 CLOSE 귀속 + 상태 전이 흐름 CLOSE 명시 | Pass — Step 2에 반영 |
| TASK.md R-3 AC | 6개 SKILL.md 단계 목록 CLOSE + 3가지 변경 (a)(b)(c) | Pass — Step 5~10에 반영 |
| TASK.md R-4 AC | additional-work.md CLOSE 재진입 원칙 + ADD_DONE.md CLOSE 소속 | Pass — Step 4에 반영 |
| TASK.md R-5 AC | 레거시 호환 원칙 opal-harness.md §3 | Pass — Step 2에 반영 |
| TASK.md R-6 AC | 10개 파일 변경이력 | Pass — Step 11에 반영 (Info 2개) |
| TASK.md R-7 AC (1)(2)(3) | opal-harness.md §1 + state-template.md + opal-harness-agentic.md §7 | Pass — Step 1,2,3에 각각 반영 |
| TASK.md 제약 조건 | `~/.opal/` 금지 / 120번 불가침 / 레거시 호환 | Pass — 모두 반영 |
| TASK.md 확정 설계 방향 | C안 핵심 원칙 5가지 | Pass — §핵심 설계에 완전 반영 |

---

## 5. 체크리스트 갱신 (TASK.md 요구사항 체크)

PLAN.md가 이하 요구사항을 계획 수준에서 충족하였으므로 TASK.md 체크박스 갱신 권고:

- R-1: [x] — state-template.md CLOSE 2행 규칙 + 최종 단계 예외 규칙 제거 + CLOSE 진입 게이트 원칙 계획 완료 (Step 1)
- R-2: [x] — opal-harness.md §3 이벤트 테이블 + 상태 전이 흐름 갱신 계획 완료 (Step 2)
- R-3: [x] — 6개 SKILL.md C안 도메인 치환값 갱신 계획 완료 (Step 5~10)
- R-4: [x] — additional-work.md CLOSE 재진입 원칙 계획 완료 (Step 4)
- R-5: [x] — 레거시 호환 원칙 opal-harness.md §3 계획 완료 (Step 2)
- R-6: [x] — 10개 파일 변경이력 갱신 계획 완료 (Step 11, Info 2개 있으나 계획 반영)
- R-7: [x] — 3개 문서 CLOSE 진입 게이트 규칙 계획 완료 (Step 1,2,3)

---

## 6. 판정

**Pass**

PLAN.md v2는 TASK.md의 R-1 ~ R-7 모든 요구사항을 체계적으로 커버하며, C안 설계 원칙이 일관되게 반영되어 있다. 현황 조사에 구체적 라인 번호가 포함되어 있고, 11개 Step 각각에 완료 기준과 테스트 방법이 명시되어 있어 즉시 EXECUTE 진입이 가능하다. Critical 또는 Warning 항목 없음. Info 2개(state-template.md 변경이력 테이블 부재 확인, additional-work.md v1.0 일시 특정)는 EXECUTE 단계에서 처리 가능하며 PLAN 품질에 영향 없다.

**Pass 권고 — EXECUTE 진입 가능.**
