# PLAN: PLAN 워커 컨벤션 [MUST] 인용 강제 — 사전 주입 강화

> 작성일: 2026-05-08
> 입력: TASK.md
> 출력: PLAN.md
> 모드: 범용 (op-task-plan, OPAL 프레임워크 메타 수정)

---

## 1. 현황 조사

### 1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | PM 디스패치 전 프로세스 SSOT — 잠재 적용 지점 #1 (§Step 3 인용 의무 카탈로그) |
| D-2 | 설계 | opal-plan-agent AGENT.md | `opal/agents/opal-plan-agent/AGENT.md` | PLAN 에이전트 행동 규칙 + 자체 로드 문서 명세 — 잠재 적용 지점 #2 |
| D-3 | 설계 | op-task-plan SKILL.md | `opal/skills/op-task-plan/SKILL.md` | 범용 PLAN 단계 스킬 + 품질 체크리스트 — 잠재 적용 지점 #3a |
| D-4 | 설계 | op-dev-plan SKILL.md | `opal/skills/op-dev-plan/SKILL.md` | dev PLAN 단계 스킬 + 품질 체크리스트 — 잠재 적용 지점 #3b |
| D-5 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 규약 SSOT — 잠재 적용 지점 #4 (§2.5 [MUST] 토큰 대상) |
| D-6 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 컨벤션 SSOT — 인용 대상 (각 프로젝트별 별도 파일) |
| D-7 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | 프로젝트 정의 + 문서 테이블 |
| D-8 | 설계 | task 136 PLAN.md | `tasks/136-260508-opp-pm-gate-convention-auto-check/` | 사후 검증(B) 분리 명시 — 본 태스크와의 책임 분담 근거 |
| D-9 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | PM 행동 프로세스 — §3 디스패치 전 프로세스 진입점 |
| D-10 | 설계 | opal-pilot-{project,dev,dev-short,dev-wireframe} SKILL.md | `opal/skills/opal-pilot-*/SKILL.md` | PLAN 단계 디스패치 프롬프트 템플릿 보유 — R-1 적용 영향 범위 |
| D-11 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | 태스크 136 산출물 — §13 컨벤션 자동 진단 (사후 검증 B), 본 태스크와 책임 분리 정합성 검증 대상 |
| D-12 | 설계 | op-task-plan plan-guide.md | `opal/skills/op-task-plan/references/plan-guide.md` | op-task-plan 스킬의 상세 가이드 — 품질 체크리스트 포함 |
| D-13 | 설계 | opal-pilot-project SKILL.md (PLAN 디스패치) | `opal/skills/opal-pilot-project/SKILL.md:35-67` | opp PLAN 디스패치 프롬프트 — "핵심 제약" 필드 부재 확인됨 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조. 유형: `기획` / `설계` / `소스` / `외부`.

### 1.2 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/pm/dispatch-process.md` | PM 디스패치 전 프로세스 SSOT | **수정** (R-1 SSOT) | `opal/core/references/pm/dispatch-process.md:48-65` |
| `opal/skills/op-task-plan/SKILL.md` | op-task-plan 스킬 본문 + 품질 체크리스트 | **수정** (R-3 절반) | `opal/skills/op-task-plan/SKILL.md:187-201` |
| `opal/skills/op-task-plan/references/plan-guide.md` | op-task-plan 상세 가이드 + 품질 체크리스트 | **수정** (R-3 절반) | `opal/skills/op-task-plan/references/plan-guide.md:149-159` |
| `opal/skills/op-dev-plan/SKILL.md` | op-dev-plan 스킬 본문 + 품질 체크리스트 | **수정** (R-3 절반) | `opal/skills/op-dev-plan/SKILL.md:415-437` |
| `opal/agents/opal-plan-agent/AGENT.md` | PLAN 전문 워커 행동 규칙 + 자체 로드 문서 | **참조 강화 (선택)** | `opal/agents/opal-plan-agent/AGENT.md:33-46, 83-89` |
| `opal/core/references/harness/citation-rules.md` | 인용 규약 SSOT | **변경 없음** (R-4 비채택) | `opal/core/references/harness/citation-rules.md:133-165` |
| `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/SKILL.md` | PM 디스패치 프롬프트 템플릿 | **변경 없음** (D-1 SSOT 참조 구조) | `opal/skills/opal-pilot-project/SKILL.md:55-58` |
| `docs/CONVENTIONS.md` | 컨벤션 SSOT (각 프로젝트별) | **변경 없음** (인용 대상) | - |

### 1.3 현재 상태

#### (1) D-1 (dispatch-process.md §Step 3) — 인용 의무 카탈로그

`opal/core/references/pm/dispatch-process.md:48-65`에 "인용 의무 규칙" 표가 정의되어 있다. 현재 카탈로그:

> **[MUST]** `` `opal/core/references/pm/dispatch-process.md` §Step 3: "원문 인용 필수: 금지사항, 아키텍처 강제 규칙, 재해석 여지가 있는 정책·명세·도메인 규칙 → `[MUST] <문서명> §N: <규칙 원문>` 형식으로 직접 인용" ``

`docs/CONVENTIONS.md`의 **[MUST]/금지/네이밍 규칙**은 "금지사항"과 "아키텍처 강제 규칙"에 추상적으로 포함되지만, **카탈로그에 명시 부재**. PM 재량으로 "선호 가이드라인"으로 분류하여 요약 처리할 위험이 있다.

