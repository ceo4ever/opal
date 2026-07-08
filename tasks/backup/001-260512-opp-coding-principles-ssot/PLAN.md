# PLAN: 카르파시 행동 원칙 흡수 — Coding Principles SSOT 신설 + TASK AC 보강

> 작성일: 2026-05-12
> 입력: TASK.md
> 출력: PLAN.md

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 외부 | karpathy-skills CLAUDE.md | [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md) | 원천 — 4원칙 흡수 대상 |
| D-2 | 소스 | opal-harness.md | `opal/core/references/opal-harness.md` | 하네스 모듈 테이블 §2 — coding-principles.md 행 추가 위치 결정 (R-1) |
| D-3 | 소스 | header-rules.md | `opal/core/references/harness/header-rules.md` | PM 주입 패턴 vs 워커 자가 로드 패턴 비교 (R-2) |
| D-4 | 소스 | op-task SKILL.md | `opal/skills/op-task/SKILL.md` | F-4 보강 대상 — AC 작성 가이드 섹션 라인 100-104 (R-3) |
| D-5 | 소스 | op-task-plan SKILL.md | `opal/skills/op-task-plan/SKILL.md` | F-5 매핑 룰 추가 위치 후보 검토 (R-4) |
| D-6 | 소스 | opal/core/AGENT.md | `opal/core/AGENT.md` | F-3 "그냥 해" 표 정확 위치 식별 — 라인 141-152 (R-5) |
| D-7 | 소스 | opal-fe-agent AGENT.md | `opal/agents/opal-fe-agent/AGENT.md` | F-2 워커 자가 로드 룰 추가 대상 파일 |
| D-8 | 소스 | opal-be-agent AGENT.md | `opal/agents/opal-be-agent/AGENT.md` | F-2 워커 자가 로드 룰 추가 대상 파일 |
| D-9 | 소스 | opal-task-agent AGENT.md | `opal/agents/opal-task-agent/AGENT.md` | F-2 워커 자가 로드 룰 추가 대상 파일 |
| D-10 | 소스 | op-dev-test-scenario SKILL.md | `opal/skills/op-dev-test-scenario/SKILL.md` | F-5 매핑 룰 최종 배치 대상 파일 검증 |
| D-11 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 형식 §2 준수 의무 (R-7) |
| D-12 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력·네이밍·언어 규칙 확인 |

