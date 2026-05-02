# QA: PLAN — 파이프라인 현황판 JSON 분리 + state-tool 도입 (B안)

> 검토일: 2026-05-01 | 판정: **Pass**

---

## 1. 요약

PLAN.md는 TASK v2의 F-1~F-23 및 T-1~T-13 전체를 커버하는 16-Step 실행 체크리스트를 포함한다. 영향 범위를 TASK의 "약 42개"에서 "추적 48개 / 수정 35개 + 신규 5파일"로 근거 기반 정정하였으며, 모든 TASK 미확정 9건 중 8건을 PLAN 단계에서 명시적 결정으로 확정했다. §1 참조 문서 테이블(D-1~D-19), 인라인 인용, [MUST] 토큰이 citation-rules.md 규정에 맞게 사용되었으며, 마이그레이션 순서 의존 관계가 TASK 제약 조건과 일치한다. 경미한 보강 필요 항목(Warning 2건)이 있으나 EXECUTE 단계에서 해소 가능하다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | §3 Step 1~16에 파일명/줄번호/완료 기준/테스트 방법이 명시됨. 소스 경로 직접 호출 검증 패턴(`bash opal/tools/state-tool/run.sh`)도 Step 1에 명시 |
| GP-2 | 의존성 순서 | Pass | TASK 제약 마이그레이션 순서와 Phase 1~9가 일치 (§2.3 상세) |
| GP-3 | TASK 반영 | Pass | F-1~F-23 전항목 매핑 확인 (§4 요구사항 커버리지 매핑 표 참조) |
| GP-4 | 파일 목록 완전성 | Pass | 신규 5파일(N-1~N-5), 수정 41개(M-1~M-41) 명세. §1 관련 파일 표에 경로+줄번호 모두 포함 |
| GP-5 | 설계 구체성 | Pass | §2.1~§2.10에서 TASK 미확정 9건 중 8건 결정. 각 결정에 근거 명시 |
| GP-6 | 체크리스트 커버리지 | Pass | F-1~F-23 모두 §3 Step에 매핑됨 (§4 매핑 표 참조) |
| 2.1 | F-1~F-23 요구사항 커버리지 | Pass | 전항목 매핑 완료. 누락 없음 |
| 2.2 | T-1~T-13 기술 결정 반영 | Pass | 전항목 §2 핵심 설계에 반영. T-11·T-12는 §2.1, T-13은 §2.5 |
| 2.3 | 마이그레이션 순서 정합성 | Pass | TASK 제약 조건 순서와 Step 1~16 Phase 구조 일치 (§3 상세) |
| 2.4 | 인용 규칙 준수 | Pass | §1 참조 테이블(D-1~D-19), 인라인 인용, [MUST] 3건 적정 사용 |
| 2.5 | Step 완료 기준 검증 가능성 | Warning | Step 3·5·6·8 완료 기준이 "grep 결과 확인" 수준 — 정량 기준(예: 0건) 미명시 항목 있음 |
| 2.6 | §4 QA 체크리스트 적정성 | Warning | 기능 테스트 18항목·일관성 9항목·문서 품질 7항목으로 충실. 단, "agentic 모드 사용자 확인 행 na 자동 마킹" 검증 항목이 일관성 섹션에 명시되지 않음 |
| 2.7 | §5 리스크 충실성 | Pass | R-1~R-9 9건, §5 하단 용어 일관성 검토 결과 6개 토큰 명시. decision_required 빈 배열 결론 적절 |
| 2.8 | 영향 범위 정정 합리성 | Pass | AGENT.md NO-OP 타당, 가이드 분류 타당 (§3 상세 검증) |

---

## 3. 지적 사항

### Warning-1 (GP-2.5): Step 완료 기준 정량화 미흡

**심각도**: Warning

**대상 Step**: Step 3, 5, 6, 8