PM 워커 컨텍스트 주입 템플릿(`opal/core/references/pm/dispatch-process.md:80-97`)의 "핵심 제약" 섹션 예시도 BE-FRAMEWORK / ARCHITECTURE만 보여주고 CONVENTIONS는 없다.

#### (2) D-2 (opal-plan-agent AGENT.md) — 자체 로드 문서 + 행동 규칙

`opal/agents/opal-plan-agent/AGENT.md:33-46`의 §자체 로드 문서:

> **[MUST]** `` `opal/agents/opal-plan-agent/AGENT.md` §자체 로드 문서: "1. docs/PROJECT.md / 2. docs/ARCHITECTURE.md / 3. docs/CONVENTIONS.md / 4. 도메인 문서 전체 ... 각 파일은 존재하는 경우에만 Read하고, 없으면 스킵한다" ``

Read 의무는 명확하지만, **Read한 CONVENTIONS.md [MUST] 항목을 PLAN.md에 옮겨 박는 의무는 미정의**. AGENT.md `:83-89`의 §행동 규칙 5개 항목 중 인용 관련 항목 부재.

다만 op-task-plan/op-dev-plan SKILL.md에 citation-rules trigger 1줄(§2.4 [MUST] 포맷)이 이미 주입되어 있으므로, **워커가 SKILL.md 프로세스를 정확히 따르면 인용 자체는 강제**된다. AGENT.md 별도 강제 없이도 SKILL.md 경로로 결과물 도달 가능 → **D-2는 보조 강화 후보**.

#### (3) D-3 (op-task-plan SKILL.md + plan-guide.md 품질 체크리스트)

`opal/skills/op-task-plan/SKILL.md:198-200` 및 `opal/skills/op-task-plan/references/plan-guide.md:157-159`:

> **[MUST]** `` `opal/skills/op-task-plan/SKILL.md` §품질 체크리스트: "재해석 여지가 있는 제약은 [MUST] 포맷으로 기재되어 있는가 (citation-rules.md §2.4)" ``

이 항목은 **포괄적**이며 "재해석 여지가 있는 제약" 안에 컨벤션 [MUST]/금지/네이밍이 포함된다. 하지만 **컨벤션을 명시 대상으로 호명하지 않으므로** 워커/QA가 누락할 수 있다. QA Gate 자동 검출의 신호 강도가 약하다.

#### (4) D-4 (op-dev-plan SKILL.md 품질 체크리스트)

`opal/skills/op-dev-plan/SKILL.md:435-437`:

D-3과 동일 항목 보유. 동일 문제. 두 SKILL.md를 동시 갱신해야 일관성 유지.

#### (5) D-5 (citation-rules.md §2.5 [MUST] 토큰 대상 6종)

`opal/core/references/harness/citation-rules.md:133-165`:

> **[MUST]** `` `opal/core/references/harness/citation-rules.md` §2.5: "개발 트랙에서 [MUST] 인용이 반드시 필요한 구체 토큰 유형 6종: (1) 필드명 (2) 함수 시그니처 (3) 타입명 (4) ERD 컬럼명 (5) IA 화면 ID/라우트 (6) 정책 조항 번호" ``

**§2.5는 헤더가 "개발 트랙 [MUST] 토큰 대상"** — 비개발 트랙에는 비적용. 컨벤션 [MUST] 규칙은 (1) 필드명 / (3) 타입명 / (6) 정책 조항을 통해 이미 사실상 커버되며, 컨벤션 자체는 §2.4 [MUST] 일반 포맷으로 인용 가능. 7번째 토큰 신설 시 기존 6종과 의미 중복 발생.

#### (6) D-10 (opal-pilot-* SKILL.md 디스패치 프롬프트) — 분기 확인

- `opal/skills/opal-pilot-dev/SKILL.md:69`, `opal/skills/opal-pilot-dev-short/SKILL.md:97`, `opal/skills/opal-pilot-dev-wireframe/SKILL.md:109`: 디스패치 프롬프트 템플릿에 `**핵심 제약**: {[MUST] <문서명> §N: <인용문> 형식 원문 인용}` 필드 명시.
- `opal/skills/opal-pilot-project/SKILL.md:35-67` (opp): **"핵심 제약" 필드 부재** — `[PM 컨텍스트 주입]` 블록(`:55-58`)에 "관련 참조 문서 경로", "기술 스택 연동 지시"만 명시.

opp PLAN 디스패치는 D-1 dispatch-process.md를 PM이 직접 따르므로 D-1 SSOT 갱신만으로 흐름 통일 가능.

#### (7) D-11 (pm-review-gate.md §13) — 사후 검증(B)과의 책임 분리

`opal/core/references/harness/pm-review-gate.md:47-62`:

§13 "컨벤션 자동 진단"은 **EXECUTE 단계 PM Gate**에서 워커 반환 `changed_files`를 대상으로 opal-convention-checker를 호출하는 사후 검출 시스템. **PLAN.md 자체는 검사 대상이 아님** (changed_files만 검사).

→ **본 태스크(A)는 PLAN.md 작성 시점의 사전 차단**, **136(B)는 EXECUTE 결과의 사후 검출**. 검사 시점·대상·메커니즘이 모두 분리되어 충돌하지 않으며, 이중 안전망 시너지 형성.