---

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/harness/coding-principles.md` | 신설 SSOT — 카르파시 4원칙 OPAL 매핑 | 신규 생성 | TASK.md F-1 |
| `opal/core/references/opal-harness.md` | 하네스 모듈 테이블 §2 — coding-principles 행 추가 | 수정 | `opal/core/references/opal-harness.md:87-98` |
| `opal/core/AGENT.md` | "그냥 해" 하네스 적용 범위 표 — Coding Principles 행 추가 | 수정 | `opal/core/AGENT.md:141-152` |
| `opal/agents/opal-fe-agent/AGENT.md` | 워커 자가 로드 의무 추가 | 수정 | `opal/agents/opal-fe-agent/AGENT.md:26-27` (Step 5~6 사이) |
| `opal/agents/opal-be-agent/AGENT.md` | 워커 자가 로드 의무 추가 | 수정 | `opal/agents/opal-be-agent/AGENT.md:26-27` (Step 5~6 사이) |
| `opal/agents/opal-task-agent/AGENT.md` | 워커 자가 로드 의무 추가 | 수정 | `opal/agents/opal-task-agent/AGENT.md:56-62` (행동 규칙 섹션) |
| `opal/skills/op-task/SKILL.md` | AC 작성 가이드 보강 — 카르파시 §4 인용 + Bad/Good 예시 추가 | 수정 | `opal/skills/op-task/SKILL.md:100-104` |
| `opal/skills/op-dev-test-scenario/SKILL.md` | AC↔verify check 매핑 표 의무 룰 추가 | 수정 | `opal/skills/op-dev-test-scenario/SKILL.md:120-129` (시나리오 작성 체크리스트) |

---

### 현재 상태

#### F-1 coding-principles.md 현황
`opal/core/references/harness/` 디렉토리에 `coding-principles.md` 파일이 **존재하지 않는다**. 하네스 모듈 테이블(`opal/core/references/opal-harness.md:87-98`)에는 현재 10개 모듈이 등재되어 있고, coding-principles 행이 없다.

#### F-2 워커 자가 로드 현황
3개 에이전트 파일 모두에 `coding-principles.md` 참조가 **전혀 없다**.
- `opal-fe-agent/AGENT.md`: 실행 프로세스 Step 5(레퍼런스 로드) → Step 6(산출물 생성) 사이에 삽입 위치가 있음. 라인 26-27 사이.
- `opal-be-agent/AGENT.md`: 동일 패턴, 라인 26-27 사이.
- `opal-task-agent/AGENT.md`: "## 행동 규칙" 섹션(라인 56-62)에 항목 추가.

#### F-3 "그냥 해" 표 현황
`opal/core/AGENT.md:141-152`에 "그냥 해 또는 직접 수행 시 하네스 적용 범위" 표가 존재한다. 현재 유지 항목: Guards, @header 규칙, OPAL Tools. `Coding Principles` 행이 **없다**.

#### F-4 AC 작성 가이드 현황
`opal/skills/op-task/SKILL.md:100-104`에 AC 작성 가이드가 존재한다. Bad/Good 예시 표에 **1행**만 있다. 카르파시 §4 인용이 **없다**.

#### F-5 AC↔TEST-SCENARIO 매핑 룰 현황
`op-dev-test-scenario/SKILL.md`의 체크리스트(라인 122-129) 첫 줄: "TASK.md의 모든 요구사항에 대해 시나리오가 존재하는가"로 요구사항 커버리지를 묻고 있으나, **AC별 매핑 표 의무화**는 없다. `op-task-plan/SKILL.md`에는 해당 내용이 없다.

---

### 영향 범위

- `coding-principles.md` 신설 → `opal-harness.md` 모듈 테이블에 행 추가 (§10 신설)
- 워커 3종 에이전트 수정 → install-mac.sh 재실행 필요 (배포 경계 준수 — 직접 편집 후 install 재실행)
- `op-task/SKILL.md` 수정 → 기존 AC 시스템과 충돌 없음 (보강만)
- `op-dev-test-scenario/SKILL.md` 수정 → opp 파이프라인은 TEST-SCENARIO 불사용이므로 영향 없음. opd/opds 파이프라인에서만 발동.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| 1 | `opal/core/references/harness/coding-principles.md` | 카르파시 4원칙 OPAL 단계 매핑 SSOT | TASK.md F-1 (D-1) |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `opal/core/references/opal-harness.md` | §2 하네스 모듈 테이블에 coding-principles 행 추가 + §10 stub 신설 | TASK.md F-1 AC(e) — 하네스 SSOT 정합 |
| 2 | `opal/core/AGENT.md` | "그냥 해" 표 유지 카테고리에 Coding Principles 행 추가 | TASK.md F-3 |
| 3 | `opal/agents/opal-fe-agent/AGENT.md` | EXECUTE 진입 시 coding-principles.md Read 의무 1줄 추가 | TASK.md F-2 |
| 4 | `opal/agents/opal-be-agent/AGENT.md` | EXECUTE 진입 시 coding-principles.md Read 의무 1줄 추가 | TASK.md F-2 |
| 5 | `opal/agents/opal-task-agent/AGENT.md` | 행동 규칙에 EXECUTE 진입 시 coding-principles.md Read 의무 추가 | TASK.md F-2 |
| 6 | `opal/skills/op-task/SKILL.md` | AC 작성 가이드에 카르파시 §4 인용 + Bad/Good 예시 1행 추가 | TASK.md F-4 |
| 7 | `opal/skills/op-dev-test-scenario/SKILL.md` | 체크리스트에 AC↔verify check 매핑 표 의무 룰 추가 | TASK.md F-5 |

#### 삭제

삭제 대상 없음.

---

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | SSOT 신설 — coding-principles.md 작성 | `opal/core/references/harness/coding-principles.md` | 중 |
| 2 | 하네스 모듈 테이블 갱신 + §10 stub 추가 | `opal/core/references/opal-harness.md` | 하 |
| 3 | "그냥 해" 표에 Coding Principles 행 추가 | `opal/core/AGENT.md` | 하 |
| 4 | FE 에이전트 자가 로드 룰 추가 | `opal/agents/opal-fe-agent/AGENT.md` | 하 |
| 4 | BE 에이전트 자가 로드 룰 추가 | `opal/agents/opal-be-agent/AGENT.md` | 하 |
| 4 | Task 에이전트 자가 로드 룰 추가 | `opal/agents/opal-task-agent/AGENT.md` | 하 |
| 5 | op-task AC 작성 가이드 보강 | `opal/skills/op-task/SKILL.md` | 하 |
| 5 | TEST-SCENARIO 매핑 룰 추가 | `opal/skills/op-dev-test-scenario/SKILL.md` | 하 |

> 순서 4 (에이전트 3종)와 순서 5 (스킬 2종)는 각각 병렬 실행 가능.
> 순서 1(SSOT 신설) → 순서 2(하네스 테이블) → 순서 3("그냥 해" 표) → 순서 4 에이전트 3종(병렬) → 순서 5 스킬 2종(병렬)

---

### 핵심 설계

#### §2.1 coding-principles.md SSOT 설계

[MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." — 본 PLAN은 산출물(.md)만 작성.

파일 구조 (TASK.md F-1 AC (b)):
```
---
module: coding-principles
적용 주체: 코드 변경하는 모든 주체
로드 시점: 워커 EXECUTE 진입 / PM 그냥 해 진입
---
```

6개 섹션 헤딩 (→ D-4 F-1 AC (b)):
- `§1 TASK 단계` — 카르파시 §1 Think Before Coding 매핑
- `§2 PLAN 단계` — 카르파시 §2 Simplicity First 설계 원칙 매핑
- `§3 TEST-SCENARIO 단계` — 카르파시 §2 희박 케이스 분류 매트릭스
- `§4 EXECUTE 단계` — 카르파시 §3 Surgical Changes 구현 원칙
- `§5 QA Gate 단계` — 카르파시 §2·§3·§4 사후 검증
- `§6 적용 매트릭스` — TASK.md §"배경 분석" 카르파시↔OPAL 단계 매트릭스 표 전재

§3 희박 케이스 분류 매트릭스 (TASK.md F-1 AC (c)) — 5행:

| 발생 가능성 | 영향도 | 처리 |
|----------|--------|------|
| 높음 | 높음 | 시나리오 필수 (Golden Path) |
| 높음 | 낮음 | 시나리오 작성 |
| 낮음 | 높음 | 시나리오 작성 + 정당화 명시 |
| 낮음 | 낮음 | 시나리오 제외 또는 Known Issue 명시 |
| 불가능 | — | 작성 금지 (위반 시 QA Fail) |

변경이력 표: v1.0 행 포함 (TASK.md F-1 AC (e)) (→ D-12 §변경이력 작성 의무)

[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"

---

#### §2.2 opal-harness.md §2 테이블 갱신 + §10 stub 신설

`opal/core/references/opal-harness.md:87-98` 모듈 테이블에 아래 행 추가 (→ D-2 §2 하네스 모듈):

```markdown
| Coding Principles | `harness/coding-principles.md` | EXECUTE 단계 진입 시 (코드 변경 워커) / PM "그냥 해" 진입 시 | §10 |
```

§10 stub 내용 (§8 @header 규칙 패턴 참조, → D-3):
```markdown
## 10. Coding Principles