- Step 3 완료 기준: "grep으로 `state-tool` 토큰이 §3 / §9 양쪽에 출현 확인" — 몇 건 이상이어야 Pass인지 불명확.
- Step 5 완료 기준: "본문에 `state init` 토큰 출현" — 1회만 출현해도 Pass로 판정될 수 있음.
- Step 6 완료 기준: "LLM 직접 갱신 표현이 0건, state-tool 호출 표현이 출현" — "출현" 횟수 미명시.
- Step 8 완료 기준: "7개 파일 grep 결과 LLM 직접 갱신 표현 0건" — 이 부분은 정량적으로 명확하나, `state-tool` 호출 표현 출현 건수 하한선이 없음.

**권고**: EXECUTE 단계에서 각 Step 검증 시 "LLM 직접 STATE.md 갱신 표현 0건 + state-tool 호출 표현 ≥1건" 패턴을 일관 적용하면 충분히 해소 가능. PLAN 재작성 불필요.

---

### Warning-2 (GP-2.6): §4 QA 체크리스트 — agentic na 자동 마킹 검증 항목 누락

**심각도**: Warning

**내용**: TASK T-2 / TASK 제약 "모드별 행 구성 차이"에서 "agentic 모드는 일부 사용자 확인 행이 `na`(-) 으로 자동 채워짐"이 명시되어 있으나, §4 일관성 테스트에 이에 대한 검증 항목이 없음. `state validate` 모드 일치 검출 항목(§4 기능 테스트 15번)에 부분적으로 포함되어 있으나, "init 시 agentic 모드 → na 행 자동 생성" happy path 자체가 §4 기능 테스트에 없음.

**권고**: EXECUTE 단계에서 F-23 dummy 태스크 (2) agentic×opd 회귀 표본으로 충분히 검증 가능. 별도 PLAN 수정 불필요.

---

## 4. 요구사항 커버리지 매핑 표 (F-1~F-23)

| 요구사항 | PLAN §3 Step | 비고 |
|---------|-------------|------|
| F-1 state-tool 디렉토리/파일 작성 | Step 1 (N-1~N-4) | 완전 커버 |
| F-2 서브 명령 7종 시그니처 | Step 1 (N-1), §2.1 | 완전 커버 |
| F-3 state.json 스키마 | Step 1 (N-3), §2.2 | 완전 커버 |
| F-4 STATE.md 자동 동기화 | Step 1 §2.1 (마커 교체 명세) | 완전 커버 |
| F-5 워커 권한 게이트 | Step 1 §2.4 (--as-worker --worker-stage 결정) | 완전 커버 |
| F-6 시점 자동 기록 | Step 1 §2.1 (subprocess date.js 호출 명세) | 완전 커버 |
| F-7 state.md 갱신 | Step 4 (M-1) | 완전 커버 |
| F-8 state-template.md 역할 축소 | Step 4 (M-2) | 완전 커버 |
| F-9 task-process.md 교체 | Step 4 (M-3) | 완전 커버 |
| F-10 pm-review-gate.md 자동 검증 추가 | Step 13 (M-4), §2.6 | 완전 커버 |
| F-11 additional-work.md 교체 | Step 13 (M-5) | 완전 커버 |
| F-12 harness-interactive + agentic 교체 | Step 13 (M-6, M-7) | 완전 커버 |
| F-13 opal-harness.md §3 + §9 갱신 | Step 3 (M-8) | 완전 커버 |
| F-14 AGENT.md STATE 표현 정합성 | M-9 (NO-OP 결정) | 완전 커버 — NO-OP 근거 `opal/core/AGENT.md:121-138` 직접 검토 |
| F-15 8개 오케스트레이터 SKILL.md | Step 6, Step 8 (M-10~M-17) | 완전 커버 |
| F-16 3개 단계 스킬 갱신 | Step 5 (M-18), Step 9 (M-20), M-19 NO-OP | 완전 커버 |
| F-17 8개 에이전트 정의 갱신 | Step 10 (M-21~M-28) | 완전 커버 |
| F-18 가이드 12개 분류 + 갱신 | §1 관련 파일 표 (실질 3개 / 단순 9개) + Step 11, 12 (M-29~M-39) | 완전 커버 |
| F-19 도구 등록부 갱신 | Step 14 (M-40) | 완전 커버 |
| F-20 install-mac.sh 갱신 | Step 15 (M-41) | 완전 커버 |
| F-21 단위 테스트 | Step 2 (N-5) | 완전 커버 |
| F-22 회귀 테스트 (134) | Step 7, §2.5 | 완전 커버 |
| F-23 추가 회귀 표본 | Step 16, §2.9 (dummy 2건 결정) | 완전 커버 |