### 1.4 영향 범위

#### 변경 시 영향을 받는 파일

| 영역 | 파일 | 영향 |
|------|------|------|
| PM SSOT | `opal/core/references/pm/dispatch-process.md` | §Step 3 인용 의무 카탈로그 명시화 → opp/opd/opds/opdw 모든 PM 디스패치 흐름이 자동 적용 (참조 구조) |
| PLAN 스킬 | `opal/skills/op-task-plan/SKILL.md` + `opal/skills/op-task-plan/references/plan-guide.md` | 품질 체크리스트 1행 추가 → op-task-plan 워커 산출물 검증 강화. opp 흐름에 영향. |
| PLAN 스킬 | `opal/skills/op-dev-plan/SKILL.md` | 품질 체크리스트 1행 추가 → op-dev-plan 워커 산출물 검증 강화. opd/opds/opdw 흐름에 영향. |
| PLAN 에이전트 (선택) | `opal/agents/opal-plan-agent/AGENT.md` | 보조 강화 — 행동 규칙 1행 추가. opd/opds 등 advanced PLAN 흐름에서 SKILL.md 외 추가 안전망 |

#### 변경 없이 그대로 작동하는 파일

| 파일 | 사유 |
|------|------|
| `opal/core/references/harness/citation-rules.md` | §2.5는 개발 트랙 토큰 6종 한정. 컨벤션 [MUST]는 §2.4 일반 포맷으로 충분히 커버. 7번째 토큰 신설 시 의미 중복 (R-4 비채택 근거) |
| `opal/skills/opal-pilot-*/SKILL.md` | 디스패치 프롬프트의 "핵심 제약" 필드는 D-1 SSOT를 참조함. SSOT 갱신으로 자동 강화 (참조 구조) |
| `docs/CONVENTIONS.md` | 본 태스크의 인용 대상이며 변경 대상 아님 |

#### 영향 받지 않는 흐름

- `docs/CONVENTIONS.md` 부재 프로젝트: D-1 §Step 3 "선별된 문서를 직접 Read하여" 단계에서 **CONVENTIONS.md 자체가 선별되지 않음** → 본 의무는 자연 스킵 (R-5 보장).
- D-2 opal-plan-agent의 `:33-46` 자체 로드 문서 §"각 파일은 존재하는 경우에만 Read하고, 없으면 스킵한다" 룰이 동일 보장.

---

## 2. 구현 계획

### 2.1 잠재 적용 지점 4개 채택 결정 (R-6)

| 지점 | 결정 | 근거 |
|------|------|------|
| **#1 (D-1 dispatch-process.md §Step 3)** | **채택 (SSOT 1순위)** | PM 디스패치 측 강제의 진본. opal-pilot-* SKILL.md는 이를 참조하므로 SSOT 1곳 수정으로 4개 오케스트레이터(opp/opd/opds/opdw) 모두 자동 적용. 최소 변경 원칙 부합. |
| **#2 (D-2 opal-plan-agent AGENT.md)** | **부분 채택 — 보조 강화** | SKILL.md citation-rules trigger가 이미 인용 자체를 강제하므로 AGENT.md는 불필요할 수 있으나, 행동 규칙 1행으로 명시화하여 워커 누락 위험 차단. opal-task-agent(opp 흐름)는 영향 받지 않으므로 AGENT.md만 수정해도 opp 흐름은 D-3가 커버. **#3과 중복 안전망**. |
| **#3 (D-3 + D-4 SKILL.md 품질 체크리스트)** | **채택 (QA 자동 검출 1순위)** | op-task-qa / op-dev-qa가 이 SKILL.md 품질 체크리스트를 따라 PLAN.md를 검증하므로, 여기에 컨벤션 [MUST] 항목을 명시하면 워커 종류 무관 모든 PLAN.md에 적용. R-3 AC 직접 충족. |
| **#4 (D-5 citation-rules.md §2.5)** | **비채택** | (a) §2.5 헤더가 "개발 트랙" 한정이며 컨벤션 [MUST]는 비개발 트랙에서도 강제되어야 하므로 §2.5에 7번째 토큰 추가 시 트랙 매트릭스(§1.5)와 의미 충돌 (b) 기존 6종 토큰(필드명/타입명/정책 조항)이 사실상 컨벤션 [MUST] 규칙의 90%+ 커버 (c) §2.4 일반 포맷이 7번째 토큰 신설 없이도 컨벤션 인용에 충분. R-4 AC 충족 — "추가하지 않은 사유"를 본 §2.1 / §리스크에 명시. |

**최소 변경 정합성**: 채택 지점 = #1 (SSOT) + #3 (QA 검출) + #2 부분 (보조). 변경 파일 4개. 4개 잠재 지점 전부 변경(=5개 파일+, citation-rules 규약 충돌)보다 2~3개 파일 적게 변경하면서 동일 효과 달성. 참조 구조(opal-pilot-* → D-1) 활용으로 4개 오케스트레이터에 자동 전파.

### 2.2 136(사후 검증 B)와 책임 분리 + 시너지