> **[필수 로드]** EXECUTE 단계에서 코드 파일 변경 시, 또는 PM "그냥 해" 직접 수행 시 로드한다.
> 탐색: `harness/coding-principles.md`
>
> 적용 주체: 코드 변경하는 모든 워커 + PM("그냥 해")
> 적용 시점: EXECUTE 단계 진입 직후 / PM 직접 수행 시
> PM Gate 검증: 산출물에 사변적 추가·인접 코드 개선·불가능 시나리오 방어 코드가 없는가
```

변경이력 표에 `v4.9 | 2026-05-12 10:56 | §2 하네스 모듈 테이블에 coding-principles 행 추가 + §10 Coding Principles stub 신설 (001)` 추가

---

#### §2.3 opal/core/AGENT.md "그냥 해" 표 갱신

`opal/core/AGENT.md:141-152` "그냥 해 또는 직접 수행 시 하네스 적용 범위" 표의 **유지** 카테고리에 행 추가 (→ D-6:141-152):

```markdown
| **유지** | Coding Principles (코드 파일 변경 시) | ✅ |
```

[MUST] TASK.md F-3 AC (a): "적용 범위 표 '유지' 카테고리에 `Coding Principles` 행이 등재"

변경이력 표에 `v2.5 | 2026-05-12 10:56 | "그냥 해" 하네스 적용 범위 표에 Coding Principles 행 추가 (001)` 추가

---

#### §2.4 워커 에이전트 3종 자가 로드 룰

**패턴 선택**: EXECUTE 진입 시점 트리거를 스킬 SKILL.md 로드 단계(Step 5 레퍼런스 로드 완료) 이후, Step 6(산출물 생성) 직전에 조건부 의무로 삽입. (→ D-3 — 워커 자가 로드 패턴)

삽입 내용 (3개 파일 공통 텍스트):
```
- EXECUTE 단계 진입 시(스킬이 `op-dev-execute` 또는 `op-task-execute` 계열일 때): `opal/core/references/harness/coding-principles.md`를 Read하고 원칙을 준수한다.
```

**opal-fe-agent/AGENT.md** 추가 위치: 실행 프로세스 Step 5(`references/` 가이드 Read) 바로 다음, Step 6(FE 산출물 생성) 앞 → `opal/agents/opal-fe-agent/AGENT.md:26-27` 사이 (현재 Step 5가 라인 26, Step 6이 라인 27)

**opal-be-agent/AGENT.md** 추가 위치: 동일 패턴 → `opal/agents/opal-be-agent/AGENT.md:26-27` 사이

**opal-task-agent/AGENT.md** 추가 위치: "## 행동 규칙" 섹션(라인 56-62)에 항목 추가

[MUST] TASK.md F-2 AC (a): "3개 파일 각각에 `harness/coding-principles.md` 문자열을 포함한 의무 줄 1개 이상 존재"
[MUST] TASK.md F-2 AC (b): "각 파일 변경이력 표에 1행 추가"

[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: 일시 포함 semver 행 추가

---

#### §2.5 op-task SKILL.md AC 작성 가이드 보강

`opal/skills/op-task/SKILL.md:100-104` AC 작성 가이드 섹션에 아래 내용 추가 (→ D-4:100-104):

카르파시 §4 원문 인용 (TASK.md F-4 AC (a)):
```
> "Strong criteria let you loop independently. Weak criteria require constant clarification." — Karpathy CLAUDE.md §4 Goal-Driven
```

Bad/Good 예시 표에 2번째 행 추가 (TASK.md F-4 AC (b)):

| Bad (모호) | Good (검증 가능) |
|-----------|-----------------|
| ~~기존 1행~~ | ~~기존 1행~~ |
| "SSOT가 잘 만들어져 있어야 한다" | "파일이 지정 경로에 존재하고, 6개 섹션 헤딩이 모두 존재하며, §3에 5행 매트릭스가 있다" |

변경이력 표에 `v1.6 | 2026-05-12 10:56 | AC 작성 가이드에 카르파시 §4 원문 인용 + Bad/Good 예시 2번째 행 추가 (001)` 추가

---

#### §2.6 op-dev-test-scenario SKILL.md 매핑 룰 추가

`opal/skills/op-dev-test-scenario/SKILL.md` 시나리오 작성 체크리스트(라인 122-129)에 아래 항목 추가 (→ D-10:122-129):

추가 항목:
```markdown
- [ ] TASK.md의 각 AC가 어느 시나리오(S-N)에 대응하는지 매핑 표가 작성되어 있는가
```

매핑 표 형식 예시를 체크리스트 뒤에 추가:
```markdown
### AC ↔ verify check 매핑 표 (의무)

