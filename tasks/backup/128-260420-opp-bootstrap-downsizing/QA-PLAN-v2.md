# QA-PLAN v2: 부트스트랩 다운사이징 — Method B 전환 검증

> 작성일: 2026-04-21  
> 검토 대상: PLAN.md v2 (C안 — 072 Method B 완전 채택)  
> 검토 기준: TASK.md 요구사항 + opal-harness.md §1 Guards + 오케스트레이터 확정 기준

---

## 판정

**⚠️ Conditional Pass — TASK.md 수정 필요 (3건), EXECUTE 전 사용자 확인 요**

PLAN v2의 Method B 설계는 논리적으로 일관되고 072 ANALYSIS 권장안과 정합한다.  
단, TASK.md가 Method A-hybrid 기준으로 작성되어 있어 C안과 직접 충돌하는 항목이 3건 존재한다.  
아래 TASK.md 수정안을 사용자가 승인하면 Gate Pass 처리한다.

---

## §1. TASK.md 충돌 분석

### ①-CRITICAL: 제약 "§2 모듈 구조 Eager 유지" vs PLAN v2 §2 Lazy 이동

**원문** (TASK.md 제약 조건):
> "opal-harness.md에서 §1 Guards와 §2 모듈 구조는 반드시 Eager 유지 (세션 시작부터 활성 필요)"

**PLAN v2 처리**: §2 모듈 구조 → `opal-harness-detail.md` 🟡 이동 (Lazy)

**충돌 근거**: TASK.md는 §2의 "서브 하네스 로딩 규칙"이 세션 시작부터 필요하다고 명시.  
072 ANALYSIS는 §2를 🟡로 분류하며, Lazy 트리거 테이블이 이 역할을 대신할 수 있다고 판단.

**C안 채택 시 수정안**:
- 제약 변경: "§1 Guards는 반드시 Eager 유지. §2 모듈 구조는 opal-harness-detail.md로 이동하고, 모듈 탐색 경로 규칙은 §1 Guards 말미에 1줄 요약 추가."
- B-4 요구사항 재정의: "§2 모듈 테이블에 state.md/task-process.md 행 추가" → "opal-harness-detail.md §2 모듈 테이블에 해당 행 추가"

### ②-CRITICAL: C-1 "opal-pm.md Read 제거" vs PLAN v2 §1+§2 Eager 유지

**원문** (TASK.md C-1):
> "AGENT.md Eager에 opal-pm.md Read 지시 없음, PM 컨텍스트 로드 2단계 절차가 AGENT.md에 직접 명시"

**PLAN v2 처리**: opal-pm.md §1+§2 (531 tok) Eager 유지. §2를 AGENT.md에 인라인하지 않음.

**충돌 근거**: 072 ANALYSIS §1.3은 §1+§2를 🔴로 분류 — Eager 유지가 올바른 분류.  
C안은 opal-pm.md를 완전 Lazy가 아닌 "🔴만 Eager, 🟡 Lazy"로 처리.  
절감량: 531 tok은 Eager에 남음 (C-1의 531 tok 추가 절감 포기).

**C안 채택 시 수정안**:
- C-1 변경: "opal-pm.md는 §1+§2 (~531 tok)만 Eager 유지. §3~§11은 opal-pm-detail.md로 분리."
- AC 변경: "Eager 단계에 opal-pm.md Read 지시 유지 (파일 자체는 유지, 내용만 슬림화)"

### ③-MAJOR: C-4 "opal-pm.md Lazy 트리거" vs PLAN v2 opal-pm-detail.md Lazy

**원문** (TASK.md C-4):
> "Lazy 트리거 테이블에 opal-pm.md 항목 추가"

**PLAN v2 처리**: opal-pm.md는 Eager 유지, opal-pm-detail.md가 Lazy 트리거 대상.

**C안 채택 시 수정안**:
- C-4 변경: "Lazy 트리거 테이블에 opal-pm-detail.md 항목 추가 (트리거: PM Gate 수행 시 / 학습 루프 진입 시)"

---

## §2. TASK.md 미충족 요구사항 (Method B 미포함)

### B-4 재해석