| 축 | 본 태스크 (사전 주입 A) | 태스크 136 (사후 검증 B) |
|----|---------------------|----------------------|
| 검사 시점 | PLAN.md 작성 중·작성 후 QA Gate | EXECUTE 완료 후 PM Gate |
| 검사 대상 | PLAN.md 자체 (코드 예시 포함) | 워커 반환 `changed_files` (실제 변경된 코드) |
| 메커니즘 | 워커 자체 인용 의무 + QA 체크리스트 항목 | opal-convention-checker 자동 호출 → GC-CONVENTION-*.md |
| 차단 단계 | EXECUTE 진입 전 (PLAN Gate) | TEST 진입 전 (EXECUTE Gate) |
| 산출물 | PLAN.md §1·§2의 컨벤션 [MUST] 인용 | GC-CONVENTION-*.md 진단 보고서 |

**시너지**:
- A 통과 → PLAN.md에 컨벤션 [MUST] 박힘 → EXECUTE 워커가 컨벤션 준수 코드 생산 → B는 위반 0건이 정상 (스킵 또는 PASS).
- A 누락 시: PLAN.md에 컨벤션 위반 코드 예시 → EXECUTE 워커가 모방 → B가 changed_files에서 검출 → 1회 재지시. **B는 A 누락의 안전망**.
- B 누락 시(`docs/CONVENTIONS.md` 부재 등): A의 사전 인용도 자연 스킵되므로 일관된 동작.

**책임 분리 명시 위치**: 본 §2.2 + §리스크 R-T2.

**충돌 검증**: 136 산출물 `opal/core/references/harness/pm-review-gate.md:47-62` §13 "컨벤션 자동 진단"은 EXECUTE 단계만 트리거. PLAN 단계 PM Gate는 영향 받지 않음. 본 태스크의 D-1 §Step 3 카탈로그 명시화는 디스패치 전 단계로 §13 트리거 시점 이전. **충돌 없음**.

### 2.3 파일 변경 계획

#### 2.3.1 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| - | (없음) | 본 태스크는 기존 진본 SSOT 갱신 한정 | - |

#### 2.3.2 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/pm/dispatch-process.md` | §Step 3 "인용 의무 규칙" 표의 "원문 인용 필수" 행에 **"코드 컨벤션의 [MUST]/금지/네이밍 규칙(`docs/CONVENTIONS.md` 등)"** 명시 추가. 워커 컨텍스트 주입 템플릿(`:80-97`)의 "핵심 제약" 예시에 컨벤션 인용 사례 1행 추가. (→ D-1 §Step 3) | R-1 AC + 채택 결정 §2.1 #1 |
| M-2 | `opal/skills/op-task-plan/SKILL.md` | §품질 체크리스트(`:187-201`)에 **"`docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 산출물 코드 예시·설계에 영향을 주는 항목이 §1 참조 문서 테이블 또는 §2 핵심 설계에 [MUST] 포맷으로 인용되어 있는가 (CONVENTIONS.md 부재 시 자동 스킵)"** 1행 추가. 변경이력 1행 추가. (→ D-3 §품질 체크리스트) | R-3 AC + 채택 결정 §2.1 #3 |
| M-3 | `opal/skills/op-task-plan/references/plan-guide.md` | §품질 체크리스트(`:149-159`)에 M-2와 동일 항목 1행 추가 (SKILL.md와 plan-guide.md가 양쪽 모두 품질 체크리스트 보유 → 동시 갱신 필요). 변경이력 1행 추가. (→ D-12) | R-3 AC + SKILL.md/plan-guide.md 일관성 |
| M-4 | `opal/skills/op-dev-plan/SKILL.md` | §품질 체크리스트(`:415-437`)에 M-2와 동일 항목 1행 추가. 변경이력 1행 추가. (→ D-4 §품질 체크리스트) | R-3 AC + 채택 결정 §2.1 #3 (대칭성) |
| M-5 | `opal/agents/opal-plan-agent/AGENT.md` | §행동 규칙(`:83-89`)에 **"[MUST] 자체 로드한 `docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 설계에 영향을 주는 항목은 PLAN.md §1 참조 문서 테이블 또는 §2 핵심 설계에 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>` 포맷으로 인용한다 (CONVENTIONS.md 부재 시 자동 스킵)"** 1행 추가. (→ D-2 §행동 규칙) | R-2 AC + 채택 결정 §2.1 #2 (부분 채택, 보조 강화) |

#### 2.3.3 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | - |

### 2.4 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | M-1 dispatch-process.md §Step 3 카탈로그 명시화 (SSOT) | `opal/core/references/pm/dispatch-process.md` | 낮음 (명시 추가만) |
| 2 | M-2 op-task-plan SKILL.md 품질 체크리스트 항목 추가 | `opal/skills/op-task-plan/SKILL.md` | 낮음 |
| 3 | M-3 op-task-plan plan-guide.md 품질 체크리스트 항목 추가 | `opal/skills/op-task-plan/references/plan-guide.md` | 낮음 |
| 4 | M-4 op-dev-plan SKILL.md 품질 체크리스트 항목 추가 | `opal/skills/op-dev-plan/SKILL.md` | 낮음 |
| 5 | M-5 opal-plan-agent AGENT.md 행동 규칙 1행 추가 | `opal/agents/opal-plan-agent/AGENT.md` | 낮음 |
| 6 | 통합 검증 — `docs/CONVENTIONS.md` 부재 프로젝트 영향 0건 + 136 §13과 충돌 0건 | (검토 전용) | 낮음 |