| AC ID | 대응 시나리오 | 비고 |
|-------|-------------|------|
| F-1 AC (a) | S-1 | 파일 존재 확인 |
| F-1 AC (b) | S-2 | 섹션 헤딩 6개 확인 |
```

[MUST] TASK.md F-5 AC (a): "단계 스킬에 'AC ↔ verify check 매핑 표 의무' 룰 추가"
[MUST] TASK.md F-5 AC (b): "매핑 표 형식 예시(2열 이상: AC ID / verify check 위치) 제공"

변경이력 표에 `v1.3 | 2026-05-12 10:56 | 시나리오 작성 체크리스트에 AC↔verify check 매핑 표 의무 룰 + 형식 예시 추가 (001)` 추가

---

## 3. 의사결정 기록

### M-1: F-5 매핑 룰 위치 — op-task-plan vs op-dev-test-scenario

**결정**: `op-dev-test-scenario/SKILL.md`에 배치한다.

**근거**:
- `op-task-plan/SKILL.md`는 PLAN 단계 스킬이다. PLAN 단계에서는 AC를 참조하지, TEST-SCENARIO verify check를 매핑하지 않는다. 추가 시 스킬 책임 범위 위반.
- `op-dev-test-scenario/SKILL.md`에는 "TASK.md의 모든 요구사항에 대해 시나리오가 존재하는가" 체크리스트 항목이 이미 있어 (→ D-10:124), AC 매핑 의무화는 기존 패턴의 구체화다.
- TASK.md F-5 "어디에" 필드에도 TEST-SCENARIO 작성 스킬이 후보로 명시됨 (→ TASK.md:108).
- opp 파이프라인은 TEST-SCENARIO 불사용이므로 이 스킬 수정이 opp 작업 흐름에 영향을 주지 않는다.

---

### M-2: opal-harness.md §2 테이블 — §10 신설 vs §8.x 부속

**결정**: §10 신설로 등재한다.

**근거**:
- §8은 "@header 규칙"으로 이름이 확정된 섹션이다. Coding Principles는 독립적인 행동 원칙 SSOT이며 @header와 별도 개념이다.
- `opal/core/references/opal-harness.md`의 §9는 "OPAL Tools"다. §10이 현재 공백 번호이며 삽입이 자연스럽다.
- 다른 SSOT 모듈(state.md, task-process.md)이 각각 독립 §(§3, §4)를 갖는 패턴과 일치한다 (→ D-2:87-98).

---

### M-3: 워커 자가 로드 삽입 방식 — 조건부 vs 무조건

**결정**: 조건부 삽입 ("EXECUTE 계열 스킬일 때") 로 한다. **트리거 스킬 목록은 에이전트 도메인별로 다르게 명시**한다.

**근거**:
- PLAN, ANALYSIS 단계를 수행하는 워커에게도 무조건 로드하면 토큰 낭비다.
- coding-principles.md의 frontmatter에 "로드 시점: 워커 EXECUTE 진입"으로 명시했으므로 일관성 유지 필요.
- header-rules.md도 "EXECUTE 단계에서 코드 파일 생성/수정 시"로 조건부 로드한다 (→ D-3: EXECUTE @header 규칙 트리거 패턴).
- **에이전트 도메인별 트리거 차이는 의도된 것**:
  - FE: `op-dev-execute` + `op-dev-wireframe` (UI 와이어프레임도 FE 도메인)
  - BE: `op-dev-execute` (와이어프레임은 BE 도메인 아님 — 미언급)
  - Task: `op-dev-execute` + `op-task-execute` (opp 범용 EXECUTE 포함)

---

### M-4: opal-task-agent 삽입 위치 — 실행 프로세스 vs 행동 규칙 섹션

**결정**: "## 행동 규칙" 섹션에 추가한다.

**근거**:
- `opal-task-agent/AGENT.md`에는 opal-fe/be-agent와 달리 "## 행동 규칙" 섹션이 이미 존재한다 (→ D-9:56-62). 이 섹션이 수행 의무를 열거하는 적합한 위치다.
- opal-fe/be-agent는 "## 행동 규칙" 섹션이 없으므로 실행 프로세스(Step 5~6 사이)에 삽입한다.

---

## 4. 실행 체크리스트

> 총 8개 Step | Phase 4개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | SSOT 신설 — 다른 모든 Step의 의존 기반 |
> | 2 | 2, 3 | 병렬 | 하네스 테이블 + "그냥 해" 표 — 독립 파일 |
> | 3 | 4, 5, 6 | 병렬 | 에이전트 3종 — 독립 파일 |
> | 4 | 7, 8 | 병렬 | 스킬 2종 — 독립 파일 |

---

### Step 1: coding-principles.md SSOT 신설 (F-1)
- [x] 완료
- **파일**: `opal/core/references/harness/coding-principles.md`
- **작업 내용**:
  - YAML frontmatter 작성 — `module`, `적용 주체: 코드 변경하는 모든 주체`, `로드 시점: 워커 EXECUTE 진입 / PM 그냥 해 진입`
  - §1 TASK 단계 — 카르파시 §1 Think Before Coding 매핑 (OPAL TASK 단계 = 요구사항 명확화·AC 수립)
  - §2 PLAN 단계 — 카르파시 §2 Simplicity First 설계 원칙 (오버-엔지니어링 금지)
  - §3 TEST-SCENARIO 단계 — 카르파시 §2 희박 케이스 분류 매트릭스 5행 전재
  - §4 EXECUTE 단계 — 카르파시 §3 Surgical Changes (지시된 것만, 인접 코드 무변경, 새 패턴 추가 전 제거)
  - §5 QA Gate 단계 — 카르파시 §2·§3·§4 사후 검증 기준
  - §6 적용 매트릭스 — 카르파시 4원칙 × OPAL 단계 표 전재
  - 변경이력 표: v1.0 행 (일시: KST, 태스크 번호 001)
- **완료 기준**:
  - (F-1 AC a) 파일이 `opal/core/references/harness/coding-principles.md`에 존재한다
  - (F-1 AC b) `§1 TASK / §2 PLAN / §3 TEST-SCENARIO / §4 EXECUTE / §5 QA Gate / §6 적용 매트릭스` 6개 헤딩이 모두 존재한다
  - (F-1 AC c) §3에 발생 가능성 × 영향도 매트릭스 5행이 모두 등재된다
  - (F-1 AC d) 헤더 frontmatter에 "적용 주체: 코드 변경하는 모든 주체"와 "로드 시점: 워커 EXECUTE 진입 / PM 그냥 해 진입" 두 줄이 명시된다
  - (F-1 AC e) 변경이력 표 v1.0 행 1개 포함
- **테스트**: Read로 파일 내용 확인, 6개 헤딩 grep 검증
- **의존**: 없음

---

### Step 2: opal-harness.md §2 테이블 + §10 stub 추가 (F-1 하네스 정합, M-2)
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  - 라인 87-98 "하네스 모듈" 테이블에 `| Coding Principles | harness/coding-principles.md | EXECUTE 단계 진입 시 (코드 변경 워커) / PM "그냥 해" 진입 시 | §10 |` 행 추가
  - §9 OPAL Tools 다음에 `## 10. Coding Principles` 섹션 stub 신설 (적용 주체/시점/PM Gate 검증 포함)
  - 변경이력 표에 `v4.9 | 2026-05-12 10:56 | §2 하네스 모듈 테이블에 coding-principles 행 추가 + §10 신설 (001)` 추가