**커버리지**: F-1~F-23 23/23 = 100%

---

## 4.1 T-1~T-13 기술 결정 반영 검증

| 기술 결정 | PLAN 반영 위치 | 결과 |
|---------|-------------|------|
| T-1 state.json 위치 | §2.2 스키마 task_id 패턴 + Step 7 완료 기준 | Pass |
| T-2 상태값 enum 매핑 | §2.2 스키마 properties.status enum | Pass |
| T-3 종료 코드 규약 | §2.1 구현 명세 + Step 1 완료 기준 | Pass |
| T-4 에러 응답 형식 | §2.1 응답 헬퍼 ok()/err() 패턴 | Pass |
| T-5 시점 기록 방법 | §2.1 subprocess date.js 호출 + §4 일관성 테스트 | Pass |
| T-6 마커 형식 | §2.1 마커 명세 + R-4 리스크 | Pass |
| T-7 advance/mark 분리 | §2.1 서브 명령 시그니처 + §4 기능 테스트 | Pass |
| T-8 init 멱등성 | §2.1 멱등성 명세 + §4 기능 테스트 | Pass |
| T-9 agentic auto-pass | §2.1 --auto-pass 명세 + M-7 agentic 하네스 | Pass |
| T-10 워커 권한 게이트 | §2.4 PLAN 결정 + §4 일관성 테스트 | Pass |
| T-11 Python 베이스 | §2.1 표준 라이브러리 import 목록 | Pass |
| T-12 호출 형식 | §2.1 7개 명령 시그니처 + §4 일관성 테스트 | Pass |
| T-13 134 마이그레이션 | §2.5 회귀 절차 + Step 7 | Pass |

**반영률**: T-1~T-13 13/13 = 100%

---

## 4.2 마이그레이션 순서 정합성 검증

TASK.md 제약 조건 순서: **도구 구현 → 단위 테스트 → 하네스 §3+§9 → state.md/state-template.md/task-process.md → op-task → opp → 134 회귀 → 나머지 pilot → 단계 스킬 → 에이전트 → 가이드 → 도구 등록부**

PLAN §3 Phase 구조:

| TASK 제약 순서 | PLAN Step | 정합 여부 |
|-------------|---------|---------|
| 도구 구현 | Step 1 (Phase 1) | 일치 |
| 단위 테스트 | Step 2 (Phase 1) | 일치 |
| 하네스 §3+§9 | Step 3 (Phase 2) | 일치 |
| state.md / state-template.md / task-process.md | Step 4 (Phase 2) | 일치 |
| op-task | Step 5 (Phase 3) | 일치 |
| opp(opal-pilot-project) | Step 6 (Phase 4) | 일치 |
| 134 자기 자신 회귀 | Step 7 (Phase 5) | 일치 |
| 나머지 pilot 일괄 | Step 8 (Phase 6, 병렬) | 일치 |
| 단계 스킬 | Step 9 (Phase 6, 병렬) | 일치 |
| 에이전트 | Step 10 (Phase 6, 병렬) | 일치 |
| 가이드 | Step 11, 12 (Phase 7, 병렬) | 일치 |
| pm-review-gate/additional-work/interactive/agentic | Step 13 (Phase 8) | 일치 |
| 도구 등록부 | Step 14 (Phase 8) | 일치 |

