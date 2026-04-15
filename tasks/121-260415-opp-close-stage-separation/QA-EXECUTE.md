# QA: EXECUTE 검증 결과 — 121 파이프라인 현황판 CLOSE 단계 분리

> 검증일: 2026-04-15 | 단계: EXECUTE | 대상: 10개 변경 파일
> 기준: TASK.md R-1~R-7 / PLAN.md §4 QA 체크리스트 / C안 설계 원칙

---

## 1. 종합 판정

**Pass**

10개 변경 파일 모두 TASK.md R-1~R-7 AC를 충족한다. C안 설계 원칙(CLOSE 2행, 직전 단계 사용자 확인 = CLOSE 진입 게이트)이 모든 파일에 일관되게 반영되어 있다. Critical/Warning 항목 없음. Info 1개(opp EXECUTE 단계에 "추가작업" 참조가 v1.9부터 존재하지만, 이는 이전 버전의 잔류가 아닌 CLOSE 단계에 정상 위치함).

---

## 2. 요구사항별 검증 (R-1 ~ R-7)

| 요구사항 | AC 충족 | 근거 (파일:라인) | 판정 |
|---------|--------|----------------|------|
| **R-1** state-template.md CLOSE 단계 규칙 추가 + "최종 단계(EXECUTE/TEST)" 예외 규칙 제거 + CLOSE 진입 게이트 원칙 반영 | Yes | state-template.md L47: CLOSE 단계 2행 구성 명시. "최종 단계(EXECUTE/TEST)" 문구 Grep 결과 0건 (변경이력 내 "제거" 언급만 존재). L52: CLOSE 진입 게이트 blockquote 존재. L60: "DONE.md 행: CLOSE 단계의 첫 행에 위치"로 산출물 행 규칙 갱신. | Pass |
| **R-2** opal-harness.md §3 이벤트 테이블 + 상태 전이 흐름 CLOSE 명시 | Yes | opal-harness.md L139: `사용자 확인 완료` — "완료 (직전 단계가 CLOSE 진입 게이트인 경우)" 기술. L142: `태스크 완료` — "CLOSE 단계 완료 시 발생" 명시. L143: `추가작업 진입` — "CLOSE 단계 재진입" 명시. L144: `추가작업 완료` — "CLOSE 재진입 완료" 명시. L153-155: 상태 전이 흐름에 "CLOSE 단계 완료 → 완료" + "완료 → 추가작업중(CLOSE 재진입)" 명시. | Pass |
| **R-3** 6개 오케스트레이터 SKILL.md 단계 목록 CLOSE 포함 + C안 변경 (a)(b)(c) | Yes | opp: 단계 목록 "TASK / PLAN / EXECUTE / CLOSE". 행 예시 #18 사용자 확인(EXECUTE 끝), #19-#20 CLOSE 2행. opd: 단계 "TASK / ANALYSIS / PLAN / EXECUTE / TEST / CLOSE". 행 #23 사용자 확인(TEST 끝), #24-#25 CLOSE 2행. opds: "TASK / PLAN / EXECUTE / TEST / CLOSE". 행 #17 사용자 확인, #18-#19 CLOSE 2행. opdw: "TASK / WIREFRAME / EXECUTE / CLOSE". 행 #18 사용자 확인, #19-#20 CLOSE 2행. opwt: "TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE". QA 끝 "다음 단계(CLOSE)로 넘어갈까요?" + CLOSE 단계 섹션 신설. opsdd: "TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE". 행 #33 사용자 확인(VERIFY 끝), #34-#35 CLOSE 2행. | Pass |
| **R-3 opwt** QA 단계에서 DONE.md 생성 제거 + CLOSE 섹션 신설 | Yes | opwt SKILL.md L195-210: QA 단계 "PM 최종 판정"에 DONE.md 생성 없음. "다음 단계(CLOSE)로 넘어갈까요?" 보고 형식. L214-229: CLOSE 단계 섹션 신설 — "DONE.md 생성 / State Gate / 완료 보고". | Pass |
| **R-3 opsdd** Phase 6 DONE→CLOSE 리네이밍 + 4행→2행 통일 | Yes | opsdd SKILL.md L51: "Phase 6: CLOSE". L257: "## Phase 6: CLOSE". L334: 행 #34 "CLOSE \| DONE.md 생성". L335: 행 #35 "CLOSE \| State Gate". 총 35행 확인. `| DONE |` 단계명 패턴 Grep 결과 0건. | Pass |
| **R-4** additional-work.md CLOSE 재진입 원칙 + ADD_DONE.md 생성 CLOSE 소속 명시 | Yes | additional-work.md L28: "CLOSE 재진입 원칙" blockquote — "추가작업은 CLOSE 단계를 재진입하여 수행한다. ADD_DONE.md 생성 → State Gate는 CLOSE 단계의 마감 블록과 동일한 패턴을 따른다." L46: 진입 절차 3단계 "CLOSE 단계 재진입: ADD_DONE.md 작성". L48-49: 5단계 State Gate / 6단계 사용자 확인 추가. | Pass |
| **R-5** 레거시 호환 원칙 명시 | Yes | opal-harness.md L160: "레거시 호환 (CLOSE 단계)" blockquote — "기존 STATE.md(CLOSE 단계 도입 전 생성)는 소급 변경하지 않는다. 신규 태스크부터 CLOSE 단계를 반영한다." state-template.md L62에도 동일 원칙 존재. | Pass |
| **R-6** 변경이력 갱신 (10개 파일, 121 참조) | Yes | state-template.md: v1.1 (121) 존재. opal-harness.md: v4.2 (121) 존재. opal-harness-agentic.md: v1.4 (121) 존재. additional-work.md: v1.1 (121) 존재. opp: v2.5 (121). opd: v3.1 (121). opds: v3.0 (121). opdw: v2.1 (121). opwt: v3.0 (121). opsdd: v2.9.0 (121). 10개 전체 확인. | Pass |
| **R-7** CLOSE 진입 게이트 Guard 3개 문서 명시 | Yes | (1) opal-harness.md L45-48: "CLOSE 진입 게이트" 서브섹션 신설 — "사용자의 확인된 지시(승인/확인/확인완료 등)가 없으면 CLOSE 단계 진입 불가. agentic 모드에서도 유지." (2) state-template.md L52: CLOSE 진입 게이트 blockquote 동일 원칙. (3) opal-harness-agentic.md L111: §7 유지되는 규칙 테이블 "CLOSE 진입 게이트" 행 — "agentic 모드에서도 이 규칙은 유지 — 다른 Gate는 PM 자율 통과 허용이나 CLOSE 진입은 예외." | Pass |