- **완료 기준**:
  - `opal-harness.md` §2 테이블에 `coding-principles.md` 행이 존재한다
  - `## 10. Coding Principles` 섹션이 파일 끝(변경이력 전)에 존재한다
  - 변경이력 표에 v4.9 행이 있다
- **테스트**: grep "coding-principles" `opal/core/references/opal-harness.md`
- **의존**: Step 1

---

### Step 3: opal/core/AGENT.md "그냥 해" 표 갱신 (F-3)
- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**:
  - 라인 141-152 "그냥 해 또는 직접 수행 시 하네스 적용 범위" 표의 **유지** 카테고리 마지막 행 아래에 `| **유지** | Coding Principles (코드 파일 변경 시) | ✅ |` 행 추가
  - 변경이력 표에 `v2.5 | 2026-05-12 10:56 | "그냥 해" 하네스 적용 범위 표에 Coding Principles 행 추가 (001)` 추가
- **완료 기준**:
  - (F-3 AC a) 적용 범위 표 "유지" 카테고리에 `Coding Principles` 행이 등재된다
  - (F-3 AC b) 해당 SSOT의 변경이력 표에 1행 추가된다
- **테스트**: grep "Coding Principles" `opal/core/AGENT.md`
- **의존**: Step 1

---

### Step 4: opal-fe-agent/AGENT.md 자가 로드 룰 추가 (F-2)
- [x] 완료
- **파일**: `opal/agents/opal-fe-agent/AGENT.md`
- **작업 내용**:
  - 실행 프로세스 Step 5(references 가이드 Read 완료) 직후, Step 6(FE 산출물 생성) 직전에 조건부 의무 삽입:
    ```
    - EXECUTE 단계 진입 시(`op-dev-execute` 또는 `op-dev-wireframe` 계열 스킬): `opal/core/references/harness/coding-principles.md`를 Read하고 §4 EXECUTE 원칙을 준수한다.
    ```
  - 변경이력 표(없으면 신설) 에 `v1.x | 2026-05-12 10:56 | EXECUTE 진입 시 coding-principles.md §4 Read 의무 추가 (001)` 행 추가