**의존 끊김/역행**: 없음. Phase 6(Step 8/9/10 병렬)이 Step 7(134 회귀) 이후라는 점도 TASK 제약의 "134 회귀 → 나머지 pilot" 순서와 정확히 일치. TASK 제약에 pm-review-gate/additional-work/interactive/agentic 순서가 별도로 명시되지 않았으나, PLAN에서 하네스 갱신 군(Step 13)이 가이드(Step 11/12) 이후로 배치된 이유가 명확하지 않다는 점은 Info 수준 관찰 사항 (진행 차단 아님 — 하네스 §3+§9는 Step 3에서 이미 선행 처리됨).

---

## 4.3 인용 규칙 준수 (citation-rules.md §4 PLAN 의무 수준)

| 항목 | 요구사항 | 확인 결과 |
|------|---------|---------|
| §1 참조 문서 테이블 | 필수 (D-N, 유형, 경로, 참조 이유) | D-1~D-19 19개 항목, 전체 4컬럼 완비 |
| 인라인 인용 | 필수 — `(→ D-N §N)` 또는 풀 포맷 | §2.1~§2.10 각 결정에 `(→ TASK T-N)` / `(→ D-N)` 형태 일관 사용 |
| [MUST] 포맷 | 필수 — 핵심 설계 중 금지/강제 규칙 | 3건: `~/.opal/` 직접 수정 금지, citation-rules §0 근거 제시 원칙, 개발 vs 배포 경계 |
| 재해석 방지 | 금지/강제 규칙은 원문 인용 | [MUST] 항목에 문서 경로 + 원문 또는 요약 포함 |
| 추측·기억 기반 금지 | §0 원칙 | PLAN §1 파일 참조 시 줄번호 명시 패턴 준수 |

---

## 4.4 Step 완료 기준 검증 가능성 (전체 스캔)

| Step | 완료 기준 | 판정 가능성 |
|------|---------|-----------|
| Step 1 | 7개 명령 --help 응답 / JSON 응답 / 종료 코드 / init 정상 동작 | Pass/Fail 명확 |
| Step 2 | `python3 -m unittest` 0 fail, 0 error | Pass/Fail 명확 |
| Step 3 | grep state-tool 출현 확인 | Warning — 건수 기준 없음 |
| Step 4 | 3개 파일 절대 경로 일관 사용 | Pass/Fail 명확 |
| Step 5 | state init 토큰 출현 | Warning — 최소 출현 횟수 미명시 |
| Step 6 | LLM 직접 갱신 0건 + state-tool 출현 | Warning — state-tool 최소 횟수 미명시 |
| Step 7 | violations 0건 + 13개 행 임포트 + 영역 보존 | Pass/Fail 명확 |
| Step 8 | 7개 파일 LLM 직접 갱신 0건 | Warning — state-tool 출현 기준 없음 |
| Step 9~16 | grep 토큰 출현 또는 수동 검증 | 대체로 명확 (grep 기준이 명시된 경우) |

---

## 4.5 영향 범위 정정 합리성 검증

### AGENT.md NO-OP 결정 검증

`opal/core/AGENT.md:121-138` 실제 내용 확인:

- 121-138 라인은 "소유자 오버라이드" 테이블 — `//` 커맨드 / "그냥 해" / "비서로" 모드 설명
- 특히 133 라인: `| **미적용** | STATE.md 생성/갱신 | ❌ |` — "그냥 해" 모드에서 STATE.md 갱신이 **미적용**임을 명시
- 즉, 이 표는 "태스크 파이프라인이 적용되지 않는 경우" 규정이며, state-tool 도입으로 갱신이 필요한 "STATE.md 갱신 주체/방법" 규정이 아님

**결론**: NO-OP 결정 타당. state-tool 도입과 무관한 "그냥 해 모드에서의 예외 규정"이므로 본 태스크에서 수정 불필요. PLAN §1 관련 파일 표의 근거("STATE 표현이 모두 '그냥 해' 모드 미적용 규정에 한정")와 일치.

