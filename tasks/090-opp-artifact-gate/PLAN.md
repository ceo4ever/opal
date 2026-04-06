# PLAN: Artifact Gate 설계 및 적용

> 태스크: 090-opp-artifact-gate | 작성일: 2026-04-06 | 스킬: opp

---

## 1. 현황 분석

### 1.1 문제 정의

QA Gate 완료의 증거(산출물 파일)가 없어도 PM Gate 및 DONE.md 생성 단계로 진입할 수 있는 구조적 빈틈이 존재한다. LLM 특성상 컨텍스트에서 규칙이 밀려나면 의도 없이 게이트를 스킵하게 된다. "의지가 아닌 구조로 강제"하기 위해 산출물 파일 존재를 게이트 진입 조건으로 명문화한다.

### 1.2 현재 게이트 구조 (opal-harness-interactive.md 기준)

```
단계 완료 → [QA Gate] → [PM Gate] → 사용자 확인
```

- **QA Gate** (§2): QA 에이전트 호출. 산출물 검증. 그러나 "QA 에이전트가 산출물을 생성했는지"는 확인하지 않음.
- **PM Gate** (§3): AGENT.md 기반 PM 검토 기준 적용. QA 산출물 존재 여부 확인 없음.
- **Artifact Gate**: 현재 없음.

### 1.3 각 오케스트레이터 게이트 현황

| 스킬 | PLAN 게이트 | EXECUTE 게이트 | 비고 |
|------|------------|--------------|------|
| opp | QA Gate → PM Gate | QA Gate → PM Gate | 정상 |
| opds | QA Gate → PM Gate | (TEST-SCENARIO) → PM Gate | QA Gate 없음 (EXECUTE) |
| opd | QA Gate → PM Gate | (TEST-SCENARIO) → PM Gate | QA Gate 없음 (EXECUTE) |
| opwt | QA Gate → PM Gate | QA Gate → **PM 검토** | "PM 검토"로만 표기 |
| opwt ANALYSIS | (없음) → **사용자 확인** | - | PM Gate 누락 |
| opdw | QA Gate → PM Gate | QA Gate → PM Gate | 정상 |
| opsdd | Phase별 Gate 있음 | EXECUTE-LOOP 내 Gate | 정상 |

### 1.4 설계 결정: 공통화 vs 인라인

**결정: 하네스 공통화 + 스킬별 산출물 매핑 테이블**

- `opal-harness-interactive.md`에 §2.5 Artifact Gate 섹션 신설 (QA Gate 완료 후, PM Gate 진입 전)
- `opal-harness-agentic.md` §4에 산출물 직접 검증 의무 강화
- `opal-harness.md` §2에 QA 산출물 표준 파일명 명세
- 각 SKILL.md에는 스킬별 단계-산출물 매핑 추가 (최소 인라인)

**근거**: 산출물 파일명은 스킬마다 다르므로 공통 하네스에서 명세하되, 스킬별 오버라이드를 허용한다.

### 1.5 파급 범위 사전 분석

| 변경 파일 | 영향 스킬 | 위험도 |
|----------|---------|--------|
| opal-harness-interactive.md | opp, opds, opd, opwt, opdw, opsdd (interactive 전체) | 중 — 모든 interactive 스킬에 Artifact Gate 추가됨 |
| opal-harness-agentic.md | 동일 스킬 agentic 모드 | 중 — agentic 강화 검토에 명시화 |
| opal-harness.md | 공통 | 낮 — QA 산출물 표준명 추가, 기존 규칙 변경 없음 |
| opwt SKILL.md | opwt만 | 낮 — opwt 게이트 표기 수정 |

---

## 2. 요구사항별 변경 명세

### 요구사항 1: Artifact Gate 규칙 추가 — opal-harness-interactive.md

**파일**: `opal/core/references/opal-harness-interactive.md`

**변경 위치**: §2(QA Gate)와 §3(PM Gate) 사이에 **§2.5 Artifact Gate** 섹션 신설

**추가 내용**:

```markdown
## 2.5 Artifact Gate

QA Gate 완료 후 PM Gate 진입 전, 필수 산출물 파일의 존재 여부를 확인한다.

**게이트 진입 조건**: QA Gate 완료 후, PM Gate 진입 전 자동 실행

**자가 점검 프롬프트**:
> "QA 산출물 파일이 존재하는가?"
> 1. 현재 단계의 필수 산출물 파일명을 확인한다 (스킬별 산출물 명세 — 하네스 §2 또는 SKILL.md 참조)
> 2. 파일이 `tasks/{NNN}-{name}/` 경로에 실제로 존재하는지 확인한다
> 3. 파일이 존재하고 비어 있지 않은지(내용 존재 여부) 확인한다

| 확인 결과 | 동작 |
|----------|------|
| 산출물 파일 존재 + 내용 있음 | PM Gate 진입 허용 |
| 산출물 파일 미존재 | QA 에이전트 재소환 → 산출물 생성 후 재확인 |
| 산출물 파일 존재하나 비어 있음 | QA 에이전트 재소환 → 산출물 재생성 후 재확인 |

**차단 원칙**: 필수 산출물이 확인되지 않으면 PM Gate 및 DONE.md 생성 단계로 진입하지 않는다.
```

**변경이력 추가**: v1.4 항목 추가

---

### 요구사항 2: Artifact Gate 규칙 추가 — opal-harness-agentic.md

**파일**: `opal/core/references/opal-harness-agentic.md`

**변경 위치**: §4(PM 자율 검토) "강화 검토 기준" 목록에 항목 추가

**추가 내용**: 기존 강화 검토 기준 5항목 중, "산출물 내용을 직접 Read하여 실질 검증" 항목 바로 앞(또는 후)에 Artifact Gate 검증 항목을 명시적으로 추가:

```markdown
**강화 검토 기준**:
1. TASK.md 요구사항 100% 충족
2. QA 결과 All Pass
3. **Artifact Gate**: QA 산출물 파일이 실제로 존재하고 내용이 있는지 확인 (하네스 §2.5 참조)
   - 파일 미존재 또는 빈 파일: PM이 QA 에이전트를 재소환하여 산출물을 생성한 후 재검증
   - agentic 모드에서는 자율 통과 시도 없이 반드시 산출물 파일을 Read하여 확인한다
4. PM 검토 기준 Pass
5. 이전 단계 산출물과 일관성 유지
6. 산출물 내용을 직접 Read하여 실질 검증
   ...
```

**변경이력 추가**: v1.2 항목 추가

---

### 요구사항 3: 필수 산출물 명세 추가 — opal-harness.md

**파일**: `opal/core/references/opal-harness.md`

**변경 위치**: §2(모듈 구조) — "QA 체크리스트 검증" 섹션 뒤에 **"QA 산출물 표준 파일명"** 서브섹션 추가

**추가 내용**:

```markdown
### QA 산출물 표준 파일명

Artifact Gate(interactive §2.5 / agentic §4)에서 확인하는 필수 산출물 파일명의 기본값.
오케스트레이터 SKILL.md에서 오버라이드 가능하며, 명시가 없으면 이 표준을 따른다.

| 단계 | 필수 산출물 파일 | 위치 |
|------|--------------|------|
| PLAN QA | `QA-PLAN.md` | `tasks/{NNN}-{name}/` |
| EXECUTE QA | `QA-EXECUTE.md` | `tasks/{NNN}-{name}/` |
| ANALYSIS QA | `QA-ANALYSIS.md` | `tasks/{NNN}-{name}/` (해당 단계가 있는 스킬만) |

**스킬별 산출물 오버라이드**: 각 오케스트레이터 SKILL.md의 "STATE.md 도메인 치환값" 또는 별도 섹션에서 단계별 QA 산출물 파일명을 명시할 수 있다.
```

**변경이력 추가**: v2.8 항목 추가

---

### 요구사항 4: 자가 점검 프롬프트 추가

요구사항 1(§2.5 Artifact Gate)에 통합 포함됨. 별도 추가 작업 없음.

**확인**: §2.5 자가 점검 프롬프트가 다음을 포함하는지 검증:
- [x] 산출물 파일 존재 여부 확인 절차
- [x] 파일 존재 시 동작 명시
- [x] 파일 부재 시 동작 명시 (QA 재소환)
- [x] 빈 파일 시 동작 명시

---

### 요구사항 5: opwt ANALYSIS 단계 PM Gate 추가