- **완료 기준**:
  - (F-2 AC a) 파일에 `harness/coding-principles.md` 문자열을 포함한 의무 줄 1개 이상 존재
  - (F-2 AC b) 변경이력 표에 1행 추가
- **테스트**: grep "coding-principles" `opal/agents/opal-fe-agent/AGENT.md`
- **의존**: Step 1

---

### Step 5: opal-be-agent/AGENT.md 자가 로드 룰 추가 (F-2)
- [x] 완료
- **파일**: `opal/agents/opal-be-agent/AGENT.md`
- **작업 내용**:
  - Step 4와 동일한 패턴: 실행 프로세스 Step 5~6 사이에 조건부 의무 삽입 (`op-dev-execute` 스킬 진입 시 coding-principles.md §4 Read 의무)
  - 변경이력 표에 `v1.x | 2026-05-12 10:56 | EXECUTE 진입 시 coding-principles.md §4 Read 의무 추가 (001)` 행 추가
- **완료 기준**:
  - (F-2 AC a) 파일에 `harness/coding-principles.md` 문자열을 포함한 의무 줄 1개 이상 존재
  - (F-2 AC b) 변경이력 표에 1행 추가
- **테스트**: grep "coding-principles" `opal/agents/opal-be-agent/AGENT.md`
- **의존**: Step 1