### 가이드 분류 샘플 검증 (단순 참조 분류 3건)

**wbs-guide.md L242**: `"STATE.md를 갱신했는가 (2-WBS → 확정, WBS 액션 목록 반영)"` — 체크리스트 1항목으로 절차 본문이 아님. "단순 참조" 분류 타당.

**verify-guide.md L171**: SDD VERIFY 가이드 L171 주변 — "STATE.md 의사결정 로그에 기록"(자유 텍스트 영역). 본 태스크 범위 외. "단순 참조" 분류 타당.

**done-template.md L57**: `"STATE.md 실행 요약 테이블 갱신 완료"` — 완료 체크리스트 항목 1줄. "단순 참조" 분류 타당.

**결론**: 샘플 3건 모두 PLAN의 "단순 참조 vs 실질 갱신" 분류 기준("체크리스트/단일 문장 참조면 단순 참조")과 일치. 분류 타당.

---

## 5. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md F-1~F-23 | PLAN §3 Step 전체 매핑 | Pass — 23/23 커버 |
| TASK.md T-1~T-13 | PLAN §2 핵심 설계 반영 | Pass — 13/13 반영 |
| TASK.md 제약 조건 마이그레이션 순서 | PLAN §3 Phase 1~9 의존 관계 | Pass — 역행 없음 |
| TASK.md 미확정 #1~#9 | PLAN §2.3~§2.10 결정 여부 | Pass — 8/9 결정, #1(영향 범위) = §1에서 해소 |
| citation-rules.md §4 PLAN 의무 수준 | §1 참조 테이블 + 인라인 인용 + [MUST] | Pass |
| opal/core/AGENT.md:121-138 | F-14 NO-OP 결정 근거 | Pass — 직접 Read 검증 완료 |

---

## 6. TASK.md 체크리스트 갱신 판단

qa-standards.md 규칙: "PLAN QA 단계에서는 TASK.md 요구사항 체크박스 중 PLAN.md가 커버하는 요구사항을 `[x]`로 갱신한다."

op-task-qa SKILL.md Step 4 규칙: "검증을 통과한 항목만 `[x]`로 갱신."

**판단**: PLAN.md는 F-1~F-23의 **설계**를 다루었으나, 실제 **구현(코드 작성/파일 수정)**은 EXECUTE 단계에서 수행된다. opp 스킬은 개발 트랙에 해당하므로 F 시리즈 요구사항의 "구현 완료" 여부는 EXECUTE QA에서 판정하는 것이 적절하다.

PLAN 단계에서 `[x]`로 갱신할 수 있는 항목은 "PLAN에서 설계·분류 결정을 내리도록 TASK.md에 명시된 항목"이다:

- **F-18** "PLAN 단계에서 grep + 본문 분석으로 실질 갱신 vs 단순 참조를 분류. 분류 결과는 PLAN.md에 명시" — 이 AC는 PLAN 단계 완료 조건이며 PLAN.md §1에 분류 결과가 명시되어 있음. → `[x]` 갱신 대상

그 외 F-1~F-17, F-19~F-23은 구현 또는 실행 검증이 AC의 핵심이므로 EXECUTE 완료 후 QA에서 갱신.

**갱신 항목**: F-18 단 1건.

---

## 7. 판정

**Pass**

PLAN.md는 F-1~F-23 / T-1~T-13 전항목을 커버하며, 마이그레이션 순서 의존 관계, citation-rules 인용 의무, TASK 미확정 사항 8건 결정, 영향 범위 정정 근거를 모두 충족한다. Warning 2건(Step 완료 기준 정량화 미흡, agentic na 마킹 검증 항목 누락)은 EXECUTE 단계에서 보완 가능한 경미한 수준이며, 즉시 EXECUTE 진행을 차단하지 않는다.