---

## 3. 일관성 검증

### CLOSE 2행 일관성 (5개 SKILL.md)

| SKILL | CLOSE 행 구성 | CLOSE 행 번호 | 이전 단계 마지막 행 +1 |
|-------|-------------|------------|---------------------|
| opp | #19 DONE.md 생성 / #20 State Gate | 19-20 | #18 사용자 확인 +1 = 19 ✅ |
| opd | #24 DONE.md 생성 / #25 State Gate | 24-25 | #23 사용자 확인 +1 = 24 ✅ |
| opds | #18 DONE.md 생성 / #19 State Gate | 18-19 | #17 사용자 확인 +1 = 18 ✅ |
| opdw | #19 DONE.md 생성 / #20 State Gate | 19-20 | #18 사용자 확인 +1 = 19 ✅ |
| opsdd | #34 DONE.md 생성 / #35 State Gate | 34-35 | #33 사용자 확인 +1 = 34 ✅ |

판정: **Pass** — 5개 SKILL.md 모두 CLOSE 2행(`DONE.md 생성 / State Gate`) 동일 구성. 행 번호 연속성 전부 충족.

### 행수 변화 검증

| SKILL | 기대 (PLAN.md) | 실제 | 판정 |
|-------|--------------|------|------|
| opp | 19→20 | 20행 확인 (#1-#20) | Pass |
| opd | 24→25 | 25행 확인 (#1-#25) | Pass |
| opds | 18→19 | 19행 확인 (#1-#19) | Pass |
| opdw | 19→20 | 20행 확인 (#1-#20) | Pass |
| opsdd | 37→35 | 35행 확인 (#1-#35) | Pass |

### 이전 최종 단계 DONE.md 생성 행 제거

- opp EXECUTE: DONE.md 생성 행 없음 ✅
- opd TEST: DONE.md 생성 행 없음 ✅ (TEST 섹션 #19-#23에 없음)
- opds TEST: DONE.md 생성 행 없음 ✅
- opdw EXECUTE: DONE.md 생성 행 없음 ✅
- opwt QA: DONE.md 생성 없음 ✅ (QA PM 최종 판정 섹션에서 CLOSE 전이만 기술)
- opsdd VERIFY: DONE.md 생성 행 없음 ✅

### 이전 최종 단계 끝 `State Gate / 사용자 확인` 2행 추가

- opp EXECUTE #17 State Gate / #18 사용자 확인 ✅
- opd TEST #22 State Gate / #23 사용자 확인 ✅
- opds TEST #16 State Gate / #17 사용자 확인 ✅
- opdw EXECUTE #17 State Gate / #18 사용자 확인 ✅
- opwt QA: PM Gate → State Gate → 사용자 확인(CLOSE 진입 승인 요청) ✅
- opsdd VERIFY: State Gate → PM Gate → State Gate → #33 사용자 확인 ✅

### "추가작업" 참조 CLOSE로 이동 확인

- opp: EXECUTE 섹션에 "추가작업" 참조 없음. CLOSE 섹션(L106)에만 존재 ✅
- opdw: EXECUTE 섹션에 "추가작업" 참조 없음. CLOSE 섹션(L99)에만 존재 ✅
- opd: TEST 섹션에 "추가작업" 참조 없음. CLOSE 섹션(L174)에만 존재 ✅
- opds: TEST 섹션에 "추가작업" 참조 없음. CLOSE 섹션(L140)에만 존재 ✅
- opwt: QA 섹션에 "추가작업" 참조 없음. CLOSE 섹션(L229)에만 존재 ✅
- opsdd: VERIFY 섹션에 "추가작업" 참조 없음. CLOSE 섹션(L273)에만 존재 ✅

### 3개 문서 CLOSE 진입 게이트 규칙 일관 서술

| 문서 | 기술 내용 | 일치 여부 |
|------|----------|----------|
| opal-harness.md §1 | "사용자의 확인된 지시(승인/확인/확인완료 등)가 없으면 CLOSE 단계 진입 불가. agentic 모드에서도 유지" | 기준 |
| state-template.md | "사용자의 확인된 지시(승인, 확인, 확인완료 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가. 이 규칙은 agentic 모드에서도 유지된다." | ✅ 동일 원칙 |
| opal-harness-agentic.md §7 | "사용자의 확인된 지시(승인/확인/확인완료 등)가 없으면 CLOSE 단계 진입 불가. agentic 모드에서도 이 규칙은 유지 — 다른 Gate는 PM 자율 통과 허용이나 CLOSE 진입은 예외." | ✅ 동일 원칙 + agentic 예외 명시 |

판정: **Pass**

### Agentic Mode 흐름도 CLOSE 포함 확인

- opp: "TASK → PLAN Gate → EXECUTE Gate → CLOSE (사용자 승인 후 자동 진행)" ✅
- opd: "TASK → ANALYSIS Gate → PLAN Gate → EXECUTE Gate → TEST Gate → CLOSE" ✅
- opds: "TASK → PLAN Gate → EXECUTE Gate → TEST Gate → CLOSE" ✅
- opdw: "TASK → WIREFRAME Gate → EXECUTE Gate → CLOSE" ✅
- opwt: 별도 Agentic Mode 섹션 없음 (opwt는 Agentic Mode 섹션 존재 안 함 — 기존 패턴 유지)
- opsdd: "TASK → SPEC Gate → REVIEW → DESIGN Gate → EXECUTE-LOOP → VERIFY → CLOSE" ✅

판정: **Pass** (opwt Agentic Mode 섹션 미존재는 기존 구조 그대로이며 이번 태스크 범위 밖)

### CLOSE 완료 보고 형식 구분 (C안)

| SKILL | 이전 단계 보고 형식 | CLOSE 보고 형식 |
|-------|-----------------|----------------|
| opp | "[EXECUTE] 완료 보고 … 다음 단계(CLOSE)로 넘어갈까요?" | "✅ [CLOSE] 태스크 완료 … 태스크가 완료되었습니다." |
| opd | "[TEST] 완료 보고 … 다음 단계(CLOSE)로 넘어갈까요?" | "✅ [CLOSE] 태스크 완료 …" |
| opds | "[TEST] 완료 보고 … 다음 단계(CLOSE)로 넘어갈까요?" | "✅ [CLOSE] 태스크 완료 …" |
| opdw | "[EXECUTE] 완료 보고 … 다음 단계(CLOSE)로 넘어갈까요?" | "✅ [CLOSE] 태스크 완료 …" |
| opwt | "[QA] 완료 보고 … 다음 단계(CLOSE)로 넘어갈까요?" | "✅ [CLOSE] 태스크 완료 …" |
| opsdd | Phase 5 VERIFY "사용자 Gate (= CLOSE 진입 게이트)" | "✅ [CLOSE] 태스크 완료 …" |

판정: **Pass** — C안 보고 형식 구분 일관 적용됨

---

## 4. 문서 품질 검증

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| Q-1 | 한국어 본문 + 영어 코드/필드명 규칙 | Pass | 10개 파일 모두 한국어 본문, 영어 단계명(CLOSE/EXECUTE/TEST) 및 파일명(DONE.md) 사용. |
| Q-2 | 기존 문서 톤/스타일 일관 | Pass | 변경된 섹션이 기존 문서의 bullet/blockquote/테이블 구조와 동일 패턴 사용. |
| Q-3 | "최종 단계 예외 규칙" 문구 state-template.md에서 실제 제거 | Pass | Grep 결과: state-template.md에서 "최종 단계.*예외 규칙" 패턴 매칭 0건 (변경이력의 "제거" 언급만 존재). |
| Q-4 | DONE.md 산출물명과 CLOSE 단계명 구분 (특히 opsdd) | Pass | opsdd: "Phase 6: CLOSE" (단계명), "DONE.md 생성" (산출물명) 명확히 구분. 폴더 구조 주석에도 "# Phase 6 — 최종 완료 확인"으로 DONE.md 산출물 역할 기술. |
| Q-5 | 변경이력 일시 형식 일치 | Pass | 10개 파일 모두 날짜 형식 `YYYY-MM-DD` 사용 (기존 파일과 동일). opsdd는 `v2.9.0` 형식(기존 semantic versioning 패턴 유지). |

---

## 5. 제약 준수

| 제약 | 검증 방법 | 결과 |
|------|----------|------|
| `~/.opal/` 경로 수정 0건 | git status 확인 — 변경 파일 목록 (`opal/core/`, `opal/skills/`만 변경됨) | Pass — ~/.opal/ 경로 수정 없음 |
| 120번 태스크 폴더 수정 0건 | git diff `tasks/120-260415-opp-pm-constraint-citation-rule/` 결과 빈 출력 | Pass — tasks/120* 수정 없음 |
| PLAN.md에 없는 파일 수정 0건 | git status 변경 파일 10개가 PLAN.md §2 영향 범위와 정확히 일치 | Pass |
| 기존 STATE.md 소급 변경 금지 | tasks/ 폴더 내 STATE.md 수정 없음 (git status 확인) | Pass |

---

## 6. 발견 사항

### Info 항목

**I-1 (Info): opp EXECUTE 섹션에 "추가작업 참조" 관련 이전 변경이력 항목 존재**

opp SKILL.md v1.9 (L189) 변경이력에 "EXECUTE 후 추가작업 참조 가이드 추가"가 기록되어 있다. 이것은 v1.9에서 EXECUTE 단계에 "추가작업" 참조를 추가한 기록이며, v2.5(121)에서 이를 CLOSE로 이동한 것이 정상 프로세스다. 현재 파일 상태는 CLOSE 섹션에만 "추가작업" 참조가 존재하며 EXECUTE 섹션에는 없다. 이력 항목은 정상 기록이므로 수정 불필요.

- 심각도: Info
- 조치: 불필요

**I-2 (Info): opd SKILL.md에 EXECUTE QA Gate 없음**

opd SKILL.md의 EXECUTE 단계 완료 후 흐름(L104-105)이 "State Gate → TEST 단계 진입"으로 구성되어 있고 QA Gate가 없다. 이는 opd의 기존 설계(EXECUTE 후 별도 QA 없이 TEST로 직행)이며 이번 태스크 범위 밖이다.

- 심각도: Info
- 조치: 불필요 (기존 설계 유지)

---

## 7. 체크리스트 갱신

### PLAN.md §4 QA 체크리스트 — 갱신 결과

EXECUTE 워커가 이미 모든 항목을 `[x]`로 갱신한 것을 확인. QA 검증 결과 모든 항목이 실제 통과하였음을 확인. 보정 없음.

**기능 테스트** (모두 Pass):
- [x] R-1: state-template.md CLOSE 단계 규칙 존재 + "최종 단계(EXECUTE/TEST)" 예외 규칙 제거
- [x] R-1: CLOSE 2행 구성(DONE.md 생성 / State Gate) 명시
- [x] R-1: 직전 단계의 사용자 확인 = CLOSE 진입 게이트 서술
- [x] R-2: 이벤트 테이블 CLOSE 귀속
- [x] R-2: 상태 전이 흐름 CLOSE 종료 단계 명시
- [x] R-3: 6개 SKILL.md 단계 목록 CLOSE 포함
- [x] R-3 opp/opd/opds/opdw: CLOSE 2행 + 이전 단계 State Gate/사용자 확인 추가
- [x] R-3 opwt: QA 단계 DONE.md 제거 + CLOSE 섹션 신설
- [x] R-3 opsdd: Phase 6 CLOSE 리네이밍 + 4행→2행
- [x] R-4: additional-work.md CLOSE 재진입 원칙 + State Gate/사용자 확인
- [x] R-5: 레거시 호환 원칙 opal-harness.md §3
- [x] R-6: 10개 파일 변경이력 (121) 참조
- [x] R-7: opal-harness.md §1 CLOSE 진입 게이트 Guard
- [x] R-7: state-template.md CLOSE 진입 게이트 원칙
- [x] R-7: opal-harness-agentic.md §7 CLOSE 진입 게이트 행

**일관성 테스트** (모두 Pass):
- [x] 5개 SKILL.md CLOSE 2행 동일 구성
- [x] CLOSE 행 번호 연속성
- [x] 이전 최종 단계 DONE.md 생성 행 완전 제거
- [x] 이전 최종 단계 끝 State Gate/사용자 확인 2행 추가
- [x] opp/opdw EXECUTE 단계 "추가작업" 참조 CLOSE로 이동
- [x] opd/opds TEST 단계 "추가작업" 참조 CLOSE로 이동
- [x] opwt QA 단계 "추가작업" 참조 CLOSE로 이동
- [x] Agentic Mode 흐름도 CLOSE 포함
- [x] state-template.md CLOSE 규칙과 6개 SKILL.md CLOSE 구성 일치
- [x] 3개 문서 CLOSE 진입 게이트 규칙 일관 서술
- [x] CLOSE 완료 보고 형식 C안 구분

**문서 품질** (모두 Pass):
- [x] 한국어 본문 + 영어 코드/필드명 규칙
- [x] 기존 문서 톤/스타일 일관
- [x] "최종 단계 예외 규칙" state-template.md에서 제거 확인
- [x] DONE.md 산출물명 vs CLOSE 단계명 구분
- [x] 변경이력 일시 형식 일치

---

## 8. 결론

**Pass — 다음 단계(CLOSE) 진입 가능.**

TASK.md R-1~R-7 요구사항이 10개 변경 파일에 완전히 반영되었다. C안 설계 원칙(CLOSE 2행, 직전 단계 사용자 확인 = CLOSE 진입 게이트, "최종 단계 예외 규칙" 소멸)이 일관되게 구현되었고, 3개 문서의 CLOSE 진입 게이트 규칙이 일관 서술되어 있다. 행수 변화 기대값(opp 20, opd 25, opds 19, opdw 20, opsdd 35)이 모두 충족된다. `~/.opal/` 경로 수정 0건, 120번 태스크 폴더 불가침이 확인되었다. Critical/Warning 항목 없음.