---

### Step 6: opal-task-agent/AGENT.md 자가 로드 룰 추가 (F-2, M-4)
- [x] 완료
- **파일**: `opal/agents/opal-task-agent/AGENT.md`
- **작업 내용**:
  - "## 행동 규칙" 섹션(현재 라인 56-62)에 항목 추가:
    ```
    - EXECUTE 단계 진입 시(스킬이 `op-dev-execute` 또는 `op-task-execute` 계열일 때): `opal/core/references/harness/coding-principles.md`를 Read하고 §4 EXECUTE 원칙을 준수한다.
    ```
  - 변경이력 표(없으면 신설)에 `v1.x | 2026-05-12 10:56 | 행동 규칙에 EXECUTE 진입 시 coding-principles.md §4 Read 의무 추가 (001)` 행 추가
- **완료 기준**:
  - (F-2 AC a) 파일에 `harness/coding-principles.md` 문자열을 포함한 의무 줄 1개 이상 존재
  - (F-2 AC b) 변경이력 표에 1행 추가
- **테스트**: grep "coding-principles" `opal/agents/opal-task-agent/AGENT.md`
- **의존**: Step 1

---

### Step 7: op-task SKILL.md AC 작성 가이드 보강 (F-4)
- [x] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**:
  - 라인 100 "AC 작성 가이드" 정의 바로 아래에 카르파시 §4 원문 인용 추가:
    ```markdown
    > "Strong criteria let you loop independently. Weak criteria require constant clarification." — Karpathy CLAUDE.md §4 Goal-Driven
    > (강력한 기준은 독립적으로 루핑할 수 있게 한다. 약한 기준은 끝없는 clarification을 유발한다.)
    ```
  - 라인 102-104 Bad/Good 표에 2번째 행 추가:
    ```
    | "SSOT가 잘 만들어져 있어야 한다" | "파일이 지정 경로에 존재하고, 6개 섹션 헤딩이 모두 존재하며, §3에 5행 매트릭스가 있다" |
    ```
  - 변경이력 표에 `v1.6 | 2026-05-12 10:56 | AC 작성 가이드에 카르파시 §4 원문 인용 + Bad/Good 예시 2번째 행 추가 (001)` 추가
- **완료 기준**:
  - (F-4 AC a) 카르파시 §4 인용문 `"Strong criteria let you loop independently. Weak criteria require constant clarification."` 이 파일에 포함된다
  - (F-4 AC b) Bad/Good 표가 최소 2행 존재한다 (기존 1행 + 신규 1행)
  - (F-4 AC c) 변경이력 표에 1행 추가
- **테스트**: grep "Strong criteria" `opal/skills/op-task/SKILL.md`
- **의존**: 없음

---

### Step 8: op-dev-test-scenario SKILL.md 매핑 룰 추가 (F-5, M-1)
- [x] 완료
- **파일**: `opal/skills/op-dev-test-scenario/SKILL.md`
- **작업 내용**:
  - 시나리오 작성 체크리스트(라인 122-129) 마지막 항목 뒤에 체크리스트 항목 추가:
    ```markdown
    - [ ] TASK.md의 각 AC가 어느 시나리오(S-N)에 대응하는지 `## AC ↔ verify check 매핑 표`가 TEST-SCENARIO.md에 작성되어 있는가
    ```
  - TEST-SCENARIO.md 통일 형식(라인 62-110) 끝에 `## AC ↔ verify check 매핑 표` 섹션 추가:
    ```markdown
    ## AC ↔ verify check 매핑 표

    | AC ID | 대응 시나리오 | 비고 |
    |-------|-------------|------|
    | {F-N AC (a)} | S-{N} | {검증 설명} |
    ```
  - 변경이력 표에 `v1.3 | 2026-05-12 10:56 | 시나리오 작성 체크리스트에 AC↔verify check 매핑 표 의무 룰 + 형식 예시 추가 (001)` 추가