**원문**: "§2 하네스 모듈 테이블에 state.md, task-process.md 행 추가"  
**Method B**: §2가 opal-harness-detail.md로 이동 → 테이블도 detail 파일에 존재  
**판정**: AC 재정의 필요. opal-harness-detail.md §2 테이블에 두 행 추가로 대체.

### D-3: Cursor/Antigravity 절 처리

**원문**: "제거" (실제 삭제)  
**PLAN v2**: 🟡 이동으로 AGENT-detail.md에 포함  
**판정**: 진정한 dead code이므로 AGENT-detail.md에서도 제외(삭제)하는 것이 올바름.  
N-1 설계에 "D-4/D-5 제외 항목(Cursor/Antigravity 절)은 AGENT-detail.md에도 포함하지 않음" 명시 필요.

---

## §3. PLAN v2 내부 일관성 검증

| 항목 | 결과 | 비고 |
|------|------|------|
| 신규 파일 7개 — 서로 독립, 순서 병렬 가능 | ✅ | |
| Step 1 → Step 2A/2B → Step 3 → Step 4 의존관계 | ✅ | |
| opal-harness.md §1 Guards Eager 보존 | ✅ | M-2에 명시 |
| opal-pm.md §1+§2 Eager 보존 | ✅ | M-3에 명시 |
| AGENT.md Eager 1~7 번호 보존 | ✅ | M-1에 명시 |
| Lazy 트리거 3행 (AGENT-detail / harness-detail / pm-detail) | ✅ | M-1에 명시 |
| install-mac.sh strip 대상: AGENT.md + opal-harness.md | ✅ | M-4에 명시 |
| N-2 opal-harness-detail.md → state.md / task-process.md 참조 | ✅ | N-2 설계에 명시 |
| N-3 opal-pm-detail.md → pm-review-gate.md / doc-code-mismatch.md 참조 | ✅ | N-3 설계에 명시 |
| D-3 Cursor/Antigravity: AGENT-detail.md 제외 명시 | ❌ Warning | N-1 설계에 미명시 |
| §2 모듈 구조 Lazy 이동 시 탐색 경로 규칙 gap | ❌ Warning | §1 Guards에 탐색 경로 요약 1줄 추가 필요 |

---

## §4. Warning 처리 방안

**Warning-1: N-1 Cursor/Antigravity 제외 미명시**  
→ PLAN.md N-1 설계에 한 줄 추가: "단, D-4(Cursor 부트스트래퍼)/D-5(Antigravity 부트스트래퍼) 절은 dead code이므로 AGENT-detail.md에서도 제외(삭제)한다."

**Warning-2: §2 Lazy 이동 시 탐색 경로 규칙 gap**  
→ PLAN.md M-2 설계에 추가: "§1 Guards 말미에 탐색 경로 규칙 1줄 삽입: '모듈 탐색 경로: `{프로젝트}/.opal/references/harness/` → `~/.opal/references/harness/` (상세: opal-harness-detail.md §2 참조)'"

---

## §5. 예상 절감량 검증

| 항목 | 072 ANALYSIS | PLAN v2 |
|------|-------------|---------|
| AGENT.md Eager 토큰 | 1,816 tok | 1,816 tok ✅ |
| opal-harness.md Eager 토큰 | 792 tok (Guards만) | 792 tok ✅ |
| opal-pm.md Eager 토큰 | 531 tok (§1+§2) | 531 tok ✅ |
| Lazy 트리거 오버헤드 | +200 B (~50 tok) | +3행 (~50 tok) ✅ |
| 전체 Eager (3파일) | ~3,189 tok | ~3,189 tok ✅ |
| identity+MEMORY+프로젝트 포함 | ~7,387 tok | ~7,387 tok ✅ |

---

## §6. TASK.md 수정안 요약

사용자 승인 필요 항목 (3건):

| # | 위치 | 현행 | C안 수정 |
|---|------|------|---------|
| ① | 제약 조건 | "§2 모듈 구조는 반드시 Eager 유지" | "§2는 opal-harness-detail.md 이동, §1 Guards에 탐색 경로 1줄 보완" |
| ② | C-1 | "opal-pm.md Read 지시 없음" | "opal-pm.md §1+§2 Eager 유지 (531 tok), §3~§11 → detail Lazy" |
| ③ | C-4 | "Lazy 트리거에 opal-pm.md 추가" | "Lazy 트리거에 opal-pm-detail.md 추가" |