**의존성**: 5개 수정 파일 모두 **상호 독립** (참조 구조이지만 동시 수정 시 충돌 없음). Phase 1에서 5개 모두 병렬 가능. Step 6은 통합 검증으로 Phase 2.

> 원칙: 의존 받는 쪽(하위 레이어)부터 구현 — 본 태스크는 5개 파일 모두 같은 레이어(메타 문서)이며 cross-reference 없음.

### 2.5 핵심 설계

#### M-1 — `opal/core/references/pm/dispatch-process.md` §Step 3 SSOT 명시화

> [MUST] `opal/core/references/pm/dispatch-process.md` §Step 3 (현재): "원문 인용 필수: 금지사항, 아키텍처 강제 규칙, 재해석 여지가 있는 정책·명세·도메인 규칙 → `[MUST] <문서명> §N: <규칙 원문>` 형식으로 직접 인용" (→ D-1 §Step 3)

**변경 내용**:

(a) "인용 의무 규칙" 표의 "원문 인용 필수" 행 "기준" 컬럼에 **명시 항목 1줄 추가**:

```
+ 코드 컨벤션의 [MUST]/금지/네이밍 규칙 (`docs/CONVENTIONS.md` 등)
```

(b) 표 하단의 예시 섹션에 **컨벤션 인용 예시 1행 추가**:

```
+ - `[MUST] CONVENTIONS.md §3.1: API 응답은 camelCase를 사용한다. 직렬화 시 snake_case 금지.`
```

(c) "워커 컨텍스트 주입 템플릿" 섹션의 "## 핵심 제약" 예시에 **컨벤션 [MUST] 항목 예시 1행 추가**:

```
+ - [MUST] CONVENTIONS.md §N: <컨벤션 강제 규칙 원문>  ← 컨벤션 [MUST]/금지/네이밍 (해당 시)
```

(d) "## 핵심 제약" 블록 아래에 **하위 호환 1줄 추가**:

```
+ > `docs/CONVENTIONS.md` 부재 시 본 항목은 자연 스킵 (Step 2 문서 선별에서 제외됨)
```

**의도**: opal-pilot-{project,dev,dev-short,dev-wireframe} SKILL.md의 "핵심 제약" 필드는 D-1을 참조하므로, D-1 1곳 갱신으로 4개 오케스트레이터의 PM 디스패치 흐름이 자동 강화됨 (참조 구조 활용).

**citation-rules.md §2.4 [MUST] 포맷 준수**: 추가되는 카탈로그 항목 자체를 [MUST] 포맷으로 박을 필요는 없음 — 본 항목은 dispatch-process 표 셀 정의이며 표 자체가 인용 의무 SSOT이다. 다만 예시는 §2.4 포맷을 준수하여 표시.

#### M-2 — `opal/skills/op-task-plan/SKILL.md` §품질 체크리스트

> [MUST] `opal/skills/op-task-plan/SKILL.md` §품질 체크리스트 (현재): "재해석 여지가 있는 제약은 [MUST] 포맷으로 기재되어 있는가 (citation-rules.md §2.4)" (→ D-3 §품질 체크리스트)

**변경 내용**:

기존 마지막 항목 다음에 **신규 항목 1행 추가**:

```
+ - [ ] `docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 산출물의 코드 예시·설계 결정에 영향을 주는 항목이 §1 참조 문서 테이블 또는 §2 핵심 설계에 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>` 포맷으로 인용되어 있는가 (CONVENTIONS.md 부재 프로젝트는 자동 스킵 — D-1 §Step 2 문서 선별에서 제외)
```

§변경이력에도 v1.4 행 추가 (137 컨벤션 [MUST] 인용 항목 신설).

**의도**: op-task-qa가 PLAN.md를 검증할 때 본 항목을 자동 적용 → 워커 누락 시 QA Gate에서 검출.

#### M-3 — `opal/skills/op-task-plan/references/plan-guide.md` §품질 체크리스트

> [MUST] `opal/skills/op-task-plan/references/plan-guide.md` §품질 체크리스트 (현재): SKILL.md와 동일 항목 9개 보유 (→ D-12)

**변경 내용**: M-2와 동일 1행 추가. SKILL.md와 plan-guide.md가 양쪽에 품질 체크리스트를 가지고 있어(citation-rules trigger가 양쪽에 트리거 1줄을 주입한 패턴 동일) **두 파일 모두 동시 갱신 필요**. §변경이력에 v1.2 행 추가.

#### M-4 — `opal/skills/op-dev-plan/SKILL.md` §품질 체크리스트

> [MUST] `opal/skills/op-dev-plan/SKILL.md` §품질 체크리스트 (현재): "재해석 여지가 있는 제약은 [MUST] 포맷으로 기재되어 있는가 (citation-rules.md §2.4)" (→ D-4)

**변경 내용**: M-2와 동일 1행 추가. dev 트랙(opd/opds/opdw)에서도 컨벤션 인용 강제. §변경이력에 v2.5 행 추가.

#### M-5 — `opal/agents/opal-plan-agent/AGENT.md` §행동 규칙

> [MUST] `opal/agents/opal-plan-agent/AGENT.md` §행동 규칙 (현재): 5개 항목 — "스킬 SKILL.md의 프로세스를 정확히 따른다" 등 (→ D-2 §행동 규칙)