- **완료 기준**:
  - (F-5 AC a) 단계 스킬에 "AC ↔ verify check 매핑 표 의무" 룰이 체크리스트 항목으로 추가된다
  - (F-5 AC b) TEST-SCENARIO.md 통일 형식에 `## AC ↔ verify check 매핑 표` 형식 예시(AC ID / 대응 시나리오 / 비고 2열 이상)가 포함된다
  - (F-5 AC c) 변경이력 표에 1행 추가
- **테스트**: grep "AC.*verify\|verify.*AC\|매핑 표" `opal/skills/op-dev-test-scenario/SKILL.md`
- **의존**: 없음

---

## 5. QA 체크리스트

### 기능 테스트

- [x] F-1: `opal/core/references/harness/coding-principles.md`가 존재하고 AC (a)~(e) 전항을 충족한다
- [x] F-2: 3개 에이전트 파일 각각에 `harness/coding-principles.md` 문자열이 포함된다 (`grep -r "coding-principles" opal/agents/`)
- [x] F-3: `opal/core/AGENT.md`의 "유지" 카테고리 표에 `Coding Principles` 행이 있다
- [x] F-4: `opal/skills/op-task/SKILL.md`에 카르파시 §4 인용문이 존재하고 Bad/Good 표가 2행 이상이다
- [x] F-5: `opal/skills/op-dev-test-scenario/SKILL.md`에 AC↔verify check 매핑 표 의무 항목이 체크리스트에 포함되고, TEST-SCENARIO.md 형식에 `## AC ↔ verify check 매핑 표` 섹션이 있다

### 일관성 테스트

- [x] `opal-harness.md` §2 테이블의 coding-principles 행 로드 시점이 `opal/core/AGENT.md` "그냥 해" 표 및 `coding-principles.md` frontmatter의 로드 시점과 일치한다
- [x] 3개 에이전트의 삽입 문구에서 파일 경로 `opal/core/references/harness/coding-principles.md`가 일치한다
- [x] 모든 수정 파일의 변경이력 표에 일시(KST: 2026-05-12 11:16) + 태스크 번호 `(001)` 행이 추가되었다
- [x] 카르파시 §4 원문이 영문 그대로 인용되었고 한국어 설명이 병기되었다 (TASK.md 제약 조건 준수)

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가 (`docs/CONVENTIONS.md` §언어 규칙)
- [x] 신규 파일 경로가 kebab-case를 따르는가 (`coding-principles.md` ✅)
- [x] YAML frontmatter가 올바른가 (coding-principles.md 헤더)
- [x] `~/.opal/` 배포 파일을 직접 수정하지 않았는가 (배포 경계 준수)
- [x] 기존 AC 시스템·op-task 흐름과 충돌 없이 보강인가 (하위 호환 확인)

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| coding-principles.md 작성 과정에서 카르파시 원문을 부정확하게 인용 | §4 EXECUTE 원칙이 원본과 다르게 적용됨 | 카르파시 원문([D-1]) 직접 참조, 영문 그대로 인용 후 한국어 설명 병기 |
| 워커 에이전트 3종 수정 후 install-mac.sh 재실행 미수행 | `~/.opal/` 배포 버전에 반영되지 않음 | EXECUTE 완료 보고 시 install 재실행 안내 포함 |
| opal-harness.md §번호 충돌 (§10이 이미 존재할 경우) | 하네스 구조 불일치 | 조사 완료 — 현재 §9가 마지막. §10은 공백이므로 충돌 없음 (`opal/core/references/opal-harness.md:203-235`) |
| op-dev-test-scenario 수정이 기존 TEST-SCENARIO.md 형식 파일과 소급 충돌 | 기존 산출물에 AC↔매핑 표가 없어 QA Fail 위험 | citation-rules.md §5 "레거시 호환 — 기존 산출물 소급 변경 불필요" 규칙 적용 — 신규 태스크부터 적용 (→ D-11 §5) |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 10:56 | 초기 작성 — 5개 F-ID × 8 Step, Phase 4개, 의사결정 M-4개 (001) |
| v1.1 | 2026-05-12 11:02 | QA-PLAN 정정 반영 — §4 QA 체크리스트 → §5, §5 리스크 → §6, M-3에 도메인별 트리거 차이 의도 명시 (001) |