**파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`

**변경 위치**: ANALYSIS 단계 "### 게이트" 섹션

**현재**:
```
ANALYSIS 완료 → 사용자 확인 (interactive) / PM 자율 승인 (agentic)
```

**변경 후**:
```
ANALYSIS 완료 → **PM Gate (자가 체크)** → 사용자 확인 (interactive) / PM 자율 승인 (agentic)
```

**PM Gate (자가 체크) 내용 추가**:

```markdown
### 게이트

ANALYSIS 완료 후 아래 절차를 순서대로 수행한다:

1. **PM Gate (자가 체크)** — ANALYSIS는 PM이 직접 수행하는 단계이므로 외부 QA 에이전트 호출 없이 PM이 자가 점검한다.
   - AGENT.md 검토 기준(§4) 7항목을 체크한다
   - ANALYSIS.md 내용이 모든 워커 결과를 취합하고 있는지 확인한다
   - 문서별 요약 및 이슈 목록이 누락 없이 작성되었는지 확인한다
   - Artifact Gate: `ANALYSIS.md` 파일이 존재하고 내용이 있는지 확인한다
2. 사용자 확인 (interactive) / PM 자율 승인 (agentic)
```

**설계 근거** (PM 사전 분석 반영):
- ANALYSIS 단계는 PM이 워커 결과를 직접 취합하는 구조이므로, 외부 QA 에이전트 호출이 아닌 **자가 체크(Self-check)** 방식
- 다른 스킬(opd 등)의 ANALYSIS PM Gate와 일관성 확보
- "사용자 확인"만 있던 구조에서 PM 검토 기준 체크 추가

**변경이력 추가**: v2.5 항목

---

### 요구사항 6: opwt EXECUTE 배치 "PM 검토" → PM Gate 명확화

**파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`

**변경 위치**: EXECUTE 단계 "### 게이트 (배치별)" 섹션

**현재**:
```
배치 완료 → **QA Gate** (op-task-qa) → PM 검토 → 사용자 확인 (interactive) / PM 자율 승인 후 다음 배치 (agentic)
```

**변경 후**:
```
배치 완료 → **QA Gate** (op-task-qa) → **PM Gate** (배치 단위 간이 검토 — 하네스 §3 참조. 전체 PM Gate는 QA 단계 최종 판정에서 수행) → 사용자 확인 (interactive) / PM 자율 승인 후 다음 배치 (agentic)
```

**설계 근거** (PM 사전 분석 반영):
- 구조 변경 없이 표기만 명확화
- "PM 검토" → "PM Gate"로 명칭 통일 (하네스 §3 용어와 일치)
- 배치 단위 간이 검토임을 명시 (§3 전체 PM Gate와 구분)
- QA 단계 말미의 "PM 최종 판정"이 실질적 전체 PM Gate 역할임을 참조 명시

**변경이력 추가**: v2.5 항목

---

## 3. 실행 체크리스트

### Step 1: opal-harness-interactive.md 수정

- [x] §2와 §3 사이에 §2.5 Artifact Gate 섹션 삽입
- [x] §2.5에 자가 점검 프롬프트(3단계 확인 절차) 포함
- [x] §2.5에 판정 테이블(존재/미존재/빈 파일 → 동작) 포함
- [x] §2.5에 "차단 원칙" 명시
- [x] 변경이력 v1.4 추가

### Step 2: opal-harness-agentic.md 수정

- [x] §4 강화 검토 기준에 Artifact Gate 항목 추가 (3번째 기준으로)
- [x] agentic 모드 특화 지침 추가 (자율 통과 시도 없이 반드시 Read 확인)
- [x] 변경이력 v1.2 추가

### Step 3: opal-harness.md 수정

- [x] §2 "QA 체크리스트 검증" 다음에 "QA 산출물 표준 파일명" 서브섹션 추가
- [x] 단계별 표준 파일명 테이블 작성 (PLAN QA-PLAN.md / EXECUTE QA-EXECUTE.md / ANALYSIS QA-ANALYSIS.md)
- [x] 스킬별 오버라이드 안내 추가
- [x] 변경이력 v2.8 추가

### Step 4: opwt SKILL.md — ANALYSIS PM Gate 추가

- [x] ANALYSIS 단계 "### 게이트" 절차를 "PM Gate(자가 체크) → 사용자 확인" 순으로 변경
- [x] 자가 체크 3항목 작성 (AGENT.md 검토 기준, 취합 확인, Artifact Gate)
- [x] 변경이력 v2.5 추가

### Step 5: opwt SKILL.md — EXECUTE PM 검토 → PM Gate 명확화