**변경 내용**:

§행동 규칙 마지막에 **신규 항목 1행 추가** (4번째와 5번째 사이 또는 마지막):

```
+ - [MUST] 자체 로드한 `docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 설계에 영향을 주는 항목은 PLAN.md §1 참조 문서 테이블 또는 §2 핵심 설계에 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>` 포맷으로 인용한다 (CONVENTIONS.md 부재 시 자동 스킵 — §자체 로드 문서 "각 파일은 존재하는 경우에만 Read하고, 없으면 스킵한다" 룰 상속).
```

**의도**: opal-plan-agent(advanced 모델 PLAN 워커, opd/opds 흐름)가 SKILL.md 프로세스 준수 외에 추가 안전망. opp 흐름은 opal-task-agent를 사용하므로 영향 없음 — opp 흐름은 M-2/M-3가 커버.

**citation-rules.md §2.4 준수**: 본 항목 자체를 [MUST] 포맷으로 박음 (재해석 여지가 있는 강제 규칙).

---

## 3. 실행 체크리스트

> 총 6개 Step | Phase 2개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1, 2, 3, 4, 5 | 병렬 | 5개 파일 모두 독립 — 상호 의존 없음 |
| 2 | 6 | 순차 | 통합 검증 (Phase 1 완료 후) |

### Step 1: dispatch-process.md §Step 3 인용 의무 카탈로그 명시화 + 워커 컨텍스트 주입 템플릿 갱신
- [x] 완료
- **agent**: opal-task-agent
- **파일**: `opal/core/references/pm/dispatch-process.md`
- **작업 내용**:
  - "인용 의무 규칙" 표의 "원문 인용 필수" 기준 컬럼에 "코드 컨벤션의 [MUST]/금지/네이밍 규칙(`docs/CONVENTIONS.md` 등)" 1행 명시
  - 표 하단 예시 섹션에 컨벤션 인용 예시 1행 추가 (`[MUST] CONVENTIONS.md §3.1: ...`)
  - "워커 컨텍스트 주입 템플릿" §"## 핵심 제약" 예시에 컨벤션 [MUST] 항목 1행 추가
  - 하위 호환 1줄 명시: "`docs/CONVENTIONS.md` 부재 시 본 항목은 자연 스킵 (Step 2 문서 선별에서 제외됨)"
- **완료 기준**: §Step 3 표·예시·템플릿 3곳 갱신 + 하위 호환 명시. opal-pilot-{project,dev,dev-short,dev-wireframe} SKILL.md 디스패치 프롬프트가 본 SSOT를 참조하므로 추가 변경 없이 4개 오케스트레이터에 전파.
- **테스트**: §4 QA 체크리스트 R-1·R-5 항목 충족 확인. 변경 후 dispatch-process.md를 다시 Read하여 카탈로그·예시·템플릿 3곳에 "CONVENTIONS" / "컨벤션" 키워드 검출.
- **의존**: 없음

### Step 2: op-task-plan SKILL.md 품질 체크리스트에 컨벤션 [MUST] 항목 추가
- [x] 완료
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-task-plan/SKILL.md`
- **작업 내용**:
  - §품질 체크리스트 마지막에 신규 항목 1행 추가 — "`docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 산출물의 코드 예시·설계 결정에 영향을 주는 항목이 §1 참조 문서 테이블 또는 §2 핵심 설계에 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>` 포맷으로 인용되어 있는가 (CONVENTIONS.md 부재 프로젝트는 자동 스킵)"
  - §변경이력에 v1.4 행 추가 — "137 — 컨벤션 [MUST] 인용 항목 신설"
- **완료 기준**: 품질 체크리스트에 신규 1행 + 변경이력 갱신. op-task-qa가 PLAN.md 검증 시 본 항목을 자동 적용.
- **테스트**: 변경 후 SKILL.md를 Read하여 §품질 체크리스트 마지막 항목 텍스트 확인.
- **의존**: 없음

### Step 3: op-task-plan plan-guide.md 품질 체크리스트에 컨벤션 [MUST] 항목 추가 (SKILL.md와 동시 갱신)
- [x] 완료
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-task-plan/references/plan-guide.md`
- **작업 내용**:
  - §품질 체크리스트 마지막에 Step 2와 동일 항목 1행 추가
  - §변경이력에 v1.2 행 추가 — "137 — 컨벤션 [MUST] 인용 항목 신설"
- **완료 기준**: SKILL.md와 plan-guide.md 양쪽 품질 체크리스트가 동일 항목 보유 (citation-rules trigger 1줄 패턴과 동일한 양쪽 동기화).
- **테스트**: 두 파일의 §품질 체크리스트 마지막 항목이 동일 텍스트인지 diff 확인.
- **의존**: 없음 (Step 2와 다른 파일)

### Step 4: op-dev-plan SKILL.md 품질 체크리스트에 컨벤션 [MUST] 항목 추가
- [x] 완료
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**:
  - §품질 체크리스트 마지막에 Step 2와 동일 항목 1행 추가
  - §변경이력에 v2.5 행 추가 — "137 — 컨벤션 [MUST] 인용 항목 신설 (op-task-plan과 대칭)"