- [x] "### 게이트 (배치별)" 텍스트에서 "PM 검토" → "PM Gate (배치 단위 간이 검토 — ...)" 로 변경
- [x] 변경이력 v2.5 추가 (Step 4와 동일 버전으로 합산)

---

## 4. QA 체크리스트

### opal-harness-interactive.md

- [x] §2.5가 §2(QA Gate)와 §3(PM Gate) 사이에 정확히 위치하는가
- [x] AC: PM Gate 진입 조건에 "QA 산출물 파일이 존재해야 한다"가 명시되어 있는가
- [x] AC: 파일 부재 시 동작(QA 재소환)이 명시되어 있는가
- [x] AC: 자가 점검 프롬프트가 포함되어 있는가

### opal-harness-agentic.md

- [x] AC: agentic 모드에서도 QA 산출물 파일 부재 시 자율 통과가 차단됨이 명시되어 있는가
- [x] Artifact Gate 항목이 강화 검토 기준 목록에 포함되어 있는가

### opal-harness.md

- [x] AC: "PLAN QA 산출물: QA-PLAN.md", "EXECUTE QA 산출물: QA-EXECUTE.md" 형식으로 필수 파일이 명시되어 있는가
- [x] 스킬별 오버라이드 안내가 포함되어 있는가

### opwt SKILL.md — ANALYSIS 게이트

- [x] AC: ANALYSIS 게이트 절차에 "PM Gate → 사용자 확인" 순서가 명시되어 있는가
- [x] PM Gate가 자가 체크 방식임이 명시되어 있는가
- [x] AGENT.md 검토 기준 체크, 취합 확인, Artifact Gate 3항목이 포함되어 있는가

### opwt SKILL.md — EXECUTE 배치 게이트

- [x] AC: EXECUTE 배치 게이트 절차가 "QA Gate → PM Gate (배치 단위 간이 검토 — 하네스 §3 참조)" 형식으로 명시되어 있는가
- [x] "전체 PM Gate는 QA 단계 최종 판정에서 수행" 참조가 포함되어 있는가

---

## 5. 변경 파일 목록

| 파일 | 변경 유형 | 변경 규모 |
|------|---------|---------|
| `opal/core/references/opal-harness-interactive.md` | 섹션 추가 | §2.5 신설 (~15줄) |
| `opal/core/references/opal-harness-agentic.md` | 목록 항목 추가 | §4 강화 검토 기준 1항목 추가 (~5줄) |
| `opal/core/references/opal-harness.md` | 서브섹션 추가 | §2 내 QA 산출물 명세 추가 (~12줄) |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 섹션 수정 | ANALYSIS 게이트 확장 + EXECUTE 게이트 표기 변경 (~10줄) |

**수정 없는 파일** (필수 산출물 명세는 harness 공통화로 처리):
- `opal/skills/opal-pilot-project/SKILL.md` — 변경 불필요
- `opal/skills/opal-pilot-dev-short/SKILL.md` — 변경 불필요
- `opal/skills/opal-pilot-dev/SKILL.md` — 변경 불필요
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md` — 변경 불필요
- `opal/skills/opal-pilot-sdd/SKILL.md` — 변경 불필요

---

## 6. 설계 판단 기록

| 판단 항목 | 결정 | 근거 |
|----------|------|------|
| Artifact Gate 위치 | interactive §2와 §3 사이 신설 | TASK.md 확정 방향 §1 — QA Gate 완료 후, PM Gate 진입 전 |
| 공통화 vs 인라인 | 하네스 공통화 (harness.md QA 산출물 명세) + 스킬별 최소 인라인 | 중복 제거. 표준 파일명은 공통 관리, 스킬별 오버라이드 허용 |
| opwt ANALYSIS PM Gate 방식 | 자가 체크(Self-check) | PM 직접 수행 단계이므로 외부 QA 에이전트 불필요. PM 사전 분석 반영 |
| opwt EXECUTE PM 검토 처리 | 표기 명확화만 (구조 변경 없음) | 배치 단위 간이 검토 구조는 의도적 설계. QA 단계 최종 판정이 전체 PM Gate 역할. PM 사전 분석 반영 |
| 타 SKILL.md 수정 여부 | 불필요 | Artifact Gate는 harness 공통 규칙으로 자동 적용. 오버라이드 필요 시만 SKILL.md 명시 |