- **완료 기준**: dev 트랙(opd/opds/opdw)의 PLAN.md QA 검증에 컨벤션 [MUST] 항목 자동 적용.
- **테스트**: 변경 후 SKILL.md를 Read하여 §품질 체크리스트 마지막 항목 텍스트 확인.
- **의존**: 없음

### Step 5: opal-plan-agent AGENT.md 행동 규칙에 컨벤션 인용 의무 1행 추가
- [x] 완료
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-plan-agent/AGENT.md`
- **작업 내용**:
  - §행동 규칙(현재 5개 항목) 끝에 신규 항목 1행 추가 — "[MUST] 자체 로드한 `docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙 중 PLAN 설계에 영향을 주는 항목은 PLAN.md §1 참조 문서 테이블 또는 §2 핵심 설계에 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>` 포맷으로 인용한다 (CONVENTIONS.md 부재 시 자동 스킵 — §자체 로드 문서 룰 상속)."
- **완료 기준**: opal-plan-agent(opd/opds advanced 모델 PLAN 워커)에 SKILL.md 외 보조 강제력 적용.
- **테스트**: AGENT.md를 Read하여 §행동 규칙에 신규 1행 추가 확인.
- **의존**: 없음

### Step 6: 통합 검증 — 하위 호환 + 136 §13 충돌 검토
- [x] 완료
- **agent**: opal-task-agent
- **파일**: (검토 전용 — 코드 수정 없음)
- **작업 내용**:
  - **하위 호환 검증**: `docs/CONVENTIONS.md` 부재 프로젝트의 PM 디스패치 흐름 시뮬레이션 — D-1 §Step 2 문서 선별에서 CONVENTIONS.md가 누락되면 §Step 3 카탈로그가 발동되지 않음을 5개 변경 파일 각각에서 확인.
  - **136 §13 충돌 검토**: `opal/core/references/harness/pm-review-gate.md:47-62` Read하여 §13 트리거(EXECUTE 단계, changed_files 대상)와 본 태스크 변경(PLAN 단계, PLAN.md 자체)이 시점·대상·메커니즘 모두 분리됨을 확인. 충돌 0건 명문화.
  - 검증 결과를 본 PLAN.md §리스크 R-T1·R-T2 대응 컬럼에 표시 (또는 별도 검증 노트 산출 없음 — PM Gate 단계에서 검토 보고).
- **완료 기준**: 두 검토 모두 충돌/회귀 0건. PM에 보고.
- **테스트**: PM Gate에서 검토자가 §리스크 표 확인.
- **의존**: Step 1, 2, 3, 4, 5 (모두)

---

## 4. QA 체크리스트

### 4.1 기능 테스트 (R-1 ~ R-6)

- [x] **R-1 PM 디스패치 측 강제** — `opal/core/references/pm/dispatch-process.md` §Step 3 "인용 의무 규칙" 표의 "원문 인용 필수" 행에 "코드 컨벤션의 [MUST]/금지/네이밍 규칙(`docs/CONVENTIONS.md` 등)"이 명시 추가되어 있는가
- [x] **R-1 PM 디스패치 측 강제 (예시)** — 동일 §Step 3 예시 섹션과 워커 컨텍스트 주입 템플릿의 "## 핵심 제약" 예시에 컨벤션 인용 사례 1행이 추가되어 있는가
- [x] **R-1 영향 범위 자동 전파** — opal-pilot-{project,dev,dev-short,dev-wireframe} SKILL.md 디스패치 프롬프트에서 "핵심 제약" 필드(또는 PM 컨텍스트 주입 블록)가 D-1을 참조하므로 추가 수정 없이 4개 오케스트레이터에 자동 적용됨이 확인되는가
- [x] **R-2 PLAN 에이전트 측 강제** — `opal/agents/opal-plan-agent/AGENT.md` §행동 규칙에 "[MUST] 자체 로드한 `docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙... PLAN.md에 [MUST] 포맷으로 인용한다" 항목이 추가되어 있는가
- [x] **R-3 PLAN.md 산출물 측 검증** — `opal/skills/op-task-plan/SKILL.md` §품질 체크리스트에 "`docs/CONVENTIONS.md`의 [MUST]/금지/네이밍 규칙... [MUST] 포맷으로 인용되어 있는가" 신규 항목이 추가되어 있는가
- [x] **R-3 PLAN.md 산출물 측 검증 (plan-guide)** — `opal/skills/op-task-plan/references/plan-guide.md` §품질 체크리스트에 SKILL.md와 동일 항목이 추가되어 있는가 (양쪽 동기화)
- [x] **R-3 PLAN.md 산출물 측 검증 (dev)** — `opal/skills/op-dev-plan/SKILL.md` §품질 체크리스트에 동일 항목이 추가되어 있는가
- [x] **R-4 인용 규약 측 토큰 확장 결정** — `opal/core/references/harness/citation-rules.md` §2.5는 변경하지 않으며, 비채택 사유가 본 PLAN.md §2.1 (#4) 또는 §리스크에 기재되어 있는가
- [x] **R-5 하위 호환** — 5개 변경 지점 모두 "`docs/CONVENTIONS.md` 부재 시 자동 스킵" 명시가 되어 있는가 (D-1 §Step 3 / op-task-plan SKILL.md+plan-guide.md / op-dev-plan SKILL.md / opal-plan-agent AGENT.md)
- [x] **R-6 적용 지점 결정 근거** — 4개 잠재 적용 지점(#1·#2·#3·#4)의 채택/부분 채택/비채택 결정 근거가 본 PLAN.md §2.1 표에 명시되어 있는가

### 4.2 일관성 테스트 (136 정합성 + SSOT 일관성)

- [x] **136(B)와 책임 분리** — 본 §2.2 표가 검사 시점·대상·메커니즘 모두 분리됨을 명시하고 있는가
- [x] **136(B)와 시너지** — 본 §2.2 시너지 단락이 사전 차단(A) + 사후 검출(B) 이중 안전망 효과를 명시하고 있는가
- [x] **136 §13과 충돌 검토** — `opal/core/references/harness/pm-review-gate.md` §13 트리거(EXECUTE 단계)와 본 태스크 변경(PLAN 단계)이 충돌 없음을 §2.2 끝 단락이 확인하고 있는가
- [x] **citation-rules §2.4 포맷 준수** — 5개 변경 파일에 추가되는 [MUST] 인용 포맷이 모두 `[MUST] '경로' §N: <원문>` 또는 동등 표현인가
- [x] **SSOT 참조 구조** — D-1 변경이 opal-pilot-{project,dev,dev-short,dev-wireframe} SKILL.md 디스패치 프롬프트에 자동 전파됨이 §2.1 (#1) + §2.4 Phase 1 비고에 명시되어 있는가

### 4.3 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명/경로 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가 (본 태스크는 신규 파일 없음 — 해당 없음)
- [x] §1 참조 문서 테이블이 D-1~D-13 13개 항목으로 작성되어 있는가 (TASK.md D-1~D-10 보존 + D-11~D-13 추가)
- [x] §2 핵심 설계 M-1~M-5에 인라인 인용 또는 [MUST] 포맷 인용이 기재되어 있는가
- [x] 재해석 여지가 있는 제약(M-1·M-5의 신설 의무)이 [MUST] 포맷으로 기재되어 있는가 (citation-rules.md §2.4)

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | `docs/CONVENTIONS.md` 부재 프로젝트에서 신규 의무가 자연 스킵되지 않고 워커가 "CONVENTIONS.md를 찾지 못함"을 블로커로 처리할 위험 | PLAN 워커 디스패치 실패 → 기존 흐름 깨짐 | 5개 변경 파일 모두 "CONVENTIONS.md 부재 시 자동 스킵" 명시. D-1 §Step 2 문서 선별 단계에서 부재 파일은 선별되지 않음을 활용. opal-plan-agent AGENT.md §자체 로드 문서 "존재하는 경우에만 Read" 룰 상속. Step 6 통합 검증에서 시뮬레이션 |
| R-T2 | 136 §13 컨벤션 자동 진단(EXECUTE 사후 검증)과 시점·대상이 다름에도 PM이 두 시스템을 동일 시점에 호출하여 중복 검사 발생 | EXECUTE 단계 PM Gate에서 PLAN.md 컨벤션 인용까지 재검증하는 비효율 | §2.2 표·시너지 단락에서 "PLAN Gate(A)" / "EXECUTE Gate(B)" 분리를 명시. 본 태스크 변경 어디에도 EXECUTE Gate 트리거 추가 없음. PM이 §13 발동 시점은 EXECUTE 결과 후만 (pm-review-gate.md `:48` 트리거 조건) |
| R-T3 | citation-rules.md §2.5 7번째 토큰 비채택 결정으로 향후 컨벤션 [MUST] 인용이 일반 §2.4 포맷에만 의존 → 형식 불일치 발생 가능 | 워커별 인용 표현 차이 | 비채택 결정의 근거를 §2.1 #4에 명시(트랙 매트릭스 충돌 + 6종 토큰 사실상 커버 + §2.4로 충분). M-2/M-3/M-4 품질 체크리스트 항목에서 인용 포맷을 `[MUST] 'docs/CONVENTIONS.md' §N: <원문>`으로 고정 → 형식 통일 |
| R-T4 | M-5 (opal-plan-agent AGENT.md) 추가 의무가 SKILL.md citation-rules trigger와 중복되어 워커 컨텍스트 부풀림 | 워커 프롬프트 길이 증가 | M-5는 행동 규칙 1행 추가에 한정(짧음). SKILL.md trigger는 인용 포맷 자체를 강제하지만 컨벤션 호명은 약함. M-5는 컨벤션 호명을 명시하므로 의미 보완. 중복이 아닌 보조 강화 |
| R-T5 | M-2/M-3/M-4 품질 체크리스트 항목 텍스트가 op-task-plan(SKILL+plan-guide), op-dev-plan SKILL 3곳에 분산되어 향후 한쪽만 갱신될 위험 | 비대칭성 발생 | citation-rules trigger 1줄 패턴(130에서 양쪽 동기화 적용)과 동일하게 3곳에 동일 텍스트 박음. 본 태스크 §변경이력에서 137 패치 명시 — 후속 갱신 시 추적 가능 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-08 | 초기 작성 — 잠재 적용 지점 4개 정밀 분석 후 #1·#3 채택 (SSOT + QA 검출), #2 부분 채택 (보조 강화), #4 비채택 (트랙 매트릭스 충돌 + 6종 토큰 사실상 커버). 5개 파일 수정(M-1~M-5) + 통합 검증 1단계 (137) |
